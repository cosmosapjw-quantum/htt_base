"""Mechanical no-overclaim lint for TSC metadata and snippets."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

FORBIDDEN_PHRASE_REGISTRY: dict[str, tuple[str, ...]] = {
    "full_polarization": (
        "full polarization solved by tsc",
        "tsc validates bb",
        "tsc validated full polarization",
    ),
    "bianchi_family": (
        "tsc identifies bianchi family",
        "bianchi family identified by tsc",
        "tsc validated bianchi family",
    ),
    "source_implies_observable": (
        "source adequate implies observable adequate",
        "source adequate therefore observable adequate",
    ),
    "mio_truth": (
        "mio truth certificate",
        "truth certified by tsc",
    ),
    "htt_evidence_correction": (
        "tsc corrected htt evidence",
        "htt evidence corrected by tsc",
    ),
}


def lint_claim_text(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    hits: list[str] = []
    for code, phrases in FORBIDDEN_PHRASE_REGISTRY.items():
        if any(phrase in lowered for phrase in phrases):
            hits.append(code)
    return tuple(hits)


def _flatten_metadata(metadata: Mapping[str, object]) -> list[str]:
    flat: list[str] = []
    for value in metadata.values():
        if isinstance(value, str):
            flat.append(value)
        elif isinstance(value, Mapping):
            flat.extend(_flatten_metadata(value))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            flat.extend(str(item) for item in value)
        elif value is not None:
            flat.append(str(value))
    return flat


def lint_metadata(metadata: Mapping[str, object]) -> tuple[str, ...]:
    reasons: set[str] = set()
    for text in _flatten_metadata(metadata):
        reasons.update(lint_claim_text(text))
    return tuple(sorted(reasons))


def build_no_overclaim_flags(
    texts: Sequence[str] = (),
    metadata: Mapping[str, object] | None = None,
) -> dict[str, bool]:
    violations: set[str] = set()
    for text in texts:
        violations.update(lint_claim_text(text))
    if metadata is not None:
        violations.update(lint_metadata(metadata))
    return {code: code not in violations for code in FORBIDDEN_PHRASE_REGISTRY}


def quarantine_reasons_from_flags(flags: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(f"no_overclaim:{code}" for code, passed in flags.items() if not passed)


__all__ = [
    "FORBIDDEN_PHRASE_REGISTRY",
    "build_no_overclaim_flags",
    "lint_claim_text",
    "lint_metadata",
    "quarantine_reasons_from_flags",
]
