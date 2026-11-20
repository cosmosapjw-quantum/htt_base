# R87 P0-B → P0-C 연구 인계 (실행용 START handoff 아님)

**2026-11-20 KST. R87 P0-B source-diagnostic slice completed; physical likelihood remains BLOCKED.**

Repo cosmosapjw-quantum/htt_base
Branch research/r69-observable-physics-bridges-20261118
Scientific R78 SSOT docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json, original science 42 payload SHA e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d, 60 nodes / 129 edges, next SQ-CF4.
Source R80 original CDS table3/table4/ReadMe and R54/R58 selected 35,970 group NPZ exact pinned bytes in R87/RESULT.json; no raw source modified.

## Completed code/science diagnostics
Source code htt/obsstat/cf4_p0b.py, tests/obsstat/test_r87_cf4_p0b.py, create-only runner scripts/r87/run_p0b.py. Exact six-measured-method group-profiled weighted Fisher graph Laplacian, SNIA=0 coordinate gauge, seven R80 method flags and unique group lineage. 926 real multiple method-presence groups but 922 error-bearing overlap groups; graph rank5; post-calibrated residual method contrasts and source-selection conditional on released table; four disjoint RA-group sky blocks heldout in downstream already intercalibrated products, NOT independent original calibration coverage. Conditional low-rank bulk/shear velocity-mode scenario reuses htt.obsstat.pv_covariance on actual selected positions and original H03 design, including exact theorem U=X A -> unchanged GLS mean + covariance inflation. No true physical S_PV or C_sel was constructed.

Source report: docs/research_program/observational_publication_20261015/R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120/{REPORT_KO,THEORY_KO,CONTRACT}.md and RESULT.json. Verified new tests 13/13 and expanded related R79-R87 scoped 281/281, R86 readiness 9/9 and R78 authority 32/32. This is not full repository CI, no source-calibrated cosmos null nor actual normal shear.

## Remaining science blocker
To satisfy SQ-CF4 full physics rather than only source diagnostics, require original *pre-intercalibration* per-indicator distances or calibrated released MCMC zero-point posterior/relative method response Jacobian, physical PV covariance or its source-matched independent field-realization ensemble, survey selection/completeness and end-to-end independent heldout/mock coverage. Missing blocks must remain explicit None/UNKNOWN. Published group method moduli cannot be treated as independent calibration posterior because upstream MCMC already used group overlaps. Fixed 4-quadrant spatial prediction improves a working residual, not upstream independent calibration coverage.

Source-qualifier SQ-CF4 remains ready_scoped for bounded diagnostics, NOT science complete. Physical status BLOCKED_PHYSICAL_PV_CALIBRATION_SELECTION_AND_HELDOUT; H02/H04/K04/PHY outputs not promoted. This is a legitimate partial source result and exact specified blocked status; do not manufacture C_selection, all-sky null or galaxy covariance.

## Next owner-selected software phase P0-C (NOT EXECUTED IN R87)
Implement a minimal **read-only fail-closed R78 60-node SQ-CF4 adapter** operating on exact R78/ R86 and R87 outputs and original source SHA, with the following acceptance:
1. Print source + scientific input contract (actual selected 35,970, R80 raw 7 methods/geo, R87 residual contrast/heldout, missing true PV/calibration/selection covariance) and node dependencies/acceptance/STOP.
2. Accept only explicitly selected bounded science node SQ-CF4 dry-run; unknown, B02, pending scientific nodes fail-closed. Never silently interpret 42-node original CLI ready_now=0 as a qualified 60-node dispatch.
3. P0-B actual missing covariance/independent heldout must yield **BLOCKED_INPUT** in the packet, not fake scientific PASS. Track callable input/output ownership, source SHA, predeclared true physical source null required and authority.
4. Add unit tests for 60 exact IDs and 129 edges, source SHA mismatch, observer frame, unqualified physical C, source already globally calibrated, R83 sealed code and no actual local agent start. R78 original 42 science and seven PHY remain unchanged.
5. Do not issue agent START, push a new branch, merge main, or run full science DAG without explicit later owner approval.

## Reproduction
From repo root:
    export PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
    .venv/bin/python -B scripts/r87/run_p0b.py --output /tmp/r87_manual_NEW.json
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r87_cf4_p0b.py
    .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority
The runner uses create-only outputs. Do not overwrite /tmp/r87_manual_NEW.json if already present; use a unique path on rerun. Native binaries for older lanes remain outside Git and are optional; R87 uses optimized NumPy/SciPy and source-conditional Woodbury.

Original R79–R85 fast lane and coding source closure remain configured. Original R87 tracked Git commits and provenance should be checked against actual HEAD before performing P0-C. No native delegated research subagent was exposed in current host; don't report parallel subagent verified.

## Final source verification (2026-11-21 KST)
Result JSON is exact-source bound and independent from a source-calibrated cosmological likelihood. P0-B actual observations/conditional models completed, physical source covariance and independent upstream zero-point validation remain BLOCKED_INPUT. P0-C remains only the next owner-selected coding action and is **NOT EXECUTED**.
