#!/usr/bin/env python3
"""Pure, fail-closed WU-009 claim boundary for future Paper-A generation.

This module validates the sealed map-free Gate-A/Gate-C authority.  It does
not import the legacy observation stack, read numerical Paper-A inputs, or
authorize regeneration of the frozen manuscript.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import re
from typing import Any


BOUNDARY_FORMAT = "PLANCK_MES_WU009_CLAIM_BOUNDARY_V1"
EXPECTED_SOURCE_SHA256 = {
    "ledger": "aeabb89ca8fae2f343d72e2933ada8f106a6f35864abc59ac6d7973e5f70ce62",
    "reconciliation": "e38464baacb2b16b2c007c74ef338231a8f25a4c326baa53d54d0817a4d6ff00",
    "terminal": "10e13dfb6efb8c0e46914ec61125904ff757e9ab9db463a50c120c6fdc208e9e",
}
EXPECTED_SOURCE_PATHS = {
    "ledger": "docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json",
    "reconciliation": "docs/generated/planck_mes_wu009_reconciliation/reconciliation.json",
    "terminal": "docs/generated/planck_mes_wu009_reconciliation/terminal.json",
}
EXPECTED_VERDICT_COUNTS = {
    "CORRECTED": 5,
    "PROVED": 61,
    "REFUTED": 5,
    "STRENGTHENED": 5,
    "UNDEFINED": 2,
}
EXPECTED_SPECIAL_IDS = {
    "CORRECTED": ("A03", "B21", "C14", "E02", "E06"),
    "REFUTED": ("A10", "A11", "C07", "D08", "E15"),
    "UNDEFINED": ("C18", "E05"),
}
EXPECTED_REPLACEMENTS = {
    "A03": "Four named generators separate O(3), not SO(3); proper-rotation separation needs the degree-15 parity/chirality datum.",
    "A10": "No equivariant full frame exists on every stratum with nontrivial stabilizer; the procedure must abstain or use stratum-specific invariants.",
    "A11": "Ordinary power plus bispectrum is not equivalent to full Krylov data.",
    "B21": "One-sided remainder control does not imply Hausdorff stability; a shared two-sided parameterization is required.",
    "C07": "An orthogonal residual alone does not make beta unidentified; an unrestricted additive octupole nuisance can.",
    "C11": "Every strictly positive quadratic sky has a unique finite rotation-free-boost/positive-M representation; boundary cases with zeros are excluded, and the result identifies a representation rather than its physical cause.",
    "C18": "The proposed projective T/Q/U generalization is undefined; arbitrary polarization has no universal finite quadratic closure, while strictly unpolarized emission preserves only Q=U=0.",
    "E01": "Weak finite ranks are superuniform, not generally uniform with ties, under joint exchangeability and a row-equivariant full scoring pipeline; this is not a guarantee conditional on every frozen reference pool.",
    "E02": "Increasing transformations preserve a tail; decreasing transformations send the LOO midrank to 1-u and require an upper/lower tail swap.",
    "E06": "Total variation directly controls event probabilities; Wasserstein distance alone does not, while a calibrated p-value coupling plus anti-concentration-type input is an additional route.",
    "E14": "Shared-data marginal e-values cannot generally be multiplied as if independent; E1=E2=2B has marginal mean one but product mean two.",
    "E15": "Selection independence is not necessary; exact symmetry and conditioning can preserve uniform query labels after symmetric data-dependent selection.",
}


class Wu009ClaimBoundaryError(RuntimeError):
    """Raised when WU-009 authority is missing, tampered, or promoted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Wu009ClaimBoundaryError(message)


def _expected_row_ids() -> tuple[str, ...]:
    return (
        *(f"A{index:02d}" for index in range(1, 15)),
        *(f"B{index:02d}" for index in range(1, 23)),
        *(f"C{index:02d}" for index in range(1, 19)),
        *(f"D{index:02d}" for index in range(1, 9)),
        *(f"E{index:02d}" for index in range(1, 17)),
    )


def _read_exact_json(path: Path | str, *, label: str) -> tuple[dict[str, Any], str]:
    source = Path(path)
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise Wu009ClaimBoundaryError(f"{label} source is unavailable: {source}") from exc
    digest = hashlib.sha256(data).hexdigest()
    _require(
        digest == EXPECTED_SOURCE_SHA256[label],
        f"{label} source identity mismatch: expected {EXPECTED_SOURCE_SHA256[label]}, got {digest}",
    )
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Wu009ClaimBoundaryError(f"{label} source is not valid UTF-8 JSON") from exc
    _require(isinstance(payload, dict), f"{label} source must be a JSON object")
    return payload, digest


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be an object")
    return value  # type: ignore[return-value]


