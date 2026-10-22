import numpy as np
G=np.zeros((3,3,3,3))
ent={(0,0,0,2):-2,(0,0,2,0):-2,(0,1,1,2):-1,(0,1,2,1):-1,(0,2,0,0):2,(0,2,2,2):-2,(1,0,1,2):-1,(1,0,2,1):-1,(1,2,0,1):1,(1,2,1,0):1,(2,0,0,0):2,(2,0,2,2):-2,(2,1,0,1):1,(2,1,1,0):1,(2,2,0,2):2,(2,2,2,0):2}
for k,v in ent.items(): G[k]=v
C=np.einsum('bcac->ba',G); A=(C-C.T)/2
print((G**2).sum(), (A**2).sum()); print(C); print(A)
print(np.allclose(G,G.transpose(1,0,2,3)), np.allclose(G,G.transpose(0,1,3,2)), np.abs(np.einsum('bcaa->bc',G)).max())
om=-(6/5)*A; print((om**2).sum(), (0.09+0.03+7.8)**2)
