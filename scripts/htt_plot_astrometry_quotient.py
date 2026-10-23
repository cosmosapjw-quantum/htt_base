#!/usr/bin/env python3
"""Plot all fixed-model contrasts from htt_astrometry_quotient summary JSON.

Reads retained summaries only, never raw rows. Bars are coordinate projections
of each model's joint three-dimensional Gaussian ellipsoid, not marginal bars.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np


def render(source: Path, output: Path):
    raw = source.read_bytes()
    data = json.loads(raw)
    if (data['owner'], data['transfer_source'], data['status']) != ('htt', 'none', 'CONDITIONAL'):
        raise ValueError('expected conditional HTT summary with no transfer')
    cohorts = data['cohorts']
    if [c['cohort'] for c in cohorts] != ['full', 'known_cut_margin']:
        raise ValueError('expected full and known_cut_margin cohorts')
    fig, axes = plt.subplots(2, 3, figsize=(16, 15), sharex=True, sharey=True)
    colors = ['#176b92', '#a64915']
    for row, cohort in enumerate(cohorts):
        models = cohort['fixed_models']
        expected = {(ell, ta, tt) for ell in (2, 3) for ta in (0, 10, 30, 100) for tt in (0, 10, 30, 100)}
        keys = [(m['lmax'], m['tau_angular'], m['tau_template']) for m in models]
        if len(keys) != 32 or set(keys) != expected:
            raise ValueError('expected each of the 32 declared fixed models exactly once')
        mean = np.array([m['low_minus_high_E1_uasyr'] for m in models])
        covariance = np.array([m['covariance_uas2yr2'] for m in models])
        threshold = cohort['fixed_family_union_95']['chi2_threshold']
        if cohort['fixed_family_union_95']['chi2_df'] != 3 or not np.isclose(threshold, 7.814727903251179):
            raise ValueError('expected 95% joint chi-square(3) ellipsoids')
        if not np.isfinite(mean).all() or not np.isfinite(covariance).all() or np.any(np.linalg.eigvalsh(covariance) <= 0):
            raise ValueError('finite means and positive definite full contrast covariances required')
        # Projection of (theta-mu)' V^-1 (theta-mu) <= q is mu_j +/- sqrt(q V_jj).
        halfwidth = np.sqrt(threshold * np.diagonal(covariance, axis1=1, axis2=2))
        y = np.arange(32)
        labels = [f'{ell} / {ta:3g} / {tt:3g}' for ell, ta, tt in keys]
        for j, ax in enumerate(axes[row]):
            ax.errorbar(mean[:, j], y, xerr=halfwidth[:, j], fmt='o', ms=3,
                        lw=1.1, capsize=2, color=colors[row])
            ax.axvline(0, color='#666666', ls='--', lw=.8)
            ax.axhline(15.5, color='#aaaaaa', lw=.8)
            ax.set_yticks(y, labels, fontsize=8, fontfamily='monospace')
            ax.set_ylim(31.8, -.8)
            ax.grid(axis='x', alpha=.2)
            ax.set_xlabel('Low minus high reported-z E1 (microarcsec/year)')
            ax.set_title(f'{cohort["cohort"]}: E{"xyz"[j]} | n = {cohort["n"]:,}', fontsize=12)
            if j == 0:
                ax.set_ylabel('Fixed model: lmax / angular RMS / template RMS', labelpad=12)
    fig.suptitle('Reported-redshift E1 contrasts: 64 fixed-model fits\n'
                 'Points: GLS means | Bars: coordinate projections of joint 95% ellipsoids (3 dof)',
                 fontsize=16, y=.98)
    fig.text(.5, .045, 'Conditional on each declared Gaussian covariance model and the same fixed selected design.\n'
             'Reported-z bins: low [0, 1), high [2, 10). RMS values are in microarcsec/year.\n'
             'Bars are projections, not the full ellipsoids; no empirical coverage or cosmic-acceleration claim.\n'
             'HTT diagnostic; transfer source: none. Selection is not rerun; original scientific nodes remain unpromoted.',
             ha='center', va='center', fontsize=10, linespacing=1.5)
    fig.subplots_adjust(left=.135, right=.98, bottom=.13, top=.91, hspace=.18, wspace=.12)
    output.parent.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams['svg.fonttype'] = 'none'
    matplotlib.rcParams['svg.hashsalt'] = 'htt-fixed-contrast-v1'
    sha = hashlib.sha256(raw).hexdigest()
    fig.savefig(output, metadata={'Date': None, 'Title': 'Conditional fixed-selected-design redshift E1 contrasts',
                'Description': f'Owner HTT; transfer none; summary sha256:{sha}; input sha256:{data["input_sha256"]}; '
                '64 fixed-model means with joint-ellipsoid coordinate projections; no empirical coverage or cosmic claim.'})
    plt.close(fig)
    return {'models': sum(len(c['fixed_models']) for c in cohorts), 'summary_sha256': sha,
            'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.input, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
