"""Exact calibration ambiguity of the stored CF4 even angular working fields.

These functions act on a fitted field, not on the raw catalogue likelihood.
No optical-to-congruence bridge, physical shear, or posterior is admitted.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.linalg import eigvalsh

ROOT = Path(__file__).resolve().parent
P1 = ROOT.parent / 'P1'
sys.path.insert(0, str(P1 / 'source'))
from h03_tomography import STF

ARRAY_SHA = 'cd38f438a0bf07385b07478c7b5c122df5af1e9bb48a5575fe1cad40ef261f27'
SOURCE_SHA = '5d31e2ab4fea682c538c31c15181ae7b07e11efba98b36c66aff6feca88f8326'
BASE_HEAD = '1e095a2749cce9b28e45aac043a82218c21f84e5'
PAIRS = tuple(itertools.combinations(range(4), 2))


def checked_read(path, digest):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('immutable source/input identity mismatch: ' + str(path))
    return raw


def load_existing():
    """Reuse the exact existing measure; never regenerate/renormalize its draws."""
    path = P1 / 'results/paired_functional_arrays.npz'
    checked_read(path, ARRAY_SHA)
    source = json.loads(checked_read(P1 / 'source/H03_SOURCE_TOMOGRAPHY.json', SOURCE_SHA))
    with np.load(path, allow_pickle=False) as data:
        draws = data['draws'].copy()
        weights = data['weights'].copy()
        ids = data['sample_id'].copy()
        physical = {k: data[k].copy() for k in ('physical_x', 'physical_Q', 'physical_F', 'physical_G_F')}
    expected = np.array([f'CF4_WORKING_JOINT_{i:05d}' for i in range(2048)])
    if draws.shape != (2048, 4, 9) or not np.array_equal(ids, expected):
        raise ValueError('joint draw identity changed')
    if not np.array_equal(weights, np.full(2048, 1/2048)) or weights.sum() != 1:
        raise ValueError('original exact finite weights required')
    if not all(np.isnan(v).all() for v in physical.values()):
        raise ValueError('physical unknowns may not be replaced by working proxies')
    return source, draws, weights, ids, physical


def even_matrices(draws):
    d = np.asarray(draws, dtype=float)
    if d.shape[-1:] != (9,) or not np.isfinite(d).all():
        raise ValueError('finite monopole/dipole/STF9 required')
    m = d[..., 0, None, None] * np.eye(3) + np.einsum('...a,aij->...ij', d[..., 4:9], STF)
    if np.any(np.linalg.eigvalsh(m)[..., 0] <= 0):
        raise ValueError('even angular field crosses zero; logarithmic domain uncertified')
    return m


def erasure_radius(matrices):
    """Min over H*>0 of sup_n |5 log10[H*/(n^T M n)]|, in mag."""
    m = np.asarray(matrices, dtype=float)
    if m.shape[-2:] != (3, 3) or not np.isfinite(m).all() or not np.allclose(m, m.swapaxes(-1,-2), atol=1e-13, rtol=0):
        raise ValueError('finite symmetric 3x3 field required')
    e = np.linalg.eigvalsh(m)
    if np.any(e[..., 0] <= 0):
        raise ValueError('positive angular field required')
    return 2.5*np.log10(e[..., -1]/e[..., 0]), np.sqrt(e[..., 0]*e[..., -1])


def directed_contrast(matrices):
    """D_jk = sup_n 5 log10[h_j(n)/h_k(n)] by generalized eigenvalues."""
    m = np.asarray(matrices, dtype=float)
    if m.shape != (4,3,3):
        raise ValueError('one coupled four-window field required')
    erasure_radius(m)  # Validate symmetry, finiteness and positive domain.
    result = np.zeros((4,4))
    for j,k in PAIRS:
        ev = eigvalsh(m[j], m[k])
        result[j,k] = 5*np.log10(ev[-1])
        result[k,j] = -5*np.log10(ev[0])
    return result


def cycles(n=4):
    """All directed simple cycles once up to cyclic permutation."""
    out = []
    for size in range(2,n+1):
        for subset in itertools.combinations(range(n), size):
            for tail in itertools.permutations(subset[1:]):
                out.append((subset[0],) + tail)
    return tuple(out)


CYCLES = cycles()


def common_calibration_radius(directed):
    """Exact minimax residual eta for E_j(n)=g(n)+c_j+e_j(n), |e_j|<=eta.

    g is one unrestricted common angular magnitude field; c_j are arbitrary
    window monopoles. Pairwise consistency requires c_j-c_k >= D_jk-2eta.
    The difference constraints are feasible iff every directed cycle has
    nonpositive total weight. Thus eta=max_cycle sum(D_jk)/(2*cycle_length).
    """
    d = np.asarray(directed, dtype=float)
    if d.shape != (4,4) or not np.isfinite(d).all():
        raise ValueError('finite four-window directed contrasts required')
    values = np.array([sum(d[j,k] for j,k in zip(c,c[1:]+c[:1]))/(2*len(c)) for c in CYCLES])
    index = int(np.argmax(values))
    eta = max(0., float(values[index]))
    w = d - 2*eta
    # Longest-path potentials from a super-source with zero edges to all nodes.
    c = np.zeros(4)
    for _ in range(3):
        c = np.maximum(c, np.max(w+c[None,:], axis=1))
    c -= c[0]
    violation = float(np.max(d-(c[:,None]-c[None,:])-2*eta))
    if violation > 2e-12:
        raise ArithmeticError('common-calibration witness violates difference constraints')
    pair_lower = max((d[j,k]+d[k,j])/4 for j,k in PAIRS)
    return eta, pair_lower, c, CYCLES[index], violation


def finite_tail(values, weights, thresholds):
    v, w = np.asarray(values), np.asarray(weights)
    if v.ndim != 1 or w.shape != v.shape or not np.isfinite(v).all() or not np.isfinite(w).all() or (w<0).any() or w.sum()!=1:
        raise ValueError('finite scalar values and original unit weights required')
    if not np.isfinite(thresholds).all():
        raise ValueError('finite thresholds required')
    return [{'threshold_mag': float(t), 'strict_mass': float(w @ (v>t)), 'tie_mass': float(w @ (v==t))} for t in thresholds]


def signed_kinematic_comparator(stf, H, omega):
    """Conditional algebra ONLY: S=sigma, Omega=omega, tilt=curvature=0.

    The input is not inferred physical shear. Used solely for radial-blindness
    witnesses: n^T Omega n=0 while x changes by -||Omega||_F^2/(6H^2).
    """
    s, o = np.asarray(stf, dtype=float), np.asarray(omega, dtype=float)
    if s.shape != (3,3) or o.shape != (3,3) or not np.isfinite(s).all() or not np.isfinite(o).all() or not np.isfinite(H) or H<=0:
        raise ValueError('finite spatial tensors and positive H required')
    if not np.allclose(s,s.T,rtol=0,atol=1e-13) or abs(np.trace(s))>1e-12 or not np.allclose(o,-o.T,rtol=0,atol=1e-13):
        raise ValueError('STF shear and antisymmetric vorticity required')
    return (np.sum(s*s)-np.sum(o*o))/(6*H*H)


def run():
    source, draws, weights, ids, physical = load_existing()
    m = even_matrices(draws)
    rho, hstar = erasure_radius(m)
    contrast = np.array([directed_contrast(row) for row in m])
    fits = [common_calibration_radius(d) for d in contrast]
    eta = np.array([f[0] for f in fits]); pair = np.array([f[1] for f in fits])
    centers = source['four_gaussian_window_centers']
    point = np.array([row['theta9'] for row in source['monopole_dipole_STF2_windows']])
    point_m = even_matrices(point)
    point_rho, point_hstar = erasure_radius(point_m)
    point_fit = common_calibration_radius(directed_contrast(point_m))
    thresholds = [.0,.01,.02,.025,.03,.04,.05,.06,.075,.1]
    qs = [.05,.5,.95]
    result = {
        'schema': 'htt.S02_even_field_calibration_obstruction/1',
        'owner':'htt', 'scope':'S02 actual-source conditional obstruction and calibration requirements; no physical mapping admission',
        'claim_tier':'C0', 'status':'CONDITIONAL', 'transfer_source':'empirical_proxy',
        'source_commit':BASE_HEAD, 'source_summary_sha256':SOURCE_SHA, 'original_array_sha256':ARRAY_SHA,
        'selected_cf4_source_npz_sha256':source['source_SHA256'], 'source_groups':source['source_groups'],
        'working_law':source['working_law'], 'working_covariance':source['full_joint_covariance_kind'],
        'sample_count':len(draws), 'joint_shape':list(draws.shape), 'weights_sum':float(weights.sum()), 'weight_each':float(weights[0]),
        'draws_regenerated':False, 'raw_catalogue_refit':'NOT_RUN', 'independent_sky_count':'NOT_ASSERTED',
        'sector':'fitted even angular working field h_j(n)=H_app,j+n^T S_app,j n, on S2; dipole excluded by definition',
        'distance_calibration_convention':'d_corrected=d_app*10^(Delta_mu/5); h_corrected=h_app*10^(-Delta_mu/5)',
        'single_window_erasure_radius_mag':{'definition':'rho_j=2.5 log10(lambda_max(M_j)/lambda_min(M_j)); M_j=H_j I+S_j',
            'quantile_levels':qs,'quantiles':np.quantile(rho,qs,axis=0).tolist(),'point_fit':point_rho.tolist(),
            'point_isotropic_H_star_km_s_Mpc':point_hstar.tolist(),
            'strict_tails':[finite_tail(rho[:,j],weights,thresholds) for j in range(4)]},
        'common_angular_calibration':{'definition':'eta*=inf_(g,c_j) sup_(j,n)|5log10 h_j(n)-g(n)-c_j|',
            'common_g_amplitude':'UNRESTRICTED; no external calibration measurement imposed',
            'eta_quantiles_mag':np.quantile(eta,qs).tolist(),'point_fit_eta_mag':point_fit[0],
            'max_pair_bound_quantiles_mag':np.quantile(pair,qs).tolist(),
            'joint_minus_pair_max_mag':float(np.max(eta-pair)),
            'joint_strictly_stronger_than_pair_count':int(np.count_nonzero(eta-pair>1e-12)),
            'cycle_lengths':{str(k):sum(len(f[3])==k for f in fits) for k in [2,3,4]},
            'point_active_cycle':list(point_fit[3]), 'max_constraint_violation_mag':max(f[4] for f in fits),
            'strict_tails':finite_tail(eta,weights,thresholds),
            'pair_necessary_radii_quantiles_mag':{f'{j}-{k}':np.quantile((contrast[:,j,k]+contrast[:,k,j])/4,qs).tolist() for j,k in PAIRS}},
        'conditional_signed_x':{'definition':'IF S_app=sigma, H_app=Theta/3 and tilt=curvature=0: x_kin=(||S||_F^2-||Omega||_F^2)/(6H^2)',
            'radial_only_identified_set':'(-infinity, ||S||_F^2/(6H^2)] for unrestricted antisymmetric Omega',
            'physical_interpretation_admitted':False,
            'upper_endpoint_quantiles':np.quantile(np.sum(draws[:,:,4:9]**2,axis=2)/(6*draws[:,:,0]**2),qs,axis=0).tolist(),
            'full_x_with_unbounded_tilt_curvature':'UNBOUNDED; no finite physical interval asserted'},
        'physical_unknown_mass':{'x_C':1.,'Q':1.,'F':1.,'G_F':1.},
        'physical_strict_Pi_outer':{key:[0.,1.] for key in ['Q','F','G_F']},
        'physical_x_sign':'UNMEASURED; no clipping or zero imputation',
        'physical_mapping_missing':[
            'source-qualified same-congruence and observer-frame optical-to-kinematic response',
            'finite-redshift remainder/evolution and peculiar-flow controls for the four overlapping windows',
            'empirical method/direction/depth distance-calibration and selected covariance/likelihood',
            'vorticity/tilt/curvature information for total signed x; positive source-bound ceiling for Q/F/G_F'],
        'canonical_recommendation':'HOLD_PENDING_PHYSICAL_MAPPING; independent review and parent decision required',
        'limitations':[
            'Exact algebra of fitted even fields; applying a distance correction to raw rows changes design and weights, so no raw catalogue prediction invariance is asserted.',
            'S2 extrema extrapolate the fitted field; no uniform data support or sky/mask completeness is inferred.',
            'Multiplicative angular calibrations allowed here need not be pure quadrupoles; log of a quadratic field contains higher even multipoles.',
            'Common calibration equality across windows is a sensitivity assumption; group/method mixing can break it.',
            'Finite-law masses are working Gaussian/Sobol quadrature, not calibrated probabilities or p-values.',
            'No measured calibration radii, physical confidence intervals, physical detection, solver or ODE calculation.'],
        'literature':[{'url':'https://arxiv.org/html/2412.14607','scope':'Boubel et al. section3: directional zeropoint/expansion degeneracy; no likelihood replication'},
            {'url':'https://arxiv.org/html/2312.09875v3','scope':'Maartens et al. sections3-4: observer frame and luminosity-distance correction; no direct finite-window shear identification'}],
        'environment':{'python':platform.python_version(),'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},
        'runtime_identity':{'requested':'gpt-6.1-sol/high','observed':'UNKNOWN','review':'PENDING_PARENT_INDEPENDENT_REVIEW'},
    }
    output = ROOT/'results'; output.mkdir(exist_ok=True)
    np.savez_compressed(output/'calibration_obstruction_arrays.npz',sample_id=ids,weights=weights,centers=centers,
        original_joint_draws=draws,original_q_app=np.linalg.norm(draws[:,:,4:9],axis=2)/draws[:,:,0],
        original_signed_STF_app_over_H=draws[:,:,4:9]/draws[:,:,:1],
        erasure_radius_mag=rho,isotropic_H_star=hstar,directed_contrast_mag=contrast,
        common_residual_radius_mag=eta,pair_lower_radius_mag=pair,window_constant_witness_mag=np.array([f[2] for f in fits]),
        conditional_x_kin_upper=np.sum(draws[:,:,4:9]**2,axis=2)/(6*draws[:,:,0]**2),**physical)
    (output/'S02_CALIBRATION_OBSTRUCTION.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    result = run()
    print(json.dumps({k:result[k] for k in ['sample_count','weights_sum','single_window_erasure_radius_mag','common_angular_calibration','canonical_recommendation']},indent=2))
