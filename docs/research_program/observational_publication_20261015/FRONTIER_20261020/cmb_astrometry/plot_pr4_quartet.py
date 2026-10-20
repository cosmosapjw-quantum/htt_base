"""Plot the stored one-realization PR4 descriptive diagnostics only."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
RESULT = HERE / "pr4_quartet_diagnostic.json"
data = json.loads(RESULT.read_text())
if data["scope"] != "C0_DIAGNOSTIC_ONLY_ONE_REALIZATION_NO_FOREGROUND_OR_COVERAGE":
    raise ValueError("unexpected result scope")
names = ("TEMPERATURE", "Q_POLARISATION", "U_POLARISATION")
labels = ("T", "Q", "U")
npix = data["products"]["cmb_A"]["npix"]
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
for axis, group, color in ((ax[0], "cmb", "#315c83"), (ax[1], "residual", "#9a6335")):
    counts = [data["full_pair_difference"][group][name]["unequal_float32_bit_patterns"] for name in names]
    unequal = [count / npix for count in counts]
    axis.bar(labels, unequal, color=color)
    axis.set_ylim(0, 1.07)
    axis.set_ylabel("A/B unequal stored pixel fraction")
    axis.set_title("Shared CMB fields" if group == "cmb" else "Distinct residual fields")
    for i, (value, count) in enumerate(zip(unequal, counts)):
        label = "N" if count == npix else "N−1" if count == npix - 1 else str(count)
        axis.text(i, min(value + 0.025, 1.02), label, ha="center", fontsize=9)
fig.text(0.5, 0.015, f"N={npix:,} pixels; MC00200 only; no observed-map match, foreground law or null coverage", ha="center", fontsize=8)
fig.tight_layout(rect=[0, 0.075, 1, 1])
fig.savefig(HERE / "PR4_QUARTET.png", dpi=180)
fig.savefig(HERE / "PR4_QUARTET.pdf")
plt.close(fig)
print("Plotted stored PR4 diagnostic JSON")
