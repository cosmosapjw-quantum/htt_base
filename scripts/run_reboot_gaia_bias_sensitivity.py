#!/usr/bin/env python3
"""Fixed-cohort linear bias supports for the saved Gaia EDR3 frame fit.

This is a conditional working-law sensitivity, not a certified physical bias
bound or the unavailable CAS-07 Jacobi theorem input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path

import numpy as np
from run_reboot_gaia_frame import design

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/observational_reboot_20261014/results/gaia_frame_v1'
EXPECTED_NPZ_SHA256 = '41b6ddcb13131b49b97efd6107816af4518fa9e23725cf3b4272c2f3a70acb8f'
R1_ARCHIVE = ROOT / 'HTT_OBSERVATIONAL_METHODS_R1_20261013_PACKAGE.zip'
R1_ARCHIVE_SHA256 = 'ea94ad68471eca0525c0b24d1ff1f9883d0b408ae8efb5ad7a5eac743dfd96e1'
R1_MEMBER = 'HTT_OBSERVATIONAL_METHODS_R1_20261013/code/observational_linear_core.py'
R1_MEMBER_SHA256 = 'b7d27f8a4b32733883b63ef4460c83855ab2f7be8a863cd6abbcf6f9edd34228'
NAMES = ('spin_x', 'spin_y', 'spin_z', 'glide_x', 'glide_y', 'glide_z')
RHO = (0., .1, .25, .5, 1., 2., 4., 8.)
BOX_MICROAS = (0., 5., 10., 20., 50.)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_error(actual, expected):
    """Norm-relative error with a zero-expectation absolute branch."""
    actual = np.asarray(actual)
    expected = np.asarray(expected)
    scale = np.linalg.norm(expected)
    return float(np.linalg.norm(actual - expected) / scale) if scale else float(np.linalg.norm(actual))


def influence(x, y, c, precision_scale=1.):
    """Return the 6 by 2N whitened and raw-observation influence maps.

    precision_scale multiplies only the numerical precision Q, while c is
    always the fixed physical sampling covariance in this function.
    """
    if any(np.iscomplexobj(a) for a in (x, y, c, precision_scale)):
        raise ValueError('real design, observations, covariance, and precision scale required')
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    c = np.asarray(c, dtype=float)
    if x.ndim != 3 or x.shape[1:] != (2, 6) or y.shape != x.shape[:2] or c.shape != (len(x), 2, 2):
        raise ValueError('aligned tangent design/observations/covariance required')
    if not all(np.isfinite(a).all() for a in (x, y, c)) or not np.isfinite(precision_scale) or precision_scale <= 0:
        raise ValueError('finite inputs and positive precision scale required')
    if not np.allclose(c, np.swapaxes(c, 1, 2), rtol=1e-12, atol=0):
        raise ValueError('symmetric 2x2 covariance blocks required')
    l = np.linalg.cholesky(c)  # fail on non-SPD; no eigenvalue floor
    w = np.linalg.solve(l, np.broadcast_to(np.eye(2), c.shape))
    a = np.sqrt(precision_scale) * np.matmul(w, x).reshape(-1, 6)
    u, s, vt = np.linalg.svd(a, full_matrices=False)
    threshold = np.finfo(float).eps * max(a.shape) * s[0]
    if int(np.sum(s > threshold)) != 6:
        raise ValueError('six-coordinate design rank deficient')
    k_svd = (vt.T / s) @ u.T
    # Map the fixed physical whitened residual z=L^-1 y; Q rescaling cancels.
    k = np.sqrt(precision_scale) * k_svd
    m = np.einsum('jni,nik->jnk', k.reshape(6, len(x), 2), w)
    coeff = np.einsum('jna,na->j', m, y)
    v = np.einsum('jna,nab,knb->jk', m, c, m)
    v_kk = k @ k.T
    if relative_error(v, v_kk) > 1e-10:
        raise AssertionError('fixed covariance sandwich differs from K K^T')
    if relative_error(np.einsum('jna,nak->jk', m, x), np.eye(6)) > 1e-12:
        raise AssertionError('M X does not reproduce the six-coordinate identity')
    return {'K': k, 'M': m, 'V': v, 'coefficients': coeff,
            'singular_values': s, 'condition': float(s[0] / s[-1]),
            'rank_threshold': float(threshold), 'L': l}


def support(fit, rho=RHO, box_microas=BOX_MICROAS):
    m, k, v = fit['M'], fit['K'], fit['V']
    sigma = np.sqrt(np.diag(v))
    if not np.all(np.isfinite(sigma)) or np.any(sigma <= 0):
        raise ValueError('positive finite six-coordinate sampling variances required')
    # One total L2 budget over all 2N whitened coordinates, never an RMS budget.
    ellipsoid = np.outer(np.asarray(rho, float), sigma)
    # Independent per-coordinate raw pmRA* and pmDEC bounds, in mas/year.
    raw_l1 = np.abs(m).sum(axis=(1, 2))
    box = np.outer(np.asarray(box_microas, float) / 1000., raw_l1)
    return sigma, ellipsoid, box


def verify_support_attainment(fit, rho=1., box_mas=.01, diagnostics=False):
    if np.iscomplexobj(rho) or np.iscomplexobj(box_mas) or not np.isfinite(rho) or not np.isfinite(box_mas) or rho < 0 or box_mas < 0:
        raise ValueError('finite nonnegative witness budgets required')
    k, m, l, sigma = fit['K'], fit['M'], fit['L'], np.sqrt(np.diag(fit['V']))
    shift_errors, norm_errors, box_errors = [], [], []
    for j in range(6):
        z = rho * k[j] / np.linalg.norm(k[j])
        raw = np.einsum('nia,na->ni', l, z.reshape(-1, 2))
        recovered = np.linalg.solve(l, raw[..., None])[..., 0].ravel()
        norm_errors.append(abs(np.linalg.norm(recovered) - rho))
        ellipsoid_shift = np.einsum('na,na->', m[j], raw)
        box_bias = box_mas * np.sign(m[j])
        box_shift = np.einsum('na,na->', m[j], box_bias)
        shift_errors.append(abs(ellipsoid_shift - rho * sigma[j]))
        box_errors.append(abs(box_shift - box_mas * np.abs(m[j]).sum()))
    result = {'ellipsoid_shift_max_abs_mas_year': float(max(shift_errors)),
              'whitened_norm_max_abs': float(max(norm_errors)),
              'box_shift_max_abs_mas_year': float(max(box_errors))}
    if result['whitened_norm_max_abs'] > 1e-12 * max(1., rho):
        raise AssertionError('constructed raw ellipsoid witness violates the whitened L2 budget')
    if diagnostics:
        return result
    return max(result['ellipsoid_shift_max_abs_mas_year'], result['box_shift_max_abs_mas_year'])


def verify_r1_identity():
    if sha256(R1_ARCHIVE) != R1_ARCHIVE_SHA256:
        raise ValueError('R1 source archive SHA256 mismatch')
    with zipfile.ZipFile(R1_ARCHIVE) as archive:
        member = archive.read(R1_MEMBER)
    if hashlib.sha256(member).hexdigest() != R1_MEMBER_SHA256:
        raise ValueError('R1 source member SHA256 mismatch')
    return member


def load_frozen():
    verify_r1_identity()
    npz_path = SOURCE / 'qualified_rows.npz'
    if sha256(npz_path) != EXPECTED_NPZ_SHA256:
        raise ValueError('immutable qualified-row source SHA256 mismatch')
    with np.load(npz_path, allow_pickle=False) as data:
        source_ids = data['source_id']
        ra, dec = data['ra'], data['dec']
        y, c = data['proper_motion'], data['covariance']
    if len(source_ids) != 4756 or len(np.unique(source_ids)) != 4756:
        raise ValueError('frozen selected cohort count or IDs changed')
    saved_path = SOURCE / 'result.json'
    saved = json.loads(saved_path.read_text())
    if saved['source_ids_decimal'] != [str(int(i)) for i in source_ids]:
        raise ValueError('saved fit and qualified source identities differ')
    if saved['coefficient_order'] != list(NAMES):
        raise ValueError('saved six-coordinate order differs')
    return source_ids, design(ra, dec), y, c, saved, saved_path


def numeric_controls(x, y, c, fit):
    controls = {}
    for alpha in (.25, 4.):
        scaled = influence(x, y, c, precision_scale=alpha)
        controls[str(alpha)] = {
            'M_relative_error': relative_error(scaled['M'], fit['M']),
            'V_relative_error': relative_error(scaled['V'], fit['V']),
            'coefficient_max_abs_mas_yr': float(np.max(np.abs(scaled['coefficients'] - fit['coefficients']))),
        }
    for scale in (2., 4.):
        scaled = influence(x, y, c * scale**2)
        sigma0, rho0, box0 = support(fit)
        sigmas, rhos, boxs = support(scaled)
        controls[f'physical_error_scale_{scale:g}'] = {
            'M_relative_error': relative_error(scaled['M'], fit['M']),
            'V_over_s2_relative_error': relative_error(scaled['V'] / scale**2, fit['V']),
            'sigma_over_s_relative_error': relative_error(sigmas / scale, sigma0),
            'rho_support_over_s_relative_error': relative_error(rhos / scale, rho0),
            'raw_box_relative_error': relative_error(boxs, box0),
        }
    # Change the coordinate unit on the same observations and their covariance.
    micro = influence(x, y * 1000., c * 1e6)
    sigma0, rho0, box0 = support(fit)
    sigmam, rhom, boxm = support(micro, box_microas=tuple(1000. * b for b in BOX_MICROAS))
    controls['mas_to_microas'] = {
        'M_relative_error': relative_error(micro['M'], fit['M']),
        'V_over_1e6_relative_error': relative_error(micro['V'] / 1e6, fit['V']),
        'sigma_over_1000_relative_error': relative_error(sigmam / 1000., sigma0),
        'rho_over_1000_relative_error': relative_error(rhom / 1000., rho0),
        'box_over_1000_relative_error': relative_error(boxm / 1000., box0),
    }
    return controls


def plot_grid(out, xvalues, supports, sigmas, filename, xlabel):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.5), sharex=True)
    for j, ax in enumerate(axes.flat):
        s = 1.96 * sigmas[j] * 1000.
        b = supports[:, j] * 1000.
        ax.plot(xvalues, np.full(len(xvalues), s), label='1.96 sigma, Gaussian proxy', color='C0')
        ax.plot(xvalues, b, label='deterministic support', color='C1')
        ax.plot(xvalues, s + b, label='sum half-width', color='C2')
        ax.set(title=NAMES[j], xlabel=xlabel, ylabel='absolute microas/year')
        ax.grid(alpha=.25)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3)
    fig.tight_layout(rect=(0, 0, 1, .94))
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'{filename}.{ext}', dpi=170)
    plt.close(fig)


def run(out: Path):
    start = time.perf_counter()
    if out.exists():
        raise ValueError('fresh output directory required')
    source_ids, x, y, c, saved, saved_path = load_frozen()
    fit = influence(x, y, c)
    saved_coeff = np.asarray(saved['full_fit']['coefficients_mas_yr'])
    saved_v = np.asarray(saved['full_fit']['covariance_mas2_yr2'])
    coeff_abs = float(np.max(np.abs(fit['coefficients'] - saved_coeff)))
    cov_rel = relative_error(fit['V'], saved_v)
    if coeff_abs > 1e-12 or cov_rel > 1e-10:
        raise AssertionError('saved baseline coefficient/covariance parity failed')
    sigma, ellipsoid, box = support(fit)
    controls = numeric_controls(x, y, c, fit)
    for row in controls.values():
        for key, val in row.items():
            if key.endswith('relative_error') and val > 1e-10:
                raise AssertionError(f'numerical rescaling invariant failed: {key}={val}')
            if key.endswith('max_abs_mas_yr') and val > 1e-12:
                raise AssertionError(f'numerical coefficient invariant failed: {key}={val}')
    attainment_detail = verify_support_attainment(fit, diagnostics=True)
    attainment = max(attainment_detail['ellipsoid_shift_max_abs_mas_year'],
                     attainment_detail['box_shift_max_abs_mas_year'])
    if attainment > 1e-12:
        raise AssertionError('support attainment failed')
    result = {
        'task': 'RB26/GAIA_EDR3_FIXED_COHORT_LINEAR_BIAS_SENSITIVITY',
        'owner': 'HTT', 'status': 'DESCRIPTIVE_CONDITIONAL',
        'source': {'qualified_rows_path': str((SOURCE / 'qualified_rows.npz').relative_to(ROOT)),
                   'qualified_rows_sha256': EXPECTED_NPZ_SHA256,
                   'saved_fit_path': str(saved_path.relative_to(ROOT)),
                   'saved_fit_sha256': sha256(saved_path),
                   'source_rows_csv_sha256': saved['source']['sha256'],
                   'source_release': 'Gaia EDR3 fixed frame-source cohort, saved RB22/AO16 result'},
        'proof_bridge': {'support_formula': 'sup_{||z||_2<=rho} e_j^T K z = rho ||K_j||_2; sup_{|b_ia|<=bbar} e_j^T M b = bbar sum_ia |M_jia|',
                         'source_R1_identity': {'archive_path': str(R1_ARCHIVE.relative_to(ROOT)),
                                                'archive_sha256': R1_ARCHIVE_SHA256,
                                                'member_path': R1_MEMBER, 'member_sha256': R1_MEMBER_SHA256,
                                                'functions': ['fixed_design_gls', 'weighted_linear_map', 'box_bias', 'ellipsoid_bias'],
                                                'status': 'source-bound finite-support specialization; no new proof audit'},
                         'CAS07_Jacobi_input': 'ABSENT', 'Lean_wrapper': 'UNVERIFIED'},
        'cohort_count': int(len(source_ids)), 'observation_coordinates': int(2 * len(source_ids)),
        'coefficient_order': list(NAMES), 'units': 'coefficients/supports mas/year internally; displayed widths microas/year',
        'design': 'pmRAstar and pmDEC interleaved per source; no additional cos(dec)',
        'sampling_law': 'fixed-cohort Gaussian 2x2 per-source marginal covariance proxy; cross-source covariance unavailable',
        'bias_sets': {'rho_whitened_total_L2': list(RHO), 'raw_box_microas_year_each_coordinate': list(BOX_MICROAS),
                      'rho_is_total_not_RMS': True, 'certified_rho_or_box_input': None},
        'coefficients_mas_year': fit['coefficients'].tolist(),
        'sampling_covariance_mas2_year2': fit['V'].tolist(),
        'sampling_sigma_microas_year': (1000 * sigma).tolist(),
        'ellipsoid_support_microas_year': (1000 * ellipsoid).tolist(),
        'box_support_microas_year': (1000 * box).tolist(),
        'ellipsoid_component_halfwidth_microas_year': (1000 * (1.96 * sigma[None, :] + ellipsoid)).tolist(),
        'box_component_halfwidth_microas_year': (1000 * (1.96 * sigma[None, :] + box)).tolist(),
        'numerical_checks': {'saved_coefficient_max_abs_mas_year': coeff_abs,
                             'saved_covariance_relative_error': cov_rel,
                             'support_attainment_max_abs_mas_year': attainment,
                             'support_witness_whitened_norm_max_abs': attainment_detail['whitened_norm_max_abs'],
                             'MX_minus_I_relative_error': relative_error(np.einsum('jna,nak->jk', fit['M'], x), np.eye(6)),
                             'My_minus_saved_max_abs_mas_year': coeff_abs,
                             'numerical_precision_and_unit_controls': controls},
        'claim_ceiling': 'fixed-design linear working-law sensitivity; coordinatewise Gaussian-reference halfwidth plus deterministic support; no joint/empirical 95% coverage, no certified physical bias, no Jacobi/CAS07 or MES bound',
        'caveats': ['selection is endogenous upstream', 'cross-source correlations and direction errors unavailable',
                    'no bound on physical rho or box bias follows from fit residuals',
                    'numerical Q rescaling leaves M and fixed-C sampling variance invariant; inverse curvature alone is not sampling covariance'],
    }
    out.mkdir(parents=True)
    try:
        np.savez(out / 'influence_blocks.npz', source_id=source_ids, M=fit['M'], K=fit['K'], covariance=fit['V'])
        plot_grid(out, RHO, ellipsoid, sigma, 'rho_absolute_widths', 'total whitened L2 rho')
        plot_grid(out, BOX_MICROAS, box, sigma, 'box_absolute_widths', 'raw per-coordinate box (microas/year)')
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        lines = ['# Gaia EDR3 fixed-cohort linear bias sensitivity', '',
                 'Six coefficient Gaussian-reference sampling covariance and deterministic bias supports for the saved 4756-source frame design.',
                 'The 1.96 sigma plus support widths are componentwise reference widths, not joint or empirical coverage.',
                 'Rho is one total norm over all 9512 whitened coordinates. The box applies independently to raw pmRAstar and pmDEC.',
                 'No certified rho, physical box bias, cross-source covariance, selection law, Jacobi/CAS07 input, or verified Lean wrapper is available.',
                 '', '![rho](rho_absolute_widths.png)', '', '![box](box_absolute_widths.png)', '',
                 'The full six-by-six sampling covariance, source identities, supports, and numerical controls are in result.json.']
        (out / 'report.md').write_text('\n'.join(lines) + '\n')
        receipt = {'source_qualified_sha256': EXPECTED_NPZ_SHA256, 'source_result_sha256': sha256(saved_path),
                   'code_sha256': sha256(Path(__file__)), 'elapsed_seconds': time.perf_counter() - start,
                   'requested_author': 'gpt-6-sol/high', 'observed_author_runtime': 'UNKNOWN',
                   'source_R1_archive_sha256': R1_ARCHIVE_SHA256, 'source_R1_member_sha256': R1_MEMBER_SHA256, 'run_kind': 'fixed-cohort saved-source numerical consumer',
                   'no_new_gaia_query_or_CAS_run': True}
        (out / 'execution_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'rows': len(source_ids), 'covariance_relative_error': cov_rel,
                          'attainment_max_abs_mas_year': attainment}))
    except Exception as exc:
        (out / 'failure.json').write_text(json.dumps({'error': type(exc).__name__, 'message': str(exc)}, indent=2) + '\n')
        raise


def closeout_saved(result_dir: Path, out: Path):
    """Verify saved influence witnesses without refitting or changing the result."""
    if out.exists():
        raise ValueError('fresh closeout directory required')
    verify_r1_identity()
    qualified = SOURCE / 'qualified_rows.npz'
    if sha256(qualified) != EXPECTED_NPZ_SHA256:
        raise ValueError('immutable qualified-row source SHA256 mismatch')
    result_path, receipt_path = result_dir / 'result.json', result_dir / 'execution_receipt.json'
    block_path = result_dir / 'influence_blocks.npz'
    prior = json.loads(result_path.read_text())
    if prior['source']['qualified_rows_sha256'] != EXPECTED_NPZ_SHA256 or prior['cohort_count'] != 4756:
        raise ValueError('saved result has wrong cohort/source binding')
    if prior['proof_bridge']['source_R1_identity']['archive_sha256'] != R1_ARCHIVE_SHA256:
        raise ValueError('saved result has wrong R1 archive binding')
    with np.load(qualified, allow_pickle=False) as data:
        source_ids, c = data['source_id'], data['covariance']
    with np.load(block_path, allow_pickle=False) as data:
        block_ids, k, m, v = data['source_id'], data['K'], data['M'], data['covariance']
    if not np.array_equal(source_ids, block_ids) or k.shape != (6, 9512) or m.shape != (6, 4756, 2) or v.shape != (6, 6):
        raise ValueError('saved influence block shape/source IDs differ')
    if not all(np.isfinite(a).all() and not np.iscomplexobj(a) for a in (k, m, v, c)):
        raise ValueError('saved influence blocks or source covariance invalid')
    if relative_error(v, prior['sampling_covariance_mas2_year2']) > 1e-12:
        raise ValueError('saved influence covariance differs from original result')
    l = np.linalg.cholesky(c)
    fit = {'K': k, 'M': m, 'V': v, 'L': l}
    checks = []
    for rho, box_mas in ((0., 0.), (1., .01), (8., .05)):
        check = verify_support_attainment(fit, rho=rho, box_mas=box_mas, diagnostics=True)
        if max(check['ellipsoid_shift_max_abs_mas_year'], check['box_shift_max_abs_mas_year']) > 1e-12:
            raise AssertionError('saved support shift attainment failed')
        checks.append({'rho_total_whitened_L2': rho, 'box_mas_year_per_raw_coordinate': box_mas, **check})
    out.mkdir(parents=True)
    binding = {'original_result_path': str(result_path), 'original_result_sha256': sha256(result_path),
               'original_execution_receipt_path': str(receipt_path), 'original_execution_receipt_sha256': sha256(receipt_path),
               'original_influence_blocks_path': str(block_path), 'original_influence_blocks_sha256': sha256(block_path),
               'qualified_rows_sha256': EXPECTED_NPZ_SHA256, 'R1_archive_sha256': R1_ARCHIVE_SHA256,
               'R1_member_sha256': R1_MEMBER_SHA256}
    closeout = {'task': prior['task'], 'scope': 'saved-influence support witness norm and shift verification only; no refit',
                'source_binding': binding, 'checks': checks, 'status': 'FINITE_NUMERICAL_CHECK_PASS',
                'scientific_admission': 'UNCHANGED_DESCRIPTIVE_CONDITIONAL'}
    (out / 'closeout.json').write_text(json.dumps(closeout, indent=2) + '\n')
    receipt = {'code_sha256': sha256(Path(__file__)), 'closeout_sha256': sha256(out / 'closeout.json'),
               'source_binding': binding, 'execution': 'saved blocks plus source covariance; no new fit or Gaia query'}
    (out / 'execution_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': closeout['status'], 'checks': len(checks)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--closeout-from-result', type=Path)
    args = parser.parse_args()
    if args.closeout_from_result is None:
        run(args.output_dir)
    else:
        closeout_saved(args.closeout_from_result, args.output_dir)
