"""Fresh targeted H03 repair review; writes only to this external directory."""
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import scipy
from scipy.linalg import null_space
from scipy.optimize import brentq
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = REPO / 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
OLD = BASE / 'products/R32-03-H03-STRUCTURED'
NEW = OLD / 'repair_01'
EXPECTED = '4a31b981231a10b449bee2b7be65d0efc181dbd077f35ea55cb23ac38caf4c9d'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def dump(p, value):
    Path(p).write_text(json.dumps(value, indent=2) + '\n')

out = {'candidate_identity': 'sha256:' + EXPECTED,
       'requested_model': 'gpt-6-astra', 'requested_effort': 'xhigh',
       'observed_runtime': 'UNKNOWN', 'formal_review_packet': 'PENDING',
       'environment': {'python': sys.executable, 'python_version': platform.python_version(),
                       'numpy': np.__version__, 'scipy': scipy.__version__}}
assert sha(NEW / 'ARTIFACT_MANIFEST.json') == EXPECTED
manifest = read(NEW / 'ARTIFACT_MANIFEST.json')
out['input_identity'] = manifest['input_identity']
out['binding'] = []
for folder in (OLD, NEW):
    man = read(folder / 'ARTIFACT_MANIFEST.json')
    for item in man['artifacts']:
        path = folder / item['path']
        actual = sha(path)
        assert actual == item['sha256'], str(path)
        if 'bytes' in item:
            assert path.stat().st_size == item['bytes']
        out['binding'].append({'path': str(path), 'sha256': actual})
for item in manifest['source_identities']:
    actual = sha(item['path'])
    assert actual == item['sha256'], item['path']
    out['binding'].append({'path': item['path'], 'sha256': actual})

