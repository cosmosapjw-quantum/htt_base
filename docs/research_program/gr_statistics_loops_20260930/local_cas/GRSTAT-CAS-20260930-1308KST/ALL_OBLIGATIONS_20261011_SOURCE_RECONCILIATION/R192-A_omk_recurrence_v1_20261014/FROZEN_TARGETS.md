# R192-A frozen targets (written before any proof compile)

Module: `lean/R192AOmkRecurrence.lean`, namespace `R192A`, `import Mathlib`.
Toolchain: Lean 4.31.0, mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f (Lake project
`/home/cosmosapjw/lean_oracles/viii_oracle`).

Scope (card R192-A): the all-order invariant-graph recurrence for the registered OMK
LRS-III/KS reduced system, its resonance (denominator-zero) set and compatibility
conditions, the existing finite coefficients as instances, and the falsity of the exact
linear graph when c2 != 0. Formal power series only: no convergence, no remainder
enclosure, no non-LRS extension, no observational value (those are other PR-192 slices).

## Definitions (verbatim transcription of the source, see SOURCE_RECOVERY.md)

Generic commutative F-algebra `A` so the SAME definition serves real points (`A = F`)
and formal power series (`A = F⟦X⟧`):

```lean
def qOMK (w : F) (S K : A) : A :=
  algebraMap F A ((1 + 3 * w) / 2) * (1 - K) + algebraMap F A (3 / 2 * (1 - w)) * S ^ 2
def fSigma (w : F) (S K : A) : A :=
  -K - algebraMap F A (1 / 2) * S *
    (algebraMap F A (1 + 3 * w) * K + algebraMap F A (3 * (1 - w)) * (1 - S ^ 2))
def fK (w : F) (S K : A) : A := 2 * K * (qOMK w S K + S)
-- invariance residual of the graph Sigma = h(K) (python line 113):
noncomputable def invRes (w : F) (h : F⟦X⟧) : F⟦X⟧ :=
  derivative F h * fK w h X - fSigma w h X
def gOMK (w : F) : F := 1 + 3 * w            -- lambda_K
def aOMK (w : F) : F := 3 / 2 * (1 - w)      -- -lambda_Sigma
def denom (w : F) (n : ℕ) : F := (n : F) * gOMK w + aOMK w
def quadE (c : ℕ → F) (n : ℕ) : F := ∑ p ∈ antidiagonal n, (p.1 : F) * c p.1 * c p.2
def cubE  (c : ℕ → F) (n : ℕ) : F :=
  ∑ p ∈ antidiagonal n, (p.1 : F) * c p.1 * ∑ q ∈ antidiagonal p.2, c q.1 * c q.2
def cub   (c : ℕ → F) (n : ℕ) : F :=
  ∑ p ∈ antidiagonal n, c p.1 * ∑ q ∈ antidiagonal p.2, c q.1 * c q.2
def rhsR (w : F) (c : ℕ → F) (n : ℕ) : F :=
  (if n = 1 then -1 else 0) + (((n - 1 : ℕ) : F) * gOMK w - gOMK w / 2) * c (n - 1)
    - 2 * quadE c n - 2 * aOMK w * cubE c n + aOMK w * cub c n
-- the general solution sequence: free value t n at resonant orders
noncomputable def seqWith (w : F) (t : ℕ → F) : ℕ → F
  | 0 => 0
  | n + 1 => if denom w (n + 1) = 0 then t (n + 1) else
      rhsR w (fun k => if k < n + 1 then seqWith w t k else 0) (n + 1) / denom w (n + 1)
```

`F` is `[Field F]` unless stated; `[CharZero F]` where numerals must be nonzero; `ℝ` for
order statements.

## Targets

