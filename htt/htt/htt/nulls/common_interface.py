"""
htt/nulls/common_interface.py — Common Null Family Interface
=============================================================
P-14 deliverable. Abstract base for 5 adversarial null families.

Each null family simulates β_true = 0 datasets with a specific
structured systematic, then measures the false-positive rate
when the FLRW_tilt inference is applied.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np

__all__ = [
    'NullFamily', 'NullDataset', 'NullFamilyResult',
    'FalsePositiveRates',
]


@dataclass
class NullDataset:
    """A single synthetic null dataset.

    All fields match the ObsData interface in evidence_models.py.
    """
    seed: int
    family: str
    # Dipole channels
    e1_CW: float       # CatWISE dipole amplitude
    e1_CW_s: float     # statistical uncertainty
    e1_rad: float       # Radio dipole amplitude
    e1_rad_s: float
    rho_CW_radio: float # correlation
    # CF4 channel
    b_CF4: float
    b_CF4_s: float
    # CMB channels (unchanged from obs_defaults)
    eps2: float
    eps3: float
    # Injected systematic
    systematic_amplitude: float
    systematic_type: str


@dataclass
class NullFamilyResult:
    """Results from running inference on all null datasets in a family."""
    family: str
    n_datasets: int
    n_detections_Pi005: int  # Π(0.05) > 0.95
    n_detections_lnB5: int  # lnB > 5
    fp_rate_Pi005: float
    fp_rate_lnB5: float
    lnB_median: float
    lnB_std: float
    beta_median_mean: float


class FalsePositiveRates:
    """Collector for false-positive rates across all families."""

    def __init__(self):
        self.results: Dict[str, NullFamilyResult] = {}

    def add(self, result: NullFamilyResult):
        self.results[result.family] = result

    def to_dict(self) -> dict:
        return {
            name: {
                'n_datasets': r.n_datasets,
                'fp_rate_Pi005': r.fp_rate_Pi005,
                'fp_rate_lnB5': r.fp_rate_lnB5,
                'lnB_median': r.lnB_median,
                'lnB_std': r.lnB_std,
                'beta_median_mean': r.beta_median_mean,
            }
            for name, r in self.results.items()
        }

    @property
    def union_fp_Pi005(self) -> float:
        """Union false-positive rate: any family triggers."""
        # Conservative: 1 - prod(1 - fp_i)
        prod = 1.0
        for r in self.results.values():
            prod *= (1.0 - r.fp_rate_Pi005)
        return 1.0 - prod


class NullFamily(ABC):
    """Abstract base class for a structured null family."""

    name: str = "abstract"

    @abstractmethod
    def generate(self, seed: int, obs_base: dict) -> NullDataset:
        """Generate a single null dataset with β_true = 0 + systematic."""
        ...

    def generate_batch(self, n: int, obs_base: dict,
                       seed_offset: int = 0) -> list:
        """Generate n null datasets."""
        return [self.generate(seed_offset + i, obs_base)
                for i in range(n)]
