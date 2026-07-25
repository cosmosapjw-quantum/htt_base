from __future__ import annotations

import dataclasses
import json
import math

import pytest

from mio.formalism.budget_spec import BudgetPolicy, BudgetUse

_COMMAND = "pytest tests/bass/test_budget_ceiling_optimizer.py -q"
_WORKTREE = "test-worktree-pr083"


def _external_entry(transfer_id: str = "aniclass.lowell.shear_to_D2.v1"):
    from bass.atlas import AtlasEntryLite
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get(transfer_id)
    return AtlasEntryLite.from_transfer_spec(
        spec,
        comparison_group="pr083-test",
        config_hash="sha256:atlas-config",
        input_hashes=("sha256:atlas-input",),
        generating_command=_COMMAND,
        git_commit_or_worktree_state=_WORKTREE,
    )


def _prior(**overrides: object):
    from bass.atlas import CeilingPrior

    values: dict[str, object] = {
        "prior_id": "prior.lowell.explicit.log-grid",
        "prior_hash": "sha256:prior-explicit",
        "prior_support": {
            "Sigma2": {
                "min": 1.0e-24,
                "max": 1.0e-20,
                "units": "dimensionless",
            }
        },
        "prior_measure": "explicit_log_grid_measure",
        "prior_description": "explicit pre-solver transfer-domain prior",
    }
    values.update(overrides)
    return CeilingPrior(**values)


def _admissible(**overrides: object):
    from bass.atlas import AdmissibleSetMetadata

    values: dict[str, object] = {
        "admissible_set_id": "admissible.lowell.external-domain",
        "admissible_set_hash": "sha256:admissible-external",
        "admissible_set_status": "external_transfer_domain",
        "admissible_set_definition_ref": "docs/pr083/external-domain-fixture",
        "parameter_bounds": {
            "Sigma2": {
                "min": 1.0e-24,
                "max": 1.0e-20,
                "units": "dimensionless",
            }
        },
        "constraints": ("finite_positive_U_C",),
        "exclusions": ("schema_only_native_entries",),
    }
    values.update(overrides)
    return AdmissibleSetMetadata(**values)


def _mes_admissible():
    return _admissible(
        admissible_set_id="admissible.mes.legacy-linear",
        admissible_set_hash="sha256:admissible-mes",
        admissible_set_status="legacy_mes_admissible",
        admissible_set_definition_ref="docs/pr083/legacy-mes-fixture",
        parameter_bounds={
            "x_C": {"min": 0.0, "max": 1.0, "units": "dimensionless_xC"}
        },
        constraints=("legacy_MES_linear_positive_ceiling",),
        exclusions=("external_transfer_certified_F",),
    )


def _external_candidate(
    *,
    U_C: float = 2.5,
    candidate_id: str = "cand.external",
    units: str = "microkelvin_squared",
):
    from bass.atlas import BudgetCeilingCandidate

    return BudgetCeilingCandidate.from_atlas_entry(
        _external_entry(),
        candidate_id=candidate_id,
        U_C=U_C,
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units=units,
        candidate_metadata={"candidate_role": "external_transfer_ceiling"},
        rank_status="full_rank",
        response_rank=2,
        nuisance_projected_rank=2,
        condition_number=8.0,
    )


def _mes_candidate(
    *,
    U_C: float = 1.0,
    candidate_id: str = "cand.mes",
    rank_status: str = "rank_not_applicable_certified_mes",
):
    from bass.atlas import BudgetCeilingCandidate

    return BudgetCeilingCandidate(
        candidate_id=candidate_id,
        U_C=U_C,
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        valid_range={"x_C_min": 0.0, "x_C_max": 1.0, "range_role": "MES_linear"},
        transfer_source="none",
        candidate_metadata={"candidate_role": "legacy_MES_linear_ceiling"},
        rank_status=rank_status,
    )


def _result(*, candidate=None, admissible=None, prior=None, **overrides: object):
    from bass.atlas import optimize_budget_ceiling

    values: dict[str, object] = {
        "ceiling_policy_id": "policy.pr083.external.max",
        "prior": prior or _prior(),
        "admissible_set": admissible or _admissible(),
        "selection_rule": "max_ceiling",
        "objective": "conservative_upper_ceiling",
        "config_hash": "sha256:policy-config",
        "input_hashes": ("sha256:policy-input",),
        "generating_command": _COMMAND,
        "git_commit_or_worktree_state": _WORKTREE,
    }
    if "candidates" not in overrides:
        values["candidates"] = (candidate or _external_candidate(),)
    values.update(overrides)
    return optimize_budget_ceiling(**values)


