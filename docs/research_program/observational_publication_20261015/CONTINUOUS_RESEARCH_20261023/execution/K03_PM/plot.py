"""Plot the retained-row K03 conditional tangent result from RESULT.json only."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

here = Path(__file__).resolve().parent
d = json.loads((here / "RESULT.json").read_text())
theta = np.asarray(d["fit"]["theta"])
sigma = np.sqrt(np.diag(np.asarray(d["fit"]["covariance"])))
angles = np.asarray(d["principal_angles"]["principal_angles_degrees"])

fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.7), gridspec_kw={"width_ratios": [1.7, 1]})
ax = axes[0]
x = np.arange(6)
ax.errorbar(x[:3], theta[:3], yerr=sigma[:3], fmt="o", capsize=3, label="history $a_b$")
ax.errorbar(x[3:], theta[3:], yerr=sigma[3:], fmt="s", capsize=3, label="local $a_\\ell$")
ax.axhline(0, color="0.55", linewidth=.8)
ax.set_xticks(x, ["$b_x$", "$b_y$", "$b_z$", "$\\ell_x$", "$\\ell_y$", "$\\ell_z$"])
ax.set_ylabel("tangent amplitude ($\\mu$as yr$^{-1}$); $\\pm1$ working SD")
ax.legend(frameon=False, fontsize=9)
ax.set_title("Six-profile conditional fit")
ax = axes[1]
ax.bar(np.arange(3), angles, color="#477eb7")
ax.set_xticks(np.arange(3), ["1", "2", "3"])
ax.set_ylim(0, 90)
ax.set_ylabel("principal angle (degrees)")
ax.set_xlabel("ordered response-space direction")
ax.set_title("History / local overlap")
fig.suptitle("K03_PM: fixed reported-z Gaia sample and per-source covariance", fontsize=11)
fig.text(.02, .025,
         "HTT C0 conditional diagnostic | analytic FLRW two-ray transfer | residual spatial covariance UNKNOWN | no physical K03 admission",
         fontsize=8)
fig.tight_layout(rect=[0, .06, 1, .95])
for ext in ("png", "pdf"):
    fig.savefig(here / f"PROFILE_DIAGNOSTIC.{ext}", dpi=180)
plt.close(fig)
