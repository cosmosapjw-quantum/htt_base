#!/usr/bin/python3
"""Independent finite design-rank and alias checks for CAS-09."""
import json
import sympy as s
checks={f'CAS-09-C{i:02d}':False for i in range(1,5)};gaps=[]
try:
 rt=s.sqrt(2); dirs=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1/rt,1/rt,0),(1/rt,0,1/rt),(0,1/rt,1/rt)]
 def e4(v):x,y,z=v;return [1,x,y,z]
 def e9(v):x,y,z=v;return [1,x,y,z,x*x-y*y,x*x-z*z,x*y,x*z,y*z]
 E4=s.Matrix([e4(v) for v in dirs]);E9=s.Matrix([e9(v) for v in dirs])
 R1,R2,c=s.symbols('R1 R2 c',positive=True)
 repeated=[dirs[i] for i in (0,1,2,4)]
 V=s.Matrix([e4(v) for v in repeated])
 rows=dirs+repeated
 B=s.Matrix([e4(v)+[r/c*t for t in e9(v)] for v,r in zip(rows,[R1]*9+[R2]*4)])
 # Subtract the R1 block contribution from each repeat; nonzero R2-R1
 # leaves four independent E4 evaluations.
 rank13=E9.rank()==9 and V.rank()==4 and s.simplify(B.det())!=0
 # rank[A B]=rankA+rankB-dim(rangeA intersect rangeB)
 # follows from dim(A+B)=dimA+dimB-dim(A∩B).
 checks['CAS-09-C01']=bool(rank13)
 gaps.append('C02: permitted inputs state but do not define the future-mass-shell intercept chart or its 13-to-12 Jacobian; physical rank was not independently certified.')
 const=s.Matrix([e4(v)+[R1/c*t for t in e9(v)] for v in dirs])
 constant_rank=const.rank()==9
 eps=s.symbols('epsilon',real=True)
 # Multiply every row of [E4, R/(c(1+eps*z)) E9] by positive
 # (1+eps*z). Each transformed E4 polynomial has degree <=2 on S²,
 # and the E9 block retains rank nine.
 x,y,z=s.symbols('x y z',real=True)
 mon=[1,x,y,z,x*x-y*y,x*x-z*z,x*y,x*z,y*z]
 # Quotient sphere x²+y²+z²=1: z*x,z*y,z*z are in span E9.
 q=s.Matrix([1,x,y,z]); target=[s.expand((1+eps*z)*v) for v in q]
 relation=(s.expand(target[0]-(mon[0]+eps*mon[3]))==0 and s.expand(target[1]-(mon[1]+eps*mon[7]))==0 and s.expand(target[2]-(mon[2]+eps*mon[8]))==0 and s.reduced(target[3]-(mon[3]+eps*(1+mon[4]-2*mon[5])/3),[x*x+y*y+z*z-1],x,y,z)[1]==0)
 checks['CAS-09-C03']=bool(constant_rank and relation)
 Zi,Z0,H,r,c=s.symbols('Zi Z0 H r c',real=True,nonzero=True)
 rho=Zi-Z0-r*H/c
 checks['CAS-09-C04']=bool(s.simplify(Z0+r*H/c+rho-Zi)==0)
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
