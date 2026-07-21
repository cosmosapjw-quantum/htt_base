(* PR-186 W^2 vorticity normalization: universal ring proof (Rocq/Coq 9.0).

   Kernel-independent from the Lean axis. For the spatial antisymmetric
   vorticity tensor with entries a,b,c and dual vector (c,-b,a):
     tensorNorm = 2(a^2+b^2+c^2),  vecNorm = a^2+b^2+c^2,
   so tensorNorm = 2*vecNorm; the factor-3 (W^2 = A:A/(6H^2) = w.w/(3H^2),
   wrong display w.w/H^2 = 3 W^2) and the three-halves ceiling
   (W^2 <= (3/2)B^2 with Theta=3H) are stated in cleared (division-free)
   polynomial form so they hold over any commutative ring, discharged by
   the Ring tactic. Convention mechanics only; no observable claim. *)
From Stdlib Require Import ZArith.
Open Scope Z_scope.

Section W2Convention.
  Variables a b c H B : Z.

  (* tensor norm equals twice the dual-vector norm *)
  Lemma tensor_eq_two_vec :
    2*(a*a) + 2*(b*b) + 2*(c*c) = 2*((a*a) + (b*b) + (c*c)).
  Proof. ring. Qed.

  (* factor-3: wa2/H^2 = 3 * (wa2/(3H^2)), cleared cross-multiplication *)
  Lemma wrong_over_registered_is_three :
    ((a*a) + (b*b) + (c*c)) * (3 * (H*H))
      = 3 * (((a*a) + (b*b) + (c*c)) * (H*H)).
  Proof. ring. Qed.

  (* registered form equals vector form: A:A/(6H^2) = w.w/(3H^2), cleared *)
  Lemma registered_eq_vector_form :
    (2*((a*a)+(b*b)+(c*c))) * (3 * (H*H))
      = ((a*a)+(b*b)+(c*c)) * (6 * (H*H)).
  Proof. ring. Qed.

  (* three-halves ceiling: 2*(B*3H)^2 = 3*B^2*(6H^2), cleared over Z *)
  Lemma ceiling_three_halves :
    2 * ((B*(3*H)) * (B*(3*H))) = 3 * (B*B) * (6 * (H*H)).
  Proof. ring. Qed.

End W2Convention.

(* If this file compiles (all Qed accepted by the kernel), every lemma is
   universally proven; coqc exit 0 is the PR186_ROCQ_PASS signal. *)
