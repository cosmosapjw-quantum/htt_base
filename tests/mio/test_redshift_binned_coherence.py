from __future__ import annotations

import json

import numpy as np
import pytest

from mio.coherence.redshift_binned import (
    ARTEFACT_FILENAME,
    DEFAULT_Z_BINS,
    RedshiftBinnedProbe,
    RedshiftDepthBinMetadata,
    STANDARD_Z_PROBES,
    emit_redshift_coherence_artefact,
    per_bin_resultants,
    to_mio_certificate,
    total_drift_deg,
)
from mio.interface.mio_certificate import certificate_to_payload


def _metadata_for_bins(
    *,
    bins=DEFAULT_Z_BINS,
    g_f_refs: bool = True,
    bridge_metadata: bool = True,
    matched_calibration: bool = True,
    sky_support_status: str = "complete",
    mask_status: str = "complete",
) -> tuple[RedshiftDepthBinMetadata, ...]:
    return tuple(
        RedshiftDepthBinMetadata(
            bin_id=f"z{i}",
            z_min=lo,
            z_max=hi,
            selection_rule=f"fixture redshift bin {i}",
            selection_hash=f"sha256:selection-{i}",
            bin_assignment_hash=f"sha256:assignment-{i}",
            sky_support_status=sky_support_status,
            mask_status=mask_status,
            covariance_status=(
                "matched_calibrated_covariance"
                if matched_calibration
                else "diagnostic_unmatched_covariance"
            ),
            covariance_metadata={
                "covariance_hash": f"sha256:covariance-{i}",
                "estimator": "fixture-bin-axis-covariance",
                "shape": [2, 2],
                "calibration_status": (
                    "matched_calibrated"
                    if matched_calibration
                    else "diagnostic_unmatched"
                ),
            },
            null_mock_status=(
                "matched_calibrated_null"
                if matched_calibration
                else "diagnostic_unmatched_null"
            ),
            null_metadata={
                "mock_bank_hash": f"sha256:null-bank-{i}",
                "calibration_status": (
                    "matched_calibrated"
                    if matched_calibration
                    else "diagnostic_unmatched"
                ),
            },
            sample_count=8 + i,
            g_f_payload_ref=f"mio.g_f.fixture.z{i}" if g_f_refs else None,
            g_f_bridge_metadata=(
                {
                    "g_f_payload_ref": f"mio.g_f.fixture.z{i}",
                    "g_f_payload_hash": f"sha256:gf-payload-{i}",
                    "score_label": "G_F",
                    "claim_tier": "diagnostic_only",
                    "bin_id": f"z{i}",
                    "selection_hash": f"sha256:selection-{i}",
                    "covariance_hash": f"sha256:covariance-{i}",
                    "config_hash": f"cfg-gf-z{i}",
                    "input_hashes": [f"sha256:gf-input-{i}"],
                }
                if g_f_refs and bridge_metadata
                else None
            ),
        )
        for i, (lo, hi) in enumerate(bins)
    )


def _certificate(**kwargs):
    bin_results = per_bin_resultants(STANDARD_Z_PROBES)
    return to_mio_certificate(
        STANDARD_Z_PROBES,
        bin_results,
        p_drift=0.25,
        total_drift=total_drift_deg(bin_results),
        input_data_hashes=["sha256:redshift-input-fixture"],
        config_hash="cfg-pr101-redshift",
        **kwargs,
    )


def _status_metadata(cert) -> dict[str, object]:
    assert cert.manifest is not None
    return cert.manifest.statistics_definitions["certificate_status_metadata"]


@pytest.mark.parametrize("invalid_sigma", (float("nan"), float("inf")))
def test_redshift_coherence_rejects_nonfinite_cone_width(
    invalid_sigma: float,
) -> None:
    probes = (
        RedshiftBinnedProbe("invalid", 0.0, 0.0, invalid_sigma, 0.1),
        RedshiftBinnedProbe("valid", 90.0, 0.0, 1.0, 0.1),
    )
    with pytest.raises(ValueError, match="finite and strictly positive"):
        per_bin_resultants(probes, bins=((0.0, 1.0),))


