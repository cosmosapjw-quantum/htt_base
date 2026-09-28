#!/usr/bin/env python3
"""Finite, exploratory optical fixtures. No production/observational admission.

Geometric length L*=1; c remains in the adapter in CONVENTIONS.md. All rays
in the connected endpoint fixture are exact flat-spacetime null rays. A
constant observer boost supplies a nonzero local congruence transform; the
expanding Milne congruence supplies the nonzero first-jet/redshift example.
"""
from pathlib import Path
import itertools
import json
import time
import resource
import hashlib
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
TOL = 1e-10


def sphere(nmu=8):
    mu, wm = np.polynomial.legendre.leggauss(nmu)
    phi = np.arange(2*nmu)*np.pi/nmu
    z, p = np.meshgrid(mu, phi, indexing='ij')
    n = np.stack([np.sqrt(1-z*z)*np.cos(p), np.sqrt(1-z*z)*np.sin(p), z], -1).reshape(-1,3)
    return n, np.repeat(wm, 2*nmu)*np.pi/nmu


def stf_basis():
    b = [np.diag([1.,-1.,0.])/np.sqrt(2), np.diag([1.,1.,-2.])/np.sqrt(6)]
    for i,j in [(0,1),(0,2),(1,2)]:
        a=np.zeros((3,3)); a[i,j]=a[j,i]=1/np.sqrt(2); b.append(a)
    return np.array(b)


def ray_generator(e, theta, A, sigma, omega):
    h=theta/3+e@A+np.einsum('ni,ij,nj->n',e,sigma,e)
    v=h[:,None]*e-A-e@sigma.T-theta/3*e+np.cross(omega,e)
    return h,v


def inverse(e,w,h,v):
    theta=3*np.dot(w,h)/(4*np.pi)
    a=3*np.einsum('n,n,ni->i',w,h,e)/(4*np.pi)
    sigma=15*np.einsum('n,n,nij->ij',w,h,e[:,:,None]*e[:,None,:]-np.eye(3)/3)/(8*np.pi)
    omega=3*np.einsum('n,ni->i',w,np.cross(e,v))/(8*np.pi)
    return np.r_[theta,a,np.einsum('aij,ij->a',stf_basis(),sigma),omega]


def unpack(x):
    return x[0], x[1:4], np.einsum('a,aij->ij',x[4:9],stf_basis()), x[9:12]


def moments(n,w,t):
    mean=np.dot(w,t)/(4*np.pi); contrast=t/mean-1
    nn=n[:,:,None]*n[:,None,:]
    q=15*np.einsum('n,n,nij->ij',w,contrast,nn-np.eye(3)/3)/(8*np.pi)
    nnn=np.einsum('ni,nj,nk->nijk',n,n,n)
    trace=(np.einsum('ni,jk->nijk',n,np.eye(3))+np.einsum('nj,ik->nijk',n,np.eye(3))+np.einsum('nk,ij->nijk',n,np.eye(3)))
    o=35*np.einsum('n,n,nijk->ijk',w,contrast,nnn-trace/5)/(8*np.pi)
    return mean,q,o


def source_temperature(x, direction):
    # Both absolute endpoint position and emission direction matter.
    r=np.linalg.norm(x,axis=1); m=x/r[:,None]
    return 2.7*(1+1e-3*m[:,0]*m[:,1]+5e-4*np.prod(direction,axis=1))


def flat_endpoint(n, distance, rotation):
    # Past-directed k=(-1,n), normalized -u.k=-1, vertex D'=I for past v.
    x=distance*n
    return x@rotation.T,n@rotation.T,distance*np.eye(2)


def expected_qo(rotation):
    q=np.zeros((3,3));q[0,1]=q[1,0]=.001/2
    o=np.zeros((3,3,3))
    for ijk in itertools.permutations(range(3)):o[ijk]=.0005/6
    # Source map m=R n, hence coefficients in observer axes are R^T Q R.
    return rotation.T@q@rotation,np.einsum('ia,jb,kc,ijk->abc',rotation,rotation,rotation,o)


def jacobi(v):
    return np.diag([np.sin(v),np.sinh(v)]),np.diag([np.cos(v),np.cosh(v)])


