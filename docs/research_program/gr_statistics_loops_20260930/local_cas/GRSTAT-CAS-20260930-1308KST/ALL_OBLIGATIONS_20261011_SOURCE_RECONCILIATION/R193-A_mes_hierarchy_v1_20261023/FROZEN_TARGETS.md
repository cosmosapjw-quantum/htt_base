# R193-A frozen targets (written before any proof compile)

Module: `lean/R193AMesHierarchy.lean`, namespace `R193A`. Toolchain Lean 4.31.0, Mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`.

## Scope (binding for every target)

- One event; orthonormal triad of the u^a rest space (h_ab = δ_ab); rest-space tensors typed
  `Vec = EuclideanSpace ℝ (Fin 3)`, `T2`, `T3`, `T4` = `EuclideanSpace ℝ (Fin 3 × …)`, norm =
  Frobenius = MESa |·|. Index convention: derivative index first.
- Relations are MESa's **linearised** ("≃") equations with O[2] dropped. No O[2] remainder bound,
  no time evolution, no global/domain statement. Card quantifiers: MESa's bounds are "for any event
  after last scattering" given B1–B3 there; the Lean theorems are the pointwise statements at an
  arbitrary event (universally quantified over the jet), i.e. the same quantifier structure.
- Strict `<` hypotheses/conclusions as in MESa (42)–(45), (51), (52). The acceleration-curl bound
  is non-strict (`≤ α Θ²`) so that α = 0 encodes the geodesic branch.
- Typed predicates: `ShearRel kq`, `VortRel`, `MomRel` (hierarchy relations, source-cited);
  `Adopted*` predicates (C1, C2, ε1 = 0, strict ordering) are **separate definitions** and are
  never hypotheses of a physical-necessity theorem.
- Coupling `kq` of ∇̂_<a q_b> in (14): printed `2`; Boltzmann-consistent `2/5` (ledger target E5).
  Both readings are carried; no target silently picks one.

## Targets

### Part T — typed operations (lemmas used by the derivation)
| id | Lean | statement |
|---|---|---|
| T1 | `norm_asymL_le` | `∀ T : T2, ‖asymL T‖ ≤ ‖T‖` |
| T2 | `norm_stfL_le` | `∀ T : T2, ‖stfL T‖ ≤ ‖T‖` |
| T3 | `norm_contrA_le`, `norm_contrB_le`, `norm_divL_le` | contraction ≤ `√3 * ‖·‖` |

### Part E — coefficient ledger / erratum
| id | Lean | statement |
|---|---|---|
| E1 | `sagFactor_eq` | `∀ L, sagFactor L = 1 / angK L` (SAG erratum (17) = (2L+1)‼/L!) |
| E2 | `sagFactor_two`, `sagFactor_three` | `= 15/2`, `= 35/2` (SAG (18),(19)) |
| E3 | `momentCoeff_vals`, `tauCoeff_vals`, `sag_eq_four_tauCoeff`, `tau_from_moment` | MESa (46) `4/3, 8/15, 8/35`; (41) `3/4, 15/8, 35/8`; (40)+(5)–(7) ⇒ (41); SAG factor = 4·(41) coefficient |
| E4 | `angK_succ`, `gradCoupling_eq`, `divCoupling_eq_one` | general-L moment hierarchy couplings `(L+1)/(2L+3)` and `1` |
| E5 | `eq14_grad_coupling` | `gradCoupling 0 = 1/3 ∧ gradCoupling 1 = 2/5 ∧ (2/5:ℚ) ≠ 2 ∧ divCoupling 0 = 1 ∧ divCoupling 1 = 1 ∧ divCoupling 2 = 1` |
| E6 | `accel_coupling` | `4 * angK 1 / angK 0 = 4/3 ∧ 4 * angK 2 = 8/15` |
| E7 (neg. control) | `sag_without_prefactor_fails` | factor without `(2ℓ+1)` ≠ 15/2 |

### Part S — shear, MESa (14) ⇒ (51)
```
theorem shear_raw_general (kq : ℝ) (hkq : 0 ≤ kq) (s : ShearJet) (h : ShearRel kq s)
    {e2 e2s e1p e3p : ℝ} (b : ShearBounds s e2 e2s e1p e3p) :
    ‖s.sigma‖ / s.Th < 8/3 * e2 + e2s + kq * (5/2) * e1p + √3 * (3/7) * e3p
