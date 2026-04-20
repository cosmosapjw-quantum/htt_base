"""Diagnostic cosmological-tilt and observer-boost composition helpers.

The production layering remains

``cosmological tilt -> observer boost``.

The helper in this module is exposed only so the FB-8 audit can pin the
non-commutation and the type distinction. It is not a production
surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from bass.observer.observer_boost import ObserverBoost
from bass.species.tilted import V_HAT_E_DEFAULT, assert_tilt_admissible


@dataclass(frozen=True)
class GlobalTiltState:
    """Minimal cosmological-tilt carrier used by the FB-8 diagnostics.

    The class mirrors the rapidity convention of ``ObserverBoost`` while
    remaining a separate type in a separate module. No inheritance and
    no silent coercion are permitted between the two surfaces.
    """

    rapidity: float
    v_hat: tuple[float, float, float] = V_HAT_E_DEFAULT

    def __post_init__(self) -> None:
        rapidity = float(self.rapidity)
        if not np.isfinite(rapidity):
            raise ValueError(
                f"rapidity must be finite; got rapidity={self.rapidity!r}"
            )
        if rapidity < 0.0:
            raise ValueError(
                f"rapidity must be non-negative; got rapidity={rapidity!r}. "
                f"Sign of the motion lives in v_hat, not in rapidity."
            )
        v_hat = tuple(float(component) for component in self.v_hat)
        beta = 0.0 if rapidity == 0.0 else float(np.tanh(rapidity))
        if beta >= 1.0:
            beta = float(np.nextafter(1.0, 0.0))
        assert_tilt_admissible(beta, v_hat)
        object.__setattr__(self, "rapidity", rapidity)
        object.__setattr__(self, "v_hat", v_hat)

    @property
    def velocity(self) -> float:
        if self.rapidity == 0.0:
            return 0.0
        beta = float(np.tanh(self.rapidity))
        if beta >= 1.0:
            return float(np.nextafter(1.0, 0.0))
        return beta


@runtime_checkable
class GlobalTilt(Protocol):
    """Typing-only stand-in for the cosmological tilt carrier."""

    rapidity: float
    v_hat: tuple[float, float, float]


def _coerce_global_tilt(global_tilt: GlobalTilt) -> tuple[float, tuple[float, float, float]]:
    if isinstance(global_tilt, ObserverBoost):
        raise TypeError(
            "compose_tilts requires a cosmological-tilt carrier, not an "
            "ObserverBoost. The two surfaces are intentionally type-distinct."
        )
    if not hasattr(global_tilt, "rapidity") or not hasattr(global_tilt, "v_hat"):
        raise TypeError(
            "global_tilt must expose 'rapidity' and 'v_hat' attributes; "
            "silent coercion from mappings/tuples is forbidden."
        )
    rapidity = float(global_tilt.rapidity)
    v_hat = tuple(float(component) for component in global_tilt.v_hat)
    beta = 0.0 if rapidity == 0.0 else float(np.tanh(rapidity))
    if beta >= 1.0:
        beta = float(np.nextafter(1.0, 0.0))
    assert_tilt_admissible(beta, v_hat)
    return rapidity, v_hat


def compose_tilts(
    global_tilt: GlobalTilt,
    observer_boost: ObserverBoost,
) -> np.ndarray:
    """Diagnostic-only FB-8.4 composition-order surface.

    This helper is reserved for the non-commutation audit and must never
    be routed into the production path. The pinned SSOT order is
    ``(cosmo-tilt -> observer-boost)``, and the diagnostic quantity is
    the naive vector sum
    ``tanh(eta_cosmo) * v_hat_cosmo + tanh(eta_obs) * v_hat_obs``.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §5 (diagnostic-only non-commutation contract).
    - ``docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md``
      `D4` and the D-answer consequence table (separate rapidity SSOT
      plus the pinned composition order).
    - Ellis, Maartens & MacCallum 2012, *Relativistic Cosmology*,
      ISBN 978-1-107-00504-0 / DOI 10.1017/CBO9781139014403 (book
      metadata verified; exact prompt-supplied `§5.2` text is not
      exposed in the accessible preview and that gap is recorded in the
      FB-META-8 audit instead of being invented).
    """
    rapidity_cosmo, v_hat_cosmo = _coerce_global_tilt(global_tilt)
    if not isinstance(observer_boost, ObserverBoost):
        raise TypeError(
            "observer_boost must be an ObserverBoost instance; no silent "
            "coercion from cosmological tilt carriers is permitted."
        )
    return (
        float(np.tanh(rapidity_cosmo)) * np.asarray(v_hat_cosmo, dtype=np.float64)
        + observer_boost.velocity * np.asarray(observer_boost.v_hat, dtype=np.float64)
    )
