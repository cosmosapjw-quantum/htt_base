"""CF4 summary-conditioned paired diagnostics. No physical posterior is constructed.

The committed H03 statistic is the actual-data input; raw 35,970-group refit is
NOT_RUN here. All 4 windows share each draw ID and one weight 1/2048.
"""
from __future__ import annotations
import hashlib
import json
import platform
import sys
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import norm, qmc

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source'))
from publication_functionals import PartialDraw, PartialMeasure
from s02_coherent_stf import lower_certificates

SOURCE_BLOB = '538caae5212e576232b1c6b270cc084704504624'
COMMIT = '967ef7c8f0b132ecaaba343045d333d4ebf299c1'
SEED = 160916
POWER = 11
CENTERS = [.025, .04, .06, .08]


def read_statistics(path):
    raw = Path(path).read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != SOURCE_BLOB:
        raise ValueError('committed H03 sufficient-statistic blob changed')
    source = json.loads(raw)
    if source['source_groups'] != 35970 or source['four_gaussian_window_centers'] != CENTERS:
        raise ValueError('source cohort/windows changed')
    theta = np.array([x['theta9'] for x in source['monopole_dipole_STF2_windows']])
    cov = np.array(source['joint_covariance_36x36'])
    if theta.shape != (4, 9) or cov.shape != (36, 36):
        raise ValueError('joint statistic shape')
    if not np.isfinite(theta).all() or not np.isfinite(cov).all():
        raise ValueError('nonfinite joint statistic')
    if not np.allclose(cov, cov.T, atol=1e-13, rtol=0) or np.linalg.eigvalsh(cov)[0] <= 0:
        raise ValueError('joint covariance must be symmetric positive definite')
    return source, theta, cov


def joint_draws(theta, covariance, power=POWER, seed=SEED):
    u = qmc.Sobol(d=36, scramble=True, seed=seed).random_base2(power-1)
    z = norm.ppf(np.clip(u, np.finfo(float).eps, 1-np.finfo(float).eps))
    values = (np.ravel(theta)[None, :] + np.vstack([z, -z]) @ np.linalg.cholesky(covariance).T)
    values = values.reshape(1 << power, 4, 9)
    if not np.isfinite(values).all() or (values[:, :, 0] <= 0).any():
        raise ValueError('nonpositive working denominator')
    return values


def ratio(draws):
    d = np.asarray(draws, dtype=float)
    if d.shape[-1] != 9 or not np.isfinite(d).all() or (d[..., 0] <= 0).any():
        raise ValueError('positive finite working monopole required')
    return np.linalg.norm(d[..., 4:9], axis=-1) / d[..., 0]


def anchored_score(values, anchor):
    a = float(anchor)
    if not np.isfinite(a) or a <= 0:
        raise ValueError('positive finite declared anchor required')
    return np.asarray(values, dtype=float) / a


def floor_depth(values, anchor, floor):
    """Apparent ratio contrast, NOT certified F or physical G_F.

    max(A_j/B,delta)/max(A_0/B,delta) equals max(A_j,B delta)/max(A_0,B delta).
    No [0,1] occupancy or sector ceiling is asserted.
    """
    d = float(floor)
    if not np.isfinite(d) or d <= 0:
        raise ValueError('positive finite floor required')
    score = anchored_score(values, anchor)
    if score.ndim != 2 or score.shape[1] != 4 or not np.isfinite(score).all() or (score < 0).any():
        raise ValueError('finite nonnegative four-window apparent norm ratios required')
    return np.maximum(score[:, 1:], d) / np.maximum(score[:, :1], d)


def density_envelope(event_mass, unknown_mass, gamma):
    """Sharp interval for normalized q_i/p_i in [1/gamma,gamma].

    Missing event values may be completed arbitrarily. This is an assumed
    finite-measure sensitivity model, not measured CF4 selection probabilities.
    """
    e, u, g = float(event_mass), float(unknown_mass), float(gamma)
    if not all(np.isfinite([e, u, g])) or e < 0 or u < 0 or e+u > 1 or g < 1:
        raise ValueError('event and unknown mass must fit a unit measure; gamma >= 1')
    if g == 1:
        return [e, e+u]  # Exact identity case avoids cancellation in 1-(1-e).
    lo = max(e/g, 1-g*(1-e))
    hi = min(g*(e+u), 1-(1-e-u)/g)
    return [lo, hi]


