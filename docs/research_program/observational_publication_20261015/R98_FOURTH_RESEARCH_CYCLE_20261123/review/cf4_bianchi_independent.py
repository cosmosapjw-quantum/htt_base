from pathlib import Path
from hashlib import sha256
import json,sys,os,time,platform
import numpy as np
from scipy.integrate import simpson, solve_ivp
from scipy.interpolate import CubicSpline
from scipy.special import sph_harm_y
from astropy.table import Table
from scripts.r98 import cf4_p1 as cf, bianchi_history as bi
from bass.recombination.reionization import SIGMA_T, C_LIGHT
rd=Path('/home/cosmosapjw/Downloads/htt_r98_independent_review')
pub=cf.OUT.parent
root=Path.cwd()
raw=cf.r97.RAW_CF4
paths=[Path(cf.__file__),Path(bi.__file__),cf.OUT,pub/'BIANCHI_HISTORY_RESULTS.json',raw/'table3.dat',raw/'table4.dat',raw/'ReadMe',Path(__file__)]
def digests(): return {str(p):sha256(p.read_bytes()).hexdigest() for p in paths}
initial=digests()
out={'python':sys.version,'numpy':np.__version__,'arch':platform.machine(),'inputs_before':initial,'working_dir':str(root)}
def named(name):
    return Table.read(raw/name,format='ascii.cds',readme=str(raw/'ReadMe'),guess=False)
t=named('table4.dat')
t3=named('table3.dat')
ids=np.asarray(t['1PGC']); sel=(np.asarray(t['V3k'])/299792.458>=.01)&(np.asarray(t['V3k'])/299792.458<=.1)
ind=np.flatnonzero(sel); ind=ind[np.argsort(ids[ind])]
p3=np.argsort(t3['1PGC']); idx=p3[np.searchsorted(np.asarray(t3['1PGC'])[p3],ids[ind])]
ra,dec=np.deg2rad(np.asarray(t['RAdeg'])[ind]),np.deg2rad(np.asarray(t['DEdeg'])[ind])
x,y,z=np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)
X=np.stack((np.ones_like(x),x,y,z,(x*x-y*y)/np.sqrt(2),(x*x+y*y-2*z*z)/np.sqrt(6),np.sqrt(2)*x*y,np.sqrt(2)*x*z,np.sqrt(2)*y*z),axis=1)
tf=lambda f:np.asarray(t[f],dtype=float)[ind]
v,cz,dm,e=tf('fV3k'),tf('V3k'),tf('DMzp'),tf('e_DMzp')
a=np.log(10)/5
s2=(a*e)**2+(250*(1+v/299792.458)/v)**2
b=[]
As=[]
for cen in [.025,.04,.06,.08]:
    w=np.exp(-.5*((cz/299792.458-cen)/.012)**2)/s2
    A=np.linalg.solve(X.T@(w[:,None]*X),X.T*w)
    b.append(A@np.log(v/74.6/10**((dm-25)/5)))
    As.append(A)
