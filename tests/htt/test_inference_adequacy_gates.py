from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from common.artifact_manifest import validate_manifest_payload
from htt.infer.null_competition import NullCompetitionHook


_COMMAND = "python -m pytest tests/htt/test_inference_adequacy_gates.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


_LINEAGE_HASH = _sha("0")


def _matched_null_report(**overrides):
    from htt.infer.matched_complexity import MatchedComplexityHook
    from htt.infer.null_competition import (
        FamilyCompetitionResult,
        NullCompetitionResult,
        build_matched_null_competition_report,
    )

    families = {
        "selection_response": FamilyCompetitionResult(
            family_name="selection_response",
            n_realizations=100,
            n_false_positives=2,
            fpr=0.02,
            mean_lnB_null=0.1,
            std_lnB_null=0.03,
            robust=True,
        ),
        "survey_axis": FamilyCompetitionResult(
            family_name="survey_axis",
            n_realizations=100,
            n_false_positives=3,
            fpr=0.03,
            mean_lnB_null=0.12,
            std_lnB_null=0.04,
            robust=True,
        ),
    }
    values = {
        "null_result": NullCompetitionResult(
            families_tested=2,
            families_robust=2,
            families_vulnerable=0,
            worst_family="survey_axis",
            worst_fpr=0.03,
            overall_robust=True,
            family_results=families,
        ),
        "matched_complexity_hook": MatchedComplexityHook(
            controls_required=("C1", "C2", "C3"),
            overall_pass=True,
            violations=(),
        ),
        "alternative_complexity_score": 6,
        "null_flexibility_scores": {
            "selection_response": 6,
            "survey_axis": 6,
        },
        "artifact_id": "htt.pr064.matched_null_competition",
        "config_hash": _LINEAGE_HASH,
        "input_hashes": (_LINEAGE_HASH, _sha("2")),
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
    }
    values.update(overrides)
    return build_matched_null_competition_report(**values)


def _matched_null_hook(report=None) -> NullCompetitionHook:
    from htt.infer.null_competition import build_null_competition_hook

    report = _matched_null_report() if report is None else report
    return build_null_competition_hook(
        matched_null_report=report,
        required_families=list(report.null_result.family_results),
        fpr_threshold=report.fpr_threshold,
    )


