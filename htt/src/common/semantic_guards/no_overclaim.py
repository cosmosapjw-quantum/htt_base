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
YAML_GUARDRAIL_SECTION_KEYS = frozenset(
    {
        "forbidden_output_language",
        "forbidden_uses",
        "mutation_registry",
        "preregistered_falsifiers",
    }
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
            r"Bianchi geometr(?:y|ies)\b[^.!?\n]{0,96}\bdetect(?:s|ed)?|"
            r"global Bianchi anisotropy detected|"  # forbidden-rule literal
            r"Bianchi famil(?:y|ies)\b[^.!?\n]{0,96}\bidentif(?:y|ies|ied)|"
            r"identified Bianchi family|"  # forbidden-rule literal
            r"family identified as|"  # forbidden-rule literal
            r"(?:we|(?:(?:the|this|that|our|your|their|a|an)\s+)?"
            r"analys(?:is|es))\b[^.!?\n]{0,96}\b"
            r"identif(?:y|ies|ied)\s+"
            r"(?:(?:a|an|the|this|that|those|these|both|several)\s+)?"
            r"Bianchi famil(?:y|ies)|"
            r"(?:we|(?:(?:the|this|that|our|your|their|a|an)\s+)?"
            r"analys(?:is|es))\b[^.!?\n]{0,96}\b"
            r"identif(?:y|ies|ied)\s+"
            r"(?:(?:the|this|that|those|these|both|several)\s+)?"
            r"famil(?:y|ies)\s+as\s+Bianchi"
            r"(?:\s+(?:type\s+)?[A-Za-z0-9_-]+)?|"
            r"(?:the\s+)?famil(?:y|ies)\s+"
            r"(?:(?:is|are|was|were|has|have|been|being|conclusively|"
            r"directly|uniquely|definitively)\s+){0,5}"
            r"identified\s+as\s+Bianchi(?:\s+(?:type\s+)?[A-Za-z0-9_-]+)?|"
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
            r"identification\s+of\s+"
            r"(?:(?:a|an|the|those|these|both|several)\s+)?"
            r"Bianchi famil(?:y|ies)|"
            r"prov(?:e|es|ed).{0,40}Bianchi type|"
            r"certif(?:y|ies|ied).{0,40}Bianchi geometry|"
            r"Bianchi geometry|geometry detected"
            r")|"
            r"(?:Bianchi family identification|identification\s+of\s+"
            r"(?:(?:a|an|the|those|these|both|several)\s+)?"
            r"Bianchi famil(?:y|ies))[^.!?\n]{0,160}\b"
            r"(?:follows?|results?)\s+from\s+(?:the\s+)?("
            r"scalar|D[_\\\-\s]?(?:\\ell|ell|l)|x\s*[,/]\s*Q|"
            r"F\s*[,/]\s*G|low[- ]ell feature|direction coherence|"
            r"directional coherence|BiPoSH norm|largest Bayes factor"
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
        rule_id="legacy_curl_physics_promotion",
        pattern=re.compile(
            r"(?:"
            r"\b(?:0\.0089|(?:WF\s+)?curl(?:[- ]?div(?:ergence)?|\s+diagnostic|\s+ratio)?)\b"
            r".{0,180}\b(?:evidence|support(?:s|ed)?|prov(?:e|es|ed)|"
            r"establish(?:es|ed)?|detect(?:s|ed)?)\b.{0,120}\b(?:"
            r"physical\s+(?:cosmic\s+)?vorticity|cosmic\s+vorticity|"
            r"cosmic\s+potential\s+flow|potential\s+flow\s+in\s+the\s+Universe)\b"
            r"|"
            r"\b(?:physical\s+(?:cosmic\s+)?vorticity|cosmic\s+vorticity|"
            r"cosmic\s+potential\s+flow|potential\s+flow\s+in\s+the\s+Universe)\b"
            r".{0,120}\b(?:evidence|support(?:s|ed)?|prov(?:e|es|ed)|"
            r"establish(?:es|ed)?|detect(?:s|ed)?)\b.{0,180}\b(?:"
            r"0\.0089|(?:WF\s+)?curl(?:[- ]?div(?:ergence)?|\s+diagnostic|\s+ratio)?)\b"
            r")",
            re.IGNORECASE,
        ),
        message=(
            "The legacy CF4 curl diagnostic is a stencil self-consistency "
            "check, not evidence for physical vorticity or cosmic potential flow."
        ),
    ),
    ClaimLanguageRule(
        rule_id="retired_p0_rescue",
        pattern=re.compile(
            r"\b(?:PR[- ]?291|CF4|(?:this|the|new)\s+(?:analysis|result))\b"
            r".{0,120}\b(?:rescu(?:e|es|ed)|reviv(?:e|es|ed)|"
            r"restor(?:e|es|ed)|rehabilitat(?:e|es|ed))\b.{0,120}\b"
            r"(?:retired\s+)?P0(?:\s+velocity[- ]shape)?(?:\s+headline)?\b|"
            r"\b(?:retired\s+)?P0(?:\s+velocity[- ]shape)?(?:\s+headline)?\b"
            r".{0,120}\b(?:rescu(?:e|es|ed)|reviv(?:e|es|ed)|"
            r"restor(?:e|es|ed)|rehabilitat(?:e|es|ed))\b",
            re.IGNORECASE,
        ),
        message="PR-291 cannot rescue the retired P0 or velocity-shape headline.",
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
    fence_character: str | None = None
    fence_length = 0
    fence_quote_depth: int | None = None
    for index, line in enumerate(lines, 1):
        stripped = line.strip()
        quote_depth = 0
        while stripped.startswith(">"):
            quote_depth += 1
            stripped = stripped[1:].lstrip()
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if in_fence and quote_depth != fence_quote_depth:
            in_fence = False
            fence_character = None
            fence_length = 0
            fence_quote_depth = None
        elif in_fence:
            if (
                fence_match is not None
                and fence_character is not None
                and fence_match.group(1)[0] == fence_character
                and len(fence_match.group(1)) >= fence_length
                and not stripped[len(fence_match.group(1)) :].strip()
            ):
                in_fence = False
                fence_character = None
                fence_length = 0
                fence_quote_depth = None
            continue
        if fence_match is not None:
            marker = fence_match.group(1)
            in_fence = True
            fence_character = marker[0]
            fence_length = len(marker)
            fence_quote_depth = quote_depth
            continue
        if not stripped:
            continue
        for rule in RULES:
            match = rule.pattern.search(line)
            if match is None:
                continue
            if _match_is_in_forbidden_markdown_column(
                lines,
                zero_based_index=index - 1,
                match=match,
                pattern=rule.pattern,
            ):
                continue
            if _is_guardrail_context(
                lines,
                index - 1,
                path=path,
                matched_text=line,
                match=match,
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
    issues.extend(_scan_multiline_claim_windows(lines, path=path))
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
        second_number, second = candidate_lines[offset + 1]
        window = f"{first} {second}"
        match = SOURCE_OBSERVABLE_CONFLATION_PATTERN.search(window)
        if match is not None and not (
            _structured_guardrail_context(lines, line_number - 1, path=path)
            or _structured_guardrail_context(lines, second_number - 1, path=path)
            or _match_sentence_has_guardrail(window, match)
        ):
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


def _scan_multiline_claim_windows(
    lines: Sequence[str],
    *,
    path: Path,
) -> tuple[ClaimLanguageIssue, ...]:
    """Catch registered promotion claims split by ordinary prose wrapping.

    The primary scanner remains line based for stable locations and narrow
    guardrail exemptions.  Publication prose, however, can wrap one semantic
    sentence over several source lines.  Fold only contiguous prose blocks,
    stopping at blank lines, fenced-code containers, genuine quote-depth
    changes, and new Markdown structural items.  CommonMark lazy blockquote
    continuations inherit the active quote depth even when the repeated ``>``
    marker is omitted.  Fence state is scoped to the quote container that
    opened it so an unterminated quoted example cannot mask later prose.
    Report only matches that genuinely span more than one source line.
    """

    rules = tuple(
        item
        for item in RULES
        if item.rule_id
        in {
            "geometry_detected",
            "scalar_family_identification",
            "legacy_curl_physics_promotion",
        }
    )
    issues: list[ClaimLanguageIssue] = []
    block: list[tuple[int, str]] = []
    in_fence = False
    fence_character: str | None = None
    fence_length = 0
    fence_quote_depth: int | None = None
    block_quote_depth: int | None = None

    def flush() -> None:
        nonlocal block_quote_depth
        if len(block) < 2:
            block.clear()
            block_quote_depth = None
            return

        joined_parts: list[str] = []
        spans: list[tuple[int, int, int]] = []
        cursor = 0
        for line_index, value in block:
            if joined_parts:
                cursor += 1
            start = cursor
            joined_parts.append(value)
            cursor += len(value)
            spans.append((start, cursor, line_index))
        joined = " ".join(joined_parts)

        for rule in rules:
            for match in rule.pattern.finditer(joined):
                touched = [
                    line_index
                    for start, stop, line_index in spans
                    if start < match.end() and stop > match.start()
                ]
                if len(touched) < 2:
                    continue
                if any(
                    _structured_guardrail_context(lines, line_index, path=path)
                    for line_index in touched
                ) or _match_sentence_has_guardrail(joined, match):
                    continue
                issues.append(
                    ClaimLanguageIssue(
                        path=path,
                        line=touched[0] + 1,
                        rule_id=rule.rule_id,
                        severity="error",
                        message=rule.message,
                        text=match.group(0).strip(),
                    )
                )
        block.clear()
        block_quote_depth = None

    for line_index, line in enumerate(lines):
        stripped = line.strip()
        quote_depth = 0
        while stripped.startswith(">"):
            quote_depth += 1
            stripped = stripped[1:].lstrip()

        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if in_fence and quote_depth != fence_quote_depth:
            # A fence belongs to the Markdown container that opened it.  A
            # quote-depth transition ends that container even when the source
            # omitted an explicit closing marker; process this line as prose
            # in its new container instead of letting stale fence state hide it.
            in_fence = False
            fence_character = None
            fence_length = 0
            fence_quote_depth = None
        elif in_fence:
            if (
                fence_match is not None
                and fence_character is not None
                and fence_match.group(1)[0] == fence_character
                and len(fence_match.group(1)) >= fence_length
                and not stripped[len(fence_match.group(1)) :].strip()
            ):
                in_fence = False
                fence_character = None
                fence_length = 0
                fence_quote_depth = None
            continue

        if fence_match is not None:
            flush()
            marker = fence_match.group(1)
            in_fence = True
            fence_character = marker[0]
            fence_length = len(marker)
            fence_quote_depth = quote_depth
            continue
        if not stripped:
            flush()
            continue

        is_structural = re.match(
            r"^(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|\|)", stripped
        ) is not None
        effective_quote_depth = quote_depth
        if (
            block
            and quote_depth == 0
            and block_quote_depth is not None
            and block_quote_depth > 0
            and not is_structural
        ):
            # CommonMark permits an ordinary paragraph continuation inside a
            # block quote to omit the repeated marker.  Retain the established
            # container depth until a real block boundary appears.
            effective_quote_depth = block_quote_depth

        if block and effective_quote_depth != block_quote_depth:
            flush()
        if block and is_structural:
            flush()
        if not block:
            block_quote_depth = effective_quote_depth
        block.append((line_index, stripped))
    flush()
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


def _is_guardrail_context(
    lines: Sequence[str],
    zero_based_index: int,
    *,
    path: Path,
    matched_text: str,
    match: re.Match[str],
) -> bool:
    if _structured_guardrail_context(lines, zero_based_index, path=path):
        return True
    return _match_sentence_has_guardrail(matched_text, match)


def _structured_guardrail_context(
    lines: Sequence[str], zero_based_index: int, *, path: Path
) -> bool:
    if path.suffix.lower() in {".yaml", ".yml"} and _is_yaml_guardrail_section(
        lines, zero_based_index
    ):
        return True
    current = lines[zero_based_index].strip()
    if re.match(r"^(?:[-*+]\s|\d+[.)]\s)", current) is None:
        return False
    for candidate in reversed(lines[:zero_based_index]):
        stripped = candidate.strip()
        if not stripped:
            break
        if re.match(r"^(?:[-*+]\s|\d+[.)]\s)", stripped):
            continue
        return re.fullmatch(r"Forbidden examples\s*:\s*", stripped, re.IGNORECASE) is not None
    return False


def _match_sentence_has_guardrail(text: str, match: re.Match[str]) -> bool:
    """Recognize only negation semantically scoped to the matched claim."""

    start = 0
    for boundary in re.finditer(r"[.!?](?:[\"')\]]*)\s+", text[: match.start()]):
        start = boundary.end()
    end_match = re.search(r"[.!?](?:[\"')\]]*)\s+", text[match.end() :])
    end = match.end() + end_match.end() if end_match is not None else len(text)
    sentence = text[start:end].lower()
    relative_start = match.start() - start
    relative_end = match.end() - start
    matched_claim = sentence[relative_start:relative_end]
    if re.search(
        r"\b(?:is|are|was|were|has|have)\s+not\s+"
        r"(?:(?:conclusively|directly|uniquely|definitively)\s+){0,3}"
        r"(?:detected|identified|supported|established|proved|certified|"
        r"validated|evidence\s+for|a\s+truth\s+certificate|"
        r"truth\s+certificates?|a\s+native\s+solver\s+result|"
        r"native\s+solver\s+results?)\b",
        matched_claim,
    ):
        return True
    if re.search(
        r"\b(?:do|does|did|can|could|may|must|should|will|would)\s+not\s+"
        r"(?:detect|identify|support|establish|prove|certify|validate|"
        r"rescue|imply|promote|claim|follow|result)\b",
        matched_claim,
    ):
        return True
    if re.search(
        r"\b(?:never|cannot)\s+(?:detect|identify|support|establish|prove|"
        r"certify|validate|rescue|imply|promote|claim)\b",
        matched_claim,
    ):
        return True
    if re.search(
        r"\bnot\s+as\s+(?:a\s+|an\s+)?(?:measurement|evidence|proof|"
        r"detection|identification)\s+(?:of|for)\b",
        matched_claim,
    ):
        return True

    prefix = sentence[:relative_start].rstrip()
    if re.search(
        r"(?:\b(?:do|does|did|must|should|can|could|may)\s+not\s+"
        r"(?:claim|assert|conclude|infer|report|say)(?:\s+that)?|"
        r"\bno)$",
        prefix,
    ):
        return True

    suffix = sentence[relative_end:]
    return re.match(
        r"^\s*(?:(?:is|are|was|were|remains?|must\s+be|should\s+be|"
        r"cannot\s+be)\s+)?(?:blocked|forbidden|rejected|not\s+supported|"
        r"not\s+allowed|not\s+claimed)\b",
        suffix,
    ) is not None


def _is_yaml_guardrail_section(
    lines: Sequence[str], zero_based_index: int
) -> bool:
    """Return true for values nested under an explicit YAML guardrail key.

    The claim scanner is intentionally line based so it can report stable source
    locations.  This small indentation walk supplies the one piece of YAML
    structure it needs: negative examples in the two registered guardrail
    sections are evidence *about* forbidden claims, not production claims.  An
    exact key allow-list prevents a nearby or similarly named positive claim
    field from inheriting the exemption.
    """

    current_line = lines[zero_based_index]
    if not current_line.strip() or current_line.lstrip().startswith("#"):
        return False
    current_indent = len(current_line) - len(current_line.lstrip(" "))

    for candidate in reversed(lines[:zero_based_index]):
        stripped = candidate.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(candidate) - len(candidate.lstrip(" "))
        if indent >= current_indent:
            continue
        key_match = re.fullmatch(r"([A-Za-z0-9_-]+)\s*:\s*(?:#.*)?", stripped)
        if key_match is None:
            current_indent = indent
            continue
        if key_match.group(1) in YAML_GUARDRAIL_SECTION_KEYS:
            return True
        current_indent = indent
    return False


def _match_is_in_forbidden_markdown_column(
    lines: Sequence[str],
    *,
    zero_based_index: int,
    match: re.Match[str],
    pattern: re.Pattern[str],
) -> bool:
    """Return true only for an exact negative Markdown-table context.

    This keeps explanatory claim matrices scannable without granting a blanket
    exemption to the table row: a forbidden phrase placed in an ``Allowed``
    cell is still reported. Claim-ledger rows receive the same narrow treatment
    only when their exact ``Status`` cell begins with ``FORBIDDEN``.
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
        if (
            any("forbidden" in cell and "reading" in cell for cell in cells)
            or "status" in cells
        ):
            header_cells = cells
            break
    if header_cells is None or len(header_cells) != len(row_spans):
        return False

    status_indexes = {
        index for index, cell in enumerate(header_cells) if cell == "status"
    }
    if any(
        re.fullmatch(
            r"forbidden(?:\s*/\s*(?:not_granted|not_evaluated))?",
            row_spans[index].group(0).strip().lower(),
        )
        is not None
        for index in status_indexes
    ):
        return True

    forbidden_indexes = {
        index
        for index, cell in enumerate(header_cells)
        if "forbidden" in cell and "reading" in cell
    }
    if not forbidden_indexes:
        return False
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
