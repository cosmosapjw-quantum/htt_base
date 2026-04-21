# MASTER_PROMPT_LIST_bass_py
## Low-ℓ Special-Purpose Solver + Direction-Dependent Likelihood Generator
## Date: 2026-04-18
## Basis: R-TILT-02/03 + 7 design documents + W3-W5 completed foundation
## Status: initial roadmap freeze; supersedes ad-hoc W6 planning

---

# §0. Product identity

## 0.1 Mission statement

BASS_py is a **low-ℓ special-purpose solver** with two coupled deliverables:

1. **Forward spectrum generator**: given kinematical quantities
   $\{\sigma_{ab}, \beta, \omega_{ab}, A_a, \dot u_a\}$ as initial conditions,
   produce $D_\ell^{TT}$ and $D_\ell^{EE}$ for $\ell \le 30$.
   This is the **inverse of the MES pipeline**: MES constrains kinematics
   from observed $D_\ell$; bass_py goes the other direction.

2. **Direction-dependent likelihood generator**: produce posterior on dipole
   direction and amplitude, conditional on each Bianchi model
   (orthogonal/tilted), compared against CF4++, CatWISE, NVSS+RACS, CMB.

The defining feature: **global tilt vs local boost discrimination**.
Using R-TILT-02/03 framework, bass_py separates three observational
signatures (R-TILT-03 §3):

| Signature | Source | TT | EE | Mechanism |
|-----------|--------|-----|-----|-----------|
| Local motion | $W_R v_{\rm loc}$ | ✓ | ✗ | Thomson isotropic in CMB rest frame |
| Cosmological tilt | $\bar\beta$ (pre-recomb) | ✓ | ✓ | Thomson scattering of tilted photon dipole |
| Tilt² effective stress | 6 cross-terms | ✓ | ✓ | Scale-independent, deterministic |

**EE is therefore required as part of the deliverable**, not optional.
Pure TT cannot discriminate local from cosmological origin.

## 0.2 Positioning relative to Rust bass_rs

| Capability | bass_py (this spec) | Rust bass_rs (parallel work) |
|------------|---------------------|------------------------------|
| ℓ range | ≤ 30 | Full (up to ~2000) |
| Spectra | TT, EE | TT, TE, EE, BB |
| Scope | Linear perturbation on Bianchi background | Linear + nonlinear |
| Accuracy target | Rigorous within reduced scope; CAMB match at FLRW limit | Production CAMB-equivalent |
| Exposure | First version meeting observational data | Final production validator |

**Honest accuracy discipline**: every docstring, every public API, every
packet output explicitly states:

- the reduced scope vs full PSTF,
- the FLRW-limit recovery precision,
- the Bianchi cross-check status (match against bass_rs when available),
- known deferrals.

## 0.3 Non-goals

bass_py deliberately does NOT target:

- Full $\ell$ up to $\sim 2000$
- $B$-mode production as primary output (computed for validation only)
- Second-order nonlinear source closure
- Dynamical recombination (isotropic $x_e(\eta)$ maintained first pass)
- Patchy reionization
- Frame-misaligned (non-principal-axis) shear

These belong to bass_rs.

---

# §1. Completed inventory (W3-W5)

## 1.1 Runtime contract (W3)

| Module | Role | Status |
|--------|------|--------|
| `bass.runtime.canonical_decision` | W3 gate enforcement | VALIDATED |
| `bass.runtime.validation_labels` | Claim tier taxonomy | VALIDATED |
| `bass.runtime.sigma_floor` | Σ² floor guard | VALIDATED |

## 1.2 Observational bounds (W4)

| Module | Role | Status |
|--------|------|--------|
| `bass.observational.planck_mes_bounds` | Pastén Option B replication | VALIDATED |
| `bass.observational.beta_threshold` | VT-07 β threshold re-derivation | VALIDATED |

## 1.3 Physics backbone (W4D3-W5-C)

| Module | Role | Status | R-TILT link |
|--------|------|--------|-------------|
| `bass.collision.thomson_tensor` | axisymmetric ℓ=2 Thomson source | VALIDATED | R-TILT-03 §3.2 |
| `bass.transport.ray_transport` | single-ℓ steady state, N₂/F₂≈28 | VALIDATED | — |
| `bass.transport.multipole_hierarchy` (W5-A) | ℓ=0..L_max streaming cascade | VALIDATED | — |
| `bass.transport.implicit_hierarchy` (W5-B) | BE/CN/EXP stiff integrators | VALIDATED | — |
| `bass.transport.bianchi_i_hierarchy` (W5-C) | m∈{0,±2} channels | VALIDATED | R-TILT-03 §3 (direction foundation) |
| `tsc.diagnostics.spherical_quadrature` | Lebedev $S^2$ integration | VALIDATED | — |
| `tsc.diagnostics.entropy_invariants` | Gram admissibility | VALIDATED | — |

## 1.4 Honest scope statement for W3-W5 deliverables

**What W3-W5 IS**: a correct implementation of the PSTF streaming-coupling
structure of Challinor-Lasenby 1999 Eq. 44, **restricted to**:
(i) homogeneous-Bianchi shear drive at ℓ=2 only,
(ii) no $\ell=1$ baryon-photon dipole equation,
(iii) no polarization feedback into the collision term,
(iv) uniform damping $\Gamma$ across all ℓ,
(v) axisymmetric-to-full-Bianchi-I off-axis channels (m∈{0,±2}),
(vi) frozen-background shear (no feedback to Einstein block).

**What W3-W5 is NOT**: a CAMB-equivalent Boltzmann solver. Full $\ell=1$
dipole coupling, baryon $v_b$, polarization recoupling, line-of-sight
integration, and $C_\ell$ assembly are deliverables of W6-W10.

## 1.5 Cumulative metrics

- 1,282 tests across 35+ modules
- 0 P0/P1 findings
- Full regression runtime: ~54 seconds
- W3→W5-C coverage: runtime contracts + observational bounds + axisymmetric-to-Bianchi-I hierarchy with three integrator families

---

# §2. DAG for W6-W15+

## 2.1 Main dependency graph

```
W5-C (Bianchi I m∈{0,±2}) [DONE]
      │
      ├─→ W6 (ℓ=1 dipole + baryon v_b + Thomson drag)
      │       │
      │       └─→ W7 (E-mode hierarchy + polter recoupling)
      │               │
      │               └─→ W8 (visibility g(η) + reionization + g·Π source)
      │                       │
      │                       ├─→ W9 (line-of-sight integration → a_{ℓm}(k))
      │                       │       │
      │                       │       └─→ W10 (C_ℓ^TT, C_ℓ^EE, D_ℓ output)
      │                       │               │
      │                       │               └─→ W11 (direction-dependent C_ℓ(n̂) + BiPoSH)
      │                       │                       │
      │                       │                       └─→ W12 (W_R local patch solver)
      │                       │                               │
      │                       │                               └─→ W13 (β→D_2 transfer function)
      │                       │                                       │
      │                       │                                       └─→ W14 (TT-vs-EE discriminator)
      │                       │                                               │
      │                       │                                               └─→ W15 (likelihood generator)
      │                       │
      │                       └─→ V1 (FLRW→CAMB cross-check, W10 gated)
      │                       └─→ V2 (Bianchi→bass_rs cross-check, W11 gated)
```

## 2.2 Critical path: W6 → W9 → W10

Without W10, no $D_\ell$ output exists. Prioritize the critical path before
opening W12 (local patch) or W15 (likelihood).

## 2.3 Validation gates (parallel track)

- **V1 FLRW→CAMB**: activated after W10. Target: 5% at $\ell \le 10$, 10%
  at $\ell \le 30$ (honest bass_py-level match, not CAMB equivalence).
- **V2 Bianchi→bass_rs**: activated after W11. Target: direction-dependent
  $a_{\ell m}$ agreement in qualitative structure at $\ell=2,3$.

---

# §3. W6 — Baryon-photon dipole coupling (the ℓ=1 closure)

**Motivation**: Current W5-A hierarchy has $\ell=0$ and $\ell=1$ as pure
damped modes with no source. But R-TILT-03 requires the dipole channel to
carry the tilt acceleration $A_a$ contribution, and Thomson drag
$\dot\tau(\Theta^{(\gamma)}_a - v_{b,a})$ provides the tight-coupling
mechanism. Without W6, no TT dipole physics.

## PROMPT W6-01: Baryon state + continuity + Euler equations

**Type**: SOLVER-IMPL | **Techniques**: PAL + Analogical + CRAG
**Depends**: W5-C | **Est.**: ~300 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: bass_py에 baryon fluid state를 도입한다. state vector:
  (δ_b, v_b^a)  — 4 DOF per k-mode for orthogonal Bianchi
                  (vector components constrained by trace-free shear)

물리 (ch05_teff_corrections.tex Eq. baryon-euler, sign-corrected per
Ma-Bertschinger 1995 Eq. 29):
  δ_b' = -k v_b - 3Φ'
  v_b' + H v_b = k Ψ + (τ̇/R_b)(3Θ_1 - v_b)
  R_b = 3ρ_b / (4ρ_γ)    [baryon-photon momentum ratio]

  Thomson drag sign convention: PLUS sign on the baryon side drives
  v_b toward 3Θ_1 (lock); equal-and-opposite sign on the photon dipole
  side (W6-02) ensures baryon+photon momentum conservation.

In homogeneous Bianchi limit, gradient terms D_a → 0 at first order,
reducing to:
  v_b' + H v_b = +(τ̇/R_b)(3Θ_1 - v_b)

구현 (new file: bass/perturbation/baryon_fluid.py):
1. BaryonFluidState frozen dataclass (δ_b, v_b tuple of 3 components)
2. BaryonParameters with R_b as function of z
3. baryon_euler_rhs(state, theta_1, psi, R_b, tau_dot, H)
4. baryon_continuity_rhs(state, k, phi_prime)
5. tight_coupling_limit test: τ̇ → ∞ ⇒ 3Θ_1 → v_b

Gating via W3 canonical_decision.

TDD (~35 tests):
  test_baryon_state_construction
  test_baryon_continuity_homogeneous_bianchi
  test_baryon_euler_thomson_drag_sign
  test_momentum_conservation_photon_baryon
  test_tight_coupling_limit_lock
  test_R_b_temperature_scaling
  test_w3_gating_all_entries

성공 기준:
  PASS: τ̇/H > 10 regime에서 |3Θ_1 - v_b|/|3Θ_1| < 0.01
  WARN: sound speed c_s² = 1/(3(1+R_b)) recovery within 5%
  FAIL: momentum conservation residual > 1e-10

