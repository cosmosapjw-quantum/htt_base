"""ver3 hierarchy state split contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

__all__ = [
    "HierarchyState",
]


@dataclass(frozen=True)
class HierarchyState:
    """Document-level hierarchy split frozen by the ver3 numerical SSOT."""

    matter_block: Mapping[str, object]
    photon_intensity_block: np.ndarray
    photon_polarization_block: Mapping[str, np.ndarray]
    neutrino_block: np.ndarray
    source_history_block: Mapping[str, object]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        photon_intensity = np.asarray(self.photon_intensity_block, dtype=np.float64)
        neutrino = np.asarray(self.neutrino_block, dtype=np.float64)
        polarization = {
            key: np.asarray(value, dtype=np.float64)
            for key, value in dict(self.photon_polarization_block).items()
        }
        object.__setattr__(self, "matter_block", dict(self.matter_block))
        object.__setattr__(self, "photon_intensity_block", photon_intensity)
        object.__setattr__(self, "photon_polarization_block", polarization)
        object.__setattr__(self, "neutrino_block", neutrino)
        object.__setattr__(self, "source_history_block", dict(self.source_history_block))
        object.__setattr__(self, "metadata", dict(self.metadata))
