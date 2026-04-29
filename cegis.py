import z3
from scope_ast import *
from static_scope import StaticScopeExecutor
from dyn_scope import DynamicScopeExecutor
from multiprocessing import Pool, cpu_count
import random


def exhaustive_random_yield(generators):
    while True:
        gen_index = random.randint(0, len(generators) - 1)
        try:
            yield next(generators[gen_index])
        except StopIteration:
            generators.pop(gen_index)
            if not generators:
                break
    return


def gen_leaf(available_vars):
    gens = [available_vars, [0, 1, 5, 10]]
    yield from exhaustive_random_yield([map(Var, gens[0]), map(Int, gens[1])])

    # for var in available_vars:
    #     yield Var(var)
    # for n in [0, 1, 5, 10]:
    #     yield Int(n)


def gen_val(depth, available_vars):
    if depth == 0:
        yield from gen_leaf(available_vars)
        return

    # leaves = list(gen_leaf(available_vars))
    # sub_fun = list(gen_fun(depth - 1, available_vars))
    # sub_val_x = list(gen_val(depth - 1, available_vars + ["x"]))

    # for val in leaves:  # ← leaf, not sub_val
    #     for body in sub_val_x:
    #         yield Let("x", val, body)

    # for func in sub_fun:
    #     for arg in leaves:  # ← leaf, not sub_val
    #         yield Apply(func, [arg])

    # for op in ["+", "-", "*", "/"]:
    #     for left in leaves:
    #         for right in leaves:
    #             yield BinOp(left, op, right)

    get_leaf_gen = lambda: gen_leaf(available_vars)
    sub_fun_gen = gen_fun(depth - 1, available_vars)
    sub_val_gen = gen_val(depth - 1, available_vars + ["x"])
    get_op_gen = lambda: random.sample(["+", "-", "*", "/"], k=4)

    let_gen = (Let("x", val, body) for body in sub_val_gen for val in get_leaf_gen())
    apply_gen = (Apply(func, [arg]) for func in sub_fun_gen for arg in get_leaf_gen())
    binop_gen = (
        BinOp(left, op, right)
        for op in get_op_gen()
        for left in get_leaf_gen()
        for right in get_leaf_gen()
    )

    yield from exhaustive_random_yield([let_gen, apply_gen, binop_gen])


def gen_fun(depth, available_vars):
    if depth == 0:
        return

    # leaves = list(gen_leaf(available_vars))
    # sub_val_y = list(gen_val(depth - 1, available_vars + ["y"]))
    # sub_fun_x = list(gen_fun(depth - 1, available_vars + ["x"]))

    # for body in sub_val_y:
    #     yield Lambda(["y"], body)

    # for val in leaves:  # ← leaf, not sub_val
    #     for body in sub_fun_x:
    #         yield Let("x", val, body)

    get_leaf_gen = lambda: gen_leaf(available_vars)
    sub_val_y_gen = gen_val(depth - 1, available_vars + ["y"])
    sub_fun_x_gen = gen_fun(depth - 1, available_vars + ["x"])

    lambda_gen = (Lambda(["y"], body) for body in sub_val_y_gen)
    let_gen = (Let("x", val, body) for body in sub_fun_x_gen for val in get_leaf_gen())

    yield from exhaustive_random_yield([lambda_gen, let_gen])


def free_vars(expr) -> set:
    """Get z3 free variable names from an expression."""
    if z3.is_const(expr):
        return {str(expr)} if expr.decl().kind() == z3.Z3_OP_UNINTERPRETED else set()
    return set().union(*[free_vars(expr.arg(i)) for i in range(expr.num_args())])


def check_candidate(generated_body):
    """
    Worker function. Each process owns its z3 Solver.
    Returns a dict of strings on divergence, None otherwise.
    """
    top_level_params = ["a", "b"]
    program = Lambda(top_level_params, generated_body)
    top_level_call = Apply(program, [Var("input_a"), Var("input_b")])

    try:
        static_val = StaticScopeExecutor().execute(top_level_call)
        dyn_val = DynamicScopeExecutor().execute(top_level_call)

        if str(static_val) == str(dyn_val):
            return None
        if not z3.is_expr(static_val) or not z3.is_expr(dyn_val):
            return None
        if free_vars(static_val) != free_vars(dyn_val):
            return None  # degenerate: one has an unbound variable the other doesn't

        solver = z3.Solver()
        solver.add(static_val != dyn_val)
        if solver.check() == z3.sat:
            model = solver.model()
            return {
                "program": pretty_print(program),
                "static": str(static_val),
                "dynamic": str(dyn_val),
                "input_a": str(model[z3.Int("input_a")]),
                "input_b": str(model[z3.Int("input_b")]),
            }
    except (TypeError, NameError):
        return None

    return None


def synthesize_diverging_program():
    for depth in range(6, 7):
        print(f"Searching tree depth {depth}...")

        count = 0
        with Pool(processes=cpu_count()) as pool:
            for result in pool.imap_unordered(
                check_candidate, gen_val(depth, ["a", "b"]), chunksize=64
            ):
                count += 1
                if count % 10000 == 0:
                    print(f"  ... {count} candidates checked", flush=True)

                if result is not None:
                    pool.terminate()
                    print(f"\n--- DIVERGENCE FOUND! (after {count} candidates) ---")
                    print(f"Synthesized program:\n{result['program']}")
                    print(f"Static Expression:  {result['static']}")
                    print(f"Dynamic Expression: {result['dynamic']}")
                    print(
                        f"Counter-example inputs: a={result['input_a']}, b={result['input_b']}"
                    )
                    return

        print(f"  Depth {depth} exhausted: {count} candidates, no divergence found")


if __name__ == "__main__":
    synthesize_diverging_program()
