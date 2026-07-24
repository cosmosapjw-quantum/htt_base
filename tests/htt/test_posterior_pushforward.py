from __future__ import annotations

import json

import pytest

from common.artifact_manifest import validate_manifest_payload
from common.transfer_registry import TransferFunctionSpec, TransferValidRange


_COMMAND = "python -m pytest tests/htt/test_posterior_pushforward.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _transfer_metadata(transfer_id: str = "aniclass-pr066") -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id=transfer_id,
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=2, ell_max=30),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref=f"aniclass:{transfer_id}",
    )
    return spec.to_metadata()


def _prerequisites(**overrides):
    from htt.departure.posterior_pushforward import PosteriorPushforwardPrerequisites

    values = {
        "local_global_status": "ready_diagnostic_likelihood",
        "local_global_report_hash": _sha("l"),
        "inference_adequacy_status": "inference_adequacy_ready",
        "inference_adequacy_report_hash": _sha("a"),
        "matched_null_status": "matched_null_ready",
        "prior_sweep_status": "prior_sweep_ready",
        "posterior_predictive_status": "posterior_predictive_ready",
        "loocv_status": "loocv_ready",
    }
    values.update(overrides)
    return PosteriorPushforwardPrerequisites(**values)


def _sample(sample_id: str, weight: float, q: float, f: float, g: float, **overrides):
    from htt.departure.posterior_pushforward import PosteriorPushforwardSample

    values = {
        "sample_id": sample_id,
        "posterior_weight": weight,
        "q_value": q,
        "f_value": f,
        "g_f_value": g,
        "x_c_value": q * 0.5,
        "transfer_source": "AniCLASS_external",
        "transfer_spec_id": "aniclass-pr066",
        "transfer_metadata": _transfer_metadata(),
        "input_hashes": (_sha(sample_id[-1]),),
    }
    values.update(overrides)
    return PosteriorPushforwardSample(**values)


def _samples():
    return (
        _sample("sample-a", 0.2, 0.10, 0.20, 1.0),
        _sample("sample-b", 0.3, 0.40, 0.60, 2.0),
        _sample("sample-c", 0.5, 0.90, 0.80, 4.0),
    )


def test_pushforward_summarizes_q_f_g_and_pi_with_manifest():
    from htt.departure.posterior_pushforward import build_posterior_pushforward_report

    report = build_posterior_pushforward_report(
        samples=_samples(),
        prerequisites=_prerequisites(),
        pi_source="Q",
        pi_thresholds=(0.2, 0.5),
        artifact_id="htt.pr066.posterior_pushforward",
        config_hash=_sha("p"),
        input_hashes=(_sha("i"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = report.as_payload()

    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "htt"
    assert payload["claim_tier"] == "conditional"
    assert payload["production_status"] == "diagnostic_only"
    assert payload["pushforward_status"] == "posterior_pushforward_ready"
    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["posterior_sample_count"] == 3
    assert payload["effective_sample_size"] == pytest.approx(1.0 / (0.2**2 + 0.3**2 + 0.5**2))
    assert payload["summaries"]["Q"]["weighted_mean"] == pytest.approx(0.59)
    assert payload["summaries"]["F"]["weighted_mean"] == pytest.approx(0.62)
    assert payload["summaries"]["G_F"]["weighted_mean"] == pytest.approx(2.8)
    assert payload["summaries"]["Q"]["weighted_quantiles"]["q50"] == pytest.approx(0.4)
    assert payload["Pi"]["source"] == "Q"
    assert payload["Pi"]["exceedance_fractions"] == pytest.approx([0.8, 0.5])
    assert payload["mio_certificate_input_status"] == "rejected_by_contract"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://pr066-posterior-pushforward.json",
    ) == ()
    text = json.dumps(payload, sort_keys=True).lower()
    assert "mio posterior" not in text
    assert "family identified" not in text
    assert "geometry detected" not in text


def test_pushforward_blocks_when_prerequisite_status_is_not_ready():
    from htt.departure.posterior_pushforward import build_posterior_pushforward_report

    report = build_posterior_pushforward_report(
        samples=_samples(),
        prerequisites=_prerequisites(inference_adequacy_status="blocked_inference_adequacy"),
        pi_source="F",
        pi_thresholds=(0.5,),
        artifact_id="htt.pr066.posterior_pushforward.blocked",
        config_hash=_sha("p"),
        input_hashes=(_sha("i"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = report.as_payload()

    assert payload["claim_tier"] == "blocked"
    assert payload["pushforward_status"] == "blocked_prerequisite_status"
    assert "inference_adequacy_not_ready" in payload["blocked_reasons"]
    assert payload["Pi"]["source"] == "F"
    assert payload["Pi"]["exceedance_fractions"] == pytest.approx([0.8])


def test_pushforward_rejects_mio_certificate_or_report_inputs():
    from workspace.contracts.mio_certificate import MioCertificate
    from htt.departure.posterior_pushforward import reject_mio_pushforward_inputs

    cert = MioCertificate(
        report_type="directional_coherence",
        probe_name="CMB",
        channel="dipole",
        departure_variables={"resultant_R": 0.91},
        adequacy_indicators={"isotropy_p_lt_0p01": True},
        consistency_metrics={"isotropy_pvalue": 0.001},
        domain_caveats=["masked_sky_partial"],
        channel_caveats=["dipole_only"],
        reduction_status="diagnostic-only",
        generated_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_data_hashes=["input"],
    )

    with pytest.raises(TypeError, match="MIO"):
        reject_mio_pushforward_inputs(cert)
    with pytest.raises(TypeError, match="MIO"):
        reject_mio_pushforward_inputs(
            {
                "owner": "MIO",
                "implementation_scope": "mio",
                "sections": {"Q": {"status": "available"}},
            }
        )


def test_transfer_provenance_is_required_for_external_pushforward_samples():
    with pytest.raises(ValueError, match="transfer_metadata"):
        _sample(
            "sample-x",
            1.0,
            0.1,
            0.2,
            1.0,
            transfer_metadata=None,
        )


def test_transfer_spec_id_must_bind_to_transfer_metadata():
    missing_id = _transfer_metadata()
    del missing_id["transfer_id"]
    with pytest.raises(ValueError, match="requires transfer_id"):
        _sample(
            "sample-x",
            1.0,
            0.1,
            0.2,
            1.0,
            transfer_metadata=missing_id,
        )

    mismatched_id = _transfer_metadata("different-transfer")
    with pytest.raises(ValueError, match="transfer_spec_id must match"):
        _sample(
            "sample-y",
            1.0,
            0.1,
            0.2,
            1.0,
            transfer_metadata=mismatched_id,
        )


def test_external_transfer_cannot_claim_native_validation():
    metadata = _transfer_metadata()
    metadata["calibration_status"] = "native_validated"

    with pytest.raises(ValueError, match="native validation"):
        _sample(
            "sample-x",
            1.0,
            0.1,
            0.2,
            1.0,
            transfer_metadata=metadata,
        )


def test_f_and_g_ranges_are_guarded():
    with pytest.raises(ValueError, match="f_value"):
        _sample("sample-x", 1.0, 0.1, -0.1, 1.0)
    with pytest.raises(ValueError, match="g_f_value"):
        _sample("sample-y", 1.0, 0.1, 0.1, 0.0)
