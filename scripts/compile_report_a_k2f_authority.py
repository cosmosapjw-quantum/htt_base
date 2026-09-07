#!/usr/bin/env python3
"""Compile the K2 candidate overlays into one deterministic authority bundle.

The compiler is intentionally narrow.  It binds the exact K2C input blobs,
applies the four registered statement revisions, appends the ten independently
reviewed claims, and materialises self-contained claim, citation, section,
integration and bibliography candidates.  It performs no observational
analysis and grants no publication or merge authority.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import yaml


class CompilationError(ValueError):
    """Raised when a K2F input or cross-authority invariant fails."""


BASE_DIR = Path("docs/codex_handoff/htt_tensorized_report_first_20260903")
REPORT_DIR = Path("docs/research_reports")
REPORT_A_DIR = REPORT_DIR / "report_a"

INPUT_PATHS: dict[str, Path] = {
    "base_claim_ledger": BASE_DIR / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml",
    "claim_overlay": BASE_DIR / "K2_40_CLAIM_CANDIDATE_OVERLAY.yaml",
    "base_citation_matrix": BASE_DIR / "REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml",
    "citation_overlay": BASE_DIR / "K2_CITATION_PROVENANCE_CANDIDATE_OVERLAY.yaml",
    "section_map": BASE_DIR / "REPORT_SECTION_CLAIM_MAP_V2_CANDIDATE.csv",
    "integration_matrix": REPORT_A_DIR / "REPORT_A_ORGANIC_INTEGRATION_MATRIX_V2_CANDIDATE.yaml",
    "base_bibliography": REPORT_DIR / "HTT_REPORT_A_REFERENCES.bib",
    "bibliography_supplement": REPORT_A_DIR / "K2_BIBLIOGRAPHY_SUPPLEMENT_CANDIDATE.bib",
}

EXPECTED_INPUT_GIT_BLOBS: dict[str, str] = {
    "base_claim_ledger": "58291e9cfac6ff85ceffbdb6bdefd50315240831",
    "claim_overlay": "394378a796a24410a4174a8222e40c5c59e9700a",
    "base_citation_matrix": "5087d39edf094f3adf7d72eed3061521ecf0b78d",
    "citation_overlay": "902b698ef81506179cb0f6e3c5d6616a3f445c55",
    "section_map": "d42a666ff0eba8fdca8afc9b4e719de6e5e12a8d",
    "integration_matrix": "28e823ce7705f0c14a4cae5edf39dc32b69d2617",
    "base_bibliography": "ba37321119725e52f1a2b0ac827050ee895e5466",
    "bibliography_supplement": "930457120f5def21321008f4f77cc2b9c0f5694a",
}

OUTPUT_NAMES: dict[str, str] = {
    "claim_ledger": "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V5.yaml",
    "citation_matrix": "REPORT_A_CITATION_PROVENANCE_MATRIX_V3.yaml",
    "section_map": "REPORT_SECTION_CLAIM_MAP_V3.csv",
    "integration_matrix": "REPORT_A_ORGANIC_INTEGRATION_MATRIX_V3.yaml",
    "bibliography": "HTT_REPORT_A_REFERENCES_V2.bib",
    "receipt": "K2F_COMPILATION_RECEIPT.json",
}

_BIB_KEY_RE = re.compile(r"^@[A-Za-z]+\{([^,]+),", flags=re.MULTILINE)


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CompilationError(f"{path} must contain a YAML mapping")
    return payload


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _merge_unique(existing: Sequence[Any], additions: Sequence[Any]) -> list[Any]:
    out: list[Any] = []
    for value in [*existing, *additions]:
        if value not in out:
            out.append(copy.deepcopy(value))
    return out


def _require_unique_ids(rows: Sequence[Mapping[str, Any]], label: str) -> list[str]:
    ids: list[str] = []
    for row in rows:
        claim_id = row.get("id")
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise CompilationError(f"{label} contains a row without a non-empty id")
        ids.append(claim_id)
    if len(ids) != len(set(ids)):
        raise CompilationError(f"{label} contains duplicate ids")
    return ids


def _claim_hash(claim_ids: Sequence[str]) -> str:
    payload = ("\n".join(sorted(claim_ids)) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compile_claim_ledger(
    base: Mapping[str, Any], overlay: Mapping[str, Any]
) -> dict[str, Any]:
    """Apply the registered K2 revisions and additions to a claim ledger."""

    base_rows = copy.deepcopy(base.get("claims"))
    additions = copy.deepcopy(overlay.get("additions"))
    revisions = copy.deepcopy(overlay.get("revisions"))
    candidate_ids = copy.deepcopy(overlay.get("candidate_claim_ids"))
    if not isinstance(base_rows, list) or not isinstance(additions, list):
        raise CompilationError("claim inputs must provide list-valued claims/additions")
    if not isinstance(revisions, list) or not isinstance(candidate_ids, list):
        raise CompilationError("claim overlay must provide revisions and candidate_claim_ids")

    base_ids = _require_unique_ids(base_rows, "base claims")
    addition_ids = _require_unique_ids(additions, "claim additions")
    declared_base_ids = overlay.get("base_claim_ids")
    if base_ids != declared_base_ids:
        raise CompilationError("base claim order/identity differs from the registered overlay")
    if set(base_ids) & set(addition_ids):
        raise CompilationError("new claims collide with base claim ids")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise CompilationError("candidate_claim_ids contains duplicates")
    if set(candidate_ids) != set(base_ids) | set(addition_ids):
        raise CompilationError("candidate_claim_ids is not the exact base-plus-addition union")

    by_id: dict[str, dict[str, Any]] = {
        row["id"]: row for row in base_rows
    }
    revised_ids: set[str] = set()
    for revision in revisions:
        if not isinstance(revision, dict):
            raise CompilationError("every revision must be a mapping")
        claim_id = revision.get("id")
        if claim_id not in by_id:
            raise CompilationError(f"revision targets unknown base claim {claim_id!r}")
        if claim_id in revised_ids:
            raise CompilationError(f"duplicate revision for {claim_id}")
        replacement = revision.get("replacement_statement")
        if not isinstance(replacement, str) or not replacement.strip():
            raise CompilationError(f"revision {claim_id} lacks a replacement statement")
        row = by_id[claim_id]
        old_statement = row.get("statement")
        if not isinstance(old_statement, str) or not old_statement.strip():
            raise CompilationError(f"base claim {claim_id} lacks a statement")
        row["superseded_statement"] = old_statement
        row["statement"] = replacement
        row["authority"] = _merge_unique(
            row.get("authority", []), revision.get("add_authority", [])
        )
        row["forbidden_extensions"] = _merge_unique(
            row.get("forbidden_extensions", []),
            revision.get("add_forbidden_extensions", []),
        )
        row["k2f_revision_source"] = "K2_40_CLAIM_CANDIDATE_OVERLAY.yaml"
        revised_ids.add(claim_id)

    for row in additions:
        if not isinstance(row, dict):
            raise CompilationError("every addition must be a mapping")
        by_id[row["id"]] = row

    ordered_rows = [by_id[claim_id] for claim_id in candidate_ids]
    for row in ordered_rows:
        if not row.get("statement") or not row.get("authority"):
            raise CompilationError(f"claim {row.get('id')} lacks statement or authority")
        if not row.get("truth_status") or not row.get("implementation_status"):
            raise CompilationError(f"claim {row.get('id')} lacks evidence status")
        if not row.get("report_role"):
            raise CompilationError(f"claim {row.get('id')} lacks report role")

    overlay_coverage = overlay.get("coverage")
    if not isinstance(overlay_coverage, dict):
        raise CompilationError("claim overlay lacks coverage mapping")
    claim_ids = [row["id"] for row in ordered_rows]
    if len(claim_ids) != int(overlay_coverage.get("candidate_claim_count", -1)):
        raise CompilationError("compiled claim count differs from overlay coverage")

    base_coverage = base.get("coverage")
    if not isinstance(base_coverage, dict):
        raise CompilationError("base ledger lacks coverage mapping")
    coverage = {
        "claim_count": len(claim_ids),
        "canonical_sorted_id_sha256": _claim_hash(claim_ids),
        "observational_claim_count": int(overlay_coverage.get("observational_claim_count", -1)),
        "corrected_planck_rank_claim_count": int(overlay_coverage.get("corrected_planck_rank_claim_count", -1)),
        "finite_healpix_no_go_claim_count": int(overlay_coverage.get("finite_healpix_no_go_claim_count", -1)),
        "bianchi_family_claim_count": int(base_coverage.get("bianchi_family_claim_count", 0)),
        "native_bass_claim_count": int(overlay_coverage.get("native_bass_claim_count", -1)),
        "all_claims_have_authority": all(bool(row.get("authority")) for row in ordered_rows),
        "all_conditional_claims_have_assumptions_or_boundary": bool(
            base_coverage.get("all_conditional_claims_have_assumptions_or_boundary", True)
        ) and all(bool(row.get("assumptions")) for row in additions),
        "all_numerical_claims_have_execution_grade": bool(
            base_coverage.get("all_numerical_claims_have_execution_grade", True)
        ),
        "all_source_only_claims_are_not_labelled_implementation_verified": bool(
            base_coverage.get(
                "all_source_only_claims_are_not_labelled_implementation_verified", True
            )
        ),
    }
    for key in (
        "observational_claim_count",
        "corrected_planck_rank_claim_count",
        "finite_healpix_no_go_claim_count",
        "bianchi_family_claim_count",
        "native_bass_claim_count",
    ):
        if coverage[key] != 0:
            raise CompilationError(f"scope firewall {key} is not zero")

    return {
        "schema": "htt.report_a.integrated_claim_evidence_ledger.v5",
        "date": "2026-09-05",
        "repository": "cosmosapjw-quantum/htt_base",
        "report_pr": 449,
        "status": "K2F_COMPILED_FORTY_CLAIM_AUTHORITY_CANDIDATE",
        "observational_data_used": False,
        "corrected_planck_tensor_rank": None,
        "merge_authorized": False,
        "supersedes": {
            "base_ledger": "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml",
            "claim_overlay": "K2_40_CLAIM_CANDIDATE_OVERLAY.yaml",
            "base_claim_count": len(base_ids),
            "added_claim_count": len(addition_ids),
            "revised_claim_count": len(revised_ids),
            "rule": (
                "This compiled file is self-contained, but remains a source candidate "
                "until independently executed and reviewed."
            ),
        },
        "claims": ordered_rows,
        "coverage": coverage,
        "remaining_before_canonical_promotion": [
            "execute the K2F compiler and contracts on an exact checkout",
            "independently review the materialised v5 and citation matrix",
            "flatten the forty claims into the revised manuscript",
        ],
        "terminal": (
            "K2F_SELF_CONTAINED_FORTY_CLAIM_LEDGER_COMPILED_AS_SOURCE_CANDIDATE__"
            "NO_OBSERVATIONAL_OR_PUBLICATION_PROMOTION"
        ),
    }


def _compile_citations(
    base: Mapping[str, Any],
    overlay: Mapping[str, Any],
    claim_ids: Sequence[str],
) -> dict[str, Any]:
    registry = copy.deepcopy(base.get("source_registry"))
    base_rows = copy.deepcopy(base.get("claim_citations"))
    candidate_registry = copy.deepcopy(overlay.get("candidate_source_registry"))
    new_rows = copy.deepcopy(overlay.get("new_claim_citations"))
    updates = copy.deepcopy(overlay.get("revised_claim_citation_updates"))
    if not all(isinstance(value, dict) for value in (registry, base_rows, candidate_registry, new_rows, updates)):
        raise CompilationError("citation inputs must be mappings")

    for key, value in candidate_registry.items():
        if key in registry:
            raise CompilationError(f"duplicate source registry key {key}")
        registry[key] = value
    for claim_id, value in new_rows.items():
        if claim_id in base_rows:
            raise CompilationError(f"new citation row collides with {claim_id}")
        base_rows[claim_id] = value
    for claim_id, update in updates.items():
        if claim_id not in base_rows:
            raise CompilationError(f"citation update targets unknown claim {claim_id}")
        row = base_rows[claim_id]
        row["internal_authority"] = _merge_unique(
            row.get("internal_authority", []),
            update.get("add_internal_authority", []),
        )
        declared_external = update.get("external_sources_unchanged")
        if declared_external is not None and row.get("external_sources") != declared_external:
            raise CompilationError(
                f"citation update for {claim_id} changes an externally frozen source list"
            )

    if set(base_rows) != set(claim_ids):
        missing = sorted(set(claim_ids) - set(base_rows))
        extra = sorted(set(base_rows) - set(claim_ids))
        raise CompilationError(f"citation/claim mismatch; missing={missing}, extra={extra}")

    ordered_rows: list[dict[str, Any]] = []
    external_count = 0
    for claim_id in claim_ids:
        row = copy.deepcopy(base_rows[claim_id])
        if not row.get("internal_authority"):
            raise CompilationError(f"citation row {claim_id} lacks internal authority")
        external = row.get("external_sources", [])
        if not isinstance(external, list):
            raise CompilationError(f"citation row {claim_id} external_sources must be a list")
        for source in external:
            if source not in registry:
                raise CompilationError(f"citation row {claim_id} uses unknown source {source}")
        external_count += bool(external)
        ordered_rows.append({"claim_id": claim_id, **row})

    return {
        "schema": "htt.report_a.citation_provenance_matrix.v3",
        "revision": "K2F_FORTY_CLAIM_COMPILATION",
        "date": "2026-09-05",
        "repository": "cosmosapjw-quantum/htt_base",
        "report_pr": 449,
        "canonical_claim_ledger_candidate": OUTPUT_NAMES["claim_ledger"],
        "formal_bibliography_candidate": OUTPUT_NAMES["bibliography"],
        "observational_data_used": False,
        "novelty_adjudicated": False,
        "merge_authorized": False,
        "source_registry": registry,
        "claim_citations": ordered_rows,
        "coverage": {
            "claim_rows": len(ordered_rows),
            "claim_rows_with_internal_authority": len(ordered_rows),
            "claim_rows_with_external_primary_or_adjacent_sources": external_count,
            "formal_bibliography_keys": len(registry),
            "direct_literature_match_for_exact_qo_krylov16": False,
            "novelty_decisions_made": 0,
            "observational_sources_used_as_results": 0,
        },
        "citation_rules": _merge_unique(
            base.get("citation_rules", []), overlay.get("citation_rules", [])
        ),
        "terminal": (
            "K2F_FORTY_CLAIM_CITATION_MATRIX_COMPILED_AS_SOURCE_CANDIDATE__"
            "NOVELTY_UNRESOLVED__OBSERVATIONAL_DATA_DEFERRED"
        ),
    }


def bibliography_keys(text: str) -> list[str]:
    return _BIB_KEY_RE.findall(text)


def merge_bibliographies(base_text: str, supplement_text: str) -> str:
    base_keys = bibliography_keys(base_text)
    supplement_keys = bibliography_keys(supplement_text)
    all_keys = [*base_keys, *supplement_keys]
    if len(all_keys) != len(set(all_keys)):
        counts = {key: all_keys.count(key) for key in set(all_keys)}
        duplicates = sorted(key for key, count in counts.items() if count > 1)
        raise CompilationError(f"duplicate bibliography key: {duplicates}")
    if len(base_keys) != 17 or len(supplement_keys) != 3:
        raise CompilationError(
            f"unexpected bibliography partition {len(base_keys)}+{len(supplement_keys)}"
        )
    return (
        "% K2F self-contained Report-A bibliography candidate.\n"
        "% Generated from the exact 17-key authority and reviewed 3-key supplement.\n\n"
        + base_text.rstrip()
        + "\n\n"
        + supplement_text.rstrip()
        + "\n"
    )


def _read_section_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise CompilationError("section map is empty")
    return rows


def _render_section_rows(rows: Sequence[Mapping[str, str]]) -> str:
    buffer = io.StringIO(newline="")
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))
    return buffer.getvalue()


def _compile_integration(
    candidate: Mapping[str, Any], claim_ids: Sequence[str]
) -> dict[str, Any]:
    out = copy.deepcopy(candidate)
    layers = out.get("layers")
    if not isinstance(layers, list):
        raise CompilationError("integration matrix lacks layers")
    placed = [claim_id for layer in layers for claim_id in layer.get("claim_ids", [])]
    if len(placed) != len(set(placed)) or set(placed) != set(claim_ids):
        raise CompilationError("integration matrix is not an exact claim bijection")
    out["schema"] = "htt.report_a.k2.organic_integration_matrix.v3"
    out["date"] = "2026-09-05"
    out["status"] = "K2F_FORTY_CLAIM_INTEGRATION_AUTHORITY_CANDIDATE"
    out["claim_ledger_candidate"] = OUTPUT_NAMES["claim_ledger"]
    out["claim_count"] = len(claim_ids)
    out["canonical_promotion"] = False
    return out


def _verify_input_blobs(repository_root: Path) -> dict[str, str]:
    actual: dict[str, str] = {}
    for key, relative in INPUT_PATHS.items():
        path = repository_root / relative
        if not path.is_file() or path.is_symlink():
            raise CompilationError(f"registered input is absent or symlinked: {relative}")
        digest = _git_blob_sha1(path.read_bytes())
        actual[key] = digest
        expected = EXPECTED_INPUT_GIT_BLOBS[key]
        if digest != expected:
            raise CompilationError(
                f"Git blob mismatch for {relative}: expected {expected}, got {digest}"
            )
    return actual


def compile_authority_bundle(
    *,
    repository_root: Path,
    output_root: Path,
    enforce_registered_input_blobs: bool = True,
) -> dict[str, Any]:
    """Compile and write the complete K2F source-candidate bundle."""

    repository_root = repository_root.resolve()
    output_root = output_root.resolve()
    input_blobs = (
        _verify_input_blobs(repository_root)
        if enforce_registered_input_blobs
        else {
            key: _git_blob_sha1((repository_root / relative).read_bytes())
            for key, relative in INPUT_PATHS.items()
        }
    )

    base_ledger = _load_yaml(repository_root / INPUT_PATHS["base_claim_ledger"])
    claim_overlay = _load_yaml(repository_root / INPUT_PATHS["claim_overlay"])
    ledger = compile_claim_ledger(base_ledger, claim_overlay)
    claim_ids = [row["id"] for row in ledger["claims"]]

    base_citations = _load_yaml(repository_root / INPUT_PATHS["base_citation_matrix"])
    citation_overlay = _load_yaml(repository_root / INPUT_PATHS["citation_overlay"])
    citations = _compile_citations(base_citations, citation_overlay, claim_ids)

    section_rows = _read_section_rows(repository_root / INPUT_PATHS["section_map"])
    section_ids = [row.get("claim_id", "") for row in section_rows]
    if len(section_ids) != len(set(section_ids)) or set(section_ids) != set(claim_ids):
        raise CompilationError("section map is not an exact claim bijection")

    integration_candidate = _load_yaml(repository_root / INPUT_PATHS["integration_matrix"])
    integration = _compile_integration(integration_candidate, claim_ids)

    bibliography = merge_bibliographies(
        (repository_root / INPUT_PATHS["base_bibliography"]).read_text(encoding="utf-8"),
        (repository_root / INPUT_PATHS["bibliography_supplement"]).read_text(encoding="utf-8"),
    )
    bib_keys = bibliography_keys(bibliography)
    if set(bib_keys) != set(citations["source_registry"]):
        missing = sorted(set(citations["source_registry"]) - set(bib_keys))
        extra = sorted(set(bib_keys) - set(citations["source_registry"]))
        raise CompilationError(f"bibliography/source-registry mismatch; missing={missing}, extra={extra}")

    output_root.mkdir(parents=True, exist_ok=True)
    rendered: dict[str, bytes] = {
        "claim_ledger": yaml.safe_dump(
            ledger, sort_keys=False, allow_unicode=True, width=100
        ).encode("utf-8"),
        "citation_matrix": yaml.safe_dump(
            citations, sort_keys=False, allow_unicode=True, width=100
        ).encode("utf-8"),
        "section_map": _render_section_rows(section_rows).encode("utf-8"),
        "integration_matrix": yaml.safe_dump(
            integration, sort_keys=False, allow_unicode=True, width=100
        ).encode("utf-8"),
        "bibliography": bibliography.encode("utf-8"),
    }
    for key, payload in rendered.items():
        path = output_root / OUTPUT_NAMES[key]
        if path.exists():
            raise CompilationError(f"refusing to overwrite existing output {path}")
        path.write_bytes(payload)

    receipt = {
        "schema": "htt.report_a.k2f.compilation_receipt.v1",
        "date": "2026-09-05",
        "repository": "cosmosapjw-quantum/htt_base",
        "report_pr": 449,
        "input_git_blobs": input_blobs,
        "output_sha256": {key: _sha256(payload) for key, payload in rendered.items()},
        "canonical_sorted_id_sha256": ledger["coverage"]["canonical_sorted_id_sha256"],
        "claim_count": len(claim_ids),
        "citation_rows": len(citations["claim_citations"]),
        "section_rows": len(section_rows),
        "integration_rows": sum(len(layer["claim_ids"]) for layer in integration["layers"]),
        "bibliography_keys": len(bib_keys),
        "observational_data_used": False,
        "claim_promotion": False,
        "merge_authorized": False,
        "terminal": "K2F_COMPILED_AUTHORITY_BUNDLE_SOURCE_VALIDATED_NO_CLAIM_PROMOTION",
    }
    receipt_path = output_root / OUTPUT_NAMES["receipt"]
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--no-enforce-input-blobs",
        action="store_true",
        help="development-only: do not require the registered Git blob identities",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    receipt = compile_authority_bundle(
        repository_root=args.repository_root,
        output_root=args.output_root,
        enforce_registered_input_blobs=not args.no_enforce_input_blobs,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
