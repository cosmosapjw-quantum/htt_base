from __future__ import annotations

import json

import pytest

from common.artifact_manifest import validate_manifest_payload


_COMMAND = "python -m pytest tests/htt/test_matched_nulls.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _family(name: str, *, fpr: float = 0.02, robust: bool = True):
    from htt.infer.null_competition import FamilyCompetitionResult

    n_realizations = 128
    n_false_positives = int(round(n_realizations * fpr))
    return FamilyCompetitionResult(
        family_name=name,
        n_realizations=n_realizations,
        n_false_positives=n_false_positives,
        fpr=n_false_positives / n_realizations,
        mean_lnB_null=0.12,
        std_lnB_null=0.03,
        robust=robust,
        status="diagnostic_only",
    )


def _null_result(*, robust: bool = True):
    from htt.infer.null_competition import NullCompetitionResult

    families = {
        "selection_response": _family("selection_response", fpr=0.02, robust=True),
        "survey_axis": _family("survey_axis", fpr=0.03, robust=True),
    }
    if not robust:
        families["survey_axis"] = _family("survey_axis", fpr=0.35, robust=False)
    worst = max(families.values(), key=lambda item: item.fpr)
    n_robust = sum(1 for item in families.values() if item.robust)
    return NullCompetitionResult(
        families_tested=len(families),
        families_robust=n_robust,
        families_vulnerable=len(families) - n_robust,
        worst_family=worst.family_name,
        worst_fpr=worst.fpr,
        overall_robust=robust,
        family_results=families,
        status="diagnostic_only",
    )


def _matched_hook(*, overall_pass: bool = True):
    from htt.infer.matched_complexity import MatchedComplexityHook

    return MatchedComplexityHook(
        controls_required=("C1", "C2", "C3"),
        overall_pass=overall_pass,
        violations=tuple() if overall_pass else ("prior_width_mismatch",),
    )


def _report_kwargs(**overrides):
    values = {
        "null_result": _null_result(),
        "matched_complexity_hook": _matched_hook(),
        "alternative_complexity_score": 6,
        "null_flexibility_scores": {
            "selection_response": 6,
            "survey_axis": 6,
        },
        "artifact_id": "htt.pr064.matched_null_competition",
        "config_hash": _sha("a"),
        "input_hashes": (_sha("b"),),
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
    }
    values.update(overrides)
    return values


def test_matched_null_report_blocks_without_matched_complexity():
    from htt.infer.null_competition import build_matched_null_competition_report

    report = build_matched_null_competition_report(
        **_report_kwargs(matched_complexity_hook=None)
    )
    payload = report.as_payload()

    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "htt"
    assert payload["claim_tier"] == "blocked"
    assert payload["production_status"] == "blocked_provenance_mismatch"
    assert payload["matched_null_status"] == "blocked_missing_matched_complexity"
    assert payload["evidence_claim_prerequisite_met"] is False
    assert payload["headline_bayes_factor_allowed"] is False
    assert "matched_complexity_report_missing" in payload["blocked_reasons"]


def test_matched_null_report_records_null_and_alternative_flexibility():
    from htt.infer.null_competition import build_matched_null_competition_report

    report = build_matched_null_competition_report(
        **_report_kwargs(candidate_log_bayes_factor=3.2, headline_requested=True)
    )
    payload = report.as_payload()

    assert payload["claim_tier"] == "conditional"
    assert payload["production_status"] == "diagnostic_only"
    assert payload["matched_null_status"] == "matched_null_ready"
    assert payload["evidence_claim_prerequisite_met"] is True
    assert payload["matched_null_headline_gate_passed"] is True
    assert payload["headline_bayes_factor_allowed"] is False
    assert payload["candidate_log_bayes_factor"] == 3.2
    assert payload["decisive_evidence_status"] == "blocked_until_pr065_prior_ppc_loocv"
    assert payload["alternative_flexibility"]["complexity_score"] == 6
    assert payload["family_results"]["selection_response"]["null_flexibility"][
        "complexity_score"
    ] == 6
    assert payload["family_results"]["survey_axis"]["matched_complexity_gap"] == 0
    assert "matched_complexity_ready" in payload["manifest"]["passed_gates"]
    assert "structured_nulls_robust" in payload["manifest"]["passed_gates"]


