import z3
from scope_ast import *
from static_scope import StaticScopeExecutor
from dyn_scope import DynamicScopeExecutor

def generate_ast(depth, available_vars):
    """
    Recursively generates AST expressions up to a certain depth.
    Restricted grammar to prevent combinatorial explosion.
    """
    # Base cases: Variables and Symbolic Constants
    if depth == 0:
        for var in available_vars:
            yield Var(var)
        # Yield a symbolic constant for Z3 to solve
        yield Int(z3.Int('c'))
        return

    # Recursive cases
    # 1. Binary Operations
    for left in generate_ast(depth - 1, available_vars):
        for right in generate_ast(depth - 1, available_vars):
            yield BinOp(left, "+", right)

    # 2. Variable Binding (Shadowing)
    # We introduce a new variable 'x' to see if it shadows improperly
    for val in generate_ast(depth - 1, available_vars):
        for body in generate_ast(depth - 1, available_vars + ['x']):
            yield Let('x', val, body)

    # 3. Higher Order Functions (Returning a closure)
    # Generates a lambda that captures the current environment
    for body in generate_ast(depth - 1, available_vars + ['y']):
        yield Lambda(['y'], body)

    # 4. Function Application
    # We apply a generated function to a generated argument
    for func in generate_ast(depth - 1, available_vars):
        for arg in generate_ast(depth - 1, available_vars):
            yield Apply(func, [arg])


def synthesize_diverging_program():
    """
    Searches for an AST where Static and Dynamic scoping yield different results.
    We wrap the generated AST in a top-level function that takes arguments.
    """
    solver = z3.Solver()
    
    # We want to synthesize the body of a top-level function f(a, b)
    top_level_params = ['a', 'b']
    
    # Iterate through increasing depths (Iterative Deepening)
    for depth in range(1, 4):
        print(f"Searching tree depth {depth}...")
        
        for generated_body in generate_ast(depth, top_level_params):
            # Construct the top-level program: (lambda (a b) <generated_body>)
            program = Lambda(top_level_params, generated_body)
            
            # Create symbolic inputs for the top-level arguments
            arg_a = Int(z3.Int('input_a'))
            arg_b = Int(z3.Int('input_b'))
            
            # Apply the program to the symbolic arguments
            top_level_call = Apply(program, [arg_a, arg_b])
            
            try:
                # Execute symbolically
                static_val = StaticScopeExecutor().execute(top_level_call)
                dyn_val = DynamicScopeExecutor().execute(top_level_call)
                
                # If they evaluate to the exact same Z3 expression structurally, skip solver
                if str(static_val) == str(dyn_val):
                    continue
                
                # Ask Z3: Is there ANY input where static != dynamic?
                solver.push()
                solver.add(static_val != dyn_val)
                
                if solver.check() == z3.sat:
                    model = solver.model()
                    print("\n--- DIVERGENCE FOUND! ---")
                    print("Synthesized Function Body AST structure found.")
                    # In a full implementation, you would write an AST pretty-printer here
                    print(f"Static Expression: {static_val}")
                    print(f"Dynamic Expression: {dyn_val}")
                    print(f"Counter-example inputs: a={model[z3.Int('input_a')]}, b={model[z3.Int('input_b')]}")
                    return
                
                solver.pop()
                
            except (TypeError, NameError):
                # Discard ill-typed ASTs (e.g., trying to Apply a BinOp instead of a Lambda)
                continue

    print("No diverging program found within depth limit.")

if __name__ == "__main__":
    synthesize_diverging_program()
