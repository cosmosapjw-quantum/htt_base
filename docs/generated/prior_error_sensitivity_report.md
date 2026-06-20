# Prior/Error Sensitivity Report (REV-R096)

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:fa1284f724c798ec70612aaf12bc00ac7ba4d9a0bc088fad460cf63519e963e2`
input_hashes:
- docs/generated/current_science_plot_payload.json:prior_support_proxy
generating_command: `venv/bin/python -m htt.infer.prior_error_sensitivity`
git_commit_or_worktree_state: `prior_error_sensitivity_fixture`

## Robustness

- ln B robust range: [-39.1, 26.4] (spread 65.5)
- Sign flip detected: true
- Single Jeffreys label allowed: false
- Rows are marginal likelihoods: false
- Boundary-mass status: not_computed_placeholder
- KL divergence status: not_computed_placeholder

## Grid

| prior_floor | ceiling | sigma_beta | lnB |
| --- | --- | --- | --- |
| 1e-12 | 1.0 | 0.00027 | 26.4 |
| 1e-06 | 1.0 | 0.00027 | -39.1 |
| 1e-09 | 1.0 | 0.00054 | 3.2 |

## Caveats

- prior/error sensitivity gate, not an evidence run
- a sign flip across the grid blocks any single Jeffreys label
- boundary-mass and KL diagnostics are placeholders, not computed
- no native low-ell solver output is introduced
