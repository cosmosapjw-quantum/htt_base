#!/usr/bin/env python3
"""Fixed-selected-row A22 quotient controls from retained 102-column scores."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import beta, chi2


EXPECTED = {
    'full': '4d9406de69546e72dff79d4fc611703e8eb450944c4dcc254f8484c98a22d5da',
    'margin': 'e0148768bfdef02c9e9291ec0bd2b79e7b1e859a5c343dc2031259c876a671e5',
}
SIGNAL, ANGULAR, TEMPLATE, L4 = 18, 24, 42, 18
NMOCK, SEED = 1024, 230623


def interval(k, n):
    return [0.0 if k == 0 else float(beta.ppf(.025, k, n-k+1)),
            1.0 if k == n else float(beta.ppf(.975, k+1, n-k))]


def run_one(name, cache, quotient):
    raw = cache.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED[name] or quotient['input_sha256'] != sha:
        raise ValueError(f'{name}: source/quotient SHA mismatch')
    with np.load(cache, allow_pickle=False) as z:
        g = np.asarray(z['G'], dtype=float)
        selected_n = int(z['n'])
    if g.shape != (SIGNAL+ANGULAR+TEMPLATE+L4,)*2:
        raise ValueError(f'{name}: wrong Gram dimension')
    g = (g+g.T)/2
    nuisance = g[SIGNAL:, SIGNAL:]
    cross = g[:SIGNAL, SIGNAL:]
    cn = cho_factor(nuisance, lower=True, check_finite=True)
    inverse_cross = cho_solve(cn, cross.T)
    f = (g[:SIGNAL, :SIGNAL] - cross@inverse_cross)
    f = (f+f.T)/2
    cf = cho_factor(f, lower=True, check_finite=True)
    projection = np.concatenate([np.eye(SIGNAL), -inverse_cross.T], axis=1)
    estimator = cho_solve(cf, projection)
    conditional_covariance = cho_solve(cf, np.eye(SIGNAL))
    annihilation = estimator@g[:, SIGNAL:]
    relative_annihilation = np.linalg.norm(annihilation)/(
        np.linalg.norm(estimator@g[:, :SIGNAL])*np.linalg.norm(g[:, SIGNAL:]))
    # Match the adapter's two E1 depth contrasts, in the declared signal order.
    k = np.zeros((6, SIGNAL))
    for j in range(3):
        k[j, j], k[j, j+12] = 1, -1
        k[j+3, j+6], k[j+3, j+12] = 1, -1
    contrast_covariance = k@conditional_covariance@k.T
    published = np.asarray(quotient['contrast_covariance'])
    covariance_max_abs_delta = float(np.max(np.abs(contrast_covariance-published)))
    if covariance_max_abs_delta > 1e-7:
        raise ArithmeticError(f'{name}: independently computed covariance mismatch')

    # Reuse the old whole-field control's finite hypermodel and mock count, but
    # change the estimator to the unrestricted deterministic nuisance quotient.
    # Shared score noise makes the two injected controls directly comparable.
    rng = np.random.default_rng(SEED)
    latent = np.zeros((NMOCK, g.shape[0]))
    latent[:, SIGNAL:SIGNAL+ANGULAR] = rng.normal(size=(NMOCK, ANGULAR))*30/np.sqrt(ANGULAR)
    latent[:, SIGNAL+ANGULAR:SIGNAL+ANGULAR+TEMPLATE] = (
        rng.normal(size=(NMOCK, TEMPLATE))*30/np.sqrt(TEMPLATE))
    noise = rng.normal(size=(NMOCK, g.shape[0]))@np.linalg.cholesky(g).T
    baseline_scores = latent@g + noise
    base_estimate = baseline_scores@estimator.T
    cutoff = float(chi2.ppf(.95, SIGNAL))
    def summarize(kind, injection):
        scores = baseline_scores + injection@g
        estimate = scores@estimator.T
        stat = np.einsum('ni,ij,nj->n', estimate, f, estimate)
        covered = int(np.count_nonzero(stat <= cutoff))
        return dict(kind=kind, covered=covered, n=NMOCK, coverage=covered/NMOCK,
                    exact_binomial95=interval(covered, NMOCK),
                    max_abs_paired_estimator_shift_uasyr=float(np.max(np.abs(estimate-base_estimate))),
                    mean_bias_uasyr=estimate.mean(axis=0).tolist(),
                    covariance_model='fixed selected rows; Gaussian score covariance G; finite injected nuisance means')
    l4 = np.zeros_like(latent)
    l4[:, -L4:] = rng.normal(size=(NMOCK, L4))*12/np.sqrt(L4)
    template = np.zeros(g.shape[0])
    template[SIGNAL+ANGULAR] = 100.0
    controls = [summarize('omitted_E4_B4_RMS12_now_in_quotient', l4),
                summarize('template_correlated_mean100_now_in_quotient', template)]
    return dict(cache_sha256=sha, selected_sources=selected_n, augmented_signal_rank=quotient['signal_rank'],
                nuisance_rank=quotient['numerical_diagnostics']['nuisance_rank'],
                requested_contrast_estimable=quotient['contrast_estimable'],
                requested_contrast_nonestimability_residuals=quotient['nonestimability_norm'],
                exact_nuisance_annihilation_identity='M G[:,18:] = 0 in exact arithmetic for nonsingular nuisance and F blocks',
                max_abs_numeric_annihilation=float(np.max(np.abs(annihilation))),
                relative_numeric_annihilation=float(relative_annihilation),
                conditional_covariance_uas2yr2=conditional_covariance.tolist(),
                six_contrast_conditional_covariance_uas2yr2=contrast_covariance.tolist(),
                adapter_covariance_max_abs_delta=covariance_max_abs_delta,
                joint18_chi2_95_cutoff=cutoff, controls=controls)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache-dir', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    a = ap.parse_args()
    result = {'owner': 'htt', 'claim_tier': 'C1', 'status': 'CONDITIONAL_DIAGNOSTIC_ONLY',
              'transfer_source': 'none', 'source_model': 'A22 retained102x102 weighted normal equations',
              'signal_units': 'microarcsecond/year', 'seed': SEED, 'mock_count_per_control': NMOCK,
              'selection_caveat': 'Sources and reported-redshift bins are held fixed. Sourcewise proper-motion/classifier selection is not replayed or calibrated by these score-only controls.',
              'residual_caveat': 'Empirical correlated residual covariance and sourcewise selection law remain UNKNOWN; conditional Gaussian score covariance G is assumed.',
              'old_cut_Q_status': 'INAPPLICABLE under unrestricted fixed nuisance means; not reused',
              'scientific_admission': 'HOLD for K03/K05 cosmic acceleration and physical response claims',
              'cohorts': {}}
    for name in EXPECTED:
        quotient = json.loads((a.output_dir/f'{name}.json').read_text())
        result['cohorts'][name] = run_one(name, a.cache_dir/f'{name}_stats.npz', quotient)
    (a.output_dir/'controls.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
