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
    def __init__(self, condition: ASTNode, then_branch: ASTNode, else_branch: ASTNode) -> None:
        self.condition: ASTNode = condition
        self.then_branch: ASTNode = then_branch
        self.else_branch: ASTNode = else_branch

class BinOp(ASTNode):
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

class Parser:
    def __init__(self, tokens: List[str]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> ASTNode:
        if self.position >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")
        
        token = self.tokens[self.position]
        self.position += 1

        if token == "(":
            return self.parse_list()
        elif token.isdigit():
            return Int(int(token))
        elif re.match(r"[a-zA-Z_]\w*", token):
            return Var(token)
        else:
            raise SyntaxError(f"Unexpected token: {token}")

    def parse_list(self) -> ASTNode:
        if self.position >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")
        
        start_token = self.tokens[self.position]
        self.position += 1

        if start_token == "let":
            name = self.tokens[self.position]
            self.position += 1
            value = self.parse()
            body = self.parse()
            self.consume(")")
            return Let(name, value, body)

        elif start_token == "if":
            condition = self.parse()
            then_branch = self.parse()
            else_branch = self.parse()
            self.consume(")")
            return If(condition, then_branch, else_branch)

        elif start_token == "lambda":
            param = self.tokens[self.position]
            self.position += 1
            body = self.parse()
            self.consume(")")
            return Lambda(param, body)

        elif start_token == "apply":
            func = self.parse()
            arg = self.parse()
            self.consume(")")
            return Apply(func, arg)

        elif start_token in {"+", "-", "*", "/"}:
            left = self.parse()
            right = self.parse()
            self.consume(")")
            return BinOp(left, start_token, right)

        else:
            raise SyntaxError(f"Unknown expression: {start_token}")

    def consume(self, expected_token: str) -> None:
        if self.position >= len(self.tokens) or self.tokens[self.position] != expected_token:
            raise SyntaxError(f"Expected '{expected_token}'")
        self.position += 1

def tokenize(src: str) -> List[str]:
    return re.findall(r"[()]|[a-zA-Z_]\w*|[+-/*=<>!?]+|\d+", src)

def parse(src: str) -> ASTNode:
    tokens = tokenize(src)
    parser = Parser(tokens)
    return parser.parse()
