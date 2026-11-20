# R81 → R78 SQ-CF4 후속 연구/코딩 인계 (복사 가능)

Repository cosmosapjw-quantum/htt_base
Active branch research/r69-observable-physics-bridges-20261118
Science SSOT docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json
Original 42 scientific node payload sha256 e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d
Pre-DAG 11–20 code SSOT htt/obsstat/phy_fast.py, htt/obsstat/phy_lane.json
C1–C10 evidence docs/research_program/observational_publication_20261015/R81_PRE_DAG_NODES11_20_20261120/
NEXT SCIENCE ID SQ-CF4, not E0/E1 or new physical PHY accepted.

1. Read current remote HEAD and source SHA, do not pin an outdated commit from this prompt. Preserve original research branch, unrelated 318 untracked paths, R78 60 nodes/129 edges and old 291-software-PR backlog untouched. Routine author-approved validated stage Git push is permitted only for scoped changes.
2. For computational analysis use HTT_ANALYSIS_BACKEND=auto. R79 htt.obsstat.pre_dag_fast.accumulate_gaia uses certified C++ 2×2 correlated proper-motion normal equations; R81 htt.obsstat.phy_fast.multi_axis_hemisphere uses certified batch Fortran/OpenMP for many axes, measured 49–54× faster than NumPy on actual CF4 selected 35,970 group geometry without >2e-11 source discrepancy. For weighted 12D radial Gram the actual NumPy BLAS was faster than optional C++; leave NumPy default.
3. Make no new source/astrophysical null from algorithm speedup. R81 inspect_external_native validates external manifest/sha and decompression budgets ONLY, not a native Bianchi solver; external SQ-NATIVE remains blocked. PH02 photon f and normal matter u, PH03 same radiation/radio beta, PHY04 actual high-z Gaia optical source map, PHY05 independent total normal u, PHY06 photon higher-l history and PHY07 correlated PV source C are missing.
4. Next SQ-CF4 source slice: actual R80 selected 35,970 CF4 group IDs, table3 method presence/source assignment and original R36/A_RAW_36x35970 operator must be maintained. Derive same-source method zero-point response/calibration and PV/selection covariance from genuine data, and test one heldout predicted contrast/coverage. Do not replace 35,970 selected groups with raw full 38,053 or selected 40–400 Mpc subset 31,382. Full-sky zero-flux Type V shear mask bounds are conditional geometry, not detected GR shear.
5. Primary experiment commands from repo root (not an automatic scientific task):
   PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B scripts/r81/verify_real_phy.py
   PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B scripts/r81/bench_real.py --repeat 5 --out /tmp/r81_phy_bench.json
   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r81_phy_fast.py
   PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority
6. Source/link status: previous CF4 table3/table4, selected-source NPZ, Gaia-CRF3 FITS were physically mounted and available on 2026-11-20; always check actual path and original SHA before new runs. Mark source environment BLOCKED if no longer mounted rather than substitute data. Full cosmological source joint null and physical GF remain UNRESOLVED.
7. Coding completion ≠ scientific completion. R81 C10_NODE_MATRIX.json and PROVENANCE.json distinguish each implemented/verified numerical route from the physically missing source. No all-family native Boltzmann code and no original P1–P6 publication claim promotion.
