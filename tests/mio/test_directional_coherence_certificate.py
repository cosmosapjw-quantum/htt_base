from __future__ import annotations

import json

import numpy as np

from mio.coherence.directional import (
    STANDARD_PROBES,
    emit_directional_coherence_artefact,
    resultant_vector,
    to_mio_certificate,
)
from mio.interface.mio_certificate import certificate_to_payload


def _certificate(**kwargs):
    return to_mio_certificate(
        STANDARD_PROBES,
        p_iso=0.02,
        resultant=resultant_vector(STANDARD_PROBES),
        input_data_hashes=["sha256:directional-input-fixture"],
        config_hash="cfg-pr100-directional",
        **kwargs,
    )


def _status_metadata(cert) -> dict[str, object]:
    assert cert.manifest is not None
    return cert.manifest.statistics_definitions["certificate_status_metadata"]


def test_directional_certificate_records_missing_covariance_statuses() -> None:
    cert = _certificate()
    manifest = cert.manifest
    metadata = _status_metadata(cert)

    assert cert.reduction_status == "diagnostic-only"
    assert manifest is not None
    assert manifest.owner == "MIO"
    assert manifest.implementation_scope == "mio"
    assert manifest.production_status == "blocked_missing_covariance"
    assert manifest.claim_tier == "blocked"
    assert "covariance_ready" in manifest.failed_gates
    assert "null_mocks_ready" in manifest.failed_gates
    assert "sky_support_complete" in manifest.failed_gates

    assert metadata["covariance_status"] == "missing"
    assert metadata["null_mock_status"] == "missing"
    assert metadata["sky_support_status"] == "partial"
    assert metadata["transfer_source"] == "none"
    assert metadata["direction_convention"] == "oriented_unit_direction"
    assert metadata["weighting_convention"] == "diagonal_sigma_cone_inverse_variance"
    assert metadata["cross_probe_covariance_status"] == "not_attached"
    assert metadata["null_calibration_status"] == "toy_isotropy_mc_unmatched"
    assert metadata["claim_scope"] == "diagnostic_only_directional_coherence"
    assert metadata["public_grade_label"] == "diagnostic-only"
    assert metadata["production_status"] == "blocked_missing_covariance"
    assert metadata["claim_tier"] == "blocked"


def test_directional_certificate_records_partial_completion_without_promotion() -> None:
    cert = _certificate(has_covariance=True)
    metadata = _status_metadata(cert)

    assert cert.manifest is not None
    assert cert.manifest.production_status == "blocked_missing_null_mocks"
    assert cert.reduction_status == "diagnostic-only"
    assert metadata["covariance_status"] == "available"
    assert metadata["null_mock_status"] == "missing"
    assert metadata["sky_support_status"] == "partial"
    assert metadata["public_grade_label"] == "diagnostic-only"


def test_directional_certificate_is_diagnostic_only_when_sky_support_incomplete() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="partial",
    )
    metadata = _status_metadata(cert)

    assert cert.manifest is not None
    assert cert.manifest.production_status == "diagnostic_only"
    assert cert.manifest.claim_tier == "exploratory"
    assert cert.reduction_status == "diagnostic-only"
    assert "sky_support_complete" in cert.manifest.failed_gates
    assert metadata["covariance_status"] == "available"
    assert metadata["null_mock_status"] == "available"
    assert metadata["sky_support_status"] == "partial"
    assert metadata["public_grade_label"] == "diagnostic-only"


def test_directional_certificate_records_complete_prerequisites_as_candidate() -> None:
    cert = _certificate(
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
    )
    metadata = _status_metadata(cert)

    assert cert.manifest is not None
    assert cert.manifest.production_status == "production_candidate"
    assert cert.reduction_status == "diagnostic-only"
    assert metadata["covariance_status"] == "available"
    assert metadata["null_mock_status"] == "available"
    assert metadata["sky_support_status"] == "complete"
    assert metadata["cross_probe_covariance_status"] == "available"
    assert metadata["null_calibration_status"] == "matched_null_mocks_available"
    assert metadata["public_grade_label"] == "production-grade"
    assert metadata["failed_gates"] == []


def test_directional_certificate_payload_has_no_truth_or_posterior_odds_surface() -> None:
    cert = _certificate()
    payload = certificate_to_payload(cert)
    payload_text = json.dumps(payload, sort_keys=True).lower()

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
    assert payload["reduction_status"] == "diagnostic-only"
    assert payload["manifest"]["statistics_definitions"][
        "certificate_status_metadata"
    ]["public_grade_label"] == "diagnostic-only"


def test_directional_emitter_preserves_complete_status_metadata(tmp_path) -> None:
    out_path = tmp_path / "mio_directional_coherence.json"

    payload = emit_directional_coherence_artefact(
        out_path,
        n_mock=16,
        rng=np.random.default_rng(seed=100),
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
    )

    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    status_metadata = loaded["certificate"]["manifest"]["statistics_definitions"][
        "certificate_status_metadata"
    ]

    assert payload == loaded
    assert loaded["certificate"]["manifest"]["production_status"] == "production_candidate"
    assert status_metadata["covariance_status"] == "available"
    assert status_metadata["null_mock_status"] == "available"
    assert status_metadata["sky_support_status"] == "complete"
    assert status_metadata["direction_convention"] == "oriented_unit_direction"
    assert status_metadata["weighting_convention"] == "diagonal_sigma_cone_inverse_variance"
    assert status_metadata["null_calibration_status"] == "matched_null_mocks_available"
    assert status_metadata["failed_gates"] == []
