import Mathlib
import G08AWhitening
import P08EllipsoidFiber

/-!
P08-B (PORT-CAS-08): ellipsoid quotient image and bounded-fibre support.

Setting (exact algebra, Euclidean dot product `⬝ᵥ`, no numerical rank rule):
* original bounded ellipsoid `K = {c + L z | z ⬝ᵥ z ≤ 1}` with an arbitrary real factor
  `L : Fin n × Fin r` (the `factor` of `htt/src/common/typefree_fibers.py::_psd_factor`);
* observation `B : Fin m × Fin n`, observed value `y`, target operator `P : Fin q × Fin n`;
* `A = B * L`, `b = y - B c`, `X` any Moore–Penrose inverse of `A`
  (`G08AWhitening.IsMoorePenrose`), `z0 = X b`, `η = z0 ⬝ᵥ z0`;
* `N : Fin r × Fin d` an orthonormal parametrisation of `ker A`
  (`Nᵀ N = 1`, `ker A = range N`).

Proved:
* Q1  `P '' (K ∩ {B x = y}) = {P (c + L z0) + √(1-η) • (P L N) u | u ⬝ᵥ u ≤ 1}` for `η < 1`
  (and Q1' for `η ≤ 1`), two-sided set equality over the whole original ellipsoid;
* Q2  basis invariance: any two orthonormal kernel parametrisations (any widths) give the same
  set; `N ↦ N R` with `Rᵀ R = 1` preserves the hypotheses and the set;
* Q3  boundary return: `η = 1` gives the single point `P (c + L z0)` (consistent with Q1' at
  radius `√0 = 0`), `η > 1` and incompatible support give `∅` (distinct causes);
* Q4  an orthonormal kernel parametrisation exists for every real matrix;
* Q5  support function `h(w) = w ⬝ᵥ θ0 + s √((Fᵀ w) ⬝ᵥ (Fᵀ w))` (bound and attainment), and
  `η` is the squared quotient gauge: the fibre image is nonempty iff the support is compatible
  and `η ≤ 1`.

No numerical SVD link, physical units, full PORT-CAS-08, or scientific admission is asserted.
-/

noncomputable section

namespace P08EllipsoidImage

open Matrix

variable {n r m q d d' : ℕ}

/-! ### Definitions -/

/-- Original bounded ellipsoid `c + L · (closed unit ball)`. -/
def Ell (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ) : Set (Fin n → ℝ) :=
  {x | ∃ z : Fin r → ℝ, z ⬝ᵥ z ≤ 1 ∧ x = c + L *ᵥ z}

/-- Image under the target operator `P` of the ellipsoid slice `K ∩ {B x = y}`. -/
def FibreImage (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ) (B : Matrix (Fin m) (Fin n) ℝ)
    (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ) : Set (Fin q → ℝ) :=
  (fun x => P *ᵥ x) '' (Ell c L ∩ {x | B *ᵥ x = y})

/-- `N` has orthonormal columns spanning exactly `ker A`. -/
def IsKerONB (A : Matrix (Fin m) (Fin r) ℝ) (N : Matrix (Fin r) (Fin d) ℝ) : Prop :=
  Nᵀ * N = 1 ∧ ∀ k, A *ᵥ k = 0 ↔ ∃ u, k = N *ᵥ u

/-- Image of the closed unit ball under `u ↦ θ0 + s • F u`. -/
def EllImage (θ0 : Fin q → ℝ) (s : ℝ) (F : Matrix (Fin q) (Fin d) ℝ) : Set (Fin q → ℝ) :=
  {θ | ∃ u : Fin d → ℝ, u ⬝ᵥ u ≤ 1 ∧ θ = θ0 + s • (F *ᵥ u)}

/-! ### Reduction to the latent fibre of P08-A -/

theorem fibreImage_eq_latent (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ) :
    FibreImage c L B P y =
      (fun z => P *ᵥ (c + L *ᵥ z)) '' P08EllipsoidFiber.Fib (B * L) (y - B *ᵥ c) := by
  ext θ
  simp only [FibreImage, Ell, P08EllipsoidFiber.Fib, Set.mem_image, Set.mem_inter_iff,
    Set.mem_setOf_eq]
  constructor
  · rintro ⟨x, ⟨⟨z, hz, rfl⟩, hB⟩, rfl⟩
    refine ⟨z, ⟨?_, hz⟩, rfl⟩
    rw [← mulVec_mulVec, ← hB, mulVec_add]
    abel
  · rintro ⟨z, ⟨hA, hz⟩, rfl⟩
    refine ⟨c + L *ᵥ z, ⟨⟨z, hz, rfl⟩, ?_⟩, rfl⟩
    rw [mulVec_add, mulVec_mulVec, hA]
    abel

/-! ### Orthonormal parametrisation of the kernel ball -/

theorem dot_mulVec_ONB (N : Matrix (Fin r) (Fin d) ℝ) (hN : Nᵀ * N = 1) (u : Fin d → ℝ) :
    (N *ᵥ u) ⬝ᵥ (N *ᵥ u) = u ⬝ᵥ u := by
  rw [dotProduct_mulVec, ← mulVec_transpose, mulVec_mulVec, hN, one_mulVec]

/-- Two-sided: `{k ∈ ker A | k ⬝ᵥ k ≤ s} = {√s • N u | u ⬝ᵥ u ≤ 1}` for `s ≥ 0`. -/
theorem kernel_ball_param (A : Matrix (Fin m) (Fin r) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hN : IsKerONB A N) (s : ℝ) (hs : 0 ≤ s) (k : Fin r → ℝ) :
    (A *ᵥ k = 0 ∧ k ⬝ᵥ k ≤ s) ↔ ∃ u, u ⬝ᵥ u ≤ 1 ∧ k = Real.sqrt s • (N *ᵥ u) := by
  constructor
  · rintro ⟨hk, hks⟩
    obtain ⟨v, rfl⟩ := (hN.2 k).mp hk
    rw [dot_mulVec_ONB N hN.1] at hks
    rcases hs.eq_or_lt with h0 | hpos
    · subst h0
      have hv : v = 0 :=
        P08EllipsoidFiber.dot_self_eq_zero v (le_antisymm hks (P08EllipsoidFiber.dot_self_nonneg v))
      refine ⟨0, by simp, ?_⟩
      simp [hv]
    · have hsq : 0 < Real.sqrt s := Real.sqrt_pos.mpr hpos
      refine ⟨(Real.sqrt s)⁻¹ • v, ?_, ?_⟩
      · rw [smul_dotProduct, dotProduct_smul, smul_eq_mul, smul_eq_mul, ← mul_assoc, ← mul_inv,
          Real.mul_self_sqrt hs, inv_mul_le_iff₀ hpos]
        linarith
      · rw [mulVec_smul, smul_smul, mul_inv_cancel₀ hsq.ne', one_smul]
  · rintro ⟨u, hu, rfl⟩
    refine ⟨?_, ?_⟩
    · rw [mulVec_smul, (hN.2 _).mpr ⟨u, rfl⟩, smul_zero]
    · rw [smul_dotProduct, dotProduct_smul, dot_mulVec_ONB N hN.1, smul_eq_mul, smul_eq_mul,
        ← mul_assoc, Real.mul_self_sqrt hs]
      nlinarith

/-! ### Q1 / Q1': the residual image -/

/-- Q1' (closed form up to and including the boundary `η = 1`). -/
theorem fibreImage_eq_of_le (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) (hN : IsKerONB (B * L) N)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1) :
    FibreImage c L B P y =
      EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
        (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N) := by
  rw [fibreImage_eq_latent, P08EllipsoidFiber.fiber_eq_kernel_ball (B * L) X _ hX hcomp]
  have hs : 0 ≤ 1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) := by linarith
  ext θ
  simp only [EllImage, Set.mem_image, Set.mem_setOf_eq]
  constructor
  · rintro ⟨z, ⟨k, hk, hkn, rfl⟩, rfl⟩
    obtain ⟨u, hu, rfl⟩ := (kernel_ball_param (B * L) N hN _ hs k).mp ⟨hk, hkn⟩
    refine ⟨u, hu, ?_⟩
    simp only [mulVec_add, mulVec_smul, ← mulVec_mulVec]
    abel
  · rintro ⟨u, hu, rfl⟩
    obtain ⟨hk, hkn⟩ := (kernel_ball_param (B * L) N hN _ hs _).mpr ⟨u, hu, rfl⟩
    refine ⟨X *ᵥ (y - B *ᵥ c) + Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c))) •
      (N *ᵥ u), ⟨_, hk, hkn, rfl⟩, ?_⟩
    simp only [mulVec_add, mulVec_smul, ← mulVec_mulVec]
    abel

