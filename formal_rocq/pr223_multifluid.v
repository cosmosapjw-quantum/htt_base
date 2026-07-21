(* PR-223 antipodal two-stream moment cone (Rocq/Coq 9.0), independent kernel.
   Streams +1, -1 (unit weight). Convention/mechanics only. *)
From Stdlib Require Import ZArith Lia.
Open Scope Z_scope.

(* zero net flux *)
Lemma first_moment_zero : (1 * 1 + 1 * (-1))%Z = 0.
Proof. lia. Qed.

(* nonzero tilt energy: second-moment trace = 2 > 0 *)
Lemma trace_positive : (1 * 1 * 1 + 1 * (-1) * (-1))%Z = 2 /\ 2 > 0.
Proof. split; lia. Qed.

(* 3*Pi = diag(4,-2,-2): traceless but nonzero -> anisotropic stress present *)
Lemma aniso_traceless : (4 + (-2) + (-2))%Z = 0.
Proof. lia. Qed.

Lemma aniso_nonzero : 4 <> 0.
Proof. lia. Qed.
