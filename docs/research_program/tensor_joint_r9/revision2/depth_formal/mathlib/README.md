# Current mathlib depth proof continuation

This is R9 revision 2, continuing 9ca515ad. The previous proof attempts and
CAS_FAIL records are preserved. No observational data or old experiment is
replayed. Existing shared mathlib **fabf563a7c95a166b8d7b6efca11c8b4dc9d911f**
and its built Lean **v4.31.0** cache are now connected explicitly through
LEAN_PATH. The repo's core-only `formal/lakefile.toml` and empty package manifest
remain unchanged. The old `import Mathlib` failure described that unconnected
core environment; it did not establish that mathlib was absent from storage.

The source is `formal/R9Depth/Recursion.lean` and `Covariance.lean`.
This continuation was Host-authored after the old child's continuation hook
denied the unreserved/unverified lifecycle. It is not an independent Lean-axis
replacement or a four-axis aggregate PASS. A separate current source review has
its own registered assignment and launch identity. Its final response reported
`GLOBAL_HOOK_IDENTITY_OR_STATE_UNVERIFIED:CHILD_BINDING_MISSING` and no further action.
At closeout, a self-declared review result and two successful compiler records
were found in its assigned directory. Host verified their hashes, source equality
and two MLflow traces. The result has null launch_id and unverified launch evidence;
these artifacts do not authenticate the child or admit independent review. Both
the final stop response and stored results are preserved, without forcing them
into a single execution narrative. The result flags the known full D3/D2/D4 gaps.
The one permitted review round is exhausted; no renamed retry or lifecycle-policy
change was made. `routing_status.json` records this reconciliation. Whole-run
acceptance is NON_PASS.

## Exact compiled scope

| Contract component | Current Lean result | Assumptions and limits |
|---|---|---|
| D1 mean map | `R9Depth.mean_linear_map` | Real coordinates, arbitrary finite index types, fixed H, componentwise MemLp 2 on a probability space. |
| D1 full covariance | `R9Depth.covariance_linear_map` | Actual mathlib covariance integrals; full H C Hᵀ, no covariance independence premise. |
| D1 PSD | `R9Depth.covariance_pullback_psd` | Any real PSD C, arbitrary compatible H; genuine real matrix PSD, not an Int-valued helper. |
| D1 cross steps | `R9Depth.all_cross_step_blocks` | Four arbitrary finite block index types. Lower block is C11−C10 Lᵀ−K C01+K C00 Lᵀ. No equal-size or diagonal-C assumption. |
| D3 inverse | `DepthLean.reconstructDependent_residualsDependent` | Reverse heterogeneous composition, arbitrary finite depth and dependent state types with two explicit additive cancellation laws. |
| D3 retained initial state | `initialDependent_reconstructDependent`, `pathEquiv`, `residualsDependent_surjective` | Both inverse directions, retained initial block and residual surjectivity. No initial state discarded. |
| D3 real specialization | `DepthLean.realBlockPathEquiv` | Arbitrary d:Nat→Nat and rectangular real K_j; no invertibility of K_j. Ordinary real vector additive groups discharge the abstract cancellation premises. |

The inverse argument and mean/covariance identities are formalizations of prior
D1/D3, not new mathematical discoveries. The original forward heterogeneous
composition is carried into the current source with its origin preserved.
The compiled sources print their axiom dependencies; the successful records
contain only Lean/mathlib's standard propext, Classical.choice and Quot.sound,
with no sorryAx, target axiom or numeric finite-fixture substitute.

`recursion_checked/` is the successful source-bound inverse/equivalence record;
`covariance_blocks/` is the successful source-bound final D1 record. Earlier
attempts include a wrong cancellation-lemma name, missing real import and a
noncomputable-definition scope error. Their source snapshots and compiler output
are preserved; those errors are not theorem counterexamples. No tolerance or
theorem target was relaxed.

## Still required for FORMAL_DEPTH

D3 still needs the explicit bridge from the path representation to a flattened
real block-triangular linear map, determinant one, homogeneous kernel
characterization and the complete singular-law/support pushforward. A set-level
equivalence alone does not discharge these measurable/topological obligations.

D2 still needs the general affine support equality, Moore–Penrose score and
chi-square law, including rank zero and off-support candidate handling. D4 still
needs PSD range consistency, singular Schur complement, full-past conditional
Gaussian law and successive innovation independence. The installed mathlib
contains Gaussian map and uncorrelated-Gaussian independence theorems, so this is
now a missing **formalization and bridge**, not an unavailable Lean engine or a
blanket absence of probability libraries. Its matrix nonsingular-inverse module
explicitly excludes pseudoinverses; no matching general Moore–Penrose/conditional
Gaussian development was found in the inspected modules. A missing theorem name
is not a proof of impossibility.

The unchanged CAS_D1–D4 contracts still govern acceptance. This new Lean evidence
does not silently update old Wolfram/SymPy/Sage results or grant an aggregate
four-axis admission. FORMAL_DEPTH therefore remains BLOCKED until every required
component and axis is accepted. The user's sixteen follow-on research bundles
remain conditional on that prerequisite; already derived MQ1/MQ2 are not redone.

## Reproduction and tracing

Use the task-local Python environment with mlflow-skinny 3.16.0:

```text
<trace-env>/bin/python docs/research_program/tensor_joint_r9/revision2/depth_formal/mathlib/verify_lean.py Recursion --output <fresh-directory> --trace-store <local-trace-store>
<trace-env>/bin/python docs/research_program/tensor_joint_r9/revision2/depth_formal/mathlib/verify_lean.py Covariance --output <another-fresh-directory> --trace-store <local-trace-store>
```

The wrapper verifies the library/toolchain pins, runs Lean with a 120-second
compiler limit, preserves source/command/stdout/stderr/exit, flushes MLflow and
reads back each trace with its root and compiler spans. The local trace store is
outside the repo; portable trace JSON is retained alongside raw execution.
Successful observability does not mean successful compilation or admission;
always read the compiler output and exact proposition scope. Initial trace
records used OK for the completed wrapper despite compiler failure; subsequent
wrapper records correctly mark nonzero compiler exits ERROR. Original traces
are retained unchanged.

All production/empirical/novelty HOLDs, full selected observation law, validated
physical response and common state–jet–anchor coverage remain unchanged. Family
alpha and each product allocation are unchanged; new alpha consumption is zero.
