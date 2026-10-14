import Mathlib
import L2W1KernelBound
import P08EllipsoidImage

/-!
# L2-W1-B: exact branches of the fibre image on bounded / curved domains

For a general admissible set `F ⊆ E` (any subset), an observation map `B` and a target map `P`,
the fibre is `F ∩ B⁻¹{y}` and the target image is `P (F ∩ B⁻¹{y})`.

Three bound notions are kept as distinct definitions:
* `FiniteDomainBound F B P` – a uniform diameter bound on the fibre images of the supplied `F`;
* `DomainCoercivity F B P`  – `‖P x - P x'‖ ≤ C ‖B x - B x'‖` for `x, x' ∈ F`;
* `GlobalCoercivity V B P`  – `‖P v‖ ≤ C ‖B v‖` on a whole linear variation space `V`
  (the left-hand side of L2-W1-A `kernel_bound_iff`).

Branches:
* general `F`: the source-defined image theorem (membership, union, monotonicity, nonemptiness,
  singleton identifiability), kernel inclusion ⇒ domain coercivity on every `F` (via L2-W1-A),
  bounded `F` ⇒ finite-domain bound;
* affine-unbounded `F = x0 + V`: domain coercivity ↔ global coercivity ↔ kernel inclusion
  (reduction to L2-W1-A), and a nonempty fibre image is bounded iff kernel inclusion holds;
* bounded `F = [-1,1]`: finite-domain bound holds while global coercivity fails;
* ellipsoid `F`: the general fibre image is P08-B's `FibreImage`, with its exact image,
  boundary branches, nonemptiness criterion and support function; it always has a finite-domain
  bound;
* box-bounded rational H-polytope: the fibre is the augmented H-polytope used by
  `typefree_fibers.rational_polytope_fiber_support`, the target support in direction `w` is the
  support of `Pᵀ w` on the fibre, LP dual certificates are sound, and one exact instance is
  certified (interval `[0, 3/2]`);
* curved `F`: an exact parabola-arc counterexample where domain coercivity holds but kernel
  inclusion fails (the universal linear iff fails), and the unbounded parabola where every fibre
  image is a singleton yet domain coercivity fails.

No general nonlinear feasible-set solver, no computable support for general curved sets, no
numerical link, and no scientific admission is asserted.
-/

noncomputable section

namespace L2W1FibreImage

open Matrix Set

/-! ## 1. General admissible set -/

section General

variable {E Y Z : Type*}

/-- Fibre of the admissible set `F` over the observed value `y`. -/
def Fibre (F : Set E) (B : E → Y) (y : Y) : Set E := F ∩ B ⁻¹' {y}

/-- Target image `P (F ∩ B⁻¹{y})`. -/
def FibreImage (F : Set E) (B : E → Y) (P : E → Z) (y : Y) : Set Z := P '' Fibre F B y

/-- G1: source-defined image theorem (membership). -/
theorem mem_fibreImage (F : Set E) (B : E → Y) (P : E → Z) (y : Y) (z : Z) :
    z ∈ FibreImage F B P y ↔ ∃ x ∈ F, B x = y ∧ P x = z := by
  simp only [FibreImage, Fibre, mem_image, mem_inter_iff, mem_preimage, mem_singleton_iff,
    and_assoc]

/-- G2: each fibre image lies in the full image `P '' F`. -/
theorem fibreImage_subset_image (F : Set E) (B : E → Y) (P : E → Z) (y : Y) :
    FibreImage F B P y ⊆ P '' F :=
  image_subset _ inter_subset_left

/-- G3: the fibre images over all observed values exhaust `P '' F`. -/
theorem iUnion_fibreImage (F : Set E) (B : E → Y) (P : E → Z) :
    ⋃ y, FibreImage F B P y = P '' F := by
  ext z
  simp only [mem_iUnion, mem_fibreImage, mem_image]
  constructor
  · rintro ⟨y, x, hx, -, rfl⟩
    exact ⟨x, hx, rfl⟩
  · rintro ⟨x, hx, rfl⟩
    exact ⟨B x, x, hx, rfl, rfl⟩

/-- G4: monotonicity in the admissible set. -/
theorem fibreImage_mono {F F' : Set E} (h : F ⊆ F') (B : E → Y) (P : E → Z) (y : Y) :
    FibreImage F B P y ⊆ FibreImage F' B P y :=
  image_subset _ (inter_subset_inter_left _ h)

/-- G5: the fibre image is nonempty iff `y` is an observable value of `F`. -/
theorem fibreImage_nonempty_iff (F : Set E) (B : E → Y) (P : E → Z) (y : Y) :
    (FibreImage F B P y).Nonempty ↔ y ∈ B '' F := by
  constructor
  · rintro ⟨z, hz⟩
    obtain ⟨x, hx, hBx, -⟩ := (mem_fibreImage F B P y z).mp hz
    exact ⟨x, hx, hBx⟩
  · rintro ⟨x, hx, hBx⟩
    exact ⟨P x, (mem_fibreImage F B P y (P x)).mpr ⟨x, hx, hBx, rfl⟩⟩

