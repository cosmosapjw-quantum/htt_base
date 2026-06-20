from __future__ import annotations

import pytest

from common.data_contracts import (
    DataAllowedUse,
    DataReadinessLevel,
    DataRole,
    SurveySupport,
    support_parity_blockers,
    survey_support_from_mapping,
    validate_data_readiness,
)


def _support(**overrides) -> SurveySupport:
    payload = {
        "survey_name": "DESI",
        "release": "Y1",
        "tracer": "BGS",
        "sky_region": "NGC",
        "redshift_range": "0.0-0.5",
        "data_path": "workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz",
        "checksum": "sha256:" + "a" * 64,
        "random_or_mask_path": "",
        "selection_weight_status": "not_bound",
        "covariance_status": "not_statistical",
        "null_mock_status": "not_statistical",
        "allowed_use": DataAllowedUse.DIAGNOSTIC_PLOT_ONLY,
        "data_role": DataRole.RAW_CATALOG,
    }
    payload.update(overrides)
    return SurveySupport(**payload)


def test_d0_accepts_derived_payload_without_randoms_or_mocks() -> None:
    support = _support(
        survey_name="Planck",
        release="PR3",
        tracer="TT",
        data_role=DataRole.HARMONIC_PRODUCT,
        selection_weight_status="not_applicable",
    )

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D0_DERIVED_AUDIT_PAYLOAD,
    )

    assert decision.allowed is True
    assert decision.claim_ceiling == "diagnostic_only"
    assert decision.blockers == ()
    assert decision.to_metadata()["support"]["data_role"] == "harmonic_product"


def test_d1_rejects_missing_checksum() -> None:
    support = _support(checksum="missing")

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D1_PRIMARY_PUBLIC_DATA,
    )

    assert decision.allowed is False
    assert decision.claim_ceiling == "blocked"
    assert "data_checksum_missing" in decision.blockers


def test_spectroscopic_dipole_rejects_missing_random_catalog() -> None:
    support = _support(selection_weight_status="native_weights_present")

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D1_PRIMARY_PUBLIC_DATA,
        intended_use="spectroscopic_dipole_production",
    )

    assert decision.allowed is False
    assert "random_or_mask_catalog_required_for_spectroscopic_dipole" in decision.blockers


def test_d2_requires_covariance_and_matched_nulls() -> None:
    support = _support(
        random_or_mask_path="workdir/randoms/desi_bgs_ngc_randoms.npz",
        random_or_mask_checksum="sha256:" + "b" * 64,
        selection_weight_status="native_weights_present",
        support_parity_status="matched_support_verified",
    )

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D2_MATCHED_MOCKS,
    )

    assert decision.allowed is False
    assert {
        "covariance_required",
        "covariance_provenance_required",
        "matched_null_mocks_required",
        "null_mock_provenance_required",
        "rank_gate_required",
        "ppc_gate_required",
        "loocv_gate_required",
    } <= set(decision.blockers)


def test_d2_rejects_toy_status_strings_without_provenance_or_gates() -> None:
    support = _support(
        random_or_mask_path="workdir/randoms/desi_bgs_ngc_randoms.npz",
        random_or_mask_checksum="sha256:" + "b" * 64,
        selection_weight_status="native_weights_present",
        support_parity_status="matched_support_verified",
        covariance_status="toy_covariance_not_a_manifest",
        null_mock_status="toy_null_bank_not_a_manifest",
    )

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D2_MATCHED_MOCKS,
    )

    assert decision.allowed is False
    assert {"covariance_required", "matched_null_mocks_required"} <= set(
        decision.blockers
    )


def test_spectroscopic_dipole_rejects_non_certified_selection_status() -> None:
    support = _support(
        random_or_mask_path="workdir/randoms/desi_bgs_ngc_randoms.npz",
        random_or_mask_checksum="sha256:" + "b" * 64,
        selection_weight_status="catalog_weight_columns_present_not_production_certified",
    )

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D1_PRIMARY_PUBLIC_DATA,
        intended_use="spectroscopic_dipole_production",
    )

    assert decision.allowed is False
    assert "selection_weight_certification_required_for_spectroscopic_dipole" in decision.blockers


def test_d2_accepts_matched_mock_support_with_bound_gate_refs() -> None:
    support = _support(
        random_or_mask_path="workdir/randoms/desi_bgs_ngc_randoms.npz",
        random_or_mask_checksum="sha256:" + "b" * 64,
        selection_weight_status="native_weights_present",
        covariance_status="mock_covariance_calibrated",
        covariance_provenance="docs/generated/covariance_manifest.json",
        null_mock_status="matched_null_mock_bank_bound",
        null_mock_provenance="docs/generated/null_mock_manifest.json",
        support_parity_status="matched_support_verified",
        rank_gate_status="rank_gate_bound",
        ppc_status="ppc_bound",
        loocv_status="loocv_bound",
    )

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D2_MATCHED_MOCKS,
    )

    assert decision.allowed is True
    assert decision.blockers == ()


def test_d3_accepts_end_to_end_simulation_support() -> None:
    support = _support(
        random_or_mask_path="workdir/randoms/desi_bgs_ngc_randoms.npz",
        random_or_mask_checksum="sha256:" + "b" * 64,
        selection_weight_status="native_weights_present",
        covariance_status="mock_covariance_calibrated",
        covariance_provenance="docs/generated/covariance_manifest.json",
        null_mock_status="end_to_end_mock_bank_bound",
        null_mock_provenance="docs/generated/null_mock_manifest.json",
        support_parity_status="matched_support_verified",
        rank_gate_status="rank_gate_bound",
        ppc_status="ppc_bound",
        loocv_status="loocv_bound",
    )

    decision = validate_data_readiness(
        support,
        DataReadinessLevel.D3_END_TO_END_SIMULATION,
        intended_use="spectroscopic_dipole_production",
    )

    assert decision.allowed is True
    assert decision.blockers == ()


def test_mapping_roundtrip_uses_string_enum_values() -> None:
    support = survey_support_from_mapping(
        {
            **_support().to_metadata(),
            "data_role": "mask",
            "random_or_mask_path": "workdir/obs_bundle/cmb/masks/temp_nside16.npz",
        }
    )

    assert support.data_role == DataRole.MASK
    assert support.to_metadata()["data_role"] == "mask"


def test_unknown_data_role_rejected() -> None:
    with pytest.raises(ValueError, match="not a valid"):
        _support(data_role="posterior")


def test_unknown_allowed_use_rejected() -> None:
    with pytest.raises(ValueError, match="not a valid"):
        _support(allowed_use="paper_main")


def test_support_parity_blocks_mismatched_random_or_mock_support() -> None:
    primary = _support(tracer="BGS", sky_region="NGC")
    companion = _support(
        data_role=DataRole.RANDOM_CATALOG,
        tracer="LRG",
        sky_region="NGC",
        random_or_mask_path="workdir/randoms/lrg_ngc_randoms.npz",
    )

    assert support_parity_blockers(primary, companion) == ("support_mismatch_tracer",)
