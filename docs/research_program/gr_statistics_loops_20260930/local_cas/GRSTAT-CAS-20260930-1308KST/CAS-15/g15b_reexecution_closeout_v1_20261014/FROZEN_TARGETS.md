# G15-B re-execution closeout — FROZEN TARGETS

Frozen 2026-10-14 (UTC 2026-10-13T21:4x), BEFORE any compile attempt in this unit
(no `raw/compile_*` file existed when this file was written).
Toolchain: Lean 4.31.0 + mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f,
Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`.
Any later change to a statement below must be recorded as a deviation in AUTHOR_RETURN.json.

## Part A — the 32 reviewed frozen statements, re-executed UNCHANGED

The frozen statements of this part are exactly the 32 theorem statements (blocks S, W, M, D, N,
I, G, B) and the definitions of the prior unit's FROZEN_TARGETS.md:

* prior file: `CAS-15/g15b_sphere_divergence_ibp_v1_20261014/FROZEN_TARGETS.md`,
  sha256 `58469ea396138b7cab0174ce4b5fc5139f960838f1d22aa70f163be6c21671ec`;
* verbatim copy in this unit: `prior/FROZEN_TARGETS_prior_58469ea3.md` (same sha256).

Names (namespace `G15B`):

| block | statements |
|---|---|
| S | Pt_tangent, gradS_inner, gradS_tangent, fderiv_eq_of_eqOn_sphere, dS_eq_of_eqOn_sphere, divS_eq_of_eqOn_sphere, dS_eq_fderiv_of_tangent, Ffield_tangent, skew_tangent |
| W | divS_eq_trace, divS_skew, divS_Ffield, divS_Ffield_tracefree, fderiv_quadWeight, divS_smul |
| M | σS_rotInv |
| D | integral_fderiv_skew, divergence_theorem, divergence_theorem_σS |
| N | divS_radial, radial_negative_control, skew_witness, witness_first_moment |
| I | ibp, commutator_moments, angular_B5, weak_residual_B5, weak_quadrupole_commutator |
| G | wB5_degree_le_four, B5_rank_le_four_moments |
| B | bridge_Fcov, bridge_Rrate |

Sources re-executed with no edits (sha256 equality with the reviewed files is required):

| file in this unit | origin | sha256 |
|---|---|---|
| `lean/G15BSphere.lean` | `CAS-15/g15b_sphere_divergence_ibp_v1_20261014/lean/G15BSphere.lean` | `d08907e948e85a0f58fe95cc59afd1f71eef1a5f56870434c5792c8cafafc6b8` |
| `lean/G15APhoton.lean` | `CAS-15/g15a_photon_energy_direction_v1_20261013/lean/G15APhoton.lean` | `fc4d060643fc84a83beb729926df21b70480328dbf2eaab73bd5e31d541a7e39` |

Scope reminder for Part A (unchanged from the prior unit): `B5_rank_le_four_moments` is I-wise,
i.e. ∀ μ ∀ I ∃ p, so p may depend on I (review note N2). It is NOT relabelled here as the
uniform rank ≤ 4 claim; that claim is target U below.

## Part B — ONE new additive target U (new module `lean/G15BUniform.lean`)

`G15BUniform.lean` imports `Mathlib` and `G15BSphere` (unchanged) and opens namespace
`G15BU`. It introduces no new definitions of physical objects; it uses `G15B.E3`, `G15B.S2`,
`G15B.RotInv`, `G15B.wB5`, `G15B.σS` exactly as in Part A.

Review note N2: the dossier phrase "only brightness moments through rank four are needed"
(DOSSIER_POSITIVE_BRIDGE.md l.149; CAS-15.json l.263 "onlyrank<=4") is uniform in the
brightness I. Target U states it with ONE polynomial p, chosen before μ and I.

### U (the additive target) — uniform rank ≤ 4

```lean
theorem B5_rank_le_four_uniform (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      (∀ m ∈ p.support, (m.sum fun _ n => n) ≤ 4) ∧
      ∀ (μ : Measure S2) [IsFiniteMeasure μ], RotInv μ → ∀ I : E3 → ℝ, Continuous I →
        (∫ e : S2, I e * wB5 H a σ e i j ∂μ =
            ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂μ) ∧
        ∫ e : S2, I e * wB5 H a σ e i j ∂μ =
          ∑ m ∈ p.support, MvPolynomial.coeff m p * ∫ e : S2, I e * ∏ k, (e : E3) k ^ m k ∂μ
```

Quantifier order: the parameters (H, a, σ, i, j) of the (B5) weight come first; then ∃ p;
then ∀ μ (finite, rotation-invariant), ∀ I (continuous). p is therefore independent of μ and
I. The quantifiers, domain (S2), measure class (finite + `RotInv`, with `σS` the dΩ instance)
and regularity (continuous I) are the requested ones. Route: derived from the reviewed
`G15B.wB5_degree_le_four` plus linearity of the integral (pointwise rewriting of the integrand,
then `integral_finsetSum` / `integral_const_mul`). No formula is postulated.

### Supporting lemma (same content, measure class not restricted)

```lean
theorem B5_rank_le_four_uniform_finite (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      (∀ m ∈ p.support, (m.sum fun _ n => n) ≤ 4) ∧
      ∀ (μ : Measure S2) [IsFiniteMeasure μ], ∀ I : E3 → ℝ, Continuous I →
        (∫ e : S2, I e * wB5 H a σ e i j ∂μ =
            ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂μ) ∧
        ∫ e : S2, I e * wB5 H a σ e i j ∂μ =
          ∑ m ∈ p.support, MvPolynomial.coeff m p * ∫ e : S2, I e * ∏ k, (e : E3) k ^ m k ∂μ
```

This drops the `RotInv` hypothesis (weaker assumption, recorded explicitly; rotation invariance
is not used by this algebraic step). U is obtained from it by discarding `RotInv μ`.

### Non-vacuity witness and negative control

```lean
-- non-vacuity: the hypothesis class of U is inhabited by the dΩ instance σS
theorem B5_rank_le_four_uniform_σS (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      ∀ I : E3 → ℝ, Continuous I →
        ∫ e : S2, I e * wB5 H a σ e i j ∂σS =
          ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂σS

-- negative control (review note N2): the I-wise quantifier order ∀ μ ∀ I ∃ p is degenerate;
-- whenever ∫ I dμ ≠ 0 a DEGREE-0 polynomial reproduces ANY prescribed value v
theorem iwise_form_degenerate (μ : Measure S2) {I : E3 → ℝ}
    (hI0 : ∫ e : S2, I e ∂μ ≠ 0) (v : ℝ) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 0 ∧
      ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂μ = v
```

The negative control shows the I-wise form carries no degree information on its own, so the
uniform form U is genuinely the stronger statement.

## Not claimed

* Sharpness of the degree-4 bound (generic attainment is not formalized).
* (B2) transport itself; C¹ extension existence; `σS` = Hausdorff measure and total mass 4π
  (all as in the prior unit).
* Recovery of the prior unit's lost development failure history (UNAVAILABLE; not recovered).
* Independent fresh review of `G15BUniform.lean`; scientific admission (HOLD).
