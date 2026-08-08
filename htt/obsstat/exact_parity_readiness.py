"""Executable, receipt-bound parity-equivariance readiness for PR-282.

This OBSSTAT surface executes one registered synthetic method contract.  It
does not accept a readiness boolean, consume observed data, establish the null
symmetry or no-tie premises, or produce model inference or a family label.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from numbers import Integral, Rational
from pathlib import Path
from typing import Any

from common.vector_tensor_statistical_foundations import (
    VectorTensorStatisticalFoundationError,
    load_pillar_s_core_registry,
)

from .egs3_evalue_merge import merge_evalues_arbitrary_dependence


PASS_TOKEN = "PASS_EXECUTABLE_P_EQUIVARIANCE"
BLOCK_TOKEN = "BLOCKED_P_EQUIVARIANCE"
SCHEMA = "obsstat.exact_parity_readiness.v1"
CLAIM_TIER = "diagnostic_only"
FAMILY_GATE = "BLOCKED_PRE_NATIVE_ATLAS"
_ROOT = Path(__file__).resolve().parents[2]
_PILLAR_S_REGISTRY = (
    "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml"
)

_SPEC_KEYS = {
    "schema",
    "pr_id",
    "title",
    "owner",
    "contributors",
    "change_set_id",
    "publication_group_id",
    "dependencies",
    "dependency_contract",
    "claim_tier",
    "claim_level",
    "scientific_artifact_mode",
    "transfer_source",
    "observed_data_executed",
    "public_use",
    "family_identification_gate",
    "gate",
    "theorem_boundary",
    "relation",
    "execution_fixture",
    "dependent_evalue_merge",
    "mutation_registry",
    "receipt_contract",
    "allowed_uses",
    "forbidden_uses",
    "caveats",
    "assumptions",
}
_MUTATIONS = (
    ("MU282-ESTIMATOR-ABSOLUTE", "absolute_krylov_value"),
    ("MU282-MASK-PAIR-DROP", "drop_first_support_only"),
    ("MU282-WEIGHT-PAIR-SKEW", "increment_first_weight_only"),
)
_CLAIM_LEVEL = {"scheme": "roadmap_rescue_v1", "level": "C2"}
_H2_SCOPE = "weighted Krylov estimator with a fixed selection mask and fixed weights"
_ASSUMPTIONS = (
    "Each sigma fixture is exactly symmetric and trace-free.",
    "The registered P is an orientation-reversing orthogonal involution.",
    "Arithmetic e-value merging is conditional on every input being a valid "
    "e-value under one common null.",
    "Convex merge weights are frozen before any execution output is viewed.",
)
_ALLOWED_USES = (
    "Synthetic method-readiness evidence for the registered estimator path.",
    "A prerequisite receipt for later separately admitted and authorized "
    "PR-290 execution.",
    "Arbitrary-dependence arithmetic e-value combination of individually "
    "valid e-values.",
)
_FORBIDDEN_USES = (
    "Observed-sky inference or Planck execution.",
    "Caller-supplied readiness or post-result threshold changes.",
    "Binomial pooling of dependent or nested sign vectors.",
    "Physical parity validation, native solver validation, geometry detection, "
    "or family identification.",
    "HTT likelihood, posterior, evidence, or MIO certificate production.",
)
_CAVEATS = (
    "H1 and H3 remain separate premises and are not established by a G3 pass.",
    "Mask deconvolution is not executed; H2 is closed only for the registered "
    "fixed-mask synthetic path.",
    "The fixture is synthetic and exercises one registered estimator, mask, "
    "weighting, and convention path.",
    "PR-151 partial/background data is forbidden input.",
)
_MERGE_FORBIDDEN = (
    "binomial_pooling_across_dependent_signs",
    "evalue_product_without_independence_or_supermartingale_contract",
)
_FIXTURE_STATUS = {
    "fixture_id": "pr282.synthetic.reflection_pairs.v1",
    "sky_support_status": "synthetic_reflection_paired_support",
    "mask_status": "synthetic_fixed_under_registered_reflection",
    "weighting_status": "synthetic_fixed_under_registered_reflection",
    "covariance_status": "not_used_by_exact_h2_execution",
    "null_mock_status": "not_used_by_exact_h2_execution",
}
_RECEIPT_BINDINGS = (
    "docs/research_program/post_pr275/pr282_spec.yaml",
    _PILLAR_S_REGISTRY,
    "htt/obsstat/exact_parity_readiness.py",
    "htt/obsstat/egs3_evalue_merge.py",
    "htt/src/common/vector_tensor_statistical_foundations.py",
    "scripts/codex_harness/run_pr282_exact_parity_readiness.py",
    "tests/obsstat/test_exact_parity_readiness.py",
    "tests/contracts/test_pillar_s_core.py",
)
_RECEIPT_METADATA = (
    "owner",
    "scope",
    "claim_tier_and_level",
    "transfer_source",
    "synthetic_sky_mask_weighting_status",
    "covariance_and_null_status",
    "assumptions",
    "caveats",
    "generating_command_or_procedure",
    "git_commit_or_worktree_state",
)
_MUTATION_RULE = (
    "Every registered mutation must execute, differ on its intended surface, "
    "and be killed. Missing, skipped, unmapped, or surviving mutations block G3."
)
_MUTATION_RESULT_KEYS = {
    "mutation_id",
    "mutation_kind",
    "executed",
    "activated",
    "killed",
    "observed_outcome",
    "observed_reasons",
    "relation_residual",
}
_MUTATION_EXPECTED_REASON = {
    "MU282-ESTIMATOR-ABSOLUTE": ("ESTIMATOR_RELATION_FAILED",),
    "MU282-MASK-PAIR-DROP": (
        "MASK_NOT_FIXED_BY_P",
        "ESTIMATOR_RELATION_FAILED",
    ),
    "MU282-WEIGHT-PAIR-SKEW": (
        "WEIGHTING_NOT_FIXED_BY_P",
        "ESTIMATOR_RELATION_FAILED",
    ),
}


class ParityReadinessError(ValueError):
    """Raised when the frozen PR-282 execution contract is structurally invalid."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ParityReadinessError(f"{name} must be a mapping")
    return value


