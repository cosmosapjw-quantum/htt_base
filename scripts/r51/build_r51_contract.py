"""Write R51_SOURCE_OPERATOR_CONTRACT.json from the code-owned response registry.

Run: PYTHONPATH=htt/src:htt:. python scripts/r51/build_r51_contract.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")]

from htt.htt.infer.r51_source_bound_response import (  # noqa: E402
    DEFERRED_PROBES, RESPONSE_TERM_REGISTRY, SOURCE_BOUND_PROBES,
)

OUT = ROOT / "docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R51"

COMPONENTS = [
    {"name": "sigma_ab (R49 state)", "basis": "Cartesian STF5 with G_STF5 metric; R51 CMB uses orthonormal STF5", "unit": "dimensionless sigma/H0",
     "congruence": "matter", "epoch": "z=0", "triad": "common Galactic triad",
     "response": "none directly; enters CMB only through SHEAR_HISTORY_OPERATOR_TYPE_I (conditional)"},
    {"name": "Sigma_ab (CMB estimand)", "basis": "orthonormal STF5, tr(E_a E_b)=delta_ab", "unit": "dimensionless (integrated shear)",
     "congruence": "photon path through matter-frame Bianchi-I geometry", "epoch": "integral z_*=1089.94 -> 0",
     "triad": "Galactic", "response": "CMB_T_TYPE_I_INTEGRATED_SHEAR (source-bound, first order)"},
    {"name": "omega_a", "basis": "axial 3-vector", "unit": "omega/H0", "congruence": "matter", "epoch": "z=0", "triad": "Galactic",
     "response": "none source-bound; Gaia B1 degenerate with marginalized frame spin -> unidentified"},
    {"name": "A_a", "basis": "polar 3-vector", "unit": "A/(c H0)", "congruence": "matter 4-acceleration (distinct from Class-B commutator a_a)",
     "epoch": "z=0", "triad": "Galactic", "response": "none source-bound in R51 (0.1 A, 0.5 A, H0(beta+A) quarantined) -> unidentified"},
    {"name": "beta_RM", "basis": "polar 3-vector", "unit": "v/c", "congruence": "radiation relative to matter", "epoch": "z_*",
     "triad": "Galactic", "response": "exact emission Lorentz factor (ell=1 linear, removed; ell=2 at O(beta^2)); not fitted in R51 T-only Sigma run"},
    {"name": "beta_MO", "basis": "polar 3-vector", "unit": "v/c", "congruence": "observer relative to matter", "epoch": "z=0",
     "triad": "Galactic", "response": "COUNT_DIPOLE_KINEMATIC (source-bound); CMB ell>=2 boost response excluded until kinematic-quadrupole removal is bound"},
    {"name": "frame_spin", "basis": "axial 3-vector", "unit": "uas/yr", "congruence": "Gaia-CRF3 vs ICRF3", "epoch": "Gaia DR3 epoch",
     "triad": "ICRS", "response": "nuisance (Schur-marginalized)"},
]

COVARIANCE = {
    "law": "finite_mc_t_loglike (Sellentin & Heavens 2016) for S from N iid same-process Gaussian MC; gaussian_loglike when C is a known model covariance",
    "mean_and_covariance_same_modes": "allowed in one normalized Gaussian with one logdet",
    "duplication_guard": "DataBlockRegistry: one byte identity -> one likelihood factor",
    "forbidden": ["automatic jitter", "pseudoinverse", "silent symmetrization", "Hartlap factor presented as posterior covariance model"],
    "cmb_mc": "SMICA FFP10 CMB+noise pairs 0-299 through the identical masked low-ell estimator; heldout calibration ids 200-299 (see PREREGISTRATION.json)",
}

SELECTION = {
    "cmb": "PR3 common Int/Pol masks (f_sky 0.779/0.781); pseudo-alm coupling inverse at lmax=6 with ell=0,1 columns deprojected; beam INT_BEAM x pixwin(2048) applied to the template",
    "commander": "map present; matched MC unavailable -> calibration UNAVAILABLE; uncalibrated difference only",
    "removed_modes": "monopole/dipole deprojected by the estimator; kinematic quadrupole removal UNBOUND -> sensitivity reported",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema_version": "htt.r51.source-operator-contract/1",
        "owner": "htt", "claim_tier": "C0", "transfer_source": "first-order Bianchi-I integrated-shear ISW (no native solver)",
        "response_terms": list(RESPONSE_TERM_REGISTRY),
        "source_bound_probes": list(SOURCE_BOUND_PROBES),
        "deferred_probes": DEFERRED_PROBES,
        "components": COMPONENTS,
        "covariance_contract": COVARIANCE,
        "selection_contract": SELECTION,
        "policy": "R49GeneralBianchiLikelihood(response_policy='source_bound') is the only physically admissible evaluation; 'r49_working_model' reproduces historical receipts only",
    }
    (OUT / "R51_SOURCE_OPERATOR_CONTRACT.json").write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
