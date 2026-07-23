(* PR-222 multi-window bulk bridge rank (Rocq/Coq 9.0), independent kernel.
   Gram G = (10W)^T(10W) = [[140,44,14],[44,78,28],[14,28,54]]. det(G)=394584. *)
From Stdlib Require Import ZArith Lia.
Open Scope Z_scope.

(* 3x3 determinant of the multi-window Gram matrix, expanded along row 1 *)
Definition detG : Z :=
  140 * (78 * 54 - 28 * 28)
  - 44 * (44 * 54 - 28 * 14)
  + 14 * (44 * 28 - 78 * 14).

Lemma detG_value : detG = 394584.
Proof. unfold detG. lia. Qed.

Lemma detG_nonzero : detG <> 0.
Proof. rewrite detG_value. lia. Qed.

(* single-window outer-product Gram (row r1=(10,1,0)): every 2x2 minor vanishes,
   e.g. minor(cols 1,2) = (10*10)*(1*1) - (10*1)*(1*10) = 0 -> rank 1 *)
Lemma single_window_minor_zero : (10*10)*(1*1) - (10*1)*(1*10) = 0.
Proof. lia. Qed.
