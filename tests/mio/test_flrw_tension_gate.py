from __future__ import annotations

import json
from pathlib import Path

import pytest

from mio.tension.flrw_tension import (
    ARTEFACT_FILENAME,
    emit_flrw_tension_artefact,
    evaluate_flrw_tension,
    to_mio_certificate,
)
from obsstat.null_ensembles import (
    LookElsewhereBookkeeping,
    NullEnsembleSpec,
    build_null_ensemble_feature_payload,
)


def _report():
    return evaluate_flrw_tension(
        {"T_directional": 2.5},
        {"T_directional": [0.2, 0.4, 0.5, 0.7]},
    )


def _null_payload(
    *,
    p_values: dict[str, float] | None = None,
    statistic_keys: tuple[str, ...] = ("T_directional",),
    status: str = "global_corrected",
    covariance_status: str = "matched_covariance_calibrated",
    null_mock_status: str = "matched_null_mocks_calibrated",
    sky_support_status: str = "complete",
    mask_status: str = "matched_mask_hash",
    noise_model_status: str = "matched_noise_model",
    tail_definitions: dict[str, str] | None = None,
):
    spec = NullEnsembleSpec(
        null_ensemble_ref="mock://obsstat/flrw-mask-noise/pr102",
        null_family="flrw_mask_noise",
        mock_count=4,
        feature_targets=("flrw_null_predictive_check",),
        statistic_keys=statistic_keys,
        sky_support_status=sky_support_status,
        mask_status=mask_status,
        noise_model_status=noise_model_status,
        covariance_status=covariance_status,
        null_mock_status=null_mock_status,
        random_seed_policy="fixed_seed_manifest:pr102",
        config_hash="sha256:pr102-null-config",
        input_hashes=("sha256:pr102-null-input",),
        generating_command="python -m pytest tests/mio/test_flrw_tension_gate.py -q",
        worktree_state="test-clean",
    )
    look = LookElsewhereBookkeeping(
        look_elsewhere_status=status,
        trial_count=len(statistic_keys),
        scan_volume={
            "feature_targets": ["flrw_null_predictive_check"],
            "statistic_keys": list(statistic_keys),
            "trial_count": len(statistic_keys),
            "global_local_status": status,
        },
        correction_method="empirical_global_tail",
        pre_registration_status="pre_registered",
        tail_definitions=(
            {key: "upper_tail" for key in statistic_keys}
            if tail_definitions is None
            else tail_definitions
        ),
    )
    return build_null_ensemble_feature_payload(
        null_ensemble=spec,
        look_elsewhere=look,
        p_values=(
            {key: 0.2 for key in statistic_keys}
            if p_values is None
            else p_values
        ),
    )


def _status_metadata(cert):
    return cert.manifest.statistics_definitions["certificate_status_metadata"]


def test_bare_null_mocks_flag_cannot_promote_flrw_tension_certificate() -> None:
    cert = to_mio_certificate(_report(), null_mocks_calibrated=True)
    metadata = _status_metadata(cert)

    assert cert.reduction_status == "diagnostic-only"
    assert cert.manifest.production_status == "blocked_missing_null_mocks"
    assert cert.manifest.claim_tier == "blocked"
    assert metadata["null_predictive_distribution_status"] == "missing"
    assert metadata["tail_probability_export_status"] == "descriptive_only_blocked"
    assert metadata["raw_anomaly_pvalue_status"] == "not_exported_as_flrw_tension"
    assert "null_mocks_ready" in metadata["failed_gates"]
    assert cert.adequacy_indicators["null_predictive_distribution_ready"] is False
    assert "min_raw_ppp_pvalue" not in cert.departure_variables
    assert "minimum_empirical_tail_probability" not in cert.departure_variables
    assert "minimum_empirical_tail_probability" not in cert.consistency_metrics


