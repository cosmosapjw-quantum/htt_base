"""Frozen R25-K03 reported-depth, full-24 covariance sensitivity calculation."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'AGENTS.md').exists())
INPUT = ROOT / 'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/R25-K03-DEPTH-COVROBUST_INPUT.json'
INPUT_SHA = '9abcf30af3fe40f52508554b03aba669789b212c2b8b0bfae5f8eba2ae01729f'
P = ROOT / 'docs/research_program/observational_publication_20261015/METHOD_EXECUTION_20261023'


def read_sources():
    if hashlib.sha256(INPUT.read_bytes()).hexdigest() != INPUT_SHA:
        raise ValueError('immutable input identity mismatch')
    spec = json.loads(INPUT.read_text())
    sources = {}
    for item in spec['sources']:
        path = ROOT / item['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'immutable source identity mismatch: {path}')
        sources[path.parent.name] = json.loads(path.read_text())
    return spec, sources


def matrices():
    """Build maps independently from rational reported-z centers."""
    centers = np.array([1/4, 7/12, 26/33], dtype=float)
    M = np.zeros((18, 24))
    for b, c in enumerate(centers):
        M[6*b:6*b+6, 6*b:6*b+6] = np.eye(6)
        M[6*b:6*b+6, 18:24] = c*np.eye(6)
    H = np.kron(np.array([[-1., 1., 0.], [0., -1., 1.]]), np.eye(6))
    Z = np.kron(np.array([[1., 0., 0.], [-1., 1., 0.], [0., -1., 1.]]), np.eye(6))
    return centers, M, H, H @ M, Z


def support(mean, cov, direction, rho):
    """Exact support of {x:(x-mean)' cov^-1 (x-mean)<=rho^2}."""
    direction = np.asarray(direction, dtype=float)
    return float(direction @ mean + rho*np.sqrt(direction @ cov @ direction))


def statistic(d, A, C, tau):
    V = A @ (C + tau*tau*np.eye(24)) @ A.T
    L = np.linalg.cholesky(V)
    y = np.linalg.solve(L, d)
    return float(y @ y), V


def crossing(d, A, C, critical):
    initial, _ = statistic(d, A, C, 0.)
    if initial <= critical:
        return {'status': 'ABSENT_ALREADY_BELOW_AT_ZERO', 'tau_uasyr': None,
                'T0': initial, 'critical': critical}
    hi = 1.
    while statistic(d, A, C, hi)[0] > critical:
        hi *= 2
        if hi > 1e8:
            raise ArithmeticError('crossing bracket not found')
    lo = 0.
    root = brentq(lambda t: statistic(d, A, C, t)[0]-critical,
                  lo, hi, xtol=1e-13, rtol=1e-13)
    residual = statistic(d, A, C, root)[0]-critical
    if abs(residual) > 1e-8:
        raise ArithmeticError('crossing residual too large')
    return {'status': 'CROSSED', 'tau_uasyr': float(root), 'bracket_uasyr': [lo, hi],
            'residual': float(residual), 'critical': float(critical)}


def calculate():
    spec, src = read_sources()
    depth, old, bundle = src['depth_images'], src['k03_depth_moments'], src['tensor_bundle']
    mu = np.asarray(depth['full24']['mean_uasyr'], dtype=float)
    C = np.asarray(depth['full24']['cov_uasyr2'], dtype=float)
    if mu.shape != (24,) or C.shape != (24, 24) or not np.allclose(C, C.T, rtol=0, atol=1e-12):
        raise ValueError('full24 source shape or symmetry')
    if np.linalg.eigvalsh(C)[0] <= 0:
        raise ValueError('full24 covariance not SPD')
    centers, M, H, A, Z = matrices()
    if not np.allclose(M, depth['depth']['M24_to_Y18'], rtol=0, atol=1e-14):
        raise ValueError('independent rational-center M mismatch')
    for tol in (1e-8, 1e-10, 1e-12):
        if np.linalg.matrix_rank(A, tol=tol) != 12:
            raise ValueError(f'A rank failure at {tol}')
    d = A @ mu
    Y = M @ mu
    G = Z @ M
    common = np.vstack([np.eye(6), np.eye(6), np.eye(6), np.zeros((6, 6))])
    if not np.allclose(A @ common, 0, rtol=0, atol=1e-14):
        raise ValueError('common-mode cancellation failed')
    rows = []
    for tau in spec['tau_uasyr']:
        T, V = statistic(d, A, C, tau)
        eig, vec = np.linalg.eigh(V)
        eigen_T = float(np.sum((vec.T @ d)**2/eig))
        if not np.isclose(T, eigen_T, rtol=1e-9, atol=1e-10):
            raise ValueError('Cholesky/eigen quadratic mismatch')
        rows.append({'tau_uasyr': tau, 'T12': T,
                     'gaussian_reference_survival': float(chi2.sf(T, 12)),
                     'moment_reference_upper_bound': float(min(1, 12/T)),
                     'V12_uasyr2': V.tolist()})
    if any(a['T12'] <= b['T12'] for a, b in zip(rows, rows[1:])):
        raise ValueError('T not strictly decreasing')
    roots = {}
    for alpha, name in [(0.05, 'alpha_0p05'), (1/80, 'alpha_1over80')]:
        roots[name] = {'gaussian_reference': crossing(d, A, C, chi2.isf(alpha, 12)),
                       'moment_reference': crossing(d, A, C, 12/alpha)}
    result = {
        'task_id': spec['task_id'], 'input_identity': 'sha256:'+INPUT_SHA,
        'scope': 'selected reported-redshift full-vector equality; exploratory covariance sensitivity',
        'source_identities': spec['sources'], 'units': {'coefficient':'microarcsec/year',
            'covariance':'(microarcsec/year)^2', 'tau':'microarcsec/year'},
        'null': 'E1/B1 six-component vector levels equal across all three reported-redshift bins; 12 restrictions',
        'distinct_prior_null': 'old six-slope zero score tests theta6=0, not equality of three full vector levels',
        'coordinates': {'full24':'gamma0[6],gamma1[6],gamma2[6],theta[6]',
            'reported_centers_rational':['1/4','7/12','26/33'], 'reported_centers':centers.tolist(),
            'E1':'polar first 3 of each six', 'B1':'axial last 3 of each six'},
        'full24': {'mean_uasyr':mu.tolist(), 'cov_uasyr2':C.tolist(), 'retained':True},
        'M24_to_Y18': M.tolist(), 'H18_to_d12':H.tolist(), 'A12x24':A.tolist(),
        'contrast12_mean_uasyr':d.tolist(),
        'inflation': {'U24_formula':'C24 + tau^2 I24', 'Loewner_upper_envelope':True,
            'full24_cross_covariance_retained':True, 'common_mode_cancellation':'A [I6;I6;I6;0]=0'},
        'reference_curves':rows, 'reference_crossings':roots,
        'reference_semantics': {'gaussian':'chi-square(12) survival under centered Gaussian with covariance dominated by Vtau; reference only',
            'moment':'min(1,12/Ttau) Markov upper bound under zero contrast mean and deterministic covariance upper bound; reference only',
            'alpha_0p05':'standalone reference', 'alpha_1over80':'scale comparison only; no R9 budget reuse'},
        'x': {'carrier':'full24', 'mean_uasyr':mu.tolist(), 'cov_uasyr2':C.tolist()},
        'Q': {'computational_reference':bundle['Q']['computational_reference'],
              'physical_MES_anchor':None, 'physical_status':'UNAVAILABLE'},
        'F': {'kind':'full24 ellipsoid family', 'center_uasyr':mu.tolist(),
              'covariance_at_tau':'U24(tau)=C24+tau^2 I24',
              'support_function':'h(v;tau,rho)=v^T mu24+rho sqrt(v^T U24(tau) v)',
              'rho':'named reference radius only; no coverage calibration',
              'physical_occupancy':'UNAVAILABLE'},
        'Pi': {'status':'UNCHANGED_ORIGINAL_EMPIRICAL_LAW',
               'source':str((P/'tensor_bundle/RESULT.json').relative_to(ROOT)),
               'source_law':bundle['Pi']['source_law'], 'retained_rows':4096,
               'original_scalar_exceedance':bundle['Pi'],
               'newly_calibrated_Pi':False, 'robust_tail_bound_is_Pi':False},
        'G_F': {'coordinates':'(Y0,delta1=Y1-Y0,delta2=Y2-Y1)',
                'map24_to_Z18':G.tolist(), 'mean18_uasyr':(G@mu).tolist(),
                'cov18_at_tau0_uasyr2':(G@C@G.T).tolist(),
                'cov18_at_tau':'G U24(tau) G^T, all 18x18 cross blocks retained',
                'Y18_mean_uasyr':Y.tolist(), 'Y18_cov_at_tau0_uasyr2':(M@C@M.T).tolist(),
                'physical_depth_status':'UNAVAILABLE'},
        'old_slope6_comparator': {'T6':old['score_chi2_6_scenario'],
             'working_tail':old['score_chi2_6_working_tail_scenario'],
             'different_null':True},
        'checks': {'A_rank_at_1e-8_1e-10_1e-12':[12,12,12],
                   'common_mode_max_abs':float(np.max(np.abs(A@common))),
                   'cholesky_eigen_agreement':True,
                   'M_independently_recomputed':True,
                   'C24_min_eigenvalue':float(np.linalg.eigvalsh(C)[0])},
        'claim_ceiling':'conditional selected reported-depth sensitivity only; no physical law, calibrated observed p, true-depth result, R9 reuse, original K03 acceptance, or family identification'}
    return result


def plot(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    mu = np.asarray(result['full24']['mean_uasyr'])
    C = np.asarray(result['full24']['cov_uasyr2'])
    A = np.asarray(result['A12x24'])
    d = A@mu
    tau = np.linspace(0, 16, 400)
    T = np.array([statistic(d,A,C,t)[0] for t in tau])
    fig, axes = plt.subplots(1,2,figsize=(11,4.2))
    axes[0].plot(tau,T,color='navy',label=r'$T_{12}(\tau)$')
    axes[0].axhline(chi2.isf(.05,12),color='darkorange',ls='--',label='Gaussian 0.05 reference')
    axes[0].axhline(12/.05,color='crimson',ls=':',label='moment 0.05 reference')
    axes[0].axhline(chi2.isf(1/80,12),color='goldenrod',ls='--',lw=.8,label='Gaussian 1/80 scale')
    axes[0].axhline(12/(1/80),color='indianred',ls=':',lw=.8,label='moment 1/80 scale')
    for group in result['reference_crossings'].values():
        for item in group.values():
            if item['status']=='CROSSED':
                axes[0].plot(item['tau_uasyr'],item['critical'],'ko',ms=3)
    axes[0].set(xlabel=r'coefficient inflation $\tau$ (µas/year)',ylabel=r'$T_{12}$',title='Reported-depth vector equality (12 contrasts)')
    axes[0].set_yscale('log')
    axes[0].set_ylim(.8,1200)
    axes[0].legend(fontsize=8)
    axes[1].plot(tau,chi2.sf(T,12),label='Gaussian reference survival',color='darkorange')
    axes[1].plot(tau,np.minimum(1,12/T),label='moment upper bound',color='crimson')
    axes[1].axhline(.05,color='black',ls='--',lw=.8)
    axes[1].axhline(1/80,color='gray',ls=':',lw=.8)
    axes[1].set(xlabel=r'coefficient inflation $\tau$ (µas/year)',ylabel='reference tail / upper bound',ylim=(0,1.02),title='Conditional reference laws')
    axes[1].legend(fontsize=8)
    fig.text(.5,.01,'Selected reported-z summaries; covariance upper-envelope scenario. No calibrated observed p or physical-depth law.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.04,1,1])
    fig.savefig(HERE/'figure.png',dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    result = calculate()
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    plot(result)
    print(json.dumps({'T0':result['reference_curves'][0]['T12'],
      'crossings':result['reference_crossings']},indent=2))
