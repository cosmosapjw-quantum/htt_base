import sympy as sp
x,y,z=sp.symbols('x y z', real=True)
s11,s22,s12,s13,s23,t11,t22,t12,t13,t23=sp.symbols('s11 s22 s12 s13 s23 t11 t22 t12 t13 t23', real=True)
p1,p2,p3,u1,u2,u3,v1,v2,v3,w1,w2,w3=sp.symbols('p1 p2 p3 u1 u2 u3 v1 v2 v3 w1 w2 w3', real=True)
n=sp.Matrix([x,y,z]); S=sp.Matrix([[s11,s12,s13],[s12,s22,s23],[s13,s23,-s11-s22]]); T=sp.Matrix([[t11,t12,t13],[t12,t22,t23],[t13,t23,-t11-t22]])
w=sp.Matrix([w1,w2,w3]); p=sp.Matrix([p1,p2,p3]); u=sp.Matrix([u1,u2,u3]); v=sp.Matrix([v1,v2,v3])
def sphere_mean(poly):
    out=0
    for powers,coef in sp.Poly(sp.expand(poly),x,y,z).terms():
        if any(q%2 for q in powers): continue
        total=sum(powers)
        m=sp.prod(sp.factorial2(q-1) for q in powers)/sp.factorial2(total+1)
        out+=coef*m
    return sp.expand(out)
Sn=S*n; Tn=T*n
bilinear=sphere_mean(Sn.dot(Tn)-(n.dot(Sn))*(n.dot(Tn)))
spin=sphere_mean(Sn.dot(w.cross(n)))
def C(q): return (p*q.T+q*p.T)/2-sp.eye(3)*(p.dot(q))/3
cpgram=sp.expand(sp.trace(C(u)*C(v))-(p.dot(p))*(u.dot(v))/2-(p.dot(u))*(p.dot(v))/6)
G=(p.dot(p))*sp.eye(3)/2+p*p.T/6
detres=sp.factor(G.det()-(p.dot(p))**3/6)
print({'bilinear_residual':sp.factor(bilinear-sp.trace(S*T)/5),'arbitrary_spin_cross':sp.factor(spin),'tilt_stf_gram_residual':sp.factor(cpgram),'tilt_gram_det_residual':detres,'sympy_version':sp.__version__})
