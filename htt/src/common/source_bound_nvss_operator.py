"""Source-bound observation operator for Northern Radio NVSS (1.4 GHz) Count Dipole.

Binds the exact NVSS dataset:
- nvss.dat.gz from /mnt/extdrive/workdir/raw/observational_bundles/NVSS/ (or htt_open_data)
- Direct declination cut: delta > -40 deg, Galactic cut |b| > 10 deg, flux threshold S > 20 mJy
- Computes measured count dipole vector D_obs, window matrix W, and shot-noise covariance
- Ellis-Baldwin response: D_model = [2 + x*(1 + alpha)] * beta_MO with NVSS x ~ 1.0, alpha ~ 0.75 => C_EB ~ 3.75
"""

from __future__ import annotations

import os
import gzip
import numpy as np
from typing import Tuple, Optional

NVSS_CANDIDATE_PATHS = [
    "/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS/nvss.dat.gz",
    "/mnt/extdrive/workdir/htt_open_data/nvss/nvss.dat.gz",
    "/mnt/extdrive/workdir/raw/observational_bundles/NVSS/nvss.dat.gz",
]
NVSS_CAT_PATH = next((p for p in NVSS_CANDIDATE_PATHS if os.path.exists(p)), NVSS_CANDIDATE_PATHS[0])



class SourceBoundNVSSOperator:
    """Source-bound observation operator for NVSS 1.4 GHz Count Dipole."""

    def __init__(
        self,
        cat_path: str = NVSS_CAT_PATH,
        s_min_mjy: float = 20.0,
        b_cut_deg: float = 10.0,
    ) -> None:
        self.cat_path = cat_path
        self.s_min_mjy = s_min_mjy
        self.b_cut_deg = b_cut_deg

        self._load_and_compute_dipole()

    def _load_and_compute_dipole(self) -> None:
        """Parse NVSS catalog, apply cuts, and compute decoupled dipole vector."""
        if not os.path.exists(self.cat_path):
            raise FileNotFoundError(f"NVSS catalog not found at {self.cat_path}")

        ra_list = []
        dec_list = []

        # Parse fixed-width NVSS catalog
        with gzip.open(self.cat_path, "rt", encoding="ascii", errors="ignore") as f:
            for line in f:
                try:
                    s14 = float(line[75:83])
                    if s14 < self.s_min_mjy:
                        continue
                    rah = int(line[40:42])
                    ram = int(line[43:45])
                    ras = float(line[46:51])
                    ra = (rah + ram / 60.0 + ras / 3600.0) * 15.0
                    de_sgn = -1.0 if line[52] == '-' else 1.0
                    ded = int(line[53:55])
                    dem = int(line[56:58])
                    des = float(line[59:63])
                    dec = de_sgn * (ded + dem / 60.0 + des / 3600.0)
                    if dec > -40.0:
                        ra_list.append(ra)
                        dec_list.append(dec)
                except Exception:
                    continue

        self.n_sources = len(ra_list)
        assert self.n_sources > 100000, f"Too few NVSS sources: {self.n_sources}"

        ra_rad = np.deg2rad(np.array(ra_list))
        dec_rad = np.deg2rad(np.array(dec_list))

        # Galactic latitude cut: |b| > b_cut_deg
        sin_b = (
            np.sin(dec_rad) * np.sin(np.deg2rad(27.12825))
            + np.cos(dec_rad) * np.cos(np.deg2rad(27.12825)) * np.cos(ra_rad - np.deg2rad(192.85948))
        )
        b_rad = np.arcsin(np.clip(sin_b, -1.0, 1.0))
        gal_mask = np.abs(np.rad2deg(b_rad)) >= self.b_cut_deg

        self.n_selected = int(np.sum(gal_mask))
        ra_sel = ra_rad[gal_mask]
        dec_sel = dec_rad[gal_mask]

        # Unit vectors for data
        n_hat = np.column_stack([
            np.cos(dec_sel) * np.cos(ra_sel),
            np.cos(dec_sel) * np.sin(ra_sel),
            np.sin(dec_sel)
        ])

        # Geometric footprint Monte Carlo for mask subtraction
        rng = np.random.RandomState(42)
        n_mc = 2000000
        ra_mc = rng.uniform(0.0, 2.0 * np.pi, n_mc)
        sin_dec_min = np.sin(np.deg2rad(-40.0))
        sin_dec_mc = rng.uniform(sin_dec_min, 1.0, n_mc)
        dec_mc = np.arcsin(sin_dec_mc)

        sin_b_mc = (
            np.sin(dec_mc) * np.sin(np.deg2rad(27.12825))
            + np.cos(dec_mc) * np.cos(np.deg2rad(27.12825)) * np.cos(ra_mc - np.deg2rad(192.85948))
        )
        gal_mask_mc = np.abs(np.rad2deg(np.arcsin(np.clip(sin_b_mc, -1.0, 1.0)))) >= self.b_cut_deg

        ra_mc_sel = ra_mc[gal_mask_mc]
        dec_mc_sel = dec_mc[gal_mask_mc]
        n_mc_sel = len(ra_mc_sel)

        n_hat_mc = np.column_stack([
            np.cos(dec_mc_sel) * np.cos(ra_mc_sel),
            np.cos(dec_mc_sel) * np.sin(ra_mc_sel),
            np.sin(dec_mc_sel)
        ])

        # Geometry window matrix from unmasked footprint
        W_mat = (3.0 / n_mc_sel) * (n_hat_mc.T @ n_hat_mc)
        inv_W = np.linalg.inv(W_mat)

        # Raw pseudo-dipoles
        d_data = (3.0 / self.n_selected) * np.sum(n_hat, axis=0)
        d_mask = (3.0 / n_mc_sel) * np.sum(n_hat_mc, axis=0)

        # Net physical dipole (mask-corrected)
        self.D_obs = inv_W @ (d_data - d_mask)
        self.amp_obs = float(np.linalg.norm(self.D_obs))

        # Shot-noise + LSS cosmic covariance
        Cov_shot = (9.0 / (self.n_selected ** 2)) * (n_hat.T @ n_hat)
        Cov_lss = (2.5e-3 ** 2) * np.eye(3)
        self.cov_D = inv_W @ Cov_shot @ inv_W.T + Cov_lss
        self.inv_cov_D = np.linalg.inv(self.cov_D)
        self.cho_cov_D = np.linalg.cholesky(self.cov_D)

        # NVSS Ellis-Baldwin coefficient: C_EB ~ 3.75
        self.C_EB = 3.75

    def evaluate_model(self, beta_MO: np.ndarray) -> Tuple[float, float]:
        """Compute chi2 and log-likelihood under matter-observer boost beta_MO."""
        D_pred = self.C_EB * beta_MO
        res = self.D_obs - D_pred

        chi2 = float(res.T @ self.inv_cov_D @ res)
        log_det = float(2.0 * np.sum(np.log(np.diag(self.cho_cov_D))))
        log_like = -0.5 * (chi2 + log_det + 3.0 * np.log(2.0 * np.pi))

        return chi2, log_like

