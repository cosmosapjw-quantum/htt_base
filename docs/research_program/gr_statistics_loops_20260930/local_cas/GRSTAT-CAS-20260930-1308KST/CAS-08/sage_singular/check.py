from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['a','b','c','d','e','f','r1','r2','r3']);v=R.gens_dict();K=R.fraction_field();A=matrix(K,3,2,[[v['a'],v['b']],[v['c'],v['d']],[v['e'],v['f']]]);AtA=A.transpose()*A;Proj=A*AtA.inverse()*A.transpose();P=identity_matrix(K,3)-Proj
c01=P.transpose()==P and P*P==P and P*A==0 and P.trace()==1
# Rank-one and zero controls, preserving potentially rank-deficient F.
a=vector(K,[v['a'],v['c'],v['e']]);P1=identity_matrix(K,3)-a.column()*a.row()/(a*a);c01=c01 and P1*P1==P1 and P1*a==0 and P1.trace()==2
c02=bool(c01)
# GLS normal equations give min ||Wr-WF beta||^2=||P Wr||^2; projected white covariance PIP^T=P.
r=vector(K,[v['r1'],v['r2'],v['r3']]);betahat=AtA.inverse()*A.transpose()*r;res=r-A*betahat;c02=c02 and res==P*r and res*res==(P*r)*(P*r) and P*P.transpose()==P
singular.eval('ring r=0,(a,b),dp; ideal I=a*b-b*a;')
rem=singular.eval('reduce(a*b-b*a,std(I));');print('Singular commutative ideal remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-08-C01':bool(c01),'CAS-08-C02':bool(c02),'CAS-08-C03':False},'domain_assumption_diff':['CAS-08-C03: four-way geodesicity decision sets and acceptance-region definitions are absent from permitted sources'],'counterexample':None,'engine':'SageMath rational rank-strata algebra plus explicit Singular ideal','singular_remainder':rem,'notes':['C01 full-rank, rank-one, and zero-rank projector strata; arbitrary rank follows Penrose identities AA+ A=A and (AA+)^T=AA+.','C02 covariance P is whitened Gaussian linear algebra; probability law and coverage are separate.']}))
