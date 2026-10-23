"""Source-conditioned SH0ES GLS; no upstream code execution or CF4 joint law."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np
from scipy import linalg
from astropy.io import fits

HERE = Path(__file__).resolve().parent
EXTERNAL = Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/shoes_ladder_20261018')
DOCUMENT = EXTERNAL / 'reanalysis_2208.11169v3.html'
PRIOR = HERE.parent / 'D03_PANTHEON_CF4/results/D03_RESULT.json'
HOSTS = 'M101 M1337 N0691 N1015 N0105 N1309 N1365 N1448 N1559 N2442 N2525 N2608 N3021 N3147 N3254 N3370 N3447 N3583 N3972 N3982 N4038 N4424 N4536 N4639 N4680 N5468 N5584 N5643 N5728 N5861 N5917 N7250 N7329 N7541 N7678 N0976 U9391'.split()
PARAMETERS = ['mu_'+h for h in HOSTS] + ['Delta_mu_N4258', 'M_H_W', 'Delta_mu_LMC', 'mu_M31', 'Delta_b_W', 'M_B', 'Z_W', 'dummy_X', 'Delta_zp', 'five_log10_H0']
SELECTORS = [38, 38, 43, 44, 45, 41, 37, 39]


class TableParser(HTMLParser):
    """Read only named Table 3's literal cells, independent of fitted values."""
    def __init__(self):
        super().__init__()
        self.active = False
        self.rows = []
        self.cells = None
        self.parts = None

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and dict(attrs).get('id') == 'S3.T3.2':
            self.active = True
        if self.active and tag == 'tr':
            self.cells = []
        if self.active and tag in ('td', 'th'):
            self.parts = []

    def handle_data(self, data):
        if self.active and self.parts is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if not self.active:
            return
        if tag in ('td', 'th') and self.parts is not None:
            self.cells.append(''.join(self.parts).strip())
            self.parts = None
        if tag == 'tr' and self.cells is not None:
            self.rows.append(self.cells)
            self.cells = None
        if tag == 'table':
            self.active = False


def named_intervals(document=DOCUMENT):
    parser = TableParser()
    parser.feed(document.read_text())
    by_name = {}
    for row in parser.rows:
        if row and row[0] in HOSTS:
            if row[0] in by_name:
                raise ValueError('duplicate Table 3 host')
            count, first, last = map(int, row[-3:])
            if last-first+1 != count:
                raise ValueError('Table 3 count/interval disagreement')
            by_name[row[0]] = (first-1, last)
    if set(by_name) != set(HOSTS):
        raise ValueError('missing named Table 3 host')
    return by_name


def validate_layout(L, y, C, intervals):
    if L.shape != (47, 3492) or y.shape != (3492,) or C.shape != (3492, 3492):
        raise ValueError('released orientation/shape must be L=47x3492, y=3492, C=3492x3492')
    if not all(np.isfinite(v).all() for v in (L, y, C)):
        raise ValueError('nonfinite released input')
    if not np.array_equal(C, C.T):
        raise ValueError('released C is not exactly symmetric')
    A = L.T
    covered = np.zeros(2150, dtype=int)
    for j, host in enumerate(HOSTS):
        lo, hi = intervals[host]
        if not 0 <= lo < hi <= 2150:
            raise ValueError('invalid named Cepheid interval')
        expected = np.zeros(2150)
        expected[lo:hi] = 1
        if not np.array_equal(A[:2150, j], expected):
            raise ValueError('named Table 3 interval mismatch: '+host)
        covered[lo:hi] += 1
    if not np.array_equal(covered, np.ones(2150)):
        raise ValueError('Table 3 intervals do not partition 2150 Cepheids')
    if not np.all(np.isin(A[:, :37], [0., 1.])):
        raise ValueError('host indicators not binary')
    if np.any(A[2150:3130, :37]) or np.any(A[3207:, :37]):
        raise ValueError('host indicators outside Cepheid/calibrator rows')
    if not np.array_equal(A[3130:3207, :37].sum(axis=1), np.ones(77)):
        raise ValueError('calibrator rows not one host each')
    expected = np.zeros((8, 47))
    expected[np.arange(8), SELECTORS] = 1
    if not np.array_equal(A[3207:3215], expected):
        raise ValueError('eight external constraint selectors mismatch')
    blocks = {37: [(2150,2593,1),(3213,3214,1)],
              38: [(0,3130,1),(3207,3209,1)],
              39: [(2648,3130,1),(3214,3215,1)],
              40: [(2593,2648,1)], 42: [(3130,3207,1),(3215,3492,1)],
              44: [(3210,3211,1)], 45: [(2648,3061,1),(3211,3212,1)],
              46: [(3215,3492,-1)]}
    for j, pieces in blocks.items():
        expected = np.zeros(3492)
        for lo, hi, value in pieces:
            expected[lo:hi] = value
        if not np.array_equal(A[:, j], expected):
            raise ValueError('named nuisance block mismatch: '+PARAMETERS[j])
    validate_dummy(C)
    return {'host_intervals_zero_based_half_open': intervals,
            'all_37_named_supports_exact': True, 'constraint_selectors_zero_based': SELECTORS,
            'dummy_row_zero_based': 3210, 'dummy_variance_mag2': float(C[3210,3210]),
            'dummy_sigma_mag': float(np.sqrt(C[3210,3210]))}


