"""Bounded alternative-whitening check for the ill-conditioned owned sky72 law.

Reads completed carriers only. This resolves the concrete condition-number risk
without regenerating observations, pair sums, or the 42 scientific experiments.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import linalg, stats


def run(root):
    folder = Path(root).resolve() / 'docs/research_program/observational_publication_20261015/R64_DIRECTIONAL_HUBBLE_20261117'
    source = folder / 'RESULTS/AUGMENTED/AUGMENTED_CARRIERS.npz'
    a = np.load(source, allow_pickle=False)
    y = a['log_sky__y']
    cov = a['log_sky__covariance']
    val, vec = linalg.eigh(cov)
    if val[0] <= 0:
        raise ValueError('sky law is not positive definite')
    w = (vec / np.sqrt(val)).T
    rows = []
    for degree in (1, 2, 3):
        key = f'log_sky__J{degree}__common_field'
        x = a[key + '__original_response']
        scale = a[key + '__parameter_scale']
        design = (w @ x) * scale
        norm = np.linalg.norm(design, axis=0)
        u, s, vh = linalg.svd(design / norm, full_matrices=False)
        rank = int(np.sum(s > s[0] * 1e-12))
        if rank != x.shape[1]:
            raise ValueError('alternative whitening loses claimed rank')
        pseudo = ((vh.T / s) @ u.T) * (scale / norm)[:, None]
        est = pseudo @ (w @ y)
        new_cov = pseudo @ pseudo.T
        old_est = a[key + '__estimate']
        old_cov = a[key + '__covariance']
        old_res = a[key + '__likelihood_offset'] - a[key + '__likelihood_factor'] @ old_est
        new_res = w @ (y - x @ est)
        chi_old, chi_new = float(old_res @ old_res), float(new_res @ new_res)
        df = len(y) - rank
        se = np.sqrt(np.diag(old_cov))
        row = dict(degree=degree, rank=rank, parameters=x.shape[1], residual_df=df,
                   max_estimate_shift_in_marginal_sd=float(np.max(np.abs(est - old_est) / se)),
                   max_covariance_difference_in_sd_units=float(np.max(np.abs(new_cov - old_cov) / np.outer(se, se))),
                   residual_chi2_original=chi_old, residual_chi2_alternative=chi_new,
                   p_original=float(stats.chi2.sf(chi_old, df)), p_alternative=float(stats.chi2.sf(chi_new, df)))
        if (row['max_estimate_shift_in_marginal_sd'] > 1e-5 or
                row['max_covariance_difference_in_sd_units'] > 1e-5 or
                abs(row['p_original'] - row['p_alternative']) > 1e-5):
            raise ValueError('alternative whitening disagrees beyond the declared stability tolerance')
        rows.append(row)
    result = dict(schema='htt.r64.whitening_stability/1', status='PASS',
                  reason='Actual sky72 covariance has condition number about3.65e7; compare Cholesky and eigensystem whitening on its saved carrier.',
                  carrier_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  covariance_condition=float(val[-1] / val[0]), covariance_min_eigenvalue=float(val[0]),
                  tolerance=1e-5, scientific_models_added=0, rows=rows)
    target = folder / 'RESULTS/WHITENING_STABILITY.json'
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    run(parser.parse_args().root)
