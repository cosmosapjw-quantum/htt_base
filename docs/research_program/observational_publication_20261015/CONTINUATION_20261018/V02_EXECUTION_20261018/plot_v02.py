"""Plots only generated V02 numerical diagnostics, no inference."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE/'results'


def main():
    report = json.loads((OUT/'V02_FINITE_RESPONSE.json').read_text())
    if (OUT/'V02_FINITE_RESPONSE.png').exists(): raise FileExistsError('CREATE_ONLY_FIGURE')
    rows = [r for r in report['experiments'] if r['label'] == 'generic']
    beta = np.array([r['speed'] for r in rows])
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.7), constrained_layout=True)
    for key, label, marker in (
        ('injection_norm_microK', 'finite injection', 'o'),
        ('finite_minus_linear_norm_microK', 'finite minus linear', 's'),
        ('finite_mode_leakage_ell6_16_to_fit2_5_microK', 'ell 6–16 leakage', '^'),
        ('wrong_boost_after_beam_delta_microK', 'wrong beam order difference', 'd')):
        ax[0].loglog(beta, [r[key] for r in rows], marker=marker, label=label)
    ax[0].set(xlabel='injected |beta| (dimensionless)', ylabel='retained coefficient norm [microK]')
    ax[0].legend(fontsize=7)
    ax[1].semilogx(beta, [r['remainder_over_beta_squared_microK'] for r in rows], 'o-')
    ax[1].set(xlabel='injected |beta|', ylabel='remainder norm / |beta|² [microK]')
    singular = report['geometric_response']['singular_values_microK_per_beta']
    ax[2].bar(np.arange(1, 4), singular, color='#456e92')
    ax[2].set(xticks=[1, 2, 3], xlabel='geometric response column index', ylabel='singular value [microK per beta]')
    for a in ax: a.grid(alpha=.2)
    fig.suptitle('SMICA_FULL finite delivered-fit surrogate; actual T mask and INT_BEAM\n'
                 'Diagnostic only: no physical observer response, covariance or velocity inference', fontsize=10)
    for suffix in ('png', 'pdf'): fig.savefig(OUT/('V02_FINITE_RESPONSE.'+suffix), dpi=180)
    plt.close(fig)


if __name__ == '__main__': main()
