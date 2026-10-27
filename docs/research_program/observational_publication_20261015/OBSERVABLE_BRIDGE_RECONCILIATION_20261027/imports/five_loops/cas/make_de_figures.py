"""Render a solver-free, analytical Loop D/E geometry figure.

Outputs: figures/figure_de_geometry.pdf and figures/figure_de_geometry.png.
No observational data, ODE integration, or fitted parameters enter this figure.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

NAVY = "#183153"
BLUE = "#3977A8"
RUST = "#AD583E"
TEAL = "#267A75"
GRAY = "#626C75"

# Loop D, exact (n_1,n_2,n_3;a)=(u,0,0;0) and (0,2u,u;0).
ric_ii = np.array([0.5, -0.5, -0.5])
ric_vii0 = np.array([-0.5, 1.5, -1.5])
assert np.array_equal(ric_ii, np.array([1, -1, -1]) / 2)
assert np.array_equal(ric_vii0, np.array([-1, 3, -3]) / 2)
assert ric_ii.sum() == ric_vii0.sum() == -0.5
assert not np.array_equal(np.sort(ric_ii), np.sort(ric_vii0))

# Loop E, equation (E17), x=n_1^2 in the stated positive H_dir domain.
x = np.linspace(0.0, 0.55, 551)
t_hdir = 2.0 / 3.0 - x
qeff = (2.0 + 3.0 * (7.0 - 9.0 * x) * x) / (2.0 - 3.0 * x) ** 2
qeff_original = -1.0 + (2.0 / 3.0 + x - 2.0 * x**2) / t_hdir**2
assert np.allclose(qeff, qeff_original, rtol=1e-13, atol=1e-13)
assert np.all(t_hdir > 0)
assert np.isclose(qeff[0], 0.5)
assert np.isclose(qeff[500], 23.0)

# Loop E, equation (E10): leading redshift terms, illustrative q_eff=1/2.
z = np.linspace(0.0, 0.12, 241)
q_example = 0.5
h_ratio_over_h0 = 1.0 - (1.0 - q_example) * z / 2.0
h_diff_over_h0 = 1.0 + (1.0 + q_example) * z
assert np.isclose(h_ratio_over_h0[-1], 0.97)
assert np.isclose(h_diff_over_h0[-1], 1.18)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.titlesize": 11,
        "axes.labelsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
    }
)

fig, axs = plt.subplots(2, 2, figsize=(10.6, 7.5), constrained_layout=True)
fig.suptitle("Spatial curvature and directional Hubble estimands", color=NAVY, fontsize=14, weight="semibold")

ax = axs[0, 0]
pos = np.arange(3)
width = 0.34
ax.bar(pos - width / 2, ric_ii, width, color=BLUE, label="Bianchi II")
ax.bar(pos + width / 2, ric_vii0, width, color=RUST, label=r"Bianchi VII$_0$")
ax.axhline(0, color=GRAY, linewidth=0.9)
ax.set_xticks(pos, [r"${}^{3}R_{11}$", r"${}^{3}R_{22}$", r"${}^{3}R_{33}$"])
ax.set_ylim(-1.82, 1.87)
ax.set_ylabel(r"Ricci eigenvalue / $u^2$ (diagonal frame)")
ax.set_title("A  Same scalar curvature, different tensors", loc="left", color=NAVY, weight="semibold")
ax.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=2)
ax.text(0.98, 0.96, r"Both ${}^{3}R/u^2=-1/2$", ha="right", va="top", transform=ax.transAxes, fontsize=8.5, color=NAVY)

ax = axs[0, 1]
ax.plot(x, t_hdir, color=TEAL, linewidth=2.2)
ax.scatter([0, 0.55], [t_hdir[0], t_hdir[-1]], s=20, color=TEAL, zorder=3)
ax.set(xlim=(0, 0.55), ylim=(0, 0.72), xlabel=r"Kasner sky direction $x=n_1^2$", ylabel=r"$t H_{\rm dir}=2/3-x$")
ax.set_title("B  Directional expansion", loc="left", color=NAVY, weight="semibold")
ax.grid(axis="y", color="#D7DEE2", linewidth=0.6)

ax = axs[1, 0]
ax.plot(x, qeff, color=RUST, linewidth=2.2)
ax.scatter([0, 0.5], [0.5, 23], s=22, color=RUST, zorder=3)
ax.annotate(r"$q_{\rm eff}(0)=1/2$", (0, 0.5), (0.07, 6.7), arrowprops={"arrowstyle": "-", "color": GRAY, "lw": 0.7}, fontsize=8.5)
ax.annotate(r"$q_{\rm eff}(1/2)=23$", (0.5, 23), (0.26, 31), arrowprops={"arrowstyle": "-", "color": GRAY, "lw": 0.7}, fontsize=8.5)
ax.set(xlim=(0, 0.55), ylim=(0, 48), xlabel=r"Kasner sky direction $x=n_1^2$", ylabel=r"$q_{\rm eff}$")
ax.set_title("C  Apparent deceleration in Ricci-flat Kasner", loc="left", color=NAVY, weight="semibold")
ax.grid(axis="y", color="#D7DEE2", linewidth=0.6)

ax = axs[1, 1]
ax.plot(z, h_ratio_over_h0, color=BLUE, linewidth=2.2, label=r"$H_{\rm ratio}/H_0=1-z/4$")
ax.plot(z, h_diff_over_h0, color=TEAL, linewidth=2.2, linestyle="--", label=r"$H_{\rm diff}/H_0=1+3z/2$")
ax.axhline(1, color=GRAY, linewidth=0.7, alpha=0.7)
ax.set(xlim=(0, 0.12), ylim=(0.95, 1.21), xlabel="Redshift $z$", ylabel=r"First-order $H/H_0$")
ax.set_title(r"D  Two estimands; illustrative $q_{\rm eff}=1/2$", loc="left", color=NAVY, weight="semibold")
ax.legend(loc="upper left", frameon=False, fontsize=8.5)
ax.grid(axis="y", color="#D7DEE2", linewidth=0.6)
ax.text(0.98, 0.04, r"Analytic $O(z)$ truncations; no observations", ha="right", va="bottom", transform=ax.transAxes, color=GRAY, fontsize=8.1)

for panel in axs.flat:
    panel.tick_params(colors=NAVY, labelsize=8.5)
    panel.xaxis.label.set_color(NAVY)
    panel.yaxis.label.set_color(NAVY)

for extension, extra in [("pdf", {}), ("png", {"dpi": 240})]:
    path = OUT / f"figure_de_geometry.{extension}"
    fig.savefig(path, bbox_inches="tight", **extra)
    print(f"wrote {path} ({path.stat().st_size} bytes)")
plt.close(fig)

print("checked: II and VII0 trace=-u^2/2; Kasner q_eff(0)=1/2, q_eff(1/2)=23; first-order ratios at z=.12 are .97 and 1.18")
