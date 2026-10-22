# First observed blocker

The first primary-toolchain lookup found that
`formal_mathlib/.lake/packages` is a broken symlink to
`/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages`.
The primary path was not repaired. The oracle fallback
`/home/cosmosapjw/lean_oracles/viii_oracle` has Lean 4.31.0 and mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, matching the frozen pin.

The first compiler invocation used:

```text
cwd=/home/cosmosapjw/lean_oracles/viii_oracle
lake env lean /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/c01_finite_adjoint_bridge_v1_20261010/lean/FiniteAdjoint.lean
exit_code=1
source_sha256=8779812ac640ee7a0cfe04786c732a3c6fd51931bc257dcac3dc75daba3e2e2c
```

The exact first source is preserved as `lean/FiniteAdjoint.attempt01.lean`.
The failure was in the negative identity-operator control, line 95:

```text
error: Type mismatch: After simplification, term
  hK
 has type
  Ne.{u_1 + 1} K 0
but is expected to have type
  Ne.{1} (inner ℝ K K) 0
```

All seven core adjoint/retained-moment declarations elaborated in that attempt.
The failed control had Lean's error-recovery `sorryAx` in its printed audit;
that failed candidate is explicitly inadmissible. The repair replaced the
incorrect simplification with `inner_self_eq_zero.mp` followed by the supplied
nonzero hypothesis. Unused finite-dimensional section hypotheses were removed
from the moment-equivalence and operator-control lemmas. There was no change to
the core mathematical assumptions or the frozen input contracts.

The second compiler attempt, preserved as `compile_attempt_02.*` and
`lean/FiniteAdjoint.attempt02.lean`, then reported two documentation-parser
errors because `omit ... in` followed a declaration doc comment. Moving the
doc comments after `omit ... in` repaired the parser issue. That attempt had
no `sorryAx`, but its nonzero exit remains a failed compile.
