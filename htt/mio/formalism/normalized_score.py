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
            "artifact_metadata": dict(self.artifact_metadata),
            "caveats": list(self.caveats),
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


__all__ = [
    "DEFAULT_Q_CAVEAT",
    "NormalizedScore",
    "NumeratorPolicy",
    "build_normalized_score",
]
