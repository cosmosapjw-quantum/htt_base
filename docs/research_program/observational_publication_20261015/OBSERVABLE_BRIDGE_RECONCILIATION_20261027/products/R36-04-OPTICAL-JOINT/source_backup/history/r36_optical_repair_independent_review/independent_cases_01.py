from pathlib import Path
import sys,json,hashlib,subprocess,os,platform,time
import numpy as np
import scipy
HERE=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_repair_independent_review')
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE=ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT'
CAND=BASE/'repair_01'
sys.path.insert(0,str(CAND))
from optical_joint import *
def clean(v):
    if isinstance(v, dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v, list): return [clean(x) for x in v]
    if isinstance(v, (float,np.floating)) and not np.isfinite(v): return {'nonfinite':str(v)}
    return v
def save(n,v): (HERE/n).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
results=[]
def check(name,o,s,dobs,b,ed=0,dm=None,witness=None):
    args={'o':np.asarray(o).tolist(),'s':np.asarray(s).tolist(),'d_obs':np.asarray(dobs).tolist(),'budget':b,'e_d':ed,'d_max':dm}
    case={'name':name,'inputs':args}
    if witness is not None:
        w=np.asarray(witness); k=KAPPA*lift_matrix(s)
        case['witness']={'d':w.tolist(),'direct_distance':_norm(w-dobs),'physical_norm':_norm(w),'residual_norm':_norm(o-k@w)}
    try:case['observed']=joint_test(o,s,dobs,b,e_d=ed,d_max=dm)
    except Exception as ex: case['exception']={'type':type(ex).__name__,'code':getattr(ex,'code',None),'message':str(ex)}
    results.append(case)
def _norm(x):return float(scipy.linalg.norm(x))
s=np.diag([.001,-.001,0.]);k=KAPPA*lift_matrix(s)
check('recorded_interior',np.zeros(7),s,np.array([.001,0,0]),1e-8,.002,.01,np.zeros(3))
check('recorded_zero_underflow',np.r_[1e-200,np.zeros(6)],np.zeros((3,3)),np.zeros(3),0)
check('recorded_nonzero_underflow',np.r_[1e-200,np.zeros(6)],np.diag([1e-200,-1e-200,0]),np.zeros(3),0)
for ed in (1e-4,1e-6,1e-8,1e-10,1e-12):
    dobs=np.array([.01,0,0]);w=dobs+np.array([ed/2,0,0]);o=k@w
    for budget in (0.,_norm(k@(w-dobs))/2):
        check('narrow_direct_'+str(ed)+'_B'+str(budget),o,s,dobs,budget,ed,.1,w)
for delta in (0.,1e-12,1e-10,1e-8,1e-6):
    target=np.array([1+delta,0,0]);o=k@target
    check('concentric_boundary_'+str(delta),o,s,np.zeros(3),0,1,1,np.array([1,0,0]))
for ed,dm,dobs in [(0.,1.,np.array([1.,0,0])),(1.,0.,np.array([1.,0,0])),(1.,1.,np.array([2.,0,0])),(1.,1.,np.array([2.+1e-10,0,0]))]:
    check('singleton_or_tangent_'+str(ed)+'_'+str(dm)+'_'+str(dobs[0]),k@np.array([3.,0,0]),s,dobs,0,ed,dm)
for scale in (1e-200,1e-300,1e-320):
    check('nonzero_s_scale_'+str(scale),np.r_[scale,np.zeros(6)],np.diag([scale,-scale,0]),np.zeros(3),0)
check('huge_residual_display',np.r_[1e200,np.zeros(6)],np.zeros((3,3)),np.zeros(3),0)
save('INITIAL_COUNTEREXAMPLES.json',results)
print(json.dumps(clean(results),indent=2,allow_nan=False))
