# Next Session Prompt

Resume the recovered MES methodology implementation in the isolated worktree
`/home/cosmosapjw/worktrees/htt-mes-integration-20260826` on branch
`changeset/pr324-mes-methodology-stack-20260826`.

## Current position

- Accepted start: `8b6028abcde18c87591789f6ba53e81157fa4eba`.
- PR-326 repaired content head: `e938756120bb084e28a678bb0fcd733a4a6158e5`.
- Canonical state after the pending closeout commit: 205/273 complete,
  PR-327 in progress, PR-151 background-only.
- PR-322..PR-326 are complete. Execute PR-327, then PR-328, PR-329, and
  PR-330; do not create another planning successor.

## Execute PR-327

1. Preserve the exact PR-315 observation plus 300 paired SMICA null rows and
   the PR-314 five-file control evidence.
2. Extend `scripts/observed_runs/run_planck_mes_morphology.py` without breaking
   the PR-325 row-anchor entrypoint.
3. Apply one preregistered row operator to every row: sigma anchor, omega
   anchor, and the eight dimensionless morphology invariants. Do not use raw
   `cl_l2/cl_l3` as duplicate amplitudes and do not fabricate directions.
4. Use the existing observation-inclusive row-equivariant max scan. Emit one
   portable 301-row package, pooled diagnostic covariance, exact finite rank,
   replay receipt, and mutation/equivariance checks.
5. Preserve generic control `133/301`; label the MES result separately. Keep
   `directional_moment_state=BLOCKED_DIRECTIONAL_SUPPORT` and
   Planck-only local/global status nonidentified.
6. Run targeted tests, negative/metamorphic tests, directly affected
   integration, and focused CI only. Obtain at most one fresh review and repair
   only reproduced material defects.

## PR-327 non-negotiable tests

- exact 301-row source/operator/covariance identities;
- row permutation and observation-index swap equivariance;
- observation-only/missing-anchor refusal;
- directional support stays blocked;
- PR-314 five Git blobs and `133/301` result remain unchanged;
- package mutation and replay mismatch fail closed;
- no import of legacy `planck_mes_bounds.py`.

## Hard stops

- Any scalar-to-vector/axis/STF fabrication.
- Commander or 999 CMB-only rows made prerequisites for Paper A.
- Any Planck-only local/global identification or pre-native family claim.
- Any source-only/superseded bulk merge, automatic PR close, security scope,
  full unrelated suite, or expectation/reference-output change without
  authority.
