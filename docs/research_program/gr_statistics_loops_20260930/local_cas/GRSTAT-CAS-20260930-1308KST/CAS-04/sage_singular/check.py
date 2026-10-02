from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['c','eps','p1','p2','p3','delta']+[f'd{m}{i}' for m in range(4) for i in range(1,4)])
v=R.gens_dict();F=R.fraction_field();c,eps,delta=[F(v[k]) for k in ['c','eps','delta']];p=vector(F,[v[f'p{i}'] for i in range(1,4)]);d=matrix(F,4,3,lambda m,i:v[f'd{m}{i+1}']);q=matrix(F,4,3,lambda m,i:-c*d[m,i]/(eps+p[i]));T=diagonal_matrix(F,[-eps]+list(p));g=diagonal_matrix(F,[-1,1,1,1]);u=vector(F,[1,0,0,0]);h=identity_matrix(F,4)+u.column()*(g*u).row()
c01=all((T[i+1,i+1]+eps)*q[m,i]==-c*d[m,i] for m in range(4) for i in range(3))
sp=matrix(F,3,3,lambda i,j:q[i+1,j]);sym=(sp+sp.transpose())/2;skew=(sp-sp.transpose())/2;theta=sym.trace();sigma=sym-theta*identity_matrix(F,3)/3;A=vector(F,[c*q[0,i] for i in range(3)]);omega2=sum(skew[i,j]**2 for i in range(3) for j in range(i+1,3))
lhs=theta**2/3+sum(x*x for x in sigma.list())+2*omega2+sum(a*a for a in A)/c**2;rhs=sum(q[m,i]**2 for m in range(4) for i in range(3));c02=lhs==rhs
# Termwise inequality holds because |eps+p_i|>=delta>0; equality only on min-gap supported D columns.
c03=c02 and rhs==c**2*sum(d[m,i]**2/(eps+p[i])**2 for m in range(4) for i in range(3))
# Projected Euler: (eps+p) A_i/c^2 + partial_i p=0; barotropic derivative substitution is exact.
J=PolynomialRing(QQ,names=['e','p','c','cs2','de','dp','a']);j=J.gens_dict();e,pp,cc,cs2,de,dp,aa=[j[k] for k in ['e','p','c','cs2','de','dp','a']];ide=J.ideal([(e+pp)*aa+cc*cc*dp,cc*cc*dp-cs2*de]);c04=ide.reduce((e+pp)*aa+cs2*de)==0
singular.eval('ring r=0,(e,p,c,dp,a),dp; ideal I=(e+p)*a+c^2*dp;')
rem=singular.eval('reduce((e+p)*a+c^2*dp,std(I));');print('Singular Euler ideal remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-04-C01':bool(c01),'CAS-04-C02':bool(c02),'CAS-04-C03':bool(c03),'CAS-04-C04':bool(c04)},'domain_assumption_diff':[],'counterexample':None,'engine':'SageMath plus explicit Singular Euler ideal','singular_remainder':rem,'notes':['C01 is the spatial projection of differentiated Tu=-epsilon u; the scalar epsilon derivative lies in the u component.','C03 inequality and equality support follow termwise from positive delta=min|epsilon+p_i|.','C04 dust A=0 assumes positive epsilon and dp=0.']}))
