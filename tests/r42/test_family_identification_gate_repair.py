"""Regression test suite for FamilyIdentificationGate Stage F repair.

Verifies:
1. Positive assertive forbidden claims are strictly blocked (fail-closed).
2. Explicitly negated statements pass without false positives.
3. Quoted prior art and citations pass without false positives.
4. Harness audit warnings, rule statements, and gate notes pass without false positives.
5. Gate evaluation properly distinguishes external transfer from native BASS solver.
"""
from __future__ import annotations

import pytest

from common.bianchi_transfer_adapter import (
    FamilyIdentificationGate,
    FamilyIdentificationBlockedError,
    TransferFunctionSpec,
    TransferValidRange,
    ObservableKind,
    CalibrationStatus,
    ClaimTier,
)
from common.transfer_registry import TransferSource


def test_positive_assertive_claims_blocked():
    """Positive assertive claims must be rejected immediately."""
    assertive_claims = [
        "We report that a Bianchi geometry detected in low-ell CMB multipoles.",
        "Bianchi family identified as Bianchi VII_0 at 3-sigma.",
        "Evidence for Bianchi family detection using Planck data.",
        "Our pipeline performs geometry detection on the sky.",
        "We achieve family identification with high confidence.",
        "The native solver result proves anisotropic expansion.",
    ]
    for claim in assertive_claims:
        with pytest.raises(FamilyIdentificationBlockedError, match="Forbidden family-identification claim detected"):
            FamilyIdentificationGate.audit_claim_text(claim)


def test_negated_statements_permitted():
    """Explicitly negated statements must not trigger false positives."""
    negated_statements = [
        "Our analysis finds no Bianchi geometry detected in the Planck data.",
        "We do not claim that any Bianchi family identified is supported.",
        "No evidence for Bianchi family detection was found across all probes.",
        "The data do not permit geometry detection at current sensitivity.",
        "We abstain from family identification without an external solver.",
        "This pipeline does not claim a native solver result.",
        "Without an authentic atlas, family identification is rejected.",
    ]
    for stmt in negated_statements:
        # Should not raise
        FamilyIdentificationGate.audit_claim_text(stmt)


def test_quoted_and_citation_text_permitted():
    """Quoted prior art, citations, and audit references must not trigger false positives."""
    quoted_texts = [
        'Prior art: the claim "Bianchi geometry detected" in Jaffe et al. (2005) is examined.',
        "Historical review: 'Bianchi family identified' claims from previous analyses are audited.",
        "Rule: The phrase 'family identification' is prohibited under Claim Tier C0.",
        "Harness warning: 'native solver result' must not be claimed before solver delivery.",
        "Policy check: verify that forbidden_claim phrase 'geometry detection' is handled.",
    ]
    for text in quoted_texts:
        # Should not raise
        FamilyIdentificationGate.audit_claim_text(text)


def test_gate_evaluation_external_transfer():
    """Verify gate evaluation distinguishes external transfer conditional status."""
    spec_ext = TransferFunctionSpec(
        transfer_id="transfer_aniclass_vii_h_v1",
        source=TransferSource.ANICLASS_EXTERNAL,
        family="VII_h",
        valid_range=TransferValidRange(k_min=1e-4, k_max=0.1, ell_min=2, ell_max=30),
        observable_kind=ObservableKind.TEMPERATURE,
        normalization="dimensionless_amplitude",
        calibration_status=CalibrationStatus.EXTERNAL_CALIBRATED,
        caveats=["External AniCLASS transfer; conditional on external numerical ODE."],
    )

    # Morphology compatibility (C5) under external transfer
    verdict_c5 = FamilyIdentificationGate.evaluate_gate(
        requested_tier=ClaimTier.C5_MORPHOLOGY_COMPATIBILITY,
        transfer_spec=spec_ext,
        is_family_identification=False,
    )
    assert verdict_c5.verdict == "MORPHOLOGY_COMPATIBILITY_TRANSFER_CONDITIONAL"
    assert verdict_c5.transfer_label == "transfer-conditional"
    assert verdict_c5.allowed_claim_tier == ClaimTier.C5_MORPHOLOGY_COMPATIBILITY

    # Family identification (C6) requested under external transfer
    verdict_c6 = FamilyIdentificationGate.evaluate_gate(
        requested_tier=ClaimTier.C6_BIANCHI_FAMILY_IDENTIFICATION,
        transfer_spec=spec_ext,
        is_family_identification=True,
    )
    assert verdict_c6.verdict == "BLOCKED"
    assert verdict_c6.transfer_label == "external-transfer-conditional"
    assert "native_lowell_bianchi_morphology_atlas" in verdict_c6.missing_gates