/-- G6: singleton identifiability of every fibre image iff `P` is constant on the `B`-fibres
of `F` (no linearity, no kernel condition). -/
theorem fibreImage_subsingleton_iff (F : Set E) (B : E → Y) (P : E → Z) :
    (∀ y, (FibreImage F B P y).Subsingleton) ↔
      ∀ x ∈ F, ∀ x' ∈ F, B x = B x' → P x = P x' := by
  constructor
  · intro h x hx x' hx' hB
    exact h (B x) ((mem_fibreImage F B P _ _).mpr ⟨x, hx, rfl, rfl⟩)
      ((mem_fibreImage F B P _ _).mpr ⟨x', hx', hB.symm, rfl⟩)
  · intro h y z hz z' hz'
    obtain ⟨x, hx, hBx, rfl⟩ := (mem_fibreImage F B P y z).mp hz
    obtain ⟨x', hx', hBx', rfl⟩ := (mem_fibreImage F B P y z').mp hz'
    exact h x hx x' hx' (hBx.trans hBx'.symm)

end General

/-! ## 2. Distinct bound notions -/

section BoundNotions

variable {E Y Z : Type*}

/-- Finite-domain bound: a uniform bound on the diameter of the fibre images of the supplied
set `F` (a statement about `F` only). -/
def FiniteDomainBound [SeminormedAddCommGroup Z] (F : Set E) (B : E → Y) (P : E → Z) : Prop :=
  ∃ R : ℝ, ∀ y, ∀ z ∈ FibreImage F B P y, ∀ z' ∈ FibreImage F B P y, ‖z - z'‖ ≤ R

/-- Domain coercivity on the supplied set `F`. -/
def DomainCoercivity [SeminormedAddCommGroup Y] [SeminormedAddCommGroup Z]
    (F : Set E) (B : E → Y) (P : E → Z) : Prop :=
  ∃ C : ℝ, 0 ≤ C ∧ ∀ x ∈ F, ∀ x' ∈ F, ‖P x - P x'‖ ≤ C * ‖B x - B x'‖

/-- Global coercivity on a whole linear variation space `V` (L2-W1-A left-hand side). -/
def GlobalCoercivity [AddCommGroup E] [Module ℝ E] [SeminormedAddCommGroup Y] [Module ℝ Y]
    [SeminormedAddCommGroup Z] [Module ℝ Z]
    (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) : Prop :=
  ∃ C : ℝ, 0 ≤ C ∧ ∀ v ∈ V, ‖P v‖ ≤ C * ‖B v‖

/-- Kernel inclusion on the variation space `V` (L2-W1-A right-hand side). -/
def KernelInclusion [AddCommGroup E] [Module ℝ E] [AddCommGroup Y] [Module ℝ Y]
    [AddCommGroup Z] [Module ℝ Z]
    (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) : Prop :=
  ∀ v ∈ V, B v = 0 → P v = 0

/-- N1: a bounded image `P '' F` gives a finite-domain bound. -/
theorem finiteDomainBound_of_isBounded_image [SeminormedAddCommGroup Z]
    (F : Set E) (B : E → Y) (P : E → Z) (h : Bornology.IsBounded (P '' F)) :
    FiniteDomainBound F B P := by
  obtain ⟨C, hC⟩ := isBounded_iff_forall_norm_le.mp h
  refine ⟨C + C, fun y z hz z' hz' => ?_⟩
  have h1 := hC z (fibreImage_subset_image F B P y hz)
  have h2 := hC z' (fibreImage_subset_image F B P y hz')
  calc ‖z - z'‖ ≤ ‖z‖ + ‖z'‖ := norm_sub_le z z'
    _ ≤ C + C := add_le_add h1 h2

/-- N2: domain coercivity forces every fibre image to be a subsingleton. -/
theorem domainCoercivity_subsingleton [SeminormedAddCommGroup Y] [NormedAddCommGroup Z]
    (F : Set E) (B : E → Y) (P : E → Z) (h : DomainCoercivity F B P) (y : Y) :
    (FibreImage F B P y).Subsingleton := by
  obtain ⟨C, -, hC⟩ := h
  intro z hz z' hz'
  obtain ⟨x, hx, hBx, rfl⟩ := (mem_fibreImage F B P y z).mp hz
  obtain ⟨x', hx', hBx', rfl⟩ := (mem_fibreImage F B P y z').mp hz'
  have h1 := hC x hx x' hx'
  rw [hBx, hBx', sub_self, norm_zero, mul_zero] at h1
  exact sub_eq_zero.mp (norm_le_zero_iff.mp h1)

end BoundNotions

/-! ## 3. Linear observation / target maps: general `F` and the affine-unbounded branch -/

section Linear

variable {E Y Z : Type*}
  [NormedAddCommGroup E] [NormedSpace ℝ E] [FiniteDimensional ℝ E]
  [NormedAddCommGroup Y] [NormedSpace ℝ Y]
  [NormedAddCommGroup Z] [NormedSpace ℝ Z]

/-- L1: global coercivity is exactly kernel inclusion (L2-W1-A, imported unchanged). -/
theorem globalCoercivity_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) :
    GlobalCoercivity V B P ↔ KernelInclusion V B P :=
  L2W1KernelBound.kernel_bound_iff V B P

/-- L2 (universal sufficient direction, any `F`): whole-space kernel inclusion gives domain
coercivity on every admissible set. -/
theorem kernelInclusion_domainCoercivity (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z)
    (h : KernelInclusion ⊤ B P) (F : Set E) : DomainCoercivity F B P := by
  obtain ⟨C, hC0, hC⟩ := (L2W1KernelBound.kernel_bound_iff ⊤ B P).mpr h
  refine ⟨C, hC0, fun x _ x' _ => ?_⟩
  rw [← map_sub, ← map_sub]
  exact hC _ Submodule.mem_top