def validate_dummy(C):
    variance = C[3210,3210]
    if not np.isclose(variance, 1e-9, rtol=1e-6, atol=0):
        raise ValueError('dummy covariance entry must be variance approximately 1e-9')
    if np.count_nonzero(C[3210]) != 1 or np.count_nonzero(C[:,3210]) != 1:
        raise ValueError('dummy has nonzero offdiagonal covariance')


def solve_gls(A, y, C):
    """Whiten once; column-scaled QR and independent SVD of same inputs."""
    chol = linalg.cholesky(C, lower=True, check_finite=True)
    Aw = linalg.solve_triangular(chol, A, lower=True)
    yw = linalg.solve_triangular(chol, y, lower=True)
    scale = np.linalg.norm(Aw, axis=0)
    if np.any(scale == 0):
        raise ValueError('zero whitened design column')
    B = Aw/scale
    Uq, R = linalg.qr(B, mode='economic')
    qs = linalg.solve_triangular(R, Uq.T@yw)
    q = qs/scale
    Ri = linalg.solve_triangular(R, np.eye(R.shape[0]))
    factor = Ri/scale[:,None]
    V = factor@factor.T
    Us, singular, Vh = linalg.svd(B, full_matrices=False)
    rank = int(np.count_nonzero(singular > singular[0]*max(B.shape)*np.finfo(float).eps))
    q_svd = (Vh.T@((Us.T@yw)/singular))/scale
    residual = yw-Aw@q
    normal = np.linalg.norm(B.T@residual)/(singular[0]*np.linalg.norm(yw))
    agreement = np.linalg.norm(q-q_svd)/max(np.linalg.norm(q),np.finfo(float).tiny)
    reconstruct = R@(scale[:,None]*V*scale[None,:])@R.T
    cov_error = np.linalg.norm(reconstruct-np.eye(len(q)))/np.sqrt(len(q))
    diagnostics = dict(rank=rank, singular_values_scaled_whitened=singular.tolist(),
                       normalized_normal_residual=float(normal), relative_q_qr_svd=float(agreement),
                       covariance_factor_reconstruction=float(cov_error),
                       chi_square=float(residual@residual), residual_dof=len(y)-len(q),
                       column_scales=scale.tolist())
    if rank != len(q) or normal > 1e-10 or agreement > 1e-8 or cov_error > 1e-10:
        raise ArithmeticError('frozen numerical acceptance failed: '+json.dumps(diagnostics))
    return q, V, q_svd, diagnostics


def project_hosts(q, V):
    n = len(q)
    P = np.eye(n)-np.ones((n,n))/n
    centered = P@q
    cov = P@V@P.T
    eigenvalues = linalg.eigvalsh(cov)
    scale = max(np.linalg.norm(cov), np.finfo(float).tiny)
    checks = {'annihilate_common': float(np.linalg.norm(P@np.ones(n))),
              'idempotence': float(np.linalg.norm(P@P-P)/np.linalg.norm(P)),
              'covariance_symmetry': float(np.linalg.norm(cov-cov.T)/scale),
              'common_offset_invariance': float(np.linalg.norm(P@(q+1.)-centered)/max(np.linalg.norm(q),1.))}
    if any(v > 1e-12 for v in checks.values()):
        raise ArithmeticError('frozen host quotient acceptance failed: '+json.dumps(checks))
    rank = int(np.count_nonzero(eigenvalues > max(abs(eigenvalues))*n*np.finfo(float).eps))
    if rank != n-1 or eigenvalues[0] < -1e-12*max(abs(eigenvalues)):
        raise ArithmeticError('host quotient covariance PSD/rank failed')
    return centered, cov, eigenvalues, rank, checks


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_actual():
    provenance = json.loads(PRIOR.read_text())['SH0ES_actual_full_input']
    arrays, records = {}, []
    for name, record in provenance['files'].items():
        path = Path(record['path'])
        if sha(path) != record['sha256'] or path.stat().st_size != record['bytes']:
            raise ValueError('immutable source identity mismatch: '+str(path))
        key = name[3]
        arrays[key] = np.asarray(fits.getdata(path),dtype=float)
        records.append(record)
    return arrays['l'], arrays['y'].reshape(-1), arrays['c'], records


