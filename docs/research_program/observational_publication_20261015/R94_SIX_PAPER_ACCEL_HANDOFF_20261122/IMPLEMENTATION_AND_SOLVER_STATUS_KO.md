# R94 | Programming acceleration and reused-solver research evidence

Current branch: research/r69-observable-physics-bridges-20261118. Starting HEAD: d3217f1d6ea427237f4b1931d6645d26775b285c. Original R78 60-node, 129-edge science SSOT SHA256 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11 unchanged. R94 is an implementation/readiness overlay, not 60 scientific acceptance passes.

## Actual optimized kernels

- scripts/r94/gaunt_fast.py replaces symbolic coefficient loops with a closed form for quadrupolar L=2 Gaunt ell->ell+2 coupling, checked against SymPy exact Wigner 3j.
- scripts/r94/gaunt_core.cpp uses source-SHA-bound C++17/OpenMP compilation cached ONLY in local Downloads.
- O(N*d) centered leave-one-out MC test replaces repeated np.delete/recalculated covariance; all 999 SMICA real harmonic inputs reproduce R93 rank 97/301=0.322259 and 249/1000=0.249.
- Latest measured kernel benchmarks live in GAUNT_CXX_SOURCE_BENCHMARK.json, approximately 400x coefficient construction, several-fold C++ projection and several-hundred-fold leave-one-out speedup at matched numerical result. These do not imply equivalent whole-program E2E speedup.
- Historical HTT source SHA-certified Fortran/C++ fast lanes for CF4, Gaia, Radio, P1 and five-view remain authoritative for their tested kernels and are not rewritten.

## Actual NSIDE2048 full-source IQU streaming pilot

- scripts/r94/stream_fullres.py --pilot --sha actually transformed 3 real PR3 FFP10 SMICA CMB+noise pairs IDs 0,818,999; noise is paired using ID modulo 300, and data input ordering RING differs from NESTED observed masks.
- Real source SHA files were checked against the existing PR150 registration; 818 retains the previously identified shortened trailing FITS padding, but complete data HDU.
- Full 2048 T/E/B at lmax48 stored privately in Downloads as a 3-sample NPZ. Measured wall runtime ~65 seconds and peak RSS ~4.9 GB. This is a source-qualified PILOT, not full 999 full-resolution completion or calibrated E/B null.
- --full streaming runner prepares 999 source IDs, checkpoints 25 realizations per private chunk, preserves all originals and does not download PR4. At unchanged measured pilot throughput, approximately six hours for the full run is a rough planning magnitude, not a guarantee. Full-run performance will differ with disk cache and SHA verification policy.

## Existing solver components actually connected

- HTT R49 general_tilted_evolution: 12 Bianchi/FLRW families with 2-fluid photon/CDM Einstein-Euler background, N=0..0.5. Max Hamiltonian residual ~2.66e-10 and Codazzi residual ~8.24e-11.
- HTT R49 general_bianchi_transfer: 12 exact synchronous tetrad null geodesic and polarization-screen solutions, plus six admissible near-FLRW linearizations and 4-family lmax8/16/24 cutoff exercises.
- BASS bianchi/q/polarization.py: exact basis-free rank-nine Thomson collision actually evaluated on 14-point Gauss-Legendre angular quadrature; fractional integrated radiation intensity difference ~5.65e-16.
- REC axisymmetric Bianchi I verified proper-time clock reused directly. REI named Thomson constants and conditional electron-history pair-difference envelope reused. Optical-depth tau ~0.18393 here uses an explicit assumed n_e0=2e-7 cm^-3 and ionized fraction x_e=1, not a source-qualified REI ionization history.
- Source/provenance and detailed per-family TT/EE/BB and constraint controls: REUSED_SOLVER_CONDITIONAL_TRANSFER.json.
- Crucial scope: this is a working mathematical/implementation Einstein-Euler + photon geodesic + constructed emission quadrupole + exact Thomson bridge, NOT a calibrated all-m Bianchi photon Boltzmann transfer or Bianchi family posterior.

## Native Rust and physics blockers still real

- Original BASS native wheel lacks ray-on threadpool symbol required by source-locked backend. R92 isolated alternate wheel had the symbol but failed source SBOM identity gate. No bypass or installation was attempted in R94.
- BASS hierarchy is currently validated only for dense PSTF rank <=6. Legacy PR13AG ell4/6/8 is a synthetic visibility and shear-source skeleton. Neither is a physically source-qualified ell~200 all-m CMB transfer.
- Need actual REC/REI recombination/reionization electron history, photon boundary, polarization convention, mask/beam/foreground, release-matched MC before B02–B05 full Bianchi family likelihood and independent source-matched high-l anisotropy p-values can pass.
- Continue solver-free morphology/cosmography/kinematics without blocking all 60 independent source routes.

## Three-source deep scan (read only)

- Dossier root: all eight PDFs enumerated, full text source-keyword counts extracted for each with PDF metadata and SHA; mathematical source candidates include Dossier I, II, IV, V, VII.
- BASS: 12,791 physical files and code symbols examined, with current solver/collision, background, Native ABI and unit conventions.
- HTT legacy: 2,913 files, 24 ZIP and 4,320 indexed ZIP members. Source hashing and scientific code symbol index, with selected 19 files source identity.
- Total 15,712 physical files, 4,320 ZIP members. Private complete filename/member index and FTS retained only under /home/cosmosapjw/Downloads/htt_r94_source_index, not committed to GitHub. No modification of source projects.

## Reproduction and science-preserving mapping

- R94_PROGRAM_EXECUTION_MAP.json assigns all 60 original R78 nodes across the six scientific papers, seven cross PHY routes and solver-specific external native lane. Original scientific next ID remains SQ-CF4.
- Existing 18 reused, 4 diagnostic, 9 blocked input and 29 blocked dependency R89 verdicts remain unchanged.
- Developer-tested source code: scripts/r94, tests/obsstat/test_r94_accel_solver_preparation.py, bench, streaming pilot and R78 strict validator. Exact test counts and Git commit are reported separately after execution and push.
- Copyable executable handoff: LOCAL_CODING_AGENT_HANDOFF_KO.md. Continue from actual protected source identities; commit only tested source changes to existing research branch. Keep 999 raw FITS, R78 science authority, other repos and unrelated user files unchanged.

## Minimal return contract for local agent

For each completed bounded P1-P6/PHY01-PHY07 unit and each named original R78 node, output exact actual source SHA/version, executed code and command, units and frame, conditional vs physical status, numerical result, MC sampling unit, beam/mask/null/calibration status, tests, used backend, measured cost, scientific blocker and next useful input. No false 60/60 SCIENCE PASS or family attribution absent actual physical forward model and source-qualified likelihood.
