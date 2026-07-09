# v7 Fortification Witnesses

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
config_hash: `sha256:5dfa0816bff10b74c722de50c9b5969e9c5f93d92a67ce54306dc38d87648be8`
generating_command: `venv/bin/python scripts/run_v7_fortification_witnesses.py`

| Witness | Verdict | Claim |
| --- | --- | --- |
| `F1_signed_box_identified_set` | `PASS` | signed component boxes with open/all curvature branches |
| `M1_gf_strictness` | `PASS` | joint interval is a subset of naive; strictness requires shared-extrema conflict |
| `M3_estimated_covariance_two_stage` | `PASS` | finite-simulation covariance uses Hotelling/F threshold |
| `M8_gate_policy` | `PASS` | printed tolerance rules reproduce the v6 pass decisions |
| `K5_plugin_firewall` | `PASS` | K5 card remains diagnostic until PLUGIN/BLOCKED components are replaced |

## Caveats

- Synthetic/statistical witness artifact only.
- No data claim, posterior odds, native solver output, or morphology-family promotion.
- K5 plugin-firewall witness references the companion K5 card output.
