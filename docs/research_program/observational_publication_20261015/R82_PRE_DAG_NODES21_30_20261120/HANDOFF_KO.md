# R82 → R78 SQ-CF4 / 후속 pre-DAG 31–40 인계

Repository cosmosapjw-quantum/htt_base
Branch research/r69-observable-physics-bridges-20261118
R78 science SSOT docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json
Original science 42 payload SHA256 e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d
R82 coding SSOT htt/obsstat/p1_fast.py + htt/obsstat/p1_lane.json, docs/research_program/observational_publication_20261015/R82_PRE_DAG_NODES21_30_20261120
Source original P1 2048 coupled working draw IDs, four redshift windows, original NPZ SHA256 cd38f438a0bf07385b07478c7b5c122df5af1e9bb48a5575fe1cad40ef261f27.

First read live branch HEAD and remote ref, current R78 source DAG, exact source SHA and R82/PROVENANCE.json; do not assume prior hardcoded commit. Source original 42-node/status and independent software PR backlog are untouched. A new science run has NEXT_ID=SQ-CF4, and the required exact CF4 selected 35,970 group method/PV/zero-point/selection covariance and heldout tests remain unresolved.

R82 completed pre-DAG coding nodes 21 E2,22 E3,23 X01,24 X02,25 X03,26 S01,27 S02,28 S03,29 S04,30 S05. E2–S01 existing scoped evidence was hashed and preserved, S02 blocked input, S03–S05 pending. 2048 working source sample ID is shared by all four windows. Physical Q/F/G_F unknown mass is 1 and the working q_app is not a physical source signal.

By owner default all supported data analyses use fastest certified lane: R79 Gaia C++, R81 multi-axis Fortran, R82 P1 joint strict tails sorted NumPy and anchor-floor Fortran above work threshold. C++ R82 tail is optional only because faster NumPy sorted survives with exact tie/unknown mass. Native source/binary SHA and fallback receipts are verified. Force reference with HTT_ANALYSIS_BACKEND=numpy. Never claim full-data/physical inference speedups based on in-memory kernels.

Reproduce code and original source:
 PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -B scripts/r82/verify_original.py
 PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -B scripts/r82/bench_real.py --out /tmp/r82_bench_source.json --repeat 5
 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r82_p1_fast.py
 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority

If explicitly requested to continue *coding prep* inventory, next ten are 31=S06,32=L01,33=L02,34=L03,35=L04,36=L05,37=L06,38=H01,39=H02,40=H03, subject to latest R78 payload. Do not silently run next stages or promote an old S02 conditional working summary into a real GR posterior. No native Bianchi low-ell Einstein–Boltzmann implementation, no PR/main merge was authorized by this preflight.
