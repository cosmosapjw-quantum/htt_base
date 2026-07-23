"""Fail-closed PR-172 metamorphic checks over existing estimator surfaces.

This module does not implement a new scientific estimator.  It evaluates
registered transform relations on deterministic synthetic fixtures and keeps
primitive metrics separate from their derived pass/fail routing.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from obsstat.cf4_velocity_estimators import Cf4Sample, estimate
from bass.los.b_mode_projector import (
    project_B_mode_transfer,
    spin2_parity_odd_combination,
)


SCHEMA = "htt.pr172.metamorphic_result.v1"
RELATION_IDS = (
    "MR172-CF4-SO3-001",
    "MR172-CF4-AXISPERM-002",
    "MR172-CF4-QUADRATIC-003",
    "MR172-CF4-MONOPOLE-004",
    "MR172-B-INDEX-ODD-005",
    "MR172-B-SUPPORT-006",
    "MR172-B-M0-CANCEL-007",
    "MR172-B-AXISYM-DOC-008",
)
MUTATION_IDS = (
    "MU172-CF4-NONLY-ROT",
    "MU172-CF4-AXIS-FIXED",
    "MU172-CF4-LINEAR-POWER",
    "MU172-CF4-DROP-INTERCEPT",
    "MU172-B-EVEN-KERNEL",
    "MU172-B-OFFSUPPORT",
    "MU172-B-M0-PLUS",
)
SPEC_PATH = Path("docs/research_program/long_horizon_rescue/pr172_spec.yaml")
EVALUATOR_PATH = Path("htt/htt/metamorphic_symmetry.py")
RUNNER_PATH = Path("scripts/codex_harness/run_pr172_metamorphic_battery.py")


def _live_source_path(path: Path) -> Path:
    """Resolve the one implementation relocated after the frozen PR-172 spec."""
    if path == Path("htt/src/common/cf4_velocity_estimators.py"):
        return Path("htt/obsstat/cf4_velocity_estimators.py")
    return path


class MetamorphicContractError(ValueError):
    """Raised when evidence cannot be routed under the frozen contract."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def semantic_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("semantic_digest", None)
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def expected_input_hashes(spec: Mapping[str, Any], repo: Path) -> dict[str, str]:
    paths = (
        SPEC_PATH,
        EVALUATOR_PATH,
        RUNNER_PATH,
        _live_source_path(Path(spec["source_bindings"]["cf4_estimator"]["path"])),
        Path(spec["source_bindings"]["b_projector"]["path"]),
        Path(spec["source_bindings"]["upstream_pr123"]["path"]),
        Path(spec["source_bindings"]["upstream_pr167"]["path"]),
    )
    return {str(path): sha256_file(repo / path) for path in paths}


def worktree_content_receipt(input_hashes: Mapping[str, str]) -> str:
    return hashlib.sha256(canonical_bytes(dict(input_hashes))).hexdigest()


def _as_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MetamorphicContractError(f"{label} must be a real number, not bool")
    result = float(value)
    if not math.isfinite(result):
        raise MetamorphicContractError(f"{label} must be finite")
    return result


def scaled_residual(actual: np.ndarray | float, expected: np.ndarray | float) -> float:
    left = np.asarray(actual, dtype=np.float64)
    right = np.asarray(expected, dtype=np.float64)
    if left.shape != right.shape:
        raise MetamorphicContractError(
            f"scaled residual shape mismatch: {left.shape} != {right.shape}"
        )
    denominator = 1.0 + np.abs(left) + np.abs(right)
    return float(np.max(np.abs(left - right) / denominator, initial=0.0))


def array_receipt(value: np.ndarray) -> dict[str, Any]:
    array = np.ascontiguousarray(np.asarray(value, dtype="<f8"))
    return {
        "shape": list(array.shape),
        "dtype": "float64-little-endian",
        "sha256": hashlib.sha256(array.tobytes(order="C")).hexdigest(),
        "float_hex": [float(item).hex() for item in array.ravel(order="C")],
    }


def _metric(
    metric_id: str,
    value: float,
    threshold: float,
    comparison: str = "le",
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "value": float(value),
        "threshold": float(threshold),
        "comparison": comparison,
    }


def metric_passes(metric: Mapping[str, Any]) -> bool:
    value = _as_float(metric.get("value"), "metric.value")
    threshold = _as_float(metric.get("threshold"), "metric.threshold")
    comparison = metric.get("comparison")
    if comparison == "le":
        return value <= threshold
    if comparison == "ge":
        return value >= threshold
    raise MetamorphicContractError(f"unsupported comparison: {comparison!r}")


def _relation(
    relation_id: str,
    adapter: str,
    metrics: list[dict[str, Any]],
    receipts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "relation_id": relation_id,
        "adapter": adapter,
        "execution_count": 1,
        "metrics": metrics,
        "primitive_receipts": dict(receipts or {}),
        "passed": all(metric_passes(row) for row in metrics),
    }