As=np.vstack(As)
m=np.column_stack([np.asarray(t3[k].filled(np.inf))[idx] for k in ('e_DMsnIa','e_DMfp','e_DMtf','e_DMsbfo','e_DMsbfi','e_DMsnII')])**-2
mm=m.sum(1);nz=mm>0;W=np.zeros((len(mm),7));W[nz,:6]=m[nz]/mm[nz,None];W[~nz,6]=1
F=np.diag(m.sum(0))-(m[nz]/mm[nz,None]).T@m[nz]
f=json.loads(cf.OUT.read_text())['fit']
cov=(As*s2)@As.T
vfull=np.asarray(t['fV3k'],float); dfull=10**((np.asarray(t['DMzp'])-25.)/5); pos=vfull>0
vpt=vfull[pos]; beta=vpt/(1+vpt/299792.458); ratio=vpt/75/dfull[pos]; arr=np.asarray(t['Vpwf'])[pos]
out['cf4']={'n':len(x),'cov_abs':float(abs(cov-np.array(f['selected_log_covariance_36x36'])).max()),'b_abs':float(abs(np.array(b)-f['selected_log_coefficients_4x9']).max()),'direct_cal_ids':ids[ind][~nz].tolist(),'cross_window_cov_norm':float(np.linalg.norm(cov[:9,9:18])),'response_maxabs':float(abs(-a*As@W-f['J_log_per_mag_36x7']).max()),'fisher_spectrum':np.linalg.eigvalsh(F).tolist(),'log10_release_max_kms':float(max(abs(beta*np.log10(ratio)-arr))),'natural_release_rms_kms':float(np.sqrt(np.mean((beta*np.log(ratio)-arr)**2)))}
q=np.zeros((2,4,2));q[:,:,0]=1;q[0,:,1]=2.**-40;q[1,:,1]=2.**-41
r=cf.finite_slice(q,np.tile([0.,1.],(4,1)),np.ones((2,4)),np.zeros(4),1.,[.5,.5],1.)
out['counterexample']={k:np.asarray(r[k]).tolist() for k in ('nominal','min_mass','max_mass','n_distinct_interior_roots')}
out['counterexample']['exact_all_six']={'nominal':1,'min':0.5,'max':1,'distinct_roots':2}
print('completed CF4',flush=True)
cs,rec=bi.optics()
def riemann_constraint(traj):
    # Koszul in an orthonormal invariant frame, [e_i,e_j]=C^k_ij.
    from itertools import permutations
    eps=np.zeros((3,3,3))
    for i,j,k in permutations(range(3)): eps[i,j,k]=1 if (j-i)%3==1 else -1
    H=traj.H_grid; residuals=[];divs=[]
    eye=np.eye(3)
    for p in range(0,len(H),4):
        A=traj.a_grid[p]; N=traj.n_grid[p]; S=traj.sigma_ab_grid[p]
        com=np.einsum('ijk,lk->ijl',eps,N)+np.einsum('i,jk->ijk',A,eye)-np.einsum('j,ik->ijk',A,eye)
        # Gamma[i,j,k] = <nabla_i e_j,e_k>; cyclic Koszul
        G=.5*(com-com.transpose(2,0,1)+com.transpose(1,2,0))
        # Explicit loops use the defining curvature and divergence contractions.
        R=sum(G[j,j,m]*G[i,m,i]-G[i,j,m]*G[j,m,i]-com[i,j,m]*G[m,j,i] for i in range(3) for j in range(3) for m in range(3))
        D=-np.einsum('jjm,mi->i',G,S)-np.einsum('jim,jm->i',G,S)
        T=np.zeros((4,4));scale=np.linalg.norm(D)
        for sp in traj.species_specs:
            u=np.r_[1.,traj.species_v_grid[sp.species][p]]
            u=u/np.sqrt(1-u[1:]@u[1:])
            rest=traj.species_eps_hat_grid[sp.species][p]; pres=sp.K_eos*rest
            t=(rest+pres)*np.outer(u,u)+pres*np.diag([-1.,1.,1.,1.]);T+=t;scale+=np.linalg.norm(t[0,1:])
        residuals.append(abs(3*H[p]**2+R/2-np.sum(S*S)/2-T[0,0]-traj.lambda_value)/(3*H[p]**2))
        divs.append(np.linalg.norm(D+T[0,1:])/max(scale,1e-250))
    return max(residuals),max(divs)
