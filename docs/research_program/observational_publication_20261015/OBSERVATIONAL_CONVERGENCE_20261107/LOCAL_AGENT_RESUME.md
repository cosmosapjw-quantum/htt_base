# Local coding-agent resume prompt — HTT R38 observational convergence

You are resuming the user's existing HTT research checkout. This is a bounded convergence-oriented project. Preserve every existing runtime, worktree, uncommitted change, acquisition reservation, artifact and scientific receipt.

## GitHub authority / branch

Repository: https://github.com/cosmosapjw-quantum/htt_base

New branch to fetch/checkout: research/observational-convergence-r38-20261107

Branch parent: research/htt-adaptive-methods-20261023 at cab89d25af52a1b978a4da8c11eecdc25bb22759 (PR #564 merge).

Research contract directory:
docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107/

Read first:
1. README_KO.md
2. RESEARCH_DAG.json
3. CLAIM_LEDGER.json
4. THEORY_AND_OBSERVABLES.md
5. DATA_AND_SAMPLER_PLAN.md
6. PR_LEGACY_AUDIT.md
7. this handoff.

Do not use Remote Desktop Commander or GUI/desktop control. Use the existing local checkout and normal GitHub fetch/push. Do not create a fresh clone/worktree unless the current environment is conclusively unavailable and the user authorizes it. Do not reset, clean, force-checkout, overwrite, kill processes, or restart a long-running task to make the workspace look tidy.

## Phase A — preserve and fingerprint current local state

1. Record git status --porcelain=v2 -b, current branch, HEAD, remotes, worktrees, active processes/long-running commands, task queues/reservations, and uncommitted diff identities. Do not stage or alter existing changes.
2. Fetch the new R38 branch. Compare it to the current local branch and report merge-base, ahead/behind and changed paths. If local work is ahead or diverged, preserve it on a separate branch/receipt; do not reset to R38.
3. Verify the GitHub tree/commit and all R38 document blob identities. Do not treat checkout of the new plan as authorization to replace the current active branch.

## Phase B — exact local data inventory before downloads

1. Inspect historical data-root manifests and only exact directories they identify. Current repo documents mention historical roots such as /mnt/extdrive/workdir/htt_open_data, but a path is not proof that the device is mounted today. Discover existing mounts without modifying/remounting them.
2. Enumerate candidate files by dataset/release/product, byte size, SHA256, FITS headers/HDU, row counts, stable identifiers, units, coordinate/redshift frames and covariance identity.
3. Produce LOCAL_DATA_INVENTORY.json and a payload SHA manifest. Distinguish verified local file, prior user-reported receipt only, GitHub metadata only, and unavailable/missing source.
4. Reconcile CF4 exactly: public VizieR Table 2 has 55,877 individual galaxy rows; grouped Tables 3/4 have 38,053 rows; prior project operator uses 35,970 selected rows. Explain row map, exclusions, join keys and selection. Do not call sample geometry a physical Hubble anisotropy.
5. Reconcile Planck PR3/PR4 maps, SMICA/Commander, masks, beams, pixel windows, frequency maps, splits, FFP10 and covariance. Verify raw FITS hashes before use; processing label is not an independent sky.
6. Reconcile Pantheon+ exact 1,701-row vector and covariance with existing 490/705-row selected blocks. Prove row-order mapping and covariance subsetting; do not symmetrize or diagonalize to force a pass.
7. Verify Quaia G<20.0 catalogue, matching selection function and random catalogue as one release family. Verify NVSS/RACS completeness/flux/tile/depth maps and Gaia DR3 quality/frame corrections.

Only missing and specifically required products may be downloaded. Prefer official sources in DATA_AND_SAMPLER_PLAN.md. Use cache-first retrieval, resume-safe writes to a new path, SHA256 after download, and retain originals. Do not bulk-download the entire Planck low-resolution archive or all DESI LSS catalogues before proving they are required.

## Phase C — code correction and local verification

Inspect current source and tests before editing. Make focused changes only:
- common covariance validator and Cholesky/triangular-solve utility;
- exact vector/covariance row selection with persisted source-key map;
- immutable data/response manifests;
- frame-aware beta_RO/beta_RM/beta_MO and intrinsic-dipole parameterization;
- nuisance-projected SVD, null-space and rank-stability output;
- separate Planck frequency/component/simulation products and same-sky covariance;
- keep E1/B1 polar/axial carrier distinct from E2/STF5 shear-history carrier;
- Cobaya Theory and dataset Likelihood adapters after finding existing package conventions.

Required tests: malformed/non-finite arrays; covariance not symmetric/positive definite; wrong row order; covariance subsetting mismatch; duplicate source IDs; missing random/selection product; frame/unit mismatch; unsupported response silently replaced by zero; duplicate same-sky likelihood; prior-induced rank inflation; beta^2 truncation misuse; masked-sky estimator against exact response oracle.

Run focused tests first and appropriate adjacent regression suite. Record exact command, environment, package versions, stdout/stderr, exit status and hashes. Do not claim full-suite pass unless actually run. If a defect requires a broad refactor, write a bounded issue/decision instead of widening scope.

## Phase D — actual observational analysis, ordered gates

1. Build deterministic single-probe adapters and synthetic injection/recovery fixtures. Synthetic data validate coverage/software only.
2. Fit M0 on Planck low-ell map/harmonic data with correct beams/masks/FFP noise/foreground covariance.
3. Fit radio NVSS/RACS and Quaia separately with their flux/depth/selection/randoms; infer beta-like count responses.
4. Fit Pantheon+ and CF4 directional distance/H(z,n) windows with exact full covariance and frame corrections.
5. Fit Gaia DR3 VSH coefficients with frame spin/glide nuisance and redshift bins.
6. Add DESI DR2 BAO/AP and ACT DR6 only as specified by data support; compressed BAO points are not a sky map.
7. Evaluate nuisance-projected response singular spectrum before joint sampling. If local boost, intrinsic dipole and global tilt are not separately identifiable, return identified quotient and sharp bounds.
8. Only after all single-probe gates pass, run M0→M1→M2 joint Cobaya posterior. Add Bianchi family M3 only with validated family-specific forward response.
9. Keep the five-variable HTT state as structured inference product, not five independent likelihood terms. Preserve full covariance and nullspace/fibre/path information.
10. Run posterior predictive checks, selection-preserving nulls, leave-one-probe-out and mask/beam/foreground/calibration sensitivities. Report a physical detection only if independent response channels and nuisance tests support it.

## Phase E — handoff and push

Required artifacts:
- LOCAL_DATA_INVENTORY.json and SHA256 manifest;
- exact source/selection/covariance manifests;
- corrected code and focused tests;
- individual probe likelihood configs and results;
- joint Cobaya config, chains, convergence and posterior predictive diagnostics;
- identifiability matrix, singular values, null vectors and five-variable tensorized output;
- claim-evidence map updating CLAIM_LEDGER.json;
- concise local execution report with unrun/blocked items.

Large FITS/catalogues/chains stay outside Git; push only code, tests, configs, compact result summaries, manifests and relative paths. Commit on the R38 branch and push to GitHub. Do not merge to main or submit a paper. Before marking any DAG node qualified, compare its acceptance criteria literally and attach exact file/hash/source evidence.