def test_optimizer_policy_outputs_positive_finite_u_c_with_range_and_metadata() -> None:
    result = _result(
        candidates=(
            _external_candidate(U_C=1.5, candidate_id="cand.low"),
            _external_candidate(U_C=2.5, candidate_id="cand.high"),
        )
    )
    payload = result.to_payload()

    assert dataclasses.is_dataclass(result)
    assert payload["owner"] == "BASS"
    assert payload["implementation_scope"] == "bass_py"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["production_status"] == "diagnostic_only"
    assert payload["ceiling_policy_id"] == "policy.pr083.external.max"
    assert payload["U_C"] == pytest.approx(2.5)
    assert math.isfinite(payload["U_C"]) and payload["U_C"] > 0.0
    assert payload["valid_range"]["ell_min"] == 2
    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["transfer_spec_id"] == "aniclass.lowell.shear_to_D2.v1"
    assert payload["prior"]["prior_id"] == "prior.lowell.explicit.log-grid"
    assert payload["admissible_set"]["admissible_set_id"] == (
        "admissible.lowell.external-domain"
    )
    assert payload["rank_status"] == "full_rank"
    assert payload["config_hash"] == "sha256:policy-config"
    assert payload["input_hashes"] == ["sha256:policy-input"]
    assert payload["generating_command"] == _COMMAND
    assert payload["git_commit_or_worktree_state"] == _WORKTREE
    assert "native_validated" not in json.dumps(payload, sort_keys=True)
    assert "family_id" not in json.dumps(payload, sort_keys=True)


def test_external_transfer_optimizer_requires_pr014_transfer_metadata() -> None:
    from bass.atlas import BudgetCeilingCandidate

    with pytest.raises(ValueError, match="transfer_metadata"):
        BudgetCeilingCandidate(
            candidate_id="bad.missing.metadata",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="microkelvin_squared",
            valid_range={"ell_min": 2, "ell_max": 2},
            transfer_source="AniCLASS_external",
            transfer_spec_id="aniclass.lowell.shear_to_D2.v1",
        )

    metadata = dict(_external_entry().transfer_metadata)
    metadata["transfer_source"] = "empirical_proxy"
    with pytest.raises(ValueError, match="transfer_source must match"):
        BudgetCeilingCandidate(
            candidate_id="bad.mismatched.metadata",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="microkelvin_squared",
            valid_range={"ell_min": 2, "ell_max": 2},
            transfer_source="AniCLASS_external",
            transfer_spec_id="aniclass.lowell.shear_to_D2.v1",
            transfer_metadata=metadata,
        )

    metadata = dict(_external_entry().transfer_metadata)
    with pytest.raises(ValueError, match="transfer_spec_id must match"):
        BudgetCeilingCandidate(
            candidate_id="bad.mismatched.transfer-id",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="microkelvin_squared",
            valid_range=metadata["valid_range"],
            transfer_source="AniCLASS_external",
            transfer_spec_id="aniclass.lowell.shear_to_D3.v1",
            transfer_metadata=metadata,
        )

    metadata = dict(_external_entry().transfer_metadata)
    with pytest.raises(ValueError, match="valid_range must match"):
        BudgetCeilingCandidate(
            candidate_id="bad.mismatched.valid-range",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="microkelvin_squared",
            valid_range={
                "k_min": 1.0e-20,
                "k_max": 1.0e9,
                "ell_min": 0,
                "ell_max": 1_000_000,
            },
            transfer_source="AniCLASS_external",
            transfer_spec_id=metadata["transfer_id"],
            transfer_metadata=metadata,
        )


