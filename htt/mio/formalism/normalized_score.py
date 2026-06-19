"""MIO Q normalized-score contract with explicit numerator and denominator policy."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import json
import math

from .budget_spec import BudgetSpec, BudgetUse
from .departure_bundle import DepartureBundle


DEFAULT_Q_CAVEAT = (
    "Q is a MIO policy-normalized diagnostic score over x_C and an explicit "
    "denominator policy; it is diagnostic-only and not an HTT inference "
    "quantity, model-selection statistic, solver validation, or classification."
)
DEFAULT_COMPARATOR_MULTIVERSE_CAVEAT = (
    "Q comparator multiverse is a MIO diagnostic specification-curve "
    "sensitivity over explicit comparator labels; it is not an HTT inference "
    "quantity, model-selection statistic, solver validation, or classification."
)
Q_DISPLAY_BLOCKED_USE_CODES = (
    "htt_inference_consumption",
    "model_selection",
    "solver_validation",
    "scalar_classification",
)


class NumeratorPolicy(StrEnum):
    """Explicit numerator-policy vocabulary for Q diagnostics."""

    SIGNED = "signed"
    ABSOLUTE = "absolute"
    POSITIVE_PART = "positive_part"


_FORBIDDEN_Q_METADATA_TERMS = (
    "filling",
    "occupancy",
    "certified_f",
    "certified f",
    "posterior",
    "evidence",
    "family_id",
    "family identification",
    "family identified",
    "family classification",
    "geometry",
    "class label",
    "class-label",
    "solver result",
    "native solver result",
    "external transfer " + "validated as " + "native",
    "validated as native",
    "native_validated",
)


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _tuple_of_str(
    values: Sequence[object],
    name: str,
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of strings")
    result = tuple(str(value).strip() for value in values)
    if require_non_empty and not result:
        raise ValueError(f"{name} must contain at least one entry")
    if any(not value for value in result):
        raise ValueError(f"{name} must contain only non-empty strings")
    return result


def _canonical_numerator_policy(policy: object) -> NumeratorPolicy:
    try:
        return NumeratorPolicy(str(policy))
    except ValueError as exc:
        allowed = ", ".join(policy.value for policy in NumeratorPolicy)
        raise ValueError(
            f"numerator policy must be explicit and one of: {allowed}"
        ) from exc


def _apply_numerator_policy(x_c: float, policy: NumeratorPolicy) -> float:
    if not math.isfinite(x_c):
        raise ValueError("x_C must be finite")
    if policy is NumeratorPolicy.SIGNED:
        return x_c
    if policy is NumeratorPolicy.ABSOLUTE:
        return abs(x_c)
    if policy is NumeratorPolicy.POSITIVE_PART:
        return max(x_c, 0.0)
    raise AssertionError(f"unhandled NumeratorPolicy {policy!r}")


def _plain_metadata(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _plain_metadata(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_plain_metadata(item) for item in value]
    return value


def _scan_reserved_language(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _scan_reserved_language(key, name)
            _scan_reserved_language(item, name)
        return
    if isinstance(value, (str, bytes)):
        text = str(value).lower()
        for term in _FORBIDDEN_Q_METADATA_TERMS:
            if term in text:
                raise ValueError(
                    f"{name} must not use reserved Q metadata language: {term}"
                )
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_reserved_language(item, name)


def _derive_config_hash(
    *,
    departure_bundle: DepartureBundle,
    budget_spec: BudgetSpec,
    numerator_policy: NumeratorPolicy,
) -> str:
    payload = {
        "budget_config_hash": budget_spec.config_hash,
        "denominator_policy": budget_spec.policy.value,
        "departure_config_hash": departure_bundle.config_hash,
        "numerator_policy": numerator_policy.value,
        "score_label": "Q",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _merged_input_hashes(
    departure_bundle: DepartureBundle,
    budget_spec: BudgetSpec,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys((*departure_bundle.input_hashes, *budget_spec.input_hashes))
    )


def _combined_transfer_source(
    departure_bundle: DepartureBundle,
    budget_spec: BudgetSpec,
) -> str:
    departure_source = departure_bundle.transfer_source
    budget_source = budget_spec.transfer_source
    non_none = [
        source for source in (departure_source, budget_source) if source != "none"
    ]
    if not non_none:
        return "none"
    if len(set(non_none)) != 1:
        raise ValueError("transfer_source mismatch between departure bundle and budget")
    if (
        departure_bundle.transfer_spec_id is not None
        and budget_spec.transfer_spec_id is not None
        and departure_bundle.transfer_spec_id != budget_spec.transfer_spec_id
    ):
        raise ValueError("transfer_spec_id mismatch between departure bundle and budget")
    return non_none[0]


def _uniform_or_mixed(values: Sequence[str]) -> str:
    if not values:
        return "not_applicable"
    unique = set(values)
    if len(unique) == 1:
        return next(iter(unique))
    return "mixed"


def _derive_multiverse_config_hash(
    *,
    scores: tuple["NormalizedScore", ...],
    baseline_comparator: str,
    summary_label: str,
) -> str:
    payload = {
        "baseline_comparator": baseline_comparator,
        "score_config_hashes": [score.config_hash for score in scores],
        "summary_label": summary_label,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class NormalizedScore:
    """MIO diagnostic ``Q`` as numerator-policy(``x_C``) over a BudgetSpec."""

    departure_bundle: DepartureBundle
    budget_spec: BudgetSpec
    numerator_policy: NumeratorPolicy | str
    score_label: str = "Q"
    config_hash: str | None = None
    input_hashes: tuple[str, ...] | None = None
    artifact_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_Q_CAVEAT,))
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"

    def __post_init__(self) -> None:
        if not isinstance(self.departure_bundle, DepartureBundle):
            raise TypeError("NormalizedScore requires a DepartureBundle")
        if not isinstance(self.budget_spec, BudgetSpec):
            raise TypeError("NormalizedScore requires a BudgetSpec")
        numerator_policy = _canonical_numerator_policy(self.numerator_policy)
        score_label = _non_empty(self.score_label, "score_label")
        if score_label != "Q":
            raise ValueError("score_label must be 'Q'")
        if self.departure_bundle.comparator != self.budget_spec.comparator:
            raise ValueError("Q comparator must match departure bundle and budget")
        if self.departure_bundle.frame != self.budget_spec.frame:
            raise ValueError("Q frame must match departure bundle and budget")
        if self.departure_bundle.units != self.budget_spec.units:
            raise ValueError("Q units must match departure bundle and budget")
        if BudgetUse.SIGNED_PROJECTION_NORMALIZATION not in (
            self.budget_spec.admissible_uses
        ):
            raise ValueError(
                "Q requires a BudgetSpec with signed_projection_normalization use"
            )
        if self.owner != "MIO":
            raise ValueError("NormalizedScore owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("NormalizedScore claim_tier must be 'diagnostic_only'")
        if self.implementation_scope != "mio":
            raise ValueError("NormalizedScore implementation_scope must be 'mio'")

        config_hash = (
            _non_empty(self.config_hash, "config_hash")
            if self.config_hash is not None
            else _derive_config_hash(
                departure_bundle=self.departure_bundle,
                budget_spec=self.budget_spec,
                numerator_policy=numerator_policy,
            )
        )
        input_hashes = (
            _tuple_of_str(self.input_hashes, "input_hashes", require_non_empty=True)
            if self.input_hashes is not None
            else _merged_input_hashes(self.departure_bundle, self.budget_spec)
        )
        if not input_hashes:
            raise ValueError("input_hashes must contain at least one hash")
        artifact_metadata = (
            {}
            if self.artifact_metadata is None
            else _plain_metadata(dict(self.artifact_metadata))
        )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_Q_CAVEAT not in caveats:
            caveats = (DEFAULT_Q_CAVEAT, *caveats)
        _scan_reserved_language(artifact_metadata, "artifact_metadata")
        _scan_reserved_language(caveats, "caveats")
        _scan_reserved_language(
            (
                self.budget_spec.denominator_label,
                *self.budget_spec.assumptions,
            ),
            "budget_spec",
        )

        _combined_transfer_source(self.departure_bundle, self.budget_spec)

        object.__setattr__(self, "numerator_policy", numerator_policy)
        object.__setattr__(self, "score_label", score_label)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "artifact_metadata", artifact_metadata)
        object.__setattr__(self, "caveats", caveats)

    @property
    def x_C(self) -> float:
        return self.departure_bundle.x_C

    @property
    def numerator_value(self) -> float:
        return _apply_numerator_policy(self.x_C, self.numerator_policy)

    @property
    def q_value(self) -> float:
        value = self.numerator_value / self.budget_spec.denominator_value
        if not math.isfinite(value):
            raise ValueError("Q value must be finite")
        return value

    @property
    def denominator_policy(self) -> str:
        return self.budget_spec.policy.value

    @property
    def transfer_source(self) -> str:
        return _combined_transfer_source(self.departure_bundle, self.budget_spec)

    @property
    def display_metadata(self) -> dict[str, object]:
        return {
            "requires_comparator_label": True,
            "comparator": self.departure_bundle.comparator,
            "frame": self.departure_bundle.frame,
            "units": self.departure_bundle.units,
            "numerator_policy": self.numerator_policy.value,
            "denominator_policy": self.denominator_policy,
            "denominator_use": BudgetUse.SIGNED_PROJECTION_NORMALIZATION.value,
            "denominator_label": self.budget_spec.denominator_label,
            "denominator_value": self.budget_spec.denominator_value,
            "blocked_use_codes": list(Q_DISPLAY_BLOCKED_USE_CODES),
        }

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "score_label": self.score_label,
            "score_kind": "policy_normalized_score",
            "x_C": self.x_C,
            "numerator_source": "x_C",
            "numerator_policy": self.numerator_policy.value,
            "numerator_value": self.numerator_value,
            "q_value": self.q_value,
            "denominator_policy": self.denominator_policy,
            "denominator_use": BudgetUse.SIGNED_PROJECTION_NORMALIZATION.value,
            "denominator_label": self.budget_spec.denominator_label,
            "denominator_value": self.budget_spec.denominator_value,
            "units": self.departure_bundle.units,
            "comparator": self.departure_bundle.comparator,
            "frame": self.departure_bundle.frame,
            "transfer_source": self.transfer_source,
            "departure_transfer_source": self.departure_bundle.transfer_source,
            "departure_transfer_spec_id": self.departure_bundle.transfer_spec_id,
            "departure_transfer_metadata": self.departure_bundle.transfer_metadata,
            "budget_transfer_source": self.budget_spec.transfer_source,
            "budget_transfer_spec_id": self.budget_spec.transfer_spec_id,
            "budget_transfer_metadata": self.budget_spec.transfer_metadata,
            "sky_support_status": self.budget_spec.sky_support_status,
            "covariance_status": self.budget_spec.covariance_status,
            "null_mock_status": self.budget_spec.null_mock_status,
            "config_hash": self.config_hash,
            "departure_config_hash": self.departure_bundle.config_hash,
            "budget_config_hash": self.budget_spec.config_hash,
            "input_hashes": list(self.input_hashes),
            "denominator_assumptions": list(self.budget_spec.assumptions),
            "display_metadata": self.display_metadata,
            "artifact_metadata": dict(self.artifact_metadata),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class ComparatorMultiverseSummary:
    """Diagnostic spread of Q over explicit comparator choices."""

    scores: tuple[NormalizedScore, ...]
    baseline_comparator: str | None = None
    summary_label: str = "Q_comparator_multiverse"
    comparator_axis_id: str = "explicit_current_code_comparator_axis"
    comparator_axis_status: str = "registered_current_code_display_axis"
    admissible_set_status: str = "explicit_display_set_not_exhaustive"
    rank_equivalence_status: str = "not_evaluated_no_equivalence_or_morphology_claim"
    generating_command: str = ""
    git_commit: str | None = None
    worktree_state: str | None = None
    config_hash: str | None = None
    input_hashes: tuple[str, ...] | None = None
    artifact_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(
        default_factory=lambda: (DEFAULT_COMPARATOR_MULTIVERSE_CAVEAT,)
    )
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"

    def __post_init__(self) -> None:
        if isinstance(self.scores, (str, bytes)):
            raise ValueError("scores must be a sequence of NormalizedScore samples")
        scores = tuple(self.scores)
        if len(scores) < 2:
            raise ValueError("scores must contain at least two comparator samples")
        if any(not isinstance(score, NormalizedScore) for score in scores):
            raise TypeError("scores must contain NormalizedScore samples")
        comparator_labels = tuple(score.departure_bundle.comparator for score in scores)
        if len(set(comparator_labels)) != len(comparator_labels):
            raise ValueError("scores must use unique comparator labels")

        baseline_comparator = (
            _non_empty(self.baseline_comparator, "baseline_comparator")
            if self.baseline_comparator is not None
            else comparator_labels[0]
        )
        if baseline_comparator not in comparator_labels:
            raise ValueError("baseline_comparator must appear in comparator labels")

        first = scores[0]
        for score in scores[1:]:
            if score.numerator_policy != first.numerator_policy:
                raise ValueError("all scores must share numerator_policy")
            if score.denominator_policy != first.denominator_policy:
                raise ValueError("all scores must share denominator_policy")
            if score.departure_bundle.frame != first.departure_bundle.frame:
                raise ValueError("all scores must share frame")
            if score.departure_bundle.units != first.departure_bundle.units:
                raise ValueError("all scores must share units")
        transfer_sources = {score.transfer_source for score in scores}
        if len(transfer_sources) != 1:
            raise ValueError("Q comparator multiverse requires uniform transfer_source")

        summary_label = _non_empty(self.summary_label, "summary_label")
        if summary_label != "Q_comparator_multiverse":
            raise ValueError("summary_label must be 'Q_comparator_multiverse'")
        comparator_axis_id = _non_empty(self.comparator_axis_id, "comparator_axis_id")
        comparator_axis_status = _non_empty(
            self.comparator_axis_status,
            "comparator_axis_status",
        )
        admissible_set_status = _non_empty(
            self.admissible_set_status,
            "admissible_set_status",
        )
        rank_equivalence_status = _non_empty(
            self.rank_equivalence_status,
            "rank_equivalence_status",
        )
        generating_command = _non_empty(
            self.generating_command,
            "generating_command",
        )
        git_commit = (
            _non_empty(self.git_commit, "git_commit")
            if self.git_commit is not None
            else None
        )
        worktree_state = (
            _non_empty(self.worktree_state, "worktree_state")
            if self.worktree_state is not None
            else None
        )
        if git_commit is None and worktree_state is None:
            raise ValueError(
                "Q comparator multiverse requires git_commit or worktree_state"
            )
        if self.owner != "MIO":
            raise ValueError("ComparatorMultiverseSummary owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError(
                "ComparatorMultiverseSummary claim_tier must be 'diagnostic_only'"
            )
        if self.implementation_scope != "mio":
            raise ValueError(
                "ComparatorMultiverseSummary implementation_scope must be 'mio'"
            )

        input_hashes = (
            _tuple_of_str(self.input_hashes, "input_hashes", require_non_empty=True)
            if self.input_hashes is not None
            else tuple(
                dict.fromkeys(
                    item for score in scores for item in score.input_hashes
                )
            )
        )
        artifact_metadata = (
            {}
            if self.artifact_metadata is None
            else _plain_metadata(dict(self.artifact_metadata))
        )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_COMPARATOR_MULTIVERSE_CAVEAT not in caveats:
            caveats = (DEFAULT_COMPARATOR_MULTIVERSE_CAVEAT, *caveats)
        _scan_reserved_language(artifact_metadata, "artifact_metadata")
        _scan_reserved_language(caveats, "caveats")
        config_hash = (
            _non_empty(self.config_hash, "config_hash")
            if self.config_hash is not None
            else _derive_multiverse_config_hash(
                scores=scores,
                baseline_comparator=baseline_comparator,
                summary_label=summary_label,
            )
        )

        object.__setattr__(self, "scores", scores)
        object.__setattr__(self, "baseline_comparator", baseline_comparator)
        object.__setattr__(self, "summary_label", summary_label)
        object.__setattr__(self, "comparator_axis_id", comparator_axis_id)
        object.__setattr__(self, "comparator_axis_status", comparator_axis_status)
        object.__setattr__(self, "admissible_set_status", admissible_set_status)
        object.__setattr__(self, "rank_equivalence_status", rank_equivalence_status)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "artifact_metadata", artifact_metadata)
        object.__setattr__(self, "caveats", caveats)
        object.__setattr__(self, "config_hash", config_hash)

    @property
    def comparator_labels(self) -> tuple[str, ...]:
        return tuple(score.departure_bundle.comparator for score in self.scores)

    @property
    def q_by_comparator(self) -> dict[str, float]:
        return {
            score.departure_bundle.comparator: score.q_value for score in self.scores
        }

    @property
    def baseline_q(self) -> float:
        return self.q_by_comparator[str(self.baseline_comparator)]

    @property
    def q_spread_absolute(self) -> float:
        values = tuple(self.q_by_comparator.values())
        return max(values) - min(values)

    @property
    def q_spread_relative_to_baseline(self) -> float | None:
        baseline = abs(self.baseline_q)
        if baseline == 0.0:
            return None
        return self.q_spread_absolute / baseline

    @property
    def transfer_source(self) -> str:
        return self.scores[0].transfer_source

    @property
    def transfer_source_by_comparator(self) -> dict[str, str]:
        return {
            score.departure_bundle.comparator: score.transfer_source
            for score in self.scores
        }

    @property
    def transfer_spec_id_by_comparator(self) -> dict[str, str | None]:
        return {
            score.departure_bundle.comparator: (
                score.departure_bundle.transfer_spec_id
                or score.budget_spec.transfer_spec_id
            )
            for score in self.scores
        }

    @property
    def display_metadata(self) -> dict[str, object]:
        first = self.scores[0]
        return {
            "requires_comparator_labels": True,
            "baseline_comparator": self.baseline_comparator,
            "comparator_labels": list(self.comparator_labels),
            "comparator_axis_id": self.comparator_axis_id,
            "comparator_axis_status": self.comparator_axis_status,
            "admissible_set_status": self.admissible_set_status,
            "rank_equivalence_status": self.rank_equivalence_status,
            "spread_role": "specification_curve_sensitivity_only",
            "q_spread_absolute": self.q_spread_absolute,
            "q_spread_relative_to_baseline": self.q_spread_relative_to_baseline,
            "numerator_policy": first.numerator_policy.value,
            "denominator_policy": first.denominator_policy,
            "denominator_use": BudgetUse.SIGNED_PROJECTION_NORMALIZATION.value,
            "frame": first.departure_bundle.frame,
            "units": first.departure_bundle.units,
            "transfer_source_by_comparator": self.transfer_source_by_comparator,
            "transfer_spec_id_by_comparator": self.transfer_spec_id_by_comparator,
            "blocked_use_codes": list(Q_DISPLAY_BLOCKED_USE_CODES),
        }

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "summary_label": self.summary_label,
            "summary_kind": "comparator_specification_curve_sensitivity",
            "comparator_axis_id": self.comparator_axis_id,
            "comparator_axis_status": self.comparator_axis_status,
            "admissible_set_status": self.admissible_set_status,
            "rank_equivalence_status": self.rank_equivalence_status,
            "baseline_comparator": self.baseline_comparator,
            "comparator_labels": list(self.comparator_labels),
            "q_by_comparator": self.q_by_comparator,
            "baseline_q": self.baseline_q,
            "q_spread_absolute": self.q_spread_absolute,
            "q_spread_relative_to_baseline": self.q_spread_relative_to_baseline,
            "score_payloads": [score.as_payload() for score in self.scores],
            "transfer_source": self.transfer_source,
            "transfer_source_by_comparator": self.transfer_source_by_comparator,
            "transfer_spec_id_by_comparator": self.transfer_spec_id_by_comparator,
            "config_hash": self.config_hash,
            "score_config_hashes": [score.config_hash for score in self.scores],
            "input_hashes": list(self.input_hashes),
            "display_metadata": self.display_metadata,
            "artifact_metadata": dict(self.artifact_metadata),
            "caveats": list(self.caveats),
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
        }


def build_normalized_score(
    departure_bundle: DepartureBundle,
    budget_spec: BudgetSpec,
    *,
    numerator_policy: NumeratorPolicy | str,
    score_label: str = "Q",
    config_hash: str | None = None,
    input_hashes: Sequence[object] | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> NormalizedScore:
    """Build a validated MIO ``Q`` diagnostic normalized score."""

    return NormalizedScore(
        departure_bundle=departure_bundle,
        budget_spec=budget_spec,
        numerator_policy=numerator_policy,
        score_label=score_label,
        config_hash=config_hash,
        input_hashes=(
            None if input_hashes is None else tuple(str(v) for v in input_hashes)
        ),
        artifact_metadata=artifact_metadata,
        caveats=(DEFAULT_Q_CAVEAT,) if caveats is None else tuple(caveats),
    )


def build_comparator_multiverse_summary(
    scores: Sequence[NormalizedScore],
    *,
    baseline_comparator: str | None = None,
    generating_command: str,
    git_commit: str | None = None,
    worktree_state: str | None = None,
    config_hash: str | None = None,
    input_hashes: Sequence[object] | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> ComparatorMultiverseSummary:
    """Build a diagnostic Q comparator specification-curve summary."""

    return ComparatorMultiverseSummary(
        scores=tuple(scores),
        baseline_comparator=baseline_comparator,
        generating_command=generating_command,
        git_commit=git_commit,
        worktree_state=worktree_state,
        config_hash=config_hash,
        input_hashes=(
            None if input_hashes is None else tuple(str(value) for value in input_hashes)
        ),
        artifact_metadata=artifact_metadata,
        caveats=(
            (DEFAULT_COMPARATOR_MULTIVERSE_CAVEAT,)
            if caveats is None
            else tuple(caveats)
        ),
    )


__all__ = [
    "ComparatorMultiverseSummary",
    "DEFAULT_COMPARATOR_MULTIVERSE_CAVEAT",
    "DEFAULT_Q_CAVEAT",
    "NormalizedScore",
    "NumeratorPolicy",
    "build_comparator_multiverse_summary",
    "build_normalized_score",
]
