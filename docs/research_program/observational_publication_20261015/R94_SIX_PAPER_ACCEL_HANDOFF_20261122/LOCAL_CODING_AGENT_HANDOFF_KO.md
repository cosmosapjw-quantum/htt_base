# R94 | Local coding agent handoff: SQ-CF4부터 60-node 실제 분석 실행과 기존 solver 최대 재사용

## 역할과 성공 기준

당신은 htt_base의 local scientific coding agent다. 새 프레임워크를 구성하거나 추가 계획만 제출하는 대신, R94에서 구현·검증된 가속 커널과 solver 조건부 bridge를 사용하여 원래 R78 과학 DAG의 SQ-CF4부터 P1–P6 6개 대주제와 PHY-01–07 교차 경로에서 **지금 실제 실행 가능한 연구를 끝까지 수행**하라. 실제 자료와 물리적으로 정당화 가능한 conditional 관측량을 계산하고, 더 이상의 독립 입력 없이는 완료할 수 없는 것만 source/model/analysis/native-transfer로 정확히 구별하여 반환하라.

원래 60-node/129-edge 과학 정본은 절대 덮어쓰지 않고, R94는 source-conditional numerical/solver implementation overlay다. 60/60 SCIENCE PASS를 만들기 위한 gate 승격은 금지한다.

- Checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base
- Active branch: research/r69-observable-physics-bridges-20261118
- Authoritative DAG: docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json
- R78 SHA256: 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11
- Next physical science ID: SQ-CF4
- R89 preexisting verdicts: REUSED_SCOPED 18, DIAGNOSTIC_COMPLETED_SCOPED 4, BLOCKED_INPUT 9, BLOCKED_DEPENDENCY 29
- 60-node R94 routing: docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122/R94_PROGRAM_EXECUTION_MAP.json
- R94 source index: SOURCE_REUSE_INDEX.json, detailed private SQLite under /home/cosmosapjw/Downloads/htt_r94_source_index/search.sqlite
- Most recent branch HEAD must be freshly checked. Do not infer current HEAD from this handoff.
- Read current AGENTS.md, R78 original publication contract, R89–R94 evidence and versioned source identities before writing.
- Mutate ONLY verified bounded files on the existing research branch; preserve unrelated 1,084 untracked files, other projects' original Git worktrees, main, source FITS, frozen R78–R93 results. No force push or merging.

## A. Prepared source-aware acceleration; run first

The existing HTT Fortran/C++ acceleration lane for CF4, Gaia, Radio, P1 and five-view must be reused, not replaced speculatively. Default HTT_ANALYSIS_BACKEND=auto; record backend receipts. Invalid native results must fail, not silently fall back.

New R94 operations already implemented:
1. scripts/r94/gaunt_fast.py + scripts/r94/gaunt_core.cpp: exact closed-form L=2 Gaunt coefficients and source-SHA-addressed compiled C++17/OpenMP bulk BiPoSH projector. Numeric-parity checked against original R93 and SymPy exact 3j.
2. Stable O(N*d) leave-one-out MC rank and variance computation, same estimator and input.
3. scripts/r94/benchmark_gaunt.py with real all-999 R93 harmonic source, source hash and benchmark in GAUNT_CXX_SOURCE_BENCHMARK.json.
4. scripts/r94/stream_fullres.py full-res NSIDE2048 T/Q/U streaming. Three actual raw FITS CMB+noise pairs [00000,00818,00999] already checked via --pilot --sha, including the known 00818 missing trailing FITS padding but complete data HDU. Pilot receipt and private harmonics are saved.
5. scripts/r94/deep_reuse_index.py indexes all 8 Dossier PDFs, BASS 12,791 files, legacy 2,913 files and 4,320 ZIP members read-only, with selected scientific source SHA and local private FTS index.
6. scripts/r94/solver_source_bridge.py runs 12 Bianchi R49 Einstein–Euler backgrounds, exact null geodesic + polarization-screen transfer, six near-FLRW conditional linearized families, BASS rank-nine exact Thomson collision, REC positive Bianchi-I clock and REI published conditional source-history envelope.

Benchmark report measured roughly 400x source coefficient table generation, several-fold BiPoSH C++ projection, and hundreds-fold LOO statistic acceleration at matched accuracy. These are kernel speedups, not global FITS E2E speedups. Set OMP_NUM_THREADS=1 and OPENBLAS_NUM_THREADS=1 for small Gaunt/GLS jobs; use tested OMP_NUM_THREADS=2 for full-res HEALPix pilot. Do not overcommit the observed 31-GiB memory (about 17 GiB initially available) or launch many simultaneous ~5-GiB FFT workers.

## B. Run the entire available SMICA FFP10 full-resolution ensemble, streaming

Original actual sources (read-only):
- /mnt/extdrive/workdir/raw/planck_ffp10/smica/cmb_mc : 999 signal CMB MC maps (all IDs 00000..00999 except 00970)
- /mnt/extdrive/workdir/raw/planck_ffp10/smica/noise_mc : 300 noise MC maps
- /mnt/extdrive/workdir/raw/planck_data/ : PR3 SMICA observed T/Q/U maps and common I, P masks
- K1 exactly verified compact source: /mnt/extdrive/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz
- R93 T NSIDE64 conditional a_lm & BiPoSH private artifact: /home/cosmosapjw/Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz

