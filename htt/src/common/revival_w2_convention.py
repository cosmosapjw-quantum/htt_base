"""PR-211: constraint-natural conventions and signed curvature split (RESCUE).

The W2 convention theorem and its five-axis CAS proof are already closed in
PR-186 (W2 := omega_ab omega^ab/(6H^2) = omega_a omega^a/(3H^2); Theta=3H gives
sqrt(omega_ab omega^ab)/Theta <= B => W2 <= 3 B^2/2; frozen W2_max unchanged).
This module is the clean-room LEGACY SUCCESSOR: the patched htt/ssot.py
conventions plus the signed DeltaOmega_k / tensor-3-Ricci PSTF split, and a
cross-reference guard that the frozen PR-186 numbers are byte-identical. It
never recomputes or re-freezes an anchor.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
PR186_CARD = REPO / "docs/generated/pr186_result_card.json"
CLEANUP_BASE = "0864b00948143d9b19d4983e50fcd2d905f4a5d3"

# Frozen PR-186 anchors this rescue cross-references (must stay byte-identical).
FROZEN_W2_MAX = 3.3789222980376e-13
FROZEN_WRONG_OVER_RIGHT_RATIO = 3


# --- patched legacy successor: constraint-natural conventions ---------------
def sigma2(sigma_ab_sq: float, H: float) -> float:
    if H <= 0:
        raise ValueError("H must be positive")
    return sigma_ab_sq / (6.0 * H * H)


def w2_from_tensor(omega_ab_sq: float, H: float) -> float:
    if H <= 0:
        raise ValueError("H must be positive")
    return omega_ab_sq / (6.0 * H * H)


def w2_from_vector(omega_a_sq: float, H: float) -> float:
    if H <= 0:
        raise ValueError("H must be positive")
    return omega_a_sq / (3.0 * H * H)


def assert_dual_identity(omega_ab_sq: float, omega_a_sq: float, H: float,
                         tol: float = 1e-13) -> None:
    """omega_ab omega^ab = 2 omega_a omega^a and the two W2 forms agree."""
    if abs(omega_ab_sq - 2.0 * omega_a_sq) > tol * max(1.0, abs(omega_ab_sq)):
        raise ValueError("dual convention omega_ab omega^ab = 2 omega_a omega^a violated")
    if abs(w2_from_tensor(omega_ab_sq, H) - w2_from_vector(omega_a_sq, H)) > tol:
        raise ValueError("W2 convention mismatch between tensor and vector forms")


def w2_ceiling(B: float) -> float:
    """sqrt(omega_ab omega^ab)/Theta <= B  =>  W2 <= 3 B^2 / 2."""
    return 1.5 * B * B


# --- signed curvature split -------------------------------------------------
def signed_delta_omega_k(value: float) -> float:
    """Scalar curvature departure DeltaOmega_k is a SIGNED carrier."""
    return float(value)


def pstf_3ricci_magnitude(components_sq: float) -> float:
    """The tensor 3-Ricci PSTF sector carries a nonnegative magnitude."""
    if components_sq < 0:
        raise ValueError("PSTF 3-Ricci magnitude must be nonnegative")
    return float(components_sq)


def force_psd_would_lose_sign(value: float) -> bool:
    """Mutation detector: forcing DeltaOmega_k to a PSD magnitude drops the sign."""
    return abs(value) != value  # True exactly when value < 0 (sign would be lost)


# --- cross-reference guard on the frozen PR-186 evidence ---------------------
def crossref_pr186() -> dict:
    if PR186_CARD.is_file():
        raw = PR186_CARD.read_bytes()
    else:
        relative = PR186_CARD.relative_to(REPO).as_posix()
        raw = subprocess.run(
            ["git", "show", f"{CLEANUP_BASE}:{relative}"],
            cwd=REPO,
            check=True,
            capture_output=True,
        ).stdout
    card = json.loads(raw)
    cas = card.get("result", {}).get("cas_status", {})
    w2 = card.get("result", {})

    def _find(obj, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    return v
                r = _find(v, key)
                if r is not None:
                    return r
        elif isinstance(obj, list):
            for x in obj:
                r = _find(x, key)
                if r is not None:
                    return r
        return None

    frozen = _find(card, "frozen_mes_vorticity_ceiling_W2_max")
    ratio = _find(card, "wrong_over_right_ratio")
    aggregate = _find(card, "aggregate")
    return {
        "pr186_terminal": card.get("terminal"),
        "cas_aggregate": aggregate,
        "frozen_W2_max": frozen,
        "wrong_over_right_ratio": ratio,
        "frozen_unchanged": frozen == FROZEN_W2_MAX,
        "ratio_is_three": str(ratio) == str(FROZEN_WRONG_OVER_RIGHT_RATIO),
        "cas_five_axis_pass": aggregate == "CAS_5AXIS_PASS",
    }