def test_null_predictive_payload_enables_candidate_gate(tmp_path: Path) -> None:
    out = tmp_path / ARTEFACT_FILENAME
    payload = emit_flrw_tension_artefact(
        out,
        {"T_directional": 2.5},
        {"T_directional": [0.2, 0.4, 0.5, 0.7]},
        null_predictive_payload=_null_payload(),
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))

    assert loaded == payload
    assert "min_raw_p_value" not in payload
    assert "minimum_empirical_tail_probability" not in payload["tail_probability_summary"]
    assert payload["statistics"][0]["empirical_tail_probability"] == pytest.approx(0.2)
    assert (
        payload["statistics"][0]["tail_probability_role"]
        == "descriptive_empirical_tail_not_flrw_tension"
    )
    cert = payload["certificate"]
    metadata = cert["manifest"]["statistics_definitions"]["certificate_status_metadata"]
    assert cert["reduction_status"] == "diagnostic-only"
    assert cert["manifest"]["production_status"] == "production_candidate"
    assert cert["manifest"]["claim_tier"] == "conditional"
    assert metadata["null_predictive_distribution_status"] == "calibrated_matched"
    assert metadata["look_elsewhere_status"] == "global_corrected"
    assert metadata["tail_probability_export_status"] == "null_predictive_calibrated"
    assert metadata["transfer_source"] == "none"
    assert cert["manifest"]["config_hash"] == "sha256:pr102-null-config"
    assert cert["manifest"]["input_hashes"] == ["sha256:pr102-null-input"]


def test_null_predictive_payload_must_match_report_statistics() -> None:
    with pytest.raises(ValueError, match="p_values must match report statistic keys"):
        to_mio_certificate(
            _report(),
            null_predictive_payload=_null_payload(
                statistic_keys=("T_other",),
                p_values={"T_other": 0.2},
            ),
        )


def test_local_or_tracked_look_elsewhere_metadata_cannot_pass_gate() -> None:
    cert = to_mio_certificate(
        _report(),
        null_predictive_payload=_null_payload(status="tracked_not_corrected"),
    )
    metadata = _status_metadata(cert)

    assert cert.manifest.production_status == "blocked_missing_null_mocks"
    assert metadata["null_predictive_distribution_status"] == "not_global_corrected"
    assert "global_look_elsewhere_ready" in metadata["failed_gates"]
    assert metadata["tail_probability_export_status"] == "descriptive_only_blocked"


def test_tail_metadata_must_match_report_tail_convention() -> None:
    with pytest.raises(ValueError, match="tail_definitions must match report tails"):
        to_mio_certificate(
            _report(),
            null_predictive_payload=_null_payload(
                tail_definitions={"T_directional": "lower_tail"}
            ),
        )


def test_adversarial_support_status_strings_do_not_promote_gate() -> None:
    cert = to_mio_certificate(
        _report(),
        null_predictive_payload=_null_payload(
            covariance_status="mock_covariance_hash_pending",
            null_mock_status="mock_bank_available",
            sky_support_status="not_complete",
            mask_status="mask_hash_pending",
            noise_model_status="noise_model_recorded",
        ),
    )
    metadata = _status_metadata(cert)

    assert cert.manifest.production_status == "blocked_missing_covariance"
    assert metadata["null_predictive_distribution_status"] == "support_metadata_incomplete"
    assert "covariance_ready" in metadata["failed_gates"]
    assert "null_mocks_ready" in metadata["failed_gates"]
    assert "sky_support_complete" in metadata["failed_gates"]
    assert "mask_ready" in metadata["failed_gates"]
    assert "noise_model_ready" in metadata["failed_gates"]


def test_null_predictive_hash_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="config_hash must match"):
        to_mio_certificate(
            _report(),
            config_hash="sha256:other-config",
            null_predictive_payload=_null_payload(),
        )

    with pytest.raises(ValueError, match="input_data_hashes must match"):
        to_mio_certificate(
            _report(),
            input_data_hashes=["sha256:other-input"],
            null_predictive_payload=_null_payload(),
        )


def test_global_payload_pvalues_must_match_corrected_tail_probabilities() -> None:
    report = evaluate_flrw_tension(
        {"T_directional": 2.5, "T_biposh": 1.5},
        {
            "T_directional": [0.2, 0.4, 0.5, 0.7],
            "T_biposh": [0.1, 0.2, 0.3, 0.4],
        },
    )
    raw_local_payload = _null_payload(
        statistic_keys=("T_directional", "T_biposh"),
        p_values={"T_directional": 0.2, "T_biposh": 0.2},
    )
    with pytest.raises(ValueError, match="corrected tail probabilities"):
        to_mio_certificate(report, null_predictive_payload=raw_local_payload)

    corrected_payload = _null_payload(
        statistic_keys=("T_directional", "T_biposh"),
        p_values={"T_directional": 0.4, "T_biposh": 0.4},
    )
    cert = to_mio_certificate(report, null_predictive_payload=corrected_payload)
    assert cert.manifest.production_status == "production_candidate"
