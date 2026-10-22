import Mathlib

/-!
# R190-A — Einstein–matter comparator: source-bound problem restoration (PR-190)

Source citations: `SOURCE_RECOVERY.md`; signatures frozen in `FROZEN_TARGETS.md`.

* Comparator `x_C = Σ² − W² + Ω_tilt + Ω_k`, c = (+,−,+,+)
  (`htt/obsstat/egs3_graded_comparator.py:48-50`).
* Registered open-branch box and sign corners
  (`htt/obsstat/egs3_linearized_realization.py:97-110`).
* Declared constraint-level class (`htt/obsstat/egs3_nonlinear_realization.py:22-43,102-140`):
  homogeneous Bianchi I/V, diagonal trace-free shear, antipodal perfect-fluid tilt pair, Λ.
* The comparator W² lives on the slice normal (`docs/research_program/egs3/CLAIM_LEDGER.yaml:280`);
  its vanishing is DERIVED here from a general Frobenius lemma.
* Local/global sharpness are typed predicates over an arbitrary evolution system; the registered
  evolution system is not transcribed (open obligation), and no attainability is assumed.
-/

noncomputable section

open Real Finset

namespace R190A

/-! ## Part A — signed comparator carrier, box, sign corners -/

/-- Comparator vector g = (Σ², W², Ω_tilt, Ω_k). -/
@[ext] structure CompVec where
  Sigma2 : ℝ
  W2 : ℝ
  Otilt : ℝ
  Ok : ℝ

/-- `x_C = c·g`, `c = (+1, −1, +1, +1)`. -/
def xC (g : CompVec) : ℝ := g.Sigma2 - g.W2 + g.Otilt + g.Ok

/-- PR-187 signed carrier `S₊³ × ℝ`: only the positive block is constrained. -/
def PosBlock (g : CompVec) : Prop := 0 ≤ g.Sigma2 ∧ 0 ≤ g.W2 ∧ 0 ≤ g.Otilt

/-- Component box (signed bounds). -/
structure CBox where
  Slo : ℝ
  Shi : ℝ
  Wlo : ℝ
  Whi : ℝ
  Tlo : ℝ
  Thi : ℝ
  Klo : ℝ
  Khi : ℝ

def CBox.Valid (B : CBox) : Prop :=
  B.Slo ≤ B.Shi ∧ B.Wlo ≤ B.Whi ∧ B.Tlo ≤ B.Thi ∧ B.Klo ≤ B.Khi

def InBox (B : CBox) (g : CompVec) : Prop :=
  (B.Slo ≤ g.Sigma2 ∧ g.Sigma2 ≤ B.Shi) ∧ (B.Wlo ≤ g.W2 ∧ g.W2 ≤ B.Whi) ∧
  (B.Tlo ≤ g.Otilt ∧ g.Otilt ≤ B.Thi) ∧ (B.Klo ≤ g.Ok ∧ g.Ok ≤ B.Khi)

inductive Corner
  | lower
  | upper

/-- Sign-corner rule for c = (+,−,+,+): minimisation takes the lower bound of every
`+` coordinate and the upper bound of the `−` (W²) coordinate. -/
def cornerPoint (B : CBox) : Corner → CompVec
  | .lower => ⟨B.Slo, B.Whi, B.Tlo, B.Klo⟩
  | .upper => ⟨B.Shi, B.Wlo, B.Thi, B.Khi⟩

lemma xC_lower_eq (B : CBox) : xC (cornerPoint B .lower) = B.Slo - B.Whi + B.Tlo + B.Klo := rfl
lemma xC_upper_eq (B : CBox) : xC (cornerPoint B .upper) = B.Shi - B.Wlo + B.Thi + B.Khi := rfl

theorem cornerPoint_mem (B : CBox) (hB : B.Valid) (k : Corner) : InBox B (cornerPoint B k) := by
  obtain ⟨h1, h2, h3, h4⟩ := hB
  cases k
  · exact ⟨⟨le_rfl, h1⟩, ⟨h2, le_rfl⟩, ⟨le_rfl, h3⟩, ⟨le_rfl, h4⟩⟩
  · exact ⟨⟨h1, le_rfl⟩, ⟨le_rfl, h2⟩, ⟨h3, le_rfl⟩, ⟨h4, le_rfl⟩⟩

theorem xC_lower_le (B : CBox) (g : CompVec) (hg : InBox B g) :
    xC (cornerPoint B .lower) ≤ xC g := by
  obtain ⟨⟨h1, -⟩, ⟨-, h2⟩, ⟨h3, -⟩, ⟨h4, -⟩⟩ := hg
  rw [xC_lower_eq]; unfold xC; linarith

theorem xC_le_upper (B : CBox) (g : CompVec) (hg : InBox B g) :
    xC g ≤ xC (cornerPoint B .upper) := by
  obtain ⟨⟨-, h1⟩, ⟨h2, -⟩, ⟨-, h3⟩, ⟨-, h4⟩⟩ := hg
  rw [xC_upper_eq]; unfold xC; linarith

