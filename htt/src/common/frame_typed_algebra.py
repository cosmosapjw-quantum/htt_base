"""PR-187: frame-indexed component algebra, signed carrier, order type system.

Three defects the audit raised are structural, not prose:

* H02/H03 -- the four components mix congruences (n-frame shear/curvature,
  u-frame tilt/vorticity, observer boost) and force a signed curvature into a
  nonnegative PSD cone. Fix: every quantity carries a ``frame`` tag and only a
  registered bridge crosses frames; the carrier is ``S+^3 x R`` so the signed
  ``DeltaOmega_k`` is never PSD-clipped.
* H09 -- ``Omega_tilt`` is O(beta^2), so subtracting ``alpha*Omega_tilt^2``
  (O(beta^4)) cannot cancel the O(beta^2) kinematic quadrupole. Fix: boost order
  is a type parameter and the order-correct deprojection subtracts an O(beta^2)
  term.
* H10 -- the antipodal-pair density normalization must be explicit. Fix: the
  single-stream and fixed-total-density pair conventions are distinct typed
  constructors.

Convention/type mechanics only; no physical or observational claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Any

# Congruence/frame tags. No default frame exists (a missing frame raises).
FRAMES = ("n", "u", "obs")
# The positive block (nonnegative) vs the signed axis.
POSITIVE_COMPONENTS = ("Sigma2", "W2", "Omega_tilt")
SIGNED_COMPONENTS = ("DeltaOmega_k",)


class FrameTypeError(TypeError):
    """Raised on an unregistered cross-frame/cross-type/order operation."""


@dataclass(frozen=True)
class Typed:
    """A component value carrying a frame tag and a boost order.

    ``order`` is the leading power of beta (the observer rapidity) the quantity
    scales as; None means order-agnostic (a pure geometric invariant).
    """

    name: str
    value: Fraction
    frame: str
    order: int | None = None
    signed: bool = False

    def __post_init__(self) -> None:
        if self.frame not in FRAMES:
            raise FrameTypeError(f"{self.name}: frame must be one of {FRAMES}")
        if not self.signed and self.value < 0:
            raise FrameTypeError(f"{self.name}: positive-block value cannot be negative")

    def _require_same_frame(self, other: "Typed", op: str) -> None:
        if self.frame != other.frame:
            raise FrameTypeError(
                f"{op}: cross-frame ({self.frame} vs {other.frame}) without a "
                "registered bridge"
            )

    def _require_same_order(self, other: "Typed", op: str) -> None:
        if self.order is not None and other.order is not None and self.order != other.order:
            raise FrameTypeError(
                f"{op}: order mismatch (O(beta^{self.order}) vs "
                f"O(beta^{other.order}))"
            )

    def __add__(self, other: "Typed") -> "Typed":
        if not isinstance(other, Typed):
            raise FrameTypeError("cannot add a bare scalar to a typed component")
        self._require_same_frame(other, "add")
        self._require_same_order(other, "add")
        return Typed(
            f"({self.name}+{other.name})", self.value + other.value, self.frame,
            self.order if self.order is not None else other.order,
            self.signed or other.signed,
        )

    def __sub__(self, other: "Typed") -> "Typed":
        if not isinstance(other, Typed):
            raise FrameTypeError("cannot subtract a bare scalar from a typed component")
        self._require_same_frame(other, "sub")
        self._require_same_order(other, "sub")
        return Typed(
            f"({self.name}-{other.name})", self.value - other.value, self.frame,
            self.order if self.order is not None else other.order,
            True,  # a difference may be negative
        )

    def mul(self, other: "Typed") -> "Typed":
        """Product adds boost orders (order bookkeeping is load-bearing)."""
        if not isinstance(other, Typed):
            raise FrameTypeError("cannot multiply a typed component by a bare scalar")
        self._require_same_frame(other, "mul")
        new_order = (
            None if self.order is None or other.order is None
            else self.order + other.order
        )
        return Typed(
            f"({self.name}*{other.name})", self.value * other.value, self.frame,
            new_order, self.signed or other.signed,
        )


# --- registered bridges (the ONLY way to cross frames) --------------------

@dataclass(frozen=True)
class Bridge:
    src_frame: str
    dst_frame: str
    remainder_order: int  # the leading beta-order of the neglected remainder
    note: str


_BRIDGE_REGISTRY = MappingProxyType({
    ("obs", "u"): Bridge(
        "obs", "u", remainder_order=3, note="observer boost to matter tilt"
    ),
    ("u", "n"): Bridge(
        "u", "n", remainder_order=2, note="tilt frame to normal frame"
    ),
})


def register_bridge(_bridge: Bridge) -> None:
    """Retained compatibility entry point; runtime authority is refused."""
    raise FrameTypeError(
        "runtime bridge registration is forbidden; the canonical bridge "
        "registry is immutable"
    )


def bridge(value: Typed, dst_frame: str) -> Typed:
    key = (value.frame, dst_frame)
    if key not in _BRIDGE_REGISTRY:
        raise FrameTypeError(
            f"no registered bridge {value.frame}->{dst_frame}; cross-frame "
            "conversion refused"
        )
    b = _BRIDGE_REGISTRY[key]
    return Typed(
        f"bridge[{b.src_frame}->{b.dst_frame}]({value.name})", value.value,
        dst_frame, value.order, value.signed,
    )

# --- exact rapidity round-trip (H03) --------------------------------------

def rapidity_roundtrip_residual(beta: Fraction) -> Fraction:
    """Boost by beta then by -beta: exact composition residual (must be 0).

    Rapidities add; a boost and its inverse compose to the identity.
    """
    composed = beta + (-beta)
    return composed


# --- boost-order facts (H09) ----------------------------------------------

def omega_tilt_leading_order() -> int:
    """Omega_tilt = (1+w) Omega_m sinh^2(beta) = O(beta^2)."""
    return 2


def kinematic_quadrupole_leading_order() -> int:
    """Observer-boost temperature quadrupole is O(beta^2)."""
    return 2


def omega_tilt_squared_order() -> int:
    return 2 * omega_tilt_leading_order()  # O(beta^4)


def forbidden_omega_tilt_squared_subtraction() -> bool:
    """True iff subtracting Omega_tilt^2 is order-inconsistent with the quadrupole.

    The quadrupole is O(beta^2); Omega_tilt^2 is O(beta^4); an O(beta^4) term
    cannot cancel an O(beta^2) term, so the subtraction is forbidden.
    """
    return omega_tilt_squared_order() != kinematic_quadrupole_leading_order()


def order_correct_deprojection_order() -> int:
    """The admissible deprojection subtracts an O(beta^2) term (order match)."""
    return kinematic_quadrupole_leading_order()


# --- signed carrier (H02) -------------------------------------------------

def psd_positive_block_only(components: dict[str, Fraction]) -> dict[str, Any]:
    """M = diag(positive block) >= 0 embeds ONLY the positive block.

    DeltaOmega_k is carried on the signed R factor of S+^3 x R and is never
    PSD-projected; both signs are admissible.
    """
    for name in POSITIVE_COMPONENTS:
        if components.get(name, Fraction(0)) < 0:
            raise FrameTypeError(f"{name} is in the positive block and cannot be negative")
    dok = components.get("DeltaOmega_k", Fraction(0))
    return {
        "positive_block": {k: components[k] for k in POSITIVE_COMPONENTS if k in components},
        "signed_axis": {"DeltaOmega_k": dok},
        "carrier": "S+^3 x R",
        "delta_omega_k_sign": (1 if dok > 0 else (-1 if dok < 0 else 0)),
        "psd_clips_signed_axis": False,
    }


# --- antipodal-pair density (H10) -----------------------------------------

def omega_tilt_single_stream(w: Fraction, omega_m: Fraction, beta2: Fraction) -> Typed:
    """Single stream: Omega_tilt = (1+w) Omega_m beta^2 (leading order)."""
    val = (1 + w) * omega_m * beta2
    return Typed("Omega_tilt_single", val, "u", order=2)


def omega_tilt_antipodal_pair(
    w: Fraction, omega_m: Fraction, beta2: Fraction, fixed_total_density: bool = True
) -> Typed:
    """Antipodal pair with the density convention made explicit.

    fixed_total_density: the two streams share the total density (each carries
    half), so the pair Omega_tilt equals the single-stream value (the factor of
    two in the stream count is cancelled by the factor of one-half in each
    stream's density). Otherwise (fixed per-stream density) it doubles.
    """
    base = (1 + w) * omega_m * beta2
    val = base if fixed_total_density else 2 * base
    return Typed(
        f"Omega_tilt_pair[{'total' if fixed_total_density else 'per_stream'}]",
        val, "u", order=2,
    )