/-- L3: a bounded admissible set has bounded fibre images (no kernel condition). -/
theorem isBounded_fibreImage (F : Set E) (hF : Bornology.IsBounded F) (B : E → Y)
    (P : E →ₗ[ℝ] Z) (y : Y) : Bornology.IsBounded (FibreImage F B P y) := by
  have h := (LinearMap.toContinuousLinearMap P).lipschitz.isBounded_image hF
  rw [LinearMap.coe_toContinuousLinearMap'] at h
  exact h.subset (fibreImage_subset_image F B P y)

/-- L4: a bounded admissible set has a finite-domain bound (no kernel condition). -/
theorem isBounded_finiteDomainBound (F : Set E) (hF : Bornology.IsBounded F) (B : E → Y)
    (P : E →ₗ[ℝ] Z) : FiniteDomainBound F B P := by
  apply finiteDomainBound_of_isBounded_image
  have h := (LinearMap.toContinuousLinearMap P).lipschitz.isBounded_image hF
  rwa [LinearMap.coe_toContinuousLinearMap'] at h

/-- Affine admissible set `x0 + V`. -/
def AffineDomain (x0 : E) (V : Submodule ℝ E) : Set E := {x | x - x0 ∈ V}

/-- A1: on the affine domain, domain coercivity is global coercivity on `V`
(reduction to L2-W1-A `affine_kernel_bound` / `kernel_bound_iff`). -/
theorem affine_domainCoercivity_iff_global (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 : E) :
    DomainCoercivity (AffineDomain x0 V) B P ↔ GlobalCoercivity V B P := by
  constructor
  · rintro ⟨C, hC0, hC⟩
    refine ⟨C, hC0, fun v hv => ?_⟩
    have h := hC (x0 + v) (by simpa [AffineDomain] using hv) x0 (by simp [AffineDomain])
    simpa [map_add] using h
  · intro hg
    obtain ⟨C, hC0, hC⟩ :=
      L2W1KernelBound.affine_kernel_bound V B P x0 ((globalCoercivity_iff V B P).mp hg)
    exact ⟨C, hC0, fun x hx x' hx' => hC x x' hx hx'⟩

/-- A2: affine-unbounded branch = L2-W1-A kernel condition. -/
theorem affine_branch_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) (x0 : E) :
    DomainCoercivity (AffineDomain x0 V) B P ↔ KernelInclusion V B P :=
  (affine_domainCoercivity_iff_global V B P x0).trans (globalCoercivity_iff V B P)

/-- Under kernel inclusion an affine fibre image is the single point `P x1`. -/
theorem affine_fibreImage_subset_singleton (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 x1 : E) (hx1 : x1 - x0 ∈ V) (hker : KernelInclusion V B P) :
    FibreImage (AffineDomain x0 V) B P (B x1) ⊆ {P x1} := by
  intro z hz
  obtain ⟨x, hx, hBx, rfl⟩ := (mem_fibreImage _ _ _ _ z).mp hz
  have hmem : x - x1 ∈ V := by
    have h := V.sub_mem hx hx1
    rwa [sub_sub_sub_cancel_right] at h
  have hB : B (x - x1) = 0 := by rw [map_sub, hBx, sub_self]
  have hP := hker _ hmem hB
  rw [map_sub, sub_eq_zero] at hP
  exact hP

/-- A3: on the affine domain, a nonempty fibre image is bounded iff kernel inclusion holds. -/
theorem affine_fibreImage_isBounded_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 x1 : E) (hx1 : x1 - x0 ∈ V) :
    Bornology.IsBounded (FibreImage (AffineDomain x0 V) B P (B x1)) ↔
      KernelInclusion V B P := by
  constructor
  · intro hb v hv hBv
    by_contra hPv
    obtain ⟨C, hC⟩ := isBounded_iff_forall_norm_le.mp hb
    have hpos : 0 < ‖P v‖ := norm_pos_iff.mpr hPv
    set t : ℝ := (|C| + ‖P x1‖ + 1) / ‖P v‖ with ht_def
    have ht0 : 0 ≤ t := by positivity
    have hmem : P (x1 + t • v) ∈ FibreImage (AffineDomain x0 V) B P (B x1) := by
      refine (mem_fibreImage _ _ _ _ _).mpr ⟨x1 + t • v, ?_, ?_, rfl⟩
      · show x1 + t • v - x0 ∈ V
        have hEq : x1 + t • v - x0 = (x1 - x0) + t • v := by abel
        rw [hEq]
        exact V.add_mem hx1 (V.smul_mem t hv)
      · rw [map_add, map_smul, hBv, smul_zero, add_zero]
    have h1 := hC _ hmem
    rw [map_add, map_smul] at h1
    have h2 : ‖t • P v‖ ≤ ‖P x1 + t • P v‖ + ‖P x1‖ := by
      calc ‖t • P v‖ = ‖(P x1 + t • P v) - P x1‖ := by rw [add_sub_cancel_left]
        _ ≤ ‖P x1 + t • P v‖ + ‖P x1‖ := norm_sub_le _ _
    have h3 : ‖t • P v‖ = |C| + ‖P x1‖ + 1 := by
      rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg ht0, ht_def, div_mul_cancel₀ _ hpos.ne']
    have h4 := le_abs_self C
    linarith
  · intro hker
    exact Bornology.isBounded_singleton.subset
      (affine_fibreImage_subset_singleton V B P x0 x1 hx1 hker)

