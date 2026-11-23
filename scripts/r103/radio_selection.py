"""Sharp extra covariance budgets for the observed same-catalogue NVSS contrast."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


SOURCE = Path('docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117/RESULTS/INTERPRETATION_SUMMARY.json')
SOURCE_SHA = '203f6cf070661afb923aa095ce992278c720f3e7a7149107c14c7e8a28c761c7'


def extra_covariance_budget(d, covariance, threshold):
    """Minimize ||E||_op over PSD E s.t. d'(C+E)^-1 d <= threshold."""
    d = np.asarray(d, dtype=float)
    c = np.asarray(covariance, dtype=float)
    if (d.ndim != 1 or c.shape != (len(d), len(d)) or len(d) == 0
            or not np.all(np.isfinite(d)) or not np.all(np.isfinite(c))
            or not np.allclose(c, c.T, rtol=1e-12, atol=0)):
        raise ValueError('finite vector and symmetric conformable covariance required')
    eig, basis = np.linalg.eigh(c)
    if min(eig) <= 0 or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError('positive definite source covariance and positive finite threshold required')
    projected = basis.T @ d
    def worst(e):
        return float(np.sum(projected**2/(eig+e)))

    base = worst(0.)
    if base <= threshold:
        return {'wald_working': base, 'threshold': threshold, 'extra_spectral_variance': 0.,
                'extra_sd': 0., 'rank_one_axis': None, 'achieved_wald': base}
    # E <= e I, and d' (C+eI)^-1 d decreases continuously to zero.
    lo, hi = 0., float((d@d)/threshold)
    for _ in range(80):
        mid = (lo+hi)/2
        if worst(mid) > threshold:
            lo = mid
        else:
            hi = mid
    v = basis @ (projected/(eig+hi))
    v /= np.linalg.norm(v)
    # (C+e vv') (C+eI)^-1 d = d because v parallels (C+eI)^-1 d.
    actual = float(d @ np.linalg.solve(c + hi*np.outer(v,v), d))
    return {'wald_working': base, 'threshold': threshold, 'extra_spectral_variance': hi,
            'extra_sd': math.sqrt(hi), 'rank_one_axis': v.tolist(), 'achieved_wald': actual}


def analyze(root):
    raw = (root / SOURCE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('R65 source identity mismatch')
    summary = json.loads(raw)
    fits = {}
    for name, fit in summary['source_definition_paired_results'].items():
        c = fit['covariance']
        # Contrast is integrated minus peak. Both off-diagonal blocks matter.
        contrast = np.asarray(c['covariance_joint'])
        h = np.block([-np.eye(2), np.eye(2)])
        recon = h @ contrast @ h.T
        discrepancy = np.max(np.abs(recon - c['covariance_contrast']))
        if discrepancy > 1e-16 or c['physical_LSS_calibrated']:
            raise ValueError(f'{name}: unexpected input covariance or source scope')
        fits[name] = {
            'shared_objects': c['n_shared'],
            'delta_log_intensity_ICRS_xy': fit['integrated_minus_peak'],
            'paired_covariance_replay_max_abs': float(discrepancy),
            'working_contours': {
                str(level): extra_covariance_budget(fit['integrated_minus_peak'], recon, -2*math.log1p(-level))
                for level in (0.95, 0.99)},
        }
    return {
        'schema': 'htt.r103.radio_covariance_budget/1', 'source_summary': str(SOURCE),
        'source_sha256': SOURCE_SHA, 'input_catalog_sha256': summary['sources']['NVSS_provider']['sha256'],
        'covariance_norm': 'spectral norm, Euclidean ICRS xy log-intensity coefficient coordinates',
        'fits': fits, 'physical_LSS_calibrated': False, 'physical_Pi': None,
        'sampling_scope': 'Actual R65 paired contrast, conditioned on the empirical Poisson source influence covariance. Extra positive covariance is an identified sensitivity budget. The physical extra covariance and its orientation are unknown.',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    record = json.dumps(analyze(Path(__file__).resolve().parents[2]), indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(record)
    else:
        print(record, end='')


if __name__ == '__main__':
    main()
