import Mathlib

/- Finite O4 contract only. Vectors are arbitrary, including zero/coincident
vectors. The dot and contractions are bilinear, never Hermitian. -/
namespace R8O4
noncomputable section
abbrev V (K : Type*) := Fin 3 → K
variable {K : Type*} [Field K] [CharZero K]
def dot (u v : V K) : K := ∑ i, u i * v i
def delta (i j : Fin 3) : K := if i = j then 1 else 0
def S2 (u v : V K) (i j : Fin 3) : K := (u i*v j+v i*u j)/2
def Q (A : K) (u v : V K) (i j : Fin 3) : K :=
  A*(S2 u v i j-delta i j*dot u v/3)
def S3 (u v w : V K) (i j k : Fin 3) : K :=
  (u i*v j*w k+u i*w j*v k+v i*u j*w k+
   v i*w j*u k+w i*u j*v k+w i*v j*u k)/6
def b (u v w : V K) (k : Fin 3) : K :=
  (dot u v*w k+dot u w*v k+dot v w*u k)/3
def O (A : K) (u v w : V K) (i j k : Fin 3) : K :=
  A*(S3 u v w i j k-(delta i j*b u v w k+
    delta i k*b u v w j+delta j k*b u v w i)/5)
def contract2 (T : Fin 3 → Fin 3 → K) (n : V K) : K :=
  ∑ i, ∑ j, T i j * n i * n j
def contract3 (T : Fin 3 → Fin 3 → Fin 3 → K) (n : V K) : K :=
  ∑ i, ∑ j, ∑ k, T i j k * n i * n j * n k

 theorem q_sym (A : K) (u v : V K) (i j : Fin 3) : Q A u v i j = Q A u v j i := by
  simp only [Q, S2, delta, eq_comm]
  ring
 theorem q_trace (A : K) (u v : V K) : (∑ i, Q A u v i i) = 0 := by
  simp [Q, S2, delta, dot, Fin.sum_univ_succ]
  ring
 theorem q_swap (A : K) (u v : V K) : Q A u v = Q A v u := by
  funext i j
  simp only [Q, S2, dot, Fin.sum_univ_succ]
  ring
 theorem q_sign (A : K) (u v : V K) : Q (-A) (-u) v = Q A u v := by
  funext i j
  simp [Q, S2, dot, Fin.sum_univ_succ]
  ring
 theorem q_zero (u v : V K) : Q 0 u v = 0 := by
  funext i j
  simp [Q]
 theorem o_swap12 (A : K) (u v w : V K) : O A u v w = O A v u w := by
  funext i j k
  simp only [O, S3, b, dot, Fin.sum_univ_succ]
  ring
 theorem o_swap23 (A : K) (u v w : V K) : O A u v w = O A u w v := by
  funext i j k
  simp only [O, S3, b, dot, Fin.sum_univ_succ]
  ring
 theorem o_sym12 (A : K) (u v w : V K) (i j k : Fin 3) :
     O A u v w i j k = O A u v w j i k := by
  simp only [O, S3]
  have hd : (delta i j : K) = delta j i := by simp [delta, eq_comm]
  rw [hd]
  ring
 theorem o_sym23 (A : K) (u v w : V K) (i j k : Fin 3) :
     O A u v w i j k = O A u v w i k j := by
  simp only [O, S3]
  have hd : (delta j k : K) = delta k j := by simp [delta, eq_comm]
  rw [hd]
  ring
 theorem o_trace (A : K) (u v w : V K) (k : Fin 3) :
     (∑ i, O A u v w i i k) = 0 := by
  fin_cases k <;> simp [O, S3, b, delta, dot, Fin.sum_univ_succ] <;> ring
 theorem o_sign (A : K) (u v w : V K) : O (-A) (-u) v w = O A u v w := by
  funext i j k
  simp [O, S3, b, dot, Fin.sum_univ_succ]
  ring
 theorem o_zero (u v w : V K) : O 0 u v w = 0 := by
  funext i j k
  simp [O]

