# Language Syntax Documentation

## Overview

This document describes the formal grammar and syntax for the expression language supported by the parser in `scope_ast.py`. The language is Lisp-like with s-expression notation, supporting integers, variables, let-bindings, conditionals, lambdas, and binary operations.

---

## Grammar

```
⟨expr⟩    ::=  ⟨int⟩ 
             | ⟨var⟩ 
             | ⟨let⟩ 
             | ⟨if⟩ 
             | ⟨lambda⟩ 
             | ⟨apply⟩ 
             | ⟨binop⟩

⟨int⟩     ::= [0-9]+

⟨var⟩     ::= [a-zA-Z_][a-zA-Z0-9_]*

⟨let⟩     ::= "(" "let" ⟨var⟩ ⟨expr⟩ ⟨expr⟩ ")"

⟨if⟩      ::= "(" "if" ⟨expr⟩ ⟨expr⟩ ⟨expr⟩ ")"

⟨lambda⟩  ::= "(" "lambda" ⟨var⟩ ⟨expr⟩ ")"

⟨apply⟩   ::= "(" "apply" ⟨expr⟩ ⟨expr⟩ ")"

⟨binop⟩   ::= "(" ⟨op⟩ ⟨expr⟩ ⟨expr⟩ ")"

⟨op⟩      ::= "+" | "-" | "*" | "/"
```

---

## Syntax Elements

### 1. **Integers**

Integer literals represent constant numeric values.

**Syntax:**
```
⟨integer⟩ ::= [0-9]+
```

**Examples:**
```
0
42
1000
999999
```

**Notes:**
- Only non-negative integers are supported
- Integers are literals and evaluate to themselves

---

### 2. **Variables**

Variable names reference values bound in the current scope.

**Syntax:**
```
⟨variable⟩ ::= [a-zA-Z_][a-zA-Z0-9_]*
```

**Examples:**
```
x
myVariable
_private
count123
result
```

**Notes:**
- Must start with a letter or underscore
- Can contain letters, digits, and underscores after the first character
- Case-sensitive: `x` and `X` are different variables
- Variables must be bound (via `let` or lambda parameter) to be used

**Error:** Using an undefined variable raises `NameError`

---

### 3. **Let Bindings**

Bind a variable to a value within a scope.

**Syntax:**
```
(let ⟨variable⟩ ⟨value-expr⟩ ⟨body-expr⟩)
```

**Components:**
- `let`: Keyword indicating a binding
- `⟨variable⟩`: Name to bind (identifier)
- `⟨value-expr⟩`: Expression whose result is bound to the variable
- `⟨body-expr⟩`: Expression evaluated with the variable in scope

**Examples:**

Simple binding:
```
(let x 10 x)
→ 10
```

Binding with computation:
```
(let x 5 (+ x 20))
→ 25
```

Nested bindings:
```
(let x 10 (let y 20 (+ x y)))
→ 30
```

Shadowing (inner binding hides outer):
```
(let x 10 (let x 20 x))
→ 20
```

**Semantics:**
- Dynamic scope: Variable availability depends on the call stack
- Static scope: Variable availability is lexically determined at definition
- Shadowing: Inner bindings override outer ones with the same name

---

### 4. **Conditionals (If)**

Evaluate one of two branches based on a condition.

**Syntax:**
```
(if ⟨condition⟩ ⟨then-branch⟩ ⟨else-branch⟩)
```

**Components:**
- `if`: Keyword indicating conditional
- `⟨condition⟩`: Expression evaluated to determine branch
- `⟨then-branch⟩`: Expression evaluated if condition is truthy
- `⟨else-branch⟩`: Expression evaluated if condition is falsy

**Examples:**

Basic conditional:
```
(if 1 10 20)
→ 10
```

Falsy condition:
```
(if 0 10 20)
→ 20
```

With comparison:
```
(if (+ 5 5) 100 200)
→ 100  (condition evaluates to 10, which is truthy)
```

**Semantics:**
- Truthy: Any non-zero value
- Falsy: Zero (0)
- Only one branch is evaluated (short-circuit evaluation in static scope)

**Note:** In dynamic scope, both branches may be evaluated; the then-branch is used regardless.

---

### 5. **Lambda (Anonymous Functions)**

Define a function that takes one parameter.

**Syntax:**
```
(lambda ⟨parameter⟩ ⟨body⟩)
```

**Components:**
- `lambda`: Keyword indicating function definition
- `⟨parameter⟩`: Formal parameter name
- `⟨body⟩`: Expression defining the function body

**Examples:**

Simple identity function:
```
(lambda x x)
→ (lambda x x)  [function object, not evaluated]
```

Function adding 10:
```
(lambda x (+ x 10))
→ (lambda x (+ x 10))
```

**Semantics:**
- Lambdas are first-class values (can be passed around)
- A lambda expression returns the lambda itself, unevaluated
- Lambdas capture their lexical environment in static scope
- Lambdas use the dynamic environment in dynamic scope

---

### 6. **Function Application (Apply)**

Call a function with an argument.

**Syntax:**
```
(apply ⟨function⟩ ⟨argument⟩)
```

**Components:**
- `apply`: Keyword indicating function application
- `⟨function⟩`: Expression that evaluates to a lambda
- `⟨argument⟩`: Expression whose result becomes the parameter value

**Examples:**

Applying an inline lambda:
```
(apply (lambda x (+ x 10)) 5)
→ 15
```

Applying a bound function:
```
(let add-ten (lambda x (+ x 10))
  (apply add-ten 5))
→ 15
```

