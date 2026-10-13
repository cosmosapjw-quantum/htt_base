"""OBS-07 manufactured remainder-sensitivity diagnostic.

This is a dimensionless algebraic sensitivity sweep.  Its radii are assumed
inputs, not measured physical K/M2/L bounds, and it supplies no physical
remainder certificate or coverage claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

RHO = np.array([0.0, 0.1, 0.3, 1.0])
Z_975 = 1.959963984540054
X = np.ones((3, 1))
C = np.eye(3)
M = np.ones(3) / 3.0
Y = np.array([0.2, -0.1, 0.5])
BOX_SCALE = np.array([1.0, 2.0, 1.0])
ELLIPSOID_E = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box_support(rho: float) -> float:
    """Support of ``|b_i| <= rho * (1, 2, 1)`` in the M direction."""
    return float(np.abs(M) @ (float(rho) * BOX_SCALE))


def ellipsoid_support(rho: float) -> float:
    """Support of ``b=E u, ||u||_2 <= rho`` in the M direction."""
    return float(float(rho) * np.linalg.norm(ELLIPSOID_E.T @ M))


def box_corners(rho: float) -> np.ndarray:
    signs = np.array(np.meshgrid(*([[-1.0, 1.0]] * 3))).T.reshape(-1, 3)
    return signs * float(rho) * BOX_SCALE


def ellipsoid_extremizer(rho: float) -> tuple[np.ndarray, np.ndarray]:
    direction = ELLIPSOID_E.T @ M
    if rho == 0.0:
        u = np.zeros(2)
    else:
        u = float(rho) * direction / np.linalg.norm(direction)
    return u, ELLIPSOID_E @ u


def sensitivity() -> dict:
    theta_hat = float(M @ Y)
    standard_error = float(1.0 / np.sqrt(3.0))
    rows = []
    for rho in RHO:
        box = box_support(float(rho))
        ellipsoid = ellipsoid_support(float(rho))
        rows.append({
            "rho_assumed": float(rho),
            "box_support": box,
            "ellipsoid_support": ellipsoid,
            "box_interval": [theta_hat - (Z_975 * standard_error + box), theta_hat + (Z_975 * standard_error + box)],
            "ellipsoid_interval": [theta_hat - (Z_975 * standard_error + ellipsoid), theta_hat + (Z_975 * standard_error + ellipsoid)],
        })
    return {
        "theta_hat": theta_hat,
        "standard_error": standard_error,
        "z_975": Z_975,
        "rho": RHO.tolist(),
        "rows": rows,
    }


def plot(report: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = report["numerical_outputs"]["rows"]
    rho = np.array([row["rho_assumed"] for row in rows])
    box = np.array([row["box_support"] for row in rows])
    ellipsoid = np.array([row["ellipsoid_support"] for row in rows])
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    axes[0].plot(rho, box, "o-", label="box support")
    axes[0].plot(rho, ellipsoid, "s-", label="ellipsoid support")
    axes[0].set(xlabel="assumed rho", ylabel="worst-case coefficient bias")
    axes[0].legend()
    for name, key in (("box", "box_interval"), ("ellipsoid", "ellipsoid_interval")):
        interval = np.asarray([row[key] for row in rows])
        axes[1].fill_between(rho, interval[:, 0], interval[:, 1], alpha=0.25, label=name)
    axes[1].axhline(report["numerical_outputs"]["theta_hat"], color="black", lw=1, label="theta hat")
    axes[1].set(xlabel="assumed rho", ylabel="sensitivity interval")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve()
    report = {
        "task": "OBS07-SENSITIVITY-v1",
        "claim_tier": "diagnostic-only manufactured sensitivity",
        "source_provenance": {
            "kind": "frozen Astra manufactured contract",
            "physical_input_status": "NOT_MEASURED",
            "physical_bridge": "OBS07_PHYSICAL_BRIDGE_HOLD",
        },
        "inputs": {
            "X": X.tolist(), "C": C.tolist(), "M": M.tolist(), "g": 1.0,
            "y": Y.tolist(), "box_scale": BOX_SCALE.tolist(), "ellipsoid_E": ELLIPSOID_E.tolist(),
        },
        "scope": {
            "statistic": "fixed manufactured GLS scalar estimate and conditional Gaussian standard error",
            "bias": "worst-case shift under separately assumed box or ellipsoid radii",
            "coverage": "NOT_CLAIMED; assumed radii are neither measured nor certified upper bounds",
            "minkowski_sum": "NOT_COMPUTED",
        },
        "environment": {
            "python": sys.version, "numpy": np.__version__, "script_sha256": sha256(script),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "requested_profile": "gpt-5.6-terra/medium", "observed_runtime": "UNKNOWN",
        },
        "numerical_outputs": sensitivity(),
    }
    json_path = args.output / "sensitivity.json"
    json_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    plot(report, args.output / "sensitivity.png")
    print(json.dumps({"json": str(json_path), "plot": str(args.output / "sensitivity.png"), "theta_hat": report["numerical_outputs"]["theta_hat"]}))


if __name__ == "__main__":
    main()
