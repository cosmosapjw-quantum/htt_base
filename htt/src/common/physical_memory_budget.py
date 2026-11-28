"""Physical state-size and signed terminal response budgets, balanced VII.

The positive metric is an enthalpy-compatible perturbation-size diagnostic,
not a conserved Hamiltonian, entropy or observational inverse covariance.
Opacity multiplication is an explicit controlled intervention.
"""
import numpy as np
from scipy.integrate import solve_ivp
from common.initial_data_response import build_system
from common.codazzi_linear_response import normalizations

def layout(m,L):
    if m<2:
        n=L-m+1;p=L-1
        I=slice(3,3+n);V=slice(3+n,3+2*n);Pp=slice(3+2*n,3+2*n+p);Pm=slice(3+2*n+p,3+2*n+2*p)
        return I,V,Pp,Pm
    n=L-1
    return slice(2,2+n),slice(2+3*n,2+4*n),slice(2+n,2+2*n),slice(2+2*n,2+3*n)

def build_context(**kwargs):
    system=build_system(**kwargs)
    tab=system["table"];zero_tab=tab.copy();zero_tab[:,1]=0
    zero=build_system(**dict(kwargs,table=zero_tab))
    if not np.array_equal(system["basis"],zero["basis"]):raise ValueError("opacity must not alter the initial basis")
    return {"system":system,"zero":zero,"m":system["m"],"L":system["L"],"layout":layout(system["m"],system["L"])}

def metric_weights(c,t):
    s=c["system"];m=c["m"];I,V,Pp,Pm=c["layout"]
    q,og,on,ob,oc,rate,k,a=s["coeff"](t)
    w=np.empty(s["basis"].shape[0],float);dw=np.zeros_like(w)
    w[0]=.25 if m==0 else 1/3
    if m<2:
        w[1:3]=[ob,oc];dw[1:3]=(2*q-1)*w[1:3]
    else:
        w[1]=k*k/3;dw[1]=2*q*w[1]
    mult=1 if m==0 else 2
    w[I]=mult*og/(16*np.pi);w[V]=mult*on/(16*np.pi)
    w[Pp]=w[Pm]=mult*og/(32*np.pi)
    for sl in (I,V,Pp,Pm):dw[sl]=(2*q-2)*w[sl]
    if np.min(w)<=0 or not np.isfinite(w).all():raise ValueError("degenerate physical metric; tensor twist must be nonzero")
    return w,dw

def collision_action(c,t,y):
    m=c["m"];I,V,Pp,Pm=c["layout"];q,og,on,ob,oc,rate,k,a=c["system"]["coeff"](t)
    z=np.zeros_like(y);z[I]=-rate*y[I];z[Pp]=-rate*y[Pp];z[Pm]=-rate*y[Pm]
    i2=I.start+(2-m if m<2 else 0);ip=Pp.start;im=Pm.start
    avg=(y[ip]+y[im])/2
    z[i2]+=rate*(y[i2]-np.sqrt(6)*avg)/10
    gain=rate*(-np.sqrt(6)*y[i2]/10+.6*avg);z[ip]+=gain;z[im]+=gain
    if m<2:
        _,g1=normalizations(m);i1=I.start+1-m
        z[1]=rate*og/ob*(y[i1]/(3*g1)-4*y[1]/3);z[i1]+=4*rate*g1*y[1]
        if m==0:z[I.start]=0
    return z

def observation(c,frame="host",high=False,Lout=8):
    m,L=c["m"],c["L"];I,V,Pp,Pm=c["layout"]
    if not 2<=Lout<=L or frame not in ("host","normal","radiation","spectator"):raise ValueError("unsupported observer/band")
    ls=list(range(max(2 if high else 1,m),Lout+1));O=np.zeros((3*len(ls),len(c["system"]["basis"])),complex)
    for j,l in enumerate(ls):
        p=(-1)**l;O[3*j,I.start+l-max(m,0)]=p/4
        if l==1:
            _,g1=normalizations(m)
            if frame=="host":O[3*j,1]=g1
            elif frame=="spectator":O[3*j,2]=g1
            elif frame=="radiation":O[3*j,I.start+1-m]+=1/4
        else:
            ip=Pp.start+l-2;im=Pm.start+l-2
            O[3*j+1,ip]=O[3*j+1,im]=-p/8
            O[3*j+2,ip]=-1j*p/8;O[3*j+2,im]=1j*p/8
    if m>0:O*=np.sqrt(2)
    return O

def whiten(M):
    M=np.asarray(M)
    if M.ndim!=2 or M.shape[0]!=M.shape[1] or not np.isfinite(M).all() or not np.allclose(M,M.conj().T,atol=1e-13,rtol=1e-12):raise ValueError("non-Hermitian metric")
    L=np.linalg.cholesky(M)
    return np.linalg.solve(L.conj().T,np.eye(len(M)))

def optical_depth(c,scale):
    tab=c["system"]["table"];nodes,w=np.polynomial.legendre.leggauss(12)
    lo=tab[:-1,0];hi=tab[1:,0];x=(lo+hi)[:,None]/2+(hi-lo)[:,None]*nodes/2
    rate=c["system"]["coeff"](x.ravel())[5].reshape(x.shape)
    return float(scale*np.sum((hi-lo)/2*(rate@w)))