/-- A4: on the affine domain, a nonempty fibre image is a subsingleton iff kernel inclusion
holds. -/
theorem affine_fibreImage_subsingleton_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 x1 : E) (hx1 : x1 - x0 ∈ V) :
    (FibreImage (AffineDomain x0 V) B P (B x1)).Subsingleton ↔ KernelInclusion V B P := by
  constructor
  · intro hs
    refine (affine_fibreImage_isBounded_iff V B P x0 x1 hx1).mp ?_
    have hx1mem : P x1 ∈ FibreImage (AffineDomain x0 V) B P (B x1) :=
      (mem_fibreImage _ _ _ _ _).mpr ⟨x1, hx1, rfl, rfl⟩
    exact Bornology.isBounded_singleton.subset fun z hz => hs hz hx1mem
  · intro hker
    exact Set.subsingleton_singleton.anti
      (affine_fibreImage_subset_singleton V B P x0 x1 hx1 hker)

end Linear

/-! ## 4. Bounded branch: finite-domain bound is not global coercivity -/

/-- Negative control (`B = 0`, `P = id`, `F = [-1, 1]`): a finite-domain bound holds while
global coercivity and kernel inclusion fail. -/
theorem bounded_branch_separation :
    FiniteDomainBound (Icc (-1 : ℝ) 1) (0 : ℝ →ₗ[ℝ] ℝ) (LinearMap.id : ℝ →ₗ[ℝ] ℝ) ∧
      ¬ GlobalCoercivity (⊤ : Submodule ℝ ℝ) (0 : ℝ →ₗ[ℝ] ℝ) (LinearMap.id : ℝ →ₗ[ℝ] ℝ) ∧
      ¬ KernelInclusion (⊤ : Submodule ℝ ℝ) (0 : ℝ →ₗ[ℝ] ℝ) (LinearMap.id : ℝ →ₗ[ℝ] ℝ) := by
  have hK : ¬ KernelInclusion (⊤ : Submodule ℝ ℝ) (0 : ℝ →ₗ[ℝ] ℝ)
      (LinearMap.id : ℝ →ₗ[ℝ] ℝ) := by
    intro h
    have h1 := h 1 Submodule.mem_top (by simp)
    simp at h1
  refine ⟨isBounded_finiteDomainBound _ (Metric.isBounded_Icc _ _) _ _, ?_, hK⟩
  rw [globalCoercivity_iff]
  exact hK

/-! ## 5. Ellipsoid branch (P08-B, imported unchanged) -/

section Ellipsoid

variable {n r m q d : ℕ}

/-- E1: the general fibre image of the ellipsoid is P08-B's `FibreImage`. -/
theorem ellipsoid_fibreImage_eq_P08 (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ) :
    FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y =
      P08EllipsoidImage.FibreImage c L B P y :=
  rfl

/-- E2: exact ellipsoid image for `η ≤ 1` (P08-B `fibreImage_eq_of_le`). -/
theorem ellipsoid_branch (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) (hN : P08EllipsoidImage.IsKerONB (B * L) N)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1) :
    FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y =
      P08EllipsoidImage.EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
        (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N) := by
  rw [ellipsoid_fibreImage_eq_P08]
  exact P08EllipsoidImage.fibreImage_eq_of_le c L B P y X N hX hcomp hN hη

/-- E3: boundary branches (`η = 1` single point, `η > 1` empty, incompatible support empty). -/
theorem ellipsoid_branch_boundary (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (hX : G08AWhitening.IsMoorePenrose (B * L) X) :
    ((∃ z, (B * L) *ᵥ z = y - B *ᵥ c) →
        (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) = 1 →
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y =
          {P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c)))}) ∧
      ((∃ z, (B * L) *ᵥ z = y - B *ᵥ c) →
        1 < (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) →
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y = ∅) ∧
      ((¬ ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) →
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y = ∅) :=
  ⟨fun hcomp hη => P08EllipsoidImage.boundary_eq_one c L B P y X hX hcomp hη,
    fun hcomp hη => P08EllipsoidImage.boundary_gt_one c L B P y X hX hcomp hη,
    fun hinc => P08EllipsoidImage.incompatible_empty c L B P y hinc⟩

