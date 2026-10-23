"""Render the scientific author's exact rational witness, without sky replay."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

p = Path(__file__).resolve().parent
r = json.loads((p / 'RESULT.json').read_text())
# Frozen author's recipe; these values come from the exact rational algebra.py.
v = [6/5, -13/5, 8/5, -1/5]
fig, axes = plt.subplots(1, 2, figsize=(10.8, 5.5))
x = np.arange(1, 5)
axes[0].bar(x-.17, v, width=.34, label='P h')
axes[0].bar(x+.17, v, width=.34, label='P (h − a)')
axes[0].axhline(0, color='black', lw=.7)
axes[0].set_xticks(x)
axes[0].set_xlabel('Rational witness coordinate')
axes[0].set_ylabel('Projected coordinate (arbitrary units)')
axes[0].legend()
rank = [r['combined_single_parameter_nuisance_rank'], r['incorrectly_split_nuisance_rank']]
axes[1].bar([0, 1], rank, color=['tab:green', 'tab:orange'])
axes[1].set_xticks([0, 1], ['Shared parameter\ncombined response', 'Incorrect independent\nsplit parameters'])
axes[1].set_ylabel('Nuisance rank in 2D rational witness')
axes[1].set_ylim(0, 2.6)
axes[1].set_yticks([0, 1, 2])
for i, q in enumerate(rank):
    axes[1].text(i, q+.06, f'Surviving dimension: {2-q}', ha='center', fontsize=9)
fig.suptitle('Rational algebra witness — not sky data')
fig.text(.05, .06, 'C0 DERIVED_CONDITIONAL: same-parameter responses combine before nuisance profiling.', fontsize=9)
fig.text(.05, .025, 'Actual source-processing Jacobians and retained physical rank UNKNOWN; no uncertainty or significance interpretation.', fontsize=9)
fig.tight_layout(rect=(0, .12, 1, .94))
fig.savefig(p / 'QUOTIENT_WITNESS.png', dpi=170)
fig.savefig(p / 'QUOTIENT_WITNESS.pdf', metadata={'CreationDate': None, 'ModDate': None})
