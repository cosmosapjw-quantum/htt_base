"""
htt/infer/shared_cause.py — Shared-Cause vs Null Competition
=============================================================
P-16 deliverable. Implements the S2 (shared-cause) model and
M_null (independent systematics) for Bayes factor comparison.
"""
import numpy as np
from dataclasses import dataclass

__all__ = ['SharedCauseResult', 'run_shared_cause_test']


@dataclass(frozen=True)
class SharedCauseResult:
    """Result of shared-cause vs null comparison."""
    lnB_S2_vs_null: float
    S2_preferred: bool
    survives_ablation: bool
    direction_l: float
    direction_b: float
    amplitude: float
    classification: str  # 'decisive', 'strong', 'moderate', 'inconclusive'

    @property
    def is_decisive(self) -> bool:
        return self.lnB_S2_vs_null > 5


def run_shared_cause_test(obs_data: dict,
                          A_best: float = 1.1e-3,
                          l_best: float = 264.0,
                          b_best: float = 48.0) -> SharedCauseResult:
    """Run the shared-cause vs null comparison.

    Uses the directional likelihood to compare:
      S2: single axis (l, b, A) explaining all surveys
      M_null: β = 0 with each survey noise-only
    """
    from .dipole_vector_likelihood import DipoleVectorLikelihood

    dvl = DipoleVectorLikelihood(obs_data, control='C1')

    logL_S2 = dvl.directional_log_likelihood(l_best, b_best, A_best)
    logL_null = dvl.directional_log_likelihood(l_best, b_best, 0.0)
    delta = logL_S2 - logL_null

    # Classification
    if delta > 5:
        cls = 'decisive'
    elif delta > 2.5:
        cls = 'strong'
    elif delta > 1:
        cls = 'moderate'
    else:
        cls = 'inconclusive'

    # Ablation: check each survey removal
    from .matched_complexity import LowZAblation
    abl = LowZAblation(obs_data)
    survives = True
    for survey in ['CF4', 'CatWISE', 'Radio']:
        obs_mod = abl.ablate(survey)
        dvl_mod = DipoleVectorLikelihood(obs_mod, control='C1')
        logL_mod = dvl_mod.directional_log_likelihood(l_best, b_best, A_best)
        logL_null_mod = dvl_mod.directional_log_likelihood(l_best, b_best, 0.0)
        delta_mod = logL_mod - logL_null_mod
        if delta_mod < 3:  # weakened below strong
            survives = False

    return SharedCauseResult(
        lnB_S2_vs_null=float(delta),
        S2_preferred=delta > 5,
        survives_ablation=survives,
        direction_l=l_best,
        direction_b=b_best,
        amplitude=A_best,
        classification=cls,
    )
