import unittest
import z3

from scope_ast import Int, Var, Let, BinOp, Lambda, Apply
from static_scope import StaticScopeExecutor
from dyn_scope import DynamicScopeExecutor
from cegis import free_vars, check_candidate, gen_val


def static(node):
    return StaticScopeExecutor().execute(node)


def dynamic(node):
    return DynamicScopeExecutor().execute(node)


def z3_eq(a, b):
    """Two z3 expressions are semantically equal iff (a != b) is unsat."""
    s = z3.Solver()
    s.add(a != b)
    return s.check() == z3.unsat


# Make sure both interpreters work (and agree!) when not dealing with closures
class InterpreterAgreementTests(unittest.TestCase):
    """Programs without captured free variables: both scopes must agree."""

    def test_int_literal(self):
        self.assertTrue(z3_eq(static(Int(7)), z3.IntVal(7)))
        self.assertTrue(z3_eq(dynamic(Int(7)), z3.IntVal(7)))

    def test_free_var_is_symbolic(self):
        self.assertTrue(z3_eq(static(Var("a")), z3.Int("a")))
        self.assertTrue(z3_eq(dynamic(Var("a")), z3.Int("a")))

    def test_binop_arithmetic(self):
        node = BinOp(Int(3), "+", Int(4))
        self.assertTrue(z3_eq(static(node), z3.IntVal(7)))
        self.assertTrue(z3_eq(dynamic(node), z3.IntVal(7)))

    def test_let_binding(self):
        # let x = 5 in x + 1
        node = Let("x", Int(5), BinOp(Var("x"), "+", Int(1)))
        self.assertTrue(z3_eq(static(node), z3.IntVal(6)))
        self.assertTrue(z3_eq(dynamic(node), z3.IntVal(6)))

    def test_apply_no_capture(self):
        # (lambda y: y + 1)(10) == 11 under both
        node = Apply(Lambda(["y"], BinOp(Var("y"), "+", Int(1))), [Int(10)])
        self.assertTrue(z3_eq(static(node), z3.IntVal(11)))
        self.assertTrue(z3_eq(dynamic(node), z3.IntVal(11)))

    def test_top_level_uses_inputs(self):
        # ((lambda a, b: a + b) input_a input_b) == input_a + input_b
        program = Lambda(["a", "b"], BinOp(Var("a"), "+", Var("b")))
        call = Apply(program, [Var("input_a"), Var("input_b")])
        expected = z3.Int("input_a") + z3.Int("input_b")
        self.assertTrue(z3_eq(static(call), expected))
        self.assertTrue(z3_eq(dynamic(call), expected))


class InterpreterDivergenceTests(unittest.TestCase):
    """Canonical programs where static and dynamic scope disagree."""

    def test_classic_capture(self):
        # let f = (lambda y: a + y) in let a = b in f(0)
        body = Let(
            "f",
            Lambda(["y"], BinOp(Var("a"), "+", Var("y"))),
            Let("a", Var("b"), Apply(Var("f"), [Int(0)])),
        )
        program = Lambda(["a", "b"], body)
        call = Apply(program, [Var("input_a"), Var("input_b")])

        s_val = static(call)
        d_val = dynamic(call)

        self.assertTrue(z3_eq(s_val, z3.Int("input_a")))
        self.assertTrue(z3_eq(d_val, z3.Int("input_b")))
        self.assertFalse(z3_eq(s_val, d_val))


# tests for CEGIS
class FreeVarsTests(unittest.TestCase):
    def test_intval_has_no_free_vars(self):
        self.assertEqual(free_vars(z3.IntVal(5)), set())

    def test_symbolic_int(self):
        self.assertEqual(free_vars(z3.Int("a")), {"a"})

    def test_compound(self):
        e = z3.Int("a") + z3.Int("b") * z3.IntVal(3)
        self.assertEqual(free_vars(e), {"a", "b"})


# Bodies are passed to check_candidate, which wraps them as
# (lambda a, b. body)(input_a, input_b).

DIVERGENT_USES_BOTH = Let(
    "f",
    Lambda(["y"], BinOp(Var("a"), "+", Var("y"))),
    Let("a", Var("b"), Apply(Var("f"), [Int(0)])),
)
# static: input_a, dynamic: input_b -- both inputs appear