def _cf4_fixture() -> Cf4Sample:
    raw = np.asarray(
        [
            [1, 0, 1],
            [0, 1, 1],
            [-1, 0, 2],
            [0, -1, 1],
            [1, 2, -1],
            [-2, 1, 1],
            [1, -2, 2],
            [2, 1, -1],
        ],
        dtype=np.float64,
    )
    n = raw / np.linalg.norm(raw, axis=1)[:, None]
    distances = np.arange(15.0, 39.0, 3.0, dtype=np.float64)
    sig_v = np.arange(250.0, 330.0, 10.0, dtype=np.float64)
    pos = n * distances[:, None]
    flow = np.asarray([120.0, -80.0, 45.0])
    v = n @ flow + 37.0
    return Cf4Sample(
        n=n,
        v=v,
        w=1.0 / sig_v**2,
        sig_v=sig_v,
        pos_hmpc=pos,
        sg=pos.copy(),
    )


def _replace_sample(sample: Cf4Sample, **updates: np.ndarray) -> Cf4Sample:
    fields = {
        "n": sample.n,
        "v": sample.v,
        "w": sample.w,
        "sig_v": sample.sig_v,
        "pos_hmpc": sample.pos_hmpc,
        "sg": sample.sg,
    }
    fields.update(updates)
    return Cf4Sample(**fields)


def _transform_sample(sample: Cf4Sample, matrix: np.ndarray) -> Cf4Sample:
    updates = {
        "n": sample.n @ matrix.T,
        "pos_hmpc": sample.pos_hmpc @ matrix.T,
    }
    if sample.sg is not None:
        updates["sg"] = sample.sg @ matrix.T
    return _replace_sample(sample, **updates)


def _normal_condition(sample: Cf4Sample, monopole: bool) -> float:
    design = (
        np.column_stack([sample.n, np.ones(len(sample.v))])
        if monopole
        else sample.n
    )
    normal = np.einsum("i,ij,ik->jk", sample.w, design, design)
    return float(np.linalg.cond(normal))


def _kernel(ell: int, big_m: int, little_m: int) -> float:
    return spin2_parity_odd_combination(ell=ell, M=big_m, m=little_m)


def _axisymmetric_challenge() -> tuple[np.ndarray, dict[str, Any]]:
    eta = np.linspace(0.0, 1.0, 9, dtype=np.float64)
    b_hist = np.zeros((9, 3, 5), dtype=np.float64)
    e_hist = np.zeros_like(b_hist)
    sigma = np.zeros((9, 5), dtype=np.float64)
    b_hist[:, 2, 0] = 1.0
    sigma[:, 2] = 1.0
    output = project_B_mode_transfer(
        photon_B_tower_history=b_hist,
        photon_E_tower_history=e_hist,
        sigma_2M_history=sigma,
        eta_grid=eta,
        visibility_history=np.ones(9, dtype=np.float64),
        k_norm=2.0,
        ell_max=3,
    )
    inputs = {
        "eta_grid": array_receipt(eta),
        "B_history": array_receipt(b_hist),
        "E_history": array_receipt(e_hist),
        "sigma_history": array_receipt(sigma),
    }
    return output, inputs


