import json
import sympy as sp
s,t=sp.symbols("s t", nonnegative=True, real=True)
flat_f=s
encoded_integral=sp.integrate(s-t,(t,0,s))
target_integral=sp.integrate((s-t)*flat_f.subs(s,t),(t,0,s))
encoded_residual=sp.Integer(0)*encoded_integral
target_residual=sp.simplify(sp.Integer(0)*target_integral-(flat_f-s))
print(json.dumps({"sympy":sp.__version__,"encoded_unscaled_integral":str(encoded_integral),"target_unscaled_integral":str(target_integral),"encoded_at_s_one":str(encoded_integral.subs(s,1)),"target_at_s_one":str(target_integral.subs(s,1)),"encoded_zero_branch_residual":str(encoded_residual),"target_zero_branch_residual":str(target_residual),"consequence":"The encoded unscaled integral differs; multiplication by zero conceals that coverage error. This is not a counterexample to C01."},sort_keys=True))
