import hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
from scipy.linalg import null_space
from scipy.stats import ncx2, chi2
repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
p=repo/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-03-PM-HISTORY'
expected='781939c14b1ae7a17f8321d268955cf099d04ede9a0bcfc4c006317d3c137424'
hashof=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert hashof(p/'ARTIFACT_MANIFEST.json')==expected
manifest=json.loads((p/'ARTIFACT_MANIFEST.json').read_text())
checks={}
refs=[]
def verify_refs(x):
    if isinstance(x,dict):
        if all(k in x for k in ('path','sha256','bytes')):
            path=Path(x['path']); assert path.stat().st_size==x['bytes'],str(path)
            assert hashof(path)==x['sha256'],str(path)
            refs.append(str(path))
        for v in x.values():verify_refs(v)
    elif isinstance(x,list):
        for v in x:verify_refs(v)
verify_refs(manifest)
receipt=json.loads(Path(manifest['raw_command_receipt']['path']).read_text());verify_refs(receipt)
contract=Path('/mnt/extdrive/workdir/htt_open_data/r36_pm_history_theory_actual/IMPLEMENTATION_CONTRACT.json')
assert hashof(contract)==manifest['frozen_contract_sha256']
checks['identity']={'candidate_manifest':expected,'distinct_references_verified':len(set(refs)),'source_bindings_verified':len(manifest['source_bindings']),'contract':hashof(contract),'input':manifest['input_identity']}
spec=importlib.util.spec_from_file_location('review_candidate',p/'pm_history.py');pm=importlib.util.module_from_spec(spec);spec.loader.exec_module(pm)
out=pm.build();stored=json.loads((p/'RESULT.json').read_text())
assert out==stored,'in-memory consumer differs from sealed RESULT.json'
checks['consumer_exact_json_values_match']=True
with np.load(pm.STATS,allow_pickle=False) as z:g,b,rows=z['G'],z['b'],int(z['n'])
assert rows==755850 and g.shape==(102,102) and b.shape==(102,)
model=pm.model_module();m,j,_=pm.embedding(model)
q,_=pm.psd_factor(g)
for key,n in [('primary_spin_glide6',pm.spin_glide()),('all97_sensitivity',pm.all97())]:
    block=out['gram'][key];info=np.array(block['profile']['information'])
    aj=j.T@g@j;an=j.T@g@n;nn=n.T@g@n
    schur=aj-an@np.linalg.solve(nn,an.T)
    error=np.linalg.norm(info-schur,2)/np.linalg.norm(aj,2)
    assert error<1e-10,error
    cov=np.array(block['joint']['joint_covariance']);fullcov=np.array(block['joint']['full5_covariance'])
    assert np.linalg.norm(fullcov-cov[:5,:5],2)/np.linalg.norm(fullcov,2)<1e-10
    joint=np.column_stack([j,n]);beta=np.array(block['joint']['joint_gls_coefficients'])
    score=joint.T@b
    score_res=np.linalg.norm(joint.T@g@joint@beta-score)/np.linalg.norm(score)
    assert score_res<1e-10
    assert np.linalg.norm(an)>0
    checks[key]={'schur_relative_error':error,'joint_score_relative_residual':score_res,'rank':block['profile']['rank'],'nuisance_rank':block['profile']['nuisance_rank'],'joint_rank':block['joint']['joint_rank'],'eigenvalues':np.linalg.eigvalsh(info).tolist()}
