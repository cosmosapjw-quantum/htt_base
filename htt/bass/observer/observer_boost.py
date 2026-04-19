"""FB-8.1 skeleton — observer-frame boost dataclass contract.

This module deliberately ships no observer-boost physics during the
FB-META-8 rotation. The public surface below is a contract placeholder
only and must raise ``NotImplementedError`` until the observer-frame
aberration and discriminator stack is wired.
"""
from __future__ import annotations

from dataclasses import dataclass

from bass.species.tilted import V_HAT_E_DEFAULT, assert_tilt_admissible

if not callable(assert_tilt_admissible):
    raise ImportError(
        "FB-8.1 requires bass.species.tilted.assert_tilt_admissible "
        "as the shared admissibility SSOT."
    )


@dataclass(frozen=True)
class ObserverBoost:
    """Future FB-8.1 observer-frame rapidity carrier.

    Contract only: this type is reserved for the observer peculiar boost
    that acts *after* the cosmological-frame FB-7 outputs are computed.
    It must not subclass, alias, or silently coerce the cosmological
    tilt surface.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §2 (canonical observer-frame dataclass contract).
    - ``docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md``
      `D4` and `D9` (rapidity SSOT reuse and type-distinct hand-off).
    - ``docs/audits/AUDIT_PHASE_FB3_2026-04-19.md §FB-3.5`` and commit
      ``c1130ad`` (decision-level rapidity SSOT plus the shared
      admissibility gate).
    - ``bass.species.tilted`` (`assert_tilt_admissible`,
      `V_HAT_E_DEFAULT`) for the shared guard convention inherited by
      this observer-only type.
    """

    rapidity: float
    v_hat: tuple[float, float, float] = V_HAT_E_DEFAULT

    def __post_init__(self) -> None:
        """Validate the future observer-boost contract via the shared gate."""
        raise NotImplementedError(
            "FB-8.1 skeleton only: ObserverBoost construction is not "
            "implemented."
        )

    @property
    def velocity(self) -> float:
        """Return the future observer speed ``tanh(rapidity)``."""
        raise NotImplementedError(
            "FB-8.1 skeleton only: ObserverBoost.velocity is not "
            "implemented."
        )

    @property
    def gamma(self) -> float:
        """Return the future observer Lorentz factor ``cosh(rapidity)``."""
        raise NotImplementedError(
            "FB-8.1 skeleton only: ObserverBoost.gamma is not "
            "implemented."
        )

    @property
    def gamma_sq(self) -> float:
        """Return the future observer ``cosh(rapidity)**2`` factor."""
        raise NotImplementedError(
            "FB-8.1 skeleton only: ObserverBoost.gamma_sq is not "
            "implemented."
        )
