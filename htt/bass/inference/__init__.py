"""bass.inference — FB-11 inference scaffolding.

This package is introduced at FB-META-11 for inference-only contracts.
During the skeleton cycle, public surfaces document the future posterior
and evidence workflow but raise `NotImplementedError` rather than
opening a fake sampling path.
"""

from bass.inference.priors import (
    Prior,
    prior_direction,
    prior_observer_boost,
    prior_rapidity,
    prior_structure_constants,
    prior_Sigma_mnu,
)

__all__ = [
    "Prior",
    "prior_rapidity",
    "prior_direction",
    "prior_Sigma_mnu",
    "prior_observer_boost",
    "prior_structure_constants",
]
