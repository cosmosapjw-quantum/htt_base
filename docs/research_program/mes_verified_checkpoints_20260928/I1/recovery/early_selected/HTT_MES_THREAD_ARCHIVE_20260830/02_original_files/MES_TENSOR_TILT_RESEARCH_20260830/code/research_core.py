"""Research reference calculations, not production HTT or observed-data inference.

Metric (-,+,+,+); sky n points outward, photon propagation is -n.
Stored c_l=(a_l0,sqrt(2)Re a_l1,-sqrt(2)Im a_l1,...).
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import permutations
import math
import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm
ETA=np.diag([-1.,1.,1.,1.])

def checked(x:ArrayLike,shape:tuple[int,...]|None=None)->NDArray:
    x=np.asarray(x,dtype=float)
    if shape is not None and x.shape!=shape: raise ValueError(f'expected {shape}, got {x.shape}')
    if not np.isfinite(x).all(): raise ValueError('nonfinite input')
    return x

def stf2(x:ArrayLike)->NDArray:
    x=checked(x,(3,3)); x=(x+x.T)/2
    return x-np.trace(x)*np.eye(3)/3

def stf3(x:ArrayLike)->NDArray:
    x=checked(x,(3,3,3)); x=sum(x.transpose(p) for p in permutations(range(3)))/6
    tr=np.einsum('iik->k',x); e=np.eye(3)
    return x-(np.einsum('ij,k->ijk',e,tr)+np.einsum('ik,j->ijk',e,tr)+np.einsum('jk,i->ijk',e,tr))/5

def mixed_stf3(s,v): return stf3(np.einsum('ij,k->ijk',checked(s,(3,3)),checked(v,(3,))))

def stored_to_unscaled(c):
    c=checked(c)
    if c.ndim!=1 or c.size%2!=1: raise ValueError('odd-length block required')
    a=c.copy(); a[1::2]/=math.sqrt(2); a[2::2]/=-math.sqrt(2)
    return a

def unscaled_to_stored(a):
    a=checked(a)
    if a.ndim!=1 or a.size%2!=1: raise ValueError('odd-length block required')
    c=a.copy(); c[1::2]*=math.sqrt(2); c[2::2]*=-math.sqrt(2)
    return c

def q_from_unscaled(a):
    a0,r1,i1,r2,i2=checked(a,(5,)); aa=math.sqrt(5/(16*math.pi))*a0
    cc=math.sqrt(15/(32*math.pi)); dd=math.sqrt(15/(8*math.pi))
    return np.array([[-aa+2*cc*r2,-2*cc*i2,-dd*r1],[-2*cc*i2,-aa-2*cc*r2,dd*i1],[-dd*r1,dd*i1,2*aa]])

def q_from_stored(c): return q_from_unscaled(stored_to_unscaled(checked(c,(5,))))

def stored_from_q(q):
    q=checked(q,(3,3)); aa=math.sqrt(5/(16*math.pi)); cc=math.sqrt(15/(32*math.pi)); dd=math.sqrt(15/(8*math.pi))
    return unscaled_to_stored([q[2,2]/(2*aa),-q[0,2]/dd,q[1,2]/dd,(q[0,0]-q[1,1])/(4*cc),-q[0,1]/(2*cc)])

def o_from_unscaled(a):
    a0,r1,i1,r2,i2,r3,i3=checked(a,(7,))
    e=math.sqrt(7/(16*math.pi)); f=math.sqrt(21/(64*math.pi)); g=math.sqrt(105/(32*math.pi)); h=math.sqrt(35/(64*math.pi))
    vals={(0,0,0):2*f*r1-2*h*r3,(0,0,1):-2*f*i1/3+2*h*i3,(0,0,2):-e*a0+2*g*r2/3,
          (0,1,1):2*f*r1/3+2*h*r3,(0,1,2):-2*g*i2/3,(1,1,1):-2*f*i1-2*h*i3,(1,1,2):-e*a0-2*g*r2/3}
    vals[(0,2,2)]=-vals[(0,0,0)]-vals[(0,1,1)]; vals[(1,2,2)]=-vals[(0,0,1)]-vals[(1,1,1)]; vals[(2,2,2)]=-vals[(0,0,2)]-vals[(1,1,2)]
    o=np.zeros((3,3,3))
    for inds,value in vals.items():
        for p in set(permutations(inds)): o[p]=value
    return o

def o_from_stored(c): return o_from_unscaled(stored_to_unscaled(checked(c,(7,))))

def tensor_pair_invariants(s,v):
    s=checked(s,(3,3)); v=checked(v,(3,))
    if not np.allclose(s,s.T,atol=1e-12,rtol=0) or abs(np.trace(s))>1e-12: raise ValueError('STF matrix required')
    s2=float(np.trace(s@s)); s3=float(np.trace(s@s@s)); m0=float(v@v); m1=float(v@s@v); m2=float(v@s@s@v)
    m3=s2*m1/2+s3*m0/3; m4=s2*m2/2+s3*m1/3
    eig=np.linalg.eigvalsh(s); kap=float(np.linalg.det(np.column_stack([v,s@v,s@s@v])))
    weights=(m2+eig*m1+(eig**2-s2/2)*m0)/(3*eig**2-s2/2) if np.min(np.diff(eig))>1e-10*max(1.,np.linalg.norm(s)) else None
    return dict(s2=s2,s3=s3,m0=m0,m1=m1,m2=m2,gram=np.array([[m0,m1,m2],[m1,m2,m3],[m2,m3,m4]]),kappa=kap,J=math.sqrt(6)*s3/s2**1.5 if s2>0 else None,spectrum=eig,K_defined=True,component_weights=weights)

def sphere_grid(nmu=24,nphi=48):
    mu,w=np.polynomial.legendre.leggauss(nmu); phi=np.arange(nphi)*2*math.pi/nphi
    mm,pp=np.meshgrid(mu,phi,indexing='ij')
    n=np.stack([np.sqrt(1-mm**2)*np.cos(pp),np.sqrt(1-mm**2)*np.sin(pp),mm],axis=-1).reshape(-1,3)
    return n,np.repeat(w,nphi)*2*math.pi/nphi

def lorentz(beta):
    b=checked(beta,(3,)); b2=float(b@b)
    if b2>=1: raise ValueError('subluminal boost required')
    g=1/math.sqrt(1-b2); jj=np.eye(3)+g*g/(g+1)*np.outer(b,b)
    L=np.zeros((4,4)); L[0,0]=g; L[0,1:]=-g*b; L[1:,0]=-g*b; L[1:,1:]=jj
    return L

def boost_directions(n,beta):
    n=checked(n); p=np.column_stack([np.ones(len(n)),-n])@lorentz(-checked(beta,(3,))).T
    return -p[:,1:]/p[:,0,None],1/p[:,0]

def ideal_temperature(n,B,beta,T_iso=1.):
    B=checked(B,(3,3))
    if not np.allclose(B,B.T,rtol=0,atol=1e-12) or abs(np.trace(B))>1e-12 or T_iso<=0: raise ValueError('STF B and positive T required')
    nr,dop=boost_directions(n,beta)
    return dop*T_iso/np.sqrt(np.einsum('ni,ij,nj->n',nr,expm(2*B),nr))

def quadratic_features(n):
    x,y,z=checked(n).T
    return np.column_stack([np.ones(len(x)),x,y,z,x*x-z*z,y*y-z*z,2*x*y,2*x*z,2*y*z])

@dataclass
class QuadraticInverse:
    beta: NDArray
    B: NDArray
    T_iso: float
    coefficients: NDArray
    relative_fit_residual: float
    gap_eigenvalues: NDArray
    timelike_eigenvalue: float

def invert_ideal_temperature(n,T,weights=None):
    """Exact-model inverse, not a generic CMB shear or tilt estimator."""
    n=checked(n); T=checked(T)
    if n.shape!=(len(T),3) or np.any(T<=0): raise ValueError('positive T and Nx3 directions required')
    if not np.allclose(np.sum(n*n,axis=1),1.,atol=1e-12,rtol=0): raise ValueError('unit directions required')
    f=T**-2; design=quadratic_features(n); w=np.ones(len(f)) if weights is None else checked(weights,(len(f),))
    if np.any(w<=0): raise ValueError('positive weights required')
    rt=np.sqrt(w); coef,_,rank,_=np.linalg.lstsq(design*rt[:,None],f*rt,rcond=None)
    if rank!=9: raise ValueError('quadratic design rank deficient')
    a,b,c,d,e=coef[4:]; F=np.array([[a,c,d],[c,b,e],[d,e,-a-b]])
    A=np.zeros((4,4)); A[0,0]=coef[0]; A[0,1:]=-coef[1:4]/2; A[1:,0]=-coef[1:4]/2; A[1:,1:]=F
    vals,vecs=np.linalg.eig(ETA@A)
    if max(abs(vals.imag).max(),abs(vecs.imag).max())>1e-9: raise ValueError('real type-I eigensystem required')
    vals=vals.real; vecs=vecs.real; norms=np.einsum('ij,ik,kj->j',vecs,ETA,vecs); ids=np.where(norms<-1e-9)[0]
    if len(ids)!=1: raise ValueError('unique timelike eigenvector required')
    i=int(ids[0]); u=vecs[:,i]/math.sqrt(-norms[i]); u*=1 if u[0]>0 else -1; beta=-u[1:]/u[0]
    gaps=np.delete(vals,i)-vals[i]
    if gaps.min()<=0: raise ValueError('positive spatial gaps required')
    L=lorentz(beta); rest=L.T@(A-vals[i]*ETA)@L; M=(rest[1:,1:]+rest[1:,1:].T)/2
    vv,U=np.linalg.eigh(M)
    if vv.min()<=0: raise ValueError('positive rest matrix required')
    logs=np.log(vv); B=U@np.diag((logs-logs.mean())/2)@U.T
    res=float(np.sqrt(np.sum(w*(f-design@coef)**2)/np.sum(w*f*f)))
    return QuadraticInverse(beta,B,float(np.exp(-sum(logs)/6)),coef,res,np.sort(gaps),float(vals[i]))

def mes_amplitude_norm_factor(ell):
    if ell<1: raise ValueError('positive ell required')
    return math.sqrt(math.prod(range(1,2*ell+2,2))/math.factorial(ell))

def mes_scalar_example(C2,C3,T0=2.7255e6):
    e2=math.sqrt(5*C2/(4*math.pi))/T0; e3=math.sqrt(7*C3/(4*math.pi))/T0
    p2=mes_amplitude_norm_factor(2)*e2; p3=mes_amplitude_norm_factor(3)*e3
    os=1.5*(3*e2+3*e3/7)**2; ow=1.5*(2*e2/15)**2; ns=1.5*(3*p2+3*p3/7)**2; nw=1.5*(2*p2/15)**2
    return dict(C2=C2,C3=C3,T0=T0,e2_RMS=e2,e3_RMS=e3,eps2_PSTF=p2,eps3_PSTF=p3,old_Sigma2=os,old_W2=ow,PSTF_Sigma2=ns,PSTF_W2=nw,Sigma2_factor=ns/os,W2_factor=nw/ow,S3_ceiling=ns**1.5/math.sqrt(6))

def generic_qo_orbit_chart(q,o):
    """Generic 9D chart retaining four proper-sign copies; no degenerate-Q chart."""
    q=checked(q,(3,3)); o=checked(o,(3,3,3)); eig,U=np.linalg.eigh(q)
    if np.min(np.diff(eig))<=1e-10*max(1.,np.linalg.norm(q)): raise ValueError('simple Q spectrum required')
    if np.linalg.det(U)<0: U[:,0]*=-1
    local=np.einsum('ia,jb,kc,ijk->abc',U,U,U,o); charts=[]
    for signs in ((1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)):
        d=np.array(signs); charts.append(local*np.einsum('i,j,k->ijk',d,d,d))
    return eig,charts

def counterstream_dust(t_end=3.,momentum=.002,samples=201,rtol=2e-11,atol=1e-15):
    """Einstein Bianchi-I with two equal/opposite conserved dust momenta.

    8*pi*G=c=1, Lambda=0, rho(0)=3. Momentum constraint q_total=0.
    H uses Friedmann; counterstream_raychaudhuri_reference evolves H independently.
    """
    from scipy.integrate import solve_ivp
    if momentum<0: raise ValueError('nonnegative momentum required')
    n0=3/math.sqrt(1+momentum**2); initial=np.array([0.,0.,0.,2e-6,-1.2e-6])
    def state(y):
        sig=np.array([y[3],y[4],-y[3]-y[4]]); num=n0*np.exp(-sum(y[:3])); p=momentum*np.exp(-y[2]); E=math.sqrt(1+p*p)
        rho=num*E; pz=num*p*p/E; pi=np.array([-pz/3,-pz/3,2*pz/3]); H=math.sqrt((rho+sig@sig/2)/3)
        return sig,rho,pz,pi,H,p/E
    def rhs(t,y):
        sig,rho,pz,pi,H,v=state(y); ds=-3*H*sig+pi
        return np.r_[H+sig,ds[:2]]
    sol=solve_ivp(rhs,(0,t_end),initial,t_eval=np.linspace(0,t_end,samples),method='DOP853',rtol=rtol,atol=atol)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[]
    for t,y in zip(sol.t,sol.y.T):
        sig,rho,pz,pi,H,v=state(y); ds=-3*H*sig+pi; i2=sig@sig; i3=sum(sig**3); d2=2*sig@ds; d3=3*(sig*sig)@ds
        J=math.sqrt(6)*i3/i2**1.5; dJ=math.sqrt(6)*(d3/i2**1.5-1.5*i3*d2/i2**2.5)
        rhsJ=3*math.sqrt(6)*pz*(i2*(sig[2]**2-i2/3)-i3*sig[2])/i2**2.5
        rows.append([t,np.mean(y[:3]),H,v,i2,i3,J,dJ,rhsJ,3*H*H-rho-i2/2,d2-(-6*H*i2+2*sig@pi),d3-(-9*H*i3+3*(sig*sig)@pi),*sig])
    return np.asarray(rows),sol.y.T

def counterstream_raychaudhuri_reference(t_end=3.,momentum=.002,samples=201,rtol=2e-11,atol=1e-15):
    from scipy.integrate import solve_ivp
    n0=3/math.sqrt(1+momentum**2); sig0=np.array([2e-6,-1.2e-6,-.8e-6]); H0=math.sqrt((3+sig0@sig0/2)/3)
    def state(y):
        sig=np.array([y[3],y[4],-y[3]-y[4]]); num=n0*np.exp(-sum(y[:3])); p=momentum*np.exp(-y[2]); E=math.sqrt(1+p*p)
        rho=num*E; pz=num*p*p/E
        return sig,rho,pz,np.array([-pz/3,-pz/3,2*pz/3])
    def rhs(t,y):
        sig,rho,pz,pi=state(y); H=y[5]
        return np.r_[H+sig,(-3*H*sig+pi)[:2],-(rho+pz/3+sig@sig)/2]
    sol=solve_ivp(rhs,(0,t_end),np.r_[np.zeros(3),sig0[:2],H0],t_eval=np.linspace(0,t_end,samples),method='DOP853',rtol=rtol,atol=atol)
    if not sol.success: raise RuntimeError(sol.message)
    cons=[]; continuity=[]
    for y in sol.y.T:
        sig,rho,pz,pi=state(y); H=y[5]; cons.append(3*H*H-rho-sig@sig/2)
        continuity.append(-3*H*rho-(H+sig[2])*pz+3*H*(rho+pz/3)+sig@pi)
    return sol.y.T,np.array(cons),np.array(continuity)


def quadrupole_boost_projection(q: ArrayLike, o: ArrayLike):
    """Least-squares projection onto O = 3 STF(beta tensor Q).

    This is an observer-space response projection, NOT an unrestricted physical
    velocity estimator. Intrinsic octupole, boost of l=4, finite-beta and map
    response terms must be separately modelled before physical use.
    """
    q = checked(q, (3, 3)); o = checked(o, (3, 3, 3))
    if not np.allclose(q, stf2(q), atol=1e-12, rtol=0):
        raise ValueError('STF quadrupole required')
    if not np.allclose(o, stf3(o), atol=1e-12, rtol=0):
        raise ValueError('STF octupole required')
    q2 = float(np.sum(q*q))
    if q2 <= 0:
        raise ValueError('nonzero quadrupole required')
    normal = q2*np.eye(3) + (6./5.)*(q@q)
    contraction = np.einsum('abc,bc->a', o, q)
    beta = np.linalg.solve(normal, contraction)
    residual = o - 3*mixed_stf3(q, beta)
    return beta, residual, float(np.linalg.cond(normal))
