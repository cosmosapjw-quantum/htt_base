"""Independent retained-artifact checks; no operator construction or H03 refit."""
from __future__ import annotations
import hashlib
import json
import platform
from pathlib import Path
import sys
import numpy as np
import scipy

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT = Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_operator_fresh_review')
BASE = ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
P = BASE/'products/R36-01-CF4-OPERATOR'
CONTRACT = Path('/mnt/extdrive/workdir/htt_open_data/r36_scientific_contract_preparation/R36-01.json')
MANIFEST_SHA = '164f5f63084caaf4ca18062d314ef53cf4773c528e72333a6b6d24a7e4437b14'
INPUT_SHA = '83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43'
IMPLEMENTATION_PACKET = '330a41bd1b4f2a5fc85a4d35cee08d31bd25fc272992c4a3ff63ecea1fc14d2f'
checks = []

def sha(path):
    return hashlib.file_digest(Path(path).open('rb'), 'sha256').hexdigest()

def check(label, condition, **metrics):
    entry = {'check': label, 'pass': bool(condition), **metrics}
    checks.append(entry)
    print(json.dumps(entry, allow_nan=False), flush=True)
    if not condition:
        raise AssertionError(label)

def close(label, value, target, *, atol, rtol):
    delta = np.abs(value-target)
    margin = atol+rtol*np.abs(target)
    check(label, np.all(delta <= margin), max_abs=float(delta.max()),
          max_tolerance_fraction=float((delta/margin).max()), atol=atol, rtol=rtol)

print(json.dumps({'python_executable': sys.executable, 'python': platform.python_version(),
                  'numpy': np.__version__, 'scipy': scipy.__version__,
                  'scope': 'saved operator independent inspection only; no new A or H03 fit'}))
manifest = json.loads((P/'ARTIFACT_MANIFEST.json').read_text())
result = json.loads((P/'RESULT.json').read_text())
controller_return = json.loads((P/'CONTROLLER_RETURN.json').read_text())
contract = json.loads(CONTRACT.read_text())
check('candidate_manifest_exact', sha(P/'ARTIFACT_MANIFEST.json') == MANIFEST_SHA,
      sha256=sha(P/'ARTIFACT_MANIFEST.json'))
check('input_manifest_exact', sha(BASE/'EVIDENCE_MANIFEST.json') == INPUT_SHA,
      sha256=sha(BASE/'EVIDENCE_MANIFEST.json'))
check('implementation_binding', manifest['packet_id'] == controller_return['packet_id'] == IMPLEMENTATION_PACKET
      and manifest['input_identity'] == controller_return['input_identity'] == 'sha256:'+INPUT_SHA
      and controller_return['candidate_identity'] == 'sha256:'+MANIFEST_SHA
      and controller_return['agent_id'] == manifest['agent_id'] == '/root/rc_330a41bd1b4f2a5f')
for entry in manifest['files']+manifest['evidence_logs']:
    p = Path(entry['path'])
    check('manifest_file:'+p.name, p.is_file() and sha(p) == entry['sha256'] and p.stat().st_size == entry['bytes'],
          sha256=sha(p), bytes=p.stat().st_size)
for name, entry in contract['source_bindings'].items():
    p = ROOT/entry['path']
    check('frozen_source:'+name, sha(p) == entry['sha256'] and p.stat().st_size == entry['bytes'],
          sha256=sha(p))
    check('result_source_binding:'+name, result['source_bindings'][entry['path']] == entry['sha256'])
source = ROOT/contract['source_bindings']['h03_raw']['path']
with np.load(source, allow_pickle=False) as source_npz:
    source_keys = source_npz.files
    src = {k: source_npz[k].copy() for k in contract['contract']['immutable_input']['columns']}
saved = json.loads((ROOT/contract['source_bindings']['h03_saved']['path']).read_text())
saved_gauge = json.loads((ROOT/contract['source_bindings']['h03_saved_gauge']['path']).read_text())
artifact = Path(result['artifact_path'])
check('result_artifact_binding', sha(artifact) == result['artifact_sha256']
      and artifact.stat().st_size == result['artifact_bytes'])
