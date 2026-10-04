"""Frozen narrow oracle, independent q2-only cubic calculation in Sage."""
import json
import sys
from sage.all import PolynomialRing,QQ
R=PolynomialRing(QQ,names=('t','x','y','z')); t,x,y,z=R.gens(); X=[t,x,y,z]; eta=[-1,1,1,1]
H=[[R(0) for _ in range(4)] for _ in range(4)]
H[0][2]=H[2][0]=-t*(x*x+y*y+z*z)/2
def D(f,a): return f.derivative(X[a])
tr=sum(eta[a]*H[a][a] for a in range(4))
divdiv=sum(eta[a]*eta[c]*D(D(H[a][c],a),c) for a in range(4) for c in range(4))
boxtr=sum(eta[a]*D(D(tr,a),a) for a in range(4))
def G(a,c):
    return (sum(eta[e]*(D(D(H[e][c],a),e)+D(D(H[e][a],c),e)) for e in range(4))
      -sum(eta[e]*D(D(H[a][c],e),e) for e in range(4))-D(D(tr,a),c)
      -(eta[a]*(divdiv-boxtr) if a==c else 0))/2
value=D(G(1,2),1).subs({t:0,x:0,y:0,z:0})
candidate=json.loads(sys.argv[1])
assert set(candidate)=={'coefficient'} and str(candidate['coefficient'])==str(value)
print(json.dumps({'valid':True,'coefficient':str(value),'component':'partial_x delta_G_12 at origin for q2=1 only'}))