/-- Q1 (interior `η < 1`): the residual image is the image of the unit ball under
`√(1-η) · P L N`, centred at `P (c + L z0)`. -/
theorem fibreImage_eq (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) (hN : IsKerONB (B * L) N)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) < 1) :
    FibreImage c L B P y =
      EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
        (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N) :=
  fibreImage_eq_of_le c L B P y X N hX hcomp hN hη.le

/-! ### Q2: basis invariance -/

/-- Q2a: any two orthonormal kernel parametrisations (of any widths) give the same image. -/
theorem basis_invariance (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (N' : Matrix (Fin r) (Fin d') ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) (hN : IsKerONB (B * L) N)
    (hN' : IsKerONB (B * L) N')
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1) :
    EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
        (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N) =
      EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
        (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N') :=
  (fibreImage_eq_of_le c L B P y X N hX hcomp hN hη).symm.trans
    (fibreImage_eq_of_le c L B P y X N' hX hcomp hN' hη)

/-- Q2b (hypothesis side): an orthogonal change of kernel basis is again admissible. -/
theorem isKerONB_mul_orthogonal (A : Matrix (Fin m) (Fin r) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (R : Matrix (Fin d) (Fin d) ℝ) (hN : IsKerONB A N) (hR : Rᵀ * R = 1) :
    IsKerONB A (N * R) := by
  have hR' : R * Rᵀ = 1 := mul_eq_one_comm.mp hR
  refine ⟨?_, ?_⟩
  · rw [transpose_mul, Matrix.mul_assoc, ← Matrix.mul_assoc Nᵀ, hN.1, Matrix.one_mul, hR]
  · intro k
    rw [hN.2 k]
    constructor
    · rintro ⟨u, rfl⟩
      exact ⟨Rᵀ *ᵥ u, by rw [mulVec_mulVec, Matrix.mul_assoc, hR', Matrix.mul_one]⟩
    · rintro ⟨u, rfl⟩
      exact ⟨R *ᵥ u, by rw [mulVec_mulVec]⟩

/-- Q2b (set side): the unit-ball image is invariant under `F ↦ F R`, `Rᵀ R = 1`. -/
theorem ellImage_mul_orthogonal (θ0 : Fin q → ℝ) (s : ℝ) (F : Matrix (Fin q) (Fin d) ℝ)
    (R : Matrix (Fin d) (Fin d) ℝ) (hR : Rᵀ * R = 1) :
    EllImage θ0 s (F * R) = EllImage θ0 s F := by
  have hR' : R * Rᵀ = 1 := mul_eq_one_comm.mp hR
  ext θ
  simp only [EllImage, Set.mem_setOf_eq]
  constructor
  · rintro ⟨u, hu, rfl⟩
    exact ⟨R *ᵥ u, by rwa [dot_mulVec_ONB R hR], by rw [mulVec_mulVec]⟩
  · rintro ⟨u, hu, rfl⟩
    refine ⟨Rᵀ *ᵥ u, ?_, ?_⟩
    · rwa [dot_mulVec_ONB Rᵀ (by rw [transpose_transpose]; exact hR')]
    · rw [mulVec_mulVec, Matrix.mul_assoc, hR', Matrix.mul_one]

/-! ### Q3: boundary return -/

/-- Radius zero collapses the image to its centre. -/
theorem ellImage_zero (θ0 : Fin q → ℝ) (F : Matrix (Fin q) (Fin d) ℝ) :
    EllImage θ0 0 F = {θ0} := by
  ext θ
  simp only [EllImage, Set.mem_setOf_eq, Set.mem_singleton_iff, zero_smul, add_zero]
  constructor
  · rintro ⟨u, -, rfl⟩
    rfl
  · rintro rfl
    exact ⟨0, by simp, rfl⟩

/-- Q3, `η = 1`: the single point `P (c + L z0)` (proved from the P08-A singleton branch). -/
theorem boundary_eq_one (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) = 1) :
    FibreImage c L B P y = {P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c)))} := by
  have h := (P08EllipsoidFiber.fiber_branches (B * L) X _ hX hcomp).2.1 hη
  rw [fibreImage_eq_latent,
    show P08EllipsoidFiber.Fib (B * L) (y - B *ᵥ c) = {X *ᵥ (y - B *ᵥ c)} from h,
    Set.image_singleton]

/-- Q3 consistency: at `η = 1` the Q1' closed form returns the same single point. -/
theorem boundary_consistent (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) = 1) :
    EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
        (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N) =
      {P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c)))} := by
  rw [hη, sub_self, Real.sqrt_zero, ellImage_zero]

