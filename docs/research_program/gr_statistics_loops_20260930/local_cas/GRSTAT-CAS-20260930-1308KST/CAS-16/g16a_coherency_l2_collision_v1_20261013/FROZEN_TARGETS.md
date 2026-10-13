# G16-A frozen targets

Origin: written fresh by this author run (T did not exist at start; no earlier FROZEN_TARGETS.md). Signatures
were elaboration-checked with `sorry` bodies in the scratch probe `raw/probes/p02_signatures.lean` (exit 0,
output kept in `p02_signatures.lean.out`) before any proof compile of the module. No proof was attempted before
freezing. Module: `lean/G16ACoherency.lean`, namespace `G16ACoherency`, imports `Mathlib` and the unchanged
CAS16-C01 `ProjectorBridge`.

## Fixed definitions (verbatim)

```lean
attribute [local instance] Matrix.frobeniusNormedAddCommGroup Matrix.frobeniusNormedSpace
  Matrix.frobeniusNormSMulClass Matrix.frobeniusIsBoundedSMul
abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := sphere (0 : E3) 1
abbrev CMat := Matrix (Fin 3) (Fin 3) ℂ          -- full complex coherency, common Cartesian frame
def dΩ : Measure S2 := (volume : Measure E3).toSphere          -- unnormalized solid angle
def vecOf (e : S2) : CAS16Projector.Vec := fun i => (e : E3) i
def Pc (v : CAS16Projector.Vec) : CMat := (CAS16Projector.projector v).map (fun r : ℝ => (r : ℂ))
def gainField (μ : Measure X) (c : ℝ) (P : X → CMat) (J : X → CMat) : X → CMat :=
  fun x => c • (P x * (∫ y, J y ∂μ) * P x)
def collisionField (μ : Measure X) (Γ c : ℝ) (P : X → CMat) (J : X → CMat) : X → CMat :=
  fun x => Γ • (-(J x) + gainField μ c P J x)
def thomsonP (e : S2) : CMat := Pc (vecOf e)
def thomsonGain (J : S2 → CMat) : S2 → CMat := gainField dΩ (3 / (8 * Real.pi)) thomsonP J
def thomsonCollision (Γ : ℝ) (J : S2 → CMat) : S2 → CMat :=
  collisionField dΩ Γ (3 / (8 * Real.pi)) thomsonP J
def collisionCLM (Γ : ℝ) : Lp CMat 2 dΩ →L[ℝ] Lp CMat 2 dΩ := Γ • (gainCLM - ContinuousLinearMap.id ℝ _)
def dΩnorm : Measure S2 := (ENNReal.ofReal (4 * Real.pi))⁻¹ • dΩ
```
`thomsonCollision Γ J e = Γ[−J(e) + 3/(8π) P_e (∫ J dΩ) P_e]` is exactly DOSSIER (C1) / Dossier IV (89)·c.
`gainCLM` is a constructed definition; T6a ties it to `thomsonGain` almost everywhere.

## Targets (exact statements)

| id | name | statement |
|---|---|---|
| T1 | `pointwise_complex_contraction` | `(v : CAS16Projector.Vec) (hv : ∑ i, v i * v i = 1) (A : CMat) : ‖Pc v * A * Pc v‖ ≤ ‖A‖` |
| T2 | `sphere_mass` | `dΩ Set.univ = ENNReal.ofReal (4 * Real.pi)` (plus `IsFiniteMeasure dΩ` instance) |
| T3 | `integral_cauchy` | `(J : S2 → CMat) (hJ : MemLp J 2 dΩ) : ‖∫ e, J e ∂dΩ‖ ≤ Real.sqrt (4 * Real.pi) * (eLpNorm J 2 dΩ).toReal` |
| T4 | `gain_L2_bound` | `(J : S2 → CMat) (hJ : MemLp J 2 dΩ) : MemLp (thomsonGain J) 2 dΩ ∧ eLpNorm (thomsonGain J) 2 dΩ ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩ` |
| T5 | `collision_L2_bound` | `(Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ) : MemLp (thomsonCollision Γ J) 2 dΩ ∧ eLpNorm (thomsonCollision Γ J) 2 dΩ ≤ ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩ` |
| T6a | `gainCLM_ae` | `(J : Lp CMat 2 dΩ) : (gainCLM J : S2 → CMat) =ᵐ[dΩ] thomsonGain (J : S2 → CMat)` |
| T6b | `gainCLM_opNorm` | `‖gainCLM‖ ≤ 3 / 2` |
| T6c | `collisionCLM_ae` | `(Γ : ℝ) (J : Lp CMat 2 dΩ) : (collisionCLM Γ J : S2 → CMat) =ᵐ[dΩ] thomsonCollision Γ (J : S2 → CMat)` |
| T6d | `collisionCLM_opNorm` | `(Γ : ℝ) (hΓ : 0 ≤ Γ) : ‖collisionCLM Γ‖ ≤ 5 / 2 * Γ` |
| T7a | `normalized_mass` | `dΩnorm Set.univ = 1` |
| T7b | `normalized_operator_eq` | `(Γ : ℝ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ) : collisionField dΩnorm Γ (3 / 2) thomsonP J = thomsonCollision Γ J` |
| T7c | `normalized_bounds` | `(Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩnorm) : eLpNorm (gainField dΩnorm (3 / 2) thomsonP J) 2 dΩnorm ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩnorm ∧ eLpNorm (collisionField dΩnorm Γ (3 / 2) thomsonP J) 2 dΩnorm ≤ ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩnorm` |
| T7d | `normalized_norm_scaling` | `(f : S2 → CMat) : eLpNorm f 2 dΩnorm = (ENNReal.ofReal (4 * Real.pi))⁻¹ ^ (1 / 2 : ℝ) * eLpNorm f 2 dΩ` |
| N1 | `neg_control_nonunit` | `¬ (‖Pc ![2, 0, 0] * Matrix.single 0 0 1 * Pc ![2, 0, 0]‖ ≤ ‖(Matrix.single 0 0 1 : CMat)‖)` — the unit hypothesis in T1 cannot be dropped |
| N2 | `isotropic_gain_witness` | `(e : S2) : thomsonGain (fun _ => (1 : CMat)) e = ((3 / 2 : ℝ) : ℂ) • thomsonP e` — non-vacuity / normalization witness (gain of the identity field equals (3/2)P_e, nonzero) |

## Alignment with the card
- Quantifiers: T4/T5/T6 are universal over all of L²(S², ℂ^{3×3}) (Bochner L² w.r.t. Frobenius norm), Γ ≥ 0
  as in the contract. Physical coherency fields (Hermitian, transverse, PSD) are a subset; no extra structure is
  assumed, so nothing is strengthened. The full (not intensity-only) complex coherency is used.
- Measure: unnormalized dΩ with mass 4π (T2 proved, not assumed); normalized convention handled by T7.
- Gain constant 3/2 = (3/(8π))·√(4π)·√(4π); full constant 5Γ/2 = Γ(1 + 3/2) via the triangle inequality.
- Not claimed: optimality of 3/2 or 5/2; tilted/moving-electron operator (Dossier IV (96)); physical identity
  Γ = c n_e σ_T; any Boltzmann/transfer statement; scientific admission.
