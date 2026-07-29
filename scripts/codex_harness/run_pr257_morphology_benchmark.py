#!/usr/bin/env python3
"""Replay the PR-257 synthetic low-ell morphology benchmark.

The generator constructs exact same-power, same-anchor counterpairs for the
registered phase, orientation, and scalar-parity interventions.  It then runs
the frozen HTT held-out rule on synthetic representation arrays.  No observed
sky, PR-151 byte, old Rust science output, external transfer, or native solver
output is read.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT / "htt" / "src", ROOT / "htt"):
    text = str(entry)
    if text not in sys.path:
        sys.path.insert(0, text)

from common.anchor_geometry import (  # noqa: E402
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (  # noqa: E402
    anchored_numeric_content_id,
    measure_schur_morphology_information,
)
from common.transfer_registry import TransferSource  # noqa: E402
from htt.statistics.morphology_benchmark import (  # noqa: E402
    MorphologyBenchmarkProtocol,
    MorphologyBenchmarkStatus,
    MorphologyRepresentation,
    RepresentationAvailability,
    RepresentationBenchmarkInput,
    RepresentationBenchmarkStatus,
    evaluate_morphology_benchmark,
)
from obsstat.lowell_counterpairs import (  # noqa: E402
    CounterpairFactor,
    FeatureAvailability,
    InterventionOperator,
    LowEllInterventionSpec,
    MorphologyFeatureKind,
    apply_lowell_counterpair_intervention,
    build_lowell_morphology_feature_packet,
    build_matched_counterpair,
    register_morphology_feature,
)
from obsstat.lowell_poles import IMPLEMENTED_HARMONIC_CONVENTION  # noqa: E402


MASTER_SEED = 20260728
TOTAL_REPLICATES = 200_000
TRAIN_REPLICATES = 120_000
VALIDATION_REPLICATES = 40_000
HELD_OUT_REPLICATES = 40_000
UNKNOWN_REPLICATES = 40_000
MAXIMUM_REPLICATES = 400_000
MAXIMUM_MCSE = 0.0025
TARGET_SHA = "bbdabec76458d0e66187fbd2631718059f7a7c8d"
OUTPUT = (
    ROOT
    / "docs/generated/pr257_lowell_morphology/"
    "morphology_benchmark.json"
)
CAS_CONTRACT = (
    ROOT
    / "docs/generated/pr257_lowell_morphology/"
    "CAS_CONTRACT_PR257_ORBIT_V2.json"
)
GENERATION_STATE_INPUTS = (
    Path(__file__),
    ROOT / "htt/htt/htt/statistics/morphology_benchmark.py",
    ROOT / "htt/obsstat/lowell_counterpairs.py",
    ROOT / "htt/src/common/anchor_geometry.py",
    ROOT / "htt/src/common/anchored_response_geometry.py",
    ROOT / "htt/src/common/transfer_registry.py",
    ROOT / "docs/research_program/premise_anchor/pr257_spec.yaml",
    CAS_CONTRACT,
)
GENERATOR_SOURCE_ID = "sha256:" + hashlib.sha256(
    Path(__file__).read_bytes()
).hexdigest()

AVAILABLE_REPRESENTATIONS = tuple(MorphologyRepresentation)[:-2]
MISSING_REPRESENTATIONS = tuple(MorphologyRepresentation)[-2:]
REPRESENTATION_DIMENSIONS = {
    MorphologyRepresentation.SCALAR_X_C: 1,
    MorphologyRepresentation.FULL_DEPARTURE_STATE: 12,
    MorphologyRepresentation.FISHER_WHITENED_STATE: 12,
    MorphologyRepresentation.ANCHOR_COORDINATE_WITH_IDENTITY: 3,
    MorphologyRepresentation.ORBIT_CATALOGUE_V2: 12,
    MorphologyRepresentation.MULTIPOLE_POWER_TENSOR: 6,
    MorphologyRepresentation.BIPOSH: 8,
}
BASE_SIGNAL_STRENGTH = {
    MorphologyRepresentation.SCALAR_X_C: 0.0,
    MorphologyRepresentation.FULL_DEPARTURE_STATE: 0.62,
    MorphologyRepresentation.FISHER_WHITENED_STATE: 0.78,
    MorphologyRepresentation.ANCHOR_COORDINATE_WITH_IDENTITY: 0.38,
    MorphologyRepresentation.ORBIT_CATALOGUE_V2: 0.92,
    MorphologyRepresentation.MULTIPOLE_POWER_TENSOR: 0.70,
    MorphologyRepresentation.BIPOSH: 0.86,
}
FACTOR_MULTIPLIER = {
    CounterpairFactor.PHASE: 0.90,
    CounterpairFactor.ORIENTATION: 0.80,
    CounterpairFactor.PARITY: 1.00,
}
FACTOR_SEEDS = {
    CounterpairFactor.PHASE: MASTER_SEED + 10_000,
    CounterpairFactor.ORIENTATION: MASTER_SEED + 20_000,
    CounterpairFactor.PARITY: MASTER_SEED + 30_000,
}


def _receipt(role: str, descriptor: object) -> str:
    encoded = json.dumps(
        {
            "descriptor": descriptor,
            "role": role,
            "schema": "PR257_SYNTHETIC_SEMANTIC_RECEIPT_V1",
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _generation_worktree_state() -> dict[str, object]:
    inputs = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in GENERATION_STATE_INPUTS
    ]
    descriptor = {
        "base_target_sha": TARGET_SHA,
        "inputs": inputs,
        "kind": "content_addressed_precommit_worktree_inputs",
        "output_excluded_to_avoid_self_reference": (
            OUTPUT.relative_to(ROOT).as_posix()
        ),
        "schema": "PR257_GENERATION_WORKTREE_STATE_V1",
    }
    return {
        **descriptor,
        "state_sha256": _receipt("generation_worktree_state", descriptor),
    }


def _canonical_float(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("benchmark payload must contain finite floats")
    if abs(value) < 1.0e-14:
        return 0.0
    return float(f"{value:.14g}")


def _canonical(value: Any) -> Any:
    if isinstance(value, (float, np.floating)):
        return _canonical_float(float(value))
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    return value


def _normalizer() -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="PR257-SYNTHETIC-COMMON-RESPONSE-NORMALIZER",
        kind=NormalizerKind.FISHER_WHITENED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("u0",),
        coordinate_map=((1.0,),),
        source_identity="PR257-SYNTHETIC-COMMON-PARAMETERIZATION",
        assumptions=(
            "same one-dimensional diagnostic parameter across representations",
        ),
    )


def _geometry(
    *,
    factor: CounterpairFactor,
    representation: MorphologyRepresentation,
    strength: float,
    normalizer: NormalizerSpec,
):
    covariance = np.eye(2, dtype=float)
    return measure_schur_morphology_information(
        baseline_response=((1.0,),),
        morphology_response=((strength,),),
        joint_covariance=covariance,
        normalizer=normalizer,
        parameter_labels=("u0",),
        transfer_id=_receipt(
            "transfer",
            {"source": "none", "role": "synthetic_hypothesis_only"},
        ),
        transfer_source=TransferSource.NONE,
        mask_id=_receipt(
            "mask",
            {"kind": "synthetic_common_full_support", "version": 1},
        ),
        joint_covariance_id=anchored_numeric_content_id(covariance),
        baseline_observable_id=_receipt(
            "baseline_observable",
            {"kind": "common_scalar_baseline", "version": 1},
        ),
        morphology_observable_id=_receipt(
            "morphology_observable",
            {
                "factor": factor.value,
                "representation": representation.value,
                "version": 1,
            },
        ),
    )


def _balanced_targets(
    rng: np.random.Generator,
    count: int,
) -> np.ndarray:
    if count % 2:
        raise ValueError("balanced synthetic target count must be even")
    values = np.tile(np.asarray((0, 1), dtype=np.int64), count // 2)
    return rng.permutation(values)


def _split_targets(
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train = _balanced_targets(rng, TRAIN_REPLICATES)
    validation = _balanced_targets(rng, VALIDATION_REPLICATES)
    held_out = _balanced_targets(rng, HELD_OUT_REPLICATES)
    if np.array_equal(validation, held_out):
        held_out = np.roll(held_out, 1)
    return train, validation, held_out


def _direction(
    *,
    factor: CounterpairFactor,
    representation: MorphologyRepresentation,
    dimension: int,
) -> np.ndarray:
    digest = hashlib.sha256(
        f"{factor.value}:{representation.value}:direction:v1".encode("ascii")
    ).digest()
    seed = int.from_bytes(digest[:8], "big") % (2**63 - 1)
    rng = np.random.default_rng(seed)
    vector = rng.normal(size=dimension)
    return vector / np.linalg.norm(vector)


def _features(
    *,
    rng: np.random.Generator,
    targets: np.ndarray,
    direction: np.ndarray,
    strength: float,
) -> np.ndarray:
    noise = rng.normal(size=(targets.shape[0], direction.shape[0]))
    signs = 2.0 * targets.astype(float) - 1.0
    return noise + signs[:, None] * strength * direction[None, :]


def _available_input(
    *,
    factor: CounterpairFactor,
    representation: MorphologyRepresentation,
    targets: tuple[np.ndarray, np.ndarray, np.ndarray],
    partition_ids: tuple[str, str, str, str],
    seed: int,
    normalizer: NormalizerSpec,
) -> RepresentationBenchmarkInput:
    rng = np.random.default_rng(seed)
    dimension = REPRESENTATION_DIMENSIONS[representation]
    base_strength = BASE_SIGNAL_STRENGTH[representation]
    strength = base_strength * FACTOR_MULTIPLIER[factor]
    direction = _direction(
        factor=factor,
        representation=representation,
        dimension=dimension,
    )
    if representation is MorphologyRepresentation.SCALAR_X_C:
        train = np.zeros((TRAIN_REPLICATES, 1), dtype=float)
        validation = np.zeros((VALIDATION_REPLICATES, 1), dtype=float)
        held_out = np.zeros((HELD_OUT_REPLICATES, 1), dtype=float)
        unknown = np.zeros((UNKNOWN_REPLICATES, 1), dtype=float)
    else:
        train = _features(
            rng=rng,
            targets=targets[0],
            direction=direction,
            strength=strength,
        )
        validation = _features(
            rng=rng,
            targets=targets[1],
            direction=direction,
            strength=strength,
        )
        held_out = _features(
            rng=rng,
            targets=targets[2],
            direction=direction,
            strength=strength,
        )
        unknown_direction = np.ones(dimension, dtype=float)
        unknown_direction /= np.linalg.norm(unknown_direction)
        unknown = (
            12.0 * unknown_direction[None, :]
            + rng.normal(0.0, 0.45, size=(UNKNOWN_REPLICATES, dimension))
        )
    mask_perturbed = held_out + rng.normal(
        0.0,
        0.12,
        size=held_out.shape,
    )
    beam_perturbed = 0.92 * held_out
    foreground = held_out + 0.28 * direction[None, :]
    geometry = _geometry(
        factor=factor,
        representation=representation,
        strength=strength,
        normalizer=normalizer,
    )
    return RepresentationBenchmarkInput(
        representation=representation,
        availability=RepresentationAvailability.AVAILABLE,
        partition_ids=partition_ids,
        train_features=train,
        train_targets=targets[0],
        validation_features=validation,
        validation_targets=targets[1],
        held_out_features=held_out,
        held_out_targets=targets[2],
        unknown_features=unknown,
        mask_perturbed_features=mask_perturbed,
        beam_perturbed_features=beam_perturbed,
        foreground_features=foreground,
        geometry=geometry,
        geometry_normalizer=normalizer,
    )


def _missing_input(
    *,
    factor: CounterpairFactor,
    representation: MorphologyRepresentation,
    partition_ids: tuple[str, str, str, str],
) -> RepresentationBenchmarkInput:
    return RepresentationBenchmarkInput(
        representation=representation,
        availability=RepresentationAvailability.MISSING_FEATURE_PROVIDER,
        partition_ids=partition_ids,
        missing_reason=(
            "provider unavailable before held-out scoring; no zero fill"
        ),
    )


def _protocol(factor: CounterpairFactor) -> MorphologyBenchmarkProtocol:
    return MorphologyBenchmarkProtocol(
        protocol_id=_receipt(
            "benchmark_protocol",
            {"factor": factor.value, "version": 1},
        ),
        preregistration_id=_receipt(
            "preregistration",
            {
                "catalogue": "PR257_ORBIT_CATALOGUE_V2",
                "availability": [item.value for item in AVAILABLE_REPRESENTATIONS],
                "missing": [item.value for item in MISSING_REPRESENTATIONS],
                "master_seed": MASTER_SEED,
                "version": 1,
            },
        ),
        catalogue_id=_receipt(
            "catalogue",
            {"id": "PR257_ORBIT_CATALOGUE_V2", "version": 1},
        ),
        master_seed=MASTER_SEED,
        train_fraction=0.6,
        validation_fraction=0.2,
        held_out_fraction=0.2,
        confidence_margin_threshold=0.2,
        unknown_distance_threshold=6.0,
        maximum_mcse=MAXIMUM_MCSE,
        null_center_id=_receipt(
            "null_center_policy",
            {"source": "train_only", "factor": factor.value},
        ),
        null_scale_id=_receipt(
            "null_scale_policy",
            {
                "source": "train_only",
                "zero_scale": "representation_abstains",
                "factor": factor.value,
            },
        ),
        available_representations=AVAILABLE_REPRESENTATIONS,
        missing_representations=MISSING_REPRESENTATIONS,
    )


def _benchmark_factor(factor: CounterpairFactor) -> dict[str, object]:
    factor_seed = FACTOR_SEEDS[factor]
    target_rng = np.random.default_rng(factor_seed)
    targets = _split_targets(target_rng)
    partition_ids = tuple(
        _receipt(
            "shared_partition",
            {
                "factor": factor.value,
                "master_seed": MASTER_SEED,
                "role": role,
                "version": 1,
            },
        )
        for role in ("train", "validation", "held_out", "unknown")
    )
    normalizer = _normalizer()
    inputs = tuple(
        _available_input(
            factor=factor,
            representation=representation,
            targets=targets,
            partition_ids=partition_ids,
            seed=factor_seed + 101 * (index + 1),
            normalizer=normalizer,
        )
        for index, representation in enumerate(AVAILABLE_REPRESENTATIONS)
    ) + tuple(
        _missing_input(
            factor=factor,
            representation=representation,
            partition_ids=partition_ids,
        )
        for representation in MISSING_REPRESENTATIONS
    )
    report = evaluate_morphology_benchmark(
        protocol=_protocol(factor),
        inputs=inputs,
    )
    payload = report.as_payload()
    payload["factor"] = factor.value
    payload["factor_seed"] = factor_seed
    payload["target_partition_ids"] = {
        role: anchored_numeric_content_id(array)
        for role, array in zip(
            ("train", "validation", "held_out"),
            targets,
            strict=True,
        )
    }
    del inputs
    gc.collect()
    return payload


def _alm_fixture() -> dict[tuple[int, int], complex]:
    result: dict[tuple[int, int], complex] = {}
    for ell in (2, 3):
        result[(ell, 0)] = complex(1.0 + 0.2 * ell, 0.0)
        for m in range(1, ell + 1):
            value = complex(0.4 * (ell + m), 0.17 * (ell - m + 1))
            result[(ell, m)] = value
            result[(ell, -m)] = ((-1) ** m) * value.conjugate()
    return result


def _additional_features():
    return (
        register_morphology_feature(
            kind=MorphologyFeatureKind.DIRECTIONAL_WAVELET,
            availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
            provider_id=_receipt(
                "wavelet_provider",
                {"availability": "missing", "version": 1},
            ),
            units="not_available",
            missing_reason="no registered directional-wavelet provider",
        ),
        register_morphology_feature(
            kind=MorphologyFeatureKind.TEB_CROSS_MORPHOLOGY,
            availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
            provider_id=_receipt(
                "teb_provider",
                {"availability": "missing", "version": 1},
            ),
            units="not_available",
            missing_reason=(
                "scalar/spin-2 convention and E/B sign are not registered"
            ),
        ),
    )


def _counterpair(factor: CounterpairFactor) -> dict[str, object]:
    reference = build_lowell_morphology_feature_packet(
        sample_id=f"PR257-{factor.value}-REFERENCE",
        alm_by_lm=_alm_fixture(),
        ell_values=(2, 3),
        additional_features=_additional_features(),
        coordinate_frame="PR257 synthetic Cartesian frame",
        harmonic_convention=IMPLEMENTED_HARMONIC_CONVENTION,
        anchor_id=_receipt(
            "typed_anchor",
            {"channel": "synthetic_shared_anchor", "version": 1},
        ),
        anchor_stress_interval=(0.6, 0.7),
        mask_id=_receipt(
            "mask",
            {"kind": "synthetic_common_full_support", "version": 1},
        ),
        beam_id=_receipt(
            "beam",
            {"kind": "synthetic_common_unit_beam", "version": 1},
        ),
        foreground_model_id=_receipt(
            "foreground",
            {"kind": "synthetic_common_baseline", "version": 1},
        ),
    )
    operator = {
        CounterpairFactor.PHASE: InterventionOperator.NONLINEAR_M_PHASE_V1,
        CounterpairFactor.ORIENTATION: (
            InterventionOperator.COMMON_PROPER_Z_ROTATION_V1
        ),
        CounterpairFactor.PARITY: InterventionOperator.SCALAR_PARITY_V1,
    }[factor]
    angle = {
        CounterpairFactor.PHASE: 0.37,
        CounterpairFactor.ORIENTATION: 0.41,
        CounterpairFactor.PARITY: None,
    }[factor]
    intervention = LowEllInterventionSpec(
        factor=factor,
        operator=operator,
        angle_radians=angle,
    )
    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=intervention,
        sample_id=f"PR257-{factor.value}-TRANSFORMED",
        additional_features=_additional_features(),
    )
    report = build_matched_counterpair(
        pair_id=f"PR257-{factor.value}-MATCHED-COUNTERPAIR",
        factor=factor,
        left=reference,
        right=transformed,
    )
    return {
        "report": report.as_payload(),
        "reference_packet": reference.as_payload(),
        "transformed_packet": transformed.as_payload(),
    }


def _same_registered_cl(left: object, right: object) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    if len(left) != len(right):
        return False
    return all(
        left_row[0] == right_row[0]
        and float(left_row[1]) == float(right_row[1])
        for left_row, right_row in zip(left, right, strict=True)
    )


def build_payload() -> dict[str, object]:
    counterpairs = {
        factor.value: _counterpair(factor)
        for factor in CounterpairFactor
    }
    factors = [
        _benchmark_factor(factor)
        for factor in CounterpairFactor
    ]
    measured = [
        result
        for factor in factors
        for result in factor["results"]
        if result["status"] != (
            RepresentationBenchmarkStatus.MISSING_FEATURE_PROVIDER.value
        )
    ]
    non_scalar = [
        result
        for result in measured
        if result["representation"]
        != MorphologyRepresentation.SCALAR_X_C.value
    ]
    controls = {
        "all_factor_reports_measured": all(
            factor["status"] == MorphologyBenchmarkStatus.MEASURED.value
            for factor in factors
        ),
        "same_power_and_anchor_counterpairs": all(
            _same_registered_cl(
                row["reference_packet"]["cl_by_ell"],
                row["transformed_packet"]["cl_by_ell"],
            )
            and row["reference_packet"]["anchor_id"]
            == row["transformed_packet"]["anchor_id"]
            and row["reference_packet"]["anchor_stress_interval"]
            == row["transformed_packet"]["anchor_stress_interval"]
            for row in counterpairs.values()
        ),
        "scalar_abstains_in_every_factor": all(
            factor["results"][0]["status"]
            == RepresentationBenchmarkStatus.DEGENERATE_ABSTENTION.value
            and factor["results"][0]["held_out_abstention_rate"] == 1.0
            for factor in factors
        ),
        "available_non_scalar_losses_improve_on_scalar": all(
            result["generator_label_loss_reduction_from_scalar"] > 0.0
            for result in non_scalar
        ),
        "unknown_source_never_forced_known": all(
            result["unknown_known_assignment_rate"] == 0.0
            for result in non_scalar
        ),
        "missing_providers_remain_missing": all(
            result["status"]
            == RepresentationBenchmarkStatus.MISSING_FEATURE_PROVIDER.value
            for factor in factors
            for result in factor["results"][-2:]
        ),
        "maximum_observed_mcse": max(
            factor["maximum_observed_mcse"] for factor in factors
        ),
        "mcse_pass": all(
            factor["maximum_observed_mcse"] <= MAXIMUM_MCSE
            for factor in factors
        ),
        "supported_rank_not_created_by_scalar": all(
            factor["results"][0]["supported_rank"] == 0
            and any(
                result["supported_rank"] > 0
                for result in factor["results"][1:-2]
            )
            for factor in factors
        ),
    }
    passed = all(
        value
        for key, value in controls.items()
        if key != "maximum_observed_mcse"
    )
    return _canonical(
        {
            "schema_version": "pr257.lowell_morphology_benchmark.v1",
            "work_unit_id": "PR-257",
            "status": "PASS" if passed else "FAIL",
            "owner": "HTT",
            "scope": "pre_solver_synthetic_methodology",
            "claim_tier": "diagnostic_only",
            "scientific_artifact_mode": "diagnostic_only",
            "data_source": "synthetic_only",
            "response_role": "hypothesis_only",
            "transfer_source": "none",
            "sky_support_status": (
                "synthetic_lowell_feature_space_not_observed_sky"
            ),
            "null_mock_status": (
                "preregistered_synthetic_counterpair_generator_only"
            ),
            "covariance_status": (
                "registered_synthetic_supported_quotient_only"
            ),
            "pr151_data_used": False,
            "old_rust_science_output_used": False,
            "native_solver_used": False,
            "observational_validation": False,
            "configuration": {
                "master_seed": MASTER_SEED,
                "factor_seeds": {
                    factor.value: FACTOR_SEEDS[factor]
                    for factor in CounterpairFactor
                },
                "total_replicates_per_factor": TOTAL_REPLICATES,
                "train_replicates": TRAIN_REPLICATES,
                "validation_replicates": VALIDATION_REPLICATES,
                "held_out_replicates": HELD_OUT_REPLICATES,
                "unknown_replicates": UNKNOWN_REPLICATES,
                "maximum_replicates_per_factor": MAXIMUM_REPLICATES,
                "maximum_mcse": MAXIMUM_MCSE,
                "split": [0.6, 0.2, 0.2],
                "balanced_binary_generator_labels": True,
                "representation_dimensions": {
                    representation.value: dimension
                    for representation, dimension
                    in REPRESENTATION_DIMENSIONS.items()
                },
                "base_signal_strength": {
                    representation.value: strength
                    for representation, strength
                    in BASE_SIGNAL_STRENGTH.items()
                },
                "factor_signal_multiplier": {
                    factor.value: multiplier
                    for factor, multiplier in FACTOR_MULTIPLIER.items()
                },
                "feature_noise": "independent_standard_normal",
                "unknown_offset_norm": 12.0,
                "unknown_noise_sigma": 0.45,
                "mask_perturbation_sigma": 0.12,
                "beam_multiplicative_factor": 0.92,
                "foreground_direction_shift": 0.28,
                "confidence_margin_threshold": 0.2,
                "unknown_distance_threshold": 6.0,
                "scoring_rule": (
                    "NEAREST_CENTROID_FIXED_MARGIN_OPEN_SET_V1"
                ),
                "abstention_cost": 0.5,
                "multiplicity_rule": (
                    "MAX_ABS_Z_FIXED_CATALOGUE_V1"
                ),
                "availability_frozen_before_scoring": True,
                "available_representations": [
                    item.value for item in AVAILABLE_REPRESENTATIONS
                ],
                "missing_representations": [
                    item.value for item in MISSING_REPRESENTATIONS
                ],
            },
            "provenance": {
                "target_ref": "origin/research/pr04-multicomponent",
                "target_sha": TARGET_SHA,
                "specification": (
                    "docs/research_program/premise_anchor/pr257_spec.yaml"
                ),
                "generating_procedure": (
                    "scripts/codex_harness/"
                    "run_pr257_morphology_benchmark.py"
                ),
                "generating_procedure_sha256": GENERATOR_SOURCE_ID,
                "generation_worktree_state": _generation_worktree_state(),
                "cas_contract_sha256": (
                    "sha256:"
                    + hashlib.sha256(CAS_CONTRACT.read_bytes()).hexdigest()
                ),
            },
            "counterpairs": counterpairs,
            "factor_reports": factors,
            "controls": controls,
            "headline_metrics": {
                "covariance_whitened_supported_singular_spectra": [
                    {
                        "factor": factor["factor"],
                        "representations": [
                            {
                                "representation": result["representation"],
                                "singular_values": result["singular_values"],
                                "supported_rank": result["supported_rank"],
                                "contraction_status": (
                                    None
                                    if result["geometry"] is None
                                    else result["geometry"]["contraction"]["status"]
                                ),
                            }
                            for result in factor["results"]
                        ],
                    }
                    for factor in factors
                ],
                "generator_label_loss_reduction": [
                    {
                        "factor": factor["factor"],
                        "values": {
                            result["representation"]: (
                                result[
                                    "generator_label_loss_reduction_from_scalar"
                                ]
                            )
                            for result in factor["results"]
                        },
                        "paired_mcse": {
                            result["representation"]: (
                                result[
                                    "generator_label_loss_reduction_mcse_from_scalar"
                                ]
                            )
                            for result in factor["results"]
                        },
                    }
                    for factor in factors
                ],
                "mask_beam_foreground_sensitivity": [
                    {
                        "factor": factor["factor"],
                        "values": {
                            result["representation"]: {
                                "mask": result["mask_decision_change_rate"],
                                "beam": result["beam_decision_change_rate"],
                                "foreground": (
                                    result["foreground_decision_change_rate"]
                                ),
                            }
                            for result in factor["results"]
                        },
                    }
                    for factor in factors
                ],
            },
            "allowed_use": [
                "synthetic matched-counterpair construction",
                "held-out representation diagnostic",
                "mask, beam, foreground, and unknown-source abstention audit",
                "next-observable planning",
            ],
            "forbidden_use": [
                "observed anomaly or source detection",
                "FLRW departure or geometry detection",
                "Bianchi family identification",
                "native-solver validation",
                "posterior, Bayes factor, e-value, or evidence",
                "complete invariant basis or generic orbit separation",
            ],
            "caveats": [
                "All skies, response geometries, and features are synthetic.",
                "The labels identify registered generators, not physical sources.",
                "Directional-wavelet and T/E/B providers are unavailable.",
                "Scalar x_C is deliberately degenerate and diagnostic-only.",
                "No p-value ranking is produced.",
            ],
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the frozen PR-257 synthetic diagnostic artifact",
    )
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"WROTE {OUTPUT.relative_to(ROOT)}")
    elif not OUTPUT.is_file():
        print(f"MISSING {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    else:
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if frozen != payload:
            print(
                "FAIL frozen PR-257 morphology benchmark drifted",
                file=sys.stderr,
            )
            return 1
    if payload["status"] != "PASS":
        print("FAIL PR-257 synthetic morphology benchmark", file=sys.stderr)
        return 1
    print(
        "PASS PR-257 synthetic morphology benchmark "
        f"factors={len(CounterpairFactor)} "
        f"held_out={HELD_OUT_REPLICATES}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
