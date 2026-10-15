# Review-only recovery: CF4 apparent STF2 scalar normalization

Date: 2026-10-16 KST. Authoring source: last known dirty checkout on `obs/solver-free-dossier-20261014`, head `13d8d85fa470d645d008986e8f77d8d0f70fdf54`. Work was **not** applied to the owner's working tree. GitHub publishing is an isolated, draft-only staged candidate; main and PR #533 remain unchanged.

## Constructive mathematical result

For a Frobenius-orthonormal STF basis `T_A` and angular fit `A_ij=Σ_A a_A T_Aij`, `A_ij A^ij=Σ_A a_A²`. If, and only if, the nontrivial physical identification `A_ij=σ_ij/H` is supplied, the standard shear definition `σ²=σ_ijσ^ij/2` and `θ=3H` imply `σ/H=||a||/√2`, `σ/θ=||a||/(3√2)`, `Σ²=||a||²/6`. This is a mathematical rescaling under a hypothesis, **not a physical Bianchi shear observation**.

The uncommitted 2026-10-15 Loop6 code output used `||a||` for a label named `sigma_over_H` and `||a||/3` for `sigma_over_theta`. Its `Sigma²=||a||²/6` was already correct. This candidate corrects only the two labels' conditional scalar normalization and adds coefficient-norm fields without changing `A`, likelihood, original CF4 observations, source weights, or native transfer.

Reference: Caceres et al., *Shear Dynamics in Bianchi I Cosmology*, arXiv:1003.3491, shear definitions and Eq.31. Independent Wolfram result: Tr(S)=0, Tr(S S^T)=Σ_A a_A², Tr(S S^T)/6=Σ_A a_A²/6.

## Evidence actually executed

The candidate Python module Git blob is `f350ea5b563cf5dcf1e4952e37b24461a8421d7b` (SHA256 `ef354266fb99d965305961524e50367a3b9dd114e7b51cbbf32a1f2380dbb386`); test Git blob `bfc20891b99ebfeec2006e55281f9161efa65668` (SHA256 `0d88dc70f14ae5f517833c8c753e13d27a396c48a10030d007e3dfe7189dff4b`). Both were independently matched to the bytes run in the ChatGPT container before GitHub upload. Full Python test path: **10 passed in 0.25 s** on isolated ChatGPT container, not owner's workstation.

The original CF4 case JSON SHA256 is `9764f6e865832e921bd9801e45790f378fa306931e7d4db41a3f4fa38352d254`, with 35,970 source groups and nine conditions. Separate non-mutating correction recomputed all 9 cases. The stored 30,000 STF coefficient draws yield max corrected quantile difference `3.469446951953614e-18`, compared to `2e-15` gate; WLS original likelihood not rerun.

Fiducial dimensionless `||a||=0.03325774236`; older `||a||/3=0.01108591412`; corrected conditional `σ/θ=0.0078389250503`. This is not a measured geometry-frame shear, posterior, tilt or Bianchi identification.

Exact immutable originals, patch, executable standalone audit source, tests, all 9 cases, stored NPZ arrays, 28-PR scope index, and SHA manifest are additionally preserved in the checked `HTT_CF4_STF_DIRTY_RECOVERY_20261016.zip` archival backup (2,413,414 bytes, SHA256 `85df2d2f4fa5ac2a8bcd7e6e13d00954a20c225ab50d4ad60d7ead35f0ba0990`). User-facing chat link and ChatGPT Library path: `/HTT_RESEARCH_BACKUPS/20261016_CF4_STF/HTT_CF4_STF_DIRTY_RECOVERY_20261016.zip`.

## Boundaries and next actions

This directory is intentionally a **staged candidate** under `docs/`, not a mutation to existing user-owned untracked `htt/obsstat` or `tests/obsstat` files. It is not deployable as canonical package code without a controlled local reconciliation.

- Software numerical check: PASS_SCOPED_CONDITIONAL (sandbox only).
- Fresh native independent-review gate: NOT_RUN, native subagent tool absent.
- Local execution: BLOCKED_RUNTIME_QUOTA (Remote Desktop Commander exhausted; do not retry).
- Scientific physical admission: HOLD_UNCHANGED. Actual CF4 selection, cross-method covariance, observer congruence, optical transfer and Bianchi shear source remain missing.
- Branch: draft-only pending review. No main merge, no paper submission, no updated physical posteriority.

The original user's uncommitted Loop1–7 research still has unmerged work. Prioritize reviewing and integrating this candidate after local access is restored, then ready Loop7 `C8-OBS-MES-EPS` and `C8-CF4-METHOD` (mathematical/conditional), while `T8-GEOM-SOURCE`, `C8-REAL-JOINT` remain physically blocked.