def test_headline_request_without_matched_complexity_is_rejected():
    from htt.infer.null_competition import build_matched_null_competition_report

    with pytest.raises(ValueError, match="matched-complexity report"):
        build_matched_null_competition_report(
            **_report_kwargs(
                matched_complexity_hook=None,
                candidate_log_bayes_factor=5.5,
                headline_requested=True,
            )
        )


def test_null_competition_hook_requires_matched_complexity_for_readiness():
    from htt.infer.null_competition import build_null_competition_hook

    result = _null_result()
    pending = build_null_competition_hook(result)
    ready = build_null_competition_hook(
        result,
        matched_complexity_hook=_matched_hook(),
        matched_null_report_hash=_sha("r"),
    )
    failed_matched = build_null_competition_hook(
        result,
        matched_complexity_hook=_matched_hook(overall_pass=False),
    )

    assert pending.ready_for_inference is False
    assert "matched_complexity_report_missing" in pending.blocked_reasons
    assert ready.ready_for_inference is True
    assert ready.matched_complexity_ready is True
    assert ready.worst_family == "survey_axis"
    assert failed_matched.ready_for_inference is False
    assert "matched_complexity_failed" in failed_matched.blocked_reasons


def test_null_result_and_hook_reject_overstrong_or_inconsistent_readiness():
    from htt.infer.null_competition import (
        FamilyCompetitionResult,
        NullCompetitionHook,
        NullCompetitionResult,
    )

    with pytest.raises(ValueError, match="diagnostic_only"):
        FamilyCompetitionResult(
            family_name="selection_response",
            n_realizations=100,
            n_false_positives=1,
            fpr=0.01,
            mean_lnB_null=0.1,
            std_lnB_null=0.02,
            robust=True,
            status="INFERENTIAL",
        )

    family = _family("selection_response", fpr=0.02, robust=True)
    with pytest.raises(ValueError, match="worst_fpr"):
        NullCompetitionResult(
            families_tested=1,
            families_robust=1,
            families_vulnerable=0,
            worst_family="selection_response",
            worst_fpr=0.75,
            overall_robust=True,
            family_results={"selection_response": family},
        )

    hook = NullCompetitionHook(
        required_families=("selection_response",),
        fpr_threshold=0.10,
        ready_for_inference=False,
        worst_family="selection_response",
        worst_fpr=0.02,
        matched_null_status="matched_null_ready",
    )
    assert hook.ready_for_inference is False
    assert hook.matched_null_status == "blocked_matched_null_prerequisites"
    assert "matched_null_not_ready" in hook.blocked_reasons


def test_null_readiness_flags_require_exact_booleans():
    from htt.infer.null_competition import (
        FamilyCompetitionResult,
        NullCompetitionResult,
    )

    with pytest.raises(TypeError, match="robust must be bool"):
        _family("selection_response", fpr=0.02, robust="false")

    family = _family("selection_response", fpr=0.02, robust=True)
    with pytest.raises(TypeError, match="overall_robust must be bool"):
        NullCompetitionResult(
            families_tested=1,
            families_robust=1,
            families_vulnerable=0,
            worst_family="selection_response",
            worst_fpr=0.02,
            overall_robust="false",
            family_results={"selection_response": family},
        )


def test_matched_null_report_manifest_and_claim_hygiene():
    from htt.infer.null_competition import build_matched_null_competition_report

    report = build_matched_null_competition_report(**_report_kwargs())
    payload = report.as_payload()

    assert validate_manifest_payload(
        payload,
        manifest_path="memory://pr064-matched-null-competition.json",
    ) == ()
    text = json.dumps(payload, sort_keys=True).lower()
    assert ("posterior " + "odds") not in text
    assert ("native " + "solver result") not in text
    assert "mio certificate" not in text
    assert "family identified" not in text
    assert "geometry detected" not in text


def test_blocked_report_survives_missing_null_flexibility_payload():
    from htt.infer.null_competition import build_matched_null_competition_report

    report = build_matched_null_competition_report(
        **_report_kwargs(null_flexibility_scores={"selection_response": 6})
    )
    payload = report.as_payload()

    assert report.evidence_claim_prerequisite_met is False
    assert "null_flexibility_scores_missing:survey_axis" in payload["blocked_reasons"]
    assert payload["family_results"]["survey_axis"]["null_flexibility"][
        "complexity_score"
    ] is None
    assert payload["family_results"]["survey_axis"]["matched_complexity_gap"] is None


