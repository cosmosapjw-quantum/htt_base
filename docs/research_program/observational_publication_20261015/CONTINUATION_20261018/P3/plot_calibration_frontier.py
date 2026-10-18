"""Plot conditional error radii, never invented observational intervals."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
data = json.loads((ROOT/"results/calibration_frontier.json").read_text())
methods = ["FP", "TF", "SN", "OTHER"]
colors = ["#3572A5", "#D07A24", "#49846A", "#99569B"]
fig, axes = plt.subplots(1,2,figsize=(11.8,4.8),gridspec_kw={"width_ratios":[1.25,1]})
fig.subplots_adjust(top=.79,bottom=.23,wspace=.30)
for method,color in zip(methods,colors):
    rows=[r for r in data["rows"] if r["method"]==method and r["law"]=="gaussian_marginals" and r["predeclared_contrasts"]==1]
    axes[0].plot([r["assumed_calibration_delta_mag"] for r in rows],[r["total_radius_upper_mag"] for r in rows],marker="o",color=color,label=method,lw=2)
axes[0].set(title="Calibration allowance adds directly to the radius",xlabel="Assumed contrast calibration bound δ [mag]",ylabel="Conservative total half-width [mag]")
axes[0].set_xticks([0,.01,.02,.05]); axes[0].set_ylim(0,.12)
axes[0].legend(frameon=False,ncol=2,loc="upper left")
x=np.arange(4)
for offset,law,color,label in [(-.18,"gaussian_marginals","#3C6D98","Gaussian marginals"),(.18,"variance_only","#B5C3CD","Variance only")]:
    vals=[next(r["noise_radius_upper_mag"] for r in data["rows"] if r["method"]==m and r["law"]==law and r["predeclared_contrasts"]==1) for m in methods]
    axes[1].bar(x+offset,vals,.34,color=color,label=label)
axes[1].set(title="Noise-law sensitivity at δ = 0",ylabel="Conservative noise half-width [mag]")
axes[1].set_xticks(x,methods); axes[1].set_ylim(0,.23); axes[1].legend(frameon=False)
for ax in axes:
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y",alpha=.22); ax.set_axisbelow(True)
fig.suptitle("CF4 H02 calibration sensitivity: actual source geometry, assumed uncertainty",fontsize=14,fontweight="bold",y=.96)
fig.text(.5,.86,"35,970 selected groups · one predeclared unit contrast · 95% simultaneous bound across four methods",ha="center",fontsize=10)
fig.text(.06,.095,"No method-specific observed centers are available: these are radius frontiers, not measured Hubble intervals.\nBounds allow arbitrary cross-method dependence. Marginal variance/noise and calibration assumptions remain unvalidated for CF4.",fontsize=9,color="#444444")
fig.savefig(ROOT/"results/calibration_frontier.png",dpi=160)
fig.savefig(ROOT/"results/calibration_frontier.pdf")
print("Saved calibration_frontier.png and calibration_frontier.pdf")
