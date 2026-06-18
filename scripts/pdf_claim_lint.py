#!/usr/bin/env python3
"""Lint compiled manuscript PDFs for claim-strength leakage.

This checker operates on the final PDF text, not only on TeX sources. It does
not ban legacy or transfer-conditional evidence discussion outright; it requires
high-strength phrases to appear inside an explicit legacy/conditioned context.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = Path("docs/generated/manuscript_pdf/htt_base_research_report.pdf")
DEFAULT_OUTPUT = Path("docs/generated/pdf_claim_lint_report.md")

FAIL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("decisive evidence", re.compile(r"\bdecisive evidence\b", re.IGNORECASE)),
    ("decisively preferred", re.compile(r"\bdecisively preferred\b", re.IGNORECASE)),
    ("decisively excluded", re.compile(r"\bdecisively excluded\b", re.IGNORECASE)),
    ("production solver", re.compile(r"\bproduction solver\b", re.IGNORECASE)),
    ("production pipeline", re.compile(r"\bproduction pipeline\b", re.IGNORECASE)),
    ("production modules", re.compile(r"\bproduction modules\b", re.IGNORECASE)),
)
LNB_NUMERIC_PATTERN = re.compile(
    r"\bln\s*B(?:\s*(?:=|≈|>|<|∈|\\in)|[A-Za-z_]*\s*(?:=|≈))",
    re.IGNORECASE,
)
FAMILY_ID_PATTERN = re.compile(r"\bBianchi family identification\b", re.IGNORECASE)
CONTEXT_MARKERS = (
    "legacy transfer-conditional",
    "transfer-conditional legacy",
    "conditioned legacy",
    "legacy conditioned",
    "conditional evidence",
    "not a current public claim",
    "appendix h",
)
NEGATIVE_FAMILY_MARKERS = (
    "not established",
    "blocked",
    "absent",
    "no family",
)


@dataclass(frozen=True)
class PdfClaimFinding:
    severity: str
    page: int
    pattern: str
    context: str


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _current_git_state(repo_root: Path) -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return f"{commit}+dirty" if dirty else commit


def _extract_pdf_pages(pdf_path: Path) -> list[str]:
    try:
        text = subprocess.check_output(
            ["pdftotext", str(pdf_path), "-"],
            text=True,
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext is required for PDF claim lint") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"pdftotext failed for {pdf_path}") from exc
    return text.split("\f")


def _normalise_context(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _has_context_marker(page_text: str) -> bool:
    lowered = _normalise_context(page_text).lower()
    return any(marker in lowered for marker in CONTEXT_MARKERS)


def _context(text: str, start: int, end: int, *, radius: int = 180) -> str:
    return _normalise_context(text[max(0, start - radius) : min(len(text), end + radius)])


def _family_id_is_negative_context(text: str, start: int, end: int) -> bool:
    window = _context(text, start, end, radius=140).lower()
    return any(marker in window for marker in NEGATIVE_FAMILY_MARKERS)


def lint_pages(pages: Iterable[str]) -> list[PdfClaimFinding]:
    findings: list[PdfClaimFinding] = []
    for page_number, page_text in enumerate(pages, start=1):
        marked_context = _has_context_marker(page_text)
        for pattern_name, pattern in FAIL_PATTERNS:
            for match in pattern.finditer(page_text):
                if marked_context:
                    continue
                findings.append(
                    PdfClaimFinding(
                        severity="fail",
                        page=page_number,
                        pattern=pattern_name,
                        context=_context(page_text, match.start(), match.end()),
                    )
                )
        for match in FAMILY_ID_PATTERN.finditer(page_text):
            if _family_id_is_negative_context(page_text, match.start(), match.end()):
                continue
            findings.append(
                PdfClaimFinding(
                    severity="fail",
                    page=page_number,
                    pattern="Bianchi family identification",
                    context=_context(page_text, match.start(), match.end()),
                )
            )
        for match in LNB_NUMERIC_PATTERN.finditer(page_text):
            if marked_context:
                continue
            findings.append(
                PdfClaimFinding(
                    severity="warn",
                    page=page_number,
                    pattern="lnB numeric or threshold",
                    context=_context(page_text, match.start(), match.end(), radius=120),
                )
            )
    return findings


def build_report_payload(
    *,
    repo_root: Path,
    pdf_path: Path,
    output_path: Path,
    generating_command: str,
) -> dict[str, object]:
    absolute_pdf = pdf_path if pdf_path.is_absolute() else repo_root / pdf_path
    pages = _extract_pdf_pages(absolute_pdf)
    findings = lint_pages(pages)
    failed = [finding for finding in findings if finding.severity == "fail"]
    warned = [finding for finding in findings if finding.severity == "warn"]
    return {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "artifact_path": _repo_relative(output_path, repo_root),
        "pdf_path": _repo_relative(absolute_pdf, repo_root),
        "pdf_sha256": _sha256_file(absolute_pdf),
        "config_hash": "sha256:" + hashlib.sha256(
            json.dumps(
                {
                    "fail_patterns": [name for name, _ in FAIL_PATTERNS],
                    "lnb_numeric_pattern": LNB_NUMERIC_PATTERN.pattern,
                    "context_markers": CONTEXT_MARKERS,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "input_hashes": [
            f"{_repo_relative(absolute_pdf, repo_root)}:{_sha256_file(absolute_pdf)}"
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": _current_git_state(repo_root),
        "page_count": len([page for page in pages if page.strip()]),
        "failed_findings": len(failed),
        "warning_findings": len(warned),
        "findings": [finding.__dict__ for finding in findings],
        "caveats": [
            "PDF text extraction is used as a final prose-surface lint.",
            "lnB numeric mentions are warnings unless paired with high-strength claim language.",
            "Legacy or conditioned pages must carry explicit context markers.",
        ],
    }


def render_report(payload: dict[str, object]) -> str:
    findings = payload["findings"]
    assert isinstance(findings, list)
    lines = [
        "# PDF Claim Lint Report",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"transfer_source: {payload['transfer_source']}",
        f"sky_support_status: {payload['sky_support_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        f"config_hash: `{payload['config_hash']}`",
        "input_hashes:",
        *[f"- {item}" for item in payload["input_hashes"]],
        "caveats:",
        *[f"- {item}" for item in payload["caveats"]],
        f"generating_command: {payload['generating_command']}",
        f"git_commit_or_worktree_state: {payload['git_commit_or_worktree_state']}",
        f"artifact_path: {payload['artifact_path']}",
        "",
        "## Summary",
        "",
        f"- PDF: `{payload['pdf_path']}`",
        f"- PDF SHA256: `{payload['pdf_sha256']}`",
        f"- Pages scanned: `{payload['page_count']}`",
        f"- Failed findings: `{payload['failed_findings']}`",
        f"- Warning findings: `{payload['warning_findings']}`",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("No PDF claim-lint findings.")
    else:
        lines.extend(
            [
                "| Severity | Page | Pattern | Context |",
                "| --- | ---: | --- | --- |",
            ]
        )
        for finding in findings:
            assert isinstance(finding, dict)
            context = str(finding["context"]).replace("|", "\\|")
            lines.append(
                f"| `{finding['severity']}` | {finding['page']} | "
                f"`{finding['pattern']}` | {context} |"
            )
    lines.append("")
    return "\n".join(lines)


def _existing_report_git_state(output_path: Path) -> str | None:
    if not output_path.exists():
        return None
    for line in output_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("git_commit_or_worktree_state: "):
            return line.split(": ", 1)[1].strip()
    return None


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = list(sys.argv[1:] if argv is None else argv)
    args = [arg for arg in args if arg != "--check"]
    return " ".join(["python", "scripts/pdf_claim_lint.py", *args]).strip()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    output_path = args.output if args.output.is_absolute() else repo_root / args.output
    payload = build_report_payload(
        repo_root=repo_root,
        pdf_path=args.pdf,
        output_path=output_path,
        generating_command=_command_from_args(argv),
    )
    if args.check:
        existing_git_state = _existing_report_git_state(output_path)
        if existing_git_state:
            payload["git_commit_or_worktree_state"] = existing_git_state
    report = render_report(payload)
    if args.check:
        if not output_path.exists():
            print("missing PDF claim lint report")
            return 1
        if output_path.read_text(encoding="utf-8") != report:
            print("stale PDF claim lint report")
            return 1
        if int(payload["failed_findings"]) > 0:
            print(f"PDF claim lint failed: {payload['failed_findings']} findings")
            return 1
        print(f"up-to-date {output_path}")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"wrote {output_path}")
    if int(payload["failed_findings"]) > 0:
        print(f"PDF claim lint failed: {payload['failed_findings']} findings")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
