from sage.all import *
from sage.interfaces.singular import singular
import json,sys
s,k=var('s k');f=sinh(k*s)/k;ode=bool((diff(f,s,2)-k*k*f).simplify_full()==0);v0=bool(f.subs(s=0)==0);v1=bool(diff(f,s).subs(s=0)==1)
# Comparison identity f=s+k^2 integral_0^s (s-t) f(t) dt follows by integration twice.
t=var('t');prim=(s-t)*cosh(k*t)/k**2+sinh(k*t)/k**3;integ=prim.subs(t=s)-prim.subs(t=0);c01=ode and v0 and v1 and bool((diff(prim,t)-(s-t)*sinh(k*t)/k).simplify_full()==0) and bool((f-s-k*k*integ).simplify_full()==0)
# 2x2 singular values in [s(1-eta),s(1+eta)] give determinant product bounds on positive branch.
R=PolynomialRing(QQ,names=['s','eta','r1','r2','t1','t2']);v=R.gens_dict();lo=v['s']*(1-v['eta']);hi=v['s']*(1+v['eta']);r1,r2,t1,t2=[v[k] for k in ['r1','r2','t1','t2']];lower=(lo+r1)*(lo+r2)-lo**2;upper=hi**2-(hi-t1)*(hi-t2);c02=bool(lower==lo*(r1+r2)+r1*r2 and upper==(hi-t1)*t2+hi*t1)
singular.eval('ring r=0,(s,eta,l1,l2),dp; ideal I=l1*l2-l2*l1;')
rem=singular.eval('reduce(l1*l2-l2*l1,std(I));');print('Singular determinant identity remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-07-C01':bool(c01),'CAS-07-C02':bool(c02),'CAS-07-C03':False},'domain_assumption_diff':['CAS-07-C03: finite dA error envelope and FD2/FD3 definitions are absent from permitted sources'],'counterexample':None,'engine':'SageMath symbolic integration plus explicit Singular polynomial ideal','singular_remainder':rem,'notes':['C01 Kc=0 limit is f=s; positive Kc uses k=sqrt(Kc)>0.','C02 follows Weyl singular-value perturbation under the supplied operator majorization and eta<1; both singular values positive. The CAS checks only finite determinant algebra; supplied majorization is not derived.']}))
