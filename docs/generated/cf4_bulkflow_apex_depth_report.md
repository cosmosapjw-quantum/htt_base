# CF4++ Bulk-Flow Apex Versus Depth (REV-R104)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
null_mock_status: bootstrap_over_correlated_reconstruction_cells
config_hash: `sha256:c0dc4ac51378f4780aaf783e21246a3466a032182c6fb90f1e903e4994943edb`
input_hashes:
- sha256:5fb994ca076235fb30db644d3d1a3672d092ed31f8ef4737bcabe2da87491909
generating_command: `python scripts/make_cf4_bulkflow_apex_depth.py`
git_commit_or_worktree_state: `7888011+dirty`

Full-sample bulk flow: 133.4 km/s toward Galactic (l, b) = 121.6, 70.8 deg.

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

- model-independent kinematic descriptor; not evidence for any Bianchi model and not a cosmological-frame-violation claim
- bulk flow is the volume-averaged CF4 reconstruction velocity per shell
- bootstrap is over correlated reconstruction cells; a lower bound on the true direction uncertainty, not a full covariance
- no native low-ell solver output or Bianchi family identification
