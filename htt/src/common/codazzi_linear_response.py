"""Independent finite-start scalar/vector anisotropy on balanced VII0/VIIh.

m=0,1. Scalar mean-density history not reconstructed; it decouples from the
first-order shear, anisotropic brightness and velocity equations. Initial
matter coflow matches native BASS, and opacity is the prescribed scalar table.
No native transport or collision code is imported.
"""
import numpy as np
from scipy.special import eval_jacobi,gammaln
from scipy.integrate import solve_ivp

def normalizations(m):
    if m==0:return np.sqrt(4*np.pi/5),np.sqrt(4*np.pi/3)
    if m==1:return -np.sqrt(8*np.pi/15),-np.sqrt(2*np.pi/3)
    raise ValueError("m must be 0 or 1")

def angular_matrices(L,m,h):
    if type(L) is not int or L<2 or m not in (0,1) or h not in (0,2,-2):raise ValueError("unsupported angular sector")
    x,w=np.polynomial.legendre.leggauss(max(32,2*L+4));w*=2*np.pi
    M,N=m,-h;sign=1
    if N>M:
        sign=(-1)**(M-N);M,N=N,M
    elif N< -M:M,N=-N,-M
    al=M-N;be=M+N
    v=[];dv=[]
    for l in range(max(m,abs(h)),L+1):
        j=l-M
        pref=sign*(-1)**(M-N)*np.exp(.5*(gammaln(l+M+1)+gammaln(l-M+1)-gammaln(l+N+1)-gammaln(l-N+1)))*np.sqrt((2*l+1)/(4*np.pi))
        fac=((1-x)/2)**(al/2)*((1+x)/2)**(be/2)
        J=eval_jacobi(j,al,be,x)
        Jd=(j+al+be+1)/2*eval_jacobi(j-1,al+1,be+1,x) if j else np.zeros_like(x)
        v.append(pref*fac*J);dv.append(pref*fac*((N-M*x)*J+(1-x*x)*Jd))
    v=np.asarray(v);dv=np.asarray(dv)
    G=(v*w)@v.T;A=(v*w)@dv.T;MM=(v*(w*x))@v.T
    if np.max(abs(G-np.eye(len(v))))>1e-9 or np.max(abs(A+A.T-2*MM))>1e-9:raise ArithmeticError("Galerkin projection identity")
    return G,A,MM

def split(y,m,L):
    n=L-m+1;p=L-1
    return y[:3],y[3:3+n],y[3+n:3+2*n],y[3+2*n:3+2*n+p],y[3+2*n+p:]

