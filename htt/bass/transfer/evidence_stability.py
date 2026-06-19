"""Transfer-conditional evidence-stability diagnostics."""
from __future__ import annotations

import math


def evidence_shift_bound(max_loglike_delta: float) -> dict[str, object]:
    """Return the diagnostic bound |Delta log Z| <= epsilon."""

    epsilon = float(max_loglike_delta)
    if not math.isfinite(epsilon) or epsilon < 0.0:
        raise ValueError("max_loglike_delta must be non-negative finite")
    return {
        "owner": "BASS",
        "implementation_scope": "bass_py",
        "claim_tier": "diagnostic_only",
        "transfer_source": "external_or_proxy_transfer",
        "transfer_conditional": True,
        "native_solver_result": False,
        "evidence_shift_upper_bound": epsilon,
        "definition": "|Delta log Z| <= sup |Delta log L| under shared prior support",
        "caveats": [
            "transfer-conditional diagnostic only",
            "not native solver validation",
            "not HTT evidence",
            "not MIO evidence",
            "not family or geometry evidence",
        ],
    }


__all__ = ["evidence_shift_bound"]
