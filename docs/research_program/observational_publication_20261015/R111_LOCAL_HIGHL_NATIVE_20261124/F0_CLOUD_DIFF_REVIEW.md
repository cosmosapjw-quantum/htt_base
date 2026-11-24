# F0 Independent Read-Only Review of R110-CLOUD Diffs

- **Reviewer**: Read-only `research` subagent (`fbdb2b3d-73fa-4403-8621-17d2b63e9006`)
- **Reviewed ranges**:
  - `BASS`: `3966f2a0824a8b32309a8a99481dd6940b952a35..21dc1a9302eb2053e0ac544827ab32e6899b9058`
  - `REC`: `f3797f42c36632d80a67f23a4e587f0799d12cc5..be75f8b1c3dbfb50ecd44fdbd6afae69ec9d959d`
  - `REI`: `25fbae98b3d63a47dfe7200160c86a36c5f80d27..fe3b4595616350c3f3d2013ebf3d761ec5115559`
  - `htt_base`: `423165ab295dbd86064dbe116d7507c270ed3d10..3f114045da63c760e0ce76522a96e1ae5bb49699`
- **Summary**: 0 CRITICAL, 1 HIGH, 4 MEDIUM, 5 LOW findings. Core derivations (discrete replay, backward Lie-group characteristics, Alexander SDIRK2, Gauss-Legendre ring SHT, Lie congruence, Omega_Lambda, REC anisotropic source) are algebraically consistent.

## Findings and R111 Remediations

1. **[HIGH] F0-1 (BASS)**: `los_sky` (`replay.rs`) omitted `min_eig < -1e-9 * min_i` negative transverse screen-eigenvalue rejection, and `recoil::trial` (`recoil.rs`) aborted instead of bisecting (`Ok(None)`) when SDIRK2 overshot positivity (`R_min = -0.2071`).
   - *Fix*: Added `min_eig` guard in `los_sky`, separated nonfinite/nonpositive errors in `to_normal`, enabled SDIRK2 nonpositivity bisection in `recoil::trial`, and added Rust unit tests.
2. **[MEDIUM] F0-2 (htt_base/BASS)**: `LOCAL_AGENT_HANDOFF.md:8` claims byte-for-byte R109 reproduction; `modes.tsv`, `cl.tsv`, `diagnostics.tsv` are byte-identical under defaults, while `run.txt` adds 10 R110 keys. `RESULTS_KO.md:6` states `+50%` at Lyα (`2차식 대비`) whereas `(exact - second)/second = +101.12%` (`2nd` underestimates exact by `50.28%`). Test count observed: 173 unit + 16 integration = 189 (`+ 3` in `examples/sky_covariance.rs`).
   - *Resolution*: Repository wins; documented transparently without altering R110 history.
3. **[MEDIUM] F0-3 (htt_base/BASS)**: `run_highl_atlas.py` defaults overwrite `RESULTS/HIGHL_ATLAS*` if `--summary/--tarball` are omitted; `commander_native.py` hardcoded `recoil_` archive member prefix and lacked unit tests.
   - *Fix*: F3 used explicit output paths in `/home/cosmosapjw/Downloads/htt_r111/f3_raw/`; added `--member-prefix` (default `recoil_`) to `commander_native.py` and added `tests/obsstat/test_r111_commander_native.py`.
4. **[MEDIUM] F0-4 (REI/REC/BASS)**: HyRec `n_H0 = 0.1897171235 m^-3` (`m_H`) differs by `+0.0541%` from REI AX08 `n_H0 = 0.1898198451 m^-3` (`m_p`). R110 Part B used `duration=7.0` (`z=0.003982`), `dust_fraction=0.75`, and omitted `+0.685` from `OMEGA_LAMBDA_1100` denominator.
   - *Resolution*: C1/C2 report both anchors and quantify the `+0.0541%` optical depth shift; C1/C3 use exact `duration = ln(1+z_emit)`, exact `dust_fraction`, and exact `Omega_Lambda`.
5. **[MEDIUM] F0-5 (REI)**: `bass_ionization::merge` allowed `z_low == 0.0` (causing `0/0` NaN and duplicate `eta`), dropped `rec(z=20)` knot in favor of `rei(z=20)` (documented `2.4e-7` linear bridge effect), and `examples/bass_ionization.rs` used unchecked CSV indexing.
   - *Fix*: Reject `z_match <= 0` in `Continuation::xe`, skip continuation cleanly when `z_low == 0.0`, use `.get().ok_or()?` in example CSV parser, and add unit test.
6. **[LOW] F0-6 (BASS)**: `homogeneous_sky.rs:361` logged `required_initial_q_over_E` with `omega_lambda=0` instead of `&sol.history[0].node`. Fixed.
7. **[LOW] F0-7 (BASS)**: `sky_spectrum::analyze_rings` lacked `n_phi >= 2*lmax+1` Nyquist check and used `1 - z*z`. Fixed with unit test; `(1-z)*(1+z)` branch activates for `|z| > 0.99999` so F3 `l<=48` Gauss-Legendre rings keep bitwise SHA-256 parity (`32/32`) with `HIGHL_ATLAS.json`.
8. **[LOW] F0-8 (BASS)**: `Settings` expanded without `Default`/`#[non_exhaustive]`. Noted.
9. **[LOW] F0-9 (REC)**: `escape_rate_factor` canceled for `tau0 << 1`; baryon rest frame assumption undocumented. Fixed (`tau0 < 1.0` branches to `tau0 * sobolev_escape_average`) with thin-depth test.
10. **[LOW] F0-10 (BASS)**: 1-ulp local BLAS/hardware diff in `THEORY_CHECKS.json`. Restored clean git state in BASS; local F1 result retained separately.
