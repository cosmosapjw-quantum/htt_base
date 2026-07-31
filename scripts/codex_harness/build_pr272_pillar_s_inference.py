#!/usr/bin/env python3
"""Build the deterministic PR-272 synthetic validation registry."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[2]
for source_root in (ROOT, ROOT / "htt/src", ROOT / "htt"):
    value = str(source_root)
    if value not in sys.path:
        sys.path.insert(0, value)

from common.sbc_ppc import (  # noqa: E402
    GaussianModel,
    run_sbc,
    sbc_lineage_hash,
    sbc_verdict,
)
from common.vector_tensor_statistical_inference import (  # noqa: E402
    CLAIM_CEILING,
    EXPECTED_SPEC_SHA256,
    ModelCandidate,
    SourceDisposition,
    ValidationStatus,
    build_joint_anchor_law,
    build_mio_depth_cross_check,
    calibrate_split_max_statistic,
    derive_seed,
    evaluate_depth_local_global,
    evaluate_depth_multiplicity,
    evaluate_joint_anchor_coverage,
    evaluate_matched_counterpair_power,
    evaluate_open_set_validation,
    evaluate_registered_composition,
    evaluate_weak_identification,
    load_preregistered_design,
)
from common.weak_id_coverage import (  # noqa: E402
    bonferroni_conf,
    clopper_pearson_lower,
    coverage_at_point,
)


OUTPUT = (
    ROOT
    / "docs/research_program/vector_tensor/proofs/"
    "PILLAR_S_INFERENCE_VALIDATION_V1.yaml"
)


def _jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Fraction):
        return str(value)
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    if hasattr(value, "as_payload"):
        return _jsonable(value.as_payload())
    if hasattr(value, "__dataclass_fields__"):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()


def _rng(master_seed: int, cell_id: str, family: str) -> np.random.Generator:
    return np.random.Generator(
        np.random.PCG64(derive_seed(master_seed, cell_id, family))
    )


def _verify_frozen_inputs(design: dict) -> None:
    for name, record in design["frozen_inputs"].items():
        path = ROOT / record["path"]
        actual = _sha256(path)
        if actual != record["sha256"]:
            raise RuntimeError(
                f"frozen input {name} drifted: {actual} != {record['sha256']}"
            )


def _build_s3(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["max_q"]
    dimension = int(config["dimension"])
    calibration_count = int(config["calibration_draws"])
    evaluation_count = int(config["evaluation_draws"])
    calibration = _rng(master_seed, "VT-S3", "calibration").normal(
        size=(calibration_count, dimension)
    )
    correct = _rng(master_seed, "VT-S3", "evaluation-correct").normal(
        size=(evaluation_count, dimension)
    )
    scale = math.sqrt(float(config["misspecified_evaluation_covariance_scale"]))
    misspecified = (
        _rng(master_seed, "VT-S3", "evaluation-misspecified").normal(
            size=(evaluation_count, dimension)
        )
        * scale
    )
    confidence = design["preregistration"]["confidence"]
    common = dict(
        alpha=float(config["alpha"]),
        family_confidence=float(confidence["family_confidence"]),
        retain_lower_bound=float(confidence["retain_lower_bound"]),
        calibration_covariance_id="identity-v1",
    )
    correct_report = calibrate_split_max_statistic(
        calibration,
        correct,
        evaluation_covariance_id="identity-v1",
        **common,
    )
    misspecified_report = calibrate_split_max_statistic(
        calibration,
        misspecified,
        evaluation_covariance_id="scaled-1.5625-v1",
        **common,
    )
    return {
        "correct": _jsonable(correct_report),
        "misspecified_covariance_negative_control": _jsonable(
            misspecified_report
        ),
        "misspecified_failure_preserved": (
            misspecified_report.status
            is ValidationStatus.FAILED_MISSPECIFIED_COVARIANCE
            and misspecified_report.simultaneous_coverage
            < float(config["misspecified_failure_upper_coverage"])
        ),
    }


def _build_s5(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["partial_identification"]
    confidence = design["preregistration"]["confidence"]
    grid = tuple(float(value) for value in config["width_grid"])
    per_point_confidence = bonferroni_conf(
        float(confidence["family_confidence"]), len(grid)
    )
    rows = []
    for index, width in enumerate(grid):
        row = coverage_at_point(
            width,
            "imbens_manski",
            n_replicates=int(config["delivered_replicates_per_grid_point"]),
            seeds=int(config["independent_seed_streams"]),
            base_seed=derive_seed(
                master_seed, f"VT-S5-{index}", "registered-coverage"
            ),
            w_key=str(width),
            s=float(config["sigma"]),
            theta0_position=str(config["least_favourable_position"]),
        )
        row["family_wise_lower"] = clopper_pearson_lower(
            int(row["covered"]),
            int(row["delivered_replicates"]),
            per_point_confidence,
        )
        rows.append(row)
    adversarial = coverage_at_point(
        grid[0],
        str(config["adversarial_method"]),
        n_replicates=int(config["delivered_replicates_per_grid_point"]),
        seeds=int(config["independent_seed_streams"]),
        base_seed=derive_seed(master_seed, "VT-S5-naive", "negative-control"),
        w_key=str(grid[0]),
        s=float(config["sigma"]),
        theta0_position=str(config["least_favourable_position"]),
    )
    adversarial["family_wise_lower"] = clopper_pearson_lower(
        int(adversarial["covered"]),
        int(adversarial["delivered_replicates"]),
        per_point_confidence,
    )
    retain = float(confidence["retain_lower_bound"])
    failures = [
        {
            "w": row["w"],
            "coverage": row["coverage"],
            "family_wise_lower": row["family_wise_lower"],
        }
        for row in rows
        if row["family_wise_lower"] < retain
    ]
    return {
        "registered_grid": _jsonable(rows),
        "minimum_family_wise_lower": min(
            row["family_wise_lower"] for row in rows
        ),
        "registered_failure_map": failures,
        "adversarial_failure_map": [
            _jsonable(adversarial)
        ]
        if adversarial["family_wise_lower"] < retain
        else [],
        "optimizer_output_probability_use": "REFUSED",
        "status": (
            ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC.value
            if not failures
            else ValidationStatus.FAILED_REGISTERED_COVERAGE.value
        ),
    }


def _build_s6(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["random_anchor"]
    confidence = design["preregistration"]["confidence"]
    law = build_joint_anchor_law(
        law_id="pr272-joint-random-anchor-v1",
        mean=(config["numerator_mean"], config["anchor_mean"]),
        covariance=config["joint_covariance"],
        sample_size=int(config["sample_size"]),
        joint_cross_covariance_declared=True,
    )
    covariance_of_mean = law.covariance / law.sample_size
    draws = _rng(master_seed, "VT-S6", "joint-estimator").multivariate_normal(
        mean=np.asarray(law.mean),
        cov=covariance_of_mean,
        size=int(config["evaluation_draws"]),
    )
    report = evaluate_joint_anchor_coverage(
        draws,
        law=law,
        true_ratio=float(config["true_ratio"]),
        normal_critical_value=float(config["normal_critical_value"]),
        family_confidence=float(confidence["family_confidence"]),
        retain_lower_bound=float(confidence["retain_lower_bound"]),
    )
    return {
        "joint_law_id": law.law_id,
        "joint_law_content_id": law.content_id,
        "coverage": _jsonable(report),
        "marginal_only_mutation": "REFUSED",
    }


def _build_sbc(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["sbc"]
    run_config = {
        "preregistration_sha256": EXPECTED_SPEC_SHA256,
        "cell": "PR272-SBC",
    }

    def run(scale: Fraction, family: str) -> dict:
        model = GaussianModel(
            Fraction(config["prior_variance"]),
            Fraction(config["likelihood_variance"]),
            int(config["observations"]),
            scale,
        )
        lineage = sbc_lineage_hash(model, run_config)
        result = run_sbc(
            model,
            n_simulations=int(config["simulations"]),
            n_draws=int(config["posterior_draws"]),
            seed=derive_seed(master_seed, "PR272-SBC", family),
            n_bins=int(config["rank_bins"]),
            lineage_hash=lineage,
            config=run_config,
        )
        result["verdict"] = sbc_verdict(
            result, float(config["pvalue_floor"])
        )
        return result

    good = run(Fraction(config["calibrated_variance_scale"]), "calibrated")
    bad = {
        str(value): run(Fraction(str(value)), f"misspecified-{value}")
        for value in config["misspecified_variance_scales"]
    }
    return {
        "calibrated": _jsonable(good),
        "misspecified": _jsonable(bad),
        "all_misspecified_fail": all(
            row["verdict"] == "inadequate_sbc_failed"
            for row in bad.values()
        ),
    }


def _build_s9(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["depth_multiplicity"]
    confidence = design["preregistration"]["confidence"]
    dimension = int(config["depth_count"])
    correlation = float(config["correlation"])
    covariance = np.full((dimension, dimension), correlation)
    np.fill_diagonal(covariance, 1.0)
    calibration = _rng(master_seed, "VT-S9", "calibration").multivariate_normal(
        np.zeros(dimension),
        covariance,
        size=int(config["calibration_draws"]),
    )
    evaluation = _rng(master_seed, "VT-S9", "evaluation").multivariate_normal(
        np.zeros(dimension),
        covariance,
        size=int(config["evaluation_draws"]),
    )
    report = evaluate_depth_multiplicity(
        calibration,
        evaluation,
        alpha=float(config["alpha"]),
        family_confidence=float(confidence["family_confidence"]),
        retain_lower_bound=float(confidence["retain_lower_bound"]),
        covariance_id="equicorrelated-depth-path-v1",
        same_centered_target=bool(config["same_centered_target_required"]),
        nested_path=bool(config["nested_path_required"]),
    )
    return {
        "report": _jsonable(report),
        "unadjusted_failure_preserved": (
            report.unadjusted_familywise_error_rate
            > float(config["unadjusted_failure_lower_fwer"])
        ),
    }


def _build_s10(design: dict) -> dict:
    config = design["preregistration"]["weak_identification"]
    covariance = np.eye(3)

    def response_space_pair(angle: float) -> tuple[np.ndarray, np.ndarray]:
        local = np.asarray([[1.0], [0.0], [0.0]])
        global_ = np.asarray(
            [[math.cos(angle)], [math.sin(angle)], [0.0]]
        )
        return local, global_

    well_local, well_global = response_space_pair(0.30)
    well = evaluate_weak_identification(
        np.diag(config["well_identified_singular_values"]),
        covariance,
        covariance_id="identity-response-covariance-v1",
        expected_covariance_id="identity-response-covariance-v1",
        singular_value_floor=float(config["singular_value_floor"]),
        local_response_space=well_local,
        global_response_space=well_global,
        principal_angle_floor_radians=float(
            config["principal_angle_floor_radians"]
        ),
        perturbation_radius=float(config["perturbation_radius"]),
    )
    weak_local, weak_global = response_space_pair(0.02)
    weak = evaluate_weak_identification(
        np.diag(config["weak_singular_values"]),
        covariance,
        covariance_id="identity-response-covariance-v1",
        expected_covariance_id="identity-response-covariance-v1",
        singular_value_floor=float(config["singular_value_floor"]),
        local_response_space=weak_local,
        global_response_space=weak_global,
        principal_angle_floor_radians=float(
            config["principal_angle_floor_radians"]
        ),
        perturbation_radius=float(config["perturbation_radius"]),
    )
    return {"well_identified": _jsonable(well), "weak": _jsonable(weak)}


def _build_s11(design: dict) -> dict:
    config = design["preregistration"]["composition"]
    orbit = np.eye(int(config["orbit_chart_dimension"]))
    response = np.asarray(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 1.0, 1.0]]
    )
    valid = evaluate_registered_composition(
        orbit,
        response,
        rank_tolerance=float(config["rank_tolerance"]),
        registered_linear_cell_only=True,
    )
    mutated = response.copy()
    mutated[:, 2] = 0.0
    negative = evaluate_registered_composition(
        orbit,
        mutated,
        rank_tolerance=float(config["rank_tolerance"]),
        registered_linear_cell_only=True,
    )
    return {"registered_cell": _jsonable(valid), "rank_loss": _jsonable(negative)}


def _build_s12(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["matched_counterpair"]
    count = int(config["replicates"])
    modes = int(config["modes_per_replicate"])
    dimension = int(config["feature_dimension"])
    noise = float(config["per_mode_feature_noise_sd"])

    def summaries(family: str, shift: float) -> np.ndarray:
        values = _rng(master_seed, "VT-S12", family).normal(
            loc=shift,
            scale=noise,
            size=(count, modes, dimension),
        )
        return np.mean(values, axis=1)

    report = evaluate_matched_counterpair_power(
        summaries("calibration-null", float(config["null_shift"])),
        summaries("evaluation-null", float(config["null_shift"])),
        summaries("alternative", float(config["alternative_shift"])),
        scalar_differences=np.zeros(count),
        anchor_differences=np.zeros(count),
        alpha=float(config["alpha"]),
        family_confidence=float(
            design["preregistration"]["confidence"]["family_confidence"]
        ),
        minimum_power_lower_bound=float(
            config["minimum_power_lower_bound"]
        ),
    )
    return _jsonable(report)


def _build_s13(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["open_set"]
    centres = np.asarray(config["known_centres"], dtype=float)
    noise = float(config["feature_noise_sd"])
    calibration_count = int(config["calibration_per_known_class"])
    evaluation_count = int(config["evaluation_per_known_class"])
    calibration_rows = []
    calibration_truth = []
    evaluation_rows = []
    evaluation_truth = []
    for index, centre in enumerate(centres):
        calibration_rows.append(
            _rng(master_seed, "VT-S13", f"calibration-{index}").normal(
                loc=centre, scale=noise, size=(calibration_count, len(centre))
            )
        )
        calibration_truth.extend([index] * calibration_count)
        evaluation_rows.append(
            _rng(master_seed, "VT-S13", f"evaluation-{index}").normal(
                loc=centre, scale=noise, size=(evaluation_count, len(centre))
            )
        )
        evaluation_truth.extend([index] * evaluation_count)
    unknown_centre = np.asarray(config["unknown_centre"], dtype=float)
    unknown = _rng(master_seed, "VT-S13", "unknown").normal(
        loc=unknown_centre,
        scale=noise,
        size=(int(config["evaluation_unknown"]), len(unknown_centre)),
    )
    report = evaluate_open_set_validation(
        np.vstack(calibration_rows),
        calibration_truth,
        np.vstack(evaluation_rows),
        evaluation_truth,
        unknown,
        known_centres=centres,
        alpha=float(config["alpha"]),
        family_confidence=float(
            design["preregistration"]["confidence"]["family_confidence"]
        ),
        minimum_known_coverage_lower_bound=float(
            config["minimum_known_coverage_lower_bound"]
        ),
        minimum_unknown_abstention_lower_bound=float(
            config["minimum_unknown_abstention_lower_bound"]
        ),
        thresholds_frozen_before_evaluation=True,
    )
    return _jsonable(report)


def _build_s14(design: dict, master_seed: int) -> dict:
    config = design["preregistration"]["depth_local_global"]
    confidence = design["preregistration"]["confidence"]
    covariance = np.asarray(config["covariance"], dtype=float)
    local = np.asarray(config["local_design"], dtype=float)
    global_ = np.asarray(config["global_design"], dtype=float)
    amplitude = float(config["true_amplitude"])
    count = int(config["evaluation_draws"])

    local_draws = _rng(master_seed, "VT-S14", "local").multivariate_normal(
        amplitude * local, covariance, size=count
    )
    global_draws = _rng(master_seed, "VT-S14", "global").multivariate_normal(
        amplitude * global_, covariance, size=count
    )
    correct = 0
    for row in local_draws:
        report = evaluate_depth_local_global(
            row,
            covariance=covariance,
            covariance_id="pr272-depth-covariance-v1",
            local_design=local,
            global_design=global_,
            mask_path_id=str(config["mask_path_id"]),
            transfer_source=str(config["transfer_source"]),
        )
        correct += int(report.selected_candidate is ModelCandidate.LOCAL)
    for row in global_draws:
        report = evaluate_depth_local_global(
            row,
            covariance=covariance,
            covariance_id="pr272-depth-covariance-v1",
            local_design=local,
            global_design=global_,
            mask_path_id=str(config["mask_path_id"]),
            transfer_source=str(config["transfer_source"]),
        )
        correct += int(report.selected_candidate is ModelCandidate.GLOBAL)
    total = 2 * count
    lower = clopper_pearson_lower(
        correct, total, float(confidence["family_confidence"])
    )
    local_mean_cross_check = build_mio_depth_cross_check(
        np.mean(local_draws, axis=0),
        local_design=local,
        global_design=global_,
        mask_path_id=str(config["mask_path_id"]),
    )
    global_mean_cross_check = build_mio_depth_cross_check(
        np.mean(global_draws, axis=0),
        local_design=local,
        global_design=global_,
        mask_path_id=str(config["mask_path_id"]),
    )
    minimum = float(config["minimum_correct_selection_lower_bound"])
    return {
        "status": (
            ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC.value
            if lower >= minimum
            else ValidationStatus.FAILED_REGISTERED_COVERAGE.value
        ),
        "correct_selection_count": correct,
        "evaluation_count": total,
        "correct_selection_rate": correct / total,
        "correct_selection_lower_bound": lower,
        "minimum_correct_selection_lower_bound": minimum,
        "HTT_owner": "HTT",
        "MIO_local_truth_cross_check": _jsonable(local_mean_cross_check),
        "MIO_global_truth_cross_check": _jsonable(global_mean_cross_check),
    }


def _record(
    theorem_id: str,
    status: str,
    *,
    program_obligation: bool = False,
) -> dict:
    boundaries = {
        "VT-S3": (
            "misspecified covariance remains a visible failed cell",
            "unadjusted coordinate tests are not familywise control",
        ),
        "VT-S5": (
            "uncertified interior extrema require an optimizer",
            "coverage is grid-conditional rather than class-wide",
        ),
        "VT-S6": (
            "marginals alone do not define a ratio confidence body",
            "an anchor interval crossing zero is unbounded or disconnected",
        ),
        "VT-S9": (
            "nonnested or differently centered depth paths are refused",
            "finite-path calibration does not cover a continuum of masks",
        ),
        "VT-S10": (
            "full rank below the frozen singular-value or angle floor abstains",
            "a wrong covariance identity is refused",
        ),
        "VT-S11": (
            "one registered linear cell is not global orbit separation",
            "rank loss in either factor kills composition identifiability",
        ),
        "VT-S12": (
            "power is conditional on the registered synthetic counterpair",
            "scalar or anchor mismatch invalidates the counterpair",
        ),
        "VT-S13": (
            "coverage is finite-library and split-conditional",
            "unknown cases abstain rather than receive a nearest family label",
        ),
        "VT-S14": (
            "the adapter remains synthetic pending admitted data",
            "MIO residual diagnostics do not contain likelihood or posterior",
        ),
    }
    assumptions = {
        "VT-S3": (
            "calibration and evaluation splits are independent and exchangeable",
            "the matched-null covariance identity is explicit",
        ),
        "VT-S5": (
            "the registered identified-set grid and least-favourable boundary are fixed",
            "the Imbens-Manski construction and confidence level are frozen",
        ),
        "VT-S6": (
            "the numerator-anchor pair has one registered joint Gaussian law",
            "the full covariance of the estimator mean is retained",
        ),
        "VT-S9": (
            "all rungs report one centered target on a nested finite path",
            "maximum-statistic null calibration uses an independent split",
        ),
        "VT-S10": (
            "response whitening uses the registered covariance",
            "rank, singular-value, principal-angle, and perturbation floors are fixed",
        ),
        "VT-S11": (
            "orbit chart and supported response share one declared linear cell",
            "the rank tolerance is fixed before evaluation",
        ),
        "VT-S12": (
            "scalar and anchor coordinates are exactly matched",
            "morphology summaries use the frozen modes and held-out split",
        ),
        "VT-S13": (
            "known centres, unknown generator, threshold, and split are frozen",
            "finite-library removal sensitivity is reported",
        ),
        "VT-S14": (
            "depth covariance, local/global designs, and mask path are explicit",
            "HTT owns GLS while MIO receives residual diagnostics only",
        ),
    }
    return {
        "theorem_id": theorem_id,
        "source_disposition": (
            SourceDisposition.PROGRAM_OBLIGATION_RETAINED.value
            if program_obligation
            else SourceDisposition.CONDITIONAL_PROGRAM_RETAINED.value
        ),
        "validation_status": status,
        "evidence_grade": "SIMULATION_DIAGNOSTIC",
        "evidence_path": (
            "docs/research_program/vector_tensor/proofs/"
            f"PILLAR_S_INFERENCE_VALIDATION_V1.yaml#validation_results.{theorem_id}"
        ),
        "assumptions": list(assumptions[theorem_id]),
        "counterexample_boundaries": list(boundaries[theorem_id]),
        "claim_ceiling": CLAIM_CEILING,
    }


def build_payload() -> dict:
    design = dict(load_preregistered_design(ROOT))
    _verify_frozen_inputs(design)
    master_seed = int(
        design["preregistration"]["random_stream"]["master_seed"]
    )
    seed_family = tuple(
        int(value)
        for value in design["preregistration"]["random_stream"]["seed_family"]
    )
    if len(seed_family) != len(set(seed_family)) or not seed_family:
        raise RuntimeError("PR-272 registered seed family must be nonempty and unique")
    stream_cells = (
        ("VT-S3", "calibration"),
        ("VT-S3", "evaluation-correct"),
        ("VT-S3", "evaluation-misspecified"),
        ("VT-S5-0", "registered-coverage"),
        ("VT-S5-1", "registered-coverage"),
        ("VT-S5-2", "registered-coverage"),
        ("VT-S5-3", "registered-coverage"),
        ("VT-S5-naive", "negative-control"),
        ("VT-S6", "joint-estimator"),
        ("PR272-SBC", "calibrated"),
        ("PR272-SBC", "misspecified-0.5"),
        ("PR272-SBC", "misspecified-2.0"),
        ("VT-S9", "calibration"),
        ("VT-S9", "evaluation"),
        ("VT-S12", "calibration-null"),
        ("VT-S12", "evaluation-null"),
        ("VT-S12", "alternative"),
        ("VT-S13", "calibration-0"),
        ("VT-S13", "calibration-1"),
        ("VT-S13", "evaluation-0"),
        ("VT-S13", "evaluation-1"),
        ("VT-S13", "unknown"),
        ("VT-S14", "local"),
        ("VT-S14", "global"),
    )
    derived_streams = {
        f"{cell}|{family}": derive_seed(master_seed, cell, family)
        for cell, family in stream_cells
    }
    results = {
        "VT-S3": _build_s3(design, master_seed),
        "VT-S5": _build_s5(design, master_seed),
        "VT-S6": _build_s6(design, master_seed),
        "VT-S9": _build_s9(design, master_seed),
        "VT-S10": _build_s10(design),
        "VT-S11": _build_s11(design),
        "VT-S12": _build_s12(design, master_seed),
        "VT-S13": _build_s13(design, master_seed),
        "VT-S14": _build_s14(design, master_seed),
    }
    results["SBC-HTT-COMPUTATION"] = _build_sbc(design, master_seed)

    statuses = {
        "VT-S3": results["VT-S3"]["correct"]["status"],
        "VT-S5": results["VT-S5"]["status"],
        "VT-S6": results["VT-S6"]["coverage"]["status"],
        "VT-S9": results["VT-S9"]["report"]["status"],
        "VT-S10": (
            ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC.value
            if (
                results["VT-S10"]["well_identified"]["status"]
                == ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC.value
                and results["VT-S10"]["weak"]["status"]
                == ValidationStatus.ABSTAIN_WEAK_IDENTIFICATION.value
            )
            else ValidationStatus.FAILED_REGISTERED_COVERAGE.value
        ),
        "VT-S11": results["VT-S11"]["registered_cell"]["status"],
        "VT-S12": results["VT-S12"]["status"],
        "VT-S13": results["VT-S13"]["status"],
        "VT-S14": results["VT-S14"]["status"],
    }
    records = [
        _record(
            theorem_id,
            statuses[theorem_id],
            program_obligation=theorem_id == "VT-S14",
        )
        for theorem_id in (
            "VT-S3",
            "VT-S5",
            "VT-S6",
            "VT-S9",
            "VT-S10",
            "VT-S11",
            "VT-S12",
            "VT-S13",
            "VT-S14",
        )
    ]
    return {
        "schema": "htt.pillar_s_inference_validation.v1",
        "authority": "PR-272",
        "preregistration_sha256": EXPECTED_SPEC_SHA256,
        "source_status_promoted": False,
        "observed_data_used": False,
        "native_solver_output_used": False,
        "transfer_source": "none",
        "claim_ceiling": CLAIM_CEILING,
        "raw_count_publication": "FORBIDDEN",
        "random_stream_receipt": {
            "engine": design["preregistration"]["random_stream"]["engine"],
            "derivation": design["preregistration"]["random_stream"][
                "derivation"
            ],
            "master_seed": master_seed,
            "registered_seed_family": list(seed_family),
            "derived_streams": derived_streams,
            "derived_streams_sha256": _canonical_sha256(derived_streams),
            "numpy_version": np.__version__,
        },
        "records": records,
        "canonical_records_sha256": _canonical_sha256(records),
        "validation_results": _jsonable(results),
        "validation_results_sha256": _canonical_sha256(
            _jsonable(results)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    rendered = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("PR-272 validation registry is stale")
        print("PR-272 validation registry is current")
        return
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
