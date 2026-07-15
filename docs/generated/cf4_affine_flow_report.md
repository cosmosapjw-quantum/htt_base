# CF4++ Affine Local-Flow Decomposition (LR-06F)

owner: OBSSTAT · claim_tier: diagnostic_only · status: RECONSTRUCTION_CONDITIONED_SYSTEMATICS_DIAGNOSTIC · ticket: LR-06F
allowed_use: paper_appendix
config_hash: `sha256:b467431f9f9099233040fe1b507a4c781bf2e3104ad5ecb69db0a0e514f85e63`
input_hashes:
- workdir/raw/cf4/CF4pp_mean_std_grids.npz:sha256:78c0515c8330066a034f5e8afb3663e6c81ddf033db302a921c662344639bc91
- docs/codex_handoff/research_remediation_state.yaml:sha256:77d36878315f041c7bb6c273a2d650f7d3fa1c8a8dc635a577527d646fa40109
generating_command: `python scripts/make_cf4_affine_flow.py`
git_commit_or_worktree_state: e6da367+dirty
finding_state: C1-K5-MV-F1 OPEN (canonical PR-120 block)
grid: 128^3, box 1000.0 Mpc, cell 7.8125 Mpc (supergalactic_cartesian)

## Affine fit vs sphere radius

| R [Mpc] | N cells | bulk |B| [km/s] | expansion Theta [km/s/Mpc] | shear [km/s/Mpc] | vorticity [km/s/Mpc] |
| --- | ---: | ---: | ---: | ---: | ---: |
| 50 | 1088 | 152.1 | 6.6636 | 12.8460 | 0.03043 |
| 100 | 8744 | 262.3 | -6.7760 | 3.1779 | 0.01754 |
| 150 | 29464 | 315.5 | -8.7259 | 1.1538 | 0.00204 |
| 200 | 70320 | 359.3 | -8.2461 | 1.2556 | 0.00050 |
| 250 | 137376 | 422.0 | -1.1947 | 1.2761 | 0.00039 |

## Bootstrap at R=150 Mpc (lower bound, correlated cells)

- bulk |B| = 315.6 +/- 2.0 km/s
- expansion Theta = -8.7282 +/- 0.0644 km/s/Mpc
- shear = 1.1555 +/- 0.0266 km/s/Mpc
- vorticity = 0.03490 +/- 0.01552 km/s/Mpc

## Curl-injection recovery (estimator validation)

- injected omega = [0.0, 0.0, 1.0] km/s/Mpc
- recovered omega = [-0.0, -0.0, 1.0] km/s/Mpc
- abs error = 2.989e-16, rel error = 2.989e-16

## Cross-reconstruction: BLOCKED_MISSING_FIELD_REALIZATIONS

only the CF4++ reconstruction is available locally; a second independent reconstruction is required for the cross-reconstruction comparison.

## Caveats

- Numerical rows are functionals of one CF4++ Wiener-filter reconstruction, not observed bulk-flow amplitude measurements.
- Vorticity is reconstruction-conditioned: potential/Wiener reconstructions suppress curl by construction, so a small recovered omega is a reconstruction property, not a detection.
- Bootstrap over correlated reconstruction cells is a lower bound on the uncertainty, not a calibrated covariance.
- Expansion Theta is the local divergence of the reconstruction, not a global H0 measurement.
- C1-K5-MV-F1 remains OPEN; no global-tilt coordinate or cosmological inference is permitted.
- No Bianchi/geometry/cosmological-frame-violation claim.