with np.load(artifact, allow_pickle=False) as data:
    art = {k: data[k].copy() for k in data.files}
A, AN, Q = art['A_raw'], art['AN'], art['Qz_whitened']
check('artifact_schema', A.shape == (36,35970) and AN.shape == (36,3)
      and Q.shape == (4,35970,4) and art['theta36'].shape == (36,)
      and art['covariance36'].shape == (36,36) and art['sigma'].shape == (35970,))
check('artifact_numeric_finite', all(np.isfinite(art[k]).all() for k in ('A_raw','AN','Qz_whitened','theta36','covariance36','sigma')))
check('source_row_identity', np.array_equal(art['group_id'],src['group_id'])
      and np.unique(src['group_id']).size == 35970)
check('source_sha_embedded', str(art['source_sha256']) == sha(source) == result['source_sha256'] == saved['source_SHA256'])
z, mu, emu, n, method = [src[k] for k in ('z_CMB','dmzp','e_dmzp','n_J2000','method_family')]
check('source_finiteness_bounds', all(np.isfinite(v).all() for v in (z,mu,emu,n))
      and np.all((z>0)&(z<.2)) and np.all(emu>0) and np.all((mu>=20)&(mu<=60)))
check('source_unit_directions', np.max(np.abs(np.sum(n*n,axis=1)-1)) <= 5e-12,
      max_norm_squared_error=float(np.max(np.abs(np.sum(n*n,axis=1)-1))), source_keys=source_keys)
check('units_and_frames', result['operator_units'] == 'Mpc^-1'
      and result['theta_units'] == 'km/s/Mpc' and result['covariance_units'] == '(km/s/Mpc)^2'
      and result['frames'] == {'direction':'outward ICRS J2000 n','redshift':'z_CMB released metadata',
                              'metric_signature':'(-,+,+,+)','speed_of_light_km_s':299792.458})
check('fixed_config', result['window_centers'] == saved['four_gaussian_window_centers'] == [.025,.04,.06,.08]
      and saved['width_z'] == .012 and set(np.unique(method)) == {'FP','OTHER','SN','TF'})

# Build the columns explicitly rather than importing the exporter's tensor/einsum.
d = np.power(10., (mu-25.)/5.)
sigma = np.sqrt(250.**2 + (70.*np.log(10.)/5.*d*emu)**2)
y = 299792.458*z
nx, ny, nz = n.T
features = np.column_stack((np.ones_like(z),nx,ny,nz,(nx*nx-ny*ny)/np.sqrt(2.),
                           (nx*nx+ny*ny-2*nz*nz)/np.sqrt(6.), np.sqrt(2.)*nx*ny,
                           np.sqrt(2.)*nx*nz,np.sqrt(2.)*ny*nz))
X = d[:,None]*features
close('sigma_export_parity',art['sigma'],sigma,atol=1e-10,rtol=1e-14)
theta_ref = np.asarray([r['theta9'] for r in saved['monopole_dipole_STF2_windows']]).reshape(36)
C_ref = np.asarray(saved['joint_covariance_36x36'])
theta = A@y
close('saved_theta_parity',theta,theta_ref,atol=1e-8,rtol=1e-10)
close('json_theta_parity',theta,np.asarray(result['theta4x9']).reshape(36),atol=1e-8,rtol=1e-10)
close('npz_theta_parity',theta,art['theta36'],atol=1e-8,rtol=1e-10)

# Contract the retained A in source-column chunks, using variance directly.
C = np.zeros((36,36))
for start in range(0,35970,997):
    end = min(start+997,35970)
    C += (A[:,start:end]*sigma[None,start:end]**2)@A[:,start:end].T