/-- E4: nonemptiness criterion (compatible support and squared quotient gauge `η ≤ 1`). -/
theorem ellipsoid_branch_nonempty_iff (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (hX : G08AWhitening.IsMoorePenrose (B * L) X) :
    (FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y).Nonempty ↔
      (∃ z, (B * L) *ᵥ z = y - B *ᵥ c) ∧
        (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1 :=
  P08EllipsoidImage.fibreImage_nonempty_iff c L B P y X hX

/-- E5: exact support function of the ellipsoid fibre image (bound and attainment). -/
theorem ellipsoid_branch_support (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) (hN : P08EllipsoidImage.IsKerONB (B * L) N)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1) (w : Fin q → ℝ) :
    IsGreatest ((fun θ => w ⬝ᵥ θ) ''
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y)
      (w ⬝ᵥ (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c)))) +
        Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c))) *
          Real.sqrt (((P * L * N)ᵀ *ᵥ w) ⬝ᵥ ((P * L * N)ᵀ *ᵥ w))) := by
  rw [ellipsoid_branch c L B P y X N hX hcomp hN hη]
  obtain ⟨hle, θ, hθ, heq⟩ := P08EllipsoidImage.support_function
    (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
    (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (Real.sqrt_nonneg _)
    (P * L * N) w
  refine ⟨⟨θ, hθ, heq⟩, ?_⟩
  rintro _ ⟨θ', hθ', rfl⟩
  exact hle θ' hθ'

/-- The closed Euclidean unit ball lies in the unit box. -/
theorem unitBall_subset_box (z : Fin r → ℝ) (hz : z ⬝ᵥ z ≤ 1) :
    z ∈ Icc (-1 : Fin r → ℝ) 1 := by
  have hi : ∀ i, z i * z i ≤ 1 := by
    intro i
    have h : z i * z i ≤ z ⬝ᵥ z := by
      unfold dotProduct
      exact Finset.single_le_sum (f := fun j => z j * z j) (fun j _ => mul_self_nonneg (z j))
        (Finset.mem_univ i)
    linarith
  refine ⟨fun i => ?_, fun i => ?_⟩
  · have := hi i
    simp only [Pi.neg_apply, Pi.one_apply]
    nlinarith
  · have := hi i
    simp only [Pi.one_apply]
    nlinarith

/-- E6: the ellipsoid branch always has a finite-domain bound (no kernel condition). -/
theorem ellipsoid_finiteDomainBound (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) :
    FiniteDomainBound (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) := by
  apply finiteDomainBound_of_isBounded_image
  have hcont : Continuous (fun z : Fin r → ℝ => P *ᵥ (c + L *ᵥ z)) := by fun_prop
  refine ((isCompact_Icc (a := (-1 : Fin r → ℝ)) (b := 1)).image hcont).isBounded.subset ?_
  rintro _ ⟨x, ⟨z, hz, rfl⟩, rfl⟩
  exact ⟨z, unitBall_subset_box z hz, rfl⟩

end Ellipsoid

/-! ## 6. Box-bounded rational H-polytope branch -/

section Polytope

variable {k n m q : ℕ}

/-- `K = {A x ≤ b, lo ≤ x ≤ hi}` (`typefree_fibers.BoundedRationalPolytope`; the box is part
of the declared domain). -/
def BoxPoly (A : Matrix (Fin k) (Fin n) ℝ) (b : Fin k → ℝ) (lo hi : Fin n → ℝ) :
    Set (Fin n → ℝ) :=
  {x | A *ᵥ x ≤ b ∧ lo ≤ x ∧ x ≤ hi}

/-- General H-polytope `{M x ≤ h}`. -/
def HPoly {ι : Type*} (M : Matrix ι (Fin n) ℝ) (h : ι → ℝ) : Set (Fin n → ℝ) :=
  {x | M *ᵥ x ≤ h}

/-- Row index of the augmented system: `A`, upper box, lower box, `B`, `-B`. -/
abbrev AugIdx (k n m : ℕ) := Fin k ⊕ (Fin n ⊕ (Fin n ⊕ (Fin m ⊕ Fin m)))

/-- Augmented constraint matrix (rows of `rational_polytope_fiber_support`, permuted). -/
def augMat (A : Matrix (Fin k) (Fin n) ℝ) (B : Matrix (Fin m) (Fin n) ℝ) :
    Matrix (AugIdx k n m) (Fin n) ℝ :=
  fromRows A (fromRows 1 (fromRows (-1) (fromRows B (-B))))

/-- Augmented right-hand side. -/
def augRhs (b : Fin k → ℝ) (lo hi : Fin n → ℝ) (y : Fin m → ℝ) : AugIdx k n m → ℝ :=
  Sum.elim b (Sum.elim hi (Sum.elim (-lo) (Sum.elim y (-y))))

/-- R1: the polytope fibre is the augmented H-polytope. -/
theorem polytope_fibre_eq_aug (A : Matrix (Fin k) (Fin n) ℝ) (b : Fin k → ℝ)
    (lo hi : Fin n → ℝ) (B : Matrix (Fin m) (Fin n) ℝ) (y : Fin m → ℝ) :
    Fibre (BoxPoly A b lo hi) (fun x => B *ᵥ x) y = HPoly (augMat A B) (augRhs b lo hi y) := by
  ext x
  simp only [Fibre, BoxPoly, HPoly, augMat, augRhs, mem_inter_iff, mem_setOf_eq, mem_preimage,
    mem_singleton_iff, fromRows_mulVec, one_mulVec, neg_mulVec, Sum.elim_le_elim_iff,
    neg_le_neg_iff]
  constructor
  · rintro ⟨⟨hA, hlo, hhi⟩, hB⟩
    exact ⟨hA, hhi, hlo, hB.le, hB.ge⟩
  · rintro ⟨hA, hhi, hlo, hB1, hB2⟩
    exact ⟨⟨hA, hlo, hhi⟩, le_antisymm hB1 hB2⟩

/-- Dot-product transport `w ⬝ (P x) = (Pᵀ w) ⬝ x`. -/
theorem dot_mulVec_eq {ι κ : Type*} [Fintype ι] [Fintype κ] (P : Matrix ι κ ℝ) (w : ι → ℝ)
    (x : κ → ℝ) : w ⬝ᵥ (P *ᵥ x) = (Pᵀ *ᵥ w) ⬝ᵥ x := by
  rw [dotProduct_mulVec, mulVec_transpose]

/-- R2: the support values of the target image in direction `w` are the support values of
`Pᵀ w` on the fibre (any admissible set; the adapter's `direction = P.T * u`). -/
theorem support_transport {Y : Type*} (F : Set (Fin n → ℝ)) (B : (Fin n → ℝ) → Y) (y : Y)
    (P : Matrix (Fin q) (Fin n) ℝ) (w : Fin q → ℝ) :
    (fun θ => w ⬝ᵥ θ) '' FibreImage F B (fun x => P *ᵥ x) y =
      (fun x => (Pᵀ *ᵥ w) ⬝ᵥ x) '' Fibre F B y := by
  rw [FibreImage, image_image]
  exact congrArg (· '' Fibre F B y) (funext fun x => dot_mulVec_eq P w x)

/-- R3: soundness of an LP dual certificate (weak duality). -/
theorem dual_certificate_upper {ι : Type*} [Fintype ι] (M : Matrix ι (Fin n) ℝ) (h : ι → ℝ)
    (c : Fin n → ℝ) (lam : ι → ℝ) (hlam : 0 ≤ lam) (hdual : Mᵀ *ᵥ lam = c) :
    ∀ x ∈ HPoly M h, c ⬝ᵥ x ≤ lam ⬝ᵥ h := by
  intro x hx
  rw [← hdual, ← dot_mulVec_eq]
  exact dotProduct_le_dotProduct_of_nonneg_left hx hlam

/-- R4: dual certificate plus attaining primal point gives the exact maximum. -/
theorem dual_certificate_isGreatest {ι : Type*} [Fintype ι] (M : Matrix ι (Fin n) ℝ)
    (h : ι → ℝ) (c : Fin n → ℝ) (lam : ι → ℝ) (hlam : 0 ≤ lam) (hdual : Mᵀ *ᵥ lam = c)
    (xs : Fin n → ℝ) (hxs : xs ∈ HPoly M h) (hval : c ⬝ᵥ xs = lam ⬝ᵥ h) :
    IsGreatest ((fun x => c ⬝ᵥ x) '' HPoly M h) (lam ⬝ᵥ h) := by
  refine ⟨⟨xs, hxs, hval⟩, ?_⟩
  rintro _ ⟨x, hx, rfl⟩
  exact dual_certificate_upper M h c lam hlam hdual x hx

/-- R5: dual certificate for `-c` plus attaining primal point gives the exact minimum. -/
theorem dual_certificate_isLeast {ι : Type*} [Fintype ι] (M : Matrix ι (Fin n) ℝ)
    (h : ι → ℝ) (c : Fin n → ℝ) (lam : ι → ℝ) (hlam : 0 ≤ lam) (hdual : Mᵀ *ᵥ lam = -c)
    (xs : Fin n → ℝ) (hxs : xs ∈ HPoly M h) (hval : c ⬝ᵥ xs = -(lam ⬝ᵥ h)) :
    IsLeast ((fun x => c ⬝ᵥ x) '' HPoly M h) (-(lam ⬝ᵥ h)) := by
  refine ⟨⟨xs, hxs, hval⟩, ?_⟩
  rintro _ ⟨x, hx, rfl⟩
  have h1 := dual_certificate_upper M h (-c) lam hlam hdual x hx
  rw [neg_dotProduct] at h1
  show -(lam ⬝ᵥ h) ≤ c ⬝ᵥ x
  linarith

/-- R6: the box gives a finite-domain bound for the polytope branch (no kernel condition). -/
theorem polytope_finiteDomainBound (A : Matrix (Fin k) (Fin n) ℝ) (b : Fin k → ℝ)
    (lo hi : Fin n → ℝ) (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) :
    FiniteDomainBound (BoxPoly A b lo hi) (fun x => B *ᵥ x) (fun x => P *ᵥ x) := by
  apply finiteDomainBound_of_isBounded_image
  have hcont : Continuous (fun x : Fin n → ℝ => P *ᵥ x) := by fun_prop
  exact ((isCompact_Icc (a := lo) (b := hi)).image hcont).isBounded.subset
    (image_subset _ fun x hx => ⟨hx.2.1, hx.2.2⟩)

/-! ### Frozen exact instance (same data as `raw/probes/probe_polytope_and_curved.py`) -/

/-- `x0 + x1 ≤ 1`. -/
def A₁ : Matrix (Fin 1) (Fin 2) ℝ := !![1, 1]
def b₁ : Fin 1 → ℝ := ![1]
def lo₁ : Fin 2 → ℝ := ![0, 0]
def hi₁ : Fin 2 → ℝ := ![1, 1]
/-- Observation `x0 - x1`. -/
def B₁ : Matrix (Fin 1) (Fin 2) ℝ := !![1, -1]
def y₁ : Fin 1 → ℝ := ![0]
/-- Target `x0 + 2 x1`. -/
def P₁ : Matrix (Fin 1) (Fin 2) ℝ := !![1, 2]
def w₁ : Fin 1 → ℝ := ![1]

/-- Dual certificate for the maximum: `3/2 · (A row) + 1/2 · (-B row)`. -/
def lamMax : AugIdx 1 2 1 → ℝ := Sum.elim ![3 / 2] (Sum.elim 0 (Sum.elim 0 (Sum.elim 0 ![1 / 2])))
/-- Dual certificate for the minimum: `1 · (lower x0) + 2 · (lower x1)`. -/
def lamMin : AugIdx 1 2 1 → ℝ := Sum.elim 0 (Sum.elim 0 (Sum.elim ![1, 2] 0))

/-- R7a: exact fibre image of the frozen instance, `{θ | 0 ≤ θ 0 ≤ 3/2}`. -/
theorem instance_fibreImage_eq :
    FibreImage (BoxPoly A₁ b₁ lo₁ hi₁) (fun x => B₁ *ᵥ x) (fun x => P₁ *ᵥ x) y₁ =
      {θ | 0 ≤ θ 0 ∧ θ 0 ≤ 3 / 2} := by
  ext θ
  rw [mem_fibreImage]
  constructor
  · rintro ⟨x, ⟨hA, hlo, hhi⟩, hB, rfl⟩
    have h1 : x 0 + x 1 ≤ 1 := by
      have := hA 0
      simpa [A₁, b₁, mulVec, dotProduct, Fin.sum_univ_two] using this
    have h2 : 0 ≤ x 0 := by simpa [lo₁] using hlo 0
    have h3 : 0 ≤ x 1 := by simpa [lo₁] using hlo 1
    have h4 : x 0 - x 1 = 0 := by
      have := congrFun hB 0
      simp [B₁, y₁, mulVec, dotProduct, Fin.sum_univ_two] at this
      linarith
    simp only [mem_setOf_eq, P₁, mulVec, dotProduct, Fin.sum_univ_two]
    simp
    constructor <;> linarith
  · rintro ⟨h0, h1⟩
    refine ⟨![θ 0 / 3, θ 0 / 3], ⟨?_, ?_, ?_⟩, ?_, ?_⟩
    · intro i
      fin_cases i
      simp [A₁, b₁, mulVec, dotProduct, Fin.sum_univ_two]
      linarith
    · intro i
      fin_cases i <;> simp [lo₁] <;> linarith
    · intro i
      fin_cases i <;> simp [hi₁] <;> linarith
    · funext i
      fin_cases i
      simp [B₁, y₁, mulVec, dotProduct, Fin.sum_univ_two]
    · funext i
      fin_cases i
      simp [P₁, mulVec, dotProduct, Fin.sum_univ_two]
      ring

/-- R7b: certified exact maximum `3/2` of the target support in direction `w₁`, via the
augmented H-representation, support transport and the dual certificate `lamMax`. -/
theorem instance_support_max :
    IsGreatest ((fun θ => w₁ ⬝ᵥ θ) ''
      FibreImage (BoxPoly A₁ b₁ lo₁ hi₁) (fun x => B₁ *ᵥ x) (fun x => P₁ *ᵥ x) y₁) (3 / 2) := by
  rw [support_transport, polytope_fibre_eq_aug]
  have hval : lamMax ⬝ᵥ augRhs b₁ lo₁ hi₁ y₁ = 3 / 2 := by
    simp [lamMax, augRhs, b₁, y₁, dotProduct, Fintype.sum_sum_type]
  rw [← hval]
  refine dual_certificate_isGreatest _ _ _ lamMax ?_ ?_ ![1 / 2, 1 / 2] ?_ ?_
  · rintro (i | i | i | i | i) <;> fin_cases i <;> simp [lamMax] <;> norm_num
  · funext j
    fin_cases j <;>
      simp [augMat, lamMax, P₁, w₁, A₁, B₁, mulVec, dotProduct, Fintype.sum_sum_type,
        Fin.sum_univ_two, Matrix.one_apply] <;> norm_num
  · rw [← polytope_fibre_eq_aug]
    refine ⟨⟨?_, ?_, ?_⟩, ?_⟩
    · intro i
      fin_cases i
      simp [A₁, b₁, mulVec, dotProduct, Fin.sum_univ_two]
      norm_num
    · intro i
      fin_cases i <;> simp [lo₁]
    · intro i
      fin_cases i <;> simp [hi₁] <;> norm_num
    · show B₁ *ᵥ ![1 / 2, 1 / 2] = y₁
      funext i
      fin_cases i
      simp [B₁, y₁, mulVec, dotProduct, Fin.sum_univ_two]
  · rw [hval]
    simp [P₁, w₁, mulVec, dotProduct, Fin.sum_univ_two, Matrix.transpose_apply]
    norm_num

/-- R7c: certified exact minimum `0`, via the dual certificate `lamMin`. -/
theorem instance_support_min :
    IsLeast ((fun θ => w₁ ⬝ᵥ θ) ''
      FibreImage (BoxPoly A₁ b₁ lo₁ hi₁) (fun x => B₁ *ᵥ x) (fun x => P₁ *ᵥ x) y₁) 0 := by
  rw [support_transport, polytope_fibre_eq_aug]
  have hval : -(lamMin ⬝ᵥ augRhs b₁ lo₁ hi₁ y₁) = 0 := by
    simp [lamMin, augRhs, lo₁, dotProduct, Fintype.sum_sum_type]
  rw [← hval]
  refine dual_certificate_isLeast _ _ _ lamMin ?_ ?_ 0 ?_ ?_
  · rintro (i | i | i | i | i) <;> fin_cases i <;> simp [lamMin]
  · funext j
    fin_cases j <;>
      simp [augMat, lamMin, P₁, w₁, A₁, B₁, mulVec, dotProduct, Fintype.sum_sum_type,
        Fin.sum_univ_two, Matrix.one_apply]
  · rw [← polytope_fibre_eq_aug]
    refine ⟨⟨?_, ?_, ?_⟩, ?_⟩
    · intro i
      fin_cases i
      simp [A₁, b₁]
    · intro i
      fin_cases i <;> simp [lo₁]
    · intro i
      fin_cases i <;> simp [hi₁]
    · show B₁ *ᵥ 0 = y₁
      funext i
      fin_cases i
      simp [y₁]
  · rw [hval]
    simp

end Polytope

/-! ## 7. Curved branch: exact counterexamples to the universal linear iff -/

section Curved

/-- Bounded parabola arc `{(t, t²) : -1 ≤ t ≤ 1}`. -/
def arc : Set (Fin 2 → ℝ) := {x | -1 ≤ x 0 ∧ x 0 ≤ 1 ∧ x 1 = x 0 ^ 2}

/-- Unbounded parabola `{(t, t²)}`. -/
def parabola : Set (Fin 2 → ℝ) := {x | x 1 = x 0 ^ 2}

/-- Observation: first coordinate. -/
def Bc : (Fin 2 → ℝ) →ₗ[ℝ] ℝ := LinearMap.proj 0

/-- Target: second coordinate. -/
def Pc : (Fin 2 → ℝ) →ₗ[ℝ] ℝ := LinearMap.proj 1

/-- C1: kernel inclusion fails (`v = (0, 1)`). -/
theorem curved_kernelInclusion_fails :
    ¬ KernelInclusion (⊤ : Submodule ℝ (Fin 2 → ℝ)) Bc Pc := by
  intro h
  have h1 := h ![0, 1] Submodule.mem_top (by simp [Bc])
  simp [Pc] at h1

/-- C2: domain coercivity on the bounded arc with `C = 2`. -/
theorem curved_arc_domainCoercivity : DomainCoercivity arc Bc Pc := by
  refine ⟨2, by norm_num, fun x hx x' hx' => ?_⟩
  obtain ⟨h1, h2, h3⟩ := hx
  obtain ⟨h1', h2', h3'⟩ := hx'
  simp only [Bc, Pc, LinearMap.proj_apply, Real.norm_eq_abs, h3, h3']
  have hfac : x 0 ^ 2 - x' 0 ^ 2 = (x 0 + x' 0) * (x 0 - x' 0) := by ring
  rw [hfac, abs_mul]
  exact mul_le_mul_of_nonneg_right (abs_le.mpr ⟨by linarith, by linarith⟩) (abs_nonneg _)

/-- C3: exact fibre images of the arc (singleton `{y²}` on `[-1, 1]`, empty outside). -/
theorem curved_arc_fibreImage (y : ℝ) :
    (y ∈ Icc (-1 : ℝ) 1 → FibreImage arc Bc Pc y = {y ^ 2}) ∧
      (y ∉ Icc (-1 : ℝ) 1 → FibreImage arc Bc Pc y = ∅) := by
  constructor
  · rintro ⟨hy1, hy2⟩
    ext z
    rw [mem_fibreImage, mem_singleton_iff]
    constructor
    · rintro ⟨x, ⟨-, -, h3⟩, hB, rfl⟩
      simp only [Bc, Pc, LinearMap.proj_apply] at hB ⊢
      rw [h3, hB]
    · rintro rfl
      refine ⟨![y, y ^ 2], ⟨by simpa using hy1, by simpa using hy2, by simp⟩, ?_, ?_⟩
      · simp [Bc]
      · simp [Pc]
  · intro hy
    ext z
    simp only [mem_fibreImage, mem_empty_iff_false, iff_false, not_exists, not_and]
    intro x hx hB _
    apply hy
    obtain ⟨h1, h2, -⟩ := hx
    simp only [Bc, LinearMap.proj_apply] at hB
    exact ⟨hB ▸ h1, hB ▸ h2⟩

/-- C4: the linear iff fails on the curved bounded arc. -/
theorem curved_linear_iff_fails :
    ¬ (DomainCoercivity arc Bc Pc ↔ KernelInclusion (⊤ : Submodule ℝ (Fin 2 → ℝ)) Bc Pc) :=
  fun h => curved_kernelInclusion_fails (h.mp curved_arc_domainCoercivity)

/-- C5: the universal linear iff, transplanted to admissible sets, is false. -/
theorem universal_linear_iff_false :
    ¬ ∀ (F : Set (Fin 2 → ℝ)) (B P : (Fin 2 → ℝ) →ₗ[ℝ] ℝ),
      (DomainCoercivity F B P ↔ KernelInclusion (⊤ : Submodule ℝ (Fin 2 → ℝ)) B P) :=
  fun h => curved_linear_iff_fails (h arc Bc Pc)

/-- C6: the unbounded parabola identifies every fibre (subsingleton images). -/
theorem parabola_identified (y : ℝ) : (FibreImage parabola Bc Pc y).Subsingleton := by
  refine (fibreImage_subsingleton_iff parabola Bc Pc).mpr ?_ y
  intro x hx x' hx' hB
  simp only [Bc, Pc, LinearMap.proj_apply] at hB ⊢
  rw [hx, hx', hB]

/-- C7: ... but has no domain coercivity (identifiability is not a coercive bound). -/
theorem parabola_not_domainCoercivity : ¬ DomainCoercivity parabola Bc Pc := by
  rintro ⟨C, hC0, hC⟩
  have h := hC ![C + 1, (C + 1) ^ 2] (by simp [parabola]) 0 (by simp [parabola])
  simp only [Bc, Pc, LinearMap.proj_apply, Real.norm_eq_abs, Pi.zero_apply, sub_zero,
    Matrix.cons_val_zero, Matrix.cons_val_one] at h
  rw [abs_of_nonneg (by positivity), abs_of_nonneg (by linarith)] at h
  nlinarith

end Curved

end L2W1FibreImage
