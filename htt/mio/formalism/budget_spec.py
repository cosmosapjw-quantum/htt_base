"""MIO denominator-policy contracts for pre-solver x/Q/Pi/F/G formalism."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from common.enum_compat import StrEnum

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry
from common.transfer_registry import (
    TransferSource,
    validate_transfer_dependent_result,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id


DEFAULT_BUDGET_CAVEAT = (
    "BudgetSpec records a MIO diagnostic denominator policy only; it is not "
    "HTT likelihood, posterior, evidence, native solver validation, or a "
    "geometry/family claim."
)


class BudgetPolicy(StrEnum):
    """Explicit denominator-policy vocabulary for MIO budget diagnostics."""

    MES_LINEAR = "MES_linear"
    EXTERNAL_TRANSFER = "external_transfer"
    ATLAS_QUANTILE = "atlas_quantile"
    OBSERVATIONAL = "observational"


class BudgetUse(StrEnum):
    """Permitted downstream uses for a denominator policy."""

    DENOMINATOR_SENSITIVITY = "denominator_sensitivity"
    SIGNED_PROJECTION_NORMALIZATION = "signed_projection_normalization"
    CERTIFIED_FILLING_CEILING = "certified_filling_ceiling"
    EXCEEDANCE_THRESHOLD = "exceedance_threshold"
    DEPTH_GAP_REFERENCE = "depth_gap_reference"


class NativeMorphologyAtlasStatus(StrEnum):
    """Pre-solver-safe status values for atlas-quantile denominator policies."""

    NOT_AVAILABLE_PRE_SOLVER = "not_available_pre_solver"
    SCHEMA_ONLY = "schema_only"
    EXTERNAL_PROXY_ONLY = "external_proxy_only"


_EXTERNAL_BUDGET_SOURCES = {
    TransferSource.ANICLASS_EXTERNAL,
    TransferSource.EXTERNAL_TRANSFER,
    TransferSource.EMPIRICAL_PROXY,
}


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _optional_non_empty(value: object | None, name: str) -> str | None:
    if value is None:
        return None
    return _non_empty(value, name)


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


def _unit_interval(value: object | None, name: str, *, include_one: bool) -> float | None:
    if value is None:
        return None
    number = _finite_float(value, name)
    upper_ok = number <= 1.0 if include_one else number < 1.0
    if number <= 0.0 or not upper_ok:
        bound = "(0, 1]" if include_one else "(0, 1)"
        raise ValueError(f"{name} must be in {bound}")
    return number


def _canonical_policy(policy: object) -> BudgetPolicy:
    try:
        return BudgetPolicy(str(policy))
    except ValueError as exc:
        allowed = ", ".join(policy.value for policy in BudgetPolicy)
        raise ValueError(
            f"denominator policy must be explicit and one of: {allowed}"
        ) from exc


def _canonical_uses(values: Sequence[object]) -> tuple[BudgetUse, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("admissible_uses must be a sequence")
    uses = tuple(BudgetUse(str(value)) for value in values)
    if not uses:
        raise ValueError("admissible_uses must contain at least one use")
    return tuple(dict.fromkeys(uses))


def _canonical_transfer_source(source: object) -> TransferSource:
    try:
        return TransferSource(str(source))
    except ValueError as exc:
        raise ValueError(f"unknown transfer_source {source!r}") from exc


def _canonical_atlas_status(status: object) -> NativeMorphologyAtlasStatus:
    try:
        return NativeMorphologyAtlasStatus(str(status))
    except ValueError as exc:
        allowed = ", ".join(status.value for status in NativeMorphologyAtlasStatus)
        raise ValueError(
            "native_morphology_atlas_status must be pre-solver-safe and one of: "
            f"{allowed}"
        ) from exc


@dataclass(frozen=True)
class BudgetSensitivityPoint:
    """One shifted denominator value for a policy-sensitivity scan."""

    policy: BudgetPolicy
    denominator_label: str
    baseline_denominator_value: float
    relative_shift: float
    denominator_value: float
    units: str
    transfer_source: str
    config_hash: str
    input_hashes: tuple[str, ...]
    assumptions: tuple[str, ...]
    sky_support_status: str
    covariance_status: str
    null_mock_status: str
    native_morphology_atlas_status: str
    source_description: str | None = None
    transfer_spec_id: str | None = None
    transfer_metadata: Mapping[str, object] | None = None
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_BUDGET_CAVEAT,))

    def __post_init__(self) -> None:
        policy = _canonical_policy(self.policy)
        denominator_label = _non_empty(self.denominator_label, "denominator_label")
        units = _non_empty(self.units, "units")
        baseline = _positive_finite_float(
            self.baseline_denominator_value,
            "baseline_denominator_value",
        )
        shift = _finite_float(self.relative_shift, "relative_shift")
        denominator_value = _positive_finite_float(
            self.denominator_value,
            "denominator_value",
        )
        transfer_source = _canonical_transfer_source(self.transfer_source)
        config_hash = _non_empty(self.config_hash, "config_hash")
        input_hashes = _tuple_of_str(
            self.input_hashes,
            "input_hashes",
            require_non_empty=True,
        )
        assumptions = _tuple_of_str(
            self.assumptions,
            "assumptions",
            require_non_empty=True,
        )
        sky_support_status = _non_empty(self.sky_support_status, "sky_support_status")
        covariance_status = _non_empty(self.covariance_status, "covariance_status")
        null_mock_status = _non_empty(self.null_mock_status, "null_mock_status")
        atlas_status = _non_empty(
            self.native_morphology_atlas_status,
            "native_morphology_atlas_status",
        )
        source_description = _optional_non_empty(
            self.source_description,
            "source_description",
        )
        transfer_spec_id = _optional_non_empty(
            self.transfer_spec_id,
            "transfer_spec_id",
        )
        transfer_metadata = (
            None if self.transfer_metadata is None else dict(self.transfer_metadata)
        )
        if transfer_source in _EXTERNAL_BUDGET_SOURCES:
            if transfer_spec_id is None:
                raise ValueError(
                    "transfer-derived BudgetSensitivityPoint requires transfer_spec_id"
                )
            if transfer_metadata is None:
                raise ValueError(
                    "transfer-derived BudgetSensitivityPoint requires transfer_metadata"
                )
            validate_transfer_dependent_result(transfer_metadata)
            metadata_source = str(transfer_metadata["transfer_source"])
            if metadata_source != transfer_source.value:
                raise ValueError(
                    "BudgetSensitivityPoint transfer_source must match metadata"
                )
        elif transfer_source is not TransferSource.NONE:
            raise ValueError(
                "BudgetSensitivityPoint cannot claim native transfer provenance"
            )
        elif transfer_spec_id is not None or transfer_metadata is not None:
            raise ValueError(
                "BudgetSensitivityPoint with transfer_source='none' cannot carry "
                "transfer provenance"
            )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_BUDGET_CAVEAT not in caveats:
            caveats = (DEFAULT_BUDGET_CAVEAT, *caveats)
        if self.owner != "MIO":
            raise ValueError("BudgetSensitivityPoint owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError(
                "BudgetSensitivityPoint claim_tier must be 'diagnostic_only'"
            )
        if self.implementation_scope != "mio":
            raise ValueError(
                "BudgetSensitivityPoint implementation_scope must be 'mio'"
            )

        object.__setattr__(self, "policy", policy)
        object.__setattr__(self, "denominator_label", denominator_label)
        object.__setattr__(self, "baseline_denominator_value", baseline)
        object.__setattr__(self, "relative_shift", shift)
        object.__setattr__(self, "denominator_value", denominator_value)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "transfer_source", transfer_source.value)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(self, "sky_support_status", sky_support_status)
        object.__setattr__(self, "covariance_status", covariance_status)
        object.__setattr__(self, "null_mock_status", null_mock_status)
        object.__setattr__(self, "native_morphology_atlas_status", atlas_status)
        object.__setattr__(self, "source_description", source_description)
        object.__setattr__(self, "transfer_spec_id", transfer_spec_id)
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        object.__setattr__(self, "caveats", caveats)

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "denominator_policy": self.policy.value,
            "denominator_label": self.denominator_label,
            "baseline_denominator_value": self.baseline_denominator_value,
            "relative_shift": self.relative_shift,
            "denominator_value": self.denominator_value,
            "units": self.units,
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "transfer_metadata": self.transfer_metadata,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "assumptions": list(self.assumptions),
            "sky_support_status": self.sky_support_status,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "native_morphology_atlas_status": self.native_morphology_atlas_status,
            "source_description": self.source_description,
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class BudgetSpec:
    """Explicit denominator-policy record for MIO diagnostic reports."""

    policy: BudgetPolicy | str
    denominator_value: float
    denominator_label: str
    comparator: str
    frame: str
    units: str
    config_hash: str
    input_hashes: tuple[str, ...]
    assumptions: tuple[str, ...]
    uncertainty: float | None = None
    confidence_level: float | None = None
    quantile: float | None = None
    redshift: float | None = None
    channel: str | None = None
    source_description: str | None = None
    native_morphology_atlas_status: str = "not_applicable"
    transfer_source: str = "none"
    transfer_spec_id: str | None = None
    transfer_metadata: Mapping[str, object] | None = None
    sky_support_status: str = "not_directional"
    covariance_status: str = "not_statistical"
    null_mock_status: str = "not_statistical"
    is_admissible_ceiling: bool = False
    admissible_uses: tuple[BudgetUse | str, ...] = (
        BudgetUse.DENOMINATOR_SENSITIVITY,
    )
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_BUDGET_CAVEAT,))
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"

    def __post_init__(self) -> None:
        policy = _canonical_policy(self.policy)
        denominator_value = _positive_finite_float(
            self.denominator_value,
            "denominator_value",
        )
        denominator_label = _non_empty(self.denominator_label, "denominator_label")
        comparator = _non_empty(self.comparator, "comparator")
        frame = _non_empty(self.frame, "frame")
        units = _non_empty(self.units, "units")
        config_hash = _non_empty(self.config_hash, "config_hash")
        input_hashes = _tuple_of_str(
            self.input_hashes,
            "input_hashes",
            require_non_empty=True,
        )
        assumptions = _tuple_of_str(
            self.assumptions,
            "assumptions",
            require_non_empty=True,
        )
        uncertainty = (
            None
            if self.uncertainty is None
            else _finite_float(self.uncertainty, "uncertainty")
        )
        if uncertainty is not None and uncertainty < 0.0:
            raise ValueError("uncertainty must be non-negative")
        confidence_level = _unit_interval(
            self.confidence_level,
            "confidence_level",
            include_one=True,
        )
        quantile = _unit_interval(self.quantile, "quantile", include_one=False)
        redshift = (
            None if self.redshift is None else _finite_float(self.redshift, "redshift")
        )
        channel = _optional_non_empty(self.channel, "channel")
        source_description = _optional_non_empty(
            self.source_description,
            "source_description",
        )
        atlas_status = _non_empty(
            self.native_morphology_atlas_status,
            "native_morphology_atlas_status",
        )
        sky_support_status = _non_empty(self.sky_support_status, "sky_support_status")
        covariance_status = _non_empty(self.covariance_status, "covariance_status")
        null_mock_status = _non_empty(self.null_mock_status, "null_mock_status")
        admissible_uses = _canonical_uses(self.admissible_uses)
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_BUDGET_CAVEAT not in caveats:
            caveats = (DEFAULT_BUDGET_CAVEAT, *caveats)
        transfer_source = _canonical_transfer_source(self.transfer_source)
        transfer_spec_id = _optional_non_empty(
            self.transfer_spec_id,
            "transfer_spec_id",
        )
        transfer_metadata = (
            None if self.transfer_metadata is None else dict(self.transfer_metadata)
        )

        self._validate_policy_specific(
            policy=policy,
            transfer_source=transfer_source,
            transfer_spec_id=transfer_spec_id,
            transfer_metadata=transfer_metadata,
            quantile=quantile,
            source_description=source_description,
            atlas_status=atlas_status,
            sky_support_status=sky_support_status,
            covariance_status=covariance_status,
            null_mock_status=null_mock_status,
            admissible_uses=admissible_uses,
        )
        if self.owner != "MIO":
            raise ValueError("BudgetSpec owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("BudgetSpec claim_tier must be 'diagnostic_only'")
        if self.implementation_scope != "mio":
            raise ValueError("BudgetSpec implementation_scope must be 'mio'")
        if (
            BudgetUse.CERTIFIED_FILLING_CEILING in admissible_uses
            and not self.is_admissible_ceiling
        ):
            raise ValueError(
                "certified filling use requires is_admissible_ceiling=True"
            )
        if (
            self.is_admissible_ceiling
            and BudgetUse.CERTIFIED_FILLING_CEILING not in admissible_uses
        ):
            raise ValueError(
                "is_admissible_ceiling=True requires certified filling use"
            )

        object.__setattr__(self, "policy", policy)
        object.__setattr__(self, "denominator_value", denominator_value)
        object.__setattr__(self, "denominator_label", denominator_label)
        object.__setattr__(self, "comparator", comparator)
        object.__setattr__(self, "frame", frame)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(self, "uncertainty", uncertainty)
        object.__setattr__(self, "confidence_level", confidence_level)
        object.__setattr__(self, "quantile", quantile)
        object.__setattr__(self, "redshift", redshift)
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "source_description", source_description)
        object.__setattr__(self, "native_morphology_atlas_status", atlas_status)
        object.__setattr__(self, "transfer_source", transfer_source.value)
        object.__setattr__(self, "transfer_spec_id", transfer_spec_id)
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        object.__setattr__(self, "sky_support_status", sky_support_status)
        object.__setattr__(self, "covariance_status", covariance_status)
        object.__setattr__(self, "null_mock_status", null_mock_status)
        object.__setattr__(self, "admissible_uses", admissible_uses)
        object.__setattr__(self, "caveats", caveats)

    @staticmethod
    def _validate_policy_specific(
        *,
        policy: BudgetPolicy,
        transfer_source: TransferSource,
        transfer_spec_id: str | None,
        transfer_metadata: Mapping[str, object] | None,
        quantile: float | None,
        source_description: str | None,
        atlas_status: str,
        sky_support_status: str,
        covariance_status: str,
        null_mock_status: str,
        admissible_uses: tuple[BudgetUse, ...],
    ) -> None:
        if policy is BudgetPolicy.EXTERNAL_TRANSFER:
            if transfer_source not in _EXTERNAL_BUDGET_SOURCES:
                raise ValueError(
                    "external_transfer policy requires an external transfer source"
                )
            if transfer_spec_id is None:
                raise ValueError(
                    "external_transfer policy requires transfer_spec_id"
                )
            if transfer_metadata is None:
                raise ValueError(
                    "external_transfer policy requires transfer_metadata"
                )
            validate_transfer_dependent_result(transfer_metadata)
            metadata_source = str(transfer_metadata["transfer_source"])
            if metadata_source != transfer_source.value:
                raise ValueError(
                    "external_transfer transfer_source must match metadata"
                )
            if BudgetUse.CERTIFIED_FILLING_CEILING in admissible_uses:
                raise ValueError(
                    "external_transfer policy cannot certify filling before "
                    "native validation gates"
                )
            return

        if transfer_source is not TransferSource.NONE or transfer_metadata is not None:
            raise ValueError(
                f"{policy.value} budget policy must not carry transfer metadata; "
                "use external_transfer policy instead"
            )
        if transfer_spec_id is not None:
            raise ValueError(
                f"{policy.value} budget policy must not carry transfer_spec_id"
            )

        if policy is BudgetPolicy.MES_LINEAR:
            return
        if policy is BudgetPolicy.ATLAS_QUANTILE:
            if quantile is None:
                raise ValueError("atlas_quantile policy requires quantile")
            if source_description is None:
                raise ValueError(
                    "atlas_quantile policy requires source_description"
                )
            _canonical_atlas_status(atlas_status)
            if BudgetUse.CERTIFIED_FILLING_CEILING in admissible_uses:
                raise ValueError(
                    "atlas_quantile policy cannot be used for certified filling "
                    "before native morphology atlas support"
                )
            return
        if policy is BudgetPolicy.OBSERVATIONAL:
            if source_description is None:
                raise ValueError(
                    "observational budget policy requires source_description"
                )
            if sky_support_status == "not_directional":
                raise ValueError(
                    "observational budget policy requires sky support status"
                )
            if covariance_status == "not_statistical":
                raise ValueError(
                    "observational budget policy requires covariance status"
                )
            if null_mock_status == "not_statistical":
                raise ValueError(
                    "observational budget policy requires null/mock status"
                )
            if BudgetUse.CERTIFIED_FILLING_CEILING in admissible_uses:
                raise ValueError(
                    "observational budget policy cannot be used for certified filling"
                )
            return
        raise AssertionError(f"unhandled BudgetPolicy {policy!r}")

    def denominator_at_shift(self, relative_shift: float) -> float:
        """Return the positive shifted denominator for a sensitivity scan."""

        shift = _finite_float(relative_shift, "relative_shift")
        factor = 1.0 + shift
        if factor <= 0.0:
            raise ValueError("shifted denominator factor must be positive")
        return _positive_finite_float(
            self.denominator_value * factor,
            "shifted denominator",
        )

    def sensitivity_grid(
        self,
        *,
        relative_shifts: Sequence[float] = (-0.1, 0.0, 0.1),
    ) -> tuple[BudgetSensitivityPoint, ...]:
        """Build diagnostic denominator-sensitivity points for this policy."""

        return tuple(
            BudgetSensitivityPoint(
                policy=self.policy,
                denominator_label=self.denominator_label,
                baseline_denominator_value=self.denominator_value,
                relative_shift=float(shift),
                denominator_value=self.denominator_at_shift(float(shift)),
                units=self.units,
                transfer_source=self.transfer_source,
                transfer_spec_id=self.transfer_spec_id,
                transfer_metadata=self.transfer_metadata,
                config_hash=self.config_hash,
                input_hashes=self.input_hashes,
                assumptions=self.assumptions,
                sky_support_status=self.sky_support_status,
                covariance_status=self.covariance_status,
                null_mock_status=self.null_mock_status,
                native_morphology_atlas_status=self.native_morphology_atlas_status,
                source_description=self.source_description,
                caveats=self.caveats,
            )
            for shift in relative_shifts
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "denominator_policy": self.policy.value,
            "denominator_label": self.denominator_label,
            "denominator_value": self.denominator_value,
            "units": self.units,
            "comparator": self.comparator,
            "frame": self.frame,
            "uncertainty": self.uncertainty,
            "confidence_level": self.confidence_level,
            "quantile": self.quantile,
            "redshift": self.redshift,
            "channel": self.channel,
            "source_description": self.source_description,
            "native_morphology_atlas_status": self.native_morphology_atlas_status,
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "transfer_metadata": self.transfer_metadata,
            "sky_support_status": self.sky_support_status,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "is_admissible_ceiling": self.is_admissible_ceiling,
            "admissible_uses": [use.value for use in self.admissible_uses],
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "assumptions": list(self.assumptions),
            "caveats": list(self.caveats),
        }


def build_budget_spec(**kwargs: object) -> BudgetSpec:
    """Build a validated MIO diagnostic budget specification."""

    return BudgetSpec(**kwargs)


def compare_denominator_policies(
    specs: Sequence[BudgetSpec],
    *,
    relative_shifts: Sequence[float] = (0.0,),
) -> tuple[BudgetSensitivityPoint, ...]:
    """Return policy-preserving sensitivity points for multiple budgets."""

    if isinstance(specs, (str, bytes)) or not specs:
        raise ValueError("compare_denominator_policies requires at least one BudgetSpec")
    points: list[BudgetSensitivityPoint] = []
    for spec in specs:
        if not isinstance(spec, BudgetSpec):
            raise TypeError("compare_denominator_policies expects BudgetSpec entries")
        points.extend(spec.sensitivity_grid(relative_shifts=relative_shifts))
    return tuple(points)


__all__ = [
    "BudgetPolicy",
    "BudgetSensitivityPoint",
    "BudgetSpec",
    "BudgetUse",
    "DEFAULT_BUDGET_CAVEAT",
    "NativeMorphologyAtlasStatus",
    "build_budget_spec",
    "compare_denominator_policies",
]
