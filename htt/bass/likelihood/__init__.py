"""bass.likelihood — cosmological-frame likelihood scaffolding.

This package is introduced at FB-META-7 to host the spectrum-to-
likelihood surfaces that sit between the BASS spectrum stack and the
future observer-frame adapter planned for FB-8.
"""

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood
from bass.likelihood.htt_decomposition import build_htt_decomposition
from bass.likelihood.observer_frame_adapter import ObserverFrameLikelihood

__all__ = [
    "CosmologicalFrameLikelihood",
    "ObserverFrameLikelihood",
    "build_htt_decomposition",
]
