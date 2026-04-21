"""bass.observer — production observer-frame boost surfaces.

BF-06 narrows the package-root API to the production observer-side boost and
harmonic-mixing helpers only. Diagnostic composition and surrogate
discriminator routes remain available from their submodules, but they are no
longer promoted as canonical package-level exports.
"""

from bass.observer.adapters import apply_observer_boost, observed_alm_mixing
from bass.observer.aberration import aberration_kernel
from bass.observer.observer_boost import ObserverBoost

__all__ = [
    "ObserverBoost",
    "aberration_kernel",
    "apply_observer_boost",
    "observed_alm_mixing",
]
