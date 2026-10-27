"""Analytic local radiation/shear response; no measured CMB or ODE.

I(e)=rho/(4*pi)*(1+a*P2(e_z)), -0.8 <= a <= 1.5, rho>0.
The three branches are exact eigenvalues of the five-dimensional STF2 operator,
with multiplicities 2, 2, 1. The dashed curve is the proven M2 lower certificate.
Run from any directory: python /absolute/path/to/this/script.py
"""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)
a = np.linspace(-0.8, 1.5, 501)
lam2 = (56-10*a)/105
lam1 = (56+5*a)/105
lam0 = (56+10*a)/105
bound = np.minimum((5-a)/15, (5+2*a)/15)

# Independent matrix assembly in an orthonormal STF2 basis, rho=1.
rt2, rt6 = np.sqrt(2), np.sqrt(6)
basis = [
    np.diag([1, -1, 0])/rt2,
    np.diag([1, 1, -2])/rt6,
    np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])/rt2,
    np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]])/rt2,
    np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]])/rt2,
]
def stf(m):
    return (m+m.T)/2-np.trace(m)*np.eye(3)/3

max_error = 0.
for ai in [-0.8, 0., .5, 1.5]:
    pi = ai*np.diag([-1., -1., 2.])/15
    response = [8*s/15+10*stf(s@pi)/7 for s in basis]
    matrix = np.array([[np.sum(t*rs) for rs in response] for t in basis])
    expected = np.sort([(56-10*ai)/105]*2
                       + [(56+5*ai)/105]*2
                       + [(56+10*ai)/105])
    err = np.max(np.abs(np.linalg.eigvalsh(matrix)-expected))
    max_error = max(max_error, float(err))
assert max_error < 1e-14
assert np.min(np.vstack([lam2, lam1, lam0])-bound) > 0
assert np.min(1+a[:, None]*np.array([-0.5, 1.])[None, :]) > 0

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42,
})
fig, ax = plt.subplots(figsize=(7.1, 4.6), constrained_layout=True)
ax.plot(a, lam2, color="#1767A4", lw=2.1,
        label=r"$|m|=2$: $(56-10a)/105$  (multiplicity 2)")
ax.plot(a, lam1, color="#C06520", lw=2.1,
        label=r"$|m|=1$: $(56+5a)/105$  (multiplicity 2)")
ax.plot(a, lam0, color="#428258", lw=2.1,
        label=r"$m=0$: $(56+10a)/105$  (multiplicity 1)")
ax.plot(a, bound, color="#363A42", lw=2, ls="--",
        label=r"Certified lower bound $\lambda_{\min}(M_2)/\rho$")
ax.axvline(0, color="#C7CBD0", lw=.8, zorder=0)
ax.set(xlim=(-.8, 1.5), ylim=(0, .72),
       xlabel=r"Brightness quadrupole amplitude $a$",
       ylabel=r"Eigenvalue / radiation energy density $\rho$")
ax.set_title("Positive local shear response under angular anisotropy",
             loc="left", fontsize=13, pad=25)
ax.text(0, 1.025, r"Analytic family $I=\rho[1+aP_2(e_z)]/(4\pi)$; no measured CMB",
        transform=ax.transAxes, fontsize=9.5, color="#525963")
ax.grid(axis="y", color="#E4E7EA", lw=.7)
ax.legend(loc="lower left", frameon=False, fontsize=8.7)
fig.savefig(OUT/"figure_a_radiation.pdf")
fig.savefig(OUT/"figure_a_radiation.png", dpi=190)
plt.close(fig)
print(json.dumps({"status": "PASS_SCOPED", "analytic_branches": 3,
                  "operator_dimension": 5, "multiplicities": [2, 2, 1],
                  "matrix_check_points": [-.8, 0., .5, 1.5],
                  "max_eigenvalue_error": max_error,
                  "min_certified_bound": float(bound.min()),
                  "min_actual_response_eigenvalue":
                      float(np.min([lam2.min(), lam1.min(), lam0.min()])),
                  "outputs": ["figures/figure_a_radiation.pdf",
                              "figures/figure_a_radiation.png"]}, indent=2))
