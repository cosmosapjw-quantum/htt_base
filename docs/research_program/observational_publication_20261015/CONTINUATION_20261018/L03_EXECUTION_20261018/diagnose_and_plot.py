"""Same-eight-row noise-amplitude sensitivity and compact diagnostic figures."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def sensitivity(coefficients):
    c = np.asarray(coefficients, dtype=float)
    if c.shape != (8, 2, 96) or not np.isfinite(c).all():
        raise ValueError("EIGHT_PAIRED_TEB_ROWS_REQUIRED")
    indices = {"T": np.arange(32), "E": [], "B": []}
    offset = 32
    for ell in range(2, 6):
        n = 2*ell+1
        indices["E"].extend(range(offset, offset+n)); offset += n
        indices["B"].extend(range(offset, offset+n)); offset += n
    out = {}
    for field, ix in indices.items():
        signal, noise = c[:, 0, ix], c[:, 1, ix]
        baseline = np.sum((signal+noise)**2, axis=1)
        if np.any(baseline <= 0):
            raise ValueError("ZERO_REFERENCE_ENERGY")
        shifts = {}
        for alpha in (.95, 1.05):
            energy = np.sum((signal+alpha*noise)**2, axis=1)
            fractional = energy/baseline-1
            shifts[str(alpha)] = {"fractional_energy_change_per_id": fractional.tolist(),
                "maximum_absolute_fractional_change": float(np.max(np.abs(fractional))),
                "median_fractional_change": float(np.median(fractional))}
        out[field] = shifts
    return {"scope": "Deterministic same-eight-ID noise-amplitude sensitivity of coefficient energy",
        "noise_amplitude_factors": [.95, 1., 1.05], "independent_realizations": 8,
        "energy_is_cl": False, "statistic_distinguishability_test": "NOT_QUALIFIED_WITH_EIGHT_ROWS",
        "physical_coverage": "NOT_ESTABLISHED", "p_value": None, "fields": out}


def main():
    directory = HERE/"results"
    targets = [directory/"NOISE_AMPLITUDE_SENSITIVITY.json", directory/"PILOT_DIAGNOSTICS.png",
               directory/"PILOT_DIAGNOSTICS.pdf"]
    if any(p.exists() for p in targets):
        raise FileExistsError("CREATE_ONLY_DIAGNOSTICS_EXIST")
    pilot = json.loads((directory/"PILOT.json").read_text())
    path = directory/"PILOT_COEFFICIENTS.npz"
    if hashlib.sha256(path.read_bytes()).hexdigest() != pilot["coefficients"]["sha256"]:
        raise ValueError("COEFFICIENT_SOURCE_CHANGED")
    with np.load(path, allow_pickle=False) as z:
        result = sensitivity(z["component_coefficients_K_CMB"])
    result.update(owner="obsstat", claim_tier="C0", status="DIAGNOSTIC_ONLY", non_claim_bearing=True,
        transfer_source="none", source_coefficients_sha256=pilot["coefficients"]["sha256"],
        method_source="Planck2018 IV section4.4.3; DOI10.1051/0004-6361/201833881",
        generating_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        caveat="Amplitude perturbation is a sensitivity calculation, not an enlarged independent bank or coverage proof.")
    with targets[0].open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.6))
    colors = ("#2864a5", "#dc7b23", "#222222")
    for column, field in enumerate(("T", "E", "B")):
        ax = axes[0, column]
        values = pilot["diagnostics"]["blocks"][field]
        for name, label, color in zip(("signal_norm_microK", "noise_plus_systematics_norm_microK", "sum_norm_microK"),
            ("CMB", "Noise + systematics", "Sum"), colors):
            ax.plot(np.arange(8), values[name], marker="o", ms=3, label=label, color=color)
        ax.set_title(field+" finite-regression norm")
        ax.set_ylabel(r"Coefficient norm [$\mu$K]")
        ax.set_xlabel("Matched simulation ID")
        ax.set_xticks(np.arange(8))
        ax.set_yscale("log")
        if column == 0:
            ax.legend(fontsize=8)
        ax = axes[1, column]
        for alpha, color in (("0.95", colors[0]), ("1.05", colors[1])):
            ax.plot(np.arange(8), np.asarray(result["fields"][field][alpha]["fractional_energy_change_per_id"])*100,
                    marker="o", ms=3, label="Noise amplitude × "+alpha, color=color)
        ax.axhline(0, color="gray", linewidth=.7)
        ax.set_title(field+" same-row noise sensitivity")
        ax.set_ylabel("Energy change [%]")
        ax.set_xlabel("Matched simulation ID")
        ax.set_xticks(np.arange(8))
        if column == 0:
            ax.legend(fontsize=8)
    fig.suptitle("Original L01 child-average support/operator: 8 FFP10 I/Q/U pairs\nDiagnostic pilot; physical coverage and joint HM/OE law unqualified", fontsize=12)
    fig.tight_layout()
    fig.savefig(targets[1], dpi=170)
    fig.savefig(targets[2])
    plt.close(fig)
    print(json.dumps({field: {alpha: row["maximum_absolute_fractional_change"] for alpha, row in values.items()}
                      for field, values in result["fields"].items()}, indent=2))


if __name__ == "__main__":
    main()