def test_optimizer_rejects_external_transfer_spoofed_as_native() -> None:
    from bass.atlas import BudgetCeilingCandidate

    base = dict(_external_entry().transfer_metadata)
    cases = [
        {"calibration_status": "native_validated"},
        {"native_solver_result": True},
        {"passed_validation_gates": ["native_transfer_validated"]},
    ]

    for index, overrides in enumerate(cases):
        metadata = dict(base)
        metadata.update(overrides)
        with pytest.raises(ValueError, match="native"):
            BudgetCeilingCandidate(
                candidate_id=f"bad.native.spoof.{index}",
                U_C=1.0,
                comparator="CMB_FLRW_reference",
                frame="normal_frame",
                units="microkelvin_squared",
                valid_range=metadata["valid_range"],
                transfer_source="AniCLASS_external",
                transfer_spec_id="aniclass.lowell.shear_to_D2.v1",
                transfer_metadata=metadata,
            )


def test_optimizer_rejects_schema_only_future_native_as_numeric_ceiling() -> None:
    from bass.atlas import AtlasEntryLite, BudgetCeilingCandidate
    from bass.transfer.native_schema import default_native_lowell_schema

    spec = default_native_lowell_schema().to_transfer_spec("alm_T")
    entry = AtlasEntryLite.from_transfer_spec(
        spec,
        comparison_group="pr083-native-schema",
        config_hash="sha256:native-schema-config",
        input_hashes=("sha256:native-schema-input",),
        generating_command=_COMMAND,
        git_commit_or_worktree_state=_WORKTREE,
    )

    with pytest.raises(ValueError, match="schema-only future native"):
        BudgetCeilingCandidate.from_atlas_entry(
            entry,
            candidate_id="bad.native.schema.numeric",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless",
        )


def test_optimizer_requires_prior_and_admissible_set_identity() -> None:
    with pytest.raises(ValueError, match="prior_id"):
        _prior(prior_id="")
    with pytest.raises(ValueError, match="prior_hash"):
        _prior(prior_hash="")
    with pytest.raises(ValueError, match="prior_support"):
        _prior(prior_support={})
    with pytest.raises(ValueError, match="admissible_set_id"):
        _admissible(admissible_set_id="")
    with pytest.raises(ValueError, match="admissible_set_status"):
        _admissible(admissible_set_status="not_declared")


def test_optimizer_rejects_hidden_default_prior_or_admissible_set() -> None:
    with pytest.raises(ValueError, match="prior_id"):
        _prior(prior_id="unknown")
    with pytest.raises(ValueError, match="prior_measure"):
        _prior(prior_measure="default")
    with pytest.raises(ValueError, match="admissible_set_id"):
        _admissible(admissible_set_id="all")
    with pytest.raises(ValueError, match="admissible_set_status"):
        _admissible(admissible_set_status="implicit")


def test_optimizer_rejects_inference_surface_fields_and_claim_phrases() -> None:
    from bass.atlas import BudgetCeilingCandidate

    with pytest.raises(ValueError, match="posterior_weight"):
        BudgetCeilingCandidate(
            candidate_id="bad.posterior",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless",
            valid_range={"x_C_min": 0.0, "x_C_max": 1.0},
            candidate_metadata={"posterior_weight": 0.25},
        )
    with pytest.raises(ValueError, match="mio_posterior_score"):
        BudgetCeilingCandidate(
            candidate_id="bad.posterior.substring",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless",
            valid_range={"x_C_min": 0.0, "x_C_max": 1.0},
            candidate_metadata={"mio_posterior_score": 0.25},
        )
    with pytest.raises(ValueError, match="certificate_ref"):
        BudgetCeilingCandidate(
            candidate_id="bad.certificate.substring",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless",
            valid_range={"x_C_min": 0.0, "x_C_max": 1.0},
            candidate_metadata={"certificate_ref": "mio://bad"},
        )

    with pytest.raises(ValueError, match="family"):
        _result(
            candidate=_mes_candidate(),
            caveats=("Bianchi family " + "identified",),
        )
    with pytest.raises(ValueError, match="MIO posterior|mio posterior"):
        _result(
            candidate=_mes_candidate(),
            caveats=("not native solver output; MIO posterior assigns odds",),
        )


