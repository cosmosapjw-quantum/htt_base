from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=[f'e{a}{i}' for a in range(4) for i in range(3)])
z=R.gens_dict();E=matrix(R,4,3,lambda a,i:z[f'e{a}{i}']);g=diagonal_matrix(R,[-1,1,1,1]);cov=g*E;v=vector(R,[(-1)**a*cov.delete_rows([a]).det() for a in range(4)]);Gram=E.transpose()*g*E
c01=all(v*g*E.column(i)==0 for i in range(3)) and v*g*v==-Gram.det()
# For timelike branch, N=v/sqrt(detGram), gamma=-u.N and beta^2=1-gamma^-2.
# Jacobian tensor transformation: g'=J^-T g J^-1, u'=J u, S'=J^-T S J^-1.
P=PolynomialRing(QQ,names=['j00','j01','j10','j11','u0','u1','s00','s01','s11']);p=P.gens_dict();K=P.fraction_field();J=matrix(K,2,2,[[p['j00'],p['j01']],[p['j10'],p['j11']]]);u=vector(K,[p['u0'],p['u1']]);S=matrix(K,2,2,[[p['s00'],p['s01']],[p['s01'],p['s11']]]);up=J*u;Sp=J.inverse().transpose()*S*J.inverse();c04=up*Sp*up==u*S*u
singular.eval('ring r=0,(a,b,c),dp; ideal I=a*b-b*a,c-c;')
rem=singular.eval('reduce(a*b-b*a,std(I));');print('Singular contraction ideal remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-17-C01':bool(c01),'CAS-17-C02':False,'CAS-17-C03':False,'CAS-17-C04':bool(c04)},'domain_assumption_diff':['CAS-17-C02: exact scaling weights for B,A,H,dA,calibration,Kc,M2,L and affine normalization are absent from permitted sources','CAS-17-C03: endpoint redshift rescalings and conformal-acceleration conventions are not fully specified in permitted sources'],'counterexample':None,'engine':'SageMath plus explicit Singular contraction ideal','singular_remainder':rem,'notes':['C01 Gram positive and future selection are domain assumptions; normalized N and beta relation are real timelike algebra.','C04 is common passive invertible coordinate transport, not physical observer replacement.']}))
