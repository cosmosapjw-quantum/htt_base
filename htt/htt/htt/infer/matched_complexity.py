"""
htt/infer/matched_complexity.py — Matched-Complexity Enforcement
================================================================
P-15 deliverable. Ensures fair comparison between controls by
matching parameter counts, prior widths, and amplitude structures.

Also implements low-z ablation logic for Phase 2 directional audit.
"""
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

from .control_registry import CONTROLS, ControlSpec

__all__ = [
    'enforce_matched_complexity',
    'MatchedComplexityReport',
    'LowZAblation',
    'ablation_result',
]


@dataclass(frozen=True)
class MatchedComplexityReport:
    """Result of matched-complexity enforcement."""
    controls_checked: tuple
    amplitude_matched: bool
    nuisance_matched: bool
    prior_width_matched: bool
    overall_pass: bool
    violations: tuple


def enforce_matched_complexity(
    control_codes: List[str] = None
) -> MatchedComplexityReport:
    """Verify that controls C1–C3 have matched complexity.

    Checks:
      1. Same number of amplitude parameters (C1 vs C2)
      2. Same number of nuisance parameters (C1 vs C2)
      3. Same prior widths (C1 vs C2 vs C3 amplitudes)
      4. C3 nuisance matches C1/C2

    C0 is exempt (baseline with different structure).
    """
    if control_codes is None:
        control_codes = ['C1', 'C2', 'C3']

    specs = [CONTROLS[c] for c in control_codes]
    violations = []

    # Check C1 vs C2 structure
    c1 = CONTROLS.get('C1')
    c2 = CONTROLS.get('C2')
    c3 = CONTROLS.get('C3')

    if c1 and c2:
        if c1.n_amplitude != c2.n_amplitude:
            violations.append(f"C1.n_amplitude={c1.n_amplitude} ≠ C2.n_amplitude={c2.n_amplitude}")
        if c1.n_nuisance != c2.n_nuisance:
            violations.append(f"C1.n_nuisance={c1.n_nuisance} ≠ C2.n_nuisance={c2.n_nuisance}")
        if c1.prior_width_amplitude != c2.prior_width_amplitude:
            violations.append(f"C1.prior_width_amp={c1.prior_width_amplitude} ≠ C2")

    if c1 and c3:
        if c1.prior_width_amplitude != c3.prior_width_amplitude:
            violations.append(f"C1.prior_width_amp ≠ C3.prior_width_amp")
        if c1.n_nuisance != c3.n_nuisance:
            violations.append(f"C1.n_nuisance ≠ C3.n_nuisance")

    amp_ok = len([v for v in violations if 'amplitude' in v]) == 0
    nui_ok = len([v for v in violations if 'nuisance' in v]) == 0
    pri_ok = len([v for v in violations if 'prior_width' in v]) == 0

    return MatchedComplexityReport(
        controls_checked=tuple(control_codes),
        amplitude_matched=amp_ok,
        nuisance_matched=nui_ok,
        prior_width_matched=pri_ok,
        overall_pass=len(violations) == 0,
        violations=tuple(violations),
    )


# ── Low-z Ablation ──────────────────────────────────────────

@dataclass(frozen=True)
class AblationResult:
    """Result of a low-z ablation test."""
    z_cut: float
    n_removed: int
    n_remaining: int
    lnB_full: float
    lnB_ablated: float
    delta_lnB: float
    direction_preserved: bool
    info_gain_preserved: bool


class LowZAblation:
    """Low-z ablation logic for the directional audit.

    Removes low-z surveys one at a time and checks whether
    the directional information gain survives.

    The key question: does removing low-z data destroy the
    directional signal, or does the CMB low-ℓ preserve it?
    """

    # Survey redshift characteristics
    SURVEY_Z = {
        'CF4': 0.05,      # median z of CF4 sample
        'CatWISE': 1.2,   # median z of CatWISE quasars
        'Radio': 0.9,     # median z of NVSS/RACS sources
        'CMB_lowl': 1089,  # last scattering
    }

    def __init__(self, obs_data: dict):
        self.obs = obs_data

    def ablate(self, remove_survey: str) -> dict:
        """Remove one survey and return modified obs_data.

        Parameters
        ----------
        remove_survey : str
            'CF4', 'CatWISE', 'Radio', or 'CMB_lowl'.

        Returns
        -------
        dict
            Modified obs_data with the survey removed (set to zero weight).
        """
        import copy
        obs_mod = copy.deepcopy(self.obs)
        dp = obs_mod['dipole_observations']

        if remove_survey == 'CF4':
            dp['cf4_watkins_2023']['sigma'] = 1e10  # effectively infinite
        elif remove_survey == 'CatWISE':
            dp['catwise_bohme_2025']['sigma_stat'] = 1e10
        elif remove_survey == 'Radio':
            dp['radio_secrest_2021']['sigma_stat'] = 1e10
        elif remove_survey == 'CMB_lowl':
            # Set CMB multipole uncertainties to infinity
            pass  # CMB channels are in the evidence_models likelihood, not here

        return obs_mod

    def run_ablation_suite(self) -> List[dict]:
        """Run ablation for each low-z survey.

        Returns list of ablation configurations.
        """
        configs = []
        for survey in ['CF4', 'CatWISE', 'Radio']:
            obs_mod = self.ablate(survey)
            configs.append({
                'removed': survey,
                'z_cut': self.SURVEY_Z[survey],
                'obs_data': obs_mod,
            })
        return configs


def ablation_result(survey: str, lnB_full: float,
                    lnB_ablated: float,
                    info_full: float, info_ablated: float,
                    threshold: float = 2.0) -> AblationResult:
    """Create an AblationResult from full and ablated runs."""
    z = LowZAblation.SURVEY_Z.get(survey, 0)
    return AblationResult(
        z_cut=z,
        n_removed=1,
        n_remaining=2,  # 3 surveys - 1
        lnB_full=lnB_full,
        lnB_ablated=lnB_ablated,
        delta_lnB=lnB_ablated - lnB_full,
        direction_preserved=abs(info_ablated) > threshold,
        info_gain_preserved=info_ablated > 0.5 * info_full,
    )
