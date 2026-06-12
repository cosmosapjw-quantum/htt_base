"""Generated DAG status snapshot and claim-ledger sidecars.

The canonical row schemas live in :mod:`common.contracts`.  This module owns
the PR-012 generator that turns the Codex DAG backlog/status YAML into a
machine-readable status snapshot, a generated claim ledger, and a Markdown
status matrix rendered from the same source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from common.claim_ledger import claim_entry_to_dict
from common.contracts import (
    ClaimLedgerEntry,
    ClaimTier,
    ImplementationScope,
    Owner,
    StatusSnapshotEntry,
    normalize_owner,
)

DEFAULT_BACKLOG_PATH = Path("docs/codex_handoff/pr_backlog.yaml")
DEFAULT_STATUS_PATH = Path("docs/codex_handoff/pr_status.yaml")

_OWNER_SCOPE = {
    Owner.COMMON: ImplementationScope.COMMON,
    Owner.HTT: ImplementationScope.HTT,
    Owner.MIO: ImplementationScope.MIO,
    Owner.BASS: ImplementationScope.BASS_PY,
    Owner.OBSSTAT: ImplementationScope.OBSSTAT,
    Owner.TSC_LEGACY: ImplementationScope.TSC_LEGACY,
}


@dataclass(frozen=True)
class StatusBundle:
    """In-memory generated sidecar bundle."""

    metadata: dict[str, object]
    status_rows: list[dict[str, object]]
    claim_rows: list[dict[str, object]]

    def status_snapshot_payload(self) -> dict[str, object]:
        """Return the canonical JSON payload for ``status_snapshot.json``."""

        return {
            "metadata": self.metadata,
            "rows": self.status_rows,
        }

    def claim_ledger_payload(self) -> dict[str, object]:
        """Return the canonical JSON payload for ``claim_ledger.json``."""

        return {
            "metadata": {
                **self.metadata,
                "source": "common.status_snapshot.claim_ledger",
                "semantic_source": "common.contracts.ClaimLedgerEntry",
            },
            "rows": self.claim_rows,
        }


@dataclass(frozen=True)
class StatusArtifactPaths:
    """Paths written by :func:`write_status_artifacts`."""

    status_snapshot_path: Path
    claim_ledger_path: Path
    status_matrix_path: Path


def snapshot_entry_to_dict(entry: StatusSnapshotEntry) -> dict[str, object]:
    """Return a JSON-ready dictionary for one status row."""

    return _json_ready(asdict(entry))


def build_status_bundle(
    *,
    backlog_path: str | Path = DEFAULT_BACKLOG_PATH,
    status_path: str | Path = DEFAULT_STATUS_PATH,
    source_commit: str | None = None,
    generated_on: str | None = None,
    generating_command: str | None = None,
) -> StatusBundle:
    """Build generated status and claim rows from DAG/status YAML files."""

    resolved_backlog = Path(backlog_path)
    resolved_status = Path(status_path)
    backlog = _load_yaml_mapping(resolved_backlog)
    status = _load_yaml_mapping(resolved_status)
    prs = _ordered_prs(backlog)
    completed = _status_set(status.get("completed"))
    blocked = _status_set(status.get("blocked"))
    in_progress = _status_set(status.get("in_progress"))
    source = source_commit or _current_source_commit()
    command = generating_command or (
        "python -m common.status_snapshot --write docs/generated/status_snapshot.json"
    )

    status_rows: list[dict[str, object]] = []
    claim_rows: list[dict[str, object]] = []
    for pr in prs:
        pr_id = _required_str(pr, "id")
        owner = _owner_from_card(str(pr.get("owner", Owner.COMMON.value)))
        scope = _OWNER_SCOPE[owner]
        state = _state_for_pr(
            pr_id=pr_id,
            completed=completed,
            blocked=blocked,
            in_progress=in_progress,
        )
        claim_tier = ClaimTier.BLOCKED if state == "blocked" else ClaimTier.DIAGNOSTIC_ONLY
        implemented = state == "completed"
        status_rows.append(
            snapshot_entry_to_dict(
                StatusSnapshotEntry(
                    artifact_id=f"codex_dag.{pr_id}",
                    owner=owner,
                    implementation_scope=scope,
                    claim_tier=claim_tier,
                    implemented=implemented,
                    smoke_tested=implemented,
                    production_validated=False,
                    manuscript_used=False,
                    source_commit=source,
                )
            )
        )
        claim_rows.append(
            claim_entry_to_dict(
                ClaimLedgerEntry(
                    artifact_id=f"codex_dag.{pr_id}",
                    owner=owner,
                    claim_tier=claim_tier,
                    allowed_claims=(_allowed_claim(pr_id, state),),
                    forbidden_claims=(
                        (
                            "DAG status is not scientific readiness, solver validation, "
                            "transfer validation, posterior evidence, MIO certification, "
                            "morphology compatibility, or family-ID evidence."
                        ),
                    ),
                    evidence_refs=(
                        _display_path(resolved_backlog),
                        _display_path(resolved_status),
                    ),
                    source_commit=source,
                    notes=(
                        f"title={str(pr.get('title', '')).strip()}",
                        f"state={state}",
                        f"depends={','.join(str(dep) for dep in pr.get('depends', []) or []) or 'none'}",
                        "transfer_source=none",
                        "null_mock_status=not_statistical",
                        "sky_support_status=not_directional",
                    ),
                )
            )
        )

    input_hashes = _input_hashes((resolved_backlog, resolved_status))
    config_hash = _config_hash(
        {
            "backlog": _display_path(resolved_backlog),
            "status": _display_path(resolved_status),
            "input_hashes": input_hashes,
            "total_prs": len(prs),
            "completed_prs": len(completed),
            "blocked_prs": len(blocked),
            "in_progress_prs": len(in_progress),
        }
    )
    metadata: dict[str, object] = {
        "source": "common.status_snapshot",
        "semantic_source": "common.contracts.StatusSnapshotEntry",
        "generated_on": generated_on or datetime.now(UTC).replace(microsecond=0).isoformat(),
        "backlog_path": _display_path(resolved_backlog),
        "status_path": _display_path(resolved_status),
        "total_prs": len(prs),
        "completed_prs": sum(row["implemented"] is True for row in status_rows),
        "blocked_prs": len(blocked),
        "in_progress_prs": len(in_progress),
        "pending_prs": len(prs) - len(completed) - len(blocked) - len(in_progress),
        "owner": Owner.COMMON.value,
        "implementation_scope": ImplementationScope.COMMON.value,
        "claim_tier": ClaimTier.DIAGNOSTIC_ONLY.value,
        "transfer_source": "none",
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "caveats": [
            "DAG completion is project bookkeeping only and is not scientific readiness.",
            "Rows never promote external-transfer outputs to native solver validation.",
            "production_validated remains false until explicit native/null/mask/covariance gates exist.",
        ],
        "generating_command": command,
        "source_commit": source,
        "worktree_state": _worktree_state(),
    }
    return StatusBundle(
        metadata=metadata,
        status_rows=status_rows,
        claim_rows=claim_rows,
    )


def render_status_matrix(bundle: StatusBundle) -> str:
    """Render a human-readable matrix from a generated bundle."""

    metadata = bundle.metadata
    by_owner = Counter(str(row["owner"]) for row in bundle.status_rows)
    by_state = Counter(_state_from_row(row) for row in bundle.status_rows)
    owner_lines = "\n".join(
        f"| `{owner}` | {count} |" for owner, count in sorted(by_owner.items())
    )
    state_lines = "\n".join(
        f"| `{state}` | {count} |" for state, count in sorted(by_state.items())
    )
    return "\n".join(
        (
            "<!-- Generated by common.status_snapshot; do not edit counts by hand. -->",
            "# Generated Status Matrix",
            "",
            "Semantic source: `htt/src/common/contracts.py::StatusSnapshotEntry`",
            "",
            "Manual status counts are prohibited; use `docs/generated/status_snapshot.json` as the canonical public status source.",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Total PRs | {metadata['total_prs']} |",
            f"| Completed PRs | {metadata['completed_prs']} |",
            f"| Blocked PRs | {metadata['blocked_prs']} |",
            f"| In progress | {metadata['in_progress_prs']} |",
            f"| Pending PRs | {metadata['pending_prs']} |",
            "",
            "| Metadata | Value |",
            "| --- | --- |",
            f"| Claim tier | `{metadata['claim_tier']}` |",
            f"| Transfer source | `{metadata['transfer_source']}` |",
            f"| Config hash | `{metadata['config_hash']}` |",
            f"| Source commit | `{metadata['source_commit']}` |",
            f"| Worktree state | `{metadata['worktree_state']}` |",
            "",
            "| Owner | Rows |",
            "| --- | ---: |",
            owner_lines,
            "",
            "| State | Rows |",
            "| --- | ---: |",
            state_lines,
            "",
            "This matrix is a diagnostic-only DAG rendering. It does not certify solver validation, posterior evidence, native transfer validation, or family-ID evidence.",
        )
    ) + "\n"


def validate_status_matrix_matches_snapshot(
    markdown: str,
    snapshot_payload: Mapping[str, object],
) -> None:
    """Raise when generated Markdown count rows drift from the JSON snapshot."""

    metadata = snapshot_payload.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("status snapshot payload is missing metadata")
    matrix_counts = _extract_matrix_counts(markdown)
    expected = {
        "Total PRs": int(metadata["total_prs"]),
        "Completed PRs": int(metadata["completed_prs"]),
        "Blocked PRs": int(metadata["blocked_prs"]),
        "In progress": int(metadata["in_progress_prs"]),
        "Pending PRs": int(metadata["pending_prs"]),
    }
    mismatches = [
        f"{metric}: markdown={matrix_counts.get(metric)!r} snapshot={value!r}"
        for metric, value in expected.items()
        if matrix_counts.get(metric) != value
    ]
    if mismatches:
        raise ValueError(
            "generated status matrix count mismatch: " + "; ".join(mismatches)
        )


def write_status_artifacts(
    output_path: str | Path,
    *,
    backlog_path: str | Path = DEFAULT_BACKLOG_PATH,
    status_path: str | Path = DEFAULT_STATUS_PATH,
    source_commit: str | None = None,
    generating_command: str | None = None,
) -> StatusArtifactPaths:
    """Write status snapshot, companion claim ledger, and status matrix."""

    status_snapshot_path = Path(output_path)
    claim_ledger_path = status_snapshot_path.with_name("claim_ledger.json")
    status_matrix_path = status_snapshot_path.with_name("status_matrix.md")
    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit=source_commit,
        generating_command=generating_command,
    )
    snapshot_payload = bundle.status_snapshot_payload()
    claim_payload = bundle.claim_ledger_payload()
    matrix = render_status_matrix(bundle)
    validate_status_matrix_matches_snapshot(matrix, snapshot_payload)

    status_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(status_snapshot_path, snapshot_payload)
    _write_json(claim_ledger_path, claim_payload)
    status_matrix_path.write_text(matrix, encoding="utf-8")
    return StatusArtifactPaths(
        status_snapshot_path=status_snapshot_path,
        claim_ledger_path=claim_ledger_path,
        status_matrix_path=status_matrix_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for ``python -m common.status_snapshot``."""

    parser = argparse.ArgumentParser(
        description="Generate DAG status snapshot and claim-ledger sidecars."
    )
    parser.add_argument(
        "--backlog",
        type=Path,
        default=DEFAULT_BACKLOG_PATH,
        help="Path to pr_backlog.yaml.",
    )
    parser.add_argument(
        "--status",
        type=Path,
        default=DEFAULT_STATUS_PATH,
        help="Path to pr_status.yaml.",
    )
    parser.add_argument(
        "--source-commit",
        default=None,
        help="Override source commit recorded in generated rows.",
    )
    parser.add_argument(
        "--write",
        type=Path,
        required=True,
        help="Path for status_snapshot.json; companion files are written nearby.",
    )
    args = parser.parse_args(argv)
    command = "python -m common.status_snapshot " + " ".join(sys.argv[1:])
    written = write_status_artifacts(
        args.write,
        backlog_path=args.backlog,
        status_path=args.status,
        source_commit=args.source_commit,
        generating_command=command,
    )
    print(f"wrote {written.status_snapshot_path}")
    print(f"wrote {written.claim_ledger_path}")
    print(f"wrote {written.status_matrix_path}")
    return 0


