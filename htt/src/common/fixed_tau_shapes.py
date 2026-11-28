"""Fixed-background, affine-depth constrained scalar opacity shape response."""
import numpy as np
from scipy.linalg import null_space
from scipy.integrate import solve_ivp
from common.physical_memory_budget import collision_action
from common.opacity_memory_kernel import _initial,_check

def source_metrics(c,w,order=12):
    _check(c,w);q,wt,u,j=w.nodes(order);rate=c["system"]["coeff"](q)[5]
    r=w.ratios(q);wg=wt*rate;t=r.T@wg;tau=float(wg.sum())
    if not np.isfinite(tau) or tau<=0:raise ValueError("nonpositive total depth")
    x=np.interp(q,w.table[:,0],w.table[:,1])
    r0=np.divide((1-u)*w.table[j,1],x,out=np.zeros_like(x),where=x>0)
    r1=np.divide(u*w.table[j+1,1],x,out=np.zeros_like(x),where=x>0)
    d=np.zeros(len(w.table));np.add.at(d,j,wg*r0);np.add.at(d,j+1,wg*r1)
    return {"t":t,"tau":tau,"nodal":d,"M_tau":r.T@(wg[:,None]*r)/tau,
        "M_clock":r.T@(wt[:,None]*r)/w.table[-1,0]}

def constrained_basis(M,t,active):
    M=np.asarray(M,float);t=np.asarray(t,float);a=np.asarray(active)
    if M.shape!=(len(t),len(t)) or a.ndim!=1 or not np.issubdtype(a.dtype,np.integer) or len(a)<2 or len(set(a))!=len(a) or np.any((a<0)|(a>=len(t))) or not np.isfinite(M).all() or not np.isfinite(t).all():raise ValueError("invalid source geometry")
    s=M[np.ix_(a,a)]
    if not np.allclose(s,s.T,rtol=1e-12,atol=1e-14):raise ValueError("non symmetric metric")
    L=np.linalg.cholesky(s);H=np.linalg.solve(L.T,np.eye(len(a)))
    row=t[a]@H
    if np.linalg.norm(row)==0:raise ValueError("degenerate depth covector")
    Z=null_space(row[None,:]);B=np.zeros((len(t),Z.shape[1]));B[a]=H@Z
    return B

def balanced_pair(t,positive,negative):
    t=np.asarray(t,float)
    if positive==negative or min(t[positive],t[negative])<=0:raise ValueError("invalid contrast")
    a=np.zeros_like(t);a[positive]=t[negative];a[negative]=-t[positive]
    return a/np.max(abs(a))

def perturb_nodes(w,f,h):
    f=np.asarray(f,float)
    if f.shape!=(len(w.table),) or not np.isfinite(f).all() or not np.isfinite(h) or np.any(1+h*f<0):raise ValueError("invalid opacity direction")
    tab=w.table.copy();tab[:,1]*=1+h*f
    return tab

def visibility(c,w,order=8):
    _check(c,w);t,wt,u,j=w.nodes(order);knots=w.table[:,0];rate=c["system"]["coeff"](t)[5]
    cells=(wt*rate).reshape(-1,order).sum(axis=1)
    suffix=np.r_[np.cumsum(cells[::-1])[::-1],0.]
    q,x=np.polynomial.legendre.leggauss(order);x=x/2;q=(q+1)/2
    rem=knots[j+1]-t
    sub=t[:,None]+rem[:,None]*q
    partial=rem*(c["system"]["coeff"](sub.ravel())[5].reshape(-1,order)@x)
    g=rate*np.exp(-suffix[j+1]-partial);mass=float(wt@g)
    if mass<=0:raise ValueError("zero visibility")
    z=1601*np.exp(-t)-1
    mean=float((wt*g)@t/mass);mean_z=float((wt*g)@z/mass)
    return {"tau":float(suffix[0]),"mass":mass,"exact_mass":float(-np.expm1(-suffix[0])),
        "mean_eta":mean,"mean_z":mean_z,"std_eta":float(np.sqrt((wt*g)@((t-mean)**2)/mass))}

def integrate_direction(c,w,f,y,rtol=2e-11,max_step=.015):
    _check(c,w);f=np.asarray(f,float);perturb_nodes(w,f,0.)
    s=c["system"];y=_initial(c,np.asarray(y)[:,None])[:,0];n=len(y)
    delta=w.table[:,1]*f
    def rhs(t,u):
        a=u.reshape(n,2);dy=s["rhs"](t,a)
        xe=np.interp(t,w.table[:,0],w.table[:,1])
        ratio=np.interp(t,w.table[:,0],delta)/xe if xe>0 else 0.
        dy[:,1]+=ratio*collision_action(c,t,a[:,[0]])[:,0]
        return dy.ravel()
    init=np.column_stack((y,np.zeros_like(y))).ravel()
    sol=solve_ivp(rhs,(0.,w.table[-1,0]),init,method="DOP853",rtol=rtol,atol=rtol/100,max_step=max_step)
    if not sol.success or not np.isfinite(sol.y).all():raise RuntimeError(sol.message)
    end=sol.y[:,-1].reshape(n,2)
    return {"end":end[:,0],"tangent":end[:,1],"nfev":int(sol.nfev),
        "max_endpoint_constraint":float(np.max(abs(s["constraint"](w.table[-1,0],end))))}

def real_map(dsky):
    # rows of all-m real physical sky, real opacity coefficient columns
    a=np.asarray(dsky,dtype=complex).reshape(len(dsky),-1).T
    return np.vstack((a.real,a.imag))
