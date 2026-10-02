#!/usr/bin/python3
"""Independent finite Bregman and residual-Gram checks for CAS-11."""
import json
import sympy as s
checks={f'CAS-11-C{i:02d}':False for i in range(1,4)};gaps=[]
try:
 F,G,H,pG,pH=s.symbols('F G H pG pH',real=True); f,g,h=s.symbols('f g h',real=True)
 Dfg=F-G-pG*(f-g);Dgh=G-H-pH*(g-h);Dfh=F-H-pH*(f-h)
 checks['CAS-11-C01']=s.expand(Dfh-Dfg-Dgh-(pG-pH)*(f-g))==0
 # For weighted inner product, residual projector Q=I-V(V^T W V)^+V^T W.
 W=s.diag(2,3,5);V=s.Matrix([[1],[1],[1]]);K=s.Matrix([[1,0],[0,1],[1,1]])
 Q=s.eye(3)-V*(V.T*W*V).inv()*V.T*W
 r=Q*K; R=s.simplify(r.T*W*r)
 checks['CAS-11-C02']=bool(R==R.T and R.det()>=0 and R[0,0]>=0 and R[1,1]>=0 and Q*V==s.zeros(3,1))
 # Universal finite proof: R=B^T B; |a.e|²<=2ε||Ba||² all a
 # implies e annihilates ker B, hence e in range R. On range R,
 # maximize ratio by a=R+e: e^T R+ e<=2ε. Conversely Cauchy
 # gives the all-a bound. This covers R=0 because e must then be 0.
 e=s.Matrix(s.symbols('e0:2',real=True)); a=s.Matrix(s.symbols('a0:2',real=True))
 positive=s.simplify((a.T*R*a)[0]-(r*a).dot(W*r*a))==0
 # Check singular and zero examples against pseudoinverse:
 Z=s.zeros(2);Rs=s.Matrix([[2,2],[2,2]]);es=s.Matrix([1,1]);null=s.Matrix([1,-1])
 singular=(Rs*Rs.pinv()*es==es and Rs*null==s.zeros(2,1) and (es.T*Rs.pinv()*es)[0]==s.Rational(1,2) and Z.pinv()==Z)
 checks['CAS-11-C02']=bool(checks['CAS-11-C02'] and positive and singular)
 checks['CAS-11-C03']=bool(Q*Q==Q and s.simplify((r.T*W*V)[0])==0 and s.simplify((r.T*W*V)[1])==0)
 gaps.append('Continuum Hessian-envelope/Taylor integral step remains an external analytic prerequisite.')
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
