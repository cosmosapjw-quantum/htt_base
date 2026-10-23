#!/usr/bin/env python3
"""Plot historical and new fixed-row whole-field score control coverage."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


HERE = Path(__file__).resolve().parent
data = json.loads((HERE/'controls.json').read_text())
prior = json.loads((HERE.parents[2]/'ADVERSARIAL_AUDIT_20261022/continuation/astrometry/RESULT.json').read_text())
old = prior['validation_mocks']['misspecification_controls']
old_by_kind = {x['kind']: x for x in old}
kinds = [('omitted_E4_B4', 'l4'),
         ('template_correlated_mean', 'template')]
fig, ax = plt.subplots(figsize=(9.2, 4.8))
positions = [0, 1, 3, 4, 6, 7]
values = []
labels = []
colors = []
for cohort, prefix, color in [('old', '', '#bb6677'), ('full', 'full', '#4477aa'),
                               ('margin', 'margin', '#228833')]:
    for old_kind, label in kinds:
        if cohort == 'old':
            d = old_by_kind[old_kind]
        else:
            d = next(x for x in data['cohorts'][cohort]['controls'] if x['kind'].startswith(old_kind))
        values.append(d['coverage'])
        labels.append(('old grid' if cohort == 'old' else prefix)+'\n'+label)
        colors.append(color)
bars = ax.bar(positions, values, color=colors, width=.78)
for bar, value in zip(bars, values):
    ax.text(bar.get_x()+bar.get_width()/2, value+.025, f'{value:.3f}', ha='center', fontsize=9)
ax.axhline(.95, color='black', linestyle='--', linewidth=1, label='nominal 95%')
ax.set(ylim=(0, 1.13), ylabel='Joint 18D conditional mock coverage',
       xticks=positions, xticklabels=labels,
       title='A22 fixed selected-row score controls, 1024 draws per case')
ax.tick_params(axis='x', labelsize=9)
ax.legend(loc='lower right')
fig.subplots_adjust(left=.09, right=.98, top=.88, bottom=.24)
fig.text(.09, .09, 'Controls: l4 E/B RMS 12 µas/yr; template mean 100 µas/yr.', fontsize=9)
fig.text(.09, .035, 'Estimators differ. New quotient includes l4 and template columns; empirical selection/residual laws unknown.', fontsize=8)
fig.savefig(HERE/'CONTROLS.png', dpi=180)