def _prior_report(**overrides):
    from htt.infer.prior_sweep import build_prior_sweep_report

    values = {
        "model": "FLRW_tilt",
        "baseline_log_evidence": 10.0,
        "sweep_log_evidences": {"narrow": 9.9, "wide": 10.2},
        "sensitivity_threshold": 0.5,
        "artifact_id": "htt.pr065.prior_sweep",
        "config_hash": _LINEAGE_HASH,
        "input_hashes": (_LINEAGE_HASH, _sha("b")),
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
        "config_hash": _LINEAGE_HASH,
        "input_hashes": (_LINEAGE_HASH, _sha("d")),
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
        "config_hash": _LINEAGE_HASH,
        "input_hashes": (_LINEAGE_HASH, _sha("f")),
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
    assert (
        validate_manifest_payload(
            payload,
            manifest_path="memory://pr065-prior-sweep.json",
        )
        == ()
    )


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
    assert (
        "posterior_predictive_pvalue_below_threshold"
        in failed_payload["blocked_reasons"]
    )


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


def test_adequacy_numeric_inputs_reject_boolean_pseudo_evidence():
    import numpy as np

    with pytest.raises(ValueError, match="numeric, not boolean"):
        _prior_report(baseline_log_evidence=True)
    with pytest.raises(ValueError, match="numeric, not boolean"):
        _ppc_report(observed={"beta_CF4": np.bool_(True), "beta_CMB": 1.2})
    with pytest.raises(ValueError, match="numeric, not boolean"):
        _loocv_report(full_log_evidence=False)


def test_decisive_language_rejected_without_all_adequacy_statuses():
    from htt.infer.prior_sweep import build_inference_adequacy_report

    with pytest.raises(ValueError, match="prior-sweep, PPC, LOOCV, and matched-null"):
        build_inference_adequacy_report(
            prior_sweep_report=_prior_report(),
            posterior_predictive_report=None,
            loocv_report=_loocv_report(),
            matched_null_hook=_matched_null_hook(),
            matched_null_report=_matched_null_report(),
            decisive_claim_requested=True,
            artifact_id="htt.pr065.inference_adequacy",
            config_hash=_LINEAGE_HASH,
            input_hashes=(_LINEAGE_HASH, _sha("7")),
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )


def test_inference_adequacy_report_carries_all_gate_statuses():
    from htt.infer.prior_sweep import build_inference_adequacy_report

    matched_null_report = _matched_null_report()
    report = build_inference_adequacy_report(
        prior_sweep_report=_prior_report(),
        posterior_predictive_report=_ppc_report(),
        loocv_report=_loocv_report(),
        matched_null_hook=_matched_null_hook(matched_null_report),
        matched_null_report=matched_null_report,
        decisive_claim_requested=True,
        artifact_id="htt.pr065.inference_adequacy",
        config_hash=_LINEAGE_HASH,
        input_hashes=(_LINEAGE_HASH, _sha("7")),
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
    assert (
        validate_manifest_payload(
            payload,
            manifest_path="memory://pr065-inference-adequacy.json",
        )
        == ()
    )
    text = json.dumps(payload, sort_keys=True).lower()
    assert ("native " + "solver result") not in text
    assert "mio certificate" not in text
    assert "family identified" not in text
    assert "geometry detected" not in text


def test_inference_adequacy_report_blocks_failed_gate_without_hiding_status():
    from htt.infer.prior_sweep import build_inference_adequacy_report

    matched_null_report = _matched_null_report()
    report = build_inference_adequacy_report(
        prior_sweep_report=_prior_report(sweep_log_evidences={"too_wide": 7.5}),
        posterior_predictive_report=_ppc_report(),
        loocv_report=_loocv_report(),
        matched_null_hook=_matched_null_hook(matched_null_report),
        matched_null_report=matched_null_report,
        artifact_id="htt.pr065.inference_adequacy",
        config_hash=_LINEAGE_HASH,
        input_hashes=(_LINEAGE_HASH, _sha("7")),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = report.as_payload()

    assert payload["claim_tier"] == "blocked"
    assert payload["inference_adequacy_status"] == "blocked_inference_adequacy"
    assert payload["prior_sweep_status"] == "blocked_prior_sensitivity"
    assert "prior_sweep_failed" in payload["blocked_reasons"]


def _build_adequacy(**overrides):
    from htt.infer.prior_sweep import build_inference_adequacy_report

    matched_null_report = _matched_null_report()
    values = {
        "prior_sweep_report": _prior_report(),
        "posterior_predictive_report": _ppc_report(),
        "loocv_report": _loocv_report(),
        "matched_null_hook": _matched_null_hook(matched_null_report),
        "matched_null_report": matched_null_report,
        "artifact_id": "htt.pr122.inference_adequacy",
        "config_hash": _LINEAGE_HASH,
        "input_hashes": (_LINEAGE_HASH, _sha("7")),
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
    }
    values.update(overrides)
    return build_inference_adequacy_report(**values)


def test_inference_adequacy_rejects_duck_typed_ready_receipts():
    fake_ppc = SimpleNamespace(
        ready_for_claims=True,
        report_hash=_sha("9"),
        posterior_predictive_status="posterior_predictive_ready",
    )

    with pytest.raises(TypeError, match="exact PriorSweepReport"):
        _build_adequacy(posterior_predictive_report=fake_ppc)


@pytest.mark.parametrize(
    ("field_name", "pseudo_evidence"),
    (
        ("posterior_predictive_report", 0.42),
        ("loocv_report", 29.7),
    ),
)
def test_inference_adequacy_rejects_caller_scalar_pseudo_evidence(
    field_name,
    pseudo_evidence,
):
    with pytest.raises(TypeError, match="exact PriorSweepReport"):
        _build_adequacy(**{field_name: pseudo_evidence})


def test_inference_adequacy_recomputes_typed_report_hashes():
    tampered = replace(_ppc_report(), pvalue=0.99)

    with pytest.raises(ValueError, match="cannot be reproduced from canonical"):
        _build_adequacy(posterior_predictive_report=tampered)


def test_inference_adequacy_rejects_cross_model_lineage():
    with pytest.raises(ValueError, match="model lineage must match"):
        _build_adequacy(loocv_report=_loocv_report(model="different_model"))


def test_inference_adequacy_rejects_mismatched_config_input_lineage():
    other_lineage = _sha("8")
    unrelated_ppc = _ppc_report(
        config_hash=other_lineage,
        input_hashes=(other_lineage, _sha("d")),
    )

    with pytest.raises(ValueError, match="common recomputed config/input lineage"):
        _build_adequacy(posterior_predictive_report=unrelated_ppc)


def test_inference_adequacy_rejects_mismatched_code_provenance():
    with pytest.raises(ValueError, match="code provenance must match"):
        _build_adequacy(
            posterior_predictive_report=_ppc_report(worktree_state="other-worktree")
        )


def test_inference_adequacy_rejects_duck_typed_matched_null_hook():
    fake_hook = SimpleNamespace(
        ready_for_inference=True,
        matched_null_report_hash=_sha("f"),
        matched_null_status="matched_null_ready",
    )

    with pytest.raises(TypeError, match="exact NullCompetitionHook"):
        _build_adequacy(
            matched_null_hook=fake_hook,
            decisive_claim_requested=True,
        )


def test_inference_adequacy_rejects_contradictory_exact_matched_null_hook():
    contradictory = NullCompetitionHook(
        required_families=("a",),
        fpr_threshold=0.10,
        ready_for_inference=True,
        worst_family="not-a",
        worst_fpr=0.99,
        matched_complexity_ready=True,
        matched_null_report_hash="not-a-hash",
        matched_null_status="whatever",
        blocked_reasons=("has_blocker",),
    )

    with pytest.raises(ValueError, match="worst_family must belong"):
        _build_adequacy(
            matched_null_hook=contradictory,
            decisive_claim_requested=True,
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"required_families": ("survey_axis", "survey_axis")}, "must be unique"),
        ({"fpr_threshold": 0.01}, "cannot exceed fpr_threshold"),
        ({"matched_null_report_hash": "not-a-hash"}, "lowercase sha256"),
        ({"matched_null_status": "arbitrary_ready"}, "status must be"),
        ({"blocked_reasons": ("hidden_failure",)}, "cannot retain blocked_reasons"),
    ),
)
def test_inference_adequacy_revalidates_each_ready_matched_null_field(
    overrides,
    message,
):
    forged = _matched_null_hook()
    for field_name, value in overrides.items():
        # Frozen dataclasses prevent accidental mutation, not hostile object
        # construction.  The consuming gate must independently revalidate.
        object.__setattr__(forged, field_name, value)

    with pytest.raises(ValueError, match=message):
        _build_adequacy(matched_null_hook=forged)


