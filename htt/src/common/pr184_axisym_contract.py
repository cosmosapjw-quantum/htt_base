"""PR-184: premise-complete B-projector axisymmetric callable contract.

Adjudicates the PR-172 documented-vs-implemented disagreement WITHOUT
editing the frozen production adapter or any PR-172 receipt:

- unconditional-callable reading: FALSE (PR-172's falsification stands);
- premise-complete reading (sigma_{2,0}-only AND zero parity-odd
  B-tower history): TRUE, exact zero on the real unedited projector.

The full spin-harmonic parity action stays UNDERDEFINED_NOT_TESTED.
Nothing here is a physical-parity, observational, or Bianchi-family
statement.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
for entry in (str(_REPO / "htt"), str(_REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from bass.los.b_mode_projector import project_B_mode_transfer  # noqa: E402

PR172_FIXTURE_VALUE = 0.006921858926603516

CONTRACT = {
    "id": "b_projector_axisymmetric_zero_premise_complete_v1",
    "premise": (
        "axisymmetric CONFIGURATION: sigma_2M history has only the M=0 "
        "component nonzero AND the photon B-tower history is identically "
        "zero (the dynamically consistent state: axisymmetric shear with "
        "sigma_{2,+/-1}=0 cannot generate a B-tower from zero initial "
        "data)"
    ),
    "conclusion": "Delta_ell^B == 0 exactly at every (ell, m)",
    "unconditional_reading": (
        "FALSE and stays falsified by PR-172: the callable consumes the "
        "B-tower history as an independent argument, so a premise-"
        "violating nonzero B_{2,-2} history yields a nonzero output "
        "confined to the m=-2 channel"
    ),
    "pr172_disposition": (
        "PR-172 remains COMPLETED_FAILED_WITH_RECEIPT; it correctly "
        "falsified the unconditional reading of the documented invariant"
    ),
    "corroboration": (
        "PR-182 CAS-verified identity I1: the mirror-fixed axisymmetric "
        "m=0 sector has exactly zero B; a B_{2,-2} history is outside "
        "that sector (corroboration only, not a dependency)"
    ),
}


class PremiseViolation(ValueError):
    """Raised when a claimed-axisymmetric configuration is not one."""


def check_axisymmetric_premise(
    sigma_2M_history: np.ndarray, photon_B_tower_history: np.ndarray
) -> None:
    """Fail-closed premise checker for the premise-complete contract."""
    sigma = np.asarray(sigma_2M_history, dtype=np.float64)
    b_hist = np.asarray(photon_B_tower_history, dtype=np.float64)
    off_axis = np.max(np.abs(np.delete(sigma, 2, axis=-1)))
    if off_axis != 0.0:
        raise PremiseViolation(
            "sigma_2M history carries M != 0 components "
            f"(max abs {off_axis!r}); the configuration is not axisymmetric"
        )
    b_max = float(np.max(np.abs(b_hist)))
    if b_max != 0.0:
        raise PremiseViolation(
            "photon B-tower history is nonzero "
            f"(max abs {b_max!r}); a nonzero parity-odd history is outside "
            "the axisymmetric m=0 sector, so the exact-zero conclusion "
            "does not apply (this is the PR-172 counterexample channel)"
        )


def _base_configuration(n_eta: int = 9):
    eta = np.linspace(0.0, 1.0, n_eta)
    e_hist = np.zeros((n_eta, 3, 5))
    sigma = np.zeros((n_eta, 5))
    sigma[:, 2] = 1.0
    return eta, e_hist, sigma


def run_adjudication() -> dict:
    """Reproduce both readings on the REAL unedited projector."""
    eta, e_hist, sigma = _base_configuration()
    common = dict(
        photon_E_tower_history=e_hist,
        sigma_2M_history=sigma,
        eta_grid=eta,
        visibility_history=np.ones(eta.size),
        k_norm=2.0,
        ell_max=3,
    )

    consistent_b = np.zeros((eta.size, 3, 5))
    check_axisymmetric_premise(sigma, consistent_b)
    consistent_out = project_B_mode_transfer(
        photon_B_tower_history=consistent_b, **common
    )
    consistent_max = float(np.max(np.abs(consistent_out)))

    violating_b = np.zeros((eta.size, 3, 5))
    violating_b[:, 2, 0] = 1.0  # B_{2,-2} = 1: the PR-172 fixture
    premise_rejected = False
    try:
        check_axisymmetric_premise(sigma, violating_b)
    except PremiseViolation:
        premise_rejected = True
    violating_out = project_B_mode_transfer(
        photon_B_tower_history=violating_b, **common
    )
    violating_max = float(np.max(np.abs(violating_out)))
    support = sorted(
        {int(m_idx) for _, m_idx in np.argwhere(np.abs(violating_out) > 0.0)}
    )

    checks = {
        "consistent_configuration_exact_zero": consistent_max == 0.0,
        "pr172_fixture_reproduced_bit_exact": (
            violating_max == PR172_FIXTURE_VALUE
        ),
        "pr172_fixture_confined_to_m_minus_2_channel": support == [0],
        "premise_checker_rejects_pr172_fixture": premise_rejected,
    }
    terminal = (
        "PREMISE_COMPLETE_CONTRACT_REGISTERED_IMPLEMENTATION_UPHELD"
        if all(checks.values())
        else "BLOCKED_DERIVATION_INCONSISTENT"
    )
    return {
        "schema": "htt.pr184.adjudication.v1",
        "contract": CONTRACT,
        "checks": checks,
        "witnesses": {
            "consistent_configuration_output_max_abs": consistent_max,
            "pr172_fixture_output_max_abs": violating_max,
            "pr172_fixture_output_support_m_indices": support,
        },
        "terminal": terminal,
        "frozen_surfaces_untouched": [
            "htt/bass/los/b_mode_projector.py",
            "docs/generated/pr172_* (all PR-172 receipts)",
        ],
        "interpretation": (
            "Callable-contract mechanics only; PR-172's falsification of "
            "the unconditional reading stands; the full spin-harmonic "
            "parity action stays UNDERDEFINED_NOT_TESTED; no physical-"
            "parity, observational, or Bianchi-family statement."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_adjudication(), sort_keys=True))
