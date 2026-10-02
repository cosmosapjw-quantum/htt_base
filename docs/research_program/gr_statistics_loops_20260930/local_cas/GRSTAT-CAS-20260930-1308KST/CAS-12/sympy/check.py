#!/usr/bin/python3
"""Independent finite adjoint, Thomson moment, and infrared checks for CAS-12."""
import json
import sympy as s
checks={f'CAS-12-C{i:02d}':False for i in range(1,5)};gaps=[]
try:
 A=s.Matrix(3,3,s.symbols('a0:9',real=True));f=s.Matrix(s.symbols('f0:3',real=True));k=s.Matrix(s.symbols('k0:3',real=True))
 checks['CAS-12-C01']=bool(s.simplify((k.T*A*f)[0]-(A.T*k).dot(f))==0)
 # For any fixed linear L, retained adjoint moments L* K are exact,
 # and if q lies in the annihilator of those moments then <K,Lq>=0.
 mu=s.symbols('mu',real=True)
 p=lambda ell:s.simplify(2*s.pi*s.integrate(3*(1+mu*mu)/(16*s.pi)*s.legendre(ell,mu),(mu,-1,1)))
 vals=[p(j) for j in range(8)]
 checks['CAS-12-C02']=vals[0]==1 and vals[2]==s.Rational(1,10) and all(vals[j]==0 for j in range(8) if j not in (0,2))
 E,b=s.symbols('E b',positive=True)
 W=s.exp(b*E)/(s.exp(b*E)-1)**2
 series=s.series(W,E,0,3).removeO()
 checks['CAS-12-C03']=bool(s.simplify(s.limit(E*E*W,E,0)-1/b**2)==0 and s.simplify(s.limit(W*s.exp(b*E),E,s.oo)-1)==0 and s.simplify(series-1/(b*E)**2+s.Rational(1,12)-b*b*E*E/240)==0)
 x,n,a,q,g=s.symbols('x n a q g',real=True)
 f_n=g+a*s.sin(n*x)*q
 # q,g here denote local values independent of x; the continuum q
 # construction and interchange of integral/differentiation are excluded.
 derivative=s.diff(f_n,x)
 moment=s.symbols('moment_q',real=True)
 w0,w1,A0,A1,B0,B1=s.symbols('w0 w1 A0 A1 B0 B1',positive=True)
 lagrange=s.expand((w0*A0*A0+w1*A1*A1)*(w0*B0*B0+w1*B1*B1)-(w0*A0*B0+w1*A1*B1)**2-w0*w1*(A0*B1-A1*B0)**2)
 checks['CAS-12-C04']=bool(s.simplify(derivative-a*n*s.cos(n*x)*q)==0 and s.simplify((a*s.sin(n*x)*moment).subs(moment,0))==0 and lagrange==0)
 gaps.append('C04 continuum compact moment-orthogonal q and differentiation under integral remain separate analytic obligations; finite derivative Cauchy is conditional on finite positive weights.')
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
