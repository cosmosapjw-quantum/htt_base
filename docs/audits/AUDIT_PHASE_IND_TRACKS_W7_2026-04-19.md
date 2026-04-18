# Phase-boundary audit — Independent Tracks Week 7

**Phase tag**: `IND_TRACKS_W7`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.2 §21 Week 7 day-by-day schedule
— TSC-03 (Days 1-2), TSC-05 (Day 3), TSC-06 (Days 4-5),
CONTRACTS-02 (Day 6), DOS-A30-MIO A35/A38/A40 (Day 7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**: v3 §4.5.4 (G19 hard separation);
§10.2bis (enforcement matrix); §11.14.6 (MIO appendix A30-range);
v3 §9.2 (F_Bayes published band); INDEPENDENT_TRACKS_PLAN v1.1
§14.3 (TSC-06 v3 G19 guard).
**Baseline head**: `fdd911e` (prior independent-tracks phase
`IND_TRACKS_W6: phase audit + next-session prompt rotation`).
**Commits this phase**:
`75b51c5` (W7D2 TSC-03 three-bound hierarchy),
`02b9b63` (W7D3 TSC-05 michaelis_menten export),
`a262bbb` (W7D5 TSC-06 htt_bridge + G19 guard),
`2d6d653` (W7D6 CONTRACTS-02 A34 G19 protocol doc),
`acef13f` (W7D7 DOS-A30-MIO A35/A38/A40 drafts).
The post-LB cleanup commit `9fe03dd` AUDIT(LB-cleanup) landed on the
bass-side lane in between and is NOT part of this audit.
**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/ bass_py/tsc/charts/
bass_py/tsc/integration/ bass_py/workspace/ bass_py/mio/` →
**994 passed, 0 failed, 8 skipped**. Week 7 delta vs Week 6
(878 / 0 / 8): **+116 new tests**, zero regressions, skip count
unchanged.

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Physics / math | MES three-bound hierarchy B_σ > B_ω > B_ü holds for positive (ε₁, ε₂, ε₃) with at least one of ε₂ or ε₃ nonzero | `tsc/admissibility/three_bound_hierarchy.py::compute_three_bound_hierarchy` | MES 1995 Paper II Theorem 3.4; htt.core.bounds coefficient table |
| Physics / math | Induced MES ceilings Σ²_max > W²_max > A²_max follow from the same hierarchy via X_max = (3/2) B_X² | `Sigma2_max`, `W2_max`, `A2_max` | MES Corollary 3.1 |
| Physics / math | W10-01 Route B SSOT: D_2(Σ² = 1e-8) ≈ 0.17411 μK² with C_1 = 1.753e7, C_2 = 6.825e5 | `tsc.charts.michaelis_menten_export.ROUTE_B_{C1,C2,D2_AT_SIGMA2_1EM8}` | bass_rs/d2_convention.rs (Rust); bass.spectrum.cl_assembly (Python mirror) |
| Physics / math | F_Bayes = 0.093 ± 0.025 (68 % → [0.068, 0.118]) at the S3 scenario | `tsc.integration.htt_bridge.PUBLISHED_F_BAYES_BAND = (0.068, 0.118)` | BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §9.2 |
| Contracts | `FFCrossCheckReport.is_cross_check` is frozen True; ValueError on attempted negation at construction | `tsc/integration/htt_bridge.py::FFCrossCheckReport.__post_init__` | v3 §4.5.4 G19; v1.1 §14.3 TSC-06 guard |
| Contracts | No merge-style API exists on the tsc↔htt bridge (no `merge`, `combine`, `unified` in `__all__`; no `F_Bayes_merged` field) | `TestTscHttFfCrossCheckNotMerged` | v3 §4.5.4 G19 sentence "never summed into a single master score"; A39 |
| Contracts | tsc-side MES bounds agree with `htt.core.bounds.{B_sigma, B_omega, B_accel}` to rtol 1e-10 | `compare_against_htt_bounds(...)` + `test_three_bound_hierarchy_matches_htt_bounds` | TSC-03 hero anchor; v1.2 §21 Days 1-2 gate |
| Contracts | tsc-side MM SSOT agrees with `bass.spectrum.cl_assembly.ROUTE_B_{C1, C2, D2_AT_SIGMA2_1EM8}` and `bass.observational.planck_mes_bounds.T_CMB_K` at bit-identity | `assert_mirror_matches_bass_ssot()` + `test_tsc_mm_constants_match_bass_ssot` | TSC-05 hero anchor |
| Manuscript | A34 documents the five-property definition of a G19-compliant cross-check plus the failure modes a merge would introduce | `docs/dossier/A34_g19_cross_check_protocol.md` | v3 §4.5.4; v1.1 §14.3 |
| Manuscript | A35/A38/A40 cross-reference landed MIO modules (HJ-02a + HJ-05a-lite) and codify the G19 stance | `docs/dossier/A35_directional_coherence.md`, `A38_masked_sky_caveats.md`, `A40_g19_architectural_stance.md` | v3 §11.14.6 (MIO appendix slots) |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `B_sigma/omega/accel(e1, e2, e3)` | non-negative finite floats | float | ✓ `_validate_epsilons` rejects negative or non-finite |
| `Sigma2_max/W2_max/A2_max(e1, e2, e3)` | non-negative finite floats | float ≥ 0 | ✓ via chained B_* evaluators |
| `compute_three_bound_hierarchy(...)` | ε triple + optional Bianchi type label + strict flag | `ThreeBoundReport` | ✓ HierarchyViolationError in strict mode when B_σ ≯ B_ω ≯ B_ü; ValueError for unknown type_name |
| `evaluate_all_bianchi_types(...)` | ε triple + strict flag | dict keyed by the 9 BIANCHI_TYPES | ✓ first offender raises in strict mode; labels round-trip |
| `compare_against_htt_bounds(...)` | ε triple + rtol | diagnostic dict with `all_agree` boolean | ✓ lazy-imports htt.core.bounds; returns floats + bools |
| `d2_route_b(sigma_sq, C1, C2)` | non-negative finite (scalar or ndarray) | float or ndarray (dispatch on scalar) | ✓ rejects C1 ≤ 0, C2 ≤ 0, negative or non-finite σ² |
| `michaelis_menten_coefficients(...)` | optional provenance | `MichaelisMentenExport` (frozen) | ✓ literals echoed from SSOT mirror |
| `export_as_dict/json(...)` | optional export + path + indent | dict / JSON string | ✓ frozen schema keys; round-trips through tmp_path |
| `assert_mirror_matches_bass_ssot(rtol=0.0)` | rtol | None | ✓ AssertionError with "drift" message on any coefficient divergence; covers C1, C2, D2 sentinel, T_CMB |
| `FFCrossCheckReport(...)` | tsc + htt F_Bayes scalars + metadata | frozen dataclass | ✓ `is_cross_check=True` enforced at __post_init__; n_samples ≥ 0 |
| `ff_gaussian_cross_check(mean, sigma, B, ...)` | finite scalars | `FFCrossCheckReport(scenario='gaussian')` | ✓ rejects sigma ≤ 0, B ≤ 0; closed-form vs MC rtol ~1e-3 at 500k draws |
| `ff_htt_mc_cross_check(scenario, N, seed, w)` | SCENARIOS key + positive N | `FFCrossCheckReport(scenario=<name>)` | ✓ raises ValueError on unknown scenario; RNG stream aligned between tsc and htt paths |
| `assert_cross_check_consistent(report, rtol, require_within_band)` | report + rtol + flag | None | ✓ CrossCheckMismatch (AssertionError subclass) on rel_diff > rtol or band violation |

## 3. Phys-math audit ledger

| # | Check | Verdict | Note |
|---|---|---|---|
| 1 | MES coefficient exactness (tsc Fraction table) | PASS | `COEFFS["sigma"] == (5/3, 3, 3/7)`, `"omega" == (3/4, 2, 2/7)`, `"accel" == (3/4, 1, 3/14)`; test_sigma_coeffs, test_omega_coeffs, test_accel_coeffs. |
| 2 | Hierarchy B_σ > B_ω > B_ü for positive ε when at least one of (ε₂, ε₃) > 0 | PASS | test_hierarchy_holds_positive_eps at 5 parameter combinations; test_ratios_less_than_one. |
| 3 | Edge case ε₂ = ε₃ = 0 ⇒ B_ω = B_ü; strict mode must flag | PASS | test_eps1_only_degenerate_equality asserts both raise in strict=True and hierarchy_strict=False in strict=False. |
| 4 | Hero rtol 1e-10 bit-identity tsc ↔ htt | PASS | test_three_bound_hierarchy_matches_htt_bounds + 5-parameter sweep in test_tsc_htt_agreement_on_sweep. |
| 5 | Route B D_2 sentinel at σ² = 1e-8 | PASS | 1.753e-1 / (1 + 6.825e-3) = 0.17411 μK², test_at_sigma2_1em8_matches_sentinel. |
| 6 | MM monotonicity in σ² on [1e-12, 1e-5] | PASS | test_monotonic_in_sigma_sq (30-point log grid). |
| 7 | MM large-σ asymptote D_2 → C_1 / C_2 | PASS | test_asymptote_at_large_sigma at σ² = 1e6. |
| 8 | TSC-05 bit-identity bass mirror (rtol 0.0) | PASS | test_tsc_mm_constants_match_bass_ssot, test_T_CMB_matches_planck_mes_bounds. |
| 9 | Drift injection fires regression | PASS | test_drift_would_raise monkeypatches ROUTE_B_C1 and confirms AssertionError("drift"). |
| 10 | S3 F_Bayes lands in [0.068, 0.118] from both tsc and htt | PASS | test_S3_cross_check_within_published_band. |
| 11 | tsc path vs htt path agreement on shared RNG stream rtol < 1e-6 | PASS | test_S3_tsc_htt_numerical_agreement. |
| 12 | is_cross_check frozen True at construction | PASS | test_default_is_cross_check_true + test_rejects_is_cross_check_false; __post_init__ ValueError path. |
| 13 | Gaussian closed-form vs MC at published anchor | PASS | test_published_scenario_yields_band at 200k draws; rel_diff < 1e-3. |
| 14 | Loud-fail mismatch surfaces | PASS | test_mismatch_raises + test_band_violation_raises (CrossCheckMismatch subclass of AssertionError). |

No failures or partials.

## 4. Equation-to-code mapping audit

| Equation / definition | Source | Implementation site |
|---|---|---|
| B_σ = (5/3) ε₁ + 3 ε₂ + (3/7) ε₃ | MES 1995 Paper II Eq. (3.7) | `tsc.admissibility.three_bound_hierarchy.B_sigma` → ``_evaluate(COEFFS["sigma"], ...)``; htt-side in `htt.core.bounds.B_sigma`; cross-check test at rtol 1e-10 |
| B_ω = (3/4) ε₁ + 2 ε₂ + (2/7) ε₃ | MES Eq. (3.12) | same dual-implementation pattern as B_σ |
| B_ü = (3/4) ε₁ + 1 ε₂ + (3/14) ε₃ | MES Eq. (3.15) | same |
| Σ²_max = (3/2) B_σ² (and W², A² analogues) | MES Corollary 3.1 | `Sigma2_max/W2_max/A2_max` helpers |
| D_2(Σ²) = C_1 Σ² / (1 + C_2 Σ²) | d2_convention.rs SSOT | `tsc.charts.michaelis_menten_export.d2_route_b` matches `bass.spectrum.cl_assembly.route_b_d2_lookup`; frozen literal mirror |
| F_Bayes = E[|x_V| / x_max] with x_V = (1+w) Ω_m sinh²(ε₁/(1+η)), x_max = (3/2) [B_σ^corr]² | htt.core.analysis_extended.FillingFraction + BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §9.2 | `tsc.integration.htt_bridge._tsc_filling_fraction_from_stream` restates the literals; `FillingFraction.mc_posterior` is the htt-side companion; two RNG draws from the same seed produce identical F_samp up to the scalar-sum reduction |
| Frame correction B_σ^corr = (1 + 2.69 ε₁) B_σ | VT-07 | `(1 + 2.69 * eps1_ref)` appears in both the htt `mc_posterior` body and the tsc `_tsc_filling_fraction_from_stream` helper |

All equation-to-code mappings are redundantly implemented on both
sides exactly as required for the TSC-03 / TSC-05 / TSC-06 cross-check
gates to be informative. No dead placeholders, no helper-as-production
confusions.

## 5. Numerical / pipeline audit

- **Determinism**: `ff_htt_mc_cross_check` reseeds
  `numpy.random.default_rng(seed)` in both paths with the same
  integer. Stream alignment relies on drawing eps1 / eps2 / eps3 in
  the same order as `FillingFraction.mc_posterior`. Audited by
  reading both bodies side by side; the order matches (eps1 then
  eps2 then eps3).
- **Overflow / underflow**: MES linear combinations and Michaelis-Menten
  denominator are well-conditioned across the tested sweep
  (σ² ∈ [1e-12, 1e6]). No `np.errstate` overrides needed.
- **Tolerance sensitivity**: The TSC-03 cross-check assertion uses
  rtol = 1e-10; tested at 5 eps combinations including zero-eps1
  and large-amplitude cases. The TSC-05 mirror check uses rtol = 0.0
  (bit-identity) and passes on 3.13 interpreter.
- **Reproducibility**: All three modules expose their seeds and
  scenario tags in the `config` echoes. `export_as_json` uses
  `sort_keys=True` so disk snapshots are reproducible byte-for-byte.
- **Skip / placeholder tracking**: Week 7 adds zero new skips. The
  standing 8 skips (W5 SKIP-05-LATENT pipeline-output fixtures,
  W5 DYNESTY-DEP, W6 SKIP-02b-v3-LEGACY) carry forward unchanged.

No numerical-layer issues detected.

## 6. Ranked failure modes

No P0 or P1 findings. Carry-forward-only entries below.

### FM1 · bass_py/tsc/ test count gate interpretation (P2)

**Type**: Testing / plan bookkeeping.
**Severity**: P2.
**Symptom**: INDEPENDENT_TRACKS_NEXT_SESSION.md §2 Week-7 final gate
says "bass_py/tsc/ 테스트 ≥ 700 (현재 615 + TSC-03/05/06 ≈ +~85)". The
actual `bass_py/tsc/` count before W7 was 482, not 615; after W7 it is
**598** (482 + 51 TSC-03 + 33 TSC-05 + 32 TSC-06 = 598).
**Root cause**: The "615" figure in the next-session prompt was an
overestimate from a rotation several weeks earlier; actual tsc-only
count has been ~482 since W4 (TSC-01 / 02 / 04 landings).
**Cheapest test**: `venv/bin/pytest bass_py/tsc/ --collect-only -q |
tail -3`.
**Correct interpretation**: the +116-test delta (well above the +85
target the plan anchored on) has been delivered; the absolute ≥700
gate was a stale figure.
**Action**: document here and update the next-session prompt header.
No P0/P1 impact.

### FM2 · ff_htt_mc_cross_check stream-alignment is a spec-shared dependency (P2)

**Type**: Interface / testing.
**Severity**: P2.
**Symptom**: `ff_htt_mc_cross_check` draws eps1 / eps2 / eps3 in the
same order as `htt.core.analysis_extended.FillingFraction.mc_posterior`.
If a future htt PR reorders the draws (e.g. samples eps2 before
eps1, or adds an additional rng.normal call mid-stream), the tsc
path diverges without either side's internal tests catching it; the
`test_S3_tsc_htt_numerical_agreement` rtol 1e-6 gate does surface
it, but the failure message points to "TSC-06 regression" rather
than "htt stream order changed".
**Root cause**: The tsc side re-seeds the same RNG and redraws; this
is the fastest implementation but couples to the htt body.
**Mitigation candidate**: Refactor `FillingFraction.mc_posterior` to
accept a pre-drawn triple (eps1, eps2, eps3) as a keyword argument;
tsc side provides the triple. Then the two paths share a single
draw by construction. **Not a W7 target** — requires touching the
bass/htt lane and must coordinate with that session.
**Cheapest test**: already in place; test fails loudly on stream
drift.
**Action**: record here as Week 8+ carry-forward.

### FM3 · Schema bump vs frozen-hash coordination (P3)

**Type**: Contract evolution.
**Severity**: P3.
**Symptom**: If TSC-05 JSON schema ever needs a new key (e.g. separate
`T_CMB_MICROK` entry for consumers that want μK natively), the
`SCHEMA_VERSION = "TSC-05/v1"` tag must bump and `test_dict_has_expected_top_level_keys`
must be updated in lock-step. Forgotten bump could leave consumers
relying on `"TSC-05/v1"` with the new keys missing.
**Root cause**: Schema freeze is enforced only via test literal,
not via a hash digest like `MioCertificate`.
**Mitigation candidate**: When an extension is actually planned, add
a hash digest test mirroring `test_miocertificate_schema_frozen`.
Premature for W7.

### FM4 · Placeholder σ_cone values on Radio / CF4pp / BiPoSH (P2, inherited)

**Type**: Data provenance.
**Severity**: P2.
**Status**: Documented in A35 §A35.2; same as W6 FM2 carry-forward.
**Action**: opportunistic during Week 8 MANU-CH12-NEW §12.2 draft.

### FM5 · `bass_py/tsc/integration/` is new surface (P3)

**Type**: Import path / tooling.
**Severity**: P3.
**Symptom**: The new `bass_py/tsc/integration/` subpackage is not
yet explicitly listed under `[tool.setuptools.packages.find]` in
`bass_py/pyproject.toml`, but the default glob matches it; tests
pass because `bass_py/conftest.py` prepends `src/` and the package
has a conventional `__init__.py`.
**Cheapest test**: the suite run already exercises the import path.
**Action**: no action; default glob covers it. Record as a pointer
so the next session doesn't re-audit this.

## 7. Verifier results

### A. Physics verifier

| Check | Result |
|---|---|
| known limit recovery (ε → 0 and large ε sweep) | **passed** — ceilings go to zero at ε=0, hierarchy preserved at 1e-2 |
| dimensional consistency (MES bounds dimensionless, D_2 in μK²) | **passed** |
| sign/normalization (non-negative amplitudes, x_V ≥ 0, F ≥ 0) | **passed** |
| positivity / admissibility (F_Bayes ≥ 0 under abs_mode='abs'; 'signed' safely used where x_V has definite sign) | **passed** |
| alternative explanation possibilities | **passed** — the hierarchy result is a coefficient identity, not a fit |

### B. Code verifier

| Check | Result |
|---|---|
| contract satisfaction (dataclass frozen flags, ValueError paths) | **passed** — 994 / 994 |
| actual code-path usage (lazy htt import avoids circular bass coupling) | **passed** |
| regression risk (drift injection test for TSC-05; mismatch test for TSC-06) | **passed** |
| reproducibility (seeds surfaced in config dicts; JSON sort_keys) | **passed** |

### C. Numerical verifier

| Check | Result |
|---|---|
| tolerance robustness (rtol=1e-10 for TSC-03, 0 for TSC-05, 1e-6 for TSC-06 numerical pair) | **passed** |
| convergence / stability (Michaelis-Menten smooth; rtol sweep stable) | **passed** |
| baseline reproducibility (D_2 sentinel + F_Bayes published band) | **passed** |
| uncertainty / misspecification awareness (carry-forwards explicit) | **passed** |

All three verifier batteries return **passed**.

## 8. Minimal repair plan

No P0 / P1 repairs required this phase. Two small clarifications
adopted in-session:

1. **Docs → prompt** — mark FM1 (test-count gate interpretation) and
   update the next-session prompt's "현재 615" figure on the
   next rotation so the Week-8 session has an accurate baseline. No
   code change.
2. **Carry FM2 to Week 8** — RNG stream-alignment dependency between
   tsc and htt mc_posterior. Refactor when the bass/htt lane is
   quiet. No code change this phase.

## 9. Minimal test set (exercised this audit)

| Category | Test | Pass criterion |
|---|---|---|
| Baseline reproduction | `test_three_bound_hierarchy_matches_htt_bounds` | tsc-htt rel_err < 1e-10 on the published (eps1_kin, eps2, eps3) triple |
| Edge / adversarial | `test_eps1_only_degenerate_equality` | strict=True raises on eps2 = eps3 = 0; strict=False surfaces hierarchy_strict=False |
| Physics sanity | `test_S3_cross_check_within_published_band` | both tsc and htt F_Bayes ∈ [0.068, 0.118] |
| Numerical stability | `test_S3_tsc_htt_numerical_agreement` | rel_difference < 1e-6 at 50 k draws |
| Regression | `test_drift_would_raise` (TSC-05) + `test_mismatch_raises` (TSC-06) | AssertionError when literals drift or when synthetic mismatch injected |

All five pass on the touched-surface run.

## 10. 최종 판정

- **판정**: **통과 (pass)**. Week 7 delivers TSC-03 / TSC-05 / TSC-06
  + CONTRACTS-02 + A35/A38/A40 drafts; 994 passed / 0 failed / 8
  skipped on the touched surface; +116 new tests; all v1.2 §21 Week-7
  sub-gates green except FM1 (the stale "615" baseline in the prompt
  — documented, no action).
- **지금 당장 구현할 1개**: none — all W7 work landed, no P0/P1 surfaced.
  On prompt rotation, refresh the "현재 615" figure to reflect actual
  tsc count **598** so Week 8 doesn't re-hit FM1.
- **지금 손대면 안 되는 1개**: `FillingFraction.mc_posterior` body
  on the htt side. FM2 flags the stream-alignment coupling, but the
  fix touches htt-internal state and must be coordinated with the
  bass/htt lane rather than resolved in this independent-tracks lane.

---

## 11. Carry-forward from prior audits

The following items were recorded in earlier phase audits and remain
open going into Week 8:

| Source | Tag | Status | Next step |
|---|---|---|---|
| W3 F1 | HEALPix RING vs iso-latitude ring scheme | P2 (open) | Swap when `healpy` adopted (parent plan §7.5) |
| W4 F1 | Mock coverage sandwich (`C_pix` non-uniform) | P2 (open) | Opportunistic during Week 8 |
| W4 F4 | Θ⁴ htt audit uses FD at h = 1e-2 | P2 (open) | Resolve when htt lands a native `_a2_coefficient_table` |
| W5 SKIP-05-LATENT | 5 pipeline-output fixture skips | P2 (open) | Week 8 HTT-STAB — add synthetic fixture stubs |
| W5 DYNESTY-DEP | `dynesty` install pending | P2 (open) | `venv/bin/pip install dynesty` in next convenient window |
| W5 APPLY-BIAS-AMP | `ChannelSummary` lacks amplitude field | P2 (open) | Opportunistic Week 8+ |
| W6 SKIP-02b-v3-LEGACY | 2 legacy mio.core / mio.reporting skips | P2 (open) | Week 8+ MANU-CH12-NEW rewrite or retire the two figures |
| W6 FM2 PROBE-SIGMA | Radio / CF4++ / BiPoSH σ_cone placeholders | P2 (open) | Opportunistic during Week 8 MANU-CH12-NEW §12.2 with literature citations |
| W6 FM4 MC-VECTORISE | `_sample_isotropic_unit_vectors` per-mock loop | P3 (open) | Only if HJ-02a moves to 1e6-mock regime |
| W6 FM5 PROBE-NAME-SCHEMA | ad-hoc probe_name string-join | P3 (open) | Deferred — requires CONTRACTS-01 hash-freeze coordination |
| W6 FM6 GIT-SHA-DRIFT | git_commit resolves at instantiation | P3 (open) | Expected behaviour; no action |
| W7 FM1 | tsc-only test count 598 not 615 | P2 (open) | Update next-session prompt on rotation |
| W7 FM2 | TSC-06 RNG stream-alignment coupling | P2 (open) | Week 8+ when bass/htt lane is quiet |
| W7 FM3 | TSC-05 JSON schema freeze is literal-based, not hash-based | P3 (open) | Add hash test on first schema extension |
| W7 FM5 | tsc/integration/ new surface not explicitly in pyproject | P3 (open) | Default glob covers it; note only |

## 12. Test surface delta summary

| Surface | Before W7 | After W7 | Δ |
|---|---|---|---|
| `bass_py/htt/tests/` | 201 / 8 | 201 / 8 | 0 |
| `bass_py/src/common/tests/` (via src/) | 143 | 143 | 0 |
| `bass_py/tsc/admissibility/` | 156 | 207 | +51 |
| `bass_py/tsc/diagnostics/` | 176 | 176 | 0 |
| `bass_py/tsc/charts/` | 150 | 183 | +33 |
| `bass_py/tsc/integration/` (new) | — | 32 | +32 |
| `bass_py/workspace/contracts/tests/` | 32 | 32 | 0 |
| `bass_py/mio/tests/` | 40 | 40 | 0 |
| **Touched surface total** | **878 / 0 / 8** | **994 / 0 / 8** | **+116 passed, 0 failed, 0 new skips** |

## 13. Lane hygiene

No modifications to `bass_py/bass/*`, `plots/physics_gallery/`, or
any bass-owned path this phase. All new files land under:

- `bass_py/tsc/admissibility/` (TSC-03 module + tests)
- `bass_py/tsc/charts/` (TSC-05 module + tests)
- `bass_py/tsc/integration/` (TSC-06 subpackage; new directory)
- `docs/dossier/` (A34 + A35 + A38 + A40)
- `docs/audits/` (this audit log)

No `plots/physics_gallery/` activity required — this lane does not
own it, and none of the W7 artefacts produce imagery
(`feedback_phase_boundary_gallery.md` is honoured by documenting the
no-op explicitly here).
