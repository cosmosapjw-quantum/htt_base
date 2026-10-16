"""P1/S01. Partial HTT statistical functionals, not a physical inference API.

Keep signed x_C, Q, certified sector F and depth G_F separate. Partial
pushforwards preserve the original joint posterior mass and draw IDs.
No MIO certificates or reports may be passed to this independent HTT layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
import math
import re
from typing import Literal, Mapping, Sequence


SOURCE = Literal["Q", "F", "G_F"]
MISSING = frozenset({"unmeasured_defined", "domain_uncertified"})
_H64 = re.compile(r"[0-9a-f]{64}\Z")


def _finite(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric, not boolean")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _nonempty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty")
    return value.strip()


@dataclass(frozen=True)
class GaussProjection:
    """One same-congruence dimensionless projection (not an observed x_C)."""
    H_s_inv: float
    shear_contract_s_inv2: float
    vorticity_contract_s_inv2: float
    omega_tilt: float
    delta_omega_k: float
    congruence_id: str
    epoch_id: str

    def x_c(self) -> float:
        _nonempty(self.congruence_id, "congruence_id")
        _nonempty(self.epoch_id, "epoch_id")
        H = _finite(self.H_s_inv, "H_s_inv")
        sig = _finite(self.shear_contract_s_inv2, "shear_contract_s_inv2")
        vort = _finite(self.vorticity_contract_s_inv2, "vorticity_contract_s_inv2")
        if sig < 0 or vort < 0:
            raise ValueError("spatial tensor contractions must be nonnegative")
        if H == 0 or not math.isfinite(6 * H * H) or 6 * H * H == 0:
            raise ValueError("H^2 normalization is undefined/unstable")
        return _finite((sig-vort)/(6*H*H) +
                       _finite(self.omega_tilt, "omega_tilt") +
                       _finite(self.delta_omega_k, "delta_omega_k"), "x_C")


def shear_anchored_q(x_c: float | None, B_sigma: float | None) -> float | None:
    """Signed x_C/U_sigma where U_sigma=3*B_sigma**2/2, not a total ceiling."""
    if x_c is None or B_sigma is None:
        return None
    x = _finite(x_c, "x_C")
    b = _finite(B_sigma, "B_sigma")
    if b < 0:
        raise ValueError("MES shear bound magnitude must be nonnegative")
    if b == 0:
        return None
    u = 1.5 * b * b
    if not math.isfinite(u) or u == 0:
        raise ValueError("MES U_sigma is numerically invalid")
    return _finite(x/u, "Q")



@dataclass(frozen=True)
class SectorCeilingReceipt:
    """Typed prior admissibility claim; does NOT independently prove its physics."""
    sector_id: str
    comparator_id: str
    frame_id: str
    ceiling_id: str
    ceiling_value: float
    source_sha256: str
    owner: str = "HTT"
    ceiling_status: str = "admissible_sign_clean_sector_ceiling"

    def __post_init__(self) -> None:
        for key in ("sector_id", "comparator_id", "frame_id", "ceiling_id"):
            _nonempty(getattr(self, key), key)
        if not isinstance(self.source_sha256,str) or not _H64.fullmatch(self.source_sha256):
            raise ValueError("source_sha256 must be a 64-character exact lowercase SHA256")
        if self.owner != "HTT" or self.ceiling_status != "admissible_sign_clean_sector_ceiling":
            raise ValueError("only an HTT-owned sign-clean sector ceiling receipt is accepted")
        value = _finite(self.ceiling_value, "ceiling_value")
        if value <= 0:
            raise ValueError("ceiling_value must be positive")

def certified_sector_f(
    sector_amplitude: float | None,
    ceiling: float | None,
    *,
    certified: bool,
    ceiling_receipt: SectorCeilingReceipt | None = None,
) -> float | None:
    """Admissible sign-clean sector with typed ceiling source and owner only."""
    if not isinstance(certified, bool):
        raise TypeError("certified must be a Boolean admission receipt")
    if not certified:
        return None
    if ceiling_receipt is None or not isinstance(ceiling_receipt, SectorCeilingReceipt):
        raise ValueError("certified F requires a typed HTT ceiling receipt")
    if sector_amplitude is None or ceiling is None:
        return None
    a = _finite(sector_amplitude, "sector_amplitude")
    u = _finite(ceiling, "ceiling")
    if u != ceiling_receipt.ceiling_value:
        raise ValueError("ceiling_value conflicts with typed source receipt")
    if u <= 0 or a < 0 or a > u:
        raise ValueError("sector ceiling/sign domain violated; clipping forbidden")
    return _finite(a/u, "F")


@dataclass(frozen=True)
class DepthContract:
    depth_bin_id: str
    congruence_id: str
    normalization_id: str
    sky_support_id: str
    selection_id: str
    covariance_id: str

    def __post_init__(self) -> None:
        for k in ("depth_bin_id", "congruence_id", "normalization_id",
                  "sky_support_id", "selection_id", "covariance_id"):
            _nonempty(getattr(self, k), k)


def depth_contrast_g_f(
    f_reference: float | None,
    f_comparison: float | None,
    reference: DepthContract,
    comparison: DepthContract,
    *,
    floor: float,
    floor_predeclared: bool,
) -> tuple[float, float] | None:
    """Return (log G_F, G_F), with a strictly registered shared-source contract."""
    if not isinstance(reference, DepthContract) or not isinstance(comparison, DepthContract):
        raise TypeError("both bin contracts are required")
    if reference.depth_bin_id == comparison.depth_bin_id:
        raise ValueError("reference and comparison depth must be distinct")
    for key in ("congruence_id", "normalization_id", "sky_support_id",
                "selection_id", "covariance_id"):
        if getattr(reference, key) != getattr(comparison, key):
            raise ValueError(f"G_F cannot mix {key}")
    if floor_predeclared is not True:
        raise ValueError("floor must be preregistered")
    delta = _finite(floor, "floor")
    if delta <= 0 or delta > 1:
        raise ValueError("floor must be in (0,1]")
    if f_reference is None or f_comparison is None:
        return None
    ref = _finite(f_reference, "F_reference")
    cmp = _finite(f_comparison, "F_comparison")
    if not 0 <= ref <= 1 or not 0 <= cmp <= 1:
        raise ValueError("F values must be in [0,1]")
    loggf = math.log(max(cmp, delta)) - math.log(max(ref, delta))
    try:
        gf = math.exp(loggf)
    except OverflowError as exc:
        raise ValueError("G_F overflow; retain log contrast and revise numeric policy") from exc
    if not math.isfinite(gf) or gf <= 0:
        raise ValueError("G_F numerical overflow/underflow")
    return (loggf, gf)


@dataclass(frozen=True)
class PartialDraw:
    sample_id: str
    weight: float
    congruence_id: str
    input_sha256: str
    q: float | None = None
    f: float | None = None
    g_f: float | None = None
    missing_reasons: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _nonempty(self.sample_id, "sample_id")
        _nonempty(self.congruence_id, "congruence_id")
        if not isinstance(self.input_sha256, str) or not _H64.fullmatch(self.input_sha256):
            raise ValueError("input_sha256 must be 64 lowercase hex digits")
        w = _finite(self.weight, "weight")
        if w < 0:
            raise ValueError("weights must be nonnegative")
        if not isinstance(self.missing_reasons, Mapping):
            raise TypeError("missing_reasons must be a mapping")
        if set(self.missing_reasons) - {"Q", "F", "G_F"}:
            raise ValueError("unknown missing reason key")
        for key, val in (("Q", self.q), ("F", self.f), ("G_F", self.g_f)):
            if val is None:
                if self.missing_reasons.get(key) not in MISSING:
                    raise ValueError(f"missing {key} needs typed reason")
            else:
                _finite(val, key)
                if key == "F" and not 0 <= val <= 1:
                    raise ValueError("F must be [0,1] on its admitted domain")
                if key == "G_F" and val <= 0:
                    raise ValueError("G_F must be strictly positive")
                if key in self.missing_reasons:
                    raise ValueError("cannot give both a value and missing reason")
        # Defensive copy avoids external mutation of the input mapping.
        object.__setattr__(self, "missing_reasons", MappingProxyType(dict(sorted(self.missing_reasons.items()))))

    def missing_reason(self, source: SOURCE) -> str | None:
        return self.missing_reasons.get(source)


@dataclass(frozen=True)
class PartialMeasure:
    draws: tuple[PartialDraw, ...]
    source_kind: str = "HTT_DERIVED_FUNCTIONALS_DIAGNOSTIC_ONLY"

    def __post_init__(self) -> None:
        if self.source_kind != "HTT_DERIVED_FUNCTIONALS_DIAGNOSTIC_ONLY":
            raise ValueError("MIO certificate or physical likelihood input is forbidden")
        draws = tuple(self.draws)
        if not draws or any(not isinstance(d, PartialDraw) for d in draws):
            raise TypeError("draws require at least one typed HTT PartialDraw")
        if len({d.sample_id for d in draws}) != len(draws):
            raise ValueError("draw IDs must be unique and preserved")
        if len({d.input_sha256 for d in draws}) != 1 or len({d.congruence_id for d in draws}) != 1:
            raise ValueError("mixed frame/source provenance; separate ensembles required")
        if not math.isclose(math.fsum(d.weight for d in draws), 1.0,
                            abs_tol=1e-12, rel_tol=0.0):
            raise ValueError("weights must sum to 1 over all draws; do not renormalize defined subset")
        object.__setattr__(self, "draws", draws)

    def exceedance(self, source: SOURCE, thresholds: Sequence[float]) -> dict[str, object]:
        if source not in ("Q", "F", "G_F"):
            raise ValueError("source must be registered as Q, F, or G_F")
        if isinstance(thresholds, (str, bytes)):
            raise TypeError("thresholds must be a finite numeric sequence")
        ts = tuple(_finite(x, "threshold") for x in thresholds)
        if not ts or any(b <= a for a,b in zip(ts, ts[1:])):
            raise ValueError("thresholds must be nonempty, unique, strictly increasing and preregistered")
        known = tuple(d for d in self.draws if getattr(d, source.lower()) is not None)
        unknown = tuple(d for d in self.draws if getattr(d, source.lower()) is None)
        unmeasured = math.fsum(d.weight for d in unknown
                              if d.missing_reason(source) == "unmeasured_defined")
        uncertified = math.fsum(d.weight for d in unknown
                               if d.missing_reason(source) == "domain_uncertified")
        mass = math.fsum(d.weight for d in unknown)
        lower = tuple(math.fsum(d.weight for d in known if getattr(d, source.lower()) > t)
                      for t in ts)
        upper = tuple(min(1.0, a+mass) for a in lower)
        return {"source": source, "thresholds": list(ts),
                "lower": list(lower), "upper": list(upper),
                "known_mass": math.fsum(d.weight for d in known),
                "unknown_mass": mass, "unmeasured_defined_mass": unmeasured,
                "domain_uncertified_mass": uncertified,
                "pointwise_bounds": "sharp_for_unrestricted_mathematical_completions_only",
                "physical_completion_admitted": False,
                "joint_curve": "same_draws_monotone_coupling_required",
                "threshold_rule": "strict_greater_than",
                "mio_input_status": "not_consumed",
                "claim_tier": "diagnostic_only"}