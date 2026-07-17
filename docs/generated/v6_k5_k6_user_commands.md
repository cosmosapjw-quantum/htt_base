# V6 K5/K6 User Commands

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_and_external_transfer_conditioned
sky_support_status: not_directional
null_mock_status: mixed_diagnostic_and_blocked
config_hash: `sha256:9326cc9796e442931f4d45a0304079f4a8112021f7c15cffba6409ab462877f8`
caveats:
- Commands only; this generator did not execute K5 or K6.
- Report stdout tail and the generated JSON path after running.
- No native low-ell solver output or family-identification claim is produced.
generating_command: python scripts/make_v6_no_download_figures.py
git_commit_or_worktree_state: content-addressed

## Commands

### K5

- input: `workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz`
- input_present: `True`
- next_turn_runnable: `False`
- run: `venv/bin/python scripts/k5_cf4_release_coverage.py`
- check after run: `venv/bin/python scripts/k5_cf4_release_coverage.py --check`
- note: execution forbidden while C1-K5-MV-F1 and N-DATA-CF4-DOWNSTREAM remain OPEN

### K6

- input: `workdir/raw/cf4/CF4pp_mean_std_grids.npz`
- input_present: `True`
- next_turn_runnable: `True`
- run: `venv/bin/python scripts/k6_cf4_curl_posterior.py`
- check after run: `venv/bin/python scripts/k6_cf4_curl_posterior.py --check`
- note: heavier grid/ensemble run; 128^3 velocity grid, N_CR=400
