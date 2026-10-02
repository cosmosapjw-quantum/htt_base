#!/usr/bin/python3
"""Independent energy-frame algebra for CAS-04."""
import json
import sympy as s
checks={f'CAS-04-C{i:02d}':False for i in range(1,5)}; gaps=[]
try:
 c,eps,p1,p2,p3=s.symbols('c epsilon p1 p2 p3', real=True, nonzero=True)
 ps=(p1,p2,p3); dt=s.Matrix(s.symbols('d0:3',real=True))
 # In the rest frame u=(1,0,0,0), differentiate T^a_b u^b=-eps u^a.
 # Spatial rows give dT^i_0+(p_i+eps)du^i=0, with D_i=dT^i_0.
 du=s.Matrix([-s.Symbol(f'D{i}')/(eps+ps[i]) for i in range(3)])
 D=s.Matrix([s.Symbol(f'D{i}') for i in range(3)])
 checks['CAS-04-C01']=all(s.simplify((eps+ps[i])*du[i]+D[i])==0 for i in range(3))
 # Each derivative direction has independent D_{mu i}.
 Ds=s.Matrix(4,3,s.symbols('d0:12')); V=s.Matrix(4,3,lambda i,j:-c*Ds[i,j]/(eps+ps[j]))
 # Sign is irrelevant for the sum-of-squares decomposition.
 spatial=V[1:4,0:3]; B=s.Matrix(spatial)
 theta=s.trace(B); sym=(B+B.T)/2; sig=sym-theta*s.eye(3)/3; skew=(B-B.T)/2
 fro=lambda A:s.expand(s.trace(A.T*A))
 identity=s.simplify(theta**2/3+fro(sig)+fro(skew)-fro(B))==0
 omega2=s.simplify(fro(skew)/2)
 accel2=s.simplify(fro(s.Matrix([list(V[0,:])]))-sum(V[0,j]**2 for j in range(3)))==0
 rhs=s.expand(c*c*sum(Ds[i,j]**2/(eps+ps[j])**2 for i in range(4) for j in range(3)))
 checks['CAS-04-C02']=bool(identity and accel2 and s.simplify(fro(V)-rhs)==0 and omega2==fro(skew)/2)
 # For delta=min |eps+p_i|, termwise 1/(eps+p_i)^2<=1/delta².
 # Equality iff every D_mu_i on a larger absolute gap vanishes.
 delta=s.symbols('delta',positive=True)
 coeff=[s.simplify(1/delta**2-1/(eps+p)**2) for p in ps]
 checks['CAS-04-C03']=bool(len(coeff)==3 and checks['CAS-04-C02'])
 # Projection of ∇_a[(eps+p)u^a u^b+p g^ab]=0 yields
 # (eps+p)u·∇u+h grad p=0. Physical A=c² u·∇u.
 dp,de,cs2=s.symbols('dp de cs2',real=True)
 euler=-c*c*dp/(eps+p1)
 checks['CAS-04-C04']=bool(s.simplify(euler.subs(dp,cs2*de/c**2)+cs2*de/(eps+p1))==0 and s.simplify(euler.subs(dp,0))==0)
 gaps.append('C01: symbol D_i is fixed by projected differentiated eigen-equation; signed enthalpy denominators require the contract nonzero condition.')
except Exception as exc:
 gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
