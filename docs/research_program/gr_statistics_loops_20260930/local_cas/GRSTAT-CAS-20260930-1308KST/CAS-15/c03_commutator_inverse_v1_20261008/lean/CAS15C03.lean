import Mathlib

/-!
CAS-15-C03, finite diagonal-basis component.  A skew 3 by 3 matrix is
represented by its independent (12,13,23) entries.  A symmetric off-diagonal
matrix uses the same three entries.  Both Frobenius norms square to twice the
sum of the three coordinate squares.  The diagonal residual is separate.
-/

namespace CAS15C03

abbrev V := Fin 3 → ℝ

def sq (x : V) : ℝ := x 0 ^ 2 + x 1 ^ 2 + x 2 ^ 2

def cm (g x : V) : V := fun i => g i * x i

def gap (m : V) : ℝ := min (|m 0 - m 1|) (min (|m 0 - m 2|) (|m 1 - m 2|))

def coeff (m : V) : V :=
  ![m 0 - m 1, m 0 - m 2, m 1 - m 2]

theorem sqv_nonneg (x : V) : 0 ≤ sq x := by
  dsimp [sq]
  positivity

theorem sq_eq_zero_iff (x : V) : sq x = 0 ↔ x = 0 := by
  constructor
  · intro h
    have h0 : x 0 ^ 2 = 0 := by
      dsimp [sq] at h
      nlinarith [sq_nonneg (x 1), sq_nonneg (x 2)]
    have h1 : x 1 ^ 2 = 0 := by
      dsimp [sq] at h
      nlinarith [sq_nonneg (x 0), sq_nonneg (x 2)]
    have h2 : x 2 ^ 2 = 0 := by
      dsimp [sq] at h
      nlinarith [sq_nonneg (x 0), sq_nonneg (x 1)]
    have hx0 : x 0 = 0 := by nlinarith [h0]
    have hx1 : x 1 = 0 := by nlinarith [h1]
    have hx2 : x 2 = 0 := by nlinarith [h2]
    ext i
    fin_cases i
    all_goals simp [hx0, hx1, hx2]
  · intro h
    subst x
    norm_num [sq]

theorem cm_apply (g x : V) (i : Fin 3) : cm g x i = g i * x i := rfl

theorem sq_cm (g x : V) :
    sq (cm g x) =
      (g 0)^2 * (x 0)^2 + (g 1)^2 * (x 1)^2 + (g 2)^2 * (x 2)^2 := by
  simp only [sq, cm]
  ring

theorem gap_le_abs01 (m : V) : gap m ≤ |m 0 - m 1| := by
  exact min_le_left _ _

theorem gap_le_abs02 (m : V) : gap m ≤ |m 0 - m 2| := by
  exact le_trans (min_le_right _ _) (min_le_left _ _)

theorem gap_le_abs12 (m : V) : gap m ≤ |m 1 - m 2| := by
  exact le_trans (min_le_right _ _) (min_le_right _ _)

theorem gap_nonneg (m : V) : 0 ≤ gap m := by
  exact le_min (abs_nonneg _) (le_min (abs_nonneg _) (abs_nonneg _))

theorem gap_pos_components (m : V) (h : 0 < gap m) :
    m 0 - m 1 ≠ 0 ∧ m 0 - m 2 ≠ 0 ∧ m 1 - m 2 ≠ 0 := by
  constructor
  · intro hz
    have : |m 0 - m 1| = 0 := by rw [hz]; simp
    linarith [gap_le_abs01 m]
  constructor
  · intro hz
    have : |m 0 - m 2| = 0 := by rw [hz]; simp
    linarith [gap_le_abs02 m]
  · intro hz
    have : |m 1 - m 2| = 0 := by rw [hz]; simp
    linarith [gap_le_abs12 m]

noncomputable def inverse (m r : V) : V :=
  ![r 0 / (m 0 - m 1), r 1 / (m 0 - m 2), r 2 / (m 1 - m 2)]

theorem cm_inverse (m r : V) (h : 0 < gap m) :
    cm (coeff m) (inverse m r) = r := by
  rcases gap_pos_components m h with ⟨h01, h02, h12⟩
  ext i
  fin_cases i
  · change (m 0 - m 1) * (r 0 / (m 0 - m 1)) = r 0
    field_simp
  · change (m 0 - m 2) * (r 1 / (m 0 - m 2)) = r 1
    field_simp
  · change (m 1 - m 2) * (r 2 / (m 1 - m 2)) = r 2
    field_simp

theorem inverse_cm (m x : V) (h : 0 < gap m) :
    inverse m (cm (coeff m) x) = x := by
  rcases gap_pos_components m h with ⟨h01, h02, h12⟩
  ext i
  fin_cases i
  all_goals simp [cm, coeff, inverse, h01, h02, h12]

