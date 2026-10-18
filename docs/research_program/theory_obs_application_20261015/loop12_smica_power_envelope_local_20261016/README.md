# Loop 12: local SMICA finite power envelope

This scoped continuation consumes PR #536's exact Loop 9 `K6..16`, PR #537's actual local-source `K17..32`, and PR #538's read-only source-bound synthetic power contract. It adds no empirical `C_l` or physical EGS response.

- `results/ell17_32_source_v1/`: raw create-only output of PR #537 `code/run_local_source.py` executed from an exact Git-object extraction in `/tmp/c8-pr538-review-20261016/htt_base`. The extraction contains code and test files, not a new repository checkout. The existing Loop 9 directory was linked read-only for source lookup; its NPZ was not copied. The raw JSON retains that execution's absolute path keys.
- `results/power_envelope_v2/`: final source-locked 32×1053 operator and three explicitly hypothetical covariance/ellipsoid scenarios. `power_envelope_v1` remains local raw first-attempt evidence and is not part of the published candidate.
- `RUN_RECEIPT.json`: exact commands, exits, source/result hashes and independent-review status.
- `NEXT_RESEARCH_DAG.json`: successor research DAG; its byte-identical compatibility mirror is under `machine_readable/research_program/theory_obs_application_20261015/loop12_smica_power_envelope_local_20261016/`.

To create a new result, use a fresh `--output` directory. The published `src/run_extended_power_envelope.py` hashes the actual Planck full SMICA FITS, masks, K1 cache, both finite operator files and predecessor references before calculation. A rerun of the PR #537 source runner from another absolute directory can yield a different *JSON byte SHA* because it records absolute paths; compare its source SHA fields, pixel support, replay residuals, matrix SHA and numerical invariants. The frozen local-run JSON/NPZ SHA values are in `RUN_RECEIPT.json`.

Scientific ceiling: `SOURCE_CONDITIONAL_MASK_GEOMETRY_SCENARIOS_ONLY`. Physical EGS and Bianchi shear/tilt remain HOLD.
