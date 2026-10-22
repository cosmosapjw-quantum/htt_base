import numpy as np, itertools
exec(open('opnorm.py').read().split("# G symmetric")[0].split("print(")[0])
I=range(3)
def contr(G): return np.einsum('bcac->ba',G)
def asym(X): return (X-X.T)/2
# param: G[b,c,a,d] = sum over sym pairs (b,c) of STF M
best=None
# try G = e_(b,c) sym ⊗ M with small integer M and pairs
import random
mats=[]
for vals in itertools.product([-1,0,1],repeat=5):
    a01,a02,a12,d0,d1=vals
    M=np.array([[d0,a01,a02],[a01,d1,a12],[a02,a12,-d0-d1]],float)
    if np.allclose(M,0): continue
    mats.append(M)
pairs=list(itertools.combinations_with_replacement(I,2))
for (p1,p2) in itertools.combinations(pairs,2):
  for M1 in mats[:]:
    for M2 in mats:
      G=np.zeros((3,3,3,3))
      for (b,c),M in [(p1,M1),(p2,M2)]:
        G[b,c]+=M
        if b!=c: G[c,b]+=M
      r=np.linalg.norm(asym(contr(G)))/np.linalg.norm(G)
      if best is None or r>best[0]: best=(r,p1,p2,M1.copy(),M2.copy())
print(best)