Reproducible process and pilot:
1. export PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
2. .venv/bin/python -B scripts/r94/stream_fullres.py --check-pilot
3. Execute .venv/bin/python -B scripts/r94/stream_fullres.py --full in an authorized long-running local agent session.
4. The --full runner checkpoints 25 CMB realizations per private NPZ under /home/cosmosapjw/Downloads/htt_r94_fullres_stream. Verify each chunk, ID, SHA, RING/NESTED distinction, polarity and source register, and resume without replacing earlier successful chunks.
5. Pilot 3 pairs took ~65 seconds and peak RSS ~4.9 GiB with full raw SHA; extrapolated order-of-magnitude cost for 999 is several hours (roughly six hours at identical per-pair throughput). Rebenchmark before setting actual wall budget; do not pretend it already ran all 999 full-res or abort all science if a single corrupted input is encountered.
6. Keep 300 unique-noise-ID primary matched sensitivity and 999 signal / 300 recycled-noise sensitivity separate; reused noise is not 999 independent draws. Original SMICA 999 are NOT Commander 999. The Commander FFP10 source is a small separate qualified set.
7. At increased ell_max, use source-matched beam, polarization convention, mask leakage, foreground and full-noise covariance. An NSIDE64 source cache lmax48 is a proxy, not true high-resolution precision. The old legacy BiPoSH 1/fsky-only and positive |a_lm|² “A20” are invalid; replace them with correct signed Gaunt/modified shape/MC-calibrated covariance.
8. Preserve private full harmonic coefficient caches, make small JSON scientific summaries in the source-controlled repo. No 1-TB duplicate of original data, no full PR4/NPIPE download.

## C. Existing solver dependencies: develop Einstein–Boltzmann components now, do not automatically block the entire study

The solver is **partly available already**. R94 REUSED_SOLVER_CONDITIONAL_TRANSFER.json provides implementation-verified results:
- HTT R49 general_tilted_evolution: all 12 admissible Class A/B+FLRW 2-fluid Einstein–Euler backgrounds on the tested short interval; numerical Einstein Hamiltonian/Codazzi controls remained small.
- HTT R49 general_bianchi_transfer: 12 exact geometry/geodesic/screen cases, 6 near-FLRW linearized cases, four-family ell-cutoff 8/16/24 tests.
- BASS bianchi/q/polarization.py: exact basis-free rank-nine Thomson collision, energy and screen constraints verified without native Rust.
- REC source: full_bianchi_hyrec/background/axisymmetric_bianchi_i.py, source-locked positive proper-time Bianchi-I clock; valid for explicitly prescribed Bianchi I.
- REI: research/flrw_pair_observable_20261016/results/THOMSON_PAIR_RESULT.json, a **pair-difference envelope**, NOT a physical redshift electron history. R94 uses deliberately constructed constant ionization fraction and electron density to connect the modules. Do not relabel constructed optical depth as REI-derived actual CMB visibility.

Physical development route, in this order:
C1. Map source frames/clock/H-normalization/c, epsilon, polarization signs across BASS–R49–REC–REI. R93 BASS–HTT Codazzi on 12 strata × 5 rotational cases already agrees to ~1e-15; reuse.
C2. Replace R94's constructed x_e(a), n_e(a) with actually source-qualified REC+REI histories wherever obtainable. Enforce release/history/clock exact identities and positive H, density, opacity.
C3. Derive full photon source \(j_\gamma,\pi_{\gamma ab},Q/U\) in BASS electron frame, carry through Thomson kernel and exact screen transport, compare to independent Type I/FLRW/Kasner limits.
C4. For all 11 Bianchi types and tilted multi-species EOS, execute R49 constrained background + exact 4D geodesics + physical emission boundary. Explicitly test q=0 vs q != 0, exceptional VI_-1/9 and sign/handedness parity. Re-run source convergence if changing physics.
C5. Reuse BASS hierarchy.py (dense PSTF Lmax6), q.transport native interface and LEGACY PR13AG L4/L6/L8 projected solver as a *numerical skeleton*. Do NOT extend dense 3^ell PSTF arrays to ell ~60; use 2ell+1 harmonic basis/sparse angular coupling or validated angular-grid transport with cutoff/absorbing-boundary tests.
C6. BASS installed native wheel lacks documented rayon_thread_pool_size; isolated candidate wheel has that symbol but failed RF00 SBOM byte identity. This is an **environment/provenance blocker**, not proof that physical equations are wrong. Rebuild/qualify a source-locked wheel only in an isolated owner-authorized BASS environment, pass documented RF00/RF01 tests, then connect; no bypass of provenance checks and no modifications to another owner's original repo by default.
C7. When a genuinely source-qualified all-m polarized hierarchy is validated, extend to ell=16,32,60,120 with physical visibility/collision boundary and convergence controls. Only then promote the external-native-transfer lane. Else keep geometric/kinematic/morphology work running.
C8. For actual CMB family model discrimination, construct likelihood for T/E/B template or offdiagonal covariance with beam, mask, selection, noise and release-matched MC. The Planck Plik-lite 613-bin scalar likelihood is only the FLRW high-ell baseline; it cannot replace coherent Bianchi phases or model-specific transfer.