close('saved_full_covariance_parity',C,C_ref,atol=1e-10,rtol=1e-9)
close('json_full_covariance_parity',C,np.asarray(result['covariance36x36']),atol=1e-10,rtol=1e-9)
close('npz_full_covariance_parity',C,art['covariance36'],atol=1e-10,rtol=1e-9)
eig = np.linalg.eigvalsh((C+C.T)/2)
psd_bound = 64*np.finfo(float).eps*36*max(1.,np.linalg.norm(C,2))
check('covariance_PSD_no_clipping', eig[0] >= -psd_bound, min_eigenvalue=float(eig[0]),
      max_eigenvalue=float(eig[-1]), psd_roundoff_bound=float(psd_bound),
      symmetry_max_abs=float(np.max(np.abs(C-C.T))))
cross = []
for i in range(4):
    for j in range(i+1,4):
        block = C[9*i:9*i+9,9*j:9*j+9]
        close(f'cross_window_{i}_{j}_parity',block,C_ref[9*i:9*i+9,9*j:9*j+9],atol=1e-10,rtol=1e-9)
        cross.append({'windows':[i,j], 'max_abs':float(np.max(np.abs(block))),
                      'frobenius':float(np.linalg.norm(block))})
check('all_cross_windows_retained',all(c['max_abs']>0 for c in cross), blocks=cross)
sel = np.zeros((9,3)); sel[1:4,:] = np.eye(3)
Z = np.column_stack([d*(method==m) for m in ['FP','OTHER','SN','TF']])
check('method_monopole_exact_identity', np.array_equal(X[:,0],Z.sum(axis=1)))
for i,centre in enumerate([.025,.04,.06,.08]):
    Ai = A[i*9:i*9+9]
    w = np.exp(-.5*((z-centre)/.012)**2)/sigma**2
    s = np.sqrt(w)
    # G A=X^T W proves the retained rows are the WLS map. No new inverse/A or fit.
    G = X.T@(w[:,None]*X)
    rhs = X.T*w[None,:]
    normal_residual = G@Ai-rhs
    relative = np.linalg.norm(normal_residual)/np.linalg.norm(rhs)
    ident_error = np.max(np.abs(Ai@X-np.eye(9)))
    check(f'raw_WLS_operator_{i}',relative <= 1e-10 and ident_error <= 1e-9,
          weighted_normal_equation_relative=float(relative), A_X_max_abs=float(ident_error),
          design_condition=float(np.sqrt(np.linalg.cond(G))))
    close(f'dipole_selector_{i}',Ai@(d[:,None]*n),sel,atol=1e-9,rtol=0.)
    close(f'saved_bulk_response_{i}',Ai@n,np.asarray(saved['monopole_dipole_STF2_windows'][i]
          ['bulk_velocity_design_response_9x3_per_Mpc']),atol=1e-10,rtol=1e-10)
    SZ = s[:,None]*Z
    SX = s[:,None]*X
    q = Q[i]
    orth_error = np.max(np.abs(q.T@q-np.eye(4)))
    span_error = np.linalg.norm(SZ-q@(q.T@SZ))/np.linalg.norm(SZ)
    projected = SX-q@(q.T@SX)
    joined = np.column_stack((SX,SZ))
    sj = np.linalg.svd(joined,compute_uv=False)
    sp = np.linalg.svd(projected,compute_uv=False)
    rank_joined = int(np.count_nonzero(sj>sj[0]*1e-10))
    rank_projected = int(np.count_nonzero(sp>sp[0]*1e-10))
    check(f'separate_gauge_{i}',orth_error<=1e-12 and span_error<=1e-12
          and rank_joined==12 and rank_projected==8
          and saved_gauge['windows'][i]['mean_design_rank']==rank_joined
          and saved_gauge['windows'][i]['remaining_theta_rank']==rank_projected,
          Q_orthogonality_max_abs=float(orth_error), weighted_method_span_relative=float(span_error),
          joined_rank=rank_joined, projected_rank=rank_projected,
          joined_singular_ratios=(sj/sj[0]).tolist(), projected_singular_ratios=(sp/sp[0]).tolist(),
          projected_monopole_relative=float(np.linalg.norm(projected[:,0])/np.linalg.norm(SX[:,0])))
