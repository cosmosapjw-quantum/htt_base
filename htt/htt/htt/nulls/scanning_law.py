"""
htt/nulls/scanning_law.py — WISE Scanning-Law Null (N1)
========================================================
Simulates ecliptic-latitude-dependent CatWISE dipole bias from
the WISE scanning pattern. Models the Bashir+2025 SBI finding.
"""
import numpy as np
from .common_interface import NullFamily, NullDataset

__all__ = ['ScanningLawNull']


class ScanningLawNull(NullFamily):
    """N1: WISE scanning-law systematic.

    The scanning pattern creates a spurious dipole aligned with
    the ecliptic poles. Amplitude A_scan is drawn from a prior
    calibrated to the Bashir+2025 SBI forward model.
    """
    name = "scanning_law"

    def __init__(self, A_scan_mean: float = 3e-4,
                 A_scan_std: float = 1e-4):
        self.A_scan_mean = A_scan_mean
        self.A_scan_std = A_scan_std

    def generate(self, seed: int, obs_base: dict) -> NullDataset:
        rng = np.random.default_rng(seed)
        A = rng.normal(self.A_scan_mean, self.A_scan_std)
        A = max(A, 0)  # non-negative amplitude

        cw = obs_base['dipole_observations']['catwise_bohme_2025']
        rad = obs_base['dipole_observations']['radio_secrest_2021']

        # CatWISE: inject scanning-law dipole (β_true = 0)
        e1_CW = A + rng.normal(0, cw['sigma_stat'])
        e1_CW = max(e1_CW, 0)

        # Radio: unaffected by WISE scanning
        e1_rad = abs(rng.normal(0, rad['sigma_stat']))

        return NullDataset(
            seed=seed, family=self.name,
            e1_CW=e1_CW, e1_CW_s=cw['sigma_stat'],
            e1_rad=e1_rad, e1_rad_s=rad['sigma_stat'],
            rho_CW_radio=0.1,
            # Legacy interface placeholders. Channel c is disabled and is
            # never read by the active null runner.
            b_CF4=0.0, b_CF4_s=np.inf,
            eps2=3.56e-6, eps3=6.07e-6,
            systematic_amplitude=A,
            systematic_type='scanning_law',
        )
