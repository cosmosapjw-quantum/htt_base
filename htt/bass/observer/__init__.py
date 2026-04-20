"""bass.observer — observer-frame boost and discriminator surfaces.

This package is introduced at FB-META-8 for *observer-frame* surfaces
only. Cosmological tilt and observer boost remain type-distinct:
``(beta_cosmo, v_hat_cosmo)`` and ``(beta_obs, v_hat_obs)`` are owned by
separate modules, with no inheritance and no silent coercion between
them.
"""

from bass.observer.adapters import apply_observer_boost, observed_alm_mixing
from bass.observer.aberration import aberration_kernel
from bass.observer.composition import GlobalTiltState, compose_tilts
from bass.observer.observer_boost import ObserverBoost

_DISCRIMINATOR_EXPORTS = {
    "CoverageReport",
    "DiscriminatorResult",
    "ObservedSpectrumDataset",
    "ObserverHypothesis",
    "TiltHypothesis",
    "coverage_report",
    "likelihood_ratio",
}

__all__ = [
    "ObserverBoost",
    "GlobalTiltState",
    "ObservedSpectrumDataset",
    "ObserverHypothesis",
    "TiltHypothesis",
    "CoverageReport",
    "DiscriminatorResult",
    "aberration_kernel",
    "apply_observer_boost",
    "compose_tilts",
    "coverage_report",
    "likelihood_ratio",
    "observed_alm_mixing",
]


def __getattr__(name: str) -> object:
    if name in _DISCRIMINATOR_EXPORTS:
        from bass.observer import discriminator as _discriminator

        return getattr(_discriminator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
