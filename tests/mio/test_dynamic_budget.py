from __future__ import annotations

import pytest


def test_dynamic_budget_barrier_certifies_synthetic_comparison_only() -> None:
    from mio.formalism.dynamic_budget import dynamic_comparison_budget_barrier

    result = dynamic_comparison_budget_barrier(
        initial_budget=0.2,
        forcing_envelope=0.1,
        damping_integral=1.5,
        comparison_budget=0.6,
        collision_gap=0.4,
        theorem_id="S3",
    )
    payload = result.as_payload()

    assert payload["owner"] == "MIO"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["theorem_id"] == "S3"
    assert payload["barrier_status"] == "synthetic_barrier_certified"
    assert payload["barrier_margin"] > 0.0
    assert payload["production_claim_allowed"] is False
    assert payload["native_solver_result"] is False
    assert payload["family_identification"] is False
    assert "not HTT evidence" in payload["caveats"]


def test_dynamic_budget_blocks_nonpositive_collision_gap() -> None:
    from mio.formalism.dynamic_budget import dynamic_comparison_budget_barrier

    result = dynamic_comparison_budget_barrier(
        initial_budget=0.2,
        forcing_envelope=0.1,
        damping_integral=1.0,
        comparison_budget=0.4,
        collision_gap=0.0,
        theorem_id="S3",
    )

    payload = result.as_payload()
    assert payload["barrier_status"] == "blocked_collision_gap_nonpositive"
    assert "collision_gap_nonpositive_blocks_exponential_forgetting_language" in payload["kill_switches"]
    assert payload["barrier_margin"] is None


def test_dynamic_budget_blocks_channel_or_operator_mismatch() -> None:
    from mio.formalism.dynamic_budget import dynamic_comparison_budget_barrier

    payload = dynamic_comparison_budget_barrier(
        initial_budget=0.1,
        forcing_envelope=0.1,
        damping_integral=1.0,
        comparison_budget=0.5,
        collision_gap=0.2,
        theorem_id="S3",
        numerator_channel="TT",
        budget_channel="EE",
        numerator_operator="x_C",
        budget_operator="x_C",
    ).as_payload()
    assert payload["barrier_status"] == "blocked_channel_or_operator_mismatch"
    assert "channel_operator_mismatch_blocks_dynamic_budget_certification" in payload["kill_switches"]

    payload = dynamic_comparison_budget_barrier(
        initial_budget=0.1,
        forcing_envelope=0.1,
        damping_integral=1.0,
        comparison_budget=0.5,
        collision_gap=0.2,
        theorem_id="S3",
        numerator_channel="TT",
        budget_channel="TT",
        numerator_operator="x_C",
        budget_operator="Q",
    ).as_payload()
    assert payload["barrier_status"] == "blocked_channel_or_operator_mismatch"


def test_bound_to_pi_domination_requires_samplewise_bound() -> None:
    from mio.formalism.bound_pushforward import bound_to_pi_domination

    result = bound_to_pi_domination(
        sample_values=(0.1, 0.2, 0.4),
        bound_values=(0.2, 0.3, 0.5),
        thresholds=(0.0, 0.25, 0.45),
        theorem_id="S4",
    )
    payload = result.as_payload()

    assert payload["domination_status"] == "samplewise_bound_dominates_pi"
    assert payload["sample_pi_curve"][1] <= payload["bound_pi_curve"][1]
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["production_claim_allowed"] is False

    with pytest.raises(ValueError, match="samplewise"):
        bound_to_pi_domination(
            sample_values=(0.1, 0.6),
            bound_values=(0.2, 0.5),
            thresholds=(0.25,),
            theorem_id="S4",
        )


def test_finite_cover_union_bound_is_diagnostic_and_fail_closed() -> None:
    from mio.formalism.bound_pushforward import finite_cover_union_bound

    result = finite_cover_union_bound((0.05, 0.1, 0.2), theorem_id="S5")
    payload = result.as_payload()
    assert payload["cover_status"] == "descriptive_cover_only"
    assert payload["union_bound"] == pytest.approx(0.35)
    assert payload["physical_cover_use_allowed"] is False
    assert payload["physical_metric_status"] == "not_bound"
    assert payload["production_claim_allowed"] is False

    with pytest.raises(ValueError, match="unit interval"):
        finite_cover_union_bound((0.2, 1.2), theorem_id="S5")


def test_finite_cover_requires_metric_mask_and_lipschitz_provenance_for_physical_cover() -> None:
    from mio.formalism.bound_pushforward import finite_cover_union_bound

    ready = finite_cover_union_bound(
        (0.05, 0.1),
        theorem_id="S5",
        physical_metric_status="bound",
        mask_selection_status="bound",
        lipschitz_provenance="bound",
    ).as_payload()
    assert ready["cover_status"] == "finite_cover_union_bound"
    assert ready["physical_cover_use_allowed"] is True

    payload = finite_cover_union_bound(
        (0.05, 0.1),
        theorem_id="S5",
        physical_metric_status="not_bound",
        mask_selection_status="not_bound",
        lipschitz_provenance="not_bound",
    ).as_payload()
    assert payload["cover_status"] == "descriptive_cover_only"
    assert payload["physical_cover_use_allowed"] is False


def test_formalism_package_exports_dynamic_budget_and_bound_pushforward() -> None:
    import mio.formalism as formalism
    from mio.formalism.bound_pushforward import bound_to_pi_domination
    from mio.formalism.dynamic_budget import dynamic_comparison_budget_barrier

    assert formalism.dynamic_comparison_budget_barrier is dynamic_comparison_budget_barrier
    assert formalism.bound_to_pi_domination is bound_to_pi_domination
