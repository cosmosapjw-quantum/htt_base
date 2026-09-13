# PR-R9-INTAKE — Preserve the complete product law through R9 paths

The current branch lacked the donor depth module and had no R9 production
intake. This change adds shared state incidence and product intake on the
existing R7 `JointObservationLaw`, then transforms observed values, means,
responses and the entire covariance together. For three independent scalar
levels the contrast covariance is [[2,-1],[-1,2]]; keeping Y0 also retains its
cross covariance and common-level signal. Original Y and its transformed view
are never independent likelihood factors.

Start: `9e9539edcdbd7bbf66e458cdce685c7a112f8a04`; user-directed successor of
PR-R9-REV2 on the same branch. The underlying Gaussian API last changed at
`619ef82decf97aa695a9e9022c7cfd0cb4863d3a`; DESI law at
`8b64fb8c00cc272de5f88937c41528f2d485cee4`. The separately pinned 6bafca66 donor
was not merged or treated as current code. Both exact GPT-6 archives/member
sets were freshly verified and their research/coding contracts applied.

## Validation and actual product

- Original revision2/run_checks.py: three exits 0 in a separate source copy;
  old evidence remains unchanged. Same rejection counts; fibre SVD-coordinate
  random direction differs with NumPy, so identical fibre-target replay is
  not asserted. Original tolerances and all invariant assertions are unchanged.
- 55 relevant tests pass, including covariance cross terms, rectangular paths,
  shared nuisance Jacobians, support/rank refusal, fitted-law rejection,
  joint jet-anchor coverage and nonregular fibre-boundary tests.
- Actual retained DESI DR1 BGS syst qiso HDF5 was decoded, passed through the
  common embedding and existing Gaussian inversion, and checked with 100000
  conditional model draws (1225 rejections). At alpha=1/80 the conditional
  qiso interval is [0.9361855679766953, 1.02957531539111].
- One native independent review and one targeted repair-closeout are registered.
  Initial independent review found no blockers. Owner then reproduced two
  narrow errors: a numeric confidence label despite an undefined denominator
  witness, and full-past conditioning that tolerated an impossible original
  nullspace component. Both failures and fixes are retained; 55 tests and a
  new source-bound product result pass after correction. Initial review source
  bytes are preserved against its prerepair seals.

The default Python lacks optional h5py; the product runner uses an existing
compatible lowell environment. No packages, services or models were installed.
The public DESI product documentation was checked for release/HDF5 semantics;
no newer input release was substituted. First canonical-card validation failed
because its explicit topological order lacked the new card; the order and
mirror were corrected without changing gates.

## Limits and continuation

This is scoped implementation and conditional product validation. R9-24 formal
admission and R9-25 actual eligible multi-depth covariance remain HOLD. The
prepared scalar DESI product has NO_DEPTH_CONTRASTS, and no raw-survey coverage
or physical state-jet-anchor confidence event is supplied. Production,
empirical, novelty and four-axis holds, R8 STOP_INVALID/25 unresolved pools,
CF4 quarantine, PR4 skip, Union3 scenario and all error budgets remain intact.
The original R9 aggregate remains historical non-PASS. Default-cwd hook lookup
used an unrelated past run; no authenticated hook/profile claim is made.

Evidence and current handoff: `docs/research_program/tensor_joint_r9/revision2/implementation/`.
Root is sole production writer; mapper and reviewer wrote only unique result
files. No native solver, reference/tolerance change or scientific claim
promotion. Scientific covariance/provider gaps are distinct from environment
and packaging issues. Ordinary non-force push and exact remote ref/file
readback follow the final review and canonical state update.
