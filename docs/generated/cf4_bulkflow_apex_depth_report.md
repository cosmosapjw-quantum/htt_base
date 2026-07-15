# CF4++ Bulk-Flow Apex Versus Depth (REV-R104)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
status: RECONSTRUCTION_CONDITIONED_SYSTEMATICS_DIAGNOSTIC
allowed_use: paper_appendix
finding_state: C1-K5-MV-F1 OPEN (canonical PR-120 block)
transfer_source: external_proxy_cf4_wf_reconstruction
null_mock_status: bootstrap_over_correlated_reconstruction_cells
config_hash: `sha256:c0dc4ac51378f4780aaf783e21246a3466a032182c6fb90f1e903e4994943edb`
input_hashes:
- sha256:5fb994ca076235fb30db644d3d1a3672d092ed31f8ef4737bcabe2da87491909
- sha256:77d36878315f041c7bb6c273a2d650f7d3fa1c8a8dc635a577527d646fa40109
generating_command: `python scripts/make_cf4_bulkflow_apex_depth.py`
git_commit_or_worktree_state: `e6da367+dirty`

Full-sample reconstruction functional: 133.4 km/s toward Galactic (l, b) = 121.6, 70.8 deg.

## Bulk-flow apex by depth shell

| r [Mpc/h] | N cells | |B| [km/s] | apex l,b [deg] | drift vs full [deg] | angle to CMB apex [deg] |
| --- | --- | --- | --- | --- | --- |
| 90-150 | 6749 | 378 (+6/5) | 300, 24 | 84.8 | 36.9 |
| 150-200 | 10254 | 531 (+4/4) | 301, 63 | 45.8 | 25.3 |
| 200-250 | 16091 | 584 (+4/4) | 239, 88 | 20.2 | 39.9 |
| 250-300 | 21788 | 588 (+4/4) | 133, 75 | 5.5 | 52.5 |
| 300-350 | 27890 | 222 (+2/2) | 114, 48 | 23.1 | 80.4 |
| 350-400 | 35806 | 128 (+1/2) | 114, -49 | 119.9 | 160.6 |
| 400-450 | 45179 | 186 (+1/1) | 120, -78 | 148.7 | 147.5 |

## Caveats

- numerical rows are functionals of one CF4++ Wiener-filter reconstruction, not observed bulk-flow amplitude measurements
- the plotted vectors are volume-averaged reconstruction velocities per shell
- bootstrap is over correlated reconstruction cells; a lower bound on the true direction uncertainty, not a full covariance
- no native low-ell solver output or Bianchi family identification
- C1-K5-MV-F1 remains OPEN; no global-tilt coordinate or cosmological inference is permitted