theorem shear_raw_source_eq51 (s : ShearJet) (h : ShearRel 2 s) {e2 e2s e1p e3p : ℝ}
    (b : ShearBounds s e2 e2s e1p e3p) :
    ‖s.sigma‖ / s.Th < 8/3 * e2 + e2s + 5 * e1p + 9/7 * e3p                 -- S1-source
theorem eq51_route_constants : (4/3 + 4/3 : ℚ) = 8/3 ∧ (2:ℚ) * momentCoeff 1 / momentCoeff 2 = 5 ∧
    (3:ℚ) * momentCoeff 3 / momentCoeff 2 = 9/7 ∧ momentCoeff 3 / momentCoeff 2 = 3/7
theorem shear_raw_sharp (kq) (hkq) (s) (h : ShearRel kq s) (b) :
    ‖s.sigma‖ / s.Th < e2s + kq * (5/2) * e1p + √3 * (3/7) * e3p               -- S2
theorem shear_boltzmann_implies_eq51 (s) (h : ShearRel (2/5) s) (b) :
    ‖s.sigma‖ / s.Th < e2s + e1p + √3 * (3/7) * e3p ∧
    ‖s.sigma‖ / s.Th < 8/3 * e2 + e2s + 5 * e1p + 9/7 * e3p                   -- S3
```
`ShearJet` carries `udot` and `ShearRel` does not constrain it: S1–S3 are the non-geodesic shear
results too (no O[1] acceleration term in (14); see SOURCE_RECOVERY §5).

### Part W — vorticity, MESa (27)+∇̂(13)+(26) ⇒ (52), non-geodesic term
```
theorem vort_raw_general (s : VortJet) (h : VortRel s) {e1p e1ps e2pp α : ℝ}
    (b : VortBounds s e1p e1ps e2pp α) :
    ‖s.omega‖ / s.Th < 9 * e1p + 3 * e1ps + √3 * (6/5) * e2pp + 3 * α            -- W1 (NG)
theorem vort_raw_geodesic (s) (h : VortRel s) (hg : s.gradudot = 0) {e1p e1ps e2pp}
    (b1p : ‖s.gradtau1‖ < e1p * s.Th) (b1ps : ‖s.gradtau1dot‖ < e1ps * s.Th ^ 2)
    (b2pp : ‖s.hesstau2‖ < e2pp * s.Th ^ 2) :
    ‖s.omega‖ / s.Th < 9 * e1p + 3 * e1ps + √3 * (6/5) * e2pp                 -- W1-geodesic
theorem vort_raw_sharp (s) (h : VortRel s) (b : VortBounds s e1p e1ps e2pp α) :
    ‖s.omega‖ / s.Th < e1p + 3 * e1ps + √3 * (6/5) * e2pp + 3 * α             -- W2
theorem Gw_typed : (∀ b c a d, gw b c a d = gw c b a d) ∧ (∀ b c a d, gw b c a d = gw b c d a) ∧
    (∀ b c, gw b c 0 0 + gw b c 1 1 + gw b c 2 2 = 0)                         -- witness typing
theorem contraction_factor_one_fails : ‖Gw‖ < ‖asymL (contrB Gw)‖           -- W3a
theorem eq52_eps2_branch_not_implied :
    ∃ s : VortJet, VortRel s ∧ s.gradudot = 0 ∧
      ‖s.gradtau1‖ < (1/100) * s.Th ∧ ‖s.gradtau1dot‖ < (1/100) * s.Th ^ 2 ∧
      ‖s.hesstau2‖ < (13/2) * s.Th ^ 2 ∧
      9 * (1/100) + 3 * (1/100) + 6/5 * (13/2) < ‖s.omega‖ / s.Th                 -- W3 (negative control)
```
Expected status: the ε'1, ε'*1 coefficients (9, 3) of (52) are source-equal; the ε''2 coefficient
6/5 is **not** implied by the formalised relation set (W3); valid coefficient `(6/5)√3`.

### Part A — acceleration (non-geodesic (13'))
```
theorem accel_combination_bound (s : MomJet) (h : MomRel s) {e1s e2p : ℝ}
    (b1 : ‖s.tau1dot‖ < e1s * s.Th) (b2 : ‖s.gradtau2‖ < e2p * s.Th) :
    ‖s.gradmu + (4 * s.mu) • s.udot‖ < s.mu * s.Th * (4 * e1s + √3 * (8/5) * e2p)   -- A1
theorem no_accel_ceiling (M : ℝ) : ∃ s : MomJet, MomRel s ∧ s.tau1 = 0 ∧ s.tau1dot = 0 ∧
    s.gradtau2 = 0 ∧ M < ‖s.udot‖                                                 -- A2
