"""Unit tests for BianchiTransferAdapter and FamilyIdentificationGate (R41-08)."""

import pytest

from common.transfer_registry import (
    TransferSource,
    ObservableKind,
    CalibrationStatus,
    TransferFunctionSpec,
    TransferValidRange,
)
from common.bianchi_transfer_adapter import (
    BianchiTransferAdapter,
    FamilyIdentificationGate,
    FamilyIdentificationBlockedError,
    TransferProvenanceViolationError,
    NativeSolverUnavailableError,
    ClaimTier,
)


def make_sample_transfer_spec(
    source=TransferSource.ANICLASS_EXTERNAL,
    cal_status=CalibrationStatus.EXTERNAL_CALIBRATED,
) -> TransferFunctionSpec:
    return TransferFunctionSpec(
        transfer_id="transfer_aniclass_vii_h_v1",
        source=source,
        family="VII_h",
        valid_range=TransferValidRange(k_min=1e-4, k_max=0.1, ell_min=2, ell_max=30),
        observable_kind=ObservableKind.TEMPERATURE,
        normalization="dimensionless_amplitude",
        calibration_status=cal_status,
        caveats=["External AniCLASS transfer; conditional on external numerical ODE."],
    )


def test_external_transfer_provenance_enforcement():
    """Verify that external transfer cannot claim native validation."""
    # Attempting to label AniCLASS as native validated
    with pytest.raises(ValueError, match="external transfer sources cannot claim native validation"):
        make_sample_transfer_spec(
            source=TransferSource.ANICLASS_EXTERNAL,
            cal_status=CalibrationStatus.NATIVE_VALIDATED,
        )


def test_external_transfer_must_be_transfer_conditional():
    """Verify that external transfer must be labeled 'transfer-conditional'."""
    spec = make_sample_transfer_spec(
        source=TransferSource.ANICLASS_EXTERNAL,
        cal_status=CalibrationStatus.EXTERNAL_CALIBRATED,
    )
    with pytest.raises(TransferProvenanceViolationError, match="must be explicitly labeled 'transfer-conditional'"):
        BianchiTransferAdapter(spec, is_transfer_conditional=False)

    # Valid when labeled transfer-conditional
    adapter = BianchiTransferAdapter(spec, is_transfer_conditional=True)
    assert adapter.is_transfer_conditional is True


def test_native_solver_unavailable_without_atlas():
    """Verify that native solver claims fail closed when atlas is absent."""
    spec_native = TransferFunctionSpec(
        transfer_id="transfer_bass_native_vii_h_v1",
        source=TransferSource.BASS_NATIVE_VALIDATED,
        family="VII_h",
        valid_range=TransferValidRange(k_min=1e-4, k_max=0.1, ell_min=2, ell_max=30),
        observable_kind=ObservableKind.TEMPERATURE,
        normalization="dimensionless_amplitude",
        calibration_status=CalibrationStatus.NATIVE_VALIDATED,
        caveats=["Native solver transfer."],
        passed_validation_gates=["native_transfer_validated"],
    )
    with pytest.raises(NativeSolverUnavailableError, match="native solver atlas is not installed"):
        BianchiTransferAdapter(spec_native, is_transfer_conditional=False)


def test_non_fabrication_rule():
    """Verify that adapters never synthesize or fake transfer values."""
    spec = make_sample_transfer_spec()
    adapter = BianchiTransferAdapter(spec, is_transfer_conditional=True)
    with pytest.raises(NotImplementedError, match="synthetic stubbing is forbidden"):
        adapter.evaluate_lowell_transfer(ell=2, k=0.01, bianchi_family="VII_h")


def test_family_identification_claim_audit():
    """Verify that forbidden claim phrases trigger immediate FamilyIdentificationBlockedError."""
    forbidden_claims = [
        "We report that a Bianchi geometry detected in low-ell CMB multipoles.",
        "Bianchi family identified as Bianchi VII_0 at 3-sigma.",
        "Evidence for Bianchi family detection using Planck data.",
    ]
    for claim in forbidden_claims:
        with pytest.raises(FamilyIdentificationBlockedError, match="Forbidden family-identification claim detected"):
            FamilyIdentificationGate.audit_claim_text(claim)

    # Permitted diagnostic C0 claims
    permitted = "A source-conditioned tensor-functional framework (proposed) under Claim Tier C0."
    FamilyIdentificationGate.audit_claim_text(permitted)


def test_family_identification_gate_evaluation():
    """Verify gate verdict blocks C6 and permits C5 only as transfer-conditional."""
    # Requesting C6 family identification
    verdict_c6 = FamilyIdentificationGate.evaluate_gate(
        requested_tier=ClaimTier.C6_BIANCHI_FAMILY_IDENTIFICATION,
        is_family_identification=True,
    )
    assert verdict_c6.verdict == "BLOCKED"
    assert verdict_c6.allowed_claim_tier == ClaimTier.C0_DIAGNOSTIC
    assert "native_lowell_bianchi_morphology_atlas" in verdict_c6.missing_gates

    # Requesting C5 morphology compatibility with external transfer
    spec_ext = make_sample_transfer_spec()
    verdict_c5 = FamilyIdentificationGate.evaluate_gate(
        requested_tier=ClaimTier.C5_MORPHOLOGY_COMPATIBILITY,
        transfer_spec=spec_ext,
        is_family_identification=False,
    )
    assert verdict_c5.verdict == "MORPHOLOGY_COMPATIBILITY_TRANSFER_CONDITIONAL"
    assert verdict_c5.transfer_label == "transfer-conditional"
    assert verdict_c5.allowed_claim_tier == ClaimTier.C5_MORPHOLOGY_COMPATIBILITY