def test_redshift_certificate_requires_depth_bin_metadata_for_covariance_gate() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
    )
    metadata = _status_metadata(cert)

    assert cert.reduction_status == "diagnostic-only"
    assert cert.manifest is not None
    assert cert.manifest.production_status == "blocked_missing_covariance"
    assert cert.manifest.claim_tier == "blocked"
    assert "depth_bin_covariance_metadata_complete" in cert.manifest.failed_gates
    assert "depth_bin_selection_metadata_complete" in cert.manifest.failed_gates
    assert metadata["descriptive_fallback"] is True
    assert metadata["covariance_status"] == "missing"
    assert metadata["depth_bin_covariance_status"] == "missing"
    assert metadata["depth_bin_selection_status"] == "missing"
    assert metadata["depth_bin_null_metadata_status"] == "missing"
    assert metadata["g_f_bridge_status"] == "not_attached"
    assert metadata["public_grade_label"] == "diagnostic-only"


def test_redshift_certificate_records_complete_depth_metadata_as_candidate() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
        depth_bin_metadata=_metadata_for_bins(),
    )
    metadata = _status_metadata(cert)

    assert cert.reduction_status == "diagnostic-only"
    assert cert.manifest is not None
    assert cert.manifest.production_status == "production_candidate"
    assert cert.manifest.claim_tier == "conditional"
    assert cert.manifest.failed_gates == []
    assert metadata["descriptive_fallback"] is False
    assert metadata["covariance_status"] == "available"
    assert metadata["null_mock_status"] == "available"
    assert metadata["sky_support_status"] == "complete"
    assert metadata["depth_bin_sky_mask_status"] == "complete"
    assert metadata["depth_bin_covariance_status"] == "complete"
    assert metadata["depth_bin_selection_status"] == "complete"
    assert metadata["depth_bin_null_metadata_status"] == "complete"
    assert metadata["g_f_bridge_status"] == "linked"
    assert metadata["public_grade_label"] == "production-grade"
    assert metadata["covariance_hashes"] == [
        "sha256:covariance-0",
        "sha256:covariance-1",
        "sha256:covariance-2",
    ]
    assert metadata["selection_hashes"] == [
        "sha256:selection-0",
        "sha256:selection-1",
        "sha256:selection-2",
    ]
    assert metadata["g_f_payload_refs"] == [
        "mio.g_f.fixture.z0",
        "mio.g_f.fixture.z1",
        "mio.g_f.fixture.z2",
    ]
    assert metadata["g_f_payload_hashes"] == [
        "sha256:gf-payload-0",
        "sha256:gf-payload-1",
        "sha256:gf-payload-2",
    ]


def test_redshift_certificate_without_gf_bridge_remains_descriptive() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
        depth_bin_metadata=_metadata_for_bins(g_f_refs=False),
    )
    metadata = _status_metadata(cert)

    assert cert.reduction_status == "diagnostic-only"
    assert cert.manifest is not None
    assert cert.manifest.production_status == "diagnostic_only"
    assert "g_f_bridge_metadata_attached" in cert.manifest.failed_gates
    assert metadata["descriptive_fallback"] is True
    assert metadata["depth_bin_covariance_status"] == "complete"
    assert metadata["depth_bin_selection_status"] == "complete"
    assert metadata["depth_bin_null_metadata_status"] == "complete"
    assert metadata["g_f_bridge_status"] == "not_attached"


def test_redshift_certificate_with_unmatched_calibration_remains_descriptive() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
        depth_bin_metadata=_metadata_for_bins(matched_calibration=False),
    )
    metadata = _status_metadata(cert)

    assert cert.reduction_status == "diagnostic-only"
    assert cert.manifest is not None
    assert cert.manifest.production_status == "blocked_missing_covariance"
    assert "covariance_ready" in cert.manifest.failed_gates
    assert "null_mocks_ready" in cert.manifest.failed_gates
    assert metadata["descriptive_fallback"] is True
    assert metadata["covariance_status"] == "missing"
    assert metadata["null_mock_status"] == "missing"
    assert metadata["depth_bin_covariance_status"] == "diagnostic_unmatched"
    assert metadata["depth_bin_null_metadata_status"] == "diagnostic_unmatched"
    assert metadata["g_f_bridge_status"] == "linked"


