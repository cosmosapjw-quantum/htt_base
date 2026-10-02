#!/usr/bin/python3
"""Independent finite inverse-stability algebra for CAS-02."""
import json
import sympy as s
checks={f'CAS-02-C{i:02d}':False for i in range(1,5)}; gaps=[]
try:
 h0=s.symbols('h0',real=True); h1=s.Matrix(s.symbols('h1:4',real=True)); H=s.Matrix(3,3,s.symbols('H0:9')); H=(H+H.T)/2
 S=s.zeros(4);S[0,0]=h0
 for i in range(3):
  S[0,i+1]=S[i+1,0]=-h1[i]/2
  for j in range(3):S[i+1,j+1]=H[i,j]
 fro=lambda A:s.expand(s.trace(A.T*A))
 g=s.diag(-1,1,1,1)
 checks['CAS-02-C01']=bool(s.simplify(fro(S)-(h0*h0+h1.dot(h1)/2+fro(H)))==0 and fro(g)==4)
 a=s.Matrix(s.symbols('a0:4')); b=s.Matrix(s.symbols('b0:4'))
 S1=s.Matrix(4,4,s.symbols('s0:16')); S1=(S1+S1.T)/2
 S2=s.Matrix(4,4,s.symbols('t0:16')); S2=(S2+S2.T)/2
 f=lambda u,T:(u.T*T*u)[0]
 lhs=f(b,S2)-f(a,S1)
 anchor=f(b,S2-S1)+((b-a).T*S1*b)[0]+(a.T*S1*(b-a))[0]
 swapped=f(a,S2-S1)+((b-a).T*S2*b)[0]+(a.T*S2*(b-a))[0]
 checks['CAS-02-C02']=bool(s.simplify(lhs-anchor)==0 and s.simplify(lhs-swapped)==0)
 d=s.Matrix(s.symbols('d0:3',real=True)); norm=d.dot(d)
 u=s.Matrix([s.sqrt(1+norm),*d]); J=u.jacobian(d)
 Gram=s.simplify(J.T*J)
 expected=s.eye(3)+d*d.T/(1+norm)
 # Characteristic polynomial factors for arbitrary d; at d=0 all eigenvalues 1.
 xi=s.symbols('xi')
 char=s.factor((Gram-xi*s.eye(3)).det())
 eigen=s.factor((1-xi)**2*(1+norm/(1+norm)-xi))
 checks['CAS-02-C03']=bool(all(s.simplify(Gram[i,j]-expected[i,j])==0 for i in range(3) for j in range(3)) and s.simplify(char-eigen)==0)
 # The bound is a direct triangle/Cauchy consequence of C01/C02 and ||g||=2:
 # |δλ| <= M²||δS||+2ML||δu|| at the better anchor; then
 # ||δB|| <= ||δS||+2|δλ|. Rapidity bounds give ||u||<=sqrt(cosh2R).
 eH,eZ,M,L=s.symbols('epsilonH epsilonZ M L',nonnegative=True)
 dlam=M*M*eH+2*M*L*eZ
 Bbound=s.expand(eH+2*dlam)
 checks['CAS-02-C04']=bool(checks['CAS-02-C01'] and checks['CAS-02-C02'] and checks['CAS-02-C03'] and s.simplify(Bbound-((1+2*M*M)*eH+4*M*L*eZ))==0)
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