def test_inference_adequacy_hash_binds_all_matched_null_decision_fields():
    baseline_report = _matched_null_report()
    baseline = _build_adequacy(
        matched_null_hook=_matched_null_hook(baseline_report),
        matched_null_report=baseline_report,
    )
    changed_report = _matched_null_report(fpr_threshold=0.20)
    changed_threshold = _build_adequacy(
        matched_null_hook=_matched_null_hook(changed_report),
        matched_null_report=changed_report,
    )

    assert baseline.report_hash != changed_threshold.report_hash
    payload = baseline.as_payload()
    assert payload["matched_null_hook"] == {
        "required_families": ["selection_response", "survey_axis"],
        "fpr_threshold": 0.10,
        "ready_for_inference": True,
        "worst_family": "survey_axis",
        "worst_fpr": 0.03,
        "scope": "pre_posterior",
        "matched_complexity_ready": True,
        "matched_null_report_hash": baseline_report.report_hash,
        "matched_null_status": "matched_null_ready",
        "blocked_reasons": [],
    }


def test_inference_adequacy_preserves_canonical_matched_null_blockers():
    blocked_report = _matched_null_report(
        null_flexibility_scores={
            "selection_response": 7,
            "survey_axis": 6,
        }
    )
    blocked_hook = _matched_null_hook(blocked_report)

    report = _build_adequacy(
        matched_null_hook=blocked_hook,
        matched_null_report=blocked_report,
    )
    payload = report.as_payload()

    assert report.ready_for_claims is False
    assert payload["matched_null_status"] == "blocked_matched_null_prerequisites"
    assert payload["matched_null_blocked_reasons"] == [
        "matched_complexity_gap:selection_response"
    ]
    assert (
        "matched_null:matched_complexity_gap:selection_response"
        in payload["blocked_reasons"]
    )


def test_ready_matched_null_hook_without_exact_report_is_rejected():
    with pytest.raises(
        ValueError, match="requires an exact MatchedNullCompetitionReport"
    ):
        _build_adequacy(
            matched_null_hook=_matched_null_hook(),
            matched_null_report=None,
        )


def test_tampered_matched_null_report_hash_cannot_authorize_readiness():
    tampered = _matched_null_report()
    object.__setattr__(tampered, "report_hash", _sha("1"))
    forged_hook = NullCompetitionHook(
        required_families=("selection_response", "survey_axis"),
        fpr_threshold=0.10,
        ready_for_inference=True,
        worst_family="survey_axis",
        worst_fpr=0.03,
        matched_complexity_ready=True,
        matched_null_report_hash=_sha("1"),
        matched_null_status="matched_null_ready",
    )

    with pytest.raises(
        ValueError,
        match="report_hash must occur exactly once|cannot be reproduced from canonical",
    ):
        _build_adequacy(
            matched_null_hook=forged_hook,
            matched_null_report=tampered,
            decisive_claim_requested=True,
        )


def test_matched_null_builder_rejects_fpr_threshold_robustness_spoof():
    from htt.infer.null_competition import (
        FamilyCompetitionResult,
        NullCompetitionResult,
    )

    spoofed_family = FamilyCompetitionResult(
        family_name="selection_response",
        n_realizations=100,
        n_false_positives=50,
        fpr=0.50,
        mean_lnB_null=0.1,
        std_lnB_null=0.03,
        robust=True,
    )
    spoofed_result = NullCompetitionResult(
        families_tested=1,
        families_robust=1,
        families_vulnerable=0,
        worst_family="selection_response",
        worst_fpr=0.50,
        overall_robust=True,
        family_results={"selection_response": spoofed_family},
    )

    with pytest.raises(ValueError, match="strict fpr < fpr_threshold"):
        _matched_null_report(
            null_result=spoofed_result,
            null_flexibility_scores={"selection_response": 6},
        )
