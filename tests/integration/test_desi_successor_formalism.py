"""PR-311 DESI BGS_BRIGHT successor-formalism contracts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCIENCE = ROOT / "htt/obsstat/desi_successor_formalism.py"
WORKER = ROOT / "scripts/observed_runs/run_desi_bgs_bright.py"
DISPATCHER = ROOT / "scripts/codex_harness/run_authorized_observational_program.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def science():
    return _load("pr311_desi_science", SCIENCE)


@pytest.fixture(scope="module")
def worker():
    return _load("pr311_desi_worker", WORKER)


def _selection(module):
    return module.DESISelection(
        release_id="DESI_DR1_LSS_IRON_V1_5",
        tracer="BGS_BRIGHT-21.5",
        base_apparent_r_limit=19.5,
        absolute_magnitude_max=-21.5,
        z_min=0.1,
        z_max=0.4,
        caps=("NGC", "SGC"),
        selection_id="desi:dr1:bgs_bright-21.5:z0.1-0.4",
        selection_derivation_id=module.SELECTION_DERIVATION_ID,
        window_ids=("desi:dr1:ngc:random0", "desi:dr1:sgc:random0"),
        operator_id="desi-pr311-identical-data-null-operator-v1",
        units_contract_id="units:DESI:number-counts-direction-redshift:v1",
        coordinate_frame_id="frame:DESI:galactic-direction-cmb-redshift:v1",
        sign_orientation_convention_id="sign:DESI:overdensity-positive:v1",
        directional_convention_id="direction:DESI:galactic-unit-vector:v1",
        harmonic_convention_id="harmonic:DESI:not-applicable:v1",
        mask_id="mask:DESI:dr1-v1.5-ngc-sgc-random-window:v1",
        sky_support_id="sky:DESI:dr1-v1.5-ngc-sgc:v1",
        covariance_id="covariance:DESI:ezmock-1000:v1",
        null_ensemble_id="null:DESI:ezmock-1000-abacus-25:v1",
        transfer_source="none",
        transfer_function_spec_id="none",
    )


def _realization(module, family: str, realization: int, *, phase: float = 0.0):
    rows_per_cell = 8
    caps = np.repeat(np.asarray(["NGC", "SGC"]), 3 * rows_per_cell)
    bins = np.tile(np.repeat(np.arange(3), rows_per_cell), 2)
    row = np.arange(caps.size, dtype=float)
    redshift = 0.15 + 0.10 * bins + 0.002 * ((row % rows_per_cell) - 3.5)
    apparent_r = 18.2 + 0.02 * (row % rows_per_cell)
    absolute_r = -22.2 + 0.03 * (row % rows_per_cell)
    longitude = 0.19 * row + phase
    latitude = 0.25 * np.sin(0.23 * row + 0.01 * realization)
    direction = np.column_stack(
        [
            np.cos(latitude) * np.cos(longitude),
            np.cos(latitude) * np.sin(longitude),
            np.sin(latitude),
        ]
    )
    random_weight = 75.0 + 4.0 * np.cos(0.17 * row + phase)
    nuisance = np.sin(0.31 * row + 0.07 * realization)
    nuisance -= np.mean(nuisance)
    cap_alpha = np.where(caps == "NGC", 0.78, 0.84)
    cap_alpha = cap_alpha * (1.0 + 2.0e-4 * realization)
    clustering = 0.006 * (direction @ np.asarray([0.4, -0.2, 0.7]))
    family_offset = 0 if family == "EZMOCK" else 100_000
    stochastic = np.random.default_rng(family_offset + realization).normal(
        0.0, 0.002, size=row.size
    )
    counts = cap_alpha * random_weight * (
        1.0 + clustering + 0.004 * nuisance + stochastic
    )
    return module.DESIRealization(
        family=family,
        realization=realization,
        tracer="BGS_BRIGHT-21.5",
        base_apparent_r_limit=19.5,
        absolute_magnitude_max=-21.5,
        cap=caps,
        redshift=redshift,
        official_sample_member=np.ones(row.size, dtype=bool),
        apparent_r_mag=apparent_r,
        absolute_magnitude_r=absolute_r,
        direction=direction,
        weighted_counts=counts,
        random_window_weight=random_weight,
        nuisance_template=nuisance,
        selection_id="desi:dr1:bgs_bright-21.5:z0.1-0.4",
        window_ids=("desi:dr1:ngc:random0", "desi:dr1:sgc:random0"),
        operator_id="desi-pr311-identical-data-null-operator-v1",
    )


def _responses(module):
    size = len(module.FEATURE_ORDER)
    x = np.linspace(-1.0, 1.0, size)
    nuisance = np.column_stack([np.ones(size), x])
    candidate = np.column_stack(
        [np.sin(1.3 * x), np.cos(1.9 * x), x * x - np.mean(x * x)]
    )
    confusion = np.column_stack(
        [np.sin(0.8 * x), np.cos(1.1 * x), np.sin(1.7 * x + 0.2)]
    )
    return nuisance, candidate, confusion


@pytest.fixture(scope="module")
def complete_case(science):
    selection = _selection(science)
    ezmock = tuple(
        _realization(science, "EZMOCK", index) for index in range(1, 1001)
    )
    abacus = tuple(
        _realization(science, "ABACUS", index, phase=0.09) for index in range(25)
    )
    nuisance, candidate, confusion = _responses(science)
    return selection, ezmock, abacus, nuisance, candidate, confusion


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("tracer", "BGS_ANY"),
        ("base_apparent_r_limit", 21.5),
        ("base_apparent_r_limit", 19.50000001),
        ("absolute_magnitude_max", 21.5),
        ("absolute_magnitude_max", -21.49999999),
        ("z_min", 0.0),
        ("z_min", 0.100000001),
        ("z_max", 0.5),
        ("z_max", 0.399999999),
        ("caps", ("SGC", "NGC")),
        ("selection_derivation_id", "locally-invented-selection"),
        ("transfer_source", "external"),
    ),
)
def test_pr311_rejects_nonexact_selection(science, field: str, value: object) -> None:
    values = {**_selection(science).__dict__, field: value}
    with pytest.raises(science.DESISuccessorError, match="selection|BGS_BRIGHT"):
        science.validate_selection(science.DESISelection(**values))


def test_pr311_refits_alpha_and_nuisance_on_every_realization(science) -> None:
    selection = _selection(science)
    first = science.fit_realization(_realization(science, "EZMOCK", 1), selection)
    second = science.fit_realization(_realization(science, "EZMOCK", 2), selection)

    assert first.feature_order == science.FEATURE_ORDER
    assert len(first.alpha_hat) == 6
    assert len(first.nuisance_hat) == 6
    assert first.alpha_hat != second.alpha_hat
    assert first.nuisance_hat != second.nuisance_hat
    assert np.all(np.isfinite(first.features))


@pytest.mark.parametrize(
    ("field", "boundary"),
    (
        ("apparent_r_mag", 19.5),
        ("absolute_magnitude_r", -21.5),
        ("redshift", 0.1),
        ("redshift", 0.4),
    ),
)
def test_pr311_row_selection_boundaries_are_strict(
    science, field: str, boundary: float
) -> None:
    baseline = _realization(science, "EZMOCK", 1)
    changed = np.asarray(getattr(baseline, field)).copy()
    changed[0] = boundary
    with pytest.raises(science.DESISuccessorError, match="official BGS_BRIGHT"):
        science.DESIRealization(**{**baseline.__dict__, field: changed})


def test_pr311_rejects_nonmember_or_nonunit_direction(science) -> None:
    baseline = _realization(science, "EZMOCK", 1)
    membership = baseline.official_sample_member.copy()
    membership[0] = False
    with pytest.raises(science.DESISuccessorError, match="official BGS_BRIGHT"):
        science.DESIRealization(
            **{**baseline.__dict__, "official_sample_member": membership}
        )
    direction = baseline.direction.copy()
    direction[0] *= 2.0
    with pytest.raises(science.DESISuccessorError):
        science.DESIRealization(**{**baseline.__dict__, "direction": direction})


def test_pr311_singular_per_realization_refit_is_rejected(science) -> None:
    baseline = _realization(science, "EZMOCK", 1)
    singular = science.DESIRealization(
        **{**baseline.__dict__, "nuisance_template": np.ones(baseline.redshift.size)}
    )
    with pytest.raises(science.DESISuccessorError, match="nuisance refit is singular"):
        science.fit_realization(singular, _selection(science))


def test_pr311_refit_is_bound_to_cap_window_and_identical_operator(science) -> None:
    selection = _selection(science)
    baseline = _realization(science, "EZMOCK", 0)
    for mutation in (
        {"tracer": "BGS_ANY"},
        {"base_apparent_r_limit": 19.50000001},
        {"absolute_magnitude_max": -21.49999999},
        {"window_ids": tuple(reversed(baseline.window_ids))},
        {"operator_id": "different-null-operator"},
    ):
        changed = science.DESIRealization(**{**baseline.__dict__, **mutation})
        with pytest.raises(science.DESISuccessorError):
            science.fit_realization(changed, selection)


def test_pr311_tomography_order_is_frozen_and_nonmetadata(science) -> None:
    fitted = science.fit_realization(
        _realization(science, "EZMOCK", 3), _selection(science)
    )
    assert fitted.feature_order == tuple(
        f"{cap}:{bin_id}:{axis}"
        for cap in ("NGC", "SGC")
        for bin_id in ("z0.1-0.2", "z0.2-0.3", "z0.3-0.4")
        for axis in ("x", "y", "z")
    )
    assert set(fitted.alpha_hat) == {
        f"{cap}:{bin_id}"
        for cap in ("NGC", "SGC")
        for bin_id in ("z0.1-0.2", "z0.2-0.3", "z0.3-0.4")
    }


def test_pr311_exact_mock_tiers_own_distinct_roles(science, complete_case) -> None:
    selection, ezmock, abacus, *_ = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)

    assert support.ezmock_count == 1000
    assert support.abacus_count == 25
    assert support.covariance_owner == "EZMOCK_1000_ONLY"
    assert support.abacus_role == "SEPARATE_HELD_OUT_VALIDATION"
    assert support.pooled_with_ezmock is False
    assert support.covariance.shape == (
        len(science.FEATURE_ORDER),
        len(science.FEATURE_ORDER),
    )
    off_diagonal = support.covariance - np.diag(np.diag(support.covariance))
    assert np.any(np.abs(off_diagonal) > 0.0)


@pytest.mark.parametrize(("ez_count", "abacus_count"), ((999, 25), (1000, 24)))
def test_pr311_partial_mock_inventory_stops_before_covariance(
    science, complete_case, monkeypatch, ez_count: int, abacus_count: int
) -> None:
    selection, ezmock, abacus, *_ = complete_case
    reached_covariance = False

    def forbidden(*_args, **_kwargs):
        nonlocal reached_covariance
        reached_covariance = True
        raise AssertionError("covariance reached with a partial inventory")

    monkeypatch.setattr(science.np, "cov", forbidden)
    with pytest.raises(science.DESISuccessorError, match="exactly 1000|exactly 25"):
        science.build_mock_support(
            ezmock[:ez_count], abacus[:abacus_count], selection
        )
    assert reached_covariance is False


def test_pr311_duplicate_mock_identity_stops_before_covariance(
    science, complete_case, monkeypatch
) -> None:
    selection, ezmock, abacus, *_ = complete_case
    duplicate = science.DESIRealization(
        **{**ezmock[1].__dict__, "realization": ezmock[0].realization}
    )
    monkeypatch.setattr(
        science.np,
        "cov",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("covariance reached with duplicate identity")
        ),
    )
    with pytest.raises(science.DESISuccessorError, match="order or family"):
        science.build_mock_support(
            (ezmock[0], duplicate, *ezmock[2:]), abacus, selection
        )


def test_pr311_abacus_is_not_silently_pooled(science, complete_case) -> None:
    selection, ezmock, abacus, *_ = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)
    ez_features = np.asarray(
        [science.fit_realization(row, selection).features for row in ezmock]
    )
    pooled = np.cov(
        np.vstack(
            [
                ez_features,
                [science.fit_realization(row, selection).features for row in abacus],
            ]
        ),
        rowvar=False,
        ddof=1,
    )
    assert not np.allclose(support.covariance, pooled, rtol=0.0, atol=1.0e-15)


def test_pr311_covariance_is_exactly_ezmock_only(science, complete_case) -> None:
    selection, ezmock, abacus, *_ = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)
    ez_features = np.asarray(
        [science.fit_realization(row, selection).features for row in ezmock]
    )
    expected = np.cov(ez_features, rowvar=False, ddof=1)
    expected = 0.5 * (expected + expected.T)
    assert np.allclose(support.covariance, expected, rtol=0.0, atol=0.0)


def test_pr311_abacus_rows_change_validation_but_not_covariance(
    science, complete_case
) -> None:
    selection, ezmock, abacus, nuisance, candidate, confusion = complete_case
    baseline = science.analyze_successor_formalism(
        ezmock,
        abacus,
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=candidate,
        confusion_templates=confusion,
        observed=False,
    )
    first = science.fit_realization(abacus[0], selection)
    shifted = science.DESIFitResult(
        **{
            **first.__dict__,
            "features": first.features + np.linspace(0.0, 0.01, first.features.size),
        }
    )
    replay = science.analyze_successor_formalism(
        ezmock,
        (shifted, *tuple(science.fit_realization(row, selection) for row in abacus[1:])),
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=candidate,
        confusion_templates=confusion,
        observed=False,
    )
    assert replay["covariance"] == baseline["covariance"]
    assert (
        replay["abacus_validation"]["whitened_mean_shift_norm"]
        != baseline["abacus_validation"]["whitened_mean_shift_norm"]
    )


def test_pr311_catastrophic_abacus_shift_vetoes_closure(
    science, complete_case
) -> None:
    selection, ezmock, abacus, nuisance, candidate, confusion = complete_case
    shifted = []
    for row in abacus:
        fitted = science.fit_realization(row, selection)
        shifted.append(
            science.DESIFitResult(
                **{**fitted.__dict__, "features": fitted.features + 1.0}
            )
        )
    result = science.analyze_successor_formalism(
        ezmock,
        tuple(shifted),
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=candidate,
        confusion_templates=confusion,
        observed=False,
    )
    validation = result["abacus_validation"]
    assert result["terminal_disposition"] == "ABACUS_HELD_OUT_VALIDATION_FAILED"
    assert validation["status"] == "FAIL_HELD_OUT_MEAN_SHIFT"
    assert (
        validation["mean_shift_rms_ratio"]
        > validation["maximum_mean_shift_rms_ratio"]
    )
    assert result["p_value"] is None
    assert result["forced_source_label"] is None


def test_pr311_response_rank_is_scale_invariant(science, complete_case) -> None:
    selection, ezmock, abacus, nuisance, candidate, _ = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)
    baseline = science.evaluate_response_rank(
        support.covariance,
        nuisance_response=nuisance,
        candidate_response=candidate,
        response_feature_order=science.FEATURE_ORDER,
    )
    assert baseline["status"] == "FULL_INCREMENTAL_RANK"
    for scale in (1.0e-12, 1.0e-6, 1.0e6, 1.0e12):
        replay = science.evaluate_response_rank(
            support.covariance,
            nuisance_response=nuisance,
            candidate_response=scale * candidate,
            response_feature_order=science.FEATURE_ORDER,
        )
        assert replay["incremental_rank"] == baseline["incremental_rank"]
        assert replay["status"] == baseline["status"]
        assert replay["column_scaling"] == "covariance_whitened_l2"


def test_pr311_response_rank_is_independent_column_scale_and_sign_invariant(
    science, complete_case
) -> None:
    selection, ezmock, abacus, nuisance, candidate, _ = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)
    baseline = science.evaluate_response_rank(
        support.covariance,
        nuisance_response=nuisance,
        candidate_response=candidate,
    )
    replay = science.evaluate_response_rank(
        support.covariance,
        nuisance_response=nuisance * np.asarray([1.0e-9, -1.0e9]),
        candidate_response=candidate * np.asarray([-1.0e12, 1.0e-7, -3.0]),
    )
    assert replay["status"] == baseline["status"] == "FULL_INCREMENTAL_RANK"
    assert replay["base_rank"] == baseline["base_rank"]
    assert replay["incremental_rank"] == baseline["incremental_rank"]


def test_pr311_rank_rejects_nuisance_or_candidate_dependence(science, complete_case) -> None:
    selection, ezmock, abacus, nuisance, candidate, _ = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)
    nuisance_deficient = np.column_stack([nuisance[:, 0], nuisance[:, 0]])
    base_failure = science.evaluate_response_rank(
        support.covariance,
        nuisance_response=nuisance_deficient,
        candidate_response=candidate,
    )
    candidate_deficient = np.column_stack(
        [candidate[:, 0], candidate[:, 0], nuisance[:, 0]]
    )
    candidate_failure = science.evaluate_response_rank(
        support.covariance,
        nuisance_response=nuisance,
        candidate_response=candidate_deficient,
    )
    assert base_failure["status"] == "NON_IDENTIFIED_ABSTAIN"
    assert candidate_failure["status"] == "NON_IDENTIFIED_ABSTAIN"


def test_pr311_rank_rejects_zero_columns_and_nonpositive_covariance(
    science, complete_case
) -> None:
    selection, ezmock, abacus, nuisance, candidate, _ = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)
    zero = candidate.copy()
    zero[:, 0] = 0.0
    with pytest.raises(science.DESISuccessorError, match="zero response column"):
        science.evaluate_response_rank(
            support.covariance,
            nuisance_response=nuisance,
            candidate_response=zero,
        )
    singular = support.covariance.copy()
    singular[0] = 0.0
    singular[:, 0] = 0.0
    with pytest.raises(science.DESISuccessorError, match="positive definite"):
        science.evaluate_response_rank(
            singular,
            nuisance_response=nuisance,
            candidate_response=candidate,
        )


def test_pr311_rank_loss_forces_abstention_without_statistic(science, complete_case) -> None:
    selection, ezmock, abacus, nuisance, _candidate, confusion = complete_case
    collinear = np.column_stack([nuisance[:, 0], nuisance[:, 0], nuisance[:, 1]])
    result = science.analyze_successor_formalism(
        ezmock,
        abacus,
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=collinear,
        confusion_templates=confusion,
        observed=False,
    )
    assert result["terminal_disposition"] == "NON_IDENTIFIED_ABSTAIN"
    assert result["p_value"] is None
    assert result["forced_source_label"] is None
    assert result["observed_statistic_seen"] is False


def test_pr311_confusion_is_diagnostic_not_attribution(science, complete_case) -> None:
    selection, ezmock, abacus, nuisance, candidate, confusion = complete_case
    result = science.analyze_successor_formalism(
        ezmock,
        abacus,
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=candidate,
        confusion_templates=confusion,
        observed=False,
    )
    diagnostic = result["component_confusion"]
    assert diagnostic["component_order"] == [
        "clustering",
        "kinematic",
        "selection",
    ]
    assert np.asarray(diagnostic["normalized_overlap_matrix"]).shape == (3, 3)
    assert diagnostic["causal_attribution_identified"] is False
    assert result["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"
    assert result["p_value"] is None
    assert result["forced_source_label"] is None


def test_pr311_confusion_is_symmetric_normalized_and_scale_invariant(
    science, complete_case
) -> None:
    selection, ezmock, abacus, _nuisance, _candidate, confusion = complete_case
    support = science.build_mock_support(ezmock, abacus, selection)
    baseline = science._confusion_diagnostic(support.covariance, confusion)
    replay = science._confusion_diagnostic(
        support.covariance,
        confusion * np.asarray([-1.0e-8, 1.0e5, -3.0]),
    )
    matrix = np.asarray(baseline["normalized_overlap_matrix"])
    assert np.allclose(matrix, matrix.T, rtol=0.0, atol=1.0e-14)
    assert np.allclose(np.diag(matrix), 1.0, rtol=0.0, atol=1.0e-14)
    assert np.allclose(
        replay["normalized_overlap_matrix"], matrix, rtol=1.0e-12, atol=1.0e-12
    )
    zero = confusion.copy()
    zero[:, 0] = 0.0
    with pytest.raises(science.DESISuccessorError, match="zero response column"):
        science._confusion_diagnostic(support.covariance, zero)


def test_pr311_attended_observed_mode_remains_diagnostic_only(
    science, complete_case
) -> None:
    selection, ezmock, abacus, nuisance, candidate, confusion = complete_case
    result = science.analyze_successor_formalism(
        ezmock,
        abacus,
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=candidate,
        confusion_templates=confusion,
        observed=True,
        observed_realization=_realization(science, "OBSERVED", 0),
    )
    assert result["terminal_disposition"] == "OBSERVED_OPERATOR_DIAGNOSTIC_COMPLETE"
    assert result["observed_statistic_seen"] is True
    assert result["observed_science_executed"] is True
    assert result["p_value"] is None
    assert result["forced_source_label"] is None
    assert result["component_confusion"]["causal_attribution_identified"] is False
    assert result["artifact_metadata"]["claim_tier"] == "diagnostic_only"
    assert result["artifact_metadata"]["public_use"] is False


def test_pr311_response_rows_are_bound_to_exact_feature_order(science, complete_case) -> None:
    selection, ezmock, abacus, nuisance, candidate, confusion = complete_case
    with pytest.raises(science.DESISuccessorError, match="feature order"):
        science.analyze_successor_formalism(
            ezmock,
            abacus,
            selection=selection,
            nuisance_response=nuisance[::-1],
            candidate_response=candidate[::-1],
            confusion_templates=confusion[::-1],
            response_feature_order=tuple(reversed(science.FEATURE_ORDER)),
            observed=False,
        )


@pytest.mark.parametrize("rows", ("1", "8", "32", "128", "full"))
def test_pr311_synthetic_profiles_are_observation_free(worker, rows: str) -> None:
    result = worker.synthetic_profile(rows=rows)
    assert result["profile_rows"] == rows
    assert result["observed_statistic_seen"] is False
    assert result["observed_science_executed"] is False
    assert result["p_value"] is None
    assert result["forced_source_label"] is None
    if rows == "full":
        assert result["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"
        assert result["mock_support"]["ezmock_count"] == 1000
        assert result["mock_support"]["abacus_count"] == 25
    else:
        assert result["terminal_disposition"] == "PROFILE_ONLY_INCOMPLETE_INVENTORY"
        assert result["covariance"] is None
        assert result["response_rank"] is None


def test_pr311_synthetic_cli_rejects_admission_and_data_root(worker, tmp_path: Path) -> None:
    output = tmp_path / "synthetic.json"
    assert worker.main(
        [
            "--synthetic-profile",
            "--admission",
            str(tmp_path / "admission.json"),
            "--data-root",
            str(tmp_path),
            "--output",
            str(output),
        ]
    ) == 2
    assert not output.exists()


@pytest.mark.parametrize("mode", ("thread", "process"))
def test_pr311_small_parallel_probes_remain_noninferential(worker, mode: str) -> None:
    result = worker.synthetic_profile(rows="8", mode=mode, workers=2)
    assert result["mode"] == mode
    assert result["profile_realization_count"] == 8
    assert result["terminal_disposition"] == "PROFILE_ONLY_INCOMPLETE_INVENTORY"
    assert result["covariance"] is None
    assert result["response_rank"] is None
    assert result["observed_statistic_seen"] is False
    assert result["observed_science_executed"] is False


def test_pr311_rootless_admission_stops_before_data_open(
    worker, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened = False

    def forbidden() -> None:
        nonlocal opened
        opened = True
        raise AssertionError("observed data open attempted")

    monkeypatch.setattr(worker, "_mark_observed_data_open_attempt", forbidden)
    admission = tmp_path / "admission.json"
    admission.write_text(json.dumps({"lane_id": "DESI"}), encoding="utf-8")
    assert worker.main(
        [
            "--run-admitted",
            "--admission",
            str(admission),
            "--data-root",
            str(tmp_path),
            "--output",
            str(tmp_path / "result.json"),
        ]
    ) == 2
    assert opened is False


def test_pr311_dispatcher_registers_one_exact_desi_profile() -> None:
    dispatcher = _load("pr311_dispatcher", DISPATCHER)
    profile = dispatcher._lane_profile("DESI")
    assert profile.analysis_plan_id == "plan:PR203-DESI-BGS-V1"
    assert profile.science_execution_mode == "desi_bgs_bright_successor_operator"
    assert profile.science_worker_relative == "scripts/observed_runs/run_desi_bgs_bright.py"
    assert profile.science_worker_arguments == ("--run-admitted",)
    assert profile.result_filename == "desi_bgs_bright_result.json"
    for forbidden in ("--all", "CROSS_PROBE", "BGS_ANY"):
        with pytest.raises(dispatcher.ObservationalProgramError):
            dispatcher._lane_profile(forbidden)


def test_pr311_worker_rebinds_exact_attended_admission(worker, monkeypatch) -> None:
    raw = b'{"admission":"DESI"}'
    record_ids = ["sha256:" + "2" * 64, "sha256:" + "3" * 64]
    decision = SimpleNamespace(
        lane_admission_bundle_id="sha256:" + "1" * 64,
        records=tuple(SimpleNamespace(record_id=value) for value in record_ids),
    )
    monkeypatch.setenv("HTT_ATTENDED_ADMISSION_SHA256", worker._raw_hash(raw))
    monkeypatch.setenv(
        "HTT_ATTENDED_ADMISSION_BUNDLE_ID", decision.lane_admission_bundle_id
    )
    monkeypatch.setenv(
        "HTT_ATTENDED_ORDERED_RECORD_IDS_SHA256", worker.canonical_sha256(record_ids)
    )
    worker._validate_attended_admission_binding(raw, decision)
    monkeypatch.setenv("HTT_ATTENDED_ADMISSION_SHA256", "sha256:" + "0" * 64)
    with pytest.raises(worker.DESIWorkerError, match="acceptance binding"):
        worker._validate_attended_admission_binding(raw, decision)


@pytest.mark.parametrize(
    "field",
    (
        "units_contract_id",
        "coordinate_frame_id",
        "sign_orientation_convention_id",
        "directional_convention_id",
        "harmonic_convention_id",
        "mask_id",
        "sky_support_id",
        "covariance_id",
        "null_ensemble_id",
        "transfer_function_spec_id",
    ),
)
def test_pr311_worker_binds_scientific_identities_to_admission(
    worker, field: str
) -> None:
    selection = worker._synthetic_selection()
    values = {
        name: getattr(selection, name) for name in worker.SEMANTIC_IDENTITY_FIELDS
    }
    record = SimpleNamespace(
        selection_id=selection.selection_id,
        transfer_source=selection.transfer_source,
        **values,
    )
    worker._bind_selection_to_admission(
        selection, SimpleNamespace(records=(record,))
    )
    changed = {**record.__dict__, field: "scientific-identity-drift"}
    with pytest.raises(worker.DESIWorkerError, match="identity drifted"):
        worker._bind_selection_to_admission(
            selection, SimpleNamespace(records=(SimpleNamespace(**changed),))
        )


def test_pr311_worker_streams_one_current_stack_compact_realization(
    science, worker, tmp_path: Path
) -> None:
    selection = worker._synthetic_selection()
    row = worker._synthetic_realization("EZMOCK", 1)
    path = tmp_path / "ezmock-0001.npz"
    np.savez(
        path,
        cap=row.cap,
        redshift=row.redshift,
        official_sample_member=row.official_sample_member,
        apparent_r_mag=row.apparent_r_mag,
        absolute_magnitude_r=row.absolute_magnitude_r,
        direction=row.direction,
        weighted_counts=row.weighted_counts,
        random_window_weight=row.random_window_weight,
        nuisance_template=row.nuisance_template,
        tracer=np.asarray(row.tracer),
        base_apparent_r_limit=np.asarray(row.base_apparent_r_limit),
        absolute_magnitude_max=np.asarray(row.absolute_magnitude_max),
        selection_id=np.asarray(row.selection_id),
        window_ids=np.asarray(row.window_ids),
        operator_id=np.asarray(row.operator_id),
    )
    fitted, observed = worker._fit_npz(
        path, family="EZMOCK", realization=1, selection=selection
    )
    assert observed is None
    assert fitted.family == "EZMOCK"
    assert fitted.realization == 1
    assert fitted.feature_order == worker.FEATURE_ORDER == science.FEATURE_ORDER
    assert np.all(np.isfinite(fitted.features))


def test_pr311_prefitted_rows_preserve_exact_tier_separation(science, complete_case) -> None:
    selection, ezmock, abacus, *_ = complete_case
    ez_fits = tuple(science.fit_realization(row, selection) for row in ezmock)
    ab_fits = tuple(science.fit_realization(row, selection) for row in abacus)
    support = science.build_mock_support(ez_fits, ab_fits, selection)
    assert support.ezmock_count == 1000
    assert support.abacus_count == 25
    assert support.pooled_with_ezmock is False


def test_pr311_output_has_no_inference_attribution_or_family_surface(worker) -> None:
    result = worker.synthetic_profile(rows="full")
    encoded = json.dumps(result, sort_keys=True).lower()
    for forbidden in (
        '"posterior"',
        '"bayes_factor"',
        '"source_label"',
        '"family_identification"',
        '"observed_amplitude"',
    ):
        assert forbidden not in encoded
    assert result["artifact_metadata"]["claim_tier"] == "diagnostic_only"
    assert result["artifact_metadata"]["public_use"] is False
    assert result["p_value"] is None
    assert result["forced_source_label"] is None
    assert result["component_confusion"]["causal_attribution_identified"] is False
    assert result["abacus_validation"]["status"] == "PASS_HELD_OUT_MEAN_SHIFT"
    assert result["artifact_metadata"]["covariance_status"] == (
        "FULL_EZMOCK_1000_COVARIANCE"
    )
    assert result["artifact_metadata"]["null_mock_status"] == (
        "EZMOCK_1000_WITH_ABACUS_25_HELD_OUT"
    )
    assert result["artifact_metadata"]["transfer_source"] == "none"
    assert "causal_component_attribution" in result["artifact_metadata"][
        "forbidden_uses"
    ]

    keys: set[str] = set()

    def collect(value: object) -> None:
        if isinstance(value, dict):
            keys.update(str(key).lower() for key in value)
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(result)
    assert keys.isdisjoint(
        {
            "x",
            "q",
            "pi",
            "f",
            "g_f",
            "mio_certificate",
            "htt_posterior",
            "local_global_disposition",
            "family_identification",
            "native_solver_result",
            "bayes_factor",
        }
    )


def test_pr311_does_not_import_invalidated_pr151_producers() -> None:
    combined = SCIENCE.read_text(encoding="utf-8") + WORKER.read_text(encoding="utf-8")
    assert "desi_dipole_mock_significance" not in combined
    assert "desi_exact_selection_card" not in combined
    assert "desi_official_mock_card.json" not in combined
    assert "docs/generated/desi_dipole_card.json" not in combined


def test_pr317_current_raw_schema_stops_before_observed_statistic(worker) -> None:
    report = worker.classify_existing_raw_compatibility(
        observed_columns={"RA", "DEC", "Z", "WEIGHT", "flux_r_dered"},
        ezmock_columns={"RA", "DEC", "Z", "WEIGHT", "NX"},
        abacus_columns={
            "RA",
            "DEC",
            "Z",
            "WEIGHT",
            "R_MAG_APP",
            "R_MAG_ABS",
        },
        random_window_keys={"NGC", "SGC", "nside", "zmin", "zmax"},
        random_window_cap_shape=(12 * 64 * 64,),
    )

    assert report["terminal_disposition"] == (
        "BLOCKED_EXISTING_RAW_INSUFFICIENT_FOR_PR311"
    )
    assert report["blockers"] == [
        "OBSERVED_ROW_MAGNITUDE_EVIDENCE_UNAVAILABLE",
        "EZMOCK_ROW_MAGNITUDE_EVIDENCE_UNAVAILABLE",
        "TOMOGRAPHIC_RANDOM_WINDOW_UNAVAILABLE",
    ]
    assert report["observed_statistic_seen"] is False
    assert report["observed_science_executed"] is False
    assert report["p_value"] is None
    assert report["forced_source_label"] is None


def test_pr317_hypothetical_complete_schema_is_not_blocked(worker) -> None:
    magnitude_columns = {
        "RA",
        "DEC",
        "Z",
        "WEIGHT",
        "R_MAG_APP",
        "R_MAG_ABS",
    }
    report = worker.classify_existing_raw_compatibility(
        observed_columns=magnitude_columns,
        ezmock_columns=magnitude_columns,
        abacus_columns=magnitude_columns,
        random_window_keys={
            "NGC",
            "SGC",
            "nside",
            "zmin",
            "zmax",
            "tomography_edges",
        },
        random_window_cap_shape=(3, 12 * 64 * 64),
    )

    assert report["terminal_disposition"] == "RAW_SCHEMA_COMPATIBLE_WITH_PR311"
    assert report["blockers"] == []
    assert report["observed_statistic_seen"] is False
