from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['h0','h11','h12','h13','h22','h23','h33','d1','d2','d3','t'])
v=R.gens_dict();hh=matrix(R,3,3,[[v['h11'],v['h12'],v['h13']],[v['h12'],v['h22'],v['h23']],[v['h13'],v['h23'],v['h33']]]);h1=vector(R,[v['d1'],v['d2'],v['d3']]);S=matrix(R,4,4,lambda i,j:v['h0'] if i==j==0 else (-h1[j-1]/2 if i==0 else -h1[i-1]/2 if j==0 else hh[i-1,j-1]));norm=sum(x*x for x in S.list());expected=v['h0']**2+(h1*h1)/2+sum(x*x for x in hh.list());c01=norm==expected and sum(x*x for x in diagonal_matrix(R,[-1,1,1,1]).list())==4
# Universal polarization identity for two generic symmetric matrices and arbitrary u1,u2.
P=PolynomialRing(QQ,names=[f'u{i}{j}' for i in (1,2) for j in range(4)]+[f's{k}{i}{j}' for k in (1,2) for i in range(4) for j in range(i,4)])
p=P.gens_dict();u1=vector(P,[p[f'u1{i}'] for i in range(4)]);u2=vector(P,[p[f'u2{i}'] for i in range(4)]);S1=matrix(P,4,4,lambda i,j:p[f's1{min(i,j)}{max(i,j)}']);S2=matrix(P,4,4,lambda i,j:p[f's2{min(i,j)}{max(i,j)}']);lhs=u2*S2*u2-u1*S1*u1;rhs=u2*(S2-S1)*u2+(u2-u1)*S1*u2+u1*S1*(u2-u1);swap=u1*(S2-S1)*u1+(u2-u1)*S2*u1+u2*S2*(u2-u1);c02=lhs==rhs==swap
# Use t=sqrt(1+d.d)>0, J=(d/t; I), J^T J=I+dd^T/t^2.
d=vector(R,[v[f'd{i}'] for i in range(1,4)]);t=v['t'];F=R.fraction_field();df=vector(F,d);J=matrix(F,4,3,lambda i,j:df[j]/t if i==0 else (1 if i-1==j else 0));gram=J.transpose()*J;target=identity_matrix(F,3)+df.column()*df.row()/t**2;ideal=R.ideal([t*t-1-d*d]);c03=gram==target and all(ideal.reduce(R((gram[i,j]-target[i,j]).numerator()))==0 for i in range(3) for j in range(3))
# radial eigenvalue, two transverse eigenvalues.
c03=c03 and all(ideal.reduce(R((sum(gram[i,j]*df[j] for j in range(3))-(1+(d*d)/t**2)*df[i]).numerator()))==0 for i in range(3))
singular.eval('ring r=0,(t,d1,d2,d3),dp; ideal I=t^2-1-d1^2-d2^2-d3^2;')
rem=singular.eval('reduce(t^2-1-d1^2-d2^2-d3^2,std(I));');print('Singular hyperboloid remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-02-C01':bool(c01),'CAS-02-C02':bool(c02),'CAS-02-C03':bool(c03),'CAS-02-C04':False},'domain_assumption_diff':['CAS-02-C04: the stated finite inverse bound formula is absent from permitted sources'],'counterexample':None,'engine':'SageMath plus explicit Singular hyperboloid ideal','singular_remainder':rem,'notes':['C03 positive branch t>0 gives u(d); radial eigenvalue 1+|d|^2/(1+|d|^2), transverse eigenvalues 1,1.','The rapidity cap uses monotonicity of r^2/(1+r^2), an analytic inequality.']}))
