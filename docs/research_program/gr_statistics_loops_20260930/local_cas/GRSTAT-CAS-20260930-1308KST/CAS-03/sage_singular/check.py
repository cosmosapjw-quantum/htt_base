from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['u0','u1','u2','u3']+[f's{i}{j}' for i in range(4) for j in range(i,4)])
z=R.gens_dict();u=vector(R,[z[f'u{i}'] for i in range(4)]);g=diagonal_matrix(R,[-1,1,1,1]);S=matrix(R,4,4,lambda i,j:z[f's{min(i,j)}{max(i,j)}']);t=u*S*u;B=S+t*g
I=R.ideal([u*g*u+1]); eigen=(g*S)*u+t*u # if Bu=0 then (gS)u=-t u; st=-t
# Quotient certificate for Bu=g*eigen on the mass shell.
c01=all(I.reduce(x)==0 for x in (B*u-g*eigen))
# Rest A=0, theta=0 kernel parameterized by arbitrary spatial STF block, all normalized u=(1,0,0,0).
P=PolynomialRing(QQ,names=['s11','s12','s13','s22','s23']);p=P.gens_dict();T=matrix(P,3,3,[[p['s11'],p['s12'],p['s13']],[p['s12'],p['s22'],p['s23']],[p['s13'],p['s23'],-p['s11']-p['s22']]]);B0=block_diagonal_matrix(matrix(P,1,1,0),T);r=vector(P,[1,0,0,0]);c01=c01 and B0*r==0 and T.trace()==0 and r*diagonal_matrix(P,[-1,1,1,1])*r==-1
singular.eval('ring r=0,(u0,u1,u2,u3),dp; ideal I=-u0^2+u1^2+u2^2+u3^2+1;')
rem=singular.eval('reduce(-u0^2+u1^2+u2^2+u3^2+1,std(I));')
print('Singular mass-shell remainder: '+rem,file=sys.stderr)
# C02 source does not define B_epsilon_chi, K for this family, or the exact slope difference.
c02=False
# C03 arbitrary fixed symmetric STF shear with det D != 0.
F=PolynomialRing(QQ,names=['H','s11','s12','s13','s22','s23','b1','b2','b3']);v=F.gens_dict();H=v['H'];sigma=matrix(F,3,3,[[v['s11'],v['s12'],v['s13']],[v['s12'],v['s22'],v['s23']],[v['s13'],v['s23'],-v['s11']-v['s22']]]);D=H*identity_matrix(F,3)+sigma;beta=vector(F,[v[f'b{i}'] for i in range(1,4)]);h1=-2*D*beta
FF=F.fraction_field();invD=D.change_ring(FF).inverse();c03=all(x==0 for x in invD*vector(FF,h1)/(-2)-vector(FF,beta));trunc=(identity_matrix(FF,3)/H-sigma.change_ring(FF)/H**2)*vector(FF,h1)/(-2)
c03=c03 and all(x==0 for x in trunc-vector(FF,beta)+sigma.change_ring(FF)**2*vector(FF,beta)/H**2)
Ds=diagonal_matrix(QQ,[QQ(3)/2,QQ(3)/4,QQ(3)/4]);bs=vector(QQ,[1,0,0]);negative=(identity_matrix(QQ,3)-diagonal_matrix(QQ,[QQ(1)/2,-QQ(1)/4,-QQ(1)/4]))*Ds*bs
c03=c03 and negative==vector(QQ,[QQ(3)/4,0,0])
print(json.dumps({'checks':{'CAS-03-C01':bool(c01),'CAS-03-C02':bool(c02),'CAS-03-C03':bool(c03)},'domain_assumption_diff':['CAS-03-C02: B_epsilon_chi family and exact slope difference are not specified in permitted contract or COMMON_SPEC.md'],'counterexample':None,'engine':'SageMath plus explicit Singular mass-shell ideal','singular_remainder':rem,'notes':['C01 proves equivalence conditionally on a timelike eigenline; no universal eigenline existence inferred.','C03 is the linear fixed-shear algebra; O(beta^2) remains analytic.']}))
