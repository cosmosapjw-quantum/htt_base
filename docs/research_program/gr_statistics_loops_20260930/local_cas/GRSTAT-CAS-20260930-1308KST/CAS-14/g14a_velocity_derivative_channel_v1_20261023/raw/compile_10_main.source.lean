import Mathlib
import Main
import VelocityJetDecomposition

/-!
# G14-A: the velocity-derivative observation channel `J(x) = h ∇_x U`

Card `tasks/G14-A.json` (GR-CAS-14).  Sources: `supplements/DOSSIER_POSITIVE_BRIDGE.md`
Eqs. (P0), (A1), (A2) and corrections 1, 4, 5; `cas/contracts/CAS-14.json`
(assumption `IndependentJ(x)=h∇_xU, known source/transport/length`, exclusions
`No propermotion=J`, `No staticremote derivative`, `No tetradspin confusion`);
`cas/COMMON_SPEC.md`.  See `SOURCE_RECOVERY.md`.

Reused UNCHANGED (compiled into `raw/imports`):
* `Main` = CAS-14 PR #487 C01-C03 (namespace `CAS14`): `W`, `P`, `G`, `b`, `G_equiv`,
  `C02_inverse_formula`, `W_sign`.
* `VelocityJetDecomposition` = P03-A (namespace `PORTCAS03VelocityJetDecomposition`):
  `pd`, `nablaUp`, `velJet`, `projUp`, `MetricCompatibleAt`, `FieldDiffAt`, Minkowski
  instances `gMink`, `Γ0`, `uEx`, `uRest`, `Dex`.

Conventions: signature `(-,+,+,+)`, `U = c u`, derivative-first `D_ab = ∇_a u_b`,
`Γ x c a d = Γ^c_{ad}(x)`, `∇_a U^c = ∂_a U^c + Γ^c_{ad} U^d`, `h^a_b = δ^a_b + u^a u_b`.
`J(x)^b = h^b_c x^a ∇_a U^c`.

No statement below assumes `proper motion = J`; T5 derives the relation in a declared
flat, instantaneous, low-velocity model and exhibits its non-identifications.
-/

open Matrix Filter Set
open scoped Topology Matrix

namespace G14A

open PORTCAS03VelocityJetDecomposition (pd nablaUp projUp velJet velJetMatrix
  MetricCompatibleAt FieldDiffAt velJet_eq_lower gMink Γ0 uEx uRest Dex)

abbrev Pt := Fin 4 → ℝ
abbrev Op := Pt →L[ℝ] Pt
abbrev V3 := Fin 3 → ℝ

/-! ## Typed channel definitions -/

