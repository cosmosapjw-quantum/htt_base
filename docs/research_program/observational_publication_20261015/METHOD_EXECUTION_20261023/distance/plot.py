"""Plot stored exploratory distance comparison without refitting."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/"RESULT.json").read_text())
scenarios=list(r["scenarios"])
models=["A_calibration_flow","B_optical_STF","C_union"]
colors=["#3366aa","#bc602e","#57875a"]
fig,axes=plt.subplots(1,2,figsize=(11.4,4.3),layout="constrained")
x=np.arange(len(scenarios))
for j,model in enumerate(models):
    scores=[r["scenarios"][s]["models"][model]["joint_log_score_per_row"] for s in scenarios]
    axes[0].bar(x+(j-1)*.24,scores,width=.23,color=colors[j],label=model.replace("_"," "))
axes[0].set_xticks(x,[s.replace("a_","a=").replace("_b_",", b=") for s in scenarios],rotation=18)
axes[0].set_ylabel("5-fold held-out joint log score / row")
axes[0].set_title("274 released moduli, complete-group folds")
axes[0].legend(fontsize=8,loc="lower left")
for j,model in enumerate(models):
    d=r["scenarios"]["a_0.055_b_0.290"]["models"][model]["oof_residual_summaries"]
    means=[d["depth_bins"][str(k)]["mean_signed_mag"] for k in range(3)]
    axes[1].plot(range(3),means,"o-",color=colors[j],label=model.replace("_"," "))
axes[1].axhline(0,color="black",linewidth=.8)
axes[1].set_xticks(range(3),["shallow","middle","deep"])
axes[1].set_ylabel("OOF signed mean residual (mag)")
axes[1].set_title("Exploratory depth residuals; a=.055, b=.29 mag")
fig.suptitle("Authored conditional distance scenarios · no physical model selection",fontsize=11)
for ext in ("png","pdf"):
    fig.savefig(HERE/f"DISTANCE_MODELS.{ext}",dpi=170)
plt.close(fig)