def test_optimizer_output_can_build_mio_budget_spec_without_losing_policy() -> None:
    result = _result()

    budget = result.to_mio_budget_spec(
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
        )
    )
    payload = budget.as_payload()
    reference = result.to_mio_reference_payload(
        admissible_uses=(BudgetUse.SIGNED_PROJECTION_NORMALIZATION,)
    )

    assert budget.policy is BudgetPolicy.EXTERNAL_TRANSFER
    assert payload["denominator_value"] == pytest.approx(result.U_C)
    assert payload["denominator_policy"] == "external_transfer"
    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["transfer_spec_id"] == "aniclass.lowell.shear_to_D2.v1"
    assert payload["transfer_metadata"]["transfer_id"] == (
        "aniclass.lowell.shear_to_D2.v1"
    )
    assert payload["config_hash"] == "sha256:policy-config"
    assert payload["input_hashes"] == ["sha256:policy-input"]
    assert "ceiling_policy_id=policy.pr083.external.max" in payload["assumptions"]
    assert reference["ceiling_result_hash"] == result.ceiling_result_hash
    assert reference["prior_hash"] == "sha256:prior-explicit"
    assert reference["admissible_set_hash"] == "sha256:admissible-external"
    assert reference["admissible_uses"] == ["signed_projection_normalization"]


def test_mio_q_and_f_reference_optimizer_policy_explicitly() -> None:
    from mio.formalism.departure_bundle import build_departure_bundle
    from mio.formalism.filling_fraction import build_certified_filling_fraction
    from mio.formalism.normalized_score import build_normalized_score

    result = _result(
        candidate=_mes_candidate(U_C=1.0),
        admissible=_mes_admissible(),
        ceiling_policy_id="policy.pr083.mes.certified",
    )
    bundle = build_departure_bundle(
        {
            "Sigma2_std": 0.2,
            "W2_std": 0.0,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="sha256:bundle-config",
        input_hashes=("sha256:bundle-input",),
    )

    q_budget = result.to_mio_budget_spec(
        admissible_uses=(BudgetUse.SIGNED_PROJECTION_NORMALIZATION,)
    )
    q = build_normalized_score(
        bundle,
        q_budget,
        numerator_policy="signed",
        artifact_metadata={
            "ceiling_policy_reference": result.to_mio_reference_payload(
                admissible_uses=(BudgetUse.SIGNED_PROJECTION_NORMALIZATION,)
            )
        },
    ).as_payload()
    q_text = json.dumps(q, sort_keys=True).lower()
    assert q["artifact_metadata"]["ceiling_policy_reference"][
        "ceiling_policy_id"
    ] == "policy.pr083.mes.certified"
    assert q["denominator_use"] == "signed_projection_normalization"
    for forbidden in (
        "filling",
        "occupancy",
        "posterior",
        "evidence",
        "family_id",
        "native_validated",
    ):
        assert forbidden not in q_text

    f_budget = result.to_mio_budget_spec(
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.CERTIFIED_FILLING_CEILING,
        )
    )
    f_payload = build_certified_filling_fraction(
        (bundle,),
        (f_budget,),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
        artifact_metadata={
            "ceiling_policy_reference": result.to_mio_reference_payload(
                admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,)
            )
        },
    ).as_payload()
    assert f_payload["artifact_metadata"]["ceiling_policy_reference"][
        "ceiling_policy_id"
    ] == "policy.pr083.mes.certified"
    assert f_payload["budget_is_admissible_ceiling"] is True
    assert f_payload["F_Bayes"] == pytest.approx(0.2)


def test_optimizer_policy_cannot_certify_f_pre_native_unless_mes_admissible() -> None:
    external = _result()
    with pytest.raises(ValueError, match="cannot certify"):
        external.to_mio_budget_spec(
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,)
        )

    non_admissible_mes = _result(
        candidate=_mes_candidate(),
        admissible=_admissible(admissible_set_status="explicit_pre_solver"),
        ceiling_policy_id="policy.pr083.mes.not-certified",
    )
    with pytest.raises(ValueError, match="cannot certify"):
        non_admissible_mes.to_mio_budget_spec(
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,)
        )

    rank_unknown_mes = _result(
        candidate=_mes_candidate(rank_status="not_evaluated"),
        admissible=_mes_admissible(),
        ceiling_policy_id="policy.pr083.mes.rank-unknown",
    )
    with pytest.raises(ValueError, match="rank_status"):
        rank_unknown_mes.to_mio_budget_spec(
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,)
        )


