"""ver3 PR-11 validation gate and fitting hard-stop helpers."""
from __future__ import annotations

from typing import Any, Mapping

__all__ = [
    "GATE_LADDER",
    "hard_gate_before_fitting",
    "score_branch_readiness",
]


GATE_LADDER: tuple[str, ...] = (
    "authority_freeze",
    "tensor_helper_correctness",
    "family_registry_freeze",
    "geometry_diagnostics_gate",
    "matter_projection_gate",
    "exact_thomson_gate",
    "visibility_history_gate",
    "family_backend_gate",
    "hierarchy_layout_gate",
    "output_split_gate",
    "fitting_gate",
)


def _gate_map(gates: Mapping[str, object]) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for gate in GATE_LADDER:
        out[gate] = bool(gates.get(gate, False))
    return out


def hard_gate_before_fitting(gates: Mapping[str, object]) -> dict[str, Any]:
    """Return a machine-readable fitting hard-stop report."""
    gate_map = _gate_map(gates)
    required = GATE_LADDER[:-1]
    missing = tuple(gate for gate in required if not gate_map[gate])
    allowed = len(missing) == 0
    return {
        "gate_name": "fitting_hard_stop",
        "allowed": allowed,
        "required_gates": required,
        "missing_gates": missing,
        "opened_gates": tuple(gate for gate, state in gate_map.items() if state),
        "reason": (
            "all upstream gates open; fitting may evaluate"
            if allowed
            else "upstream gates missing; fitting prohibited"
        ),
    }


def score_branch_readiness(gates: Mapping[str, object]) -> int:
    """Map consecutive opened gates onto the ver3 readiness scoreboard."""
    gate_map = _gate_map(gates)
    consecutive = 0
    for gate in GATE_LADDER:
        if not gate_map[gate]:
            break
        consecutive += 1
    if consecutive == 0:
        return 0
    if consecutive <= 3:
        return 4
    if consecutive <= 8:
        return 6
    if consecutive <= 10:
        return 8
    return 10
