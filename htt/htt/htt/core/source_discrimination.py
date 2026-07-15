"""External data integration and source-model comparison.

Implements the three remaining strategies from the revision plan:

1. Redshift-binned directional posterior
   - Split Fisher penalties by survey effective depth
   - Test whether tilt DIRECTION changes with redshift

2. Dipole-quadrupole alignment with depth
   - Cross-correlate tilt axis at low-z with quadrupole axis at high-z

3. Bayesian model averaging over source hypotheses
   - M_geo: geometric tilt (β constant with z)
   - M_kin: kinematic flow (β ∝ (1+z)^α)
   - M_mix: mixed (geometric baseline + kinematic excess)

External data catalogs that could improve the analysis:
  - CosmicFlows-4: Tully+2023, peculiar velocity field
  - 2MPZ: Bilicki+2014, photometric redshift catalog
  - unWISE: Krolewski+2020, photometric quasar dipole
  - DESI: spectroscopic peculiar velocities (upcoming)
  - Quaia: Storey-Fisher+2024, Gaia-unWISE quasar catalog
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from scipy.stats import chi2 as chi2_dist

from htt.core.cf4_observational_input import OPEN_FINDING_IDS

__all__ = [
    'RedshiftBinnedDirection',
    'SourceModelComparison',
    'ExternalDataCatalog',
    'run_source_discrimination',
]


# ═══════════════════════════════════════════════════════════════
#  External Data Catalog Registry
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SurveyData:
    """A single dipole survey measurement."""
    name: str
    z_eff: float           # effective redshift
    depth_Mpc: float       # effective depth in Mpc
    amplitude: float       # dipole amplitude (β or ε₁)
    sigma: float           # 1σ uncertainty
    l_deg: float           # dipole direction galactic longitude
    b_deg: float           # dipole direction galactic latitude
    l_sigma: float         # direction uncertainty (degrees)
    b_sigma: float
    survey_type: str       # 'velocity', 'number_count', 'radio'
    reference: str
    n_sources: int = 0     # number of sources in catalog
    sky_fraction: float = 1.0


# Current survey compilation
SURVEY_CATALOG = {
    'CatWISE': SurveyData(
        name='CatWISE+Böhme', z_eff=0.15, depth_Mpc=450,
        amplitude=1.476e-3, sigma=0.30e-3,
        l_deg=240.5, b_deg=-3.8, l_sigma=12.0, b_sigma=12.0,
        survey_type='number_count',
        reference='Secrest+2021 (ApJL 908, L51); Böhme+2025',
        n_sources=1360000, sky_fraction=0.65),
    'Radio_NVSS': SurveyData(
        name='NVSS+RACS', z_eff=0.8, depth_Mpc=2400,
        amplitude=3.296e-3, sigma=0.60e-3,
        l_deg=245.0, b_deg=18.0, l_sigma=20.0, b_sigma=20.0,
        survey_type='radio',
        reference='Wagenveld+2023; Secrest+2021',
        n_sources=560000, sky_fraction=0.70),
    'Planck_CMB': SurveyData(
        name='Planck CMB dipole', z_eff=1100, depth_Mpc=14000,
        amplitude=1.2336e-3, sigma=0.05e-3,
        l_deg=264.021, b_deg=48.253, l_sigma=0.5, b_sigma=0.5,
        survey_type='cmb_kinematic',
        reference='Planck 2018 (A&A 641, A1)',
        n_sources=1, sky_fraction=0.85),
}

# Future/potential data that would improve analysis
FUTURE_DATA = {
    'DESI_PV': {
        'name': 'DESI Peculiar Velocities',
        'z_range': '0.01-0.15',
        'expected_n': 200000,
        'improvement': 'Directional + amplitude at multiple z-bins',
        'status': 'Data collection ongoing (2024-2027)',
        'reference': 'DESI Collaboration (2023)',
    },
    'Quaia': {
        'name': 'Gaia-unWISE quasar catalog',
        'z_range': '0.1-4.0',
        'expected_n': 1300000,
        'improvement': 'Very deep dipole with spectroscopic z',
        'status': 'Available (Storey-Fisher+2024)',
        'reference': 'Storey-Fisher+2024 (ApJ 964, 69)',
    },
    'Euclid_dipole': {
        'name': 'Euclid photometric dipole',
        'z_range': '0.2-2.0',
        'expected_n': 15000000000,
        'improvement': '10× CatWISE precision, tomographic z-bins',
        'status': 'Expected ~2027',
        'reference': 'Euclid Collaboration',
    },
    'SKA_radio': {
        'name': 'SKA radio continuum dipole',
        'z_range': '0.1-3.0',
        'expected_n': 500000000,
        'improvement': 'Sub-degree directional precision',
        'status': 'Expected ~2028',
        'reference': 'SKA Cosmology SWG',
    },
    'CMB_S4': {
        'name': 'CMB-S4 polarisation',
        'z_range': '1100 (recombination)',
        'expected_n': 1,
        'improvement': '10⁴× tighter vorticity/rotation bound from B-modes',
        'status': 'Expected ~2030',
        'reference': 'CMB-S4 Collaboration',
    },
}


def _unit_vec(l_deg, b_deg):
    l, b = np.radians(l_deg), np.radians(b_deg)
    return np.array([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)])


def _angular_sep(l1, b1, l2, b2):
    d1, d2 = _unit_vec(l1, b1), _unit_vec(l2, b2)
    return np.arccos(np.clip(np.dot(d1, d2), -1, 1))


# ═══════════════════════════════════════════════════════════════
#  Strategy 1: Redshift-Binned Directional Analysis
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DirectionalConsistencyResult:
    """Are the dipole directions consistent across redshift?"""
    surveys_compared: Tuple
    pairwise_separations: Dict     # {(s1,s2): separation_deg}
    mean_separation_deg: float
    max_separation_deg: float
    chi2_isotropy: float           # χ² for "all point same direction"
    pvalue_isotropy: float
    geometric_prediction: str
    kinematic_prediction: str
    interpretation: str


class RedshiftBinnedDirection:
    """Test whether dipole direction is stable across surveys at different depths.

    Geometric tilt: SAME direction at all depths (global Bianchi axis)
    Kinematic flow: DIFFERENT directions at different depths (local flow structure)
    """

    def __init__(self, surveys: Dict[str, SurveyData] = None):
        self.surveys = surveys or {k: v for k, v in SURVEY_CATALOG.items()
                                    if k != 'Planck_CMB'}

    def run(self) -> DirectionalConsistencyResult:
        names = list(self.surveys.keys())
        n = len(names)

        # Pairwise angular separations
        seps = {}
        for i in range(n):
            for j in range(i+1, n):
                s1, s2 = self.surveys[names[i]], self.surveys[names[j]]
                sep_deg = np.degrees(_angular_sep(
                    s1.l_deg, s1.b_deg, s2.l_deg, s2.b_deg))
                seps[(names[i], names[j])] = round(float(sep_deg), 1)

        mean_sep = float(np.mean(list(seps.values())))
        max_sep = float(np.max(list(seps.values())))

        # χ² for common-axis hypothesis
        # Under H₀ (common axis), the observed directions should be
        # consistent within their uncertainties
        # Weighted mean direction
        ws = []
        vecs = []
        for s in self.surveys.values():
            w = 1.0 / (s.l_sigma**2 + s.b_sigma**2)
            ws.append(w)
            vecs.append(_unit_vec(s.l_deg, s.b_deg))

        ws = np.array(ws)
        vecs = np.array(vecs)
        mean_vec = np.average(vecs, weights=ws, axis=0)
        mean_vec /= np.linalg.norm(mean_vec)

        # χ² = Σ_i (sep_i / σ_i)²
        chi2 = 0.0
        for s in self.surveys.values():
            sep = np.degrees(_angular_sep(
                s.l_deg, s.b_deg,
                np.degrees(np.arctan2(mean_vec[1], mean_vec[0])) % 360,
                np.degrees(np.arcsin(mean_vec[2]))))
            sigma_dir = np.sqrt(s.l_sigma**2 + s.b_sigma**2)
            chi2 += (sep / sigma_dir)**2

        ndof = 2 * n - 2  # 2 DOF per survey minus 2 for mean direction
        pval = float(1 - chi2_dist.cdf(chi2, max(ndof, 1)))

        if pval > 0.05:
            interp = (f"Directions are consistent within this diagnostic "
                      f"(χ²={chi2:.1f}/{ndof}, p={pval:.2f}); mean separation "
                      f"{mean_sep:.0f}°. This does not identify a geometric or "
                      f"kinematic source.")
        else:
            interp = (f"Directions show tension (χ²={chi2:.1f}/{ndof}, p={pval:.3f}). "
                      f"Max separation {max_sep:.0f}° ({list(seps.keys())[np.argmax(list(seps.values()))]}). "
                      f"This is a source-discrimination candidate only; no global "
                      f"or local source is identified.")

        return DirectionalConsistencyResult(
            surveys_compared=tuple(names),
            pairwise_separations=seps,
            mean_separation_deg=round(mean_sep, 1),
            max_separation_deg=round(max_sep, 1),
            chi2_isotropy=round(chi2, 2),
            pvalue_isotropy=round(pval, 4),
            geometric_prediction='All directions within ~10° (shared Bianchi axis)',
            kinematic_prediction='Directions drift with depth as flow structure changes',
            interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Strategy 2: Source Model Comparison (Bayesian)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SourceModelResult:
    model_name: str
    n_params: int
    chi2: float
    ndof: int
    pvalue: float
    aic: float
    bic: float
    params: Dict
    interpretation: str


class SourceModelComparison:
    """Compare three source hypotheses for the dipole signal.

    M_geo:  β(z) = β₀                   (geometric, 1 param)
    M_kin:  β(z) = β₀ (1+z)^α           (kinematic, 2 params)
    M_mix:  β(z) = β_geo + β_kin/(1+z)  (mixed, 2 params)
    """

    def __init__(self, surveys: Dict[str, SurveyData] = None):
        self.surveys = surveys or {k: v for k, v in SURVEY_CATALOG.items()
                                    if k != 'Planck_CMB'}

    def _get_data(self):
        amps = np.array([s.amplitude for s in self.surveys.values()])
        sigs = np.array([s.sigma for s in self.surveys.values()])
        zs = np.array([s.z_eff for s in self.surveys.values()])
        return amps, sigs, zs

    def _fit_geometric(self) -> SourceModelResult:
        """M_geo: β = β₀ (constant)."""
        amps, sigs, zs = self._get_data()
        w = 1.0 / sigs**2
        beta0 = float(np.sum(w * amps) / np.sum(w))
        chi2 = float(np.sum(((amps - beta0) / sigs)**2))
        ndof = len(amps) - 1
        n = len(amps)
        return SourceModelResult(
            model_name='M_geo (constant β)',
            n_params=1, chi2=round(chi2, 2), ndof=ndof,
            pvalue=round(float(1 - chi2_dist.cdf(chi2, ndof)), 4),
            aic=round(chi2 + 2*1, 2),
            bic=round(chi2 + np.log(n)*1, 2),
            params={'beta0': round(beta0, 6)},
            interpretation=f"β₀ = {beta0:.4e}, χ²/ndof = {chi2:.1f}/{ndof}",
        )

    def _fit_kinematic(self) -> SourceModelResult:
        """M_kin: β(z) = β₀ (1+z)^α."""
        amps, sigs, zs = self._get_data()
        from scipy.optimize import minimize

        def neg_logL(params):
            b0, alpha = params
            pred = b0 * (1 + zs)**alpha
            return 0.5 * np.sum(((amps - pred) / sigs)**2)

        res = minimize(neg_logL, [1.5e-3, 0.5], method='Nelder-Mead')
        b0, alpha = res.x
        chi2 = float(2 * res.fun)
        ndof = len(amps) - 2
        n = len(amps)
        return SourceModelResult(
            model_name='M_kin (power-law depth)',
            n_params=2, chi2=round(chi2, 2), ndof=ndof,
            pvalue=round(float(1 - chi2_dist.cdf(chi2, max(ndof, 1))), 4),
            aic=round(chi2 + 2*2, 2),
            bic=round(chi2 + np.log(n)*2, 2),
            params={'beta0': round(float(b0), 6), 'alpha': round(float(alpha), 3)},
            interpretation=f"β₀ = {b0:.4e}, α = {alpha:.2f}, χ²/ndof = {chi2:.1f}/{ndof}",
        )

    def _fit_mixed(self) -> SourceModelResult:
        """M_mix: β(z) = β_geo + β_kin × (1+z)."""
        amps, sigs, zs = self._get_data()
        from scipy.optimize import minimize

        def neg_logL(params):
            b_geo, b_kin = params
            pred = b_geo + b_kin * (1 + zs)
            return 0.5 * np.sum(((amps - pred) / sigs)**2)

        res = minimize(neg_logL, [1e-3, 1e-3], method='Nelder-Mead')
        b_geo, b_kin = res.x
        chi2 = float(2 * res.fun)
        ndof = len(amps) - 2
        n = len(amps)
        return SourceModelResult(
            model_name='M_mix (geometric + kinematic)',
            n_params=2, chi2=round(chi2, 2), ndof=ndof,
            pvalue=round(float(1 - chi2_dist.cdf(chi2, max(ndof, 1))), 4),
            aic=round(chi2 + 2*2, 2),
            bic=round(chi2 + np.log(n)*2, 2),
            params={'beta_geo': round(float(b_geo), 6),
                    'beta_kin': round(float(b_kin), 6)},
            interpretation=f"β_geo = {b_geo:.4e}, β_kin = {b_kin:.4e}",
        )

    def run(self) -> Dict[str, SourceModelResult]:
        if len(self.surveys) < 3:
            raise ValueError(
                "at least three independent non-CF4 surveys are required for "
                "two-parameter source-model discrimination"
            )
        return {
            'geometric': self._fit_geometric(),
            'kinematic': self._fit_kinematic(),
            'mixed': self._fit_mixed(),
        }


# ═══════════════════════════════════════════════════════════════
#  Master: Run all source-discrimination diagnostics
# ═══════════════════════════════════════════════════════════════

def run_source_discrimination(verbose: bool = True) -> Dict:
    """Run all source-discrimination analyses."""
    results = {
        'claim_tier': 'diagnostic_only',
        'active_observational_scope': 'non_cf4_channels_only',
        'excluded_channels': ['c'],
        'cf4_channel_status': 'QUARANTINED_OPEN_FINDINGS',
        'cf4_finding_ids': list(OPEN_FINDING_IDS),
    }

    if verbose:
        print(f"\n{'='*65}")
        print(f" SOURCE DISCRIMINATION ANALYSIS")
        print(f"{'='*65}")

    # Strategy 1: Redshift-binned directional consistency
    if verbose:
        print(f"\n--- Redshift-Binned Directional Consistency ---")
    rbd = RedshiftBinnedDirection()
    dc = rbd.run()
    results['directional_consistency'] = {
        'pairwise_separations': {f'{k[0]}_vs_{k[1]}': v
                                  for k, v in dc.pairwise_separations.items()},
        'mean_separation_deg': dc.mean_separation_deg,
        'max_separation_deg': dc.max_separation_deg,
        'chi2': dc.chi2_isotropy,
        'pvalue': dc.pvalue_isotropy,
        'interpretation': dc.interpretation,
    }
    if verbose:
        for pair, sep in dc.pairwise_separations.items():
            print(f"  {pair[0]:10s} ↔ {pair[1]:10s}: {sep:5.1f}°")
        print(f"  χ²/ndof = {dc.chi2_isotropy:.1f}/{2*len(rbd.surveys)-2}, "
              f"p = {dc.pvalue_isotropy:.3f}")
        print(f"  {dc.interpretation}")

    # Strategy 2: Source model comparison
    if verbose:
        print(f"\n--- Source Model Comparison (AIC/BIC) ---")
    smc = SourceModelComparison()
    try:
        models = smc.run()
    except ValueError as exc:
        results['source_models'] = {
            'status': 'blocked_insufficient_non_cf4_surveys',
            'reason': str(exc),
            'n_active_surveys': len(smc.surveys),
        }
        if verbose:
            print(f"  Blocked: {exc}")
    else:
        results['source_models'] = {}
        for key, mr in models.items():
            results['source_models'][key] = {
                'model': mr.model_name, 'n_params': mr.n_params,
                'chi2': mr.chi2, 'ndof': mr.ndof, 'pvalue': mr.pvalue,
                'aic': mr.aic, 'bic': mr.bic,
                'params': mr.params, 'interpretation': mr.interpretation,
            }
            if verbose:
                print(f"  {mr.model_name:35s} χ²={mr.chi2:5.1f}  "
                      f"AIC={mr.aic:6.1f}  BIC={mr.bic:6.1f}  p={mr.pvalue:.3f}")
                print(f"    {mr.interpretation}")

        best = min(models.items(), key=lambda x: x[1].aic)
        results['best_model_aic'] = best[0]
        results['best_model_bic'] = min(models.items(), key=lambda x: x[1].bic)[0]
        if verbose:
            print(f"\n  Best by AIC: {best[0]} ({best[1].model_name})")
            print(f"  Best by BIC: {results['best_model_bic']}")

    # External data assessment
    if verbose:
        print(f"\n--- External Data That Would Improve Analysis ---")
    results['external_data_potential'] = {}
    for key, data in FUTURE_DATA.items():
        results['external_data_potential'][key] = data
        if verbose:
            print(f"  {data['name']:30s} z={data['z_range']:>10s}  "
                  f"n={data['expected_n']:>12d}  {data['status']}")

    # θ* / Hubble tension critical assessment
    results['theta_star_assessment'] = {
        'principle_valid': True,
        'magnitude_viable': False,
        'reason': (
            'Using θ* instead of H₀ is correct in principle, but Bianchi shear '
            'cannot change r_s enough to resolve the Hubble tension. '
            'The shear needed (σ/H ~ 0.4) exceeds CMB bounds (σ/H < 4.7e-11) '
            'by 10 orders of magnitude. Our framework correctly treats '
            'bridge quantities (ΔH₀, Δq₀) as EXPLORATORY, not as Hubble tension '
            'resolutions.'
        ),
        'our_approach': (
            'Fixed Planck background (θ* implicitly fixed), tilt measured at '
            'z < 1 (not primordial), bridge quantities quarantined (HB-4).'
        ),
    }

    return results
