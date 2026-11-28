"""Independent Koszul and angular Galerkin algebra checks, before solver implementation."""
import json
import numpy as np
from scipy.special import eval_jacobi, gammaln

def basis(l,h,x):
    n=-h;j=l-2;al=2-n;be=2+n
    p=np.exp(.5*(gammaln(l+3)+gammaln(l-1)-gammaln(l+n+1)-gammaln(l-n+1)))*np.sqrt((2*l+1)/(4*np.pi))
    w=((1-x)/2)**(al/2)*((1+x)/2)**(be/2)
    J=eval_jacobi(j,al,be,x)
    Jd=(j+al+be+1)/2*eval_jacobi(j-1,al+1,be+1,x) if j else np.zeros_like(x)
    return p*w*J,p*w*((n-2*x)*J+(1-x*x)*Jd)
def main():
    eps=np.zeros((3,3,3));eps[0,1,2]=eps[1,2,0]=eps[2,0,1]=1;eps[0,2,1]=eps[2,1,0]=eps[1,0,2]=-1
    delta=np.eye(3);rng=np.random.default_rng(123);maxr=0.
    for _ in range(80):
        k,a,x,y=rng.uniform(-.2,.2,4);N=np.array([[k+x,y,0],[y,k-x,0],[0,0,0]]);av=np.array([0,0,a])
        C=np.einsum("ijl,lr->ijr",eps,N)+np.einsum("i,jr->ijr",av,delta)-np.einsum("j,ir->ijr",av,delta)
        G=(C-C.transpose(2,0,1)+C.transpose(1,2,0))/2
        r=np.zeros((3,3))
        for j in range(3):
            for l in range(3):
                r[j,l]=sum(G[j,l,m]*G[i,m,i]-G[i,l,m]*G[j,m,i]-C[i,j,m]*G[m,l,i] for i in range(3) for m in range(3))
        want=np.array([[-2*a*a+2*k*x-2*a*y,2*a*x+2*k*y,0],[2*a*x+2*k*y,-2*a*a-2*k*x+2*a*y,0],[0,0,-2*(a*a+x*x+y*y)]])
        maxr=max(maxr,float(np.max(abs(r-want))))
    assert maxr<1e-13
    x,w=np.polynomial.legendre.leggauss(48);w*=2*np.pi;rows={}
    for h in (0,2,-2):
        v,d=map(np.asarray,zip(*(basis(l,h,x) for l in range(2,17))))
        gram=(v*w)@v.T;M=(v*(w*x))@v.T;A=(v*w)@d.T
        z={"gram_error":float(np.max(abs(gram-np.eye(len(v))))),"M_symmetry":float(np.max(abs(M-M.T))),"A_identity":float(np.max(abs(A+A.T-2*M))),"M22":float(M[0,0])}
        assert max(z["gram_error"],z["M_symmetry"],z["A_identity"],abs(z["M22"]+h/3))<2e-11
        rows[str(h)]=z
    f2=2/(np.sqrt(6)*np.sqrt(5/(4*np.pi)))
    print(json.dumps({"ricci_random_cases":80,"ricci_max_abs_error":maxr,"angular":rows,"f2":f2,"scope":"direct Koszul contraction and analytic Jacobi derivatives, finite quadrature"},indent=2))
if __name__=="__main__":main()