def _sequence(value: object, name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ParityReadinessError(f"{name} must be a sequence")
    return tuple(value)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ParityReadinessError(f"{name} must be non-empty trimmed text")
    return value


def _texts(value: object, name: str) -> tuple[str, ...]:
    return tuple(_text(item, name) for item in _sequence(value, name))


def _fraction(value: object, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, Rational):
        raise ParityReadinessError(f"{name} must be an exact rational")
    if isinstance(value, Integral):
        return Fraction(int(value), 1)
    return Fraction(value)


def _fraction_payload(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _fraction_from_payload(value: object, name: str) -> Fraction:
    row = _mapping(value, name)
    if set(row) != {"numerator", "denominator"}:
        raise ParityReadinessError(f"{name} must contain numerator and denominator")
    numerator = row["numerator"]
    denominator = row["denominator"]
    if (
        isinstance(numerator, bool)
        or isinstance(denominator, bool)
        or not isinstance(numerator, int)
        or not isinstance(denominator, int)
        or denominator <= 0
    ):
        raise ParityReadinessError(f"{name} must be a finite exact fraction")
    return Fraction(numerator, denominator)


def _matrix(value: object, name: str) -> tuple[tuple[Fraction, ...], ...]:
    rows = _sequence(value, name)
    if len(rows) != 3:
        raise ParityReadinessError(f"{name} must be a 3x3 matrix")
    matrix = tuple(
        tuple(_fraction(item, name) for item in _sequence(row, name))
        for row in rows
    )
    if any(len(row) != 3 for row in matrix):
        raise ParityReadinessError(f"{name} must be a 3x3 matrix")
    return matrix


def _vector(value: object, name: str) -> tuple[Fraction, ...]:
    vector = tuple(_fraction(item, name) for item in _sequence(value, name))
    if len(vector) != 3:
        raise ParityReadinessError(f"{name} must be a 3-vector")
    return vector


def _matmul(
    left: tuple[tuple[Fraction, ...], ...],
    right: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(
        tuple(
            sum(
                (left[row][inner] * right[inner][column] for inner in range(3)),
                start=Fraction(0, 1),
            )
            for column in range(3)
        )
        for row in range(3)
    )


def _matvec(
    matrix: tuple[tuple[Fraction, ...], ...],
    vector: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    return tuple(
        sum(
            (matrix[row][column] * vector[column] for column in range(3)),
            start=Fraction(0, 1),
        )
        for row in range(3)
    )


def _transpose(
    matrix: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(matrix[column][row] for column in range(3)) for row in range(3))


def _determinant(matrix: tuple[tuple[Fraction, ...], ...]) -> Fraction:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def _krylov(
    sigma: tuple[tuple[Fraction, ...], ...],
    beta: tuple[Fraction, ...],
    *,
    absolute: bool,
) -> Fraction:
    sigma_beta = _matvec(sigma, beta)
    sigma2_beta = _matvec(sigma, sigma_beta)
    columns = tuple(
        tuple(column[row] for column in (beta, sigma_beta, sigma2_beta))
        for row in range(3)
    )
    result = _determinant(columns)
    return abs(result) if absolute else result


def _parse_contract(spec: Mapping[str, Any]) -> dict[str, Any]:
    unexpected = sorted(set(spec) - _SPEC_KEYS)
    missing = sorted(_SPEC_KEYS - set(spec))
    if unexpected:
        raise ParityReadinessError(
            "unexpected top-level PR-282 spec field(s): " + ", ".join(unexpected)
        )
    if missing:
        raise ParityReadinessError(
            "missing top-level PR-282 spec field(s): " + ", ".join(missing)
        )
    if spec["schema"] != "htt.pr282.exact_parity_readiness_spec.v1":
        raise ParityReadinessError("PR-282 spec schema drifted")
    if (
        spec["pr_id"] != "PR-282"
        or spec["owner"] != "OBSSTAT"
        or spec["title"] != "Exact parity readiness and executable P-equivariance"
    ):
        raise ParityReadinessError("PR-282 identity or owner drifted")
    if (
        spec["change_set_id"] != "CS-PR282-EXACT-PARITY"
        or spec["publication_group_id"] != "PG-PR282-EXACT-PARITY"
    ):
        raise ParityReadinessError("PR-282 change-set or publication-group identity drifted")
    if _texts(spec["contributors"], "contributors") != ("COMMON",):
        raise ParityReadinessError("PR-282 contributors drifted")
    if (
        _texts(spec["dependencies"], "dependencies") != ("PR-280",)
        or dict(_mapping(spec["dependency_contract"], "dependency_contract"))
        != {"upstream_id": "PR-280", "mode": "requires_terminal_receipt"}
    ):
        raise ParityReadinessError("PR-282 dependency contract drifted")
    if (
        spec["claim_tier"] != CLAIM_TIER
        or dict(_mapping(spec["claim_level"], "claim_level")) != _CLAIM_LEVEL
        or spec["scientific_artifact_mode"] != "synthetic_diagnostic"
    ):
        raise ParityReadinessError("PR-282 claim tier drifted")
    if spec["transfer_source"] != "none":
        raise ParityReadinessError("PR-282 transfer source must remain none")
    if spec["observed_data_executed"] is not False or spec["public_use"] is not False:
        raise ParityReadinessError("PR-282 cannot execute observed data or enable public use")
    if spec["family_identification_gate"] != FAMILY_GATE:
        raise ParityReadinessError("PR-282 family-identification gate drifted")

    gate = _mapping(spec["gate"], "gate")
    if (
        gate.get("gate_id") != "G3"
        or gate.get("statement")
        != "Estimator, mask, and weighting pass executable parity equivariance."
        or gate.get("pass_token") != PASS_TOKEN
        or gate.get("block_token") != BLOCK_TOKEN
        or gate.get("derivation_rule")
        != (
            "The terminal token is recomputed from clean primitive executions "
            "and the complete registered mutation battery. No caller-supplied "
            "readiness, pass, or threshold field is accepted."
        )
        or set(gate) != {
            "gate_id",
            "statement",
            "pass_token",
            "block_token",
            "derivation_rule",
        }
    ):
        raise ParityReadinessError("PR-282 G3 terminal contract drifted")

    theorem = _mapping(spec["theorem_boundary"], "theorem_boundary")
    if theorem.get("h2_p_equivariant_estimator") != (
        "EXECUTED_REGISTERED_SYNTHETIC_PATH_ONLY"
    ):
        raise ParityReadinessError("PR-282 must execute only the registered synthetic H2 path")
    if (
        theorem.get("source_obligation") != "TF-09-PARITY-SIGN-EXACTNESS"
        or theorem.get("h1_reflection_symmetric_null")
        != "NOT_EVALUATED_METHOD_ONLY"
        or theorem.get("h2_executed_scope") != _H2_SCOPE
        or theorem.get("h3_no_atom_at_zero")
        != "CONDITIONAL_AND_NOT_ESTABLISHED_BY_G3"
    ):
        raise ParityReadinessError("PR-282 theorem boundary drifted")
    if _texts(theorem.get("h2_not_executed"), "h2_not_executed") != (
        "mask_deconvolution",
        "observed_selection_function",
        "point_source_hole_correction",
    ):
        raise ParityReadinessError("PR-282 H2 exclusions drifted")
    if set(theorem) != {
        "source_obligation",
        "h1_reflection_symmetric_null",
        "h2_p_equivariant_estimator",
        "h2_executed_scope",
        "h2_not_executed",
        "h3_no_atom_at_zero",
        "consequence_if_all_three_hold",
        "forbidden_inference",
    }:
        raise ParityReadinessError("PR-282 theorem boundary drifted")
    if theorem.get("consequence_if_all_three_hold") != (
        "The nonzero parity-odd sign is an exact fair Bernoulli bit under the "
        "registered null. PR-282 establishes only the executable H2 method gate."
    ) or theorem.get("forbidden_inference") != (
        "A G3 pass does not establish H1, H3, observed-sky validity, a physical "
        "parity claim, transfer validation, geometry detection, or family "
        "identification."
    ):
        raise ParityReadinessError("PR-282 theorem boundary drifted")

    relation = _mapping(spec["relation"], "relation")
    if (
        set(relation)
        != {
            "relation_id",
            "relation_class",
            "estimator_id",
            "estimator_definition",
            "input_action",
            "output_action",
            "reflection_matrix",
            "support_permutation",
            "coordinate_frame",
            "handedness",
            "parity_exponent",
            "expected_output_sign",
            "numeric_contract",
            "mask_action",
            "weighting_action",
        }
        or relation.get("relation_id") != "PR282-P-EQUIVARIANCE-001"
        or relation.get("relation_class") != "ANTI_EQUIVARIANT"
        or relation.get("estimator_id") != "weighted_krylov_pseudoscalar_mean.v1"
        or relation.get("estimator_definition")
        != (
            "On each registered support element compute "
            "K_beta=det[beta,sigma beta,sigma^2 beta], then take the masked "
            "convex weighted mean over active support."
        )
        or relation.get("input_action")
        != (
            "Apply the registered support involution and transform sigma to "
            "P sigma P^T and beta to P beta."
        )
        or relation.get("output_action")
        != "psi_hat maps exactly to minus psi_hat."
        or relation.get("expected_output_sign") != -1
        or relation.get("numeric_contract")
        != "exact_rational_arithmetic_no_tolerance"
        or relation.get("coordinate_frame")
        != "synthetic_registered_cartesian_right_handed"
        or relation.get("handedness")
        != "right_handed_input_frame_with_orientation_reversing_P"
        or relation.get("parity_exponent") != 1
        or relation.get("mask_action")
        != "fixed_under_registered_support_permutation"
        or relation.get("weighting_action")
        != "fixed_under_registered_support_permutation"
    ):
        raise ParityReadinessError("PR-282 relation contract drifted")
    reflection = _matrix(relation.get("reflection_matrix"), "reflection_matrix")
    identity = tuple(
        tuple(Fraction(int(row == column), 1) for column in range(3))
        for row in range(3)
    )
    if _matmul(reflection, _transpose(reflection)) != identity:
        raise ParityReadinessError("reflection_matrix must be exactly orthogonal")
    if _determinant(reflection) != -1:
        raise ParityReadinessError("reflection_matrix must reverse orientation")
    if _matmul(reflection, reflection) != identity:
        raise ParityReadinessError("reflection_matrix must be an exact involution")

    raw_permutation = _sequence(relation.get("support_permutation"), "support_permutation")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in raw_permutation):
        raise ParityReadinessError("support_permutation must contain integers")
    permutation = tuple(int(value) for value in raw_permutation)
    if set(permutation) != set(range(len(permutation))):
        raise ParityReadinessError("support_permutation must be a permutation")
    if any(permutation[permutation[index]] != index for index in range(len(permutation))):
        raise ParityReadinessError("support_permutation must be an involution")

    fixture = _mapping(spec["execution_fixture"], "execution_fixture")
    if set(fixture) != {
        "fixture_id",
        "sigma_by_support",
        "beta_by_support",
        "mask",
        "weights",
        "sky_support_status",
        "mask_status",
        "weighting_status",
        "covariance_status",
        "null_mock_status",
    } or any(
        fixture.get(field) != expected
        for field, expected in _FIXTURE_STATUS.items()
    ):
        raise ParityReadinessError("PR-282 execution fixture metadata drifted")
    sigmas = tuple(
        _matrix(item, "sigma_by_support")
        for item in _sequence(fixture.get("sigma_by_support"), "sigma_by_support")
    )
    betas = tuple(
        _vector(item, "beta_by_support")
        for item in _sequence(fixture.get("beta_by_support"), "beta_by_support")
    )
    masks = _sequence(fixture.get("mask"), "mask")
    if any(type(value) is not bool for value in masks):
        raise ParityReadinessError("mask must contain booleans")
    mask = tuple(bool(value) for value in masks)
    weights = tuple(
        _fraction(value, "weights")
        for value in _sequence(fixture.get("weights"), "weights")
    )
    size = len(permutation)
    if not size or not (len(sigmas) == len(betas) == len(mask) == len(weights) == size):
        raise ParityReadinessError("fixture, mask, weights, and support action must align")
    if any(weight < 0 for weight in weights):
        raise ParityReadinessError("weights must be nonnegative")
    if not any(active and weight > 0 for active, weight in zip(mask, weights, strict=True)):
        raise ParityReadinessError("fixture requires positive active weight")
    for sigma in sigmas:
        if sigma != _transpose(sigma):
            raise ParityReadinessError("sigma_by_support must be exactly symmetric")
        if sum((sigma[index][index] for index in range(3)), start=Fraction(0, 1)) != 0:
            raise ParityReadinessError("sigma_by_support must be exactly trace-free")

    mutation_rows = tuple(
        _mapping(row, "mutation_registry")
        for row in _sequence(spec["mutation_registry"], "mutation_registry")
    )
    if any(
        set(row)
        != {"mutation_id", "mutation_kind", "intended_defect", "expected_kill"}
        for row in mutation_rows
    ):
        raise ParityReadinessError("PR-282 mutation registry drifted")
    registered = tuple(
        (row.get("mutation_id"), row.get("mutation_kind")) for row in mutation_rows
    )
    mutation_annotations = tuple(
        (row.get("intended_defect"), row.get("expected_kill"))
        for row in mutation_rows
    )
    if registered != _MUTATIONS or mutation_annotations != (
        (
            "erase the parity-odd estimator sign",
            "clean anti-equivariance relation fails",
        ),
        (
            "break mask invariance within a reflection pair",
            "mask equivariance precondition blocks G3",
        ),
        (
            "break weighting invariance within a reflection pair",
            "weighting equivariance precondition blocks G3",
        ),
    ):
        raise ParityReadinessError("PR-282 mutation registry drifted")

    receipt_contract = _mapping(spec["receipt_contract"], "receipt_contract")
    expected_receipt_contract = {
        "output_path": "docs/generated/pr282_exact_parity_readiness_receipt.json",
        "content_address": (
            "sha256_of_canonical_json_excluding_receipt_content_sha256"
        ),
        "required_bindings": list(_RECEIPT_BINDINGS),
        "terminal_precedence": [
            "BLOCKED_CONTRACT_INVALID",
            BLOCK_TOKEN,
            PASS_TOKEN,
        ],
        "mutation_rule": _MUTATION_RULE,
        "required_metadata": list(_RECEIPT_METADATA),
    }
    if dict(receipt_contract) != expected_receipt_contract:
        raise ParityReadinessError("PR-282 receipt contract drifted")

    assumptions = _texts(spec["assumptions"], "assumptions")
    if assumptions != _ASSUMPTIONS:
        raise ParityReadinessError("PR-282 assumptions drifted")

    allowed_uses = _texts(spec["allowed_uses"], "allowed_uses")
    forbidden_uses = _texts(spec["forbidden_uses"], "forbidden_uses")
    caveats = _texts(spec["caveats"], "caveats")
    if allowed_uses != _ALLOWED_USES:
        raise ParityReadinessError("PR-282 allowed uses drifted")
    if forbidden_uses != _FORBIDDEN_USES:
        raise ParityReadinessError("PR-282 forbidden uses drifted")
    if caveats != _CAVEATS:
        raise ParityReadinessError("PR-282 caveats drifted")

    merge = _mapping(spec["dependent_evalue_merge"], "dependent_evalue_merge")
    if (
        set(merge)
        != {
            "merge_id",
            "dependence_class",
            "combination_rule",
            "common_null_id",
            "input_validity_status",
            "weight_registration_status",
            "inputs",
            "weights",
            "forbidden_combinations",
        }
        or merge.get("merge_id") != "pr282.synthetic.dependent-sign-vectors.v1"
        or merge.get("dependence_class") != "ARBITRARY_OR_DEPENDENT"
        or merge.get("combination_rule") != "CONVEX_ARITHMETIC_MEAN"
        or merge.get("common_null_id") != "pr282.synthetic.common-null.v1"
        or merge.get("input_validity_status")
        != "CONDITIONAL_ON_EACH_INPUT_BEING_A_VALID_EVALUE_UNDER_COMMON_NULL"
        or merge.get("weight_registration_status")
        != "FIXED_IN_SPEC_BEFORE_EXECUTION"
        or _texts(
            merge.get("forbidden_combinations"),
            "dependent_evalue_merge.forbidden_combinations",
        )
        != _MERGE_FORBIDDEN
    ):
        raise ParityReadinessError("dependent e-value merge contract drifted")
    merge_inputs = tuple(
        _mapping(row, "dependent_evalue_merge.inputs")
        for row in _sequence(merge["inputs"], "dependent_evalue_merge.inputs")
    )
    if any(
        set(row) != {"vector_id", "numerator", "denominator"}
        for row in merge_inputs
    ):
        raise ParityReadinessError(
            "dependent e-value input row must contain only vector_id, numerator, and denominator"
        )
    labels = tuple(_text(row.get("vector_id"), "vector_id") for row in merge_inputs)
    e_values = tuple(
        _fraction_from_payload(
            {
                "numerator": row.get("numerator"),
                "denominator": row.get("denominator"),
            },
            "e_value",
        )
        for row in merge_inputs
    )
    merge_weights = tuple(
        _fraction_from_payload(row, "e_value weight")
        for row in _sequence(merge["weights"], "dependent_evalue_merge.weights")
    )

    try:
        source_registry = load_pillar_s_core_registry(_ROOT)
        source_record = source_registry.record(theorem["source_obligation"])
    except VectorTensorStatisticalFoundationError as exc:
        raise ParityReadinessError(
            f"authoritative Pillar-S source obligation is invalid: {exc}"
        ) from exc
    source_obligation_record = {
        "registry_path": _PILLAR_S_REGISTRY,
        "registry_sha256": source_registry.registry_sha256,
        "obligation_id": source_record.obligation_id,
        "source_status": source_record.source_status,
        "source_proof_adjudication_status": (
            source_record.source_proof_adjudication_status
        ),
        "source_statement_identity_sha256": (
            source_record.source_statement_identity_sha256
        ),
        "relation_to_source": source_record.relation_to_source,
        "evidence_grade": source_record.evidence_grade.value,
        "verdict": source_record.verdict.value,
        "claim_ceiling": source_record.claim_ceiling,
    }

    return {
        "relation": relation,
        "theorem": theorem,
        "reflection": reflection,
        "permutation": permutation,
        "fixture": fixture,
        "sigmas": sigmas,
        "betas": betas,
        "mask": mask,
        "weights": weights,
        "merge": merge,
        "merge_labels": labels,
        "merge_e_values": e_values,
        "merge_weights": merge_weights,
        "assumptions": assumptions,
        "allowed_uses": allowed_uses,
        "forbidden_uses": forbidden_uses,
        "caveats": caveats,
        "receipt_contract": receipt_contract,
        "source_obligation_record": source_obligation_record,
    }


def _weighted_estimate(
    *,
    sigmas: tuple[tuple[tuple[Fraction, ...], ...], ...],
    betas: tuple[tuple[Fraction, ...], ...],
    mask: tuple[bool, ...],
    weights: tuple[Fraction, ...],
    absolute: bool,
) -> tuple[Fraction, tuple[Fraction, ...]]:
    components = tuple(
        _krylov(sigma, beta, absolute=absolute)
        for sigma, beta in zip(sigmas, betas, strict=True)
    )
    total_weight = sum(
        (weight for active, weight in zip(mask, weights, strict=True) if active),
        start=Fraction(0, 1),
    )
    if total_weight <= 0:
        raise ParityReadinessError("estimator requires positive active weight")
    total = sum(
        (
            weight * component
            for active, weight, component in zip(mask, weights, components, strict=True)
            if active
        ),
        start=Fraction(0, 1),
    )
    return total / total_weight, components


def _transformed_fixture(contract: Mapping[str, Any]) -> tuple[
    tuple[tuple[tuple[Fraction, ...], ...], ...],
    tuple[tuple[Fraction, ...], ...],
]:
    reflection = contract["reflection"]
    reflection_t = _transpose(reflection)
    sigmas = tuple(
        _matmul(
            _matmul(reflection, contract["sigmas"][source_index]),
            reflection_t,
        )
        for source_index in contract["permutation"]
    )
    betas = tuple(
        _matvec(reflection, contract["betas"][source_index])
        for source_index in contract["permutation"]
    )
    return sigmas, betas


def _execute(
    contract: Mapping[str, Any],
    *,
    mask: tuple[bool, ...] | None = None,
    weights: tuple[Fraction, ...] | None = None,
    absolute: bool = False,
) -> dict[str, Any]:
    mask_i = contract["mask"] if mask is None else mask
    weights_i = contract["weights"] if weights is None else weights
    baseline, components = _weighted_estimate(
        sigmas=contract["sigmas"],
        betas=contract["betas"],
        mask=mask_i,
        weights=weights_i,
        absolute=absolute,
    )
    transformed_sigmas, transformed_betas = _transformed_fixture(contract)
    transformed, transformed_components = _weighted_estimate(
        sigmas=transformed_sigmas,
        betas=transformed_betas,
        mask=mask_i,
        weights=weights_i,
        absolute=absolute,
    )
    permutation = contract["permutation"]
    mask_equivariant = all(mask_i[index] == mask_i[permutation[index]] for index in range(len(mask_i)))
    weighting_equivariant = all(
        weights_i[index] == weights_i[permutation[index]] for index in range(len(weights_i))
    )
    expected_sign = Fraction(int(contract["relation"]["expected_output_sign"]), 1)
    residual = transformed - expected_sign * baseline
    relation_passed = residual == 0
    reasons: list[str] = []
    if not mask_equivariant:
        reasons.append("MASK_NOT_FIXED_BY_P")
    if not weighting_equivariant:
        reasons.append("WEIGHTING_NOT_FIXED_BY_P")
    if not relation_passed:
        reasons.append("ESTIMATOR_RELATION_FAILED")
    outcome = PASS_TOKEN if not reasons else BLOCK_TOKEN
    return {
        "baseline": _fraction_payload(baseline),
        "transformed": _fraction_payload(transformed),
        "baseline_components": [_fraction_payload(value) for value in components],
        "transformed_components": [
            _fraction_payload(value) for value in transformed_components
        ],
        "relation_residual": _fraction_payload(residual),
        "mask_equivariant": mask_equivariant,
        "weighting_equivariant": weighting_equivariant,
        "relation_passed": relation_passed,
        "outcome": outcome,
        "reasons": reasons,
    }


def _run_mutations(contract: Mapping[str, Any], clean: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mutation_id, mutation_kind in _MUTATIONS:
        if mutation_kind == "absolute_krylov_value":
            execution = _execute(contract, absolute=True)
            activated = execution["baseline_components"] != clean["baseline_components"]
        elif mutation_kind == "drop_first_support_only":
            mask = list(contract["mask"])
            mask[0] = False
            activated = tuple(mask) != contract["mask"]
            execution = _execute(contract, mask=tuple(mask))
        elif mutation_kind == "increment_first_weight_only":
            weights = list(contract["weights"])
            weights[0] += Fraction(1, 1)
            activated = tuple(weights) != contract["weights"]
            execution = _execute(contract, weights=tuple(weights))
        else:  # pragma: no cover - registry validation is exhaustive
            raise ParityReadinessError(f"unhandled mutation kind: {mutation_kind}")
        killed = bool(activated and execution["outcome"] == BLOCK_TOKEN)
        rows.append(
            {
                "mutation_id": mutation_id,
                "mutation_kind": mutation_kind,
                "executed": True,
                "activated": bool(activated),
                "killed": killed,
                "observed_outcome": execution["outcome"],
                "observed_reasons": execution["reasons"],
                "relation_residual": execution["relation_residual"],
            }
        )
    return rows


def _validate_mutation_results(
    mutations: Sequence[Mapping[str, Any]],
) -> tuple[list[str], list[str]]:
    """Derive fail-closed terminal evidence from the returned mutation rows."""

    expected_pairs = tuple(_MUTATIONS)
    actual_pairs: list[tuple[object, object]] = []
    invalid_ids: list[str] = []
    counts = {mutation_id: 0 for mutation_id, _ in expected_pairs}
    structurally_consistent = True

    for index, raw_row in enumerate(mutations):
        row = _mapping(raw_row, "mutation result")
        mutation_id = row.get("mutation_id")
        mutation_kind = row.get("mutation_kind")
        actual_pairs.append((mutation_id, mutation_kind))
        if isinstance(mutation_id, str) and mutation_id in counts:
            counts[mutation_id] += 1
        row_id = mutation_id if isinstance(mutation_id, str) else f"row:{index}"

        expected_reasons = _MUTATION_EXPECTED_REASON.get(mutation_id)
        observed_reasons = row.get("observed_reasons")
        reasons_valid = (
            isinstance(observed_reasons, list)
            and expected_reasons is not None
            and tuple(observed_reasons) == expected_reasons
        )
        try:
            residual = _fraction_from_payload(
                row.get("relation_residual"),
                "mutation relation_residual",
            )
            residual_valid = residual != 0
        except ParityReadinessError:
            residual_valid = False

        flags_valid = (
            type(row.get("executed")) is bool
            and row["executed"] is True
            and type(row.get("activated")) is bool
            and row["activated"] is True
            and type(row.get("killed")) is bool
            and row["killed"] is True
            and row.get("observed_outcome") == BLOCK_TOKEN
        )
        row_consistent = (
            set(row) == _MUTATION_RESULT_KEYS
            and flags_valid
            and reasons_valid
            and residual_valid
        )
        if not row_consistent:
            structurally_consistent = False
            invalid_ids.append(row_id)

    exact_coverage = tuple(actual_pairs) == expected_pairs
    for mutation_id, count in counts.items():
        if count != 1:
            invalid_ids.append(mutation_id)
    for mutation_id, _ in actual_pairs:
        if isinstance(mutation_id, str) and mutation_id not in counts:
            invalid_ids.append(mutation_id)
    if not exact_coverage and not invalid_ids:
        invalid_ids.extend(mutation_id for mutation_id, _ in expected_pairs)

    if exact_coverage and structurally_consistent:
        return [], []
    survivors = list(dict.fromkeys(invalid_ids))
    return ["REGISTERED_MUTATION_RESULTS_INCOMPLETE_OR_INCONSISTENT"], survivors


def _build_unsigned_receipt(spec: Mapping[str, Any]) -> dict[str, Any]:
    contract = _parse_contract(spec)
    clean = _execute(contract)
    mutations = _run_mutations(contract, clean)
    mutation_reasons, survivors = _validate_mutation_results(mutations)
    reasons = list(clean["reasons"])
    reasons.extend(mutation_reasons)
    outcome = PASS_TOKEN if not reasons else BLOCK_TOKEN

    merge_report = merge_evalues_arbitrary_dependence(
        labels=contract["merge_labels"],
        e_values=contract["merge_e_values"],
        weights=contract["merge_weights"],
    )
    relation = contract["relation"]
    fixture = contract["fixture"]
    mask_payload = list(contract["mask"])
    weight_payload = [_fraction_payload(value) for value in contract["weights"]]
    convention_payload = {
        "relation_id": relation["relation_id"],
        "relation_class": relation["relation_class"],
        "coordinate_frame": relation["coordinate_frame"],
        "handedness": relation["handedness"],
        "parity_exponent": relation["parity_exponent"],
        "expected_output_sign": relation["expected_output_sign"],
        "reflection_matrix": relation["reflection_matrix"],
        "support_permutation": relation["support_permutation"],
        "numeric_contract": relation["numeric_contract"],
    }
    merge_payload = {
        "merge_id": contract["merge"]["merge_id"],
        "combination_rule": merge_report.combination_rule,
        "dependence_class": merge_report.dependence_class,
        "independence_assumed": merge_report.independence_assumed,
        "common_null_required": merge_report.common_null_required,
        "common_null_id": contract["merge"]["common_null_id"],
        "input_validity_status": contract["merge"]["input_validity_status"],
        "prespecified_weights_required": merge_report.prespecified_weights_required,
        "weight_registration_status": contract["merge"][
            "weight_registration_status"
        ],
        "validity_scope": merge_report.validity_scope,
        "inputs": [
            {
                "vector_id": label,
                "e_value": _fraction_payload(value),
                "weight": _fraction_payload(weight),
            }
            for label, value, weight in zip(
                merge_report.labels,
                merge_report.e_values,
                merge_report.weights,
                strict=True,
            )
        ],
        "merged_e_value": _fraction_payload(merge_report.merged_e_value),
        "pooled_sign_count": None,
    }
    clean_payload = dict(clean)
    clean_payload.pop("outcome")
    clean_payload.pop("reasons")
    return {
        "schema": SCHEMA,
        "owner": "OBSSTAT",
        "contributors": ["COMMON"],
        "scope": "synthetic executable P-equivariance method readiness",
        "claim_tier": CLAIM_TIER,
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "synthetic_diagnostic",
        "transfer_source": "none",
        "sky_support_status": fixture["sky_support_status"],
        "mask_status": fixture["mask_status"],
        "weighting_status": fixture["weighting_status"],
        "covariance_status": fixture["covariance_status"],
        "null_mock_status": fixture["null_mock_status"],
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": FAMILY_GATE,
        "content_bindings": {
            "spec_semantic_sha256": _sha256(spec),
            "fixture_content_sha256": _sha256(
                {
                    "fixture_id": fixture["fixture_id"],
                    "sigma_by_support": fixture["sigma_by_support"],
                    "beta_by_support": fixture["beta_by_support"],
                }
            ),
            "estimator_content_sha256": _sha256(
                {
                    "estimator_id": relation["estimator_id"],
                    "estimator_definition": relation["estimator_definition"],
                }
            ),
            "mask_content_sha256": _sha256(mask_payload),
            "weighting_content_sha256": _sha256(weight_payload),
            "convention_content_sha256": _sha256(convention_payload),
            "mutation_registry_content_sha256": _sha256(spec["mutation_registry"]),
            "receipt_contract_content_sha256": _sha256(spec["receipt_contract"]),
        },
        "theorem_boundary": {
            "source_obligation": contract["theorem"]["source_obligation"],
            "source_obligation_record": contract["source_obligation_record"],
            "h1_reflection_symmetric_null": contract["theorem"][
                "h1_reflection_symmetric_null"
            ],
            "h2_p_equivariant_estimator": contract["theorem"][
                "h2_p_equivariant_estimator"
            ],
            "h2_executed_scope": contract["theorem"]["h2_executed_scope"],
            "h2_not_executed": list(contract["theorem"]["h2_not_executed"]),
            "h3_no_atom_at_zero": contract["theorem"]["h3_no_atom_at_zero"],
        },
        "relation": {
            "estimator_id": relation["estimator_id"],
            **convention_payload,
            "mask_action": relation["mask_action"],
            "weighting_action": relation["weighting_action"],
        },
        "clean_execution": clean_payload,
        "dependent_evalue_merge": merge_payload,
        "mutations": mutations,
        "terminal": {
            "gate_id": "G3",
            "g3_outcome": outcome,
            "reasons": reasons,
            "mutation_survivors": survivors,
            "scientific_status": "OPEN_UNCHANGED",
        },
        "assumptions": list(contract["assumptions"]),
        "generating_procedure": (
            "obsstat.exact_parity_readiness.build_parity_readiness_receipt "
            "from frozen exact primitives"
        ),
        "allowed_uses": list(contract["allowed_uses"]),
        "forbidden_uses": list(contract["forbidden_uses"]),
        "caveats": list(contract["caveats"]),
    }


def build_parity_readiness_receipt(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the frozen primitives and return a self-addressed G3 receipt."""

    if not isinstance(spec, Mapping):
        raise ParityReadinessError("spec must be a mapping")
    unsigned = _build_unsigned_receipt(deepcopy(dict(spec)))
    return {**unsigned, "receipt_content_sha256": _sha256(unsigned)}


def validate_parity_readiness_receipt(
    receipt: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> tuple[str, ...]:
    """Recompute every derived field and reject even a rehashed forged verdict."""

    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        return ("receipt must be a mapping",)
    recorded_hash = receipt.get("receipt_content_sha256")
    unsigned = dict(receipt)
    unsigned.pop("receipt_content_sha256", None)
    if recorded_hash != _sha256(unsigned):
        errors.append("receipt_content_sha256 mismatch")
    try:
        expected = build_parity_readiness_receipt(spec)
    except (ParityReadinessError, ValueError) as exc:
        errors.append(f"spec cannot reproduce receipt: {exc}")
        return tuple(errors)
    if dict(receipt) != expected:
        errors.append("receipt differs from recomputed receipt")
    return tuple(errors)


__all__ = [
    "BLOCK_TOKEN",
    "PASS_TOKEN",
    "ParityReadinessError",
    "build_parity_readiness_receipt",
    "validate_parity_readiness_receipt",
]
