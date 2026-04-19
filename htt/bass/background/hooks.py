"""bass/background/hooks.py — Per-era thermodynamic hooks.

Migrated from legacy/bass/bass/background/hooks.py (v8.3.0).

``HookState`` is a frozen-ish dataclass snapshot of the active
thermodynamic configuration (Thomson rate, effective DOF, visibility,
tight-coupling + free-streaming flags) at a given era.  Callable
``EVENT_HOOKS[era]`` lambdas return the appropriate ``HookState`` given
a redshift, so the background RHS can inject era-specific coefficients
without cluttering its own signature with seven scalars.

This is a lightweight shim that exists primarily to keep the
``nonperturbative_tilt`` RHS signature stable during legacy migration.
The production hook mechanism lives in ``bass.recombination`` and
``bass.transport`` which consume HyRec-2 + the m∈{0,±2} Boltzmann
hierarchies respectively.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

import numpy as np

__all__ = ['HookState', 'EVENT_HOOKS', 'apply_hooks']


@dataclass
class HookState:
    """Active hook configuration for the current era.

    Attributes
    ----------
    tau_dot : float
        Thomson scattering rate proxy (arbitrary units).
    g_star : float
        Effective relativistic DOF.
    N_eff : float
        Effective neutrino number (Planck 2018 default 3.044).
    kappa_opacity : float
        Compton opacity proxy.
    visibility : float
        Visibility function g(η) proxy.
    tight_coupling : bool
        Photon-baryon tight coupling active.
    free_streaming : bool
        Neutrinos in free-streaming regime.
    """
    tau_dot: float = 0.0
    g_star: float = 3.363
    N_eff: float = 3.044
    kappa_opacity: float = 0.0
    visibility: float = 0.0
    tight_coupling: bool = True
    free_streaming: bool = False


EVENT_HOOKS: Dict[str, Callable[[float], HookState]] = {
    'deep_radiation': lambda z: HookState(
        tau_dot=1.0e4, g_star=10.75, tight_coupling=True,
    ),
    'neutrino_decoupling': lambda z: HookState(
        tau_dot=1.0e3, g_star=10.75, N_eff=3.044, free_streaming=True,
    ),
    'ee_annihilation': lambda z: HookState(
        tau_dot=500.0, g_star=3.363, free_streaming=True,
    ),
    'radiation_matter_transition': lambda z: HookState(
        tau_dot=100.0, g_star=3.363, free_streaming=True,
    ),
    'recombination': lambda z: HookState(
        tau_dot=max(0.0, 50.0 * float(np.exp(-((z - 1100.0) ** 2) / (200.0 ** 2)))),
        visibility=float(np.exp(-((z - 1100.0) ** 2) / (80.0 ** 2))),
        tight_coupling=(z > 1050.0),
        free_streaming=True,
    ),
    'drag_epoch': lambda z: HookState(
        tau_dot=0.1, visibility=0.01,
        tight_coupling=False, free_streaming=True,
    ),
    'dark_ages': lambda z: HookState(
        tau_dot=0.0, tight_coupling=False, free_streaming=True,
    ),
    'reionization': lambda z: HookState(
        tau_dot=0.05 * (1.0 + z) ** 2 if z > 6.0 else 0.01,
        kappa_opacity=0.054,
        tight_coupling=False, free_streaming=True,
    ),
    'de_domination': lambda z: HookState(
        tau_dot=0.0, tight_coupling=False, free_streaming=True,
    ),
    'late_time': lambda z: HookState(
        tau_dot=0.0, tight_coupling=False, free_streaming=True,
    ),
}


def apply_hooks(era: str, z: float) -> HookState:
    """Return the hook configuration for ``era`` at redshift ``z``.

    Unknown eras return a default ``HookState`` (no active overrides).
    """
    hook = EVENT_HOOKS.get(era)
    if hook is None:
        return HookState()
    return hook(z)
