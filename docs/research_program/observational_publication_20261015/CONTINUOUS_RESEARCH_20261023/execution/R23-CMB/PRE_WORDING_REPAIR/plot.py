"""Mechanical rendering of the frozen Astra split-projection experiment."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out = Path(__file__).resolve().parent
data = json.loads((out / 'RESULT.json').read_text())
labels = {'native': 'Original pseudoalm', 20: 'Secondary |b|>20°, L128',
          30: 'Secondary |b|>30°, L128'}
fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.6))
for row in data['rows']:
    x = [p['alpha'] for p in row['path']]
    for ax, key in zip(axes, ['J234', 'alignment23_squared']):
        ax.plot(x, [p['features'][key] for p in row['path']], 'o-',
                label=labels[row['operator']])
        ax.set_xlabel('Removed fraction α of fitted split-direction component')
        ax.grid(alpha=.2)
axes[0].set_ylabel('Signed J234')
axes[1].set_ylabel('Alignment23 squared')
axes[1].set_ylim(0, 1)
axes[0].legend(fontsize=8)
fig.suptitle('One observed PR3 sky — split-direction sensitivity')
fig.text(.05, .075, 'C0 DIAGNOSTIC: data-derived HM/OE projection in processed E ℓ2–4; Euclidean harmonic-power metric.', fontsize=9)
fig.text(.05, .035, 'No physical cleaning or null probability. Windows repeat operators on one sky. α scales amplitude, not power.', fontsize=9)
fig.tight_layout(rect=(0, .12, 1, .94))
fig.savefig(out / 'SPLIT_PROJECTION.png', dpi=170)
fig.savefig(out / 'SPLIT_PROJECTION.pdf', metadata={'CreationDate': None, 'ModDate': None})
