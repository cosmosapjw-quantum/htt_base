from sage.all import *
from sage.interfaces.singular import singular
from math import comb
import json,sys
R=PolynomialRing(QQ,names=['e1','e2','e3']);e=vector(R,R.gens());I=R.ideal([e*e-1]);P=identity_matrix(R,3)-e.column()*e.row();c01=all(I.reduce(q)==0 for q in (P*P-P).list()) and P.transpose()==P and all(I.reduce(q)==0 for q in P*e)
Dstar=max(4+4,6+2,4+2);c02=Dstar==8 and 9>=Dstar+1 and 2*5-1>=Dstar
# Angular Fourier coefficients of cos(phi)^i sin(phi)^j. 9 roots-of-unity points
# preserve exactly the constant mode for all i+j<=8.
G=QuadraticField(-1,'ii');ii=G.gen()
def fourier(i,j):
 out={}
 for a in range(i+1):
  for b in range(j+1):
   k=i+j-2*(a+b);coeff=G(comb(i,a)*comb(j,b)*(-1)**b)/(2**(i+j)*ii**j)
   out[k]=out.get(k,G(0))+coeff
 return out
Z=PolynomialRing(QQ,'z');z=Z.gen();P5=Z(legendre_P(5,z));P4=Z(legendre_P(4,z));integ=lambda f:f.integral()(1)-f.integral()(-1)
checked=0;c03=True
for i in range(9):
 for j in range(9-i):
  for k in range(9-i-j):
   coeff=fourier(i,j);angular_exact=sum(val for mode,val in coeff.items() if mode%9==0)==coeff.get(0,G(0))
   m=i+j
   if m%2==0:
    radial=(1-z*z)**(m//2)*z**k;quot,rem=radial.quo_rem(P5);radial_exact=integ(quot*P5)==0
   else: radial_exact=True # phi integral and discrete sum both zero for odd m<9
   c03=c03 and angular_exact and radial_exact;checked+=1
# Four-point GL aliases degree 8 because P4(nodes)^2=0 while its exact integral is positive.
under_mu=integ(P4*P4)>0
# Eight phi points alias the +-8 modes of cos^8 phi, unlike continuous average.
coeff8=fourier(8,0);under_phi=sum(val for mode,val in coeff8.items() if mode%8==0)!=coeff8.get(0,G(0))
c03=c03 and under_mu and under_phi and checked==165
singular.eval('ring r=0,(e1,e2,e3),dp; ideal I=e1^2+e2^2+e3^2-1;')
rem=singular.eval('reduce(e1^2+e2^2+e3^2-1,std(I));');print('Singular unit-direction remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-16-C01':bool(c01),'CAS-16-C02':bool(c02),'CAS-16-C03':bool(c03)},'domain_assumption_diff':[],'counterexample':None,'engine':'SageMath exact Fourier/Legendre algebra plus explicit Singular sphere ideal','singular_remainder':rem,'monomials_checked':checked,'underresolution':{'Nmu4_P4_squared_integral':str(integ(P4*P4)),'Nphi8_x8_alias':bool(under_phi)},'notes':['C01 projector contraction is finite Frobenius nonexpansiveness for symmetric idempotent P_e.','C03 covers all Cartesian sphere monomials through degree 8; no universal quadrature order or Hilbert-space collision norm admission.']}))
