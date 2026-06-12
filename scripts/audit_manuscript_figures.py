#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
for root in (COMMON_ROOT, REPO_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from common.artifact_manifest import (  # noqa: E402
    DEFAULT_SCAN_ROOTS,
    FIGURE_SUFFIXES,
    build_quarantine_report,
)
from common.semantic_guards.no_overclaim import scan_text  # noqa: E402


DEFAULT_MANUSCRIPT_ROOT = REPO_ROOT / "docs" / "manuscript"
DEFAULT_INVENTORY_OUTPUT = (
    REPO_ROOT / "docs" / "generated" / "manuscript_figure_inventory.md"
)
DEFAULT_MISSING_OUTPUT = (
    REPO_ROOT / "docs" / "generated" / "missing_figure_references.md"
)
GRAPHICS_EXTENSIONS = tuple(sorted(FIGURE_SUFFIXES | {".eps"}))
INCLUDEGRAPHICS_RE = re.compile(
    r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}"
)
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}]+\}\s*)+)\}")
GRAPHICSPATH_ITEM_RE = re.compile(r"\{([^{}]+)\}")
MANUAL_STATUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("pytest_count", re.compile(r"\b\d+\s+passed\b", re.IGNORECASE)),
    (
        "test_count",
        re.compile(r"\b\d+\s+(?:automated\s+)?tests?\b", re.IGNORECASE),
    ),
    (
        "module_count",
        re.compile(r"\b\d+\s+production\s+modules?\b", re.IGNORECASE),
    ),
    (
        "manifest_ready_count",
        re.compile(r"\b\d+\s+(?:are\s+)?manifest-ready\b", re.IGNORECASE),
    ),
    (
        "blocked_figure_count",
        re.compile(r"\b\d+\s+(?:remain\s+)?blocked\b", re.IGNORECASE),
    ),
    (
        "status_counter",
        re.compile(
            r"\b(?:implemented|production-validated|smoke-tested|manuscript-used)\s*[=:]?\s*\d+\b",
            re.IGNORECASE,
        ),
    ),
)
CLAIM_RISK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "solver_validated_transfer",
        re.compile(
            r"\b(?:solver[- ]validated|validated by the solver)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "overstrong_validation_wording",
        re.compile(
            r"\bvalidated for\b",
            re.IGNORECASE,
        ),
    ),
    (
        "premature_family_identification",
        re.compile(r"\bfamily identification\b", re.IGNORECASE),
    ),
    (
        "production_value",
        re.compile(r"\bproduction values?\b", re.IGNORECASE),
    ),
)
FAMILY_IDENTIFICATION_NEGATIONS = (
    "family identification is not established",
    "family identification remains blocked",
    "family identification is blocked",
    "no family identification",
)


@dataclass(frozen=True)
class IncludeGraphicsRef:
    tex_path: str
    line: int
    include_path: str


@dataclass(frozen=True)
class ManuscriptFigureRecord:
    tex_path: str
    line: int
    include_path: str
    status: str
    reason: str
    resolved_path: str | None
    manifest_path: str | None


@dataclass(frozen=True)
class ManuscriptTextIssue:
    path: str
    line: int
    issue_type: str
    rule_id: str
    text: str


@dataclass(frozen=True)
class ManuscriptFigureAudit:
    manuscript_root: str
    scan_roots: tuple[str, ...]
    graphicspaths: tuple[str, ...]
    figure_records: tuple[ManuscriptFigureRecord, ...]
    text_issues: tuple[ManuscriptTextIssue, ...]
    tex_inputs: tuple[str, ...]

    @property
    def missing_records(self) -> tuple[ManuscriptFigureRecord, ...]:
        return tuple(record for record in self.figure_records if record.status == "missing")

    @property
    def quarantined_records(self) -> tuple[ManuscriptFigureRecord, ...]:
        return tuple(
            record for record in self.figure_records if record.status == "quarantined"
        )

    @property
    def resolved_records(self) -> tuple[ManuscriptFigureRecord, ...]:
        return tuple(record for record in self.figure_records if record.status == "resolved")


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _strip_tex_comment(line: str) -> str:
    escaped = False
    for index, char in enumerate(line):
        if char == "%" and not escaped:
            return line[:index]
        escaped = char == "\\" and not escaped
    return line


