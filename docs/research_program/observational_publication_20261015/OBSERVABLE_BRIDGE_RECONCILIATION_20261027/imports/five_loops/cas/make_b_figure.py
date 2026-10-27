"""Render Loop B7a: finite analytical illustration, with no observed sky data.

The shaded region is a conservative scalar norm envelope, not an exact tensor
identified set. Outputs are publication PDF and 300 dpi PNG beside this project.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
qmax, delta_m = 0.10, 0.02
width = qmax + delta_m
factor = np.sqrt(3.0 / 2.0)

def envelope(m):
    m = np.asarray(m, dtype=float)
    return factor * np.maximum(0.0, m - width), factor * (m + width)

# Independent endpoint checks against explicit hand-computed B7a values.
points = np.array([0.0, 0.12, 0.30, 0.50])
low, high = envelope(points)
expected_low = factor * np.array([0.0, 0.0, 0.18, 0.38])
expected_high = factor * np.array([0.12, 0.24, 0.42, 0.62])
np.testing.assert_allclose(low, expected_low, rtol=0, atol=2e-16)
np.testing.assert_allclose(high, expected_high, rtol=0, atol=2e-16)
for amplitude in (0.0, 0.1, 0.4):
    d = np.array([0.0, 0.0, amplitude])
    dd_stf = np.outer(d, d) - np.dot(d, d) * np.eye(3) / 3
    np.testing.assert_allclose(np.linalg.norm(dd_stf, "fro"),
                               np.sqrt(2/3) * np.dot(d, d), atol=1e-16)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10.0,
    "mathtext.fontset": "stix", "axes.labelsize": 12,
    "axes.linewidth": 0.8, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.facecolor": "white", "figure.facecolor": "white",
})
fig = plt.figure(figsize=(7.6, 6.5))
ax = fig.add_axes([0.12, 0.39, 0.82, 0.44])
blue, ink, muted = "#205D8F", "#222A30", "#5F6973"
x = np.linspace(0, 0.50, 1001)
lower, upper = envelope(x)
ax.fill_between(x, lower, upper, color="#D9E8F4", zorder=1)
ax.plot(x, upper, color=blue, lw=1.9, zorder=3)
ax.plot(x, lower, color=blue, lw=1.9, zorder=3)
ax.plot(x, factor*x, color=muted, ls=(0, (4, 3)), lw=1.25, zorder=2)
ax.vlines(width, 0, factor*(2*width), color="#97A2AC", lw=0.9,
          ls=(0, (2, 3)), zorder=0)
ax.set_xlim(0, 0.50)
ax.set_ylim(0, 0.80)
ax.set_xlabel(r"Measured residual norm $\|\widehat M\|_F$  (dimensionless)", labelpad=9)
ax.set_ylabel(r"Intrinsic-dipole amplitude squared $|d|^2$", labelpad=9)
ax.xaxis.set_major_locator(MultipleLocator(0.10))
ax.yaxis.set_major_locator(MultipleLocator(0.20))
ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
ax.grid(axis="y", color="#DDE2E7", lw=0.65)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(length=3.5, color="#5F6973")
ax.text(0.32, 0.735, "Upper bound", color=blue, fontsize=10.2)
ax.text(0.35, factor*(0.35-width)-0.060, "Lower bound", color=blue, fontsize=10.2)
ax.text(0.016, 0.705, "Conservative norm envelope", color=ink, fontsize=10.2)
ax.text(0.016, 0.638, r"$q_{\max}=0.10,\quad\delta_M=0.02$", color=ink, fontsize=11)
ax.annotate(r"Zero-contamination relation", xy=(0.27, factor*0.27),
            xytext=(0.03, 0.465), color=muted, fontsize=9.1,
            arrowprops={"arrowstyle": "-", "color": muted, "lw": 0.8})
ax.text(width+0.006, 0.033, r"$0.12$", color=muted, fontsize=9.3)
fig.text(0.12, 0.945, "Conditional intrinsic-dipole bounds", fontsize=16,
         weight="semibold", color=ink)
fig.text(0.12, 0.897, "Equation B7a  |  Analytical illustration; no observed sky data",
         fontsize=10.2, color=muted)
fig.text(0.12, 0.255,
         r"$\sqrt{3/2}\,\max(0,\|\widehat M\|_F-q_{\max}-\delta_M)"
         r"\;\leq\;|d|^2\;\leq\;"
         r"\sqrt{3/2}\,(\|\widehat M\|_F+q_{\max}+\delta_M)$",
         fontsize=12, color=ink)
caption = (
    r"$M=K-\mathrm{STF}(aa^{\mathsf{T}})$; $\|\cdot\|_F$ is the full Cartesian Frobenius norm."
    "\n"
    r"Assumptions: $\|Q_{\rm intrinsic}\|_F\leq q_{\max}$ and "
    r"$\|\widehat M-[Q_{\rm intrinsic}-\mathrm{STF}(dd^{\mathsf{T}})]\|_F\leq\delta_M$."
    "\n"
    "Shading gives necessary scalar bounds, not full tensor compatibility or a confidence region."
    "\n"
    "All values are dimensionless. The illustrative range demonstrates the finite algebra only."
)
fig.text(0.12, 0.175, caption, fontsize=9.0, color=muted,
         va="top", linespacing=1.65)
pdf = OUT / "figure_b_dipole.pdf"
png = OUT / "figure_b_dipole.png"
metadata = {"Title": "Conditional intrinsic-dipole bounds", "Author": "HTT internal theory loop B",
            "Subject": "Analytical B7a norm envelope; illustrative inputs; no observations"}
fig.savefig(pdf, metadata=metadata)
fig.savefig(png, dpi=300, metadata={"Description": metadata["Subject"]})
plt.close(fig)
print("PASS: endpoint identities and STF Frobenius normalization")
for m, l, u in zip(points, low, high):
    print(f"norm={m:.2f}: |d|^2 in [{l:.9f}, {u:.9f}]")
print(f"Created {pdf}")
print(f"Created {png}")