close('exported_AN',AN,A@n,atol=1e-10,rtol=1e-10)
close('json_AN',np.asarray(result['AN_36x3_inverse_Mpc']),AN,atol=1e-10,rtol=1e-10)
response = np.column_stack((AN,-AN))
nullbasis = np.vstack((np.eye(3),np.eye(3)))
rs = np.linalg.svd(response,compute_uv=False)
check('source_observer_rank_and_null', np.count_nonzero(rs>rs[0]*1e-10)==3
      and np.max(np.abs(response@nullbasis))<=1e-12
      and result['source_bulk_response']=='+AN' and result['observer_velocity_response']=='-AN',
      singular_value_ratios=(rs/rs[0]).tolist(), null_residual_max=float(np.max(np.abs(response@nullbasis))))
h = np.array([17.,-23.,31.])
close('source_positive_injection',A@(y+n@h)-theta,AN@h,atol=1e-8,rtol=1e-10)
close('observer_negative_injection',A@(y-n@h)-theta,-AN@h,atol=1e-8,rtol=1e-10)
permuted = np.arange(len(y)-1,-1,-1)
check('unchanged_A_permuted_rows_falsifies',not np.allclose(A@y[permuted],theta_ref,atol=1e-8,rtol=1e-10),
      max_theta_error=float(np.max(np.abs(A@y[permuted]-theta_ref))))
close('co_permuted_A_and_y_recovers',A[:,permuted]@y[permuted],theta_ref,atol=1e-8,rtol=1e-10)
table = np.genfromtxt(P/'TABLE.csv',delimiter=',',names=True)
theta4 = theta.reshape(4,9)
table_expected = np.column_stack(([.025,.04,.06,.08],theta4[:,0],np.linalg.norm(theta4[:,1:4],axis=1),
                                 np.linalg.norm(theta4[:,4:],axis=1),np.sqrt(np.diag(C)[::9])))
close('table_values',np.column_stack([table[k] for k in table.dtype.names]),table_expected,atol=1e-10,rtol=1e-11)
check('raw_gauge_claim_boundary',result['nuisance']['raw_theta']=='identity/no method projection'
      and result['nuisance']['anchored_monopole']=='NOT_IDENTIFIED'
      and result['claim_tier']=='DIAGNOSTIC_ONLY_CONDITIONAL_FIXED_WEIGHT'
      and result['owner']=='obsstat'
      and result['status']=='PROPOSED_PENDING_INDEPENDENT_REVIEW')

# Prepare an altered metadata fixture solely in reviewer-owned storage. Retained A
# remains unchanged; recomputed fixture SHA lets the row-ID guard be tested itself.
fixture = OUT/'permuted_id_fixture'
fixture.mkdir(exist_ok=True)
art['group_id'] = art['group_id'][::-1].copy()
np.savez_compressed(fixture/'A_permuted_ids.npz',**art)
fixture_result = dict(result)
fixture_result['artifact_path'] = str(fixture/'A_permuted_ids.npz')
fixture_result['artifact_sha256'] = sha(fixture/'A_permuted_ids.npz')
fixture_result['artifact_bytes'] = (fixture/'A_permuted_ids.npz').stat().st_size
(fixture/'RESULT.json').write_text(json.dumps(fixture_result,indent=2,allow_nan=False)+'\n')
output = {'schema':'htt.r36.review_checks/1', 'candidate_identity':'sha256:'+MANIFEST_SHA,
          'input_identity':'sha256:'+INPUT_SHA, 'contract_sha256':sha(CONTRACT),
          'review_mode':'PREPARATION_ONLY_NO_CONTROLLER_PACKET', 'checks':checks,
          'summary':{'checks_passed':len(checks), 'checks_failed':0},
          'runtime':{'requested_model':'gpt-6-astra','requested_effort':'xhigh','observed':'UNKNOWN',
                     'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
(OUT/'NUMERICAL_CHECKS.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
print(json.dumps(output['summary']))
