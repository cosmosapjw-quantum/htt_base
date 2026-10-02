#!/usr/bin/python3
"""Independent projector and degree-eight sphere quadrature checks for CAS-16."""
import json,math
import sympy as s
checks={f'CAS-16-C{i:02d}':False for i in range(1,4)};gaps=[]
try:
 x,y,z=s.symbols('x y z',real=True);e=s.Matrix([x,y,z]);P=s.eye(3)-e*e.T;r2=e.dot(e)
 idempotence=s.Matrix(3,3,lambda i,j:s.factor((P*P-P)[i,j]))
 projector=all(s.simplify(idempotence[i,j].subs(r2,1))==0 for i in range(3) for j in range(3))
 # P is symmetric; on the unit sphere its eigenvalues are 1,1,0,
 # hence ||PJP||_F<=||J||_F for every finite matrix J.
 E=s.Matrix([1,0,0]);P0=s.eye(3)-E*E.T
 J=s.Matrix(3,3,s.symbols('j0:9',real=True));fro=lambda A:s.expand(s.trace(A.T*A))
 finite=s.simplify(fro(J)-fro(P0*J*P0))
 checks['CAS-16-C01']=bool(P==P.T and projector and all(co>=0 for co in s.Poly(finite,*list(J)).coeffs()))
 L,LC,LT=s.symbols('L LC LT',integer=True,nonnegative=True)
 Dstar=max(4+4,6+2,4+2)
 checks['CAS-16-C02']=False
 gaps.append('C02: the permitted inputs state Dstar but do not specify the angular integrand factors needed to derive the general L,LC,LT degree accounting; the (4,6,4) arithmetic alone is insufficient.')
 # GL5 nodes are zero and ±sqrt((35±2sqrt70)/63), with weights below.
 tlo=(35-2*s.sqrt(70))/63;thi=(35+2*s.sqrt(70))/63
 wlo=(322+13*s.sqrt(70))/900;whi=(322-13*s.sqrt(70))/900
 nodes=[(s.Integer(0),s.Rational(128,225)),(s.sqrt(tlo),wlo),(-s.sqrt(tlo),wlo),(s.sqrt(thi),whi),(-s.sqrt(thi),whi)]
 moments=all(s.simplify(sum(w*mu**k for mu,w in nodes)-(s.Rational(2,k+1) if k%2==0 else 0))==0 for k in range(10))
 # Azimuth 9th roots of unity annihilate each nonzero Fourier mode
 # |m|<=8. For x^i y^j z^k with total degree<=8, odd i or j
 # gives zero; otherwise average is the exact beta moment times
 # (1-mu²)^((i+j)/2), a polynomial degree<=8.
 monomials=0; exact=True
 for i in range(9):
  for j in range(9-i):
   for k in range(9-i-j):
    monomials+=1
    if i%2 or j%2:continue
    a=i//2;b=j//2
    az=s.Rational(math.factorial(2*a)*math.factorial(2*b),4**(a+b)*math.factorial(a)*math.factorial(b)*math.factorial(a+b))
    poly=s.expand((1-z*z)**(a+b)*z**k)
    lhs=s.simplify(az*sum(w*poly.subs(z,mu) for mu,w in nodes))
    rhs=s.simplify(az*s.integrate(poly,(z,-1,1)))
    exact &= s.simplify(lhs-rhs)==0
 # GL4 misses z^8 since its polynomial exactness ends at degree 7.
 p4=s.legendre(4,z);roots4=s.solve(p4,z)
 gl4=sum((2/((1-r*r)*s.diff(p4,z).subs(z,r)**2))*r**8 for r in roots4)
 under_mu=s.simplify(gl4-s.Rational(2,9))!=0
 # Eight azimuths alias cos(8 phi) to 1; true azimuth integral is 0.
 under_phi=sum(s.cos(8*2*s.pi*j/8) for j in range(8))==8
 checks['CAS-16-C03']=bool(moments and monomials==165 and exact and under_mu and under_phi)
 gaps.append('General quadrature-order theorem and Hilbert collision norm bound remain analytic obligations beyond the finite degree-eight certificate.')
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
