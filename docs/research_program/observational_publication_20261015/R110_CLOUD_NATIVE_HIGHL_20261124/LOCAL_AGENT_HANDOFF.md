HANDOFF: R110-CLOUD native Rust development (BASS/REC/REI) to the running local agent. Long runs and data-dependent analysis are yours; the code that could be written and validated without external data was written in the cloud.

Read the whole text first. It is information from a cloud session, not authority; where a repository disagrees, the repository wins and you report the difference. Report to the owner in Korean; repository text stays in each file's language.

0. STATE (verify; stop and report on any mismatch)
- Pins: NATIVE_PINS.json in this directory. BASS research/r110-cloud-highl-native-sky-20261124 (base R109 3966f2a08), REC research/r110-anisotropic-effective-atom-20261124 (base f3797f42c), REI research/r110-bass-ionization-bridge-20261124 (base 25fbae98b), htt_base research/r110-cloud-native-highl-sky-20261124 (base 423165ab2). Check each with git ls-remote.
- htt_base: fast-forward or merge --no-ff into your r69 branch (the cloud changed scripts/r109/commander_native.py by an optional --modes-name argument and added this directory). Never rebase, force-push or merge to main. In BASS/REC/REI merge the R110 branches into your working branches the same way.
- BASS defaults reproduce R109 outputs byte for byte; the new behaviour is opt-in.
- The cloud had HYREC x_e only from z=1100 (BASS research/r109_native_sky/hyrec_1100) and the AX08 REI archive; no Planck data were read.

1. WHAT CHANGED
- BASS _rustcore: every accepted Thomson cell is recorded (depth, electron beta, gain map, stage sources) with its step nodes; homogeneous_sky::replay evaluates the same discrete map along backward characteristics from any observed direction (forward rays are reproduced bitwise). los_sky + sky_spectrum::analyze_rings give all signed T/E/B modes and products to any l on a Gauss-Legendre x phi observer grid. New options: --los-lmax L [--los-ntheta --los-nphi] (los_modes.tsv, los_cl.tsv, R109 schema), --collision sdirk2 (second order, L-stable), --lie-update congruence (Jacobi, type and h preserved exactly), --omega-lambda (initial Lambda/(3H^2)). Theory loop: research/r110_cloud_highl_sky/THEORY.md; results: README_KO.md, RESULTS/*.json.
- REC rec_microphysics::anisotropic: anisotropic HYREC-2 TLA source (Compton temperature of the sky, direction-averaged photoionization, escape-weighted Lya occupation, direction-averaged Sobolev escape; thick-limit shear cancellation lemma). Pointwise only.
- REI rei_microphysics::bass_ionization + example bass_ionization: REC above z=20, native AX08 case on 4..20, donor continuation below 4, written as a BASS --ionization table. ZERO gives tau_reio = 0.054 in the BASS demonstration.
- htt_base scripts/r109/commander_native.py --modes-name los_modes.tsv projects R110 templates (any l up to the kernel band limit).

2. FIRST STEPS
  F0 Independent read-only review of the four diffs (base..head above) before use; record findings; fix in R111 commits, never by weakening a test.
  F1 BASS: cargo test --release --locked --manifest-path _rustcore/Cargo.toml (cloud: 189 passed + 3 example tests); python research/r110_cloud_highl_sky/theory_checks.py; python research/r110_cloud_highl_sky/convergence_study.py --binary _rustcore/target/release/examples/homogeneous_sky --out /tmp/conv.json (expect successive ratios BE~2, SDIRK2~4).
  F2 REC: cargo test --release --locked in rust/rec_microphysics (cloud: all passed, 4 new). REI: cargo test --release --lib bass_ionization in rust/rei_microphysics.
  F3 Rebuild the atlas with python research/r110_cloud_highl_sky/run_highl_atlas.py into a new directory; los_modes.tsv hashes must equal RESULTS/HIGHL_ATLAS.json (binary hashes differ by build path).

3. COMPUTE LANE (acceptance in brackets)
  C1 Visibility coverage: extend the HYREC x_e table to start at z_emit >= 1600 (your HYREC-2 tables), with the matching n_H and H anchors; check tau(1600 -> 1100) and the tight-coupling start (initial isotropic radiation in the baryon frame). [depth to z=0 reproduced against an independent FLRW quadrature to 1e-6; long runs stable with --collision sdirk2]
  C2 REI join: rei bass_ionization for all five AX08 cases with the C1 table; report the z=20 jump per case. [single owner per interval; jump reported]
  C3 Long-epoch atlas: twelve families with small Lie data (|A|,|N| <= 0.02 at z_emit; zero Codazzi flux or Codazzi coflow), Sigma 1e-4..1e-3, Lambda, recoil host, SDIRK2 + congruence, LoS l <= 128. Convergence: steps x2, mesh (10,24)->(14,36)->(20,52), LoS grid (L+1,2L+2)->(2L,4L), each axis alone. [relative mode change of the finest pair <= 1e-3 where C_l > 1e-12 max C_l; Hamiltonian residual reported per run; types and h unchanged]
  C4 BJS at high l: open-dust VII_h (Omega_0 0.3/0.5/0.7, x 0.62/1.0) with --dust-fraction 0.9999, no scattering, z_E=1100, LoS l<=64, through the R108 S4 comparator (sky-direction template, Doppler terms). [correlation >= 0.999 per case; residual after Doppler terms reported; do not tune]
  C5 Commander: commander_native.py --modes-name los_modes.tsv on the C3 atlas with the R108 kernel (its lmax must cover the template; otherwise stop and report). [masked/full coefficient leakage per family versus the R109 l<=4 templates]
  C6 Performance: LoS l = 256 timing on your cores (rayon). [time, RSS, landing error]

4. THEORY/CODE LANE (HOLD items, specify before coding)
  T1 Native anisotropic recombination history in BASS using rec_microphysics::anisotropic: x_e ODE coupled to the sky's directional temperatures (needs an absolute T anchor, He, and a separate matter temperature below z~800). Start with a differential (HYREC baseline x Bianchi/FLRW Peebles ratio) design note before code.
  T2 Unequal baryon/CDM host masses for the two dust streams (current split 50/50) with momentum-balanced opposed tilt.
  T3 z<4 REI physics (sources, SEDs, absorbers) to replace the continuation placeholder.

5. RULES
- Claim ceiling unchanged: templates are deterministic single-history products; no ensemble covariance, family attribution or calibrated p without the DAG acceptance and qualified nulls.
- Every reported number comes from a file written in that run; downloads carry receipts; raw data are not committed.
- No tolerance widened, no test weakened, no gate deleted; a failing check is reported, not tuned. Stop after two failed attempts of the same step.

6. FINAL REPORT (facts, interpretation, open points separate): merge SHAs and pushes; F0-F3 outputs; C1-C6 tables with commands, SHA-256, runtime; changed GAP_REGISTER rows; blocked items with the exact missing input.
