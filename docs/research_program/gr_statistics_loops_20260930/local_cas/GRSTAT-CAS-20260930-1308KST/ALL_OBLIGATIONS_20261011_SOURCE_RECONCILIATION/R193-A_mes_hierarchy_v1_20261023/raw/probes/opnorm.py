import numpy as np, itertools
I=range(3)
# basis of tensors G[b,c,a,d] symmetric traceless in (a,d)
def stf2_basis():
    B=[]
    for (i,j) in [(0,1),(0,2),(1,2)]:
        M=np.zeros((3,3));M[i,j]=M[j,i]=1/np.sqrt(2);B.append(M)
    M=np.diag([1,-1,0])/np.sqrt(2);B.append(M)
    M=np.diag([1,1,-2])/np.sqrt(6);B.append(M)
    return B
S=stf2_basis()
basis=[]
for b in I:
  for c in I:
    for M in S:
      G=np.zeros((3,3,3,3));G[b,c]=M;basis.append(G)
def contr(G): return np.einsum('bcac->ba',G)
def asym(X): return (X-X.T)/2
A=np.array([asym(contr(G)).ravel() for G in basis]).T
F=np.array([contr(G).ravel() for G in basis]).T
print("STF(a,d): op norm asym∘contr =",np.linalg.norm(A,2)," contr =",np.linalg.norm(F,2))
# unconstrained
basisU=[]
for idx in itertools.product(I,I,I,I):
  G=np.zeros((3,3,3,3));G[idx]=1;basisU.append(G)
A=np.array([asym(contr(G)).ravel() for G in basisU]).T
F=np.array([contr(G).ravel() for G in basisU]).T
print("unconstrained: asym∘contr =",np.linalg.norm(A,2)," contr =",np.linalg.norm(F,2))
# rank-3 STF xi gradient: H[d,c,a,b] with (c,a,b) STF; contraction d=c -> (a,b)
import sympy
# build STF rank3 basis numerically: symmetric traceless 3-index space dim 7
sym=[]
for idx in itertools.combinations_with_replacement(I,3):
  T=np.zeros((3,3,3))
  for p in set(itertools.permutations(idx)): T[p]=1
  sym.append(T.ravel())
Sm=np.array(sym).T  # 27x10
# traceless constraint: sum_c T[c,c,a]=0
C=np.array([[ (np.einsum('cca->a',v.reshape(3,3,3)))[a] for v in Sm.T] for a in I])
# null space of C within span
u,s,vt=np.linalg.svd(C); ns=vt[np.sum(s>1e-10):].T
STF3=Sm@ns
Q,_=np.linalg.qr(STF3); print("dim STF3",Q.shape[1])
basis3=[]
for d in I:
  for k in range(Q.shape[1]):
    H=np.zeros((3,3,3,3));H[d]=Q[:,k].reshape(3,3,3);basis3.append(H)
D=np.array([np.einsum('ccab->ab',H).ravel() for H in basis3]).T
print("STF3 div op norm =",np.linalg.norm(D,2))
DU=np.array([np.einsum('ccab->ab',G).ravel() for G in basisU]).T
print("unconstrained div op norm =",np.linalg.norm(DU,2))
# G symmetric in (b,c) and STF in (a,d)
basisS=[]
for (b,c) in itertools.combinations_with_replacement(I,2):
  for M in S:
    G=np.zeros((3,3,3,3));G[b,c]=M;G[c,b]=M
    basisS.append(G/np.linalg.norm(G))
# orthonormal? check gram
Gm=np.array([g.ravel() for g in basisS]).T
Q2,_=np.linalg.qr(Gm)
A=np.array([asym(contr(q.reshape(3,3,3,3))).ravel() for q in Q2.T]).T
F=np.array([contr(q.reshape(3,3,3,3)).ravel() for q in Q2.T]).T
print("sym(b,c)+STF(a,d): asym∘contr =",np.linalg.norm(A,2)," contr =",np.linalg.norm(F,2))
