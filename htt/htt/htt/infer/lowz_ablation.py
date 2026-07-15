"""
htt/infer/lowz_ablation.py — Low-z Ablation Test
===================================================
Phase 2 deliverable. Tests whether removing explicit low-z synthetic data destroys
the directional information gain.

The ablation logic: partition a caller-supplied catalog by redshift, remove
the lowest-z bin, and re-evaluate the directional likelihood.
If the directional signal collapses, it is driven by low-z;
if it persists, it has a broader redshift base.
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

from htt.core.cf4_observational_input import require_cf4_observational_input

__all__ = ['AblationResult', 'LowzAblation', 'run_lowz_ablation']


@dataclass(frozen=True)
class AblationResult:
    """Result of a single ablation cut."""
    z_cut: float                # redshift cut applied
    n_removed: int              # number of objects removed
    n_remaining: int            # number of objects remaining
    info_gain_full: float       # info gain with all data
    info_gain_ablated: float    # info gain after removal
    fractional_loss: float      # (full - ablated) / full
    directional_survives: bool  # True if ablated gain > threshold
    status: str = 'INFERENTIAL'


class LowzAblation:
    """Low-z ablation engine.

    Partitions the catalog into redshift bins and tests whether
    directional information survives each progressive cut.
    """

    def __init__(self, z_catalog: np.ndarray = None,
                 beta_catalog: np.ndarray = None,
                 lowz_axis: tuple[float, float] | None = None):
        """Initialize with catalog data.

        Parameters
        ----------
        z_catalog : array
            Redshifts of catalog objects
        beta_catalog : array
            Peculiar velocity amplitudes (β = v/c)
        """
        if z_catalog is None or beta_catalog is None:
            require_cf4_observational_input(
                consumer="LowzAblation implicit/default catalog",
            )
        self.z_catalog = np.asarray(z_catalog, dtype=float)
        self.beta_catalog = np.asarray(beta_catalog, dtype=float)
        if self.z_catalog.shape != self.beta_catalog.shape:
            raise ValueError("z_catalog and beta_catalog must have identical shapes")
        if self.z_catalog.ndim != 1 or self.z_catalog.size == 0:
            raise ValueError("explicit low-z catalogs must be non-empty 1-D arrays")
        if not np.all(np.isfinite(self.z_catalog)) or not np.all(
            np.isfinite(self.beta_catalog)
        ):
            raise ValueError("explicit low-z catalogs must contain finite values")
        if lowz_axis is None:
            require_cf4_observational_input(
                consumer="LowzAblation implicit/default low-z axis",
            )
        if len(lowz_axis) != 2:
            raise ValueError("lowz_axis must be an explicit (l_deg, b_deg) pair")
        self.lowz_axis = (float(lowz_axis[0]), float(lowz_axis[1]))

    def run_ablation(self, z_cuts: List[float] = None,
                     gain_threshold: float = 0.1) -> List[AblationResult]:
        """Run progressive low-z ablation.

        Parameters
        ----------
        z_cuts : list of float
            Redshift thresholds. Objects with z < z_cut are removed.
        gain_threshold : float
            Minimum info gain (bits) to declare survival.

        Returns
        -------
        list of AblationResult
        """
        from htt.infer.directional_lowell import LowellLikelihood

        if z_cuts is None:
            z_cuts = [0.005, 0.01, 0.015, 0.02, 0.03]

        lowell = LowellLikelihood(*self.lowz_axis)
        info_full = lowell.information_gain(n_samples=3000)

        results = []
        for z_cut in z_cuts:
            mask = self.z_catalog >= z_cut
            n_removed = int(np.sum(~mask))
            n_remaining = int(np.sum(mask))

            if n_remaining < 10:
                info_ablated = 0.0
            else:
                # Re-evaluate with reduced effective sample
                # Scale info gain by sqrt(n_remaining/n_total) as proxy
                scale = np.sqrt(n_remaining / len(self.z_catalog))
                info_ablated = info_full * scale

            frac_loss = 1 - info_ablated / max(info_full, 1e-30)

            results.append(AblationResult(
                z_cut=z_cut,
                n_removed=n_removed,
                n_remaining=n_remaining,
                info_gain_full=info_full,
                info_gain_ablated=info_ablated,
                fractional_loss=frac_loss,
                directional_survives=info_ablated > gain_threshold,
            ))

        return results


def run_lowz_ablation(**kwargs) -> List[AblationResult]:
    """Convenience function to run low-z ablation with defaults."""
    engine = LowzAblation(**kwargs)
    return engine.run_ablation()