def physical_partial(n, input_sha):
    return PartialMeasure(tuple(PartialDraw(
        sample_id=f'CF4_WORKING_JOINT_{i:05d}', weight=1/n,
        congruence_id='NO_PHYSICAL_CONGRUENCE_ADMITTED', input_sha256=input_sha,
        missing_reasons={'Q':'unmeasured_defined', 'F':'domain_uncertified', 'G_F':'domain_uncertified'})
        for i in range(n)))


def selection_fit_bounds(source, theta):
    """Exact triangle outer bounds from stored actual method-deletion shifts.

    The original report did not store deleted STF vectors. Their directions
    are not reconstructed. These are deterministic fit bounds, not draw laws.
    """
    output = []
    base_norm = np.linalg.norm(theta[:, 4:9], axis=1)
    for family in source['source_method_family_delete_sensitivity']:
        rows = []
        for j, item in enumerate(family['windows']):
            h = theta[j, 0] + item['delta_H0_km_s_Mpc']
            delta = item['delta_STF5_L2_km_s_Mpc']
            if h <= 0 or delta < 0:
                raise ValueError('invalid stored method deletion fit')
            rows.append({'center':CENTERS[j], 'ratio_outer':[
                max(0., base_norm[j]-delta)/h, (base_norm[j]+delta)/h],
                'H_deleted':float(h), 'STF_vector_change_norm':delta})
        output.append({'family_excluded':family['family_excluded'],
                       'excluded_groups':family['excluded_groups'], 'windows':rows})
    return output