theorem kernel_zero (m x : V) (h : 0 < gap m)
    (hx : cm (coeff m) x = 0) : x = 0 := by
  calc
    x = inverse m (cm (coeff m) x) := (inverse_cm m x h).symm
    _ = 0 := by simpa [hx, inverse]

theorem unique_inverse (m r x : V) (h : 0 < gap m)
    (hx : cm (coeff m) x = r) : x = inverse m r := by
  calc
    x = inverse m (cm (coeff m) x) := (inverse_cm m x h).symm
    _ = inverse m r := by rw [hx]

theorem commutator_entry (m : V) (w : Fin 3 → Fin 3 → ℝ)
    (i j : Fin 3) :
    (m i * w i j - w i j * m j) = (m i - m j) * w i j := by ring

theorem diagonal_residual (m : V) (w : Fin 3 → Fin 3 → ℝ)
    (i : Fin 3) : m i * w i i - w i i * m i = 0 := by ring

theorem sq_gap (m x : V) (h : 0 ≤ gap m) :
    (gap m)^2 * sq x ≤ sq (cm (coeff m) x) := by
  have h0 : (gap m)^2 ≤ (m 0 - m 1)^2 := by
    nlinarith [gap_le_abs01 m, abs_nonneg (m 0 - m 1),
      sq_abs (m 0 - m 1)]
  have h1 : (gap m)^2 ≤ (m 0 - m 2)^2 := by
    nlinarith [gap_le_abs02 m, abs_nonneg (m 0 - m 2), sq_abs (m 0 - m 2)]
  have h2 : (gap m)^2 ≤ (m 1 - m 2)^2 := by
    nlinarith [gap_le_abs12 m, abs_nonneg (m 1 - m 2), sq_abs (m 1 - m 2)]
  have h0' := mul_le_mul_of_nonneg_right h0 (sq_nonneg (x 0))
  have h1' := mul_le_mul_of_nonneg_right h1 (sq_nonneg (x 1))
  have h2' := mul_le_mul_of_nonneg_right h2 (sq_nonneg (x 2))
  change (gap m)^2 * (x 0 ^ 2 + x 1 ^ 2 + x 2 ^ 2) ≤
    ((m 0 - m 1) * x 0)^2 +
    ((m 0 - m 2) * x 1)^2 +
    ((m 1 - m 2) * x 2)^2
  nlinarith

theorem repeated01_kernel (m : V) (h : m 0 = m 1) :
    cm (coeff m) (![1,0,0] : V) = 0 ∧ (![1,0,0] : V) ≠ 0 := by
  constructor
  · ext i
    fin_cases i
    all_goals simp [cm, coeff, h]
  · intro hz
    have := congrArg (fun v : V => v 0) hz
    norm_num at this

theorem repeated02_kernel (m : V) (h : m 0 = m 2) :
    cm (coeff m) (![0,1,0] : V) = 0 ∧ (![0,1,0] : V) ≠ 0 := by
  constructor
  · ext i
    fin_cases i
    all_goals simp [cm, coeff, h]
  · intro hz
    have := congrArg (fun v : V => v 1) hz
    norm_num at this

theorem repeated12_kernel (m : V) (h : m 1 = m 2) :
    cm (coeff m) (![0,0,1] : V) = 0 ∧ (![0,0,1] : V) ≠ 0 := by
  constructor
  · ext i
    fin_cases i
    all_goals simp [cm, coeff, h]
  · intro hz
    have := congrArg (fun v : V => v 2) hz
    simp at this

theorem isotropic_zero (c : ℝ) (x : V) :
    cm (coeff (![c,c,c] : V)) x = 0 := by
  ext i
  fin_cases i
  all_goals simp [cm, coeff]

def commLinear (m : V) : V →ₗ[ℝ] V where
  toFun := cm (coeff m)
  map_add' := by
    intro x y
    ext i
    simp [cm, mul_add]
  map_smul' := by
    intro c x
    ext i
    simp [cm, mul_left_comm, mul_comm]

theorem commLinear_injective (m : V) (h : 0 < gap m) :
    Function.Injective (commLinear m) := by
  intro x y hxy
  apply (inverse_cm m x h).symm.trans
  rw [show cm (coeff m) x = cm (coeff m) y from hxy]
  exact inverse_cm m y h

theorem commLinear_rank_three (m : V) (h : 0 < gap m) :
    Module.finrank ℝ (LinearMap.range (commLinear m)) = 3 := by
  rw [LinearMap.finrank_range_of_inj (commLinear_injective m h)]
  simp [V]

def loss (m r d x : V) : ℝ :=
  2 * sq (cm (coeff m) x - r) + sq d

theorem loss_at_inverse (m r d : V) (h : 0 < gap m) :
    loss m r d (inverse m r) = sq d := by
  simp [loss, cm_inverse m r h, sq]

