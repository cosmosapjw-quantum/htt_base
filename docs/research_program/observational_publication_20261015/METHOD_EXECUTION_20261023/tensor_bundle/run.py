"""Generate the bounded tensor scenario product and diagnostic figures."""
import hashlib
import json
import platform
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

from adapter import HERE, INPUT_SHA, load_reviewed_state, build, sha


def main():
    result, arrays = build()
    np.savez_compressed(HERE / "SAMPLES.npz", **arrays)
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    source, mean, cov = load_reviewed_state()
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
    x = np.arange(24)
    axes[0].errorbar(x, mean, yerr=2*np.sqrt(np.diag(cov)), fmt="o", markersize=3)
    axes[0].axhline(0, color="0.5", linewidth=.8)
    axes[0].set(title="Full24 fitted state and conditional 2-sigma diagonal scales",
                ylabel="microarcsec/year", xlabel="Six E1/B1 components per bin, then six slopes")
    y = np.asarray(result["G_F"]["Y18_mean_uasyr"])
    z = np.asarray(result["G_F"]["Z18_mean_uasyr"])
    for b in range(3):
        axes[1].scatter(np.arange(6)+6*b, y[6*b:6*b+6], label=f"Y{b}")
    axes[1].set(title="Signed Y18 depth path (reported-z working coordinates)",
                xlabel="Depth block / component", ylabel="microarcsec/year")
    axes[1].legend(ncol=3)
    fig.savefig(HERE / "TENSOR_DIAGNOSTICS.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    rho = [r["rho"] for r in result["F"]["region_family"]]
    exact = [r["reference_occupancy_exact"] for r in result["F"]["region_family"]]
    empirical = [r["reference_occupancy_empirical"] for r in result["F"]["region_family"]]
    ax.plot(rho, exact, "o-", label="Gaussian working-law exact")
    ax.plot(rho, empirical, "x--", label="4096 seeded replicates")
    ax.set(xlabel="Common ellipsoid radius rho", ylabel="Reference occupancy",
           ylim=(-.02, 1.02), title="Conditional computational occupancy; no survey coverage")
    ax.legend()
    fig.savefig(HERE / "REGION_OCCUPANCY.png", dpi=150)
    plt.close(fig)
    receipt = {"task_id": "R24-TENSOR-BUNDLE", "input_sha256": INPUT_SHA,
               "source_candidate": result["source_candidate"],
               "command": "python run.py", "cwd": str(HERE),
               "environment": {"python": platform.python_version(), "numpy": np.__version__,
                               "scipy": scipy.__version__, "executable": sys.executable},
               "generated_sha256": {name: sha(HERE/name) for name in
                                    ("RESULT.json", "SAMPLES.npz", "TENSOR_DIAGNOSTICS.png", "REGION_OCCUPANCY.png")},
               "status": "SCENARIO_GENERATED_NOT_INDEPENDENTLY_REVIEWED"}
    (HERE / "RAW_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "n": len(arrays["sample24_uasyr"]),
                      "result_sha256": receipt["generated_sha256"]["RESULT.json"]}))


if __name__ == "__main__":
    main()
