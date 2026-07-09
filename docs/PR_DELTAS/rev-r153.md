# REV-R148..R153 - v7 (Fifth Revision) external-audit report: strengthened theorems

owner: COMMON
implementation_scope: common (htt/obsstat + research_gates/egs3 + formal + sage + wolfram + report)
claim_tier: diagnostic_only
transfer_source: none (symbolic seals + synthetic witnesses; no downloads, no raw data)
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Answer the four 2026-07-09 external review bundles (critic + referee F1-F3/M1-M10/m1-m12
+ fortification + strengthened-publication) and produce a v7 (Fifth Revision) research
report. Strengthen every flagged result rather than tone it down.

## Findings addressed (finding -> strengthened response -> seal)

- **F1** Omega_k signed domain -> **T1'** signed-box two-branch identified interval
  ([0.11,0.17] open / [0.09,0.17] all) + DL1 monotonicity. `signed_box_interval_seal`.
- **M1** P36 "strict whenever" refuted -> **T2'** strictness-iff (strict iff a shared
  component has c_N c_D>0); 400/400 exact-Fraction witness + aligned counterexample.
  `gf_strictness_exact_seal`.
- **M2** P31 sharpness gap -> **T3-lin** linearized realization of both endpoints by a
  1+3 initial-data mode superposition (Gauss+momentum residuals <1e-10) + xAct covariant
  seal; full nonlinear King-Ellis realization deferred (ticketed). `linearized_realization_seal`.
- **M3/P35/E3** -> **T4'/T5'/T8'** estimated-covariance Hotelling/F thresholds (exact size),
  exact deterministic-width Imbens-Manski coverage, consistent monotone noncentral-chi2 power;
  each cross-checked by independent Monte-Carlo. `coverage_strengthened_seal`.
- **m1** -> **T9'** exact multi-component tilt Gauss budget; single-species bit-identical.
  `multicomponent_tilt_seal`.
- **M4** MES coefficients not rederived -> provenance seal: cross-registry consistency, a
  genuine rederivation of the ordering theorem B_sigma>B_omega>B_accel (Thm 3.4), the (3/2)
  conversion, epsilon-registry provenance (registered W2_max=1.309e-6). Multipole coefficients
  honestly stay registered-external (ticketed). `mes_provenance_seal`.
- **M5** measured R undisclosed -> whitened-R SVD disclosure: rank-2 structural (sigma3/sigma2=0),
  null {W2, Omega_k}, Fisher duplication 2/(1+rho). `measured_response_seal`.
- **M6/M7** DESI window / CF4 Malmquist -> synthetic forward models reproducing both systematics
  from zero signal. `data_lane_forward_seal`.
- **F2** no worked application -> end-to-end K5/CF4 identified-interval card on real CF4 |B| with
  the registered MES W^2 ceiling (observational claim withheld; Sigma^2/Omega_k registered-pending).

## Multi-engine seal lanes (new)

- SymPy (report-gating), SageMath+Singular (`egs3-sage`; exact-QQ polyhedra reproducing the F1
  endpoints + Bianchi V ideal membership), Lean 4 core (`egs3-lean`; `native_decide` gate-promotion
  lattice + endpoint certificates), Wolfram/xAct (`v7-wolfram`; T4' FRatioDistribution + T3-lin
  covariant residual). `make v7-seals`. Report gating stays SymPy-only.

## Surface

- `make egs3-gates` 109 -> 169 (axis G G1-G10 + realization). Results table 32 -> 43 rows.
  CLAIM_LEDGER += 8. New tickets: mes_full_rederivation.
- `scripts/build_external_audit_report_v7.py` -> `external_audit_research_report_20260710_v7/`
  (45-page PDF + zip) + root PDF; new Fifth-Revision response section rendered from the seal
  artifacts; REQUIRED_ARTIFACTS += 8 v7 seals; --check byte-stable; check_claim_language clean.
  v6/v6.1 packages left byte-frozen.
- Completed a v6.1 figure-curation migration (fixing a Phase-0 conditioned-legacy desync);
  regenerated all audit packages.

## Claim discipline

Diagnostic-only. Symbolic/closed-form seals + synthetic forward-model witnesses; no data,
detection, family/geometry, native-solver, or posterior claim. x_C anchors bit-identical
(axis-G CoVe guard); parent-identity + Bianchi V seals byte-frozen. Deferred + ticketed: full
nonlinear T3, MES multipole rederivation, K1 real E2E, DESI certified randoms, K5 Sigma^2/Omega_k
registered artifacts, mathlib-backed Lean generalizations.

## Validation

| Check | Status |
| --- | --- |
| `make egs3-gates` | 169 OK |
| `make v7-seals` (SymPy/Sage/Lean/Wolfram) | all PASS + `--check` current |
| `build_external_audit_report_v7.py` + `--check` | 45-page PDF; text artifacts byte-stable |
| `check_claim_language.py` v7 package | clean |
| `claim_lint_research_surfaces.py` / `pdf_claim_lint.py` | clean |
| `pytest tests/contracts` | 391 passed / 1 pre-existing (cf4pp network-blocked in sandbox) |
