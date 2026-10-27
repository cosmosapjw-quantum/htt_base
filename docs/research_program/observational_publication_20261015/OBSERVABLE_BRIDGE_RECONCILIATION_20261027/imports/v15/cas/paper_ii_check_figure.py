"""Plot the proved finite beam envelope; no observed spectrum."""
from pathlib import Path
import importlib.util
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("beam_check",ROOT/"cas/paper_ii_check.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
r=np.linspace(1,2.2,100)
R=mod.rmin(r)
eta=np.array([0. if abs(x-1)<1e-14 else mod.invQbe(mod.QC*x) for x in R])
equal=(.5*(1+r**3))**4/(.5*(1+r**4))**3
assert np.all(R<=equal+1e-13) and np.all(equal<=1+1e-13)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                     "pdf.fonttype":42,"axes.spines.top":False,"axes.spines.right":False})
fig,ax=plt.subplots(1,2,figsize=(10.1,4.25),constrained_layout=True)
ax[0].fill_between(r,R,1,color="#dbe9f4")
ax[0].plot(r,R,color="#24679a",lw=2,label="Sharp lower envelope")
ax[0].plot(r,equal,color="#b76a2b",lw=1.8,ls="--",label="Equal endpoint weights")
ax[0].axhline(1,color="#52634e",lw=1,ls=":")
ax[0].set(xlabel=r"Beam temperature range $r=T_{\max}/T_{\min}$",
          ylabel=r"$\overline{\mathcal{Q}}_{NE}/Q_c$",
          title="A  Population ratio after angular mixing",
          xlim=(1,2.2),ylim=(.35,1.04))
ax[0].legend(loc="lower left",frameon=False,fontsize=8.5)
ax[1].fill_between(r,eta,0,color="#f2e3d7")
ax[1].plot(r,eta,color="#9c582d",lw=2)
ax[1].axhline(0,color="#52634e",lw=1,ls=":")
ax[1].set(xlabel=r"Beam temperature range $r=T_{\max}/T_{\min}$",
          ylabel=r"Calibrated log-fugacity $\eta_{\rm eff}$",
          title="B  Apparent population shift, Planck reference",
          xlim=(1,2.2),ylim=(min(eta)*1.1,.035))
for a in ax:a.grid(axis="y",color="#e5e7e9",lw=.7)
fig.suptitle("Finite-amplitude beam calibration bounds",fontsize=14,fontweight="bold")
fig.text(.5,-.035,"Positive, energy-independent beam; all underlying rays have η = 0. "
         "Calibrated η is a two-moment representative, not a true chemical distortion.",
         ha="center",fontsize=8.5,color="#50565d")
(ROOT/"figures").mkdir(exist_ok=True)
fig.savefig(ROOT/"figures/paper_ii_population_beam.pdf",bbox_inches="tight")
fig.savefig(ROOT/"figures/paper_ii_population_beam.png",dpi=220,bbox_inches="tight")
