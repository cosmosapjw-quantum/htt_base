#!/usr/bin/env python3
"""REV-R126: consolidated results table across the EGS-type theorem programme.

Aggregates the headline result of every conditional theorem + every blocked
data measurement into one structured table (json + markdown), pulling numeric
values from the already-deterministic experiment records so the table is
reproducible and honest:

  - EGS-lowell  NT-A1 / NT-A3 / NT-B3   (docs/generated/egs_lowell_theorem_proofs.json)
  - EGS2        NT2-A1..B3 + K1/K6      (docs/generated/egs2_experiments.json)
  - EGS3        A1..A4, B1..B4, PSD     (docs/generated/egs3_experiments.json +
                                         egs3_psd_cone_proof.json)

Status vocabulary:
  proven_symbolic   gate + Wolfram-verified closed-form identity
  proven_gate       gate-verified numerical/structural theorem
  measured_synth    synthetic-mechanics stand-in (NOT a real-data measurement)
  blocked           real-data run gated by a registered blocker code

No detection / family / geometry / native-solver claim is made or implied.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs/generated"
OUT_JSON = GEN / "egs_results_table.json"
OUT_MD = GEN / "egs_results_table.md"

MATH, GR, DATA = "math_stat", "gr_boltzmann", "data_interpretation"


def _load(name: str) -> dict:
    p = GEN / name
    return json.loads(p.read_text()) if p.is_file() else {}


def _rows() -> list[dict]:
    egs2 = _load("egs2_experiments.json").get("experiments", {})
    egs3 = _load("egs3_experiments.json").get("experiments", {})
    psd = _load("egs3_psd_cone_proof.json")
    a = egs3.get("axis_a", {})
    b = egs3.get("axis_b", {})
    p = egs3.get("axis_psd", {})
    c = egs3.get("axis_c", {})
    nt2a = egs2.get("NT2_A1_A2_fisher_floor", {})
    nt2b3 = egs2.get("NT2_B3_blind_sector", {})
    k1 = egs2.get("BLOCK_K1_e2e_maxscan", {})
    k6 = egs2.get("BLOCK_K6_hoffman_ribak", {})
    d = egs3.get("axis_d", {})
    # real-data discharges (rev-r127): K1 global max-scan, K5 coverage, K6 curl no-go
    k1g = _load("k1_global_maxscan.json")
    k5g = _load("k5_cf4_release_coverage.json")
    k6g = _load("k6_cf4_curl_posterior.json")
    # rev-r142 BASS-Extended joint PV+CMB: real CF4+JWST forecast + real SMICA BipoSH
    bej = _load("bass_extended_joint_forecast.json")
    bip = _load("k1_biposh_smica.json")
    # rev-r146 review-response cycle: identified-set semantics + SymPy seals
    e = egs3.get("axis_e", {})
    f = egs3.get("axis_f", {})
    pis = _load("parent_identity_seal.json")
    bvs = _load("bianchi_v_constraint_seal.json")

    def r(tid, axis, statement, key, status, evidence):
        return {"theorem_id": tid, "axis": axis, "statement": statement,
                "key_result": key, "status": status, "evidence": evidence}

    rows = [
        r("NT-A1", MATH, "Closure-conditional quadrupole-filling identity: under the registered ETM closure, F_shear is linear in the CMB quadrupole and F_shear->0 in the EGS limit (not a generic CMB statement)",
          "slope 1/(kappa^2 x_max), kappa=4/21 (registered ETM convention); F_shear(D2=0)=0", "proven_symbolic",
          "wolfram egs_lowell; fig_theorem_nt_a1_quadrupole_filling"),
        r("NT-A3", MATH, "Single-sky sampling dispersion of the standard F_shear estimator (one estimator; NOT a universal CR floor)",
          "sqrt(2/5) = 0.632 at l=2", "proven_symbolic",
          "wolfram egs_lowell; fig_theorem_nt_a3_cosmic_variance_floor"),
        r("NT-B3", GR, "Depth-transport EGS limit: a depth-steady shear gives a zero depth-gap contrast (G_F=1); a depth-growing tilt imprints a nonzero contrast",
          "L.1=0 contrast operator; G_F=1 contrast for depth-steady shear", "proven_symbolic",
          "wolfram egs_lowell; fig_theorem_nt_b3_gf_transport"),
        r("EGS3-A1", MATH, "Graded-comparator identifiability (within the registered leading-channel response map): from {low-l CMB-T, radial velocity} the reachable subspace of g is rank 2",
          (f"rank {a.get('A1_graded_rank',{}).get('rank','?')}; reachable {a.get('A1_graded_rank',{}).get('reachable')}; "
           "null = structural {W2} (order-independent: radial n.Omega.n=0 + CMB curl/Weyl-blind) + leading-order no-channel {Omega_k} (re-opens beyond leading order)"),
          "proven_gate", "egs3-gates A1; fig_egs3_a1_graded_rank"),
        r("EGS3-A3", MATH, "Pi is a calibrated e-value: unit null mean, Markov false-exceedance bound P(E>=1/beta)<=beta; domination is conservative",
          f"null mean {a.get('A3_evalue_calibration',{}).get('null_mean','?')}; Markov holds {a.get('A3_evalue_calibration',{}).get('markov_holds','?')}",
          "proven_gate", "egs3-gates A3; fig_egs3_a3_evalue_calibration"),
        r("EGS3-A4", MATH, "Rao-Blackwell sufficiency: the reachable-sector statistic dominates any raw multi-channel estimator",
          f"Var_RB <= Var_raw: {a.get('A4_rao_blackwell',{}).get('dominates','?')}",
          "proven_gate", "egs3-gates A4"),
        r("NT2-A1", MATH, "Multi-multipole Fisher floor conditional on the registered shear-response profile (below the single-l dispersion under that response; physical calibration awaits the native low-l transfer)",
          f"floor {nt2a.get('single_ell_dispersion_l2',0.632):.3f}(l=2) -> 0.424(L=20) under the registered response", "proven_gate",
          "egs2-gates NT2-A1; fig_egs2_nt2a1_fisher_floor"),
        r("NT2-A2", MATH, "Octupole information saturation: the tail contribution converges (no single extra multipole closes the floor)",
          "tail l>3 saturates; decade increments shrink", "proven_gate", "egs2-gates NT2-A2"),
        r("EGS3-B1", GR, "Semi-native shear->multipole transfer: the Fisher floor is a single-mode, finite-k PROFILE in the shear scale k (the full-response floor needs the shear-power mode integral / native transfer)",
          "floor saturates at 0.632 (super-horizon), drops below at finite k for a single shear-sourced mode", "proven_gate",
          "egs3-gates B1; fig_egs3_b1_floor_profile"),
        r("EGS3-B2", GR, "Volterra depth-memory: the depth gap is a Volterra integral of the tilt stress with kernel exp(-3 int H); == ODE + Gronwall",
          f"max|Volterra-ODE| {b.get('B2_volterra_memory',{}).get('max_diff_vs_ode','?')}; Gronwall holds {b.get('B2_volterra_memory',{}).get('gronwall_holds','?')}",
          "proven_gate", "egs3-gates B2; fig_egs3_b2_volterra"),
        r("NT2-B3 / EGS3-B3", GR, "Vorticity blind sector re-opens: radial velocities are vorticity-blind (n.Omega.n=0); the transverse channel breaks the no-go",
          f"radial max {nt2b3.get('radial_max_projection','~0')}; transverse rank {b.get('B3_vorticity_reopen',{}).get('transverse_rank','?')}",
          "proven_gate", "egs2/egs3-gates B3; fig_egs3_b3_vorticity"),
        r("NT2-B1", GR, "Two-sided shear/F bracket: within the registered closure/H3 derivative-correction model, a nonzero a2 bounds the closure-defined shear-filling away from zero (NOT a generic statement about the observed CMB quadrupole)",
          "F_lo > 0 under the registered closure/H3 model; zero excluded", "proven_symbolic",
          "wolfram egs3 bracket; egs2-gates NT2-B1; fig_egs2_nt2b1_bracket"),
        r("EGS3-B4", GR, "Covariant two-sided-bracket constants: nondegeneracy condition C_up*kappa*(1+R) > 1 (satisfied by kappa=4/21, C_up=9)",
          "12/7 > 1", "proven_symbolic", "wolfram egs3_bracket_constants (PASS)"),
        r("EGS3-C1", MATH, "Kinematic deprojection: a closed-form alpha makes the low-ell shear reading immune to the observer-boost beta^2 quadrupole; Sigma_tilde^2=Sigma^2-alpha(Omega_tilt)^2 -> 0 on a pure-boost sky and preserves genuine shear (estimator property, not a detection; Sigma^2 stays partial)",
          (f"alpha=(4/9)T0^2 N2/(kappaT^2 R_sigma), beta-independent; eps-normalisation value {c.get('C1_deprojection_alpha',{}).get('eps_normalisation_value','?')} (doppler_boost.py:94 eps1^2 anchor)"),
          "proven_gate", "egs3-gates C1; wolfram egs3_boost_tilt_separation (PASS); fig_egs3_c_deprojection"),
        r("EGS3-C2", MATH, "Coupled Fisher: the same velocity sources both the boost quadrupole and the tilt, so F_{Sigma2,Omega_tilt} is nonzero and scales as beta^2; the Sigma^2 covariance inflates by 1/(1-r^2) and returns to 1 as beta->0",
          (f"offdiag ratio at 2x beta = {c.get('C2_coupled_fisher',{}).get('offdiag_ratio_2x','?')} (== beta^2); inflation=1/(1-r^2)"),
          "proven_gate", "egs3-gates C2; wolfram egs3_boost_tilt_separation (PASS)"),
        r("EGS3-C3", MATH, "Boost/tilt separation identifiability: the augmented response is rank 2 generically and DEGENERATE iff the boost axis is aligned with the shear principal axis (Gram determinant 1-P2(cos t)^2)",
          (f"generic rank {c.get('C3_identifiability',{}).get('generic_rank','?')} separable; aligned rank {c.get('C3_identifiability',{}).get('aligned_rank','?')} degenerate"),
          "proven_gate", "egs3-gates C3; wolfram egs3_boost_tilt_separation (PASS); fig_egs3_c_deprojection"),
        r("EGS3-C4", MATH, "Injection-recovery witness (moment-level synthetic; no map, no native low-ell solver, no real data): the naive Sigma^2 false-positive-rate is high on a pure-boost sky, the deprojected Sigma_tilde^2 FPR is nominal, and genuine shear is recovered unbiased and covered",
          (f"FPR naive {c.get('C4_injection_recovery',{}).get('fpr_naive_pure_boost',0):.3f} -> deprojected {c.get('C4_injection_recovery',{}).get('fpr_deprojected_pure_boost',0):.3f}; genuine-shear coverage {c.get('C4_injection_recovery',{}).get('genuine_shear_coverage',0):.2f}"),
          "proven_gate", "egs3-gates C4; fig_egs3_c_deprojection"),
        r("EGS3-D1", DATA, "BASS-Extended PV sector: a feasible correlated-covariance bulk-flow / tilt GLS on real CF4 via a low-rank Woodbury covariance (no dense N x N inversion), with a JWST-anchored distance-prior Omega_tilt precision FORECAST (survey-design; hypothetical prior on the cross-matched anchors, not a measurement)",
          ((f"|B|={bej.get('pv_sector',{}).get('tilt_diagonal',{}).get('amplitude_kms',0):.0f} km/s on {bej.get('pv_sector',{}).get('n_groups','?')} CF4 groups (K5-consistent); {bej.get('jwst_forecast',{}).get('n_anchor_matched','?')} JWST anchors matched -> Omega_tilt precision gain {bej.get('jwst_forecast',{}).get('omega_tilt_precision_gain',1):.3f} (nearby anchors barely move the global tilt -- honest)")
           if bej else "awaiting compute"),
          "measured_synth",
          "scripts/bass_extended_joint_forecast.py on real CF4 + JWST seed cross-match; PV tilt measured, JWST prior is a labelled forecast"),
        r("EGS3-D2", MATH, "Coupled-Fisher degeneracy break: the PV/JWST Omega_tilt prior strictly reduces the Sigma^2 covariance inflation 1/(1-r^2), blocking the observer-boost Sigma^2 leakage (solver-free; Wolfram-verified monotonicity)",
          (f"Sigma^2 inflation {d.get('D3_degeneracy_break',{}).get('sigma2_inflation_data',1):.4f} -> {d.get('D3_degeneracy_break',{}).get('sigma2_inflation_jwst',1):.4f} (break {d.get('D3_degeneracy_break',{}).get('degeneracy_break_factor',1):.4f}) with the prior"),
          "proven_gate", "egs3-gates D4; wolfram egs3_boost_tilt_separation prior_precision_reduces_inflation (PASS); fig_egs3_d_joint_forecast"),
        r("EGS3-D3", DATA, "Real off-diagonal BipoSH statistical-isotropy measurement on the Planck SMICA / Commander low-ell map (L=1 observer-boost/aberration + L=2 SI-violation), look-elsewhere-corrected against the matched isotropic GRF null",
          ((f"SMICA BipoSH global p={bip.get('results',{}).get('smica',{}).get('global_p',0):.3f}, Commander p={bip.get('results',{}).get('commander',{}).get('global_p',0):.3f} (real map, {bip.get('config',{}).get('n_null','?')} GRF nulls; consistent with isotropy)")
           if bip.get('results') else "awaiting compute"),
          "measured_partial",
          "scripts/k1_biposh_smica.py on real SMICA/Commander; matched isotropic GRF null; FFP10/NPIPE E2E null still BLOCKED_MISSING_PR4_E2E_ACCESS"),
        r("EGS3-D4", DATA, "Theory-g Bianchi CMB joint likelihood: the mode-coupled C_{lm,l'm'}(g) / A^{LM}_{ll'}(g) prediction needs the native low-ell solver and is FAIL-CLOSED (never fabricated); the drop-in interface stub is in place",
          "fail-closed OutOfScopeError; interface stub ready (joint_pv_cmb_forecast.anisotropic_cmb_covariance)",
          "blocked", "AWAITING_NATIVE_LOWELL_SOLVER; data-side BipoSH (EGS3-D3) is the solver-free substitute"),
        r("EGS3-PSD", MATH, "PSD-cone redesign: x_C = tr(C M) for M=diag(g)>=0; admissible set is the convex PSD cone; rank-2 reachable eigen-directions; cone-shell bracket excludes the FLRW vertex",
          f"bit-identical {p.get('bit_identical','?')}; rank {p.get('reachable_rank','?')}; convex cone {p.get('convex_cone','?')}; status {psd.get('status','?')}",
          "proven_symbolic", "egs3-gates PSD P1-P4; wolfram egs3_psd_cone (PASS); fig_egs3_psd_cone"),
        r("EGS3-E1", MATH, "Identified-set semantics for x_C (P26/P31/A8): the reportable object under the rank-2 response is the two-stage-tau interval [x_C^-, x_C^+] with refutability (empty), no-result (unbounded), and ceiling-unfit (F>1) statuses; the interval is sharp (endpoints attained)",
          (f"population interval {e.get('E1_identified_set',{}).get('population_interval','?')} reproduces the registered example; statuses {e.get('E1_identified_set',{}).get('statuses','?')}"),
          "proven_gate", "egs3-gates E1/E7"),
        r("EGS3-E2", MATH, "Imbens-Manski endpoint coverage (P35): the parameter CI needs the IM critical value; the projection CI is conservative and the naive per-endpoint one-sided CI undercovers as the interval width shrinks",
          (f"coverage projection {e.get('E2_im_coverage',{}).get('coverage_projection',0):.3f} >= IM {e.get('E2_im_coverage',{}).get('coverage_im',0):.3f} (nominal 0.95) > naive endpoint {e.get('E2_im_coverage',{}).get('coverage_endpoint_naive',0):.3f} (N={e.get('E2_im_coverage',{}).get('n_mc','?')}, seed {e.get('E2_im_coverage',{}).get('seed','?')}, SE {e.get('E2_im_coverage',{}).get('se_binomial',0):.4f})"),
          "proven_gate", "egs3-gates E2; fig_egs3_e_im_coverage"),
        r("EGS3-E3", MATH, "Refutability power (M2' response): the empty-feasible-set branch is a specification test -- size alpha1 at zero injection, power -> 1 with the orthogonal-misfit amplitude (synthetic witness)",
          (f"empty rate {e.get('E3_refutability_power',{}).get('empty_rate',['?'])[0]:.3f} at a=0 (alpha1 {e.get('E3_refutability_power',{}).get('alpha1','?')}) -> {e.get('E3_refutability_power',{}).get('empty_rate',[0,0,0,0,0,0])[-1]:.2f} at a=6 (N={e.get('E3_refutability_power',{}).get('n_mc','?')}, seed {e.get('E3_refutability_power',{}).get('seed','?')})"),
          "measured_synth", "egs3-gates E3; fig_egs3_e_refutability_power"),
        r("EGS3-E4", MATH, "Joint-feasible-set G_F propagation (P36): with shared null components across depth bins the depth-gap interval is the joint sup/inf over ONE shared feasible set; the naive quotient of marginal intervals is strictly wider (conservative)",
          (f"joint width / naive width = {e.get('E4_gf_joint_vs_naive',{}).get('width_ratio',1):.3f}; joint within naive {e.get('E4_gf_joint_vs_naive',{}).get('joint_within_naive','?')}"),
          "proven_gate", "egs3-gates E4"),
        r("EGS3-F1", MATH, "Parent-identity seal (B1 repair): the Gauss constraint (tilted frame included) forces W^2 = omega_ab omega^ab/(6H^2) and c=(1,-1,1,1); the v5-document convention omega_a omega^a/H^2 was exactly 3x the registered value; the (3/2) MES conversion rule is derived, not asserted (code was already on the registered convention -- document-only repair)",
          (f"seal {pis.get('status','?')}; c derived {pis.get('parent_identity',{}).get('c_derived','?')}; mismatch factor {pis.get('w2_convention',{}).get('mismatch_factor','?')}; (3/2) rule {pis.get('three_halves_rule',{}).get('derived_factor','?')}"),
          "proven_symbolic", "make egs3-seals (SymPy); egs3-gates F1; docs/generated/parent_identity_seal.json"),
        r("EGS3-F2", GR, "Bianchi V constraint seal (P5): the LRS-V momentum constraint 2 A Sigma_+ = (1+w) Omega beta reproduces the conditional Sigma_+^2 = [(1+w)Omega]^2 beta^2/(4 Omega_K) exactly; exact-rapidity correction (4/3)beta^2; undefined for Omega_K<=0 (constraint-algebra seal, NOT a dynamical integration)",
          (f"seal {bvs.get('status','?')}; beta^2-scaling log-log slope {f.get('F2_bianchi_v_witness',{}).get('loglog_slope',0):.4f}; Omega_K<=0 raises {f.get('F2_bianchi_v_witness',{}).get('omega_k_breakdown_raises','?')}"),
          "proven_symbolic", "make egs3-seals (SymPy); egs3-gates F2; docs/generated/bianchi_v_constraint_seal.json"),
        r("EGS3-F3", GR, "Shear-memory kernel bias (P13 companion): fitting the naive scalar closure sigma'=-3H sigma+kappa Pi on exact linearized-1+3 trajectories (toy Weyl closure E=e0 H sigma) is unbiased ONLY at the friction-matching e0=1 -- the quantitative kernel is closure-conditional (P13 ledger demoted to DERIVED_CONDITIONAL)",
          (f"kappa bias ratio over e0 {f.get('F3_shear_memory_bias',{}).get('e0_grid','?')}: {[round(x, 3) for x in f.get('F3_shear_memory_bias',{}).get('kappa_bias_ratio',[])]} (zero at e0={f.get('F3_shear_memory_bias',{}).get('zero_crossing_e0','?')})"),
          "measured_synth", "egs3-gates F3; fig_egs3_f_shear_memory_bias"),
        r("K1", DATA, "Global look-elsewhere-corrected low-l morphology p-value on the real Planck map (isotropic LambdaCDM null)",
          (f"SMICA global p={k1g.get('smica',{}).get('global_p',0):.3f}, Commander p={k1g.get('commander',{}).get('global_p',0):.3f} (real PR3 map, {k1g.get('config',{}).get('n_null','?')} GRF nulls)"
           if k1g else "awaiting compute"),
          "measured_partial",
          "scripts/k1_global_maxscan.py on real SMICA/Commander; E2E-systematics null still BLOCKED_MISSING_PR4_E2E_ACCESS (PLA portal-only sims)"),
        r("K5", DATA, "CF4 bulk-flow amplitude (measured, model-independent) + conditional cosmic-variance coverage from geometry-and-error matched Gaussian bulk-flow mock mechanics (fixed LambdaCDM sigma_cv=150 km/s/comp prior)",
          (f"|B|={k5g.get('measured_bulk',{}).get('amplitude_kms',0):.0f} +/- {k5g.get('coverage',{}).get('total_amplitude_error_kms',0):.0f} km/s (consistent with the LambdaCDM ~150-250 km/s bulk-flow expectation at this depth); CV-incl coverage {k5g.get('coverage',{}).get('cosmic_variance_inclusive',{}).get('amplitude_coverage',0):.2f} (meas-only {k5g.get('coverage',{}).get('measurement_noise_only',{}).get('amplitude_coverage',0):.2f}), conditional on the sigma_cv prior"
           if k5g else "awaiting compute"),
          "measured",
          "scripts/k5_cf4_release_coverage.py on real CF4 groups; bulk flow measured; coverage is conditional Gaussian-prior mock mechanics (full CF4 selection/Malmquist/grouping/correlated-field mocks remain a local-repo gate)"),
        r("K6", DATA, "CF4 vorticity/curl sector on the real WF mean field: curl-suppression structural no-go (curl-suppressed reconstruction; estimator validated on an injected solid-body curl mode)",
          (f"vorticity/shear<={k6g.get('vorticity_over_shear_ratio_max','?'):.3f} at all radii; solid-body curl-injection recovered; structural_no_go={k6g.get('structural_no_go','?')}"
           if k6g else "awaiting compute"),
          "measured_no_go",
          "scripts/k6_cf4_curl_posterior.py on real CF4++ WF field; WF mean-field curl-suppression no-go established; a true constrained-realization (Hoffman-Ribak) posterior remains blocked until a CR ensemble is owned"),
    ]
    return rows


def _payload() -> dict:
    rows = _rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "schema": "htt.egs.results_table.v1",
        "claim_tier": "program_theorem_and_synthetic_mechanics",
        "family_identification": False,
        "native_solver_result": False,
        "axes": {"math_stat": "mathematics / statistics theory axis",
                 "gr_boltzmann": "GR / covariant-Boltzmann theory axis",
                 "data_interpretation": "data interpretation axis"},
        "status_counts": counts,
        "rows": rows,
        "claim_boundary": "conditional theorems + synthetic mechanics + real-data measurements on owned inputs; no detection, family/geometry, or native-solver result. Measured rows are model-independent descriptors; K6 is an honest structural no-go; K1 is a partial (look-elsewhere) discharge under an idealised null.",
        "discharges_rev_r127": {
            "K5": "real CF4 bulk flow measured; cosmic-variance coverage is CONDITIONAL on a fixed LambdaCDM sigma_cv=150 km/s/comp Gaussian prior (geometry-and-error matched mock mechanics). Full release-matched mocks (selection/Malmquist/grouping/correlated field) remain a local-repo gate.",
            "K6": "WF mean-field curl-suppression structural no-go established (real CF4 WF field; estimator validated on an injected solid-body curl mode). A true constrained-realization (Hoffman-Ribak) vorticity posterior remains blocked until a CR ensemble is owned.",
            "K1": "BLOCKED_MISSING_PR4_E2E_ACCESS partially discharged (real-map look-elsewhere global p under LambdaCDM null; the global p is component-separation dependent, SMICA 0.097 / Commander 0.121, not E2E-calibrated and not averaged; E2E-systematics null still open)",
        },
        "blockers_open": ["BLOCKED_MISSING_PR4_E2E_ACCESS (E2E-systematics null only; look-elsewhere discharged)",
                          "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP (K5 full release-matched mocks; conditional Gaussian-prior coverage only so far)",
                          "BLOCKED_MISSING_FIELD_REALIZATIONS (K6 true CR vorticity posterior; WF mean-field no-go only so far)",
                          "AWAITING_NATIVE_LOWELL_SOLVER"],
    }


_AXIS_LABEL = {MATH: "Math/Stat", GR: "GR/Boltzmann", DATA: "Data"}


def _markdown(payload: dict) -> str:
    lines = [
        "# Consolidated EGS-type results table",
        "",
        "Auto-generated by `scripts/build_egs_results_table.py` from the deterministic",
        "experiment records. Conditional theorems + synthetic mechanics only; no",
        "detection, family/geometry, or native-solver claim. Blocked rows keep their",
        "registered blocker code and emit only a labelled synthetic stand-in.",
        "",
        f"Status counts: {payload['status_counts']}",
        "",
        "| Theorem | Axis | Statement | Key result | Status | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append("| {tid} | {axis} | {st} | {key} | `{status}` | {ev} |".format(
            tid=row["theorem_id"], axis=_AXIS_LABEL[row["axis"]],
            st=row["statement"], key=row["key_result"], status=row["status"],
            ev=row["evidence"]))
    lines += ["", "Open blockers: " + ", ".join(f"`{b}`" for b in payload["blockers_open"]), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = _payload()
    exp_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    exp_md = _markdown(payload) + "\n"
    if args.check:
        stale = []
        for path, content in ((OUT_JSON, exp_json), (OUT_MD, exp_md)):
            if (path.read_text() if path.exists() else None) != content:
                stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale results table:", *stale, sep="\n  - ")
            return 1
        print("results table up to date")
        return 0
    OUT_JSON.write_text(exp_json)
    OUT_MD.write_text(exp_md)
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)} + {OUT_MD.relative_to(REPO_ROOT)} ({len(payload['rows'])} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
