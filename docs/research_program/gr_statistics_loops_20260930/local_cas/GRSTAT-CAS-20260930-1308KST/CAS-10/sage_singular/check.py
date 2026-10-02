from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['u0','u1','u2','u3','c']+[f's{i}{j}' for i in range(4) for j in range(i,4)])
z=R.gens_dict();u=vector(R,[z[f'u{i}'] for i in range(4)]);g=diagonal_matrix(R,[-1,1,1,1]);S=matrix(R,4,4,lambda i,j:z[f's{min(i,j)}{max(i,j)}']);t=u*S*u;B=S+t*g;b=B*u;A=2*z['c']*b
J=(S*u)*g*(S*u)+t*t;rhs=(A*g*A)/(4*z['c']**2)
I=R.ideal([u*g*u+1]);numerator=R((J-rhs).numerator());c02=I.reduce(numerator)==0 and I.reduce(b*u)==0
singular.eval('ring r=0,(u0,u1,u2,u3),dp; ideal I=-u0^2+u1^2+u2^2+u3^2+1;')
rem=singular.eval('reduce(-u0^2+u1^2+u2^2+u3^2+1,std(I));')
print('Singular mass-shell remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-10-C01':False,'CAS-10-C02':bool(c02),'CAS-10-C03':False,'CAS-10-C04':False},'domain_assumption_diff':['CAS-10-C01: two rational morphology tuples and separate-sector powers are absent from permitted sources','CAS-10-C03: finite Gaussian mean vectors and compression blocks are absent from permitted sources','CAS-10-C04: quintic cutoff polynomial and rational bound construction are absent from permitted sources'],'counterexample':None,'engine':'SageMath plus explicit Singular mass-shell ideal','singular_remainder':rem,'notes':['C02 equality certified on mass shell; nonnegative spatial norm and zero iff A=0 use future timelike branch.']}))
