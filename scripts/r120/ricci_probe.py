"""Direct Koszul contraction for rank-two Jacobi-admissible Lie charts."""
import json
import numpy as np

def direct(b,d,a):
    n=np.diag([0.,b,d]);v=np.array([a,0.,0.])
    e=np.zeros((3,3,3))
    for i,j,k in [(0,1,2),(1,2,0),(2,0,1)]:e[i,j,k]=1;e[j,i,k]=-1
    c=np.einsum("ijl,lk->kij",e,n)+np.einsum("i,kj->kij",v,np.eye(3))-np.einsum("j,ki->kij",v,np.eye(3))
    g=np.empty_like(c)
    for k,i,j in np.ndindex(c.shape):
        g[k,i,j]=(c[k,i,j]-c[i,j,k]+c[j,k,i])/2
    ric=np.zeros((3,3))
    for j,k in np.ndindex(ric.shape):
        ric[j,k]=sum(g[m,j,k]*g[i,i,m]-g[m,i,k]*g[i,j,m]-c[m,i,j]*g[i,m,k]
                     for i in range(3) for m in range(3))
    return ric

def formula(b,d,a):
    return np.array([[-.5*(b-d)**2-2*a*a,0,0],
        [0,.5*(b*b-d*d)-2*a*a,(b-d)*a],
        [0,(b-d)*a,-.5*(b*b-d*d)-2*a*a]])

def main():
    rng=np.random.default_rng(120)
    pts=[(k*np.exp(u),s*k*np.exp(-u),a) for s in (-1,1)
         for k in (0.,.001,.01,.1) for a in (0.,.001,.005,.02) for u in (-.3,0,.3)]
    pts.extend(tuple(x) for x in rng.uniform(-1,1,(128,3)))
    errors=[np.max(abs(direct(*v)-formula(*v))) for v in pts]
    assert max(errors)<2e-14
    # Balanced VII has isotropic Ricci at any k; balanced VI does not.
    for k in (.001,.01,.1):
        np.testing.assert_allclose(direct(k,k,.005),-2*.005**2*np.eye(3),atol=1e-15)
    print(json.dumps({"seed":120,"points":len(pts),"max_ricci_abs_error":float(max(errors)),
       "balanced_VII_isotropic_ricci":True,"scope":"finite direct-index contraction, not Einstein evolution"},indent=2))
if __name__=="__main__":main()
