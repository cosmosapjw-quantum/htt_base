"""Independent first-order finite-start Bianchi I Einstein--Thomson oracle.

Unit initial STF derivative. Time eta=ln(a/a_emit), table-only cold opacity.
State (s,a,b,v): H-normalized shear, intensity coefficient, screen STF
polarization coefficient and collisionless neutrino intensity coefficient.
"""
import numpy as np
from scipy.integrate import solve_ivp

def system_matrix(q,omega_gamma,omega_nu,unused,rate):
    # Fourth argument reserved for no additional source (must be zero).
    if unused!=0:raise ValueError("oracle has no extra source")
    return np.array([[q-2.,.4*omega_gamma,0.,.4*omega_nu],
        [-4.,-.9*rate,-.6*rate,0.],[0.,-.1*rate,-.4*rate,0.],[-4.,0.,0.,0.]])

def integrate_response(anchors,f_nu,table,c_sigma,method="DOP853",rtol=2e-10,atol=2e-12,max_step=.02):
    tab=np.asarray(table,dtype=float);duration=float(anchors["duration"])
    if tab.ndim!=2 or tab.shape[1]!=2 or len(tab)<2 or not np.isfinite(tab).all() or tab[0,0]!=0 or abs(tab[-1,0]-duration)>1e-11 or np.any(np.diff(tab[:,0])<=0) or np.any(tab[:,1]<0):
        raise ValueError("invalid complete ionization table")
    L=float(anchors["omega_lambda_emit"]);d=float(anchors["dust_fraction"]);f=float(f_nu)
    c=float(c_sigma);nh=float(anchors["n_h_emit_m3"]);he=float(anchors["h_emit_s"])
    if not np.isfinite([duration,L,d,f,c,nh,he,rtol,atol,max_step]).all() or not (duration>0 and 0<=L<1 and 0<=d<1 and 0<=f<1 and c>0 and nh>0 and he>0 and rtol>0 and atol>0 and max_step>0):
        raise ValueError("invalid background or integration parameters")
    m0=(1-L)*d;r0=(1-L)*(1-d)
    def coefficients(t):
        m=m0*np.exp(-3*t);r=r0*np.exp(-4*t);h2=m+r+L
        return (.5*m+r-L)/h2,(1-f)*r/h2,f*r/h2,c*nh*np.exp(-3*t)*np.interp(t,tab[:,0],tab[:,1])/(he*np.sqrt(h2))
    def matrix(t):
        q,g,n,k=coefficients(t);return system_matrix(q,g,n,0.,k)
    opts={"rtol":rtol,"atol":atol,"max_step":max_step,"method":method,"t_eval":tab[:,0]}
    if method in ("Radau","BDF"):opts["jac"]=lambda t,y:matrix(t)
    sol=solve_ivp(lambda t,y:matrix(t)@y,(0.,duration),[1.,0.,0.,0.],**opts)
    if not sol.success or not np.isfinite(sol.y).all() or sol.y.shape!=(4,len(tab)):raise RuntimeError("linear solve failed: "+sol.message)
    # Independent Gauss integration across every actual source knot, not a sum
    # over the solver's adaptive time steps.
    nodes,w=np.polynomial.legendre.leggauss(12);lo=tab[:-1,0];hi=tab[1:,0]
    pts=(lo+hi)[:,None]/2+(hi-lo)[:,None]*nodes/2
    rate=coefficients(pts.reshape(-1))[-1].reshape(pts.shape)
    tau=float(np.sum((hi-lo)/2*(rate@w)))
    return {"endpoint":sol.y[:,-1],"history":np.column_stack((sol.t,sol.y.T)),
            "tau":tau,"method":method,"nfev":int(sol.nfev),"rtol":rtol,"atol":atol,"max_step":max_step}

def axial_sky(state,eps,ell_max=8):
    if type(ell_max) is not int or ell_max<2:raise ValueError("invalid ell_max")
    s,a,b,v=np.asarray(state,dtype=float)
    if not np.isfinite([s,a,b,v,eps]).all():raise ValueError("nonfinite linear coefficient")
    out=np.zeros(((ell_max+1)**2-4,3),complex)
    out[2]=eps*np.sqrt(4*np.pi/5)/4*np.array([a,-np.sqrt(6)*b,0.])
    return out