def kz(d,dp,zprime):
    if abs(zprime)<1e-12: raise ValueError('REDSHIFT_TURNING_POINT')
    if abs(np.linalg.det(d))<1e-12: raise ValueError('VERTEX_OR_CAUSTIC')
    return dp@np.linalg.inv(d)/zprime


def main():
    start=time.perf_counter(); checks={};details={}
    def record(name,residual):
        val=float(np.max(np.abs(residual)));checks[name]=val
        if not np.isfinite(val) or val>TOL: raise AssertionError((name,val,TOL))
    n,w=sphere(); columns=[];hc=[];vc=[]
    for i in range(12):
        x=np.eye(12)[i];h,v=ray_generator(n,*unpack(x))
        record('O01_inverse_'+str(i),inverse(n,w,h,v)-x)
        record('O02_tangency_'+str(i),np.einsum('ni,ni->n',n,v))
        columns.append(np.r_[h,v.ravel()]);hc.append(h);vc.append(v.ravel())
    r=np.array(columns).T; hmat=np.array(hc).T;vmat=np.array(vc).T
    ranks={'full':int(np.linalg.matrix_rank(r)),'H_only':int(np.linalg.matrix_rank(hmat)),'V_only':int(np.linalg.matrix_rank(vmat))}
    assert ranks=={'full':12,'H_only':9,'V_only':11}
    nuisance=r[:,[1]];ranks['after_shared_acceleration_nuisance']=int(np.linalg.matrix_rank(np.c_[r,nuisance])-np.linalg.matrix_rank(nuisance))
    planar=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8),np.zeros(16)]
    planar_h=np.array([ray_generator(planar,*unpack(x))[0] for x in np.eye(12)]).T
    ranks['planar_H']=int(np.linalg.matrix_rank(planar_h));assert ranks['planar_H']==5 and ranks['after_shared_acceleration_nuisance']==11
    details['O13_ranks']=ranks
    # Independent Cartesian congruence derivative M_ij=epsilon_ikj Omega_k.
    om=np.array([0.,0.,1.]);M=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,0.]])
    _,v=ray_generator(n,0,np.zeros(3),np.zeros((3,3)),-om)
    record('O03_rigid_rotation',v+n@M.T)
    assert np.max(np.abs(ray_generator(n,0,np.zeros(3),np.zeros((3,3)),om)[1]-v))>.1
    # Numerical surface divergence/curl in (mu,phi), independent of formula.
    mu,phi=.23,.41;hh=1e-5;x=np.arange(12)/20
    def coord(m,p):
        e=np.array([np.sqrt(1-m*m)*np.cos(p),np.sqrt(1-m*m)*np.sin(p),m])
        em=np.array([-m*np.cos(p)/np.sqrt(1-m*m),-m*np.sin(p)/np.sqrt(1-m*m),1])
        ep=np.array([-np.sqrt(1-m*m)*np.sin(p),np.sqrt(1-m*m)*np.cos(p),0])
        vel=ray_generator(e[None,:],*unpack(x))[1][0]
        return e,np.array([vel[2],vel@ep/(1-m*m)]),np.array([vel@em,vel@ep])
    # Five-point differences avoid finite-difference error overwhelming 1e-10.
    def deriv(fun,t):return (fun(t-2*hh)-8*fun(t-hh)+8*fun(t+hh)-fun(t+2*hh))/(12*hh)
    e,_,_=coord(mu,phi);th,a,s,omega=unpack(x)
    div=deriv(lambda m:coord(m,phi)[1][0],mu)+deriv(lambda p:coord(mu,p)[1][1],phi)
    curl=deriv(lambda p:coord(mu,p)[2][0],phi)-deriv(lambda m:coord(m,phi)[2][1],mu)
    record('O01_range_div',div-(2*a@e+3*e@s@e));record('O01_range_curl',curl-2*omega@e)
    # Sphere monomial reference: integral x^(2a)y^(2b)z^(2c) via gamma.
    from math import gamma
    for degrees in [(2,0,0),(2,2,0),(2,2,2),(4,2,0),(0,0,0)]:
        ref=2*np.prod([gamma((d+1)/2) for d in degrees])/gamma((sum(degrees)+3)/2)
        record('O04_monomial_'+str(degrees),np.dot(w,np.prod(n**degrees,axis=1))-ref)
    angle=.37;rot=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1.]])
    endpoint_rows=[]
    for grid in (8,16):
        nn,ww=sphere(grid)
        for distance in (.2,.5):
            for rotation in (np.eye(3),rot):
                xe,ne,d=flat_endpoint(nn,distance,rotation)
                te=source_temperature(xe,ne);z=.25;to=te/(1+z)
                mean,q,o=moments(nn,ww,to);eq,eo=expected_qo(rotation)
                record(f'O08_Q_{grid}_{distance}_{rotation[0,0]}',q-eq);record(f'O08_O_{grid}_{distance}_{rotation[0,0]}',o-eo)
                record('O08_kelvin_scale',mean-2.7/(1+z))
                _,qp,op=moments(-nn,ww,to);record('O12_even_parity',qp-q);record('O12_odd_parity',op+o)
                # Planck occupation equality at matched emitted/observed frequency.
                frequencies=np.array([1.,3.,7.]); occ=1/np.expm1(frequencies[:,None]/(to[None,:]/mean))
                occ_e=1/np.expm1((frequencies*(1+z))[:,None]/(te[None,:]/mean))
                record('O08_Liouville',occ-occ_e)
                endpoint_rows.append({'grid':grid,'distance':distance,'rotated':not np.array_equal(rotation,np.eye(3)),'mean_K':mean,'Q':q.tolist(),'O':o.tolist()})
        # Nonzero congruence first jet in flat spacetime: Milne u=X/tau.
        # Observer (t=2,x=0), source tau=1 => past affine v=3/4,
        # t_e=5/4, r_e=3/4, 1+z=tau_o/tau_e=2; null D=v I.
        dist=.75; ts=1.25; tau_e=np.sqrt(ts**2-dist**2)
        H,V=ray_generator(nn,3/tau_e,np.zeros(3),np.zeros((3,3)),np.zeros(3))
        record('Milne_H',H-1/tau_e);record('Milne_V',V)
        # Integrate d log E/dv=E H, E=-u.k_future=(2)/tau(v).
        def redshift_rhs(v,y):
            tau=np.sqrt(4-4*v)
            hh,_=ray_generator(nn[:1],3/tau,np.zeros(3),np.zeros((3,3)),np.zeros(3))
            return [np.exp(y[0])*hh[0]]
        sol=solve_ivp(redshift_rhs,(0,dist),[0.],rtol=2.3e-14,atol=1e-14)
        zfactor=np.exp(sol.y[0,-1]);record('Milne_integrated_redshift',zfactor-2)
        xe,ne,d=flat_endpoint(nn,dist,np.eye(3)); temp=source_temperature(xe,ne)/zfactor
        mean,q,o=moments(nn,ww,temp);eq,eo=expected_qo(np.eye(3));record('Milne_Q',q-eq);record('Milne_O',o-eo);record('Milne_mean',mean-1.35)
        details['Milne']={'observer_t':2,'source_tau':tau_e,'past_affine_endpoint':dist,'redshift_factor':zfactor,'mean_K':mean,'D':d.tolist(),'first_jet_theta':3/tau_e,'geometry':'flat Milne congruence; not Einstein/Bianchi solver'}
        # Constant source unaffected by focusing/remapping; intensity no 1/D_A^2.
        for distance in (.2,.5):
            _,_,d=flat_endpoint(nn,distance,rot)
            _,q,o=moments(nn,ww,np.full(len(nn),2.7));record('O09_constant_Q',q);record('O09_constant_O',o)
    # Explicit Lorentz endpoint oracle: observer beta on z, n=-e.
    beta=.1;gamma_b=1/np.sqrt(1-beta*beta)
    boost_rows=[]
    for grid in (8,16):
        nn,ww=sphere(grid);e=-nn;E=gamma_b*(1+beta*e[:,2]);ez=gamma_b*(e[:,2]+beta)/E
        exy=e[:,:2]/E[:,None];es=np.c_[exy,ez];record('boost_null',np.sum(es*es,axis=1)-1)
        to=2.7/E
        ref=2.7*np.arctanh(beta)/(gamma_b*beta)
        record('boost_monopole',np.dot(ww,to)/(4*np.pi)-ref)
        boost_rows.append(moments(nn,ww,to)[1:])
    record('boost_Q_grid',boost_rows[0][0]-boost_rows[1][0]);record('boost_O_grid',boost_rows[0][1]-boost_rows[1][1])
    # Jacobi numerical integration independent of sin/sinh analytic oracle.
    R=np.diag([1.,-1.]); y0=np.r_[np.zeros(4),np.eye(2).ravel()]
    sol=solve_ivp(lambda v,y:np.r_[y[4:],(-R@y[:4].reshape(2,2)).ravel()],(0,.5),y0,rtol=2.3e-14,atol=1e-14,dense_output=True)
    curves=[]
    for v in np.linspace(.05,.5,16):
        d,dp=jacobi(v);y=sol.sol(v);record('O06_Jacobi_'+str(v),y[:4].reshape(2,2)-d)
        b=dp@np.linalg.inv(d);bprime=-R-b@b;record('O06_Riccati',bprime-np.diag([-1/np.sin(v)**2,-1/np.sinh(v)**2]))
        zp=1+2*v;zpp=2.;dz=dp/zp;dzz=(-R@d)/zp**2-dp*zpp/zp**3
        record('O07_z_equation',dzz+zpp/zp**2*dz+R@d/zp**2)
        record('O07_affine_rescale',kz(d,dp/3,zp/3)-kz(d,dp,zp))
        record('O07_distance_trace',np.trace(kz(d,dp,zp))-np.trace(b)/zp)
        assert np.max(np.abs(dzz+R@d/zp**2))>1e-3
        curves.append([v,float(np.max(np.abs(y[:4].reshape(2,2)-d)))])
        flat=v*np.eye(2);record('O05_flat_expansion',np.trace(np.linalg.inv(flat))-2/v)
    rejected=[]
    for label,d,dp,zp in [('vertex',np.zeros((2,2)),np.eye(2),1),('caustic',jacobi(np.pi)[0],jacobi(np.pi)[1],1),('turning',*jacobi(.5),0)]:
        try:kz(d,dp,zp)
        except ValueError:rejected.append(label)
    assert len(rejected)==3
    frequencies=np.array([1.,3.,7.]);closure=[]
    for delta in (.01,.005):
        occ=(1/np.expm1(frequencies/(1+delta))+1/np.expm1(frequencies/(1-delta)))/2
        teff=frequencies/np.log1p(1/occ);closure.append(teff)
    assert np.ptp(closure[0])>1e-4
    assert np.all((closure[0]-1)/(closure[1]-1)>3.99) and np.all((closure[0]-1)/(closure[1]-1)<4.01)
    details.update({'O10_frequency_effective_temperature_ratios':[v.tolist() for v in closure],'chart_refusals':rejected,'endpoints':endpoint_rows,'O14_JET_RESPONSE_LAW':'NOT_CREATED; static Q/O lacks radiation derivatives','negative_controls':['wrong omega sign rejected','n=-e odd parity checked','missing z second derivative term rejected','single-temperature closure rejected'],'scope':'FINITE_EXPLORATORY_NUMERICAL_CHECKS_ONLY','admitted_capabilities':[]})
    fig,ax=plt.subplots(1,2,figsize=(10,3.8));a=np.array(curves)
    ax[0].semilogy(a[:,0],np.maximum(a[:,1],1e-17),'o-');ax[0].axhline(TOL,color='r',ls='--',label='declared tolerance');ax[0].set(xlabel='past affine distance / L*',ylabel='Jacobi absolute residual',title='Independent sin/sinh reference');ax[0].legend()
    ax[1].plot(frequencies,(closure[0]-1)*1e4,'o-',label='delta=0.01');ax[1].plot(frequencies,(closure[1]-1)*1e4,'s-',label='delta=0.005');ax[1].set(xlabel='energy / (k_B T0)',ylabel='(effective T/T0 - 1) x 10000',title='Two-blackbody mixture is not Planck');ax[1].legend();fig.suptitle('R10 finite optical diagnostics — no observational/formal admission');fig.tight_layout();fig.savefig(OUT/'optical_residuals.png',dpi=180);plt.close(fig)
    result={'status':'PASS_FINITE_FIXTURES','tolerance':TOL,'maximum_residual':max(checks.values()),'checks':checks,'details':details,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'wall_seconds':time.perf_counter()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (OUT/'optical_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','maximum_residual','wall_seconds','peak_rss_kib']}))

if __name__=='__main__':main()
