from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['m1','m2','m3','w12','w13','w23','n1','n2','n3'])
v=R.gens_dict();M=diagonal_matrix(R,[v['m1'],v['m2'],v['m3']]);W=matrix(R,3,3,[[0,v['w12'],v['w13']],[-v['w12'],0,v['w23']],[-v['w13'],-v['w23'],0]]);C=M*W-W*M
c03=all(C[i,j]==(M[i,i]-M[j,j])*W[i,j] for i in range(3) for j in range(3));gap=sum((M[i,i]-M[j,j])**2*W[i,j]**2 for i in range(3) for j in range(i+1,3));c03=c03 and gap==(C.transpose()*C).trace()/2
# On distinct eigenvalue stratum, each W_ij=R_ij/(m_i-m_j); kernel is trivial.
c03=c03 and all((C[i,j]/(M[i,i]-M[j,j]))==W[i,j] for i in range(3) for j in range(i+1,3))
# For an axisymmetric M=aI+b nn^T, [M,W]=0 iff Wn=0 when b!=0; two nonparallel axes force W=0.
N=vector(R,[v['n1'],v['n2'],v['n3']]);I=R.ideal([N*N-1]);An=N.column()*N.row();Comm=An*W-W*An
# Verify exact structural equivalence modulo unit sphere and skewness.
ker=I.ideal if False else R.ideal([N*N-1]+Comm.list());c04=all(ker.reduce(q)==0 for q in list(W*N))
# Two exact nonparallel controls n=e1,e2 show rank three of stacked rotation response.
e1=vector(QQ,[1,0,0]);e2=vector(QQ,[0,1,0]);W0=matrix(R,3,3,W);C1=(e1.column()*e1.row())*W0-W0*(e1.column()*e1.row());C2=(e2.column()*e2.row())*W0-W0*(e2.column()*e2.row());c04=c04 and all(R.ideal(C1.list()+C2.list()).reduce(W0[i,j])==0 for i in range(3) for j in range(i+1,3))
singular.eval('ring r=0,(n1,n2,n3),dp; ideal I=n1^2+n2^2+n3^2-1;')
rem=singular.eval('reduce(n1^2+n2^2+n3^2-1,std(I));');print('Singular sphere remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-15-C01':False,'CAS-15-C02':False,'CAS-15-C03':bool(c03),'CAS-15-C04':bool(c04)},'domain_assumption_diff':['CAS-15-C01: target photon direction/energy formulas are not specified in permitted sources','CAS-15-C02: pointwise sphere polynomial, divergence weights and weak quadrupole residual are not specified in permitted sources'],'counterexample':None,'engine':'SageMath plus explicit Singular sphere ideal','singular_remainder':rem,'notes':['C03 gap inequality is finite norm algebra for distinct eigenvalues; perturbation needs the stated amplitude bound.','C04 two axisymmetric nonparallel directions have zero common skew commutant; no observed spacetime derivative is inferred.']}))
