"""Low-ell scalar summaries packaged as OBSSTAT features only.

The statistics here are observer-side scalar compressions.  They are useful
for diagnostics and null-calibrated feature packaging, but they are not HTT
likelihood evidence, MIO certificates, morphology compatibility, geometry
detection, or Bianchi family identification.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import math
from typing import Any

import numpy as np
from numpy.polynomial.legendre import leggauss, legval

__all__ = [
    "LowEllNullCalibration",
    "LowEllScalarSummary",
    "compute_cl_from_alm",
    "summarize_lowell_scalars",
]


_SCHEMA_VERSION = "obsstat.scalar_lowell.v1"
_FEATURE_CAVEAT = (
    "low-ell scalar feature only; diagnostic summary, not model input, "
    "not MIO output, not morphology compatibility, and not family ID"
)
_NULL_CALIBRATED_STATISTICS = {
    "s_one_half",
    "parity_even_over_odd_ratio",
    "parity_asymmetry",
    "planarity_mean",
}
_FORBIDDEN_PAYLOAD_TERMS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "certificate",
    "truth",
    "geometry detected",
    "detected geometry",
    "family identified",
    "family identification",
    "family ranking",
    "native solver result",
)


@dataclass(frozen=True)
class LowEllNullCalibration:
    """Optional null-calibration metadata for scalar feature p-values."""

    null_ensemble_ref: str
    look_elsewhere_status: str
    p_values: Mapping[str, float]
    mock_count: int | None = None
    tail_definitions: Mapping[str, str] = field(default_factory=dict)
    covariance_status: str = "not_supplied"
    mask_status: str = "not_supplied"
    scan_volume: Mapping[str, Any] = field(default_factory=dict)
    caveats: tuple[str, ...] = (
        "null calibration metadata only; not a model-input score",
    )

    def __post_init__(self) -> None:
        if not str(self.null_ensemble_ref).strip():
            raise ValueError("LowEllNullCalibration.null_ensemble_ref is required")
        if str(self.look_elsewhere_status).strip().lower() not in {
            "tracked",
            "look_elsewhere_tracked",
            "corrected",
            "look_elsewhere_corrected",
            "global_corrected",
            "documented",
        }:
            raise ValueError(
                "LowEllNullCalibration.look_elsewhere_status must document "
                "tracked or corrected look-elsewhere provenance"
            )
        p_values = {str(key): float(value) for key, value in self.p_values.items()}
        if not p_values:
            raise ValueError("LowEllNullCalibration.p_values must be non-empty")
        for key, value in p_values.items():
            _validate_pvalue_key(key)
            if not math.isfinite(value) or not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"LowEllNullCalibration.p_values[{key!r}] must be in [0, 1]"
                )
        object.__setattr__(self, "p_values", p_values)
        if self.mock_count is None or int(self.mock_count) <= 0:
            raise ValueError("LowEllNullCalibration.mock_count must be positive")
        object.__setattr__(self, "mock_count", int(self.mock_count))
        tail_definitions = {
            str(key): str(value).strip()
            for key, value in self.tail_definitions.items()
        }
        missing_tail = [key for key in p_values if not tail_definitions.get(key)]
        if missing_tail:
            raise ValueError(
                "LowEllNullCalibration.tail_definitions must cover every p-value "
                f"key: {missing_tail}"
            )
        object.__setattr__(
            self,
            "tail_definitions",
            tail_definitions,
        )
        if str(self.covariance_status).strip().lower() == "not_supplied":
            raise ValueError("LowEllNullCalibration.covariance_status is required")
        if str(self.mask_status).strip().lower() == "not_supplied":
            raise ValueError("LowEllNullCalibration.mask_status is required")
        scan_volume = {str(key): value for key, value in self.scan_volume.items()}
        if not scan_volume:
            raise ValueError("LowEllNullCalibration.scan_volume is required")
        object.__setattr__(
            self,
            "scan_volume",
            scan_volume,
        )
        object.__setattr__(self, "caveats", tuple(str(item) for item in self.caveats))
        _reject_forbidden_payload_language(
            {
                "null_ensemble_ref": self.null_ensemble_ref,
                "look_elsewhere_status": self.look_elsewhere_status,
                "p_values": p_values,
                "tail_definitions": tail_definitions,
                "covariance_status": self.covariance_status,
                "mask_status": self.mask_status,
                "scan_volume": scan_volume,
                "caveats": self.caveats,
            },
            path="LowEllNullCalibration",
        )

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-compatible null-calibration metadata."""

        return {
            "null_ensemble_ref": self.null_ensemble_ref,
            "look_elsewhere_status": self.look_elsewhere_status,
            "p_values": dict(self.p_values),
            "mock_count": self.mock_count,
            "tail_definitions": dict(self.tail_definitions),
            "covariance_status": self.covariance_status,
            "mask_status": self.mask_status,
            "scan_volume": dict(self.scan_volume),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class LowEllScalarSummary:
    """Feature-only low-ell scalar summary with explicit definitions."""

    cl_by_ell: Mapping[int, float]
    ell_min: int
    ell_max: int
    s_one_half: float
    parity: Mapping[str, Any]
    planarity: Mapping[str, Any]
    definitions: Mapping[str, str]
    channel: str = "TT"
    statistic_role: str = "feature_only"
    claim_tier: str = "diagnostic_only"
    model_role: str = "not_model_input"
    transfer_source: str = "none"
    null_calibration: LowEllNullCalibration | None = None
    metadata_schema: str = _SCHEMA_VERSION
    caveats: tuple[str, ...] = (_FEATURE_CAVEAT,)

    def __post_init__(self) -> None:
        ell_min_i = int(self.ell_min)
        ell_max_i = int(self.ell_max)
        if ell_min_i < 0:
            raise ValueError("LowEllScalarSummary.ell_min must be non-negative")
        if ell_max_i < ell_min_i:
            raise ValueError("LowEllScalarSummary.ell_max must be >= ell_min")
        object.__setattr__(self, "ell_min", ell_min_i)
        object.__setattr__(self, "ell_max", ell_max_i)
        s_one_half = float(self.s_one_half)
        if not math.isfinite(s_one_half) or s_one_half < 0.0:
            raise ValueError(
                "LowEllScalarSummary.s_one_half must be finite and non-negative"
            )
        object.__setattr__(self, "s_one_half", s_one_half)
        if self.claim_tier != "diagnostic_only":
            raise ValueError("LowEllScalarSummary.claim_tier must be diagnostic_only")
        if self.model_role != "not_model_input":
            raise ValueError(
                "LowEllScalarSummary.model_role must be not_model_input"
            )
        if self.transfer_source != "none":
            raise ValueError("LowEllScalarSummary transfer_source must be none")
        expected_role = (
            "null_calibrated_feature"
            if self.null_calibration is not None
            else "feature_only"
        )
        if self.statistic_role != expected_role:
            raise ValueError(
                "LowEllScalarSummary.statistic_role must match null calibration "
                f"status: {expected_role}"
            )
        cl_by_ell = {
            int(ell): float(value) for ell, value in self.cl_by_ell.items()
        }
        if set(cl_by_ell) != set(range(ell_min_i, ell_max_i + 1)):
            raise ValueError(
                "LowEllScalarSummary.cl_by_ell must cover the selected ell range"
            )
        for ell, value in cl_by_ell.items():
            if ell < 0:
                raise ValueError("LowEllScalarSummary C_l ell keys must be non-negative")
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(
                    "LowEllScalarSummary C_l values must be finite and non-negative"
                )
        object.__setattr__(self, "cl_by_ell", cl_by_ell)
        object.__setattr__(
            self,
            "parity",
            _json_mapping(self.parity),
        )
        _validate_numeric_payload(self.parity, path="LowEllScalarSummary.parity")
        object.__setattr__(
            self,
            "planarity",
            _json_mapping(self.planarity),
        )
        _validate_numeric_payload(self.planarity, path="LowEllScalarSummary.planarity")
        object.__setattr__(
            self,
            "definitions",
            {str(key): str(value) for key, value in self.definitions.items()},
        )
        object.__setattr__(self, "caveats", tuple(str(item) for item in self.caveats))
        _reject_forbidden_payload_language(
            {
                "channel": self.channel,
                "definitions": self.definitions,
                "caveats": self.caveats,
            },
            path="LowEllScalarSummary",
        )

    def to_feature_payload(self) -> dict[str, Any]:
        """Return an OBSSTAT scalar feature block safe for ObservableVector."""

        payload: dict[str, Any] = {
            "metadata_schema": self.metadata_schema,
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": self.claim_tier,
            "production_status": "diagnostic_only",
            "statistic_role": self.statistic_role,
            "model_role": self.model_role,
            "transfer_source": self.transfer_source,
            "channel": self.channel,
            "ell_range": [self.ell_min, self.ell_max],
            "cl_by_ell": {str(ell): value for ell, value in self.cl_by_ell.items()},
            "s_one_half": self.s_one_half,
            "parity": _json_payload_mapping(self.parity),
            "planarity": _json_payload_mapping(self.planarity),
            "definitions": dict(self.definitions),
            "claim_status": {
                "geometry_status": "blocked_pre_native_atlas",
                "family_status": "blocked_pre_native_atlas",
                "inference_status": "not_model_input",
                "mio_status": "not_mio_output",
            },
            "caveats": list(self.caveats),
        }
        if self.null_calibration is not None:
            payload["null_calibration"] = self.null_calibration.to_metadata()
        else:
            payload["null_calibration"] = {
                "status": "not_null_calibrated",
                "caveats": ["no p-value or tail statistic supplied"],
            }
        return payload


def summarize_lowell_scalars(
    cl_by_ell: Mapping[int, float] | None = None,
    *,
    ell_min: int = 2,
    ell_max: int | None = None,
    alm_by_lm: Mapping[tuple[int, int], complex | float] | None = None,
    channel: str = "TT",
    s_one_half_quadrature_order: int = 256,
    null_calibration: LowEllNullCalibration | None = None,
    mask_status: str = "not_supplied",
    monopole_dipole_status: str = "excluded_by_ell_min",
    template_subtraction_status: str = "not_applied",
) -> LowEllScalarSummary:
    """Compute feature-only low-ell scalar summaries with explicit definitions."""

    ell_min_i = int(ell_min)
    if ell_min_i < 0:
        raise ValueError("ell_min must be non-negative")
    cl = _prepare_cl_by_ell(cl_by_ell, alm_by_lm=alm_by_lm)
    if not cl:
        raise ValueError("at least one C_l or alm entry is required")
    ell_max_i = int(max(cl) if ell_max is None else ell_max)
    if ell_max_i < ell_min_i:
        raise ValueError("ell_max must be >= ell_min")
    selected = _select_contiguous_cl(cl, ell_min=ell_min_i, ell_max=ell_max_i)
    s_one_half = _compute_s_one_half(
        selected,
        quadrature_order=int(s_one_half_quadrature_order),
    )
    parity = _compute_parity(selected)
    planarity = _compute_planarity(
        alm_by_lm or {},
        ell_min=ell_min_i,
        ell_max=ell_max_i,
    )
    return LowEllScalarSummary(
        cl_by_ell=selected,
        ell_min=ell_min_i,
        ell_max=ell_max_i,
        channel=str(channel),
        s_one_half=float(s_one_half),
        parity=parity,
        planarity=planarity,
        definitions=_definitions(
            mask_status=mask_status,
            monopole_dipole_status=monopole_dipole_status,
            template_subtraction_status=template_subtraction_status,
            s_one_half_quadrature_order=int(s_one_half_quadrature_order),
            cl_source=_cl_source_label(cl_by_ell, alm_by_lm),
        ),
        statistic_role=(
            "null_calibrated_feature"
            if null_calibration is not None
            else "feature_only"
        ),
        null_calibration=null_calibration,
    )


def compute_cl_from_alm(
    alm_by_lm: Mapping[tuple[int, int], complex | float],
) -> dict[int, float]:
    """Compute ``C_l = (2l+1)^-1 sum_m |a_lm|^2`` from dense full alms."""

    grouped = _group_dense_full_alm(alm_by_lm)
    out: dict[int, float] = {}
    for ell, values in grouped.items():
        power = sum(abs(values.get(m, 0.0j)) ** 2 for m in range(-ell, ell + 1))
        out[ell] = float(power / (2 * ell + 1))
    return out


def _prepare_cl_by_ell(
    cl_by_ell: Mapping[int, float] | None,
    *,
    alm_by_lm: Mapping[tuple[int, int], complex | float] | None,
) -> dict[int, float]:
    cl: dict[int, float] = {}
    alm_cl: dict[int, float] = {}
    if alm_by_lm:
        alm_cl.update(compute_cl_from_alm(alm_by_lm))
        cl.update(alm_cl)
    if cl_by_ell:
        for raw_ell, raw_value in cl_by_ell.items():
            ell = int(raw_ell)
            value = float(raw_value)
            if ell < 0:
                raise ValueError("C_l ell keys must be non-negative")
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("C_l values must be finite and non-negative")
            if ell in alm_cl and not math.isclose(
                value,
                alm_cl[ell],
                rel_tol=1.0e-10,
                abs_tol=1.0e-12,
            ):
                raise ValueError("C_l values are inconsistent with alm-derived C_l")
            cl[ell] = value
    return cl


def _select_contiguous_cl(
    cl_by_ell: Mapping[int, float],
    *,
    ell_min: int,
    ell_max: int,
) -> dict[int, float]:
    missing = [ell for ell in range(ell_min, ell_max + 1) if ell not in cl_by_ell]
    if missing:
        raise ValueError(f"missing C_l values for ell={missing}")
    return {ell: float(cl_by_ell[ell]) for ell in range(ell_min, ell_max + 1)}


def _compute_s_one_half(
    cl_by_ell: Mapping[int, float],
    *,
    quadrature_order: int,
) -> float:
    if quadrature_order < 8:
        raise ValueError("s_one_half_quadrature_order must be >= 8")
    nodes, weights = leggauss(quadrature_order)
    x = 0.75 * nodes - 0.25
    scaled_weights = 0.75 * weights
    ell_max = max(cl_by_ell)
    coeffs = np.zeros(ell_max + 1, dtype=float)
    for ell, cl_value in cl_by_ell.items():
        coeffs[ell] = (2 * ell + 1) * float(cl_value) / (4.0 * math.pi)
    ctheta = legval(x, coeffs)
    return float(np.sum(scaled_weights * ctheta * ctheta))


def _compute_parity(cl_by_ell: Mapping[int, float]) -> dict[str, Any]:
    even = 0.0
    odd = 0.0
    weights: dict[int, float] = {}
    for ell, value in cl_by_ell.items():
        weight = float(ell * (ell + 1)) / (2.0 * math.pi)
        weights[int(ell)] = weight
        if ell % 2 == 0:
            even += weight * float(value)
        else:
            odd += weight * float(value)
    ratio = None if odd == 0.0 else even / odd
    denom = even + odd
    asymmetry = None if denom == 0.0 else (even - odd) / denom
    return {
        "definition": "P_+=sum_even ell(ell+1)C_l/(2pi); "
        "P_-=sum_odd ell(ell+1)C_l/(2pi)",
        "weight": "ell_ell_plus_one_over_2pi",
        "even_power": float(even),
        "odd_power": float(odd),
        "even_over_odd_ratio": None if ratio is None else float(ratio),
        "asymmetry": None if asymmetry is None else float(asymmetry),
        "zero_odd_power_policy": "ratio_null_when_odd_power_zero",
        "weights_by_ell": weights,
    }


def _compute_planarity(
    alm_by_lm: Mapping[tuple[int, int], complex | float],
    *,
    ell_min: int,
    ell_max: int,
) -> dict[str, Any]:
    if not alm_by_lm:
        return {
            "status": "not_computed_no_alm",
            "definition": "sum_m m^2 |a_lm|^2 / (l^2 sum_m |a_lm|^2)",
            "axis_rotation_status": "not_rotated",
            "by_ell": {},
            "mean": None,
            "zero_denominator_policy": "null_when_power_zero",
        }
    grouped_all = _group_dense_full_alm(alm_by_lm)
    grouped = {
        ell: values
        for ell, values in grouped_all.items()
        if ell_min <= ell <= ell_max
    }
    by_ell: dict[int, float | None] = {}
    for ell in range(ell_min, ell_max + 1):
        values = grouped.get(ell, {})
        denom = sum(abs(values.get(m, 0.0j)) ** 2 for m in range(-ell, ell + 1))
        if ell < 1 or denom == 0.0:
            by_ell[ell] = None
            continue
        weighted = sum(
            (m * m) * abs(values.get(m, 0.0j)) ** 2
            for m in range(-ell, ell + 1)
        )
        by_ell[ell] = float(weighted / ((ell * ell) * denom))
    finite_values = [value for value in by_ell.values() if value is not None]
    return {
        "status": "computed_from_alm",
        "definition": "sum_m m^2 |a_lm|^2 / (l^2 sum_m |a_lm|^2)",
        "axis_rotation_status": "input_frame_only_not_optimized",
        "optimizer_status": "not_run",
        "degeneracy_policy": "null_when_ell_less_than_one_or_power_zero",
        "by_ell": by_ell,
        "mean": (
            None
            if not finite_values
            else float(sum(finite_values) / len(finite_values))
        ),
        "zero_denominator_policy": "null_when_power_zero",
    }


def _definitions(
    *,
    mask_status: str,
    monopole_dipole_status: str,
    template_subtraction_status: str,
    s_one_half_quadrature_order: int,
    cl_source: str,
) -> dict[str, str]:
    return {
        "cl": "C_l=(2l+1)^-1 sum_m |a_lm|^2 for TT scalar features",
        "cl_source": cl_source,
        "alm_storage": (
            "dense_full_m_minus_l_to_plus_l; every m mode must be supplied"
        ),
        "s_one_half": (
            "integral_-1_to_1/2 [sum_l (2l+1) C_l P_l(x)/(4pi)]^2 dx"
        ),
        "s_one_half_legendre_convention": (
            "P_l(x) evaluated as NumPy Legendre series coefficients"
        ),
        "s_one_half_quadrature": (
            f"Gauss-Legendre quadrature on [-1,1/2], order="
            f"{int(s_one_half_quadrature_order)}"
        ),
        "parity": (
            "even/odd powers use w_l=l(l+1)/(2pi) over the selected ell range"
        ),
        "planarity": (
            "input-frame m^2 power fraction; no axis optimization or morphology claim"
        ),
        "mask_status": str(mask_status),
        "monopole_dipole_status": str(monopole_dipole_status),
        "template_subtraction_status": str(template_subtraction_status),
    }


def _json_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            out[str(key)] = _json_mapping(item)
        else:
            out[str(key) if not isinstance(key, int) else key] = item
    return out


def _json_payload_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            out[str(key)] = _json_payload_mapping(item)
        else:
            out[str(key)] = item
    return out


def _group_dense_full_alm(
    alm_by_lm: Mapping[tuple[int, int], complex | float],
) -> dict[int, dict[int, complex]]:
    grouped: dict[int, dict[int, complex]] = {}
    for key, value in alm_by_lm.items():
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError("alm_by_lm keys must be (ell, m) tuples")
        ell, m = int(key[0]), int(key[1])
        if ell < 0 or abs(m) > ell:
            raise ValueError("alm_by_lm key has invalid ell/m")
        coeff = complex(value)
        if not (math.isfinite(coeff.real) and math.isfinite(coeff.imag)):
            raise ValueError("alm coefficients must be finite")
        grouped.setdefault(ell, {})[m] = coeff
    for ell, values in grouped.items():
        expected = set(range(-ell, ell + 1))
        present = set(values)
        if present != expected:
            missing = sorted(expected - present)
            extra = sorted(present - expected)
            details: list[str] = []
            if missing:
                details.append(f"missing m={missing}")
            if extra:
                details.append(f"unexpected m={extra}")
            raise ValueError(
                "alm_by_lm dense_full storage requires every m mode for "
                f"ell={ell}: {', '.join(details)}"
            )
    return grouped


def _cl_source_label(
    cl_by_ell: Mapping[int, float] | None,
    alm_by_lm: Mapping[tuple[int, int], complex | float] | None,
) -> str:
    has_cl = bool(cl_by_ell)
    has_alm = bool(alm_by_lm)
    if has_cl and has_alm:
        return "provided_cl_checked_against_dense_full_alm_overlap"
    if has_alm:
        return "computed_from_dense_full_alm"
    return "provided_cl_by_ell"


def _validate_pvalue_key(key: str) -> None:
    if key in _NULL_CALIBRATED_STATISTICS:
        return
    if key.startswith("cl_ell_"):
        suffix = key.removeprefix("cl_ell_")
        if suffix.isdigit():
            return
    raise ValueError(
        "LowEllNullCalibration.p_values keys must name known low-ell "
        "statistics or cl_ell_<n>"
    )


def _validate_numeric_payload(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _validate_numeric_payload(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _validate_numeric_payload(item, path=f"{path}[{idx}]")
        return
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            raise ValueError(f"{path} contains a non-finite numeric value")


def _reject_forbidden_payload_language(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(term in key_text for term in _FORBIDDEN_PAYLOAD_TERMS):
                raise ValueError(f"{path}.{key} contains forbidden claim language")
            _reject_forbidden_payload_language(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _reject_forbidden_payload_language(item, path=f"{path}[{idx}]")
        return
    if isinstance(value, str):
        text = value.lower()
        if any(term in text for term in _FORBIDDEN_PAYLOAD_TERMS):
            raise ValueError(f"{path} contains forbidden claim language")
