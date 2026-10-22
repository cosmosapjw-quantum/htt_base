import numpy as np, itertools
from fractions import Fraction
I=range(3)
def contr(G): return np.einsum('bcac->ba',G)
def asym(X): return (X-X.T)/2
S=[]
for (i,j) in [(0,1),(0,2),(1,2)]:
    M=np.zeros((3,3));M[i,j]=M[j,i]=1;S.append(M)
S.append(np.diag([1.,-1,0]));S.append(np.diag([1.,1,-2]))
basis=[]
for (b,c) in itertools.combinations_with_replacement(I,2):
  for M in S:
    G=np.zeros((3,3,3,3));G[b,c]+=M
    if b!=c: G[c,b]+=M
    basis.append(G)
B=np.array([g.ravel() for g in basis]).T
# maximize |A x|/|B x| generalized eig
A=np.array([asym(contr(g)).ravel() for g in basis]).T
import scipy.linalg as sl
w,v=sl.eigh(A.T@A, B.T@B)
x=v[:,-1]; print(w[-1])
x=x/np.max(np.abs(x)); print(np.round(x,4))
G=(B@x).reshape(3,3,3,3)
nz=[(idx,round(G[idx],4)) for idx in itertools.product(I,I,I,I) if abs(G[idx])>1e-9]
print(nz)
