import Mathlib

/-!
Exact Lean certificate for CAS-10-C02.

The coordinates use the declared orthonormal frame with metric
`diag (-1, 1, 1, 1)`.  `Sym4` stores exactly the ten independent entries of
a real symmetric covariant matrix.  No result from another CAS axis is used.
-/

namespace CAS10C02

@[ext]
structure Vec4 where
  t : ℝ
  x : ℝ
  y : ℝ
  z : ℝ

instance : Zero Vec4 := ⟨0, 0, 0, 0⟩

def eDot (v w : Vec4) : ℝ :=
  v.t * w.t + v.x * w.x + v.y * w.y + v.z * w.z

def gDot (v w : Vec4) : ℝ :=
  -v.t * w.t + v.x * w.x + v.y * w.y + v.z * w.z

def lower (v : Vec4) : Vec4 := ⟨-v.t, v.x, v.y, v.z⟩

def add (v w : Vec4) : Vec4 :=
  ⟨v.t + w.t, v.x + w.x, v.y + w.y, v.z + w.z⟩

def scale (a : ℝ) (v : Vec4) : Vec4 :=
  ⟨a * v.t, a * v.x, a * v.y, a * v.z⟩

structure Sym4 where
  s00 : ℝ
  s01 : ℝ
  s02 : ℝ
  s03 : ℝ
  s11 : ℝ
  s12 : ℝ
  s13 : ℝ
  s22 : ℝ
  s23 : ℝ
  s33 : ℝ

def symMul (S : Sym4) (u : Vec4) : Vec4 :=
  ⟨S.s00 * u.t + S.s01 * u.x + S.s02 * u.y + S.s03 * u.z,
   S.s01 * u.t + S.s11 * u.x + S.s12 * u.y + S.s13 * u.z,
   S.s02 * u.t + S.s12 * u.x + S.s22 * u.y + S.s23 * u.z,
   S.s03 * u.t + S.s13 * u.x + S.s23 * u.y + S.s33 * u.z⟩

def h (S : Sym4) (u : Vec4) : ℝ := eDot u (symMul S u)

def restShift (u v : Vec4) : Vec4 :=
  add v (scale (eDot u v) (lower u))

def b (S : Sym4) (u : Vec4) : Vec4 :=
  restShift u (symMul S u)

def A (c : ℝ) (S : Sym4) (u : Vec4) : Vec4 :=
  scale (2 * c) (b S u)

def Jgeo (S : Sym4) (u : Vec4) : ℝ :=
  gDot (symMul S u) (symMul S u) + (h S u) ^ 2

theorem b_orthogonal (S : Sym4) (u : Vec4)
    (hmass : gDot u u = -1) :
    eDot u (b S u) = 0 := by
  change eDot u (restShift u (symMul S u)) = 0
  calc
    eDot u (restShift u (symMul S u)) =
        eDot u (symMul S u) * (1 + gDot u u) := by
          dsimp [restShift, add, scale, lower, eDot, gDot]
          ring
    _ = 0 := by rw [hmass]; ring

theorem b_square_eq_Jgeo (S : Sym4) (u : Vec4)
    (hmass : gDot u u = -1) :
    gDot (b S u) (b S u) = Jgeo S u := by
  change gDot (restShift u (symMul S u)) (restShift u (symMul S u)) =
    gDot (symMul S u) (symMul S u) + eDot u (symMul S u) ^ 2
  calc
    gDot (restShift u (symMul S u)) (restShift u (symMul S u)) =
        gDot (symMul S u) (symMul S u) +
          2 * eDot u (symMul S u) ^ 2 +
          eDot u (symMul S u) ^ 2 * gDot u u := by
            dsimp [restShift, add, scale, lower, eDot, gDot]
            ring
    _ = gDot (symMul S u) (symMul S u) + eDot u (symMul S u) ^ 2 := by
      rw [hmass]
      ring