def plot(cov):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots(figsize=(10,9))
    limit = float(np.max(np.abs(cov)))
    artist = ax.imshow(cov, cmap='RdBu_r', vmin=-limit,vmax=limit)
    ax.set_xticks(range(37), HOSTS, rotation=90, fontsize=7)
    ax.set_yticks(range(37), HOSTS, fontsize=7)
    ax.set_title('Source-conditioned SH0ES host covariance after common-mode quotient')
    fig.colorbar(artist, ax=ax, label='Covariance of centered distance moduli [mag²]')
    fig.text(.5,.015,'HTT C0 diagnostic • released Gaussian model • Pantheon+/CF4 joint law UNKNOWN',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.035,1,1))
    for suffix in ('png','pdf'):
        fig.savefig(HERE/f'HOST_COVARIANCE.{suffix}',dpi=170)
    plt.close(fig)


def main():
    start = time.monotonic()
    if any(os.environ.get(k) != '2' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')):
        raise ValueError('run with exactly two BLAS/OMP threads')
    L,y,C,records = load_actual()
    layout = validate_layout(L,y,C,named_intervals())
    q,V,qsvd,checks = solve_gls(L.T,y,C)
    centered,hostcov,eigenvalues,rank,projection = project_hosts(q[:37],V[:37,:37])
    H0 = float(10**(q[46]/5))
    H0_sigma = float(H0*np.log(10)/5*np.sqrt(V[46,46]))
    np.savez_compressed(HERE/'HOST_COVARIANCE.npz', host_names=np.array(HOSTS),
                        parameter_names=np.array(PARAMETERS), q=q, covariance=V,q_svd=qsvd,
                        host_mean=q[:37],host_covariance=V[:37,:37],
                        centered_host_mean=centered, centered_host_covariance=hostcov,
                        centered_host_covariance_eigenvalues=eigenvalues)
    import scipy, astropy
    result = dict(owner='htt',claim_tier='C0',status='CONDITIONAL_DIAGNOSTIC_REVIEW_PENDING',
                  scope='full released linear Gaussian ladder GLS and common-host quotient',
                  source_binding='COMPOSITE: official DataRelease matrices + arXiv:2208.11169v3 section 2.1 and named Table 3',
                  official_commit='c447f0fea703fcd0fff57de5000947b5ca81286b',
                  official_parameter_dictionary='NOT_PROVIDED_BY_RELEASE',
                  transfer_source='none',inputs=records,source_documents=json.loads((EXTERNAL/'ACQUISITION.json').read_text()),
                  readme_sha256=sha(Path(records[0]['path']).parent/'SH0ES_README.md'),
                  parameter_units=['mag']*41+['mag/dex','mag','mag/dex','mag','mag','5 log10(H0 / (km s^-1 Mpc^-1))'],
                  parameter_names=PARAMETERS,parameters=q.tolist(),parameter_sigma=np.sqrt(np.diag(V)).tolist(),
                  layout=layout,numerics=checks,host_quotient={'rank':rank,'checks':projection,'eigenvalues_mag2':eigenvalues.tolist()},
                  baseline_reproduction_diagnostic={'H0_km_s_Mpc':H0,'delta_method_sigma_km_s_Mpc':H0_sigma,
                  'uncertainty':'source Gaussian covariance; first-order propagation, not CF4 posterior'},
                  slope_convention={'official_README_baseline':-3.285,'reanalysis_baseline':-3.286,'reported_parameter':'Delta_b_W only; discrepancy unresolved'},
                  retained_rows=3492,retained_parameters=47,original_42_states='UNCHANGED_HOLD_OR_CONDITIONAL',
                  physical_eta_anchor='NOT_ESTABLISHED',pantheon_cf4_joint_law='UNKNOWN',
                  requested_runtime='gpt-6.1-sol/high',observed_runtime='UNKNOWN',
                  git_head_at_run=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  interpreter=sys.executable,python=platform.python_version(),packages={'numpy':np.__version__,'scipy':scipy.__version__,'astropy':astropy.__version__},
                  threads={'OPENBLAS_NUM_THREADS':os.environ['OPENBLAS_NUM_THREADS'],'OMP_NUM_THREADS':os.environ['OMP_NUM_THREADS']},
                  caveats=['source-conditioned Gaussian linear model','no physical eta anchor','shared Pantheon/CF4 calibration law unknown','no independent-survey or physical anisotropy significance','D07 97/97 finite campaign untouched'],
                  elapsed_seconds_before_plot=time.monotonic()-start)
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    plot(hostcov)
    print(json.dumps({'H0':H0,'sigma_H0':H0_sigma,'numerics':checks,'host_rank':rank,'elapsed_seconds':time.monotonic()-start}))


if __name__ == '__main__':
    main()