CRAG: diagram showing photon-baryon lock at high τ̇, decoupling at z~1074.

Honest scope note in docstring:
  "First-order baryon fluid on orthogonal Bianchi. CDM not yet included
   (W6-03). Photon-baryon slip beyond leading-order not included (deferred
   to W6-04 2nd-order TCA matching Document 12 §1 ceiling)."
```

---

## PROMPT W6-02: ℓ=1 dipole drive in photon hierarchy

**Type**: SOLVER-IMPL | **Techniques**: PAL + CoVe
**Depends**: W6-01 | **Est.**: ~250 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: W5-A multipole_hierarchy에 ℓ=1 equation을 다음으로 확장:
  Θ̇_1 + Γ Θ_1 = k_eff[1/3 Θ_0 - 2/3 Θ_2]
                 + (4/3)(k/S) A_1     ← ACCELERATION DRIVE
                 + τ̇(v_{b,1} - Θ_1)   ← DOPPLER DRIVE
                 + ... (shear only at ℓ=2 as before)

where A_a is the tilt-induced four-acceleration at ℓ=1.

In homogeneous Bianchi limit (D_a → 0):
  Θ̇_1 + Γ Θ_1 = τ̇(v_{b,1} - Θ_1) + A_1 contribution from tilt

R-TILT-03 connection: A_a from tilt gradient ∂_a β, at support boundary
of W_R in W12. For W6 scope, A_a treated as external input parameter.

구현 (modify bass/transport/multipole_hierarchy.py):
1. Add dipole_drive_vector: contributions at ℓ=1
2. source_vector_full: now includes δ_{ℓ,1} and δ_{ℓ,2} drives
3. New parameter BaryonCouplingParameters(R_b, v_b, tau_dot)
4. Backward-compatible: if BaryonCoupling=None, fall back to W5-A behavior

TDD (~40 tests):
  test_dipole_equation_no_shear_no_tilt_zero_source
  test_dipole_equation_tilt_drive_only
  test_dipole_equation_thomson_drag_lock_to_vb
  test_W5A_backward_compatibility_without_baryon
  test_bianchi_homogeneous_limit_structure
  test_momentum_conservation_with_baryon_coupling
  test_four_acceleration_input_validation

성공 기준:
  PASS: A_1 = v_b = 0 → W5-A solution bit-exact
  PASS: high τ̇ regime → Θ_1 lock to v_b within 1%
  FAIL: dipole drive structure inconsistent with ch05 Eq. photon-dipole

CRAG: showing dipole source decomposition (intrinsic / tilt / Doppler)
vs η.

Honest scope: "ℓ=1 drive in homogeneous Bianchi. Spatial D_a terms
deferred to W9 (line-of-sight). k-gradient source (4/3)(k/S) A_k
treated as external input per R-TILT-03 §1 for now."
```

---

## PROMPT W6-03: CDM state (collisionless dust closure)

**Type**: SOLVER-IMPL | **Techniques**: PAL + CoVe
**Depends**: W6-01 | **Est.**: ~200 lines | **Think**: T2 | **Web**: W0

```
[web:off] [think:standard]

목표: CDM state (δ_c, v_c^a) 추가. ZERO collision (collisionless).

물리:
  δ_c' = -k v_c - 3Φ'
  v_c' + H v_c = k Ψ    [no Thomson, no tilt drive in first pass]

주의 (baryon_CDM_문제 per memory):
  CDM 4 DOF is "cold single-stream (dust) closure"
  π_c = 0 is exact WITHIN THE MODEL assumption (not kinetic theory exact).
  Level 2 upgrade candidate: velocity-dispersion tensor σ^(v)_{ij}
  — explicitly deferred to bass_rs.

구현 (new file: bass/perturbation/cdm_fluid.py):
1. CDMFluidState frozen dataclass
2. cdm_continuity_rhs
3. cdm_euler_rhs (no collision terms)
4. Integration with gravity (Ψ) — external input for W6, becomes self-
   consistent after W9

TDD (~20 tests):
  test_cdm_no_collision_identity
  test_cdm_continuity_homogeneous_bianchi
  test_cdm_euler_gravity_only
  test_cdm_decoupled_from_thomson

성공 기준:
  PASS: CDM evolution independent of τ̇
  PASS: gravitational instability recovery (δ_c growth in matter era)

Honest scope: "Dust closure with π_c = 0. Velocity dispersion tensor
is upgrade candidate deferred to bass_rs."
```

---

## PROMPT W6-04: Quadrupole-aware TCA closure (2nd-order)

**Type**: SOLVER-IMPL | **Techniques**: PAL + Self-Refine + CRAG
**Depends**: W6-02 | **Est.**: ~350 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: explicit (Θ_2, E_2) 2-variable closure를 CAMB/CLASS-style 2차
TCA로 구현한다. Document 12 §1 ceiling 해소의 핵심.

