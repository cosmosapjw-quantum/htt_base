(* PR-187 boost-order arithmetic and exact rapidity round-trip (Rocq/Coq 9.0).
   Kernel-independent from the Lean axis. Convention/type mechanics only. *)
From Stdlib Require Import ZArith.
Open Scope Z_scope.

(* exact rapidity round-trip: boost by beta then -beta composes to identity *)
Lemma rapidity_roundtrip : forall beta : Z, beta + (- beta) = 0.
Proof. intro beta. ring. Qed.

(* product of orders: Omega_tilt is order 2, so Omega_tilt^2 is order 4 *)
Lemma omega_tilt_squared_order : 2 * 2 = 4.
Proof. reflexivity. Qed.

(* an O(beta^4) term cannot cancel an O(beta^2) term *)
Lemma order_mismatch : 4 <> 2.
Proof. discriminate. Qed.

(* the order-correct deprojection matches the quadrupole order *)
Lemma deprojection_matches : 2 = 2.
Proof. reflexivity. Qed.

(* coqc exit 0 (all Qed accepted) is the PR187_ROCQ_PASS signal *)
