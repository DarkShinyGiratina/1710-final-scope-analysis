from scope_ast import *
import z3


class Closure:
    """Captures the definition-time environment for static scoping."""

    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env


class StaticScopeExecutor:
    def __init__(self):
        self.environment = {}

    def execute(self, node: ASTNode):
        match node:
            case Int():
                return z3.IntVal(node.value)

            case Var():
                if node.name in self.environment:
                    return self.environment[node.name]
                # If variable is not in env, treat it as a symbolic constant
                return z3.Int(node.name)

            case Let():
                old_env = self.environment.copy()
                self.environment[node.name] = self.execute(node.value)
                result = self.execute(node.body)
                self.environment = old_env
                return result

            case If():
                condition = self.execute(node.condition)
                then_val = self.execute(node.then_branch)
                else_val = self.execute(node.else_branch)
                # Returns a symbolic conditional expression
                return z3.If(condition != 0, then_val, else_val)

            case BinOp():
                left = self.execute(node.left)
                right = self.execute(node.right)
                return self._evaluate_binop(node.operator, left, right)

            case Lambda():
                # Capture the current environment (Lexical Scoping)
                return Closure(node.params, node.body, self.environment.copy())

            case Apply():
                closure = self.execute(node.func)
                if isinstance(closure, Closure):
                    # Evaluate all arguments first
                    arg_vals = [self.execute(arg) for arg in node.args]

                    old_env = self.environment
                    self.environment = closure.env.copy()
                    # Bind all parameters
                    for param, val in zip(closure.params, arg_vals):
                        self.environment[param] = val

                    result = self.execute(closure.body)
                    self.environment = old_env
                    return result

    def _evaluate_binop(self, operator, left, right):
        if not z3.is_expr(left) or not z3.is_expr(right):
            raise TypeError(f"BinOp operands must be z3 expressions, got {type(left)}, {type(right)}")
        if operator == '+':
            return left + right
        if operator == '-':
            return left - right
        if operator == '*':
            return left * right
        if operator == '/':
            return left / right
        raise ValueError(f"Unknown operator {operator}")
