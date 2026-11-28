"""Physical initial-data checks and local Euclidean SO(3)/amplitude quotient.

All geometric data are Hubble normalized. This module does not solve Einstein's
equations or define an observational Fisher matrix.
"""
import numpy as np

def unpack6(values):
    v=np.asarray(values,dtype=float)
    if v.shape!=(6,) or not np.isfinite(v).all():
        raise ValueError("expected finite symmetric packed tensor")
    return np.array([[v[0],v[3],v[4]],[v[3],v[1],v[5]],[v[4],v[5],v[2]]])

def initial_geometry(point,omega_lambda):
    n=unpack6(point["N6"]);s=unpack6(point["shear6"]);a=np.asarray(point["A3"],dtype=float)
    if a.shape!=(3,) or not np.isfinite(a).all() or not np.isfinite(omega_lambda) or omega_lambda<0:
        raise ValueError("invalid A or Lambda density")
    if abs(np.trace(s))>1e-12*(1+np.linalg.norm(s)):
        raise ValueError("shear must be trace-free")
    j=n@a
    if np.linalg.norm(j)>1e-12*np.linalg.norm(n)*np.linalg.norm(a):
        raise ValueError("Jacobi N A != 0")
    k=(np.sum(n*n)-.5*np.trace(n)**2)/6+a@a
    omega=1-np.sum(s*s)/6-k-omega_lambda
    if omega<=0 or not np.isfinite(omega):raise ValueError("nonpositive Gauss energy")
    ns=n@s; ax=np.array([ns[1,2]-ns[2,1],ns[2,0]-ns[0,2],ns[0,1]-ns[1,0]])
    f=(3*s@a+ax)/(3*omega)
    if not np.isfinite(f).all() or np.linalg.norm(f)>=1:
        raise ValueError("nonphysical required total flux/E")
    return {"K":float(k),"omega_E":float(omega),"required_flux_over_E":f.tolist(),
            "jacobi_norm":float(np.linalg.norm(j))}

def lie_text(point,omega_lambda):
    initial_geometry(point,omega_lambda)
    return "".join(name+" "+" ".join(format(float(x),".17g") for x in point[key])+"\n"
                   for name,key in (("shear","shear6"),("n","N6"),("a","A3")))

def realify(x):
    x=np.asarray(x,dtype=complex).reshape(-1)
    return np.concatenate((x.real,x.imag))

def generators(x,ell_min,ell_max):
    a=np.asarray(x,dtype=complex)
    if type(ell_min) is not int or type(ell_max) is not int or not 0<=ell_min<=ell_max:
        raise ValueError("invalid harmonic band")
    if a.shape!=((ell_max+1)**2-ell_min**2,3) or not np.isfinite(a).all():
        raise ValueError("invalid all-m TEB array")
    out=np.empty((3,*a.shape),complex)
    for l in range(ell_min,ell_max+1):
        m=np.arange(-l,l+1)
        jp=np.diag(np.sqrt(l*(l+1)-m[:-1]*(m[:-1]+1)),k=-1)
        jx=(jp+jp.T)/2;jy=(jp-jp.T)/(2j);jz=np.diag(m)
        sl=slice(l*l-ell_min**2,(l+1)**2-ell_min**2)
        for i,j in enumerate((jx,jy,jz)):out[i,sl,:]=-1j*j@a[sl,:]
    return out

def central_derivative(minus,plus,width):
    a=np.asarray(minus,dtype=complex);b=np.asarray(plus,dtype=complex)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all() or not np.isfinite(width) or width<=0:
        raise ValueError("invalid central stencil")
    return (b-a)/(2*width)

def quotient_metric(x,derivatives,ell_min,ell_max,rtol=1e-10):
    """Real least squares on shared amplitude + infinitesimal SO(3) directions."""
    x=np.asarray(x,dtype=complex);d=np.asarray(derivatives,dtype=complex)
    g=generators(x,ell_min,ell_max)
    if d.ndim!=3 or d.shape[1:]!=x.shape or not np.isfinite(d).all() or not len(d):
        raise ValueError("invalid derivative array")
    if not np.isfinite(rtol) or not 0<rtol<1:raise ValueError("invalid nuisance SVD tolerance")
    y=realify(x);norm=np.linalg.norm(y)
    if norm<=0 or not np.isfinite(norm):raise ValueError("zero/nonfinite sky")
    u=np.column_stack([y,*[realify(v) for v in g]])/norm
    j=np.column_stack([realify(v) for v in d])/norm
    w,s,_=np.linalg.svd(u,full_matrices=False)
    rank=int(np.count_nonzero(s>rtol*s[0]))
    basis=w[:,:rank];proj=j-basis@(basis.T@j)
    sig=np.linalg.svd(proj,compute_uv=False)
    return {"gram":proj.T@proj,"singular_values":sig,"nuisance_singular_values":s,
            "nuisance_rank":rank,"raw_column_norms":np.linalg.norm(j,axis=0),
            "projected_column_norms":np.linalg.norm(proj,axis=0),"projected":proj,
            "nuisance_residual":float(np.linalg.norm(basis.T@proj))}
