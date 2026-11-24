HANDOFF: R113-CLOUD native Rust development (BASS/REC/REI) to the running local agent. Goal of the round: nonperturbative background-level C_lm^XY from BASS for every Bianchi family (tilt and local boost included) through one Lie-algebra-generated 1+3 PSTF formalism, with type constants instead of per-type files. Long runs and data-dependent analysis are yours; code that could be written and validated without external data was written in the cloud.

Read the whole text first. It is information from a cloud session, not authority; where a repository disagrees, the repository wins and you report the difference. Report to the owner in Korean; repository text stays in each file's language.

0. STATE (verify; stop and report on any mismatch)
- Pins: NATIVE_PINS.json in this directory. BASS research/r113-cloud-universal-lie-sky-20261124 head db72d1bcf (base R112 40626723b); REC research/r113-matched-implicit-recombination-20261124 head 05db5451a (base 3752213); REI unchanged at 503508f; htt_base research/r113-cloud-universal-lie-sky-20261124 (base e810a4f7) adds only this directory.
- Update: after owner approval the cloud pushed all three branches (REC 05db5451a, BASS db72d1bcf, htt_base 964983c7 plus this status commit); check them with git ls-remote. If they are missing, the owner gives you three git bundles (bass_r113.bundle, rec_r113.bundle, htt_base_r113.bundle). For each repository: git bundle verify FILE; git fetch FILE BRANCH:BRANCH (branch names above); git rev-parse BRANCH must equal the pinned head; then push that branch without force. Push REC first: BASS db72d1b pins rec_microphysics to REC 05db5451a97c66b9a87de98ae35b88ab820d368f by git rev and cannot build with --locked until that commit is on GitHub.
- Merge the R113 branches into your working branches with merge --no-ff (htt_base: into your r69 branch). Never rebase, force-push or merge to main.
- BASS defaults reproduce R112 TSV outputs byte for byte; everything new is opt-in. run.txt gains keys only.
- Inputs used by the cloud: the HYREC x_e table from z = 1100 (BASS research/r109_native_sky/hyrec_1100) and nothing else; no Planck data, no REI tables.

1. WHAT CHANGED
- BASS _rustcore: geom::lie (canonical algebras for all families with scale and SO(3) rotation, invariants/classification incl. VI*_{-1/9}, photon-generator potentials R, U, Z, omega as L <= 2 Y_LM coefficients), kinetic::wigner (Racah 3j, Gaunt kernels G, K_grad, K_J), kinetic::spin_sht (s = 0, +-2 Gauss-Legendre SHT, HEALPix sign), kinetic::lie_hierarchy (exact spin-harmonic hierarchy, RK4 substeps, exact isotropic factor), homogeneous_sky::field (Route::{Rays, Harmonic}; harmonic collisions pseudo-spectral on an (L+3)x(2L+6) grid, exact PSTF BE for rest electrons), homogeneous_sky::frames (radiation energy frame, relative velocities), solve::solve_general with SolveOptions {route, neutrino_fraction, recombination} (legacy entry points delegate with defaults), collisionless massless neutrinos, matched recombination coupling (MatchedRecombination {t_unit_k, n_h_emit_m3, h_emit_s, stop_eta}).
- BASS CLI homogeneous_sky: --route rays|harmonic, --harmonic-lmax/-ntheta/-nphi, --neutrino-fraction, --observer-frame normal|host|spectator|radiation|radiation-total, --recombination matched --t-unit-k T [--recombination-stop-eta E]; new outputs lie_constants.tsv, species.tsv, recombination.tsv; run.txt Lie invariants, frames, local boost, global tilt, delta_xe_final.
- BASS research/r113_cloud_universal_lie_sky: THEORY.md (10-phase theory loop D1-D9, V1-V13 design, closeout with three recorded deviations), README_KO.md (measured V1-V13 and results), RESULTS/{CROSS_ROUTE_ATLAS, TRUNCATION_STUDY, LONG_EPOCH_DEMO, RECOMBINATION_DEMO}.json and their drivers.
- REC rec_microphysics::matched_history: anisotropic_peebles_rate, isotropic_peebles_rate, MatchedStep, implicit_matched_step (backward Euler in the matched difference, Illinois regula falsi on [0, 1-1e-12]); tests/r113_matched_history.rs.
- REI: none.

