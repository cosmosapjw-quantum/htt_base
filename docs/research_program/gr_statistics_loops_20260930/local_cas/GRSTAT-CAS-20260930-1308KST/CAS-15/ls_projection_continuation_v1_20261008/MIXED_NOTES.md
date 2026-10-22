# CAS15-C03 mixed norm author result

`Mixed.lean` proves, for **every** real 3 by 3 matrix `A` and flat 3 by 3 real matrix `X`,

`‖AX − XA‖F ≤ 2 ‖A‖op ‖X‖F`.

`F3 = EuclideanSpace ℝ (Fin 3 × Fin 3)` supplies exactly the entrywise Frobenius norm. `opNorm A = ‖Matrix.toEuclideanCLM A‖` is the operator norm induced by the Euclidean norm on `EuclideanSpace ℝ (Fin 3)`. The proof applies the operator bound to each column, sums the squared estimates, uses transposition to obtain right multiplication, and then applies the triangle inequality. Since the theorem has no matrix symmetry or skew premise, it specializes to symmetric `DeltaM` and skew `W` without changing the constant or norm. The algebraic commutator is `AX − XA`, as required by the adopted CAS15-C03 inputs.

Compiled declarations: `CAS15Mixed.norm_leftMul_le`, `norm_rightMul_le`, `norm_comm_le`, `norm_flat_comm_le`. `matrixOf : F3 → M3` converts flat entries to an ordinary matrix. `CAS15Frobenius.comm` uses the same flat entries; equality of the two commutator definitions is left to the synthesis file owned by the coordinator.

Validation: from `/home/cosmosapjw/lean_oracles/viii_oracle`, run `lake env lean /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/ls_projection_continuation_v1_20261008/Mixed.lean`. Final `mixed_logs/attempt8.exit` is `0`, stderr empty, and stdout reports only `[propext, Classical.choice, Quot.sound]` for all four public theorems. Lean is 4.31.0, commit `68218e876d2a38b1985b8590fff244a83c321783`; mathlib checkout is `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. Final source SHA256 is `5f637968997a48560a69358e0b7726b0a532f36337d8e12965ee5ebb5238be3a`.

The first draft failed to compile from API and sum-rewriting mistakes; its console error is retained as `mixed_logs/attempt1.console_transcript.txt`. Subsequent failed attempts 2, 4, 5, and 6 are retained as raw redirected stdout/stderr and exit files; attempts 3, 7, and 8 exited 0 at their respective intermediate source versions. No `sorry`, extra axiom, target-as-assumption, or scalar substitute for the operator norm is used.

Scope: this theorem supplies only the mixed operator/Frobenius commutator estimate. It does not prove the rotated coercivity/gap estimate, Weyl eigenvalue perturbation, full least-squares synthesis, or CAS15-C03/four-axis adjudication. Scientific admission remains `HOLD`. Requested author setting: `gpt-6-sol/high`; observed runtime setting: `UNKNOWN` because no independent runtime metadata receipt was provided to this author.
