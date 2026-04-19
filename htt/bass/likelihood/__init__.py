"""bass.likelihood — cosmological-frame likelihood scaffolding.

This package is introduced at FB-META-7 to host the spectrum-to-
likelihood surfaces that sit between the BASS spectrum stack and the
future observer-frame adapter planned for FB-8.
"""

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood
from bass.likelihood.htt_decomposition import build_htt_decomposition
from bass.likelihood.planck2018_flrw_match import (
    validate_planck2018_flrw_limit_match,
)

__all__ = [
    "CosmologicalFrameLikelihood",
    "build_htt_decomposition",
    "validate_planck2018_flrw_limit_match",
]
