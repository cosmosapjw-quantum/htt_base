(* PR-189 joint support vs product box (Rocq/Coq 9.0), independent kernel.
   Fixture c=(1,1), 0<=x<=1, 0<=y<=1, x+y<=1. Convention/mechanics only. *)
From Stdlib Require Import ZArith Lia.
Open Scope Z_scope.

(* the coupling x+y<=1 keeps every feasible objective strictly below the
   product-box sup of 2 *)
Lemma coupling_below_product : forall x y : Z, x + y <= 1 -> x + y < 2.
Proof. intros x y H. lia. Qed.

(* joint sup is achieved at the witness (1,0): obj = 1 *)
Lemma joint_witness_value : (1 + 0)%Z = 1.
Proof. lia. Qed.

(* product-box corner (1,1): obj = 2 *)
Lemma product_corner_value : (1 + 1)%Z = 2.
Proof. lia. Qed.

(* strict containment: joint sup 1 < product sup 2 *)
Lemma strict_narrower : 1 < 2.
Proof. lia. Qed.
