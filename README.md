# 1710 Final

## Goal
Our high-level goal from the project proposal has stayed the same: 
> We hope to learn more precise and potentially complex examples of programs that behave differently with static and dynamic scope. 

We also came up with the lower-level goal of better understanding how CEGIS works by implementing it. 

## Modeling Choices

### Essential Bucket
- Modeling a program: we created an AST that can represent a small toy language (a subset of SMoL used in CSCI 1730)
  - Core features: number literals, `let`, `lambda`
- Modeling the execution of a program with static and dynamic scope: we wrote two symbolic execution engines, one that uses static scope and one that uses dynamic scope
- Automatically generating syntactically and semantically correct programs: we did CEGIS!
  - This became essential once we saw that writing two symbolic execution engines is fairly simple (at least for the language we're using)

### Not Critical Bucket
- BinOps: these allow us to have programs that do things! But in theory we could do without them, but the only behavior difference we would find is dynamic would return a value when static gives an undefined error. 
- Conditionals: same as binops

### Abstracted Away Bucket
- Concrete syntax (when generating and executing programs)
- Multiple types (we only have `Int`--one could imagine adding strings or booleans but these don't fundamentally change how scope behaves)
- Data structures 

## Model Behavior
Run our model with `python cegis.py`. 
You will need to have Python, z3, Racket, and the [smol language](https://github.com/shriram/smol) installed. 

Essentially we use the two models of static and dynamic scope with CEGIS to generate an AST that produces different results when run with the two symbolic execution engines. 
We pretty-print the output in syntax that matches the `smol` syntax and run it with `#lang smol/hof` for static scope and `#lang smol/dyn-scope-is-bad` to compare the output when the program is _actually_ interpreted. 
So the output is the program in `smol` syntax, the symbolic expressions that differ as well as the values that make them different, and the real output of the program with the different scopes. 

## What We Learned
We had hoped to be able to generate more novel divergences in behavior. 
Unfortunately, due to how small our language has to be, we did not learn any new ways in which dynamic and static scope could have different behavior. 
We did gain experience writing and optimizing CEGIS programs--we learned that randomness and parallelism are necessary in order to make it somewhat performant. 

## AI 
We used an LLM to write a lot of the code for this assignment, partially to see how well it would do and partially because we felt that we already mostly knew how to write a symbolic execution engine and interpreter from SMT2 and two of us taking PL. 

## Collaboration
We only collaborated with each other. 
