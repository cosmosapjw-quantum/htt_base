#!/usr/bin/env python3
"""Build or check the source-only PR-123 mutation-laboratory artifacts."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import numpy as np
import yaml

from common.k6_continuum_oracle import (
    K6_ALLOWED_REPOSITORY_CONSUMERS,
    run_k6_continuum_suite,
)
from common.oracle_lab import (
    FROZEN_MUTATION_IDS,
    OracleLabError,
    OracleLineage,
    canonical_json_bytes,
    content_sha256,
    validate_seed_ledger,
    validate_lineage_rows,
    validate_outcomes,
)
from common.oracle_references import run_non_k6_reference_cases


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "docs/research_program/long_horizon_rescue/pr123_spec.yaml"
REFERENCE_PATH = REPO_ROOT / "htt/src/common/oracle_references.py"
K6_PATH = REPO_ROOT / "htt/src/common/k6_continuum_oracle.py"
LAB_PATH = REPO_ROOT / "htt/src/common/oracle_lab.py"
SCRIPT_PATH = Path(__file__).resolve()
REMEDIATION_STATE_PATH = REPO_ROOT / "docs/codex_handoff/research_remediation_state.yaml"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs/generated"
OUTPUT_NAMES = (
    "pr123_oracle_lineage_manifest.json",
    "pr123_mutation_lab_report.json",
    "pr123_k6_continuum_card.json",
    "pr123_surviving_mutations.json",
    "pr123_attempt_history.json",
    "pr123_artifact_manifest.json",
)
FORBIDDEN_REFERENCE_IMPORT_PREFIXES = (
    "obsstat",
    "htt.infer",
    "htt.obsstat",
    "scripts",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _normalize_historical_hash(
    mapping: dict[str, Any], key: str, replacement: str
) -> None:
    if _is_sha256(mapping.get(key)):
        mapping[key] = replacement


def _render(value: Any) -> bytes:
    normalized = json.loads(canonical_json_bytes(value))
    return (json.dumps(normalized, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _semantic_payload(name: str, payload: bytes) -> Any:
    """Remove only generation-time self-references from a check comparison."""

    value = json.loads(payload)
    metadata = value.get("metadata")
    if isinstance(metadata, dict):
        for row in metadata.get("input_hashes", []):
            if (
                isinstance(row, dict)
                and row.get("path") in {
                    SCRIPT_PATH.relative_to(REPO_ROOT).as_posix(),
                    K6_PATH.relative_to(REPO_ROOT).as_posix(),
                }
            ):
                _normalize_historical_hash(
                    row, "sha256", "<historical-maintained-source>"
                )
        state = metadata.get("git_commit_or_worktree_state")
        if isinstance(state, dict):
            _normalize_historical_hash(
                state,
                "source_snapshot_sha256",
                "<historical-source-snapshot>",
            )
    if name == "pr123_k6_continuum_card.json":
        _normalize_historical_hash(
            value,
            "oracle_lineage_manifest_hash",
            "<historical-lineage-artifact>",
        )
    if name == "pr123_oracle_lineage_manifest.json":
        for row in value.get("lineage_rows", []):
            reference = (
                row.get("reference_path_and_sha256")
                if isinstance(row, dict)
                else None
            )
            if (
                isinstance(reference, dict)
                and reference.get("path")
                == K6_PATH.relative_to(REPO_ROOT).as_posix()
            ):
                _normalize_historical_hash(
                    reference,
                    "sha256",
                    "<historical-maintained-source>",
                )
    if name == "pr123_artifact_manifest.json":
        for row in value.get("artifacts", []):
            if isinstance(row, dict):
                _normalize_historical_hash(
                    row, "sha256", "<historical-artifact>"
                )
    return value


def _stored_artifacts_are_bound(output_dir: Path) -> bool:
    try:
        manifest = json.loads(
            (output_dir / "pr123_artifact_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        lineage = json.loads(
            (output_dir / "pr123_oracle_lineage_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        k6_card = json.loads(
            (output_dir / "pr123_k6_continuum_card.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if k6_card.get("oracle_lineage_manifest_hash") != content_sha256(lineage):
        return False
    rows = manifest.get("artifacts")
    if not isinstance(rows, list) or len(rows) != len(OUTPUT_NAMES) - 1:
        return False
    expected = set(OUTPUT_NAMES[:-1])
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            return False
        relative = row.get("path")
        if not isinstance(relative, str):
            return False
        name = Path(relative).name
        if relative != f"docs/generated/{name}" or name not in expected:
            return False
        path = output_dir / name
        if (
            name in seen
            or not path.is_file()
            or _sha256(path) != row.get("sha256")
            or path.stat().st_size != row.get("size_bytes")
        ):
            return False
        seen.add(name)
    return seen == expected


def _stored_payload_is_current(path: Path, name: str, current: bytes) -> bool:
    if not path.is_file():
        return False
    try:
        return _semantic_payload(name, path.read_bytes()) == _semantic_payload(
            name, current
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False


def _function_metrics(path: Path, symbol: str) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    node = next(
        (
            item
            for item in tree.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            and item.name == symbol
        ),
        None,
    )
    if node is None or node.end_lineno is None:
        raise OracleLabError(f"missing source symbol {symbol} in {path}")
    branch_types = (ast.If, ast.For, ast.While, ast.Try, ast.Match)
    return {
        "sloc": int(node.end_lineno - node.lineno + 1),
        "branches": int(sum(isinstance(item, branch_types) for item in ast.walk(node))),
    }


def _imports(path: Path) -> set[str]:
    result: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
            result.update(f"{node.module}.{alias.name}" for alias in node.names)
    return result


def _local_call_closure_metrics(path: Path, roots: list[str]) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    pending = list(roots)
    seen: set[str] = set()
    while pending:
        symbol = pending.pop()
        if symbol in seen or symbol not in functions:
            continue
        seen.add(symbol)
        for node in ast.walk(functions[symbol]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in functions and node.func.id not in seen:
                    pending.append(node.func.id)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                for loaded in ast.walk(value):
                    if isinstance(loaded, ast.Name) and loaded.id in functions and loaded.id not in seen:
                        pending.append(loaded.id)
    if set(roots) - set(functions):
        raise OracleLabError(f"missing closure roots in {path}: {set(roots) - set(functions)}")
    branch_types = (ast.If, ast.For, ast.While, ast.Try, ast.Match)
    return {
        "sloc": sum(functions[name].end_lineno - functions[name].lineno + 1 for name in seen),
        "branches": sum(
            isinstance(item, branch_types)
            for name in seen
            for item in ast.walk(functions[name])
        ),
        "function_count": len(seen),
    }


def _automated_scan_checks(
    path: Path,
    forbidden_symbols: set[str],
    *,
    allowed_local_shadows: frozenset[str] = frozenset(),
) -> dict[str, bool]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports_clean = not any(
        imported == prefix or imported.startswith(prefix + ".")
        for imported in _imports(path)
        for prefix in FORBIDDEN_REFERENCE_IMPORT_PREFIXES
    )
    dynamic_primitives = {
        "eval", "exec", "compile", "__import__", "getattr", "globals",
        "locals", "vars", "setattr", "delattr", "__builtins__", "__dict__",
        "__getattr__", "__getattribute__", "attrgetter", "methodcaller",
        "import_module", "exec_module", "parse",
    }
    mapped_callable_aliases = set(forbidden_symbols)
    mapped_name_aliases: set[str] = set()
    dynamic_aliases = set(dynamic_primitives)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound = alias.asname or alias.name
                if alias.name in forbidden_symbols:
                    mapped_callable_aliases.add(bound)
                if alias.name in dynamic_primitives:
                    dynamic_aliases.add(bound)

    def _literal_string(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = _literal_string(node.left)
            right = _literal_string(node.right)
            if left is not None and right is not None:
                return left + right
        if isinstance(node, ast.JoinedStr):
            pieces = [
                item.value
                for item in node.values
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
            if len(pieces) == len(node.values):
                return "".join(pieces)
        return None

    def _subscript_key(node: ast.Subscript) -> str | None:
        return _literal_string(node.slice)

    def _assignment_targets(node: ast.Assign | ast.AnnAssign) -> list[str]:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return [
            child.id
            for target in targets
            for child in ast.walk(target)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
        ]

    def _rhs_kinds(value: ast.AST) -> tuple[bool, bool, bool]:
        mapped_callable = False
        mapped_name = False
        dynamic_callable = False
        if isinstance(value, ast.Name):
            mapped_callable = value.id in mapped_callable_aliases
            mapped_name = value.id in mapped_name_aliases
            dynamic_callable = value.id in dynamic_aliases
        elif isinstance(value, ast.Attribute):
            mapped_callable = value.attr in forbidden_symbols
            dynamic_callable = value.attr in dynamic_primitives
        elif isinstance(value, ast.Subscript):
            key = _subscript_key(value)
            mapped_callable = key in forbidden_symbols
            dynamic_callable = key in dynamic_primitives
        elif isinstance(value, ast.Constant) and isinstance(value.value, str):
            mapped_name = value.value in forbidden_symbols
        elif isinstance(value, ast.Call):
            func = value.func
            dynamic_factory = (
                isinstance(func, ast.Name) and func.id in dynamic_aliases
            ) or (
                isinstance(func, ast.Attribute) and func.attr in dynamic_primitives
            ) or (
                isinstance(func, ast.Subscript)
                and _subscript_key(func) in dynamic_primitives
            )
            has_mapped_name = any(
                (isinstance(child, ast.Constant) and child.value in forbidden_symbols)
                or (isinstance(child, ast.Name) and child.id in mapped_name_aliases)
                for child in ast.walk(value)
            )
            mapped_callable = dynamic_factory and has_mapped_name
        return mapped_callable, mapped_name, dynamic_callable

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            mapped_callable, mapped_name, dynamic_callable = _rhs_kinds(node.value)
            for target in _assignment_targets(node):
                if mapped_callable and target not in mapped_callable_aliases:
                    mapped_callable_aliases.add(target)
                    changed = True
                if mapped_name and target not in mapped_name_aliases:
                    mapped_name_aliases.add(target)
                    changed = True
                if dynamic_callable and target not in dynamic_aliases:
                    dynamic_aliases.add(target)
                    changed = True

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    scope_types = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)

    def _lexical_scope(node: ast.AST) -> ast.AST:
        current = node
        while current not in (tree,):
            current = parents[current]
            if isinstance(current, scope_types):
                return current
        return tree

    scope_bindings: dict[ast.AST, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            scope_bindings.setdefault(_lexical_scope(node), set()).add(node.id)

    def _is_allowed_local_shadow(node: ast.Name) -> bool:
        return (
            node.id in allowed_local_shadows
            and node.id in scope_bindings.get(_lexical_scope(node), set())
        )

    mapped_symbol_reference = any(
        (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in forbidden_symbols
            and not _is_allowed_local_shadow(node)
        )
        or (isinstance(node, ast.Attribute) and node.attr in forbidden_symbols)
        or (isinstance(node, ast.alias) and node.name in forbidden_symbols)
        or (_literal_string(node) in forbidden_symbols)
        for node in ast.walk(tree)
    )
    dynamic_reference = any(
        (isinstance(node, ast.Name) and node.id in dynamic_primitives)
        or (isinstance(node, ast.Attribute) and node.attr in dynamic_primitives)
        or (isinstance(node, ast.alias) and node.name in dynamic_primitives)
        or (_literal_string(node) in dynamic_primitives)
        for node in ast.walk(tree)
    )
    mapped_call_or_indirection = mapped_symbol_reference
    dynamic_call_or_codegen = dynamic_reference
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            mapped_call_or_indirection |= node.func.id in mapped_callable_aliases
            dynamic_call_or_codegen |= node.func.id in dynamic_aliases
        elif isinstance(node.func, ast.Attribute):
            mapped_call_or_indirection |= node.func.attr in forbidden_symbols
            dynamic_call_or_codegen |= node.func.attr in dynamic_primitives
        elif isinstance(node.func, ast.Subscript):
            key = _subscript_key(node.func)
            mapped_call_or_indirection |= key in forbidden_symbols
            dynamic_call_or_codegen |= key in dynamic_primitives
        mapped_call_or_indirection |= any(
            (_literal_string(child) in forbidden_symbols)
            or (isinstance(child, ast.Name) and child.id in mapped_name_aliases)
            for child in ast.walk(node)
        )
    return {
        "forbidden_import_prefixes_clean": imports_clean,
        "mapped_production_symbol_calls_clean": not mapped_call_or_indirection,
        "dynamic_import_and_codegen_clean": not dynamic_call_or_codegen,
    }


def _review_input_paths(spec: dict[str, Any]) -> list[tuple[Path, str]]:
    records: list[tuple[Path, str]] = []
    provenance = spec["review_provenance"]
    records.append((REPO_ROOT / provenance["merged_result"]["path"], provenance["merged_result"]["sha256"]))
    records.extend(
        (REPO_ROOT / row["path"], row["sha256"])
        for row in provenance["role_results"]
    )
    for attempt in spec["spec_amendment"]["invalidated_attempts"]:
        hostile = attempt["invalidating_review"]
        records.append((REPO_ROOT / hostile["merged_result_path"], hostile["merged_result_sha256"]))
        run_dir = REPO_ROOT / ".agent-harness/runs" / hostile["run_id"] / "results"
        records.extend(
            (run_dir / f"{assignment_id}.json", expected_hash)
            for assignment_id, expected_hash in hostile["result_hashes"].items()
        )
    return records


def _input_hashes(spec: dict[str, Any]) -> list[dict[str, str]]:
    source_records = {
        record["repository_path"]: record["repository_sha256"]
        for record in spec["equation_source_definitions"].values()
        if "repository_path" in record
    }
    base_paths = (
        SPEC_PATH, LAB_PATH, REFERENCE_PATH, K6_PATH, SCRIPT_PATH,
        REMEDIATION_STATE_PATH,
    )
    rows = [
        {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha256(path)}
        for path in base_paths
    ]
    for relative, generation_hash in sorted(source_records.items()):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise OracleLabError(f"repository source missing: {relative}")
        rows.append({"path": relative, "sha256": generation_hash})
    for path, expected_hash in _review_input_paths(spec):
        if not path.is_file() or _sha256(path) != expected_hash:
            raise OracleLabError(f"review provenance hash mismatch: {path}")
        rows.append({"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": expected_hash})
    return rows


def _validate_equation_sources(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    definitions = spec["equation_source_definitions"]
    referenced = {
        source_id
        for source_ids in spec["equation_source_registry"].values()
        for source_id in source_ids
    }
    if set(definitions) != referenced:
        raise OracleLabError("equation/source registry is not exactly resolved")
    for source_id, record in definitions.items():
        if not record.get("kind") or not record.get("statement"):
            raise OracleLabError(f"incomplete equation/source definition: {source_id}")
        if record["kind"] in {"repository_audit_source", "external_api_source"}:
            if not record.get("repository_path") and not str(record.get("url", "")).startswith("https://"):
                raise OracleLabError(f"unresolvable source definition: {source_id}")
        if record.get("repository_path"):
            path = REPO_ROOT / record["repository_path"]
            if not _is_sha256(record.get("repository_sha256")):
                raise OracleLabError(
                    f"invalid historical repository source hash: {source_id}"
                )
            if not path.is_file():
                raise OracleLabError(f"repository source missing: {source_id}")
    return definitions


def _validate_remediation_state(spec: dict[str, Any]) -> dict[str, Any]:
    contract = spec["remediation_state_contract"]
    path = REPO_ROOT / contract["path"]
    if path != REMEDIATION_STATE_PATH or _sha256(path) != contract["sha256"]:
        raise OracleLabError("remediation-state root hash mismatch")
    state = yaml.safe_load(path.read_text(encoding="utf-8"))
    findings = state.get("findings", [])
    statuses = [row.get("scientific_status") for row in findings]
    census = state.get("census", {})
    if (
        len(findings) != contract["finding_count"]
        or statuses.count("OPEN") != contract["finding_count"]
        or any(status != "OPEN" for status in statuses)
        or census.get("finding_count") != contract["finding_count"]
        or census.get("scientific_status_counts") != contract["required_scientific_status_counts"]
        or census.get("rescued_count") != contract["rescued_count"]
    ):
        raise OracleLabError("remediation-state OPEN/RESCUED census drift")
    return {
        "path": contract["path"],
        "sha256": contract["sha256"],
        "finding_count": len(findings),
        "scientific_status_counts": {"OPEN": statuses.count("OPEN")},
        "rescued_count": 0,
        "disposition_changes": [],
    }


def _resolve_fixture_template(value: Any, *, replicates: int, ppc_draws: int) -> Any:
    if value == "$runtime_replicates":
        return replicates
    if value == "$ppc_draws":
        return ppc_draws
    if isinstance(value, dict):
        return {
            key: _resolve_fixture_template(item, replicates=replicates, ppc_draws=ppc_draws)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _resolve_fixture_template(item, replicates=replicates, ppc_draws=ppc_draws)
            for item in value
        ]
    return value


def _expected_fixture_hashes(
    spec: dict[str, Any],
    *,
    replicates: int,
    ppc_draws: int,
    consumer_inventory: list[str],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for mutation_id, record in spec["fixture_registry"].items():
        if record.get("payload_kind") == "k6_contract_and_runtime_consumer_inventory":
            payload = {
                "contract": spec["k6_continuum_contract"],
                "consumer_inventory": consumer_inventory,
            }
        else:
            payload = _resolve_fixture_template(
                record["payload_template"],
                replicates=replicates,
                ppc_draws=ppc_draws,
            )
        result[mutation_id] = content_sha256(payload)
    if set(result) != set(FROZEN_MUTATION_IDS):
        raise OracleLabError("fixture registry does not cover frozen mutations")
    return result


def _expected_seed_slots(replicates: int) -> list[dict[str, Any]]:
    paired_groups = (
        ("cf4_constrained_linear_estimator", "paired_clean_and_mutant"),
        ("grf_hermitian_generation", "paired_clean_and_mutant"),
        ("desi_per_realization_normalization", "paired_clean_and_mutant"),
        ("jwst_synthetic_weighting_reference", "clean_coverage"),
    )
    slots = [
        {
            "lane_id": lane_id,
            "role": role,
            "replicate": replicate,
            "spawn_key": [group_index * replicates + replicate],
        }
        for group_index, (lane_id, role) in enumerate(paired_groups)
        for replicate in range(replicates)
    ]
    for replicate in range(replicates):
        slots.extend((
            {
                "lane_id": "posterior_predictive_mechanics_reference",
                "role": "clean_posterior_predictive",
                "replicate": replicate,
                "spawn_key": [4 * replicates + replicate],
            },
            {
                "lane_id": "posterior_predictive_mechanics_reference",
                "role": "mutant_plugin_predictive",
                "replicate": replicate,
                "spawn_key": [5 * replicates + replicate],
            },
        ))
    return slots


def _expected_execution_count(contract: dict[str, int], replicates: int) -> int:
    return int(contract["per_replicate"]) * replicates + int(contract["fixed"])


def _metadata(
    spec: dict[str, Any],
    config_hash: str,
    artifact_id: str,
    input_hashes: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "owner": spec["owner"],
        "contributors": list(spec["contributors"]),
        "implementation_scope": list(spec["implementation_scope"]),
        "claim_tier": spec["claim_tier"],
        "claim_level": dict(spec["claim_level"]),
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": list(spec["allowed_use"]),
        "forbidden_use": [
            "observed estimates, p-values, significance, posterior odds, or adequacy",
            "matched-null or covariance validation",
            "native-transfer, geometry, morphology-family, or remediation promotion",
        ],
        "transfer_source": spec["transfer_source"],
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "sky_support_status": spec["sky_support_status"],
        "null_mock_status": spec["null_mock_status"],
        "caveats": [
            "Synthetic and analytic mechanics only; all scientific findings remain OPEN.",
            "Internal role separation is correlated process evidence, not external replication.",
            "The PR4/NPIPE zero-command field is an in-process scope declaration, not authenticated shell history.",
        ],
        "generating_command": "venv/bin/python -B scripts/codex_harness/run_pr123_oracle_lab.py --write --tier contract",
        "git_commit_or_worktree_state": {
            "baseline_commit": spec["baseline_commit"],
            "state_kind": "commit_independent_exact_source_snapshot",
            "source_snapshot_sha256": content_sha256(input_hashes),
        },
        "consumer_list": ["PR-123 tests", "PR-123 artifact manifest", "later registered PR regression gates"],
        "generated_on": "2026-07-16",
    }


def _k6_consumer_inventory() -> tuple[list[str], list[str]]:
    needles = ("common.k6_continuum_oracle", "run_k6_continuum_suite")
    roots = (
        REPO_ROOT / "htt",
        REPO_ROOT / "scripts",
        REPO_ROOT / "tests",
    )
    inventory = []
    for root in roots:
        for path in root.rglob("*.py"):
            if path == K6_PATH:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(needle in text for needle in needles):
                inventory.append(path.relative_to(REPO_ROOT).as_posix())
    inventory = sorted(set(inventory))
    unexpected = sorted(set(inventory) - K6_ALLOWED_REPOSITORY_CONSUMERS)
    return inventory, unexpected


def _lineage_rows(
    spec: dict[str, Any],
    expected_fixture_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[OracleLineage] = []
    for mutation in spec["mutation_registry"]:
        mutation_id = mutation["mutation_id"]
        reference_path = K6_PATH if mutation_id == "low_order_curl_stencil" else REFERENCE_PATH
        production_records = []
        production_symbols: list[str] = []
        production_metrics = {"sloc": 0, "branches": 0, "function_count": 0}
        for record in mutation["production_paths"]:
            path = REPO_ROOT / record["path"]
            if not _is_sha256(record.get("sha256")):
                raise OracleLabError(
                    f"invalid mapped production source hash: {record['path']}"
                )
            if not path.is_file():
                raise OracleLabError(f"mapped production source missing: {record['path']}")
            for symbol in record["symbols"]:
                _function_metrics(path, symbol)
                production_symbols.append(symbol)
            closure = _local_call_closure_metrics(path, list(record["symbols"]))
            for key in production_metrics:
                production_metrics[key] += closure[key]
            production_records.append(
                {
                    "path": record["path"],
                    "sha256": record["sha256"],
                    "symbols": list(record["symbols"]),
                }
            )
        reference_metrics = _local_call_closure_metrics(
            reference_path, list(mutation["reference_kernel_symbols"])
        )
        mutant_metrics = _local_call_closure_metrics(
            reference_path, [mutation["mutant_symbol"]]
        )
        evaluator_key = "k6" if mutation_id == "low_order_curl_stencil" else "non_k6"
        evaluator_contract = spec["evaluator_contract"][evaluator_key]
        evaluator_metrics = _function_metrics(reference_path, evaluator_contract["symbol"])
        design_authors = (
            "codex:/root/pr123_physstat_v2",
            "codex:/root/pr123_code_map_v2",
        )
        row = OracleLineage(
            mutation_id=mutation_id,
            lane_id=mutation["lane_id"],
            production_paths_and_sha256=tuple(production_records),
            production_symbols=tuple(production_symbols),
            reference_path_and_sha256={
                "path": reference_path.relative_to(REPO_ROOT).as_posix(),
                "sha256": _sha256(reference_path),
            },
            reference_symbol=mutation["reference_symbol"],
            reference_kernel_symbols=tuple(mutation["reference_kernel_symbols"]),
            mutant_symbol=mutation["mutant_symbol"],
            evaluator_symbol=evaluator_contract["symbol"],
            algorithm_id=mutation["algorithm_id"],
            equation_or_source_ids=tuple(spec["equation_source_registry"][mutation_id]),
            fixture_ids_and_hashes=(
                {
                    "fixture_id": f"PR123-FIXTURE-{mutation_id}",
                    "sha256": expected_fixture_hashes[mutation_id],
                },
            ),
            design_author_ids=design_authors,
            transcriber_id="codex:/root",
            reviewer_id="codex:/root/pr123_claim_v2",
            random_stream_namespace=f"PR123/{mutation['lane_id']}",
            shared_lineage_disclosures=(
                "roadmap_card_and_audit_equations_shared_by_design",
                "main_writer_transcribed_blind_role_designs",
                "all_internal_codex_roles_are_process_correlated",
                "random_stream_coupling_is_lane_specific_and_recorded_in_seed_ledger",
            ),
            later_production_owner=mutation["later_production_owner"],
            later_adjudication_owner=spec["evaluator_contract"]["later_adjudication_owner"],
            reference_metrics=reference_metrics,
            mutant_metrics=mutant_metrics,
            evaluator_metrics=evaluator_metrics,
            complexity_budget={
                "max_sloc": int(mutation["max_reference_sloc"]),
                "max_branches": int(mutation["max_reference_branches"]),
                "max_mutant_sloc": int(mutation["max_mutant_sloc"]),
                "max_mutant_branches": int(mutation["max_mutant_branches"]),
                "max_evaluator_sloc": int(evaluator_contract["max_sloc"]),
                "max_evaluator_branches": int(evaluator_contract["max_branches"]),
                "mapped_production_call_closure_sloc": production_metrics["sloc"],
                "mapped_production_call_closure_branches": production_metrics["branches"],
            },
            automated_scan_checks=_automated_scan_checks(
                reference_path,
                set(production_symbols),
                allowed_local_shadows=(
                    frozenset({"curl", "divergence"})
                    if mutation_id == "low_order_curl_stencil"
                    else frozenset()
                ),
            ),
            manual_algorithm_adjudication=dict(
                spec["evaluator_contract"]["manual_algorithm_adjudication"]
            ),
            independence_class="distinct_internal_algorithm_with_disclosed_process_correlation_C2",
        )
        rows.append(row)
    return validate_lineage_rows(rows)


def build_payloads(tier: str) -> dict[str, bytes]:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr123_oracle_lab.v6":
        raise OracleLabError("unsupported PR-123 spec schema")
    mutation_ids = tuple(row["mutation_id"] for row in spec["mutation_registry"])
    if mutation_ids != FROZEN_MUTATION_IDS:
        raise OracleLabError("spec mutation order or identity drift")
    equation_source_definitions = _validate_equation_sources(spec)
    remediation_state_receipt = _validate_remediation_state(spec)
    config_hash = _sha256(SPEC_PATH)
    input_hashes = _input_hashes(spec)
    replicates = int(spec["seed_contract"]["contract_replicates"])
    if tier == "extended":
        replicates = min(64, replicates * 4)
    non_k6, seed_ledger = run_non_k6_reference_cases(
        root_seed=int(spec["seed_contract"]["root_seed"]),
        replicates=replicates,
        ppc_draws=int(spec["seed_contract"]["ppc_draws_per_replicate"]),
    )
    seed_ledger = validate_seed_ledger(
        seed_ledger,
        root_seed=int(spec["seed_contract"]["root_seed"]),
        bit_generator=spec["seed_contract"]["bit_generator"],
        expected_slots=_expected_seed_slots(replicates),
    )
    consumer_inventory, unexpected_consumers = _k6_consumer_inventory()
    k6_card, k6_outcome = run_k6_continuum_suite(
        spec["k6_continuum_contract"],
        consumer_inventory=consumer_inventory,
        unexpected_consumers=unexpected_consumers,
    )
    fixture_hashes = _expected_fixture_hashes(
        spec,
        replicates=replicates,
        ppc_draws=int(spec["seed_contract"]["ppc_draws_per_replicate"]),
        consumer_inventory=consumer_inventory,
    )
    expected_registry = {
        row["mutation_id"]: {
            "lane_id": row["lane_id"],
            "property_ids": tuple(row["property_ids"]),
            "reference_symbol": row["reference_symbol"],
            "mutant_symbol": row["mutant_symbol"],
            "fixture_hash": fixture_hashes[row["mutation_id"]],
            "reference_execution_count": _expected_execution_count(
                row["execution_count_contract"]["reference"], replicates
            ),
            "mutant_execution_count": _expected_execution_count(
                row["execution_count_contract"]["mutant"], replicates
            ),
            "metric_keys": tuple(row["metric_keys"]),
        }
        for row in spec["mutation_registry"]
    }
    summary = validate_outcomes((*non_k6, k6_outcome), expected_registry)
    lineage = _lineage_rows(spec, fixture_hashes)
    seed_hash = content_sha256(seed_ledger)
    lineage_scan_failures = [
        row["mutation_id"]
        for row in lineage
        if not all(row["automated_scan_checks"].values())
    ]
    lineage_core = {
        "schema": "htt.pr123.oracle_lineage_manifest.v6",
        "metadata": _metadata(spec, config_hash, "PR123-ORACLE-LINEAGE", input_hashes),
        "independence_scope": "internal_C2_mechanics_not_external_replication",
        "lineage_rows": lineage,
        "equation_source_definitions": equation_source_definitions,
        "automated_scan_failures": lineage_scan_failures,
        "manual_adjudication_scope": "correlated_internal_hostile_review",
        "all_rows_valid": not lineage_scan_failures and len(lineage) == 9,
    }
    mutation_core = {
        "schema": "htt.pr123.mutation_lab_report.v6",
        "metadata": _metadata(spec, config_hash, "PR123-MUTATION-LAB", input_hashes),
        "tier": tier,
        "mutation_registry_hash": content_sha256(spec["mutation_registry"]),
        "property_registry_hash": content_sha256(spec["property_registry"]),
        "seed_ledger_hash": seed_hash,
        "seed_ledger": seed_ledger,
        "summary": summary,
        "pr4_scope_receipt": {
            "declared_in_process_commands_run": 0,
            "inputs": [],
            "authentication_scope": "current_generator_process_and_registered_patch_only",
            "historical_shell_audit_claimed": False,
        },
        "scientific_status": "OPEN",
        "remediation_disposition_changes": [],
        "remediation_state_receipt": remediation_state_receipt,
    }
    k6_core = {
        **k6_card,
        "metadata": _metadata(spec, config_hash, "PR123-K6-CONTINUUM", input_hashes),
        "oracle_lineage_manifest_hash": content_sha256(lineage_core),
        "mutation_status": k6_outcome.status,
        "mutation_killed": k6_outcome.mutant_killed,
        "allowed_statement": "catalog-independent numerical upper-bound mechanics under roadmap_rescue_v1:C2",
        "forbidden_statement": "observed vorticity or empirical CF4 field content",
    }
    survivors_core = {
        "schema": "htt.pr123.surviving_mutations.v6",
        "metadata": _metadata(spec, config_hash, "PR123-SURVIVORS", input_hashes),
        "registered_count": summary["registered_count"],
        "survivor_count": summary["survivor_count"],
        "survivors": summary["survivors"],
        "lane_blocking_rule": "every survivor remains recorded and blocks its own lane",
        "aggregate_status": summary["aggregate_status"],
        "scientific_status": "OPEN",
    }
    attempt_history_core = {
        "schema": "htt.pr123.attempt_history.v6",
        "metadata": _metadata(spec, config_hash, "PR123-ATTEMPT-HISTORY", input_hashes),
        "attempts": [
            *[
                {
                    "attempt_id": attempt["attempt_id"],
                    "config_hash": attempt["config_hash"],
                    "status": "INVALIDATED_FALSE_GREEN",
                    "counts_must_not_be_consumed": True,
                    "artifact_hashes": dict(attempt["artifact_hashes"]),
                    "invalidating_review": dict(attempt["invalidating_review"]),
                }
                for attempt in spec["spec_amendment"]["invalidated_attempts"]
            ],
            {
                "attempt_id": spec["spec_amendment"]["current_attempt_id"],
                "config_hash": config_hash,
                "status": summary["aggregate_status"],
                "prospective_preregistration_claimed": False,
                "scientific_status": "OPEN",
            },
        ],
    }
    first = {
        OUTPUT_NAMES[0]: _render(lineage_core),
        OUTPUT_NAMES[1]: _render(mutation_core),
        OUTPUT_NAMES[2]: _render(k6_core),
        OUTPUT_NAMES[3]: _render(survivors_core),
        OUTPUT_NAMES[4]: _render(attempt_history_core),
    }
    manifest_core = {
        "schema": "htt.pr123.artifact_manifest.v6",
        "metadata": _metadata(spec, config_hash, "PR123-ARTIFACT-MANIFEST", input_hashes),
        "artifacts": [
            {
                "path": f"docs/generated/{name}",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            }
            for name, payload in first.items()
        ],
        "all_required_artifacts_present": True,
        "aggregate_status": summary["aggregate_status"],
        "claim_release_allowed": False,
        "scientific_status": "OPEN",
        "pr4_scope_receipt": mutation_core["pr4_scope_receipt"],
    }
    return {**first, OUTPUT_NAMES[5]: _render(manifest_core)}


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--tier", choices=("contract", "extended"), default="contract")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    payloads = build_payloads(args.tier)
    output_dir = args.output_dir.resolve()
    if args.check:
        stale = [
            name
            for name, payload in payloads.items()
            if not _stored_payload_is_current(
                output_dir / name, name, payload
            )
        ]
        if not stale and not _stored_artifacts_are_bound(output_dir):
            stale.append("pr123_artifact_manifest.json")
        if stale:
            print(json.dumps({"status": "stale", "artifacts": stale}, sort_keys=True))
            return 1
        print(json.dumps({"status": "current", "artifacts": list(payloads)}, sort_keys=True))
        return 0
    for name in OUTPUT_NAMES:
        _atomic_write(output_dir / name, payloads[name])
    print(json.dumps({"status": "written", "artifacts": list(payloads)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