| id | Lean name | statement (exact) |
|---|---|---|
| T1 | `coeff_invRes_zero` | `(w : F) (c : ℕ → F) (hc0 : c 0 = 0) : coeff 0 (invRes w (mk c)) = 0` |
| T2 | `coeff_invRes_succ` | `(w : F) (c : ℕ → F) (n : ℕ) : coeff (n + 1) (invRes w (mk c)) = denom w (n + 1) * c (n + 1) - rhsR w c (n + 1)` (ALL n, no hypothesis) |
| T3 | `invariant_iff_recurrence` | `(w : F) (c : ℕ → F) (hc0 : c 0 = 0) : invRes w (mk c) = 0 ↔ ∀ n, 1 ≤ n → denom w n * c n = rhsR w c n` |
| T4 | `rhsR_lower_order` | `(w : F) (c c' : ℕ → F) (n : ℕ) (hn : 1 ≤ n) (hc0 : c 0 = 0) (hagree : ∀ k, k < n → c k = c' k) : rhsR w c n = rhsR w c' n` (the recurrence is genuinely triangular) |
| T5 | `solution_iff` | `(w : F) (c : ℕ → F) (hc0 : c 0 = 0) : invRes w (mk c) = 0 ↔ (c = seqWith w c ∧ ∀ n, 1 ≤ n → denom w n = 0 → rhsR w c n = 0)` |
| T6 | `seqWith_invariant_iff` | `(w : F) (t : ℕ → F) : invRes w (mk (seqWith w t)) = 0 ↔ ∀ n, 1 ≤ n → denom w n = 0 → rhsR w (seqWith w t) n = 0` (compatibility conditions) |
| T6b | `seqWith_resonant` | `(w : F) (t : ℕ → F) (n : ℕ) (hn : 1 ≤ n) (hres : denom w n = 0) : seqWith w t n = t n` (resonant coefficient is free) |
| T7 | `exists_unique_of_nonresonant` | `(w : F) (hnr : ∀ n, 1 ≤ n → denom w n ≠ 0) : ∃! c : ℕ → F, c 0 = 0 ∧ invRes w (mk c) = 0` |
| T8 | `two_mul_denom` | `(w : F) (n : ℕ) : 2 * denom w n = (6 * (n : F) - 3) * w + (2 * (n : F) + 3)` |
| T8b | `denom_eq_zero_iff` | `[CharZero F] (w : F) (n : ℕ) (hn : 1 ≤ n) : denom w n = 0 ↔ w = -(2 * (n : F) + 3) / (6 * (n : F) - 3)` |
| T8c | `denom_one/two/three` | `denom w 1 = (3 * w + 5) / 2`, `denom w 2 = (9 * w + 7) / 2`, `denom w 3 = 3 * (5 * w + 3) / 2` (registered factors) |
| T8d | `denom_ne_zero_marginal` | `[CharZero F] (n : ℕ) (hn : 1 ≤ n) : denom (-1/3 : F) n ≠ 0 ∧ denom (1 : F) n ≠ 0` (marginal entries are not denominator zeros) |
| T9 | `denom_pos_on_domain` | `(w : ℝ) (hlo : -1/3 < w) (hhi : w < 1) (n : ℕ) (hn : 1 ≤ n) : 0 < denom w n` |
| T9b | `resonance_mem_Ico` | `(n : ℕ) (hn : 1 ≤ n) : -5/3 ≤ -(2 * (n : ℝ) + 3) / (6 * n - 3) ∧ -(2 * (n : ℝ) + 3) / (6 * n - 3) < -1/3` |
| T9c | `exists_unique_on_domain` | `(w : ℝ) (hlo : -1/3 < w) (hhi : w < 1) : ∃! c : ℕ → ℝ, c 0 = 0 ∧ invRes w (mk c) = 0` |
| T10a | `rhsR_one/two/three` | for `c 0 = 0`: `rhsR w c 1 = -1`; `rhsR w c 2 = c 1 * (gOMK w / 2 - 2 * c 1)`; `rhsR w c 3 = 3 * gOMK w / 2 * c 2 - 6 * c 1 * c 2 - aOMK w * c 1 ^ 3` |
| T10b | `coeff_one_of_invariant` | `(w) (c) (hc0) (hinv : invRes w (mk c) = 0) (h1 : 3 * w + 5 ≠ 0) : c 1 = -2 / (3 * w + 5)` (`[CharZero F]`) |
| T10c | `coeff_two_of_invariant` | `... (h1) (h2 : 9 * w + 7 ≠ 0) : c 2 = -2 * (9 * w ^ 2 + 18 * w + 13) / ((3 * w + 5) ^ 2 * (9 * w + 7))` |
| T10d | `coeff_two_spec_form` | same hyps: `c 2 = c 1 * (gOMK w / 2 - 2 * c 1) / (2 * gOMK w + aOMK w)` (pr131 form, s = -a) |
| T10e | `coeff_three_of_invariant` | `... (h1) (h2) (h3 : 5 * w + 3 ≠ 0) : c 3 = -2 * (81 * w ^ 4 + 324 * w ^ 3 + 594 * w ^ 2 + 460 * w + 141) / ((3 * w + 5) ^ 3 * (5 * w + 3) * (9 * w + 7))` |
| T10f | `dust_values` / `radiation_values` | `[CharZero F]`, `c 0 = 0`, `invRes 0 (mk c) = 0 → c 1 = -2/5 ∧ c 2 = -26/175 ∧ c 3 = -94/875`; `w = 1/3 → -1/3, -1/9, -2/27` |
| T11 | `linear_graph_not_invariant` | `[CharZero F] (w : F) (h1 : 3 * w + 5 ≠ 0) (h2 : 9 * w + 7 ≠ 0) (hq : 9 * w ^ 2 + 18 * w + 13 ≠ 0) (κ : F) : invRes w (C κ * X) ≠ 0` |
| T11b | `linear_graph_not_invariant_on_domain` | `(w : ℝ) (hlo : -1/3 < w) (hhi : w < 1) (κ : ℝ) : invRes w (C κ * X) ≠ 0` |
| T12 | `linear_line_defect` | `(w K : F) (h1 : 3 * w + 5 ≠ 0) : fSigma w (-2 / (3 * w + 5) * K) K - (-2 / (3 * w + 5)) * fK w (-2 / (3 * w + 5) * K) K = (-2 / (3 * w + 5)) * ((1 + 3 * w) / 2 - 2 * (-2 / (3 * w + 5))) * K ^ 2 - 3 / 2 * (1 - w) * (-2 / (3 * w + 5)) ^ 3 * K ^ 3` (real-point tangency defect of the line Sigma = kappa K; `A = F`) |
| T12b | `dust_line_counterexample` | `fSigma (0 : ℚ) (-2/5 * (1/10)) (1/10) - (-2/5) * fK (0 : ℚ) (-2/5 * (1/10)) (1/10) = -319/62500` (recorded counterexample: at w = 0, K = 1/10 the vector field is not tangent to Sigma = -2K/5) |
| N1 | `no_solution_order_one_resonance` | `[CharZero F] (c) (hc0) : invRes (-5/3 : F) (mk c) ≠ 0` (negative control: incompatible at n = 1) |
| N2 | `no_solution_order_two_resonance` | `[CharZero F] (c) (hc0) : invRes (-7/9 : F) (mk c) ≠ 0` (compatibility fails: rhsR 2 = -5/8) |
| N3 | `no_solution_order_three_resonance` | `[CharZero F] (c) (hc0) : invRes (-3/5 : F) (mk c) ≠ 0` (compatibility fails: rhsR 3 = -567/512) |
| V1 | `dust_solution_exists` | `∃ c : ℕ → ℝ, c 0 = 0 ∧ invRes 0 (mk c) = 0 ∧ c 2 = -26/175` (non-vacuity) |

Quantifier fidelity notes:
- T2/T3 are for every n (formal power series coefficient comparison), not a finite scan.
- T5/T6 characterize ALL formal zero-constant invariant graphs for EVERY w (resonant or not):
  at each resonant order the coefficient is free and the compatibility condition
  `rhsR w c n = 0` is necessary and sufficient. The general compatibility condition is
  stated, not decided, for n >= 4; N1-N3 decide it for the first three resonances.
- T11 is a formal-power-series statement; T12/T12b are real-point statements on the
  vector field itself.
- Not claimed: convergence of the series, analyticity of the manifold, remainder bounds,
  non-LRS perturbation stability, any observational value, scientific admission.