def _source_bindings(spec: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    bindings: dict[str, Any] = {}
    for key in ("cf4_estimator", "b_projector"):
        frozen = spec["source_bindings"][key]
        relative = _live_source_path(Path(frozen["path"]))
        path = repo / relative
        actual = sha256_file(path)
        bindings[key] = {
            "path": str(relative),
            "expected_sha256": frozen["sha256"],
            "actual_sha256": actual,
            "matched": actual == frozen["sha256"],
        }
    return bindings


def _clean_relations(spec: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tolerance = float(spec["tolerances"]["scaled_float_residual"])
    sample = _cf4_fixture()
    condition = _normal_condition(sample, monopole=True)
    max_condition = float(spec["conventions"]["cf4"]["max_normal_matrix_condition_number"])
    if not math.isfinite(condition) or condition > max_condition:
        raise MetamorphicContractError("CF4 fixture violates frozen conditioning guard")

    base = estimate(sample, monopole=True, label="pr172_base")
    rotation = np.asarray(spec["transforms"]["proper_rotation"]["numeric_matrix"], dtype=np.float64)
    if scaled_residual(rotation @ rotation.T, np.eye(3)) > 2e-15:
        raise MetamorphicContractError("frozen rotation is not orthogonal")
    if abs(float(np.linalg.det(rotation)) - 1.0) > 2e-15:
        raise MetamorphicContractError("frozen rotation is not proper")
    block_rotation = np.eye(4)
    block_rotation[:3, :3] = rotation
    rotated = estimate(
        _transform_sample(sample, rotation), monopole=True, label="pr172_rotated"
    )
    relation_rotation = _relation(
        RELATION_IDS[0],
        "cf4_estimator",
        [
            _metric("coefficient_scaled_residual", scaled_residual(rotated.coeffs, block_rotation @ base.coeffs), tolerance),
            _metric("noise_covariance_scaled_residual", scaled_residual(rotated.noise_cov, block_rotation @ base.noise_cov @ block_rotation.T), tolerance),
            _metric("cosmic_covariance_scaled_residual", scaled_residual(rotated.cv_cov, block_rotation @ base.cv_cov @ block_rotation.T), tolerance),
        ],
        {"base_coefficients": array_receipt(base.coeffs), "rotated_coefficients": array_receipt(rotated.coeffs)},
    )

    permutation = np.asarray(spec["transforms"]["axis_permutation"]["matrix"], dtype=np.float64)
    block_permutation = np.eye(4)
    block_permutation[:3, :3] = permutation
    permuted = estimate(
        _transform_sample(sample, permutation), monopole=True, label="pr172_axis_permuted"
    )
    relation_permutation = _relation(
        RELATION_IDS[1],
        "cf4_estimator",
        [
            _metric("coefficient_scaled_residual", scaled_residual(permuted.coeffs, block_permutation @ base.coeffs), tolerance),
            _metric("full_covariance_scaled_residual", scaled_residual(permuted.full_cov, block_permutation @ base.full_cov @ block_permutation.T), tolerance),
        ],
        {"permuted_coefficients": array_receipt(permuted.coeffs)},
    )

    amplitude_scale = float(spec["transforms"]["amplitude_scale"])
    scaled = estimate(
        _replace_sample(sample, v=amplitude_scale * sample.v),
        monopole=True,
        label="pr172_amplitude_scaled",
    )
    base_power = float(base.bulk_flow_vector() @ base.bulk_flow_vector())
    scaled_power = float(scaled.bulk_flow_vector() @ scaled.bulk_flow_vector())
    relation_quadratic = _relation(
        RELATION_IDS[2],
        "cf4_estimator",
        [
            _metric("coefficient_linearity_scaled_residual", scaled_residual(scaled.coeffs, amplitude_scale * base.coeffs), tolerance),
            _metric("full_covariance_invariance_scaled_residual", scaled_residual(scaled.full_cov, base.full_cov), tolerance),
            _metric("bulk_power_quadratic_scaled_residual", scaled_residual(scaled_power, amplitude_scale**2 * base_power), tolerance),
        ],
        {"scaled_coefficients": array_receipt(scaled.coeffs), "base_bulk_power": base_power, "scaled_bulk_power": scaled_power},
    )

    shift = float(spec["transforms"]["monopole_shift_kms"])
    shifted_sample = _replace_sample(sample, v=sample.v + shift)
    shifted = estimate(shifted_sample, monopole=True, label="pr172_monopole_shifted")
    base_flow_only = estimate(sample, monopole=False, label="pr172_flow_only_base")
    shifted_flow_only = estimate(
        shifted_sample, monopole=False, label="pr172_flow_only_shifted"
    )
    flow_only_leak = float(
        np.max(np.abs(shifted_flow_only.coeffs - base_flow_only.coeffs))
    )
    expected_shifted = base.coeffs.copy()
    expected_shifted[3] += shift
    relation_monopole = _relation(
        RELATION_IDS[3],
        "cf4_estimator",
        [
            _metric("augmented_coefficient_scaled_residual", scaled_residual(shifted.coeffs, expected_shifted), tolerance),
            _metric("full_covariance_invariance_scaled_residual", scaled_residual(shifted.full_cov, base.full_cov), tolerance),
            _metric("flow_only_leakage_challenge_kms", flow_only_leak, float(spec["tolerances"]["flow_only_monopole_leak_challenge_min_kms"]), "ge"),
        ],
        {"augmented_shifted_coefficients": array_receipt(shifted.coeffs), "flow_only_delta": array_receipt(shifted_flow_only.coeffs - base_flow_only.coeffs)},
    )

    anti_residual = 0.0
    support_residual = 0.0
    cancellation_residual = 0.0
    kernel_values: list[float] = []
    for ell in range(2, 7):
        cancellation = 0.0
        for big_m in range(-2, 3):
            for little_m in range(-2, 3):
                value = _kernel(ell, big_m, little_m)
                reflected = _kernel(ell, -big_m, -little_m)
                anti_residual = max(anti_residual, abs(reflected + value))
                if abs(big_m - little_m) != 2:
                    support_residual = max(support_residual, abs(value))
                kernel_values.append(value)
            cancellation += _kernel(ell, big_m, 0)
        cancellation_residual = max(cancellation_residual, abs(cancellation))

    relation_odd = _relation(
        RELATION_IDS[4], "b_projector",
        [_metric("kernel_anti_equivariance_residual", anti_residual, 0.0)],
        {"enumerated_kernel": array_receipt(np.asarray(kernel_values))},
    )
    relation_support = _relation(
        RELATION_IDS[5], "b_projector",
        [_metric("off_support_max_abs", support_residual, 0.0)],
    )
    relation_cancel = _relation(
        RELATION_IDS[6], "b_projector",
        [_metric("m_zero_signed_sum_max_abs", cancellation_residual, 0.0)],
    )
    axisym_output, axisym_inputs = _axisymmetric_challenge()
    relation_axisym = _relation(
        RELATION_IDS[7], "b_projector",
        [_metric("documented_axisymmetric_zero_max_abs", float(np.max(np.abs(axisym_output))), 0.0)],
        {**axisym_inputs, "projector_output": array_receipt(axisym_output)},
    )

    relations = [
        relation_rotation,
        relation_permutation,
        relation_quadratic,
        relation_monopole,
        relation_odd,
        relation_support,
        relation_cancel,
        relation_axisym,
    ]
    state = {
        "sample": sample,
        "base": base,
        "rotation": rotation,
        "block_rotation": block_rotation,
        "rotated": rotated,
        "permutation": permutation,
        "block_permutation": block_permutation,
        "permuted": permuted,
        "amplitude_scale": amplitude_scale,
        "base_power": base_power,
        "shifted_sample": shifted_sample,
        "base_flow_only": base_flow_only,
        "shifted_flow_only": shifted_flow_only,
        "condition_number": condition,
    }
    return relations, state


def _execute_mutation(
    mutation_id: str,
    relation_id: str,
    callable_id: str,
    evaluator: Callable[[], tuple[float, dict[str, Any], dict[str, Any]]],
) -> dict[str, Any]:
    invocation_count = 0

    def invoke() -> tuple[float, dict[str, Any], dict[str, Any]]:
        nonlocal invocation_count
        invocation_count += 1
        return evaluator()

    activation_delta, mutated_metric, primitives = invoke()
    relation_would_pass = metric_passes(mutated_metric)
    killed = bool(activation_delta > 0.0 and not relation_would_pass)
    primitive_sha256 = hashlib.sha256(canonical_bytes(primitives)).hexdigest()
    return {
        "mutation_id": mutation_id,
        "relation_id": relation_id,
        "execution_count": invocation_count,
        "activation_delta": float(activation_delta),
        "mutated_metric": mutated_metric,
        "witness_value": float(mutated_metric["value"]),
        "kill_threshold": float(mutated_metric["threshold"]),
        "relation_would_pass": relation_would_pass,
        "execution_receipt": {
            "callable_id": callable_id,
            "invoked": invocation_count == 1,
            "invocation_count": invocation_count,
            "primitive_sha256": primitive_sha256,
            "primitives": primitives,
        },
        "killed": killed,
    }


def _mutations(spec: Mapping[str, Any], state: Mapping[str, Any]) -> list[dict[str, Any]]:
    tolerance = float(spec["tolerances"]["scaled_float_residual"])
    sample: Cf4Sample = state["sample"]
    base = state["base"]
    rotation = state["rotation"]
    block_rotation = state["block_rotation"]
    correct_rotated = state["rotated"]

    block_permutation = state["block_permutation"]
    correct_permuted = state["permuted"]
    amplitude_scale = float(state["amplitude_scale"])
    base_power = float(state["base_power"])
    expected_power = amplitude_scale**2 * base_power

    def n_only_rotation() -> tuple[float, dict[str, Any], dict[str, Any]]:
        mutated = estimate(
            _replace_sample(sample, n=sample.n @ rotation.T),
            monopole=True,
            label="mutant_n_only_rotation",
        )
        witness = scaled_residual(
            mutated.full_cov, block_rotation @ base.full_cov @ block_rotation.T
        )
        activation = scaled_residual(mutated.full_cov, correct_rotated.full_cov)
        return activation, _metric("mutated_full_covariance_scaled_residual", witness, tolerance), {
            "mutated_full_covariance": array_receipt(mutated.full_cov),
            "correct_full_covariance": array_receipt(correct_rotated.full_cov),
        }

    def fixed_axis_output() -> tuple[float, dict[str, Any], dict[str, Any]]:
        mutated = np.asarray(base.coeffs, dtype=np.float64).copy()
        expected = block_permutation @ base.coeffs
        witness = scaled_residual(mutated, expected)
        activation = scaled_residual(mutated, correct_permuted.coeffs)
        return activation, _metric("mutated_coefficient_equivariance_residual", witness, tolerance), {
            "mutated_coefficients": array_receipt(mutated),
            "expected_coefficients": array_receipt(expected),
        }

    def linear_power_output() -> tuple[float, dict[str, Any], dict[str, Any]]:
        mutated_power = amplitude_scale * base_power
        witness = scaled_residual(mutated_power, expected_power)
        return witness, _metric("mutated_quadratic_power_scaled_residual", witness, tolerance), {
            "mutated_power": float(mutated_power),
            "expected_power": float(expected_power),
        }

    def drop_intercept_output() -> tuple[float, dict[str, Any], dict[str, Any]]:
        mutated_base = estimate(sample, monopole=False, label="mutant_drop_intercept_base")
        mutated_shifted = estimate(
            state["shifted_sample"], monopole=False, label="mutant_drop_intercept_shifted"
        )
        delta = mutated_shifted.coeffs - mutated_base.coeffs
        witness = float(np.max(np.abs(delta)))
        return witness, _metric("mutated_bulk_flow_invariance_residual_kms", witness, tolerance), {
            "mutated_bulk_delta": array_receipt(delta),
        }

    def even_kernel(ell: int, big_m: int, little_m: int) -> float:
        return abs(_kernel(ell, big_m, little_m))

    def offsupport_kernel(ell: int, big_m: int, little_m: int) -> float:
        value = _kernel(ell, big_m, little_m)
        if ell == 2 and big_m == 0 and little_m == 0:
            return value + 0.5
        return value

    def plus_kernel(ell: int, big_m: int, little_m: int) -> float:
        return abs(_kernel(ell, big_m, little_m))

    def kernel_mutation(
        mutant: Callable[[int, int, int], float], relation: str
    ) -> tuple[float, dict[str, Any], dict[str, Any]]:
        original_values: list[float] = []
        mutant_values: list[float] = []
        witness = 0.0
        for ell in range(2, 7):
            if relation == "m0":
                witness = max(
                    witness,
                    abs(sum(mutant(ell, big_m, 0) for big_m in range(-2, 3))),
                )
            for big_m in range(-2, 3):
                for little_m in range(-2, 3):
                    original = _kernel(ell, big_m, little_m)
                    changed = mutant(ell, big_m, little_m)
                    original_values.append(original)
                    mutant_values.append(changed)
                    if relation == "anti":
                        witness = max(
                            witness,
                            abs(changed + mutant(ell, -big_m, -little_m)),
                        )
                    elif relation == "support" and abs(big_m - little_m) != 2:
                        witness = max(witness, abs(changed))
        original_array = np.asarray(original_values, dtype=np.float64)
        mutant_array = np.asarray(mutant_values, dtype=np.float64)
        activation = float(np.max(np.abs(mutant_array - original_array)))
        metric_ids = {
            "anti": "mutated_kernel_anti_equivariance_residual",
            "support": "mutated_off_support_max_abs",
            "m0": "mutated_m_zero_signed_sum_max_abs",
        }
        return activation, _metric(metric_ids[relation], witness, 0.0), {
            "original_kernel": array_receipt(original_array),
            "mutated_kernel": array_receipt(mutant_array),
        }

    evaluators = (
        (MUTATION_IDS[0], RELATION_IDS[0], "mutant_n_only_rotation", n_only_rotation),
        (MUTATION_IDS[1], RELATION_IDS[1], "mutant_fixed_axis_output", fixed_axis_output),
        (MUTATION_IDS[2], RELATION_IDS[2], "mutant_linear_power_output", linear_power_output),
        (MUTATION_IDS[3], RELATION_IDS[3], "mutant_drop_intercept_output", drop_intercept_output),
        (MUTATION_IDS[4], RELATION_IDS[4], "mutant_even_kernel", lambda: kernel_mutation(even_kernel, "anti")),
        (MUTATION_IDS[5], RELATION_IDS[5], "mutant_offsupport_kernel", lambda: kernel_mutation(offsupport_kernel, "support")),
        (MUTATION_IDS[6], RELATION_IDS[6], "mutant_plus_kernel", lambda: kernel_mutation(plus_kernel, "m0")),
    )
    return [
        _execute_mutation(mutation_id, relation_id, callable_id, evaluator)
        for mutation_id, relation_id, callable_id, evaluator in evaluators
    ]


def expected_terminal(relations: list[Mapping[str, Any]], mutations: list[Mapping[str, Any]]) -> str:
    if any(not bool(row.get("passed")) for row in relations):
        return "BLOCKED_METAMORPHIC_RELATION_VIOLATION"
    if any(not bool(row.get("killed")) for row in mutations):
        return "BLOCKED_METAMORPHIC_RELATION_VIOLATION"
    return "PASS_METAMORPHIC_SELF_CONSISTENCY_C1"


def build_battery(spec: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    if tuple(row.get("relation_id") for row in spec.get("relations", [])) != RELATION_IDS:
        raise MetamorphicContractError("relation registry differs from frozen order")
    if tuple(row.get("mutation_id") for row in spec.get("mutation_registry", [])) != MUTATION_IDS:
        raise MetamorphicContractError("mutation registry differs from frozen order")
    bindings = _source_bindings(spec, repo)
    # Frozen source hashes remain visible as historical diagnostics, but they
    # must not prevent the live semantic battery from running after a valid
    # maintenance change. Historical receipt validation stays fail-closed.
    relations, state = _clean_relations(spec)
    mutations = _mutations(spec, state)
    input_hashes = expected_input_hashes(spec, repo)
    content_receipt = worktree_content_receipt(input_hashes)
    adapter_status = {}
    for adapter in ("cf4_estimator", "b_projector"):
        rows = [row for row in relations if row["adapter"] == adapter]
        adapter_status[adapter] = (
            "PASS_REGISTERED_RELATIONS"
            if all(row["passed"] for row in rows)
            else "BLOCKED_METAMORPHIC_RELATION_VIOLATION"
        )
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "pr_id": "PR-172",
        "claim_id": "C-PR172-METAMORPHIC-CONSISTENCY",
        "owner": "COMMON",
        "contributors": ["OBSSTAT"],
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "scientific_status": "OPEN",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": input_hashes[str(SPEC_PATH)],
        "input_hashes": input_hashes,
        "source_bindings": bindings,
        "fixture_guards": {
            "cf4_normal_condition_number": float(state["condition_number"]),
            "max_allowed_condition_number": float(spec["conventions"]["cf4"]["max_normal_matrix_condition_number"]),
        },
        "relations": relations,
        "mutations": mutations,
        "adapter_status": adapter_status,
        "terminal": expected_terminal(relations, mutations),
        "lineage": {
            "kind": "same_production_adapter_metamorphic_pair",
            "independent_numerical_oracle_count": 0,
            "base_and_transformed_runs_are_independent_oracles": False,
        },
        "sky_support_status": "synthetic_fixture_not_observed_sky",
        "mask_status": "not_applicable_synthetic_fixture",
        "covariance_status": "mechanics_only_not_covariance_validation",
        "null_mock_status": "not_run_not_applicable",
        "allowed_uses": ["internal C1 regression gating of the exact registered estimator surfaces"],
        "forbidden_uses": [
            "physical validation",
            "observed parity or anisotropy inference",
            "independent-oracle support",
            "geometry or Bianchi-family identification",
        ],
        "caveats": [
            "A CF4 covariance-equivariance pass does not validate the fiducial covariance model.",
            "B index oddness is not a physical spatial-parity test.",
            "The axisymmetric challenge tests the callable's documented contract with a shape-valid state.",
        ],
        "generating_command": "PYTHONPATH=htt/src:htt venv/bin/python -B scripts/codex_harness/run_pr172_metamorphic_battery.py --write",
        "git_commit": spec["baseline_commit"],
        "worktree_content_receipt": content_receipt,
        "worktree_state": f"{spec['baseline_commit']}+content-sha256:{content_receipt}",
        "runtime_environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "threads": {"OPENBLAS": 1, "OMP": 1, "MKL": 1},
        },
    }
    report["semantic_digest"] = semantic_digest(report)
    return report


def _expected_relation_contract(spec: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    tolerance = float(spec["tolerances"]["scaled_float_residual"])
    leakage = float(spec["tolerances"]["flow_only_monopole_leak_challenge_min_kms"])
    return {
        RELATION_IDS[0]: {
            "adapter": "cf4_estimator",
            "metrics": (
                ("coefficient_scaled_residual", "le", tolerance),
                ("noise_covariance_scaled_residual", "le", tolerance),
                ("cosmic_covariance_scaled_residual", "le", tolerance),
            ),
        },
        RELATION_IDS[1]: {
            "adapter": "cf4_estimator",
            "metrics": (
                ("coefficient_scaled_residual", "le", tolerance),
                ("full_covariance_scaled_residual", "le", tolerance),
            ),
        },
        RELATION_IDS[2]: {
            "adapter": "cf4_estimator",
            "metrics": (
                ("coefficient_linearity_scaled_residual", "le", tolerance),
                ("full_covariance_invariance_scaled_residual", "le", tolerance),
                ("bulk_power_quadratic_scaled_residual", "le", tolerance),
            ),
        },
        RELATION_IDS[3]: {
            "adapter": "cf4_estimator",
            "metrics": (
                ("augmented_coefficient_scaled_residual", "le", tolerance),
                ("full_covariance_invariance_scaled_residual", "le", tolerance),
                ("flow_only_leakage_challenge_kms", "ge", leakage),
            ),
        },
        RELATION_IDS[4]: {
            "adapter": "b_projector",
            "metrics": (("kernel_anti_equivariance_residual", "le", 0.0),),
        },
        RELATION_IDS[5]: {
            "adapter": "b_projector",
            "metrics": (("off_support_max_abs", "le", 0.0),),
        },
        RELATION_IDS[6]: {
            "adapter": "b_projector",
            "metrics": (("m_zero_signed_sum_max_abs", "le", 0.0),),
        },
        RELATION_IDS[7]: {
            "adapter": "b_projector",
            "metrics": (("documented_axisymmetric_zero_max_abs", "le", 0.0),),
        },
    }


def _expected_mutation_contract(spec: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    tolerance = float(spec["tolerances"]["scaled_float_residual"])
    rows = (
        (MUTATION_IDS[0], RELATION_IDS[0], "mutant_n_only_rotation", "mutated_full_covariance_scaled_residual", tolerance),
        (MUTATION_IDS[1], RELATION_IDS[1], "mutant_fixed_axis_output", "mutated_coefficient_equivariance_residual", tolerance),
        (MUTATION_IDS[2], RELATION_IDS[2], "mutant_linear_power_output", "mutated_quadratic_power_scaled_residual", tolerance),
        (MUTATION_IDS[3], RELATION_IDS[3], "mutant_drop_intercept_output", "mutated_bulk_flow_invariance_residual_kms", tolerance),
        (MUTATION_IDS[4], RELATION_IDS[4], "mutant_even_kernel", "mutated_kernel_anti_equivariance_residual", 0.0),
        (MUTATION_IDS[5], RELATION_IDS[5], "mutant_offsupport_kernel", "mutated_off_support_max_abs", 0.0),
        (MUTATION_IDS[6], RELATION_IDS[6], "mutant_plus_kernel", "mutated_m_zero_signed_sum_max_abs", 0.0),
    )
    return {
        mutation_id: {
            "relation_id": relation_id,
            "callable_id": callable_id,
            "metric_id": metric_id,
            "comparison": "le",
            "threshold": threshold,
        }
        for mutation_id, relation_id, callable_id, metric_id, threshold in rows
    }


def validate_battery(report: Mapping[str, Any], spec: Mapping[str, Any], repo: Path) -> list[str]:
    errors: list[str] = []
    recomputed_relation_passes: list[bool] = []
    recomputed_mutation_kills: list[bool] = []
    if report.get("schema") != SCHEMA:
        errors.append("result schema mismatch")
    if report.get("public_use") is not False or report.get("scientific_status") != "OPEN":
        errors.append("claim quarantine mismatch")
    if report.get("claim_level") != {"scheme": "roadmap_rescue_v1", "level": "C1"}:
        errors.append("claim level mismatch")
    expected_hashes = expected_input_hashes(spec, repo)
    expected_config_hash = expected_hashes[str(SPEC_PATH)]
    expected_content_receipt = worktree_content_receipt(expected_hashes)
    if report.get("config_hash") != expected_config_hash:
        errors.append("config hash mismatch")
    if report.get("input_hashes") != expected_hashes:
        errors.append("input hash inventory mismatch")
    if report.get("worktree_content_receipt") != expected_content_receipt:
        errors.append("worktree content receipt mismatch")
    if report.get("git_commit") != spec.get("baseline_commit"):
        errors.append("git commit mismatch")
    if report.get("worktree_state") != f"{spec.get('baseline_commit')}+content-sha256:{expected_content_receipt}":
        errors.append("worktree state mismatch")
    if report.get("covariance_status") != "mechanics_only_not_covariance_validation":
        errors.append("covariance status mismatch")
    if report.get("null_mock_status") != "not_run_not_applicable":
        errors.append("null mock status mismatch")
    relations = report.get("relations")
    mutations = report.get("mutations")
    if not isinstance(relations, list) or not relations:
        errors.append("relation registry missing or empty")
        relations = []
    if not isinstance(mutations, list) or not mutations:
        errors.append("mutation registry missing or empty")
        mutations = []
    if tuple(row.get("relation_id") for row in relations if isinstance(row, dict)) != RELATION_IDS:
        errors.append("relation identity/order mismatch")
    if tuple(row.get("mutation_id") for row in mutations if isinstance(row, dict)) != MUTATION_IDS:
        errors.append("mutation identity/order mismatch")
    relation_contract = _expected_relation_contract(spec)
    for row in relations:
        if not isinstance(row, dict):
            errors.append("relation row is not an object")
            recomputed_relation_passes.append(False)
            continue
        count = row.get("execution_count")
        if isinstance(count, bool) or count != 1:
            errors.append(f"{row.get('relation_id')}: invalid execution count")
        frozen = relation_contract.get(str(row.get("relation_id")))
        if frozen is None:
            errors.append(f"{row.get('relation_id')}: no frozen relation contract")
        elif row.get("adapter") != frozen["adapter"]:
            errors.append(f"{row.get('relation_id')}: adapter binding mismatch")
        metrics = row.get("metrics")
        if not isinstance(metrics, list) or not metrics:
            errors.append(f"{row.get('relation_id')}: metrics missing")
            recomputed_relation_passes.append(False)
            continue
        actual_metric_contract = tuple(
            (metric.get("metric_id"), metric.get("comparison"), metric.get("threshold"))
            for metric in metrics
            if isinstance(metric, dict)
        )
        if frozen is None or actual_metric_contract != frozen["metrics"]:
            errors.append(f"{row.get('relation_id')}: metric contract mismatch")
        try:
            if frozen is None or len(metrics) != len(frozen["metrics"]):
                recomputed = False
            else:
                frozen_metrics = []
                for metric, (metric_id, comparison, threshold) in zip(
                    metrics, frozen["metrics"]
                ):
                    frozen_metrics.append(
                        {
                            "metric_id": metric_id,
                            "value": _as_float(metric.get("value"), "metric.value"),
                            "threshold": threshold,
                            "comparison": comparison,
                        }
                    )
                recomputed = all(metric_passes(metric) for metric in frozen_metrics)
        except (AttributeError, MetamorphicContractError) as exc:
            errors.append(f"{row.get('relation_id')}: {exc}")
            recomputed_relation_passes.append(False)
            continue
        recomputed_relation_passes.append(recomputed)
        if row.get("passed") is not recomputed:
            errors.append(f"{row.get('relation_id')}: forged relation verdict")
    mutation_contract = _expected_mutation_contract(spec)
    for row in mutations:
        if not isinstance(row, dict):
            errors.append("mutation row is not an object")
            recomputed_mutation_kills.append(False)
            continue
        count = row.get("execution_count")
        if isinstance(count, bool) or count != 1:
            errors.append(f"{row.get('mutation_id')}: invalid execution count")
            recomputed_mutation_kills.append(False)
            continue
        frozen = mutation_contract.get(str(row.get("mutation_id")))
        if frozen is None:
            errors.append(f"{row.get('mutation_id')}: no frozen mutation contract")
            recomputed_mutation_kills.append(False)
            continue
        if row.get("relation_id") != frozen["relation_id"]:
            errors.append(f"{row.get('mutation_id')}: relation binding mismatch")
        metric = row.get("mutated_metric")
        if not isinstance(metric, dict):
            errors.append(f"{row.get('mutation_id')}: mutated metric missing")
            recomputed_mutation_kills.append(False)
            continue
        actual_metric_contract = (
            metric.get("metric_id"), metric.get("comparison"), metric.get("threshold")
        )
        expected_metric_contract = (
            frozen["metric_id"], frozen["comparison"], frozen["threshold"]
        )
        if actual_metric_contract != expected_metric_contract:
            errors.append(f"{row.get('mutation_id')}: metric contract mismatch")
        receipt = row.get("execution_receipt")
        receipt_valid = isinstance(receipt, dict)
        if not receipt_valid:
            errors.append(f"{row.get('mutation_id')}: execution receipt missing")
            receipt = {}
        invocation_count = receipt.get("invocation_count")
        if isinstance(invocation_count, bool) or invocation_count != 1:
            errors.append(f"{row.get('mutation_id')}: invalid receipt invocation count")
            receipt_valid = False
        if receipt.get("callable_id") != frozen["callable_id"] or receipt.get("invoked") is not True:
            errors.append(f"{row.get('mutation_id')}: callable execution binding mismatch")
            receipt_valid = False
        primitives = receipt.get("primitives")
        if not isinstance(primitives, dict) or not primitives:
            errors.append(f"{row.get('mutation_id')}: primitive receipt missing")
            receipt_valid = False
        elif receipt.get("primitive_sha256") != hashlib.sha256(canonical_bytes(primitives)).hexdigest():
            errors.append(f"{row.get('mutation_id')}: primitive receipt hash mismatch")
            receipt_valid = False
        try:
            activation = _as_float(row.get("activation_delta"), "activation_delta")
            witness = _as_float(row.get("witness_value"), "witness_value")
            threshold = _as_float(row.get("kill_threshold"), "kill_threshold")
        except MetamorphicContractError as exc:
            errors.append(f"{row.get('mutation_id')}: {exc}")
            recomputed_mutation_kills.append(False)
            continue
        if witness != metric.get("value") or threshold != metric.get("threshold"):
            errors.append(f"{row.get('mutation_id')}: witness/metric mismatch")
        try:
            frozen_metric = {
                "metric_id": frozen["metric_id"],
                "value": _as_float(metric.get("value"), "mutated_metric.value"),
                "threshold": frozen["threshold"],
                "comparison": frozen["comparison"],
            }
            relation_would_pass = metric_passes(frozen_metric)
        except MetamorphicContractError as exc:
            errors.append(f"{row.get('mutation_id')}: {exc}")
            relation_would_pass = True
        if row.get("relation_would_pass") is not relation_would_pass:
            errors.append(f"{row.get('mutation_id')}: forged mutated-relation verdict")
        recomputed = bool(receipt_valid and activation > 0.0 and not relation_would_pass)
        recomputed_mutation_kills.append(recomputed)
        if row.get("killed") is not recomputed:
            errors.append(f"{row.get('mutation_id')}: forged mutation verdict")
    if relations and mutations:
        recomputed_terminal = (
            "PASS_METAMORPHIC_SELF_CONSISTENCY_C1"
            if len(recomputed_relation_passes) == len(RELATION_IDS)
            and len(recomputed_mutation_kills) == len(MUTATION_IDS)
            and all(recomputed_relation_passes)
            and all(recomputed_mutation_kills)
            else "BLOCKED_METAMORPHIC_RELATION_VIOLATION"
        )
        if report.get("terminal") != recomputed_terminal:
            errors.append("forged terminal state")
        expected_adapter_status = {}
        relation_pairs = list(zip(relations, recomputed_relation_passes))
        for adapter in ("cf4_estimator", "b_projector"):
            passes = [
                passed
                for relation, passed in relation_pairs
                if isinstance(relation, dict)
                and relation_contract.get(str(relation.get("relation_id")), {}).get("adapter") == adapter
            ]
            expected_adapter_status[adapter] = (
                "PASS_REGISTERED_RELATIONS"
                if passes and all(passes)
                else "BLOCKED_METAMORPHIC_RELATION_VIOLATION"
            )
        if report.get("adapter_status") != expected_adapter_status:
            errors.append("forged adapter status")
    bindings = report.get("source_bindings")
    if not isinstance(bindings, dict):
        errors.append("source bindings missing")
    else:
        for key in ("cf4_estimator", "b_projector"):
            frozen = spec["source_bindings"][key]
            row = bindings.get(key, {})
            actual = sha256_file(repo / _live_source_path(Path(frozen["path"])))
            if row.get("actual_sha256") != actual or row.get("expected_sha256") != frozen["sha256"] or row.get("matched") is not True:
                errors.append(f"{key}: source binding mismatch")
    if report.get("semantic_digest") != semantic_digest(report):
        errors.append("semantic digest mismatch")
    return errors
