"""Joint multi-survey hierarchical likelihood contract (schema only).

REV-R097 defines the minimum fields required before CatWISE / radio / CF4
amplitudes may be multiplied or compared as a shared source model. This is not
an observed-data inference: it is a fail-closed contract that blocks the
conditional-independence product until cross-probe covariance, mask/selection
metadata, survey calibration nuisance, shared LSS covariance, and held-out
predictive status are all bound.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

__all__ = [
    "REQUIRED_JOINT_FIELDS",
    "JointSurveyHierarchyContract",
    "build_joint_hierarchy_contract",
]

REQUIRED_JOINT_FIELDS = (
    "cross_probe_covariance",
    "mask_selection_metadata",
    "survey_calibration_nuisance",
    "shared_lss_covariance",
    "heldout_predictive",
)

_BLOCK_REASON_BY_FIELD = {
    "cross_probe_covariance": "cross_probe_covariance_not_bound",
    "mask_selection_metadata": "mask_selection_metadata_not_bound",
    "survey_calibration_nuisance": "survey_calibration_nuisance_not_bound",
    "shared_lss_covariance": "shared_lss_covariance_not_bound",
    "heldout_predictive": "heldout_predictive_not_run",
}

_BOUND_TOKENS = frozenset({"bound", "complete", "passed"})


@dataclass(frozen=True)
class JointSurveyHierarchyContract:
    probes: tuple[str, ...]
    covariance_status: str
    mask_selection_status: str
    nuisance_status: str
    shared_lss_covariance_status: str
    heldout_status: str
    config_hash: str
    input_hashes: tuple[str, ...]
    generating_command: str
    worktree_state: str

    def _status_for(self, field: str) -> str:
        return {
            "cross_probe_covariance": self.covariance_status,
            "mask_selection_metadata": self.mask_selection_status,
            "survey_calibration_nuisance": self.nuisance_status,
            "shared_lss_covariance": self.shared_lss_covariance_status,
            "heldout_predictive": self.heldout_status,
        }[field]

    def _is_bound(self, field: str) -> bool:
        return str(self._status_for(field)).strip().lower() in _BOUND_TOKENS

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        return tuple(
            _BLOCK_REASON_BY_FIELD[field]
            for field in REQUIRED_JOINT_FIELDS
            if not self._is_bound(field)
        )

    @property
    def conditional_independence_product_allowed(self) -> bool:
        return not self.blocked_reasons

    @property
    def claim_tier(self) -> str:
        return "blocked" if self.blocked_reasons else "conditional"

    def as_payload(self) -> dict[str, Any]:
        return {
            "owner": "HTT",
            "implementation_scope": "htt",
            "schema_version": "htt.joint_survey_hierarchy.v1",
            "claim_tier": self.claim_tier,
            "probes": list(self.probes),
            "field_status": {
                field: self._status_for(field) for field in REQUIRED_JOINT_FIELDS
            },
            "required_fields": list(REQUIRED_JOINT_FIELDS),
            "conditional_independence_product_allowed": (
                self.conditional_independence_product_allowed
            ),
            "blocked_reasons": list(self.blocked_reasons),
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "worktree_state": self.worktree_state,
            "caveats": [
                "schema-only joint-survey hierarchy contract, not an inference",
                "the conditional-independence product is blocked until every "
                "required field is bound",
                "no native low-ell solver output is introduced",
            ],
        }


def build_joint_hierarchy_contract(
    *,
    probes: Sequence[str],
    covariance_status: str,
    nuisance_status: str,
    heldout_status: str,
    mask_selection_status: str = "not_bound",
    shared_lss_covariance_status: str = "not_bound",
    config_hash: str,
    input_hashes: Sequence[str],
    generating_command: str,
    worktree_state: str,
) -> JointSurveyHierarchyContract:
    probe_tuple = tuple(str(item) for item in probes)
    if not probe_tuple:
        raise ValueError("probes must be a non-empty sequence")
    return JointSurveyHierarchyContract(
        probes=probe_tuple,
        covariance_status=str(covariance_status),
        mask_selection_status=str(mask_selection_status),
        nuisance_status=str(nuisance_status),
        shared_lss_covariance_status=str(shared_lss_covariance_status),
        heldout_status=str(heldout_status),
        config_hash=str(config_hash),
        input_hashes=tuple(str(item) for item in input_hashes),
        generating_command=str(generating_command),
        worktree_state=str(worktree_state),
    )
