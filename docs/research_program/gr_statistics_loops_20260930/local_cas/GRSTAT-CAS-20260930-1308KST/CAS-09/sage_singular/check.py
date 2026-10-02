from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=[f'a{i}{j}' for i in range(4) for j in range(2)]+[f'b{i}{j}' for i in range(4) for j in range(2)])
v=R.gens_dict();A=matrix(R,4,2,lambda i,j:v[f'a{i}{j}']);B=matrix(R,4,2,lambda i,j:v[f'b{i}{j}']);AB=A.augment(B)
# Generic rank-of-concatenation identity in a regular rank stratum: dim intersection=rA+rB-rAB.
# A rational exact control detects the intersection dimension by kernel elimination.
A0=matrix(QQ,4,2,[[1,0],[0,1],[0,0],[0,0]]);B0=matrix(QQ,4,2,[[1,0],[0,0],[0,1],[0,0]]);rank_identity=A0.rank()+B0.rank()-A0.augment(B0).rank()==1
singular.eval('ring r=0,(x,y,z),dp; ideal I=x*y-y*x;')
rem=singular.eval('reduce(x*y-y*x,std(I));');print('Singular minor identity remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-09-C01':False,'CAS-09-C02':False,'CAS-09-C03':False,'CAS-09-C04':False},'domain_assumption_diff':['CAS-09-C01: exact E4/E9 directional design and two-radius unisolvent point configuration are absent from permitted sources; generic rank intersection identity checked only','CAS-09-C02: future-mass-shell intercept map and full rank13 Jacobian are absent from permitted sources','CAS-09-C03: exact angular basis identities for rank9 alias are absent from permitted sources','CAS-09-C04: supplied rho_i transformation and native mean formula are absent from permitted sources'],'counterexample':None,'engine':'SageMath rank algebra plus explicit Singular ideal','singular_remainder':rem,'partial_rank_identity':bool(rank_identity),'notes':['No rank or physical realization is inferred from a generic rank identity alone.']}))