theorem least_squares_minimal (m r d x : V) (h : 0 < gap m) :
    loss m r d (inverse m r) ≤ loss m r d x := by
  rw [loss_at_inverse m r d h]
  dsimp [loss]
  linarith [sqv_nonneg (cm (coeff m) x - r)]

theorem least_squares_unique (m r d x : V) (h : 0 < gap m)
    (heq : loss m r d x = loss m r d (inverse m r)) :
    x = inverse m r := by
  have hsq : sq (cm (coeff m) x - r) = 0 := by
    rw [loss_at_inverse m r d h] at heq
    dsimp [loss] at heq
    linarith
  have hzero := (sq_eq_zero_iff _).mp hsq
  have hfit : cm (coeff m) x = r := sub_eq_zero.mp hzero
  exact unique_inverse m r x h hfit

theorem ordered_pair_gap (a b ah bh e : ℝ)
    (ha : |ah - a| ≤ e) (hb : |bh - b| ≤ e) :
    |a - b| - 2 * e ≤ |ah - bh| := by
  have ha' := abs_le.mp ha
  have hb' := abs_le.mp hb
  have hpos := le_abs_self (ah - bh)
  have hneg := neg_abs_le (ah - bh)
  have hab : |a - b| ≤ |ah - bh| + 2 * e := by
    apply abs_le.mpr
    constructor <;> rcases ha' with ⟨haLo, haHi⟩
    · rcases hb' with ⟨hbLo, hbHi⟩
      linarith
    · rcases hb' with ⟨hbLo, hbHi⟩
      linarith
  linarith

theorem ordered_gap_bound (m mh : V) (e : ℝ)
    (hmatch : ∀ i : Fin 3, |mh i - m i| ≤ e) :
    gap m - 2 * e ≤ gap mh := by
  have h01 := ordered_pair_gap (m 0) (m 1) (mh 0) (mh 1) e (hmatch 0) (hmatch 1)
  have h02 := ordered_pair_gap (m 0) (m 2) (mh 0) (mh 2) e (hmatch 0) (hmatch 2)
  have h12 := ordered_pair_gap (m 1) (m 2) (mh 1) (mh 2) e (hmatch 1) (hmatch 2)
  dsimp [gap]
  exact le_min (le_trans (sub_le_sub_right (min_le_left _ _) _) h01)
    (le_min
      (le_trans (sub_le_sub_right (le_trans (min_le_right _ _) (min_le_left _ _)) _) h02)
      (le_trans (sub_le_sub_right (le_trans (min_le_right _ _) (min_le_right _ _)) _) h12))

/-- The normed-space perturbation implication.  In the matrix application,
the `hdelta` premise is supplied by the commutator operator/Frobenius norm
estimate and `hcoercive` by the spectral gap.  Those bridges are separate
obligations, not hidden in this theorem. -/
theorem perturbation_from_coercivity
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (L Lh : E →ₗ[ℝ] E) (W Wh R Rh : E)
    (δh εR εM Wstar : ℝ)
    (hgap : 0 < δh) (hεM : 0 ≤ εM)
    (hcoercive : ∀ x : E, δh * ‖x‖ ≤ ‖Lh x‖)
    (htrue : L W = R) (hfit : Lh Wh = Rh)
    (hR : ‖Rh - R‖ ≤ εR)
    (hdelta : ‖Lh W - L W‖ ≤ 2 * εM * ‖W‖)
    (hW : ‖W‖ ≤ Wstar) :
    ‖Wh - W‖ ≤ (εR + 2 * εM * Wstar) / δh := by
  have hrep : Lh (Wh - W) = (Rh - R) - (Lh W - L W) := by
    simp only [map_sub, hfit, htrue]
    abel
  have hmul : 2 * εM * ‖W‖ ≤ 2 * εM * Wstar := by
    exact mul_le_mul_of_nonneg_left hW (by positivity)
  have htotal : δh * ‖Wh - W‖ ≤ εR + 2 * εM * Wstar := by
    calc
      δh * ‖Wh - W‖ ≤ ‖Lh (Wh - W)‖ := hcoercive _
      _ = ‖(Rh - R) - (Lh W - L W)‖ := by rw [hrep]
      _ ≤ ‖Rh - R‖ + ‖Lh W - L W‖ := norm_sub_le _ _
      _ ≤ εR + 2 * εM * Wstar := by linarith
  exact (le_div_iff₀ hgap).2 (by simpa [mul_comm] using htotal)

end CAS15C03

#print axioms CAS15C03.cm_inverse
#print axioms CAS15C03.commLinear_rank_three
#print axioms CAS15C03.sq_gap
#print axioms CAS15C03.least_squares_unique
#print axioms CAS15C03.ordered_gap_bound
#print axioms CAS15C03.perturbation_from_coercivity
#print axioms CAS15C03.repeated01_kernel
#print axioms CAS15C03.isotropic_zero
