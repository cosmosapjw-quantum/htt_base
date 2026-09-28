# R10 return: executed optical fixture and source-bound T9 failure

**PARTIAL_RESEARCH_CHECKPOINT — independent review blocked; scientific admission HOLD.**
Owner: HTT research. Transfer source: none; synthetic flat/Milne and prescribed
optical tidal fixtures only. No native Bianchi/family claim, new observed method,
production patch, merge, ready/canonical promotion, or visibility change.

## What was actually added

[optical_fixture.py](optical_fixture.py) connects a nonzero first jet through
H,V, an exact central null ray and Jacobi distance, numerically integrated
collisionless redshift, source radiation, and full Cartesian STF Q/O. This is
an executed fixture, not a restatement of the plan. In flat Milne coordinates,
theta=3/tau, H=1/tau and V=0 give endpoint (t,r)=(1.25,0.75)L*, redshift
factor 2 and mean temperature 1.35 K. The independent source polynomial fixes
Qxy=0.0005 and Oxyz=0.0005/6 (including permutations). Detailed signs, units,
Riemann, screen and tetrad conventions are in [CONVENTIONS.md](CONVENTIONS.md).

Finite first-jet rank is 12, H-only rank 9, V-only rank 11. A planar H design
has rank 5; a shared nuisance column reduces the full target rank to 11.
These are ideal/processed design examples, not measured generators or a CMB
first-jet inversion. Numerical range constraints are checked at one generic
direction; no all-mask/continuum certification is claimed.

[optical_results.json](optical_results.json) contains generated tensors and
residuals. Maximum checked residual is 5.998090912839871e-12 against the
predeclared 1e-10 threshold. ODE Jacobi residuals are around 1e-14.
The [residual figure](optical_residuals.png) also displays the frequency-dependent
effective temperature of a two-blackbody mixture; halving its temperature
contrast quarters its leading discrepancy. This rejects exact single-Planck
closure for finite angular mixing. PNG was visually inspected.

## T9: a real current-consumer failure, no automatic repair

[t9_diagnosis.py](t9_diagnosis.py) integrates epsilon^4 F' independently of
T9 tables for F=exp(-epsilon/E*), obtaining -4 Pi0. With the actual proper/
conformal adapter and scalar packing round trip, the current tensor, packed
and public photon RHS return +4 a sigma Pi0 instead of -4 a sigma Pi0.
All five STF basis shears at a=1 and a=2 disagree with normalized residual 2.
The first physical comparison is preserved in [t9_attempt03.log](t9_attempt03.log)
and [t9_results.json](t9_results.json); exit 1 is intentional and remains FAIL.

The counterfactual output-sign reversal agrees for this isolated source. It
is a diagnostic only: it does not install a candidate patch or qualify the
full hierarchy. The mixed five-m matrix executes, but its CG normalization
relative to Cartesian Pi remains unresolved. FORMAL_T9 and current four-axis
run-adjudicate evidence are absent, so OP-07 is blocked. Do not flip the entire
RHS or treat packed/full parity as a physics oracle. Future affected scope:
terms.py T9, generated packed T9 cache, public photon/shared neutrino RHS and
its derivative-based consumers; mode_mixing_blocks pre9 needs its own adapter
resolution. Historical generated results are not rewritten or universally
invalidated from this isolated test.

Initial failures are also retained: [attempt01](t9_attempt01.log) was a missing
`htt/src` import path; [attempt02](t9_attempt02.log) was a keyword-only call
error. Both were fixed locally without changing production source or scientific
reference. The third attempt reached the physics failure. None was erased.

## R9 progressed independently, with existing results reused

[r9_reuse.json](r9_reuse.json) binds actual donor files to commit
870bd67af159993ccde4ede9923424a475c01375 and includes immutable donor URLs.
The donor checkout is clean. Existing CF3–SDSS 294-row calibration/depth
features and D3 Lean compile are reused, without replaying completed mocks or
claiming these are an available CF4 selected law. Joint covariance, selected
observation law, physical response and common state/jet/anchor coverage remain
UNAVAILABLE. D3 transport does not close D2/D4 or independent admission.

The new independent finite full-Q/O covariance discriminator has residual
3.330937692535408e-16 for C2=C3 cancellation. A shared-calibration target has
quotient rank zero. These are deterministic response-law checks, not new mocks
or observational confidence. R9-03..18 are not declared completed. New observed
methods qualified/executed: **none**. Alpha spent: 0; all original allocations,
P0 quarantine and PR4/NPIPE exclusion are retained. Missing physical jet and
remainder providers leave the optical-to-physical image whole-domain.

## Source, execution and validation

- Fixed plan commit: c8bd214a61088b684cad1d08873f05227cf5bfb0.
- Fixed plan tree: d66ccc669492c2b6f233d58b818c86b69fc3aaa7.
- Both verified; all manifest entries match ([log](plan_manifest.log)).
- Isolated branch: `research/r10-optical-mapping-local-20260920`.
- Worktree: `/mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree`.
- Moved bulk data remain under `/mnt/extdrive/workdir`; the prior turn's
  compatibility link preserves donor absolute paths. No bulk copies made.
- [runtime.json](runtime.json): actual Python/NumPy/SciPy/Matplotlib versions.
  Python executed `print(6*7)` and returned 42. C++/Wolfram were not invoked
  because these finite calculations did not require them. No new CAS claim.
- Installed physmath research/coding 4.0.0 instructions were read alongside
  repository skills. Their Claude-oriented routing text was not treated as
  model identity. Developer identifies GPT-6; exact runtime SKU is not exposed.
- `python3 .../local_execution/optical_fixture.py`: exit 0, final [log](optical_attempt02.log).
- `python3 .../local_execution/t9_diagnosis.py`: exit 1, physical mismatch retained.
- `python3 .../local_execution/r9_reuse.py`: exit 0, [log](r9_execution.log).
- `python3 -m pytest .../local_execution/test_optical_fixture.py -q`: exit 0,
  five tests ([log](pytest.log)); wrong-parity consumer assertion is rejected.
- `validate_plan.py`: PASS_STRUCTURAL_ONLY, 36 nodes / 24 unchanged R9 nodes.
- Canonical DAG validator: exit 0, 195 cards. Canonical status not changed.
- `git diff --check`: exit 0. No production source modifications.

## Independent review blocker and return decision

A registered Terra/high reviewer was selected with frozen source inputs and
validator. Native PreToolUse rejected it **before dispatch** with
CLIENT_WORKTREE_MISMATCH: the client is open at the original checkout while
the registered source is the isolated worktree. See [review_blocker.json](review_blocker.json).
Changing a subprocess cwd or prompt cannot establish native child identity.
The original checkout also has an unrelated active EXTERNAL-FUSION run; it was
not replaced to manufacture a successful review. No reviewer result exists,
and Host self-checks are not labelled independent review.

The handoff explicitly permits Git return at any terminal/partial checkpoint.
This publication is that failure-bearing checkpoint; it does not satisfy the
normal independently-reviewed completion bar. The process acceptance is
STOP_INVALID at the review/return boundary, not an invalidation of all finite
optical results. Production/observed/novelty admission remains HOLD.

Next minimal action: open the Codex client at the exact isolated worktree,
reconcile the undelivered registered review and finish one independent review
of these source/result files without rerunning archived R8/R9 pools. Then
prepare scoped FORMAL_T9 obligations, including mixed-mode normalization, before
any sign candidate. Continue R9 product/law work independently of optical
readiness. [MAIN_CONTINUATION_PROMPT.md](MAIN_CONTINUATION_PROMPT.md) supplies
the return fields and exact source references.
