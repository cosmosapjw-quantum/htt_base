import G16BBandlimit

/-! G16-B axiom audit: frozen-signature bindings (`example`) and `#print axioms` for every
public theorem of `G16BBandlimit`. -/

open G16B

-- Frozen signature bindings (FROZEN_TARGETS.md)
example (L : ℕ) : shBand L ≤ cartSpan L := shBand_le_cartSpan L
example {A B : ℕ} {f g : ChartFn} (hf : f ∈ cartSpan A) (hg : g ∈ cartSpan B) :
    f * g ∈ cartSpan (A + B) := mul_mem_cartSpan hf hg
example {A B : ℕ} (h : A ≤ B) : cartSpan A ≤ cartSpan B := cartSpan_mono h
example (i j : Fin 3) : (fun μ φ => eVec μ φ i * eVec μ φ j) ∈ cartSpan 2 := eiej_mem i j
example (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    weakKernel H a σ i j ∈ cartSpan 4 := weakKernel_mem H a σ i j
example {L : ℕ} {I : ChartFn} (hI : I ∈ shBand L) (H : ℝ) (a : Fin 3 → ℝ)
    (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    weakResidualIntegrand I H a σ i j ∈ cartSpan (L + 4) := weakResidual_mem hI H a σ i j
example {L : ℕ} {I : ChartFn} (hI : I ∈ shBand L) (i j : Fin 3) :
    momentIntegrand I i j ∈ cartSpan (L + 2) := moment_mem hI i j
example {LC : ℕ} {C : ChartFn} (hC : C ∈ shBand LC) (i j : Fin 3) :
    collisionIntegrand C i j ∈ cartSpan (LC + 2) := collision_mem hC i j
example {LT : ℕ} {T : ChartFn} (hT : T ∈ shBand LT) (i j : Fin 3) :
    transportIntegrand T i j ∈ cartSpan (LT + 2) := transport_mem hT i j
example {L LC LT : ℕ} {I C T : ChartFn}
    (hI : I ∈ shBand L) (hC : C ∈ shBand LC) (hT : T ∈ shBand LT)
    (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    momentIntegrand I i j ∈ cartSpan (Dstar L LC LT) ∧
    weakResidualIntegrand I H a σ i j ∈ cartSpan (Dstar L LC LT) ∧
    collisionIntegrand C i j ∈ cartSpan (Dstar L LC LT) ∧
    transportIntegrand T i j ∈ cartSpan (Dstar L LC LT) ∧
    residualIntegrand I C T H a σ i j ∈ cartSpan (Dstar L LC LT) :=
  dstar_membership hI hC hT H a σ i j
example (a b c : ℕ) : quadRule (CAS16C03.monomial a b c) = CAS16C03.productRule a b c :=
  quadRule_monomial a b c
example (a b c : ℕ) : sphereMeanFn (CAS16C03.monomial a b c) = CAS16C03.sphereMean a b c :=
  sphereMeanFn_monomial a b c
example {f : ChartFn} (hf : f ∈ cartSpan 8) : quadRule f = sphereMeanFn f :=
  quadRule_exact_cartSpan8 hf
example : Dstar 4 6 4 = 8 := dstar_464
example : (Dstar 4 6 4 + 1 + 1) / 2 ≤ 5 ∧ Dstar 4 6 4 + 1 ≤ 9 ∧ Dstar 4 6 4 ≤ 2 * 5 - 1 :=
  c3_arith_464
example {I C T : ChartFn}
    (hI : I ∈ shBand 4) (hC : C ∈ shBand 6) (hT : T ∈ shBand 4)
    (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    quadRule (momentIntegrand I i j) = sphereMeanFn (momentIntegrand I i j) ∧
    quadRule (weakResidualIntegrand I H a σ i j) =
      sphereMeanFn (weakResidualIntegrand I H a σ i j) ∧
    quadRule (collisionIntegrand C i j) = sphereMeanFn (collisionIntegrand C i j) ∧
    quadRule (transportIntegrand T i j) = sphereMeanFn (transportIntegrand T i j) ∧
    quadRule (residualIntegrand I C T H a σ i j) =
      sphereMeanFn (residualIntegrand I C T H a σ i j) :=
  actual_integrands_exact_464 hI hC hT H a σ i j
example (D N : ℕ) : (D + 1 + 1) / 2 ≤ N ↔ D + 1 ≤ 2 * N := c3_ceil_iff D N
example (L : ℕ) : (fun _ _ => (1 : ℝ)) ∈ shBand L := one_mem_shBand L
example : weakKernel 0 0 !![1, 0, 0; 0, 0, 0; 0, 0, 0] 0 0 0 0 ≠ 0 := weakKernel_witness_ne
example : shCos 4 4 ∈ shBand 4 := shCos_witness_mem

-- Definitional bindings to the accepted C03 objects
example : CAS16C03.fullMonomialClaim := CAS16C03.fullMonomialTheorem

#check @G16B.monomial_mem_cartSpan
#check @G16B.cartSpan_mono
#check @G16B.monomial_mul
#check @G16B.mul_mem_cartSpan
#check @G16B.cosHarm_succ
#check @G16B.sinHarm_succ
#check @G16B.harm_mem
#check @G16B.polyEval_mem
#check @G16B.legendreP_natDegree_le
#check @G16B.assocLegendrePoly_natDegree_le
#check @G16B.shCos_eq
#check @G16B.shSin_eq
#check @G16B.shCos_mem
#check @G16B.shSin_mem
#check @G16B.shBand_le_cartSpan
#check @G16B.eCoord_mem
#check @G16B.const_mem
#check @G16B.eiej_mem
#check @G16B.weakKernel_mem
#check @G16B.weakResidual_mem
#check @G16B.moment_mem
#check @G16B.collision_mem
#check @G16B.transport_mem
#check @G16B.dstar_membership
#check @G16B.quadRule_monomial
#check @G16B.sphereMeanFn_monomial
#check @G16B.continuous_of_mem_cartSpan
#check @G16B.quadRule_add
#check @G16B.quadRule_smul
#check @G16B.quadRule_zero
#check @G16B.sphereMeanFn_zero
#check @G16B.sphereMeanFn_add
#check @G16B.sphereMeanFn_smul
#check @G16B.quadRule_exact_cartSpan8
#check @G16B.dstar_464
#check @G16B.c3_arith_464
#check @G16B.actual_integrands_exact_464
#check @G16B.c3_ceil_iff
#check @G16B.one_mem_shBand
#check @G16B.weakKernel_witness_ne
#check @G16B.shCos_witness_mem

#print axioms G16B.monomial_mem_cartSpan
#print axioms G16B.cartSpan_mono
#print axioms G16B.monomial_mul
#print axioms G16B.mul_mem_cartSpan
#print axioms G16B.cosHarm_succ
#print axioms G16B.sinHarm_succ
#print axioms G16B.harm_mem
#print axioms G16B.polyEval_mem
#print axioms G16B.legendreP_natDegree_le
#print axioms G16B.assocLegendrePoly_natDegree_le
#print axioms G16B.shCos_eq
#print axioms G16B.shSin_eq
#print axioms G16B.shCos_mem
#print axioms G16B.shSin_mem
#print axioms G16B.shBand_le_cartSpan
#print axioms G16B.eCoord_mem
#print axioms G16B.const_mem
#print axioms G16B.eiej_mem
#print axioms G16B.weakKernel_mem
#print axioms G16B.weakResidual_mem
#print axioms G16B.moment_mem
#print axioms G16B.collision_mem
#print axioms G16B.transport_mem
#print axioms G16B.dstar_membership
#print axioms G16B.quadRule_monomial
#print axioms G16B.sphereMeanFn_monomial
#print axioms G16B.continuous_of_mem_cartSpan
#print axioms G16B.quadRule_add
#print axioms G16B.quadRule_smul
#print axioms G16B.quadRule_zero
#print axioms G16B.sphereMeanFn_zero
#print axioms G16B.sphereMeanFn_add
#print axioms G16B.sphereMeanFn_smul
#print axioms G16B.quadRule_exact_cartSpan8
#print axioms G16B.dstar_464
#print axioms G16B.c3_arith_464
#print axioms G16B.actual_integrands_exact_464
#print axioms G16B.c3_ceil_iff
#print axioms G16B.one_mem_shBand
#print axioms G16B.weakKernel_witness_ne
#print axioms G16B.shCos_witness_mem
#print axioms CAS16C03.fullMonomialTheorem
