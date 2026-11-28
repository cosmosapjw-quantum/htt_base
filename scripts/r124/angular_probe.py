"""Independent angular basis and cold-screen collision checks for m=0,1."""
import numpy as np
import json
from scipy.special import eval_jacobi,gammaln
def basis(l,m,h,x):
    # d^l_{m,-h}; reduce by exact Wigner symmetries to M>=|N|.
    M,N=m,-h;sign=1
    if N>M:
        sign=(-1)**(M-N);M,N=N,M
    elif N< -M:
        M,N=-N,-M
    j=l-M;al=M-N;be=M+N
    pref=sign*(-1)**(M-N)*np.exp(.5*(gammaln(l+M+1)+gammaln(l-M+1)-gammaln(l+N+1)-gammaln(l-N+1)))*np.sqrt((2*l+1)/(4*np.pi))
    w=((1-x)/2)**(al/2)*((1+x)/2)**(be/2)
    J=eval_jacobi(j,al,be,x);Jd=(j+al+be+1)/2*eval_jacobi(j-1,al+1,be+1,x) if j else np.zeros_like(x)
    return pref*w*J,pref*w*((N-M*x)*J+(1-x*x)*Jd)
def main():
    x,w=np.polynomial.legendre.leggauss(48);weights=w*2*np.pi;out={}
    for m in (0,1):
        S=np.diag([-.5,-.5,1.]) if m==0 else np.array([[0.,0.,1.],[0.,0.,0.],[1.,0.,0.]])
        f2=np.sqrt(4*np.pi/5) if m==0 else -np.sqrt(8*np.pi/15)
        g1=np.sqrt(4*np.pi/3) if m==0 else -np.sqrt(2*np.pi/3)
        ph=2*np.pi*np.arange(32)/32
        mu,phi=np.meshgrid(x,ph,indexing="ij");r=np.sqrt(1-mu**2)
        n=np.stack((r*np.cos(phi),r*np.sin(phi),mu),-1)
        et=np.stack((mu*np.cos(phi),mu*np.sin(phi),-r),-1);ep=np.stack((-np.sin(phi),np.cos(phi),np.zeros_like(phi)),-1)
        P=np.eye(3)-n[...,None]*n[...,None,:]
        f=np.einsum("...i,ij,...j->...",n,S,n);J=P@S@P+f[...,None,None]*P/2
        q=np.einsum("...i,...ij,...j->...",et,J,et)-np.einsum("...i,...ij,...j->...",ep,J,ep)
        u=2*np.einsum("...i,...ij,...j->...",et,J,ep)
        dip=n[...,2] if m==0 else n[...,0]
        def proj(field,l,h):
            return np.sum(field*np.conjugate(basis(l,m,h,x)[0][:,None]*np.exp(1j*m*phi))*w[:,None]*(2*np.pi/len(ph)))
        errors={"f2":float(abs(proj(f,2,0)-f2)),"g1":float(abs(proj(dip,1,0)-g1)),
            "Pplus":float(abs(proj(q+1j*u,2,2)-np.sqrt(6)*f2)),"Pminus":float(abs(proj(q-1j*u,2,-2)-np.sqrt(6)*f2))}
        mats={}
        for h in (0,2,-2):
            ls=range(max(m,abs(h)),17);v,d=map(np.asarray,zip(*(basis(l,m,h,x) for l in ls)))
            G=(v*weights)@v.T;A=(v*weights)@d.T;M=(v*(weights*x))@v.T
            mats[str(h)]=max(float(np.max(abs(G-np.eye(len(v))))),float(np.max(abs(A+A.T-2*M))))
            if h==0:
                j1=1-m;j2=2-m
                # Flux dipole source coefficient of geometric stress, with a=0.37,k=0.21.
                val=(.37*A[j1,j2]+1j*m*.21*M[j1,j2])*f2/(3*g1)
                target=(.37+1j*m*.21/3)*2/5
                errors["moment_constraint"]=float(abs(val-target))
                if m==0:errors["monopole_to_dipole"]=float(abs(A[j1,0]))
        assert max(*errors.values(),*mats.values())<2e-11,(m,errors,mats)
        out[str(m)]={"f2":f2,"g1":g1,"screen_and_moment_errors":errors,"gram_advection_max":mats}
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
