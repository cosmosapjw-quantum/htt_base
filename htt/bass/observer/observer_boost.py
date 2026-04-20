"""Observer-frame boost carrier for the FB-8 observer layer.

``ObserverBoost`` is the observer-side analogue of the cosmological
tilt rapidity surface, but it is intentionally **not** the same type
and does not inherit from it. The observer boost acts only after the
cosmological-frame FB-7 quantities have been formed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from bass.species.tilted import V_HAT_E_DEFAULT, assert_tilt_admissible

if not callable(assert_tilt_admissible):
    raise ImportError(
        "FB-8.1 requires bass.species.tilted.assert_tilt_admissible "
        "as the shared admissibility SSOT."
    )


@dataclass(frozen=True)
class ObserverBoost:
    """Observer-frame rapidity carrier.

    This type is reserved for the observer peculiar boost that acts
    *after* the cosmological-frame FB-7 outputs are computed. It must
    not subclass, alias, or silently coerce the cosmological tilt
    surface.

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
        """Validate the observer boost via the shared FB-3.5 guard."""
        rapidity = float(self.rapidity)
        if not np.isfinite(rapidity):
            raise ValueError(
                f"rapidity must be finite; got rapidity={self.rapidity!r}"
            )
        if rapidity < 0.0:
            raise ValueError(
                f"rapidity must be non-negative; got rapidity={rapidity!r}. "
                f"Sign of the motion lives in v_hat, not in the scalar rapidity."
            )
        v_hat = tuple(float(component) for component in self.v_hat)
        beta = 0.0 if rapidity == 0.0 else float(np.tanh(rapidity))
        if beta >= 1.0:
            beta = math.nextafter(1.0, 0.0)
        assert_tilt_admissible(beta, v_hat)
        object.__setattr__(self, "rapidity", rapidity)
        object.__setattr__(self, "v_hat", v_hat)

    @property
    def velocity(self) -> float:
        """Return the observer speed ``tanh(rapidity)``."""
        if self.rapidity == 0.0:
            return 0.0
        beta = float(np.tanh(self.rapidity))
        if beta >= 1.0:
            return math.nextafter(1.0, 0.0)
        return beta

    @property
    def gamma(self) -> float:
        """Return the observer Lorentz factor ``cosh(rapidity)``."""
        return float(np.cosh(self.rapidity))

    @property
    def gamma_sq(self) -> float:
        """Return the observer ``cosh(rapidity)**2`` factor."""
        gamma = self.gamma
        return float(gamma * gamma)
