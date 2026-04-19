"""
htt/infer/null_competition.py — Structured-Null Competition Engine
=====================================================================
Milestone M2.2 deliverable. Formally competes the shared-cause model
against each structured-null family at the DOF level.

The competition logic:
  1. For each null family, generate N synthetic datasets with β_true=0.
  2. Run the shared-cause test on each synthetic dataset.
  3. Record the false-positive rate (fraction where shared-cause is preferred).
  4. If ANY null family has FPR > threshold, the shared-cause detection
     is not robust against that systematic.

This is the adversarial complement to shared_cause.py: the null families
try to mimic the signal, and the competition engine measures how often
they succeed.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from htt.nulls import NULL_REGISTRY
from htt.nulls.common_interface import NullFamily
from htt.infer.shared_cause import run_shared_cause_test, SharedCauseResult

__all__ = [
    'NullCompetitionResult', 'FamilyCompetitionResult',
    'NullCompetitionEngine', 'run_null_competition',
]


@dataclass(frozen=True)
class FamilyCompetitionResult:
    """Result of competing one null family against shared-cause."""
    family_name: str
    n_realizations: int
    n_false_positives: int      # times shared-cause preferred on null data
    fpr: float                  # false-positive rate
    mean_lnB_null: float        # mean ln B(shared-cause vs null) on null data
    std_lnB_null: float
    robust: bool                # True if fpr < threshold
    status: str = 'INFERENTIAL'


@dataclass(frozen=True)
class NullCompetitionResult:
    """Full competition result across all null families."""
    families_tested: int
    families_robust: int
    families_vulnerable: int
    worst_family: str
    worst_fpr: float
    overall_robust: bool        # True if ALL families are robust
    family_results: Dict[str, FamilyCompetitionResult] = field(default_factory=dict)
    status: str = 'INFERENTIAL'


class NullCompetitionEngine:
    """Runs the full structured-null competition.

    For each null family in the registry, generates synthetic datasets
    and tests whether the shared-cause model produces false positives.
    """

    def __init__(self, n_realizations: int = 50,
                 fpr_threshold: float = 0.10,
                 obs_base: Optional[dict] = None):
        """
        Parameters
        ----------
        n_realizations : int
            Number of synthetic datasets per null family.
        fpr_threshold : float
            Maximum acceptable false-positive rate (default 10%).
        obs_base : dict, optional
            Base observational parameters for null generation.
        """
        self.n_realizations = n_realizations
        self.fpr_threshold = fpr_threshold

        if obs_base is not None:
            self.obs_base = obs_base
        else:
            # Load from canonical obs_defaults.json
            import json
            from pathlib import Path
            obs_path = Path(__file__).resolve().parent.parent.parent.parent / \
                'workspace' / 'data' / 'obs_defaults.json'
            if obs_path.exists():
                with open(obs_path) as f:
                    self.obs_base = json.load(f)
            else:
                # Minimal fallback for testing
                self.obs_base = {
                    'dipole_observations': {
                        'catwise_bohme_2025': {'eps1': 1.5e-2, 'sigma_stat': 3e-3, 'sigma_sys': 1e-3},
                        'radio_secrest_2021': {'eps1': 1.3e-2, 'sigma_stat': 4e-3, 'sigma_sys': 2e-3},
                        'cf4_watkins_2023': {'beta': 1.334e-3, 'sigma': 0.13e-3},
                    },
                    'planck2018': {'eps1': 1.2336e-3},
                }

    def compete_family(self, family_name: str) -> FamilyCompetitionResult:
        """Compete one null family against the shared-cause model."""
        if family_name not in NULL_REGISTRY:
            raise KeyError(f"Unknown null family: {family_name}")

        FamilyClass = NULL_REGISTRY[family_name]
        family = FamilyClass()

        lnB_values = []
        false_positives = 0

        for i in range(self.n_realizations):
            # Generate null data (β_true = 0 + systematic)
            null_data = family.generate(seed=i, obs_base=self.obs_base)

            # Convert NullDataset → obs_data format for shared-cause test
            obs_data = {
                'dipole_observations': {
                    'catwise_bohme_2025': {
                        'eps1': null_data.e1_CW,
                        'sigma_stat': null_data.e1_CW_s,
                        'sigma_sys': 0.0,
                    },
                    'radio_secrest_2021': {
                        'eps1': null_data.e1_rad,
                        'sigma_stat': null_data.e1_rad_s,
                        'sigma_sys': 0.0,
                    },
                    'cf4_watkins_2023': {
                        'beta': null_data.b_CF4,
                        'sigma': null_data.b_CF4_s,
                    },
                    'rho_CW_radio': null_data.rho_CW_radio,
                },
            }

            # Run shared-cause test on null data
            result = run_shared_cause_test(
                obs_data=obs_data,
                A_best=0.0011,  # default amplitude
            )

            lnB_values.append(result.lnB_S2_vs_null)
            if result.S2_preferred:
                false_positives += 1

        lnB_arr = np.array(lnB_values)
        fpr = false_positives / self.n_realizations

        return FamilyCompetitionResult(
            family_name=family_name,
            n_realizations=self.n_realizations,
            n_false_positives=false_positives,
            fpr=fpr,
            mean_lnB_null=float(lnB_arr.mean()),
            std_lnB_null=float(lnB_arr.std()),
            robust=fpr < self.fpr_threshold,
        )

    def run_all(self) -> NullCompetitionResult:
        """Run competition across all null families."""
        results = {}
        for name in NULL_REGISTRY:
            results[name] = self.compete_family(name)

        n_robust = sum(1 for r in results.values() if r.robust)
        n_vuln = len(results) - n_robust
        worst = max(results.values(), key=lambda r: r.fpr)

        return NullCompetitionResult(
            families_tested=len(results),
            families_robust=n_robust,
            families_vulnerable=n_vuln,
            worst_family=worst.family_name,
            worst_fpr=worst.fpr,
            overall_robust=n_vuln == 0,
            family_results=results,
        )


def run_null_competition(n_realizations: int = 50,
                         fpr_threshold: float = 0.10) -> NullCompetitionResult:
    """Convenience function to run full null competition."""
    engine = NullCompetitionEngine(
        n_realizations=n_realizations,
        fpr_threshold=fpr_threshold,
    )
    return engine.run_all()
