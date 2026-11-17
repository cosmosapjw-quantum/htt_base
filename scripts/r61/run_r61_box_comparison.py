#!/usr/bin/env python3
"""R8 comparison correction: reuse mixed enclosures, compute the actual box range.

The older triangle-inequality bound is preserved and separately named.
No mixed-invariant fit, ellipsoid optimization, or scientific scope is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import chi2

R58_RESULTS = Path('docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS')
MODELS = ('log', 'log_mono', 'log_split', 'log_survey', 'log_mono_radial',
          'log_mono_galactic', 'log_mono_error')
MAG_GRID = (0., .001, .005, .01)
EXPECTED_MIXED_SOURCE_HEAD = 'fb6ae9f21585e194ef29dabc91d79a529e0ac57e'
EXPECTED_NAMES = ['V_x_km_s', 'V_y_km_s', 'V_z_km_s', 'dH_x', 'dH_y', 'dH_z',
                  'kappa_0', 'kappa_1', 'kappa_2', 'kappa_3', 'kappa_4']


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def require_equal(observed, expected, what):
    if observed != expected:
        raise ValueError(f'{what} mismatch: observed={observed!r}; expected={expected!r}')


def resolve_recorded_path(recorded, repo_root):
    path = Path(recorded)
    return path if path.is_absolute() else repo_root/path


def load_and_verify(repo_root, mixed_path, mixed_runner_path):
    manifest_path = repo_root/R58_RESULTS/'OWNED_TENSOR_RESULT.json'
    carrier_path = repo_root/R58_RESULTS/'OWNED_TENSOR_CARRIERS.npz'
    manifest = json.loads(manifest_path.read_text())
    mixed = json.loads(mixed_path.read_text())
    carrier_sha, manifest_sha = sha256(carrier_path), sha256(manifest_path)
    require_equal(carrier_sha, manifest['carrier_sha256'], 'R58 carrier/manifest SHA256')
    source = mixed['source']
    for key in ('carrier_sha256_recorded', 'carrier_sha256_observed'):
        require_equal(source[key], carrier_sha, 'existing mixed source '+key)
    require_equal(source['manifest_sha256'], manifest_sha, 'existing mixed R58 manifest SHA256')
    require_equal(source['source_head'], EXPECTED_MIXED_SOURCE_HEAD, 'existing mixed source HEAD')
    component_path = resolve_recorded_path(mixed['implementation']['component_path'], repo_root)
    require_equal(sha256(component_path), mixed['implementation']['component_sha256'],
                  'existing mixed component SHA256')
    require_equal(sha256(mixed_runner_path), mixed['implementation']['runner_sha256'],
                  'existing mixed runner SHA256')
    require_equal(mixed['status'], 'TOLERANCE_MET', 'existing mixed status')
    require_equal(mixed['all_witness_checks_passed'], True, 'existing mixed witness checks')
    require_equal(mixed['all_endpoints_converged'], True, 'existing mixed convergence')
    require_equal(mixed['model_order'], list(MODELS), 'existing mixed model order')
    require_equal(mixed['calibration_fullsky_rms_mag_grid'], list(MAG_GRID), 'existing mixed grid')
    require_equal(mixed['covariance_inflation_lambda'], 1., 'existing mixed covariance lambda')
    require_equal(mixed['cutoff_dof'], 11, 'existing mixed cutoff degrees of freedom')
    cutoff = float(chi2.ppf(.95, 11))
    if abs(mixed['cutoff']-cutoff) > 1e-12:
        raise ValueError('Existing mixed cutoff differs from chi-square-11(.95).')
    ix = [0, 1, 2, 6, 7, 8, 9, 10]
    units = np.r_[np.full(3, 1/299792.458), np.ones(5)]
    inputs = {}
    with np.load(carrier_path, allow_pickle=False) as carrier:
        require_equal(carrier['parameter_names'].tolist(), EXPECTED_NAMES, 'R58 parameter names')
        for model in MODELS:
            h11 = np.asarray(carrier[model+'__estimate11'], float)
            C11 = np.asarray(carrier[model+'__cov11'], float)
            if h11.shape != (11,) or C11.shape != (11, 11):
                raise ValueError('R58 array shape mismatch for '+model)
            h = h11[ix]*units
            C = C11[np.ix_(ix, ix)]*units[:, None]*units[None, :]
            np.linalg.cholesky(C)
            inputs[model] = (h, C)
    lookup = {(r['model'], r['calibration_fullsky_rms_mag']): r for r in mixed['results']}
    if len(lookup) != 28 or len(mixed['results']) != 28 or set(lookup) != {(m,g) for m in MODELS for g in MAG_GRID}:
        raise ValueError('Existing mixed results do not contain the exact distinct 7-by-4 grid.')
    checks = {
        'status': 'VERIFIED', 'existing_mixed_json_path': str(mixed_path),
        'existing_mixed_json_sha256': sha256(mixed_path),
        'R58_manifest_path': str(manifest_path), 'R58_manifest_sha256': manifest_sha,
        'R58_carrier_path': str(carrier_path), 'R58_carrier_sha256': carrier_sha,
        'existing_mixed_source_head': source['source_head'],
        'existing_component_path': str(component_path), 'existing_component_sha256': sha256(component_path),
        'existing_runner_path': str(mixed_runner_path), 'existing_runner_sha256': sha256(mixed_runner_path),
        'new_runner_source_head': subprocess.run(['git', '-C', str(repo_root), 'rev-parse', 'HEAD'],
                                               check=True, capture_output=True, text=True).stdout.strip(),
        'head_interpretation': 'existing mixed source HEAD is pinned; current integration HEAD is recorded separately',
    }
    return inputs, lookup, cutoff, checks


def compare_one(h, C, E, cutoff, old, box_function):
    rho = float(old['rho'])
    expected_rho = old['calibration_fullsky_rms_mag']/(5/np.log(10))
    if abs(rho-expected_rho) > 1e-16:
        raise ValueError('Existing mixed calibration conversion is inconsistent.')
    widths = np.sqrt(cutoff*np.diag(C))
    low, high = h-widths, h+widths
    box = box_function(low[:3], high[:3], low[3:], high[3:], E, rho=rho)
    outer = np.array(old['result']['outer_range'], float)
    feasible = np.array(old['result']['feasible_range'], float)
    mixed_width_upper = float(outer[1]-outer[0])
    mixed_width_lower = float(feasible[1]-feasible[0])
    if mixed_width_lower <= 0:
        raise ValueError('Expected positive feasible mixed range width.')
    box_width = box['width']
    box_guard = box['guard']
    bmax = np.maximum(np.abs(low[:3]), np.abs(high[:3]))
    kmax = np.maximum(np.abs(low[3:]), np.abs(high[3:]))
    legacy_bound = float(np.sum(kmax*np.einsum('i,aij,j->a', bmax, np.abs(E), bmax))
                         + np.sqrt(5)*rho*float(bmax@bmax))
    recorded_bound = old['component_box']['symmetric_bound']
    if abs(legacy_bound-recorded_bound) > 1e-12*max(legacy_bound, np.finfo(float).tiny):
        raise ValueError('Recomputed legacy triangle bound does not match existing mixed result.')
    checks = {
        'joint_feasible_range_inside_box_guarded_range': bool(
            feasible[0] >= box['guarded_range'][0]-1e-18 and feasible[1] <= box['guarded_range'][1]+1e-18),
        'box_candidates_inside_legacy_triangle_range': bool(
            box['range'][0] >= -legacy_bound-1e-18 and box['range'][1] <= legacy_bound+1e-18),
        'box_witness_constraints': [],
    }
    for key in ('minimum_witness', 'maximum_witness'):
        w = box[key]
        beta, kappa, Q = np.array(w['beta']), np.array(w['kappa']), np.array(w['Qcal'])
        K = np.einsum('a,aij->ij', kappa, E)
        reconstructed = float(beta@(K-Q)@beta)
        checks['box_witness_constraints'].append({
            'endpoint': key,
            'beta_inside': bool(np.all(beta >= low[:3]) and np.all(beta <= high[:3])),
            'kappa_inside': bool(np.all(kappa >= low[3:]) and np.all(kappa <= high[3:])),
            'calibration_norm_passed': bool(np.linalg.norm(Q, 'fro') <= np.sqrt(15/2)*rho+1e-13),
            'phi_reconstruction_abs_error': abs(reconstructed-w['phi']),
        })
    # The interval below accounts for the already-known joint endpoint gaps.
    # The box guard is numerical, so the ratio bracket is not formally certified.
    ratio_bracket = [max(box_width-2*box_guard, 0)/mixed_width_upper,
                     (box_width+2*box_guard)/mixed_width_lower]
    return {
        'model': old['model'], 'calibration_fullsky_rms_mag': old['calibration_fullsky_rms_mag'], 'rho': rho,
        'joint_ellipsoid_reused': {
            'outer_range': outer.tolist(), 'feasible_range': feasible.tolist(),
            'width_bracket': [mixed_width_lower, mixed_width_upper],
            'maximum_endpoint_gap': old['result']['max_gap'],
            'source': 'unaltered existing R61 mixed endpoint result',
        },
        'actual_coordinate_box': box,
        'legacy_triangle_bound': {
            'symmetric_bound': legacy_bound, 'width': 2*legacy_bound,
            'legacy_width_over_joint_enclosing_width': 2*legacy_bound/mixed_width_upper,
            'interpretation': 'additional triangle-inequality relaxation, not the exact coordinate-box range',
        },
        'comparison': {
            'actual_box_width_over_joint_enclosing_width': box_width/mixed_width_upper,
            'actual_box_width_over_joint_width_bracket_with_numerical_guard': ratio_bracket,
            'legacy_triangle_width_over_actual_box_width': 2*legacy_bound/box_width,
            'interpretation': 'The actual-box/joint ratio isolates replacing the joint ellipsoid by its coordinate-support box; the legacy/actual-box ratio isolates additional triangle-bound slack.',
        },
        'checks': checks,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mixed-result', type=Path, help='Defaults to sibling MIXED/R61_MIXED_INVARIANT_RESULT.json.')
    parser.add_argument('--mixed-runner', type=Path, help='Defaults to scripts/r61/run_r61_mixed_invariant.py under repo root.')
    args = parser.parse_args(argv)
    repo_root, output = args.repo_root.resolve(), args.output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise FileExistsError(f'Refusing to overwrite a nonempty output path: {output}')
    mixed_path = args.mixed_result.resolve() if args.mixed_result else output.parent/'MIXED'/'R61_MIXED_INVARIANT_RESULT.json'
    mixed_runner = args.mixed_runner.resolve() if args.mixed_runner else repo_root/'scripts/r61/run_r61_mixed_invariant.py'
    sys.path[:0] = [str(repo_root/'htt'), str(repo_root/'htt/src')]
    from htt.htt.infer.r61_box_comparison import mixed_invariant_box_range
    from htt.htt.infer.r61_mixed_invariant import standard_stf_basis
    import htt.htt.infer.r61_box_comparison as component
    started = time.monotonic()
    inputs, old, cutoff, provenance = load_and_verify(repo_root, mixed_path, mixed_runner)
    E = standard_stf_basis()
    results = []
    for model in MODELS:
        h, C = inputs[model]
        for magnitude in MAG_GRID:
            row = compare_one(h, C, E, cutoff, old[model, magnitude], mixed_invariant_box_range)
            results.append(row)
            print(model, magnitude, row['actual_coordinate_box']['range'],
                  row['comparison']['actual_box_width_over_joint_enclosing_width'], flush=True)
    passed = all(r['checks']['joint_feasible_range_inside_box_guarded_range']
                 and r['checks']['box_candidates_inside_legacy_triangle_range']
                 and all(w['beta_inside'] and w['kappa_inside'] and w['calibration_norm_passed']
                         and w['phi_reconstruction_abs_error'] <= 1e-18
                         for w in r['checks']['box_witness_constraints']) for r in results)
    exact_ratios = [r['comparison']['actual_box_width_over_joint_enclosing_width'] for r in results]
    slack_ratios = [r['comparison']['legacy_triangle_width_over_actual_box_width'] for r in results]
    payload = {
        'schema': 'R61_COORDINATE_BOX_COMPARISON_V1',
        'status': 'COMPARISON_CHECKS_PASSED' if passed else 'COMPARISON_CHECK_FAILED',
        'scope': 'R8 interpretation correction using existing 28 mixed endpoints; no new scientific loop',
        'arithmetic': 'FLOAT64_FINITE_FACE_ENUMERATION_NOT_FORMAL_INTERVAL_PROOF',
        'source_checks': provenance, 'confidence_level': .95, 'cutoff_dof': 11,
        'cutoff': cutoff, 'covariance_inflation_lambda': 1., 'n_results': len(results),
        'results': results,
        'summary': {
            'actual_box_over_joint_enclosing_width_ratio_range': [min(exact_ratios), max(exact_ratios)],
            'legacy_triangle_over_actual_box_width_ratio_range': [min(slack_ratios), max(slack_ratios)],
            'maximum_box_numerical_guard': max(r['actual_coordinate_box']['guard'] for r in results),
            'interpretation_correction': 'The former legacy-bound/joint-width factor combines coordinate-box geometry and triangle-inequality slack. Only the separately reported actual-box/joint factor measures the coordinate-domain replacement.',
        },
        'implementation': {
            'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
            'component_path': str(Path(component.__file__).resolve()),
            'component_sha256': sha256(component.__file__), 'runner_sha256': sha256(__file__),
        },
        'elapsed_seconds': time.monotonic()-started,
        'limitations': ['Finite exact-arithmetic characterization evaluated in float64; numerical guard is not a formal interval proof.',
                        'The coordinate box is an enclosing superset of the same ellipsoid, not a separately calibrated confidence law.',
                        'Existing joint endpoints and their gaps are reused without rerunning or modifying them.'],
    }
    output.mkdir(parents=True, exist_ok=True)
    target = output/'R61_BOX_COMPARISON_RESULT.json'
    target.write_text(json.dumps(payload, indent=2, allow_nan=False)+'\n')
    print(payload['status'], target, flush=True)
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
