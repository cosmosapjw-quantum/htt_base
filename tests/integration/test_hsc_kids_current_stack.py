"""PR-310 HSC/KiDS typed spin-2 and joint-rank contracts."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCIENCE = ROOT / "htt/obsstat/hsc_kids_current_stack.py"
WORKER = ROOT / "scripts/observed_runs/run_hsc_kids.py"
DISPATCHER = ROOT / "scripts/codex_harness/run_authorized_observational_program.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _science():
    return _load("pr310_hsc_kids_science", SCIENCE)


def _worker():
    return _load("pr310_hsc_kids_worker", WORKER)


def _survey_identity(module, survey: str):
    prefix = "hsc" if survey == "HSC" else "kids"
    calibration_role = (
        "multiplicative_shear_calibration"
        if survey == "HSC"
        else "lensfit_shear_response"
    )
    calibration_component = (
        "hsc_shear_calibration" if survey == "HSC" else "kids_shear_response"
    )
    return module.SurveyIdentity(
        survey_id=survey,
        release_id=("HSC_S19A_Y3" if survey == "HSC" else "KIDS_1000_DR4_1"),
        product_component=f"{prefix}_product",
        mask_component=f"{prefix}_mask",
        randoms_component=f"{prefix}_randoms",
        psf_component=f"{prefix}_psf",
        n_z_component=f"{prefix}_n_z",
        calibration_component=calibration_component,
        covariance_component=f"{prefix}_covariance",
        calibration_role=calibration_role,
        component_order="GAMMA1_THEN_GAMMA2",
        tangent_basis="RIGHT_HANDED_NORTH_EAST_SKY",
        spin_convention="PASSIVE_EXP_MINUS_2I_PSI",
    )


def _raw(module, survey: str, *, q=None, u=None, bins=None):
    q_values = np.asarray(q if q is not None else [1.0, 0.4, -0.3, 0.2])
    u_values = np.asarray(u if u is not None else [0.2, -0.5, 0.7, -0.1])
    weights = (
        np.asarray([1.0, 2.0, 1.5, 0.5])
        if q_values.size == 4
        else np.ones(q_values.size)
    )
    return module.RawSpin2Field(
        identity=_survey_identity(module, survey),
        gamma1=q_values,
        gamma2=u_values,
        bin_index=np.asarray(bins if bins is not None else [0, 0, 1, 1]),
        weights=weights,
    )


def _provider_matrix(rows: int = 4) -> np.ndarray:
    c = 1.0 / math.sqrt(2.0)
    identity = np.eye(rows)
    return np.block([[c * identity, c * identity], [-c * identity, c * identity]])


def _labelled(module, survey: str):
    return module.label_eb(
        _raw(module, survey),
        provider_matrix=_provider_matrix(),
        provider_id=f"{survey.lower()}-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )


def _tomography(module, survey: str):
    return module.execute_tomography(
        _labelled(module, survey),
        bins=(
            module.TomographyBin(
                survey_id=survey,
                bin_index=0,
                bin_id=f"{survey.lower()}-z0",
                z_min=(0.3 if survey == "HSC" else 0.1),
                z_max=(0.7 if survey == "HSC" else 0.5),
                n_z_id=f"{survey.lower()}-nz-0",
                calibration_id=f"{survey.lower()}-cal-0",
                response_id=f"{survey.lower()}-response-0",
            ),
            module.TomographyBin(
                survey_id=survey,
                bin_index=1,
                bin_id=f"{survey.lower()}-z1",
                z_min=(0.7 if survey == "HSC" else 0.5),
                z_max=(1.2 if survey == "HSC" else 0.9),
                n_z_id=f"{survey.lower()}-nz-1",
                calibration_id=f"{survey.lower()}-cal-1",
                response_id=f"{survey.lower()}-response-1",
            ),
        ),
    )


def _operator(module, feature_order: tuple[str, ...]):
    size = len(feature_order)
    mixing = np.eye(size)
    for index in range(size):
        mixing[index, (index + 1) % size] = 0.04
    return module.PseudoClOperator.build(
        operator_id="pseudo-cl-current-stack-v1",
        mask_id="nontrivial-synthetic-mask-v1",
        feature_order=feature_order,
        mixing_matrix=mixing,
        inverse_matrix=np.linalg.inv(mixing),
    )


def _joint_case(module):
    hsc = _tomography(module, "HSC")
    kids = _tomography(module, "KiDS")
    hsc_operator = _operator(module, hsc.feature_order)
    kids_operator = _operator(module, kids.feature_order)
    hsc_features = hsc_operator.apply(hsc.true_features)
    kids_features = kids_operator.apply(kids.true_features)
    count = len(hsc_features)
    hsc_covariance = 1.8 * np.eye(count)
    kids_covariance = 1.5 * np.eye(count)
    cross_covariance = 0.08 * np.eye(count)
    joint_features = np.concatenate([hsc_features, kids_features])
    x = np.linspace(-1.0, 1.0, joint_features.size)
    nuisance = np.column_stack([np.ones_like(x), x])
    candidate = np.column_stack([np.sin(1.7 * x), np.cos(2.3 * x)])
    return {
        "hsc": hsc,
        "kids": kids,
        "hsc_operator": hsc_operator,
        "kids_operator": kids_operator,
        "hsc_features": hsc_features,
        "kids_features": kids_features,
        "hsc_covariance": hsc_covariance,
        "kids_covariance": kids_covariance,
        "cross_covariance": cross_covariance,
        "nuisance": nuisance,
        "candidate": candidate,
    }


def test_pr310_rejects_exchanged_survey_components() -> None:
    module = _science()
    hsc = _survey_identity(module, "HSC")
    kids = _survey_identity(module, "KiDS")
    module.validate_survey_pair(hsc, kids)

    swapped = module.SurveyIdentity(
        **{**hsc.__dict__, "psf_component": kids.psf_component}
    )
    with pytest.raises(module.HscKidsCurrentStackError, match="HSC.*psf"):
        module.validate_survey_pair(swapped, kids)

    swapped = module.SurveyIdentity(
        **{**kids.__dict__, "n_z_component": hsc.n_z_component}
    )
    with pytest.raises(module.HscKidsCurrentStackError, match="KiDS.*n_z"):
        module.validate_survey_pair(hsc, swapped)


def test_pr310_worker_applies_survey_specific_psf_and_calibration() -> None:
    worker = _worker()
    baseline_documents = worker._synthetic_documents()
    baseline = worker.analyze_documents(baseline_documents, observed=False)

    calibration_changed = json.loads(json.dumps(baseline_documents))
    calibration_changed["hsc_shear_calibration"]["component_correction"] = [
        1.25,
        1.25,
        1.25,
        1.25,
    ]
    recalibrated = worker.analyze_documents(calibration_changed, observed=False)
    assert recalibrated["typed_feature_vectors"]["HSC"] != baseline[
        "typed_feature_vectors"
    ]["HSC"]
    assert recalibrated["typed_feature_vectors"]["KiDS"] == baseline[
        "typed_feature_vectors"
    ]["KiDS"]

    psf_changed = json.loads(json.dumps(baseline_documents))
    psf_changed["hsc_psf"]["additive_gamma1"] = [0.1, 0.1, 0.1, 0.1]
    corrected = worker.analyze_documents(psf_changed, observed=False)
    assert corrected["typed_feature_vectors"]["HSC"] != baseline[
        "typed_feature_vectors"
    ]["HSC"]


def test_pr310_spin2_rotation_uses_passive_double_angle() -> None:
    module = _science()
    raw = _raw(module, "HSC", q=[1.0], u=[0.0], bins=[0])

    quarter_turn = module.rotate_raw_components(raw, math.pi / 4.0)
    half_turn = module.rotate_raw_components(raw, math.pi / 2.0)
    full_turn = module.rotate_raw_components(raw, math.pi)

    np.testing.assert_allclose(quarter_turn.gamma1, [0.0], atol=1.0e-14)
    np.testing.assert_allclose(quarter_turn.gamma2, [-1.0], atol=1.0e-14)
    np.testing.assert_allclose(half_turn.gamma1, [-1.0], atol=1.0e-14)
    np.testing.assert_allclose(half_turn.gamma2, [0.0], atol=1.0e-14)
    np.testing.assert_allclose(full_turn.gamma1, [1.0], atol=1.0e-14)
    np.testing.assert_allclose(full_turn.gamma2, [0.0], atol=1.0e-14)


def test_pr310_raw_pair_cannot_be_relabelled_as_eb() -> None:
    module = _science()
    raw = _raw(module, "HSC")

    with pytest.raises(module.HscKidsCurrentStackError, match="raw.*E/B"):
        module.label_eb(
            raw,
            provider_matrix=np.eye(8),
            provider_id="raw-alias",
            output_order="E_THEN_B",
        )
    with pytest.raises(module.HscKidsCurrentStackError, match="output order"):
        module.label_eb(
            raw,
            provider_matrix=_provider_matrix(),
            provider_id="wrong-order",
            output_order="B_THEN_E",
        )


def test_pr310_tomography_executes_and_is_row_permutation_invariant() -> None:
    module = _science()
    baseline = _tomography(module, "HSC")
    raw = _raw(module, "HSC")
    permutation = np.asarray([2, 0, 3, 1])
    permuted = module.RawSpin2Field(
        identity=raw.identity,
        gamma1=raw.gamma1[permutation],
        gamma2=raw.gamma2[permutation],
        bin_index=raw.bin_index[permutation],
        weights=raw.weights[permutation],
    )
    labelled = module.label_eb(
        permuted,
        provider_matrix=_provider_matrix()[
            np.r_[permutation, permutation + 4]
        ][:, np.r_[permutation, permutation + 4]],
        provider_id="hsc-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )
    replay = module.execute_tomography(labelled, bins=baseline.bins)
    np.testing.assert_allclose(replay.true_features, baseline.true_features)

    changed = module.RawSpin2Field(
        identity=raw.identity,
        gamma1=raw.gamma1,
        gamma2=raw.gamma2,
        bin_index=np.asarray([0, 1, 1, 1]),
        weights=raw.weights,
    )
    changed_labelled = module.label_eb(
        changed,
        provider_matrix=_provider_matrix(),
        provider_id="hsc-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )
    changed_result = module.execute_tomography(changed_labelled, bins=baseline.bins)
    assert not np.allclose(changed_result.true_features, baseline.true_features)


def test_pr310_tomography_rejects_survey_nz_or_response_exchange() -> None:
    module = _science()
    labelled = _labelled(module, "HSC")
    bins = list(_tomography(module, "HSC").bins)
    bins[0] = module.TomographyBin(
        **{**bins[0].__dict__, "n_z_id": "kids-nz-0"}
    )
    with pytest.raises(module.HscKidsCurrentStackError, match="survey-specific"):
        module.execute_tomography(labelled, bins=tuple(bins))


def test_pr310_pseudo_cl_recovers_both_pure_modes_under_nontrivial_mask() -> None:
    module = _science()
    tomography = _tomography(module, "HSC")
    operator = _operator(module, tomography.feature_order)

    oracle = operator.pure_mode_oracle()
    recovered = operator.apply(tomography.true_features)

    assert oracle["pure_e_to_b_max_abs"] <= 1.0e-14
    assert oracle["pure_b_to_e_max_abs"] <= 1.0e-14
    assert oracle["status"] == "TWO_WAY_PURE_MODE_PASS"
    np.testing.assert_allclose(recovered, tomography.true_features, atol=1.0e-12)
    assert np.any(np.abs(operator.mixing_matrix - np.eye(len(recovered))) > 0.0)


def test_pr310_pseudo_cl_rejects_feature_order_and_mask_inverse_drift() -> None:
    module = _science()
    tomography = _tomography(module, "HSC")
    operator = _operator(module, tomography.feature_order)

    with pytest.raises(module.HscKidsCurrentStackError, match="feature order"):
        operator.apply(
            tomography.true_features,
            feature_order=tuple(reversed(tomography.feature_order)),
        )
    with pytest.raises(module.HscKidsCurrentStackError, match="mask-coupling"):
        module.PseudoClOperator.build(
            operator_id="broken",
            mask_id="nontrivial",
            feature_order=tomography.feature_order,
            mixing_matrix=operator.mixing_matrix,
            inverse_matrix=np.eye(len(tomography.feature_order)),
        )


def test_pr310_shortest_geodesic_transport_and_headless_axis() -> None:
    module = _science()
    transported = module.parallel_transport_axis(
        start=np.asarray([1.0, 0.0, 0.0]),
        end=np.asarray([0.0, 1.0, 0.0]),
        tangent=np.asarray([0.0, 1.0, 0.0]),
    )
    np.testing.assert_allclose(transported, [-1.0, 0.0, 0.0], atol=1.0e-14)
    recovered = module.parallel_transport_axis(
        start=np.asarray([0.0, 1.0, 0.0]),
        end=np.asarray([1.0, 0.0, 0.0]),
        tangent=transported,
    )
    np.testing.assert_allclose(recovered, [0.0, 1.0, 0.0], atol=1.0e-14)
    assert module.headless_axis_alignment(transported, -transported) == 1.0

    with pytest.raises(module.HscKidsCurrentStackError, match="antipodal"):
        module.parallel_transport_axis(
            start=np.asarray([1.0, 0.0, 0.0]),
            end=np.asarray([-1.0, 0.0, 0.0]),
            tangent=np.asarray([0.0, 1.0, 0.0]),
        )


@pytest.mark.parametrize("mutation", ("missing", "zero", "asymmetric", "indefinite"))
def test_pr310_joint_covariance_abstains_before_rank(mutation: str) -> None:
    module = _science()
    case = _joint_case(module)
    cross = case["cross_covariance"].copy()
    hsc = case["hsc_covariance"].copy()
    if mutation == "missing":
        cross = None
    elif mutation == "zero":
        cross[:] = 0.0
    elif mutation == "asymmetric":
        hsc[0, 1] = 0.4
    else:
        hsc[0, 0] = -1.0

    result = module.analyze_joint_response(
        hsc_features=case["hsc_features"],
        kids_features=case["kids_features"],
        hsc_feature_order=case["hsc"].feature_order,
        kids_feature_order=case["kids"].feature_order,
        hsc_covariance=hsc,
        kids_covariance=case["kids_covariance"],
        cross_covariance=cross,
        nuisance_response=case["nuisance"],
        candidate_response=case["candidate"],
        observed=False,
    )
    assert result["terminal_disposition"] == "JOINT_COVARIANCE_REQUIRED_ABSTAIN"
    assert result["response_rank"] is None
    assert result["p_value"] is None
    assert result["forced_source_label"] is None


def test_pr310_rank_is_scale_stable_and_overlap_abstains() -> None:
    module = _science()
    case = _joint_case(module)
    baseline = module.analyze_joint_response(
        hsc_features=case["hsc_features"],
        kids_features=case["kids_features"],
        hsc_feature_order=case["hsc"].feature_order,
        kids_feature_order=case["kids"].feature_order,
        hsc_covariance=case["hsc_covariance"],
        kids_covariance=case["kids_covariance"],
        cross_covariance=case["cross_covariance"],
        nuisance_response=case["nuisance"],
        candidate_response=case["candidate"],
        observed=False,
    )
    assert baseline["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"
    for scale in (1.0e-12, 1.0e-6, 1.0e6, 1.0e12):
        result = module.analyze_joint_response(
            hsc_features=case["hsc_features"],
            kids_features=case["kids_features"],
            hsc_feature_order=case["hsc"].feature_order,
            kids_feature_order=case["kids"].feature_order,
            hsc_covariance=case["hsc_covariance"],
            kids_covariance=case["kids_covariance"],
            cross_covariance=case["cross_covariance"],
            nuisance_response=case["nuisance"],
            candidate_response=scale * case["candidate"],
            observed=False,
        )
        assert result["response_rank"]["status"] == "FULL_INCREMENTAL_RANK"
        assert result["response_rank"]["incremental_rank"] == 2

    overlap = np.column_stack([case["nuisance"][:, 0], case["nuisance"][:, 0]])
    result = module.analyze_joint_response(
        hsc_features=case["hsc_features"],
        kids_features=case["kids_features"],
        hsc_feature_order=case["hsc"].feature_order,
        kids_feature_order=case["kids"].feature_order,
        hsc_covariance=case["hsc_covariance"],
        kids_covariance=case["kids_covariance"],
        cross_covariance=case["cross_covariance"],
        nuisance_response=case["nuisance"],
        candidate_response=overlap,
        observed=False,
    )
    assert result["terminal_disposition"] == "NON_IDENTIFIED_ABSTAIN"
    assert result["p_value"] is None
    assert result["forced_source_label"] is None


@pytest.mark.parametrize("rows", ("1", "8", "32", "128", "full"))
def test_pr310_synthetic_profiles_are_observation_free(rows: str) -> None:
    worker = _worker()
    result = worker.synthetic_profile(rows=rows)

    assert result["row_label"] == rows
    assert result["row_count"] == worker.PROFILE_ROWS[rows]
    assert result["observed_statistic_seen"] is False
    assert result["observed_science_executed"] is False
    assert result["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"
    assert result["max_rss_bytes"] > 0


def test_pr310_synthetic_cli_rejects_admission_and_data_root(tmp_path: Path) -> None:
    worker = _worker()
    output = tmp_path / "synthetic.json"

    assert worker.main(
        [
            "--synthetic-profile",
            "--rows",
            "1",
            "--admission",
            str(tmp_path / "admission.json"),
            "--data-root",
            str(tmp_path),
            "--output",
            str(output),
        ]
    ) == 2
    assert not output.exists()


def test_pr310_rootless_or_partial_admission_stops_before_data_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = _worker()
    opened = False

    def forbidden() -> None:
        nonlocal opened
        opened = True
        raise AssertionError("observed data open attempted")

    monkeypatch.setattr(worker, "_mark_observed_data_open_attempt", forbidden)
    admission = tmp_path / "admission.json"
    admission.write_text(json.dumps({"lane_id": "HSC_KIDS"}), encoding="utf-8")

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


def test_pr310_dispatcher_registers_one_exact_hsc_kids_profile() -> None:
    dispatcher = _load("pr310_dispatcher", DISPATCHER)
    profile = dispatcher._lane_profile("HSC_KIDS")

    assert profile.analysis_plan_id == "plan:PR292-HSC-KIDS-SPIN2-V1"
    assert profile.science_worker_relative == "scripts/observed_runs/run_hsc_kids.py"
    assert profile.science_worker_arguments == ("--run-admitted",)
    assert profile.result_filename == "hsc_kids_result.json"
    for forbidden in ("--all", "CROSS_PROBE", "HSC", "KiDS"):
        with pytest.raises(dispatcher.ObservationalProgramError):
            dispatcher._lane_profile(forbidden)


def test_pr310_synthetic_output_has_no_inference_or_family_surface() -> None:
    worker = _worker()
    result = worker.synthetic_profile(rows="8")
    encoded = json.dumps(result, sort_keys=True).lower()

    for forbidden in (
        '"prior"',
        '"likelihood"',
        '"posterior"',
        '"evidence"',
        '"bayes_factor"',
        '"x_c"',
        '"q_policy"',
        '"pi_exceedance"',
        '"g_f"',
        '"family_identification"',
    ):
        assert forbidden not in encoded
    assert result["p_value"] is None
    assert result["forced_source_label"] is None
