"""Fixed-clock nodal opacity tangent and goal adjoint for finite Bianchi modes.

Perturb actual linearly interpolated xe nodes, not a separately interpolated
multiplicative factor. No new ionization history or coupled producer derivative.
"""
import numpy as np
from scipy.integrate import solve_ivp
from common.physical_memory_budget import collision_action,metric_weights,observation

class NodalWindows:
    def __init__(self,table,groups):
        a=np.asarray(table,dtype=float);g=np.asarray(groups)
        if a.ndim!=2 or a.shape[1]!=2 or len(a)<2 or not np.isfinite(a).all() or a[0,0]!=0 or np.any(np.diff(a[:,0])<=0) or np.any(a[:,1]<0):raise ValueError("invalid opacity table")
        if g.shape!=(len(a),) or not np.issubdtype(g.dtype,np.integer) or np.any((g<0)|(g>=5)):raise ValueError("invalid node groups")
        self.table=a.copy();self.groups=g.copy();self.components=a[:,1,None]*np.eye(5)[g]
    def ratios(self,t):
        t=np.asarray(t,dtype=float);x=np.interp(t,self.table[:,0],self.table[:,1])
        y=np.stack([np.interp(t,self.table[:,0],self.components[:,i]) for i in range(5)],axis=-1)
        return np.divide(y,x[...,None],out=np.zeros_like(y),where=x[...,None]>0)
    def perturb(self,alpha):
        a=np.asarray(alpha,dtype=float)
        if a.shape!=(5,) or not np.isfinite(a).all() or np.any(a < -1):raise ValueError("invalid fractional opacity perturbation")
        z=self.table.copy();z[:,1]*=1+a[self.groups]
        return z
    def nodes(self,order):
        if order not in (4,8,12):raise ValueError("unsupported quadrature")
        x,w=np.polynomial.legendre.leggauss(order);u=(1+x)/2;w=w/2
        t=self.table[:,0];dt=np.diff(t)
        return (t[:-1,None]+dt[:,None]*u).ravel(),(dt[:,None]*w).ravel(),np.tile(u,len(dt)),np.repeat(np.arange(len(dt)),order)

def _check(c,w):
    if not np.array_equal(c["system"]["table"],w.table):raise ValueError("window and context opacity mismatch")

def _initial(c,y):
    y=np.asarray(y,dtype=complex);s=c["system"]
    if y.ndim!=2 or y.shape[0]!=len(s["basis"]) or y.shape[1]<1 or not np.isfinite(y).all():raise ValueError("invalid initial state matrix")
    if not s["scalar_reality"](y) or np.max(abs(s["constraint"](0.,y)))>1e-11*(1+np.linalg.norm(y)):raise ValueError("initial state violates reality/Codazzi")
    return y

def _solve(rhs,span,y,rtol,max_step,**kwargs):
    s=solve_ivp(rhs,span,y,method="DOP853",rtol=rtol,atol=rtol/100,max_step=max_step,**kwargs)
    if not s.success or not np.isfinite(s.y).all():raise RuntimeError("opacity response integration: "+s.message)
    return s

def solve_state(c,y,rtol=2e-11,max_step=.015,dense=False):
    y=_initial(c,np.asarray(y)[:,None])[:,0];s=c["system"];T=s["table"][-1,0]
    f=_solve(lambda t,z:s["rhs"](t,z[:,None])[:,0],(0.,T),y,rtol,max_step,dense_output=dense)
    return {"end":f.y[:,-1],"solution":f,"nfev":int(f.nfev)}

def integrate_windows(c,w,initial,rtol=2e-10,max_step=.025):
    _check(c,w);Y0=_initial(c,initial);s=c["system"];n,p=Y0.shape
    z=np.zeros((n,6,p),complex);z[:,0]=Y0
    def rhs(t,flat):
        Y=flat.reshape(n,6,p);dy=s["rhs"](t,Y.reshape(n,-1)).reshape(n,6,p)
        CY=collision_action(c,t,Y[:,0]);dy[:,1:]+=CY[:,None,:]*w.ratios(t)[None,:,None]
        return dy.ravel()
    t=s["table"][:,0];ts=t[np.unique(np.r_[np.arange(0,len(t),16),len(t)-1])]
    sol=_solve(rhs,(0.,t[-1]),z.ravel(),rtol,max_step,t_eval=ts)
    E=sol.y[:,-1].reshape(n,6,p);history=sol.y.T.reshape(len(ts),n,6*p)
    constraint=np.asarray([s["constraint"](t,y) for t,y in zip(ts,history)])
    q,wt,_,_=w.nodes(12);rate=s["coeff"](q)[5]
    tau=np.sum((wt*rate)[:,None]*w.ratios(q),axis=0)
    return {"end":E[:,0],"tangent":E[:,1:].transpose(1,0,2),"initial":Y0,"tau":tau,"eta":ts,"constraint":constraint,
        "max_constraint":float(np.max(abs(constraint))),"nfev":int(sol.nfev),"rtol":rtol,"max_step":max_step}

