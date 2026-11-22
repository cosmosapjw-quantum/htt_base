# R96 → Local Coding Agent: three actual theory loops and next bounded science implementation

## Goal and authority

Continue HTT research from **SQ-CF4** and the six papers P1–P6 / seven PHY cross-studies, using R96 executed mathematics and actual data to complete the next real science units. Do not create another ceremony-only readiness/gate cycle. Reuse BASS, REC, REI, prior R49/R62/R89–R95 and the rescued legacy code, but respect provenance and source scopes.

Checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base
Branch: research/r69-observable-physics-bridges-20261118
R96 parent HEAD at study start: a87df07da328ba6d704e7cf0d554081f52d39213
Original R78 INTEGRATED_DAG.json SHA256: 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11
Original DAG: 60 nodes, 129 edges, NEXT_ID SQ-CF4.
Source conditional implementation PASS is not physical publication approval. Keep original 60 scientific verdicts unchanged unless a genuinely qualified new physical result independently satisfies the original criterion. Distinguish DATA / MODEL / ADDITIONAL_ANALYSIS / NATIVE_TRANSFER.

First check current actual HEAD, AGENTS.md, git status, original R78 and R95/R96 source artifacts. Unrelated 1,084 untracked user files and historical source ZIPs are protected; do not delete, rewrite or bulk-add. Preserve REC's existing dirty tracked source; BASS, REI and other owners' checkouts are read-only unless their owner specifically authorizes mutation. Do not merge/force push. No full PR4 download. Any missing public file goes ONLY to /home/cosmosapjw/Downloads after official-source check and hash registration; do not copy TB-class original FITS.

## Existing R96 calculations and 30 theory stages

The following are three COMPLETED BOUNDED theory R1–R10 cycles, not a 60-node claim:
A: THEORY_A_CF4_R1_R10_KO.md ; actual CF4_COVARIANCE_RECONCILIATION.json
B: THEORY_B_CMB_R1_R10_KO.md ; actual CMB_MASK_BIPO_CROSSVALIDATED_NULL.json
C: THEORY_C_BIANCHI_R1_R10_KO.md ; actual SPIN2_MBLOCK_HIERARCHY.json

Scripts:
- scripts/r96/cf4_covariance_bridge.py
- scripts/r96/legacy_biposh_recovered.py
- scripts/r96/cmb_crossfit_null.py
- scripts/r96/spin2_mblock_extension.py
- scripts/r96/reindex_source_reuse.py
- scripts/r96/github_reuse_audit.py
- scripts/r96/build_agent_dispatch.py

The full 60-node work routing, original outcomes and next work are in R96_LOCAL_AGENT_60_NODE_DISPATCH.json. Source sha/roots from SOURCE_REUSE_AUDIT.json and GITHUB_SOURCE_AUDIT.json. Private full path and ZIP inventory is /home/cosmosapjw/Downloads/htt_r96_private_index/source_search.sqlite. The legacy original was intentionally preserved, while the new repaired code is versioned as scripts/r96/legacy_biposh_recovered.py.

## A. Next CF4 scientific calculation, highest priority

Start with all 35,970 actual source groups (no illustrative subsample). R96 has shown:
  C_R36 = C_PV + K4 Sigma4 K4^T + R_old
  C_R95(sigma) = C_PV + C_H03noise + J7 (sigma^2 I_7) J7^T.
R36 R_old is SPD but C_R36 - (C_PV+C_H03noise) is indefinite (eigen min -0.90324, max +0.25713), NOT an additive independent noise term. Do not double-count these covariances.
R96 rebuilt all 4x9 H03 windows and real 36x7 R27 channel support, verified direct Cholesky/low-rank Woodbury. H0 conditional examples R36 72.238±0.388 vs R95 zero-cal 72.926±0.359 vs .05-mag cal 72.010±1.106 km/s/Mpc. None is a new measurement.

Next task: reconcile the original R36 method K/Sigma source; identify precisely independent covariance components and correct the historical legacy forward-likelihood consumer so it accepts only typed covariance-model versions. Seek published/locally available pre-intercalibration CF4 zero-point source or raw anchors. If not obtainable, implement proper partial-identification bounds, reproduce released data comparisons (TF,FP,SN,etc), and stop without fabricated upstream posterior. Add explicit independent heldout only if actual data source permits. Verify full source/normal-frame frame/units, selection/method overlap and all-window covariance.
Acceptance: source identity SHA, PSD and model provenance, Woodbury-dense numerical parity, full-window comparison, conditional claim vs physical blocker.

## B. Next CMB masked BiPoSH and polarisation null

Do not reprocess 1TB raw data: R95 already completed 999 full-res NSIDE2048 CMB MC + 300 real noise MC, checkpointed at ~/Downloads/htt_r94_fullres_stream. R95 tested T,E,B masked pseudo-Cl, signed L=2 ell-to-ell+2 60D. Difference of 999 repeated noise vs 300 unique noise cannot be misrepresented as independence. Commander-only null remains separately blocked.

R96 now added a **correct maintained legacy BiPoSH function** with same purpose as old bianchi_departure_v091/htt/likelihood/biposh_masked.py, which had bogus positive |a_lm|² and fsky covariance. Corrected public functions estimate_biposh_L2/BiPoSHLikelihood/biposh_variance require matched MC and 5D or full covariance; missing MC is a fail-closed error. The original legacy snapshot was not overwritten to preserve its source identity. Import the corrected implementation in actual HTT consumers after checking their call signatures.

