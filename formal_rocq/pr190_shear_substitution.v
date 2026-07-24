(* PR-190 Bianchi-I dust identities and component-endpoint mismatch.
   Metric/physics scope is fixed by the shared CAS contract. *)
From Stdlib Require Import Reals Field Lra.
Open Scope R_scope.

Definition denominator (s z : R) : R := s + (1 - s) * z.

Lemma dust_gauss_constraint_identity :
  forall s z : R, denominator s z <> 0 ->
    s / denominator s z + (1 - s) * z / denominator s z = 1.
Proof.
  intros s z H.
  unfold denominator in H |- *.
  field.
  exact H.
Qed.

Lemma dust_logistic_evolution_identity :
  forall s z : R, denominator s z <> 0 ->
    (-3 * s * (1 - s) * z) / (denominator s z * denominator s z)
      + 3 * (s / denominator s z) * (1 - s / denominator s z) = 0.
Proof.
  intros s z H.
  unfold denominator in H |- *.
  field.
  exact H.
Qed.

Lemma dust_hubble_evolution_identity :
  forall s z : R, denominator s z <> 0 ->
    (-3 + (3 / 2) * (1 - s) * z / denominator s z)
      + (3 / 2) * (1 + s / denominator s z) = 0.
Proof.
  intros s z H.
  unfold denominator in H |- *.
  field.
  exact H.
Qed.

Lemma lower_scalar_match :
  (13 / 150) - (1 / 50) + (1 / 50) + (-1 / 150) = (2 / 25).
Proof. field. Qed.

Lemma lower_component_gap_witness :
  Rabs ((1 / 50) - 0) = (1 / 50).
Proof. rewrite Rabs_right; lra. Qed.

Lemma upper_scalar_match :
  (1 / 10) - (3 / 100) + (3 / 100) + 0 = (1 / 10).
Proof. field. Qed.

Lemma upper_component_gap_witness :
  Rabs ((3 / 100) - 0) = (3 / 100).
Proof. rewrite Rabs_right; lra. Qed.