theorem box_image (B : CBox) (hB : B.Valid) (x : ℝ) :
    (∃ g, InBox B g ∧ xC g = x) ↔
      xC (cornerPoint B .lower) ≤ x ∧ x ≤ xC (cornerPoint B .upper) := by
  constructor
  · rintro ⟨g, hg, rfl⟩
    exact ⟨xC_lower_le B g hg, xC_le_upper B g hg⟩
  · rintro ⟨hlo, hhi⟩
    rcases eq_or_lt_of_le (le_trans hlo hhi) with heq | hlt
    · exact ⟨cornerPoint B .lower, cornerPoint_mem B hB _, by linarith⟩
    · rw [xC_lower_eq] at hlo hlt
      rw [xC_upper_eq] at hhi hlt
      obtain ⟨h1, h2, h3, h4⟩ := hB
      have hpos : 0 < (B.Shi - B.Wlo + B.Thi + B.Khi) - (B.Slo - B.Whi + B.Tlo + B.Klo) :=
        sub_pos.2 hlt
      set t := (x - (B.Slo - B.Whi + B.Tlo + B.Klo)) /
        ((B.Shi - B.Wlo + B.Thi + B.Khi) - (B.Slo - B.Whi + B.Tlo + B.Klo)) with ht
      have ht0 : 0 ≤ t := div_nonneg (by linarith) hpos.le
      have ht1 : t ≤ 1 := (div_le_one hpos).2 (by linarith)
      have htx : (B.Slo - B.Whi + B.Tlo + B.Klo) +
          t * ((B.Shi - B.Wlo + B.Thi + B.Khi) - (B.Slo - B.Whi + B.Tlo + B.Klo)) = x := by
        rw [ht]; field_simp; ring
      have ht1' : 0 ≤ 1 - t := by linarith
      refine ⟨⟨(1 - t) * B.Slo + t * B.Shi, (1 - t) * B.Whi + t * B.Wlo,
               (1 - t) * B.Tlo + t * B.Thi, (1 - t) * B.Klo + t * B.Khi⟩, ?_, ?_⟩
      · refine ⟨⟨?_, ?_⟩, ⟨?_, ?_⟩, ⟨?_, ?_⟩, ⟨?_, ?_⟩⟩ <;> dsimp only <;>
          nlinarith [mul_nonneg ht0 (sub_nonneg.2 h1), mul_nonneg ht1' (sub_nonneg.2 h1),
            mul_nonneg ht0 (sub_nonneg.2 h2), mul_nonneg ht1' (sub_nonneg.2 h2),
            mul_nonneg ht0 (sub_nonneg.2 h3), mul_nonneg ht1' (sub_nonneg.2 h3),
            mul_nonneg ht0 (sub_nonneg.2 h4), mul_nonneg ht1' (sub_nonneg.2 h4)]
      · rw [← htx]; unfold xC; dsimp only; ring

theorem lower_argmin_unique (B : CBox) (g : CompVec) (hg : InBox B g)
    (h : xC g = xC (cornerPoint B .lower)) : g = cornerPoint B .lower := by
  obtain ⟨⟨h1, -⟩, ⟨-, h2⟩, ⟨h3, -⟩, ⟨h4, -⟩⟩ := hg
  rw [xC_lower_eq] at h; unfold xC at h
  apply CompVec.ext <;> simp only [cornerPoint] <;> linarith

theorem upper_argmax_unique (B : CBox) (g : CompVec) (hg : InBox B g)
    (h : xC g = xC (cornerPoint B .upper)) : g = cornerPoint B .upper := by
  obtain ⟨⟨-, h1⟩, ⟨h2, -⟩, ⟨-, h3⟩, ⟨-, h4⟩⟩ := hg
  rw [xC_upper_eq] at h; unfold xC at h
  apply CompVec.ext <;> simp only [cornerPoint] <;> linarith

/-- Anti-swap: any box point whose W² is below the W² upper bound lies strictly above the
lower endpoint (no shear/other-sector substitute reaches it). -/
theorem lower_strict_of_W2_lt (B : CBox) (g : CompVec) (hg : InBox B g) (hW : g.W2 < B.Whi) :
    xC (cornerPoint B .lower) < xC g := by
  obtain ⟨⟨h1, -⟩, -, ⟨h3, -⟩, ⟨h4, -⟩⟩ := hg
  rw [xC_lower_eq]; unfold xC; linarith

/-- Registered open-curvature box. -/
def regBox : CBox := ⟨12/100, 12/100, 0, 4/100, 3/100, 3/100, 0, 2/100⟩

theorem regBox_valid : regBox.Valid := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> norm_num [regBox]

theorem reg_corners :
    cornerPoint regBox .lower = ⟨12/100, 4/100, 3/100, 0⟩ ∧
    cornerPoint regBox .upper = ⟨12/100, 0, 3/100, 2/100⟩ ∧
    xC (cornerPoint regBox .lower) = 11/100 ∧ xC (cornerPoint regBox .upper) = 17/100 := by
  refine ⟨rfl, rfl, ?_, ?_⟩
  · rw [xC_lower_eq]; norm_num [regBox]
  · rw [xC_upper_eq]; norm_num [regBox]

/-- Algebraic (level-1) attainability. -/
def AlgebraicAttained (B : CBox) (x : ℝ) : Prop := ∃ g, InBox B g ∧ PosBlock g ∧ xC g = x

theorem reg_algebraic_iff (x : ℝ) : AlgebraicAttained regBox x ↔ 11/100 ≤ x ∧ x ≤ 17/100 := by
  rw [← reg_corners.2.2.1, ← reg_corners.2.2.2, ← box_image regBox regBox_valid]
  constructor
  · rintro ⟨g, hg, -, hx⟩; exact ⟨g, hg, hx⟩
  · rintro ⟨g, hg, hx⟩
    refine ⟨g, hg, ?_, hx⟩
    obtain ⟨⟨h1, -⟩, ⟨h2, -⟩, ⟨h3, -⟩, -⟩ := hg
    simp only [regBox] at h1 h2 h3
    exact ⟨by linarith, by linarith, by linarith⟩

theorem reg_lower_forces_W2 (g : CompVec) (hg : InBox regBox g) (h : xC g = 11/100) :
    g.W2 = 4/100 := by
  have := lower_argmin_unique regBox g hg (by rw [h, reg_corners.2.2.1])
  rw [this, reg_corners.1]

theorem shear_swap_control : xC ⟨12/100, 0, 3/100, 0⟩ = 15/100 ∧ (15/100 : ℝ) ≠ 11/100 := by
  constructor
  · unfold xC; norm_num
  · norm_num

/-! ## Part C — PR-186 / PR-187 convention-authority cross-check -/

def IsAntisym (A : Fin 3 → Fin 3 → ℝ) : Prop := ∀ i j, A j i = -A i j

/-- Dual vector ω_a = ½ ε_abc ω^bc of a spatial antisymmetric tensor. -/
def dualVec (A : Fin 3 → Fin 3 → ℝ) : Fin 3 → ℝ := ![A 1 2, A 2 0, A 0 1]

def tensorSq (A : Fin 3 → Fin 3 → ℝ) : ℝ := ∑ i, ∑ j, A i j ^ 2

def vecSq (v : Fin 3 → ℝ) : ℝ := ∑ i, v i ^ 2

theorem tensorSq_eq_two_vecSq (A : Fin 3 → Fin 3 → ℝ) (hA : IsAntisym A) :
    tensorSq A = 2 * vecSq (dualVec A) := by
  have h10 : A 1 0 = -A 0 1 := hA 0 1
  have h20 : A 2 0 = -A 0 2 := hA 0 2
  have h21 : A 2 1 = -A 1 2 := hA 1 2
  have h00 : A 0 0 = 0 := by linarith [hA 0 0]
  have h11 : A 1 1 = 0 := by linarith [hA 1 1]
  have h22 : A 2 2 = 0 := by linarith [hA 2 2]
  have hv : vecSq (dualVec A) = A 1 2 ^ 2 + A 2 0 ^ 2 + A 0 1 ^ 2 := by
    simp [vecSq, dualVec, Fin.sum_univ_three]
  rw [hv]
  simp only [tensorSq, Fin.sum_univ_three]
  rw [h10, h20, h21, h00, h11, h22]; ring

/-- Registered PR-186 convention `W² = ω_abω^ab / (6H²)`. -/
def W2reg (A : Fin 3 → Fin 3 → ℝ) (H : ℝ) : ℝ := tensorSq A / (6 * H ^ 2)

theorem W2reg_eq_vecForm (A : Fin 3 → Fin 3 → ℝ) (hA : IsAntisym A) (H : ℝ) :
    W2reg A H = vecSq (dualVec A) / (3 * H ^ 2) := by
  rw [W2reg, tensorSq_eq_two_vecSq A hA]; ring

theorem wrong_display_is_three (A : Fin 3 → Fin 3 → ℝ) (hA : IsAntisym A) (H : ℝ) :
    vecSq (dualVec A) / H ^ 2 = 3 * W2reg A H := by
  rw [W2reg_eq_vecForm A hA]; ring

theorem W2_ceiling (A : Fin 3 → Fin 3 → ℝ) (H B : ℝ) (hH : 0 < H)
    (h : √(tensorSq A) / (3 * H) ≤ B) : W2reg A H ≤ 3/2 * B ^ 2 := by
  have hT : 0 ≤ tensorSq A :=
    Finset.sum_nonneg (fun i _ => Finset.sum_nonneg (fun j _ => sq_nonneg (A i j)))
  have h3H : 0 < 3 * H := by linarith
  have hs : √(tensorSq A) ≤ B * (3 * H) := (div_le_iff₀ h3H).1 h
  have hs0 : 0 ≤ √(tensorSq A) := Real.sqrt_nonneg _
  have hsq : tensorSq A ≤ (B * (3 * H)) ^ 2 := by
    calc tensorSq A = √(tensorSq A) ^ 2 := (Real.sq_sqrt hT).symm
      _ ≤ (B * (3 * H)) ^ 2 := pow_le_pow_left₀ hs0 hs 2
  have h6 : 0 < 6 * H ^ 2 := by positivity
  rw [W2reg, div_le_iff₀ h6]
  have e : (B * (3 * H)) ^ 2 = 3/2 * B ^ 2 * (6 * H ^ 2) := by ring
  linarith

theorem W2_theta_form (v H : ℝ) : 3 * (v / (3 * H) ^ 2) = v / (3 * H ^ 2) := by ring

theorem Sigma2_theta_form (S H : ℝ) : 3/2 * (S / (3 * H) ^ 2) = S / (6 * H ^ 2) := by ring

/-- n-frame energy density of one perfect-fluid stream (rest density μ, p = wμ) at
rapidity β: `T₀₀ = (μ+p) cosh²β − p`. -/
def streamEnergy (μ w β : ℝ) : ℝ := (1 + w) * μ * cosh β ^ 2 - w * μ

/-- n-frame energy flux of one stream along its tilt direction: `(μ+p) sinh β cosh β`. -/
def streamFlux (μ w β : ℝ) : ℝ := (1 + w) * μ * sinh β * cosh β

theorem streamEnergy_eq (μ w β : ℝ) : streamEnergy μ w β = μ + (1 + w) * μ * sinh β ^ 2 := by
  rw [streamEnergy, Real.cosh_sq]; ring

theorem pair_flux_cancel (μ w β : ℝ) : streamFlux μ w β + streamFlux μ w (-β) = 0 := by
  simp only [streamFlux, Real.sinh_neg, Real.cosh_neg]; ring

theorem pair_energy_eq (μ w β : ℝ) :
    streamEnergy μ w β + streamEnergy μ w (-β) = 2 * μ + 2 * ((1 + w) * μ * sinh β ^ 2) := by
  rw [streamEnergy_eq, streamEnergy_eq, Real.sinh_neg]; ring

def tiltSingle (w Om β : ℝ) : ℝ := (1 + w) * Om * sinh β ^ 2

/-- PR-187 pair-density conventions (`frame_typed_algebra.py:216-231`). -/
inductive PairConv
  | fixedTotal
  | perStream

def tiltPair : PairConv → ℝ → ℝ → ℝ → ℝ
  | .fixedTotal, w, Om, β => tiltSingle w Om β
  | .perStream, w, Om, β => 2 * tiltSingle w Om β

theorem pair_excess_labels (μs w β : ℝ) :
    (streamEnergy μs w β + streamEnergy μs w (-β)) - 2 * μs = tiltPair .fixedTotal w (2 * μs) β ∧
    (streamEnergy μs w β + streamEnergy μs w (-β)) - 2 * μs = tiltPair .perStream w μs β := by
  rw [pair_energy_eq]
  constructor <;> simp only [tiltPair, tiltSingle] <;> ring

theorem mixed_label_doublecounts (μs w β : ℝ) (h : (1 + w) * μs * sinh β ^ 2 ≠ 0) :
    tiltPair .perStream w (2 * μs) β ≠ (streamEnergy μs w β + streamEnergy μs w (-β)) - 2 * μs := by
  rw [pair_energy_eq]; simp only [tiltPair, tiltSingle]
  intro h'
  apply h
  linear_combination h' / 2

/-! ## Part F — Frobenius: the slice-normal congruence is vorticity-free -/

/-- First jet at a point of the slice normal `n_a = −N ∂_a t` in a chart (indices 0..3). -/
structure SliceJet where
  N : ℝ
  dt : Fin 4 → ℝ
  dN : Fin 4 → ℝ
  hessT : Fin 4 → Fin 4 → ℝ
  Gam : Fin 4 → Fin 4 → Fin 4 → ℝ
  nUp : Fin 4 → ℝ
  gInv : Fin 4 → Fin 4 → ℝ

namespace SliceJet

def nCov (J : SliceJet) (a : Fin 4) : ℝ := -J.N * J.dt a

/-- Torsion-free connection, symmetric Hessian of the time function, lapse ≠ 0, n·n = −1. -/
def Valid (J : SliceJet) : Prop :=
  J.N ≠ 0 ∧ (∀ a b, J.hessT a b = J.hessT b a) ∧ (∀ e c d, J.Gam e c d = J.Gam e d c) ∧
    ∑ a, J.nUp a * J.nCov a = -1

/-- `∇_c n_d = ∂_c n_d − Γ^e_{cd} n_e`, `∂_c n_d = −(∂_c N) ∂_d t − N ∂_c∂_d t`. -/
def covDeriv (J : SliceJet) (c d : Fin 4) : ℝ :=
  -(J.dN c * J.dt d) - J.N * J.hessT c d - ∑ e, J.Gam e c d * J.nCov e

/-- Projector `h_a{}^b = δ_a^b + n_a n^b`. -/
def proj (J : SliceJet) (a b : Fin 4) : ℝ := (if a = b then 1 else 0) + J.nCov a * J.nUp b

/-- Vorticity `ω_ab = h_a{}^c h_b{}^d ∇_[c n_d]`. -/
def vort (J : SliceJet) (a b : Fin 4) : ℝ :=
  ∑ c, ∑ d, J.proj a c * J.proj b d * ((J.covDeriv c d - J.covDeriv d c) / 2)

/-- `ω_ab ω^ab` with the inverse metric. -/
def vortSq (J : SliceJet) : ℝ :=
  ∑ a, ∑ b, ∑ c, ∑ d, J.gInv a c * J.gInv b d * J.vort a b * J.vort c d

end SliceJet

/-- Comparator W² on the slice normal (PR-186 normalization). -/
def W2n (J : SliceJet) (H : ℝ) : ℝ := J.vortSq / (6 * H ^ 2)

lemma proj_n (J : SliceJet) (hJ : J.Valid) (b : Fin 4) :
    ∑ d, J.proj b d * J.nCov d = 0 := by
  obtain ⟨-, -, -, hn⟩ := hJ
  have h1 : ∑ d, J.proj b d * J.nCov d = J.nCov b + J.nCov b * ∑ d, J.nUp d * J.nCov d := by
    simp only [SliceJet.proj, add_mul, Finset.sum_add_distrib, Finset.mul_sum]
    congr 1
    · simp
    · exact Finset.sum_congr rfl (fun d _ => by ring)
  rw [h1, hn]; ring

lemma covDeriv_antisym (J : SliceJet) (hJ : J.Valid) (c d : Fin 4) :
    (J.covDeriv c d - J.covDeriv d c) / 2 =
      (J.dN c * J.nCov d - J.dN d * J.nCov c) / (2 * J.N) := by
  obtain ⟨hN, hH, hG, -⟩ := hJ
  have hs : ∑ e, J.Gam e c d * J.nCov e = ∑ e, J.Gam e d c * J.nCov e :=
    Finset.sum_congr rfl (fun e _ => by rw [hG e c d])
  simp only [SliceJet.covDeriv]
  rw [hH c d, hs]
  simp only [SliceJet.nCov]
  field_simp
  ring

theorem frobenius_vort_zero (J : SliceJet) (hJ : J.Valid) (a b : Fin 4) : J.vort a b = 0 := by
  have key : J.vort a b = ((∑ c, J.proj a c * J.dN c) * (∑ d, J.proj b d * J.nCov d)
      - (∑ c, J.proj a c * J.nCov c) * (∑ d, J.proj b d * J.dN d)) / (2 * J.N) := by
    simp only [SliceJet.vort, covDeriv_antisym J hJ]
    rw [Finset.sum_mul_sum, Finset.sum_mul_sum, ← Finset.sum_sub_distrib, Finset.sum_div]
    refine Finset.sum_congr rfl (fun c _ => ?_)
    rw [← Finset.sum_sub_distrib, Finset.sum_div]
    refine Finset.sum_congr rfl (fun d _ => ?_)
    ring
  rw [key, proj_n J hJ a, proj_n J hJ b]; ring

theorem W2n_zero (J : SliceJet) (hJ : J.Valid) (H : ℝ) : W2n J H = 0 := by
  simp [W2n, SliceJet.vortSq, frobenius_vort_zero J hJ]

/-- Comoving jet: N = 1, t-gradient e⁰, n_a = −e⁰, n^a = e₀, flat connection. -/
def canonJet : SliceJet where
  N := 1
  dt := ![1, 0, 0, 0]
  dN := fun _ => 0
  hessT := fun _ _ => 0
  Gam := fun _ _ _ => 0
  nUp := ![1, 0, 0, 0]
  gInv := fun a b => if a = b then (if a = 0 then -1 else 1) else 0

theorem canonJet_valid : canonJet.Valid := by
  refine ⟨by norm_num [canonJet], fun _ _ => rfl, fun _ _ _ => rfl, ?_⟩
  simp [SliceJet.nCov, canonJet, Fin.sum_univ_four]

/-- Negative control: a non-integrable "normal" (antisymmetric part in the would-be Hessian). -/
def badJet : SliceJet where
  N := 1
  dt := ![1, 0, 0, 0]
  dN := fun _ => 0
  hessT := fun c d => if c = 1 ∧ d = 2 then 1 else 0
  Gam := fun _ _ _ => 0
  nUp := ![1, 0, 0, 0]
  gInv := fun a b => if a = b then (if a = 0 then -1 else 1) else 0

theorem badJet_partial_valid :
    badJet.N ≠ 0 ∧ (∀ e c d, badJet.Gam e c d = badJet.Gam e d c) ∧
      ∑ a, badJet.nUp a * badJet.nCov a = -1 ∧ badJet.hessT 1 2 ≠ badJet.hessT 2 1 := by
  refine ⟨by norm_num [badJet], fun _ _ _ => rfl, ?_, ?_⟩
  · simp [SliceJet.nCov, badJet, Fin.sum_univ_four]
  · simp [badJet]

theorem badJet_vort_ne : badJet.vort 1 2 = -1/2 ∧ badJet.vort 1 2 ≠ 0 := by
  have h : badJet.vort 1 2 = -1/2 := by
    simp [SliceJet.vort, SliceJet.proj, SliceJet.covDeriv, SliceJet.nCov, badJet,
      Fin.sum_univ_four]
    norm_num
  exact ⟨h, by rw [h]; norm_num⟩

/-! ## Part D — declared constraint-level class; typed candidate maps -/

/-- PR-187 frame tags; the comparator vector of a datum is typed in the n-frame. -/
inductive Frame
  | n
  | u
  | obs

structure FrameG (f : Frame) where
  g : CompVec

/-- Instantaneous homogeneous Bianchi I/V datum (source class). -/
structure HomData where
  H : ℝ
  a : ℝ
  s1 : ℝ
  s2 : ℝ
  s3 : ℝ
  w : ℝ
  mus : ℝ
  beta : ℝ
  d : Fin 3 → ℝ
  Lam : ℝ
  kap : ℝ
  nab : Fin 3 → Fin 3 → ℝ
  jet : SliceJet

namespace HomData

/-- a_i = (a, 0, 0). -/
def avec (D : HomData) : Fin 3 → ℝ := ![D.a, 0, 0]
def sdiag (D : HomData) : Fin 3 → ℝ := ![D.s1, D.s2, D.s3]
/-- `a_b σ^{ab}` for diagonal σ. -/
def aSigma (D : HomData) (i : Fin 3) : ℝ := D.avec i * D.sdiag i
def Sigma2 (D : HomData) : ℝ := (D.s1 ^ 2 + D.s2 ^ 2 + D.s3 ^ 2) / (6 * D.H ^ 2)
def R3 (D : HomData) : ℝ := -6 * D.a ^ 2
def Ok (D : HomData) : ℝ := -D.R3 / (6 * D.H ^ 2)
def rhoN (D : HomData) : ℝ := streamEnergy D.mus D.w D.beta + streamEnergy D.mus D.w (-D.beta)
def Om (D : HomData) : ℝ := D.kap * (2 * D.mus) / (3 * D.H ^ 2)
def Otilt (D : HomData) : ℝ := D.kap * (D.rhoN - 2 * D.mus) / (3 * D.H ^ 2)
def OL (D : HomData) : ℝ := D.Lam / (3 * D.H ^ 2)
def W2 (D : HomData) : ℝ := W2n D.jet D.H
def flux (D : HomData) (i : Fin 3) : ℝ :=
  (streamFlux D.mus D.w D.beta + streamFlux D.mus D.w (-D.beta)) * D.d i

def Domain (D : HomData) : Prop :=
  0 < D.H ∧ 0 < D.kap ∧ 0 ≤ D.mus ∧ -1 ≤ D.w ∧ D.w ≤ 1 ∧ D.s1 + D.s2 + D.s3 = 0 ∧
    ∑ i, D.d i ^ 2 = 1 ∧ D.jet.Valid ∧ ∀ i j, D.nab i j = 0

/-- Normalized Gauss constraint (`egs3_nonlinear_realization.py:139-140`). -/
def Gauss (D : HomData) : Prop := D.Om + D.OL + D.Ok + D.Otilt + D.Sigma2 - D.W2 = 1

/-- (0i) momentum constraint `k a_bσ^{ab} + κ q^a = 0` (source: k = 3). -/
def Momentum (k : ℝ) (D : HomData) : Prop := ∀ i, k * D.aSigma i + D.kap * D.flux i = 0

/-- Jacobi `n^{ab} a_b = 0`. -/
def Jacobi (D : HomData) : Prop := ∀ i, ∑ b, D.nab i b * D.avec b = 0

def ConstraintOK (k : ℝ) (D : HomData) : Prop :=
  D.Domain ∧ D.Gauss ∧ D.Momentum k ∧ D.Jacobi

/-- Comparator vector of the datum (slice-normal W²). -/
def invariants (D : HomData) : CompVec := ⟨D.Sigma2, D.W2, D.Otilt, D.Ok⟩

def invariantsN (D : HomData) : FrameG .n := ⟨D.invariants⟩

theorem W2_zero (D : HomData) (hJ : D.jet.Valid) : D.W2 = 0 := W2n_zero D.jet hJ D.H

theorem Otilt_eq (D : HomData) : D.Otilt = tiltPair .fixedTotal D.w D.Om D.beta := by
  simp only [Otilt, rhoN, pair_energy_eq, tiltPair, tiltSingle, Om]; ring

lemma flux_zero (D : HomData) (i : Fin 3) : D.flux i = 0 := by
  simp [flux, pair_flux_cancel]

lemma aSigma_vals (D : HomData) :
    D.aSigma 0 = D.a * D.s1 ∧ D.aSigma 1 = 0 ∧ D.aSigma 2 = 0 := by
  simp [aSigma, avec, sdiag]

theorem momentum_iff_transverse (k : ℝ) (hk : k ≠ 0) (D : HomData) :
    D.Momentum k ↔ D.a * D.s1 = 0 := by
  obtain ⟨h0, h1, h2⟩ := aSigma_vals D
  constructor
  · intro h
    have h' := h 0
    rw [flux_zero, h0, mul_zero, add_zero] at h'
    exact (mul_eq_zero.1 h').resolve_left hk
  · intro h i
    rw [flux_zero, mul_zero, add_zero]
    fin_cases i
    · simp [h0, h]
    · simp [h1]
    · simp [h2]

theorem posBlock (k : ℝ) (D : HomData) (hD : D.ConstraintOK k) :
    PosBlock D.invariants ∧ 0 ≤ D.invariants.Ok := by
  obtain ⟨⟨hH, hk, hm, hw, -, -, -, hJ, -⟩, -⟩ := hD
  have hH2 : 0 < D.H ^ 2 := by positivity
  refine ⟨⟨?_, ?_, ?_⟩, ?_⟩
  · show 0 ≤ D.Sigma2
    unfold Sigma2; positivity
  · show 0 ≤ D.W2
    rw [W2_zero D hJ]
  · show 0 ≤ D.Otilt
    rw [Otilt_eq]; simp only [tiltPair, tiltSingle, Om]
    have : 0 ≤ 1 + D.w := by linarith
    positivity
  · show 0 ≤ D.Ok
    unfold Ok R3; rw [neg_mul, neg_neg]; positivity

end HomData

/-- Background parameters (H, w, Ω_m, κ) of the candidate map. -/
structure Background where
  H : ℝ
  w : ℝ
  Om : ℝ
  kap : ℝ

def Background.Valid (P : Background) : Prop :=
  0 < P.H ∧ -1 < P.w ∧ P.w ≤ 1 ∧ 0 < P.Om ∧ 0 < P.kap

/-- Face of comparator vectors reachable in the slice-normal class. -/
def NormalFace (g : CompVec) : Prop := g.W2 = 0 ∧ 0 ≤ g.Sigma2 ∧ 0 ≤ g.Otilt ∧ 0 ≤ g.Ok

/-- Typed candidate map: comparator vector ↦ Bianchi I/V datum (transverse shear
diag(0, s, −s), structure parameter a = H√Ω_k, aligned antipodal pair, Λ from Gauss). -/
def candidate (P : Background) (g : CompVec) : HomData where
  H := P.H
  a := P.H * √g.Ok
  s1 := 0
  s2 := P.H * √(3 * g.Sigma2)
  s3 := -(P.H * √(3 * g.Sigma2))
  w := P.w
  mus := 3 * P.H ^ 2 * P.Om / (2 * P.kap)
  beta := arsinh √(g.Otilt / ((1 + P.w) * P.Om))
  d := ![1, 0, 0]
  Lam := 3 * P.H ^ 2 * (1 - P.Om - xC g)
  kap := P.kap
  nab := fun _ _ => 0
  jet := canonJet

theorem candidate_Om (P : Background) (hP : P.Valid) (g : CompVec) :
    (candidate P g).Om = P.Om := by
  obtain ⟨hH, -, -, -, hk⟩ := hP
  simp only [HomData.Om, candidate]
  field_simp

theorem candidate_OL (P : Background) (hP : P.Valid) (g : CompVec) :
    (candidate P g).OL = 1 - P.Om - xC g := by
  obtain ⟨hH, -, -, -, -⟩ := hP
  simp only [HomData.OL, candidate]
  field_simp

theorem candidate_invariants (P : Background) (hP : P.Valid) (g : CompVec) (hg : NormalFace g) :
    (candidate P g).invariants = g := by
  obtain ⟨hW, hS, hT, hK⟩ := hg
  have hP' := hP
  obtain ⟨hH, hw, -, hOm, hk⟩ := hP
  have hH0 : P.H ≠ 0 := hH.ne'
  apply CompVec.ext
  · show (candidate P g).Sigma2 = g.Sigma2
    simp only [HomData.Sigma2, candidate]
    have e : (P.H * √(3 * g.Sigma2)) ^ 2 = P.H ^ 2 * (3 * g.Sigma2) := by
      rw [mul_pow, Real.sq_sqrt (by linarith)]
    rw [neg_sq, e]
    field_simp
    ring
  · show (candidate P g).W2 = g.W2
    rw [HomData.W2_zero _ canonJet_valid, hW]
  · show (candidate P g).Otilt = g.Otilt
    rw [HomData.Otilt_eq, candidate_Om P hP' g]
    simp only [tiltPair, tiltSingle, candidate, Real.sinh_arsinh]
    have hpos : 0 < (1 + P.w) * P.Om := mul_pos (by linarith) hOm
    rw [Real.sq_sqrt (div_nonneg hT hpos.le)]
    field_simp
  · show (candidate P g).Ok = g.Ok
    simp only [HomData.Ok, HomData.R3, candidate]
    rw [mul_pow, Real.sq_sqrt hK]
    field_simp

theorem candidate_constraintOK (k : ℝ) (P : Background) (hP : P.Valid) (g : CompVec)
    (hg : NormalFace g) : (candidate P g).ConstraintOK k := by
  have hinv := candidate_invariants P hP g hg
  have hP' := hP
  obtain ⟨hH, hw, hw1, hOm, hk⟩ := hP
  refine ⟨⟨hH, hk, ?_, hw.le, hw1, ?_, ?_, canonJet_valid, fun _ _ => rfl⟩, ?_, ?_, ?_⟩
  · show 0 ≤ 3 * P.H ^ 2 * P.Om / (2 * P.kap)
    positivity
  · show (0 : ℝ) + P.H * √(3 * g.Sigma2) + -(P.H * √(3 * g.Sigma2)) = 0
    ring
  · show ∑ i, (![1, 0, 0] : Fin 3 → ℝ) i ^ 2 = 1
    simp [Fin.sum_univ_three]
  · -- Gauss
    have hS : (candidate P g).Sigma2 = g.Sigma2 := congrArg CompVec.Sigma2 hinv
    have hW : (candidate P g).W2 = g.W2 := congrArg CompVec.W2 hinv
    have hT : (candidate P g).Otilt = g.Otilt := congrArg CompVec.Otilt hinv
    have hK : (candidate P g).Ok = g.Ok := congrArg CompVec.Ok hinv
    show (candidate P g).Om + (candidate P g).OL + (candidate P g).Ok + (candidate P g).Otilt
      + (candidate P g).Sigma2 - (candidate P g).W2 = 1
    rw [candidate_Om P hP' g, candidate_OL P hP' g, hS, hW, hT, hK]
    unfold xC; ring
  · -- momentum: transverse shear (s1 = 0) and antipodal pair
    intro i
    rw [HomData.flux_zero, mul_zero, add_zero]
    have h0 := (HomData.aSigma_vals (candidate P g))
    fin_cases i
    · simp [h0.1, candidate]
    · simp [h0.2.1]
    · simp [h0.2.2]
  · intro i
    simp [candidate]

theorem candidate_typeI_iff (P : Background) (hP : P.Valid) (g : CompVec) (hg : NormalFace g) :
    (candidate P g).a = 0 ↔ g.Ok = 0 := by
  obtain ⟨hH, -, -, -, -⟩ := hP
  obtain ⟨-, -, -, hK⟩ := hg
  show P.H * √g.Ok = 0 ↔ g.Ok = 0
  rw [mul_eq_zero, Real.sqrt_eq_zero hK]
  constructor
  · rintro (h | h)
    · exact absurd h hH.ne'
    · exact h
  · intro h; exact Or.inr h

/-- Non-vacuity background: H = 1, dust, Ω_m = 3/10, κ = 1. -/
def regBackground : Background := ⟨1, 0, 3/10, 1⟩

theorem regBackground_valid : regBackground.Valid := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> norm_num [regBackground]

theorem realizable_iff_normalFace (k : ℝ) (g : CompVec) :
    (∃ D : HomData, D.ConstraintOK k ∧ D.invariants = g) ↔ NormalFace g := by
  constructor
  · rintro ⟨D, hD, rfl⟩
    obtain ⟨⟨h1, -, h3⟩, h4⟩ := HomData.posBlock k D hD
    exact ⟨HomData.W2_zero D hD.1.2.2.2.2.2.2.1, h1, h3, h4⟩
  · intro hg
    exact ⟨candidate regBackground g, candidate_constraintOK k _ regBackground_valid g hg,
      candidate_invariants _ regBackground_valid g hg⟩

/-! ## Part E — separate sharpness predicates -/

def ConstraintAttained (k : ℝ) (B : CBox) (x : ℝ) : Prop :=
  ∃ D : HomData, D.ConstraintOK k ∧ InBox B D.invariants ∧ xC D.invariants = x

/-- Typed evolution system on an encoded state space. -/
structure EvolSys where
  m : ℕ
  enc : HomData → (Fin m → ℝ)
  F : (Fin m → ℝ) → (Fin m → ℝ)
  Cons : (Fin m → ℝ) → Prop
  Dom : (Fin m → ℝ) → Prop

def LocalDev (S : EvolSys) (D : HomData) : Prop :=
  ∃ ε > 0, ∃ γ : ℝ → (Fin S.m → ℝ), γ 0 = S.enc D ∧
    ∀ t ∈ Set.Ioo (-ε) ε, HasDerivAt γ (S.F (γ t)) t ∧ S.Cons (γ t) ∧ S.Dom (γ t)

def GlobalDev (S : EvolSys) (T : ℝ) (D : HomData) : Prop :=
  0 < T ∧ ∃ γ : ℝ → (Fin S.m → ℝ), γ 0 = S.enc D ∧
    ∀ t ∈ Set.Icc 0 T, HasDerivWithinAt γ (S.F (γ t)) (Set.Icc 0 T) t ∧ S.Cons (γ t) ∧
      S.Dom (γ t)

def LocalAttained (k : ℝ) (S : EvolSys) (B : CBox) (x : ℝ) : Prop :=
  ∃ D : HomData, D.ConstraintOK k ∧ InBox B D.invariants ∧ xC D.invariants = x ∧ LocalDev S D

def GlobalAttained (k : ℝ) (S : EvolSys) (T : ℝ) (B : CBox) (x : ℝ) : Prop :=
  ∃ D : HomData, D.ConstraintOK k ∧ InBox B D.invariants ∧ xC D.invariants = x ∧
    LocalDev S D ∧ GlobalDev S T D

/-- The registered PR-190 statement: every comparator value of the box interval is
dynamically attained in the declared class. -/
def FullDynSharp (k : ℝ) (S : EvolSys) (T : ℝ) (B : CBox) : Prop :=
  ∀ x, xC (cornerPoint B .lower) ≤ x → x ≤ xC (cornerPoint B .upper) → GlobalAttained k S T B x

theorem ladder (k : ℝ) (S : EvolSys) (T : ℝ) (B : CBox) (x : ℝ) :
    (GlobalAttained k S T B x → LocalAttained k S B x) ∧
    (LocalAttained k S B x → ConstraintAttained k B x) ∧
    (ConstraintAttained k B x → AlgebraicAttained B x) := by
  refine ⟨?_, ?_, ?_⟩
  · rintro ⟨D, h1, h2, h3, h4, -⟩; exact ⟨D, h1, h2, h3, h4⟩
  · rintro ⟨D, h1, h2, h3, -⟩; exact ⟨D, h1, h2, h3⟩
  · rintro ⟨D, h1, h2, h3⟩; exact ⟨D.invariants, h2, (HomData.posBlock k D h1).1, h3⟩

/-! ## Part D (cont.) — registered box: exact constraint-level image -/

def regFaceVector (x : ℝ) : CompVec := ⟨12/100, 0, 3/100, x - 15/100⟩

theorem constraint_image_reg (k x : ℝ) :
    ConstraintAttained k regBox x ↔ 15/100 ≤ x ∧ x ≤ 17/100 := by
  constructor
  · rintro ⟨D, hD, hbox, hx⟩
    have hW : D.invariants.W2 = 0 := HomData.W2_zero D hD.1.2.2.2.2.2.2.1
    obtain ⟨⟨h1, h2⟩, -, ⟨h3, h4⟩, ⟨h5, h6⟩⟩ := hbox
    simp only [regBox] at h1 h2 h3 h4 h5 h6
    unfold xC at hx
    constructor <;> linarith
  · rintro ⟨hlo, hhi⟩
    have hg : NormalFace (regFaceVector x) := by
      refine ⟨rfl, ?_, ?_, ?_⟩ <;> simp only [regFaceVector] <;> linarith
    refine ⟨candidate regBackground (regFaceVector x),
      candidate_constraintOK k _ regBackground_valid _ hg, ?_, ?_⟩
    · rw [candidate_invariants _ regBackground_valid _ hg]
      refine ⟨⟨?_, ?_⟩, ⟨?_, ?_⟩, ⟨?_, ?_⟩, ⟨?_, ?_⟩⟩ <;> simp only [regFaceVector, regBox] <;>
        linarith
    · rw [candidate_invariants _ regBackground_valid _ hg]
      unfold xC regFaceVector; ring

theorem lower_not_constraint_attained (k : ℝ) : ¬ ConstraintAttained k regBox (11/100) := by
  rw [constraint_image_reg]; norm_num

theorem interior_challenge_not_attained (k : ℝ) : ¬ ConstraintAttained k regBox (12/100) := by
  rw [constraint_image_reg]; norm_num

theorem upper_constraint_attained (k : ℝ) : ConstraintAttained k regBox (17/100) := by
  rw [constraint_image_reg]; norm_num

theorem no_data_realizes_lower (D : HomData) (hJ : D.jet.Valid) :
    D.invariants ≠ cornerPoint regBox .lower := by
  intro h
  have h1 : D.invariants.W2 = (cornerPoint regBox .lower).W2 := congrArg CompVec.W2 h
  rw [reg_corners.1] at h1
  have h2 : D.invariants.W2 = 0 := HomData.W2_zero D hJ
  rw [h2] at h1; norm_num at h1

theorem joint_strictly_inside_product (k : ℝ) :
    (∀ x, ConstraintAttained k regBox x → AlgebraicAttained regBox x) ∧
    ∃ x, AlgebraicAttained regBox x ∧ ¬ ConstraintAttained k regBox x := by
  refine ⟨fun x hx => (ladder k ⟨0, fun _ => 0, fun _ => 0, fun _ => True, fun _ => True⟩ 1
    regBox x).2.2 hx, 11/100, ?_, lower_not_constraint_attained k⟩
  rw [reg_algebraic_iff]; norm_num

theorem full_dyn_sharp_refuted (k : ℝ) (S : EvolSys) (T : ℝ) : ¬ FullDynSharp k S T regBox := by
  intro h
  have hx := h (11/100) (by rw [reg_corners.2.2.1]) (by rw [reg_corners.2.2.2]; norm_num)
  exact lower_not_constraint_attained k
    ((ladder k S T regBox _).2.1 ((ladder k S T regBox _).1 hx))

theorem lower_not_local (k : ℝ) (S : EvolSys) : ¬ LocalAttained k S regBox (11/100) :=
  fun h => lower_not_constraint_attained k ((ladder k S 1 regBox _).2.1 h)

theorem lower_not_global (k : ℝ) (S : EvolSys) (T : ℝ) :
    ¬ GlobalAttained k S T regBox (11/100) :=
  fun h => lower_not_local k S ((ladder k S T regBox _).1 h)

/-! ## Typed candidate maps on sign corners and comparator values -/

open Classical in
def cornerData (P : Background) (B : CBox) (c : Corner) : Option HomData :=
  if NormalFace (cornerPoint B c) then some (candidate P (cornerPoint B c)) else none

theorem cornerData_sound (k : ℝ) (P : Background) (hP : P.Valid) (B : CBox) (c : Corner)
    (D : HomData) (h : cornerData P B c = some D) :
    D.invariants = cornerPoint B c ∧ D.ConstraintOK k := by
  unfold cornerData at h
  split_ifs at h with hf
  cases h
  exact ⟨candidate_invariants P hP _ hf, candidate_constraintOK k P hP _ hf⟩

theorem cornerData_complete (k : ℝ) (P : Background) (B : CBox) (c : Corner)
    (h : cornerData P B c = none) :
    ¬ ∃ D : HomData, D.ConstraintOK k ∧ D.invariants = cornerPoint B c := by
  rw [realizable_iff_normalFace]
  intro hf
  unfold cornerData at h
  rw [if_pos hf] at h
  cases h

theorem cornerData_reg (P : Background) :
    cornerData P regBox .lower = none ∧
    cornerData P regBox .upper = some (candidate P (cornerPoint regBox .upper)) := by
  constructor
  · unfold cornerData
    rw [if_neg]
    rw [reg_corners.1]
    rintro ⟨h, -⟩
    norm_num at h
  · unfold cornerData
    rw [if_pos]
    rw [reg_corners.2.1]
    refine ⟨rfl, ?_, ?_, ?_⟩ <;> norm_num

open Classical in
def valueData (P : Background) (x : ℝ) : Option HomData :=
  if 15/100 ≤ x ∧ x ≤ 17/100 then some (candidate P (regFaceVector x)) else none

theorem valueData_sound (k : ℝ) (P : Background) (hP : P.Valid) (x : ℝ) (D : HomData)
    (h : valueData P x = some D) :
    D.ConstraintOK k ∧ InBox regBox D.invariants ∧ xC D.invariants = x := by
  unfold valueData at h
  split_ifs at h with hx
  cases h
  obtain ⟨hlo, hhi⟩ := hx
  have hg : NormalFace (regFaceVector x) := by
    refine ⟨rfl, ?_, ?_, ?_⟩ <;> simp only [regFaceVector] <;> linarith
  refine ⟨candidate_constraintOK k P hP _ hg, ?_, ?_⟩
  · rw [candidate_invariants P hP _ hg]
    refine ⟨⟨?_, ?_⟩, ⟨?_, ?_⟩, ⟨?_, ?_⟩, ⟨?_, ?_⟩⟩ <;> simp only [regFaceVector, regBox] <;>
      linarith
  · rw [candidate_invariants P hP _ hg]
    unfold xC regFaceVector; ring

theorem valueData_complete (k : ℝ) (P : Background) (x : ℝ) (h : valueData P x = none) :
    ¬ ConstraintAttained k regBox x := by
  rw [constraint_image_reg]
  intro hx
  unfold valueData at h
  rw [if_pos hx] at h
  cases h

theorem upper_witness_explicit :
    regBackground.Valid ∧
    (candidate regBackground (cornerPoint regBox .upper)).ConstraintOK 3 ∧
    (candidate regBackground (cornerPoint regBox .upper)).invariants = cornerPoint regBox .upper ∧
    (candidate regBackground (cornerPoint regBox .upper)).a ≠ 0 ∧
    (candidate regBackground (cornerPoint regBox .upper)).OL = 53/100 := by
  have hf : NormalFace (cornerPoint regBox .upper) := by
    rw [reg_corners.2.1]; refine ⟨rfl, ?_, ?_, ?_⟩ <;> norm_num
  refine ⟨regBackground_valid, candidate_constraintOK 3 _ regBackground_valid _ hf,
    candidate_invariants _ regBackground_valid _ hf, ?_, ?_⟩
  · intro h
    rw [candidate_typeI_iff _ regBackground_valid _ hf, reg_corners.2.1] at h
    norm_num at h
  · rw [candidate_OL _ regBackground_valid, reg_corners.2.2.2]; norm_num [regBackground]

theorem candidate_reg_OL_pos (x : ℝ) (hlo : 15/100 ≤ x) (hhi : x ≤ 17/100) :
    0 < (candidate regBackground (regFaceVector x)).OL := by
  rw [candidate_OL _ regBackground_valid]
  unfold xC regFaceVector regBackground
  dsimp only
  linarith

end R190A
