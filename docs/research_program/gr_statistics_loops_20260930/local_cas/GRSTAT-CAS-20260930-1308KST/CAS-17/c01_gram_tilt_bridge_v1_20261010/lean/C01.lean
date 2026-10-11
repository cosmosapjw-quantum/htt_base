import Mathlib.Analysis.Matrix.PosDef
import Mathlib.Analysis.Real.Sqrt
import Mathlib.Tactic

/-!
CAS-17-C01 only. Orthonormal coordinates, signature (-,+,+,+).
Covariant epsilon_0123 = +1, hence contravariant epsilon^0123 = -1.
The coordinate wedge below is epsilon^{abcd} a_b b_c c_d.
Contract SHA256: a2817237e6cf8ad79e1222e4a06aa340db985f02a987b2c8d0b0b4dc84df9328.
COMMON_SPEC SHA256: 4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897.
No historical source or sibling-axis result is imported.
-/
namespace CAS17C01
noncomputable section

structure Vec where
  t : ℝ
  x : ℝ
  y : ℝ
  z : ℝ

def lorentz (a b : Vec) : ℝ := -a.t * b.t + a.x * b.x + a.y * b.y + a.z * b.z
def spatial (a b : Vec) : ℝ := a.x * b.x + a.y * b.y + a.z * b.z
def scale (r : ℝ) (a : Vec) : Vec := ⟨r*a.t, r*a.x, r*a.y, r*a.z⟩
def det3 (a b c d e f g h i : ℝ) : ℝ := a*e*i-a*f*h-b*d*i+b*f*g+c*d*h-c*e*g

def wedge (a b c : Vec) : Vec :=
  ⟨-det3 a.x a.y a.z b.x b.y b.z c.x c.y c.z,
   -det3 a.t a.y a.z b.t b.y b.z c.t c.y c.z,
   det3 a.t a.x a.z b.t b.x b.z c.t c.x c.z,
   -det3 a.t a.x a.y b.t b.x b.y c.t c.x c.y⟩

def triple (a b c : Vec) : Fin 3 → Vec := ![a,b,c]
def gram (a b c : Vec) : Matrix (Fin 3) (Fin 3) ℝ :=
  fun i j => lorentz (triple a b c i) (triple a b c j)

theorem wedge_orthogonal (a b c : Vec) :
    lorentz (wedge a b c) a = 0 ∧ lorentz (wedge a b c) b = 0 ∧
      lorentz (wedge a b c) c = 0 := by
  dsimp [lorentz, wedge, det3]
  constructor
  · ring
  constructor <;> ring

theorem wedge_norm (a b c : Vec) :
    lorentz (wedge a b c) (wedge a b c) = -(gram a b c).det := by
  rw [Matrix.det_fin_three]
  dsimp [gram, triple, lorentz, wedge, det3]
  ring

theorem lorentz_scale (r s : ℝ) (a b : Vec) :
    lorentz (scale r a) (scale s b) = r*s*lorentz a b := by
  dsimp [lorentz, scale]
  ring

def futureSign (v : Vec) : ℝ := if 0 < v.t then 1 else -1
def normal (a b c : Vec) : Vec :=
  scale (futureSign (wedge a b c) / Real.sqrt (gram a b c).det) (wedge a b c)
def FutureUnit (v : Vec) : Prop := 0 < v.t ∧ lorentz v v = -1
def gamma (u N : Vec) : ℝ := -lorentz u N
def relativeSpatial (u N : Vec) : Vec :=
  ⟨u.t-gamma u N*N.t, u.x-gamma u N*N.x,
    u.y-gamma u N*N.y, u.z-gamma u N*N.z⟩
def betaSq (u N : Vec) : ℝ :=
  lorentz (relativeSpatial u N) (relativeSpatial u N) / (gamma u N)^2
def beta (u N : Vec) : ℝ := Real.sqrt (betaSq u N)

theorem sign_sq (v : Vec) : futureSign v ^ 2 = 1 := by
  unfold futureSign
  split <;> norm_num

theorem future_sign_pos (v : Vec) (hv : lorentz v v < 0) :
    0 < futureSign v * v.t := by
  have ht : v.t ≠ 0 := by
    intro ht
    dsimp [lorentz] at hv
    rw [ht] at hv
    nlinarith [sq_nonneg v.x, sq_nonneg v.y, sq_nonneg v.z]
  unfold futureSign
  split_ifs with h
  · simpa using h
  · have : v.t < 0 := lt_of_le_of_ne (le_of_not_gt h) ht
    simpa using neg_pos.mpr this

theorem normal_future_unit (a b c : Vec) (hG : (gram a b c).PosDef) :
    FutureUnit (normal a b c) := by
  have hd : 0 < (gram a b c).det := hG.det_pos
  have hs : 0 < Real.sqrt (gram a b c).det := Real.sqrt_pos.mpr hd
  have hs0 : Real.sqrt (gram a b c).det ≠ 0 := ne_of_gt hs
  have hsq := Real.sq_sqrt (le_of_lt hd)
  have hv : lorentz (wedge a b c) (wedge a b c) < 0 := by
    rw [wedge_norm]; exact neg_neg_of_pos hd
  constructor
  · dsimp [normal, scale]
    rw [div_mul_eq_mul_div]
    exact div_pos (future_sign_pos _ hv) hs
  · unfold normal
    rw [lorentz_scale, wedge_norm]
    have hsign := sign_sq (wedge a b c)
    field_simp
    nlinarith

