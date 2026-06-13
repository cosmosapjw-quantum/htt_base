from __future__ import annotations

from htt.infer.matched_complexity import MatchedComplexityReport, build_matched_complexity_hook
from htt.infer.null_competition import (
    FamilyCompetitionResult,
    NullCompetitionResult,
    build_null_competition_hook,
)


_REPORT_HASH = "sha256:" + "r" * 64


def test_matched_complexity_hook_preserves_pre_inference_scope():
    report = MatchedComplexityReport(
        controls_checked=("C1", "C2", "C3"),
        amplitude_matched=True,
        nuisance_matched=True,
        prior_width_matched=True,
        overall_pass=True,
        violations=tuple(),
    )
    hook = build_matched_complexity_hook(report)
    assert hook.scope == "pre_inference_only"
    assert hook.overall_pass is True
    assert hook.controls_required == ("C1", "C2", "C3")


def test_null_competition_hook_can_remain_pending():
    hook = build_null_competition_hook()
    assert hook.ready_for_inference is False
    assert hook.scope == "pre_posterior"


def test_null_competition_hook_reflects_result_readiness():
    family_result = FamilyCompetitionResult(
        family_name="mask_leakage",
        n_realizations=100,
        n_false_positives=1,
        fpr=0.01,
        mean_lnB_null=0.2,
        std_lnB_null=0.1,
        robust=True,
    )
    result = NullCompetitionResult(
        families_tested=1,
        families_robust=1,
        families_vulnerable=0,
        worst_family="mask_leakage",
        worst_fpr=0.01,
        overall_robust=True,
        family_results={"mask_leakage": family_result},
    )
    hook = build_null_competition_hook(
        result,
        matched_complexity_hook=build_matched_complexity_hook(),
        matched_null_report_hash=_REPORT_HASH,
    )
    assert hook.ready_for_inference is True
    assert hook.worst_family == "mask_leakage"
