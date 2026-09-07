#!/usr/bin/env python3
"""Generate the PR-408 WU-001 registered survivor source surface.

This script does one deliberately narrow job.  It reads the frozen PR-405
candidate matrix and materializes every eligible broad PASS row plus every
declared supplemental scoped candidate.  It does *not* assign truth, novelty,
or publication roles.  Those are successor decisions.

The generated surface preserves broad/scoped identities, source terminal
states, evidence references, semantic links, and exact source-object identity.
It fails closed on count drift, duplicate identities, observed-data use, or a
missing statement identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence


SOURCE_SCHEMA = "htt.theory_promotion_matrix.v1"
OUTPUT_SCHEMA = "htt.registered_survivor_surface.v1"
EXACT_RESULT_CLASS = "EXACT_OR_CONDITIONAL_THEOREM_CORE"
SYNTHETIC_RESULT_CLASS = "PREREGISTERED_SYNTHETIC_RESULT_NOT_THEOREM"
TERMINAL_TO_TRIAGE = {
    "PROMOTED": "INCLUDED",
    "UNRESOLVED": "DEFERRED",
    "DEFERRED": "DEFERRED",
    "NOT_ATTEMPTED": "DEFERRED",
    "REFUTED": "EXCLUDED",
}
FORBIDDEN_ASSIGNMENT_KEYS = {
    "truth_status",
    "novelty_status",
    "publication_role",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SurvivorTriageError(ValueError):
    """Raised when the frozen survivor-source contract fails closed."""


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SurvivorTriageError(f"{name} must be a mapping")
    return value


def _sequence(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise SurvivorTriageError(f"{name} must be a sequence")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SurvivorTriageError(f"{name} must be non-empty trimmed text")
    return value


def _optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise SurvivorTriageError(f"{name} must be an integer >= {minimum}")
    return value


def _scoped_coverage_counts(coverage: Mapping[str, Any]) -> tuple[int, int]:
    """Read the real nested declaration or a complete legacy flat pair."""
    keys = (
        "supplemental_scoped_candidates_expected",
        "supplemental_scoped_candidates_classified",
    )
    path = "candidate_coverage_proof"

    def pair(value: Mapping[str, Any], name: str) -> tuple[int, int]:
        return (
            _integer(value.get(keys[0]), f"{name}.{keys[0]}"),
            _integer(value.get(keys[1]), f"{name}.{keys[1]}"),
        )

    if "coverage_basis" not in coverage:
        return pair(coverage, path)
    nested = _mapping(coverage["coverage_basis"], f"{path}.coverage_basis")
    counts = pair(nested, f"{path}.coverage_basis")
    if any(key in coverage for key in keys):
        if pair(coverage, path) != counts:
            raise SurvivorTriageError(
                "duplicate scoped coverage declarations disagree"
            )
    return counts


def _sha256(value: object, name: str) -> str:
    text = _text(value, name)
    if _SHA256_RE.fullmatch(text) is None:
        raise SurvivorTriageError(f"{name} must be a lowercase SHA-256 hex digest")
    return text


def _texts(value: object, name: str) -> list[str]:
    out = [
        _text(item, f"{name}[{index}]")
        for index, item in enumerate(_sequence(value, name))
    ]
    if len(out) != len(set(out)):
        raise SurvivorTriageError(f"{name} must not contain duplicates")
    return out


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def _content_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _run_git(repo: Path, *args: str, text: bool = False) -> bytes | str:
    command = ["git", "-C", str(repo), *args]
    try:
        return subprocess.check_output(
            command, stderr=subprocess.STDOUT, text=text
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "output", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", errors="replace")
        raise SurvivorTriageError(
            f"git command failed: {' '.join(command)}; {str(detail).strip()}"
        ) from exc


def load_git_source(
    *,
    repo: Path,
    ref: str,
    path: str,
    expected_blob: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read one matrix from an exact Git object without checking it out."""

    repo = repo.resolve()
    if not repo.is_dir():
        raise SurvivorTriageError("repository path does not exist")
    ref = _text(ref, "matrix ref")
    path = _text(path, "matrix path")
    commit = str(
        _run_git(repo, "rev-parse", f"{ref}^{{commit}}", text=True)
    ).strip()
    blob = str(
        _run_git(repo, "rev-parse", f"{ref}:{path}", text=True)
    ).strip()
    if expected_blob is not None and blob != _text(
        expected_blob, "expected git blob"
    ):
        raise SurvivorTriageError(
            f"matrix git blob mismatch: expected {expected_blob}, observed {blob}"
        )
    raw = _run_git(repo, "show", f"{ref}:{path}")
    assert isinstance(raw, bytes)
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SurvivorTriageError("matrix Git object is not UTF-8") from exc
    try:
        matrix = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise SurvivorTriageError("matrix Git object is not valid JSON") from exc
    if not isinstance(matrix, dict):
        raise SurvivorTriageError("matrix JSON root must be an object")
    source = {
        "mode": "GIT_OBJECT",
        "commit": commit,
        "git_blob": blob,
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    return matrix, source


def load_file_source(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = path.resolve()
    if not path.is_file():
        raise SurvivorTriageError("matrix file does not exist")
    raw = path.read_bytes()
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SurvivorTriageError("matrix file is not UTF-8") from exc
    try:
        matrix = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise SurvivorTriageError("matrix file is not valid JSON") from exc
    if not isinstance(matrix, dict):
        raise SurvivorTriageError("matrix JSON root must be an object")
    source = {
        "mode": "DIRECT_FILE",
        "commit": None,
        "git_blob": None,
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    return matrix, source


def _validate_source(source: Mapping[str, Any]) -> dict[str, Any]:
    mode = _text(source.get("mode", "BOUND_METADATA"), "source.mode")
    path = _text(source.get("path"), "source.path")
    digest = _sha256(source.get("sha256"), "source.sha256")
    commit = _optional_text(source.get("commit"), "source.commit")
    git_blob = _optional_text(source.get("git_blob"), "source.git_blob")
    if mode == "GIT_OBJECT" and (commit is None or git_blob is None):
        raise SurvivorTriageError(
            "Git-object source requires commit and git blob"
        )
    return {
        "mode": mode,
        "commit": commit,
        "git_blob": git_blob,
        "path": path,
        "sha256": digest,
    }


def _all_candidate_ids(
    rows: Sequence[Any],
    scoped: Sequence[Any],
) -> list[str]:
    ids: list[str] = []
    for index, raw in enumerate(rows):
        row = _mapping(raw, f"rows[{index}]")
        ids.append(_text(row.get("claim_id"), f"rows[{index}].claim_id"))
    for index, raw in enumerate(scoped):
        row = _mapping(raw, f"supplemental_scoped_candidates[{index}]")
        ids.append(
            _text(
                row.get("candidate_id"),
                f"supplemental_scoped_candidates[{index}].candidate_id",
            )
        )
    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        raise SurvivorTriageError(
            "duplicate candidate identity in source matrix: "
            + ", ".join(duplicates)
        )
    return ids


def _broad_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    candidate_id = _text(row.get("claim_id"), "broad candidate claim_id")
    statement_id = _sha256(
        row.get("source_statement_identity_sha256"),
        f"{candidate_id}.source statement identity",
    )
    if row.get("observed_data_used") is not False:
        raise SurvivorTriageError(
            f"eligible candidate {candidate_id} uses observed data"
        )
    result_class = _text(
        row.get("theory_result_class"),
        f"{candidate_id}.theory_result_class",
    )
    if result_class == EXACT_RESULT_CLASS:
        survivor_class = "EXACT_OR_CONDITIONAL_BROAD"
    elif result_class == SYNTHETIC_RESULT_CLASS:
        survivor_class = "SYNTHETIC_BROAD"
    else:
        raise SurvivorTriageError(
            f"eligible broad candidate {candidate_id} uses an unknown result class"
        )
    statement = row.get("source_statement")
    if statement is None:
        statement = row.get("adjudicated_statement")
    return {
        "candidate_id": candidate_id,
        "source_kind": "BROAD_ROW",
        "triage_disposition": "INCLUDED",
        "survivor_class": survivor_class,
        "parent_candidate_id": None,
        "source_statement": _text(
            statement, f"{candidate_id}.source_statement"
        ),
        "source_statement_identity_sha256": statement_id,
        "source_terminal_state": _text(
            row.get("scientific_terminal_state"),
            f"{candidate_id}.scientific_terminal_state",
        ),
        "source_broad_verdict": _text(
            row.get("broad_verdict"),
            f"{candidate_id}.broad_verdict",
        ),
        "source_theory_result_class": result_class,
        "source_group": _optional_text(
            row.get("source_group"), f"{candidate_id}.source_group"
        ),
        "source_partition": _optional_text(
            row.get("source_partition"), f"{candidate_id}.source_partition"
        ),
        "source_row_id": _optional_text(
            row.get("source_row_id"), f"{candidate_id}.source_row_id"
        ),
        "source_release_disposition": _optional_text(
            row.get("current_release_disposition"),
            f"{candidate_id}.current_release_disposition",
        ),
        "claim_ceiling": _optional_text(
            row.get("claim_ceiling"), f"{candidate_id}.claim_ceiling"
        ),
        "evidence_refs": sorted(
            _texts(
                row.get("evidence_refs", []),
                f"{candidate_id}.evidence_refs",
            )
        ),
        "observed_data_used": False,
    }


def _scoped_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    candidate_id = _text(row.get("candidate_id"), "scoped candidate_id")
    parent = _text(row.get("source_candidate_id"), f"{candidate_id}.parent")
    if candidate_id == parent:
        raise SurvivorTriageError(
            f"scoped candidate {candidate_id} collapses into its broad parent"
        )
    if row.get("observed_data_used") is not False:
        raise SurvivorTriageError(
            f"declared scoped candidate {candidate_id} uses observed data"
        )
    terminal = _text(
        row.get("scientific_terminal_state"),
        f"{candidate_id}.scientific_terminal_state",
    )
    try:
        disposition = TERMINAL_TO_TRIAGE[terminal]
    except KeyError as exc:
        raise SurvivorTriageError(
            f"scoped candidate {candidate_id} uses unknown terminal state {terminal}"
        ) from exc
    return {
        "candidate_id": candidate_id,
        "source_kind": "SCOPED_CHILD",
        "triage_disposition": disposition,
        "survivor_class": _text(
            row.get("candidate_kind"), f"{candidate_id}.candidate_kind"
        ),
        "parent_candidate_id": parent,
        "source_statement": _text(
            row.get("statement"), f"{candidate_id}.statement"
        ),
        "source_statement_identity_sha256": _sha256(
            row.get("statement_identity_sha256"),
            f"{candidate_id}.statement identity",
        ),
        "source_terminal_state": terminal,
        "source_broad_verdict": None,
        "source_theory_result_class": None,
        "source_group": None,
        "source_partition": None,
        "source_row_id": None,
        "source_release_disposition": _optional_text(
            row.get("current_release_disposition"),
            f"{candidate_id}.current_release_disposition",
        ),
        "claim_ceiling": _optional_text(
            row.get("claim_ceiling"), f"{candidate_id}.claim_ceiling"
        ),
        "evidence_refs": sorted(
            _texts(
                row.get("evidence_refs", []),
                f"{candidate_id}.evidence_refs",
            )
        ),
        "observed_data_used": False,
    }


def _relation_surface(
    matrix: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    included_ids = {str(row["candidate_id"]) for row in candidates}
    parent_ids = {
        str(row["parent_candidate_id"])
        for row in candidates
        if row.get("parent_candidate_id") is not None
    }
    relevant = included_ids | parent_ids
    relations: list[dict[str, Any]] = []

    for index, raw in enumerate(matrix.get("semantic_links", [])):
        link = _mapping(raw, f"semantic_links[{index}]")
        claims = _texts(link.get("claims"), f"semantic_links[{index}].claims")
        if not relevant.intersection(claims):
            continue
        relations.append(
            {
                "claims": claims,
                "relation": _text(
                    link.get("relation"), f"semantic_links[{index}].relation"
                ),
                "note": _optional_text(
                    link.get("note"), f"semantic_links[{index}].note"
                ),
                "source": "PR405_SEMANTIC_LINK",
            }
        )

    for row in candidates:
        parent = row.get("parent_candidate_id")
        if parent is None:
            continue
        relations.append(
            {
                "claims": [str(parent), str(row["candidate_id"])],
                "relation": "PARENT_CHILD",
                "note": (
                    "Broad parent and scoped child remain distinct "
                    "statement identities."
                ),
                "source": "PR405_SUPPLEMENTAL_SCOPED_CANDIDATE",
            }
        )
    relations.sort(key=lambda item: canonical_bytes(item))
    return relations


def _forbidden_key_scan(value: object, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in FORBIDDEN_ASSIGNMENT_KEYS:
                raise SurvivorTriageError(
                    f"A2 source surface must not assign {key} at {path}"
                )
            _forbidden_key_scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _forbidden_key_scan(child, f"{path}[{index}]")


def build_surface(
    matrix: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
) -> dict[str, Any]:
    """Build and validate the deterministic WU-001 source surface."""

    matrix = _mapping(matrix, "matrix")
    if matrix.get("schema") != SOURCE_SCHEMA:
        raise SurvivorTriageError(f"matrix schema must be {SOURCE_SCHEMA}")
    scope = _mapping(matrix.get("scope"), "matrix.scope")
    if scope.get("observed_data_used") is not False:
        raise SurvivorTriageError("source matrix uses observed data")
    coverage_source = _mapping(
        matrix.get("candidate_coverage_proof"),
        "matrix.candidate_coverage_proof",
    )
    if coverage_source.get("coverage_complete") is not True:
        raise SurvivorTriageError("source candidate coverage is not complete")

    rows = _sequence(matrix.get("rows"), "matrix.rows")
    scoped_rows = _sequence(
        matrix.get("supplemental_scoped_candidates"),
        "matrix.supplemental_scoped_candidates",
    )
    _all_candidate_ids(rows, scoped_rows)

    broad_exact: list[dict[str, Any]] = []
    broad_synthetic: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        row = _mapping(raw, f"rows[{index}]")
        if not (
            row.get("broad_verdict") == "PASS"
            and row.get("scientific_terminal_state") == "PROMOTED"
        ):
            continue
        candidate = _broad_candidate(row)
        if candidate["survivor_class"] == "EXACT_OR_CONDITIONAL_BROAD":
            broad_exact.append(candidate)
        else:
            broad_synthetic.append(candidate)

    counts = _mapping(matrix.get("counts"), "matrix.counts")
    declared_exact = _integer(
        counts.get("exact_or_conditional_theory_pass_rows"),
        "counts.exact_or_conditional_theory_pass_rows",
    )
    declared_synthetic = _integer(
        counts.get("synthetic_only_pass_rows"),
        "counts.synthetic_only_pass_rows",
    )
    declared_broad = _integer(
        counts.get("row_level_pass_total"),
        "counts.row_level_pass_total",
    )
    observed_broad = len(broad_exact) + len(broad_synthetic)
    if (
        len(broad_exact) != declared_exact
        or len(broad_synthetic) != declared_synthetic
        or observed_broad != declared_broad
    ):
        raise SurvivorTriageError(
            "broad PASS count differs from the frozen source declaration: "
            f"exact={len(broad_exact)}/{declared_exact}, "
            f"synthetic={len(broad_synthetic)}/{declared_synthetic}, "
            f"total={observed_broad}/{declared_broad}"
        )

    declared_scoped, classified_scoped = _scoped_coverage_counts(coverage_source)
    if (
        len(scoped_rows) != declared_scoped
        or classified_scoped != declared_scoped
    ):
        raise SurvivorTriageError(
            "declared scoped-child count differs from source coverage"
        )
    scoped = [
        _scoped_candidate(
            _mapping(raw, f"supplemental_scoped_candidates[{index}]")
        )
        for index, raw in enumerate(scoped_rows)
    ]

    candidates = sorted(
        broad_exact + broad_synthetic + scoped,
        key=lambda row: str(row["candidate_id"]),
    )
    ids = [str(row["candidate_id"]) for row in candidates]
    if len(ids) != len(set(ids)):
        raise SurvivorTriageError(
            "duplicate candidate identity in generated surface"
        )

    dispositions = {
        name: sum(row["triage_disposition"] == name for row in candidates)
        for name in ("INCLUDED", "DEFERRED", "EXCLUDED")
    }
    expected_included = declared_broad + sum(
        row["source_terminal_state"] == "PROMOTED" for row in scoped
    )
    if dispositions["INCLUDED"] != expected_included:
        raise SurvivorTriageError("included survivor count is inconsistent")

    normalized_source = _validate_source(source)
    payload: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "source": normalized_source,
        "purpose": (
            "Mechanically complete source triage for PR-408 WU-001; "
            "no truth, novelty, or publication-role assignment."
        ),
        "release_authority": False,
        "observed_data_used": False,
        "unique_theorem_count": None,
        "coverage": {
            "exact_or_conditional_broad": len(broad_exact),
            "synthetic_broad": len(broad_synthetic),
            "broad_total": observed_broad,
            "scoped_children": len(scoped),
            "registered_total": len(candidates),
            "included_total": dispositions["INCLUDED"],
            "deferred_total": dispositions["DEFERRED"],
            "excluded_total": dispositions["EXCLUDED"],
            "missing_disposition_count": 0,
            "duplicate_candidate_id_count": 0,
        },
        "invariants": {
            "all_eligible_broad_rows_present": True,
            "all_declared_scoped_children_present": True,
            "broad_parent_scoped_child_identity_separate": True,
            "semantic_duplicates_not_collapsed": True,
            "truth_novelty_publication_unassigned": True,
            "observational_claims_admitted": False,
        },
        "candidates": candidates,
        "relations": _relation_surface(matrix, candidates),
    }
    _forbidden_key_scan(payload)
    payload["content_id"] = _content_id(payload)
    return payload


def write_surface(
    surface: Mapping[str, Any],
    output: Path,
    *,
    replace: bool = False,
) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not replace:
        raise SurvivorTriageError(
            f"output already exists and is preserved: {output}"
        )
    data = canonical_bytes(surface)
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    temporary.write_bytes(data)
    temporary.replace(output)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--matrix", type=Path, help="Direct matrix JSON path")
    source.add_argument("--repo", type=Path, help="Git repository root")
    parser.add_argument("--matrix-ref", help="Exact commit/ref for --repo mode")
    parser.add_argument("--matrix-path", help="Repository path for --repo mode")
    parser.add_argument("--expect-git-blob", help="Expected matrix Git blob SHA")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.matrix is not None:
            if args.matrix_ref or args.matrix_path or args.expect_git_blob:
                raise SurvivorTriageError(
                    "Git-object arguments cannot accompany --matrix"
                )
            matrix, source = load_file_source(args.matrix)
        else:
            if not args.matrix_ref or not args.matrix_path:
                raise SurvivorTriageError(
                    "--repo requires --matrix-ref and --matrix-path"
                )
            matrix, source = load_git_source(
                repo=args.repo,
                ref=args.matrix_ref,
                path=args.matrix_path,
                expected_blob=args.expect_git_blob,
            )
        surface = build_surface(matrix, source=source)
        write_surface(surface, args.output, replace=args.replace)
    except SurvivorTriageError as exc:
        print(f"STOP_INVALID: {exc}", file=sys.stderr)
        return 2

    summary = {
        "state": "REGISTERED_SURVIVOR_SOURCE_SURFACE_GENERATED",
        "output": str(args.output.resolve()),
        "content_id": surface["content_id"],
        "coverage": surface["coverage"],
        "release_authority": False,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
