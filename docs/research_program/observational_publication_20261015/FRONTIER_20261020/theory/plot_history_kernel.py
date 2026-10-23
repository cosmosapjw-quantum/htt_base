"""Publication-style rendering of the new analytic benchmark; no data fit."""
import hashlib
import json
from pathlib import Path
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from verify_history_kernel import OMEGA_R, background

started = time.perf_counter()
root = Path(__file__).resolve().parent
z = np.geomspace(1e-4, 2.0, 400)
rows = [background(float(x)) for x in z]
local = np.array([row["A_local"] for row in rows])
history = np.array([row["h_history"] for row in rows])
ratio = history / local
coefficient = (3 + OMEGA_R) / 4
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.titlesize": 11, "axes.labelsize": 11,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False,
})
fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.4))
panels = [
    (local, 1 / z, "#285f9f", r"Local observer response $A$", r"$A(z)$", r"$1/z$"),
    (history, coefficient * z, "#a6452c", r"Compensated history response $h$",
     r"$h(z)$", r"$(3+\Omega_r)z/4$"),
    (ratio, coefficient * z * z, "#3c7e59", r"Ratio controlling radial rank",
     r"$F(z)=h(z)/A(z)$", r"$(3+\Omega_r)z^2/4$"),
]
for ax, (value, limit, color, title, ylabel, low_label) in zip(axes, panels):
    ax.loglog(z, value, color=color, linewidth=2.3, label="Closed analytic response")
    ax.loglog(z, limit, color="#666666", linestyle="--", linewidth=1.2,
              label="Low-$z$: " + low_label)
    ax.set(title=title, xlabel="Observed redshift $z$", ylabel=ylabel)
    ax.grid(which="major", color="#dddddd", linewidth=0.6)
    ax.legend(frameon=False, fontsize=8.2, loc="best")
fig.suptitle("Finite-depth local and compensated matter–radiation responses",
             fontsize=14, y=0.985)
fig.text(0.5, 0.902,
         r"Hypothetical flat background: $\Omega_m=0.9999$, $\Omega_r=0.0001$, "
         r"$\Omega_\Lambda=0$ · first order in velocities · no observational fit",
         ha="center", fontsize=10, color="#444444")
fig.text(0.5, 0.018,
         "Source and observer share the current dust flow in the history column. "
         "Actual survey rank remains conditional on angular support and nuisance projection.",
         ha="center", fontsize=8.3, color="#444444")
fig.subplots_adjust(top=0.77, bottom=0.17, left=0.07, right=0.985, wspace=0.33)
png = root / "history_response.png"
pdf = root / "history_response.pdf"
fig.savefig(png, dpi=250)
fig.savefig(pdf)
plt.close(fig)
receipt = {
    "status": "completed", "kind": "new analytic benchmark plot",
    "elapsed_seconds": time.perf_counter() - started,
    "points": len(z), "redshift_interval": [float(z[0]), float(z[-1])],
    "background": {"Omega_m": 1 - OMEGA_R, "Omega_r": OMEGA_R, "Omega_Lambda": 0},
    "matplotlib_version": matplotlib.__version__, "numpy_version": np.__version__,
    "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "source_kernel": "verify_history_kernel.py",
    "outputs": [png.name, pdf.name],
    "existing_data_campaigns_rerun": False,
    "ode_or_quadrature": False,
}
(root / "PLOT_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
