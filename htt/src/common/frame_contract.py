"""PR-125 canonical frame, order, domain and premise contract.

Typed objects for the conventions that were previously implicit prose:
observer frames, perturbative order, background class, units, harmonic
convention, and redshift/depth convention. Theorem, transfer, and estimator
artifacts reference ONE registered contract instead of ad-hoc strings.

Fail-closed rules (spec `pr125_spec.yaml`):

- every contract field is required — there are no silent defaults; the only
  defaulted construction lives in the labeled ``legacy_reproduction_contract``
  channel, which is reproduction-mode only;
- unknown frame/order/background/units/harmonic/depth values raise;
- a tilt magnitude may not be read across frames without the registered
  transform (scalar-alias firewall);
- ``beta == 0`` alone NEVER satisfies the FLRW limit — the historical
  ``beta=0 => EGS/FLRW`` shortcut is structurally rejected.

All kinematic witnesses are exact ``Fraction`` computations (rapidity
velocity-composition), so round-trip/associativity/antisymmetry hold
bit-exactly, not to tolerance. Convention contract correctness is
roadmap_rescue_v1:C1 governance; no physical statement is validated here.

Registered limitations (disclosed, owned by later PRs):

- states and contracts are cross-validated only where an API takes both
  (``global_tilt_limit``); a declared FLRW background with a sheared state
  is caught at the limit-predicate layer, not at construction;
- the vorticity-norm sign registry is prose-only in this PR (no helicity
  witness); only the tilt antisymmetry is machine-witnessed;
- all scalar kinematics here are COLLINEAR; non-collinear composition is a
  separate typed theorem (SIG-P7).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Mapping

SCHEMA_VERSION = "pr125.frame_contract.v1"


class FrameContractError(ValueError):
    """Raised on any premise-contract violation (fail-closed)."""


class _StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - repr sugar
        return self.value


class Frame(_StrEnum):
    NORMAL = "NORMAL"                  # slice-normal congruence n^a
    MATTER = "MATTER"                  # total-matter u^a
    ELECTRON = "ELECTRON"              # electron/baryon drift frame
    CMB = "CMB"                        # radiation dipole-free frame
    LOCAL_OBSERVER = "LOCAL_OBSERVER"  # heliocentric/Local Group observer
    FRAME_FREE = "FRAME_FREE"          # pure-algebra sector (no sky frame)


class PerturbativeOrder(_StrEnum):
    BACKGROUND = "BACKGROUND"
    LINEAR = "LINEAR"
    SECOND_ORDER = "SECOND_ORDER"
    EXACT = "EXACT"


class BackgroundClass(_StrEnum):
    FLRW_FLAT = "FLRW_FLAT"
    FLRW_CURVED = "FLRW_CURVED"
    BIANCHI_I = "BIANCHI_I"
    BIANCHI_II = "BIANCHI_II"
    BIANCHI_IV = "BIANCHI_IV"
    BIANCHI_V = "BIANCHI_V"
    BIANCHI_VI_0 = "BIANCHI_VI_0"
    BIANCHI_VI_H = "BIANCHI_VI_H"
    BIANCHI_VII_0 = "BIANCHI_VII_0"
    BIANCHI_VII_H = "BIANCHI_VII_H"
    BIANCHI_VIII = "BIANCHI_VIII"
    BIANCHI_IX = "BIANCHI_IX"
    LRS_BIANCHI_III = "LRS_BIANCHI_III"
    KANTOWSKI_SACHS = "KANTOWSKI_SACHS"
    NOT_APPLICABLE_ALGEBRAIC = "NOT_APPLICABLE_ALGEBRAIC"


class UnitsConvention(_StrEnum):
    DIMENSIONLESS_HUBBLE_NORMALIZED = "DIMENSIONLESS_HUBBLE_NORMALIZED"
    MICRO_K2 = "MICRO_K2"
    KM_S = "KM_S"
    MPC_COMOVING = "MPC_COMOVING"
    PURE_NUMBER = "PURE_NUMBER"


class HarmonicConvention(_StrEnum):
    COMPLEX_SPHERICAL_CAMB = "COMPLEX_SPHERICAL_CAMB"
    REAL_SPHERICAL = "REAL_SPHERICAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RedshiftDepthConvention(_StrEnum):
    CZ_KM_S = "CZ_KM_S"
    COMOVING_MPC = "COMOVING_MPC"
    DISTANCE_MODULUS = "DISTANCE_MODULUS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


_REQUIRED_FIELDS = (
    "frame", "perturbative_order", "background_class", "units",
    "harmonic_convention", "redshift_depth_convention",
)


def _coerce(enum_cls, value, field: str):
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(str(value))
    except ValueError as exc:
        raise FrameContractError(
            f"unknown {field} value {value!r}; registered: "
            f"{[member.value for member in enum_cls]}"
        ) from exc


@dataclass(frozen=True)
class PremiseContract:
    """One fully explicit premise contract. Every field is required."""

    frame: Frame
    perturbative_order: PerturbativeOrder
    background_class: BackgroundClass
    units: UnitsConvention
    harmonic_convention: HarmonicConvention
    redshift_depth_convention: RedshiftDepthConvention
    reproduction_mode: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame", _coerce(Frame, self.frame, "frame"))
        object.__setattr__(
            self, "perturbative_order",
            _coerce(PerturbativeOrder, self.perturbative_order,
                    "perturbative_order"))
        object.__setattr__(
            self, "background_class",
            _coerce(BackgroundClass, self.background_class,
                    "background_class"))
        object.__setattr__(self, "units",
                           _coerce(UnitsConvention, self.units, "units"))
        object.__setattr__(
            self, "harmonic_convention",
            _coerce(HarmonicConvention, self.harmonic_convention,
                    "harmonic_convention"))
        object.__setattr__(
            self, "redshift_depth_convention",
            _coerce(RedshiftDepthConvention, self.redshift_depth_convention,
                    "redshift_depth_convention"))
        if not isinstance(self.reproduction_mode, bool):
            raise FrameContractError("reproduction_mode must be a bool")

    @classmethod
    def from_payload(cls, payload: Mapping) -> "PremiseContract":
        """Explicit-field construction: a missing field FAILS (no defaults)."""
        if not isinstance(payload, Mapping):
            raise FrameContractError("premise contract payload must be a mapping")
        missing = [field for field in _REQUIRED_FIELDS if field not in payload]
        if missing:
            raise FrameContractError(
                f"premise contract fields missing (no silent defaults): {missing}"
            )
        unknown = set(payload) - set(_REQUIRED_FIELDS) - {"reproduction_mode"}
        if unknown:
            raise FrameContractError(
                f"unknown premise contract fields: {sorted(unknown)}"
            )
        return cls(
            frame=payload["frame"],
            perturbative_order=payload["perturbative_order"],
            background_class=payload["background_class"],
            units=payload["units"],
            harmonic_convention=payload["harmonic_convention"],
            redshift_depth_convention=payload["redshift_depth_convention"],
            reproduction_mode=payload.get("reproduction_mode", False),
        )

    def as_payload(self) -> dict:
        return {
            "frame": self.frame.value,
            "perturbative_order": self.perturbative_order.value,
            "background_class": self.background_class.value,
            "units": self.units.value,
            "harmonic_convention": self.harmonic_convention.value,
            "redshift_depth_convention": self.redshift_depth_convention.value,
            "reproduction_mode": self.reproduction_mode,
        }

    @property
    def contract_id(self) -> str:
        canonical = json.dumps(self.as_payload(), sort_keys=True).encode()
        return "pc-" + hashlib.sha256(canonical).hexdigest()[:16]


def legacy_reproduction_contract() -> PremiseContract:
    """The ONLY defaulted construction — labeled reproduction channel.

    Reproduces the implicit historical convention (matter-frame linear
    bounds in Hubble-normalized units, CAMB harmonics, cz depths). Active
    producers must build explicit contracts instead; this channel exists so
    byte-stable reproduction surfaces can name what they assumed.
    """
    return PremiseContract(
        frame=Frame.MATTER,
        perturbative_order=PerturbativeOrder.LINEAR,
        background_class=BackgroundClass.FLRW_FLAT,
        units=UnitsConvention.DIMENSIONLESS_HUBBLE_NORMALIZED,
        harmonic_convention=HarmonicConvention.COMPLEX_SPHERICAL_CAMB,
        redshift_depth_convention=RedshiftDepthConvention.CZ_KM_S,
        reproduction_mode=True,
    )


# ---------------------------------------------------------------------------
# exact kinematics: rapidity composition + frame boosts
# ---------------------------------------------------------------------------

def compose_beta(beta1: Fraction, beta2: Fraction) -> Fraction:
    """Exact relativistic velocity composition (collinear)."""
    b1, b2 = Fraction(beta1), Fraction(beta2)
    for b in (b1, b2):
        if not (-1 < b < 1):
            raise FrameContractError(f"beta out of the open unit interval: {b}")
    return (b1 + b2) / (1 + b1 * b2)


@dataclass(frozen=True)
class FrameBoost:
    """A registered boost from ``source`` to ``target`` with exact beta.

    Sign convention (spec sign_registry): beta points FROM source TO
    target; the inverse boost carries exactly ``-beta`` (antisymmetry).
    """

    source: Frame
    target: Frame
    beta: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _coerce(Frame, self.source, "frame"))
        object.__setattr__(self, "target", _coerce(Frame, self.target, "frame"))
        beta = Fraction(self.beta)
        if not (-1 < beta < 1):
            raise FrameContractError(f"boost beta out of range: {beta}")
        if self.source is self.target and beta != 0:
            raise FrameContractError("a self-boost must carry beta == 0")
        object.__setattr__(self, "beta", beta)

    def inverse(self) -> "FrameBoost":
        return FrameBoost(source=self.target, target=self.source,
                          beta=-self.beta)

    @staticmethod
    def validate_pair(forward: "FrameBoost", backward: "FrameBoost") -> None:
        """The REAL antisymmetry validator: a declared A->B / B->A boost
        pair must satisfy backward == forward.inverse() exactly (frames
        swapped AND beta negated). A same-sign pair is the registered
        sign-flip defect."""
        if (backward.source is not forward.target
                or backward.target is not forward.source):
            raise FrameContractError(
                "boost pair endpoints do not mirror: "
                f"{forward.source.value}->{forward.target.value} vs "
                f"{backward.source.value}->{backward.target.value}"
            )
        if backward.beta != -forward.beta:
            raise FrameContractError(
                "boost pair violates the antisymmetry witness: "
                f"boost({backward.source.value}->{backward.target.value})."
                f"beta = {backward.beta} but the registered convention "
                f"requires exactly {-forward.beta}"
            )

    def then(self, other: "FrameBoost") -> "FrameBoost":
        if other.source is not self.target:
            raise FrameContractError(
                f"boost composition frame mismatch: {self.target.value} != "
                f"{other.source.value}"
            )
        return FrameBoost(source=self.source, target=other.target,
                          beta=compose_beta(self.beta, other.beta))


def transform_tilt(value: Fraction, boost: "FrameBoost | None",
                   declared_frame: Frame, requested_frame: Frame) -> Fraction:
    """Move a tilt magnitude between frames through a declared boost.

    REGISTERED SEMANTICS (the load-bearing sign convention):

    - ``value`` is the velocity of the MEASURED congruence as read in the
      DECLARED frame;
    - ``boost.beta`` is the velocity of the TARGET frame as measured in the
      SOURCE frame ("beta points FROM source TO target");
    - therefore the reading in the target frame is the relativistic
      velocity SUBTRACTION ``compose(value, -boost.beta)``. Witness: a
      congruence at rest in the declared frame (value = 0) is read as
      ``-boost.beta`` in the target frame.

    Collinear scalars only — the non-collinear composition is a separate
    typed theorem (SIG-P7) and is NOT representable by this helper.

    The scalar-alias firewall guarantees FRAME-LABEL discipline: a value
    declared in one frame cannot be read in another without a boost whose
    endpoints match exactly, and a same-frame read must not carry a boost.
    The firewall does not attest the boost's beta provenance.
    """
    declared = _coerce(Frame, declared_frame, "frame")
    requested = _coerce(Frame, requested_frame, "frame")
    if declared is requested:
        if boost is not None:
            raise FrameContractError(
                "a same-frame read must not supply a boost (nothing to "
                "transform); drop it or fix the declared/requested frames"
            )
        return Fraction(value)
    if boost is None:
        raise FrameContractError(
            "scalar alias without a frame transform: value is declared in "
            f"{declared.value} but requested in {requested.value}"
        )
    if boost.source is not declared or boost.target is not requested:
        raise FrameContractError(
            "scalar alias without a matching frame transform: value is "
            f"declared in {declared.value} but requested in "
            f"{requested.value} and the supplied boost maps "
            f"{boost.source.value} -> {boost.target.value}"
        )
    return compose_beta(Fraction(value), -boost.beta)


# ---------------------------------------------------------------------------
# kinematic state + limit predicates
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KinematicState:
    """Exact kinematic state used by the limit predicates."""

    beta: Fraction
    sigma2: Fraction
    w2: Fraction
    delta_omega_k: Fraction

    def __post_init__(self) -> None:
        for name in ("beta", "sigma2", "w2", "delta_omega_k"):
            object.__setattr__(self, name, Fraction(getattr(self, name)))
        if not (-1 < self.beta < 1):
            raise FrameContractError("beta out of the open unit interval")
        if self.sigma2 < 0 or self.w2 < 0:
            raise FrameContractError(
                "sigma2 and w2 are quadratic moments and must be nonnegative"
            )


def no_tilt_limit(state: KinematicState) -> bool:
    """beta == 0 ONLY. Deliberately NOT sufficient for the FLRW limit."""
    return state.beta == 0


def flrw_limit(state: KinematicState) -> bool:
    """The full FLRW limit needs EVERY departure to vanish.

    ``beta == 0`` alone never suffices (the forbidden EGS shortcut): shear,
    vorticity, and anisotropic curvature must vanish independently.
    """
    return (state.beta == 0 and state.sigma2 == 0 and state.w2 == 0
            and state.delta_omega_k == 0)


def require_flrw_limit(state: KinematicState) -> None:
    if no_tilt_limit(state) and not flrw_limit(state):
        raise FrameContractError(
            "beta == 0 does not imply the FLRW/EGS limit: nonzero "
            f"(sigma2={state.sigma2}, w2={state.w2}, "
            f"delta_omega_k={state.delta_omega_k}) survives the no-tilt limit"
        )
    if not flrw_limit(state):
        raise FrameContractError("state is not in the FLRW limit")


def local_boost_limit(state: KinematicState, boost: FrameBoost) -> KinematicState:
    """Observer-boost reattribution at LINEAR order in beta (collinear).

    The tilt reading transforms by the registered subtraction (the state's
    beta is measured in the boost SOURCE frame; the returned beta is the
    reading in the boost TARGET frame). Copying sigma2/w2/delta_omega_k is
    the LINEAR-ORDER convention map ONLY: at O(beta^2) the observer-
    inferred shear reading leaks (the rev-r141 kinematic deprojection
    Sigma~^2 = Sigma^2 - alpha*(Omega_tilt)^2 owns that correction). This
    helper is a convention map, not a deprojection.
    """
    return KinematicState(
        beta=compose_beta(state.beta, -boost.beta),
        sigma2=state.sigma2,
        w2=state.w2,
        delta_omega_k=state.delta_omega_k,
    )


def global_tilt_limit(state: KinematicState,
                      contract: PremiseContract) -> bool:
    """Nonzero homogeneous tilt on a declared ANISOTROPIC homogeneous
    (Bianchi/LRS/KS) background class; FLRW classes, though spatially
    homogeneous, are excluded by definition of this limit."""
    return state.beta != 0 and contract.background_class in {
        BackgroundClass.BIANCHI_I,
        BackgroundClass.BIANCHI_II,
        BackgroundClass.BIANCHI_IV,
        BackgroundClass.BIANCHI_V,
        BackgroundClass.BIANCHI_VI_0,
        BackgroundClass.BIANCHI_VI_H,
        BackgroundClass.BIANCHI_VII_0,
        BackgroundClass.BIANCHI_VII_H,
        BackgroundClass.BIANCHI_VIII,
        BackgroundClass.BIANCHI_IX,
        BackgroundClass.LRS_BIANCHI_III,
        BackgroundClass.KANTOWSKI_SACHS,
    }
