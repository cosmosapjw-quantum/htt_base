"""
Phase 5: Species-relative tilt (placeholder).

Multi-fluid extension: β_baryon - β_CDM - β_neutrino.
This is an open calculation (cf. ch02_sec8_multi_fluid.tex).

Phase 5 status: STUB — awaiting multi-fluid solver extension.
"""
from dataclasses import dataclass
from typing import Optional
import numpy as np

__all__ = ['SpeciesRelativeTilt', 'NOT_IMPLEMENTED_MSG']

NOT_IMPLEMENTED_MSG = (
    "Species-relative tilt requires the multi-fluid extension "
    "(cf. §2.8, Proposition: single-fluid boundary). "
    "The single-fluid safe-route mappings are not automatically "
    "portable to generic multi-fluid models."
)

@dataclass(frozen=True)
class SpeciesRelativeTilt:
    """Placeholder for multi-fluid species-relative tilt."""
    beta_baryon: Optional[float] = None
    beta_CDM: Optional[float] = None
    beta_neutrino: Optional[float] = None
    delta_beta_bCDM: Optional[float] = None
    status: str = 'NOT_ESTABLISHED'
    message: str = NOT_IMPLEMENTED_MSG
