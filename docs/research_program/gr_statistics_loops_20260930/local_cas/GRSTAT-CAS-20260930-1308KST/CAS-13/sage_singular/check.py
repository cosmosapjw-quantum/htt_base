from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['p','y']);v=R.gens_dict();p,y=v['p'],v['y'];q=(p-3)*(p-4)/12+p*(4-p)*y**3/3+p*(p-3)*y**4/4
c01=q(y=1)==1 and q.derivative(y)(y=1)==p and q.derivative(y,2)(y=1)==p*(p-1)
third=p*(p-1)*(p-2)-q.derivative(y,3)(y=1)
# Two-node formulas over exact rational function field and positive, distinct node denominators.
S=PolynomialRing(QQ,names=['a','b','u','d','m3','m4']);v=S.gens_dict();a,b,u,d,m3,m4=[v[k] for k in ['a','b','u','d','m3','m4']];F=S.fraction_field();wu=(m3-a**3)/(u**3-a**3);wb=(m3-d**3)/(b**3-d**3)
lo3=(1-wu)*a**3+wu*u**3;hi3=(1-wb)*d**3+wb*b**3;lo4=(1-wu)*a**4+wu*u**4;hi4=(1-wb)*d**4+wb*b**4
node_lo=(m4-a**4)*(u**3-a**3)-(m3-a**3)*(u**4-a**4);node_hi=(b**4-m4)*(b**3-d**3)-(b**3-m3)*(b**4-d**4)
c02=lo3==m3 and hi3==m3 and (lo4-m4)==-node_lo/(u**3-a**3) and (hi4-m4)==node_hi/(b**3-d**3)
# Boundary branches are defined as measures, never by coincident-node quotients.
we=(m3-a**3)/(b**3-a**3);end3=(1-we)*a**3+we*b**3;end4=(1-we)*a**4+we*b**4
c02=c02 and end3==m3 and end4==a**4+(m3-a**3)*(b**4-a**4)/(b**3-a**3)
# Differentiate both node ratio functions and compare with the manifest positive form.
Dlo=(u**4-a**4)/(u**3-a**3);Dhi=(b**4-d**4)/(b**3-d**3);dlo=Dlo.derivative(u);dhi=Dhi.derivative(d)
c02=c02 and dlo==u**2*(3*a*a+2*a*u+u*u)/(a*a+a*u+u*u)**2 and dhi==d**2*(3*b*b+2*b*d+d*d)/(b*b+b*d+d*d)**2
# Hermite systems independently solved over Q(a,u), then exact polynomial factor certificates.
T=PolynomialRing(QQ,names=['a','u']);aa,uu=T.gens();K=T.fraction_field();Y=PolynomialRing(K,'y');yy=Y.gen();delta=3*aa**2+2*aa*uu+uu**2;mat=matrix(K,[[1,aa**3,aa**4],[1,uu**3,uu**4],[0,3*uu**2,4*uu**3]])
residuals={};c03=True
for power in (5,6):
 rhs=vector(K,[aa**power,uu**power,power*uu**(power-1)]);coef=mat.solve_right(rhs);Q=Y(coef[0]+coef[1]*yy**3+coef[2]*yy**4);res=yy**power-Q
 if power==5: P=delta*yy**2+(2*aa**2*uu+aa*uu**2)*yy+aa**2*uu**2
 else: P=delta*yy**3+(3*aa**3+8*aa**2*uu+5*aa*uu**2+2*uu**3)*yy**2+(2*aa**3*uu+5*aa**2*uu**2+2*aa*uu**3)*yy+aa**3*uu**2+2*aa**2*uu**3
 ok=res==(yy-aa)*(yy-uu)**2*P/delta and Q(aa)==aa**power and Q(uu)==uu**power and Q.derivative()(uu)==power*uu**(power-1)
 c03=c03 and ok; residuals[str(power)]={'coefficients':[str(x) for x in coef],'factor_certificate':bool(ok)}
# Lower y-a>=0, upper y-b<=0, remaining factors positive for positive a,b,u,d,y.
# Boundary node coincidence is handled by limiting Dirac measures, never 0/0 evaluation.
L,U=var('L U');pred=2*L*U/(L+U);risk=(U-L)/(U+L);c04=bool(((pred-L)/L-risk).simplify_full()==0 and ((U-pred)/U-risk).simplify_full()==0)
singular.eval('ring r=0,(a,u,y),dp; ideal I=(y-a)*(y-u)^2;')
rem=singular.eval('reduce((y-a)*(y-u)^2,std(I));');print('Singular Hermite-contact ideal remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-13-C01':bool(c01),'CAS-13-C02':bool(c02),'CAS-13-C03':bool(c03),'CAS-13-C04':bool(c04)},'domain_assumption_diff':[],'counterexample':None,'engine':'SageMath rational interpolation plus explicit Singular contact ideal','singular_remainder':rem,'third_derivative_gap':str(third),'hermite':residuals,'notes':['C02 node existence/uniqueness uses the verified strictly positive ratio derivatives and strict interior feasibility; endpoint/Dirac branches use limits.','C03 signed certificates prove p=5,6 only; general real p>4 principal-representation theorem remains an analytic obligation.','C04 requires 0<L<=U and relative error loss; integrated bandpass Taylor and fixed-prior frame comparisons remain outside this component.']}))
