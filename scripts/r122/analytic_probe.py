"""Independent spherical quadrature check of the STF coherency reduction."""
import json
import numpy as np

def main():
    x,w=np.polynomial.legendre.leggauss(12);phi=2*np.pi*np.arange(24)/24
    mu,ph=np.meshgrid(x,phi,indexing="ij")
    n=np.stack((np.sqrt(1-mu**2)*np.cos(ph),np.sqrt(1-mu**2)*np.sin(ph),mu),axis=-1).reshape(-1,3)
    weights=np.repeat(w/48,24)
    S=np.array([[.3,.2,.1],[.2,-.1,.12],[.1,.12,-.2]])
    P=np.eye(3)-n[:,:,None]*n[:,None,:]
    f=np.einsum("ni,ij,nj->n",n,S,n)
    A=f[:,None,None]*P/2;B=P@S@P+f[:,None,None]*P/2
    mean=lambda v:np.einsum("n,nij->ij",weights,v)
    a,b=.17,-.13
    J=a*A+b*B;collision=1.5*P@mean(J)@P-J
    pred=(-.9*a-.6*b)*A+(-.1*a-.4*b)*B
    pressure=mean(f[:,None,None]*n[:,:,None]*n[:,None,:])
    err={"mean_A":float(np.max(abs(mean(A)+S/15))),"mean_B":float(np.max(abs(mean(B)-2*S/5))),
         "collision":float(np.max(abs(collision-pred))),"pressure":float(np.max(abs(pressure-2*S/15)))}
    assert max(err.values())<2e-14
    eig=np.linalg.eigvals([[-.9,-.6],[-.1,-.4]])
    assert np.max(abs(eig.imag))<1e-14
    print(json.dumps({"quadrature_points":len(n),"errors":err,"eigenvalues":eig.real.tolist(),
      "scope":"finite exact-degree angular quadrature, independent screen tensor construction"},indent=2))
if __name__=="__main__":main()
