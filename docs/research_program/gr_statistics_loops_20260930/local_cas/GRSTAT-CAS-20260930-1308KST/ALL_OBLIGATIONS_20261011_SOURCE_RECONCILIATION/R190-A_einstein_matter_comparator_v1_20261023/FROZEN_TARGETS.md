# R190-A frozen targets (written before any proof compile)

Module `lean/R190AComparator.lean`, namespace `R190A`. Lean 4.31.0, Mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`.
Sources and citations: `SOURCE_RECOVERY.md`. Allowed axioms: `propext`, `Classical.choice`,
`Quot.sound`.

## Scope (binding)

- Comparator `x_C = Σ² − W² + Ω_tilt + Ω_k`, c = (+,−,+,+) (`egs3_graded_comparator.py:48-50`);
  registered open-branch box Σ² = 12/100, W² ∈ [0, 4/100], Ω_tilt = 3/100, Ω_k ∈ [0, 2/100]
  (`egs3_linearized_realization.py:97-110`).
- **Declared solution class (constraint level), recovered verbatim:** instantaneous homogeneous
  Bianchi I (a = 0) / Bianchi V (a_i = (a,0,0), ³R = −6a², n_ab = 0) data with diagonal
  trace-free shear, a two-stream antipodal perfect-fluid tilt pair (rest density μ_s per stream,
  p = wμ, rapidities ±β along a unit direction d), cosmological constant Λ, coupling κ; Gauss in
  the source's normalized form `Ω_m + Ω_Λ + Ω_k + Ω_tilt + Σ² − W² = 1`; (0i) momentum
  constraint `k · a_bσ^{ab} + κ q^a = 0` with the coefficient `k` **universally quantified**
  (source: 3, convention-dependent); Jacobi `n^{ab} a_b = 0`.
- **Comparator congruence = slice normal n** (CLAIM_LEDGER:280). W² is computed from a first
  jet of n_a = −N ∂_a t with a torsion-free connection and the projector h = δ + n⊗n^♯
  (n·n = −1); W²[n] = 0 is a **theorem** (C11), not a definition.
- Ω_tilt is **derived** from the n-frame stress-energy of the pair: κ(ρ_n − 2μ_s)/(3H²).
  Ω_m = κ·2μ_s/(3H²) (fixed-total label, PR-187 default).
- Local/global predicates are defined over a generic typed evolution system `EvolSys`
  (state `Fin m → ℝ`, vector field, constraint set, domain); the registered evolution system is
  NOT transcribed (open obligation O1). Every refutation below is quantified over all
  `EvolSys`, all horizons T and all momentum coefficients k.
- No theorem assumes attainability of a target as a hypothesis. Physical attainability beyond
  constraint level is not claimed.

## Part A — algebraic level, sign corners (PR-189 factorized corollary)

| id | Lean name | statement |
|---|---|---|
| A1 | `cornerPoint_mem` | `∀ B : CBox, B.Valid → ∀ k : Corner, InBox B (cornerPoint B k)` |
| A2 | `xC_lower_le` | `∀ B g, InBox B g → xC (cornerPoint B .lower) ≤ xC g` |
| A3 | `xC_le_upper` | `∀ B g, InBox B g → xC g ≤ xC (cornerPoint B .upper)` |
| A4 | `box_image` | `∀ B, B.Valid → ∀ x, (∃ g, InBox B g ∧ xC g = x) ↔ xC (cornerPoint B .lower) ≤ x ∧ x ≤ xC (cornerPoint B .upper)` |
| A5 | `lower_argmin_unique` | `∀ B g, InBox B g → xC g = xC (cornerPoint B .lower) → g = cornerPoint B .lower` |
| A6 | `upper_argmax_unique` | `∀ B g, InBox B g → xC g = xC (cornerPoint B .upper) → g = cornerPoint B .upper` |
| A7 (anti-swap) | `lower_strict_of_W2_lt` | `∀ B g, InBox B g → g.W2 < B.Whi → xC (cornerPoint B .lower) < xC g` |
| A8 | `reg_corners` | `cornerPoint regBox .lower = ⟨12/100, 4/100, 3/100, 0⟩ ∧ cornerPoint regBox .upper = ⟨12/100, 0, 3/100, 2/100⟩ ∧ xC (cornerPoint regBox .lower) = 11/100 ∧ xC (cornerPoint regBox .upper) = 17/100` |
| A9 | `reg_algebraic_iff` | `∀ x, AlgebraicAttained regBox x ↔ 11/100 ≤ x ∧ x ≤ 17/100` |
| A10 | `reg_lower_forces_W2` | `∀ g, InBox regBox g → xC g = 11/100 → g.W2 = 4/100` |
| A11 (neg. control) | `shear_swap_control` | `xC ⟨12/100, 0, 3/100, 0⟩ = 15/100 ∧ (15/100 : ℝ) ≠ 11/100` |

`AlgebraicAttained B x := ∃ g, InBox B g ∧ PosBlock g ∧ xC g = x`.

## Part C — PR-186/PR-187 convention-authority cross-check

| id | Lean name | statement |
|---|---|---|
| C1 | `tensorSq_eq_two_vecSq` | `∀ A, IsAntisym A → tensorSq A = 2 * vecSq (dualVec A)` (3×3, dual ω_a = ½ε_abcω^bc) |
| C2 | `W2reg_eq_vecForm` | `∀ A, IsAntisym A → ∀ H, W2reg A H = vecSq (dualVec A) / (3 * H ^ 2)` |
| C3 | `wrong_display_is_three` | `∀ A, IsAntisym A → ∀ H, vecSq (dualVec A) / H ^ 2 = 3 * W2reg A H` |
| C4 | `W2_ceiling` | `∀ A H B, 0 < H → √(tensorSq A) / (3 * H) ≤ B → W2reg A H ≤ 3/2 * B ^ 2` |
| C5 | `W2_theta_form` | `∀ v H : ℝ, 3 * (v / (3 * H) ^ 2) = v / (3 * H ^ 2)` |
| C6 | `Sigma2_theta_form` | `∀ S H : ℝ, 3/2 * (S / (3 * H) ^ 2) = S / (6 * H ^ 2)` |
| C7 | `streamEnergy_eq` | `∀ μ w β, streamEnergy μ w β = μ + (1 + w) * μ * sinh β ^ 2` (from T₀₀ = (μ+p)cosh²β − p) |
| C8 | `pair_flux_cancel` | `∀ μ w β, streamFlux μ w β + streamFlux μ w (-β) = 0` |
| C9 | `pair_excess_labels` | `∀ μs w β, ρpair − 2μs = tiltPair .fixedTotal w (2*μs) β ∧ ρpair − 2μs = tiltPair .perStream w μs β` |
| C10 (neg. control) | `mixed_label_doublecounts` | `∀ μs w β, (1+w)*μs*sinh β^2 ≠ 0 → tiltPair .perStream w (2*μs) β ≠ ρpair − 2μs` |

(ρpair := `streamEnergy μs w β + streamEnergy μs w (-β)`.)

## Part F — Frobenius for the comparator congruence (derived, general)

| id | Lean name | statement |
|---|---|---|
| C11 | `frobenius_vort_zero` | `∀ J : SliceJet, J.Valid → ∀ a b, J.vort a b = 0` |
| C12 | `W2n_zero` | `∀ J, J.Valid → ∀ H, W2n J H = 0` |
| C13 (neg. control) | `badJet_partial_valid`, `badJet_vort_ne` | a jet satisfying every `Valid` clause except Hessian symmetry (non-integrable n) has `vort 1 2 = -1/2 ≠ 0` |
| C14 (non-vacuity) | `canonJet_valid` | the comoving jet (N=1, n = −dt) is `Valid` |

`SliceJet.Valid J := J.N ≠ 0 ∧ (∀ a b, hessT a b = hessT b a) ∧ (∀ e c d, Gam e c d = Gam e d c) ∧ ∑ a, nUp a * nCov a = -1`.

## Part D — constraint level in the declared class; typed candidate maps

| id | Lean name | statement |
|---|---|---|
| D1 | `HomData.W2_zero` | `∀ D : HomData, D.jet.Valid → D.W2 = 0` |
| D2 | `HomData.Otilt_eq` | `∀ D, D.Otilt = tiltPair .fixedTotal D.w D.Om D.beta` |
| D3 | `HomData.momentum_iff_transverse` | `∀ k ≠ 0, ∀ D, D.Momentum k ↔ D.a * D.s1 = 0` |
| D4 | `HomData.posBlock` | `∀ k D, D.ConstraintOK k → PosBlock D.invariants ∧ 0 ≤ D.invariants.Ok` |
| D5 | `candidate_invariants` | `∀ P, P.Valid → ∀ g, NormalFace g → (candidate P g).invariants = g` |
| D6 | `candidate_constraintOK` | `∀ k P, P.Valid → ∀ g, NormalFace g → (candidate P g).ConstraintOK k` |
| D7 | `candidate_typeI_iff` | `∀ P, P.Valid → ∀ g, NormalFace g → ((candidate P g).a = 0 ↔ g.Ok = 0)` |
| D8 | `realizable_iff_normalFace` | `∀ k g, (∃ D : HomData, D.ConstraintOK k ∧ D.invariants = g) ↔ NormalFace g` |
| D9 | `constraint_image_reg` | `∀ k x, ConstraintAttained k regBox x ↔ 15/100 ≤ x ∧ x ≤ 17/100` |
| D10 | `lower_not_constraint_attained` | `∀ k, ¬ ConstraintAttained k regBox (11/100)` |
| D11 | `interior_challenge_not_attained` | `∀ k, ¬ ConstraintAttained k regBox (12/100)` |
| D12 | `upper_constraint_attained` | `∀ k, ConstraintAttained k regBox (17/100)` |
| D13 | `no_data_realizes_lower` | `∀ D : HomData, D.jet.Valid → D.invariants ≠ cornerPoint regBox .lower` |
| D14 | `joint_strictly_inside_product` | `∀ k, (∀ x, ConstraintAttained k regBox x → AlgebraicAttained regBox x) ∧ ∃ x, AlgebraicAttained regBox x ∧ ¬ ConstraintAttained k regBox x` |
| D15 | `cornerData_sound` | `∀ k P, P.Valid → ∀ B c D, cornerData P B c = some D → D.invariants = cornerPoint B c ∧ D.ConstraintOK k` |
| D16 | `cornerData_complete` | `∀ k P B c, cornerData P B c = none → ¬ ∃ D : HomData, D.ConstraintOK k ∧ D.invariants = cornerPoint B c` |
| D17 | `cornerData_reg` | `∀ P, cornerData P regBox .lower = none ∧ cornerData P regBox .upper = some (candidate P (cornerPoint regBox .upper))` |
| D18 | `valueData_sound` | `∀ k P, P.Valid → ∀ x D, valueData P x = some D → D.ConstraintOK k ∧ InBox regBox D.invariants ∧ xC D.invariants = x` |
| D19 | `valueData_complete` | `∀ k P x, valueData P x = none → ¬ ConstraintAttained k regBox x` |
| D20 (non-vacuity) | `upper_witness_explicit` | `regBackground.Valid ∧ (candidate regBackground (cornerPoint regBox .upper)).ConstraintOK 3 ∧ (candidate regBackground (cornerPoint regBox .upper)).invariants = cornerPoint regBox .upper ∧ (candidate regBackground (cornerPoint regBox .upper)).a ≠ 0 ∧ (candidate regBackground (cornerPoint regBox .upper)).OL = 53/100` |
| D21 | `candidate_reg_OL_pos` | `∀ x, 15/100 ≤ x → x ≤ 17/100 → 0 < (candidate regBackground (regFaceVector x)).OL` |

`NormalFace g := g.W2 = 0 ∧ 0 ≤ g.Sigma2 ∧ 0 ≤ g.Otilt ∧ 0 ≤ g.Ok`;
`ConstraintAttained k B x := ∃ D : HomData, D.ConstraintOK k ∧ InBox B D.invariants ∧ xC D.invariants = x`;
`regBackground := ⟨1, 0, 3/10, 1⟩` (H, w, Ω_m, κ); `regFaceVector x := ⟨12/100, 0, 3/100, x − 15/100⟩`.
The candidate maps are `candidate : Background → CompVec → HomData` (meaningful on
`NormalFace`), `cornerData : Background → CBox → Corner → Option HomData`,
`valueData : Background → ℝ → Option HomData`; the comparator vector of a datum is typed in the
n-frame (`HomData.invariantsN : HomData → FrameG .n`).

## Part E — separate sharpness predicates and the PR-190 statement

`LocalDev S D`, `GlobalDev S T D` (definitions in the module), `LocalAttained k S B x`,
`GlobalAttained k S T B x`, `FullDynSharp k S T B := ∀ x, lo ≤ x → x ≤ hi → GlobalAttained k S T B x`.

| id | Lean name | statement |
|---|---|---|
| E1 | `ladder` | `∀ k S T B x, (GlobalAttained k S T B x → LocalAttained k S B x) ∧ (LocalAttained k S B x → ConstraintAttained k B x) ∧ (ConstraintAttained k B x → AlgebraicAttained B x)` |
| E2 | `full_dyn_sharp_refuted` | `∀ k S T, ¬ FullDynSharp k S T regBox` |
| E3 | `lower_not_local`, `lower_not_global` | `∀ k S, ¬ LocalAttained k S regBox (11/100)`; `∀ k S T, ¬ GlobalAttained k S T regBox (11/100)` |

## Open obligations (not claimed)

- O1: `LocalAttained k S_reg regBox (17/100)` and `GlobalAttained … ` for the registered evolution
  system `S_reg` of the declared class (transcription of the KE-DYN / Bianchi-V system, constraint
  propagation, Picard–Lindelöf, ≥ 5 e-fold horizon). Open proof obligation, not external.
- O2: same for every x ∈ (15/100, 17/100) (constraint level proved by D9).
- External blocker X1: re-attribution of the comparator W² from n to u (owner definition choice).