spec = importlib.util.spec_from_file_location('h03_reviewed_consumer', NEW / 'consumer.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
# Keep the exact loaded source and inputs; redirect only its output root.
mod.HERE = HERE / 'consumer_output'
start = time.monotonic()
with (HERE / 'raw/consumer.stdout').open('w') as f, (HERE / 'raw/consumer.stderr').open('w') as g:
    with contextlib.redirect_stdout(f), contextlib.redirect_stderr(g):
        mod.main()
out['consumer_seconds'] = time.monotonic() - start
saved_old, saved_new, actual = [read(p / 'generated/analysis.json') for p in (OLD, NEW, mod.HERE)]
out['consumer_equalities'] = {}
for name, rec in actual['designs'].items():
    diffs = {}
    for comparison, target in [('original', saved_old), ('repaired', saved_new)]:
        tar = target['designs'][name]
        assert rec['rank_B'] == tar['rank_B']
        assert rec['status'] == tar['status']
        ds = {}
        for field in ('T_floor', 'rho_sat', 'rho95', 'q_min_restricted', 'lambda95'):
            a, b = rec[field], tar[field]
            if b is None:
                assert a is None
                ds[field] = None
            else:
                ds[field] = abs(a-b)
                assert abs(a-b) <= 1e-10 * max(1, abs(b))
        for field in ('rho', 'T_min'):
            delta = np.max(np.abs(np.array(rec['curve'][field])-np.array(tar['curve'][field])))
            assert delta <= 1e-10
            ds['curve_' + field + '_max_abs_error'] = float(delta)
        diffs[comparison] = ds
    out['consumer_equalities'][name] = diffs
out['consumer_curve_point_count'] = sum(len(v['curve']['T_min']) for v in actual['designs'].values())
assert out['consumer_curve_point_count'] == 363

# Independently reconstruct the full dipole marginal and use symmetric whitening
# plus a 6D left-null basis rather than the author's Cholesky/12D projector route.
source = read(BASE / 'evidence/sources/H03_SOURCE_TOMOGRAPHY.json')
wins = source['monopole_dipole_STF2_windows']
indices = [9*w+k for w in range(4) for k in (1,2,3)]
C = np.asarray(source['joint_covariance_36x36'])[np.ix_(indices, indices)]
y = np.concatenate([np.asarray(w['theta9'])[1:4] for w in wins])
R = np.vstack([np.asarray(w['bulk_velocity_design_response_9x3_per_Mpc'])[1:4] for w in wins])
X = np.column_stack([R, np.tile(np.eye(3), (4, 1))])
carrier = read(NEW / 'generated/source_carrier.json')
assert np.array_equal(C, np.asarray(carrier['C_dipole_12x12']))
assert np.array_equal(y, np.asarray(carrier['y_signed_12_km_s_Mpc']))
assert np.array_equal(X, np.asarray(carrier['X_12x6']))
assert sha(OLD / 'generated/source_carrier.json') == sha(NEW / 'generated/source_carrier.json')
ev, V = np.linalg.eigh(C)
assert ev.min() > 0
W = (V * ev**-0.5) @ V.T
N = null_space((W @ X).T)
assert N.shape == (12, 6)
z = N.T @ W @ y
T0 = float(z @ z)
tau = float(chi2.ppf(.95,6))
assert abs(T0 - actual['T0']) < 1e-9
assert abs(tau - 12.591587243743977) < 1e-12
cross = C.copy()
for i in range(4):
    cross[3*i:3*i+3, 3*i:3*i+3] = 0
out['source_reconstruction'] = {'C_marginal_exact': True, 'y_exact': True, 'X_exact': True,
    'all_off_diagonal_entries_retained': True, 'cross_window_nonzero_count': int(np.count_nonzero(cross)),
    'min_C_eigenvalue': float(ev.min()), 'T0_independent': T0, 'tau': tau,
    'null_basis_shape': list(N.shape), 'frozen_carrier_byte_identical': True}
zcent = np.asarray([w['z_center'] for w in wins])
p = np.asarray([w['source_method_distance_weight_fractions']['FP'] for w in wins])
Dz = np.kron(((zcent-.04)/source['width_z'])[:,None], np.eye(3))
Df = np.kron((p-p[0])[:,None], np.eye(3))
designs = {'depth_slope': Dz, 'FP_composition': Df, 'joint': np.column_stack([Dz,Df])}
out['independent_designs'] = {}
for name, D in designs.items():
    J = N.T @ W @ D
    # Solve normal equations in coefficient coordinates, independently of SVD formulas.
    G = J.T @ J
    rhs = J.T @ z
    eta_sat = np.linalg.solve(G, rhs)
    floor = float(np.linalg.norm(z-J @ eta_sat)**2)
    sat = float(np.linalg.norm(eta_sat))
    s = np.linalg.svd(J, compute_uv=False)
    rank = int(np.sum(s/s.max() >= 1e-10))
    def eta_lam(lam):
        return np.linalg.solve(G + lam*np.eye(len(rhs)), rhs)
    def target_T(lam):
        return float(np.linalg.norm(z-J @ eta_lam(lam))**2)
    def root(fn):
        hi=1.
        while fn(hi) <= 0:
            hi*=2
        return brentq(fn,0.,hi,xtol=1e-13,rtol=9e-16)
    curve=[]
    rec=actual['designs'][name]
    for rho in rec['curve']['rho']:
        if rho == 0:
            val = T0
        elif rho >= sat:
            val = floor
        else:
            lam=root(lambda x: rho - np.linalg.norm(eta_lam(x)))
            val=target_T(lam)
        curve.append(val)
    err=float(np.max(np.abs(np.asarray(curve)-rec['curve']['T_min'])))
    assert err < 1e-8
    assert abs(floor-rec['T_floor']) < 1e-8
    assert rank == rec['rank_B']
    rho=None
    direct_refit=None
    if floor < tau:
        lam=root(lambda x: target_T(x)-tau)
        eta=eta_lam(lam)
        rho=float(np.linalg.norm(eta))
        assert abs(rho-rec['rho95']) < 1e-10*max(1,abs(rho))
        b=np.linalg.lstsq(W @ X,W @ (y-D @ eta),rcond=None)[0]
        direct_refit=float(np.linalg.norm(W @ (y-D @ eta-X @ b))**2)
        assert abs(direct_refit-tau) < 1e-8
    out['independent_designs'][name]={'rank':rank,'floor':floor,'rho95':rho,
        'rho_sat':sat,'curve_max_abs_error':err,'direct_refit_T':direct_refit,
        'unprojected_norm':float(np.linalg.norm(W @ D,2)),
        'minimum_projected_global_ratio':float(s.min()/np.linalg.norm(W @ D,2))}

# Exact zero-response identity through the actual repaired analysis function.
L=np.linalg.cholesky(C)
A=mod.solve_triangular(L,X,lower=True)
Q,_=np.linalg.qr(A,mode='reduced')
P=np.eye(12)-Q @ Q.T
r=P @ mod.solve_triangular(L,y,lower=True)
t0=float(r @ r)
zero=mod.analyse('review_D_equals_X',X,y,C,L,X,A,Q,P,r,t0,tau,known_projected_zero=True)
assert zero['rank_B'] == 0 and zero['rho_sat'] == 0
assert zero['rho95'] is None and zero['q_min_restricted'] is None
assert np.max(np.abs(np.asarray(zero['curve']['T_min'])-t0)) == 0
zd=mod.svd_data(P @ A,A,r,known_projected_zero=True)
large_values=[mod.curve_at_rho(rho,zd[2],zd[4],zd[6],zd[7],t0)[0] for rho in (0.,1.,10.,1e100)]
assert all(v==t0 for v in large_values)
try:
    mod.analyse('review_unqualified_zero',X,y,C,L,X,A,Q,P,r,t0,tau)
    raise AssertionError('unqualified projected roundoff was admitted')
except ValueError as exc:
    assert str(exc) == 'NUMERIC_RANK_HOLD'
out['D_equals_X']={'rank':zero['rank_B'],'rho95':None,'q_min':None,
    'floor':zero['T_floor'],'T0':t0,'curve_constant':True,
    'tested_rho':[0.,1.,10.,1e100],'T_at_tested_rho':large_values,
    'projected_frobenius_norm':float(np.linalg.norm(P @ A)),
    'global_reference':float(np.linalg.norm(A,2)),
    'without_structural_identity':'NUMERIC_RANK_HOLD'}

# Guard samples distinguish structural nulls, unresolved small response, and resolved signal.
out['rank_guard_samples']=[]
for scale in (1e-14, 1e-12, 5e-11, 1e-10, 2e-10):
    try:
        rr=mod.svd_data(scale*np.eye(2),np.eye(2),np.ones(2))[-1]
        status='RESOLVED'
        assert scale>=1e-10 and rr==2
    except ValueError as exc:
        status=str(exc); rr=None
        assert scale<1e-10 and status=='NUMERIC_RANK_HOLD'
    out['rank_guard_samples'].append({'ratio':scale,'status':status,'rank':rr})

# Analytic 2D fixture: B=(1,0)^T, r=(1,sqrt(floor)); exact rho=q=1 at floor=tau.
out['boundary_samples']=[]
for offset, exact, expected in [(0.,True,'FINITE_FLOOR_EQUALITY'),(0.,False,'NUMERIC_BOUNDARY_FLOOR'),
    (5e-10,False,'NUMERIC_BOUNDARY_FLOOR'),(-5e-10,False,'NUMERIC_BOUNDARY_FLOOR'),
    (.25,False,'THRESHOLD_UNATTAINABLE_FOR_THIS_D'),(-.25,False,'FINITE_CROSSING')]:
    floor=tau+offset
    value=mod.threshold(np.ones(1),np.ones(1),floor,1.,floor+1.,tau,exact_floor_equality=exact)
    status,rho=value[:2]
    qmin=mod.image_budget(status,floor+1.,floor,tau)
    assert status==expected
    if exact:
        assert rho==1 and qmin==1
    elif offset==-.25:
        assert abs(rho-.5)<1e-12 and abs(qmin-.5)<1e-12
    else:
        assert rho is None and qmin is None
    out['boundary_samples'].append({'offset':offset,'analytic_equality':exact,'status':status,'rho':rho,'q_min':qmin})
baseline=mod.threshold(np.ones(1),np.ones(1),tau-1.,1.,tau,tau,exact_baseline_adequate=True)
assert baseline[0]=='ALREADY_ADEQUATE' and baseline[1]==0
assert mod.image_budget(baseline[0],tau,tau-1.,tau)==0
out['exact_adequate_baseline']={'status':baseline[0],'rho':0,'q_min':0}
assert sha(NEW / 'ARTIFACT_MANIFEST.json')==EXPECTED
out['candidate_manifest_unchanged']=True
out['status']='PASS_TARGETED_INDEPENDENT_NUMERICS'
dump(HERE / 'INDEPENDENT_NUMERICS.json',out)
print(json.dumps({k:out[k] for k in ('status','consumer_curve_point_count','independent_designs','D_equals_X','boundary_samples')},indent=2))
