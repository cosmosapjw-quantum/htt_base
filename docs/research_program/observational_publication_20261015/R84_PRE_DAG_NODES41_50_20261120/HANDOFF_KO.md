# R84 → R78 다음 과학 실행 및 51–60 코딩 준비 인계

**Source identity**
- Repository: cosmosapjw-quantum/htt_base
- Branch: research/r69-observable-physics-bridges-20261118
- R78 SSOT: docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json (60 nodes, 129 edges)
- Original 42-node payload SHA256: e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d
- R84 code SSOT: htt/obsstat/p4_bianchi_fast.py, htt/obsstat/p4_lane.json, htt/obsstat/native/p4_conditional_axis_scan.f90, scripts/r84/, tests/obsstat/test_r84_p4_bianchi_fast.py
- R84 evidence: docs/research_program/observational_publication_20261015/R84_PRE_DAG_NODES41_50_20261120/
- NEXT science action: **SQ-CF4**. R84 did not mutate original R78 scientific states.

**41–50 status and limitations**
H04,H05,H06 remain pending: existing H03 working 36x36 conditional source covariance and rank/Schur arithmetic cannot replace method/PV/selection covariance or measured H(z,n). V01–V03 remain completed_scoped historically: same-frame rapidity, local finite Planck boost, distinct global tilt history contracts preserved. V04 is pending: local/global projected-rank API tested synthetically; no independent measured global source transport. V05 remains pending: source-conditional R65/R74 original 33,000 ICRS selected pixels, 185 rings, 3 flux counts, exact F and dF/dbeta, not physically measured beta or cosmic Pi. V06 pending. B01 completed_scoped as 11 canonical 3D Lie groups with N.a=0 and exceptional VI_-1/9 internal rank2 branch, not a twelfth class or all-m polarized solver.

**Optimized lane policy**
HTT_ANALYSIS_BACKEND=auto uses SHA-certified Fortran12 for supported large NVSS multi-axis, three-band conditional score calculations. Precomputed weights/score bound to exact float64 C-order direction SHA, native source and binary SHA checked each invocation. Explicit NumPy stays independent reference/fallback. C9 post-binding 96-axis, 5-run medians: NumPy 0.014137s, Fortran12 0.003060s, 4.62x, max F and score discrepancy below 9e-16. Excludes source ring setup (~0.0223s), original catalogue IO, instrument/physical fitting, all null calibration. R79 Gaia C++, R81 CF4 batch Fortran, R82 P1 sorted NumPy/Fortran, R83 H03 Fortran remain unchanged.

**Reproduction**
From repository root:
    export PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
    .venv/bin/python -B scripts/r84/verify_source.py
    .venv/bin/python -B scripts/r84/bench_real.py
    .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r84_p4_bianchi_fast.py
    .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority
For wider C10 208 scoped regressions, load exact nine native library shared-file paths via R79–R84 certified builders; the tested files are enumerated in R84/C6_TESTS.json. The 208-test local run also reads pre-existing dirty R83 test file. It is not a repository-wide clean-checkout PASS. No native binary was committed.

**Protected mutations and evidence**
Before next task, check current branch/remote SHA and source hashes. R83 files tests/obsstat/test_r83_p2p3_fast.py and scripts/r83/run_h03_fast.py were pre-existing uncommitted and untouched; do not stage them as R84. Original R84 C7 historical source evidence was restored to its previously committed checksum after being regenerated under newer C9 native default; native re-run evidence is separately C9_AUTO_RECHECK.json. No old scientific results overwritten.

**Next work**
The next actual science node is SQ-CF4: exact original selected 35,970 CF4 group ID/method-family genealogy, independently qualified correlated peculiar velocity, method zero-point and selection covariance, and heldout coverage. Do not promote a diagonal working covariance into full physical inference.

For the **next coding-preparation request only**, the continuing inventory is 51 B02, 52 B03, 53 B04, 54 B05, 55 K01, 56 K02, 57 K03, 58 K04, 59 K05, 60 K06. Reconfirm live R78 DAG before executing. No all-m polarized native Bianchi solver without legitimate source, no automatic main merge or force push. Stage-scoped owner-authorized commit/push only after actual verification.