Do not declare SQ-NATIVE/B02–B05 physically accepted from a short background ODE, constructed photon pi or synthetic opacity.

## D. 8-group source execution, 6 papers and 7 cross routes

Execute in data-friendly groups with bounded source checks, not another all-gates meeting:

- G01/COMMON: freeze R78 source SHA, all 60 IDs, physical vs code readiness, independent data sources, selected units/frame conventions.
- G02/CF4, SQ-CF4 first: actually use original 35,970 CF4 groups, R36 low-k physical-modeled 36D PV covariance and R27 7-method calibration quotient, new Mayukh SR gamma correction and method genealogy; attempt independent upstream/selection/heldout only where source-qualified. Do not infer original MCMC posterior from post-intercalibration catalog. Run all source-available windows, not tiny illustrative subsets.
- G03/Gaia, P6: reuse all 634,233 selected Quaia/CRF3 source, four working weight estimands, 48-patch jackknife and VLBA comparison; add scanning-law/AGN matched null if real source allows.
- G04/Radio, P4: reuse five entire actual NVSS/RACS/SPICE-RACS/SUMSS/LoTSS surveys, flux/area/tile/noise correction, LSS/source matching; retain actual joint-covariance limitation.
- G05/Planck, P2: complete full-res streaming; SMICA source-matched BipoSH and T/E/B MC, compare PR3 Commander observing maps but do not combine different component separation MC sets. Use R94 accelerated kernel. Investigate high ell >48 only with mask/beam/pixelization convergence and physical Bianchi model.
- G06/P1: typed five-variable x, Q, Pi, F, GF (null where missing) on existing 2048 coupled draws and physical source-specific floors; retained unknown masses, no imaginary Pi/null.
- G07/Bianchi, P5: R49/BASS/REC/REI physical geometry and conditional polarized propagation, 12 Bianchi types, 7-nuisance R62 CF4 signed tensor compatibility (84 witnesses), finite-z Sachs/Jacobi. Identify type-equivalence classes and *conditional* exclusions only when source transport and EOS constrain them.
- G08/Optical + PHY-01 through PHY-07: independent source/frame/unit/covariance and mask-response checks, finite-z optical, radio-Gaia-CF4 directional morphology, photon source, Lie flux, phase observables; attach each named PHY result to the original DAG ID without changing old acceptance.
- Data missing / model missing / further analysis needed / native solver missing must be separate buckets, each with a *specific* next input or calculation. One missing gate must not stop other independent work.

## E. Tests and exact execution contract

On first fetch and after bounded patches:
- Read current AGENTS.md and actual latest HEAD, git status, available worktree, prior R78/R89–R94 owner evidence.
- Use scripts/r94/prepare_handoff.py, tests/obsstat/test_r94_accel_solver_preparation.py and scripts/r94 benchmark/stream/pilot data.
- Native backend must use g++ C++17/OpenMP with original source SHA, compiled binary under Downloads. C++/NumPy parity required; no speedup claim absent matched input and accuracy.
- The R94 pilot is exactly three raw pairs 0,818,999; ID818 has 1,218-byte missing trailing FITS padding but complete HDU and registered SHA, while ID970 genuinely absent. Do not repair FITS in place or invent an ID.
- All new observation statistics use units, frame, source release, mask, noise matching and explicit MC sampling unit. Distinguish observed conditional p, model posterior, computational PASS and publication qualification.
- No repeated unnecessary full historic regression for meta-gates. Unit/integration/physics oracles for changed code once, then one bounded adversarial review.
- Material bounded results may be selectively committed/pushed to the existing research branch, with exact current HEAD, changed file list, tests, SHA and remote result. Never change main or unrequested unrelated user data.

## F. Final return payload to the research lead

Give actual P1–P6/PHY01–07 results and all 60 original node states with:
node ID, source identity and hash, actual executed code/command, runtime and memory, math-to-code/units, scientific status, numerical result, null and covariance, readiness vs publication gate, newly solved physical model, remaining exact blocker, next independent unit.

Specifically enumerate: all 999 raw full-res FFP10 T/E/B processing count (or exact partial count if interrupted), 300 primary unique-noise null status, BASS 12-family background/Thomson/REC/REI forward model status, source-typed five views, false-PASS negative controls, commits/push IDs, and 60-node science original acceptance unchanged unless genuinely supported.

**Stop condition:** Finish all currently available source-qualified analyses and source-aware solver tests; leave only actual external input, specific unavailable native physics, or bounded production-long-run items as open. Do not claim source-matched Bianchi family attribution or 60/60 acceptance without actual physical forward likelihood.