def _validate_ledger(ledger: Mapping[str, Any]) -> dict[str, object]:
    _require(
        ledger.get("format") == "PLANCK_MES_WU009_THEOREM_ADJUDICATION_V1",
        "unsupported theorem-ledger format",
    )
    _require(ledger.get("authority_source") == "USER_SUPPLIED_SUMMARY", "ledger authority drifted")
    _require(
        ledger.get("claim_tier") == "THEOREM_SUMMARY_AUTHORITY_NO_CLAIM_PROMOTION",
        "ledger claim tier drifted",
    )
    _require(
        ledger.get("forbidden_uses")
        == [
            "Representing this transcription or its bounded checks as replay of P01-P27.",
            "Promoting a Bianchi geometry, family, or physical cause from representation contracts.",
            "Regenerating claim-bearing paper artifacts before successor release gates seal.",
        ],
        "ledger forbidden-use boundary drifted",
    )
    _require(
        ledger.get("formal_proof_provenance") == "FORMAL_DOSSIER_PENDING",
        "formal dossier must remain pending",
    )
    _require(ledger.get("formal_dossier_replayed") is False, "P01-P27 must not be labeled locally replayed")
    _require(ledger.get("row_count") == 78, "ledger row_count must equal 78")
    rows = ledger.get("rows")
    _require(isinstance(rows, list), "ledger rows must be an array")
    _require(all(isinstance(row, Mapping) for row in rows), "every ledger row must be an object")
    typed_rows = [row for row in rows if isinstance(row, Mapping)]
    row_ids = [row.get("id") for row in typed_rows]
    _require(tuple(row_ids) == _expected_row_ids(), "ledger IDs or canonical ordering drifted")
    _require(len(set(row_ids)) == 78, "ledger IDs must be unique")

    verdict_counts = dict(sorted(Counter(row.get("verdict") for row in typed_rows).items()))
    _require(verdict_counts == EXPECTED_VERDICT_COUNTS, "ledger verdict counts drifted")
    for verdict, expected_ids in EXPECTED_SPECIAL_IDS.items():
        actual_ids = tuple(row["id"] for row in typed_rows if row.get("verdict") == verdict)
        _require(actual_ids == expected_ids, f"{verdict} theorem IDs drifted")

    rows_by_id = {str(row["id"]): row for row in typed_rows}
    for row_id, replacement in EXPECTED_REPLACEMENTS.items():
        _require(
            rows_by_id[row_id].get("replacement_statement") == replacement,
            f"corrected replacement statement drifted for {row_id}",
        )
    for row in typed_rows:
        _require(
            row.get("evidence_status") == "SUMMARY_ONLY_FORMAL_DOSSIER_PENDING",
            f"ledger evidence promotion detected for {row.get('id')}",
        )
        _require(
            row.get("release_status") == "NOT_RELEASED_FORMAL_DOSSIER_PENDING",
            f"ledger release promotion detected for {row.get('id')}",
        )
        proof_reference = row.get("summary_proof_reference")
        _require(
            isinstance(proof_reference, str)
            and re.fullmatch(r"USER_SUMMARY:P(?:0[1-9]|1[0-9]|2[0-7])", proof_reference) is not None,
            f"invalid summary-only proof reference for {row.get('id')}",
        )
    return {
        "row_count": 78,
        "verdict_counts": EXPECTED_VERDICT_COUNTS.copy(),
        "corrected_ids": list(EXPECTED_SPECIAL_IDS["CORRECTED"]),
        "refuted_ids": list(EXPECTED_SPECIAL_IDS["REFUTED"]),
        "undefined_ids": list(EXPECTED_SPECIAL_IDS["UNDEFINED"]),
        "authority_source": "USER_SUPPLIED_SUMMARY",
        "formal_proof_provenance": "FORMAL_DOSSIER_PENDING",
        "formal_dossier_replayed": False,
    }