```

### Part P — physical necessity (derived) vs adopted (separate predicates)
```
theorem dust_forces_geodesic (rho : ℝ) (udot : Vec) (hρ : 0 < rho) (hmom : rho • udot = 0) : udot = 0
theorem theta_tR_eq_three (Th T Tdot : ℝ) (hT : 0 < T) (hTh : 0 < Th)
    (h36 : Tdot = -(Th / 3) * T) : Th * (T / |Tdot|) = 3
theorem mudot0_neg (Th mu mudot0 : ℝ) (hTh : 0 < Th) (hmu : 0 < mu)
    (h : mudot0 = -(4/3) * Th * mu) : mudot0 < 0
theorem reduce_sigma … : rawSigma e2 e2s e1p e3p ≤ Bsigma e1 e2 e3        (under C1, C2 hypotheses)
theorem reduce_sigma_tight (e1 e2 e3) : rawSigma e2 (e2/3) (e1/3) (e3/3) = Bsigma e1 e2 e3
theorem reduce_omega … : rawOmega e1p e1ps e2pp ≤ Bomega e1 e2           (under C1, C2 hypotheses)
theorem reduce_omega_tight (e1 e2) : rawOmega (e1/3) (e1/9) (e2/9) = Bomega e1 e2
theorem transcription_adjudication : (∀ c, c + 1/3 = 3 ↔ c = 8/3) ∧ (3/8 + 1/3 : ℝ) ≠ 3 ∧
    (∀ c, c * (1/3) = 3/7 ↔ c = 9/7) ∧ (7/9 * (1/3) : ℝ) ≠ 3/7 ∧
    (∀ c, c * (1/9) = 2/15 ↔ c = 6/5) ∧ (5/6 * (1/9) : ℝ) ≠ 2/15
theorem hierarchy_strict_iff (e1 e2 e3) : Bomega e1 e2 < Bsigma e1 e2 e3 ↔ e1 < 43/25 * e2 + 9/35 * e3
theorem Bomega_pos_iff (h1 : 0 ≤ e1) (h2 : 0 ≤ e2) : 0 < Bomega e1 e2 ↔ 0 < e1 ∨ 0 < e2
theorem strict_hierarchy_not_forced : ∃ s : ShearJet, ShearRel 2 s ∧ ‖s.tau1‖ < 1 ∧
    ‖s.tau2‖ < 1/100 ∧ ‖s.tau3‖ < 1/100 ∧ ¬ AdoptedStrictHierarchy 1 (1/100) (1/100)
theorem eps1_zero_not_forced : ∃ s : ShearJet, ShearRel 2 s ∧ ShearRel (2/5) s ∧ s.tau1 ≠ 0
theorem eps1_interval_nondegenerate (h2 : 0 < e2) (h3 : 0 ≤ e3) : 0 < 43/25*e2 + 9/35*e3 ∧
    ∀ e1, 0 ≤ e1 → e1 < 43/25*e2 + 9/35*e3 → AdoptedStrictHierarchy e1 e2 e3
theorem C1_not_forced : ∃ s : ShearJet, ShearRel 2 s ∧ ¬ AdoptedC1Jet s
theorem C2_not_forced : ∃ s : ShearJet, ShearRel 2 s ∧ ¬ AdoptedC2Jet s
```

### Part C — ceiling map (PR-186 convention W² = ω_abω^ab/(6H²), Θ = 3H)
```
theorem ceiling_map (x Th H B : ℝ) (hx : 0 ≤ x) (hH : 0 < H) (hTh : Th = 3 * H)
    (hb : x / Th < B) : x ^ 2 / (6 * H ^ 2) < 3/2 * B ^ 2
theorem cs_ceiling_factor (e2 : ℝ) : 3/2 * (√3 * (2/15) * e2) ^ 2 = 3 * (3/2 * (2/15 * e2) ^ 2)
```

## Explicitly NOT targeted (would be over-claims)

- the angular moment identity ⟨e^{<A_L>}e_{<B_L>}⟩ = κ_L Δ (enters as the shared constant only);
- the Boltzmann projection producing the relation sets (cited derivation, prose + ledger E4–E6);
- O[2] remainder control, existence of full Einstein–Boltzmann solutions realising W3/A2;
- MESb (print-only) coefficients; the sharp (typed) contraction constants √(5/3), √(5/4), √(7/5)
  (numerical probes only, `raw/probes/opnorm.out`);
- any statement that MESa (52) is false for actual solutions (W3 is relative to `VortRel`).