물리 (CAMB-TCA mapping doc §7.3):
  Leading order (with polarization feedback):
    π_γ = (32/45)(k/κ')(σ + 3q_γ/4)
    E_2 = π_γ / 4

  2-variable closure (Document 8 §7):
    Θ̇_2^m = S_{2,T}^m + Γ_T(-9/10 Θ_2^m - √6/10 E_2^m)
    Ė_2^m = S_{2,E}^m + Γ_T(-2/5 E_2^m - 3/(5√6) Θ_2^m)

  At tight coupling (Θ̇ = Ė = 0), these become:
    0 ≈ S_{2,T}^m + Γ_T(-9/10 Θ_2^m - √6/10 E_2^m)
    0 ≈ S_{2,E}^m + Γ_T(-2/5 E_2^m - 3/(5√6) Θ_2^m)

  equivalently Γ_T M · X = +S:

  Matrix form:
    Γ_T [9/10  √6/10 ] [Θ_2]   [S_{2,T}]
        [3/(5√6) 2/5 ] [E_2] = +[S_{2,E}]

  Leading TCA closure (invert, with M^{-1} = [[4/3, -√6/3], [-√6/3, 3]]):
    Θ_2^m = +Γ_T^{-1}[(4/3)S_{2,T}^m - (√6/3)S_{2,E}^m] + O(Γ_T^{-2})
    E_2^m = +Γ_T^{-1}[-(√6/3)S_{2,T}^m + 3 S_{2,E}^m] + O(Γ_T^{-2})

  Physical check: S_T > 0 (positive shear) → Θ_2 > 0 (positive
  anisotropic stress), consistent with CAMB π_γ ≈ (32/45)κ̇⁻¹(σ+3q_γ/4).

  If S_{2,E} subleading:
    E_2 ≃ -(√6/4)Θ_2
    Π^m = Θ_2^m - √6 E_2^m ≃ (5/2)Θ_2^m

  Combined source:
    ζ = (3/4)I_2 + (9/2)E_2  [CAMB notation: polter = pig/10 + 9 E_2/15 = (2/15)ζ]

구현 (new file: bass/closure/quadrupole_tca.py):
1. build_tca_matrix(gamma_T) → 2x2 matrix
2. solve_tca_closure(S_T, S_E, gamma_T) → (Θ_2, E_2)
3. combined_source_pi(theta_2, E_2) → Π
4. polter(pig, E_2) → CAMB combined source notation
5. Second-order correction (Cyr-Racine Sigurdson):
   factor (1 + 11 κ̈/(6 κ'²))
6. Toggle: use_second_order_TCA: bool (default True)

TDD (~45 tests):
  test_matrix_assembly_analytic
  test_leading_order_closure_formula
  test_E2_pig_quarter_approximation
  test_pi_combined_source_leading
  test_polter_camb_notation_match
  test_second_order_correction_sign
  test_tca_flrw_scalar_limit_recovery
  test_tilted_quadrupole_closure_branch
  test_stability_high_gamma_T
  test_small_S_E_asymptotic

성공 기준:
  PASS: FLRW scalar limit → CAMB (32/45)(k/κ')(σ + 3q_γ/4) recovery
  PASS: 2nd-order correction factor within 0.1% of CRS formula
  PASS: Π^m ≃ (5/2)Θ_2^m when S_{2,E} subleading
  WARN: deep-stiff regime (Γ_T > 10^6) shows 2-3% drift

CRAG: comparison plot of 1st vs 2nd order TCA in transition regime.

Honest scope: "2nd-order TCA per CAMB notes §7.4 + CRS corrections.
For tilted Bianchi, variables should be tilded per Document 8 §7.
Tilded branch implemented but full frame-change boost deferred to W12."
```

---

# §4. W7 — E-mode polarization hierarchy

**Motivation**: Document 14 (§7 in earlier knowledge base) establishes the
E-mode hierarchy with modified streaming coefficients, and R-TILT-03 §3.2
requires EE for the cosmological-tilt signature. W5-A/B/C only evolved
intensity; polarization was collapsed into quasi-static $E_2 = \Theta_2/4$.

## PROMPT W7-01: E-mode multipole state + streaming coupling

**Type**: SOLVER-IMPL | **Techniques**: PAL + Analogical
**Depends**: W6-04 | **Est.**: ~400 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: E-mode hierarchy E_ℓ^m (ℓ≥2) with spin-2 streaming coefficients.

물리 (Document 14 §7 + Challinor 1999 polarization):
  Ė_ℓ^m + Γ_T E_ℓ^m = k_eff [α_ℓ^{m,E} E_{ℓ-1}^m - β_ℓ^{m,E} E_{ℓ+1}^m]
                      + collision source at ℓ=2
                      + mixing from temperature quadrupole

  E-mode streaming coefficients (spin-2):
    α_ℓ^{m,E} = √[(ℓ²-m²)(ℓ²-4)] / [ℓ(2ℓ+1)]
    β_ℓ^{m,E} = √[((ℓ+1)²-m²)((ℓ+1)²-4)] / [(ℓ+1)(2ℓ+1)]

  Note: additional factor [(ℓ+3)(ℓ-1)]/[(2ℓ+1)(ℓ+1)] for β compared
  to intensity (CAMB-TCA doc §4.3). This is the transverse-traceless
  projection factor.

  Collision source at ℓ=2 (Pontzen-Challinor harmonic notation,
  Document 8 §6.2):
    (DE_2^m/Dη)_coll = Γ_T[-E_2^m + (3/5)(E_2^m - Θ_2^m/√6)]
                     = -Γ_T(2/5 E_2^m + 3/(5√6) Θ_2^m)

  B-mode: ℓ=0 and ℓ=1 vanish (spin-2 constraint). B is NOT sourced
  directly by Thomson scattering at linear order in FLRW. In Bianchi,
  background polarization-basis rotation generates E→B mixing — but
  that's W9+ scope. First pass: evolve B trivially as zero in FLRW limit.

구현 (new file: bass/transport/emode_hierarchy.py):
1. EModeState frozen dataclass (E_ℓ for ℓ=2..L_max, per m)
2. pstf_emode_coupling_coeffs(ell, m) → (α^E, β^E)
3. build_emode_streaming_matrix(k_eff, L_max, m)
4. build_emode_source_vector(S_E_2, L_max, m)
5. compute_emode_steady_state (linsolve with proper damping)
6. integrate_emode_to_steady_state (using W5-B implicit integrator)

TDD (~55 tests):
  test_emode_coupling_coefficients_analytic
  test_emode_alpha_beta_vs_intensity_differ
  test_ell_min_2_constraint (E_0 = E_1 = 0)
  test_emode_source_only_at_ell_2
  test_emode_hierarchy_m0_fcli_limit
  test_emode_collision_structure
  test_tca_closure_feeds_emode_hierarchy
  test_transverse_traceless_factor_recovery
  test_integration_to_steady_state

성공 기준:
  PASS: coefficient formula rel err < 1e-14
  PASS: m=0 axisymmetric case, E_2 from TCA matches single-ℓ
  FAIL: if α^E, β^E don't reduce to Thomson ΔE_ℓ = 0 in FLRW isotropic

CRAG: comparison of I-mode vs E-mode streaming coefficients.

Honest scope: "E-mode free-streaming + Thomson collision. E→B mixing
from background polarization basis rotation (Pontzen-Challinor §4) is
deferred to W9 line-of-sight integration."
```

---

## PROMPT W7-02: Polter recoupling — close the collision loop

**Type**: SOLVER-IMPL | **Techniques**: PAL + Self-Consistency + CRAG
**Depends**: W7-01, W6-04 | **Est.**: ~300 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: W6-04 quadrupole TCA와 W7-01 E-mode hierarchy를 polter 
combination으로 완전 결합.

물리 (CAMB-TCA mapping doc §1):
  polter = pig/10 + 9 E_2 / 15
         = (3 I_2 + 18 E_2) / 30
         = (2/15) ζ  where ζ = (3/4) I_2 + (9/2) E_2

  Verification: (2/15) × [(3/4) I_2 + (9/2) E_2]
                = (2/15)(3/4) I_2 + (2/15)(9/2) E_2
                = (1/10) I_2 + (3/5) E_2  ✓  matches pig/10 + 9 E_2/15

  Collision source at ℓ=2 in CAMB sign convention:
    C_I_2 = -κ' × (I_2 - polter × factor)
    C_E_2 = -κ' × (E_2 + polter × E-factor)

  The combined source ζ propagates through BOTH hierarchies.
  This closes the Thomson collision loop that was open in W6-04
  (which assumed E_2 = π_γ/4 algebraically).

구현 (new file: bass/closure/polter_recoupling.py):
1. compute_polter(pig: float, E_2: float) → float
2. collision_source_I2(polter: float, Gamma_T: float) → float
3. collision_source_E2(polter: float, Gamma_T: float) → float
4. full_recoupled_tca(S_T, S_E, Gamma_T) → (Θ_2, E_2, Π, polter)
   — full 2x2 solve with polter in source, not just quasi-static
5. Upgrade toggle: use_polter_recoupling vs use_TCA_leading
   (both active; recoupling default for production)

TDD (~35 tests):
  test_polter_formula_camb_exact
  test_ratio_pig_to_E2_after_recoupling
  test_collision_source_closes_loop
  test_recoupled_vs_leading_tca_agreement_smallGamma
  test_recoupled_tca_damping_recovery
  test_flrw_scalar_polter_matches_camb_fortran
  test_tilted_extension_via_tilded_variables
  test_E2_not_just_quarter_pig_in_general

성공 기준:
  PASS: leading TCA recovery at Γ_T → ∞
  PASS: polter sign matches CAMB sign convention (E_2 opposite to literature)
  PASS: recoupled E_2/π_γ ratio deviates from 1/4 in transition regime
  FAIL: if dynamics shows no E-mode feedback to intensity quadrupole

CRAG: E_2/π_γ ratio vs Γ_T showing deviation from quasi-static 1/4.

Honest scope: "Full collision recoupling via polter. This closes the
Thomson loop — intensity and E-mode quadrupoles now cross-feed through
the collision kernel as in CAMB. Sign convention flagged per CAMB notes
(code's E_2 opposite to Challinor 1999 convention)."
```

---

# §5. W8 — Visibility + reionization

**Motivation**: D_ℓ output requires visibility-weighted source integral
(Document 12 §2). Recombination visibility + reionization bump are core.
R-TILT-02 §3.3 Pastén connection also lives here.

## PROMPT W8-01: Recombination history ingest + visibility g(η)

**Type**: SOLVER-IMPL | **Techniques**: PAL + CoVe
**Depends**: W7-02 | **Est.**: ~350 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: isotropic recombination history (x_e(η), T_m(η))를 외부 소스
(RECFAST table or HyRec output)에서 ingest. visibility function g(η)
계산.

물리 (standard):
  Γ_T(η) = a(η) n_e(η) x_e(η) σ_T
  κ(η) = ∫_η^η_0 Γ_T(η') dη'
  g(η) = Γ_T(η) exp(-κ(η))

  g(η) peaks at recombination (z ~ 1074) and drops to zero by z ~ 800.

스코프 제한 (Document 8 §8): 
  "first pass에서는 (x_e(η), T_m(η))는 standard isotropic history
   그대로. 미세구조 anisotropization은 bass_rs 영역."

구현 (new file: bass/history/recombination_adapter.py):
1. RecombinationHistory frozen dataclass:
   (eta_grid, xe_grid, Tm_grid, metadata)
2. load_recfast_table(path) → RecombinationHistory
3. load_hyrec_output(path) → RecombinationHistory
4. compute_optical_depth(history, a_grid, ne_interp) → kappa(η)
5. compute_visibility(history, kappa) → g(η)
6. visibility_peak_location(g_array, eta_array) → eta_star

TDD (~40 tests):
  test_recfast_ingest_structure
  test_xe_monotonic_during_recombination
  test_visibility_peak_at_z_1074
  test_optical_depth_monotone_decreasing
  test_g_integral_to_unity
  test_external_history_does_not_bypass_w3_gate

성공 기준:
  PASS: g(η) peak at z = 1074 ± 10
  PASS: ∫g dη = 1 (normalization) within 0.1%
  PASS: compatibility with any external recombination code (modular)

Honest scope: "Isotropic x_e(η) from external recombination code.
Direction-dependent recombination (δτ'(n̂), anisotropic Peebles C)
is bass_rs territory."
```

---

## PROMPT W8-02: Reionization tanh history + late-time g bump

**Type**: SOLVER-IMPL | **Techniques**: PAL
**Depends**: W8-01 | **Est.**: ~200 lines | **Think**: T2 | **Web**: W0

```
[web:off] [think:standard]

목표: reionization을 tanh model로 추가. low-ℓ EE/TE의 핵심.

물리 (Lewis 2008 standard form):
  x_e^rei(z) = (x_e,post/2) [1 + tanh((y(z_re) - y(z))/Δy)]
  y(z) = (1+z)^{3/2}
  z_re ≃ 7.7 (Planck 2018), Δz ≃ 0.5
  τ_rei ≃ 0.0544

구현 (new file: bass/history/reionization_tanh.py):
1. TanhReionization parameters (z_re, delta_z, x_e_post)
2. xe_tanh(z, params) → x_e
3. combine_recombination_reionization(history_rec, rei_params) → full
4. compute_tau_reio(a_grid, ne_interp) → τ_rei
5. double_reionization option (HeII bump at z ~ 3.5)

TDD (~25 tests):
  test_xe_asymptotic_pre_reio_matches_recombination
  test_xe_asymptotic_post_reio_equals_unity
  test_tanh_midpoint_at_z_re
  test_planck_tau_reio_recovery
  test_visibility_has_reionization_bump_at_z7
  test_double_reionization_HeII

성공 기준:
  PASS: τ_rei(z_re=7.7) = 0.0544 ± 0.001
  PASS: visibility has secondary peak at z~7
  PASS: low-ℓ EE impact visible in downstream W10 output

Honest scope: "Homogeneous x_e^rei(z). Patchy reionization deferred
to bass_rs. Second-peak visibility bump is critical for low-ℓ EE
(Document 6 §4 strong recommendation)."
```

---

## PROMPT W8-03: g·Π source assembly

**Type**: SOLVER-IMPL | **Techniques**: PAL + Self-Refine
**Depends**: W8-02 | **Est.**: ~250 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: visibility-weighted quadrupole source for line-of-sight integration.

물리 (Document 6 §4 + CAMB-TCA doc):
  For TT:  S_T(η) = g(η) [Θ_0 + Ψ + (dipole terms) + polter/10]
  For EE:  S_E(η) = g(η) × polter × (spin-2 projection factor)
  
  Note: S_T, S_E are sources BEFORE projection integrals.
  Projection kernels → a_{ℓm} are in W9.

  R-TILT-03 §3 connection:
    At W8 level, S_T and S_E already carry the tilt signature difference:
      - Local motion: modifies Θ_0, Θ_1 via boost (no effect on Θ_2, E_2)
      - Cosmological tilt: modifies σ and hence Θ_2, E_2
      - Tilt² cross-terms: appear in higher-order S

구현 (new file: bass/source/visibility_weighted_source.py):
1. assemble_temperature_source(bass_state, history) → S_T(η) grid
2. assemble_polarization_source(bass_state, history) → S_E(η) grid
3. source_decomposition into {SW, Doppler, ISW, pol}
4. diagnostic: integrated source ∫|S_T|² dη (variance proxy)
5. Honest flag: source modifications for local-motion-only vs cosm-tilt

TDD (~35 tests):
  test_S_T_only_nonzero_near_visibility_peak
  test_S_E_zero_if_polter_zero
  test_source_decomposition_sum_identity
  test_local_motion_only_affects_dipole
  test_cosmological_tilt_affects_quadrupole
  test_flrw_isotropic_matches_standard_camb_sources

성공 기준:
  PASS: source peak at visibility peak
  PASS: local-motion vs cosm-tilt signatures distinguishable at source level
  PASS: FLRW scalar isotropic source matches standard CAMB source structure

Honest scope: "Visibility-weighted sources for line-of-sight. Isotropic
recombination visibility (no direction-dependent δτ). Local and cosm
tilt signatures distinguishable at source level per R-TILT-03 §3."
```

---

# §6. W9 — Line-of-sight integration

**Motivation**: Document 6 §5 + Document 7 §11 specify the transition from
FLRW $j_\ell$ kernel to anisotropic matrix propagator. Critical for
direction-dependent $a_{\ell m}$.

## PROMPT W9-01: FLRW Bessel kernel baseline

**Type**: SOLVER-IMPL | **Techniques**: PAL + Analogical + CoVe
**Depends**: W8-03 | **Est.**: ~400 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: Standard FLRW line-of-sight integration (Seljak-Zaldarriaga 1996).
FLRW limit이 정확히 작동해야 W10에서 CAMB 비교 가능.

물리:
  Transfer function for scalar mode:
    Δ_ℓ^T(k) = ∫ dη S_T(k, η) j_ℓ[k(η_0 - η)]
    Δ_ℓ^E(k) = ∫ dη S_E(k, η) × [transverse-traceless projection] × j_ℓ
    
  For E-mode:
    √[(ℓ+2)!/(ℓ-2)!] / [k(η_0-η)]² × j_ℓ[k(η_0-η)]
    = √[(ℓ-1)ℓ(ℓ+1)(ℓ+2)] × j_ℓ / [k(η_0-η)]²

구현 (new file: bass/los/flrw_bessel_projector.py):
1. spherical_bessel_grid(ell_max, kr_grid) → lookup table
2. project_temperature_to_alm(S_T, k, eta_grid, ell_max) → a_{ℓ0}^T
   (scalar mode: m=0 only in FLRW)
3. project_polarization_to_alm(S_E, k, eta_grid, ell_max) → a_{ℓ0}^E
4. diagnostic: convergence vs eta resolution
5. FLRW_identity_test: isotropic source input → a_{ℓ0} only (m=±1,±2 = 0)

TDD (~40 tests):
  test_bessel_orthogonality_numerical
  test_isotropic_source_only_m0
  test_integration_convergence_halving_dη
  test_ell_range_no_off_by_one
  test_E_mode_projection_factor_formula
  test_analytic_sharp_visibility_approximation

성공 기준:
  PASS: ∫j_ℓ² dk recovers analytic normalization within 0.1%
  PASS: isotropic S_T → a_{ℓ0} only, m≠0 coefficients < 1e-10
  PASS: convergence at dη = 0.1 Mpc (FLRW default resolution)

Honest scope: "FLRW Bessel baseline. Bianchi extension (matrix propagator)
in W9-02. This module is the reference that must be recovered as Σ → 0
limit of any Bianchi calculation."
```

---

## PROMPT W9-02: Matrix propagator for Bianchi I (m∈{0,±2})

**Type**: SOLVER-IMPL | **Techniques**: PAL + Graph-of-Thoughts + Reflexion
**Depends**: W9-01, W5-C | **Est.**: ~600 lines | **Think**: T4 | **Web**: W0

```
[web:off] [think:heavy]

목표: anisotropic background propagator 구현. W5-C의 m∈{0,±2} 채널이
line-of-sight 단계에서 어떻게 각 m 채널로 투영되는지 계산.

물리 (Document 6 §5 + Document 7 §11):
  State vector: X(η) = {Θ_{ℓm}, E_{ℓm}, B_{ℓm}}, ℓ≤L_max, m∈{0,±2}
  Evolution:
    X'(η) = L_B[σ_ab] X(η) + C_T[v_e] X(η) + S_pert[v_e](η)
  Formal solution:
    X(η_0) = P exp[∫ L_B + C_T dη] X(η_*)
             + ∫ P exp[∫ L_B + C_T dη'] S_pert(η) dη

  For orthogonal Bianchi I (A_a = 0, ω_a = 0), L_B contains:
    - Shear-induced m-mixing at same ℓ
    - No polarization-basis rotation (ψ' = 0 for Type I per
      Pontzen-Challinor "n_3 = n_2" case)
  
  This simplifies considerably vs general Bianchi VIIh. For Bianchi I
  first pass, E→B mixing remains negligible.

Step-Back:
  1. Why matrix propagator at all?
     Because σ_ab at the source eta couples Θ_{ℓ,±2} to Θ_{ℓ,0}
     during propagation. FLRW j_ℓ cannot carry this.
  2. What's the minimum change from FLRW?
     Per m channel, projection from ℓ_source to ℓ_obs:
       Δ_ℓ^{m=0} projects like scalar
       Δ_ℓ^{m=±2} projects like tensor (different Bessel-like kernels)
     For pure Bianchi I (no polarization rotation), each m evolves
     independently to observer.

구현 (new file: bass/los/bianchi_propagator.py):
1. compute_m0_projector (reduces to FLRW Bessel)
2. compute_m2_projector (tensor-mode Bessel combination, for |m|=2)
3. matrix_propagator_m0_m2 (block-diagonal if no E/B mixing)
4. project_bianchi_I_to_alm (uses W5-C output + matrix propagator)
5. FLRW recovery test: σ → 0 must recover W9-01 bit-exact

TDD (~50 tests):
  test_m0_projector_reduces_to_flrw_bessel
  test_m2_projector_tensor_pattern
  test_flrw_recovery_bit_exact
  test_bianchi_i_m2_channel_nonzero
  test_block_diagonal_no_EB_mixing
  test_direction_dependent_alm_output
  test_m_plus_minus_2_symmetry
  test_propagator_stability_moderate_sigma

성공 기준:
  PASS: σ→0 recovery bit-exact to W9-01
  PASS: σ > 0 produces a_{ℓ,±2} ≠ 0 as expected from W5-C
  WARN: E→B leakage should be <1e-8 for Bianchi I (physical floor)
  FAIL: if m-channel outputs not consistent with W5-C amplitudes

CRAG: 4-panel figure showing σ ladder (0, 1e-8, 1e-6, 1e-4) effect on
a_{ℓm} pattern.

Honest scope: "Matrix propagator for orthogonal Bianchi I with
axisymmetric shear. Full polarization rotation (Bianchi VIIh, IX) and
tilt-induced basis change are bass_rs scope. E→B mixing floor validated
for Bianchi I specifically."
```

---

# §7. W10 — C_ℓ assembly + D_ℓ output

**Motivation**: This closes the forward spectrum generator deliverable.
All prior W work converges here. Output: $D_\ell^{TT}$, $D_\ell^{EE}$.

## PROMPT W10-01: C_ℓ TT/EE from a_{ℓm}

**Type**: SOLVER-IMPL | **Techniques**: PAL + Self-Consistency + CRAG
**Depends**: W9-02 | **Est.**: ~450 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: a_{ℓm}를 primordial power spectrum P(k)와 합성해서 C_ℓ^TT, C_ℓ^EE
생성. D_ℓ = ℓ(ℓ+1)C_ℓ/(2π) × T_CMB² 출력.

물리:
  Isotropic (FLRW) case:
    C_ℓ = 4π ∫ d(ln k) P(k) × Σ_m |Δ_ℓ^m(k)|²
    
  Anisotropic (Bianchi I) case:
    C_{ℓm,ℓ'm'} = 4π ∫ d(ln k) P(k) × Δ_ℓ^m(k) Δ_{ℓ'}^{m'*}(k)
    
    Isotropic diagonal part: C_ℓ
    Off-diagonal m-m' pieces enter BiPoSH (W11)
    
  Route B validation (memory):
    D_2(Σ²=1e-8) = 0.1741 μK² (ESTABLISHED per d2_convention.rs)
    
구현 (new file: bass/spectrum/cl_assembly.py):
1. assemble_isotropic_cl_TT(alm_T, pk) → C_ℓ
2. assemble_isotropic_cl_EE(alm_E, pk) → C_ℓ
3. assemble_cross_cl_TE(alm_T, alm_E, pk) → C_ℓ^TE
4. compute_Dl(Cl, ell_array, T_CMB=2.7255) → D_ℓ
5. D_2_sentinel(Sigma_squared) → production D₂ value

TDD (~40 tests):
  test_isotropic_cl_positivity
  test_D_2_value_matches_production_sigma_1e8
  test_D_l_scaling_with_Sigma_squared (linear at small Σ²)
  test_Michaelis_Menten_C1_C2_recovery
  test_cross_TE_sign_convention
  test_high_ell_convergence_plateau

성공 기준:
  PASS: D₂(Σ²=1e-8) = 0.1741 μK² (anti-regression guard)
  PASS: D_ℓ ∝ Σ² over 4 decades (linear regime)
  PASS: Michaelis-Menten C_1, C_2 within 0.5%

Honest scope: "C_ℓ assembly for ℓ≤30. Higher-ℓ convergence is not a
bass_py guarantee. Planck/ACT comparison requires external likelihood
pipeline (HTT integration)."
```

---

## PROMPT W10-02: FLRW→CAMB validation gate (V1)

**Type**: VALIDATION | **Techniques**: CRITIC + Multi-Agent Debate
**Depends**: W10-01 | **Est.**: ~350 lines | **Think**: T4 | **Web**: W1

```
[web:minimal] [think:heavy]

목표: FLRW limit에서 bass_py의 C_ℓ^TT, C_ℓ^EE를 CAMB v1.6.6과 비교.
첫 번째 "데이터 노출" validation gate.

테스트 프로토콜:
1. CAMB를 Planck 2018 cosmology로 실행, ℓ=2..30의 TT, EE C_ℓ 저장
2. bass_py를 동일 cosmology + σ = 0 + β = 0으로 실행
3. per-ℓ relative error 계산: |C_ℓ^bass - C_ℓ^CAMB| / C_ℓ^CAMB
4. 3개 tier로 분류:
   - ℓ=2..5: accuracy tier A (target < 5%)
   - ℓ=6..15: accuracy tier B (target < 10%)
   - ℓ=16..30: accuracy tier C (target < 15%)

Document 12 ceiling analysis 연결:
  85% current → 95% target via:
    - 2nd-order TCA (W6-04) ✓
    - Visibility-weighted integral (W8-03) ✓
    - L=4 min, L=6 default (W5-A coverage) ✓

Adversarial self-ask:
  Q: 왜 CAMB와 100% 일치는 불가능?
  A: (a) FLRW recombination model 차이 (RECFAST vs HyRec)
     (b) k-grid 해상도
     (c) absent ℓ≥3 backreaction in bass_py (bass_rs scope)
     (d) baryon-photon slip beyond 2nd-order TCA
     → 5-15% tier targets are HONEST given these

CRITIC:
  Q: 만약 tier C에서 < 5%가 나오면?
  A: 과적합 의심. source decomposition으로 분리해서 지금 쓰는 physics가
     CAMB에 없는 effect를 포함하는지 확인.
  Q: 만약 tier A에서 > 10%가 나오면?
  A: P0 failure. source/TCA/recombination 어느 쪽에 bug인지 진단:
     - TT만 틀림 → SW/ISW source
     - EE만 틀림 → polter recoupling (W7-02)
     - 둘 다 → recombination history ingest (W8-01)

구현 (new file: bass/validation/flrw_camb_gate.py):
1. load_camb_reference(camb_version="1.6.6") → Cl_T, Cl_E arrays
2. compute_bass_flrw_spectrum(cosmology_params) → Cl_T, Cl_E
3. per_ell_relative_error(bass_Cl, camb_Cl, ell_array) → errors
4. tier_classification(errors, ell_array) → {A: pass/fail, B: ..., C: ...}
5. generate_validation_packet(results) → markdown report

TDD (~30 tests):
  test_camb_ingest_structure
  test_per_ell_relative_error_formula
  test_tier_boundaries
  test_zero_error_identity (bass_Cl = camb_Cl)
  test_systematic_offset_detection
  test_V1_gate_all_tiers_pass_or_fail_classification

성공 기준:
  V1 PASS: all three tiers within target
  V1 WARN: tier B or C miss target by < 5% (documented, move to W11)
  V1 FAIL: tier A miss OR any tier miss by > 10%

CRAG: 4-panel figure: Cl_T overlay, Cl_E overlay, residual vs ℓ,
tier classification heatmap.

Honest scope declaration:
  "bass_py FLRW accuracy: tier A <5%, tier B <10%, tier C <15%.
   This is NOT CAMB equivalence — this is 'honest first-exposure' scope.
   Full CAMB accuracy achieved by Rust bass_rs."
```

---

# §8. W11 — Direction-dependent C_ℓ(n̂) + BiPoSH

**Motivation**: Statistical isotropy breaks in Bianchi. $C_\ell$ alone
loses information. Need $C_{\ell m, \ell' m'}$ (direction-dependent) +
BiPoSH.

## PROMPT W11-01: Direction-dependent C_ℓ(n̂)

**Type**: SOLVER-IMPL | **Techniques**: PAL + Graph-of-Thoughts
**Depends**: W10-02 | **Est.**: ~500 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: direction-dependent power C_ℓ(n̂) 계산. W5-C의 m 채널 구조가
여기서 직접 관측된다.

물리 (Hajian-Souradeep 2003):
  C_ℓ(n̂) = Σ_m C_{ℓm} |Y_ℓ^m(n̂)|²
  
  For Bianchi I (aligned with z-axis):
    C_{ℓ, m=0} from m=0 channel of W5-C
    C_{ℓ, m=±2} from m=±2 channel of W5-C
    C_{ℓ, m=±1} = 0 (diagonal shear doesn't excite)
  
  Direction posterior input: axis (l, b) describes σ_ab orientation

구현 (new file: bass/spectrum/direction_dependent_cl.py):
1. direction_dependent_cl_map(Cl_lm_dict, nside=16) → HEALPix map
2. axis_rotation(Cl_lm_dict, l_deg, b_deg) → rotated Cl_{lm}
3. cl_moments(C_n): spherical mean, dipole, quadrupole of C_ℓ(n̂)
4. FLRW recovery test: isotropic → C_ℓ(n̂) = const
5. Visualization: Mollweide projection of C_ℓ(n̂)

TDD (~35 tests):
  test_cl_n_flrw_constant
  test_cl_n_axis_aligned_m0_dominance
  test_cl_n_m2_pattern
  test_rotation_of_axis_shifts_pattern
  test_healpix_output_compatibility
  test_m_plus_minus_2_symmetric_pattern

성공 기준:
  PASS: σ=0 → C_ℓ(n̂) = const within 1e-10
  PASS: aligned Bianchi I axis → dipole/quadrupole of C_ℓ(n̂)
    detectable at σ² > 1e-10

Honest scope: "Direction-dependent C_ℓ for Bianchi I principal-axis
frame. Frame-misaligned shear (non-principal-axis) requires rotation
to principal axes — not yet automated."
```

---

## PROMPT W11-02: BiPoSH coefficients A^{LM}_{ℓ₁ℓ₂}

**Type**: SOLVER-IMPL | **Techniques**: PAL + CoVe + CRAG
**Depends**: W11-01 | **Est.**: ~400 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: BiPoSH coefficients — isotropy 위반의 quantitative measure.

물리 (Hajian-Souradeep 2003):
  A^{LM}_{ℓ₁ℓ₂} = Σ_{m₁,m₂} ⟨a_{ℓ₁m₁} a*_{ℓ₂m₂}⟩ × CG(ℓ₁m₁, ℓ₂m₂ | LM)
  
  Parity: A^{LM} = 0 for odd L + ℓ₁ + ℓ₂
  FLRW: A^{LM}_{ℓ₁ℓ₂} = C_ℓ δ_{ℓ₁ℓ₂} δ_{L0} δ_{M0}
  Bianchi: L=2 quadrupole breaks isotropy visibly
  
  Pastén bound connection (R-TILT-02 §3.3):
    BiPoSH at L=2, ℓ₁=ℓ₂=2 relates to u̇_a × Θ dipole
    → modernize COBE u̇/Θ < 1e-4 bound

구현 (new file: bass/spectrum/biposh.py):
1. clebsch_gordan_table(ell_max) → CG matrix lookup
2. compute_biposh_coefficients(alm, ell_max) → A^{LM}_{ℓ₁ℓ₂} dict
3. parity_filter (enforce L+ℓ₁+ℓ₂ even)
4. bianchi_i_biposh_L2_signature(sigma_squared) → prediction
5. Pastén-bound projection: A^{2M}_{22} → u̇/Θ estimate

TDD (~40 tests):
  test_clebsch_gordan_orthogonality
  test_flrw_biposh_diagonal_only
  test_parity_filter_odd_zero
  test_bianchi_L2_signature_nonzero_for_Sigma_gt_floor
  test_pasten_projection_bound_connection
  test_biposh_hermitian_property
  test_angular_momentum_triangle_inequality

성공 기준:
  PASS: FLRW → A^{LM} = 0 for L>0 within 1e-10
  PASS: Bianchi I at σ²=1e-6 → A^{2M}_{22} >> noise
  PASS: parity-forbidden entries numerically zero (< 1e-12)

Honest scope: "BiPoSH diagnostic for low-ℓ (ℓ₁,ℓ₂ ≤ 10). Higher-ℓ and
pure-B mode BiPoSH not in scope. Pastén bound projection is an
interpretive tool, not a computation."
```

---

## PROMPT W11-03: Bianchi→bass_rs validation gate (V2)

**Type**: VALIDATION | **Techniques**: CRITIC + CoVe
**Depends**: W11-02 | **Est.**: ~300 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: bass_rs가 동일 physics input에 대해 생성하는 direction-dependent
a_{ℓm}과 bass_py 결과 비교. bass_py가 데이터에 노출되기 전 마지막 gate.

테스트 프로토콜:
1. 동일 Bianchi I configuration (σ², axis) 선택
2. bass_rs에서 a_{ℓm}^{T,E} 생성 (HDF5 export)
3. bass_py에서 동일 config로 a_{ℓm}^{T,E} 생성
4. 비교:
   - Amplitude: |Δa_{ℓm}| / |a_{ℓm}^bass_rs|
   - Phase: arg(a_{ℓm}^py) - arg(a_{ℓm}^bass_rs)
   - m-channel partition: m=0, m=±2 agreement
5. Qualitative check: direction posterior의 peak location 일치

구현 (new file: bass/validation/bass_rs_cross_check.py):
1. load_bass_rs_output(hdf5_path) → a_{ℓm} arrays
2. compute_bass_py_equivalent(config) → a_{ℓm} arrays
3. amplitude_phase_comparison(bass_py, bass_rs) → report
4. direction_posterior_peak_check(py_axis, rs_axis) → offset in degrees

Kill criterion:
  - bass_rs not ready for cross-check: V2 is BLOCKED (accept W10-02 V1 
    as sufficient for first data exposure, with explicit "pending V2" tag)
  - If bass_rs ready but bass_py m=±2 amplitudes miss by > 20%: FAIL
  - Direction posterior peaks disagree by > 10°: FAIL

성공 기준:
  V2 PASS: m=0 amplitudes agree within 15%, m=±2 within 25%,
           direction peak within 5°
  V2 WARN: within 2x of targets above, documented
  V2 BLOCKED: bass_rs not ready (documented as such)

Honest scope: "V2 is a cross-code validation. Targets are CALIBRATION,
not accuracy demands — both codes have reduced-scope regimes. V2 PASS
indicates bass_py is consistent with bass_rs at the level where both
agree with physics."
```

---

# §9. W12 — W_R local patch solver (R-TILT-02 direct implementation)

**Motivation**: This is the spec's unique deliverable — discriminating
local motion ($W_R v_{\rm loc}$) from cosmological tilt. W12 implements
R-TILT-02 directly.

## PROMPT W12-01: W_R window function + regularity guards

**Type**: SOLVER-IMPL | **Techniques**: PAL + CoVe
**Depends**: W11-03 | **Est.**: ~300 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: R-TILT-02 §1-2에 명시된 W_R window를 구현. C² smoothness,
compact support, boundary regularity.

물리 (R-TILT-02 §1.2):
  W_R(r) = { 1                                           r ≤ R_inner
           { (1/2)[1 + cos(π(r - R_inner)/(R - R_inner))]  R_inner < r ≤ R
           { 0                                           r > R
  R_inner = (4/5)R,  taper width = R/5

  Properties:
    - C² at r = R (W_R = W_R' = W_R'' = 0)
    - C¹ at r = R_inner
    - max gradient = π/(2(R - R_inner)) = 5π/(2R)
    - R = 200 Mpc → max gradient ~ 0.04 Mpc⁻¹

  Regularity bound: |D_i v_loc^a| ≲ R⁻¹ |v_loc^a| naturally satisfied

  Boundary contribution to D_2 (R-TILT-02 §2.1):
    ~ (v_loc/c)² × (ℓ_D/R)² ~ 10⁻⁶ × 10⁻⁴ ~ 10⁻¹⁰
    (safely below pipeline sensitivity 10⁻⁶)

구현 (new file: bass/local_patch/window_function.py):
1. WindowConfig dataclass (R_Mpc, window_type: cosine|wendland)
2. raised_cosine_taper(r, R, R_inner) → W
3. wendland_c2_kernel(r, R) → W (alternative)
4. window_gradient(r, R, R_inner) → ∂_r W (vector returned)
5. regularity_monitor(W_array, v_loc_array) → passes |D_i v| < |v|/R
6. compact_support_guard: r > R → return 0 always (safety net)

TDD (~35 tests):
  test_w_at_center_equals_one
  test_w_at_R_equals_zero
  test_w_continuous_at_R_inner
  test_c2_at_R_vanishing_first_second_derivs
  test_max_gradient_formula
  test_boundary_contribution_below_sensitivity
  test_compact_support_strict
  test_regularity_bound_natural_satisfaction

성공 기준:
  PASS: W(0)=1, W(R)=0, W'(R)=0, W''(R)=0 exactly
  PASS: |∂_r W|_max = 5π/(2R) within 1e-12
  PASS: surface contribution to D_2 < 1e-10 for R=200 Mpc, v_loc=300 km/s

CRAG: window function profile, gradient profile, regularity metric.

Honest scope: "R-TILT-02 spec §1-2 directly implemented. R=200 Mpc is
DEFAULT (not mandatory — configurable per observer analysis). Patch
center at observer location; off-center patches require separate
implementation."
```

---

## PROMPT W12-02: Frame-attribution bias channel (Term 3)

**Type**: SOLVER-IMPL | **Techniques**: PAL + Self-Refine + CRAG
**Depends**: W12-01 | **Est.**: ~350 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: R-TILT-02 §3.1-3.2의 frame-attribution bias channel을 구현.
β ≤ ε_1/(1 + η_u̇) correction.

물리 (R-TILT-02 §3):
  Term 3 (2β^{⟨a} W_R v_loc^{b⟩}) is the channel through which
  frame-attribution bias operates.
  
  η_u̇ = 1/12 (production value per VT-07)
  Corrected safe-route: β ≤ ε_1 / (1 + η_u̇) = (12/13) ε_1

  Four-acceleration u̇_a:
    u̇_a = A_a + (terms from ∂_a β)
  
  At the W_R support boundary:
    ∂_a(W_R v_loc) contributes to u̇_a (bounded by C² smoothness)

  Pastén framework (R-TILT-02 §3.3):
    δz/(1+z) ⊃ ∫ u̇_a n^a dλ / H
    → modernize Stoeger-Araujo-Gebbie u̇/Θ < 10⁻⁴

구현 (new file: bass/local_patch/frame_attribution_bias.py):
1. compute_term3_source(beta, W_R, v_loc, v_loc_gradient) → tensor
2. eta_u_dot_correction(single_fluid=True) → 1/12 (production)
   (multi-fluid extension documented as TODO for bass_rs)
3. four_acceleration_from_tilt_gradient(W_R, v_loc) → u̇_a
4. pasten_projection(u_dot_local, Theta_expansion) → |u̇/Θ|
5. compare_to_COBE_bound(u_dot_over_theta) → ratio vs 1e-4

TDD (~30 tests):
  test_term3_structure_trace_free
  test_term3_vanishes_at_beta_zero
  test_term3_vanishes_outside_support
  test_eta_u_dot_value
  test_beta_max_corrected_bound
  test_four_acceleration_smooth_at_boundary
  test_pasten_projection_formula
  test_COBE_bound_local_scale_compatible

성공 기준:
  PASS: η_u̇ = 1/12 exact (production)
  PASS: β_max = (12/13) ε_1 for single-fluid
  PASS: u̇/Θ locally bounded < 10⁻³ (consistent with β scale)

CRAG: profile of u̇_a across W_R boundary; Pastén bound visualization.

Honest scope: "R-TILT-02 §3 directly implemented. Multi-fluid η_u̇
extension is bass_rs scope. Pastén bound is interpretive — not a
hard gate. Term 3 propagation to D_2 requires W13."
```

---

# §10. W13 — β→D_2 transfer function (R-TILT-03 direct implementation)

## PROMPT W13-01: Dynamical tilt source in shear equation

**Type**: SOLVER-IMPL | **Techniques**: PAL + Analogical
**Depends**: W12-02 | **Est.**: ~400 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: R-TILT-03 §2의 full dynamical vs MES algebraic 차이 구현.
tilt source as persistent regenerator of shear.

물리 (R-TILT-03 §2.1):
  σ̇_{⟨ab⟩} + Θ σ_{ab} + ³S_{ab} = κ [(ρ̂+p̂)Γ² v_{⟨a}v_{b⟩} + π_{ab}^{kinetic}]
  
  For radiation era (β frozen, w=1/3):
    σ_{ab}(η) ∝ a⁻³ × [decaying homogeneous]
                + ∫ κ π^{tilt}(η') G(η,η') dη'  [particular integral]

  The particular integral is NEW vs MES and represents the steady-state
  shear maintained by tilt.

  Magnitude for β = 1.36e-3, dust:
    π^{tilt}/ρ ~ β² ~ 1.85e-6
    σ/H ~ Ω_m β² / 2(1-q) ~ 3e-7
    → 3% correction to D_2 vs MES bound

구현 (new file: bass/einstein/shear_with_tilt_source.py):
1. tilt_anisotropic_stress(rho, p, Gamma_rapidity, v) → π^{tilt}_{ab}
2. shear_equation_rhs_with_tilt_source(sigma, pi_tilt, pi_kinetic,
                                        Theta_expansion) → σ̇
3. steady_state_shear_with_tilt(beta, cosmology) → σ/H estimate
4. compare_to_MES_algebraic(D2_dynamical, D2_MES) → correction factor

TDD (~35 tests):
  test_tilt_stress_beta_squared_scaling
  test_radiation_era_equilibrium
  test_matter_era_decay
  test_MES_recovery_for_tilt_zero
  test_3_percent_correction_magnitude_beta_1e_3
  test_shear_regeneration_particular_integral

성공 기준:
  PASS: π^{tilt}/ρ ~ β² within 5% (small-β regime)
  PASS: D_2^dynamical / D_2^MES ≈ 1 + 0.03 at β = 1.36e-3
  PASS: MES limit (β→0) bit-exact recovery

CRAG: shear evolution with tilt source on/off.

Honest scope: "Dynamical tilt source in shear equation. Feeds W13-02
(full transfer function). MES algebraic bound retained as validation
reference."
```

---

## PROMPT W13-02: Full β→D_2 transfer function via W10-01 pipeline

**Type**: SOLVER-IMPL | **Techniques**: PAL + Self-Consistency + CRAG
**Depends**: W13-01, W10-01 | **Est.**: ~400 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: β(η) → π^{tilt}(η) → σ(η) → Θ_{ab}^{(ν,γ)} → D_2 전체 chain을
W8-10 pipeline으로 통과. R-TILT-03의 §1 chain 완성.

물리:
  Currently in bass_rs (per memory):
    D_2 = C_1 Σ² / (1 + C_2 Σ²), Route B Michaelis-Menten
    
  Full dynamical (W13 target):
    D_2(Σ², β) = Σ_ℓ {contribution of W10-01 pipeline with tilt-regenerated σ}
    
    For orthogonal Bianchi (β=0): recover Route B exactly
    For tilted Bianchi (β>0): additional 3% correction at β=1.36e-3

구현 (new file: bass/transfer/full_dynamical_transfer.py):
1. compute_dynamical_D2(Sigma_squared, beta, cosmology) → D_2 full
2. compute_mes_algebraic_D2(Sigma_squared) → D_2 MES
3. tilt_correction_fraction(D2_full, D2_MES) → correction
4. Route_B_regression_guard: β=0 → Michaelis-Menten bit-exact
5. tilt_scaling_test: D_2 deviation vs β²

TDD (~30 tests):
  test_beta_zero_recovers_Route_B
  test_D_2_monotone_in_beta
  test_tilt_correction_scaling_beta_squared
  test_production_D2_at_sigma_1e8_beta_zero
  test_full_transfer_consistency

성공 기준:
  PASS: D_2(Σ²=1e-8, β=0) = 0.1741 μK² bit-exact
  PASS: D_2(Σ²=1e-8, β=1.36e-3) within 3-5% of Route B scaled
  PASS: Production D_2 SSOT regression guard preserved

CRAG: D_2(Σ², β) 2D surface plot.

Honest scope: "Full dynamical transfer function. Validates that Route B
MES bound remains useful for β=0 but misses 3% correction for realistic
tilt. Higher-order tilt (β³, β⁴) corrections are bass_rs scope."
```

---

# §11. W14 — TT-vs-EE discriminator (R-TILT-03 §3 the core deliverable)

## PROMPT W14-01: Three-signature separator

**Type**: SOLVER-IMPL | **Techniques**: PAL + Multi-Agent Debate + CRAG
**Depends**: W13-02 | **Est.**: ~500 lines | **Think**: T4 | **Web**: W0

```
[web:off] [think:heavy]

목표: R-TILT-03 §3의 three observational signatures를 bass_py에서
계산 가능하도록 코드 레벨에서 분리.

물리 (R-TILT-03 §3):
  Signature 1 (Local motion, TT-only):
    D_ℓ^{TT,local} = result of W_R v_loc (no Thomson amplification)
    D_ℓ^{EE,local} = 0  (Thomson isotropic in CMB rest frame)
    
  Signature 2 (Cosmological tilt, TT+EE):
    D_ℓ^{TT,cosm} ~ σ² ~ β²_cosm (from shear amplification)
    D_ℓ^{EE,cosm} ~ σ² ~ β²_cosm (from pre-recomb Thomson coupling)
    
  Signature 3 (Tilt² effective stress, scale-independent quadrupolar):
    Six cross-terms per R-TILT-01 (Complete tilt² cross-term table):
      1. β² 
      2. 2β^{⟨a} δβ^{b⟩}
      3. 2β^{⟨a} W_R v_loc^{b⟩}  ← frame-attribution channel
      4. δβ^{⟨a} δβ^{b⟩}
      5. 2δβ^{⟨a} W_R v_loc^{b⟩}
      6. W_R² v_loc^{⟨a} v_loc^{b⟩}

구현 (new file: bass/discriminator/tt_ee_separator.py):
1. compute_local_motion_signature(W_R, v_loc) → (D_TT_local, D_EE_local=0)
2. compute_cosmological_tilt_signature(beta_bar, sigma) → (D_TT_cosm, D_EE_cosm)
3. compute_tilt_squared_signatures(beta, delta_beta, W_R, v_loc) → 6 terms
4. assemble_total(local, cosmological, quadratic) → D_ℓ^TT, D_ℓ^EE
5. EE_TT_ratio_discriminator: R(ℓ) = D_ℓ^EE / D_ℓ^TT
   - R → 0 means pure local motion
   - R ≥ EE/TT threshold means cosmological tilt dominant
6. partial_contribution_fractions: {local, cosm, quad²} fractions

Adversarial test:
  Q: local와 cosmological이 구분 불가능한 degenerate regime?
  A: Yes — at very small β where local and cosmological both give
     similar TT amplitude. Discriminator only useful above a β threshold.
     Document this as "EE discrimination power" curve.

TDD (~45 tests):
  test_local_motion_zero_EE
  test_cosmological_tilt_nonzero_EE
  test_quadratic_term_3_frame_attribution_scaling
  test_EE_TT_ratio_discriminator_curves
  test_degeneracy_at_small_beta_flagged
  test_six_cross_terms_structure
  test_total_reconstruction_from_three_signatures

성공 기준:
  PASS: D_EE^local = 0 exactly (machine precision)
  PASS: D_EE^cosm / D_TT^cosm > 0.1 at β = 1.36e-3 (discriminable)
  PASS: Term 3 scales as β × v_loc (frame-attribution channel correct)

CRAG: 3-panel figure:
  (a) D_ℓ TT/EE for pure local motion
  (b) D_ℓ TT/EE for pure cosmological tilt
  (c) D_ℓ TT/EE for combined realistic scenario

Honest scope: "Three-signature separator is a CODE-LEVEL tool, not a
data-fitting layer. The actual discrimination requires external data
(CMB EE spectrum). bass_py produces the discrimination templates;
HTT/MIO does the likelihood."
```

---

# §12. W15 — Direction likelihood generator

## PROMPT W15-01: Sky geometry + ZoA handling + selection (Doc 4+5)

**Type**: SOLVER-IMPL | **Techniques**: PAL + CoVe
**Depends**: W14-01 | **Est.**: ~600 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: Document 4, 5의 CPU 재설계 로드맵에 따라 sky geometry/selection
layer 구현. HEALPix + ZoA mask + completeness.

배경 (Documents 4 §8 + 5):
  Current repo state: PR13AH/AJ/AM의 diagnostic ZoA가 production axis로
  승격된 문제. 수정 방향:
    1. Layer A (sky geometry): lb_to_unitvec, spherical_mean with unit vectors
    2. Layer B (fast estimator): WLS bulk-flow
    3. Layer C (fiducial Bayesian): dynesty posterior
    4. Layer D (downstream): production-gated axis use

  uniform_fallback은 production에서 금지.
  20° ZoA cut은 diagnostic default, not production default.

구현 (new files in bass/sky/):
1. sky_geometry.py:
   - lb_to_unitvec(l_deg, b_deg)
   - unitvec_to_lb(vec)
   - spherical_mean(lb, weights) using unit vectors
2. healpix_selection.py:
   - build_zoa_mask(l, b, bcut, nside)
   - build_angular_completeness(l, b, nside, smooth_sigma_pix)
3. contracts.py:
   - SkySelectionConfig dataclass
   - production_mode flag enforcement

TDD (~40 tests):
  test_lb_to_unitvec_roundtrip
  test_spherical_mean_no_galactic_plane_bias
  test_zoa_mask_construction
  test_completeness_smoothing_no_negative_values
  test_production_mode_forbids_uniform_fallback
  test_diagnostic_mode_allows_fallback_with_tag

성공 기준:
  PASS: all unit-vector roundtrips within 1e-14
  PASS: production mode raises on all-zero weights
  PASS: ZoA mask + completeness independent dimensions

Honest scope: "Layer A/B of Document 4 roadmap. Layer C (dynesty
inference) and D (downstream gate) follow in W15-02, W15-03."
```

---

## PROMPT W15-02: WLS bulk-flow estimator + dynesty posterior (Doc 4 §5-6)

**Type**: SOLVER-IMPL | **Techniques**: PAL + Self-Refine
**Depends**: W15-01 | **Est.**: ~700 lines | **Think**: T3 | **Web**: W0

```
[web:off] [think:extended]

목표: Document 4의 Layer B (fast estimator) + Layer C (fiducial Bayesian
inference) 구현. CF4++ dipole direction posterior 산출.

물리/통계 (Doc 4 §5-6):
  WLS bulk-flow:
    A = Σ_i w_i n̂_i n̂_i^T
    b = Σ_i w_i u_i n̂_i
    V̂ = A⁻¹ b
    w_i = 1 / σ_{i,eff}²
  
  Gaussian likelihood:
    ln L = -(1/2) Σ_i [(u_i - V·n̂_i)² / σ_{i,eff}² + ln(2π σ_{i,eff}²)]
  
  dynesty parameters:
    θ = (V_x, V_y, V_z, σ_*)
    Priors: uniform V_x,y,z ∈ (-V_max, V_max), σ_* ∈ (0, σ_max)
    Output: posterior samples, log-evidence

bass_py specific:
  L (l,b) posterior from V̂ posterior (not from mean of samples' (l,b))
  Bianchi model-specific: given each model (orthogonal Bianchi I,
  tilted Bianchi VIIh), posterior conditional on the model
  D_2 comparison: each model's D_2(Σ², β) vs observed D_ℓ

구현 (new files in bass/posterior/):
1. bulkflow_estimator.py (WLS)
2. bulkflow_likelihood.py (Gaussian + prior transform for dynesty)
3. direction_posterior_sampler.py (dynesty wrapper)
4. posterior_summary.py (HPD, resultant, HEALPix density map)
5. model_conditional_posterior.py
   - for each Bianchi model, compute conditional direction posterior
   - report evidence ln B against FLRW null

TDD (~55 tests):
  test_wls_bulkflow_recovery_synthetic
  test_wls_covariance_eigenvalue_ordering
  test_likelihood_gaussian_structure
  test_dynesty_nested_sampling_converges
  test_posterior_mean_not_from_lb_mean (spherical mean)
  test_hpd_region_coverage
  test_model_conditional_evidence
  test_cf4_plus_plus_ingest

성공 기준:
  PASS: synthetic dipole recovery within 68% CL
  PASS: posterior HPD cone includes injected axis at 95% CL
  PASS: evidence comparison between models consistent with prior expectations

CRAG: 4-panel figure:
  (a) posterior samples on sky (Mollweide)
  (b) marginals V_x, V_y, V_z
  (c) evidence bars for {FLRW null, orthogonal BI, tilted BI, tilted VIIh}
  (d) direction HPD contour

Honest scope: "Fiducial Bayesian inference with dynesty. Model evidence
comparison is valid WITHIN the set of tested models. Beyond-ΛCDM
alternatives (isocurvature dipole per Chen+Han+Qiu 2025) are not
automatic — require external extension."
```

---

## PROMPT W15-03: Mock calibration + production gate (Doc 4 §6 + 5)

**Type**: VALIDATION | **Techniques**: PAL + CRITIC + Adversarial
**Depends**: W15-02 | **Est.**: ~500 lines | **Think**: T4 | **Web**: W0

```
[web:off] [think:heavy]

목표: mock injection-recovery로 posterior bias/coverage 측정.
production gate 최종 설정.

프로토콜 (Doc 4 §6):
  1. Isotropic null mocks (no dipole): recover direction posterior,
     check that 68% CL excludes isotropic at noise-level frequency.
  2. Injected-dipole mocks at various amplitudes:
     Injected (l_inj, b_inj, V_inj) → recovered posterior.
     Measure: offset, amplitude bias, credible interval coverage.
  3. ZoA ladder: b_cut ∈ {0°, 10°, 20°, 30°} → posterior stability.
  4. Selection weight: isotropic weights vs completeness-aware weights.
  5. Production gate:
     - Bias < 2σ_posterior
     - Coverage 90-95% (expected 95% nominal)
     - Stability across ZoA ladder < 5° direction offset

구현 (new file: bass/posterior/mock_calibration.py):
1. generate_isotropic_mocks(n_objects, n_mocks, catalog_template)
2. generate_injected_dipole_mocks(V_inj_array, n_mocks)
3. run_calibration_pipeline(mocks, inference_config) → bias/coverage
4. zoa_ladder_stability_test(real_data, b_cut_array)
5. production_gate_evaluator(calibration_results) → pass/fail/warn

Adversarial:
  Q: what if ZoA=20° already contains Galactic plane bias that mocks
     don't have?
  A: Layer C mock calibration applies identical ZoA. Any offset IS the
     bias to report. Don't mask the bias in calibration.
  Q: what if production gate fails?
  A: Flag specific channel (bias vs coverage vs stability) and go back
     to W15-02 for that channel. Don't push to downstream.

TDD (~35 tests):
  test_isotropic_mock_no_dipole_recovery
  test_injected_dipole_unbiased_recovery
  test_coverage_95_percent_nominal
  test_zoa_ladder_stability
  test_completeness_weighting_bias_reduction
  test_production_gate_pass_conditions

성공 기준:
  PASS: null posterior excludes isotropic at <5% tail (no false positives)
  PASS: injected recovery coverage 90-95% at all injected amplitudes
  PASS: ZoA ladder max offset < 5°
  PASS: production gate flag = PASS

Honest scope: "Mock calibration is the ONLY path to production gate.
Without mocks, posterior interpretation is diagnostic-level only.
Mock catalog must be isotropic (null) and injected-dipole both —
neither alone is sufficient."
```

---

# §13. Validation gate tracks

## 13.1 Validation ladder (summary)

| Gate | Location | Target | Blocks |
|------|----------|--------|--------|
| V1 FLRW→CAMB | W10-02 | tier A <5%, B <10%, C <15% | W11+ |
| V2 Bianchi→bass_rs | W11-03 | m=0 <15%, m=±2 <25%, direction <5° | W12+ (soft-optional if bass_rs unavailable) |
| V3 W_R boundary | W12-01 | D_2 contribution < 1e-10 | W13 |
| V4 Tilt transfer | W13-02 | Route B recovery at β=0 | W14 |
| V5 Discriminator | W14-01 | D_EE^local = 0 | W15 |
| V6 Direction posterior | W15-03 | Mock coverage 90-95% | Production release |

## 13.2 Tier labeling convention

All numerical outputs tagged with:

- **ESTABLISHED**: rigorously validated against external reference
- **CONDITIONAL**: validated within stated conditions
- **EXPLORATORY**: predictive, no external validation available

Each W-deliverable packet MUST declare tier for key outputs.

---

# §14. Honest accuracy documentation protocol

## 14.1 Every public API entry includes:

1. **Scope statement**: what this module does
2. **Deferred items**: what's explicitly NOT in scope (with link to bass_rs)
3. **Validation status**: against which external reference (CAMB, bass_rs)
4. **Accuracy tier**: within bass_py context (not CAMB equivalence)

## 14.2 Required docstring pattern

```python
def compute_D_ell(bass_state, ell_max):
    """
    Compute D_ℓ power spectrum from bass_py state.

    Scope:
        Low-ℓ (ℓ ≤ 30) TT/EE from given kinematical inputs.
        Forward direction of MES inference.

    Accuracy tier:
        tier A (ℓ ≤ 5): < 5% vs CAMB FLRW limit (validated W10-02)
        tier B (ℓ = 6-15): < 10%
        tier C (ℓ = 16-30): < 15%

    Not in scope (see bass_rs):
        - Nonlinear perturbation
        - ℓ > 30
        - TE/BB spectra as primary output
        - Dynamical recombination
        - Patchy reionization

    References:
        R-TILT-03 §1 (computational chain)
        Document 10 PR-P6 (TE/EE plotting pipeline position)
    """
```

## 14.3 Release note discipline

Each W-release packet explicitly includes:

- Honest scope declaration
- CAMB match status
- bass_rs cross-check status (or reason unavailable)
- Deferred items list
- Production readiness flag (PASS/WARN/BLOCKED)

---

# §15. Architecture invariants

## 15.1 Hard invariants (never violated)

1. **Frame discipline**: transport in $(n^a)$-frame, collision in $(u_e^a)$-frame
2. **Honest scope**: no docstring claims full PSTF or CAMB equivalence
3. **W3 gating**: all public entries gate on `CanonicalDecision`
4. **d2_convention.rs / d2_convention.py SSOT**: Production $D_2 = 0.1741\,\mu K^2$ anti-regression guard
5. **L=4 minimum**: no $L=2$ truncation in production path
6. **EE required**: never produce TT without EE as peer

## 15.2 Frozen directory structure

```
bass_py/bass_py_monorepo/
├── bass/
│   ├── background/          [W3-W5 complete]
│   ├── runtime/              [W3 complete]
│   ├── observational/        [W4 complete]
│   ├── collision/            [W4D3 complete]
│   ├── transport/            [W5-A/B/C complete]
│   ├── perturbation/         [W6 new]
│   ├── closure/              [W6-04 / W7-02 new]
│   ├── history/              [W8 new]
│   ├── source/               [W8-03 new]
│   ├── los/                  [W9 new]
│   ├── spectrum/             [W10/W11 new]
│   ├── local_patch/          [W12 new — R-TILT-02]
│   ├── einstein/             [W13-01 new — R-TILT-03]
│   ├── transfer/             [W13-02 new]
│   ├── discriminator/        [W14 new]
│   ├── sky/                  [W15-01 new]
│   ├── posterior/            [W15-02/03 new]
│   └── validation/           [continuous]
└── tsc/                      [W3-W5 utilities, unchanged]
```

## 15.3 Rust bass_rs coordination

- bass_py does NOT depend on bass_rs at runtime (independent implementation)
- V2 validation is OPTIONAL gate (bass_rs may not be ready)
- HDF5 export format shared between bass_py and bass_rs where possible
- bass_py does NOT attempt to match bass_rs output beyond V2 targets

---

# §16. DAG execution order (critical path highlighted)

**Critical path (forward spectrum)**:
```
W6-01 (baryon) → W6-02 (dipole drive) → W6-04 (TCA)
    → W7-01 (E-mode) → W7-02 (polter) → W8-01 (visibility)
    → W8-02 (reionization) → W8-03 (source) → W9-01 (FLRW LoS)
    → W9-02 (Bianchi propagator) → W10-01 (C_ℓ) → W10-02 (V1 gate)
```

**Direction-posterior path (likelihood generator)**:
```
W10-02 → W11-01 (direction Cl) → W11-02 (BiPoSH) → W11-03 (V2 gate)
    → W12-01 (W_R window) → W12-02 (frame bias)
    → W13-01 (tilt source) → W13-02 (transfer)
    → W14-01 (discriminator)
    → W15-01 (sky) → W15-02 (posterior) → W15-03 (V6 gate)
```

**Parallel optional track**:
```
W6-03 (CDM) — can run in parallel with W6-02 if prioritized
```

## 16.1 Effort estimate (from est. lines)

| Phase | Weeks | Cumulative lines |
|-------|-------|------------------|
| W6 (4 prompts) | ~3 weeks | +1100 lines, ~150 tests |
| W7 (2 prompts) | ~2 weeks | +700 lines, ~90 tests |
| W8 (3 prompts) | ~2 weeks | +800 lines, ~100 tests |
| W9 (2 prompts) | ~3 weeks | +1000 lines, ~90 tests |
| W10 (2 prompts) | ~2 weeks | +800 lines, ~70 tests |
| W11 (3 prompts) | ~2 weeks | +1200 lines, ~115 tests |
| W12 (2 prompts) | ~2 weeks | +650 lines, ~65 tests |
| W13 (2 prompts) | ~1.5 weeks | +800 lines, ~65 tests |
| W14 (1 prompt) | ~1 week | +500 lines, ~45 tests |
| W15 (3 prompts) | ~3 weeks | +1800 lines, ~130 tests |
| **Total** | **~21 weeks** | **+9350 lines, ~920 tests** |

Cumulative after W15: ~27,000 lines, ~2,200 tests.

---

# §17. Score card template (use each packet)

```
PR-XX: [W#-##]: Title
Status: [NOT_STARTED | IN_PROGRESS | VALIDATED | BLOCKED]
Tests: __ / __ 
Honest scope declared: [YES | NO]
V-gate status: [if gated, which V, current state]
Lines: __ 
Depends complete: [YES | NO]
Production ready: [YES | NO | WARN]
```

---

# §18. Revision history

- **v1.0 (2026-04-18)**: Initial roadmap freeze, W6-W15, 24 prompts.
  Based on R-TILT-02/03, 7 design documents, W3-W5 completed foundation.
  Honest scope discipline introduced as architecture invariant.

- **v1.1 (2026-04-18)**: Sign correction in §3 W6-01 Thomson drag
  equation. The original text propagated ch05 manuscript sign (−),
  but Ma-Bertschinger 1995 Eq. 29 and CAMB notes §7.3 require (+) for
  the baryon-side drag so that v_b is driven toward 3Θ_1 at tight
  coupling. Caught during W6-01 implementation by
  `test_thomson_drag_sign_pushes_v_b_toward_3_theta`. The ch05
  manuscript may also need review in a future retrofit task.

- **v1.2 (2026-04-18)**: Multiple corrections discovered during systematic
  verification against the project textbook framework document
  (low-ℓ tetrad-based Bianchi solver standard form):

  1. **P1 physics fix — W6-04 TCA inverse sign error.** The v1.1
     §3 W6-04 spec wrote `Γ_T M X = -S` and inverse formulas with an
     overall negative sign. The correct convention (per Pontzen-
     Challinor 2007 Eq. 5.1 and Ma-Bertschinger 1995 Eq. 63) is
     `Γ_T M X = +S`, giving Θ_2 = +Γ_T⁻¹[(4/3)S_T - (√6/3)S_E],
     E_2 = +Γ_T⁻¹[-(√6/3)S_T + 3 S_E]. Physical check: S_T>0 gives
     Θ_2>0 (positive shear creates positive π_γ, matching CAMB's
     `cmbmain.f90` TCA formula).
     
     Detected by systematic cross-reference with the textbook
     framework document §4.1 TCA matrix. NOT detected by W6-04's
     52 self-consistent tests because the sign is invariant under
     the tested quantities (ratio E_2/Θ_2, Π/Θ_2, matrix-solve
     cross-check). Fix deployed:
     - `quadrupole_tca.py:solve_tca_closure`: overall signs flipped
     - `quadrupole_tca.py:tca_closure_matrix_solve`: rhs sign flipped
     - `test_quadrupole_tca.py:test_formula_S_T_only`: expected values
       updated + physical sign checks added (`assert theta > 0`)
     - `test_quadrupole_tca.py:test_formula_S_E_only`: same
     - Module and roadmap docstrings updated with derivation

  2. **P4 arithmetic typo — polter-ζ relation.** The v1.1 §4 W7-02
     prompt wrote `polter = (3 I_2 + 27 E_2)/30 = (3/30)ζ`. Correct
     is `polter = (3 I_2 + 18 E_2)/30 = (2/15)ζ`. Code was correct;
     only the roadmap comment was wrong.

- **Scheduled W7-01 refactoring (v1.2 design note)**: The systematic
  verification also flagged two API-level concerns that are not
  immediate bugs but require structural cleanup when E-mode hierarchy
  is introduced:

  1. **Finding B.1/C.1 — damping interface ambiguity.** W5-A's scalar
     `damping_rate` applied uniformly across ℓ is a declared skeleton
     simplification. For photons, ℓ=0 should have NO Thomson damping
     (collision formula has `1 - δ_{ℓ0}` factor), and ℓ=2 picks up
     `(9/10)τ̇ + (√6/10)τ̇ E_2/Θ_2` rather than simple τ̇. The
     W6-02 `build_damping_vector` adds τ̇ at ℓ=1 on top of the W5-A
     baseline, creating a double-counting risk if callers mistakenly
     set the W5-A baseline to τ̇ itself.
     
     Resolution scheduled for W7-01: introduce `DampingProfile` spec
     with explicit `hubble_rate` (all ℓ) and `thomson_rate` (ℓ-
     dependent via the collision formula) separation. Until then,
     callers must interpret `damping_rate` as Hubble-only and use
     `BaryonCoupling` for Thomson drag at ℓ=1.

  2. **Finding B.2 — W5-C m=±2 Wigner normalization deferred.**
     `decompose_shear_to_m_channels` returns raw amplitudes without
     Wigner normalization for the m=±2 channel. Axisymmetric
     reductions (s_plus=0) are unaffected. Full Bianchi I with
     off-axis shear requires Wigner factor; scheduled for W7+.

- **Scheduled W12 refactoring**: Rename W6-02 `BaryonCoupling.v_b` to
  `v_e` (electron-frame velocity) once full species-tilt support
  arrives. Currently v_b = v_e under single-tilt assumption, so the
  rename is cosmetic.

---

# §19. Next actions

1. User reviews this v1.0 roadmap
2. Decide parallel track policy (can W12+ start before V2 bass_rs available?)
3. Freeze W6-01 start
4. Create honest-scope docstring templates for W3-W5 retrofit
   (separate minor task, ~1 day)
5. Begin W6-01 implementation

---

**End of MASTER_PROMPT_LIST_bass_py.md**
