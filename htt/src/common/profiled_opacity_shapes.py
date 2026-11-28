"""Nested fixed-depth nodal tangents and real initial-state nuisance profile.

Input metrics are declared size diagnostics. A retained numerical range is not
a certified exact rank, and unbounded linear profiling is not a physical prior.
"""
import numpy as np
from scipy.integrate import solve_ivp
from common.physical_memory_budget import collision_action
from common.opacity_memory_kernel import _initial

def nested_groups(g):
    g=np.asarray(g)
    if g.ndim!=1 or not np.issubdtype(g.dtype,np.integer) or not np.array_equal(np.unique(g),np.arange(5)) or np.any(np.diff(g)<0):raise ValueError("invalid ordered source groups")
    out=np.full(len(g),16,dtype=int)
    for i in range(4):
        ids=np.flatnonzero(g==i)
        if len(ids)<4:raise ValueError("too few source nodes")
        for j,part in enumerate(np.array_split(ids,4)):out[part]=4*i+j
    return out

def aggregation(n):
    if n not in (4,8,16):raise ValueError("unsupported nested level")
    return np.eye(n)[np.arange(16)//(16//n)]

class NodalBasis:
    def __init__(self,table,g):
        a=np.asarray(table,float);g=np.asarray(g)
        if a.ndim!=2 or a.shape[1]!=2 or len(a)<2 or not np.isfinite(a).all() or a[0,0]!=0 or np.any(np.diff(a[:,0])<=0) or np.any(a[:,1]<0):raise ValueError("invalid table")
        if g.shape!=(len(a),) or not np.issubdtype(g.dtype,np.integer) or not np.array_equal(np.unique(g),np.arange(17)):raise ValueError("invalid nested labels")
        self.table=a.copy();self.groups=g.copy();self.components=a[:,1,None]*np.eye(17)[g,:16]
    def ratios(self,t):
        t=np.asarray(t,float);x=np.interp(t,self.table[:,0],self.table[:,1])
        y=np.stack([np.interp(t,self.table[:,0],self.components[:,i]) for i in range(16)],axis=-1)
        return np.divide(y,x[...,None],out=np.zeros_like(y),where=x[...,None]>0)
    def nodes(self,order):
        q,w=np.polynomial.legendre.leggauss(order);u=(q+1)/2;w=w/2
        t=self.table[:,0];dt=np.diff(t)
        return (t[:-1,None]+dt[:,None]*u).ravel(),(dt[:,None]*w).ravel()

def nodal_metric(c,w,order=12):
    if not np.array_equal(c["system"]["table"],w.table):raise ValueError("source mismatch")
    q,wt=w.nodes(order);rate=c["system"]["coeff"](q)[5];r=w.ratios(q);wg=wt*rate;t=r.T@wg;tau=float(wg.sum())
    if tau<=0 or not np.isfinite(tau):raise ValueError("nonpositive depth")
    return {"t":t,"tau":tau,"M_tau":r.T@(wg[:,None]*r)/tau,"M_clock":r.T@(wt[:,None]*r)/w.table[-1,0]}

def integrate_nested(c,w,y,rtol=2e-11,max_step=.015):
    if not np.array_equal(c["system"]["table"],w.table):raise ValueError("source mismatch")
    s=c["system"];y=_initial(c,np.asarray(y)[:,None])[:,0];n=len(y)
    z=np.zeros((n,17),complex);z[:,0]=y
    def rhs(t,flat):
        a=flat.reshape(n,17);b=s["rhs"](t,a)
        b[:,1:]+=collision_action(c,t,a[:,[0]])*w.ratios(t)[None,:]
        return b.ravel()
    tt=s["table"][:,0];ts=tt[np.unique(np.r_[np.arange(0,len(tt),32),len(tt)-1])]
    sol=solve_ivp(rhs,(0.,tt[-1]),z.ravel(),method="DOP853",rtol=rtol,atol=rtol/100,max_step=max_step,t_eval=ts)
    if not sol.success or not np.isfinite(sol.y).all():raise RuntimeError(sol.message)
    hist=sol.y.T.reshape(len(ts),n,17);end=hist[-1];constraint=np.asarray([s["constraint"](t,a) for t,a in zip(ts,hist)])
    return {"end":end[:,0],"tangent":end[:,1:],"eta":ts,"constraint":constraint,"max_constraint":float(np.max(abs(constraint))),"nfev":int(sol.nfev)}

def compact_sky(x,m,high=False):
    # all-m ell1..8 rows, one positive m (and factor sqrt2) at each ell.
    a=np.asarray(x,complex);L=int(round(np.sqrt(a.shape[0]+1)))-1
    if (L+1)**2-1!=a.shape[0] or a.shape[1]!=3 or m not in (0,1,2):raise ValueError("invalid sky shape")
    ls=range(max(m,2 if high else 1),L+1)
    return (np.sqrt(2) if m else 1)*a[[l*l-1+l+m for l in ls]].reshape(-1,*a.shape[2:])

def real_shape_map(Z):
    Z=np.asarray(Z,complex)
    return np.vstack((Z.real,Z.imag))

def real_initial_map(Z,m):
    Z=np.asarray(Z,complex)
    if Z.ndim!=2 or m not in (0,1,2):raise ValueError("invalid initial map")
    return real_shape_map(Z) if m==0 else np.block([[Z.real,-Z.imag],[Z.imag,Z.real]])

def unpack_ic(v,m):
    v=np.asarray(v,float)
    if m==0:return v.astype(complex)
    if len(v)%2:raise ValueError("phase mismatch")
    a,b=np.split(v,2);return a+1j*b

def profile(T,S,cutoff):
    T=np.asarray(T,float);S=np.asarray(S,float)
    if T.ndim!=2 or S.ndim!=2 or len(T)!=len(S) or not np.isfinite(T).all() or not np.isfinite(S).all() or not np.isfinite(cutoff) or cutoff<0:raise ValueError("invalid profile")
    U,s,Vh=np.linalg.svd(T,full_matrices=False);r=int(np.sum(s>cutoff));Q=U[:,:r]
    P=Q@Q.T;E=S-Q@(Q.T@S)
    C=-(Vh[:r].T/s[:r])@(Q.T@S) if r else np.zeros((T.shape[1],S.shape[1]))
    return {"P":P,"E":E,"C":C,"singular_values":s,"rank":r,"cutoff":float(cutoff)}
