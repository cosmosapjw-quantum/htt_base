"""Redshift-selection correction metadata for spectroscopic dipole features."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re
from typing import Any

import numpy as np

__all__ = [
    "RedshiftSelectionCorrectionSpec",
    "apply_redshift_selection_correction",
]


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_OBSERVED_SELECTION_BASES = {"observed_redshift", "observed_redshift_selected"}
_SELECTION_BASES = {
    "observed_redshift",
    "observed_redshift_selected",
    "cosmological_redshift",
    "rest_frame_redshift",
}
_BOUND_STATUSES = {
    "correction_model_bound",
    "redshift_selection_correction_bound",
    "survey_correction_bound",
}
_TOY_BOUND_STATUSES = {
    "toy_correction_bound",
}
_BLOCKING_STATUSES = {
    "missing",
    "not_bound",
    "not_available",
    "metadata_only",
    "required_not_bound",
}


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


def _vector3(value: object, field: str) -> tuple[float, float, float]:
    array = np.asarray(value, dtype=float)
    if array.shape != (3,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must be a finite 3-vector")
    return (float(array[0]), float(array[1]), float(array[2]))


@dataclass(frozen=True)
class RedshiftSelectionCorrectionSpec:
    """Diagnostic metadata for redshift-selection dipole corrections."""

    z_bin_id: str
    selection_basis: str
    correction_status: str
    config_hash: str
    input_hashes: Sequence[str]
    generating_command: str
    worktree_state: str
    correction_vector: Sequence[float] = (0.0, 0.0, 0.0)
    reference_id: str = "von_hausegger_dalang_2025_prd111_123547"

    def __post_init__(self) -> None:
        object.__setattr__(self, "z_bin_id", _text(self.z_bin_id, "z_bin_id"))
        basis = _text(self.selection_basis, "selection_basis").lower()
        if basis not in _SELECTION_BASES:
            raise ValueError("selection_basis is not supported")
        object.__setattr__(self, "selection_basis", basis)
        status = _text(self.correction_status, "correction_status").lower()
        object.__setattr__(self, "correction_status", status)
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
        object.__setattr__(
            self,
            "correction_vector",
            _vector3(self.correction_vector, "correction_vector"),
        )
        object.__setattr__(self, "reference_id", _text(self.reference_id, "reference_id"))

    @property
    def required_for_observed_redshift_bins(self) -> bool:
        return self.selection_basis in _OBSERVED_SELECTION_BASES

    @property
    def is_bound(self) -> bool:
        return self.correction_status in _BOUND_STATUSES or self.correction_status in _TOY_BOUND_STATUSES

    @property
    def is_survey_bound(self) -> bool:
        return self.correction_status in _BOUND_STATUSES

    @property
    def blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.required_for_observed_redshift_bins and not self.is_survey_bound:
            blockers.append("redshift_selection_correction_not_bound")
        if self.correction_status in _BLOCKING_STATUSES:
            blockers.append(f"redshift_selection_status_{self.correction_status}")
        return tuple(dict.fromkeys(blockers))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": "diagnostic_only",
            "transfer_source": "none",
            "artifact_role": "redshift_selection_correction_metadata",
            "z_bin_id": self.z_bin_id,
            "selection_basis": self.selection_basis,
            "required_for_observed_redshift_bins": self.required_for_observed_redshift_bins,
            "correction_status": self.correction_status,
            "is_bound": self.is_bound,
            "is_survey_bound": self.is_survey_bound,
            "correction_vector": list(self.correction_vector),
            "references": [
                self.reference_id,
                "https://doi.org/10.1103/PhysRevD.111.123547",
            ],
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit_or_worktree_state": self.worktree_state,
            "publication_ready": False,
            "blockers": list(self.blockers),
            "caveats": [
                "metadata and toy correction hook only",
                "requires survey-specific selection model before public result use",
                "no null-calibrated significance is attached",
            ],
        }


def apply_redshift_selection_correction(
    dipole_vector: Sequence[float],
    correction: RedshiftSelectionCorrectionSpec,
) -> np.ndarray:
    """Apply the diagnostic correction hook when its metadata is bound."""

    vector = np.asarray(dipole_vector, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError("dipole_vector must be a finite 3-vector")
    if not correction.is_bound:
        return vector.copy()
    return vector - np.asarray(correction.correction_vector, dtype=float)
