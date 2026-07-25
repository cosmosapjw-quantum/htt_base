from __future__ import annotations

import json

import pytest

from common.artifact_manifest import validate_manifest_payload
from mio.decomposition.evidence_anatomy import (
    HttEvidenceTrace,
    HttEvidenceTraceTerm,
    build_evidence_anatomy_narrative_report,
    build_htt_evidence_trace_from_payload,
)
from mio.diagnostics.predictive_residuals import (
    ResidualChannelSlice,
    build_predictive_residual_atlas,
    predictive_residual_atlas_payload,
)


_COMMAND = "python -m pytest tests/mio/test_mio_evidence_anatomy_no_merge.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _trace_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "trace_id": "htt.pr103.trace",
        "owner": "HTT",
        "implementation_scope": "htt",
        "model_label": "local_global_candidate",
        "total_delta_lnB": 2.15,
        "evidence_ref": "htt.pr065.inference_adequacy",
        "channel_contributions": {
            "cmb_low_ell": 1.25,
            "velocity_depth": 0.70,
            "survey_systematic": 0.20,
        },
        "input_hashes": [_sha("i")],
        "config_hash": _sha("c"),
        "prior_sweep_status": "prior_sweep_ready",
        "posterior_predictive_status": "posterior_predictive_ready",
        "loocv_status": "loocv_ready",
        "matched_null_status": "matched_null_ready",
    }
    payload.update(overrides)
    return payload


def _atlas():
    return build_predictive_residual_atlas(
        (
            ResidualChannelSlice(
                "local_global_candidate",
                "TT",
                2,
                5,
                rms_residual=0.30,
                max_abs_residual=0.50,
                n_modes=4,
            ),
            ResidualChannelSlice(
                "null_competitor",
                "EE",
                2,
                5,
                rms_residual=0.10,
                max_abs_residual=0.20,
                n_modes=4,
            ),
        ),
        atlas_ref="mio.residual.atlas",
        covariance_ref="htt.pr065.posterior_predictive",
    )


def test_evidence_trace_payload_is_copied_and_rejected_as_mio_input():
    source = _trace_payload()
    trace = build_htt_evidence_trace_from_payload(source)
    source["total_delta_lnB"] = 999.0
    source["channel_contributions"] = {"mutated": 999.0}

    assert trace.total_delta_lnB == pytest.approx(2.15)
    assert trace.channel_contributions == {
        "cmb_low_ell": pytest.approx(1.25),
        "survey_systematic": pytest.approx(0.20),
        "velocity_depth": pytest.approx(0.70),
    }
    with pytest.raises(ValueError, match="HTT"):
        build_htt_evidence_trace_from_payload(_trace_payload(owner="MIO"))
    with pytest.raises(ValueError, match="merge"):
        build_htt_evidence_trace_from_payload(
            _trace_payload(mio_htt_merged_score=1.0)
        )


@pytest.mark.parametrize(
    ("overrides", "field"),
    (
        ({"config_hash": None}, "config_hash"),
        ({"input_hashes": [None]}, "input_hashes"),
        (
            {
                "channel_contributions": None,
                "terms": [{"channel": None, "delta_lnB": 2.15}],
            },
            r"terms\[0\]\.channel",
        ),
    ),
)
def test_evidence_trace_rejects_null_required_fields(overrides, field):
    with pytest.raises(ValueError, match=field):
        build_htt_evidence_trace_from_payload(_trace_payload(**overrides))


def test_predictive_residual_payload_is_diagnostic_context_only():
    payload = predictive_residual_atlas_payload(_atlas())

    assert payload["owner"] == "MIO"
    assert payload["implementation_scope"] == "mio"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["mio_role"] == "residual_context_only"
    assert payload["not_htt_evidence"] is True
    assert payload["worst_model_label"] == "local_global_candidate"
    assert payload["worst_channel"] == "TT"
    assert "single_score" not in payload


def test_evidence_anatomy_narrative_records_no_merge_manifest():
    trace = build_htt_evidence_trace_from_payload(_trace_payload())
    report = build_evidence_anatomy_narrative_report(
        evidence_trace=trace,
        residual_atlas=_atlas(),
        artifact_id="mio.pr103.evidence_anatomy",
        artifact_path="memory://mio/pr103/evidence_anatomy.json",
        config_hash=_sha("p"),
        input_hashes=(_sha("i"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = report.as_payload()

    assert payload["owner"] == "MIO"
    assert payload["implementation_scope"] == "mio"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["production_status"] == "diagnostic_only"
    assert payload["trace_source_owner"] == "HTT"
    assert payload["mio_role"] == "diagnostic_narrative_only"
    assert payload["htt_evidence_modification_status"] == "read_only_copy"
    assert payload["single_score_status"] == "forbidden_no_owner_merge"
    assert payload["ready_for_diagnostic_narrative"] is True
    assert payload["anatomy"]["total_delta_lnB"] == pytest.approx(2.15)
    assert payload["anatomy"]["reconstructed_delta_lnB"] == pytest.approx(2.15)
    assert payload["residual_context"]["worst_channel"] == "TT"
    assert payload["htt_evidence_trace"]["total_delta_lnB"] == pytest.approx(2.15)
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://mio-pr103-evidence-anatomy.json",
    ) == ()
    text = json.dumps(payload, sort_keys=True).lower()
    assert "mio posterior" not in text
    assert "truth certificate" not in text
    assert "family identified" not in text
    assert "geometry detected" not in text


def test_narrative_blocks_failed_adequacy_without_changing_trace_values():
    report = build_evidence_anatomy_narrative_report(
        evidence_trace=build_htt_evidence_trace_from_payload(
            _trace_payload(posterior_predictive_status="blocked_posterior_predictive")
        ),
        artifact_id="mio.pr103.evidence_anatomy.blocked",
        artifact_path="memory://mio/pr103/evidence_anatomy_blocked.json",
        config_hash=_sha("p"),
        input_hashes=(_sha("i"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = report.as_payload()

    assert payload["claim_tier"] == "blocked"
    assert payload["production_status"] == "blocked_provenance_mismatch"
    assert "posterior_predictive_not_ready" in payload["blocked_reasons"]
    assert payload["anatomy"]["total_delta_lnB"] == pytest.approx(2.15)


def test_narrative_rejects_direct_mio_terms_and_single_score_requests():
    trace = HttEvidenceTrace(
        trace_id="htt.pr103.trace",
        model_label="local_global_candidate",
        total_delta_lnB=1.0,
        evidence_ref="htt.pr065.inference_adequacy",
        terms=(
            HttEvidenceTraceTerm(
                channel="cmb",
                delta_lnB=1.0,
                source_ref="htt.term.cmb",
            ),
        ),
        input_hashes=(_sha("i"),),
        config_hash=_sha("c"),
        prior_sweep_status="prior_sweep_ready",
        posterior_predictive_status="posterior_predictive_ready",
        loocv_status="loocv_ready",
        matched_null_status="matched_null_ready",
    )

    with pytest.raises(ValueError, match="single"):
        build_evidence_anatomy_narrative_report(
            evidence_trace=trace,
            requested_single_score=True,
            artifact_id="mio.pr103.bad",
            artifact_path="memory://mio/pr103/bad.json",
            config_hash=_sha("p"),
            input_hashes=(_sha("i"),),
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )
    with pytest.raises(ValueError, match="MIO"):
        HttEvidenceTraceTerm(
            channel="mio_diagnostic",
            delta_lnB=1.0,
            source_ref="mio.certificate",
            source_owner="MIO",
        )
