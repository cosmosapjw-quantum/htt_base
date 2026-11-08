"""Bianchi Transfer Adapter and Family-Compatibility Gate (R41-08).

Formalizes transfer provenance enforcement and the strict family-identification gate:
1. Strict fail-closed boundary: External transfer functions (AniCLASS, external solvers)
   MUST NEVER be labeled as native BASS / native solver results, and must be labeled
   'transfer-conditional'.
2. Zero Bianchi Family Identification: Family-identification or geometry-detection claims
   are strictly BLOCKED until an external native low-ell Bianchi Boltzmann solver arrives,
   provides an authentic morphology atlas, and passes external null/mask/covariance gates.
3. No fake solver simulation: Adapters must never synthesize, fabricate, or stub transfer values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Sequence, Tuple
from pathlib import Path

from common.enum_compat import StrEnum
from common.transfer_registry import (
    TransferSource,
    ObservableKind,
    CalibrationStatus,
    TransferFunctionSpec,
    TransferValidRange,
)


class ClaimTier(StrEnum):
    """Authoritative Claim Tiers for HTT/MIO framework."""
    C0_DIAGNOSTIC = "C0"
    C1_SCALAR_DEPARTURE = "C1"
    C2_CERTIFIED_FILLING = "C2"
    C3_DEPTH_DIRECTION_DIAGNOSTIC = "C3"
    C4_GLOBAL_TILT_CANDIDATE = "C4"
    C5_MORPHOLOGY_COMPATIBILITY = "C5"
    C6_BIANCHI_FAMILY_IDENTIFICATION = "C6"


class FamilyIdentificationBlockedError(PermissionError):
    """Raised when an unauthorized family-identification or geometry-detection claim is made."""
    pass


class TransferProvenanceViolationError(ValueError):
    """Raised when transfer function provenance is mislabeled or violates native gates."""
    pass


class NativeSolverUnavailableError(RuntimeError):
    """Raised when native Boltzmann solver is requested prior to delivery of external native solver."""
    pass


# Authoritative path for the future native Bianchi morphology atlas
NATIVE_SOLVER_ATLAS_DIR = Path("/mnt/extdrive/workdir/native_bianchi_atlas")
NATIVE_ATLAS_MANIFEST = NATIVE_SOLVER_ATLAS_DIR / "ATLAS_MANIFEST.json"


def is_native_atlas_present() -> bool:
    """Check whether a verified native low-ell Bianchi morphology atlas exists on disk."""
    return NATIVE_SOLVER_ATLAS_DIR.is_dir() and NATIVE_ATLAS_MANIFEST.is_file()


@dataclass(frozen=True)
class FamilyCompatibilityGateVerdict:
    """Diagnostic gate verdict for Bianchi morphology compatibility."""
    verdict: str  # "BLOCKED", "MORPHOLOGY_COMPATIBILITY_TRANSFER_CONDITIONAL", "PASSED"
    requested_claim_tier: str
    allowed_claim_tier: str
    is_family_identification_claimed: bool
    is_native_atlas_available: bool
    transfer_label: str
    missing_gates: Tuple[str, ...]
    blocking_reasons: Tuple[str, ...]


class BianchiTransferAdapter:
    """Adapter governing Bianchi transfer function provenance and execution."""

    def __init__(
        self,
        spec: TransferFunctionSpec,
        is_transfer_conditional: bool = True,
    ) -> None:
        self.spec = spec
        self.is_transfer_conditional = is_transfer_conditional
        self._validate_provenance()

    def _validate_provenance(self) -> None:
        """Enforce strict transfer provenance firewall."""
        source = TransferSource(self.spec.source)
        cal_status = CalibrationStatus(self.spec.calibration_status)

        # External sources (e.g. AniCLASS, external solvers) cannot claim native validation
        if source in (TransferSource.ANICLASS_EXTERNAL, TransferSource.EXTERNAL_TRANSFER):
            if cal_status in (CalibrationStatus.NATIVE_PROVISIONAL, CalibrationStatus.NATIVE_VALIDATED):
                raise TransferProvenanceViolationError(
                    f"External transfer source {source} cannot claim native status {cal_status}"
                )
            if not self.is_transfer_conditional:
                raise TransferProvenanceViolationError(
                    "External transfer products must be explicitly labeled 'transfer-conditional'"
                )

        if source in (TransferSource.BASS_NATIVE_PROVISIONAL, TransferSource.BASS_NATIVE_VALIDATED):
            if not is_native_atlas_present():
                raise NativeSolverUnavailableError(
                    "Native BASS transfer source declared, but native solver atlas is not installed on disk."
                )

    def evaluate_lowell_transfer(
        self,
        ell: int,
        k: float,
        bianchi_family: str,
    ) -> np.ndarray:
        """Evaluate low-ell transfer function under strict non-fabrication rules."""
        # Never simulate or hardcode fake solver outputs
        source = TransferSource(self.spec.source)
        if source in (TransferSource.BASS_NATIVE_PROVISIONAL, TransferSource.BASS_NATIVE_VALIDATED):
            if not is_native_atlas_present():
                raise NativeSolverUnavailableError(
                    "Native Boltzmann solver output cannot be evaluated: native solver has not arrived."
                )
            raise NotImplementedError("Native atlas reader not yet bound to disk.")

        # External transfer requires real external solver wrapper or pre-computed tabular grids
        raise NotImplementedError(
            f"Transfer evaluation for {self.spec.transfer_id} must invoke external solver binary; "
            "synthetic stubbing is forbidden in this repo."
        )


class FamilyIdentificationGate:
    """Enforces non-overclaim boundaries on Bianchi family identification."""

    FORBIDDEN_CLAIM_PHRASES = (
        "Bianchi geometry detected",
        "Bianchi family identified",
        "Bianchi family detection",
        "geometry detection",
        "family identification",
        "native solver result",
    )

    NEGATION_OR_CONTEXT_MARKERS = (
        "no ", "not ", "neither ", "nor ", "cannot ", "does not ", "never ",
        "without ", "refute", "refutes", "refuted", "forbidden", "blocked",
        "prohibit", "reject", "unsupported", "abstain", "caution", "disclaim",
        "quarantine", "unresolved", "rule", "gate", "policy", "phrase",
        "criteria", "warning", "note", "citation", "quote", "prior art"
    )

    @classmethod
    def audit_claim_text(cls, text: str) -> None:
        """Fail closed if forbidden family-identification language is asserted positively.
        
        Upgraded in R42 Stage F:
        - Prevents false-positive rejections on explicitly negated sentences,
          quotations, historical citations, or audit policy text.
        - Preserves strict fail-closed rejection of positive assertive claims.
        """
        text_lower = text.lower()
        for phrase in cls.FORBIDDEN_CLAIM_PHRASES:
            p_lower = phrase.lower()
            idx = 0
            while True:
                pos = text_lower.find(p_lower, idx)
                if pos == -1:
                    break
                end_pos = pos + len(p_lower)
                idx = end_pos

                # 1. Check if enclosed in quotes or backticks
                pre = text[max(0, pos - 2):pos]
                post = text[end_pos:min(len(text), end_pos + 2)]
                if any(q in pre for q in ("\"", "'", "`")) and any(q in post for q in ("\"", "'", "`")):
                    continue

                # 2. Extract surrounding sentence / clause
                s_start = max(
                    text_lower.rfind(".", 0, pos),
                    text_lower.rfind("\n", 0, pos),
                    text_lower.rfind(";", 0, pos)
                )
                s_start = 0 if s_start == -1 else s_start + 1
                s_end = text_lower.find(".", end_pos)
                if s_end == -1:
                    s_end = len(text_lower)
                next_nl = text_lower.find("\n", end_pos)
                if next_nl != -1 and next_nl < s_end:
                    s_end = next_nl

                sentence = text_lower[s_start:s_end]
                # If sentence contains negation or audit markers, it is non-assertive
                if any(marker in sentence for marker in cls.NEGATION_OR_CONTEXT_MARKERS):
                    continue

                # Positive assertion without qualification triggers fail-closed error
                raise FamilyIdentificationBlockedError(
                    f"Forbidden family-identification claim detected: '{phrase}'. "
                    "Claim is blocked until native low-ell morphology atlas is validated."
                )

    @classmethod
    def evaluate_gate(
        cls,
        requested_tier: str,
        transfer_spec: Optional[TransferFunctionSpec] = None,
        is_family_identification: bool = False,
    ) -> FamilyCompatibilityGateVerdict:
        """Evaluate family-identification gate against repository status and claim tier."""
        native_available = is_native_atlas_present()
        missing = []
        reasons = []

        if is_family_identification or requested_tier == ClaimTier.C6_BIANCHI_FAMILY_IDENTIFICATION:
            if not native_available:
                # Check if an external transfer is provided
                if transfer_spec is not None and TransferSource(transfer_spec.source) in (
                    TransferSource.ANICLASS_EXTERNAL, TransferSource.EXTERNAL_TRANSFER
                ):
                    # External transfer conditional family evaluation
                    missing.append("native_lowell_bianchi_morphology_atlas")
                    reasons.append(
                        "Family identification is strictly transfer-conditional upon external solver; "
                        "not admitted as native BASS family identification."
                    )
                    return FamilyCompatibilityGateVerdict(
                        verdict="BLOCKED",
                        requested_claim_tier=requested_tier,
                        allowed_claim_tier=ClaimTier.C0_DIAGNOSTIC,
                        is_family_identification_claimed=True,
                        is_native_atlas_available=False,
                        transfer_label="external-transfer-conditional",
                        missing_gates=tuple(missing),
                        blocking_reasons=tuple(reasons),
                    )

                missing.append("native_lowell_bianchi_morphology_atlas")
                missing.append("external_null_mask_covariance_gates")
                reasons.append(
                    "Family identification is strictly blocked until an authentic native solver "
                    "morphology atlas is delivered and passes external null/mask gates."
                )
                return FamilyCompatibilityGateVerdict(
                    verdict="BLOCKED",
                    requested_claim_tier=requested_tier,
                    allowed_claim_tier=ClaimTier.C0_DIAGNOSTIC,
                    is_family_identification_claimed=True,
                    is_native_atlas_available=False,
                    transfer_label="forbidden_unverified",
                    missing_gates=tuple(missing),
                    blocking_reasons=tuple(reasons),
                )

        # For morphology compatibility (C5) under external transfer:
        if requested_tier == ClaimTier.C5_MORPHOLOGY_COMPATIBILITY:
            if transfer_spec is not None:
                src = TransferSource(transfer_spec.source)
                if src in (TransferSource.ANICLASS_EXTERNAL, TransferSource.EXTERNAL_TRANSFER):
                    return FamilyCompatibilityGateVerdict(
                        verdict="MORPHOLOGY_COMPATIBILITY_TRANSFER_CONDITIONAL",
                        requested_claim_tier=requested_tier,
                        allowed_claim_tier=ClaimTier.C5_MORPHOLOGY_COMPATIBILITY,
                        is_family_identification_claimed=False,
                        is_native_atlas_available=False,
                        transfer_label="transfer-conditional",
                        missing_gates=("native_solver_atlas",),
                        blocking_reasons=(),
                    )

        # Default allowed tier prior to native solver is C0
        return FamilyCompatibilityGateVerdict(
            verdict="PASSED",
            requested_claim_tier=requested_tier,
            allowed_claim_tier=ClaimTier.C0_DIAGNOSTIC,
            is_family_identification_claimed=False,
            is_native_atlas_available=native_available,
            transfer_label="transfer-conditional" if transfer_spec else "none",
            missing_gates=(),
            blocking_reasons=(),
        )
