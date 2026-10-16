"""Render descriptive scenario comparisons; never labels these as measured uncertainties."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

root=Path(__file__).resolve().parents[1]
source=root/'results/source_power_v1/RESULT.json'
results=json.loads(source.read_text())
output=root/'results/source_power_v1'

fig,ax=plt.subplots(figsize=(8.3,4.6))
ells=np.arange(6,17)
for case in results['cases']:
    arr=case['independent_shell_covariance']['per_shell_contributions']
    ax.plot(ells,[x['trace_fraction'] for x in arr],marker='o',label=case['template_name'].split('_')[0].capitalize())
ax.set_xlabel('Harmonic shell ℓ (real source geometry; conditional Cℓ)')
ax.set_ylabel('Fraction of output covariance trace')
ax.set_title('PR536 mask geometry × hypothetical harmonic power')
ax.legend()
fig.tight_layout()
fig.savefig(output/'TRACE_SHARE_BY_SHELL.png',dpi=160)
plt.close(fig)

fig,ax=plt.subplots(figsize=(8.3,4.6))
for case in results['cases']:
    corr=case['manufactured_cross_shell_rho']
    rhos=sorted(float(x) for x in corr)
    ax.plot(rhos,[corr[str(x)]['leading_std'] for x in rhos],marker='o',label=case['template_name'].split('_')[0].capitalize())
ax.set_xlabel('Manufactured cross-shell correlation ρ')
ax.set_ylabel('Top output standard deviation (scenario units)')
ax.set_title('Not a measured Planck noise/systematics covariance')
ax.legend()
fig.tight_layout()
fig.savefig(output/'SENSITIVITY_TO_CROSS_SHELL_CORRELATION.png',dpi=160)
plt.close(fig)
print('FIGURES_CREATED',*[str(x) for x in output.glob('*.png')])
