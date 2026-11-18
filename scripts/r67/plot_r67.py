from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root=Path("docs/research_program/observational_publication_20261015/R67_SEVEN_AXIS_FUSION_20261118/RESULTS")
a=json.loads((root/"CF4_METHOD_CONTRAST.json").read_text())
g=json.loads((root/"GAIA_EB_FRAME.json").read_text())["results"]["quality"]
names=list(a["pairs"])+["joint network"]
p_nom=[a["pairs"][k]["naive_chisq_reference_p"] for k in a["pairs"]]+[a["network"]["naive_chisq_reference_p"]]
p_wild=[a["pairs"][k]["wild_group_p_exploratory"] for k in a["pairs"]]+[a["network"]["wild_group_p_exploratory"]]
fig,axes=plt.subplots(2,1,figsize=(9,8.5),layout="constrained")
idx=np.arange(len(names))
axes[0].bar(idx-.18,p_nom,.36,label="naive chi-square working law")
axes[0].bar(idx+.18,p_wild,.36,label="group-wild (32,768)")
axes[0].axhline(.05,ls="--",lw=1,label="reference 0.05")
axes[0].set(xticks=idx,xticklabels=names,ylabel="Exploratory tail probability",title="Same-CF4-group method contrasts, angular 8 / network 16 df")
axes[0].legend(fontsize=8)
v=np.asarray(g["coefs_EB_microarcsecyr"])
formal=np.asarray(g["formal_marginal_sigma_microarcsecyr"])
patch=np.asarray(g["spatial_cluster_192_patch_sigma_microarcsecyr"])
x=np.arange(6)
axes[1].errorbar(x,v,yerr=patch,fmt="o",capsize=4,label="192-patch sandwich diagnostic")
axes[1].errorbar(x+.12,v,yerr=formal,fmt=".",capsize=2,label="sourcewise formal errors")
axes[1].axhline(0,lw=.8)
axes[1].set(xticks=x,xticklabels=["E_x","E_y","E_z","B_x","B_y","B_z"],
            ylabel="Gaia fitted coefficient [μas/year]",
            title="Gaia-CRF3 E/B l=1 diagnostic; not a matter-vorticity measurement")
axes[1].legend(fontsize=8)
fig.savefig(root/"R67_FUSION_DIAGNOSTICS.png",dpi=160)
fig.savefig(root/"R67_FUSION_DIAGNOSTICS.pdf")
plt.close(fig)
print("figure",root/"R67_FUSION_DIAGNOSTICS.png")