/- Enumerate the images of an arbitrary three-element permutation; injectivity
rules out the 21 non-permutation triples. This proves arbitrary permutations,
not just a finite numerical vector fixture. -/
 theorem perm_cases (p : Equiv.Perm (Fin 3)) :
     (p 0 = 0 ∧ p 1 = 1 ∧ p 2 = 2) ∨
     (p 0 = 0 ∧ p 1 = 2 ∧ p 2 = 1) ∨
     (p 0 = 1 ∧ p 1 = 0 ∧ p 2 = 2) ∨
     (p 0 = 1 ∧ p 1 = 2 ∧ p 2 = 0) ∨
     (p 0 = 2 ∧ p 1 = 0 ∧ p 2 = 1) ∨
     (p 0 = 2 ∧ p 1 = 1 ∧ p 2 = 0) := by
  have h01 : p 0 ≠ p 1 := p.injective.ne (by decide)
  have h02 : p 0 ≠ p 2 := p.injective.ne (by decide)
  have h12 : p 1 ≠ p 2 := p.injective.ne (by decide)
  generalize h0 : p 0 = x
  generalize h1 : p 1 = y
  generalize h2 : p 2 = z
  fin_cases x <;> fin_cases y <;> fin_cases z <;> simp_all
 theorem o_vector_perm (A : K) (v : Fin 3 → V K) (p : Equiv.Perm (Fin 3)) :
     O A (v (p 0)) (v (p 1)) (v (p 2)) = O A (v 0) (v 1) (v 2) := by
  rcases perm_cases p with h|h|h|h|h|h <;> rcases h with ⟨h0,h1,h2⟩ <;> rw [h0,h1,h2]
  all_goals funext i j k
  all_goals simp only [O, S3, b, dot, Fin.sum_univ_succ]
  all_goals ring
 theorem o_index_perm (A : K) (u v w : V K) (idx : Fin 3 → Fin 3)
     (p : Equiv.Perm (Fin 3)) :
     O A u v w (idx (p 0)) (idx (p 1)) (idx (p 2)) =
     O A u v w (idx 0) (idx 1) (idx 2) := by
  rcases perm_cases p with h|h|h|h|h|h <;> rcases h with ⟨h0,h1,h2⟩ <;> rw [h0,h1,h2]
  · exact o_sym23 _ _ _ _ _ _ _
  · exact o_sym12 _ _ _ _ _ _ _
  · rw [o_sym23, o_sym12]
  · rw [o_sym12, o_sym23]
  · rw [o_sym12, o_sym23, o_sym12]
 theorem q_contraction (A : K) (u v n : V K) :
     contract2 (Q A u v) n = A*(dot u n*dot v n-dot u v*dot n n/3) := by
  simp [contract2, Q, S2, delta, dot, Fin.sum_univ_succ]
  ring
 theorem o_contraction (A : K) (u v w n : V K) :
     contract3 (O A u v w) n =
     A*(dot u n*dot v n*dot w n-3*dot (b u v w) n*dot n n/5) := by
  simp [contract3, O, S3, b, delta, dot, Fin.sum_univ_succ]
  ring

def nullVector (z : ℂ) : V ℂ := ![1-z^2, Complex.I*(1+z^2), 2*z]
 theorem null_cone (z : ℂ) : dot (nullVector z) (nullVector z) = 0 := by
  apply Complex.ext <;> simp [dot, nullVector, Fin.sum_univ_succ, pow_two] <;> ring
 theorem q_null (A : ℂ) (u v : V ℂ) (z : ℂ) :
     contract2 (Q A u v) (nullVector z) = A*dot u (nullVector z)*dot v (nullVector z) := by
  rw [q_contraction, null_cone]
  ring
 theorem o_null (A : ℂ) (u v w : V ℂ) (z : ℂ) :
     contract3 (O A u v w) (nullVector z) =
     A*dot u (nullVector z)*dot v (nullVector z)*dot w (nullVector z) := by
  rw [o_contraction, null_cone]
  ring

def complexify (u : V ℝ) : V ℂ := fun i => (u i : ℂ)
 theorem q_cast (A : ℝ) (u v : V ℝ) (i j : Fin 3) :
     ((Q A u v i j : ℝ) : ℂ) = Q (A : ℂ) (complexify u) (complexify v) i j := by
  simp only [Q, S2, delta, dot, complexify, Fin.sum_univ_succ]
  split_ifs <;> push_cast <;> ring
 theorem o_cast (A : ℝ) (u v w : V ℝ) (i j k : Fin 3) :
     ((O A u v w i j k : ℝ) : ℂ) = O (A : ℂ) (complexify u) (complexify v) (complexify w) i j k := by
  simp only [O, S3, b, delta, dot, complexify, Fin.sum_univ_succ]
  split_ifs <;> push_cast <;> ring
 theorem q_real_null (A : ℝ) (u v : V ℝ) (z : ℂ) :
     contract2 (fun i j => ((Q A u v i j : ℝ) : ℂ)) (nullVector z) =
     (A : ℂ)*dot (complexify u) (nullVector z)*dot (complexify v) (nullVector z) := by
  simp_rw [q_cast]
  exact q_null _ _ _ _
 theorem o_real_null (A : ℝ) (u v w : V ℝ) (z : ℂ) :
     contract3 (fun i j k => ((O A u v w i j k : ℝ) : ℂ)) (nullVector z) =
     (A : ℂ)*dot (complexify u) (nullVector z)*dot (complexify v) (nullVector z)*
     dot (complexify w) (nullVector z) := by
  simp_rw [o_cast]
  exact o_null _ _ _ _ _

#print axioms q_trace
#print axioms q_swap
#print axioms q_sign
#print axioms q_zero
#print axioms o_trace
#print axioms o_vector_perm
#print axioms o_index_perm
#print axioms o_sign
#print axioms o_zero
#print axioms null_cone
#print axioms q_real_null
#print axioms o_real_null
end
end R8O4
