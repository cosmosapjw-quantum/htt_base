"""Independent bounded C9 for R98 signed Codazzi, transported eigenlines, and sky moments.
Run from repository root: PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B <this-file>.
"""
from pathlib import Path
import hashlib
import json
from itertools import permutations
import numpy as np
from scipy.linalg import eigh
from scipy.spatial.transform import Rotation
from scipy.special import sph_harm_y
from scripts.r98 import bianchi_history as bh
from scripts.r90.sf_attribution import codazzi_stf

out=Path(__file__).resolve().parent
src=out.parent
cross=src/'CROSS_PHY_RESULTS.json'
sky=src/'BIANCHI_HISTORY_RESULTS.json'
code=Path('scripts/r98/cross_phy.py')
inputs=[Path(__file__).resolve(),cross,sky,code,Path('scripts/r90/sf_attribution.py'),Path(bh.__file__)]
def identities():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
before=identities()
prod=json.loads(cross.read_text())
assert before[code.name]==prod['source_sha256']['implementation']

# Build the full structure tensor, use the Levi-Civita connection via Koszul,
# then take -D_j sigma^j_i; no call to the compact R49 divergence routine.
def divergence(S,A,N):
    eps=np.zeros((3,3,3))
    for i,j,k in permutations(range(3)):
        eps[i,j,k]=(1 if (j-i)%3==1 else -1)
    C=np.einsum('ijp,kp->ijk',eps,N)+np.einsum('i,jk->ijk',A,np.eye(3))-np.einsum('j,ik->ijk',A,np.eye(3))
    G=.5*(C-C.transpose(2,0,1)+C.transpose(1,2,0))
    return -np.einsum('jjp,pi->i',G,S)-np.einsum('jip,jp->i',G,S)
E=[np.diag([1,-1,0])/np.sqrt(2),np.diag([1,1,-2])/np.sqrt(6)]
for i,j in [(0,1),(0,2),(1,2)]:
    S=np.zeros((3,3)); S[i,j]=S[j,i]=1/np.sqrt(2); E.append(S)
N=np.diag([0.,3e-4,-12e-4]);support=[]
for scale,r in zip((.99,1.,1.01),prod['PHY05']['near_exception']):
    A=np.array([2e-4*scale,0.,0.])
    M=np.column_stack([-divergence(S,A,N) for S in E])
    transformed=codazzi_stf(tuple(-N.diagonal()),A[0])
    raw=codazzi_stf(tuple(N.diagonal()),A[0])
    v=np.linalg.svd(M,compute_uv=False)
    assert np.array_equal(np.linalg.matrix_rank(M,tol=1e-12),r['rank'])
    assert np.allclose(v,r['singular_values'],atol=1e-17,rtol=0)
    assert np.max(abs(M-transformed))<1e-17 and np.max(abs(M-raw))>1e-3
    support.append({'rank':r['rank'],'same_n_norm_max':float(np.max(abs(raw-M))),'converted_norm_max':float(np.max(abs(transformed-M)))})
# In a parallel-transported orthonormal triad of the geodesic normal, matrices
# at two times share a common frame identification. Projective angle via atan2 is
# stable close to zero. A time-dependent component rotation requires a propagator.
def angles(line,ref):
    return np.rad2deg(np.arctan2(np.linalg.norm(np.cross(line,ref),axis=-1),np.abs(np.sum(line*ref,axis=-1))))
def analysis(S):
    Sn=S/np.linalg.norm(S,axis=(1,2))[:,None,None]
    e,U=zip(*[eigh(q,driver='evd') for q in Sn])
    e=np.stack(e); U=np.stack(U)[:,:,-1]
    return Sn,U,float((e[:,-1]-e[:,-2]).min()),float(angles(U,U[0]).max())