def _iter_tex_files(manuscript_root: Path) -> tuple[Path, ...]:
    return tuple(sorted(manuscript_root.rglob("*.tex")))


def _extract_graphicspaths(tex_files: Iterable[Path]) -> tuple[str, ...]:
    paths: list[str] = []
    seen: set[str] = set()
    for tex_file in tex_files:
        text = tex_file.read_text(encoding="utf-8", errors="ignore")
        for match in GRAPHICSPATH_RE.finditer(text):
            for item in GRAPHICSPATH_ITEM_RE.findall(match.group(1)):
                clean = item.strip()
                if clean and clean not in seen:
                    seen.add(clean)
                    paths.append(clean)
    return tuple(paths)


def _extract_includegraphics(tex_file: Path, repo_root: Path) -> tuple[IncludeGraphicsRef, ...]:
    refs: list[IncludeGraphicsRef] = []
    for line_number, line in enumerate(
        tex_file.read_text(encoding="utf-8", errors="ignore").splitlines(),
        1,
    ):
        stripped = _strip_tex_comment(line)
        for match in INCLUDEGRAPHICS_RE.finditer(stripped):
            refs.append(
                IncludeGraphicsRef(
                    tex_path=_repo_relative(tex_file, repo_root),
                    line=line_number,
                    include_path=match.group(1).strip(),
                )
            )
    return tuple(refs)


def _with_candidate_extensions(path: Path) -> tuple[Path, ...]:
    if path.suffix:
        return (path,)
    return tuple(path.with_suffix(suffix) for suffix in GRAPHICS_EXTENSIONS)


def _resolve_candidates(
    include_path: str,
    *,
    tex_file: Path,
    repo_root: Path,
    manuscript_root: Path,
    graphicspaths: tuple[str, ...],
) -> tuple[Path, ...]:
    raw = Path(include_path)
    bases: list[Path] = []
    if raw.is_absolute():
        bases.append(Path("/"))
    else:
        bases.extend([tex_file.parent, manuscript_root, repo_root])
        for graphicspath in graphicspaths:
            graph_path = Path(graphicspath)
            if graph_path.is_absolute():
                bases.append(graph_path)
            else:
                bases.extend(
                    [
                        repo_root / graph_path,
                        manuscript_root / graph_path,
                        tex_file.parent / graph_path,
                    ]
                )
    candidates: list[Path] = []
    seen: set[Path] = set()
    for base in bases:
        stem = raw if raw.is_absolute() else base / raw
        for candidate in _with_candidate_extensions(stem):
            normalized = candidate.resolve()
            if normalized not in seen:
                seen.add(normalized)
                candidates.append(normalized)
    return tuple(candidates)


def _manual_status_issues(tex_file: Path, repo_root: Path) -> tuple[ManuscriptTextIssue, ...]:
    issues: list[ManuscriptTextIssue] = []
    for line_number, line in enumerate(
        tex_file.read_text(encoding="utf-8", errors="ignore").splitlines(),
        1,
    ):
        stripped = _strip_tex_comment(line).strip()
        if not stripped:
            continue
        for rule_id, pattern in MANUAL_STATUS_PATTERNS:
            if pattern.search(stripped):
                issues.append(
                    ManuscriptTextIssue(
                        path=_repo_relative(tex_file, repo_root),
                        line=line_number,
                        issue_type="manual_status_number",
                        rule_id=rule_id,
                        text=stripped,
                    )
                )
                break
    return tuple(issues)


def _claim_risk_issues(tex_file: Path, repo_root: Path) -> tuple[ManuscriptTextIssue, ...]:
    issues: list[ManuscriptTextIssue] = []
    for line_number, line in enumerate(
        tex_file.read_text(encoding="utf-8", errors="ignore").splitlines(),
        1,
    ):
        stripped = _strip_tex_comment(line).strip()
        if not stripped:
            continue
        for rule_id, pattern in CLAIM_RISK_PATTERNS:
            if pattern.search(stripped):
                if rule_id == "premature_family_identification" and any(
                    negation in stripped.lower()
                    for negation in FAMILY_IDENTIFICATION_NEGATIONS
                ):
                    continue
                issues.append(
                    ManuscriptTextIssue(
                        path=_repo_relative(tex_file, repo_root),
                        line=line_number,
                        issue_type="claim_risk_phrase",
                        rule_id=rule_id,
                        text=stripped,
                    )
                )
                break
    return tuple(issues)


