# REV-R111 - LR-06F: CF4++ affine local-flow gradient posterior

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: cf4_reconstruction_grid
null_mock_status: bootstrap_over_correlated_reconstruction_cells
generating_command: `python scripts/make_cf4_affine_flow.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Continue the runnable LR-06 work. LR-06F (3D local-flow gradient posterior)
needs only the CF4++ reconstruction field, which is already local, and no native
low-ell solver, so it is executed now.

## Result

`htt/obsstat/affine_flow.py` fits the affine flow v = B + M r in spheres about
the observer on the local CF4++ supergalactic velocity grid (128^3, 1000 Mpc box,
7.81 Mpc cells) and splits the velocity-gradient tensor M into bulk B, expansion
Theta = tr(M), trace-free shear sigma, and vorticity omega.

| R [Mpc] | N cells | bulk |B| [km/s] | shear [km/s/Mpc] | vorticity [km/s/Mpc] |
| --- | ---: | ---: | ---: | ---: |
| 50  | 1088   | 152 | 12.85 | 0.030 |
| 100 | 8744   | 262 | 3.18  | 0.018 |
| 150 | 29464  | 316 | 1.15  | 0.002 |
| 200 | 70320  | 359 | 1.26  | 0.0005 |
| 250 | 137376 | 422 | 1.28  | 0.0004 |

- Bulk flow grows 152 -> 422 km/s over 50-250 Mpc (consistent with CF4 bulk-flow
  literature). Bootstrap at 150 Mpc: |B| = 315.6 +/- 2.0 km/s (lower bound).
- Vorticity is ~0 and falls with radius: the CF4 reconstruction is curl-suppressed
  by construction, so this is the honest reconstruction-conditioned result, not a
  detection.
- Curl-injection recovery: an injected solid-body rotation is recovered with
  rel-error 3e-16 — the estimator's curl channel is validated independently of
  the (near-zero) data vorticity.

## Claim boundary

Diagnostic-only OBSSTAT feature extraction. Vorticity reconstruction-conditioned;
expansion is the local reconstruction divergence, not H0; bootstrap is a lower
bound, not a calibrated covariance. Cross-reconstruction comparison is
`BLOCKED_MISSING_FIELD_REALIZATIONS` (only CF4++ is local). No Bianchi, geometry,
or cosmological-frame-violation claim.

## Validation

| Command | Status |
| --- | --- |
| `pytest tests/obsstat/test_affine_flow.py` | 5 passed (decomposition, exact affine recovery, curl injection) |
| `python scripts/make_cf4_affine_flow.py` | report + figure written; curl-inj rel-err 3e-16 |
