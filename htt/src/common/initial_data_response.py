"""Constrained low-multipole initial-data operator for balanced VII0/VIIh.

Batched linear Galerkin system on a fixed isotropic background. Reuses the
independently checked angular matrices and observable conventions of R123/124,
but assembles its own multi-column evolution. No native transport imported.
"""
import numpy as np
from scipy.integrate import solve_ivp
from common.codazzi_linear_response import angular_matrices as av,normalizations,sector_sky
from common.curved_tensor_response import angular_matrices as at,F2,tensor_sky

def build_system(anchors,f_nu,f_b,table,c_sigma,k0,a0,m,L):
    tab=np.asarray(table,dtype=float)
    T=float(anchors["duration"]);dust=float(anchors["dust_fraction"]);lam=float(anchors["omega_lambda_emit"])
    nh=float(anchors["n_h_emit_m3"]);he=float(anchors["h_emit_s"])
    f,fb,c,k0,a0=map(float,(f_nu,f_b,c_sigma,k0,a0))
    if m not in (0,1,2) or type(L) is not int or L<2:raise ValueError("unsupported sector")
    if tab.ndim!=2 or tab.shape[1]!=2 or len(tab)<2 or not np.isfinite(tab).all() or tab[0,0]!=0 or abs(tab[-1,0]-T)>1e-11 or np.any(np.diff(tab[:,0])<=0) or np.any(tab[:,1]<0):raise ValueError("invalid complete opacity table")
    if not np.isfinite([T,dust,lam,nh,he,f,fb,c,k0,a0]).all() or not (T>0 and 0<dust<1 and 0<=lam<1 and 0<f<1 and 0<fb<1 and nh>0 and he>0 and c>0 and lam+a0*a0<1):raise ValueError("invalid background")
    m0=(1-lam-a0*a0)*dust;r0=(1-lam-a0*a0)*(1-dust)
    def coeff(t):
        matter=m0*np.exp(-3*t);r=r0*np.exp(-4*t);K=a0*a0*np.exp(-2*t);h2=matter+r+lam+K
        scale=np.exp(-t)/np.sqrt(h2)
        return (.5*matter+r-lam)/h2,(1-f)*r/h2,f*r/h2,fb*matter/h2,(1-fb)*matter/h2,c*nh*np.exp(-3*t)*np.interp(t,tab[:,0],tab[:,1])/(he*np.sqrt(h2)),k0*scale,a0*scale
    if m<2:
        f2,g1=normalizations(m);n=L-m+1;p=L-1
        mat=[av(L,m,h)[1:] for h in (0,2,-2)]
        labels=["shear","relative_dust","photon_dipole","neutrino_dipole","photon_quadrupole","neutrino_quadrupole","E","B"]
        B=np.zeros((3+2*n+2*p,len(labels)),complex)
        I=slice(3,3+n);V=slice(3+n,3+2*n);Pp=slice(3+2*n,3+2*n+p);Pm=slice(3+2*n+p,3+2*n+2*p)
        i1=3+1-m;i2=3+2-m;v1=3+n+1-m;v2=3+n+2-m;ip=Pp.start;im=Pm.start
        B[0,0]=1;B[1:3,0]=(a0+1j*m*k0/3)/m0
        B[1,1]=1-fb;B[2,1]=-fb
        B[i1,2]=4*g1;B[1:3,2]=-4*(1-f)*r0/(3*m0)
        B[v1,3]=4*g1;B[1:3,3]=-4*f*r0/(3*m0)
        B[i2,4]=4*f2;B[v2,5]=4*f2;B[ip,6]=B[im,6]=-4*f2
        B[ip,7]=4j*f2;B[im,7]=-4j*f2
        def rhs(t,y):
            q,og,on,ob,oc,rate,k,a=coeff(t)
            L0,Lp,Lm=(a*A+1j*m*k*M for A,M in mat)
            z=np.empty_like(y)
            z[0]=(q-2)*y[0]+.4*(og*y[i2]+on*y[v2])/f2
            z[1]=-y[1]+rate*og/ob*(y[i1]/(3*g1)-4*y[1]/3);z[2]=-y[2]
            z[I]=L0@y[I]-rate*y[I];z[V]=L0@y[V]
            z[Pp]=Lp@y[Pp]-rate*y[Pp];z[Pm]=Lm@y[Pm]-rate*y[Pm]
            if m==0:z[3]+=rate*y[3]
            avg=(y[ip]+y[im])/2
            z[i1]+=4*rate*g1*y[1];z[i2]+=-4*f2*y[0]+rate*(y[i2]-np.sqrt(6)*avg)/10
            z[v2]-=4*f2*y[0];gain=rate*(-np.sqrt(6)*y[i2]/10+.6*avg)
            z[ip]+=gain;z[im]+=gain
            return z
        def constraint(t,y):
            q,og,on,ob,oc,rate,k,a=coeff(t)
            return og*y[i1]/(3*g1)+on*y[v1]/(3*g1)+ob*y[1]+oc*y[2]-(a+1j*m*k/3)*y[0]
        def scalar_reality(y):
            if m!=0:return True
            return bool(max(np.max(abs(y[:3+2*n].imag)),np.max(abs(y[Pp]-y[Pm].conjugate())))<1e-12)
    else:
        n=L-1;f2=F2;mat=[at(L,h)[1:] for h in (0,2,-2)]
        labels=["shear","metric","photon_quadrupole","neutrino_quadrupole","E","B"]
        B=np.zeros((2+4*n,len(labels)),complex)
        I=slice(2,2+n);Pp=slice(2+n,2+2*n);Pm=slice(2+2*n,2+3*n);V=slice(2+3*n,2+4*n)
        i2=I.start;v2=V.start;ip=Pp.start;im=Pm.start
        B[0,0]=1;B[1,1]=1;B[i2,2]=4*f2;B[v2,3]=4*f2
        B[ip,4]=B[im,4]=-4*f2;B[ip,5]=4j*f2;B[im,5]=-4j*f2
        def rhs(t,y):
            q,og,on,ob,oc,rate,k,a=coeff(t)
            L0,Lp,Lm=(a*A+2j*k*M for A,M in mat)
            z=np.empty_like(y)
            z[0]=(q-2)*y[0]-2*k*(k-1j*a)*y[1]+.4*(og*y[i2]+on*y[v2])/f2
            z[1]=2*y[0];z[I]=L0@y[I]-rate*y[I];z[V]=L0@y[V]
            z[Pp]=Lp@y[Pp]-rate*y[Pp];z[Pm]=Lm@y[Pm]-rate*y[Pm]
            avg=(y[ip]+y[im])/2
            z[i2]+=-4*f2*y[0]+rate*(y[i2]-np.sqrt(6)*avg)/10
            z[v2]-=4*f2*y[0];gain=rate*(-np.sqrt(6)*y[i2]/10+.6*avg)
            z[ip]+=gain;z[im]+=gain
            return z
        def constraint(t,y):return np.zeros_like(y[0])
        def scalar_reality(y):return True
    if np.max(abs(constraint(0.,B)))>1e-12 or not scalar_reality(B):raise ArithmeticError("invalid typed basis")
    return {"basis":B,"labels":labels,"rhs":rhs,"constraint":constraint,"scalar_reality":scalar_reality,"coeff":coeff,"table":tab,"m":m,"L":L,"k0":k0,"a0":a0}