private theorem spatial_cauchy (u v : Vec4) :
    0 ≤
      (u.x ^ 2 + u.y ^ 2 + u.z ^ 2) *
          (v.x ^ 2 + v.y ^ 2 + v.z ^ 2) -
        (u.x * v.x + u.y * v.y + u.z * v.z) ^ 2 := by
  nlinarith [sq_nonneg (u.x * v.y - u.y * v.x),
    sq_nonneg (u.x * v.z - u.z * v.x),
    sq_nonneg (u.y * v.z - u.z * v.y)]

theorem rest_space_nonneg (u v : Vec4)
    (hmass : gDot u u = -1) (horth : eDot u v = 0) :
    0 ≤ gDot v v := by
  let U : ℝ := u.x ^ 2 + u.y ^ 2 + u.z ^ 2
  let V : ℝ := v.x ^ 2 + v.y ^ 2 + v.z ^ 2
  let D : ℝ := u.x * v.x + u.y * v.y + u.z * v.z
  have hm : u.t ^ 2 = 1 + U := by
    dsimp [U, gDot] at hmass ⊢
    nlinarith
  have ho : D = -u.t * v.t := by
    dsimp [D, eDot] at horth ⊢
    nlinarith
  have hs : D ^ 2 = u.t ^ 2 * v.t ^ 2 := by
    rw [ho]
    ring
  have hc : 0 ≤ U * V - D ^ 2 := by
    dsimp [U, V, D]
    exact spatial_cauchy u v
  have hV : 0 ≤ V := by
    dsimp [V]
    positivity
  have ht : 0 < u.t ^ 2 := by
    rw [hm]
    dsimp [U]
    nlinarith [sq_nonneg u.x, sq_nonneg u.y, sq_nonneg u.z]
  have hid : u.t ^ 2 * gDot v v = V + (U * V - D ^ 2) := by
    calc
      u.t ^ 2 * gDot v v = u.t ^ 2 * (V - v.t ^ 2) := by
        dsimp [V, gDot]
        ring
      _ = (1 + U) * (V - v.t ^ 2) := by rw [hm]
      _ = V + (U * V - D ^ 2) := by rw [hs, hm]; ring
  have hp : 0 ≤ u.t ^ 2 * gDot v v := by
    rw [hid]
    positivity
  nlinarith

theorem rest_space_zero_iff (u v : Vec4)
    (hmass : gDot u u = -1) (hfuture : 0 < u.t)
    (horth : eDot u v = 0) :
    gDot v v = 0 ↔ v = 0 := by
  constructor
  · intro hq
    let U : ℝ := u.x ^ 2 + u.y ^ 2 + u.z ^ 2
    let V : ℝ := v.x ^ 2 + v.y ^ 2 + v.z ^ 2
    let D : ℝ := u.x * v.x + u.y * v.y + u.z * v.z
    have hm : u.t ^ 2 = 1 + U := by
      dsimp [U, gDot] at hmass ⊢
      nlinarith
    have ho : D = -u.t * v.t := by
      dsimp [D, eDot] at horth ⊢
      nlinarith
    have hs : D ^ 2 = u.t ^ 2 * v.t ^ 2 := by
      rw [ho]
      ring
    have hc : 0 ≤ U * V - D ^ 2 := by
      dsimp [U, V, D]
      exact spatial_cauchy u v
    have hV : 0 ≤ V := by
      dsimp [V]
      positivity
    have hid : u.t ^ 2 * gDot v v = V + (U * V - D ^ 2) := by
      calc
        u.t ^ 2 * gDot v v = u.t ^ 2 * (V - v.t ^ 2) := by
          dsimp [V, gDot]
          ring
        _ = (1 + U) * (V - v.t ^ 2) := by rw [hm]
        _ = V + (U * V - D ^ 2) := by rw [hs, hm]; ring
    have hVz : V = 0 := by
      nlinarith
    have hx : v.x = 0 := by
      dsimp [V] at hVz
      nlinarith [sq_nonneg v.x, sq_nonneg v.y, sq_nonneg v.z]
    have hy : v.y = 0 := by
      dsimp [V] at hVz
      nlinarith [sq_nonneg v.x, sq_nonneg v.y, sq_nonneg v.z]
    have hz : v.z = 0 := by
      dsimp [V] at hVz
      nlinarith [sq_nonneg v.x, sq_nonneg v.y, sq_nonneg v.z]
    have ht0 : v.t = 0 := by
      dsimp [eDot] at horth
      rw [hx, hy, hz] at horth
      nlinarith
    change v = ⟨0, 0, 0, 0⟩
    ext <;> assumption
  · intro hv
    change v = ⟨0, 0, 0, 0⟩ at hv
    subst v
    norm_num [gDot]

