import numpy as np
from scipy.special import sph_harm_y
from scripts.r97 import bianchi_coupled_m_transport as c
from bass.transport.general_bianchi_transfer import gl_sphere_grid, _spherical_screen_basis, _fast_scalar_alm_from_gl, _fast_spin2_alm_from_gl,qu_from_spin2_alm
th,ph,d,w=gl_sphere_grid(18); e,p=_spherical_screen_basis(d); P=np.eye(3)-np.einsum('...i,...j->...ij',d,d)
def outer(a,b): return np.einsum('...i,...j->...ij',a,b)
for jj,ch in enumerate(['T','E','B']):
 T=sph_harm_y(2,0,th,ph).real if ch=='T' else np.zeros_like(th)
 Q,U=qu_from_spin2_alm({(2,0):1} if ch=='E' else {},{(2,0):1} if ch=='B' else {},th,ph,ell_max=4)
 J=.5*(T[...,None,None]*P+Q[...,None,None]*(outer(e,e)-outer(p,p))+U[...,None,None]*(outer(e,p)+outer(p,e)))
 Jbar=np.sum(w[...,None,None]*J,axis=(0,1))
 C=3/(8*np.pi)*(P@Jbar@P)-J
 def project(a,b): return np.einsum('...i,...ij,...j->...',a,C,b)
 t=_fast_scalar_alm_from_gl(np.trace(C,axis1=-2,axis2=-1),18,4)
 E,B=_fast_spin2_alm_from_gl(project(e,e)-project(p,p),project(e,p)+project(p,e),18,4)
 idx,dim=c._mode_index_table(4,(0,)); _,K=c._build_diag_stream_and_thomson(4,(0,),idx,dim,0.)
 print(ch,'direct',np.real([t[2,0],E[2,0],B[2,0]]),'code',K.toarray()[[idx[cc][2,0] for cc in ('T','E','B')],idx[ch][2,0]].real)
