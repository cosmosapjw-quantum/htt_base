"""Historical MIO F-ratio reproduction with sample-wise pushforward."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
import warnings

from common.statistical_foundations import (
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
)

from .budget_spec import BudgetSpec, BudgetUse
from .departure_bundle import DepartureBundle


DEFAULT_F_CAVEAT = (
    "F is a historical denominator-conditioned MIO diagnostic ratio. It is "
    "not filling, occupancy, distance, probability, evidence, an identified "
    "estimand, or a family classifier."
)

LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "mio.formalism.filling_fraction is a legacy reproduction surface; "
    "use LegacyProjectionReport and typed sector stress for active analysis",
    DeprecationWarning,
    stacklevel=2,
)

_FORBIDDEN_F_METADATA_TERMS = (
    "posterior",
    "posterior odds",
    "evidence",
    "likelihood",
    "bayes factor",
    "model weight",
    "htt evidence",
    "mio posterior",
    "truth certificate",
    "certifies truth",
    "model-independent proof",
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
    "physical occupancy",
    "volume fraction",
    "occupied sector",
    "certified occupancy",
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


def _finite_float(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _positive_finite_float(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be positive finite")
    return number


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
        for term in _FORBIDDEN_F_METADATA_TERMS:
            if term in text:
                raise ValueError(
                    f"{name} must not use reserved F metadata language: {term}"
                )
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_reserved_language(item, name)


def _derive_config_hash(
    *,
    departure_bundles: tuple[DepartureBundle, ...],
    budget_specs: tuple[BudgetSpec, ...],
    score_label: str,
) -> str:
    payload = {
        "budget_config_hashes": [budget.config_hash for budget in budget_specs],
        "denominator_policies": [budget.policy.value for budget in budget_specs],
        "departure_config_hashes": [
            bundle.config_hash for bundle in departure_bundles
        ],
        "score_label": score_label,
        "sample_pushforward": "sample_wise_F",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _merged_input_hashes(
    departure_bundles: tuple[DepartureBundle, ...],
    budget_specs: tuple[BudgetSpec, ...],
) -> tuple[str, ...]:
    values: list[str] = []
    for bundle in departure_bundles:
        values.extend(bundle.input_hashes)
    for budget in budget_specs:
        values.extend(budget.input_hashes)
    return tuple(dict.fromkeys(values))


def _combined_transfer_source(
    departure_bundles: tuple[DepartureBundle, ...],
    budget_specs: tuple[BudgetSpec, ...],
) -> str:
    sources = [
        source
        for source in (
            *[bundle.transfer_source for bundle in departure_bundles],
            *[budget.transfer_source for budget in budget_specs],
        )
        if source != "none"
    ]
    if not sources:
        return "none"
    if len(set(sources)) != 1:
        raise ValueError("transfer_source mismatch across F samples")
    spec_ids = [
        spec_id
        for spec_id in (
            *[bundle.transfer_spec_id for bundle in departure_bundles],
            *[budget.transfer_spec_id for budget in budget_specs],
        )
        if spec_id is not None
    ]
    if len(set(spec_ids)) > 1:
        raise ValueError("transfer_spec_id mismatch across F samples")
    return sources[0]


def _uniform_or_mixed(values: Sequence[str]) -> str:
    unique = set(values)
    if len(unique) == 1:
        return next(iter(unique))
    return "mixed"


def _sequence_of_bundles(
    values: Sequence[DepartureBundle],
) -> tuple[DepartureBundle, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("departure_bundles must be a sequence")
    result = tuple(values)
    if not result:
        raise ValueError("departure_bundles must contain at least one sample")
    if any(not isinstance(value, DepartureBundle) for value in result):
        raise TypeError("departure_bundles must contain DepartureBundle samples")
    return result


def _sequence_of_budgets(values: Sequence[BudgetSpec]) -> tuple[BudgetSpec, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("budget_specs must be a sequence")
    result = tuple(values)
    if not result:
        raise ValueError("budget_specs must contain at least one sample")
    if any(not isinstance(value, BudgetSpec) for value in result):
        raise TypeError("budget_specs must contain BudgetSpec samples")
    return result


@dataclass(frozen=True)
class CertifiedFillingFraction:
    """Deprecated compatibility carrier for sample-wise historical ``x_C/U``."""

    departure_bundles: tuple[DepartureBundle, ...]
    budget_specs: tuple[BudgetSpec, ...]
    score_label: str = "F"
    generating_command: str = ""
    git_commit: str | None = None
    worktree_state: str | None = None
    config_hash: str | None = None
    input_hashes: tuple[str, ...] | None = None
    artifact_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_F_CAVEAT,))
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"

    def __post_init__(self) -> None:
        departure_bundles = _sequence_of_bundles(self.departure_bundles)
        budget_specs = _sequence_of_budgets(self.budget_specs)
        if len(departure_bundles) != len(budget_specs):
            raise ValueError(
                "departure_bundles and budget_specs must have the same sample count"
            )
        score_label = _non_empty(self.score_label, "score_label")
        if score_label != "F":
            raise ValueError("score_label must be 'F'")
        generating_command = _non_empty(
            self.generating_command,
            "generating_command",
        )
        git_commit = (
            None if self.git_commit is None else _non_empty(self.git_commit, "git_commit")
        )
        worktree_state = (
            None
            if self.worktree_state is None
            else _non_empty(self.worktree_state, "worktree_state")
        )
        if git_commit is None and worktree_state is None:
            raise ValueError("F payload requires git_commit or worktree_state")
        if self.owner != "MIO":
            raise ValueError("CertifiedFillingFraction owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError(
                "CertifiedFillingFraction claim_tier must be 'diagnostic_only'"
            )
        if self.implementation_scope != "mio":
            raise ValueError(
                "CertifiedFillingFraction implementation_scope must be 'mio'"
            )

        first_bundle = departure_bundles[0]
        for index, (bundle, budget) in enumerate(
            zip(departure_bundles, budget_specs, strict=True)
        ):
            if bundle.comparator != budget.comparator:
                raise ValueError(f"F sample {index} comparator mismatch")
            if bundle.frame != budget.frame:
                raise ValueError(f"F sample {index} frame mismatch")
            if bundle.units != budget.units:
                raise ValueError(f"F sample {index} units mismatch")
            if bundle.comparator != first_bundle.comparator:
                raise ValueError("all F samples must share comparator")
            if bundle.frame != first_bundle.frame:
                raise ValueError("all F samples must share frame")
            if bundle.units != first_bundle.units:
                raise ValueError("all F samples must share units")
            if BudgetUse.CERTIFIED_FILLING_CEILING not in budget.admissible_uses:
                raise ValueError(
                    "F requires a BudgetSpec with certified_filling_ceiling use"
                )
            if not budget.is_admissible_ceiling:
                raise ValueError("F requires an admissible certified ceiling")
            numerator = _finite_float(bundle.x_C, f"sample {index} x_C")
            if numerator < 0.0:
                raise ValueError("F requires sign-clean nonnegative x_C samples")
            ceiling = _positive_finite_float(
                budget.denominator_value,
                f"sample {index} U",
            )
            numerator / ceiling

        config_hash = (
            _non_empty(self.config_hash, "config_hash")
            if self.config_hash is not None
            else _derive_config_hash(
                departure_bundles=departure_bundles,
                budget_specs=budget_specs,
                score_label=score_label,
            )
        )
        input_hashes = (
            _tuple_of_str(self.input_hashes, "input_hashes", require_non_empty=True)
            if self.input_hashes is not None
            else _merged_input_hashes(departure_bundles, budget_specs)
        )
        if not input_hashes:
            raise ValueError("input_hashes must contain at least one hash")
        artifact_metadata = (
            {}
            if self.artifact_metadata is None
            else _plain_metadata(dict(self.artifact_metadata))
        )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_F_CAVEAT not in caveats:
            caveats = (DEFAULT_F_CAVEAT, *caveats)
        _scan_reserved_language(artifact_metadata, "artifact_metadata")
        _scan_reserved_language(
            tuple(caveat for caveat in caveats if caveat != DEFAULT_F_CAVEAT),
            "caveats",
        )
        _scan_reserved_language(
            tuple(budget.denominator_label for budget in budget_specs),
            "budget_spec",
        )
        _scan_reserved_language(
            tuple(
                assumption
                for budget in budget_specs
                for assumption in budget.assumptions
            ),
            "budget_spec",
        )

        _combined_transfer_source(departure_bundles, budget_specs)

        object.__setattr__(self, "departure_bundles", departure_bundles)
        object.__setattr__(self, "budget_specs", budget_specs)
        object.__setattr__(self, "score_label", score_label)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "artifact_metadata", artifact_metadata)
        object.__setattr__(self, "caveats", caveats)

    @property
    def sample_count(self) -> int:
        return len(self.departure_bundles)

    @property
    def x_C_samples(self) -> tuple[float, ...]:
        return tuple(bundle.x_C for bundle in self.departure_bundles)

    @property
    def U_samples(self) -> tuple[float, ...]:
        return tuple(budget.denominator_value for budget in self.budget_specs)

    @property
    def f_samples(self) -> tuple[float, ...]:
        return tuple(
            bundle.x_C / budget.denominator_value
            for bundle, budget in zip(
                self.departure_bundles,
                self.budget_specs,
                strict=True,
            )
        )

    @property
    def absolute_component_total_samples(self) -> tuple[float, ...]:
        return tuple(
            bundle.absolute_component_total for bundle in self.departure_bundles
        )

    @property
    def cancellation_index_samples(self) -> tuple[float, ...]:
        return tuple(bundle.cancellation_index for bundle in self.departure_bundles)

    @property
    def sector_magnitude_companion_samples(self) -> tuple[float, ...]:
        return tuple(
            bundle.absolute_component_total / budget.denominator_value
            for bundle, budget in zip(
                self.departure_bundles,
                self.budget_specs,
                strict=True,
            )
        )

    @property
    def total_anisotropy_magnitude_samples(self) -> tuple[float, ...]:
        return self.sector_magnitude_companion_samples

    @property
    def F_Bayes(self) -> float:
        """Deprecated alias; this is an arithmetic mean, not Bayesian."""
        warnings.warn(
            "F_Bayes is a deprecated name for mean_samplewise_legacy_F",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.mean_samplewise_legacy_F

    @property
    def mean_samplewise_legacy_F(self) -> float:
        return math.fsum(self.f_samples) / self.sample_count

    @property
    def exceedance_samples(self) -> tuple[float, ...]:
        """One-way denominator stress retained without clipping or rejection."""
        return tuple(max(value - 1.0, 0.0) for value in self.f_samples)

    @property
    def M_sector_magnitude(self) -> float:
        return math.fsum(self.sector_magnitude_companion_samples) / self.sample_count

    @property
    def M_total_anisotropy(self) -> float:
        return self.M_sector_magnitude

    @property
    def denominator_policy(self) -> str:
        policies = {budget.policy.value for budget in self.budget_specs}
        if len(policies) != 1:
            return "mixed"
        return next(iter(policies))

    @property
    def transfer_source(self) -> str:
        return _combined_transfer_source(self.departure_bundles, self.budget_specs)

    def as_payload(self) -> dict[str, object]:
        f_samples = self.f_samples
        m_samples = self.sector_magnitude_companion_samples
        budget = self.budget_specs[0]
        bundle = self.departure_bundles[0]
        return {
            "schema": "mio.legacy_projection_f.v2",
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "status": "legacy_reproduction_only",
            "classification": BC1_LEGACY_PROJECTION,
            "representation_policy": BC2_NO_REPRESENTATION_PROMOTION,
            "allowed_use": ["historical reproduction", "threshold diagnostics"],
            "forbidden_use": [
                "filling",
                "occupancy",
                "distance",
                "probability",
                "evidence",
                "family identification",
            ],
            "score_label": self.score_label,
            "score_kind": "legacy_denominator_conditioned_ratio",
            "sample_pushforward": "sample_wise",
            "aggregation_method": "sample_mean_of_samplewise_F",
            "ratio_of_means_used": False,
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
            "sign_clean_sector": True,
            "numerator_source": "x_C",
            "numerator_policy": "signed_sign_clean",
            "x_C_samples": list(self.x_C_samples),
            "U_samples": list(self.U_samples),
            "f_samples": list(f_samples),
            "absolute_component_total_samples": list(
                self.absolute_component_total_samples
            ),
            "cancellation_index_samples": list(self.cancellation_index_samples),
            "M_samples": list(m_samples),
            "M_sector_magnitude": self.M_sector_magnitude,
            "M_kind": "unsigned_component_total_over_admissible_ceiling",
            "M_definition": (
                "M = absolute_component_total / U, reported as the unsigned "
                "sector-magnitude companion to signed F"
            ),
            "F_definition": (
                "F = x_C / U under the recorded historical denominator "
                "policy; no clipping is applied"
            ),
            "mean_samplewise_legacy_F": self.mean_samplewise_legacy_F,
            "exceedance_samples": list(self.exceedance_samples),
            "legacy_compatibility": {
                "F_Bayes": self.mean_samplewise_legacy_F,
                "original_field_semantics": "arithmetic_mean_not_Bayesian",
            },
            "f_min": min(f_samples),
            "f_max": max(f_samples),
            "m_min": min(m_samples),
            "m_max": max(m_samples),
            "sample_count": self.sample_count,
            "valid_sample_count": self.sample_count,
            "invalid_sample_count": 0,
            "invalid_sample_reasons": [],
            "denominator_policy": self.denominator_policy,
            "denominator_use": BudgetUse.CERTIFIED_FILLING_CEILING.value,
            "denominator_labels": [
                budget.denominator_label for budget in self.budget_specs
            ],
            "budget_is_admissible_ceiling": True,
            "admissible_uses": [
                sorted(use.value for use in budget.admissible_uses)
                for budget in self.budget_specs
            ],
            "units": bundle.units,
            "comparator": bundle.comparator,
            "frame": bundle.frame,
            "transfer_source": self.transfer_source,
            "departure_transfer_sources": [
                bundle.transfer_source for bundle in self.departure_bundles
            ],
            "departure_transfer_spec_ids": [
                bundle.transfer_spec_id for bundle in self.departure_bundles
            ],
            "departure_transfer_metadata": [
                bundle.transfer_metadata for bundle in self.departure_bundles
            ],
            "sector_profiles": [
                bundle.sector_profile for bundle in self.departure_bundles
            ],
            "display_metadata": {
                "requires_sector_profile": True,
                "requires_absolute_component_total": True,
                "requires_cancellation_index": True,
                "requires_magnitude_companion_M": True,
                "F_interpretation": (
                    "signed projection fraction of an admissible ceiling; "
                    "not a material-occupancy or volume-readout claim"
                ),
                "M_interpretation": (
                    "unsigned sector-magnitude companion; can "
                    "diverge from F under cancellation"
                ),
                "blocked_use_codes": [
                    "material_occupancy",
                    "inference_probability",
                    "scalar_classification",
                    "solver_validation",
                ],
            },
            "budget_transfer_sources": [
                budget.transfer_source for budget in self.budget_specs
            ],
            "budget_transfer_spec_ids": [
                budget.transfer_spec_id for budget in self.budget_specs
            ],
            "budget_transfer_metadata": [
                budget.transfer_metadata for budget in self.budget_specs
            ],
            "sky_support_status": _uniform_or_mixed(
                [budget.sky_support_status for budget in self.budget_specs]
            ),
            "sky_support_statuses": [
                budget.sky_support_status for budget in self.budget_specs
            ],
            "covariance_status": _uniform_or_mixed(
                [budget.covariance_status for budget in self.budget_specs]
            ),
            "covariance_statuses": [
                budget.covariance_status for budget in self.budget_specs
            ],
            "null_mock_status": _uniform_or_mixed(
                [budget.null_mock_status for budget in self.budget_specs]
            ),
            "null_mock_statuses": [
                budget.null_mock_status for budget in self.budget_specs
            ],
            "config_hash": self.config_hash,
            "departure_config_hashes": [
                bundle.config_hash for bundle in self.departure_bundles
            ],
            "budget_config_hashes": [
                budget.config_hash for budget in self.budget_specs
            ],
            "input_hashes": list(self.input_hashes),
            "denominator_assumptions": [
                list(budget.assumptions) for budget in self.budget_specs
            ],
            "artifact_metadata": dict(self.artifact_metadata),
            "caveats": list(self.caveats),
        }


def build_certified_filling_fraction(
    departure_bundles: Sequence[DepartureBundle],
    budget_specs: Sequence[BudgetSpec],
    *,
    generating_command: str,
    git_commit: str | None = None,
    worktree_state: str | None = None,
    score_label: str = "F",
    config_hash: str | None = None,
    input_hashes: Sequence[object] | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> CertifiedFillingFraction:
    """Build a validated MIO ``F`` certified filling-fraction diagnostic."""

    return CertifiedFillingFraction(
        departure_bundles=tuple(departure_bundles),
        budget_specs=tuple(budget_specs),
        score_label=score_label,
        generating_command=generating_command,
        git_commit=git_commit,
        worktree_state=worktree_state,
        config_hash=config_hash,
        input_hashes=(
            None
            if input_hashes is None
            else _tuple_of_str(input_hashes, "input_hashes", require_non_empty=True)
        ),
        artifact_metadata=artifact_metadata,
        caveats=(DEFAULT_F_CAVEAT,) if caveats is None else tuple(caveats),
    )


__all__ = [
    "CertifiedFillingFraction",
    "DEFAULT_F_CAVEAT",
    "build_certified_filling_fraction",
]
