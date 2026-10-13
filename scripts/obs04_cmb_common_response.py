#!/usr/bin/env python3
"""Descriptive saved CMB coefficients and declared STF sensitivity; no inference."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'htt'))
sys.path.insert(0, str(ROOT / 'htt' / 'src'))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_stf(q):
    q = np.asarray(q, dtype=float)
    if q.shape != (3, 3) or not np.isfinite(q).all():
        raise ValueError('finite 3x3 Q required')
    if not np.allclose(q, q.T, atol=1e-10, rtol=0) or abs(np.trace(q)) > 1e-10:
        raise ValueError('symmetric trace-free Q required')
    return q


def sensitivity(q, e_q):
    """Outer envelopes conditional on ||delta Q||_F <= e_q, in microkelvin."""
    q = check_stf(q)
    e_q = np.asarray(e_q, dtype=float)
    if e_q.ndim != 1 or not len(e_q) or not np.isfinite(e_q).all() or np.any(e_q < 0):
        raise ValueError('nonempty finite nonnegative declared e_Q grid required')
    norm = np.linalg.norm(q, 'fro')
    eigenvalues = np.linalg.eigvalsh(q)
    return {'declared_e_Q_uK': e_q.tolist(), 'ordered_eigenvalues_uK': eigenvalues.tolist(),
            'eigenvalue_lower_uK': (eigenvalues[None, :] - e_q[:, None]).tolist(),
            'eigenvalue_upper_uK': (eigenvalues[None, :] + e_q[:, None]).tolist(),
            'frobenius_norm_uK': float(norm),
            'frobenius_lower_uK': np.maximum(0, norm-e_q).tolist(),
            'frobenius_upper_uK': (norm+e_q).tolist()}


def sphere_mean_square(q):
    """Product Gauss-Legendre/azimuth quadrature, exact for degree-four polynomial."""
    q = check_stf(q)
    z, weights = np.polynomial.legendre.leggauss(5)
    phi = np.arange(12)*2*np.pi/12
    n = np.stack(np.broadcast_arrays(np.sqrt(1-z[:, None]**2)*np.cos(phi),
                                    np.sqrt(1-z[:, None]**2)*np.sin(phi), z[:, None]), axis=-1)
    t = np.einsum('...i,ij,...j->...', n, q, n)
    return float(np.sum(weights[:, None]*t*t)/(2*len(phi)))


def downstream_response(mask):
    from obsstat.r7_cmb_product_response import pixel_fit_geometry
    _, design = pixel_fit_geometry()
    fit = design[mask]
    # Inject all 36 fitted harmonics simultaneously; no n-by-n matrix.
    recovered, _, rank, singular = np.linalg.lstsq(fit, fit, rcond=None)
    target = recovered[4:16, 4:16]
    leakage = recovered[4:16][:, np.r_[0:4, 16:36]]
    return {'status': 'FINITE_INJECTED_DOWNSTREAM_CHECK', 'rank': int(rank),
            'fit_condition': float(singular[0]/singular[-1]),
            'target_identity_max_abs_error': float(np.max(np.abs(target-np.eye(12)))),
            'fitted_nuisance_leakage_max_abs': float(np.max(np.abs(leakage))),
            'operator': 'NSIDE64 pixel-center real Y ell0..5 -> common mask -> unweighted least squares -> ell2,3',
            'scope': 'finite fitted harmonic subspace only; excludes ell>5 leakage, native beam, averaging/pixel window, foreground and noise response',
            'full_native_response': 'HOLD_NOT_BOUND'}


def generate(npz_path, metadata_path, output, grid):
    metadata = json.loads(metadata_path.read_text())
    processing = metadata['processing']
    with np.load(npz_path, allow_pickle=False) as saved:
        ids = saved['sample_ids'].tolist()
        mask = saved['common_mask']
        if mask.dtype != np.bool_ or mask.shape != (49152,):
            raise ValueError('stored NSIDE64 Boolean common mask required')
        if hashlib.sha256(mask.tobytes()).hexdigest() != processing['mask_sha256']:
            raise ValueError('stored mask identity mismatch')
        if int(mask.sum()) != processing['valid_pixels']:
            raise ValueError('mask count mismatch')
        values = {}
        records = {r['sample_id']: r for r in metadata['records']}
        for name in ('PR3_SMICA', 'PR3_COMMANDER'):
            index = ids.index(name)
            row = saved['retained_K'][index]
            q_k = saved['Q'][index]
            if row.shape != (32,) or not np.isfinite(row).all():
                raise ValueError('finite retained ell2..5 coefficients required')
            if not np.array_equal(row, np.asarray(records[name]['retained_K'])) or not np.array_equal(q_k, records[name]['Q_K']):
                raise ValueError('NPZ/JSON saved record mismatch')
            q = check_stf(q_k*1e6)
            numerical = sphere_mean_square(q)
            analytic = float(2*np.linalg.norm(q, 'fro')**2/15)
            coeff = row[:12]*1e6
            harmonic = float(np.dot(coeff[:5], coeff[:5])/(4*np.pi))
            if not np.allclose([numerical, harmonic], analytic, atol=1e-10, rtol=1e-12):
                raise ValueError('quadrupole normalization mismatch')
            values[name] = {'coefficients_l2_l3_uK': coeff.tolist(), 'Q_uK': q.tolist(),
                            'sensitivity': sensitivity(q, grid),
                            'normalization': {'sphere_quadrature_mean_square_uK2': numerical,
                                              'two_fifteenths_frobenius_squared_uK2': analytic,
                                              'harmonic_power_over_4pi_uK2': harmonic}}
        difference = np.asarray(values['PR3_COMMANDER']['coefficients_l2_l3_uK'])-values['PR3_SMICA']['coefficients_l2_l3_uK']
        response = downstream_response(mask)
    result = {'task': 'OBS-04', 'owner': 'obsstat', 'claim_tier': 'C0',
              'scope': 'DESCRIPTIVE_SAVED_COMMON_MASK_COEFFICIENTS_AND_DECLARED_STF_SENSITIVITY',
              'non_claim_bearing': True, 'units': 'uK_CMB', 'frame': 'GALACTIC',
              'harmonic_layout': 'ORTHONORMAL_REAL_M0_COS_SIN: ell2 first five, ell3 next seven',
              'sources_sha256': {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha256(p) for p in (npz_path, metadata_path, Path(__file__), ROOT/'htt/obsstat/r8_product_intake.py', ROOT/'htt/obsstat/r7_cmb_product_response.py')},
              'processing': {k: processing[k] for k in ('id','processing_id','nside','mask_sha256','valid_pixels','beam_policy')},
              'transfer_source': 'released PR3 temperature maps; saved pixel-averaged controls',
              'response_matched': False, 'sky_support_status': 'STORED_COMMON_MASK',
              'null_mock_status': 'UNAVAILABLE', 'coverage': 'HOLD',
              'statistical_intervals': 'HOLD_COVARIANCE_CROSS_MAP_LAW_MATCHED_SIMULATIONS_AND_BIAS_BOUND_MISSING',
              'declared_radius_status': 'SENSITIVITY_PARAMETER_ONLY_NOT_MEASURED_ERROR_OR_PHYSICAL_BOUND',
              'products': values, 'commander_minus_smica_uK': difference.tolist(),
              'difference_norms_uK': {str(ell): float(np.linalg.norm(difference[slice(a,b)])) for ell,a,b in ((2,0,5),(3,5,12))},
              'downstream_response': response,
              'caveats': ['Same sky products are correlated; difference has no significance calibration.',
                          'Native map-specific beams differ and were not deconvolved; shared downstream fit does not match the full response.',
                          'A common additive coefficient bias cancels in a difference; small spread cannot bound common bias.',
                          'Declared Frobenius radii produce conditional outer envelopes, without confidence coverage.',
                          'Q is a temperature quadrupole tensor; physical interpretation remains HOLD.']}
    output.mkdir(parents=True, exist_ok=True)
    (output/'diagnostic.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    plot(result, output)
    return result


def plot(result, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for name, row in result['products'].items():
        axes[0].plot(np.arange(12), row['coefficients_l2_l3_uK'], 'o-', label=name)
    axes[0].set_ylabel('saved coefficient [µK CMB]'); axes[0].legend()
    axes[1].bar(np.arange(12), result['commander_minus_smica_uK'])
    axes[1].set_ylabel('Commander − SMICA [µK CMB]')
    axes[1].set_xticks(np.arange(12), ['2:0','2:1c','2:1s','2:2c','2:2s','3:0','3:1c','3:1s','3:2c','3:2s','3:3c','3:3s'], rotation=45)
    for ax in axes: ax.axvline(4.5, color='gray', linestyle=':'); ax.axhline(0, color='gray', linewidth=.5)
    fig.suptitle('Stored common-mask fits; full native responses differ\nDescriptive differences; covariance and coverage HOLD')
    fig.tight_layout()
    for ext in ('png','pdf'): fig.savefig(output/f'coefficients_and_differences.{ext}')
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, (name,row) in zip(axes, result['products'].items()):
        s = row['sensitivity']; x = np.asarray(s['declared_e_Q_uK'])
        for i in range(3):
            ax.fill_between(x, np.asarray(s['eigenvalue_lower_uK'])[:,i], np.asarray(s['eigenvalue_upper_uK'])[:,i], alpha=.2)
            ax.plot(x, np.full_like(x, s['ordered_eigenvalues_uK'][i]), label=f'λ{i+1}')
        ax.set_title(name); ax.set_xlabel('declared e_Q [µK CMB]'); ax.legend()
    axes[0].set_ylabel('ordered Q eigenvalue envelope [µK CMB]')
    fig.suptitle('Conditional Frobenius sensitivity envelope; no confidence coverage')
    fig.tight_layout()
    for ext in ('png','pdf'): fig.savefig(output/f'quadrupole_sensitivity.{ext}')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'docs/generated/tensor_joint_r8/owned_controls/cmb/cmb_controls.npz')
    parser.add_argument('--metadata', type=Path, default=ROOT/'docs/generated/tensor_joint_r8/owned_controls/cmb/cmb.json')
    parser.add_argument('--output', type=Path, default=ROOT/'docs/observational_methods_20261013/OBS-04')
    parser.add_argument('--e-q', nargs='+', type=float, default=[0,1,3,5])
    args = parser.parse_args()
    result = generate(args.input.resolve(), args.metadata.resolve(), args.output, args.e_q)
    print(json.dumps({'difference_norms_uK': result['difference_norms_uK'], 'downstream_response': result['downstream_response'], 'coverage': result['coverage']}, indent=2))
