"""PR-310 HSC/KiDS typed spin-2 and joint-rank contracts."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import yaml


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
        redshift=np.asarray(
            ([0.4, 0.6, 0.8, 1.0] if survey == "HSC" else [0.2, 0.4, 0.6, 0.8])
            if q_values.size == 4
            else [0.4] * q_values.size
        ),
        weights=weights,
        sky_xy_radians=(
            np.asarray([[0.0, 0.0], [0.2, 0.1], [0.5, 0.4], [0.8, 0.7]])
            if q_values.size == 4
            else np.zeros((q_values.size, 2))
        ),
    )


def _provider_matrix(rows: int = 4) -> np.ndarray:
    row = np.arange(rows, dtype=float)[:, None]
    mode = np.arange(rows, dtype=float)[None, :]
    nonlocal_basis = np.sqrt(2.0 / rows) * np.cos(
        math.pi * (row + 0.5) * mode / rows
    )
    nonlocal_basis[:, 0] /= math.sqrt(2.0)
    c = 1.0 / math.sqrt(2.0)
    return np.block(
        [
            [c * nonlocal_basis, c * nonlocal_basis],
            [-c * nonlocal_basis, c * nonlocal_basis],
        ]
    )


def _labelled(module, survey: str):
    return module.label_eb(
        _raw(module, survey),
        provider_matrix=_provider_matrix(),
        provider_id=f"{survey.lower()}-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )


def _tomography(module, survey: str):
    identity = _survey_identity(module, survey)
    return module.execute_tomography(
        _labelled(module, survey),
        n_z_weights=np.asarray([1.0, 1.2, 0.9, 1.1]),
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7]),
        flat_sky_wavevector=(2.0, 1.0),
        bins=(
            module.TomographyBin(
                survey_id=survey,
                bin_index=0,
                bin_id=f"{survey.lower()}-z0",
                z_min=(0.3 if survey == "HSC" else 0.1),
                z_max=(0.7 if survey == "HSC" else 0.5),
                n_z_id=f"{identity.n_z_component}:{survey.lower()}-z0",
                calibration_id=f"{identity.calibration_component}:{survey.lower()}-z0",
                response_id=(
                    f"{identity.calibration_component}:{identity.calibration_role}:"
                    f"{survey.lower()}-z0"
                ),
                shear_calibration_factor=1.01,
                response_factor=0.99,
            ),
            module.TomographyBin(
                survey_id=survey,
                bin_index=1,
                bin_id=f"{survey.lower()}-z1",
                z_min=(0.7 if survey == "HSC" else 0.5),
                z_max=(1.2 if survey == "HSC" else 0.9),
                n_z_id=f"{identity.n_z_component}:{survey.lower()}-z1",
                calibration_id=f"{identity.calibration_component}:{survey.lower()}-z1",
                response_id=(
                    f"{identity.calibration_component}:{identity.calibration_role}:"
                    f"{survey.lower()}-z1"
                ),
                shear_calibration_factor=0.98,
                response_factor=1.02,
            ),
        ),
    )


def _operator(module, feature_order: tuple[str, ...]):
    size = len(feature_order)
    mixing = np.eye(size)
    for index in range(size):
        mixing[index, (index + 1) % size] = 0.04
    pure_e = np.asarray([name.endswith(":EE") for name in feature_order], dtype=float)
    pure_b = np.asarray([name.endswith(":BB") for name in feature_order], dtype=float)
    return module.PseudoClOperator.build(
        operator_id="pseudo-cl-current-stack-v1",
        mask_id="nontrivial-synthetic-mask-v1",
        feature_order=feature_order,
        mixing_matrix=mixing,
        inverse_matrix=np.linalg.inv(mixing),
        pure_e_pseudo_response=mixing @ pure_e,
        pure_b_pseudo_response=mixing @ pure_b,
    )


def _joint_case(module):
    hsc = _tomography(module, "HSC")
    kids = _tomography(module, "KiDS")
    hsc_operator = _operator(module, hsc.feature_order)
    kids_operator = _operator(module, kids.feature_order)
    hsc_features = hsc_operator.deconvolve(hsc.pseudo_features)
    kids_features = kids_operator.deconvolve(kids.pseudo_features)
    count = len(hsc_features)
    rng = np.random.default_rng(20260825)
    sample_count = 64
    shared = rng.normal(size=(sample_count, 4))
    hsc_null = shared @ rng.normal(size=(4, count)) + rng.normal(
        scale=0.35, size=(sample_count, count)
    )
    kids_null = shared @ rng.normal(size=(4, count)) + rng.normal(
        scale=0.35, size=(sample_count, count)
    )
    realization_ids = tuple(
        f"synthetic-same-sky-{index:03d}" for index in range(sample_count)
    )
    evidence = module.derive_paired_same_sky_joint_covariance(
        hsc_null_features=hsc_null,
        kids_null_features=kids_null,
        hsc_feature_order=hsc.feature_order,
        kids_feature_order=kids.feature_order,
        hsc_feature_units=("dimensionless_shear_squared",) * count,
        kids_feature_units=("dimensionless_shear_squared",) * count,
        hsc_normalization_ids=tuple(
            f"{name}:SYNTHETIC_PSEUDO_CL_V1" for name in hsc.feature_order
        ),
        kids_normalization_ids=tuple(
            f"{name}:SYNTHETIC_PSEUDO_CL_V1" for name in kids.feature_order
        ),
        hsc_realization_ids=realization_ids,
        kids_realization_ids=realization_ids,
        realization_source_identity="synthetic-paired-same-sky-null-v1",
        sky_realization_role="PAIRED_SAME_SKY_COSMIC_REALIZATION",
        overlap_support_identity="synthetic-common-overlap-support-v1",
        hsc_operator_identity="hsc-pseudo-cl-current-stack-v1",
        kids_operator_identity="kids-pseudo-cl-current-stack-v1",
    )
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
        "hsc_null": hsc_null,
        "kids_null": kids_null,
        "realization_ids": realization_ids,
        "covariance_evidence": evidence,
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
    baseline = worker.analyze_documents(
        baseline_documents, execution_mode="SYNTHETIC_PROFILE"
    )

    calibration_changed = json.loads(json.dumps(baseline_documents))
    calibration_changed["hsc_shear_calibration"]["component_correction"] = [
        1.25,
        1.25,
        1.25,
        1.25,
    ]
    recalibrated = worker.analyze_documents(
        calibration_changed, execution_mode="SYNTHETIC_PROFILE"
    )
    assert recalibrated["typed_feature_vectors"]["HSC"] != baseline[
        "typed_feature_vectors"
    ]["HSC"]
    assert recalibrated["typed_feature_vectors"]["KiDS"] == baseline[
        "typed_feature_vectors"
    ]["KiDS"]

    psf_changed = json.loads(json.dumps(baseline_documents))
    psf_changed["hsc_psf"]["additive_gamma1"] = [0.1, 0.1, 0.1, 0.1]
    corrected = worker.analyze_documents(
        psf_changed, execution_mode="SYNTHETIC_PROFILE"
    )
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
    with pytest.raises(module.HscKidsCurrentStackError, match="normalized nonlocal"):
        module.label_eb(
            raw,
            provider_matrix=2.0 * np.eye(8),
            provider_id="scaled-raw-alias",
            output_order="E_THEN_B",
        )
    with pytest.raises(TypeError):
        module.LabelledEBField(
            identity=raw.identity,
            e_mode=raw.gamma1,
            b_mode=raw.gamma2,
            bin_index=raw.bin_index,
            redshift=raw.redshift,
            weights=raw.weights,
            provider_id="constructor-bypass",
        )
    assert not hasattr(module.LabelledEBField, "_from_provider")
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
        redshift=raw.redshift[permutation],
        weights=raw.weights[permutation],
        sky_xy_radians=raw.sky_xy_radians[permutation],
    )
    labelled = module.label_eb(
        permuted,
        provider_matrix=_provider_matrix()[
            np.r_[permutation, permutation + 4]
        ][:, np.r_[permutation, permutation + 4]],
        provider_id="hsc-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )
    replay = module.execute_tomography(
        labelled,
        bins=baseline.bins,
        n_z_weights=np.asarray([1.0, 1.2, 0.9, 1.1])[permutation],
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7])[permutation],
        flat_sky_wavevector=baseline.flat_sky_wavevector,
    )
    np.testing.assert_allclose(replay.pseudo_features, baseline.pseudo_features)

    changed = module.RawSpin2Field(
        identity=raw.identity,
        gamma1=raw.gamma1,
        gamma2=raw.gamma2,
        bin_index=np.asarray([0, 1, 1, 1]),
        redshift=np.asarray([0.4, 0.8, 0.9, 1.0]),
        weights=raw.weights,
        sky_xy_radians=raw.sky_xy_radians,
    )
    changed_labelled = module.label_eb(
        changed,
        provider_matrix=_provider_matrix(),
        provider_id="hsc-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )
    changed_result = module.execute_tomography(
        changed_labelled,
        bins=baseline.bins,
        n_z_weights=np.asarray([1.0, 1.2, 0.9, 1.1]),
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7]),
        flat_sky_wavevector=baseline.flat_sky_wavevector,
    )
    assert not np.allclose(changed_result.pseudo_features, baseline.pseudo_features)


def test_pr310_tomography_rejects_survey_nz_or_response_exchange() -> None:
    module = _science()
    labelled = _labelled(module, "HSC")
    bins = list(_tomography(module, "HSC").bins)
    bins[0] = module.TomographyBin(
        **{**bins[0].__dict__, "n_z_id": "kids-nz-0"}
    )
    with pytest.raises(module.HscKidsCurrentStackError, match="survey-specific"):
        module.execute_tomography(
            labelled,
            bins=tuple(bins),
            n_z_weights=np.ones(4),
            mask_weights=np.ones(4),
            flat_sky_wavevector=(2.0, 1.0),
        )


def test_pr310_tomography_nz_calibration_and_response_are_executable() -> None:
    module = _science()
    baseline = _tomography(module, "HSC")
    bins = list(baseline.bins)
    bins[0] = module.TomographyBin(
        **{**bins[0].__dict__, "response_factor": 0.77}
    )
    changed = module.execute_tomography(
        _labelled(module, "HSC"),
        bins=tuple(bins),
        n_z_weights=np.asarray([1.0, 1.2, 0.9, 1.1]),
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7]),
        flat_sky_wavevector=baseline.flat_sky_wavevector,
    )
    assert not np.allclose(changed.pseudo_features, baseline.pseudo_features)
    changed_nz = module.execute_tomography(
        _labelled(module, "HSC"),
        bins=baseline.bins,
        n_z_weights=np.asarray([2.0, 0.5, 0.9, 1.1]),
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7]),
        flat_sky_wavevector=baseline.flat_sky_wavevector,
    )
    assert not np.allclose(changed_nz.pseudo_features, baseline.pseudo_features)


def test_pr310_pseudo_cl_recovers_both_pure_modes_under_nontrivial_mask() -> None:
    module = _science()
    tomography = _tomography(module, "HSC")
    operator = _operator(module, tomography.feature_order)

    oracle = operator.pure_mode_oracle()
    recovered = operator.deconvolve(tomography.pseudo_features)

    assert oracle["pure_e_to_b_max_abs"] <= 1.0e-14
    assert oracle["pure_b_to_e_max_abs"] <= 1.0e-14
    assert oracle["status"] == "TWO_WAY_PURE_MODE_PASS"
    assert np.any(np.abs(operator.mixing_matrix - np.eye(len(recovered))) > 0.0)


def test_pr310_pure_mode_oracle_is_independent_of_coupling_inverse() -> None:
    module = _science()
    tomography = _tomography(module, "HSC")
    operator = _operator(module, tomography.feature_order)
    drifted = operator.mixing_matrix.copy()
    drifted[1, 0] += 0.25
    with pytest.raises(module.HscKidsCurrentStackError, match="pure-mode"):
        module.PseudoClOperator.build(
            operator_id="drifted",
            mask_id="same-injection-oracle",
            feature_order=tomography.feature_order,
            mixing_matrix=drifted,
            inverse_matrix=np.linalg.inv(drifted),
            pure_e_pseudo_response=operator.pure_e_pseudo_response,
            pure_b_pseudo_response=operator.pure_b_pseudo_response,
        ).pure_mode_oracle()


def test_pr310_pseudo_cl_rejects_feature_order_and_mask_inverse_drift() -> None:
    module = _science()
    tomography = _tomography(module, "HSC")
    operator = _operator(module, tomography.feature_order)

    with pytest.raises(module.HscKidsCurrentStackError, match="feature order"):
        operator.deconvolve(
            tomography.pseudo_features,
            feature_order=tuple(reversed(tomography.feature_order)),
        )
    with pytest.raises(module.HscKidsCurrentStackError, match="mask-coupling"):
        module.PseudoClOperator.build(
            operator_id="broken",
            mask_id="nontrivial",
            feature_order=tomography.feature_order,
            mixing_matrix=operator.mixing_matrix,
            inverse_matrix=np.eye(len(tomography.feature_order)),
            pure_e_pseudo_response=operator.pure_e_pseudo_response,
            pure_b_pseudo_response=operator.pure_b_pseudo_response,
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
    assert module.transported_headless_axis_alignment(
        start=np.asarray([1.0, 0.0, 0.0]),
        end=np.asarray([0.0, 1.0, 0.0]),
        left_tangent=np.asarray([0.0, 1.0, 0.0]),
        right_tangent=-transported,
    ) == 1.0

    with pytest.raises(module.HscKidsCurrentStackError, match="antipodal"):
        module.parallel_transport_axis(
            start=np.asarray([1.0, 0.0, 0.0]),
            end=np.asarray([-1.0, 0.0, 0.0]),
            tangent=np.asarray([0.0, 1.0, 0.0]),
        )


def test_pr320_paired_same_sky_covariance_matches_joint_sample_covariance() -> None:
    module = _science()
    case = _joint_case(module)
    evidence = case["covariance_evidence"]
    expected = np.cov(
        np.column_stack([case["hsc_null"], case["kids_null"]]),
        rowvar=False,
        ddof=1,
    )

    np.testing.assert_allclose(evidence.joint_covariance, expected, rtol=0.0, atol=1.0e-12)
    assert evidence.sample_count == 64
    assert evidence.centering_rule == "JOINT_SAMPLE_MEAN"
    assert evidence.denominator_rule == "N_MINUS_ONE"
    assert evidence.sky_realization_role == "PAIRED_SAME_SKY_COSMIC_REALIZATION"


def test_pr320_covariance_evidence_cannot_be_directly_constructed() -> None:
    module = _science()
    case = _joint_case(module)

    with pytest.raises(TypeError):
        module.PairedSameSkyJointCovariance(
            **case["covariance_evidence"].__dict__
        )
    with pytest.raises(ValueError):
        case["covariance_evidence"].joint_covariance[0, 0] = 0.0


def test_pr320_missing_cross_information_abstains_before_rank() -> None:
    module = _science()
    case = _joint_case(module)

    result = module.analyze_joint_response(
        hsc_features=case["hsc_features"],
        kids_features=case["kids_features"],
        hsc_feature_order=case["hsc"].feature_order,
        kids_feature_order=case["kids"].feature_order,
        joint_covariance_evidence=None,
        nuisance_response=case["nuisance"],
        candidate_response=case["candidate"],
        response_feature_order=(*case["hsc"].feature_order, *case["kids"].feature_order),
        observed=False,
    )
    assert result["terminal_disposition"] == "NON_IDENTIFIED_CROSS_SURVEY_COVARIANCE"
    assert result["response_rank"] is None
    assert result["p_value"] is None
    assert result["forced_source_label"] is None


def test_pr320_paired_realization_order_mismatch_is_rejected() -> None:
    module = _science()
    case = _joint_case(module)
    with pytest.raises(module.HscKidsCurrentStackError, match="realization IDs"):
        module.derive_paired_same_sky_joint_covariance(
            hsc_null_features=case["hsc_null"],
            kids_null_features=case["kids_null"],
            hsc_feature_order=case["hsc"].feature_order,
            kids_feature_order=case["kids"].feature_order,
            hsc_feature_units=("dimensionless",) * case["hsc_null"].shape[1],
            kids_feature_units=("dimensionless",) * case["kids_null"].shape[1],
            hsc_normalization_ids=case["hsc"].feature_order,
            kids_normalization_ids=case["kids"].feature_order,
            hsc_realization_ids=case["realization_ids"],
            kids_realization_ids=tuple(reversed(case["realization_ids"])),
            realization_source_identity="synthetic-paired-same-sky-null-v1",
            sky_realization_role="PAIRED_SAME_SKY_COSMIC_REALIZATION",
            overlap_support_identity="synthetic-common-overlap-support-v1",
            hsc_operator_identity="hsc-pseudo-cl-current-stack-v1",
            kids_operator_identity="kids-pseudo-cl-current-stack-v1",
        )


def test_pr320_feature_unit_shape_drift_is_rejected() -> None:
    module = _science()
    case = _joint_case(module)
    with pytest.raises(module.HscKidsCurrentStackError, match="feature units length"):
        module.derive_paired_same_sky_joint_covariance(
            hsc_null_features=case["hsc_null"],
            kids_null_features=case["kids_null"],
            hsc_feature_order=case["hsc"].feature_order,
            kids_feature_order=case["kids"].feature_order,
            hsc_feature_units=("dimensionless",),
            kids_feature_units=("dimensionless",) * case["kids_null"].shape[1],
            hsc_normalization_ids=case["hsc"].feature_order,
            kids_normalization_ids=case["kids"].feature_order,
            hsc_realization_ids=case["realization_ids"],
            kids_realization_ids=case["realization_ids"],
            realization_source_identity="synthetic-paired-same-sky-null-v1",
            sky_realization_role="PAIRED_SAME_SKY_COSMIC_REALIZATION",
            overlap_support_identity="synthetic-common-overlap-support-v1",
            hsc_operator_identity="hsc-pseudo-cl-current-stack-v1",
            kids_operator_identity="kids-pseudo-cl-current-stack-v1",
        )


def test_pr320_evidenced_zero_cross_block_is_not_missing_information() -> None:
    module = _science()
    evidence = module.derive_paired_same_sky_joint_covariance(
        hsc_null_features=np.asarray([[-1.0], [-1.0], [1.0], [1.0]]),
        kids_null_features=np.asarray([[-1.0], [1.0], [-1.0], [1.0]]),
        hsc_feature_order=("HSC:h0",),
        kids_feature_order=("KiDS:k0",),
        hsc_feature_units=("dimensionless",),
        kids_feature_units=("dimensionless",),
        hsc_normalization_ids=("HSC:h0:norm-v1",),
        kids_normalization_ids=("KiDS:k0:norm-v1",),
        hsc_realization_ids=("r0", "r1", "r2", "r3"),
        kids_realization_ids=("r0", "r1", "r2", "r3"),
        realization_source_identity="orthogonal-paired-null-v1",
        sky_realization_role="PAIRED_SAME_SKY_COSMIC_REALIZATION",
        overlap_support_identity="common-support-v1",
        hsc_operator_identity="hsc-op-v1",
        kids_operator_identity="kids-op-v1",
    )
    result = module.analyze_joint_response(
        hsc_features=[0.0],
        kids_features=[0.0],
        hsc_feature_order=("HSC:h0",),
        kids_feature_order=("KiDS:k0",),
        joint_covariance_evidence=evidence,
        nuisance_response=[[1.0], [0.0]],
        candidate_response=[[0.0], [1.0]],
        response_feature_order=("HSC:h0", "KiDS:k0"),
        observed=False,
    )
    assert result["joint_covariance"]["cross_block_evidenced"] is True
    assert result["joint_covariance"]["cross_block_zero"] is True
    assert result["response_rank"]["status"] == "LOCAL_STRUCTURAL_FULL_INCREMENTAL_RANK"


def test_pr320_psd_singular_joint_covariance_stops_before_whitening() -> None:
    module = _science()
    evidence = module.derive_paired_same_sky_joint_covariance(
        hsc_null_features=[[-1.0], [1.0]],
        kids_null_features=[[-2.0], [2.0]],
        hsc_feature_order=("HSC:h0",),
        kids_feature_order=("KiDS:k0",),
        hsc_feature_units=("dimensionless",),
        kids_feature_units=("dimensionless",),
        hsc_normalization_ids=("HSC:h0:norm-v1",),
        kids_normalization_ids=("KiDS:k0:norm-v1",),
        hsc_realization_ids=("r0", "r1"),
        kids_realization_ids=("r0", "r1"),
        realization_source_identity="rank-one-paired-null-v1",
        sky_realization_role="PAIRED_SAME_SKY_COSMIC_REALIZATION",
        overlap_support_identity="common-support-v1",
        hsc_operator_identity="hsc-op-v1",
        kids_operator_identity="kids-op-v1",
    )
    result = module.analyze_joint_response(
        hsc_features=[0.0],
        kids_features=[0.0],
        hsc_feature_order=("HSC:h0",),
        kids_feature_order=("KiDS:k0",),
        joint_covariance_evidence=evidence,
        nuisance_response=[[1.0], [0.0]],
        candidate_response=[[0.0], [1.0]],
        response_feature_order=("HSC:h0", "KiDS:k0"),
        observed=False,
    )
    assert result["terminal_disposition"] == "COVARIANCE_VALID_WHITENING_UNAVAILABLE"
    assert result["joint_covariance"]["status"] == "PAIRED_SAME_SKY_JOINT_COVARIANCE_VALID"
    assert result["response_rank"] is None


def test_pr310_rank_is_scale_stable_and_overlap_abstains() -> None:
    module = _science()
    case = _joint_case(module)
    baseline = module.analyze_joint_response(
        hsc_features=case["hsc_features"],
        kids_features=case["kids_features"],
        hsc_feature_order=case["hsc"].feature_order,
        kids_feature_order=case["kids"].feature_order,
        joint_covariance_evidence=case["covariance_evidence"],
        nuisance_response=case["nuisance"],
        candidate_response=case["candidate"],
        response_feature_order=(*case["hsc"].feature_order, *case["kids"].feature_order),
        observed=False,
    )
    assert baseline["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"
    for scale in (1.0e-12, 1.0e-6, 1.0e6, 1.0e12):
        result = module.analyze_joint_response(
            hsc_features=case["hsc_features"],
            kids_features=case["kids_features"],
            hsc_feature_order=case["hsc"].feature_order,
            kids_feature_order=case["kids"].feature_order,
            joint_covariance_evidence=case["covariance_evidence"],
            nuisance_response=case["nuisance"],
            candidate_response=scale * case["candidate"],
            response_feature_order=(*case["hsc"].feature_order, *case["kids"].feature_order),
            observed=False,
        )
        assert result["response_rank"]["status"] == "LOCAL_STRUCTURAL_FULL_INCREMENTAL_RANK"
        assert result["response_rank"]["incremental_rank"] == 2

    overlap = np.column_stack([case["nuisance"][:, 0], case["nuisance"][:, 0]])
    result = module.analyze_joint_response(
        hsc_features=case["hsc_features"],
        kids_features=case["kids_features"],
        hsc_feature_order=case["hsc"].feature_order,
        kids_feature_order=case["kids"].feature_order,
        joint_covariance_evidence=case["covariance_evidence"],
        nuisance_response=case["nuisance"],
        candidate_response=overlap,
        response_feature_order=(*case["hsc"].feature_order, *case["kids"].feature_order),
        observed=False,
    )
    assert result["terminal_disposition"] == "NON_IDENTIFIED_ABSTAIN"
    assert result["p_value"] is None
    assert result["forced_source_label"] is None


def test_pr310_response_rows_are_bound_to_exact_feature_order() -> None:
    module = _science()
    case = _joint_case(module)
    order = (*case["hsc"].feature_order, *case["kids"].feature_order)
    with pytest.raises(module.HscKidsCurrentStackError, match="response feature order"):
        module.analyze_joint_response(
            hsc_features=case["hsc_features"],
            kids_features=case["kids_features"],
            hsc_feature_order=case["hsc"].feature_order,
            kids_feature_order=case["kids"].feature_order,
            joint_covariance_evidence=case["covariance_evidence"],
            nuisance_response=case["nuisance"][::-1],
            candidate_response=case["candidate"][::-1],
            response_feature_order=tuple(reversed(order)),
            observed=False,
        )


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
    ):
        assert forbidden not in encoded
    assert "family_identification" in result["artifact_metadata"]["forbidden_uses"]
    assert result["p_value"] is None
    assert result["forced_source_label"] is None


def test_pr310_observed_mode_requires_admission_context_and_flags_are_monotone() -> None:
    worker = _worker()
    documents = worker._synthetic_documents()
    with pytest.raises(worker.HscKidsWorkerError, match="admission context"):
        worker.analyze_documents(documents, execution_mode="ADMITTED_OBSERVED")

    mutated = json.loads(json.dumps(documents))
    mutated["hsc_kids_cross_covariance"] = {
        **mutated["hsc_kids_cross_covariance"],
        "covariance_branch": "CROSS_INFORMATION_ABSENT",
    }
    result = worker.analyze_documents(
        mutated,
        execution_mode="ADMITTED_OBSERVED",
        admission_context={
            "lane_admission_bundle_id": "sha256:" + "1" * 64,
            "ordered_record_ids": ["sha256:" + "2" * 64],
        },
    )
    assert result["terminal_disposition"] == "NON_IDENTIFIED_CROSS_SURVEY_COVARIANCE"
    assert result["observed_statistic_seen"] is True
    assert result["observed_science_executed"] is True


def test_pr320_legacy_arbitrary_cross_matrix_has_no_covariance_authority() -> None:
    worker = _worker()
    documents = json.loads(json.dumps(worker._synthetic_documents()))
    cross = documents["hsc_kids_cross_covariance"]
    size = len(cross["hsc_feature_order"])
    cross["covariance_branch"] = "LEGACY_ARBITRARY_MATRIX"
    cross["matrix"] = (0.08 * np.eye(size)).tolist()

    result = worker.analyze_documents(documents, execution_mode="SYNTHETIC_PROFILE")
    assert result["terminal_disposition"] == "NON_IDENTIFIED_CROSS_SURVEY_COVARIANCE"
    assert result["joint_covariance"]["cross_block_evidenced"] is False
    assert result["response_rank"] is None


def test_pr310_result_metadata_is_truthful_and_proportional() -> None:
    result = _worker().synthetic_profile(rows="1")
    metadata = result["artifact_metadata"]
    assert metadata["owner"] == "OBSSTAT"
    assert metadata["artifact_mode"] == "synthetic_operator_diagnostic"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["null_mock_status"] == "PAIRED_SAME_SKY_SYNTHETIC_NULLS_BOUND"
    assert metadata["covariance_status"] == "PAIRED_SAME_SKY_JOINT_COVARIANCE_VALID"
    assert metadata["public_use"] is False
    assert metadata["allowed_use"] == "internal_operator_validation"
    assert "family_identification" in metadata["forbidden_uses"]
    assert metadata["source_releases"] == {
        "HSC": "HSC_S19A_Y3",
        "KiDS": "KIDS_1000_DR4_1",
    }


def test_pr310_pseudo_power_consumes_sky_coordinates_and_fourier_mode() -> None:
    module = _science()
    raw = _raw(module, "HSC")
    sky = np.asarray([[0.0, 0.0], [0.2, 0.1], [0.5, 0.4], [0.8, 0.7]])
    positioned = module.RawSpin2Field(**{**raw.__dict__, "sky_xy_radians": sky})
    labelled = module.label_eb(
        positioned,
        provider_matrix=_provider_matrix(),
        provider_id="hsc-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )
    baseline = _tomography(module, "HSC")
    measured = module.execute_tomography(
        labelled,
        bins=baseline.bins,
        n_z_weights=np.asarray([1.0, 1.2, 0.9, 1.1]),
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7]),
        flat_sky_wavevector=(2.0, 1.0),
    )
    shifted_sky = sky.copy()
    shifted_sky[1, 0] += 0.13
    shifted = module.RawSpin2Field(**{**raw.__dict__, "sky_xy_radians": shifted_sky})
    shifted_labelled = module.label_eb(
        shifted,
        provider_matrix=_provider_matrix(),
        provider_id="hsc-registered-nonlocal-eb-v1",
        output_order="E_THEN_B",
    )
    changed = module.execute_tomography(
        shifted_labelled,
        bins=baseline.bins,
        n_z_weights=np.asarray([1.0, 1.2, 0.9, 1.1]),
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7]),
        flat_sky_wavevector=(2.0, 1.0),
    )
    different_mode = module.execute_tomography(
        labelled,
        bins=baseline.bins,
        n_z_weights=np.asarray([1.0, 1.2, 0.9, 1.1]),
        mask_weights=np.asarray([1.0, 0.8, 0.9, 0.7]),
        flat_sky_wavevector=(3.0, 1.0),
    )
    assert measured.flat_sky_wavevector == (2.0, 1.0)
    assert all(":k=2,1:" in name for name in measured.feature_order)
    assert not np.allclose(measured.pseudo_features, changed.pseudo_features)
    assert not np.allclose(measured.pseudo_features, different_mode.pseudo_features)


def test_pr310_worker_rebinds_exact_attended_admission(monkeypatch) -> None:
    worker = _worker()
    raw = b'{"admission":"A"}'
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
        "HTT_ATTENDED_ORDERED_RECORD_IDS_SHA256",
        worker.canonical_sha256(record_ids),
    )
    worker._validate_attended_admission_binding(raw, decision)
    monkeypatch.setenv("HTT_ATTENDED_ADMISSION_SHA256", "sha256:" + "0" * 64)
    with pytest.raises(worker.HscKidsWorkerError, match="acceptance binding"):
        worker._validate_attended_admission_binding(raw, decision)


def test_pr310_dispatcher_passes_acceptance_bound_admission_environment(
    tmp_path: Path,
) -> None:
    dispatcher = _load("pr310_binding_dispatcher", DISPATCHER)
    profile = dispatcher._lane_profile("HSC_KIDS")
    environment = dispatcher._environment(
        tmp_path,
        profile=profile,
        science=True,
        candidate_root=ROOT,
        candidate_commit="a" * 40,
        candidate_tree="b" * 40,
        runtime_contract={"import_roots": [str(tmp_path)]},
        admission_sha256="sha256:" + "1" * 64,
        admission_bundle_id="sha256:" + "2" * 64,
        ordered_record_ids_sha256="sha256:" + "3" * 64,
    )
    assert environment["HTT_ATTENDED_ADMISSION_SHA256"] == "sha256:" + "1" * 64
    assert environment["HTT_ATTENDED_ADMISSION_BUNDLE_ID"] == "sha256:" + "2" * 64
    assert (
        environment["HTT_ATTENDED_ORDERED_RECORD_IDS_SHA256"]
        == "sha256:" + "3" * 64
    )


def _pr321_sacc_payload(module):
    tracer_order = ("wl_0", "wl_1", "wl_2", "wl_3")
    tracer_pairs = tuple(
        (left, right)
        for left_index, left in enumerate(tracer_order)
        for right in tracer_order[left_index:]
    )
    ell = (
        150.0,
        250.0,
        350.0,
        500.0,
        700.0,
        900.0,
        1200.0,
        1600.0,
        2000.0,
        2600.0,
        3400.0,
        4200.0,
        5400.0,
        7000.0,
        8600.0,
        11000.0,
        14200.0,
    )
    tracer_z = tuple(np.linspace(0.0, 3.0, 8) for _ in tracer_order)
    tracer_nz = tuple(
        np.exp(-0.5 * ((z - mean) / 0.35) ** 2)
        for z, mean in zip(tracer_z, (0.5, 0.8, 1.1, 1.4), strict=True)
    )
    return {
        "data_type": "cl_ee",
        "tracer_order": tracer_order,
        "tracer_quantities": ("galaxy_shear",) * 4,
        "tracer_z": tracer_z,
        "tracer_nz": tracer_nz,
        "tracer_pairs": tracer_pairs,
        "ell_by_pair": (ell,) * 10,
        "window_shapes": ((15274, 17),) * 10,
        "window_column_sums": (tuple(np.ones(17)),) * 10,
        "window_support_sha256_float64_le": "1" * 64,
        "window_weight_sha256_float64_le": "2" * 64,
        "window_support_identical_across_pairs": True,
        "window_weight_pair_count": 10,
        "data_vector": np.linspace(1.0e-10, 2.0e-9, 170),
        "covariance": np.diag(np.linspace(1.0e-24, 2.0e-22, 170)),
        "loader_version": "2.1.2",
        "legacy_stored_order": True,
        "legacy_order_crosscheck": {
            "row_values_match_payload_mean": True,
            "pair_blocks_contiguous": True,
            "pair_selection_indices_match": True,
            "pair_selection_values_match": True,
            "covariance_selection_indices_match": True,
        },
        "observed_payload_validated": True,
    }


def test_pr321_requires_and_binds_four_nz_tracers() -> None:
    module = _science()
    payload = _pr321_sacc_payload(module)
    result = module.analyze_hsc_released_sacc(**payload)

    binding = result["source_redshift_distributions"]
    assert list(binding) == list(payload["tracer_order"])
    for row, z, nz in zip(
        binding.values(), payload["tracer_z"], payload["tracer_nz"], strict=True
    ):
        assert row["z_sha256"] == hashlib.sha256(
            np.asarray(z, dtype="<f8").tobytes()
        ).hexdigest()
        assert row["nz_sha256"] == hashlib.sha256(
            np.asarray(nz, dtype="<f8").tobytes()
        ).hexdigest()
        assert row["sample_count"] == 8
        expected_integral = np.sum(np.diff(z) * (nz[:-1] + nz[1:]) / 2.0)
        assert row["integral_raw"] == pytest.approx(expected_integral)

    missing = _pr321_sacc_payload(module)
    missing["tracer_nz"] = missing["tracer_nz"][:3]
    with pytest.raises(module.HscKidsCurrentStackError, match="N\\(z\\).*four"):
        module.analyze_hsc_released_sacc(**missing)

    nonpositive = _pr321_sacc_payload(module)
    nonpositive["tracer_nz"] = (
        np.zeros(8),
        *nonpositive["tracer_nz"][1:],
    )
    with pytest.raises(module.HscKidsCurrentStackError, match="N\\(z\\).*positive"):
        module.analyze_hsc_released_sacc(**nonpositive)


def test_pr321_generated_result_conforms_expected_result_schema() -> None:
    expected = yaml.safe_load(
        (
            ROOT
            / "docs/codex_handoff/pr321_reaudit/EXPECTED_RESULT_SCHEMA.yaml"
        ).read_text(encoding="utf-8")
    )
    actual = json.loads(
        (ROOT / "docs/generated/pr321_hsc_sacc_result.json").read_text(
            encoding="utf-8"
        )
    )

    def require_expected_shape(expected_value, actual_value, path: str) -> None:
        if isinstance(expected_value, dict):
            assert isinstance(actual_value, dict), f"{path} must be an object"
            for key, child in expected_value.items():
                assert key in actual_value, f"missing required result path {path}.{key}"
                require_expected_shape(child, actual_value[key], f"{path}.{key}")
            return
        if expected_value == "<derived>":
            assert actual_value is not None, f"{path} must contain a derived value"
            return
        assert actual_value == expected_value, f"{path} drifted"

    require_expected_shape(expected, actual, "result")


def test_pr321_fiducial_indices_and_covariance_slice() -> None:
    module = _science()
    payload = _pr321_sacc_payload(module)
    result = module.analyze_hsc_released_sacc(**payload)

    expected_indices = [
        pair_index * 17 + band_index
        for pair_index in range(10)
        for band_index in range(2, 8)
    ]
    vector = np.asarray(payload["data_vector"], dtype="<f8")[expected_indices]
    covariance = np.asarray(payload["covariance"], dtype="<f8")[
        np.ix_(expected_indices, expected_indices)
    ]
    fiducial = result["fiducial_selection"]
    assert fiducial["selection_id"] == "HSC_Y3_DALAL23_300_LT_ELL_LT_1800_V1"
    assert fiducial["ell_min_exclusive"] == 300.0
    assert fiducial["ell_max_exclusive"] == 1800.0
    assert fiducial["retained_bin_indices_per_pair"] == list(range(2, 8))
    assert fiducial["retained_ell_centres"] == [
        350.0, 500.0, 700.0, 900.0, 1200.0, 1600.0
    ]
    assert fiducial["ordered_index_sha256"] == hashlib.sha256(
        np.asarray(expected_indices, dtype="<i8").tobytes()
    ).hexdigest()
    assert fiducial["vector_size"] == 60
    assert fiducial["data_vector_sha256_float64_le"] == hashlib.sha256(
        vector.tobytes()
    ).hexdigest()
    assert fiducial["covariance_shape"] == [60, 60]
    assert fiducial["covariance_sha256_float64_le"] == hashlib.sha256(
        covariance.tobytes()
    ).hexdigest()
    assert fiducial["rank"] == 60
    assert fiducial["minimum_eigenvalue"] > 0.0
    assert result["terminal_disposition"] == (
        "READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE"
    )


def test_pr321_legacy_order_crosschecks_mean_pair_api_and_covariance() -> None:
    module = _science()
    payload = _pr321_sacc_payload(module)
    result = module.analyze_hsc_released_sacc(**payload)
    assert result["legacy_order_crosscheck"] == {
        "status": "INDEPENDENT_SACC_API_CROSSCHECK_PASS",
        **payload["legacy_order_crosscheck"],
    }

    for key in payload["legacy_order_crosscheck"]:
        drifted = _pr321_sacc_payload(module)
        drifted["legacy_order_crosscheck"] = {
            **drifted["legacy_order_crosscheck"],
            key: False,
        }
        with pytest.raises(module.HscKidsCurrentStackError, match="ordering crosscheck"):
            module.analyze_hsc_released_sacc(**drifted)


def test_pr321_sacc_is_scalar_tomographic_control_not_directional_mes_input() -> None:
    module = _science()
    result = module.analyze_hsc_released_sacc(**_pr321_sacc_payload(module))
    boundary = result["directional_and_MES_boundary"]
    assert boundary == {
        "directional_support_status": (
            "NONE_COMPRESSED_ROTATION_INVARIANT_POWER_SPECTRA"
        ),
        "MES_methodology_role": "SCALAR_TOMOGRAPHIC_CONTROL_ONLY",
        "vector_tensor_moment_eligibility": (
            "FORBIDDEN_NO_DIRECTION_INDEXED_FIELD"
        ),
        "local_boost_global_tilt_eligibility": (
            "NOT_APPLICABLE_NO_DIRECTIONAL_RESPONSE"
        ),
        "CMB_MES_anchor_compatibility": (
            "BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER"
        ),
    }


def test_pr321_rejects_cmb_mes_anchor_without_channel_matched_transfer() -> None:
    module = _science()
    result = module.analyze_hsc_released_sacc(**_pr321_sacc_payload(module))
    boundary = result["directional_and_MES_boundary"]
    assert (
        boundary["CMB_MES_anchor_compatibility"]
        == "BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER"
    )
    assert result["artifact_metadata"]["transfer_source"] == "none"
    assert result["response_rank"]["rank"] is None


def test_pr321_status_urls_are_bound_to_correct_internal_prs() -> None:
    status = (ROOT / "docs/codex_handoff/pr_status.yaml").read_text(encoding="utf-8")
    mirror = (ROOT / "machine_readable/pr_status.yaml").read_text(encoding="utf-8")
    assert status == mirror
    pr289 = status[status.index("    PR-289:") : status.index("    PR-290:")]
    pr321 = status[status.index("    PR-321:") : status.index("execution_lane:")]
    assert "https://github.com/cosmosapjw-quantum/htt_base/pull/386" in pr289
    assert "https://github.com/cosmosapjw-quantum/htt_base/pull/412" in pr321
    assert (
        "data_readiness: "
        "READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE"
    ) in pr321


def test_pr321_semantic_scope_replaces_false_loc_cap() -> None:
    spec = (ROOT / "docs/research_program/post_pr275/pr321_spec.yaml").read_text(
        encoding="utf-8"
    )
    delta = (ROOT / "docs/PR_DELTAS/pr-321.md").read_text(encoding="utf-8")
    combined = spec + "\n" + delta
    assert "semantic_boundary:" in spec
    assert "exact_allowlist:" in spec
    assert "generated_and_mirror_paths:" in spec
    assert "net additions at most 700" not in combined
    assert "new_science_modules_max: 0" in spec


def test_pr321_hsc_sacc_contract_is_hsc_only_and_covariance_bound() -> None:
    module = _science()
    result = module.analyze_hsc_released_sacc(**_pr321_sacc_payload(module))

    assert result["terminal_disposition"] == (
        "READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE"
    )
    assert result["full_release"]["vector_size"] == 170
    assert result["covariance"]["rank"] == 170
    assert result["window_operator"]["pair_count"] == 10
    assert result["window_operator"]["bandpowers_per_pair"] == 17
    assert result["window_operator"]["window_support_sha256_float64_le"] == "1" * 64
    assert result["window_operator"]["window_weight_sha256_float64_le"] == "2" * 64
    assert result["reference_status"] == "FIDUCIAL_REFERENCE_VECTOR_STILL_REQUIRED"
    assert result["observed_state"] == {
        "observed_payload_validated": True,
        "observed_released_data_vector_parsed": True,
        "observed_summary_statistic_present": True,
        "observed_statistic_seen": True,
        "htt_derived_statistic_computed": False,
        "observed_science_inference_executed": False,
    }
    assert result["response_rank"]["status"] == "NOT_EVALUATED"
    assert result["response_rank"]["rank"] is None
    metadata = result["artifact_metadata"]
    assert (metadata["transfer_source"], metadata["null_mock_status"]) == (
        "none", "NOT_PROVIDED_NOT_EVALUATED")
    assert metadata["unit_status"] == "SACC_NATIVE_CL_EE_NO_CONVERSION"
    assert metadata["response_rank_status"] == "NOT_EVALUATED"
    assert len(metadata["caveats"]) == 4
    assert result["p_value"] is None
    assert result["source_label"] is None
    assert result["family_identification"] == "FORBIDDEN"
    assert "KiDS" not in json.dumps(result)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("data_type", "cl_bb", "E-mode"),
        ("tracer_order", ("wl_1", "wl_0", "wl_2", "wl_3"), "tracer order"),
        ("legacy_stored_order", False, "stored row order"),
    ],
)
def test_pr321_hsc_sacc_rejects_release_semantic_drift(
    field: str, value: object, message: str
) -> None:
    module = _science()
    payload = _pr321_sacc_payload(module)
    payload[field] = value
    with pytest.raises(module.HscKidsCurrentStackError, match=message):
        module.analyze_hsc_released_sacc(**payload)


def test_pr321_hsc_sacc_rejects_missing_window_or_covariance_support() -> None:
    module = _science()
    payload = _pr321_sacc_payload(module)
    payload["window_shapes"] = ((15274, 17),) * 9
    with pytest.raises(module.HscKidsCurrentStackError, match="window"):
        module.analyze_hsc_released_sacc(**payload)

    payload = _pr321_sacc_payload(module)
    payload["window_weight_sha256_float64_le"] = "not-a-digest"
    with pytest.raises(module.HscKidsCurrentStackError, match="window weights"):
        module.analyze_hsc_released_sacc(**payload)

    payload = _pr321_sacc_payload(module)
    payload["window_weight_pair_count"] = 9
    with pytest.raises(module.HscKidsCurrentStackError, match="window identity"):
        module.analyze_hsc_released_sacc(**payload)

    payload = _pr321_sacc_payload(module)
    payload["covariance"] = np.ones((170, 170))
    with pytest.raises(module.HscKidsCurrentStackError, match="positive definite"):
        module.analyze_hsc_released_sacc(**payload)


def test_pr321_worker_rejects_input_drift_before_sacc_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = _worker()
    source = tmp_path / "hsc.sacc"
    source.write_bytes(b"not-the-frozen-sacc")
    loaded = False

    def forbidden(_path: Path):
        nonlocal loaded
        loaded = True
        raise AssertionError("SACC payload loaded before identity rejection")

    monkeypatch.setattr(worker, "_load_hsc_sacc", forbidden)
    with pytest.raises(worker.HscKidsWorkerError, match="identity"):
        worker.inspect_hsc_sacc(
            path=source,
            confirmation_sha256=worker.PR321_HSC_SACC_SHA256,
        )
    assert loaded is False


def test_pr321_worker_emits_no_observed_values_or_inference_surface(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = _worker()
    science = _science()
    source = tmp_path / "hsc.sacc"
    source.write_bytes(b"synthetic-sacc-contract")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(worker, "PR321_HSC_SACC_SHA256", digest)
    monkeypatch.setattr(worker, "PR321_HSC_SACC_SIZE", source.stat().st_size)
    monkeypatch.setattr(worker, "_load_hsc_sacc", lambda _path: _pr321_sacc_payload(science))

    result = worker.inspect_hsc_sacc(path=source, confirmation_sha256=digest)
    encoded = json.dumps(result, sort_keys=True)
    assert result["terminal_disposition"] == (
        "READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE"
    )
    assert result["input_identity"]["sha256"] == digest
    assert result["input_identity"]["byte_size"] == source.stat().st_size
    assert result["observed_state"] == {
        "observed_payload_validated": True,
        "observed_released_data_vector_parsed": True,
        "observed_summary_statistic_present": True,
        "observed_statistic_seen": True,
        "htt_derived_statistic_computed": False,
        "observed_science_inference_executed": False,
    }
    assert '"data_vector":' not in encoded
    assert '"likelihood"' not in encoded
    assert '"posterior"' not in encoded
    assert '"KiDS"' not in encoded


def test_pr321_worker_binds_hash_and_parse_to_one_open_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = _worker()
    science = _science()
    source = tmp_path / "hsc.sacc"
    original = b"frozen-sacc-bytes"
    replacement = b"changed-sacc-byte"
    assert len(original) == len(replacement)
    source.write_bytes(original)
    digest = hashlib.sha256(original).hexdigest()
    monkeypatch.setattr(worker, "PR321_HSC_SACC_SHA256", digest)
    monkeypatch.setattr(worker, "PR321_HSC_SACC_SIZE", len(original))

    parsed_bytes = []
    def replace_path_then_load(source_input: object):
        staged = tmp_path / "replacement.sacc"
        staged.write_bytes(replacement)
        staged.replace(source)
        parsed_bytes.append(
            source_input.getvalue() if hasattr(source_input, "getvalue")
            else Path(source_input).read_bytes()
        )
        return _pr321_sacc_payload(science)
    monkeypatch.setattr(worker, "_load_hsc_sacc", replace_path_then_load)
    result = worker.inspect_hsc_sacc(path=source, confirmation_sha256=digest)
    assert parsed_bytes == [original]
    assert source.read_bytes() == replacement
    assert result["input_identity"]["sha256"] == digest


def test_pr321_loader_recognizes_the_exact_direct_legacy_order_notice() -> None:
    worker = _worker()
    notice = (
        "Warning: The FITS format without the 'sacc_ordering' column is deprecated\n"
        "Assuming data rows are in the correct order as it was before version 1.0.\n"
    )
    assert worker._legacy_sacc_order_notice(notice) is True
    assert worker._legacy_sacc_order_notice("") is False
    assert worker._legacy_sacc_order_notice("unrelated loader output\n") is False