def integrate_sector(anchors,f_nu,f_b,table,c_sigma,k0,a0,m,L,rtol=2e-9,atol=None,max_step=.025):
    tab=np.asarray(table,dtype=float);T=float(anchors["duration"])
    d=float(anchors["dust_fraction"]);lam=float(anchors["omega_lambda_emit"])
    nh=float(anchors["n_h_emit_m3"]);he=float(anchors["h_emit_s"])
    c=float(c_sigma);f=float(f_nu);fb=float(f_b);k0=float(k0);a0=float(a0)
    if atol is None:atol=rtol/100
    if tab.ndim!=2 or tab.shape[1]!=2 or len(tab)<2 or not np.isfinite(tab).all() or tab[0,0]!=0 or abs(tab[-1,0]-T)>1e-11 or np.any(np.diff(tab[:,0])<=0) or np.any(tab[:,1]<0):raise ValueError("invalid complete opacity table")
    if not np.isfinite([T,d,lam,nh,he,c,f,fb,k0,a0,rtol,atol,max_step]).all() or not (T>0 and 0<d<1 and 0<=lam<1 and 0<=f<1 and 0<fb<1 and nh>0 and he>0 and c>0 and lam+a0*a0<1 and rtol>0 and atol>0 and max_step>0):raise ValueError("invalid background")
    f2,g1=normalizations(m);n=L-m+1;p=L-1
    mat=[angular_matrices(L,m,h)[1:] for h in (0,2,-2)]
    m0=(1-lam-a0*a0)*d;r0=(1-lam-a0*a0)*(1-d)
    def coeff(t):
        matter=m0*np.exp(-3*t);r=r0*np.exp(-4*t);K=a0*a0*np.exp(-2*t);H2=matter+r+lam+K
        scale=np.exp(-t)/np.sqrt(H2)
        return (.5*matter+r-lam)/H2,(1-f)*r/H2,f*r/H2,fb*matter/H2,(1-fb)*matter/H2,c*nh*np.exp(-3*t)*np.interp(t,tab[:,0],tab[:,1])/(he*np.sqrt(H2)),k0*scale,a0*scale
    def rhs(t,y):
        (s,b,cold),I,V,Pp,Pm=split(y,m,L)
        q,og,on,ob,oc,rate,k,a=coeff(t)
        L0,Lp,Lm=(a*A+1j*m*k*M for A,M in mat)
        fgam=I[1-m]/(3*g1)
        stress=.4*(og*I[2-m]+on*V[2-m])/f2
        ds=(q-2)*s+stress
        db=-b+rate*og/ob*(fgam-4*b/3)
        dc=-cold
        dI=L0@I-rate*I;dV=L0@V;dPp=Lp@Pp-rate*Pp;dPm=Lm@Pm-rate*Pm
        if m==0:dI[0]+=rate*I[0]
        avg=(Pp[0]+Pm[0])/2
        dI[1-m]+=rate*4*g1*b
        dI[2-m]+=-4*s*f2+rate*(I[2-m]-np.sqrt(6)*avg)/10
        dV[2-m]-=4*s*f2
        gain=rate*(-np.sqrt(6)*I[2-m]/10+.6*avg)
        dPp[0]+=gain;dPm[0]+=gain
        return np.concatenate(([ds,db,dc],dI,dV,dPp,dPm))
    initial=(a0+1j*m*k0/3)/m0
    y0=np.zeros(3+2*n+2*p,complex);y0[:3]=[1,initial,initial]
    sol=solve_ivp(rhs,(0.,T),y0,method="DOP853",rtol=rtol,atol=atol,max_step=max_step,t_eval=tab[:,0])
    if not sol.success or not np.isfinite(sol.y).all() or sol.y.shape!=(len(y0),len(tab)):raise RuntimeError("sector integration: "+sol.message)
    q,og,on,ob,oc,rate,k,a=coeff(sol.t)
    s,b,cold=sol.y[:3];fgam=sol.y[3+1-m]/(3*g1);fnu=sol.y[3+n+1-m]/(3*g1)
    flux=og*fgam+on*fnu+ob*b+oc*cold
    res=flux-(a+1j*m*k/3)*s
    hist=np.column_stack((sol.t,s,b,cold,fgam,fnu,flux,res))
    nodes,w=np.polynomial.legendre.leggauss(12);lo=tab[:-1,0];hi=tab[1:,0]
    pts=(lo+hi)[:,None]/2+(hi-lo)[:,None]*nodes/2
    tau=float(np.sum((hi-lo)/2*(coeff(pts.ravel())[5].reshape(pts.shape)@w)))
    rad_total=.75*(og[-1]*fgam[-1]+on[-1]*fnu[-1])/(og[-1]+on[-1])
    return {"endpoint":sol.y[:,-1],"history":hist,"tau":tau,"nfev":int(sol.nfev),"L":L,"m":m,"k0":k0,"a0":a0,
        "rtol":rtol,"atol":atol,"max_step":max_step,"initial_coflow":initial,
        "host_beta":b[-1],"spectator_beta":cold[-1],"photon_energy_beta":.75*fgam[-1],"total_radiation_beta":rad_total,
        "max_codazzi":float(np.max(abs(res))),"endpoint_codazzi":res[-1]}

def sector_sky(state,m,L,out_lmax=8,frame="normal"):
    if type(L) is not int or type(out_lmax) is not int or not 2<=out_lmax<=L or m not in (0,1):raise ValueError("invalid sector or band")
    y=np.asarray(state,dtype=complex)
    if y.shape!=(3+2*(L-m+1)+2*(L-1),) or not np.isfinite(y).all():raise ValueError("invalid state")
    (_,b,cold),I,V,Pp,Pm=split(y,m,L);_,g1=normalizations(m)
    obs={"normal":0.,"host":b,"spectator":cold,"radiation":I[1-m]/(4*g1)}
    if frame not in obs:raise ValueError("unsupported observer")
    out=np.zeros(((out_lmax+1)**2-1,3),complex)
    for l in range(1,out_lmax+1):
        par=(-1)**l
        z=np.array([par*I[l-m]/4,0j,0j])
        if l==1:z[0]+=g1*obs[frame]
        else:z[1:]=par*np.array([-.5*(Pp[l-2]+Pm[l-2]),-.5j*(Pp[l-2]-Pm[l-2])])/4
        if m==0:
            if np.max(abs(z.imag))>1e-11:raise ArithmeticError("scalar reality")
            out[l*l-1+l]=z.real
        else:
            out[l*l-1+l+m]=z;out[l*l-1+l-m]=(-1)**m*z.conjugate()
    return out
