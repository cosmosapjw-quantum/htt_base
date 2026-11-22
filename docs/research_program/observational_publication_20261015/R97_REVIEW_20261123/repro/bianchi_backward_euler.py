import numpy as np, scipy, sys
from scipy.sparse import eye
from scipy.sparse.linalg import splu
from scripts.r97 import bianchi_coupled_m_transport as c
vis=c._prepare_physical_visibility_timeline(); v=vis
z=v['z_fwd']; H=v['H_fwd_Mpc']; q=v['tdot_fwd_Mpc']
print('versions',sys.version.split()[0],np.__version__,scipy.__version__,flush=True)
print('Nstep,z0,zf,max_kdt,max_dtau',len(v['d_eta']),z[0],z[-1],.002*np.max(v['d_eta']),np.max(v['d_eta']*(q[1:]+q[:-1])/2),flush=True)
h=c._family_rescaled_trajectory_history('VI_-1/9_exception',z,sigma_amp=5e-5,omega_k=.04)
a=np.array([.04,-.02,.03]); n=np.array([[.05,.03,-.01],[.03,-.02,.04],[-.01,.04,.06]])
print('Na oracle',n@a,'norm',np.linalg.norm(n@a),'relative',np.linalg.norm(n@a)/(np.linalg.norm(a)*np.linalg.norm(n)),'Na physical',h['n']@h['a'],flush=True)
for L, sig, factors in [(16,np.diag([1.,1.,-2.])*5e-5/np.sqrt(6.),[1,2,4,8,16,32]),(60,h['sig'],[1,2,4,8,16,32])]:
 m=(-2,-1,0,1,2); idx,dim=c._mode_index_table(L,m); A,K=c._build_diag_stream_and_thomson(L,m,idx,dim,.002)
 M=c._project_gamma4_to_coupled_m_operators(L,m,idx,dim,sig,h['a'],h['n'])['M_geo_exact']; quad=c.stf_source_harmonics(sig)
 I=eye(dim,dtype=complex,format='csc'); E=list(idx['E'].values()); B=list(idx['B'].values()); T=list(idx['T'].values()); Ts=[i for (l,mu),i in idx['T'].items() if mu]
 for r in factors:
  y=np.zeros(dim,complex)
  for j,dt in enumerate(v['d_eta']):
   zm=(z[j]+z[j+1])/2; hc=(H[j]+H[j+1])/(2*(1+zm)); t=(q[j]+q[j+1])/2; decay=((1+zm)/1100)**(-.25)
   ds=np.zeros(dim,complex)
   for mu in m: ds[idx['T'][(2,mu)]]=-hc*decay*quad[mu]*(dt/r)
   lu=splu(I-(dt/r)*(A+t*K+hc*M))
   for i in range(r): y=lu.solve(y+ds)
  print('L,r,BE,Tscatter,Epower,Bpower',L,r,np.linalg.norm(y[B])/np.linalg.norm(y[E]),np.linalg.norm(y[Ts])**2/np.linalg.norm(y[T])**2,np.linalg.norm(y[E])**2,np.linalg.norm(y[B])**2,flush=True)