def integrate_budget(c,scale,rtol=2e-10,max_step=.025):
    if not np.isfinite([scale,rtol,max_step]).all() or scale<0 or min(rtol,max_step)<=0:raise ValueError("invalid scale/tolerance")
    s=c["system"];zsys=c["zero"];B=s["basis"];n,p=B.shape;size=n*p;pp=p*p
    def rhs(t,state):
        y=state[:size].reshape(n,p);g=zsys["rhs"](t,y);coll=scale*collision_action(c,t,y);w,dw=metric_weights(c,t)
        q=y.conj().T@(w[:,None]*coll);D=-(q+q.conj().T)
        q=y.conj().T@(w[:,None]*g);N=q+q.conj().T+y.conj().T@(dw[:,None]*y)
        return np.concatenate(((g+coll).ravel(),D.ravel(),N.ravel()))
    tab=s["table"];idx=np.unique(np.r_[np.arange(0,len(tab),16),len(tab)-1]);times=tab[idx,0]
    y0=np.concatenate((B.ravel(),np.zeros(2*pp,complex)))
    sol=solve_ivp(rhs,(0.,tab[-1,0]),y0,method="DOP853",rtol=rtol,atol=rtol/100,max_step=max_step,t_eval=times)
    if not sol.success or not np.isfinite(sol.y).all() or sol.y.shape!=(len(y0),len(times)):raise RuntimeError("budget integration: "+sol.message)
    end=sol.y[:size,-1].reshape(n,p);D=sol.y[size:size+pp,-1].reshape(p,p);N=sol.y[size+pp:,-1].reshape(p,p)
    wi,_=metric_weights(c,0.);wf,_=metric_weights(c,times[-1]);M=B.conj().T@(wi[:,None]*B);J=end.conj().T@(wf[:,None]*end)
    H=whiten(M);den=max(np.linalg.norm(M),np.linalg.norm(J),np.linalg.norm(D),np.linalg.norm(N))
    closure=J-M-N+D
    symerr=max(np.linalg.norm(D-D.conj().T),np.linalg.norm(N-N.conj().T))
    hist=np.asarray([s["constraint"](t,y.reshape(n,p)) for t,y in zip(times,sol.y[:size].T)])
    return {"initial":B,"endpoint":end,"D":D,"N":N,"M":M,"J":J,"wi":wi,"wf":wf,"whitener":H,
        "eta":times,"constraint":hist,"tau":optical_depth(c,scale),"nfev":int(sol.nfev),
        "closure_relative":float(np.linalg.norm(closure)/den),"closure_whitened":float(np.linalg.norm(H.conj().T@closure@H,ord=2)),
        "min_D_eigenvalue":float(np.min(np.linalg.eigvalsh((D+D.conj().T)/2))),"symmetry_error":float(symerr),
        "max_constraint":float(np.max(abs(hist))),"scale":float(scale),"rtol":rtol,"max_step":max_step}

def adjoint_objective(c,scale,weights,rtol=2e-11,widths=(.01,.003),frame="host",high=False):
    s=c["system"];B=s["basis"];v=np.asarray(weights,dtype=complex)
    if v.shape!=(B.shape[1],) or not np.isfinite(v).all() or not s["scalar_reality"]((B@v)[:,None]):raise ValueError("invalid physical initial mixture")
    if scale<=max(widths):raise ValueError("centered FD requires positive nearby scales")
    T=s["table"][-1,0];O=observation(c,frame,high);y0=B@v;n=len(y0)
    def A(t,y,lam):return c["zero"]["rhs"](t,y)+lam*collision_action(c,t,y)
    def forward(lam,dense=False):
        f=solve_ivp(lambda t,y:A(t,y[:,None],lam)[:,0],(0.,T),y0,method="DOP853",rtol=rtol,atol=rtol/100,max_step=.015,dense_output=dense)
        if not f.success or not np.isfinite(f.y).all():raise RuntimeError("forward sensitivity "+f.message)
        z=O@f.y[:,-1]
        return .5*float(np.vdot(z,z).real),f,z
    val,f,z=forward(scale,True);terminal=O.conj().T@z;eye=np.eye(n,dtype=complex)
    def backward(t,u):
        p=u[:n];mat=A(t,eye,scale);cy=collision_action(c,t,f.sol(t)[:,None])[:,0]
        return np.r_[-mat.conj().T@p,-np.vdot(p,cy).real]
    adj=solve_ivp(backward,(T,0.),np.r_[terminal,0j],method="DOP853",rtol=rtol,atol=rtol/100,max_step=.015)
    if not adj.success or not np.isfinite(adj.y).all():raise RuntimeError("adjoint "+adj.message)
    p0=adj.y[:n,-1];grad=float(adj.y[-1,-1].real);duality=float(abs(np.vdot(p0,y0)-np.vdot(z,z))/max(np.vdot(z,z).real,1e-30))
    fd=[]
    for h in widths:
        plus,_,_=forward(scale+h);minus,_,_=forward(scale-h);d=(plus-minus)/(2*h)
        fd.append({"width":h,"value":d,"absolute_error":abs(d-grad),"relative_error":abs(d-grad)/max(abs(grad),1e-30)})
    return {"objective":val,"gradient":grad,"duality_relative":duality,"fd":fd,"p0":p0,"z":z,
            "initial_gradient":B.conj().T@p0,"weights":v,"nfev_forward":int(f.nfev),"nfev_adjoint":int(adj.nfev),"frame":frame,"high":high}
