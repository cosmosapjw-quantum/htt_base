import Main

/-!
G10-A: rest-space positivity and the scalar geodesicity invariant, stated on
the physical domain of CAS-10-C02 (PR #489 source `Main.lean`, reused unchanged).

Domain: `c > 0`, `u` future unit timelike (`gDot u u = -1`, `0 < u.t`) in the
orthonormal frame with metric `diag (-1, 1, 1, 1)`; `S` real symmetric
(`Sym4`).  `A c S u = 2 c b`, `b` the rest projection of `S u`
(COMMON_SPEC: `A_cov = 2 c B u`).  Positivity is proved on the rest space of
`u`, not for the ambient Lorentz form; the negative controls show it fails
without the mass-shell/orthogonality domain.
-/

namespace G10ARestspace

open CAS10C02

/-- The covariant acceleration annihilates the 4-velocity (`u^a A_a = 0`). -/
theorem acceleration_orthogonal (c : ℝ) (S : Sym4) (u : Vec4)
    (hmass : gDot u u = -1) :
    eDot u (A c S u) = 0 := by
  have hb : eDot u (b S u) = 0 := b_orthogonal S u hmass
  simp only [A, scale, eDot] at hb ⊢
  linear_combination (2 * c) * hb

/-- Rest-space positivity of the acceleration norm and of `Jgeo`, and the
geodesicity criterion, on the same physical domain. -/
theorem restspace_geodesicity (c : ℝ) (S : Sym4) (u : Vec4)
    (hc : 0 < c) (hmass : gDot u u = -1) (hfuture : 0 < u.t) :
    eDot u (A c S u) = 0 ∧
    0 ≤ gDot (A c S u) (A c S u) ∧
    (gDot (A c S u) (A c S u) = 0 ↔ A c S u = 0) ∧
    Jgeo S u = gDot (A c S u) (A c S u) / (4 * c ^ 2) ∧
    0 ≤ Jgeo S u ∧
    (Jgeo S u = 0 ↔ A c S u = 0) := by
  have hA := acceleration_orthogonal c S u hmass
  obtain ⟨_, _, hJA, hJ0, hJz⟩ := mass_shell_invariant c S u hc hmass hfuture
  exact ⟨hA, rest_space_nonneg u (A c S u) hmass hA,
    rest_space_zero_iff u (A c S u) hmass hfuture hA, hJA, hJ0, hJz⟩

/-- Negative control: the ambient Lorentz form is not positive; a unit
timelike vector itself has negative square. -/
theorem ambient_form_not_positive :
    ∃ v : Vec4, gDot v v < 0 := ⟨⟨1, 0, 0, 0⟩, by norm_num [gDot]⟩

/-- Negative control: without orthogonality to `u` the rest-space
positivity fails (take `v = u`). -/
theorem orthogonality_needed :
    ∃ u v : Vec4, gDot u u = -1 ∧ 0 < u.t ∧ eDot u v ≠ 0 ∧ gDot v v < 0 :=
  ⟨⟨1, 0, 0, 0⟩, ⟨1, 0, 0, 0⟩, by norm_num [gDot], by norm_num,
    by norm_num [eDot], by norm_num [gDot]⟩

/-- Negative control: off the unit mass shell `Jgeo` can be negative, so
positivity must not be asserted for unconstrained `S, u`. -/
theorem off_shell_Jgeo_negative :
    ∃ (S : Sym4) (u : Vec4), Jgeo S u < 0 := by
  refine ⟨⟨1, 0, 0, 0, 0, 0, 0, 0, 0, 0⟩, ⟨1 / 2, 0, 0, 0⟩, ?_⟩
  norm_num [Jgeo, gDot, h, eDot, symMul]

end G10ARestspace
