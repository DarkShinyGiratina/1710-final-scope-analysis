import re
from typing import List


class ASTNode:
    pass


class Int(ASTNode):
    def __init__(self, value: int) -> None:
        self.value: int = value


class Var(ASTNode):
    def __init__(self, name: str) -> None:
        self.name: str = name


class Let(ASTNode):
    def __init__(self, name: str, value: ASTNode, body: ASTNode) -> None:
        self.name: str = name
        self.value: ASTNode = value
        self.body: ASTNode = body


class If(ASTNode):
    def __init__(
        self, condition: ASTNode, then_branch: ASTNode, else_branch: ASTNode
    ) -> None:
        self.condition: ASTNode = condition
        self.then_branch: ASTNode = then_branch
        self.else_branch: ASTNode = else_branch


class BinOp(ASTNode):
    def __init__(self, left: ASTNode, operator: str, right: ASTNode) -> None:
        self.left: ASTNode = left
        self.operator: str = operator
        self.right: ASTNode = right


class CondOp(ASTNode):
    def __init__(self, left: ASTNode, operator: str, right: ASTNode) -> None:
        self.left: ASTNode = left
        self.operator: str = operator
        self.right: ASTNode = right


class Lambda(ASTNode):
    def __init__(self, params: list[str], body: ASTNode):
        self.params = params
        self.body = body


class Apply(ASTNode):
    def __init__(self, func: ASTNode, args: list[ASTNode]):
        self.func = func
        self.args = args


def pretty_print(node: ASTNode, toplevel_name: str | None = None) -> str:
    match node:
        case Int():
            return str(node.value)
        case Var():
            return node.name
        case BinOp():
            return f"({node.operator} {pretty_print(node.left)} {pretty_print(node.right)})"
        case Let():
            return f"(let ([{node.name} {pretty_print(node.value)}])\n  {pretty_print(node.body)})"
        case If():
            return f"(if {pretty_print(node.condition)}\n  {pretty_print(node.then_branch)}\n  {pretty_print(node.else_branch)})"
        case CondOp():
            return f"({node.operator} {pretty_print(node.left)} {pretty_print(node.right)})"
        case Lambda():
            params = " ".join(node.params)
            body_str = pretty_print(node.body)

            # use deffun for top-level lambdas
            if toplevel_name is not None:
                return f"(deffun ({toplevel_name} {params})\n {body_str})"
            else:
                return f"(lambda ({params}) {body_str})"
        case Apply():
            args = " ".join(pretty_print(a) for a in node.args)
            return f"({pretty_print(node.func)} {args})"
        case _:
            return f"<unknown node: {type(node).__name__}>"
