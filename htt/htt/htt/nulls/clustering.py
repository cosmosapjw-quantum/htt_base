"""
htt/nulls/clustering.py — Clustering-Dipole Null (N3, Bashir-type)
htt/nulls/response.py  — Selection-Response Null (N4)
htt/nulls/survey_axis.py — Survey-Axis Null (N5)
=================================================================
Combined file for efficiency. Each class is importable separately.
"""
import numpy as np
from .common_interface import NullFamily, NullDataset

__all__ = ['ClusteringDipoleNull', 'SelectionResponseNull', 'SurveyAxisNull']


class ClusteringDipoleNull(NullFamily):
    """N3: Clustering-dipole systematic (Bashir-type).

    Local large-scale structure creates a number-count dipole
    that mimics a kinematic signal. The amplitude is drawn from
    the clustering-dipole posterior of Bashir+2025.
    """
    name = "clustering_dipole"

    def __init__(self, A_clust_mean: float = 4e-4,
                 A_clust_std: float = 1.5e-4):
        self.A_clust_mean = A_clust_mean
        self.A_clust_std = A_clust_std

    def generate(self, seed: int, obs_base: dict) -> NullDataset:
        rng = np.random.default_rng(seed)
        A = max(rng.normal(self.A_clust_mean, self.A_clust_std), 0)

        cw = obs_base['dipole_observations']['catwise_bohme_2025']
        rad = obs_base['dipole_observations']['radio_secrest_2021']
        cf4 = obs_base['dipole_observations']['cf4_watkins_2023']

        e1_CW = abs(rng.normal(A, cw['sigma_stat']))
        e1_rad = abs(rng.normal(A * 0.7, rad['sigma_stat']))
        # Clustering affects CF4 bulk flow too (local structure)
        b_CF4 = abs(rng.normal(A * 0.3, cf4['sigma']))

        return NullDataset(
            seed=seed, family=self.name,
            e1_CW=e1_CW, e1_CW_s=cw['sigma_stat'],
            e1_rad=e1_rad, e1_rad_s=rad['sigma_stat'],
            rho_CW_radio=0.2,
            b_CF4=b_CF4, b_CF4_s=cf4['sigma'],
            eps2=3.56e-6, eps3=6.07e-6,
            systematic_amplitude=A,
            systematic_type='clustering_dipole',
        )


class SelectionResponseNull(NullFamily):
    """N4: Selection-response systematic.

    Redshift-dependent selection function creates an apparent
    dipole through anisotropic completeness. Models the
    von Hausegger & Dalang (2025) selection-effect mechanism.
    """
    name = "selection_response"

    def __init__(self, A_sel_mean: float = 2e-4,
                 A_sel_std: float = 1e-4):
        self.A_sel_mean = A_sel_mean
        self.A_sel_std = A_sel_std

    def generate(self, seed: int, obs_base: dict) -> NullDataset:
        rng = np.random.default_rng(seed)
        A = max(rng.normal(self.A_sel_mean, self.A_sel_std), 0)

        cw = obs_base['dipole_observations']['catwise_bohme_2025']
        rad = obs_base['dipole_observations']['radio_secrest_2021']
        cf4 = obs_base['dipole_observations']['cf4_watkins_2023']

        e1_CW = abs(rng.normal(A, cw['sigma_stat']))
        # Radio less affected (different selection function)
        e1_rad = abs(rng.normal(A * 0.3, rad['sigma_stat']))
        b_CF4 = abs(rng.normal(0, cf4['sigma']))

        return NullDataset(
            seed=seed, family=self.name,
            e1_CW=e1_CW, e1_CW_s=cw['sigma_stat'],
            e1_rad=e1_rad, e1_rad_s=rad['sigma_stat'],
            rho_CW_radio=0.1,
            b_CF4=b_CF4, b_CF4_s=cf4['sigma'],
            eps2=3.56e-6, eps3=6.07e-6,
            systematic_amplitude=A,
            systematic_type='selection_response',
        )


class SurveyAxisNull(NullFamily):
    """N5: Survey-axis systematic.

    Common sky coverage between CatWISE and Radio creates
    correlated systematics. Models shared ecliptic-latitude
    and declination dependencies.
    """
    name = "survey_axis"

    def __init__(self, rho_shared: float = 0.5,
                 A_axis_mean: float = 3e-4):
        self.rho_shared = rho_shared
        self.A_axis_mean = A_axis_mean

    def generate(self, seed: int, obs_base: dict) -> NullDataset:
        rng = np.random.default_rng(seed)

        cw = obs_base['dipole_observations']['catwise_bohme_2025']
        rad = obs_base['dipole_observations']['radio_secrest_2021']
        cf4 = obs_base['dipole_observations']['cf4_watkins_2023']

        # Generate correlated CW + Radio systematics
        A_common = rng.normal(self.A_axis_mean, 1e-4)
        A_cw = A_common + rng.normal(0, 1e-4)
        A_rad = A_common + rng.normal(0, 1.5e-4)

        e1_CW = abs(A_cw + rng.normal(0, cw['sigma_stat']))
        e1_rad = abs(A_rad + rng.normal(0, rad['sigma_stat']))
        b_CF4 = abs(rng.normal(0, cf4['sigma']))

        return NullDataset(
            seed=seed, family=self.name,
            e1_CW=e1_CW, e1_CW_s=cw['sigma_stat'],
            e1_rad=e1_rad, e1_rad_s=rad['sigma_stat'],
            rho_CW_radio=self.rho_shared,
            b_CF4=b_CF4, b_CF4_s=cf4['sigma'],
            eps2=3.56e-6, eps3=6.07e-6,
            systematic_amplitude=abs(A_common),
            systematic_type='survey_axis',
        )
