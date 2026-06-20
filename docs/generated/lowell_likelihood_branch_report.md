# Low-ell Likelihood Branch Report (REV-R099)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R099 split low-ell likelihood branches`
git_commit_or_worktree_state: pending_rev_r099_commit

## Purpose

Split the two admissible low-ell Bianchi likelihood branches and forbid a
central scalar chi-square from standing in for either. Enforced by
`obsstat.lowell_likelihood_branches.classify_lowell_likelihood`.

## Branches

### Mean-template branch (`deterministic_mean_template`)

Bianchi enters as a deterministic mean template. It requires a harmonic-space
template AND either orientation marginalization or a noncentral statistic.
A central scalar chi-square (e.g. a `D2_D3_scalar` feature) with
`orientation_status = not_marginalized` is blocked with
`noncentral_or_harmonic_orientation_required`.

### Covariance / BiPoSH branch (`stochastic_covariance`)

Bianchi enters as a stochastic anisotropic covariance. It requires a full
anisotropic covariance. A `diagonal_only` or `not_bound` covariance is blocked
with `full_covariance_not_bound`.

## Why a central scalar chi-square is insufficient

A central scalar chi-square is neither harmonic nor noncentral (so it fails the
mean-template branch) and is not a full anisotropic covariance (so it fails the
covariance branch). It therefore closes neither branch.

## Manuscript impact

- `docs/manuscript/ch07_results.tex`: the D2/D3 scalar chi-square statistics now
  carry an explicit low-ell likelihood branch caveat.
- `docs/manuscript/ch09_discussion.tex`: the discussion records that a genuine
  low-ell test must take one of the two branches; the native low-ell atlas
  remains the prerequisite.

## Status

- Both branches remain blocked for a central scalar chi-square.
- Closing either branch requires the native low-ell morphology atlas.
