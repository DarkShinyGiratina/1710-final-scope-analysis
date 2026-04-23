from scope_ast import parse
from static_scope import StaticScopeExecutor
from dyn_scope import DynamicScopeExecutor
import z3

# This program defines x=10, then a function f that uses x.
# Then it redefines x=20 and calls f.
code = """
(let x 10
  (let f (lambda y (+ x y))
    (let x 20
      (apply f 5))))
"""

ast = parse(code)
static_res = StaticScopeExecutor().execute(ast)
# Static: f captured x=10. Result: 10 + 5 = 15
print(f"Static Result: {static_res}") 

dyn_res = DynamicScopeExecutor().execute(ast)
# Dynamic: f looks at current stack where x=20. Result: 20 + 5 = 25
print(f"Dynamic Result: {dyn_res}")

# Use Z3 to prove they are different
solver = z3.Solver()
solver.add(static_res != dyn_res)
if solver.check() == z3.sat:
    print("Static and Dynamic scoping yield different symbolic results.")
