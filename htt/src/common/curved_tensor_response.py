"""Independent finite-start linear balanced VII0/VIIh tensor-sector response.

Only m=+/-2, no linear tilt, Fermi frame, prescribed scalar xe. All brightness
coefficients normalized by mean intensity; observer T,E,B divide by four.
No native BASS transport matrix or Wigner recurrence is imported.
"""
import numpy as np
from scipy.special import eval_jacobi,gammaln
from scipy.integrate import solve_ivp

F2=2/(np.sqrt(6)*np.sqrt(5/(4*np.pi)))

def angular_matrices(L,h):
    if type(L) is not int or L<2 or h not in (0,2,-2):
        raise ValueError("unsupported tensor spin sector")
    x,w=np.polynomial.legendre.leggauss(max(32,2*L+4));w*=2*np.pi
    n=-h;al=2-n;be=2+n
    v=[];der=[]
    for l in range(2,L+1):
        j=l-2
        pref=np.exp(.5*(gammaln(l+3)+gammaln(l-1)-gammaln(l+n+1)-gammaln(l-n+1)))*np.sqrt((2*l+1)/(4*np.pi))
        f=((1-x)/2)**(al/2)*((1+x)/2)**(be/2)
        z=eval_jacobi(j,al,be,x)
        dz=(j+al+be+1)/2*eval_jacobi(j-1,al+1,be+1,x) if j else np.zeros_like(x)
        v.append(pref*f*z)
        der.append(pref*f*((n-2*x)*z+(1-x*x)*dz))
    v=np.asarray(v);der=np.asarray(der)
    gram=(v*w)@v.T;A=(v*w)@der.T;M=(v*(w*x))@v.T
    if np.max(abs(gram-np.eye(L-1)))>1e-9 or np.max(abs(A+A.T-2*M))>1e-9:
        raise ArithmeticError("angular projection invariant")
    return gram,A,M

def integrate_tensor(anchors,f_nu,table,c_sigma,k0,a0,L,rtol=2e-9,atol=None,max_step=.03):
    tab=np.asarray(table,dtype=float)
    T=float(anchors["duration"]);d0=float(anchors["dust_fraction"]);lam=float(anchors["omega_lambda_emit"])
    nh=float(anchors["n_h_emit_m3"]);he=float(anchors["h_emit_s"]);c=float(c_sigma)
    f=float(f_nu);k0=float(k0);a0=float(a0)
    if atol is None:atol=rtol/100
    if tab.ndim!=2 or tab.shape[1]!=2 or len(tab)<2 or not np.isfinite(tab).all() or tab[0,0]!=0 or abs(tab[-1,0]-T)>1e-11 or np.any(np.diff(tab[:,0])<=0) or np.any(tab[:,1]<0):
        raise ValueError("invalid complete opacity table")
    if not np.isfinite([T,d0,lam,nh,he,c,f,k0,a0,rtol,atol,max_step]).all() or not (T>0 and 0<=d0<1 and 0<=lam<1 and 0<=f<1 and nh>0 and he>0 and c>0 and lam+a0*a0<1 and rtol>0 and atol>0 and max_step>0):
        raise ValueError("invalid background or integration parameters")
    n=L-1;mat=[angular_matrices(L,h)[1:] for h in (0,2,-2)]
    m0=(1-lam-a0*a0)*d0;r0=(1-lam-a0*a0)*(1-d0)
    def coeff(t):
        m=m0*np.exp(-3*t);r=r0*np.exp(-4*t);K=a0*a0*np.exp(-2*t)
        h2=m+r+lam+K;H=np.sqrt(h2);scale=np.exp(-t)/H
        return (.5*m+r-lam)/h2,(1-f)*r/h2,f*r/h2,c*nh*np.exp(-3*t)*np.interp(t,tab[:,0],tab[:,1])/(he*H),k0*scale,a0*scale
    def rhs(t,y):
        s,d=y[:2];I,Pp,Pm,V=y[2:].reshape(4,n)
        q,og,on,rate,k,a=coeff(t)
        L0,Lp,Lm=(a*A+2j*k*M for A,M in mat)
        avg=.5*(Pp[0]+Pm[0])
        ds=(q-2)*s-2*k*(k-1j*a)*d+.4*(og*I[0]+on*V[0])/F2
        dI=L0@I-rate*I;dPp=Lp@Pp-rate*Pp;dPm=Lm@Pm-rate*Pm;dV=L0@V
        dI[0]+=-4*s*F2+rate*(I[0]/10-np.sqrt(6)*avg/10)
        gain=rate*(-np.sqrt(6)*I[0]/10+.6*avg)
        dPp[0]+=gain;dPm[0]+=gain;dV[0]-=4*s*F2
        return np.concatenate(([ds,2*s],dI,dPp,dPm,dV))
    init=np.zeros(2+4*n,complex);init[0]=1
    sol=solve_ivp(rhs,(0.,T),init,method="DOP853",rtol=rtol,atol=atol,max_step=max_step,t_eval=tab[:,0])
    if not sol.success or not np.isfinite(sol.y).all() or sol.y.shape!=(len(init),len(tab)):raise RuntimeError("tensor integration: "+sol.message)
    nodes,w=np.polynomial.legendre.leggauss(12);lo=tab[:-1,0];hi=tab[1:,0]
    pts=(lo+hi)[:,None]/2+(hi-lo)[:,None]*nodes/2
    rates=coeff(pts.ravel())[3].reshape(pts.shape)
    tau=float(np.sum((hi-lo)/2*(rates@w)))
    return {"endpoint":sol.y[:,-1],"history":np.column_stack((sol.t,sol.y[:2].T)),
            "tau":tau,"nfev":int(sol.nfev),"L":L,"rtol":rtol,"atol":atol,"max_step":max_step,
            "k0":k0,"a0":a0,"background_end":dict(zip(("q","omega_gamma","omega_nu","rate","k","a"),map(float,coeff(T))))}

def tensor_sky(state,L,out_lmax=8):
    if type(L) is not int or type(out_lmax) is not int or not 2<=out_lmax<=L:
        raise ValueError("invalid output band")
    y=np.asarray(state,dtype=complex)
    if y.shape!=(2+4*(L-1),) or not np.isfinite(y).all():raise ValueError("invalid tensor state")
    I,Pp,Pm,V=y[2:].reshape(4,L-1)
    out=np.zeros(((out_lmax+1)**2-4,3),complex)
    for l in range(2,out_lmax+1):
        j=l-2;par=(-1)**l
        z=par*np.array([I[j],-.5*(Pp[j]+Pm[j]),-.5j*(Pp[j]-Pm[j])])/4
        out[l*l-4+l+2]=z
        out[l*l-4+l-2]=z.conjugate()
    return out