R96 fullres paired SMICA FFP10 60D statistics, using exactly 300 independent noise IDs and 999 CMB signals:
- R95 diagonal empirical 60D rank 0.259136.
- Full-covariance leave-one-out with fixed correlation shrinkage lambda 0.05/0.20/0.40: ranks 0.10299/0.11296/0.14286.
- Disjoint even-ID train150/odd-ID heldout150: empirical rank 0.172185.
These are *not* detection claims; shrinkage/mask/beam/foreground/source-null decisions remain consequential. Signal-only/noise-only/cross-term bias decomposition is in source JSON.

Next work: actual Planck same-pipeline mask-beam-polarization injection tests and independent source-matched noise/foreground MC; compute Wigner9j/empirical response matrix and its inverse/regularization for signed L=2 BipoSH with masked T/E/B. Evaluate conditional inference under additional shrinkage alternatives fixed before looking at observed data. For family attribution, model-specific Bianchi T/E/B template/anisotropic covariance needed. Do not use PlikLite power as phase likelihood. Do not imply cross-method Commander p from SMICA 300 noise null.

Acceptance: injection recovery bias within calibrated MC errors; covariance train/test exchangeability, finite full mask coupling and E->B leakage, source-only statistical significance clearly marked exploratory until physical null qualified.

## C. Bianchi full polarised transfer, solver work

R95 actual Einstein-Euler backgrounds 17 bounded evolutions, source-typed HyRec2+tanh visibility, exact BASS basis-free Thomson collision, and m=0 T/E L60 120 states exist. The number 11155 is a theoretical all-m state capacity, not implemented. R96 now implements exactly derived spin-weighted cosθ recurrence with actual R49 spin-weighted harmonics and explicit m=-2,-1,0,1,2 T/E/B *source-response* sparse LU over L=8,16,32,60. The recurrence max error was ~1.78e-16, free-streaming operator skew-Hermitian, Thomson 2x2 eigenvalues (-1,-0.3), and B=0 in k=0 and m=0 controls. Model quadrupole is constructed fixed STF sigma/H=1e-4; not yet a general curved tilted Bianchi connection or source history.

Next highest-value work: project full R49/BASS synchronous-tetrad 4D connection, Sachs screen parallel transport and time-dependent Einstein-Euler sigma/N/a into **spin harmonics**, yielding nonzero curved Bianchi coupling between m sectors. Respect E/B handedness and vector/tensor parity; compare Type I, V, VI_-1/9, VII_h, IX with independent geodesic angular-grid oracle. Join REC/REI source-qualified electron history and actual photon source/congruence for all selected EOS; no fake early redshift continuation of R49 late-time truncated trajectories. Compare L=16/32/60/96 with independent angular-grid discretizations and derive physics-respecting truncation/absorbing boundary. Only after validation move external native Boltzmann SQ-NATIVE/B02–B05 to accepted. BASS Rust ABI/SBOM mismatch is a runtime provenance blocker; do not bypass or silently install a mismatched wheel.

Acceptance: meaningful physical source histories, Hamiltonian/Codazzi/Jacobi, positivity, Thomson energy, screen transversality, proper SO(3)/handedness, zero-shear FLRW, mode parity and convergence; publication-level likelihood only after source-matched T/E/B and observational matched null.

## Cross-paper deployment and DAG

R96_LOCAL_AGENT_60_NODE_DISPATCH.json maps all 60 IDs. Start SQ-CF4. Continue P1 2048 coupled draws/physical partial-ID, P4 all five Radio survey flux ladders and selection/LSS null, P6 Gaia/Quaia 634233 clean QSO and frame/scan null, and each PHY01–07 in parallel with independent source qualification. Do not let a missing native photon hierarchy block morphology/cosmography/kinematical classification. Conversely, do not set physical Pi or G_F without a defined source-specific measure/transport/null and observed scale. Preserve R95 original states: 18 reused scoped, 12 newly conditional, 3 diagnostic, 7 input blocked, 20 dependency blocked.

## Reproduce and verify

From the active checkout:

    export PYTHONPATH=.:htt:htt/src
    export PYTHONDONTWRITEBYTECODE=1
    export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
    export OPENBLAS_NUM_THREADS=1
    export OMP_NUM_THREADS=1
    .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r96_three_theory_loops.py
    .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r95_science_execution.py
    .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority

Targeted high-cost R96 complete result scripts already ran. Their outputs are create-only; do not rerun to replace files. For new physics questions, append new R97 artifacts preserving SHA readback.

Return for each bounded unit: exact node, formula and model scope, source SHA/version, executed command and observable, units/frame/IC/BC, CPU/backend/runtime, numerical error and independent oracle, selected null, rejection or condition, physical interpretation, still-needed data/model, commit/push SHA. Preserve original DAG and separate scientific acceptance from code readiness.

## Stop conditions

Stop each bounded scientific unit when its numerically checked conclusion is available or a named essential source is absent; do not start another endless audit. Do not declare all 60 physical nodes complete unless all original acceptance criteria are independently established. Native agent delegation is NOT_RUN in Chat if no actual host subagent tool; local coding agent may use its own genuine worker tools and must identify actual dispatched runs.
