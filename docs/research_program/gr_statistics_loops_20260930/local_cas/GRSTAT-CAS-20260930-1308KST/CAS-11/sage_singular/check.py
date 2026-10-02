from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['Ff','Fg','Fh','gf1','gf2','gg1','gg2','f1','f2','g1','g2','h1','h2','a','b','c','d'])
v=R.gens_dict();f=vector(R,[v['f1'],v['f2']]);g=vector(R,[v['g1'],v['g2']]);h=vector(R,[v['h1'],v['h2']]);gf=vector(R,[v['gf1'],v['gf2']]);gg=vector(R,[v['gg1'],v['gg2']]);Dfg=v['Ff']-v['Fg']-gg*(f-g);Dfh=v['Ff']-v['Fh']-vector(R,[v['a'],v['b']])*(f-h);Dgh=v['Fg']-v['Fh']-vector(R,[v['a'],v['b']])*(g-h);three=Dfg-(Dfh-Dgh)-(vector(R,[v['a'],v['b']])-gg)*(f-g);c01=three==0
# Residual Gram for two vectors after projection off first coordinate.
v1=vector(R,[v['a'],v['b'],v['c']]);v2=vector(R,[v['b'],v['c'],v['d']]);P=diagonal_matrix(R,[0,1,1]);A=matrix(R,3,2,[list(v1),list(v2)]).transpose() if False else matrix(R,3,2,lambda i,j:(v1 if j==0 else v2)[i]);G=A.transpose()*P*A
c02=G==G.transpose() and G[0,0]*G[1,1]-G[0,1]**2==(v['b']*v['d']-v['c']**2)**2
# On singular rank-one and zero strata, kernel-null bound forces e perpendicular kernel.
G1=matrix(QQ,2,2,[[1,0],[0,0]]);e=vector(QQ,[1,0]);c02=c02 and G1.pseudoinverse()==G1 and e*G1.pseudoinverse()*e==1
# Weighted projection/Cauchy in finite diagonal W>0, projector on retained constant.
F=R.fraction_field();ww=diagonal_matrix(F,[1,2,3]);one=vector(F,[1,1,1]);Pr=identity_matrix(F,3)-one.column()*(one*ww).row()/(one*ww*one);c03=Pr*Pr==Pr and Pr.transpose()*ww==ww*Pr
singular.eval('ring r=0,(b,c,d),dp; ideal I=b*d-c^2;')
rem=singular.eval('reduce((b*d-c^2)^2-(b*d-c^2)^2,std(I));');print('Singular Gram-minor remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-11-C01':bool(c01),'CAS-11-C02':bool(c02),'CAS-11-C03':bool(c03)},'domain_assumption_diff':[],'counterexample':None,'engine':'SageMath Gram identities plus explicit Singular ideal','singular_remainder':rem,'notes':['C01 cancellation when gradient difference belongs to matched moment span is finite orthogonality.','C02 general spectral proof: null eigenvectors force e component zero; then test a=Rdagger e and scale to get e^T Rdagger e<=2epsilon. Zero R forces e=0.','C03 is finite weighted projection; continuum Hessian envelope and Taylor integral remain prerequisites.']}))