def _claim_language_issues(tex_file: Path, repo_root: Path) -> tuple[ManuscriptTextIssue, ...]:
    issues = scan_text(
        tex_file.read_text(encoding="utf-8", errors="ignore"),
        path=Path(_repo_relative(tex_file, repo_root)),
    )
    return tuple(
        ManuscriptTextIssue(
            path=str(issue.path),
            line=issue.line,
            issue_type="forbidden_claim_language",
            rule_id=issue.rule_id,
            text=issue.text,
        )
        for issue in issues
    )


def build_manuscript_figure_audit(
    repo_root: str | Path,
    *,
    manuscript_root: str | Path,
    quarantine_scan_roots: Iterable[str] = DEFAULT_SCAN_ROOTS,
) -> ManuscriptFigureAudit:
    root = Path(repo_root).resolve()
    manuscript = Path(manuscript_root)
    if not manuscript.is_absolute():
        manuscript = root / manuscript
    manuscript = manuscript.resolve()
    scan_roots = tuple(quarantine_scan_roots)
    tex_files = _iter_tex_files(manuscript)
    graphicspaths = _extract_graphicspaths(tex_files)
    quarantine = build_quarantine_report(root, scan_roots=scan_roots)
    quarantined = {record.path: record for record in quarantine.quarantined_figures}
    manifested = {record.path: record for record in quarantine.manifested_figures}

    records: list[ManuscriptFigureRecord] = []
    text_issues: list[ManuscriptTextIssue] = []
    for tex_file in tex_files:
        text_issues.extend(_claim_language_issues(tex_file, root))
        text_issues.extend(_claim_risk_issues(tex_file, root))
        text_issues.extend(_manual_status_issues(tex_file, root))
        for ref in _extract_includegraphics(tex_file, root):
            existing = next(
                (
                    candidate
                    for candidate in _resolve_candidates(
                        ref.include_path,
                        tex_file=tex_file,
                        repo_root=root,
                        manuscript_root=manuscript,
                        graphicspaths=graphicspaths,
                    )
                    if candidate.exists()
                ),
                None,
            )
            if existing is None:
                records.append(
                    ManuscriptFigureRecord(
                        tex_path=ref.tex_path,
                        line=ref.line,
                        include_path=ref.include_path,
                        status="missing",
                        reason="no_candidate_found",
                        resolved_path=None,
                        manifest_path=None,
                    )
                )
                continue
            relative = _repo_relative(existing, root)
            if relative in quarantined:
                q_record = quarantined[relative]
                records.append(
                    ManuscriptFigureRecord(
                        tex_path=ref.tex_path,
                        line=ref.line,
                        include_path=ref.include_path,
                        status="quarantined",
                        reason=q_record.reason,
                        resolved_path=relative,
                        manifest_path=q_record.manifest_path,
                    )
                )
            else:
                m_record = manifested.get(relative)
                records.append(
                    ManuscriptFigureRecord(
                        tex_path=ref.tex_path,
                        line=ref.line,
                        include_path=ref.include_path,
                        status="resolved",
                        reason=(
                            "valid_manifest"
                            if m_record is not None
                            else "resolved_outside_quarantine_scan"
                        ),
                        resolved_path=relative,
                        manifest_path=m_record.manifest_path if m_record else None,
                    )
                )
    return ManuscriptFigureAudit(
        manuscript_root=_repo_relative(manuscript, root),
        scan_roots=scan_roots,
        graphicspaths=graphicspaths,
        figure_records=tuple(records),
        text_issues=tuple(text_issues),
        tex_inputs=tuple(_repo_relative(path, root) for path in tex_files),
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _worktree_state(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return "dirty" if completed.stdout.strip() else "clean"


def _audit_config_hash(audit: ManuscriptFigureAudit) -> str:
    payload = {
        "figure_records": [record.__dict__ for record in audit.figure_records],
        "graphicspaths": audit.graphicspaths,
        "manuscript_root": audit.manuscript_root,
        "scan_roots": audit.scan_roots,
        "text_issues": [issue.__dict__ for issue in audit.text_issues],
        "tex_inputs": audit.tex_inputs,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _input_hash_rows(audit: ManuscriptFigureAudit, repo_root: Path) -> list[str]:
    rows: list[str] = []
    seen: set[str] = set()
    for relative in audit.tex_inputs:
        if relative in seen:
            continue
        path = repo_root / relative
        if path.exists() and path.is_file():
            rows.append(f"- {relative}: `{_file_sha256(path)}`")
            seen.add(relative)
    quarantine = repo_root / "docs" / "generated" / "quarantined_figures.md"
    if quarantine.exists() and "docs/generated/quarantined_figures.md" not in seen:
        rows.append(
            "- docs/generated/quarantined_figures.md: "
            f"`{_file_sha256(quarantine)}`"
        )
    return rows or ["- none: `no_manuscript_inputs`"]


def _metadata_lines(
    audit: ManuscriptFigureAudit,
    *,
    repo_root: Path,
    output_path: Path | str,
    generating_command: str,
) -> list[str]:
    output = Path(output_path)
    output_text = _repo_relative(output, repo_root) if output.is_absolute() else output.as_posix()
    return [
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        f"config_hash: `{_audit_config_hash(audit)}`",
        "input_hashes:",
        *_input_hash_rows(audit, repo_root),
        "caveats:",
        "- Manuscript figure inventory only; this report does not promote figures.",
        "- Missing or quarantined figure references block final manuscript freeze until explained.",
        "- Text audit findings are audit findings, not scientific results.",
        f"generating_command: {generating_command}",
        f"git_commit: {_git_commit(repo_root)}",
        f"worktree_state: {_worktree_state(repo_root)}",
        f"output_path: {output_text}",
    ]


def _figure_rows(records: Iterable[ManuscriptFigureRecord]) -> list[str]:
    rows = [
        "| Source | Include | Status | Resolved path | Manifest | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    count = 0
    for record in records:
        count += 1
        rows.append(
            "| "
            f"`{record.tex_path}:{record.line}` | "
            f"`{record.include_path}` | "
            f"`{record.status}` | "
            f"`{record.resolved_path or 'none'}` | "
            f"`{record.manifest_path or 'none'}` | "
            f"`{record.reason}` |"
        )
    if count == 0:
        rows.append("| none | none | none | none | none | none |")
    return rows


def _issue_rows(issues: Iterable[ManuscriptTextIssue]) -> list[str]:
    rows = [
        "| Source | Type | Rule | Text SHA256 |",
        "| --- | --- | --- | --- |",
    ]
    count = 0
    for issue in issues:
        count += 1
        text_digest = hashlib.sha256(issue.text.encode("utf-8")).hexdigest()
        rows.append(
            "| "
            f"`{issue.path}:{issue.line}` | "
            f"`{issue.issue_type}` | "
            f"`{issue.rule_id}` | "
            f"`{text_digest}` |"
        )
    if count == 0:
        rows.append("| none | none | none | none |")
    return rows


def render_inventory_markdown(
    audit: ManuscriptFigureAudit,
    *,
    repo_root: Path | str,
    output_path: Path | str,
    generating_command: str,
) -> str:
    root = Path(repo_root).resolve()
    lines = [
        "# Manuscript Figure Inventory",
        "",
        *_metadata_lines(
            audit,
            repo_root=root,
            output_path=output_path,
            generating_command=generating_command,
        ),
        "",
        "## Summary",
        "",
        f"- Manuscript root: `{audit.manuscript_root}`",
        f"- TeX inputs scanned: {len(audit.tex_inputs)}",
        f"- Includegraphics refs: {len(audit.figure_records)}",
        f"- Resolved refs: {len(audit.resolved_records)}",
        f"- Quarantined refs: {len(audit.quarantined_records)}",
        f"- Missing refs: {len(audit.missing_records)}",
        f"- Text audit findings: {len(audit.text_issues)}",
        f"- Graphicspaths: {', '.join(f'`{path}`' for path in audit.graphicspaths) or 'none'}",
        "",
        "## Figure References",
        "",
        *_figure_rows(audit.figure_records),
        "",
        "## Text Audit Findings",
        "",
        *_issue_rows(audit.text_issues),
        "",
    ]
    return "\n".join(lines)


def render_missing_references_markdown(
    audit: ManuscriptFigureAudit,
    *,
    repo_root: Path | str,
    output_path: Path | str,
    generating_command: str,
) -> str:
    root = Path(repo_root).resolve()
    lines = [
        "# Missing and Quarantined Manuscript Figure References",
        "",
        *_metadata_lines(
            audit,
            repo_root=root,
            output_path=output_path,
            generating_command=generating_command,
        ),
        "",
        "## Summary",
        "",
        f"- Missing refs: {len(audit.missing_records)}",
        f"- Quarantined refs: {len(audit.quarantined_records)}",
        f"- Forbidden-claim findings: {sum(issue.issue_type == 'forbidden_claim_language' for issue in audit.text_issues)}",
        f"- Claim-risk findings: {sum(issue.issue_type == 'claim_risk_phrase' for issue in audit.text_issues)}",
        f"- Manual/status-number findings: {sum(issue.issue_type == 'manual_status_number' for issue in audit.text_issues)}",
        "",
        "## Missing Figure References",
        "",
        *_figure_rows(audit.missing_records),
        "",
        "## Quarantined Figure References",
        "",
        *_figure_rows(audit.quarantined_records),
        "",
        "## Text Audit Findings",
        "",
        *_issue_rows(audit.text_issues),
        "",
    ]
    return "\n".join(lines)


def _command_from_args(argv: list[str] | None) -> str:
    command_args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", "scripts/audit_manuscript_figures.py", *command_args])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory manuscript includegraphics refs and claim/status audit findings."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        default=DEFAULT_MANUSCRIPT_ROOT,
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        dest="scan_roots",
        help="repo-relative scan root for manifest quarantine state; may repeat",
    )
    parser.add_argument(
        "--output-inventory",
        type=Path,
        default=DEFAULT_INVENTORY_OUTPUT,
    )
    parser.add_argument(
        "--output-missing",
        type=Path,
        default=DEFAULT_MISSING_OUTPUT,
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    manuscript_root = (
        args.manuscript_root
        if args.manuscript_root.is_absolute()
        else repo_root / args.manuscript_root
    )
    scan_roots = tuple(args.scan_roots or DEFAULT_SCAN_ROOTS)
    command = _command_from_args(argv)
    audit = build_manuscript_figure_audit(
        repo_root,
        manuscript_root=manuscript_root,
        quarantine_scan_roots=scan_roots,
    )
    inventory_output = (
        args.output_inventory
        if args.output_inventory.is_absolute()
        else repo_root / args.output_inventory
    )
    missing_output = (
        args.output_missing
        if args.output_missing.is_absolute()
        else repo_root / args.output_missing
    )
    inventory = render_inventory_markdown(
        audit,
        repo_root=repo_root,
        output_path=inventory_output,
        generating_command=command,
    )
    missing = render_missing_references_markdown(
        audit,
        repo_root=repo_root,
        output_path=missing_output,
        generating_command=command,
    )
    summary = (
        "manuscript figure audit: "
        f"includegraphics={len(audit.figure_records)} "
        f"resolved={len(audit.resolved_records)} "
        f"quarantined={len(audit.quarantined_records)} "
        f"missing={len(audit.missing_records)} "
        f"text_findings={len(audit.text_issues)}"
    )
    if args.dry_run:
        print(summary)
        print()
        print(inventory)
        print()
        print(missing)
    else:
        inventory_output.parent.mkdir(parents=True, exist_ok=True)
        missing_output.parent.mkdir(parents=True, exist_ok=True)
        inventory_output.write_text(inventory, encoding="utf-8")
        missing_output.write_text(missing, encoding="utf-8")
        print(f"wrote {_repo_relative(inventory_output, repo_root)}")
        print(f"wrote {_repo_relative(missing_output, repo_root)}")
        print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
