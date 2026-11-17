#!/usr/bin/env python3
"""Run the frozen R61 mixed-invariant grid directly from the pinned R58 carrier.

Usage:
  python run_r61_mixed_invariant.py --repo-root /path/to/repo --output /path/to/results

No input covariance is altered. Local optimization supplies witnesses; the
production component supplies float64 analytic global enclosures and gaps.
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
MAG_RMS_GRID = (0.0, 0.001, 0.005, 0.01)
C_KM_S = 299792.458
EXPECTED_NAMES = ['V_x_km_s', 'V_y_km_s', 'V_z_km_s', 'dH_x', 'dH_y',
                  'dH_z', 'kappa_0', 'kappa_1', 'kappa_2', 'kappa_3', 'kappa_4']


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_inputs(repo_root):
    directory = repo_root / R58_RESULTS
    manifest_path = directory / 'OWNED_TENSOR_RESULT.json'
    manifest = json.loads(manifest_path.read_text())
    carrier_path = directory / 'OWNED_TENSOR_CARRIERS.npz'
    recorded = manifest['carrier_sha256']
    observed = sha256(carrier_path)
    if observed != recorded:
        raise ValueError(f'R58 carrier SHA256 mismatch: recorded={recorded}, observed={observed}')
    ix = np.array([0, 1, 2, 6, 7, 8, 9, 10])
    units = np.r_[np.full(3, 1 / C_KM_S), np.ones(5)]
    inputs = {}
    with np.load(carrier_path, allow_pickle=False) as carrier:
        if carrier['parameter_names'].tolist() != EXPECTED_NAMES:
            raise ValueError('R58 parameter order does not match the locked alpha11 convention.')
        for model in MODELS:
            h11 = np.asarray(carrier[model + '__estimate11'], dtype=float)
            C11 = np.asarray(carrier[model + '__cov11'], dtype=float)
            if h11.shape != (11,) or C11.shape != (11, 11):
                raise ValueError(f'Unexpected R58 input shape for {model}.')
            h8 = h11[ix] * units
            C8 = C11[np.ix_(ix, ix)] * units[:, None] * units[None, :]
            inputs[model] = (h8, C8)
    provenance = {
        'manifest_path': str(manifest_path), 'manifest_sha256': sha256(manifest_path),
        'carrier_path': str(carrier_path), 'carrier_sha256_recorded': recorded,
        'carrier_sha256_observed': observed, 'carrier_identity_status': 'BYTE_IDENTITY_MATCH',
        'manifest_baseline': manifest.get('baseline'),
        'manifest_source_root_head': manifest.get('source_root_head'),
        'input_parameter_order11': EXPECTED_NAMES,
        'coordinate_order8': ['beta_x', 'beta_y', 'beta_z', *EXPECTED_NAMES[6:]],
        'velocity_conversion': 'beta=V/c; all velocity covariance rows and columns scaled by 1/c',
        'projection': 'principal covariance submatrix, unchanged chi-square-11 cutoff',
        'full_beta_kappa_cross_covariance': True,
    }
    return inputs, provenance


def witness_checks(result, h, C, E, cutoff, rho):
    checks = []
    for endpoint, key, feasible_index in (
        ('minimum', 'minimum_witness', 0), ('maximum', 'maximum_witness', 1)
    ):
        witness = result[key]
        beta = np.array(witness['beta'])
        kappa = np.array(witness['kappa'])
        Qcal = np.array(witness['Qcal'])
        dz = np.r_[beta, kappa] - h
        mahal = float(dz @ np.linalg.solve(C, dz))
        K = np.einsum('a,aij->ij', kappa, E)
        phi = float(beta @ (K - Qcal) @ beta)
        cal_norm = float(np.linalg.norm(Qcal, 'fro'))
        phi_error = abs(phi - witness['phi'])
        endpoint_error = abs(phi - result['feasible_range'][feasible_index])
        passed = bool(
            mahal <= cutoff + 1e-10
            and cal_norm <= np.sqrt(15 / 2) * rho + 1e-13
            and np.max(np.abs(Qcal - Qcal.T)) <= 1e-13
            and abs(np.trace(Qcal)) <= 1e-13
            and phi_error <= 1e-18 and endpoint_error <= 1e-18
        )
        checks.append({
            'endpoint': endpoint, 'passed': passed,
            'ellipsoid_quadratic': mahal, 'cutoff_excess': mahal - cutoff,
            'calibration_frobenius': cal_norm,
            'calibration_frobenius_bound': float(np.sqrt(15 / 2) * rho),
            'calibration_fullsky_rms': float(np.sqrt(2 / 15) * cal_norm),
            'phi_reconstruction_abs_error': phi_error,
            'feasible_endpoint_abs_error': endpoint_error,
        })
    return checks


def component_box_bound(h, C, E, cutoff, rho):
    """Superset bound derived from coordinate supports of this SAME ellipsoid."""
    bmax = np.abs(h[:3]) + np.sqrt(cutoff * np.diag(C)[:3])
    kmax = np.abs(h[3:]) + np.sqrt(cutoff * np.diag(C)[3:])
    return float(np.sum(kmax * np.einsum('i,aij,j->a', bmax, np.abs(E), bmax))
                 + np.sqrt(5) * rho * (bmax @ bmax))


def model_unions(records):
    unions = []
    for magnitude in MAG_RMS_GRID:
        selected = [r for r in records if r['calibration_fullsky_rms_mag'] == magnitude]
        outer_lo = min(r['result']['outer_range'][0] for r in selected)
        outer_hi = max(r['result']['outer_range'][1] for r in selected)
        feasible_lo = min(r['result']['feasible_range'][0] for r in selected)
        feasible_hi = max(r['result']['feasible_range'][1] for r in selected)
        unions.append({
            'calibration_fullsky_rms_mag': magnitude,
            'rho': float(magnitude / (5 / np.log(10))),
            'outer_range': [outer_lo, outer_hi],
            'feasible_range': [feasible_lo, feasible_hi],
            'minimum_bracket': [outer_lo, feasible_lo],
            'maximum_bracket': [feasible_hi, outer_hi],
            'max_gap': max(feasible_lo - outer_lo, outer_hi - feasible_hi),
            'minimum_enclosing_model': min(selected, key=lambda r: r['result']['outer_range'][0])['model'],
            'maximum_enclosing_model': max(selected, key=lambda r: r['result']['outer_range'][1])['model'],
            'minimum_witness_model': min(selected, key=lambda r: r['result']['feasible_range'][0])['model'],
            'maximum_witness_model': max(selected, key=lambda r: r['result']['feasible_range'][1])['model'],
            'interpretation': 'range over the finite union of seven projected original ellipsoids; no independence assumption',
        })
    return unions


def write_figure(records, inputs, E, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    selected_magnitudes = (0., .005)
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3), sharex=True, sharey=True)
    colors = ('#245c8a', '#c36623')
    selected = [r for r in records if r['calibration_fullsky_rms_mag'] in selected_magnitudes]
    low = min(r['result']['outer_range'][0] for r in selected) / 1e-7
    high = max(r['result']['outer_range'][1] for r in selected) / 1e-7
    margin = .07 * (high - low)
    centers = {}
    for model, (h, unused) in inputs.items():
        centers[model] = float(h[:3] @ np.einsum('a,aij->ij', h[3:], E) @ h[:3]) / 1e-7
    for ax, magnitude, color in zip(axes, selected_magnitudes, colors):
        for row, model in enumerate(MODELS):
            item = next(r for r in records if r['model'] == model and r['calibration_fullsky_rms_mag'] == magnitude)
            lo, hi = np.array(item['result']['outer_range']) / 1e-7
            ax.hlines(row, lo, hi, color=color, linewidth=2.8)
            ax.vlines([lo, hi], row - .11, row + .11, color=color, linewidth=1.3)
            ax.scatter([centers[model]], [row], color='#20252a', s=18, zorder=3)
        ax.axvline(0, color='#7b8790', linewidth=.8, linestyle=':')
        ax.set_title(f'Calibration full-sky RMS: {magnitude * 1000:g} mmag', fontsize=10)
        ax.set_xlabel(r'$\phi=\beta^T(K-Q_{\rm cal})\beta\quad[10^{-7}]$', fontsize=10)
        ax.set_xlim(low - margin, high + margin)
        ax.grid(axis='x', color='#e4e8eb', linewidth=.7)
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].set_yticks(np.arange(len(MODELS)), MODELS)
    axes[0].invert_yaxis()
    fig.suptitle('R61 mixed invariant: joint-ellipsoid enclosing ranges', fontsize=12)
    legend = [Line2D([0], [0], color='#245c8a', lw=2.8, label='Enclosing range'),
              Line2D([0], [0], color='#20252a', marker='o', linestyle='', markersize=4,
                     label='Center value at zero calibration')]
    fig.legend(handles=legend, loc='lower center', ncol=2, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, .08, 1, .94))
    files = []
    for suffix in ('png', 'pdf'):
        path = output / f'R61_MIXED_INVARIANT_INTERVALS.{suffix}'
        fig.savefig(path, dpi=180, bbox_inches='tight')
        files.append(path)
    plt.close(fig)
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='Output directory.')
    parser.add_argument('--atol', type=float, default=1e-10)
    parser.add_argument('--max-nodes', type=int, default=10000, help='Expansion cap per endpoint.')
    args = parser.parse_args(argv)
    repo_root, output = args.repo_root.resolve(), args.output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise FileExistsError(f'Refusing to overwrite a nonempty output path: {output}')
    output.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(repo_root / 'htt'), str(repo_root / 'htt' / 'src')]
    from htt.htt.infer.r61_mixed_invariant import mixed_shear_range, standard_stf_basis
    import htt.htt.infer.r61_mixed_invariant as component

    started = time.monotonic()
    inputs, provenance = load_inputs(repo_root)
    provenance['source_head'] = subprocess.run(
        ['git', '-C', str(repo_root), 'rev-parse', 'HEAD'],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    E = standard_stf_basis()
    cutoff = float(chi2.ppf(.95, 11))
    records = []
    for model in MODELS:
        h, C = inputs[model]
        for magnitude in MAG_RMS_GRID:
            rho = float(magnitude / (5 / np.log(10)))
            result = mixed_shear_range(h, C, E, cutoff, rho=rho,
                                       atol=args.atol, max_nodes=args.max_nodes)
            checks = witness_checks(result, h, C, E, cutoff, rho)
            component_bound = component_box_bound(h, C, E, cutoff, rho)
            width = float(result['outer_range'][1] - result['outer_range'][0])
            contained = bool(result['outer_range'][0] >= -component_bound - 1e-18
                             and result['outer_range'][1] <= component_bound + 1e-18)
            records.append({
                'model': model, 'calibration_fullsky_rms_mag': magnitude, 'rho': rho,
                'witness_checks': checks, 'result': result,
                'component_box': {
                    'law': 'coordinate-support superset of the same original ellipsoid',
                    'symmetric_bound': component_bound, 'width': 2 * component_bound,
                    'joint_enclosing_width': width,
                    'joint_to_component_box_width_ratio': width / (2 * component_bound),
                    'component_box_to_joint_width_ratio': 2 * component_bound / width,
                    'joint_range_contained': contained,
                },
            })
            print(f'{model} mag_rms={magnitude:g} status={result["status"]} '
                  f'gap={result["max_gap"]:.6g}', flush=True)

    figure_files = write_figure(records, inputs, E, output)
    checks_passed = all(all(w['passed'] for w in r['witness_checks'])
                        and r['component_box']['joint_range_contained'] for r in records)
    converged = all(r['result']['converged'] for r in records)
    result = {
        'schema': 'R61_MIXED_INVARIANT_RANGE_V1',
        'status': 'TOLERANCE_MET' if converged and checks_passed else 'INCOMPLETE_OR_CHECK_FAILED',
        'all_witness_checks_passed': checks_passed, 'all_endpoints_converged': converged,
        'arithmetic': 'FLOAT64_ANALYTIC_ENCLOSURE_NOT_FORMAL_INTERVAL_PROOF',
        'source': provenance, 'n_models': len(MODELS), 'n_grid_results': len(records),
        'model_order': list(MODELS), 'calibration_fullsky_rms_mag_grid': list(MAG_RMS_GRID),
        'confidence_level': .95, 'cutoff_dof': 11, 'cutoff': cutoff,
        'covariance_inflation_lambda': 1., 'c_km_s': C_KM_S,
        'calibration_conversion': 'rho=mag_rms/(5/ln(10))',
        'atol': args.atol, 'max_nodes_per_endpoint': args.max_nodes,
        'max_gap': max(r['result']['max_gap'] for r in records),
        'results': records, 'model_union': model_unions(records),
        'implementation': {
            'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
            'component_path': str(Path(component.__file__).resolve()),
            'component_sha256': sha256(component.__file__), 'runner_sha256': sha256(__file__),
        },
        'figures': [{'file': p.name, 'sha256': sha256(p)} for p in figure_files],
        'elapsed_seconds': time.monotonic() - started,
        'limitations': [
            'Ordinary float64 evaluates analytic enclosing formulas; no directed-rounding interval proof.',
            'Conditional fixed-covariance Gaussian law and the selected calibration domain are inherited assumptions.',
            'Local multistart extrema are witnesses only; each claimed numerical sharpness is an achieved global gap.',
            'Component-box comparison is a superset of the same ellipsoid, not an independent-component confidence law.',
        ],
    }
    path = output / 'R61_MIXED_INVARIANT_RESULT.json'
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(f'{result["status"]}: {path}', flush=True)
    return 0 if converged and checks_passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