DIVERGENT_IGNORES_INPUTS = Let(
    "x",
    Int(5),
    Let(
        "f",
        Lambda(["y"], BinOp(Var("x"), "+", Var("y"))),
        Let("x", Int(100), Apply(Var("f"), [Int(0)])),
    ),
)
# static: 5, dynamic: 100 -- diverges, but neither input_a nor input_b appears

DIVERGENT_ONE_INPUT = Let(
    "f",
    Lambda(["y"], BinOp(Var("a"), "+", Var("y"))),
    Let("a", Int(100), Apply(Var("f"), [Int(0)])),
)
# static: input_a, dynamic: 100 -- only input_a appears

CONVERGENT = BinOp(Var("a"), "+", Var("b"))
# both: input_a + input_b


class CheckCandidateTests(unittest.TestCase):
    def test_divergent_uses_both_inputs_returns_dict(self):
        result = check_candidate(DIVERGENT_USES_BOTH)
        assert result is not None
        # Guarantee our inputs are actually used
        self.assertNotEqual(result["input_a"], "None")
        self.assertNotEqual(result["input_b"], "None")
        self.assertNotEqual(result["static"], result["dynamic"])

    def test_convergent_returns_none(self):
        self.assertIsNone(check_candidate(CONVERGENT))

    # test our input filter (made to get more "interesting" programs)
    def test_divergent_but_ignores_inputs_filtered_out(self):
        self.assertIsNone(check_candidate(DIVERGENT_IGNORES_INPUTS))

    def test_divergent_with_only_one_input_filtered_out(self):
        self.assertIsNone(check_candidate(DIVERGENT_ONE_INPUT))


def ast_height(node) -> int:
    match node:
        case Int() | Var():
            return 1
        case Let():
            return 1 + max(ast_height(node.value), ast_height(node.body))
        case BinOp():
            return 1 + max(ast_height(node.left), ast_height(node.right))
        case Lambda():
            return 1 + ast_height(node.body)
        case Apply():
            return 1 + max([ast_height(node.func)] + [ast_height(a) for a in node.args])
        case _:
            raise AssertionError(f"unexpected node {type(node).__name__}")


def assert_well_scoped(node, scope: set):
    """Raise AssertionError if any Var in `node` references a name not in `scope`."""
    match node:
        case Int():
            return
        case Var():
            assert node.name in scope, f"unbound variable {node.name!r} (scope: {scope})"
        case Let():
            assert_well_scoped(node.value, scope)
            assert_well_scoped(node.body, scope | {node.name})
        case BinOp():
            assert_well_scoped(node.left, scope)
            assert_well_scoped(node.right, scope)
        case Lambda():
            assert_well_scoped(node.body, scope | set(node.params))
        case Apply():
            assert_well_scoped(node.func, scope)
            for a in node.args:
                assert_well_scoped(a, scope)
        case _:
            raise AssertionError(f"unexpected node {type(node).__name__}")


class GeneratorTests(unittest.TestCase):
    """Property tests sampling from the (random, infinite) gen_val stream."""

    SAMPLES = 200

    def _sample(self, depth, available_vars):
        gen = gen_val(depth, list(available_vars))
        out = []
        for _ in range(self.SAMPLES):
            try:
                out.append(next(gen))
            except StopIteration:
                break
        # depth>=1 should be able to produce SAMPLES candidates without exhausting
        self.assertGreater(len(out), 0)
        return out

    def test_all_samples_are_well_scoped(self):
        # Top-level scope is whatever the synthesizer passes in. CEGIS uses ["a","b"].
        available = {"a", "b"}
        for node in self._sample(depth=3, available_vars=available):
            assert_well_scoped(node, available)

    def test_depth_bounds_height(self):
        # Each recursion step adds at most one Lambda/Let/Apply/BinOp wrapper
        # plus a leaf. Height grows roughly linearly in `depth`; cap generously.
        depth = 3
        max_expected_height = 2 * depth + 2
        for node in self._sample(depth=depth, available_vars={"a", "b"}):
            h = ast_height(node)
            self.assertLessEqual(
                h, max_expected_height,
                f"AST height {h} exceeds bound {max_expected_height} at depth {depth}",
            )

    def test_depth_zero_emits_only_leaves(self):
        gen = gen_val(0, ["a", "b"])
        for _ in range(50):
            try:
                node = next(gen)
            except StopIteration:
                break
            self.assertIn(type(node), (Int, Var))


if __name__ == "__main__":
    unittest.main()