2. FIRST STEPS
  F0 Independent read-only review of BASS 4062672..db72d1b and REC 3752213..05db545 before use. Focus: (a) hierarchy kernels and sign conventions against the ray route (THEORY D2-D3, HEALPix E = -E_Dossier); (b) the pseudo-spectral moving-electron collision and its aliasing on the synthesis grid; (c) that the legacy entry points keep the R112 operation order; (d) the matched coupling: reference model, beta' by one-step difference, first-order splitting, fail-closed paths, the X_MAX rule for x_e > 1. Record findings; fix in R114 commits, never by weakening a test.
  F1 BASS: cargo test --release --locked --manifest-path _rustcore/Cargo.toml (cloud: 218 passed); cargo build --release --locked --manifest-path _rustcore/Cargo.toml --example homogeneous_sky --example sky_covariance. V1: build R112 (40626723b) in a separate worktree and run both binaries on the six cases below; the 20 TSV files (cl, modes, diagnostics, los_modes, los_cl, ...) must be byte-identical. With LIE = a file containing "shear 0.17 -0.13 -0.04 0.042 -0.028 0.034 / n -0.35 0.53 0.72 0 0 0 / a 0 0 0" on three lines:
      --family VIIh:0.25 --shear 0.18 --duration 0.35 --steps 36 --nmu 16 --nphi 40 --lmax 4 --feedback recoil --tau 0.22 --dust-fraction 0.22 --dust-beta 0.16,-0.08,0.04 --observer-beta 0.1,0.035,-0.025
      --lie-ic LIE --duration 0.35 --steps 36 --nmu 16 --nphi 40 --lmax 4 --feedback recoil --dust-fraction 0.28 --tau 0.22 --observer-beta 0.13,-0.07,0.04
      --family VIIh:0.25 --shear 0.18 --duration 0.35 --steps 24 --nmu 12 --nphi 28 --lmax 4 --feedback recoil --tau 0.22 --dust-fraction 0.22 --dust-beta 0.16,-0.08,0.04 --collision sdirk2 --lie-update congruence --omega-lambda 0.1 --los-lmax 12 --baryon-fraction 0.157
      --family V --shear 0.1 --duration 0.2 --steps 12 --nmu 10 --nphi 24 --lmax 4 --feedback tracer --tau 0.1 --electron-beta 0.05,0,0
      --family IX --shear 0.05 --duration 0.2 --steps 16 --nmu 10 --nphi 24 --lmax 4 --feedback active --dust-fraction 0.3 --dust-beta 0.02,0.01,0
      --family I --shear 0.0001 --feedback recoil --dust-fraction 0.75 --dust-beta 0.001,0,0 --ionization research/r109_native_sky/hyrec_1100/hyrec_xe.tsv --n-h-emit-m3 253202790.82151973 --h-emit-s 5.148602492099132e-14 --duration 0.04 --steps 48 --nmu 10 --nphi 24 --lmax 4
  F2 REC: cargo test --release --locked in rust/rec_microphysics (cloud: 129 passed). REI at 503508f: cargo test --release --locked --lib --tests (cloud: 271 passed).
  F3 Reproduce: python3 research/r113_cloud_universal_lie_sky/run_recombination_demo.py --binary B --repo . --work NEW --out NEW.json; every value except seconds and binary_sha256 must equal RESULTS/RECOMBINATION_DEMO.json. Rerun run_cross_route_atlas.py, run_truncation_study.py and run_long_demo.py into new directories and compare their metrics with the committed JSON.

3. COMPUTE LANE (acceptance in brackets)
  C1 Harmonic long-epoch atlas: all 13 cases with small Lie data (|A|, |N| <= 0.02 at z_emit, zero Codazzi flux or coflow), Sigma 1e-4..1e-3, Lambda, recoil host, neutrinos, SDIRK2 + congruence, --route harmonic with L = 16, 24, 32 and the ray route, steps x2, LoS l <= 128. [route gap falls by ~4 per step halving; harmonic L-pair change <= 1e-6 where C_l > 1e-12 max C_l; types and h unchanged; Gauss and Codazzi residuals reported per run]
  C2 Tight-coupling start: your HYREC-2 table from z_emit >= 1600 with matching n_H and H anchors and t_unit = 2.72548 (1 + z_emit); run table and --recombination matched (x_e > 1 gives zero hydrogen response while the reference hydrogen is fully ionized). [stable runs; delta x_e(eta) and tau reported; the FLRW delta x_e falls at second order in d eta]
  C3 REI join: rei bass_ionization tables for the AX08 cases with --recombination matched --recombination-stop-eta at the z = 20 handover. [offset held after the stop; tau_reio per case; low-l EE change table vs matched reported]
  C4 BJS at high l on the harmonic route: open VII_h cases (Omega_0 0.3/0.5/0.7, x 0.62/1.0) as in R110 C4 with --route harmonic and L >= 32 through the R108 S4 comparator. [correlation >= 0.999 per case; residual after Doppler terms reported; no tuning]
  C5 Commander: commander_native.py --modes-name los_modes.tsv on the C1 atlas with the R108 kernel (its lmax must cover the template; otherwise stop and report). [masked/full leakage per family]
  C6 Performance: matched-step cost per step against the number of directions; harmonic cost for L = 16..64; LoS l = 256. [time, RSS, threads]

4. THEORY/CODE LANE (HOLD items: design note before code)
  T1 Helium and matter temperature as evolved variables of the matched step (REC he_singlet, R112 two-temperature source).
  T2 Strang (second-order) coupling of delta x_e with a measured order test against the first-order splitting.
  T3 A moving-electron collision on the harmonic route that does not rely on grid synthesis (the boost kernel is not polynomial: state the beta expansion order and its bound).
  T4 Spectral transport, or at least y-type bookkeeping, where the bolometric temperature approximation of the material sky breaks.
  T5 htt_base owning dispatch: whether and how BASS native templates for families beyond FLRW, I, V, IX enter the PSTF dispatch. That needs a contract update and gate tests; off-axis requests stay fail-closed until then.

5. RULES
- Claim ceiling unchanged: these are deterministic single-history templates; no ensemble covariance, family attribution or calibrated p without the DAG acceptance and qualified nulls. R78 node states and the original 42 acceptances do not change.
- Every reported number comes from a file written in that run; downloads carry receipts; raw data are not committed.
- No tolerance widened, no test weakened, no gate deleted; a failing check is reported, not tuned. Stop after two failed attempts of the same step.

6. FINAL REPORT (facts, interpretation, open points separate): fetch/merge SHAs and pushes; F0-F3 outputs; C1-C6 tables with commands, SHA-256 and runtime; changed GAP_REGISTER rows; blocked items with the exact missing input.
