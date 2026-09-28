from sage.all import QQ, PolynomialRing, matrix, vector, identity_matrix
from math import prod
names='x y z s11 s22 s12 s13 s23 t11 t22 t12 t13 t23 p1 p2 p3 u1 u2 u3 v1 v2 v3 w1 w2 w3'.split()
R=PolynomialRing(QQ,names=names)
d={name:g for name,g in zip(names,R.gens())}
x,y,z=[d[k] for k in ('x','y','z')]
s11,s22,s12,s13,s23=[d[k] for k in ('s11','s22','s12','s13','s23')]
t11,t22,t12,t13,t23=[d[k] for k in ('t11','t22','t12','t13','t23')]
n=vector(R,[x,y,z]); S=matrix(R,[[s11,s12,s13],[s12,s22,s23],[s13,s23,-s11-s22]]); T=matrix(R,[[t11,t12,t13],[t12,t22,t23],[t13,t23,-t11-t22]])
p=vector(R,[d[k] for k in ('p1','p2','p3')]);u=vector(R,[d[k] for k in ('u1','u2','u3')]);v=vector(R,[d[k] for k in ('v1','v2','v3')]);w=vector(R,[d[k] for k in ('w1','w2','w3')])
def odd_double_factorial(k):
    return prod(range(k,0,-2))
def mean(poly):
    total=R.zero()
    for exps, coeff in poly.dict().items():
        a,b,c=exps[0:3]
        if a%2 or b%2 or c%2: continue
        q=QQ(odd_double_factorial(a-1)*odd_double_factorial(b-1)*odd_double_factorial(c-1))/odd_double_factorial(a+b+c+1)
        total+=coeff*q*prod(R.gen(i)**exps[i] for i in range(3,len(exps)))
    return total
Sn=S*n;Tn=T*n
bilinear=mean(Sn.dot_product(Tn)-n.dot_product(Sn)*n.dot_product(Tn))-(S*T).trace()/5
spin=mean(Sn.dot_product(w.cross_product(n)))
def C(q): return (p.column()*q.row()+q.column()*p.row())/2-identity_matrix(R,3)*p.dot_product(q)/3
cp=(C(u)*C(v)).trace()-p.dot_product(p)*u.dot_product(v)/2-p.dot_product(u)*p.dot_product(v)/6
G=identity_matrix(R,3)*p.dot_product(p)/2+p.column()*p.row()/6
det=G.det()-p.dot_product(p)**3/6
print({'bilinear_residual':bilinear==0,'spin_cross':spin==0,'tilt_gram':cp==0,'tilt_det':det==0,'sage_version':'installed'})