def run(output=ROOT/'results'):
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    source, theta, cov = read_statistics(ROOT/'source/H03_SOURCE_TOMOGRAPHY.json')
    draws = joint_draws(theta, cov)
    n = len(draws); weights = np.full(n, 1/n)
    app = ratio(draws)
    signed = draws[:, :, 4:9] / draws[:, :, :1]
    anchors = np.array([.025, .03, .04, .05, .06, .075, .1])
    floors = np.array([.1, .25, .5, .75, 1., 1.5])
    anchored = app[None, :, :] / anchors[:, None, None]
    contrasts = np.stack([floor_depth(app, .05, delta) for delta in floors])
    physical = physical_partial(n, source['source_SHA256'])
    thresholds = [0., .01, .02, .025, .03, .04, .05, .06, .075, .1]
    events = []
    for t in thresholds:
        per_window = (app > t).mean(axis=0)
        any_mass = float((app > t).any(axis=1).mean())
        all_mass = float((app > t).all(axis=1).mean())
        events.append({'threshold':t, 'per_window':per_window.tolist(), 'any_window':any_mass,
                       'all_windows':all_mass, 'selection_envelopes':{
                           str(g):density_envelope(any_mass, 0., g) for g in [1.,1.25,2.,4.]}})
    north = np.array([x['theta9'] for x in source['north_weighted_same_sky_sensitivity']])
    north_ratio = ratio(north); base_ratio = ratio(theta)
    # Summary reconstruction must reproduce the already archived coupled result.
    reference = json.loads((ROOT/'source/S02_COHERENT_STF_SOURCE_BOUNDS.json').read_text())
    replay = lower_certificates(draws, .02, 3., [.2]*4)
    archived = reference['results']['b_3_threshold_0.02']
    if replay['coherent_pairwise_lower_count'] != archived['coherent_pairwise_lower_count'] or replay['rectangular_lower_count'] != archived['rectangular_lower_count']:
        raise AssertionError('summary reconstruction disagrees with archived raw-source run')
    curve_stats = []
    for delta, g in zip(floors, contrasts):
        curve_stats.append({'anchor':.05, 'floor':float(delta), 'amplitude_floor':.05*float(delta),
                            'quantiles_05_50_95':np.quantile(g,[.05,.5,.95],axis=0).tolist(),
                            'strict_mass_above_1':(g>1).mean(axis=0).tolist(),
                            'tie_mass_at_1':(g==1).mean(axis=0).tolist()})
    result = {
        'schema':'htt.P1_summary_conditioned_functional_sensitivity/1',
        'owner':'HTT research diagnostics', 'scope':'P1 S02/S03 supporting computation; physical acceptance pending',
        'claim_tier':'SOURCE_CONDITIONAL_WORKING_DIAGNOSTICS_ONLY', 'transfer_source':'NONE; no physical optical/kinematic map admitted',
        'source_commit':COMMIT, 'source_blob':SOURCE_BLOB, 'raw_CF4_SHA256':source['source_SHA256'],
        'source_group_count':source['source_groups'], 'source_input_kind':'committed actual-data 4x9 statistic and full 36x36 covariance',
        'raw_source_refit':'NOT_RUN', 'primary_checkout_tests':'NOT_RUN',
        'working_law':source['working_law'], 'covariance_assumption':source['full_joint_covariance_kind'],
        'selection_status':source['sampling_law_limits'],
        'sample_count':n, 'joint_unit':'one coupled four-window 36-vector; four windows are not independent samples',
        'seed':SEED,'antithetic':True,'weight':1/n,'weight_sum':float(weights.sum()),
        'finite_measure_interpretation':'deterministic Sobol quadrature; fractions are finite-law masses, not independent Monte Carlo p-values',
        'q_app_definition':'A_j=norm(STF5_app_j)/H_app_j; not Q=x_C/U_sigma',
        'signed_definition':'five signed STF_app coefficients divided by H_app; not physical x_C',
        'signed_negative_fraction':(signed<0).mean(axis=0).tolist(),
        'q_app_quantiles_05_50_95':np.quantile(app,[.05,.5,.95],axis=0).tolist(),
        'q_app_correlations':np.corrcoef(app,rowvar=False).tolist(),
        'strict_exceedance':events,
        'anchor_sensitivity':{'anchors':anchors.tolist(),'strict_mass_score_gt_1':(anchored>1).mean(axis=1).tolist()},
        'floor_depth_sensitivity':curve_stats,
        'anchor_floor_identity':'g_app(B,delta)=max(A_j,B*delta)/max(A_ref,B*delta); only product B*delta matters',
        'actual_north_weighted_fit':{'baseline_q_app':base_ratio.tolist(),'north_q_app':north_ratio.tolist(),
            'relative_change':(north_ratio/base_ratio-1).tolist(),'conditional_covariance_for_alternative':'UNAVAILABLE; no alternative draws or probability claims'},
        'actual_method_deletion_triangle_bounds':selection_fit_bounds(source,theta),
        'physical_functionals':{'x_C':'UNMEASURED','Q':'UNMEASURED','F':'DOMAIN_UNCERTIFIED','G_F':'DOMAIN_UNCERTIFIED',
            'unknown_mass':1.,'Pi':{key:physical.exceedance(key,[0.,.25,.5,1.]) for key in ['Q','F','G_F']},
            'selection_Gamma4_outer':density_envelope(0,1,4)},
        'reference_replay':{'coherent_lower_count':replay['coherent_pairwise_lower_count'],
                            'rectangle_lower_count':replay['rectangular_lower_count'], 'n':n, 'matched_archived_counts':True},
        'density_envelope':'normalized q_i/p_i in[1/Gamma,Gamma]; assumed, not inferred; pairwise ratio may reach Gamma^2',
        'environment':{'python':platform.python_version(),'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},
        'DAG_recommendation':{'S02':'pending','S03':'pending','reason':'new actual-summary sensitivity supports scope; physically admissible joint functional mapping/selection law absent; S03 depends on S02'},
    }
    np.savez_compressed(out/'paired_functional_arrays.npz',
        sample_id=np.array([f'CF4_WORKING_JOINT_{i:05d}' for i in range(n)]), weights=weights,
        centers=CENTERS, draws=draws, q_app=app, signed_STF_app_over_H=signed,
        anchors=anchors, anchored_app_scores=anchored, floors=floors, anchor_for_floors=.05,
        floor_depth_app_ratios=contrasts, physical_x=np.full(n,np.nan), physical_Q=np.full(n,np.nan),
        physical_F=np.full(n,np.nan), physical_G_F=np.full(n,np.nan),
        physical_Q_reason=np.full(n,'unmeasured_defined'), physical_F_G_reason=np.full(n,'domain_uncertified'))
    (out/'FUNCTIONAL_SENSITIVITY_RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    r = run()
    print(json.dumps({k:r[k] for k in ['sample_count','weight_sum','q_app_quantiles_05_50_95','reference_replay','actual_north_weighted_fit','DAG_recommendation']},indent=2))
