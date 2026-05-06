from scope_ast import *
import z3


class DynamicScopeExecutor:
    def __init__(self):
        # Stack of environments: List[Dict[str, z3_expr]]
        self.environment_stack = [{}]

    def execute(self, node: ASTNode):
        match node:
            case Int():
                return z3.IntVal(node.value)

            case Var():
                for env in reversed(self.environment_stack):
                    if node.name in env:
                        return env[node.name]
                return z3.Int(node.name)

            case Let():
                val = self.execute(node.value)
                # Create new scope level
                new_env = {node.name: val}
                self.environment_stack.append(new_env)
                result = self.execute(node.body)
                self.environment_stack.pop()
                return result

            case If():
                condition = self.execute(node.condition)
                # normalize to Bool if needed
                if z3.is_bool(condition):
                    cond_expr = condition
                else:
                    cond_expr = condition != 0
                return z3.If(
                    cond_expr,
                    self.execute(node.then_branch),
                    self.execute(node.else_branch),
                )

            case CondOp():
                left = self.execute(node.left)
                right = self.execute(node.right)
                op = node.operator
                if op in ("=", "=="):
                    return left == right
                if op == "<":
                    return left < right
                if op == ">":
                    return left > right
                if op == "<=":
                    return left <= right
                if op == ">=":
                    return left >= right
                raise ValueError(f"Unknown conditional operator {op}")

            case BinOp():
                return self._evaluate_binop(
                    node.operator, self.execute(node.left), self.execute(node.right)
                )

            case Lambda():
                return node  # Just return the AST; no environment captured

            case Apply():
                func = self.execute(node.func)
                if isinstance(func, Lambda):
                    arg_vals = [self.execute(arg) for arg in node.args]

                    # Bind all parameters in a new environment frame
                    new_env = {param: val for param, val in zip(func.params, arg_vals)}
                    self.environment_stack.append(new_env)

                    result = self.execute(func.body)
                    self.environment_stack.pop()
                    return result
                raise TypeError(f"Cannot apply non-function: {func}")

            case _:
                raise NotImplementedError(f"Unhandled node type: {type(node)}")

    def _evaluate_binop(self, operator, left, right):
        if not z3.is_expr(left) or not z3.is_expr(right):
            raise TypeError(
                f"BinOp operands must be z3 expressions, got {type(left)}, {type(right)}"
            )
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            return left / right
        raise ValueError(f"Unknown operator {operator}")
