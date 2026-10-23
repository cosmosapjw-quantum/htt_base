"""Descriptive fixed-scenario figure for the conditional optical quotient."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ALPHA = .05


def remainder_plot_data(row: dict, noise_case: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Analytic curve with the exact overlap threshold and frozen marker data."""
    d0 = float(row["d0"])
    rho_star = float(row["overlap_rho_star"])
    tau = float(noise_case["tau"])
    marker_rho = np.array([point["rho"] for point in noise_case["remainder_power"]])
    marker_power = np.array([point["maximin_power"] for point in noise_case["remainder_power"]])
    if tau <= 0 or abs(rho_star-d0/2) > 1e-12:
        raise ValueError("invalid fixed overlap geometry")
    radius = np.unique(np.concatenate((np.linspace(0, 1, 501), marker_rho, [rho_star])))
    power = norm.cdf(norm.ppf(ALPHA)+np.maximum(0., d0-2*radius)/tau)
    power[radius >= rho_star] = ALPHA
    reference = norm.cdf(norm.ppf(ALPHA)+np.maximum(0., d0-2*marker_rho)/tau)
    if not np.allclose(marker_power, reference, rtol=0, atol=1e-12):
        raise ValueError("frozen remainder markers disagree with analytic law")
    return radius, power, marker_rho, marker_power


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
        axes[i, 0].set(xlabel="fixed amplitude a (dimensionless)",
                       ylabel="projected d0 (whitened, dimensionless)", title=label)
        chosen = [r for r in rows if r["direction"] == "+ex"]
        for j, tau in enumerate(result["tau_hypothetical"]):
            axes[i, 1].plot([r["amplitude"] for r in chosen],
                            [r["noise"][j]["oracle_power"] for r in chosen], "o-", ms=3, label=f"tau={tau:g} (dimensionless)")
        axes[i, 1].set(xlabel="fixed amplitude a (+ex, dimensionless)", ylabel="oracle power",
                       title="known hypothetical noise")
        r = next(r for r in chosen if r["amplitude"] == .3)
        for j, tau in enumerate(result["tau_hypothetical"]):
            radius, power, marker_rho, marker_power = remainder_plot_data(r, r["noise"][j])
            line, = axes[i, 2].plot(radius, power, "-", lw=1.4,
                                    label=f"tau={tau:g} (dimensionless)")
            axes[i, 2].plot(marker_rho, marker_power, "o", ms=3, color=line.get_color())
        axes[i, 2].axvline(r["overlap_rho_star"], color="black", ls=":", lw=1)
        axes[i, 2].axhline(ALPHA, color="black", ls="--", lw=.8)
        axes[i, 2].set_xscale("symlog", linthresh=1e-4)
        axes[i, 2].set(xlabel="hypothetical rho (+ex, a=.3; whitened, dimensionless)",
                       ylabel="maximin power", title="exact overlap at rho = d0/2")
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