def goal_kernel(c,w,y,rtol=2e-11,max_step=.015):
    _check(c,w);s=c["system"];y=_initial(c,np.asarray(y)[:,None])[:,0];n=len(y);T=w.table[-1,0]
    f=solve_state(c,y,rtol,max_step,True);O=observation(c,"host");z=O@f["end"]
    term=np.column_stack([O[i::3].conj().T@z[i::3] for i in range(3)])
    eye=np.eye(n,dtype=complex)
    def back(t,p):return (-s["rhs"](t,eye).conj().T@p.reshape(n,3)).ravel()
    a=_solve(back,(T,0.),term.ravel(),rtol,max_step,dense_output=True)
    wi,_=metric_weights(c,0.);size=float(np.vdot(y,wi*y).real)
    if size<=0:raise ValueError("zero initial physical size")
    def quad(order):
        t,weights,u,idx=w.nodes(order);nnode=len(w.table);kg=np.zeros((3,nnode));mass=np.zeros((3,5));loss=np.zeros(5);tau=np.zeros(5)
        for start in range(0,len(t),256):
            sl=slice(start,min(start+256,len(t)));tt=t[sl];ww=weights[sl];uu=u[sl];jj=idx[sl]
            yy=f["solution"].sol(tt).T;pp=a.sol(tt).T.reshape(len(tt),n,3)
            cy=np.stack([collision_action(c,t0,v[:,None])[:,0] for t0,v in zip(tt,yy)])
            K=np.einsum("tni,tn->ti",pp.conj(),cy).real
            W=np.stack([metric_weights(c,t0)[0] for t0 in tt]);D=-2*np.sum((yy.conj()*W*cy).real,axis=1)/size
            xe=np.interp(tt,w.table[:,0],w.table[:,1]);x0=w.table[jj,1];x1=w.table[jj+1,1]
            r0=np.divide((1-uu)*x0,xe,out=np.zeros_like(xe),where=xe>0);r1=np.divide(uu*x1,xe,out=np.zeros_like(xe),where=xe>0)
            for k in range(3):
                np.add.at(kg[k],jj,ww*r0*K[:,k]);np.add.at(kg[k],jj+1,ww*r1*K[:,k])
            ratios=w.ratios(tt);mass+=abs(K).T@(ww[:,None]*ratios)
            loss+=D@(ww[:,None]*ratios);tau+=s["coeff"](tt)[5]@(ww[:,None]*ratios)
        group=np.stack([kg[:,w.groups==j].sum(axis=1) for j in range(5)],axis=1)
        return kg,group,mass,loss,tau
    kg,g,mass,loss,tau=quad(8);k4,g4,m4,d4,t4=quad(4)
    p0=a.y[:,-1].reshape(n,3)
    pair=np.real(p0.conj().T@y);norms=np.array([np.vdot(z[i::3],z[i::3]).real for i in range(3)])
    return {"end":f["end"],"z":z,"initial":y,"p0":p0,"knot_gradient":kg,"group_gradient":g,"absolute_mass":mass,"loss":loss,"tau":tau,
        "initial_size":size,"objective":norms/2,"duality_abs":float(np.max(abs(pair-norms))),
        "quadrature_group_abs":float(np.max(abs(g-g4))),"quadrature_knot_l1":float(np.max(np.sum(abs(kg-k4),axis=1))),
        "quadrature_loss_abs":float(np.max(abs(loss-d4))),"nfev_forward":f["nfev"],"nfev_adjoint":int(a.nfev),"rtol":rtol,"max_step":max_step}
