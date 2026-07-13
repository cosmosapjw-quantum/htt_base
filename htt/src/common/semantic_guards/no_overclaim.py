"""Claim-language guards for pre-solver HTT/MIO/BASS work.

The guard is intentionally narrow: it blocks production-style language that is
scientifically forbidden before native low-ell morphology atlas support, while
allowing explicit negative guardrails and archival examples.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re


SCAN_SUFFIXES = frozenset({".md", ".tex", ".rst", ".py", ".yaml", ".yml", ".json"})
EXCLUDED_DIR_NAMES = frozenset(
    {".git", ".mypy_cache", ".pytest_cache", ".venv", "venv", "__pycache__", "build", "dist", "node_modules"}
)
ARCHIVAL_DOC_PARTS = frozenset(
    {
        "audits",
        "design",
        "dossier",
        "packets",
        "ver2_upgrade",
        "ver3",
        "lowell_bianchi",
        "bianchi_design_pack_v5",
    }
)
ARCHIVAL_FILE_PREFIXES = (
    "BASS_PY_HTT_TSC",
    "BASS_PY_HTT_TSC_MIO",
    "INDEPENDENT_TRACKS_",
)
GUARDRAIL_MARKERS = (
    "blocked",
    "cannot",
    "do not",
    "does not",
    "fail",
    "forbidden",
    "guardrail",
    "kill",
    "must not",
    "never",
    "no ",
    "none ",
    "not ",
    "overclaim",
    "reject",
    "risk",
    "without",
    "아님",
    "금지",
    "부족",
    "실패",
    "차단",
)

SOURCE_OBSERVABLE_CONFLATION_PATTERN = re.compile(
    r"\b(?:source\s+(?:is\s+)?adequate|adequate\s+source|source\s+adequacy)"
    r".{0,100}\b(?:automatically\s+implies|implies?|therefore|hence|means|"
    r"proves?|is\s+sufficient\s+for|suffices\s+for|is\s+enough\s+for)"
    r".{0,100}\b(?:observable\s+(?:is\s+)?adequate|"
    r"the\s+observable\s+is\s+adequate|observable\s+adequacy)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ClaimLanguageRule:
    rule_id: str
    pattern: re.Pattern[str]
    message: str


@dataclass(frozen=True)
class ClaimLanguageIssue:
    path: Path
    line: int
    rule_id: str
    severity: str
    message: str
    text: str


RULES: tuple[ClaimLanguageRule, ...] = (
    ClaimLanguageRule(
        rule_id="geometry_detected",
        pattern=re.compile(
            r"\b("
            r"Bianchi geometry (?:is |was |has been )?detected|"  # forbidden-rule literal
            r"global Bianchi anisotropy detected|"  # forbidden-rule literal
            r"Bianchi family (?:is |was |has been )?identified|"  # forbidden-rule literal
            r"identified Bianchi family|"  # forbidden-rule literal
            r"family identified as|"  # forbidden-rule literal
            r"(?:we\s+)?identif(?:y|ies|ied)\s+(?:a\s+|the\s+)?Bianchi family|"
            r"(?:we\s+)?detect(?:s|ed)?\s+(?:a\s+|the\s+)?Bianchi geometry"
            r")\b",
            re.IGNORECASE,
        ),
        message=(
            "Bianchi geometry/family detection claims are blocked before native "
            "morphology atlas gates."
        ),
    ),
    ClaimLanguageRule(
        rule_id="scalar_family_identification",
        pattern=re.compile(
            r"\b("
            r"scalar|D[_\\\-\s]?(?:\\ell|ell|l)|x\s*[,/]\s*Q|"
            r"F\s*[,/]\s*G|low[- ]ell feature|direction coherence"
            r"|directional coherence|BiPoSH norm|largest Bayes factor"
            r").{0,160}\b("
            r"family identification|identif(?:y|ies|ied).{0,40}famil|"
            r"prov(?:e|es|ed).{0,40}Bianchi type|"
            r"certif(?:y|ies|ied).{0,40}Bianchi geometry|"
            r"Bianchi geometry|geometry detected"
            r")",
            re.IGNORECASE,
        ),
        message=(
            "Scalar or low-ell summaries cannot identify Bianchi family or "
            "geometry before native morphology atlas gates."
        ),
    ),
    ClaimLanguageRule(
        rule_id="tsc_teff_full_solver",
        pattern=re.compile(
            r"\b(TSC|Teff|T_eff|\\Teff)\b.{0,140}\b("
            r"full solver|full[- ]polar(?:ization|isation)|"
            r"full E/B polar(?:ization|isation)|full spin[- ]?2|"
            r"full Boltzmann hierarchy solver|closes? the full polar|"
            r"validates BB"
            r")",
            re.IGNORECASE,
        ),
        message=(
            "TSC/Teff may be legacy or trace/source semantics only; full-solver "
            "or full-polarisation claims are forbidden."
        ),
    ),
    ClaimLanguageRule(
        rule_id="mio_truth_or_posterior",  # forbidden-rule id
        pattern=re.compile(
            r"\bMIO\b.{0,140}\b("
            r"truth certificate|certif(?:y|ies|ied).{0,60}truth|"
            r"adjudicat(?:e|es|ed).{0,60}posterior|posterior evidence|"
            r"posterior odds|model posterior|p-values?.{0,80}HTT evidence|"
            r"combined MIO\+HTT score"
            r")",
            re.IGNORECASE,
        ),
        message=(
            "MIO certificates are diagnostic reports, not truth certificates "
            "or posterior/evidence terms."
        ),
    ),
    ClaimLanguageRule(
        rule_id="mio_truth_or_posterior",  # forbidden-rule id
        pattern=re.compile(r"\bcombined\s+MIO\+HTT\s+score\b", re.IGNORECASE),
        message=(
            "MIO diagnostics and HTT evidence must not be collapsed into a "
            "combined score."
        ),
    ),
    ClaimLanguageRule(
        rule_id="external_transfer_as_native",
        pattern=re.compile(
            r"\b(AniCLASS|external transfer)\b.{0,140}\b("
            r"native (?:solver )?(?:result|evidence|validation|validated)|"
            r"validated as native|validates native BASS"
            r")",
            re.IGNORECASE,
        ),
        message="External/AniCLASS transfer outputs cannot be labeled native.",
    ),
    ClaimLanguageRule(
        rule_id="source_observable_conflation",
        pattern=SOURCE_OBSERVABLE_CONFLATION_PATTERN,
        message=(
            "Source adequacy, propagation adequacy, and observable adequacy "
            "must remain separate semantic statuses."
        ),
    ),
)


def scan_text(text: str, *, path: Path = Path("<text>")) -> tuple[ClaimLanguageIssue, ...]:
    """Return claim-language errors found in one text payload."""

    if path.suffix.lower() in {".json"}:
        text = _json_text_values(text)
    issues: list[ClaimLanguageIssue] = []
    lines = text.splitlines()
    in_fence = False
    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            continue
        for rule in RULES:
            match = rule.pattern.search(line)
            if match is None:
                continue
            if _is_guardrail_context(lines, index - 1):
                continue
            if _match_is_in_forbidden_markdown_column(
                lines,
                zero_based_index=index - 1,
                match=match,
                pattern=rule.pattern,
            ):
                continue
            if match:
                issues.append(
                    ClaimLanguageIssue(
                        path=path,
                        line=index,
                        rule_id=rule.rule_id,
                        severity="error",
                        message=rule.message,
                        text=line.strip(),
                    )
                )
    issues.extend(_scan_source_observable_windows(lines, path=path))
    return tuple(issues)


def _scan_source_observable_windows(
    lines: Sequence[str],
    *,
    path: Path,
) -> tuple[ClaimLanguageIssue, ...]:
    """Catch source/observable conflations split across adjacent lines."""

    issues: list[ClaimLanguageIssue] = []
    in_fence = False
    candidate_lines: list[tuple[int, str]] = []
    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            continue
        candidate_lines.append((index, stripped))

    for offset, (line_number, first) in enumerate(candidate_lines[:-1]):
        if _is_guardrail_context(lines, line_number - 1):
            continue
        second_number, second = candidate_lines[offset + 1]
        if _is_guardrail_context(lines, second_number - 1):
            continue
        window = f"{first} {second}"
        if SOURCE_OBSERVABLE_CONFLATION_PATTERN.search(window):
            issues.append(
                ClaimLanguageIssue(
                    path=path,
                    line=line_number,
                    rule_id="source_observable_conflation",
                    severity="error",
                    message=(
                        "Source adequacy, propagation adequacy, and observable "
                        "adequacy must remain separate semantic statuses."
                    ),
                    text=window.strip(),
                )
            )
    return tuple(issues)


def scan_paths(paths: Sequence[Path], *, include_archives: bool = False) -> tuple[ClaimLanguageIssue, ...]:
    """Scan supported text files under paths and return all claim-language errors."""

    issues: list[ClaimLanguageIssue] = []
    for path in iter_text_files(paths, include_archives=include_archives):
        issues.extend(scan_text(path.read_text(encoding="utf-8", errors="ignore"), path=path))
    return tuple(issues)


def iter_text_files(paths: Sequence[Path], *, include_archives: bool = False) -> Iterator[Path]:
    """Yield supported text files, skipping generated/cache/archive paths by default."""

    for root in paths:
        if root.is_file():
            candidates: Iterable[Path] = (root,)
        elif root.is_dir():
            candidates = root.rglob("*")
        else:
            continue
        for path in sorted(candidates):
            if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if not include_archives and _is_archival_path(path):
                continue
            yield path


def render_issues(issues: Sequence[ClaimLanguageIssue]) -> str:
    if not issues:
        return "No forbidden claim language detected."
    lines = ["Forbidden claim language detected:"]
    for issue in issues:
        lines.append(
            f"{issue.rule_id}: {issue.path}:{issue.line}: "
            f"{issue.message} :: {issue.text}"
        )
    return "\n".join(lines)


def issue_to_dict(issue: ClaimLanguageIssue) -> dict[str, object]:
    return {
        "line": issue.line,
        "message": issue.message,
        "path": str(issue.path),
        "rule_id": issue.rule_id,
        "severity": issue.severity,
        "text": issue.text,
    }


def _json_text_values(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text
    return "\n".join(_flatten_json_values(data))


def _flatten_json_values(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key in sorted(value):
            yield from _flatten_json_values(value[key])
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_json_values(item)


def _is_archival_path(path: Path) -> bool:
    parts = set(path.parts)
    if "generated" in parts:
        return True
    if any(path.name.startswith(prefix) for prefix in ARCHIVAL_FILE_PREFIXES):
        return True
    return bool(parts & ARCHIVAL_DOC_PARTS)


def _is_guardrail_context(lines: Sequence[str], zero_based_index: int) -> bool:
    current = lines[zero_based_index].strip()
    if current.startswith("|") and current.endswith("|"):
        # Nearby table headers such as ``Forbidden reading`` describe a column,
        # not every cell in the following rows.  Per-cell handling lives in
        # ``_match_is_in_forbidden_markdown_column`` below.
        window = current.lower()
        return any(marker in window for marker in GUARDRAIL_MARKERS)
    start = max(0, zero_based_index - 2)
    stop = min(len(lines), zero_based_index + 2)
    window = " ".join(lines[start:stop]).lower()
    return any(marker in window for marker in GUARDRAIL_MARKERS)


def _match_is_in_forbidden_markdown_column(
    lines: Sequence[str],
    *,
    zero_based_index: int,
    match: re.Match[str],
    pattern: re.Pattern[str],
) -> bool:
    """Return true only when a match ends in an explicit forbidden-reading cell.

    This keeps explanatory claim matrices scannable without granting a blanket
    exemption to the table row: a forbidden phrase placed in an ``Allowed``
    cell is still reported.
    """

    row = lines[zero_based_index]
    row_spans = tuple(re.finditer(r"(?<=\|)[^|]*(?=\|)", row))
    if not row_spans:
        return False

    header_cells: tuple[str, ...] | None = None
    for header_index in range(zero_based_index, max(-1, zero_based_index - 20), -1):
        candidate = lines[header_index].strip()
        if not candidate.startswith("|") or not candidate.endswith("|"):
            break
        cells = tuple(cell.strip().lower() for cell in candidate.strip("|").split("|"))
        if any("forbidden" in cell and "reading" in cell for cell in cells):
            header_cells = cells
            break
    if header_cells is None or len(header_cells) != len(row_spans):
        return False

    forbidden_indexes = {
        index
        for index, cell in enumerate(header_cells)
        if "forbidden" in cell and "reading" in cell
    }
    first_forbidden_start = min(
        row_spans[index].start() for index in forbidden_indexes
    )
    if pattern.search(row[:first_forbidden_start]):
        # The claim is already complete before the explanatory forbidden cell.
        return False
    match_endpoint = max(match.start(), match.end() - 1)
    return any(
        index in forbidden_indexes and cell.start() <= match_endpoint < cell.end()
        for index, cell in enumerate(row_spans)
    )


__all__ = [
    "ClaimLanguageIssue",
    "ClaimLanguageRule",
    "RULES",
    "iter_text_files",
    "issue_to_dict",
    "render_issues",
    "scan_paths",
    "scan_text",
]