def test_redshift_certificate_with_partial_bin_sky_support_remains_descriptive() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
        depth_bin_metadata=_metadata_for_bins(sky_support_status="partial"),
    )
    metadata = _status_metadata(cert)

    assert cert.reduction_status == "diagnostic-only"
    assert cert.manifest is not None
    assert cert.manifest.production_status == "diagnostic_only"
    assert "sky_support_complete" in cert.manifest.failed_gates
    assert "depth_bin_sky_mask_metadata_complete" in cert.manifest.failed_gates
    assert metadata["caller_sky_support_status"] == "complete"
    assert metadata["sky_support_status"] == "partial"
    assert metadata["depth_bin_sky_mask_status"] == "partial"
    assert metadata["descriptive_fallback"] is True


def test_redshift_certificate_rejects_metadata_bin_mismatch() -> None:
    mismatched = _metadata_for_bins(bins=((0.0, 0.2), (0.2, 10.0), (100.0, 2000.0)))
    bin_results = per_bin_resultants(STANDARD_Z_PROBES)

    with pytest.raises(ValueError, match="must match redshift bin"):
        to_mio_certificate(
            STANDARD_Z_PROBES,
            bin_results,
            p_drift=0.2,
            total_drift=total_drift_deg(bin_results),
            has_covariance=True,
            has_null_mocks=True,
            sky_support_status="complete",
            depth_bin_metadata=mismatched,
        )


def test_redshift_metadata_rejects_reserved_claim_language() -> None:
    with pytest.raises(ValueError, match="reserved"):
        RedshiftDepthBinMetadata(
            bin_id="z0",
            z_min=0.0,
            z_max=0.1,
            selection_rule="posterior odds selection",
            selection_hash="sha256:selection",
            bin_assignment_hash="sha256:assignment",
            sky_support_status="complete",
            mask_status="complete",
            covariance_status="matched_calibrated_covariance",
            covariance_metadata={
                "covariance_hash": "sha256:covariance",
                "estimator": "fixture",
                "shape": [2, 2],
                "calibration_status": "matched_calibrated",
            },
            null_mock_status="matched_calibrated_null",
            null_metadata={
                "mock_bank_hash": "sha256:null",
                "calibration_status": "matched_calibrated",
            },
            sample_count=3,
        )


def test_redshift_certificate_payload_has_no_inference_or_family_surface() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
        depth_bin_metadata=_metadata_for_bins(),
    )
    payload_text = json.dumps(certificate_to_payload(cert), sort_keys=True).lower()

    for forbidden in (
        "posterior",
        "posterior_odds",
        "likelihood",
        "evidence",
        "truth_certificate",
        "family_identification",
        "geometry_detected",
        "native_solver_result",
    ):
        assert forbidden not in payload_text


def test_redshift_emitter_preserves_complete_status_metadata(tmp_path) -> None:
    out_path = tmp_path / ARTEFACT_FILENAME
    payload = emit_redshift_coherence_artefact(
        out_path,
        n_mock=16,
        rng=np.random.default_rng(seed=101),
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
        depth_bin_metadata=_metadata_for_bins(),
    )

    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    metadata = loaded["certificate"]["manifest"]["statistics_definitions"][
        "certificate_status_metadata"
    ]

    assert payload == loaded
    assert loaded["certificate"]["manifest"]["production_status"] == "production_candidate"
    assert metadata["depth_bin_covariance_status"] == "complete"
    assert metadata["depth_bin_selection_status"] == "complete"
    assert metadata["depth_bin_null_metadata_status"] == "complete"
    assert metadata["g_f_bridge_status"] == "linked"