theorem spatial_cauchy (a b : Vec) :
    spatial a b ^ 2 ≤ spatial a a * spatial b b := by
  dsimp [spatial]
  nlinarith [sq_nonneg (a.x*b.y-a.y*b.x),
    sq_nonneg (a.x*b.z-a.z*b.x), sq_nonneg (a.y*b.z-a.z*b.y)]

theorem future_time_ge_one (v : Vec) (hv : FutureUnit v) : 1 ≤ v.t := by
  rcases hv with ⟨ht, hn⟩
  dsimp [lorentz] at hn
  nlinarith [sq_nonneg v.x, sq_nonneg v.y, sq_nonneg v.z]

theorem gamma_ge_one (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    1 ≤ gamma u N := by
  have hu1 := future_time_ge_one u hu
  have hN1 := future_time_ge_one N hN
  have hp : 1 ≤ u.t * N.t := by nlinarith
  have hcs := spatial_cauchy u N
  have huS : spatial u u = u.t^2-1 := by
    have := hu.2
    dsimp [lorentz, spatial] at *
    nlinarith
  have hNS : spatial N N = N.t^2-1 := by
    have := hN.2
    dsimp [lorentz, spatial] at *
    nlinarith
  rw [huS, hNS] at hcs
  have hS : spatial u N ≤ u.t*N.t-1 := by
    by_contra h
    have hlt : u.t*N.t-1 < spatial u N := lt_of_not_ge h
    have hspos : 0 < spatial u N := by linarith
    nlinarith [sq_nonneg (u.t-N.t)]
  dsimp [gamma, lorentz, spatial] at *
  linarith

theorem relativeSpatial_identities (u N : Vec)
    (hu : FutureUnit u) (hN : FutureUnit N) :
    lorentz (relativeSpatial u N) N = 0 ∧
    lorentz (relativeSpatial u N) (relativeSpatial u N) = gamma u N ^ 2 - 1 := by
  have hsym : lorentz N u = lorentz u N := by dsimp [lorentz]; ring
  have hn := hN.2
  have hun := hu.2
  constructor
  · have hid : lorentz (relativeSpatial u N) N = lorentz u N - gamma u N * lorentz N N := by
      dsimp [lorentz, relativeSpatial]; ring
    rw [hid, hn]
    dsimp [gamma]
    ring
  · have hid : lorentz (relativeSpatial u N) (relativeSpatial u N) =
        lorentz u u - 2*gamma u N * lorentz u N + gamma u N ^ 2 * lorentz N N := by
      dsimp [lorentz, relativeSpatial]; ring
    rw [hid, hun, hn]
    dsimp [gamma]
    ring

theorem beta_formula (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    betaSq u N = 1 - (gamma u N)⁻¹ ^ 2 ∧ 0 ≤ betaSq u N ∧ betaSq u N < 1 := by
  have hg := gamma_ge_one u N hu hN
  have hgpos : 0 < gamma u N := by linarith
  have hg0 : gamma u N ≠ 0 := ne_of_gt hgpos
  have hr := (relativeSpatial_identities u N hu hN).2
  have hformula : betaSq u N = 1 - (gamma u N)⁻¹ ^ 2 := by
    unfold betaSq
    rw [hr]
    field_simp
  refine ⟨hformula, ?_, ?_⟩
  · unfold betaSq
    rw [hr]
    exact div_nonneg (by nlinarith) (sq_nonneg _)
  · rw [hformula]
    have : 0 < (gamma u N)⁻¹ ^ 2 := sq_pos_of_pos (inv_pos.mpr hgpos)
    linarith

theorem beta_squared (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    beta u N ^ 2 = 1 - (gamma u N)⁻¹ ^ 2 := by
  have hb := beta_formula u N hu hN
  unfold beta
  rw [Real.sq_sqrt hb.2.1, hb.1]

/-- Full finite C01 bridge, including genuinely constructed normal and speed square. -/
theorem c01_gram_tilt_bridge (a b c u : Vec)
    (hG : (gram a b c).PosDef) (hu : FutureUnit u) :
    lorentz (wedge a b c) a = 0 ∧
    lorentz (wedge a b c) b = 0 ∧
    lorentz (wedge a b c) c = 0 ∧
    lorentz (wedge a b c) (wedge a b c) = -(gram a b c).det ∧
    FutureUnit (normal a b c) ∧
    1 ≤ gamma u (normal a b c) ∧
    lorentz (relativeSpatial u (normal a b c)) (normal a b c) = 0 ∧
    beta u (normal a b c) ^ 2 = 1 - (gamma u (normal a b c))⁻¹ ^ 2 ∧
    betaSq u (normal a b c) = 1 - (gamma u (normal a b c))⁻¹ ^ 2 ∧
    0 ≤ betaSq u (normal a b c) ∧ betaSq u (normal a b c) < 1 := by
  have ho := wedge_orthogonal a b c
  have hn := normal_future_unit a b c hG
  have hb := beta_formula u (normal a b c) hu hn
  exact ⟨ho.1, ho.2.1, ho.2.2, wedge_norm a b c, hn,
    gamma_ge_one u _ hu hn, (relativeSpatial_identities u _ hu hn).1,
    beta_squared u _ hu hn, hb.1, hb.2⟩

#check c01_gram_tilt_bridge
#print axioms wedge_orthogonal
#print axioms wedge_norm
#print axioms normal_future_unit
#print axioms gamma_ge_one
#print axioms relativeSpatial_identities
#print axioms beta_formula
#print axioms beta_squared
#print axioms c01_gram_tilt_bridge
end
end CAS17C01