qa=np.linalg.qr(q@j,mode='reduced')[0];qb=np.linalg.qr(q@pm.spin_glide(),mode='reduced')[0]
cc=np.linalg.svd(qa.T@qb,compute_uv=False)
reported=np.array(out['gram']['primary_spin_glide6']['joint']['canonical_correlations'])
assert np.max(np.abs(cc-reported))<1e-12
checks['canonical_correlation_qr_error']=float(np.max(np.abs(cc-reported)))
# Use independent orthogonal complements, including annihilation relative to original scale.
for name,n,signal in [('free_e2',np.column_stack([pm.spin_glide(),np.eye(102)[:,18:23]]),j),('common_spin',pm.spin_glide(),pm.spin_glide()[:,3:])]:
    z=null_space((q@n).T,rcond=1e-10);projected=z.T@q@signal
    ratio=np.linalg.norm(projected,2)**2/np.linalg.norm(q@signal,2)**2
    assert ratio<1e-20
    checks[name+'_independent_relative_information']=float(ratio)
info=np.array(out['gram']['primary_spin_glide6']['profile']['information'])
rng=np.random.default_rng(27102026)
u=np.linalg.qr(rng.normal(size=(5,5)))[0]
rot=pm.power_frontier(u.T@info@u);orig=out['power_frontier']
assert abs(rot['rho80_best_uasyr']/orig['rho80_best_uasyr']-1)<1e-12
assert abs(rot['rho80_worst_uasyr']/orig['rho80_worst_uasyr']-1)<1e-12
assert abs(ncx2.sf(chi2.ppf(.95,5),5,orig['lambda80'])-.8)<1e-10
rankdef=pm.power_frontier(np.diag([0,1,2,3,4]))
assert rankdef['rank']==4 and rankdef['rho80_worst_uasyr'] is None
checks['power_rotation_root_rank_deficient_controls']=True
for h in out['history_images']:
    k=h['k'];r=np.column_stack([k*np.eye(5),-np.eye(5)])
    ih=np.array(h['information_10x10']);z=np.concatenate([np.eye(5),k*np.eye(5)],axis=0)
    assert np.allclose(ih,r.T@info@r,rtol=1e-12,atol=1e-12)
    assert np.linalg.norm(r@z)<1e-12
    assert np.linalg.norm(ih@z)<1e-10*np.linalg.norm(ih)
checks['history_full10_images_nulls']=True
# Independently evaluate the physical map and preserved sign at actual inverse-second scale.
a=pm.tensor(np.array([3,-2,5,1,-4])*1e-18);dt=1e13;D=pm.C_KMS*dt
near=pm.endpoint_response(-dt*a,np.zeros((3,3)),a,D)
assert np.max(np.abs(near-a))/np.max(np.abs(a))<1e-12
far=pm.endpoint_response(np.zeros((3,3)),pm.tensor(np.array([.1,.2,-.1,0,.3])),a,1e30)
assert np.max(np.abs(far+a))/np.max(np.abs(a))<1e-6
for scale in [1.,1e-18,1e-160,1e-320,np.nextafter(0.,1.)]:
    t=np.diag([scale,-scale,0.]);assert np.array_equal(pm.checked_stf(t),t)
    for defect in [scale*np.eye(3),scale*np.array([[0,1,0],[-1,0,0],[0,0,0]])]:
        try:pm.checked_stf(defect)
        except ValueError:pass
        else:raise AssertionError(('invalid STF accepted',scale))
checks['scale_relative_stf_and_physical_sign_controls']=True
# Bound with D != c Delta_t and nonzero sigma_o; fixed-axis quadratic history.
t=pm.E[1];sig=.03*t;L=.04;dt=.5;c=1
for D in [.2,.5,1.,3.]:
    bs=-dt*sig+.5*L*dt**2*t
    a=pm.endpoint_response(bs,np.zeros((3,3)),sig,D,c=c)
    bound=pm.history_bound(sig,dt,D,L,c=c)
    assert np.linalg.norm(a-sig)<=bound+1e-12
checks['finite_history_bound_nontrivial_distance']=True
assert hashof(p/'ARTIFACT_MANIFEST.json')==expected
checks['python']=sys.version
checks['numpy']=np.__version__
import scipy
checks['scipy']=scipy.__version__
print(json.dumps(checks,indent=2,allow_nan=False))
