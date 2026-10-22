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

/-- `P_{q_s → p} U(q_s)`: the velocity at `q_s` transported back to `p`, where `Π s` is the
forward transport `T_p → T_{q_s}` in coordinate components. -/
noncomputable def transportBack (Π : ℝ → Op) (U : Pt → Pt) (q : ℝ → Pt) (s : ℝ) : Pt :=
  Ring.inverse (Π s) (U (q s))

/-- The declared finite-baseline map of Eq. (A1): `h_p [P_{q_s→p} U(q_s) - U(p)] / s`. -/
noncomputable def finiteBaselineMap (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Pt)
    (Π : ℝ → Op) (U : Pt → Pt) (q : ℝ → Pt) (p : Pt) (s : ℝ) : Pt :=
  projUp (g p) (u p) *ᵥ (s⁻¹ • (transportBack Π U q s - U p))

/-- Transport rule input: the parallel-transport equation `dΠ/ds = -Γ(q̇, ·) Π` at `s = 0`,
with `Π 0 = 1` and `q̇ 0 = X`. -/
structure TransportGerm (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (p X : Pt) (Π : ℝ → Op) :
    Prop where
  base : Π 0 = 1
  deriv : HasDerivAt Π (-(gammaOp Γ p X)) 0

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
  rw [← ContinuousLinearMap.mul_apply, Units.mul_inv, ContinuousLinearMap.one_apply]

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
  have h := hI.clm_apply hV
  convert h using 1
  simp only [Function.comp_def, hq0, hE0, Ring.inverse_unit,
    ContinuousLinearMap.neg_apply, ContinuousLinearMap.mulLeftRight_apply,
    ContinuousLinearMap.mul_apply, spinOf, ContinuousLinearMap.add_apply, unit_apply_inv,
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
    {p X : Pt} {Π : ℝ → Op} {q : ℝ → Pt}
    (hΠ : TransportGerm Γ p X Π) (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    HasDerivAt (transportBack Π U q) (covDeriv Γ U p X) 0 := by
  have hb : Π 0 = ((1 : Opˣ) : Op) := by rw [Units.val_one]; exact hΠ.base
  have h := frame_components_hasDerivAt (Γ := Γ) (E0 := 1) hb hΠ.deriv hq0 hq hU
  have hs : spinOf 1 (-(gammaOp Γ p X)) Γ p X = 0 :=
    spinOf_parallel (Γ := Γ) 1 (by simp)
  rw [hs] at h
  simpa [transportBack] using h

theorem finiteBaseline_tendsto_J {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Pt}
    {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ} {U : Pt → Pt} {p X : Pt} {Π : ℝ → Op}
    {q : ℝ → Pt}
    (hΠ : TransportGerm Γ p X Π) (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    Tendsto (finiteBaselineMap g u Π U q p) (𝓝[≠] 0) (𝓝 (Jchan g u Γ U p X)) := by
  have hd := transportBack_hasDerivAt hΠ hq0 hq hU
  have hs := hasDerivAt_iff_tendsto_slope.mp hd
  have h0 : transportBack Π U q 0 = U p := by
    simp [transportBack, hΠ.base, hq0]
  have hcont : Continuous fun v : Pt => projUp (g p) (u p) *ᵥ v :=
    Continuous.matrix_mulVec continuous_const continuous_id
  have hT := (hcont.tendsto _).comp hs
  refine hT.congr' (Eventually.of_forall fun s => ?_)
  simp [finiteBaselineMap, slope_def_module, h0]

/-- Negative control: without transport (`Π ≡ 1`) the quotient converges to the coordinate
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
    have := (hf t ht).sub ((hasDerivWithinAt_id (s := Icc 0 s) (x := t)).smul_const (f' 0))
    simpa using this
  have hb : ∀ t ∈ Ico 0 s, ‖f' t - f' 0‖ ≤ M * s := fun t ht =>
    (hlip t ht).trans (mul_le_mul_of_nonneg_left ht.2.le hM)
  have key := norm_image_sub_le_of_norm_deriv_le_segment' hφ hb s ⟨hs.le, le_rfl⟩
  have hrw : s⁻¹ • (f s - f 0) - f' 0 = s⁻¹ • (φ s - φ 0) := by
    simp only [hφdef, zero_smul, sub_zero]
    rw [smul_sub (s⁻¹) (f s - s • f' 0), smul_sub (s⁻¹) (f s), smul_smul,
      inv_mul_cancel₀ hs.ne', one_smul]
    abel
  rw [hrw, norm_smul, Real.norm_eq_abs, abs_inv, abs_of_pos hs]
  calc s⁻¹ * ‖φ s - φ 0‖ ≤ s⁻¹ * (M * s * (s - 0)) :=
        mul_le_mul_of_nonneg_left key (inv_nonneg.mpr hs.le)
    _ = M * s := by field_simp

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
    HasDerivAt.sum (fun i _ => (hc i).mul (hc i))
  convert hs using 1
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
  convert h4 using 1
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
  have h := hR.clm_apply (direction_hasDerivAt hD hn hr0 hr)
  convert h using 1
  rw [hR0, hr0, dirOf_base hD hn]
  simp [crossOp]
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

theorem proper_motion_decomposition {D : ℝ} {n : V3} (hD : 0 < D) (hn : n ⬝ᵥ n = 1)
    (Jm : Matrix (Fin 3) (Fin 3) ℝ) (Ω e : V3) :
    D⁻¹ • CAS14.P n (jetV Jm (D • n) + e) - Ω ⨯₃ n
      = CAS14.P n (symJ Jm *ᵥ n) + (omegaOf Jm - Ω) ⨯₃ n + D⁻¹ • CAS14.P n e := by
  have hDn : D ≠ 0 := hD.ne'
  ext k
  fin_cases k <;>
    simp [CAS14.P, jetV, symJ, omegaOf, mulVec, dotProduct, Fin.sum_univ_three,
      cross_apply] <;> field_simp <;> ring

theorem expansion_invisible (ℓ : ℝ) (n : V3) (hn : n ⬝ᵥ n = 1) :
    CAS14.P n (jetV (ℓ • (1 : Matrix (Fin 3) (Fin 3) ℝ)) n) = 0 ∧
      (ℓ ≠ 0 → jetV (ℓ • (1 : Matrix (Fin 3) (Fin 3) ℝ)) n ≠ jetV 0 n) := by
  have hj : jetV (ℓ • (1 : Matrix (Fin 3) (Fin 3) ℝ)) n = ℓ • n := by
    ext j
    fin_cases j <;> simp [jetV, Fin.sum_univ_three, Matrix.one_apply]
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
  ext k
  fin_cases k <;>
    simp [CAS14.P, jetV, symJ, omegaOf, dotProduct, Fin.sum_univ_three, cross_apply] <;> ring

theorem noncomoving_unbounded (n Δv : V3) (hΔ : CAS14.P n Δv ≠ 0) (C : ℝ) :
    ∃ D > 0, C < (D⁻¹ • CAS14.P n Δv) ⬝ᵥ (D⁻¹ • CAS14.P n Δv) := by
  set w := CAS14.P n Δv
  have hnn : 0 ≤ w ⬝ᵥ w := Finset.sum_nonneg (fun i _ => mul_self_nonneg (w i))
  have hpos : 0 < w ⬝ᵥ w :=
    lt_of_le_of_ne hnn (fun h => hΔ (dotProduct_self_eq_zero.mp h.symm))
  have hC : 0 < |C| + 1 := by positivity
  refine ⟨Real.sqrt ((w ⬝ᵥ w) / (|C| + 1)), Real.sqrt_pos.mpr (div_pos hpos hC), ?_⟩
  have hsq : Real.sqrt ((w ⬝ᵥ w) / (|C| + 1)) ^ 2 = (w ⬝ᵥ w) / (|C| + 1) :=
    Real.sq_sqrt (div_pos hpos hC).le
  rw [dotProduct_smul, smul_dotProduct, smul_eq_mul, smul_eq_mul, ← mul_assoc,
    ← mul_inv, ← pow_two, hsq, inv_div, div_mul_cancel₀ _ hpos.ne']
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
  rw [Finset.mul_sum]
  ring_nf
  simp only [Finset.mul_sum, Finset.sum_mul]
  apply congrArg₂ (· + ·) rfl
  apply Finset.sum_congr rfl
  intro d _
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
      vecMulVec_apply, Fin.sum_univ_four] <;> ring

end G14A
