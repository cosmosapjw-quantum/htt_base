"""Development-only symbolic table; Lean CAS05C03.lean is the proof authority."""
import sympy as s

qv = {i:s.Symbol(f'q{i}') for i in range(1,4)}
mv = {(i,j):s.Symbol(f'm{i}{j}') for i in range(1,4) for j in range(1,4)}

def q(i): return 0 if i == 0 else qv[i]
def M(i,j): return 0 if i == 0 or j == 0 else mv[i,j]
def S(i,j): return (M(i,j)+M(j,i))/2
def W(i,j): return (M(i,j)-M(j,i))/2
def D(i,j): return int(i == j)
def SD(i,j): return 0 if i == 0 else D(i,j)
def sig(i): return -1 if i == 0 else 1
def J0i(i,d,e,f):
    return -q(i)*(D(d,0)*SD(e,f)+D(e,0)*SD(d,f)+D(f,0)*SD(d,e)) - s.Rational(2,5)*(SD(d,e)*W(i,f)+SD(d,f)*W(i,e)+SD(e,f)*W(i,d))
def Jii(d,e,f):
    return -(D(d,0)*S(e,f)+D(e,0)*S(d,f)+D(f,0)*S(d,e))
def J(a,c,d,e,f):
    if a==0: return 0 if c==0 else J0i(c,d,e,f)
    if c==0: return J0i(a,d,e,f)
    return D(a,c)*Jii(d,e,f)
def ddG(mu,nu,a,c,e):
    return sig(a)*s.Rational(1,2)*(J(e,a,mu,nu,c)+J(c,a,mu,nu,e)-J(c,e,mu,nu,a))
def dR(mu,a,c):
    return sum(ddG(mu,e,e,c,a)-ddG(mu,c,e,e,a) for e in range(4))
def dEin(mu,a,c):
    return s.expand(dR(mu,a,c)-D(a,c)*sig(a)*s.Rational(1,2)*sum(sig(e)*dR(mu,e,e) for e in range(4)))
for mu in range(4):
    print('mu',mu)
    for a in range(4):
        for c in range(a,4):
            print(a,c,s.factor(dEin(mu,a,c)))