/-- `(Γ_X)^c_d = X^a Γ^c_{ad}(p)`. -/
def gammaMat (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (p X : Pt) : Matrix (Fin 4) (Fin 4) ℝ :=
  Matrix.of fun c d => ∑ a, X a * Γ p c a d

/-- `Γ_X` as a continuous linear operator on coordinate components. -/
noncomputable def gammaOp (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (p X : Pt) : Op :=
  LinearMap.toContinuousLinearMap (Matrix.toLin' (gammaMat Γ p X))

/-- Coordinate (partial) derivative `X^a ∂_a U^c` at `p`. -/
noncomputable def coordDeriv (U : Pt → Pt) (p X : Pt) : Pt :=
  fun c => ∑ a, X a * pd (fun y => U y c) p a

/-- Covariant derivative `X^a ∇_a U^c` at `p` (P03-A `nablaUp`). -/
noncomputable def covDeriv (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (U : Pt → Pt) (p X : Pt) : Pt :=
  fun c => ∑ a, X a * nablaUp Γ U p a c

/-- The observation channel `J(x) = h ∇_x U` (Eq. (A1) target). -/
noncomputable def Jchan (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Pt)
    (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (U : Pt → Pt) (p X : Pt) : Pt :=
  projUp (g p) (u p) *ᵥ covDeriv Γ U p X

/-- Tetrad spin (connection coefficients) of a frame field along `X`:
`S = E0⁻¹ (dE/ds + Γ_X E0)`, i.e. `∇_X e_I = e_J S^J_I`. -/
noncomputable def spinOf (E0 : Opˣ) (E' : Op) (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (p X : Pt) : Op :=
  (↑E0⁻¹ : Op) * (E' + gammaOp Γ p X * (E0 : Op))

/-- `P_{q_s → p} U(q_s)`: the velocity at `q_s` transported back to `p`, where `Tr s` is the
forward transport `T_p → T_{q_s}` in coordinate components. -/
noncomputable def transportBack (Tr : ℝ → Op) (U : Pt → Pt) (q : ℝ → Pt) (s : ℝ) : Pt :=
  Ring.inverse (Tr s) (U (q s))

/-- The declared finite-baseline map of Eq. (A1): `h_p [P_{q_s→p} U(q_s) - U(p)] / s`. -/
noncomputable def finiteBaselineMap (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Pt)
    (Tr : ℝ → Op) (U : Pt → Pt) (q : ℝ → Pt) (p : Pt) (s : ℝ) : Pt :=
  projUp (g p) (u p) *ᵥ (s⁻¹ • (transportBack Tr U q s - U p))

/-- Transport rule input: the parallel-transport equation `dTr/ds = -Γ(q̇, ·) Tr` at `s = 0`,
with `Tr 0 = 1` and `q̇ 0 = X`. -/
structure TransportGerm (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (p X : Pt) (Tr : ℝ → Op) :
    Prop where
  base : Tr 0 = 1
  deriv : HasDerivAt Tr (-(gammaOp Γ p X)) 0

theorem gammaOp_apply (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (p X v : Pt) :
    gammaOp Γ p X v = gammaMat Γ p X *ᵥ v := by
  simp [gammaOp, Matrix.toLin'_apply]

/-! ## T1 coordinate-derivative correction -/

theorem covDeriv_eq_coordDeriv_add (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (U : Pt → Pt)
    (p X : Pt) :
    covDeriv Γ U p X = coordDeriv U p X + gammaMat Γ p X *ᵥ U p := by
  funext c
  simp only [covDeriv, coordDeriv, nablaUp, gammaMat, Pi.add_apply, mulVec, dotProduct,
    Matrix.of_apply, Fin.sum_univ_four]
  ring

theorem J_sub_coord (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Pt)
    (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (U : Pt → Pt) (p X : Pt) :
    Jchan g u Γ U p X - projUp (g p) (u p) *ᵥ coordDeriv U p X
      = projUp (g p) (u p) *ᵥ (gammaMat Γ p X *ᵥ U p) := by
  rw [Jchan, covDeriv_eq_coordDeriv_add, Matrix.mulVec_add, add_sub_cancel_left]

/-! ## T2 frame-component derivative and tetrad spin -/

theorem single_decomp (X : Pt) : X = ∑ a, X a • (Pi.single a (1 : ℝ) : Pt) := by
  ext j
  simp [Finset.sum_apply, Pi.single_apply]

theorem coordinate_components_hasDerivAt {U : Pt → Pt} {p X : Pt} {q : ℝ → Pt}
    (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    HasDerivAt (fun s => U (q s)) (coordDeriv U p X) 0 := by
  rw [hasDerivAt_pi]
  intro c
  have h1 : HasFDerivAt (fun y => U y c) (fderiv ℝ (fun y => U y c) p) (q 0) := by
    rw [hq0]; exact (hU c).hasFDerivAt
  have h2 := h1.comp_hasDerivAt (0 : ℝ) hq
  have hval : coordDeriv U p X c = fderiv ℝ (fun y => U y c) p X := by
    conv_rhs => rw [single_decomp X]
    rw [map_sum]
    simp only [coordDeriv, pd, map_smul, smul_eq_mul]
  rw [hval]
  exact h2

theorem unit_apply_inv (E0 : Opˣ) (v : Pt) : (E0 : Op) ((↑E0⁻¹ : Op) v) = v := by
  rw [← mul_apply_eq_comp, Units.mul_inv, one_apply_eq_self]

theorem frame_components_hasDerivAt {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {U : Pt → Pt}
    {p X : Pt} {E : ℝ → Op} {E' : Op} {E0 : Opˣ} {q : ℝ → Pt}
    (hE0 : E 0 = E0) (hE : HasDerivAt E E' 0) (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    HasDerivAt (fun s => Ring.inverse (E s) (U (q s)))
      ((↑E0⁻¹ : Op) (covDeriv Γ U p X) - spinOf E0 E' Γ p X ((↑E0⁻¹ : Op) (U p))) 0 := by
  have hinv : HasFDerivAt (Ring.inverse : Op → Op)
      (-ContinuousLinearMap.mulLeftRight ℝ Op (↑E0⁻¹ : Op) (↑E0⁻¹ : Op)) (E 0) := by
    rw [hE0]; exact hasFDerivAt_ringInverse (𝕜 := ℝ) E0
  have hI := hinv.comp_hasDerivAt (0 : ℝ) hE
  have hV := coordinate_components_hasDerivAt (U := U) hq0 hq hU
  have h : HasDerivAt (fun s => Ring.inverse (E s) (U (q s)))
      ((-ContinuousLinearMap.mulLeftRight ℝ Op (↑E0⁻¹ : Op) (↑E0⁻¹ : Op)) E' (U (q 0)) +
        (Ring.inverse (E 0)) (coordDeriv U p X)) 0 := hI.clm_apply hV
  refine h.congr_deriv ?_
  rw [hq0, hE0, Ring.inverse_unit]
  simp only [ContinuousLinearMap.neg_apply, ContinuousLinearMap.mulLeftRight_apply,
    mul_apply_eq_comp, spinOf, ContinuousLinearMap.add_apply, unit_apply_inv,
    covDeriv_eq_coordDeriv_add, map_add, gammaOp_apply]
  abel

theorem spinOf_parallel {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {p X : Pt} {E' : Op}
    (E0 : Opˣ) (h : E' = -(gammaOp Γ p X * (E0 : Op))) : spinOf E0 E' Γ p X = 0 := by
  simp [spinOf, h]

theorem spinOf_coordinate (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (p X : Pt) :
    spinOf 1 0 Γ p X = gammaOp Γ p X := by
  simp [spinOf]

/-- Rest tetrad (`E0⁻¹ U(p) = c e0`): the tetrad-spin correction is `-c S e0`. -/
theorem rest_tetrad_spin_correction {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {U : Pt → Pt}
    {p X : Pt} {E : ℝ → Op} {E' : Op} {E0 : Opˣ} {q : ℝ → Pt} {c : ℝ}
    (hrest : (↑E0⁻¹ : Op) (U p) = c • PortCas01.e0)
    (hE0 : E 0 = E0) (hE : HasDerivAt E E' 0) (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    HasDerivAt (fun s => Ring.inverse (E s) (U (q s)))
      ((↑E0⁻¹ : Op) (covDeriv Γ U p X) - c • spinOf E0 E' Γ p X PortCas01.e0) 0 := by
  have h := frame_components_hasDerivAt (Γ := Γ) hE0 hE hq0 hq hU
  rwa [hrest, map_smul] at h

theorem rotation_spin_rest_free (S : Op) (hS : S PortCas01.e0 = 0) (c : ℝ) :
    S (c • PortCas01.e0) = 0 := by
  rw [map_smul, hS, smul_zero]

/-- Boost generator `K₁` (mixes `e0` and `e1`). -/
def boostGenMat : Matrix (Fin 4) (Fin 4) ℝ :=
  !![0, 1, 0, 0; 1, 0, 0, 0; 0, 0, 0, 0; 0, 0, 0, 0]

/-- Rotation generator `R₃` (rotates `e1` into `e2`). -/
def rotGenMat : Matrix (Fin 4) (Fin 4) ℝ :=
  !![0, 0, 0, 0; 0, 0, -1, 0; 0, 1, 0, 0; 0, 0, 0, 0]

noncomputable def boostGen : Op := LinearMap.toContinuousLinearMap (Matrix.toLin' boostGenMat)
noncomputable def rotGen : Op := LinearMap.toContinuousLinearMap (Matrix.toLin' rotGenMat)

theorem rotGen_e0 : rotGen PortCas01.e0 = 0 := by
  ext i
  fin_cases i <;> simp [rotGen, rotGenMat, Matrix.toLin'_apply, PortCas01.e0, mulVec,
    dotProduct, Fin.sum_univ_four]

/-- Negative control: a boost-type tetrad spin contaminates the rest-tetrad derivative. -/
theorem boost_spin_witness (c : ℝ) (hc : c ≠ 0) :
    boostGen (c • PortCas01.e0) = c • (![0, 1, 0, 0] : Pt) ∧ c • (![0, 1, 0, 0] : Pt) ≠ 0 := by
  refine ⟨?_, ?_⟩
  · ext i
    fin_cases i <;> simp [boostGen, boostGenMat, Matrix.toLin'_apply, PortCas01.e0, mulVec,
      dotProduct, Fin.sum_univ_four]
  · intro h
    have := congrFun h 1
    simp at this
    exact hc this

/-- Negative control: in a non-rest tetrad (`U(p)` with spatial part `v`), a pure rotation
spin produces a nonzero correction. -/
theorem rotation_spin_nonrest_witness (a v : ℝ) (hv : v ≠ 0) :
    rotGen ![a, v, 0, 0] = ![0, 0, v, 0] ∧ (![0, 0, v, 0] : Pt) ≠ 0 := by
  refine ⟨?_, ?_⟩
  · ext i
    fin_cases i <;> simp [rotGen, rotGenMat, Matrix.toLin'_apply, mulVec, dotProduct,
      Fin.sum_univ_four]
  · intro h
    have := congrFun h 2
    simp at this
    exact hv this

/-! ## T3 finite-baseline channel (A1), remainder and calibration -/

theorem transportBack_hasDerivAt {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {U : Pt → Pt}
    {p X : Pt} {Tr : ℝ → Op} {q : ℝ → Pt}
    (hTr : TransportGerm Γ p X Tr) (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    HasDerivAt (transportBack Tr U q) (covDeriv Γ U p X) 0 := by
  have hb : Tr 0 = ((1 : Opˣ) : Op) := by rw [Units.val_one]; exact hTr.base
  have h := frame_components_hasDerivAt (Γ := Γ) (E0 := 1) hb hTr.deriv hq0 hq hU
  have hs : spinOf 1 (-(gammaOp Γ p X)) Γ p X = 0 :=
    spinOf_parallel (Γ := Γ) 1 (by simp)
  rw [hs] at h
  unfold transportBack
  refine h.congr_deriv ?_
  simp

theorem finiteBaseline_tendsto_J {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Pt}
    {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {U : Pt → Pt} {p X : Pt} {Tr : ℝ → Op}
    {q : ℝ → Pt}
    (hTr : TransportGerm Γ p X Tr) (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    Tendsto (finiteBaselineMap g u Tr U q p) (𝓝[≠] 0) (𝓝 (Jchan g u Γ U p X)) := by
  have hd := transportBack_hasDerivAt hTr hq0 hq hU
  have hs := hasDerivAt_iff_tendsto_slope.mp hd
  have h0 : transportBack Tr U q 0 = U p := by
    simp [transportBack, hTr.base, hq0]
  have hcont : Continuous fun v : Pt => projUp (g p) (u p) *ᵥ v :=
    Continuous.matrix_mulVec continuous_const continuous_id
  have hT := (hcont.tendsto _).comp hs
  refine hT.congr' (Eventually.of_forall fun s => ?_)
  simp [finiteBaselineMap, slope_def_module, h0]

/-- Negative control: without transport (`Tr ≡ 1`) the quotient converges to the coordinate
derivative, i.e. to `J - h Γ_X U`, not to `J`. -/
theorem untransported_baseline_bias {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Pt}
    {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {U : Pt → Pt} {p X : Pt} {q : ℝ → Pt}
    (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    Tendsto (finiteBaselineMap g u (fun _ => 1) U q p) (𝓝[≠] 0)
      (𝓝 (Jchan g u Γ U p X - projUp (g p) (u p) *ᵥ (gammaMat Γ p X *ᵥ U p))) := by
  have hd := coordinate_components_hasDerivAt hq0 hq hU
  have hs := hasDerivAt_iff_tendsto_slope.mp hd
  have hcont : Continuous fun v : Pt => projUp (g p) (u p) *ᵥ v :=
    Continuous.matrix_mulVec continuous_const continuous_id
  have hT := (hcont.tendsto _).comp hs
  have hlim : projUp (g p) (u p) *ᵥ coordDeriv U p X
      = Jchan g u Γ U p X - projUp (g p) (u p) *ᵥ (gammaMat Γ p X *ᵥ U p) := by
    rw [← J_sub_coord g u Γ U p X, sub_sub_cancel]
  rw [← hlim]
  refine hT.congr' (Eventually.of_forall fun s => ?_)
  simp [finiteBaselineMap, slope_def_module, transportBack, hq0]

/-- Finite-baseline remainder for any declared positive norm. -/
theorem finiteBaseline_remainder {F : Type*} [NormedAddCommGroup F] [NormedSpace ℝ F]
    {f f' : ℝ → F} {s M : ℝ} (hs : 0 < s) (hM : 0 ≤ M)
    (hf : ∀ t ∈ Icc 0 s, HasDerivWithinAt f (f' t) (Icc 0 s) t)
    (hlip : ∀ t ∈ Ico 0 s, ‖f' t - f' 0‖ ≤ M * t) :
    ‖s⁻¹ • (f s - f 0) - f' 0‖ ≤ M * s := by
  set φ : ℝ → F := fun t => f t - t • f' 0 with hφdef
  have hφ : ∀ t ∈ Icc 0 s, HasDerivWithinAt φ (f' t - f' 0) (Icc 0 s) t := by
    intro t ht
    have h2 := (hf t ht).sub ((hasDerivWithinAt_id (s := Icc 0 s) (x := t)).smul_const (f' 0))
    rw [one_smul] at h2
    exact h2
  have hb : ∀ t ∈ Ico 0 s, ‖f' t - f' 0‖ ≤ M * s := fun t ht =>
    (hlip t ht).trans (mul_le_mul_of_nonneg_left ht.2.le hM)
  have key := norm_image_sub_le_of_norm_deriv_le_segment' hφ hb s ⟨hs.le, le_rfl⟩
  have hrw : s⁻¹ • (f s - f 0) - f' 0 = s⁻¹ • (φ s - φ 0) := by
    simp only [hφdef, zero_smul, sub_zero, smul_sub, smul_smul, inv_mul_cancel₀ hs.ne',
      one_smul]
    abel
  rw [hrw, norm_smul, Real.norm_eq_abs, abs_inv, abs_of_pos hs]
  calc s⁻¹ * ‖φ s - φ 0‖ ≤ s⁻¹ * (M * s * (s - 0)) :=
        mul_le_mul_of_nonneg_left key (inv_nonneg.mpr hs.le)
    _ = M * s := by
        rw [sub_zero, mul_comm, mul_assoc, mul_inv_cancel₀ hs.ne', mul_one]

/-- Clock/velocity calibration `κ` and length calibration `ℓ` of the reported baseline:
the measured quotient converges to `(κ/ℓ) J`. -/
theorem calibrated_quotient_tendsto (κ ℓ : ℝ) {dU : ℝ → Pt} {J : Pt}
    (h : Tendsto (fun s => s⁻¹ • dU s) (𝓝[≠] 0) (𝓝 J)) :
    Tendsto (fun s => (ℓ * s)⁻¹ • (κ • dU s)) (𝓝[≠] 0) (𝓝 ((κ / ℓ) • J)) := by
  have := h.const_smul (κ / ℓ)
  refine this.congr' (Eventually.of_forall fun s => ?_)
  simp only [smul_smul, mul_inv, div_eq_mul_inv]
  ring_nf

theorem miscalibration_changes_limit (κ ℓ : ℝ) (J : Pt) (hJ : J ≠ 0) (h : κ / ℓ ≠ 1) :
    (κ / ℓ) • J ≠ J := by
  intro hc
  have h2 : (κ / ℓ - 1) • J = 0 := by rw [sub_smul, hc, one_smul, sub_self]
  rcases smul_eq_zero.mp h2 with h3 | h3
  · exact h (sub_eq_zero.mp h3)
  · exact hJ h3

/-! ## T5 observer-time proper motion (declared flat, instantaneous, low-velocity model) -/

/-- Unit direction of a nonzero relative position. -/
noncomputable def dirOf (r : V3) : V3 := (Real.sqrt (r ⬝ᵥ r))⁻¹ • r

/-- `Ω × ·` as a continuous linear map. -/
noncomputable def crossOp (Ω : V3) : V3 →L[ℝ] V3 :=
  LinearMap.toContinuousLinearMap (crossProduct Ω)

theorem dot_hasDerivAt {r : ℝ → V3} {r' : V3} (hr : HasDerivAt r r' 0) :
    HasDerivAt (fun t => r t ⬝ᵥ r t) (2 * (r 0 ⬝ᵥ r')) 0 := by
  have hc := hasDerivAt_pi.mp hr
  have hs : HasDerivAt (fun t => ∑ i, r t i * r t i)
      (∑ i, (r' i * r 0 i + r 0 i * r' i)) 0 :=
    HasDerivAt.fun_sum (A := fun i t => r t i * r t i) (fun i _ => (hc i).mul (hc i))
  have hs' : HasDerivAt (fun t => r t ⬝ᵥ r t) (∑ i, (r' i * r 0 i + r 0 i * r' i)) 0 := hs
  refine hs'.congr_deriv ?_
  simp only [dotProduct, Fin.sum_univ_three]
  ring

theorem direction_hasDerivAt {r : ℝ → V3} {r' n : V3} {D : ℝ} (hD : 0 < D)
    (hn : n ⬝ᵥ n = 1) (hr0 : r 0 = D • n) (hr : HasDerivAt r r' 0) :
    HasDerivAt (fun t => dirOf (r t)) (D⁻¹ • CAS14.P n r') 0 := by
  have hdd : r 0 ⬝ᵥ r 0 = D * D := by
    rw [hr0, dotProduct_smul, smul_dotProduct, hn]; simp
  have hsq : Real.sqrt (r 0 ⬝ᵥ r 0) = D := by rw [hdd, Real.sqrt_mul_self hD.le]
  have h1 := dot_hasDerivAt hr
  have h2 := h1.sqrt (by rw [hdd]; positivity)
  have h3 := h2.inv (by rw [hsq]; exact hD.ne')
  have h4 := h3.smul hr
  have h5 : HasDerivAt (fun t => dirOf (r t))
      ((Real.sqrt (r 0 ⬝ᵥ r 0))⁻¹ • r' +
        (-(2 * (r 0 ⬝ᵥ r') / (2 * Real.sqrt (r 0 ⬝ᵥ r 0))) /
          Real.sqrt (r 0 ⬝ᵥ r 0) ^ 2) • r 0) 0 := h4
  refine h5.congr_deriv ?_
  rw [hsq, hr0]
  ext i
  simp only [CAS14.P, Pi.smul_apply, Pi.sub_apply, Pi.add_apply, smul_eq_mul,
    dotProduct_smul, smul_dotProduct]
  field_simp
  ring

theorem dirOf_base {n : V3} {D : ℝ} (hD : 0 < D) (hn : n ⬝ᵥ n = 1) : dirOf (D • n) = n := by
  have hdd : (D • n) ⬝ᵥ (D • n) = D * D := by
    rw [dotProduct_smul, smul_dotProduct, hn]; simp
  rw [dirOf, hdd, Real.sqrt_mul_self hD.le, smul_smul, inv_mul_cancel₀ hD.ne', one_smul]

/-- Proper motion read in an observer frame rotating at `Ω` relative to a non-rotating
reference: `μ = D⁻¹ P_n ṙ - Ω × n`. -/
theorem frame_drift_hasDerivAt {r : ℝ → V3} {r' n : V3} {D : ℝ} (R : ℝ → (V3 →L[ℝ] V3))
    (Ω : V3) (hR0 : R 0 = 1) (hR : HasDerivAt R (-(crossOp Ω)) 0) (hD : 0 < D)
    (hn : n ⬝ᵥ n = 1) (hr0 : r 0 = D • n) (hr : HasDerivAt r r' 0) :
    HasDerivAt (fun t => R t (dirOf (r t))) (D⁻¹ • CAS14.P n r' - Ω ⨯₃ n) 0 := by
  have h : HasDerivAt (fun t => R t (dirOf (r t)))
      ((-(crossOp Ω)) (dirOf (r 0)) + (R 0) (D⁻¹ • CAS14.P n r')) 0 :=
    hR.clm_apply (direction_hasDerivAt hD hn hr0 hr)
  refine h.congr_deriv ?_
  have hc : crossOp Ω n = Ω ⨯₃ n := rfl
  rw [hR0, hr0, dirOf_base hD hn, ContinuousLinearMap.neg_apply, hc, one_apply_eq_self]
  abel

/-- Velocity-jet action `J(x)_j = x^i J_ij` (derivative-first, rest-space components). -/
def jetV (Jm : Matrix (Fin 3) (Fin 3) ℝ) (x : V3) : V3 := fun j => ∑ i, x i * Jm i j

noncomputable def symJ (Jm : Matrix (Fin 3) (Fin 3) ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  (1 / 2 : ℝ) • (Jm + Jmᵀ)

/-- `W_ij = ε_ijk ω_k` for the antisymmetric part `W = (J - Jᵀ)/2`. -/
noncomputable def omegaOf (Jm : Matrix (Fin 3) (Fin 3) ℝ) : V3 :=
  ![(Jm 1 2 - Jm 2 1) / 2, (Jm 2 0 - Jm 0 2) / 2, (Jm 0 1 - Jm 1 0) / 2]

theorem jet_split (Jm : Matrix (Fin 3) (Fin 3) ℝ) (x : V3) :
    jetV Jm x = symJ Jm *ᵥ x + omegaOf Jm ⨯₃ x := by
  ext j
  fin_cases j <;>
    simp [jetV, symJ, omegaOf, mulVec, dotProduct, Fin.sum_univ_three, cross_apply] <;> ring

theorem jetV_smul (Jm : Matrix (Fin 3) (Fin 3) ℝ) (a : ℝ) (x : V3) :
    jetV Jm (a • x) = a • jetV Jm x := by
  ext j
  simp only [jetV, Pi.smul_apply, smul_eq_mul, Finset.mul_sum]
  exact Finset.sum_congr rfl (fun i _ => by ring)

theorem jetV_eq_transpose_mulVec (S : Matrix (Fin 3) (Fin 3) ℝ) (x : V3) :
    jetV S x = Sᵀ *ᵥ x := by
  ext j
  simp only [jetV, mulVec, dotProduct, Matrix.transpose_apply]
  exact Finset.sum_congr rfl (fun i _ => mul_comm _ _)

theorem symJ_transpose (Jm : Matrix (Fin 3) (Fin 3) ℝ) : (symJ Jm)ᵀ = symJ Jm := by
  simp [symJ, Matrix.transpose_add, Matrix.transpose_smul, add_comm]

theorem P_add (n a b : V3) : CAS14.P n (a + b) = CAS14.P n a + CAS14.P n b := by
  simp only [CAS14.P, dotProduct_add, add_smul]
  abel

theorem P_smul (n a : V3) (c : ℝ) : CAS14.P n (c • a) = c • CAS14.P n a := by
  simp only [CAS14.P, dotProduct_smul, smul_eq_mul, smul_sub, smul_smul]

theorem P_cross_self (n ω : V3) : CAS14.P n (ω ⨯₃ n) = ω ⨯₃ n := by
  simp [CAS14.P, dot_cross_self]

theorem sub_cross_eq (a b n : V3) : (a - b) ⨯₃ n = a ⨯₃ n - b ⨯₃ n := by
  simp [map_sub, LinearMap.sub_apply]

theorem proper_motion_decomposition {D : ℝ} {n : V3} (hD : 0 < D)
    (Jm : Matrix (Fin 3) (Fin 3) ℝ) (Ω e : V3) :
    D⁻¹ • CAS14.P n (jetV Jm (D • n) + e) - Ω ⨯₃ n
      = CAS14.P n (symJ Jm *ᵥ n) + (omegaOf Jm - Ω) ⨯₃ n + D⁻¹ • CAS14.P n e := by
  have hDn : D ≠ 0 := hD.ne'
  rw [jetV_smul, P_add, P_smul, jet_split, P_add, P_cross_self, smul_add (D⁻¹), smul_smul,
    inv_mul_cancel₀ hDn, one_smul, sub_cross_eq]
  abel

theorem expansion_invisible (ℓ : ℝ) (n : V3) (hn : n ⬝ᵥ n = 1) :
    CAS14.P n (jetV (ℓ • (1 : Matrix (Fin 3) (Fin 3) ℝ)) n) = 0 ∧
      (ℓ ≠ 0 → jetV (ℓ • (1 : Matrix (Fin 3) (Fin 3) ℝ)) n ≠ jetV 0 n) := by
  have hj : jetV (ℓ • (1 : Matrix (Fin 3) (Fin 3) ℝ)) n = ℓ • n := by
    ext j
    fin_cases j <;> simp [jetV, Matrix.one_apply] <;> ring
  have hz : jetV 0 n = 0 := by ext j; simp [jetV]
  refine ⟨?_, fun hℓ => ?_⟩
  · rw [hj, CAS14.P, dotProduct_smul, hn]; simp
  · rw [hj, hz]
    intro h
    rcases smul_eq_zero.mp h with h1 | h1
    · exact hℓ h1
    · rw [h1, dotProduct_zero] at hn; exact zero_ne_one hn

theorem vorticity_frame_degeneracy (Jm : Matrix (Fin 3) (Fin 3) ℝ) (n : V3) :
    CAS14.P n (jetV Jm n) - omegaOf Jm ⨯₃ n
      = CAS14.P n (jetV (symJ Jm) n) - (0 : V3) ⨯₃ n := by
  rw [jetV_eq_transpose_mulVec (symJ Jm), symJ_transpose, jet_split Jm n, P_add, P_cross_self]
  simp [map_zero, LinearMap.zero_apply]

theorem noncomoving_unbounded (n Δv : V3) (hΔ : CAS14.P n Δv ≠ 0) (C : ℝ) :
    ∃ D > (0 : ℝ), C < (D⁻¹ • CAS14.P n Δv) ⬝ᵥ (D⁻¹ • CAS14.P n Δv) := by
  set w := CAS14.P n Δv
  have hnn : 0 ≤ w ⬝ᵥ w := Finset.sum_nonneg (fun i _ => mul_self_nonneg (w i))
  have hpos : 0 < w ⬝ᵥ w :=
    lt_of_le_of_ne hnn (fun h => hΔ (dotProduct_self_eq_zero.mp h.symm))
  have hC : 0 < |C| + 1 := by positivity
  set D := Real.sqrt ((w ⬝ᵥ w) / (|C| + 1)) with hDdef
  have hDpos : 0 < D := Real.sqrt_pos.mpr (div_pos hpos hC)
  have hD2 : D ^ 2 = (w ⬝ᵥ w) / (|C| + 1) := Real.sq_sqrt (div_pos hpos hC).le
  refine ⟨D, hDpos, ?_⟩
  have hDne : D ≠ 0 := hDpos.ne'
  have hwne : w ⬝ᵥ w ≠ 0 := hpos.ne'
  have hCne : |C| + 1 ≠ 0 := hC.ne'
  have hval : (D⁻¹ • w) ⬝ᵥ (D⁻¹ • w) = |C| + 1 := by
    rw [dotProduct_smul, smul_dotProduct, smul_eq_mul, smul_eq_mul]
    have h1 : D⁻¹ * (D⁻¹ * (w ⬝ᵥ w)) = (w ⬝ᵥ w) / D ^ 2 := by field_simp
    rw [h1, hD2]
    field_simp
  rw [hval]
  linarith [le_abs_self C]

/-- Positive control (ideal comoving observer, non-rotating frame, exact linear field):
three axis-direction drifts determine the vorticity. -/
theorem vorticity_from_axis_drifts (Jm : Matrix (Fin 3) (Fin 3) ℝ) :
    (1 / 2 : ℝ) • ∑ i : Fin 3,
        (Pi.single i 1 : V3) ⨯₃ CAS14.P (Pi.single i 1) (jetV Jm (Pi.single i 1))
      = omegaOf Jm := by
  ext k
  fin_cases k <;>
    simp [Fin.sum_univ_three, CAS14.P, jetV, omegaOf, cross_apply, dotProduct,
      Pi.single_apply] <;> ring

/-! ## T6 J correspondence to CAS-14 and the 4D→3D rest-frame bridge -/

theorem residual_eq_cas14 (Jm : Matrix (Fin 3) (Fin 3) ℝ) (x : V3) :
    jetV Jm x - symJ Jm *ᵥ x = -CAS14.W (omegaOf Jm) x := by
  rw [jet_split, add_sub_cancel_left, CAS14.W_sign, neg_neg]

theorem cas14_inverse_recovers_jet_vorticity {ι : Type*} [Fintype ι] [DecidableEq ι]
    (w : ι → ℝ) (x : ι → V3) (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i)
    (i j : ι) (hij : x i ⨯₃ x j ≠ 0) (Jm : Matrix (Fin 3) (Fin 3) ℝ) :
    (CAS14.G_equiv w x hx hw i j hij).symm
      (CAS14.b w x (fun k => jetV Jm (x k) - symJ Jm *ᵥ x k)) = omegaOf Jm := by
  have h : (fun k => jetV Jm (x k) - symJ Jm *ᵥ x k)
      = fun k => -CAS14.W (omegaOf Jm) (x k) := funext fun k => residual_eq_cas14 Jm (x k)
  rw [h]
  exact CAS14.C02_inverse_formula w x (omegaOf Jm) hx hw i j hij

theorem pd_const_mul {f : Pt → ℝ} {x : Pt} (hf : DifferentiableAt ℝ f x) (c : ℝ) (a : Fin 4) :
    pd (fun y => c * f y) x a = c * pd f x a := by
  unfold pd
  rw [fderiv_const_mul hf]
  simp

theorem covDeriv_smul {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {u : Pt → Pt} {p : Pt}
    (hu : ∀ c, DifferentiableAt ℝ (fun y => u y c) p) (c : ℝ) (X : Pt) :
    covDeriv Γ (fun y => c • u y) p X = c • covDeriv Γ u p X := by
  funext b
  simp only [covDeriv, nablaUp, Pi.smul_apply, smul_eq_mul]
  simp only [pd_const_mul (hu b) c, Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro a _
  have h : ∑ d, Γ p b a d * (c * u p d) = c * ∑ d, Γ p b a d * u p d := by
    rw [Finset.mul_sum]; exact Finset.sum_congr rfl (fun d _ => by ring)
  rw [h]
  ring

theorem J_rest_frame {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Pt}
    {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {p : Pt}
    (hg : g p = PortCas01.eta) (hu : u p = PortCas01.e0)
    (hd : FieldDiffAt g u p) (hc : MetricCompatibleAt Γ g p) (c : ℝ) (X : Pt) :
    Jchan g u Γ (fun y => c • u y) p X
      = fun b => if b = 0 then 0 else ∑ a, X a * (c * velJetMatrix Γ g u p a b) := by
  rw [Jchan, covDeriv_smul hd.2 c X, hg, hu]
  have hlow : ∀ a b, velJetMatrix Γ g u p a b = ∑ e, g p b e * nablaUp Γ u p a e := by
    intro a b
    simp only [velJetMatrix, Matrix.of_apply]
    exact velJet_eq_lower hd hc a b
  funext b
  simp only [hlow, hg]
  fin_cases b <;>
    simp [projUp, PortCas01.eta, PortCas01.e0, covDeriv, mulVec, dotProduct,
      Fin.sum_univ_four] <;> ring

/-! ## T1-W rotating-chart witness (Levi-Civita at the origin) -/

/-- Rotating chart of Minkowski space (`c = 1`, rotation rate `Ω` about the 3-axis):
`ds² = -(1-Ω²(x²+y²))dt² + 2Ω(x dy - y dx)dt + dx² + dy² + dz²`. -/
def grot (Ω : ℝ) (y : Pt) : Matrix (Fin 4) (Fin 4) ℝ :=
  !![-1 + Ω ^ 2 * (y 1 ^ 2 + y 2 ^ 2), -(Ω * y 2), Ω * y 1, 0;
     -(Ω * y 2), 1, 0, 0;
     Ω * y 1, 0, 1, 0;
     0, 0, 0, 1]

/-- Inertial (non-rotating, non-expanding) observers expressed in the rotating chart. -/
def urot (Ω : ℝ) (y : Pt) : Pt := ![1, Ω * y 2, -(Ω * y 1), 0]

/-- Levi-Civita symbols `Γ^c_{ad}` of `grot Ω` at the origin, held constant in the chart
(only the value at the origin is used). -/
def Γrot (Ω : ℝ) (_ : Pt) (c a d : Fin 4) : ℝ :=
  if c = 1 ∧ ((a = 0 ∧ d = 2) ∨ (a = 2 ∧ d = 0)) then -Ω
  else if c = 2 ∧ ((a = 0 ∧ d = 1) ∨ (a = 1 ∧ d = 0)) then Ω else 0

theorem pd_const (k : ℝ) (x : Pt) (a : Fin 4) : pd (fun _ => k) x a = 0 := by
  simp [pd]

theorem pd_lin (k : ℝ) (i : Fin 4) (x : Pt) (a : Fin 4) :
    pd (fun y => k * y i) x a = k * (Pi.single a (1 : ℝ) : Pt) i := by
  unfold pd
  rw [((hasFDerivAt_apply (𝕜 := ℝ) i x).const_mul k).fderiv]
  simp

theorem pd_neg_lin (k : ℝ) (i : Fin 4) (x : Pt) (a : Fin 4) :
    pd (fun y => -(k * y i)) x a = -(k * (Pi.single a (1 : ℝ) : Pt) i) := by
  unfold pd
  have h : HasFDerivAt (fun y : Pt => -(k * y i)) _ x :=
    ((hasFDerivAt_apply (𝕜 := ℝ) i x).const_mul k).neg
  rw [h.fderiv]
  simp

theorem pd_quad_origin (Ω : ℝ) (a : Fin 4) :
    pd (fun y : Pt => -1 + Ω ^ 2 * (y 1 ^ 2 + y 2 ^ 2)) 0 a = 0 := by
  unfold pd
  have h1 := (hasFDerivAt_apply (𝕜 := ℝ) (1 : Fin 4) (0 : Pt)).pow 2
  have h2 := (hasFDerivAt_apply (𝕜 := ℝ) (2 : Fin 4) (0 : Pt)).pow 2
  have h : HasFDerivAt (fun y : Pt => -1 + Ω ^ 2 * (y 1 ^ 2 + y 2 ^ 2)) _ 0 :=
    ((h1.add h2).const_mul (Ω ^ 2)).const_add (-1)
  rw [h.fderiv]
  simp

theorem rotating_chart_witness (Ω : ℝ) (hΩ : Ω ≠ 0) :
    MetricCompatibleAt (Γrot Ω) (grot Ω) 0 ∧ (∀ c a d, Γrot Ω 0 c a d = Γrot Ω 0 c d a) ∧
    (∀ y, urot Ω y ⬝ᵥ (grot Ω y *ᵥ urot Ω y) = -1) ∧ FieldDiffAt (grot Ω) (urot Ω) 0 ∧
    (∀ X, covDeriv (Γrot Ω) (urot Ω) 0 X = 0) ∧
    coordDeriv (urot Ω) 0 (Pi.single 1 1) = ![0, 0, -Ω, 0] ∧
    coordDeriv (urot Ω) 0 (Pi.single 1 1) ≠ 0 := by
  have hcoord : coordDeriv (urot Ω) 0 (Pi.single 1 1) = ![0, 0, -Ω, 0] := by
    funext c
    fin_cases c <;>
      simp [coordDeriv, urot, pd_lin, pd_neg_lin, pd_const, Pi.single_apply]
  refine ⟨?_, ?_, ?_, ?_, ?_, hcoord, ?_⟩
  · intro a b c
    fin_cases a <;> fin_cases b <;> fin_cases c <;>
      simp [grot, Γrot, Fin.sum_univ_four, pd_lin, pd_neg_lin, pd_const, pd_quad_origin]
  · intro c a d
    fin_cases c <;> fin_cases a <;> fin_cases d <;> simp [Γrot]
  · intro y
    simp [urot, grot, dotProduct, mulVec, Fin.sum_univ_four]
    ring
  · refine ⟨fun b c => ?_, fun c => ?_⟩
    · fin_cases b <;> fin_cases c <;> simp [grot] <;> fun_prop
    · fin_cases c <;> simp [urot] <;> fun_prop
  · intro X
    funext c
    fin_cases c <;>
      simp [covDeriv, nablaUp, urot, Γrot, Fin.sum_univ_four, pd_lin, pd_neg_lin, pd_const,
        Pi.single_apply]
  · rw [hcoord]
    intro h
    have h2 := congrFun h 2
    simp at h2
    exact hΩ h2

/-! ## T7 typed calibration contract (G17-D OperationalWitness pattern) -/

inductive SupplyStatus
  | supplied
  | notSupplied
  deriving DecidableEq

/-- Supply ledger for every external input of the channel. -/
structure G14ASupplyLedger where
  sourceIdentification : SupplyStatus
  transportRule : SupplyStatus
  tangentDirections : SupplyStatus
  baselineLength : SupplyStatus
  clockCalibration : SupplyStatus
  lengthCalibration : SupplyStatus
  nonrotatingFrame : SupplyStatus
  opticalSymmetricRate : SupplyStatus
  finiteBaselineRemainder : SupplyStatus

/-- Actual status for this run (recorded operational data, NOT a theorem): no actual
source identification, transport, tangent, baseline, clock, length, frame, optical-rate or
remainder witness has been supplied. -/
def g14aSupplyLedger : G14ASupplyLedger :=
  ⟨.notSupplied, .notSupplied, .notSupplied, .notSupplied, .notSupplied, .notSupplied,
    .notSupplied, .notSupplied, .notSupplied⟩

/-- The mathematical hypotheses an actual calibrated application must discharge. -/
structure CalibratedDerivativeChannel (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Pt)
    (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (U : Pt → Pt) (p X : Pt) where
  Tr : ℝ → Op
  q : ℝ → Pt
  germ : TransportGerm Γ p X Tr
  q0 : q 0 = p
  qd : HasDerivAt q X 0
  reg : ∀ c, DifferentiableAt ℝ (fun y => U y c) p

theorem CalibratedDerivativeChannel.tendsto_J {g : Pt → Matrix (Fin 4) (Fin 4) ℝ}
    {u : Pt → Pt} {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {U : Pt → Pt} {p X : Pt}
    (ch : CalibratedDerivativeChannel g u Γ U p X) :
    Tendsto (finiteBaselineMap g u ch.Tr U ch.q p) (𝓝[≠] 0) (𝓝 (Jchan g u Γ U p X)) :=
  finiteBaseline_tendsto_J ch.germ ch.q0 ch.qd ch.reg

theorem gammaMat_Γ0 (p X : Pt) : gammaMat Γ0 p X = 0 := by
  ext c d
  simp [gammaMat, Γ0]

theorem gammaOp_Γ0 (p X : Pt) : gammaOp Γ0 p X = 0 := by
  ext v i
  simp [gammaOp_apply, gammaMat_Γ0]

/-- Synthetic consistency witness only (Minkowski, Cartesian chart, explicit field): the
hypothesis bundle is satisfiable.  It is not a supplied observation. -/
theorem channel_nonvacuous (c : ℝ) :
    Nonempty (CalibratedDerivativeChannel gMink uEx Γ0 (fun y => c • uEx y) 0
      (Pi.single 1 1)) := by
  refine ⟨⟨fun _ => 1, fun s => s • (Pi.single 1 1 : Pt), ⟨rfl, ?_⟩, by simp, ?_, ?_⟩⟩
  · rw [gammaOp_Γ0, neg_zero]
    exact hasDerivAt_const _ _
  · simpa using (hasDerivAt_id (0 : ℝ)).smul_const (Pi.single 1 1 : Pt)
  · intro i
    have := (PORTCAS03VelocityJetDecomposition.uEx_diff 0).2 i
    simpa [Pi.smul_apply, smul_eq_mul] using this.const_mul c

/-! ## T8 zeroth-order / static data negative control -/

theorem uRest_diff (x : Pt) : FieldDiffAt gMink uRest x :=
  ⟨fun b c => by simp [gMink], fun c => by simp [uRest]⟩

theorem zeroth_order_insufficient (c : ℝ) :
    (c • uRest 0 = c • uEx 0) ∧
    Jchan gMink uRest Γ0 (fun y => c • uRest y) 0 (Pi.single 1 1) = 0 ∧
    Jchan gMink uEx Γ0 (fun y => c • uEx y) 0 (Pi.single 1 1) = ![0, 3 * c, 0, 0] := by
  refine ⟨?_, ?_, ?_⟩
  · rw [PORTCAS03VelocityJetDecomposition.uEx_zero]; rfl
  · rw [J_rest_frame (g := gMink) (u := uRest) (Γ := Γ0) (p := 0) rfl rfl (uRest_diff 0)
      (PORTCAS03VelocityJetDecomposition.mink_compatible 0) c,
      PORTCAS03VelocityJetDecomposition.uRest_jet_zero]
    funext b
    simp
  · rw [J_rest_frame (g := gMink) (u := uEx) (Γ := Γ0) (p := 0) rfl
      PORTCAS03VelocityJetDecomposition.uEx_zero (PORTCAS03VelocityJetDecomposition.uEx_diff 0)
      (PORTCAS03VelocityJetDecomposition.mink_compatible 0) c,
      PORTCAS03VelocityJetDecomposition.uEx_jet_zero]
    funext b
    fin_cases b <;> simp [Dex, Pi.single_apply] <;> ring

/-- Any observation functional of the zeroth-order data (event and source velocity there),
in particular a single static snapshot, takes equal values on two fields whose `J` differ. -/
theorem zeroth_order_functional_insufficient {α : Type*} (Obs : Pt → Pt → α) (c : ℝ)
    (hc : c ≠ 0) :
    Obs 0 (c • uRest 0) = Obs 0 (c • uEx 0) ∧
    Jchan gMink uRest Γ0 (fun y => c • uRest y) 0 (Pi.single 1 1)
      ≠ Jchan gMink uEx Γ0 (fun y => c • uEx y) 0 (Pi.single 1 1) := by
  obtain ⟨h1, h2, h3⟩ := zeroth_order_insufficient c
  refine ⟨by rw [h1], ?_⟩
  rw [h2, h3]
  intro h
  have h1' : (![0, 3 * c, 0, 0] : Pt) 1 = 0 := by rw [← h]; rfl
  simp at h1'
  exact hc h1'

end G14A
