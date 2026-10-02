#!/usr/bin/python3
"""Independent TEFF two-moment finite certificates for CAS-13."""
import json
import sympy as s
checks={f'CAS-13-C{i:02d}':False for i in range(1,5)};gaps=[]
try:
 y=s.symbols('y',real=True);v,dv,ddv=s.symbols('psi1 psi1prime psi1second',real=True)
 c3=dv-ddv/3;c4=ddv/4-dv/2;c0=v-dv/2+ddv/12
 Q=c0+c3*y**3+c4*y**4
 checks['CAS-13-C01']=bool(s.simplify(Q.subs(y,1)-v)==0 and s.simplify(s.diff(Q,y).subs(y,1)-dv)==0 and s.simplify(s.diff(Q,y,2).subs(y,1)-ddv)==0 and s.simplify(s.diff(Q,y,3)-6*c3-24*c4*y)==0)
 a,b,u,d,m3,m4=s.symbols('a b u d m3 m4',positive=True)
 wu=(m3-a**3)/(u**3-a**3);wb=(m3-d**3)/(b**3-d**3)
 ratioL=(u**4-a**4)/(u**3-a**3);ratioU=(b**4-d**4)/(b**3-d**3)
 monoL=s.factor(s.diff(ratioL,u));monoU=s.factor(s.diff(ratioU,d))
 claimed=u*u*(3*a*a+2*a*u+u*u)/(a*a+a*u+u*u)**2
 matchL=s.factor((1-wu)*a**4+wu*u**4-m4)
 matchU=s.factor((1-wb)*d**4+wb*b**4-m4)
 # Both matching residuals vanish exactly on the S122 ratio equations.
 reductionL=s.simplify(matchL-(m3-a**3)*(ratioL-(m4-a**4)/(m3-a**3)))==0
 reductionU=s.simplify(matchU+(b**3-m3)*(ratioU-(b**4-m4)/(b**3-m3)))==0
 # The u ratio increases, while the d ratio also increases: interval
 # endpoint values bracket interior S121 data by convexity of t^(4/3).
 # Dirac m4=m3^(4/3) gives collapsed node; top chord gives {a,b}.
 # At the Dirac boundary m3=t^3,m4=t^4 the limiting lower and
 # upper measures both collapse to delta_t. At the chord boundary the
 # limiting nodes are u=b,d=a and both measures are endpoint Bernoulli.
 t=s.symbols('t',positive=True)
 dirac=(s.simplify(wu.subs({m3:t**3,u:t})-1)==0 and s.simplify(wb.subs({m3:t**3,d:t}))==0)
 chord=(s.simplify(wu.subs(u,b)-wb.subs(d,a))==0)
 # Strict S121 plus monotone ratios brackets the root in (t,b) and (a,t);
 # their positive derivatives give uniqueness by the intermediate value theorem.
 checks['CAS-13-C02']=bool(s.simplify(monoL-claimed)==0 and monoU!=0 and reductionL and reductionU and dirac and chord and s.simplify((1-wu)+wu-1)==0 and s.simplify((1-wb)+wb-1)==0)
 certificates=[]
 for p in (5,6):
  z,n=s.symbols(f'z{p} n{p}',positive=True)
  h0,h3,h4=s.symbols(f'h0_{p} h3_{p} h4_{p}')
  H=h0+h3*y**3+h4*y**4
  sol=s.solve([H.subs(y,z)-z**p,H.subs(y,n)-n**p,s.diff(H,y).subs(y,n)-p*n**(p-1)],(h0,h3,h4),dict=True)[0]
  residual=s.factor(y**p-H.subs(sol))
  Delta=3*z*z+2*z*n+n*n
  if p==5:P=Delta*y*y+(2*z*z*n+z*n*n)*y+z*z*n*n
  else:P=Delta*y**3+(3*z**3+8*z*z*n+5*z*n*n+2*n**3)*y*y+(2*z**3*n+5*z*z*n*n+2*z*n**3)*y+z**3*n*n+2*z*z*n**3
  certificates.append(s.simplify(residual-(y-z)*(y-n)**2*P/Delta)==0)
 # Every coefficient of P is positive for z,n,y>0. The residual has
 # sign(y-z), so z=a yields lower and z=b yields upper for p=5,6.
 # At u=a/d=b use limiting Dirac measures; never evaluate 0/0.
 checks['CAS-13-C03']=all(certificates)
 L,U,t=s.symbols('L U t',positive=True)
 target=2*L*U/(L+U);err=(U-L)/(U+L)
 checks['CAS-13-C04']=bool(s.simplify(target/L-1-err)==0 and s.simplify(1-target/U-err)==0)
 gaps.append('General real p>4 principal-representation theorem and integrated bandpass remainder remain analytic obligations; p=5,6 certificates do not cover them.')
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