Multiple applications (currying-style):
```
(let double (lambda x (* x 2))
  (apply (lambda f (apply f 21)) double))
→ 42
```

**Error:** Attempting to apply a non-lambda raises `TypeError`

**Semantics:**
- Only lambdas can be applied; built-in operators are not lambdas
- Parameter binding follows the scoping rules of the executor
- The function body is evaluated with the parameter bound

---

### 7. **Binary Operations**

Arithmetic operations on two operands.

**Syntax:**
```
(⟨operator⟩ ⟨left⟩ ⟨right⟩)
```

**Operators:**

| Operator | Operation | Example | Result |
|----------|-----------|---------|--------|
| `+` | Addition | `(+ 5 3)` | `8` |
| `-` | Subtraction | `(- 10 4)` | `6` |
| `*` | Multiplication | `(* 6 7)` | `42` |
| `/` | Division | `(/ 20 4)` | `5` |

**Examples:**

Simple arithmetic:
```
(+ 10 20)
→ 30

(- 100 25)
→ 75

(* 6 7)
→ 42

(/ 100 5)
→ 20
```

Nested operations (left-to-right evaluation):
```
(+ (* 2 3) (- 10 4))
→ (+ 6 6)
→ 12
```

With variables:
```
(let x 5
  (let y 3
    (+ (* x y) (- x y))))
→ (+ 15 2)
→ 17
```

**Error:** Unknown operators raise `ValueError`

**Semantics:**
- Both operands are evaluated left-to-right
- Operations follow standard arithmetic rules
- Division performs floating-point division (Python `/` operator)

---

## Whitespace and Tokenization

The parser tokenizes input using the following rules:

**Token patterns:**
```
[()]              - Parentheses
[a-zA-Z_]\w*      - Identifiers (variables, keywords)
[+-/*=<>!?]+      - Operators
\d+               - Integers
```

**Whitespace:**
- Any amount of whitespace (spaces, tabs, newlines) between tokens is ignored
- Whitespace is required between tokens that would otherwise merge

**Examples:**

Equivalent forms (all parse identically):
```
(+ 1 2)
(+ 1 2)
(+1 2)        ← No space before 1
( + 1 2 )     ← Extra spaces
```

Invalid tokenization:
```
(+1 2)        ← Parsed as identifier "+1", not "+" and "1"
(add 1 2)     ← Identifier "add" not recognized as operator
```

---

## Complete Examples

### Example 1: Basic Arithmetic
```
Input:  (+ (* 3 4) 5)
Parse:  BinOp(BinOp(Int(3), "*", Int(4)), "+", Int(5))
Result: 17
```

### Example 2: Let Binding
```
Input:  (let x 10 (+ x 5))
Parse:  Let("x", Int(10), BinOp(Var("x"), "+", Int(5)))
Result: 15
```

### Example 3: Conditional
```
Input:  (if (- 10 10) 100 200)
Parse:  If(BinOp(Int(10), "-", Int(10)), Int(100), Int(200))
Result: 200
```

### Example 4: Lambda with Application
```
Input:  (apply (lambda x (+ x 1)) 41)
Parse:  Apply(Lambda("x", BinOp(Var("x"), "+", Int(1))), Int(41))
Result: 42
```

### Example 5: Nested Let with Lambda
```
Input:  (let f (lambda x (* x 2)) (apply f 21))
Parse:  Let("f", Lambda("x", BinOp(Var("x"), "*", Int(2))), 
            Apply(Var("f"), Int(21)))
Result: 42
```

### Example 6: Complex Expression
```
Input:  (let a 5 
          (let b 10 
            (if (+ a b) 
              (* a b) 
              0)))
Result: 50
```

---

## Error Handling

### Parser Errors

**SyntaxError: Unexpected end of input**
```
(+ 1
```
Incomplete expression; closing parenthesis expected.

**SyntaxError: Unexpected token**
```
(+ @ 2)
```
Invalid token `@` encountered.

**SyntaxError: Expected ')'**
```
(+ 1 2
```
Missing closing parenthesis.

**SyntaxError: Unknown expression**
```
(unknown x y)
```
Unknown keyword or invalid expression form.

### Execution Errors (Runtime)

**NameError: Variable '...' is not defined**
```
x
```
Variable `x` used without being bound.

**TypeError: Attempted to call non-lambda object**
```
(apply 42 10)
```
Trying to apply a non-function value.

**ValueError: Unknown operator '...'**
Operator not in `{+, -, *, /}` (internal parser error, should not occur).

---

## Scope Semantics

### Dynamic Scope
Variables are resolved from the current call stack. Inner scopes shadow outer scopes.

```
(let x 10
  (let f (lambda y (+ x y))
    (let x 20
      (apply f 1))))
→ 21  (x is 20 at application time)
```

### Static Scope
Variables are resolved from their lexical definition context. Bindings are fixed at definition.

```
(let x 10
  (let f (lambda y (+ x y))
    (let x 20
      (apply f 1))))
→ 11  (x is 10 from the outer binding)
```

---

## Implementation Notes

The parser in `scope_ast.py` provides:

- **`tokenize(src: str) → List[str]`**: Converts source string to tokens
- **`parse(src: str) → ASTNode`**: Parses tokens into an AST
- **`Parser` class**: Low-level parsing with position tracking
  - `parse()`: Parse a single expression
  - `parse_list()`: Parse a parenthesized list expression
  - `consume(token)`: Verify and consume an expected token

All syntax is converted to an AST of `ASTNode` subclasses:
`Int`, `Var`, `Let`, `If`, `BinOp`, `Lambda`, `Apply`
