"""Hard inference envelope (PA-12 / PA-5).

Audits R17-P3 (2026-04-29) found the inference layer enforces
``FittingBlockedError`` correctly when downstream gates are missing,
but does *not* hard-stop a request whose **target family** lies outside
the supported envelope:

- the strong-IC envelope is ``{FLRW, I, V, IX}`` (per
  :data:`bass.hierarchy.seed_factory.STRONG_FAMILIES`);
- the eight remaining families (II, III, IV, VI_0, VI_h, VII_0, VII_h,
  VIII) only have *template-card* IC and explicit
  ``NotImplementedError('FB-5.2')`` for off-axis modes;
- headline science numbers (``ln B``, ``β``, ``F_Bayes``) are research
  goals and currently have no production code path.

Without an envelope guard, a YAML config that points at a
non-strong family or marks ``headline_results=true`` could silently run
the synthetic-surrogate Gaussian harness *or* attempt a live posterior
that the gate would later block deeper in the stack — both make
overclaim trivially easy.

This module exposes:

- :class:`EnvelopeError` — raised at the entry boundary.
- :class:`InferenceEnvelopeRequest` — frozen request descriptor.
- :func:`enforce_inference_envelope` — single hard gate.

The function is invoked from :mod:`bass.inference.__main__` *before any
solver call*, so violations surface immediately with a structured
diagnostic instead of being masked by the downstream
``FittingBlockedError`` ladder.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from bass.hierarchy.seed_factory import (
    STRONG_FAMILIES,
    TEMPLATE_CARD_FAMILIES,
)

__all__ = [
    "EnvelopeError",
    "InferenceEnvelopeRequest",
    "ALLOWED_DATASET_KINDS",
    "HEADLINE_SCIENCE_FORBIDDEN_KEYS",
    "enforce_inference_envelope",
]


#: Dataset kinds that the FB-11 CLI is permitted to dispatch.
ALLOWED_DATASET_KINDS: frozenset[str] = frozenset(
    {"type_i_native_validation", "synthetic_surrogate"}
)

#: Config keys whose presence implies a headline-science claim. Any
#: such key forces an explicit ``allow_research_goal_only=True`` opt-in.
HEADLINE_SCIENCE_FORBIDDEN_KEYS: tuple[str, ...] = (
    "publish_ln_B",
    "publish_F_Bayes",
    "publish_beta_threshold_as_production",
    "publish_planck_18_bayes_factor",
)


class EnvelopeError(RuntimeError):
    """Raised when an inference request falls outside the supported envelope.

    This is a *hard* gate (raised at CLI entry, before any solver / gate
    bundle work). It signals that the request — independent of solver
    health — is asking for a number that the production code is not
    permitted to produce. Use ``ValueError``-like exit handling.
    """

    def __init__(
        self,
        *,
        reason: str,
        violations: tuple[str, ...],
        request: "InferenceEnvelopeRequest",
    ) -> None:
        self.reason = str(reason)
        self.violations = tuple(violations)
        self.request = request
        super().__init__(
            f"inference envelope violation: {reason}; violations={list(violations)!r}"
        )


@dataclass(frozen=True)
class InferenceEnvelopeRequest:
    """Frozen descriptor of an inference request, normalized for the gate."""

    dataset_kind: str
    truth_type: str | None = None
    target_families: tuple[str, ...] = ()
    allow_template_card: bool = False
    allow_research_goal_only: bool = False
    headline_keys_present: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_kind", str(self.dataset_kind))
        if self.truth_type is not None:
            object.__setattr__(self, "truth_type", str(self.truth_type))
        object.__setattr__(
            self,
            "target_families",
            tuple(str(f) for f in self.target_families),
        )
        object.__setattr__(
            self,
            "headline_keys_present",
            tuple(str(k) for k in self.headline_keys_present),
        )


def _coerce_families(payload: Mapping[str, object] | None) -> tuple[str, ...]:
    if payload is None:
        return ()
    raw = payload.get("target_families")
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, Iterable):
        return tuple(str(item) for item in raw)
    raise TypeError("envelope.target_families must be a string or iterable")


def _detect_headline_keys(config: Mapping[str, object]) -> tuple[str, ...]:
    """Return the headline-science keys present anywhere in the config."""
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, Mapping):
            for k, v in node.items():
                if str(k) in HEADLINE_SCIENCE_FORBIDDEN_KEYS and bool(v):
                    found.append(str(k))
                walk(v)
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)

    walk(config)
    return tuple(sorted(set(found)))


def _build_request(config: Mapping[str, object]) -> InferenceEnvelopeRequest:
    dataset = dict(config.get("dataset", {})) if isinstance(config, Mapping) else {}
    envelope = (
        dict(config.get("envelope", {}))
        if isinstance(config, Mapping) and isinstance(config.get("envelope"), Mapping)
        else {}
    )
    target_families = _coerce_families(envelope) or _coerce_families(dataset)
    if not target_families:
        truth = dataset.get("truth_type")
        if truth is not None:
            target_families = (str(truth),)
    return InferenceEnvelopeRequest(
        dataset_kind=str(dataset.get("kind", "")),
        truth_type=(
            str(dataset["truth_type"]) if "truth_type" in dataset else None
        ),
        target_families=target_families,
        allow_template_card=bool(envelope.get("allow_template_card", False)),
        allow_research_goal_only=bool(
            envelope.get("allow_research_goal_only", False)
        ),
        headline_keys_present=_detect_headline_keys(config),
    )


def enforce_inference_envelope(
    config: Mapping[str, object],
) -> InferenceEnvelopeRequest:
    """Hard-gate an inference request *before* any solver call.

    The gate checks four invariants:

    1. ``dataset.kind`` is in :data:`ALLOWED_DATASET_KINDS`.
    2. Every ``target_family`` in the request is either (a) in
       :data:`bass.hierarchy.seed_factory.STRONG_FAMILIES`, or (b) in
       :data:`TEMPLATE_CARD_FAMILIES` *with* an explicit
       ``envelope.allow_template_card: true`` opt-in.
    3. No headline-science key (e.g. ``publish_ln_B``) is set unless
       ``envelope.allow_research_goal_only: true`` is also set, which
       documents that the user understands this is a research-goal
       config, not a production-claim config.
    4. ``synthetic_surrogate`` requests must mark
       ``dataset.allow_surrogate: true`` (cross-checked here so the
       envelope is the single point of refusal).

    Returns the parsed :class:`InferenceEnvelopeRequest` on success;
    raises :class:`EnvelopeError` on any violation.
    """
    request = _build_request(config)
    violations: list[str] = []
    reasons: list[str] = []

    if request.dataset_kind not in ALLOWED_DATASET_KINDS:
        violations.append(f"dataset.kind={request.dataset_kind!r}")
        reasons.append(
            "dataset.kind must be one of " + repr(sorted(ALLOWED_DATASET_KINDS))
        )

    bad_families: list[str] = []
    template_families_in_request: list[str] = []
    for family in request.target_families:
        if family in STRONG_FAMILIES:
            continue
        if family in TEMPLATE_CARD_FAMILIES:
            template_families_in_request.append(family)
            continue
        bad_families.append(family)

    if bad_families:
        violations.append("target_families=" + repr(sorted(bad_families)))
        reasons.append(
            "target families outside the registry; allowed: "
            + repr(sorted(STRONG_FAMILIES | TEMPLATE_CARD_FAMILIES))
        )

    if template_families_in_request and not request.allow_template_card:
        violations.append(
            "template_card_families_without_opt_in="
            + repr(sorted(template_families_in_request))
        )
        reasons.append(
            "fitting on template-card families requires "
            "envelope.allow_template_card=true; "
            "see bass/hierarchy/seed_factory.py:STRONG_FAMILIES"
        )

    if request.headline_keys_present and not request.allow_research_goal_only:
        violations.append(
            "headline_science_without_research_goal_only="
            + repr(list(request.headline_keys_present))
        )
        reasons.append(
            "headline-science keys "
            + repr(list(HEADLINE_SCIENCE_FORBIDDEN_KEYS))
            + " require envelope.allow_research_goal_only=true; "
            "no production code path currently emits these numbers"
        )

    dataset = dict(config.get("dataset", {})) if isinstance(config, Mapping) else {}
    if request.dataset_kind == "synthetic_surrogate" and not bool(
        dataset.get("allow_surrogate", False)
    ):
        violations.append("synthetic_surrogate_without_allow_surrogate")
        reasons.append(
            "synthetic_surrogate dataset must set "
            "dataset.allow_surrogate=true so reviewers can grep for the opt-in"
        )

    if violations:
        raise EnvelopeError(
            reason="; ".join(reasons) if reasons else "envelope violation",
            violations=tuple(violations),
            request=request,
        )
    return request