def _load_yaml_mapping(path: Path) -> Mapping[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a YAML mapping")
    return payload


def _ordered_prs(backlog: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_prs = backlog.get("prs")
    if not isinstance(raw_prs, list):
        raise ValueError("backlog must contain a prs list")
    by_id: dict[str, Mapping[str, object]] = {}
    for raw in raw_prs:
        if not isinstance(raw, Mapping):
            raise ValueError("every PR card must be a mapping")
        pr_id = _required_str(raw, "id")
        by_id[pr_id] = raw
    order = _topological_order(backlog)
    ordered = [by_id[pr_id] for pr_id in order if pr_id in by_id]
    remaining = sorted(set(by_id) - set(order))
    ordered.extend(by_id[pr_id] for pr_id in remaining)
    return ordered


def _topological_order(backlog: Mapping[str, object]) -> list[str]:
    policy = backlog.get("policy")
    if isinstance(policy, Mapping):
        raw_order = policy.get("topological_order")
        if isinstance(raw_order, list):
            return [str(pr_id) for pr_id in raw_order]
    raw_order = backlog.get("topological_order")
    if isinstance(raw_order, list):
        return [str(pr_id) for pr_id in raw_order]
    return []


def _owner_from_card(raw_owner: str) -> Owner:
    owner = raw_owner.strip()
    if owner == "BASS_PY":
        return Owner.BASS
    if owner == "MANUSCRIPT":
        return Owner.COMMON
    return normalize_owner(owner)


def _required_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"PR card missing non-empty {key}")
    return value


def _status_set(value: object) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {str(item) for item in value if str(item)}
    raise ValueError("status fields must be null, a string, or a list")


def _state_for_pr(
    *,
    pr_id: str,
    completed: set[str],
    blocked: set[str],
    in_progress: set[str],
) -> str:
    if pr_id in completed:
        return "completed"
    if pr_id in blocked:
        return "blocked"
    if pr_id in in_progress:
        return "in_progress"
    return "pending"


def _state_from_row(row: Mapping[str, object]) -> str:
    if bool(row.get("implemented")):
        return "completed"
    if row.get("claim_tier") == ClaimTier.BLOCKED.value:
        return "blocked"
    return "not_completed"


def _allowed_claim(pr_id: str, state: str) -> str:
    return f"{pr_id} is marked {state.replace('_', ' ')} in the Codex DAG status snapshot."


def _input_hashes(paths: Sequence[Path]) -> list[str]:
    return [f"{_display_path(path)}:{_sha256_file(path)}" for path in paths]


def _config_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(_json_ready(payload), sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _current_source_commit() -> str:
    commit = _run_git(("rev-parse", "--short", "HEAD")) or "unknown"
    state = _worktree_state()
    return f"{commit}+dirty" if state == "dirty" else commit


def _worktree_state() -> str:
    status = _run_git(("status", "--short"))
    if status is None:
        return "unknown"
    return "dirty" if status else "clean"


def _run_git(args: Sequence[str]) -> str | None:
    completed = subprocess.run(
        ("git", *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _extract_matrix_counts(markdown: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in markdown.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2:
            continue
        metric, raw_value = cells
        if metric in {"Metric", "---"}:
            continue
        try:
            counts[metric] = int(raw_value)
        except ValueError:
            continue
    return counts


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (Owner, ImplementationScope, ClaimTier)):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    return value


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
