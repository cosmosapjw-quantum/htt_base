# Predictive Adequacy Report (REV-R098)

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:55e61191cf6687981bf5e797a660890dbc00831f8993e21a454c6ccc22551cc3`
input_hashes:
- docs/generated/result_pack_B.md:channel_b_ppc
generating_command: `venv/bin/python -m htt.infer.predictive_adequacy`
git_commit_or_worktree_state: `predictive_adequacy_fixture`

## Adequacy

- PPC p-value: 0.012 (threshold 0.05)
- PPC failed: true
- LOOCV status: not_run
- Adequacy status: failed
- Evidence claim allowed: false
- Blocked reasons: ppc_failure, loocv_not_run

## Required next models

- single_beta
- survey_specific_amplitudes
- mixture_outlier
- systematic_response

## Caveats

- a failed PPC or unrun LOOCV blocks any channel evidence claim
- blocked status holds until a later model comparison fixes it
- no native low-ell solver output is introduced
