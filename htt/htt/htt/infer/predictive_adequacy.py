"""Predictive adequacy gate: PPC failure and LOOCV absence block evidence.

REV-R098 treats a failed posterior predictive check (PPC) and an unrun
leave-one-out cross-validation (LOOCV) as evidence blockers. A channel that
fails the registered PPC criterion, or whose LOOCV has not run, may not carry an
evidence claim until a later model comparison fixes it.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence

__all__ = [
    "PredictiveAdequacyGate",
    "adequacy_gate",
    "REQUIRED_NEXT_MODELS",
    "render_markdown",
]

REQUIRED_NEXT_MODELS = (
    "single_beta",
    "survey_specific_amplitudes",
    "mixture_outlier",
    "systematic_response",
)

_LOOCV_OK_TOKENS = frozenset({"passed", "complete", "run"})


@dataclass(frozen=True)
class PredictiveAdequacyGate:
    ppc_p_value: float
    ppc_threshold: float
    loocv_status: str
    config_hash: str
    input_hashes: tuple[str, ...]
    generating_command: str
    worktree_state: str

    @property
    def ppc_failed(self) -> bool:
        return self.ppc_p_value < self.ppc_threshold

    @property
    def loocv_run(self) -> bool:
        return str(self.loocv_status).strip().lower() in _LOOCV_OK_TOKENS

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.ppc_failed:
            reasons.append("ppc_failure")
        if not self.loocv_run:
            reasons.append("loocv_not_run")
        return tuple(reasons)

    @property
    def adequacy_status(self) -> str:
        return "failed" if self.blocked_reasons else "passed"

    @property
    def evidence_claim_allowed(self) -> bool:
        return not self.blocked_reasons

    def as_payload(self) -> dict[str, Any]:
        return {
            "owner": "HTT",
            "implementation_scope": "htt",
            "schema_version": "htt.predictive_adequacy.v1",
            "claim_tier": "blocked" if self.blocked_reasons else "conditional",
            "ppc_p_value": self.ppc_p_value,
            "ppc_threshold": self.ppc_threshold,
            "ppc_failed": self.ppc_failed,
            "loocv_status": self.loocv_status,
            "adequacy_status": self.adequacy_status,
            "evidence_claim_allowed": self.evidence_claim_allowed,
            "blocked_reasons": list(self.blocked_reasons),
            "required_next_models": list(REQUIRED_NEXT_MODELS),
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "worktree_state": self.worktree_state,
            "caveats": [
                "a failed PPC or unrun LOOCV blocks any channel evidence claim",
                "blocked status holds until a later model comparison fixes it",
                "no native low-ell solver output is introduced",
            ],
        }


def adequacy_gate(
    *,
    ppc_p_value: float,
    ppc_threshold: float,
    loocv_status: str,
    config_hash: str,
    input_hashes: Sequence[str],
    generating_command: str,
    worktree_state: str,
) -> PredictiveAdequacyGate:
    p_value = float(ppc_p_value)
    threshold = float(ppc_threshold)
    if not math.isfinite(p_value) or not 0.0 <= p_value <= 1.0:
        raise ValueError("ppc_p_value must be within [0, 1]")
    if not math.isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        raise ValueError("ppc_threshold must be within [0, 1]")
    return PredictiveAdequacyGate(
        ppc_p_value=p_value,
        ppc_threshold=threshold,
        loocv_status=str(loocv_status),
        config_hash=str(config_hash),
        input_hashes=tuple(str(item) for item in input_hashes),
        generating_command=str(generating_command),
        worktree_state=str(worktree_state),
    )


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Predictive Adequacy Report (REV-R098)",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        f"config_hash: `{payload['config_hash']}`",
        "input_hashes:",
        *[f"- {item}" for item in payload["input_hashes"]],
        f"generating_command: `{payload['generating_command']}`",
        f"git_commit_or_worktree_state: `{payload['worktree_state']}`",
        "",
        "## Adequacy",
        "",
        f"- PPC p-value: {payload['ppc_p_value']} (threshold {payload['ppc_threshold']})",
        f"- PPC failed: {str(payload['ppc_failed']).lower()}",
        f"- LOOCV status: {payload['loocv_status']}",
        f"- Adequacy status: {payload['adequacy_status']}",
        f"- Evidence claim allowed: {str(payload['evidence_claim_allowed']).lower()}",
        f"- Blocked reasons: {', '.join(payload['blocked_reasons']) or 'none'}",
        "",
        "## Required next models",
        "",
        *[f"- {model}" for model in payload["required_next_models"]],
        "",
        "## Caveats",
        "",
        *[f"- {item}" for item in payload["caveats"]],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    """Write the channel-(b) predictive adequacy report (PPC fail, LOOCV not run)."""
    import hashlib
    import json
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    gate = adequacy_gate(
        ppc_p_value=0.012,
        ppc_threshold=0.05,
        loocv_status="not_run",
        config_hash="sha256:"
        + hashlib.sha256(b"predictive_adequacy_channel_b").hexdigest(),
        input_hashes=("docs/generated/result_pack_B.md:channel_b_ppc",),
        generating_command="venv/bin/python -m htt.infer.predictive_adequacy",
        worktree_state="predictive_adequacy_fixture",
    )
    payload = gate.as_payload()
    out_json = repo_root / "docs" / "generated" / "predictive_adequacy_report.json"
    out_md = repo_root / "docs" / "generated" / "predictive_adequacy_report.md"
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
