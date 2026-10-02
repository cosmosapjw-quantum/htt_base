#!/usr/bin/python3
"""Independent SymPy checks for the fixed scalar component of CAS-06."""
import json
import sympy as s
checks={f'CAS-06-C{i:02d}':False for i in range(1,5)}
gaps=[]
try:
 r,t,th,ph=s.symbols('r t theta phi',real=True)
 alpha,eps0,kappa,mu,Lam,q,Ps=s.symbols('alpha epsilon0 kappa mu Lambda q Pstar',positive=True)
 nu=s.Function('nu')(r); m=s.Function('m')(r)
 F=1-2*m/r-Lam*r*r/3
 # Static scalar psi=q t, g00=-exp(2nu); X=q² exp(-2nu)/2.
 X=q*q*s.exp(-2*nu)/2
 exponent=(1+alpha)/(2*alpha)
 P=Ps*X**exponent
 PX=s.diff(P,X) if not X.has(r) else exponent*P/X
 energy=s.simplify(2*X*PX-P)
 ratio=s.simplify(PX/(PX+2*X*(exponent*(exponent-1)*P/X**2)))
 # J^a=P_X g^ab psi_b; only t component, all fields independent of t.
 Jt=-PX*q*s.exp(-2*nu)
 current_div=s.diff(Jt,t)
 stress=s.simplify(energy-(2*exponent-1)*P)==0
 checks['CAS-06-C03']=bool(stress and s.simplify(ratio-alpha)==0 and current_div==0)
 gaps.extend([
  'C01: complete Christoffel/Riemann/Einstein reduction with TOV differential substitutions was not established by this finite scalar check.',
  'C02: full matched-event tetrad curvature, Weyl derivative, and rate claims were not established.',
  'C04: the exact algebraic divergence expression in y is not displayed in permitted inputs; cannot certify its claimed branch.'
 ])
except Exception as exc:
 gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
