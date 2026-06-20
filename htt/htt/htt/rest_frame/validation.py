"""Validation summary gates for joint rest-frame diagnostics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re
from typing import Any


__all__ = ["RestFrameValidationSummary"]


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ALLOWED_STATUSES = {"passed", "not_bound", "failed", "not_evaluated"}
_STATUS_FIELDS = (
    "prior_support_status",
    "matched_null_status",
    "ppc_status",
    "leave_one_out_status",
    "covariance_sensitivity_status",
)


def _text(value: object, field: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _sha256_text(value: object, field: str) -> str:
    text = _text(value, field)
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{field} must be a sha256 hash")
    return text


def _sha256_sequence(value: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{field} must be a non-empty sequence of sha256 hashes")
    return tuple(_sha256_text(item, field) for item in value)


def _status(value: object, field: str) -> str:
    text = _text(value, field).lower()
    if text not in _ALLOWED_STATUSES:
        raise ValueError(f"{field} must be one of {', '.join(sorted(_ALLOWED_STATUSES))}")
    return text


@dataclass(frozen=True)
class RestFrameValidationSummary:
    """Pre-inference validation-status bundle for rest-frame model candidates."""

    prior_support_status: str
    matched_null_status: str
    ppc_status: str
    leave_one_out_status: str
    covariance_sensitivity_status: str
    config_hash: str
    input_hashes: Sequence[str]
    generating_command: str
    worktree_state: str

    def __post_init__(self) -> None:
        for field in _STATUS_FIELDS:
            object.__setattr__(self, field, _status(getattr(self, field), field))
        object.__setattr__(self, "config_hash", _sha256_text(self.config_hash, "config_hash"))
        object.__setattr__(
            self,
            "input_hashes",
            _sha256_sequence(tuple(self.input_hashes), "input_hashes"),
        )
        object.__setattr__(
            self,
            "generating_command",
            _text(self.generating_command, "generating_command"),
        )
        object.__setattr__(self, "worktree_state", _text(self.worktree_state, "worktree_state"))

    @property
    def blockers(self) -> tuple[str, ...]:
        blockers = [
            f"{field}_not_passed"
            for field in _STATUS_FIELDS
            if getattr(self, field) != "passed"
        ]
        return tuple(blockers)

    @property
    def evidence_grade_allowed(self) -> bool:
        return False

    @property
    def validation_preconditions_passed(self) -> bool:
        return not self.blockers

    @property
    def claim_status(self) -> str:
        if self.validation_preconditions_passed:
            return "validation_preconditions_passed"
        return "blocked_validation_incomplete"

    def to_payload(self) -> dict[str, Any]:
        return {
            "owner": "HTT",
            "implementation_scope": "htt",
            "claim_tier": "diagnostic_only",
            "artifact_role": "joint_rest_frame_validation_summary",
            "production_status": "pre_inference_gate",
            "transfer_source": "none",
            "native_solver_result": False,
            "family_identification": False,
            "prior_support_status": self.prior_support_status,
            "matched_null_status": self.matched_null_status,
            "ppc_status": self.ppc_status,
            "leave_one_out_status": self.leave_one_out_status,
            "covariance_sensitivity_status": self.covariance_sensitivity_status,
            "evidence_grade_allowed": self.evidence_grade_allowed,
            "validation_preconditions_passed": self.validation_preconditions_passed,
            "claim_status": self.claim_status,
            "blockers": list(self.blockers),
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit_or_worktree_state": self.worktree_state,
            "caveats": [
                "validation preconditions only",
                "does not create evidence-grade output",
                "does not identify a Bianchi family or geometry",
            ],
        }
