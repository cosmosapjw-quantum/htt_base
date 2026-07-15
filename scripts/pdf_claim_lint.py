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
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.cf4_p0_quarantine import (  # noqa: E402
    BLOCK_RELATIVE_PATH,
    load_block_record,
    validate_active_text,
)


DEFAULT_PDF = Path("docs/generated/manuscript_pdf/htt_base_research_report.pdf")
DEFAULT_MANIFEST = Path(
    "docs/generated/manuscript_pdf/htt_base_research_report.manifest.json"
)
DEFAULT_OUTPUT = Path("docs/generated/pdf_claim_lint_report.md")

FAIL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("decisive evidence", re.compile(r"\bdecisive evidence\b", re.IGNORECASE)),
    ("decisively preferred", re.compile(r"\bdecisively preferred\b", re.IGNORECASE)),
    ("decisively excluded", re.compile(r"\bdecisively excluded\b", re.IGNORECASE)),
    ("odds exceeding", re.compile(r"\bodds exceeding\b", re.IGNORECASE)),
    (
        "combined significance now exceeds",
        re.compile(r"\bcombined significance now exceeds\b", re.IGNORECASE),
    ),
    (
        "property of the data, not a model failure",
        re.compile(
            r"\bproperty of the data,\s*not a model failure\b", re.IGNORECASE
        ),
    ),
    (
        "most conservative choice",
        re.compile(r"\bmost conservative choice\b", re.IGNORECASE),
    ),
    (
        "one-sixteenth of the MES-allowed anisotropy budget",
        re.compile(
            r"\bone[-\s]+sixteenth of the MES[-\s]+allowed anisotropy budget\b",
            re.IGNORECASE,
        ),
    ),
    (
        "data support a tilt-like degree of freedom",
        re.compile(r"\bdata support a tilt-like degree of freedom\b", re.IGNORECASE),
    ),
    (
        "conditional evidence for global tilt",
        re.compile(r"\bconditional evidence for global tilt\b", re.IGNORECASE),
    ),
    ("production solver", re.compile(r"\bproduction solver\b", re.IGNORECASE)),
    ("production pipeline", re.compile(r"\bproduction pipeline\b", re.IGNORECASE)),
    ("production modules", re.compile(r"\bproduction modules\b", re.IGNORECASE)),
    # PR07 audit-repair forbidden overclaims (NT-A1/A3/B3 + A-Wigner + K-reports).
    # "EGS identity" overclaims an EGS theorem ("EGS-type" remains allowed).
    ("EGS identity", re.compile(r"\bEGS identity\b", re.IGNORECASE)),
    ("cosmic-variance floor", re.compile(r"\bcosmic[-\s]variance floor\b", re.IGNORECASE)),
    ("tilt signature", re.compile(r"\btilt signature\b", re.IGNORECASE)),
    ("model-independent anomaly", re.compile(r"\bmodel[-\s]independent anomaly\b", re.IGNORECASE)),
    ("CRLB", re.compile(r"\bCram[eé]r[-\s]Rao\b|\bCRLB\b", re.IGNORECASE)),
    ("minimum-variance estimator", re.compile(r"\bminimum[-\s]variance estimator\b", re.IGNORECASE)),
)
STRICT_FAIL_PATTERN_NAMES = {
    "odds exceeding",
    "combined significance now exceeds",
    "property of the data, not a model failure",
    "most conservative choice",
    "one-sixteenth of the MES-allowed anisotropy budget",
    "data support a tilt-like degree of freedom",
    "conditional evidence for global tilt",
    # PR07 overclaims that must never appear, even in a "legacy"/conditioned context.
    "EGS identity",
    "cosmic-variance floor",
    "tilt signature",
    "model-independent anomaly",
    "CRLB",
}
LNB_NUMERIC_PATTERN = re.compile(
    r"\bln\s*B\|?(?:\s*(?:=|≈|>|<|∈|\\in)|[A-Za-z_]*\s*(?:=|≈))",
    re.IGNORECASE,
)
LNB_HIGH_STRENGTH_PATTERN = re.compile(
    r"\b("
    r"global\s+tilt|"
    r"detection|detections|detected|detects|"
    r"decisive|decisively|"
    r"evidence|"
    r"odds|"
    r"support|supports|supported|"
    r"survive|survives|survived|"
    r"establish|establishes|established"
    r")\b",
    re.IGNORECASE,
)
LNB_SAFE_DIAGNOSTIC_MARKERS = (
    "diagnostic preference",
    "diagnostic-preference",
    "conditional diagnostic",
    "direction-marginalized",
    "direction-marginalised",
    "model-comparison summary",
    "not established",
    "jeffreys scale",
    "qualitative interpretation",
    "not worth more than a bare mention",
)
LNB_DOWNCLAIM_MARKERS = (
    "premise-conditioned amplitude fit",
    "admitted-amplitude",
    "admitted amplitude",
    "admitted dipole-amplitude premise",
    "configured likelihood-ratio",
    "configured likelihood ratio",
    "legacy transfer-conditional ranking",
    "transfer-conditional ranking",
    "legacy high-support diagnostic bin",
    "legacy high-support rejection bin",
    "historical high-support threshold",
    "conditioned legacy run",
    "not a source-identification claim",
    "not source-identification",
    "source origin is not established",
    "source-identification is blocked",
    "not support for anisotropic spatial geometry",
    "not a geometry or family claim",
    "not native-transfer evidence",
    "not an independent discovery",
    "not promoted here",
    "conditional on the matter-dipole premise",
    "no positive support",
    "prior- and error-budget-sensitive",
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


def verify_pdf_manifest_pair(
    pdf_path: Path,
    manifest_path: Path,
    *,
    manifest_member_path: str | None = None,
) -> str:
    """Return the PDF digest only when the companion manifest binds exact bytes."""

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse PDF companion manifest {manifest_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("PDF companion manifest must be a JSON object")
    expected = payload.get("artifact_sha256")
    if manifest_member_path is not None:
        rows = payload.get("archive_entries")
        if not isinstance(rows, list):
            raise ValueError("PDF companion manifest lacks archive_entries")
        matches = [
            row
            for row in rows
            if isinstance(row, dict) and row.get("source_path") == manifest_member_path
        ]
        if len(matches) != 1:
            raise ValueError(
                f"PDF companion manifest must bind exactly one {manifest_member_path!r} row"
            )
        expected = matches[0].get("sha256")
    actual = _sha256_file(pdf_path)
    if expected != actual:
        raise ValueError(
            f"PDF companion manifest digest mismatch: expected {expected or 'missing'}, got {actual}"
        )
    return actual


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


def _has_context_marker(text: str) -> bool:
    lowered = _normalise_context(text).lower()
    return any(marker in lowered for marker in CONTEXT_MARKERS)


def _context(text: str, start: int, end: int, *, radius: int = 180) -> str:
    return _normalise_context(text[max(0, start - radius) : min(len(text), end + radius)])


def _lnb_high_strength_claim_context(context: str) -> bool:
    lowered = context.lower()
    has_high_strength = LNB_HIGH_STRENGTH_PATTERN.search(context) is not None
    if not has_high_strength:
        return False
    if "detection" in lowered or "detected" in lowered:
        return True
    if "jeffreys scale" in lowered or "qualitative interpretation" in lowered:
        return False
    if any(marker in lowered for marker in LNB_DOWNCLAIM_MARKERS):
        return False
    if "detection" not in lowered and any(
        marker in lowered for marker in LNB_SAFE_DIAGNOSTIC_MARKERS
    ):
        return False
    return True


def _family_id_is_negative_context(text: str, start: int, end: int) -> bool:
    window = _context(text, start, end, radius=140).lower()
    return any(marker in window for marker in NEGATIVE_FAMILY_MARKERS)


def lint_pages(pages: Iterable[str]) -> list[PdfClaimFinding]:
    findings: list[PdfClaimFinding] = []
    for page_number, page_text in enumerate(pages, start=1):
        for issue in validate_active_text(
            f"pdf_text/page_{page_number:04d}.txt",
            page_text,
            repo_root=REPO_ROOT,
        ):
            findings.append(
                PdfClaimFinding(
                    severity="fail",
                    page=page_number,
                    pattern=f"CF4 P0 quarantine: {issue.signature_id or issue.code}",
                    context=issue.detail,
                )
            )
        for pattern_name, pattern in FAIL_PATTERNS:
            for match in pattern.finditer(page_text):
                context = _context(page_text, match.start(), match.end())
                if (
                    pattern_name not in STRICT_FAIL_PATTERN_NAMES
                    and _has_context_marker(context)
                ):
                    continue
                findings.append(
                    PdfClaimFinding(
                        severity="fail",
                        page=page_number,
                        pattern=pattern_name,
                        context=context,
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
            context = _context(page_text, match.start(), match.end(), radius=160)
            if _lnb_high_strength_claim_context(context):
                findings.append(
                    PdfClaimFinding(
                        severity="fail",
                        page=page_number,
                        pattern="lnB numeric with high-strength claim language",
                        context=context,
                    )
                )
                continue
            findings.append(
                PdfClaimFinding(
                    severity="warn",
                    page=page_number,
                    pattern="lnB numeric or threshold",
                    context=context,
                )
            )
    return findings


def build_report_payload(
    *,
    repo_root: Path,
    pdf_path: Path,
    manifest_path: Path | None,
    output_path: Path,
    generating_command: str,
) -> dict[str, object]:
    absolute_pdf = pdf_path if pdf_path.is_absolute() else repo_root / pdf_path
    absolute_manifest = (
        None
        if manifest_path is None
        else manifest_path
        if manifest_path.is_absolute()
        else repo_root / manifest_path
    )
    config_hash = "sha256:" + hashlib.sha256(
        json.dumps(
            {
                "fail_patterns": [name for name, _ in FAIL_PATTERNS],
                "lnb_numeric_pattern": LNB_NUMERIC_PATTERN.pattern,
                "lnb_high_strength_pattern": LNB_HIGH_STRENGTH_PATTERN.pattern,
                "lnb_safe_diagnostic_markers": LNB_SAFE_DIAGNOSTIC_MARKERS,
                "context_markers": CONTEXT_MARKERS,
                "missing_current_pdf_policy": "blocked_by_cf4_p0_quarantine",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if not absolute_pdf.is_file():
        if absolute_manifest is not None and absolute_manifest.exists():
            raise ValueError(
                "PDF companion manifest exists while the bound PDF is missing: "
                f"{_repo_relative(absolute_manifest, repo_root)}"
            )
        block = load_block_record(repo_root)
        return {
            "owner": "COMMON",
            "implementation_scope": "common",
            "claim_tier": "blocked",
            "transfer_source": "none",
            "sky_support_status": "not_applicable_no_current_pdf",
            "null_mock_status": "not_applicable_no_current_pdf",
            "artifact_path": _repo_relative(output_path, repo_root),
            "status": "BLOCKED_NO_CURRENT_PDF",
            "claim_lint_passed": False,
            "pdf_path": _repo_relative(absolute_pdf, repo_root),
            "pdf_sha256": None,
            "pdf_manifest_path": (
                _repo_relative(absolute_manifest, repo_root)
                if absolute_manifest is not None
                else None
            ),
            "quarantine_block_path": BLOCK_RELATIVE_PATH.as_posix(),
            "quarantine_block_sha256": "sha256:" + block.sha256,
            "config_hash": config_hash,
            "input_hashes": [
                f"{BLOCK_RELATIVE_PATH.as_posix()}:sha256:{block.sha256}"
            ],
            "generating_command": generating_command,
            "git_commit_or_worktree_state": _current_git_state(repo_root),
            "page_count": 0,
            "failed_findings": 0,
            "warning_findings": 0,
            "findings": [],
            "open_findings": [
                str(row["finding_id"]) for row in block.findings
            ],
            "caveats": [
                "No current manuscript PDF exists at the active path, so no PDF prose surface was scanned.",
                "The prior PDF and lint report are immutable historical evidence under legacy/cf4_p0 with public_use false.",
                "This blocked report is not a passing PDF claim lint and cannot satisfy a publication gate.",
                "The canonical CF4 P0 block record is authoritative and authorizes no replacement value.",
            ],
        }
    if absolute_manifest is None or not absolute_manifest.is_file():
        raise ValueError("a current PDF requires an existing companion manifest")
    pdf_digest = verify_pdf_manifest_pair(absolute_pdf, absolute_manifest)
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
        "status": "PASS" if not failed else "FAIL",
        "claim_lint_passed": not failed,
        "pdf_path": _repo_relative(absolute_pdf, repo_root),
        "pdf_sha256": pdf_digest,
        "pdf_manifest_path": _repo_relative(absolute_manifest, repo_root),
        "quarantine_block_path": None,
        "quarantine_block_sha256": None,
        "config_hash": config_hash,
        "input_hashes": [
            f"{_repo_relative(absolute_pdf, repo_root)}:{pdf_digest}",
            f"{_repo_relative(absolute_manifest, repo_root)}:{_sha256_file(absolute_manifest)}",
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": _current_git_state(repo_root),
        "page_count": len([page for page in pages if page.strip()]),
        "failed_findings": len(failed),
        "warning_findings": len(warned),
        "findings": [finding.__dict__ for finding in findings],
        "open_findings": [],
        "caveats": [
            "PDF text extraction is used as a final prose-surface lint.",
            "lnB numeric mentions are warnings unless paired with high-strength claim language.",
            "Direction-marginalized diagnostic-preference language is allowed as a warning-only technical Bayes-factor mention.",
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
        f"status: {payload['status']}",
        f"claim_lint_passed: {str(payload['claim_lint_passed']).lower()}",
        "",
        "## Summary",
        "",
        f"- PDF: `{payload['pdf_path']}`",
        f"- PDF SHA256: `{payload['pdf_sha256']}`",
        f"- PDF manifest: `{payload['pdf_manifest_path']}`",
        f"- Quarantine block: `{payload['quarantine_block_path']}`",
        f"- Quarantine block SHA256: `{payload['quarantine_block_sha256']}`",
        f"- Pages scanned: `{payload['page_count']}`",
        f"- Failed findings: `{payload['failed_findings']}`",
        f"- Warning findings: `{payload['warning_findings']}`",
        f"- Open findings: `{', '.join(payload['open_findings'])}`",
        "",
        "## Findings",
        "",
    ]
    if payload["status"] == "BLOCKED_NO_CURRENT_PDF":
        lines.append(
            "No current PDF was linted. This surface is blocked by the canonical CF4 P0 quarantine record."
        )
    elif not findings:
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
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
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
        manifest_path=args.manifest,
        output_path=output_path,
        generating_command=_command_from_args(argv),
    )
    if args.check:
        existing_git_state = _existing_report_git_state(output_path)
        if existing_git_state:
            payload["git_commit_or_worktree_state"] = existing_git_state
    report = render_report(payload)
    claim_lint_passed = (
        payload.get("status") == "PASS"
        and payload.get("claim_lint_passed") is True
        and int(payload["failed_findings"]) == 0
    )
    if args.check:
        if not output_path.exists():
            print("missing PDF claim lint report")
            return 1
        if output_path.read_text(encoding="utf-8") != report:
            print("stale PDF claim lint report")
            return 1
        if not claim_lint_passed:
            print(
                "PDF claim lint did not pass: "
                f"status={payload.get('status')} "
                f"failed_findings={payload['failed_findings']}"
            )
            return 1
        print(f"up-to-date {output_path}")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"wrote {output_path}")
    if not claim_lint_passed:
        print(
            "PDF claim lint did not pass: "
            f"status={payload.get('status')} "
            f"failed_findings={payload['failed_findings']}"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
