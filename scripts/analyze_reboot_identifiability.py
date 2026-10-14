#!/usr/bin/env python3
"""Run a declared linear-response laboratory; this is not a CF4/CMB fit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from htt.infer.nuisance_rank import nuisance_projected_rank


def information(target, nuisance, covariance):
    """Profile Fisher information for a fixed, known SPD Gaussian covariance.

    Cholesky-whiten both blocks, then project out the fitted nuisance column
    space. This function makes no empirical covariance or physical-response claim.
    """
    target = np.asarray(target, dtype=float)
    nuisance = np.asarray(nuisance, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    if target.ndim != 2 or nuisance.ndim != 2:
        raise ValueError('responses must be matrices')
    n = target.shape[0]
    if nuisance.shape[0] != n or cov.shape != (n, n):
        raise ValueError('incompatible dimensions')
    if not all(np.isfinite(a).all() for a in (target, nuisance, cov)):
        raise ValueError('finite matrices required')
    if not np.allclose(cov, cov.T, rtol=1e-12, atol=1e-14):
        raise ValueError('symmetric covariance required')
    factor = np.linalg.cholesky(cov)
    a = np.linalg.solve(factor, target)
    b = np.linalg.solve(factor, nuisance)
    if b.shape[1]:
        # Column normalization preserves the nuisance span under a change of
        # parameter units; a tiny parameter coefficient is not zero response.
        norms = np.linalg.norm(b, axis=0)
        nonzero = norms > 0
        scaled = b[:, nonzero] / norms[nonzero]
        u, s, _ = np.linalg.svd(scaled, full_matrices=False)
        rank = np.count_nonzero(s > 1e-10 * s[0]) if s.size else 0
        a = a - u[:, :rank] @ (u[:, :rank].T @ a)
    return a.T @ a


def laboratory():
    # Dimensionless standardized observations and parameters. These responses are
    # specified examples, not approximations to an observed cosmological transfer.
    local = np.kron(np.ones((4, 1)), np.eye(3))
    depths = np.array([0., 1., 2., 3.])
    depth_response = np.kron(depths[:, None], np.eye(3))
    shell_cov = .35 ** np.abs(np.subtract.outer(np.arange(4), np.arange(4)))
    covariance = np.kron(shell_cov, np.diag([1., 1.5, 2.]) ** 2)
    cases = []
    for name, target, nuisance in (
        ('shared_constant', local, local),
        ('depth_response', depth_response, local),
        ('free_shell_nuisance', depth_response, np.eye(12)),
    ):
        audit = nuisance_projected_rank(target, nuisance, covariance).as_payload()
        if not np.isfinite(audit['condition_number']):
            audit['condition_number'] = None
        cases.append({'case': name, 'rank': audit['projected_rank'],
                      'singular_values': audit['singular_values'],
                      'profile_information': information(target, nuisance, covariance).tolist(),
                      'audit': audit})
    eps = np.geomspace(1e-5, 1., 81)
    curve = []
    for e in eps:
        target = local + e * depth_response
        audit = nuisance_projected_rank(target, local, covariance)
        curve.append({'depth_amplitude': float(e),
                      'minimum_singular_value': float(min(audit.singular_values)),
                      'maximum_singular_value': float(max(audit.singular_values))})
    b = np.ones((3, 1)); g = np.arange(3.)[:, None]
    return {'schema': 'htt.reboot-response-laboratory/1', 'owner': 'htt',
            'status': 'SYNTHETIC_LINEAR_RESPONSE_EXPERIMENT', 'claim_tier': 'C0',
            'artifact_mode': 'EXPLORATORY_NONAUTHORITATIVE',
            'scope': 'Known SPD Gaussian covariance; declared dimensionless responses',
            'transfer_source': 'none', 'null_status': 'NO_OBSERVED_HYPOTHESIS_TEST',
            'covariance_status': 'SPECIFIED_SYNTHETIC_KNOWN_SPD',
            'allowed_use': 'Check design rank and conditioning logic for future response providers',
            'forbidden_uses': ['observed tilt estimate', 'Bianchi family identification',
                               'empirical uncertainty or response-rank certification'],
            'model': 'y = B beta_local + G beta_global + noise',
            'units': 'dimensionless standardized observable and parameter coordinates',
            'covariance': covariance.tolist(), 'local_response': local.tolist(),
            'global_depth_response': depth_response.tolist(), 'cases': cases,
            'near_degeneracy': curve,
            'exact_three_row_check': {
                'identity_information': float(information(g, b, np.eye(3))[0, 0]),
                'heteroscedastic_information': float(information(g, b, np.diag([1., 4., 9.]))[0, 0]),
                'references': {'identity': '2', 'heteroscedastic': '26/49'},
                'wolfram': 'research/WOLFRAM_CHECK.json; algebra sanity, not four-axis CAS'},
            'interpretation': [
                'The constant target is absorbed by the local nuisance response.',
                'The specified depth response adds three identifiable linear directions.',
                'A free nuisance vector in every shell absorbs all target directions.',
                'Near-collinear full-rank responses can still carry arbitrarily little information.',
                'Actual local/global discrimination requires physical responses, covariance and remainder.']}


def write_result(output_dir):
    result = laboratory()
    result['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / 'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    plt.rcParams.update({'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(10.3, 4.5))
    labels = ['Constant\nresponse', 'Depth\nresponse', 'Free shell\nnuisance']
    axes[0].bar(labels, [c['rank'] for c in result['cases']], color=['#999999','#0072B2','#D55E00'])
    axes[0].set(ylabel='Rank after nuisance projection', ylim=(0,3.5), yticks=[0,1,2,3],
                title='Which directions survive?')
    x = [r['depth_amplitude'] for r in result['near_degeneracy']]
    axes[1].loglog(x, [r['minimum_singular_value'] for r in result['near_degeneracy']],
                   label='smallest singular value', color='#0072B2')
    axes[1].loglog(x, [r['maximum_singular_value'] for r in result['near_degeneracy']],
                   label='largest singular value', color='#D55E00')
    axes[1].set(xlabel='Added depth-response amplitude', ylabel='Whitened singular value',
                title='Full rank can be weakly identified')
    axes[1].legend(fontsize=8)
    fig.suptitle('Local/global response laboratory | synthetic fixed-covariance model', fontsize=12)
    fig.text(.5,.014,'HTT C0 exploratory; no CMB/CF4 fit or physical transfer. All coordinates are dimensionless.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=(0,.04,1,.95))
    for ext in ('png','pdf'):
        fig.savefig(output_dir / f'response_identifiability.{ext}', dpi=170)
    plt.close(fig)
    (output_dir/'report.md').write_text('''# Local/global response laboratory

This generated experiment uses declared dimensionless matrices and a known
correlated Gaussian covariance. It is not an observational fit. The existing HTT
`nuisance_projected_rank` code is reused.

The constant target has rank 0 after profiling local boost. The specified depth
target has rank 3; a free vector nuisance in each shell reduces its rank to 0.
The smallest singular value decreases linearly with the added depth amplitude:
formal full rank alone does not provide useful precision. The three-row exact
check gives information 2 with identity noise and 26/49 with variances (1,4,9),
matching the independent Wolfram algebra check.

![Synthetic response diagnosis](response_identifiability.png)

Physical continuation: replace these explicit example matrices with
source-bound local observer, matter-tilt and survey response derivatives. State
parameter units and scales before singular-value thresholds; validate derivatives
and truncation bounds, then test null-calibrated power. No universal no-go or
new physical identification follows from the example.
''')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = write_result(args.output_dir)
    print(json.dumps({'status':result['status'], 'ranks':[c['rank'] for c in result['cases']]}))