frame=Rotation.from_rotvec([.5,.2,-.7]).as_matrix()
hist={}
for fam,r in prod['PHY06'].items():
    _,tr=bh.background(fam,samples=641); Sn,U,gap,angle=analysis(tr.sigma_ab_grid)
    S=Sn[::4]; u=U[::4]; idx=angles(u,u[0]).argmax()
    rg=angles(u,u[0]).max(); gap_grid=np.min(np.diff(np.linalg.eigvalsh(S)[:,-2:],axis=-1))
    assert abs(rg-r['largest_top_eigenline_angle_degrees'])<3e-6
    assert abs(gap_grid-r['minimum_top_spectral_gap'])<1e-10
    rigid=analysis(frame@S@frame.T)[3]
    assert abs(rigid-rg)<1e-9
    hist[fam]={'161_angle_stable_deg':float(rg),'161_gap':float(gap_grid),'641_angle_deg':angle,'641_gap':gap,'common_frame_rotation_change_deg':float(rigid-rg),'161_archive_angle_error_deg':float(rg-r['largest_top_eigenline_angle_degrees'])}
    if fam=='VII_h':
        # Rotate the basis at the maximizing time so the eigenline there aligns
        # with the initial line, while the basis at the initial slice is fixed.
        ref=u[0]; now=u[idx]*np.sign(u[idx]@ref)
        axis=np.cross(now,ref); turn=Rotation.from_rotvec(np.arctan2(np.linalg.norm(axis),now@ref)*axis/np.linalg.norm(axis)).as_matrix()
        hist[fam]['gauge_example']={'fixed_FW_angle_deg':float(angles(now,ref)),'uncompensated_time_dependent_component_angle_deg':float(angles(turn@now,ref)),'parallel_transporter_compensated_deg':float(angles(turn.T@turn@now,ref))}
# Direct spherical-harmonic sky on a different tensor grid, positive arrival intensity.
x,w=np.polynomial.legendre.leggauss(41); phi=np.arange(86)*2*np.pi/86
th,ph=np.meshgrid(np.arccos(x),phi,indexing='ij')
nh=np.stack((np.sin(th)*np.cos(ph),np.sin(th)*np.sin(ph),np.cos(th)),axis=-1)
name='alm_rows_ell_ascending_entries_m_minus_ell_to_plus_ell_Re_Im'
a=json.loads(sky.read_text())['families']['VI_h']['sky']['T'][name]
delta=sum(complex(*val)*sph_harm_y(l,m,th,ph) for l,row in enumerate(a) for m,val in zip(range(-l,l+1),row))
assert abs(delta.imag).max()<1e-12
weight=(1+delta.real)**4*w[:,None]*(2*np.pi/86)
m=np.einsum('ij,ijk->k',weight,nh)/weight.sum()
S=np.einsum('ij,ijk,ijl->kl',weight,nh,nh)/weight.sum()
ref=prod['PHY02']['conditional_bolometric_sky']['VI_h']
dm=float(np.linalg.norm(m-np.array(ref['m_arrival']))); ds=float(np.linalg.norm(S-np.array(ref['S'])))
assert max(dm,ds)<1e-12
after=identities()
assert before==after
report={'run_status':'completed','inputs_sha256':before,'unchanged_inputs':True,'assertion_tested':'R90 to R49 signed Codazzi in the stated diagonal VI_h axes, arc between top oriented-independent eigenspaces at 161 sample times using the normal Fermi-Walker frame, and reconstructed positive blackbody angular moments for the stored VI_h T sky','PHY05':support,'PHY06':hist,'PHY02':{'independent_VI_h_arrival_first_moment_norm_error':dm,'second_moment_norm_error':ds,'physical_momentum_direction_is_minus_arrival':True},'interpretation':'Two-time angle and commutator use the Fermi-Walker frame along the geodesic normal. In a rotating local frame include the two-time transporter. One-time chi and gaps are independently rotation invariant. 161-node extrema are discrete, do not supply a continuous gap bound, vorticity, or G_F.'}
(out/'CROSS_PHY_C9.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('PHY05','PHY06','PHY02')},indent=2))
