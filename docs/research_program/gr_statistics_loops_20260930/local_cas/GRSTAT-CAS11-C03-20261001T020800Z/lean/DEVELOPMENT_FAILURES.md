# Interactive development failures retained for C03

These are the raw failed shell/compiler outputs from this axis author's public tool calls before the final successful runner execution. The shell/Lean commands were run in the exact worktree at `/home/cosmosapjw/Dropbox/bianchi/htt_base`; the Lean command's cwd was `/home/cosmosapjw/Dropbox/bianchi/htt_base/formal_mathlib`. They were development attempts, not the final axis execution. Each recorded tool exit was 1.

## Initial path failure

Command: shell heredoc writing `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean`, followed by `lake env lean ../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean`; cwd `formal_mathlib`. Exit: 1. Output:

```text
/bin/bash: line 1: docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean: No such file or directory
no such file or directory (error code: 4294967294)
  file: ../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean
```

## First compiler failure: inner-product notation parsing

Argv: `lake env lean ../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean`; cwd `formal_mathlib`. Exit: 1. Output:

```text
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:26:34: error: unexpected identifier; expected command
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:42:27: error: unexpected identifier; expected ':=', 'where' or '|'
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:49:72: error: unexpected identifier; expected ':=', 'where' or '|'
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:71:11: error: unexpected identifier; expected '|' or '|ₘ'
'CAS11C03.projection_idempotent' depends on axioms: [propext, Classical.choice, Quot.sound]
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:75:14: error(lean.unknownIdentifier): Unknown constant `projection_orthogonal`
'CAS11C03.gram_quadratic_identity' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.gram_quadratic_norm_sq' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.gram_positive_semidefinite' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.weighted_cauchy_schwarz' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
```

## Second compiler failure: notation still not parsed

Same argv/cwd. Exit: 1. Output:

```text
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:26:38: error: unexpected identifier; expected command
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:42:29: error: unexpected identifier; expected ':=', 'where' or '|'
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:49:76: error: unexpected identifier; expected ':=', 'where' or '|'
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:71:11: error: unexpected identifier; expected '|' or '|ₘ'
'CAS11C03.projection_idempotent' depends on axioms: [propext, Classical.choice, Quot.sound]
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:75:14: error(lean.unknownIdentifier): Unknown constant `projection_orthogonal`
'CAS11C03.gram_quadratic_identity' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.gram_quadratic_norm_sq' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.gram_positive_semidefinite' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.weighted_cauchy_schwarz' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
```

## Third compiler failure: residual Gram symmetry rewrite

Same argv/cwd. Exit: 1. Output:

```text
Try this:
  [apply] ring_nf
  
  The `ring` tactic failed to close the goal. Use `ring_nf` to obtain a normal form.
    
  Note that `ring` works primarily in *commutative* rings. If you have a noncommutative ring, abelian group or module, consider using `noncomm_ring`, `abel` or `module` instead.
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:49:85: error: unsolved goals
case e_f.e_f
E : Type u_1
ι : Type u_2
inst✝³ : NormedAddCommGroup E
inst✝² : InnerProductSpace ℝ E
inst✝¹ : FiniteDimensional ℝ E
inst✝ : Fintype ι
V : Submodule ℝ E
K : ι → E
a : ι → ℝ
i j : ι
⊢ a i * ⟪residual V K i, residual V K j⟫ * a j = a i * a j * ⟪residual V K j, residual V K i⟫
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:70:0: warning: automatically included section variable(s) unused in theorem `CAS11C03.weighted_cauchy_schwarz`:
  [FiniteDimensional ℝ E]
consider restructuring your `variable` declarations so that the variables are not in scope or explicitly omit them:
  omit [FiniteDimensional ℝ E] in theorem ...

Note: This linter can be disabled with `set_option linter.unusedSectionVars false`
'CAS11C03.projection_idempotent' depends on axioms: [propext, Classical.choice, Quot.sound]
'CAS11C03.projection_orthogonal' depends on axioms: [propext, Classical.choice, Quot.sound]
'CAS11C03.gram_quadratic_identity' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.gram_quadratic_norm_sq' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.gram_positive_semidefinite' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
'CAS11C03.weighted_cauchy_schwarz' depends on axioms: [propext, Classical.choice, Quot.sound]
```

## Fourth compiler failure: overbroad square-certificate rewrite

Same argv/cwd. Exit: 1. Output:

```text
../docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean:79:58: error: Tactic `rewrite` failed: Did not find an occurrence of the pattern
  inner ?m.114 (?x - ?y) ?z
in the target expression
  ⟪⟪y, y⟫ • x, ⟪y, y⟫ • x⟫ - ⟪⟪y, y⟫ • x, ⟪x, y⟫ • y⟫ - (⟪⟪x, y⟫ • y, ⟪y, y⟫ • x⟫ - ⟪⟪x, y⟫ • y, ⟪x, y⟫ • y⟫) =
    ⟪y, y⟫ * (⟪y, y⟫ * ⟪x, x⟫ - ⟪x, y⟫ ^ 2)

E : Type u_1
inst✝² : NormedAddCommGroup E
inst✝¹ : InnerProductSpace ℝ E
inst✝ : FiniteDimensional ℝ E
x y : E
b : ℝ := ⟪y, y⟫
c : ℝ := ⟪x, y⟫
z : E := b • x - c • y
⊢ ⟪⟪y, y⟫ • x, ⟪y, y⟫ • x⟫ - ⟪⟪y, y⟫ • x, ⟪x, y⟫ • y⟫ - (⟪⟪x, y⟫ • y, ⟪y, y⟫ • x⟫ - ⟪⟪x, y⟫ • y, ⟪x, y⟫ • y⟫) =
    ⟪y, y⟫ * (⟪y, y⟫ * ⟪x, x⟫ - ⟪x, y⟫ ^ 2)
'CAS11C03.projection_idempotent' depends on axioms: [propext, Classical.choice, Quot.sound]
'CAS11C03.projection_orthogonal' depends on axioms: [propext, Classical.choice, Quot.sound]
'CAS11C03.gram_quadratic_identity' depends on axioms: [propext, Classical.choice, Quot.sound]
'CAS11C03.gram_quadratic_norm_sq' depends on axioms: [propext, Classical.choice, Quot.sound]
'CAS11C03.gram_positive_semidefinite' depends on axioms: [propext, Classical.choice, Quot.sound]
'CAS11C03.weighted_cauchy_schwarz' depends on axioms: [propext, sorryAx, Classical.choice, Quot.sound]
```