def integrate_columns(system,initial=None,rtol=2e-9,atol=None,max_step=.025):
    B=system["basis"] if initial is None else np.asarray(initial,dtype=complex)
    if B.ndim!=2 or B.shape[0]!=system["basis"].shape[0] or B.shape[1]<1 or not np.isfinite(B).all():raise ValueError("invalid initial matrix")
    if not system["scalar_reality"](B) or np.max(abs(system["constraint"](0.,B)))>1e-11*(1+np.linalg.norm(B)):raise ValueError("initial data violates linear reality/Codazzi")
    if atol is None:atol=rtol/100
    if not np.isfinite([rtol,atol,max_step]).all() or min(rtol,atol,max_step)<=0:raise ValueError("invalid tolerance")
    shape=B.shape;tab=system["table"]
    sol=solve_ivp(lambda t,y:system["rhs"](t,y.reshape(shape)).ravel(),(0.,tab[-1,0]),B.ravel(),method="DOP853",rtol=rtol,atol=atol,max_step=max_step,t_eval=tab[:,0])
    if not sol.success or not np.isfinite(sol.y).all() or sol.y.shape!=(B.size,len(tab)):raise RuntimeError("batched integration: "+sol.message)
    history=sol.y.reshape((*shape,len(tab))).transpose(2,0,1)
    constraints=np.asarray([system["constraint"](t,y) for t,y in zip(sol.t,history)])
    return {"endpoint":history[-1],"initial":B.copy(),"constraint_history":constraints,"eta":sol.t,"max_constraint":float(np.max(abs(constraints))),"nfev":int(sol.nfev),"rtol":rtol,"atol":atol,"max_step":max_step}

def observe_columns(Y,system,frame="host",out_lmax=8):
    m,L=system["m"],system["L"];Y=np.asarray(Y,dtype=complex)
    if Y.ndim!=2 or Y.shape[0]!=system["basis"].shape[0]:raise ValueError("invalid endpoint")
    if m<2:
        return np.stack([sector_sky(y,m,L,out_lmax,frame) for y in Y.T],axis=-1)
    if frame not in ("normal","host","spectator","radiation"):raise ValueError("invalid observer")
    return np.stack([np.vstack((np.zeros((3,3),complex),tensor_sky(y,L,out_lmax))) for y in Y.T],axis=-1)

def response_matrix(x,m,high=False):
    """Real scalar or complex positive-m operator preserving all-m norm."""
    x=np.asarray(x,dtype=complex)
    if x.ndim!=3 or x.shape[1]!=3 or m not in (0,1,2):raise ValueError("invalid response")
    L=int(round(np.sqrt(x.shape[0]+1)))-1
    if (L+1)**2-1!=x.shape[0]:raise ValueError("invalid all-m band")
    lmin=2 if high else 1
    if m==0:
        y=x[lmin*lmin-1:].reshape(-1,x.shape[-1])
        return np.vstack((y.real,y.imag))
    rows=[x[l*l-1+l+m] for l in range(max(lmin,m),L+1)]
    return np.sqrt(2)*np.asarray(rows).reshape(-1,x.shape[-1])
