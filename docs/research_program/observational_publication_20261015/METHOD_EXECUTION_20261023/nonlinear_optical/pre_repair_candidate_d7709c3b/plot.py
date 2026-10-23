"""Descriptive fixed-scenario figure for the conditional optical quotient."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent


def main() -> None:
    result = json.loads((HERE/"RESULT.json").read_text())
    fig, axes = plt.subplots(4, 3, figsize=(14, 13), constrained_layout=True)
    for i, scenario in enumerate(result["scenarios"]):
        rows = scenario["rows"]
        label = f"ac={scenario['calibration_ac_mag']:g}, bc={scenario['group_bc_mag']:g} mag"
        for name in result["directions"]:
            chosen = [r for r in rows if r["direction"] == name and r["amplitude"] > 0]
            axes[i, 0].plot([r["amplitude"] for r in chosen], [r["d0"] for r in chosen], "o-", ms=3, label=name)
        axes[i, 0].set_yscale("log")
        axes[i, 0].set(xlabel="fixed amplitude a", ylabel="projected d0", title=label)
        chosen = [r for r in rows if r["direction"] == "+ex"]
        for j, tau in enumerate(result["tau_hypothetical"]):
            axes[i, 1].plot([r["amplitude"] for r in chosen],
                            [r["noise"][j]["oracle_power"] for r in chosen], "o-", ms=3, label=f"tau={tau:g}")
        axes[i, 1].set(xlabel="fixed amplitude a (+ex)", ylabel="oracle power", title="known hypothetical noise")
        r = next(r for r in chosen if r["amplitude"] == .3)
        for j, tau in enumerate(result["tau_hypothetical"]):
            curve = r["noise"][j]["remainder_power"]
            axes[i, 2].plot([x["rho"] for x in curve], [x["maximin_power"] for x in curve],
                            "o-", ms=3, label=f"tau={tau:g}")
        axes[i, 2].axvline(r["overlap_rho_star"], color="black", ls=":", lw=1)
        axes[i, 2].set_xscale("symlog", linthresh=1e-4)
        axes[i, 2].set(xlabel="hypothetical radius rho (+ex, a=.3)", ylabel="maximin power",
                       title="same ball under both hypotheses")
        for ax in axes[i]:
            ax.grid(alpha=.25)
    axes[0, 0].legend(fontsize=7, ncol=2)
    axes[0, 1].legend(fontsize=7)
    axes[0, 2].legend(fontsize=7)
    fig.suptitle("Conditional leading-low-z nonlinear optical quotient; descriptive fixed scenarios", fontsize=15)
    fig.savefig(HERE/"OPTICAL_QUOTIENT.png", dpi=160)
    fig.savefig(HERE/"OPTICAL_QUOTIENT.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