/-- Q3, `η > 1`: empty (norm cause). -/
theorem boundary_gt_one (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c)
    (hη : 1 < (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c))) :
    FibreImage c L B P y = ∅ := by
  have h := (P08EllipsoidFiber.fiber_branches (B * L) X _ hX hcomp).1 hη
  rw [fibreImage_eq_latent,
    show P08EllipsoidFiber.Fib (B * L) (y - B *ᵥ c) = ∅ from h, Set.image_empty]

/-- Q3, incompatible support: empty (support cause, no Moore–Penrose data needed). -/
theorem incompatible_empty (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (hinc : ¬ ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) :
    FibreImage c L B P y = ∅ := by
  have h := P08EllipsoidFiber.incompatible_empty (B * L) (y - B *ᵥ c) hinc
  rw [fibreImage_eq_latent,
    show P08EllipsoidFiber.Fib (B * L) (y - B *ᵥ c) = ∅ from h, Set.image_empty]

/-! ### Q4: existence of an orthonormal kernel parametrisation -/

/-- `ker A` transported to Euclidean space (same underlying vectors). -/
def kerE (A : Matrix (Fin m) (Fin r) ℝ) : Submodule ℝ (EuclideanSpace ℝ (Fin r)) :=
  Submodule.comap (WithLp.linearEquiv 2 ℝ (Fin r → ℝ)).toLinearMap (LinearMap.ker A.mulVecLin)

theorem mem_kerE (A : Matrix (Fin m) (Fin r) ℝ) (x : EuclideanSpace ℝ (Fin r)) :
    x ∈ kerE A ↔ A *ᵥ WithLp.ofLp x = 0 := by
  simp [kerE, Submodule.mem_comap, LinearMap.mem_ker]

/-- Columns: the standard orthonormal basis of `kerE A`, read back as plain vectors. -/
def kerN (A : Matrix (Fin m) (Fin r) ℝ) :
    Matrix (Fin r) (Fin (Module.finrank ℝ (kerE A))) ℝ :=
  fun i j => WithLp.ofLp ((stdOrthonormalBasis ℝ (kerE A) j : kerE A) : EuclideanSpace ℝ (Fin r)) i

theorem kerN_mulVec (A : Matrix (Fin m) (Fin r) ℝ)
    (u : Fin (Module.finrank ℝ (kerE A)) → ℝ) :
    kerN A *ᵥ u = WithLp.ofLp
      ((∑ j, u j • stdOrthonormalBasis ℝ (kerE A) j : kerE A) : EuclideanSpace ℝ (Fin r)) := by
  funext l
  rw [Submodule.coe_sum, WithLp.ofLp_sum, Finset.sum_apply]
  simp only [mulVec, dotProduct, kerN, Submodule.coe_smul, WithLp.ofLp_smul, Pi.smul_apply,
    smul_eq_mul]
  exact Finset.sum_congr rfl fun j _ => mul_comm _ _

theorem kerN_orthonormal (A : Matrix (Fin m) (Fin r) ℝ) : (kerN A)ᵀ * kerN A = 1 := by
  ext i j
  have h := orthonormal_iff_ite.mp (stdOrthonormalBasis ℝ (kerE A)).orthonormal i j
  rw [Submodule.coe_inner, EuclideanSpace.inner_eq_star_dotProduct] at h
  rw [Matrix.mul_apply, Matrix.one_apply, ← h]
  simp only [transpose_apply, kerN, dotProduct, Pi.star_apply, star_trivial]
  exact Finset.sum_congr rfl fun k _ => mul_comm _ _

theorem kerN_range (A : Matrix (Fin m) (Fin r) ℝ) (k : Fin r → ℝ) :
    A *ᵥ k = 0 ↔ ∃ u, k = kerN A *ᵥ u := by
  constructor
  · intro hk
    have hx : WithLp.toLp 2 k ∈ kerE A := (mem_kerE A _).mpr hk
    refine ⟨fun i => inner ℝ (stdOrthonormalBasis ℝ (kerE A) i) ⟨WithLp.toLp 2 k, hx⟩, ?_⟩
    rw [kerN_mulVec, (stdOrthonormalBasis ℝ (kerE A)).sum_repr' ⟨WithLp.toLp 2 k, hx⟩]
  · rintro ⟨u, rfl⟩
    rw [kerN_mulVec]
    exact (mem_kerE A _).mp (∑ j, u j • stdOrthonormalBasis ℝ (kerE A) j : kerE A).2

/-- Q4: every real matrix admits an orthonormal parametrisation of its kernel. -/
theorem exists_kerONB (A : Matrix (Fin m) (Fin r) ℝ) :
    ∃ d, ∃ N : Matrix (Fin r) (Fin d) ℝ, IsKerONB A N :=
  ⟨_, kerN A, kerN_orthonormal A, kerN_range A⟩

/-- Q4 corollary: with `X` from `G08AWhitening.moorePenrose_exists` and `N` from
`exists_kerONB`, the Q1 identity is realised for all data with compatible support and `η < 1`. -/
theorem fibreImage_exists_param (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) :
    ∃ X : Matrix (Fin r) (Fin m) ℝ, G08AWhitening.IsMoorePenrose (B * L) X ∧
      ∃ d, ∃ N : Matrix (Fin r) (Fin d) ℝ, IsKerONB (B * L) N ∧
        ((X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) < 1 →
          FibreImage c L B P y =
            EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
              (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N)) := by
  obtain ⟨X, hX⟩ := G08AWhitening.moorePenrose_exists (B * L)
  obtain ⟨d, N, hN⟩ := exists_kerONB (B * L)
  exact ⟨X, hX, d, N, hN, fun hη => fibreImage_eq c L B P y X N hX hcomp hN hη⟩

/-! ### Q5: support function and quotient gauge -/

/-- Cauchy–Schwarz for the real dot product, squared form. -/
theorem dot_sq_le (a u : Fin d → ℝ) : (a ⬝ᵥ u) ^ 2 ≤ (a ⬝ᵥ a) * (u ⬝ᵥ u) := by
  have h := Finset.sum_mul_sq_le_sq_mul_sq Finset.univ a u
  simpa [dotProduct, pow_two] using h

/-- Q5a: support function of the residual image, bound and attainment. -/
theorem support_function (θ0 : Fin q → ℝ) (s : ℝ) (hs : 0 ≤ s) (F : Matrix (Fin q) (Fin d) ℝ)
    (w : Fin q → ℝ) :
    (∀ θ ∈ EllImage θ0 s F,
        w ⬝ᵥ θ ≤ w ⬝ᵥ θ0 + s * Real.sqrt ((Fᵀ *ᵥ w) ⬝ᵥ (Fᵀ *ᵥ w))) ∧
      ∃ θ ∈ EllImage θ0 s F,
        w ⬝ᵥ θ = w ⬝ᵥ θ0 + s * Real.sqrt ((Fᵀ *ᵥ w) ⬝ᵥ (Fᵀ *ᵥ w)) := by
  have hdual : ∀ u : Fin d → ℝ, w ⬝ᵥ (F *ᵥ u) = (Fᵀ *ᵥ w) ⬝ᵥ u := by
    intro u
    rw [dotProduct_mulVec, ← mulVec_transpose]
  set a := Fᵀ *ᵥ w with ha
  have haa : 0 ≤ a ⬝ᵥ a := P08EllipsoidFiber.dot_self_nonneg a
  refine ⟨?_, ?_⟩
  · rintro θ ⟨u, hu, rfl⟩
    rw [dotProduct_add, dotProduct_smul, smul_eq_mul, hdual]
    have hcs := dot_sq_le a u
    have h2 : (a ⬝ᵥ u) ^ 2 ≤ a ⬝ᵥ a := by
      have hu0 : 0 ≤ u ⬝ᵥ u := P08EllipsoidFiber.dot_self_nonneg u
      nlinarith
    have h3 : a ⬝ᵥ u ≤ Real.sqrt (a ⬝ᵥ a) := (le_abs_self _).trans (Real.abs_le_sqrt h2)
    nlinarith
  · rcases haa.eq_or_lt with h0 | hpos
    · refine ⟨θ0 + s • (F *ᵥ 0), ⟨0, by simp, rfl⟩, ?_⟩
      rw [← h0, Real.sqrt_zero]
      simp
    · have hsq : 0 < Real.sqrt (a ⬝ᵥ a) := Real.sqrt_pos.mpr hpos
      refine ⟨θ0 + s • (F *ᵥ ((Real.sqrt (a ⬝ᵥ a))⁻¹ • a)),
        ⟨(Real.sqrt (a ⬝ᵥ a))⁻¹ • a, ?_, rfl⟩, ?_⟩
      · rw [smul_dotProduct, dotProduct_smul, smul_eq_mul, smul_eq_mul, ← mul_assoc, ← mul_inv,
          Real.mul_self_sqrt haa, inv_mul_cancel₀ hpos.ne']
      · rw [dotProduct_add, dotProduct_smul, smul_eq_mul, hdual, dotProduct_smul, smul_eq_mul]
        congr 2
        rw [inv_mul_eq_iff_eq_mul₀ hsq.ne', Real.mul_self_sqrt haa]

/-- Q5b (gauge): `η` is the squared minimal gauge over the compatible fibre, attained at `z0`. -/
theorem eta_squared_gauge (A : Matrix (Fin m) (Fin r) ℝ) (X : Matrix (Fin r) (Fin m) ℝ)
    (b : Fin m → ℝ) (hX : G08AWhitening.IsMoorePenrose A X) (hcomp : ∃ z, A *ᵥ z = b) :
    A *ᵥ (X *ᵥ b) = b ∧ ∀ z, A *ᵥ z = b → (X *ᵥ b) ⬝ᵥ (X *ᵥ b) ≤ z ⬝ᵥ z :=
  ⟨(P08EllipsoidFiber.compatible_iff A X b hX).mp hcomp,
    fun z hz => (P08EllipsoidFiber.min_norm A X b hX hcomp z hz).1⟩

/-- Q5b (boundary link): the fibre image is nonempty iff the support is compatible and the
squared quotient gauge `η` is at most one. -/
theorem fibreImage_nonempty_iff (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (hX : G08AWhitening.IsMoorePenrose (B * L) X) :
    (FibreImage c L B P y).Nonempty ↔
      (∃ z, (B * L) *ᵥ z = y - B *ᵥ c) ∧
        (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1 := by
  rw [fibreImage_eq_latent, Set.image_nonempty]
  constructor
  · rintro ⟨z, hz, hzn⟩
    have hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c := ⟨z, hz⟩
    exact ⟨hcomp, (P08EllipsoidFiber.min_norm (B * L) X _ hX hcomp z hz).1.trans hzn⟩
  · rintro ⟨hcomp, hη⟩
    exact ⟨X *ᵥ (y - B *ᵥ c), (P08EllipsoidFiber.compatible_iff (B * L) X _ hX).mp hcomp, hη⟩

end P08EllipsoidImage
