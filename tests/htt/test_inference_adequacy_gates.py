from __future__ import annotations

import json

import pytest

from common.artifact_manifest import validate_manifest_payload
from htt.infer.null_competition import NullCompetitionHook


_COMMAND = "python -m pytest tests/htt/test_inference_adequacy_gates.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _matched_null_hook() -> NullCompetitionHook:
    return NullCompetitionHook(
        required_families=("selection_response", "survey_axis"),
        fpr_threshold=0.10,
        ready_for_inference=True,
        worst_family="survey_axis",
        worst_fpr=0.02,
        matched_complexity_ready=True,
        matched_null_report_hash=_sha("n"),
        matched_null_status="matched_null_ready",
    )


def _prior_report(**overrides):
    from htt.infer.prior_sweep import build_prior_sweep_report

    values = {
        "model": "FLRW_tilt",
        "baseline_log_evidence": 10.0,
        "sweep_log_evidences": {"narrow": 9.9, "wide": 10.2},
        "sensitivity_threshold": 0.5,
        "artifact_id": "htt.pr065.prior_sweep",
        "config_hash": _sha("a"),
        "input_hashes": (_sha("b"),),
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
    }
    values.update(overrides)
    return build_prior_sweep_report(**values)


def _ppc_report(**overrides):
    from htt.infer.posterior_predictive import build_posterior_predictive_report

    values = {
        "model": "FLRW_tilt",
        "observed": {"beta_CF4": 1.0, "beta_CMB": 1.2},
        "predicted": {"beta_CF4": 1.05, "beta_CMB": 1.1},
        "sigma": {"beta_CF4": 0.2, "beta_CMB": 0.25},
        "pvalue": 0.42,
        "min_pvalue": 0.05,
        "max_abs_pull": 3.0,
        "artifact_id": "htt.pr065.ppc",
        "config_hash": _sha("c"),
        "input_hashes": (_sha("d"),),
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
    }
    values.update(overrides)
    return build_posterior_predictive_report(**values)


def _loocv_report(**overrides):
    from htt.infer.loocv import build_loocv_report

    values = {
        "model": "FLRW_tilt",
        "full_log_evidence": 10.0,
        "fold_log_evidences": {"drop_CF4": 9.8, "drop_CMB": 9.9},
        "max_delta_threshold": 0.5,
        "min_folds": 2,
        "artifact_id": "htt.pr065.loocv",
        "config_hash": _sha("e"),
        "input_hashes": (_sha("f"),),
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
    }
    values.update(overrides)
    return build_loocv_report(**values)


def test_prior_sweep_report_records_stability_and_manifest():
    report = _prior_report()
    payload = report.as_payload()

    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "htt"
    assert payload["claim_tier"] == "conditional"
    assert payload["production_status"] == "diagnostic_only"
    assert payload["prior_sweep_status"] == "prior_sweep_ready"
    assert payload["max_abs_delta_log_evidence"] == pytest.approx(0.2)
    assert payload["sweep_points"]["wide"]["delta_log_evidence"] == pytest.approx(0.2)
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://pr065-prior-sweep.json",
    ) == ()


def test_failed_prior_sweep_downgrades_claim_tier():
    report = _prior_report(sweep_log_evidences={"too_wide": 7.5})
    payload = report.as_payload()

    assert payload["claim_tier"] == "blocked"
    assert payload["prior_sweep_status"] == "blocked_prior_sensitivity"
    assert "prior_sensitivity_exceeds_threshold" in payload["blocked_reasons"]


def test_posterior_predictive_report_requires_pvalue_and_pull_status():
    report = _ppc_report()
    failed = _ppc_report(pvalue=0.01)

    payload = report.as_payload()
    failed_payload = failed.as_payload()

    assert payload["posterior_predictive_status"] == "posterior_predictive_ready"
    assert payload["ndof"] == 2
    assert payload["max_abs_pull_observed"] == pytest.approx(0.4)
    assert failed_payload["claim_tier"] == "blocked"
    assert "posterior_predictive_pvalue_below_threshold" in failed_payload[
        "blocked_reasons"
    ]


