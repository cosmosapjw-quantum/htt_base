# REV-R155..R158 - v8 (Sixth Revision): primary-source rederivation, exact realization, Teff lane

owner: COMMON
implementation_scope: common (htt/obsstat + htt/teff + formal_mathlib + wolfram + report)
claim_tier: diagnostic_only
transfer_source: none (web-sourced primary literature + exact symbolic algebra; no downloads)
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Solve M4 by web-searching the original MES paper for the coefficient definitions; re-run the
adversarial-verification subagents that died on a spend limit; do the remaining non-data-blocked
deferrals (everything except 1TB-download items like K1 E2E); and apply the new max-entropy Teff
draft uploaded at repo root, reviving the deprecated TSC module.

## What landed (finding -> response -> seal)

- **M4** (registered-external MES coefficients) -> **sigma rederived bit-exact** from MESa
  (astro-ph/9501016) raw eq (51) + C1/C2; omega/accel pinned to MESb (PRD 51,5942, print-only)
  with documented Paper-I/II lineage. `mes_rederivation_seal`. Ticket -> partially_resolved.
- **T3-full** (deferred King-Ellis) -> **exact endpoint attainability**: both identified-interval
  endpoints realized by exact homogeneous initial-data configs (Bianchi I / Bianchi V transverse
  shear + antipodal tilt), exactly-zero Gauss+momentum residuals. SymPy + Wolfram/xAct.
  `nonlinear_realization_seal`. NOT a full nonlinear interval-sharpness theorem (P31 bound +
  King-Ellis dynamics stay deferred; corrected after the adversarial pass).
- **mathlib** -> separate `formal_mathlib/` (mathlib v4.31.0) proving forall-parameter T1'/DL1/T2'
  over the rationals; core native_decide lane untouched. `egs3_v8_mathlib_seal`.
- **K5 Omega_k** -> leading-order structural null already certified (measured_response_seal);
  finite ceiling documented as blocked on the higher-order transfer (not a download).
- **Teff draft + TSC revival** -> additive active `Owner.TEFF` + `TEFF_REPRESENTATIVE` bundle
  (diagnostic_only), legacy freeze untouched; `htt/teff/` implements a_xi=(2,2zeta4,(7/4)zeta4),
  c_p=(p-4)/2^{p+1}, SO(3) Gram PSD + L^2 staircase, two-temp R4=1/R3=-3/2/R5=+5/2
  nonidentifiability. SymPy + Wolfram. `teff_representative_seal`.
- **Adversarial verification** (re-run of the spend-limit-killed pass) -> 7 skeptics, 5 CONFIRMED
  / 2 PLAUSIBLE / 0 REFUTED, all math correct; honesty fixes applied in-session.
  `v8_adversarial_verification.json`.

## New engines / lanes

- `formal_mathlib/` mathlib-backed Lean lane (`make v8-mathlib`); `wolfram/v8_t3_king_ellis.wls`
  + `wolfram/v8_teff_representative.wls` (`make v8-wolfram`); `make teff-gates`; `make v8-seals`.

## Surface

- `make egs3-gates` 163 -> 183 (M4 + T3-full gates); `make teff-gates` 9 (separate lane).
  CLAIM_LEDGER += 3.
  New tickets: t3_king_ellis, k5_omega_k_higher_order_ceiling, teff_representative_nonclaims,
  gf_interval_latent_quotient_bug.
- `scripts/build_external_audit_report_v8.py` -> `external_audit_research_report_20260710_v8/`
  (47-page PDF + zip) + root PDF; new Sixth-Revision response section + adversarial-verification
  summary rendered from the v8 seals; REQUIRED_ARTIFACTS += 4 v8 seals; --check byte-stable;
  check_claim_language clean. v5/v6/v6.1/v7 packages byte-frozen.
- Regenerated pr04-research + code-capability audit packages to inventory the new surface
  (also cleared a pre-existing code-capability staleness).

## Claim discipline

Diagnostic-only. Web-sourced primary literature + exact symbolic/closed-form seals; no data,
detection, family/geometry, native-solver, or posterior claim. x_C anchors + W2_max=1.309e-6
bit-identical; TSC_LEGACY freeze + guard tests untouched. Deferred (ticketed): full King-Ellis
dynamical realization, MESb print-scan value-pin, K1 E2E / DESI randoms / K6 (1TB downloads),
K5 higher-order Omega_k transfer, v7 T2' latent-path fix (next re-freeze cycle).

## Validation

| Check | Status |
| --- | --- |
| `make egs3-gates` | 191 OK |
| `make teff-gates` | 9 OK |
| `make v7-sympy-seals` + `--check` | all PASS + current (incl. mes_rederivation, nonlinear, teff) |
| `make v8-wolfram` (T3-full + Teff, xAct) | PASS |
| `make v8-mathlib` (`lake build`) | PASS (8560 jobs) |
| `build_external_audit_report_v8.py` + `--check` | 47-page PDF; text artifacts byte-stable |
| v7 report `--check` | still byte-frozen |
| `check_claim_language.py` v8 package | clean |
| adversarial verification (7 skeptics) | 5 CONFIRMED / 2 PLAUSIBLE / 0 REFUTED |
| `pytest tests/contracts` | 1 pre-existing (cf4pp network-blocked) vs 2 at baseline |
