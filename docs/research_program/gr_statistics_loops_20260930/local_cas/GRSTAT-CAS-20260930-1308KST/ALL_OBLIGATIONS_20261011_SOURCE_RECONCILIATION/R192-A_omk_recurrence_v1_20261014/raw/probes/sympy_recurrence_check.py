import sympy as sp
w,K=sp.symbols('w K')
g=1+3*w; a=sp.Rational(3,2)*(1-w)
N=7
c={0:0}
for n in range(1,N+1):
    quad=sum(i*c.get(i,0)*c.get(n-i,0) for i in range(0,n+1))
    cub=sum((1-2*i)*c.get(i,0)*c.get(j,0)*c.get(n-i-j,0) for i in range(0,n+1) for j in range(0,n-i+1))
    R=(-1 if n==1 else 0)+(g*(n-1)-g/2)*c[n-1]-2*quad+a*cub
    c[n]=sp.factor(sp.simplify(R/(g*n+a)))
C3=-2*(81*w**4+324*w**3+594*w**2+460*w+141)/((3*w+5)**3*(5*w+3)*(9*w+7))
print(sp.simplify(c[1]+2/(3*w+5)), sp.simplify(c[2]+2*(9*w**2+18*w+13)/((3*w+5)**2*(9*w+7))), sp.simplify(c[3]-C3))
# direct series check
h=sum(c[i]*K**i for i in range(1,N+1))
q=g*(1-K)/2+a*h**2
FS=-K-(h/2)*(g*K+3*(1-w)*(1-h**2)); FK=2*K*(q+h)
res=sp.expand(sp.diff(h,K)*FK-FS)
print([sp.simplify(res.coeff(K,n)) for n in range(0,N+1)])
for wv in [0,sp.Rational(1,3)]:
    print([c[n].subs(w,wv) for n in range(1,5)])
# linear graph tangency defect dust
k1=-sp.Rational(2,5); wv=0
gg=g.subs(w,wv); aa=a.subs(w,wv)
S=k1*K
FSl=(-K-(S/2)*(gg*K+3*(1-wv)*(1-S**2))); FKl=2*K*(gg*(1-K)/2+aa*S**2+S)
print(sp.expand(FSl-k1*FKl), (FSl-k1*FKl).subs(K,sp.Rational(1,10)))
# compat at resonances
for wv,n0 in [(-sp.Rational(5,3),1),(-sp.Rational(7,9),2),(-sp.Rational(3,5),3)]:
    gg=g.subs(w,wv); aa=a.subs(w,wv); print(wv, gg*n0+aa)