_,traj=bi.background('VII_h',samples=321);ham,cod=riemann_constraint(traj)
hf=float(cs.H_of_z(bi.Z_INITIAL));op=lambda N,H: C_LIGHT*SIGMA_T*cs.n_H_today*np.exp(-3*N)*rec.query_x_e(np.expm1(-N))/H
fineN=np.linspace(bi.N_INITIAL,0,24001); H=np.exp(CubicSpline(traj.N_grid,np.log(traj.H_grid*hf))(fineN)); tau=simpson(op(fineN,H),x=fineN)
chi=simpson(C_LIGHT*np.exp(-fineN)/H,x=fineN)/3.085677581491367e22
out['VII_h']={'independent_koszul_ham':ham,'independent_koszul_codazzi':cod,'quad_tau':tau,'conformal_Mpc':chi,'quad_tau_vs_archived':float(tau-json.loads((pub/'BIANCHI_HISTORY_RESULTS.json').read_text())['families']['VII_h']['optical_depth_to_initial'])}
print('completed VII_h',flush=True)
# Type I, exact homogeneous collisionless energy with backward blueshift and linear momentum map.
state,traj=bi.background('I',samples=641)
geom,_=bi.background_checks(state,traj)
Sh=CubicSpline(traj.N_grid,traj.sigma_ab_grid/traj.H_grid[:,None,None],axis=0)
fund=solve_ivp(lambda n,q:(-Sh(n)@q.reshape(3,3)).ravel(),(0,bi.N_INITIAL),np.eye(3).ravel(),method='DOP853',rtol=2e-12,atol=1e-15).y[:,-1].reshape(3,3)
ct,w=np.polynomial.legendre.leggauss(18);ph=np.arange(40)*2*np.pi/40
th,phi=np.meshgrid(np.arccos(ct),ph,indexing='ij'); d=np.stack((np.sin(th)*np.cos(phi),np.sin(th)*np.sin(phi),np.cos(th)),axis=-1)
temperature=-np.log(np.linalg.norm(d@fund.T,axis=-1));harm=lambda ell,m:np.conj(sph_harm_y(ell,m,th,phi))
analytic=np.array([np.sum(w[:,None]*2*np.pi/40*temperature*harm(l,m)) for l in range(2,6) for m in range(-l,l+1)])
ang=bi.Angular(5)
checks={}
for ref in [2,4,8]:
    sky,_=bi.evolve(ang,traj,geom,ref,collision=False)
    tt=bi.low_modes(ang,sky,'T')
    checks[str(ref)]=float(np.linalg.norm(tt-analytic)/np.linalg.norm(analytic))
# linear shear response for Thomson quadrupole; dual eigenspaces -1,-0.3; at O(eps) geometry*anisotropy drops out.
hn=np.exp(CubicSpline(traj.N_grid,np.log(traj.H_grid*hf))(fineN)); rate=op(fineN,hn)
from scipy.integrate import cumulative_trapezoid
back=-cumulative_trapezoid(rate[::-1],fineN[::-1],initial=0.)[::-1]
sint=Sh(fineN)
Yints=np.array([np.einsum('ab,abi,abj,ab->ij',np.broadcast_to(w[:,None]*2*np.pi/40,th.shape),d,d,harm(2,m)) for m in range(-2,3)])
src=-np.einsum('nij,mij->nm',sint,Yints)
e1=np.exp(-back); e3=np.exp(-.3*back)
te=[simpson(src*p[:,None],x=fineN,axis=0) for p in [(6*e1+e3)/7,np.sqrt(6)*(e3-e1)/7]]
sky,_=bi.evolve(ang,traj,geom,8)
out['I']={'collisionless_covector_map_error':checks,'analytic_Thomson_relative_quadrupole':{ch:float(np.linalg.norm(np.array([sky[ang.idx[ch][2,m]] for m in range(-2,3)])-e)/np.linalg.norm(e)) for ch,e in zip(['T','E'],te)}}
out['inputs_after']=digests();out['inputs_same']=(initial==out['inputs_after'])
(rd/'review_result.json').write_text(json.dumps(out,indent=2,default=float)+'\n')
print(json.dumps({k:v for k,v in out.items() if k in ['I','VII_h','cf4','counterexample','inputs_same']},indent=2,default=float),flush=True)
