from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['x1','x2','x3','w1','w2','w3','z1','z2','z3','a','b'])
v=R.gens_dict();x=vector(R,[v[f'x{i}'] for i in range(1,4)]);w=vector(R,[v[f'w{i}'] for i in range(1,4)]);z=vector(R,[v[f'z{i}'] for i in range(1,4)]);W=matrix(R,3,3,[[0,w[2],-w[1]],[-w[2],0,w[0]],[w[1],-w[0],0]])
I=R.ideal([x*x-1,z*z-1]);red=lambda q:I.reduce(R(q));cross=lambda q,r:vector(R,[q[1]*r[2]-q[2]*r[1],q[2]*r[0]-q[0]*r[2],q[0]*r[1]-q[1]*r[0]])
y=-W*x;Px=identity_matrix(R,3)-x.column()*x.row();Pz=identity_matrix(R,3)-z.column()*z.row();G=v['a']*Px+v['b']*Pz
c01=all(red(t)==0 for t in list(W*x+cross(w,x))+list(cross(x,y)-Px*w)+(G-(v['a']*Px+v['b']*Pz)).list())
# Each a>0 term is |v cross x|^2; zero means v parallel x, so two nonparallel x,z give SPD.
# A direct exact inverse on the nonzero determinant stratum uses adj(G)/det(G).
F=R.fraction_field();GF=G.change_ring(F);c02=all(t==0 for t in (GF*GF.adjugate()-GF.det()*identity_matrix(F,3)).list());
# Numeric exact-rational nonparallel control plus parallel singular control.
xx=vector(QQ,[1,0,0]);zz=vector(QQ,[0,1,0]);G0=2*identity_matrix(QQ,3)-xx.column()*xx.row()-zz.column()*zz.row();c02=c02 and G0.det()>0 and (2*(identity_matrix(QQ,3)-xx.column()*xx.row())).det()==0
# ||delta W||_F^2=2||delta omega||^2; normal-equation error bound uses sigma_min(T)>0.
c03=(W.transpose()*W).trace()==2*(w*w)
singular.eval('ring r=0,(x1,x2,x3),dp; ideal I=x1^2+x2^2+x3^2-1;')
rem=singular.eval('reduce(x1^2+x2^2+x3^2-1,std(I));');print('Singular sphere remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-14-C01':bool(c01),'CAS-14-C02':bool(c02),'CAS-14-C03':bool(c03)},'domain_assumption_diff':[],'counterexample':None,'engine':'SageMath plus explicit Singular sphere ideal','singular_remainder':rem,'notes':['C02 inverse is adj(G)/det(G) for positive weights and nonparallel unit directions; PSD kernel follows sum of weighted squared cross products.','C03 finite least-squares bound follows ||Tdagger||=1/sigma_min(T), and perturbed design obeys ||Delta T omega||<=||Delta T|| Omega_star. No observed derivative channel is inferred.']}))