def test_loocv_report_records_most_sensitive_fold_and_blocks_large_delta():
    report = _loocv_report()
    failed = _loocv_report(fold_log_evidences={"drop_CF4": 7.0, "drop_CMB": 9.9})

    payload = report.as_payload()
    failed_payload = failed.as_payload()

    assert payload["loocv_status"] == "loocv_ready"
    assert payload["most_sensitive_fold"]["fold_id"] == "drop_CF4"
    assert payload["max_abs_delta_log_evidence"] == pytest.approx(0.2)
    assert failed_payload["loocv_status"] == "blocked_loocv_instability"
    assert "loocv_delta_exceeds_threshold" in failed_payload["blocked_reasons"]


def test_loocv_min_folds_rejects_non_integral_counts():
    with pytest.raises(ValueError, match="positive integer"):
        _loocv_report(min_folds=1.5)


def test_decisive_language_rejected_without_all_adequacy_statuses():
    from htt.infer.prior_sweep import build_inference_adequacy_report

    with pytest.raises(ValueError, match="prior-sweep, PPC, LOOCV, and matched-null"):
        build_inference_adequacy_report(
            prior_sweep_report=_prior_report(),
            posterior_predictive_report=None,
            loocv_report=_loocv_report(),
            matched_null_hook=_matched_null_hook(),
            decisive_claim_requested=True,
            artifact_id="htt.pr065.inference_adequacy",
            config_hash=_sha("g"),
            input_hashes=(_sha("h"),),
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )


def test_inference_adequacy_report_carries_all_gate_statuses():
    from htt.infer.prior_sweep import build_inference_adequacy_report

    report = build_inference_adequacy_report(
        prior_sweep_report=_prior_report(),
        posterior_predictive_report=_ppc_report(),
        loocv_report=_loocv_report(),
        matched_null_hook=_matched_null_hook(),
        decisive_claim_requested=True,
        artifact_id="htt.pr065.inference_adequacy",
        config_hash=_sha("g"),
        input_hashes=(_sha("h"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = report.as_payload()

    assert payload["claim_tier"] == "conditional"
    assert payload["production_status"] == "diagnostic_only"
    assert payload["inference_adequacy_status"] == "inference_adequacy_ready"
    assert payload["decisive_evidence_language_status"] == "conditional_pre_solver"
    assert payload["prior_sweep_status"] == "prior_sweep_ready"
    assert payload["posterior_predictive_status"] == "posterior_predictive_ready"
    assert payload["loocv_status"] == "loocv_ready"
    assert payload["matched_null_status"] == "matched_null_ready"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://pr065-inference-adequacy.json",
    ) == ()
    text = json.dumps(payload, sort_keys=True).lower()
    assert ("native " + "solver result") not in text
    assert "mio certificate" not in text
    assert "family identified" not in text
    assert "geometry detected" not in text


def test_inference_adequacy_report_blocks_failed_gate_without_hiding_status():
    from htt.infer.prior_sweep import build_inference_adequacy_report

    report = build_inference_adequacy_report(
        prior_sweep_report=_prior_report(sweep_log_evidences={"too_wide": 7.5}),
        posterior_predictive_report=_ppc_report(),
        loocv_report=_loocv_report(),
        matched_null_hook=_matched_null_hook(),
        artifact_id="htt.pr065.inference_adequacy",
        config_hash=_sha("g"),
        input_hashes=(_sha("h"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = report.as_payload()

    assert payload["claim_tier"] == "blocked"
    assert payload["inference_adequacy_status"] == "blocked_inference_adequacy"
    assert payload["prior_sweep_status"] == "blocked_prior_sensitivity"
    assert "prior_sweep_failed" in payload["blocked_reasons"]
