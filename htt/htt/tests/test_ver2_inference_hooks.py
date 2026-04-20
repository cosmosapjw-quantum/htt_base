from __future__ import annotations

from htt.infer.matched_complexity import MatchedComplexityReport, build_matched_complexity_hook
from htt.infer.null_competition import NullCompetitionResult, build_null_competition_hook


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
    result = NullCompetitionResult(
        families_tested=2,
        families_robust=2,
        families_vulnerable=0,
        worst_family="mask_leakage",
        worst_fpr=0.01,
        overall_robust=True,
        family_results={},
    )
    hook = build_null_competition_hook(result)
    assert hook.ready_for_inference is True
    assert hook.worst_family == "mask_leakage"
