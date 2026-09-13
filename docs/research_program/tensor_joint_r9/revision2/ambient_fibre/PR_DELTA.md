# PR-R9-FIBRE — fixed ambient STF numerical reproduction

The previous comparison used different ambient functionals when an SVD basis
changed. This increment fixes Cartesian q, v and the STF3 direction a first,
then transforms both the contraction and the functional into each basis.
The existing production helper and original reference evidence are unchanged.
The starting commit is af5fe14a60658ff7926e58ea512bd3014aeba2ba.

Two existing environments agree on support 0.9745422070448619 across 35 basis
representations each. The independent reviewer used explicit Cartesian entries
and 80-decimal arithmetic and obtained 0.974542207044862226..., differing by
3.27e-16 at the inherited 1e-10 tolerance. Reconstructed witnesses, contraction,
norm and objective residuals pass. The changed-target negative control shifts
support by -0.06902074514451273. Relevant validation passes 38/38; the reviewer
separately checked the three new tests and the source-bound saved results.

Root accepts this finite numerical comparison after the independent review
found no blocking correctness, regression, test, claim or maintainability defect.
The registered review is `.agent-harness/runs/R9-FIBRE-20260913/results/fibre_review.json`;
its report and independent decimal result are under that run's
`artifacts/fibre_review/`. No repair episode was necessary. The comparison is
DIAGNOSTIC_ONLY: it does not recover the original random target, certify every
basis or boundary, handle uncertain q, prove a physical bound, or admit four-axis
CAS. New alpha consumption is zero and every existing HOLD/quarantine remains.

A disjoint targeted readiness map is retained under `artifacts/dag_inputs/`.
Its FAIL outcome means required formal and observed-law prerequisites remain
unavailable, not that the numerical comparison failed. R9-02 needs a current
proposition-specific CAS contract and actual independent axis work. This is
pending implementation, distinct from the original preselection, FP/refitting,
richness, shared CF3 anchor and physical-response inputs that are not available.
Pinned Lean 4.31 core compilation and SymPy work; mathlib is not configured in
this project. A Sage-to-Singular probe was unmeasured at 30 seconds. Root corrects
one bounded inventory detail: `/usr/bin/Singular` exists; a lower-case `singular`
lookup does not establish absence. No formal capability is admitted by readiness.

User-repaired global authority 3379cc219ed6b5e44a2b50d7224324a89fdf77ab is installed.
The previously denied exact registered task was retried and native launch worked.
All five current hook hashes were approved/enabled through the official config
API with reloadUserConfig requested. The temporary server's reload is observed;
the existing desktop thread's reload and authenticated lifecycle are unverified.
No global policy source was changed, no old budget was reset and no local model
was dispatched in this stage. The trust receipt contains only hook identities;
private config backups remain outside this repository.

Both registered result envelopes are validated directly. The numerical review
PASS, readiness FAIL and unauthenticated aggregate remain separate. No whole-run
or scientific PASS is asserted. Canonical status and mirrors are synchronized;
the 150-completed checkpoint records the next R9 slice. Per explicit user
instruction, validation uses this existing worktree and delivery verifies only
the pushed remote ref, without a separate clone or verification worktree.

Checkpoint 150: 150/203 completed (73.89%), dependency-weighted completion
79.51%, longest-path completion 54/66 (81.82%). This is repository bookkeeping,
not scientific progress or R9 capability admission. The changed suite collected
and passed 38 tests with no skips; broad unrelated collection was not repeated.
No claim-tier drift was found in this increment. The operational report retains
PR-172/247 blockers and dormant external branches. The active research slice
continues with proposition-specific R9-02 depth execution and the missing
selected-law/physical inputs listed above, without reopening unchanged products.
Registered result validation reports zero errors for both envelopes; the run
closed normally while retaining readiness FAIL and numerical-review PASS.