def _validate_reconciliation(reconciliation: Mapping[str, Any]) -> dict[str, object]:
    _require(
        reconciliation.get("format") == "PLANCK_MES_WU009_MAP_FREE_RECONCILIATION_V1",
        "unsupported reconciliation format",
    )
    _require(
        reconciliation.get("overall_state") == "SUCCEEDED_NO_CLAIM_PROMOTION",
        "reconciliation did not preserve the no-promotion terminal",
    )
    _require(
        reconciliation.get("claim_tier") == "MAP_FREE_RECONCILIATION_NO_CLAIM_PROMOTION",
        "reconciliation claim tier drifted",
    )
    _require(
        reconciliation.get("transfer_source") == "COMMITTED_PREDECESSOR_TEXT_ARTIFACTS_ONLY",
        "reconciliation transfer source drifted",
    )
    _require(
        reconciliation.get("forbidden_uses")
        == [
            "new observed rank or detection claim",
            "family or physical-cause identification",
            "same-sky independent replication claim",
            "formal P01-P27 replay claim",
        ],
        "reconciliation forbidden-use boundary drifted",
    )
    observed = _require_mapping(reconciliation.get("observed_result"), "observed_result")
    _require(observed.get("computed") is False, "a new observed result is forbidden in this receipt")
    _require(observed.get("rank") is None, "a new observed rank is forbidden in this receipt")
    _require(observed.get("score") is None and observed.get("statistic") is None, "a new observed statistic is forbidden")
    _require(observed.get("state") == "NO_ADMISSIBLE_NEW_RESULT", "observed-result abstention drifted")

    historical = _require_mapping(reconciliation.get("historical_results"), "historical_results")
    wu006 = _require_mapping(historical.get("WU006"), "historical_results.WU006")
    _require(wu006.get("family_rank") == "27/301", "WU-006 family rank drifted")
    _require(
        wu006.get("local_ranks") == {"R_v0": "4/301", "R_v2": "4/301"},
        "WU-006 local ranks drifted or were conflated with the family rank",
    )
    _require(
        wu006.get("interpretation") == "HISTORICAL_FAMILY_AND_LOCAL_RANKS_DISTINCT",
        "WU-006 family/local interpretation drifted",
    )
    wu007 = _require_mapping(historical.get("WU007"), "historical_results.WU007")
    _require(wu007.get("null_sensitivity_ranks") == ["61/1000", "55/1000"], "WU-007 ranks drifted")
    _require(
        wu007.get("interpretation") == "NULL_POOL_SENSITIVITY_NOT_INDEPENDENT_REPLICATION",
        "WU-007 must remain same-observation null-pool sensitivity",
    )
    wu008 = _require_mapping(historical.get("WU008"), "historical_results.WU008")
    _require(
        wu008.get("scope") == "OBSERVATION_BLIND_REGISTERED_200_REFERENCE_METHOD_POWER",
        "WU-008 must remain observation-blind method power",
    )
    _require(wu008.get("arms_independent") is False, "WU-008 arms must not be labeled independent")
    _require(wu008.get("predecessor_rewritten") is False, "WU-008 predecessor mutation detected")
    return {
        "WU006": {
            "family_rank": "27/301",
            "local_ranks": {"R_v0": "4/301", "R_v2": "4/301"},
            "interpretation": "HISTORICAL_FAMILY_AND_LOCAL_RANKS_DISTINCT",
        },
        "WU007": {
            "null_sensitivity_ranks": ["61/1000", "55/1000"],
            "interpretation": "SAME_OBSERVATION_NULL_POOL_SENSITIVITY",
        },
        "WU008": {
            "scope": "OBSERVATION_BLIND_REGISTERED_200_REFERENCE_METHOD_POWER",
            "interpretation": "METHOD_POWER_ONLY_NO_OBSERVATIONAL_OR_CAUSAL_PROMOTION",
        },
    }


def _validate_terminal(terminal: Mapping[str, Any]) -> None:
    _require(
        terminal.get("format") == "PLANCK_MES_WU009_MAP_FREE_RECONCILIATION_TERMINAL_V1",
        "unsupported reconciliation terminal format",
    )
    _require(terminal.get("state") == "SUCCEEDED_NO_CLAIM_PROMOTION", "terminal state drifted")
    required_false = (
        "claim_promotion",
        "formal_dossier_replayed",
        "new_observed_rank",
        "new_observed_result",
        "predecessors_mutated",
        "raw_data_accessed",
        "raw_data_mutation",
    )
    for field in required_false:
        _require(terminal.get(field) is False, f"terminal promotion or mutation detected: {field}")