def test_gf_matched_null_forecast_blocks_failed_fpr_without_retuning():
    from htt.infer.null_competition import build_gf_matched_null_forecast_report

    report = build_gf_matched_null_forecast_report(
        null_result=_null_result(robust=False),
        matched_complexity_hook=_matched_hook(),
        alternative_complexity_score=6,
        null_flexibility_scores={
            "selection_response": 6,
            "survey_axis": 6,
        },
        artifact_id="htt.rev069.gf_matched_null_forecast",
        config_hash=_sha("f"),
        input_hashes=(_sha("g"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
        threshold_config_hash=_sha("t"),
        threshold_selection_rationale="pre-registered REV-R069 forecast threshold",
    )
    payload = report.as_payload()

    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "htt"
    assert payload["claim_tier"] == "blocked"
    assert payload["artifact_mode"] == "forecast_only"
    assert payload["forecast_only"] is True
    assert payload["observed_data_evidence"] is False
    assert payload["matched_null_status"] == "forecast_matched_null_blocked"
    assert payload["local_global_separation_status"] == (
        "blocked_existing_null_bank_insufficient"
    )
    assert payload["authorization_scope"] == "design_sensitivity_only"
    assert payload["global_tilt_wording_allowed"] is False
    assert payload["threshold_pre_registered"] is True
    assert payload["threshold_config_hash"] == _sha("t")
    assert payload["retuning_after_failure"] is False
    assert "structured_nulls_not_robust" in payload["blocked_reasons"]
    assert "forecast_matched_null_fpr_threshold_not_met" in payload["blocked_reasons"]
    assert payload["false_positive_rate_statement"]["kind"] == (
        "count_with_wilson_upper_bound"
    )
    assert "FPR=0" not in json.dumps(payload, sort_keys=True)
    assert "global tilt detected" not in json.dumps(payload, sort_keys=True).lower()


def test_gf_matched_null_forecast_pass_still_blocks_observed_claims():
    from htt.infer.null_competition import build_gf_matched_null_forecast_report

    report = build_gf_matched_null_forecast_report(
        null_result=_null_result(robust=True),
        matched_complexity_hook=_matched_hook(),
        alternative_complexity_score=6,
        null_flexibility_scores={
            "selection_response": 6,
            "survey_axis": 6,
        },
        artifact_id="htt.rev069.gf_matched_null_forecast",
        config_hash=_sha("f"),
        input_hashes=(_sha("g"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
        threshold_config_hash=_sha("t"),
        threshold_selection_rationale="pre-registered REV-R069 forecast threshold",
    )
    payload = report.as_payload()

    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["matched_null_status"] == "forecast_matched_null_passed"
    assert payload["observed_data_evidence"] is False
    assert payload["global_tilt_wording_allowed"] is False
    assert payload["decisive_evidence_status"] == (
        "blocked_forecast_only_not_observed_evidence"
    )


def test_gf_matched_null_forecast_labels_fixture_source_and_dirty_worktree():
    from htt.infer.null_competition import build_gf_matched_null_forecast_report

    report = build_gf_matched_null_forecast_report(
        null_result=_null_result(robust=False),
        matched_complexity_hook=_matched_hook(),
        alternative_complexity_score=6,
        null_flexibility_scores={
            "selection_response": 6,
            "survey_axis": 6,
        },
        artifact_id="htt.rev069.gf_matched_null_forecast",
        config_hash=_sha("f"),
        input_hashes=(_sha("g"),),
        generating_command=_COMMAND,
        git_commit="abc1234",
        worktree_state="abc1234+dirty",
        threshold_config_hash=_sha("t"),
        threshold_selection_rationale="pre-registered REV-R069 forecast threshold",
    )
    payload = report.as_payload()

    assert payload["forecast_source_kind"] == "deterministic_current_code_fixture"
    assert payload["forecast_source_description"].startswith(
        "Deterministic current-code"
    )
    assert payload["false_positive_rate_statement"]["source_kind"] == (
        "deterministic_current_code_fixture"
    )
    assert payload["git_commit_or_worktree_state"] == "abc1234+dirty"
    assert payload["manifest"]["code_version"] == "abc1234+dirty"
    assert payload["matched_null_report"]["git_commit_or_worktree_state"] == (
        "abc1234+dirty"
    )
    assert payload["matched_null_report"]["manifest"]["code_version"] == (
        "abc1234+dirty"
    )
