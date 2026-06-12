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
            r"Bianchi geometry detected|"  # forbidden-rule literal
            r"global Bianchi anisotropy detected|"  # forbidden-rule literal
            r"Bianchi family identified|"  # forbidden-rule literal
            r"identified Bianchi family|"  # forbidden-rule literal
            r"family identified as"  # forbidden-rule literal
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
        if _is_guardrail_context(lines, index - 1):
            continue
        for rule in RULES:
            if rule.pattern.search(line):
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
    start = max(0, zero_based_index - 2)
    stop = min(len(lines), zero_based_index + 2)
    window = " ".join(lines[start:stop]).lower()
    return any(marker in window for marker in GUARDRAIL_MARKERS)


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
