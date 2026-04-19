"""FB-8.4 skeleton — non-commutation and composition-order contract.

This module deliberately ships no boost-composition physics during the
FB-META-8 rotation. The public surface below is a diagnostic-only
contract placeholder and must raise ``NotImplementedError`` until the
observer-versus-cosmological non-commutation audit is implemented.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np

from bass.observer.observer_boost import ObserverBoost


@runtime_checkable
class GlobalTilt(Protocol):
    """Placeholder protocol for the future cosmological-frame tilt carrier.

    This is a typing-only stand-in for the extended-bundle `GlobalTilt`
    dataclass referenced by the FB-8 / FB-11 plans. It is not an
    implementation surface and must not be treated as an observer boost.
    """

    rapidity: float
    v_hat: tuple[float, float, float]


def compose_tilts(
    global_tilt: GlobalTilt,
    observer_boost: ObserverBoost,
) -> np.ndarray:
    """Diagnostic-only FB-8.4 composition-order surface.

    Contract only: this helper is reserved for the non-commutation audit
    and must never be routed into the production path. The pinned SSOT
    order is `(cosmo-tilt -> observer-boost)`, and the diagnostic
    quantity is the naive vector sum
    `tanh(eta_cosmo) * v_hat_cosmo + tanh(eta_obs) * v_hat_obs`.

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
    raise NotImplementedError(
        "FB-8.4 skeleton only: diagnostic tilt composition is not "
        "implemented."
    )