theorem A_square_identity (c : ℝ) (S : Sym4) (u : Vec4)
    (hc : 0 < c) :
    gDot (A c S u) (A c S u) / (4 * c ^ 2) =
      gDot (b S u) (b S u) := by
  have hcn : c ≠ 0 := ne_of_gt hc
  dsimp [A, scale, gDot]
  field_simp
  ring

theorem A_zero_iff_b_zero (c : ℝ) (S : Sym4) (u : Vec4)
    (hc : 0 < c) :
    A c S u = 0 ↔ b S u = 0 := by
  have h2c : 2 * c ≠ 0 := mul_ne_zero (by norm_num) (ne_of_gt hc)
  change scale (2 * c) (b S u) = ⟨0, 0, 0, 0⟩ ↔ b S u = ⟨0, 0, 0, 0⟩
  constructor
  · intro hA
    have ht := congrArg Vec4.t hA
    have hx := congrArg Vec4.x hA
    have hy := congrArg Vec4.y hA
    have hz := congrArg Vec4.z hA
    dsimp [scale] at ht hx hy hz
    ext
    · exact (mul_eq_zero.mp ht).resolve_left h2c
    · exact (mul_eq_zero.mp hx).resolve_left h2c
    · exact (mul_eq_zero.mp hy).resolve_left h2c
    · exact (mul_eq_zero.mp hz).resolve_left h2c
  · intro hb
    rw [hb]
    norm_num [scale]

theorem mass_shell_invariant (c : ℝ) (S : Sym4) (u : Vec4)
    (hc : 0 < c) (hmass : gDot u u = -1) (hfuture : 0 < u.t) :
    eDot u (b S u) = 0 ∧
    Jgeo S u = gDot (b S u) (b S u) ∧
    Jgeo S u = gDot (A c S u) (A c S u) / (4 * c ^ 2) ∧
    0 ≤ Jgeo S u ∧
    (Jgeo S u = 0 ↔ A c S u = 0) := by
  have hob : eDot u (b S u) = 0 := b_orthogonal S u hmass
  have hbj : gDot (b S u) (b S u) = Jgeo S u :=
    b_square_eq_Jgeo S u hmass
  have hpos : 0 ≤ gDot (b S u) (b S u) :=
    rest_space_nonneg u (b S u) hmass hob
  have hz : gDot (b S u) (b S u) = 0 ↔ b S u = 0 :=
    rest_space_zero_iff u (b S u) hmass hfuture hob
  have hAq := A_square_identity c S u hc
  have hAz := A_zero_iff_b_zero c S u hc
  refine ⟨hob, hbj.symm, ?_, ?_, ?_⟩
  · linarith
  · linarith
  · rw [← hbj, hz, ← hAz]

#print axioms b_orthogonal
#print axioms b_square_eq_Jgeo
#print axioms rest_space_nonneg
#print axioms rest_space_zero_iff
#print axioms A_square_identity
#print axioms A_zero_iff_b_zero
#print axioms mass_shell_invariant

end CAS10C02