def validate_wu009_claim_boundary_payloads(
    ledger: Mapping[str, Any],
    reconciliation: Mapping[str, Any],
    terminal: Mapping[str, Any],
    *,
    source_identities: Mapping[str, Mapping[str, str]] | None = None,
) -> dict[str, object]:
    """Validate decoded WU-009 authority and return a deterministic boundary."""

    _require(isinstance(ledger, Mapping), "ledger payload must be an object")
    _require(isinstance(reconciliation, Mapping), "reconciliation payload must be an object")
    _require(isinstance(terminal, Mapping), "terminal payload must be an object")
    ledger_summary = _validate_ledger(ledger)
    historical = _validate_reconciliation(reconciliation)
    _validate_terminal(terminal)
    identities = {
        label: dict(sorted(identity.items()))
        for label, identity in sorted((source_identities or {}).items())
    }
    verified = bool(identities) and all(
        identities.get(label, {}).get("sha256") == digest
        for label, digest in EXPECTED_SOURCE_SHA256.items()
    )
    return {
        "format": BOUNDARY_FORMAT,
        "source_identities": identities,
        "source_identity_verified": verified,
        "ledger": ledger_summary,
        "reconciliation_state": "SUCCEEDED_NO_CLAIM_PROMOTION",
        "historical_results": historical,
        "corrected_semantics": {
            "finite_rank": "superuniform only under joint exchangeability plus a complete row-equivariant scoring pipeline",
            "decreasing_transformations": "decreasing transformations require an upper/lower tail swap",
            "positive_quadratic_inverse": "representation identification only; empirical Planck use requires absolute positive temperature with verified monopole and dipole",
            "component_products_and_splits": "same-sky robustness, never independent cosmic replication",
            "polarization_rank_prerequisite": "E/B or cross-field rank requires a matched dependence-preserving polarization null and complete row-equivariant pipeline",
            "cross_field_joint_conditional_diagnostics": "EXPLORATORY_ONLY",
            "shared_data_e_values": "shared-data marginal e-values cannot generally be multiplied as if independent",
            "claim_ceiling": "PRE_NATIVE_ATLAS_CONDITIONAL_MORPHOLOGY_ONLY",
        },
        "claim_promotion": False,
        "new_observed_rank": False,
        "raw_data_accessed": False,
        "raw_data_mutation": False,
        "paper_regeneration": {
            "authorized": False,
            "state": "BLOCKED_UNTIL_GATE_E_FROZEN_SUCCESSOR",
            "required_binding": "GATE_E_FROZEN_SUCCESSOR",
            "gate_e_binding": None,
        },
    }


def load_wu009_claim_boundary(
    ledger_path: Path | str,
    reconciliation_path: Path | str,
    terminal_path: Path | str,
) -> dict[str, object]:
    """Load exact sealed sources and return the validated WU-009 boundary."""

    paths = {
        "ledger": Path(ledger_path),
        "reconciliation": Path(reconciliation_path),
        "terminal": Path(terminal_path),
    }
    loaded: dict[str, dict[str, Any]] = {}
    identities: dict[str, dict[str, str]] = {}
    for label, path in paths.items():
        payload, digest = _read_exact_json(path, label=label)
        loaded[label] = payload
        identities[label] = {
            "path": EXPECTED_SOURCE_PATHS[label],
            "sha256": digest,
        }
    return validate_wu009_claim_boundary_payloads(
        loaded["ledger"],
        loaded["reconciliation"],
        loaded["terminal"],
        source_identities=identities,
    )


def require_paper_regeneration_authority(boundary: Mapping[str, Any]) -> None:
    """Fail closed unless a future boundary binds a sealed Gate-E successor."""

    _require(isinstance(boundary, Mapping), "WU-009 boundary must be an object")
    _require(boundary.get("format") == BOUNDARY_FORMAT, "unsupported WU-009 boundary format")
    _require(boundary.get("source_identity_verified") is True, "WU-009 source identities are not verified")
    _require_mapping(boundary.get("paper_regeneration"), "paper_regeneration")
    raise Wu009ClaimBoundaryError(
        "current V1 boundary never authorizes paper regeneration; a future version must "
        "validate an exact GATE_E_FROZEN_SUCCESSOR source before authorization"
    )


__all__ = [
    "BOUNDARY_FORMAT",
    "Wu009ClaimBoundaryError",
    "load_wu009_claim_boundary",
    "require_paper_regeneration_authority",
    "validate_wu009_claim_boundary_payloads",
]