def test_optimizer_depth_gap_reference_requires_bin_and_null_metadata() -> None:
    result = _result(candidate=_mes_candidate(), admissible=_mes_admissible())
    with pytest.raises(ValueError, match="depth_gap_metadata"):
        result.to_mio_budget_spec(admissible_uses=(BudgetUse.DEPTH_GAP_REFERENCE,))

    depth_result = _result(
        candidate=_mes_candidate(),
        admissible=_mes_admissible(),
        depth_gap_metadata={
            "bin_edges": [0.0, 0.5, 1.0],
            "depth_convention": "redshift_bin_edges",
            "denominator_evolution_status": "piecewise_constant_per_bin",
            "covariance_status": "mock_covariance_available",
            "null_mock_status": "matched_null_available",
        },
    )
    budget = depth_result.to_mio_budget_spec(
        admissible_uses=(BudgetUse.DEPTH_GAP_REFERENCE,)
    )
    reference = depth_result.to_mio_reference_payload(
        admissible_uses=(BudgetUse.DEPTH_GAP_REFERENCE,)
    )

    assert BudgetUse.DEPTH_GAP_REFERENCE in budget.admissible_uses
    assert budget.covariance_status == "mock_covariance_available"
    assert budget.null_mock_status == "matched_null_available"
    assert reference["depth_gap_metadata"]["bin_edges"] == [0.0, 0.5, 1.0]
    assert any(
        item.startswith("depth_gap_metadata_hash=") for item in budget.assumptions
    )


def test_quantile_higher_selects_existing_candidate_without_interpolation() -> None:
    result = _result(
        candidates=(
            _mes_candidate(U_C=1.0, candidate_id="cand.1"),
            _mes_candidate(U_C=2.0, candidate_id="cand.2"),
            _mes_candidate(U_C=5.0, candidate_id="cand.5"),
        ),
        admissible=_mes_admissible(),
        selection_rule="quantile_higher",
        quantile=0.5,
    )

    assert result.U_C == pytest.approx(2.0)
    assert result.selected_candidate.candidate_id == "cand.2"
    assert [item["candidate_id"] for item in result.rejected_candidates] == [
        "cand.1",
        "cand.5",
    ]


def test_optimizer_rejects_mixed_transfer_source_candidate_sets() -> None:
    with pytest.raises(ValueError, match="transfer_source"):
        _result(
            candidates=(
                    _mes_candidate(U_C=1.0, candidate_id="cand.mes"),
                    _external_candidate(
                        U_C=2.0,
                        candidate_id="cand.external",
                        units="dimensionless_hubble_normalized",
                    ),
                )
            )


def test_rejected_candidates_preserve_full_provenance() -> None:
    result = _result(
        candidates=(
            _external_candidate(U_C=1.5, candidate_id="cand.low"),
            _external_candidate(U_C=2.5, candidate_id="cand.high"),
        )
    )

    rejected = result.to_payload()["rejected_candidates"][0]
    assert rejected["candidate_id"] == "cand.low"
    assert rejected["transfer_source"] == "AniCLASS_external"
    assert rejected["transfer_spec_id"] == "aniclass.lowell.shear_to_D2.v1"
    assert rejected["valid_range"]["ell_min"] == 2
    assert rejected["transfer_metadata"]["transfer_id"] == (
        "aniclass.lowell.shear_to_D2.v1"
    )


def test_direct_candidate_valid_range_must_be_structured() -> None:
    from bass.atlas import BudgetCeilingCandidate

    base = {
        "candidate_id": "bad.range",
        "U_C": 1.0,
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless",
    }
    for valid_range in (
        {"x_C_min": 1.0, "x_C_max": 0.0},
        {"ell_min": "two", "ell_max": 2},
        {"range_role": "missing_bounds"},
    ):
        with pytest.raises(ValueError, match="valid_range"):
            BudgetCeilingCandidate(**base, valid_range=valid_range)


def test_rank_invariants_fail_closed() -> None:
    from bass.atlas import BudgetCeilingCandidate

    with pytest.raises(ValueError, match="full_rank"):
        BudgetCeilingCandidate(
            candidate_id="bad.fullrank.no-rank",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless",
            valid_range={"x_C_min": 0.0, "x_C_max": 1.0},
            rank_status="full_rank",
        )
    with pytest.raises(ValueError, match="rank_status"):
        BudgetCeilingCandidate(
            candidate_id="bad.rank.status",
            U_C=1.0,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless",
            valid_range={"x_C_min": 0.0, "x_C_max": 1.0},
            rank_status="best_rank",
        )
