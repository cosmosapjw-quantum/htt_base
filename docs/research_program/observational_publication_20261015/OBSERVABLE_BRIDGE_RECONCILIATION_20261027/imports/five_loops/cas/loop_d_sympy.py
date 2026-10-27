"""Finite orthonormal-frame Levi-Civita and Ricci calculation for Loop D."""
import sympy as s

N1, N2, N3, A = s.symbols('N1 N2 N3 A', real=True)
n = s.diag(N1, N2, N3)
a = [A, 0, 0]
eps = s.LeviCivita
C = lambda i,j,k: s.expand(sum(eps(i,j,l)*n[l,k] for l in range(3)) + a[i]*int(j==k)-a[j]*int(i==k))
Gamma = lambda i,j,k: s.expand((C(i,j,k)-C(j,k,i)+C(k,i,j))/2)
R = lambda l,m,i,j: s.expand(sum(Gamma(j,m,k)*Gamma(i,k,l)-Gamma(i,m,k)*Gamma(j,k,l) for k in range(3))-sum(C(i,j,k)*Gamma(k,m,l) for k in range(3)))
Ric = s.Matrix(3,3,lambda j,k:s.factor(sum(R(i,j,i,k) for i in range(3))))
print('Jacobi product:', s.Matrix(n)*s.Matrix(a))
print('Ricci in frame (a_1=A, n_1=0):', Ric.subs(N1,0))
for label, vals in {'I':(0,0,0,0),'II':(s.Symbol('u',positive=True),0,0,0),
 'IX':(s.Symbol('u',positive=True),)*3+(0,),
 'V':(0,0,0,s.Symbol('v',positive=True)),
 'VII0-flat':(0,s.Symbol('u',positive=True),s.Symbol('u',positive=True),0),
 'VII0-generic':(0,s.Symbol('u',positive=True),s.Symbol('v',positive=True),0)}.items():
    r=s.simplify(Ric.subs(dict(zip((N1,N2,N3,A),vals))))
    print(label,'Ricci=',r,'scalar=',s.trace(r))
