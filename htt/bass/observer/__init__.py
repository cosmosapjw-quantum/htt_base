"""bass.observer — observer-frame boost and discriminator scaffolding.

This package is introduced at FB-META-8 for *observer-frame* surfaces
only. Cosmological tilt and observer boost remain type-distinct:
``(beta_cosmo, v_hat_cosmo)`` and ``(beta_obs, v_hat_obs)`` are owned by
separate modules, with no inheritance and no silent coercion between
them.
"""

from bass.observer.aberration import aberration_kernel
from bass.observer.observer_boost import ObserverBoost

__all__ = ["ObserverBoost", "aberration_kernel"]
