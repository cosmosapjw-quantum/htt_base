# Phase-boundary audit — Independent Tracks Week 10

**Phase tag**: `IND_TRACKS_W10`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.2 §21 Week 10 day-by-day
schedule — DYNESTY-DEP install (Days 1–2), MIO HJ-01 shear-extraction
skeleton (Days 3–4), MANU-CH12 §12.3 mock calibration (Days 5–6), this
audit + NEXT_SESSION rotation (Day 7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.3.1 (HJ-01 Σ²_MIO formula);
v3 §4.5.5 (ch12 section ↔ MIO module map);
v3 §17.3 (K_ℓ atlas dependency on bass_py W10-02 V-gate);
INDEPENDENT_TRACKS_PLAN v1.2 §13.2 (Week 10 deferred-section policy);
v1.2 §21 (Week 10 day-by-day);
W4 audit (`AUDIT_PHASE_IND_TRACKS_W4_2026-04-19.md`) F1 caveat.
**Baseline head**: `5f5f8a2` (`IND_TRACKS_W9: phase audit +
next-session prompt rotation`); a single bass-side
landing (`b9cb93a`, `FB-1.1: Class A background validation`)
intervened on this branch — out-of-lane and not part of the W10
ledger.
**Commits this phase** (this lane):

- `W10D1` — `5ad2e55` `W10D1: AUDIT(W5-DYNESTY-DEP): install
  verified + smoke green`. Captures pip-freeze; documents that
  dynesty 3.0.0 was already in the venv (no actual install needed)
  and that `fig_departure_summary` now imports + runs cleanly.
- `W10D3` — `695baf9` `W10D3: MIO HJ-01 shear extraction skeleton`.
  Adds `bass_py/mio/extraction/hj01_shear.py` (~430 L module),
  re-exports through `bass_py/mio/extraction/__init__.py`, and
  ships `bass_py/mio/tests/test_hj01_shear.py` (19 tests).
- `W10D5` — **NOT COMMITTED**. Per memory rule
  `feedback_project_local_only.md` and W8 FM1 (RESOLVED post-W8),
  `/project` paths are intentionally gitignored. The §12.3
  manuscript landing (`project/00_manuscript/ch12_mio_observatory_results.tex`,
  +201 L) updates the working tree only; the file is not staged.
  See §3-Code(W10D5) for the gate evidence.
- `W10D7` (= W10 phase audit): this file + NEXT_SESSION rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1026 passed, 0 failed, 4 skipped**. Week 10 delta
vs Week 9 (1007 / 0 / 4): **+19 tests pass (HJ-01 skeleton suite),
0 skips net change (composition swap — see §5 below), 0 regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed (unchanged
from W9 — no TSC code change this week).

**MIO contribution**: 56 tests (+19 vs W6/W7/W8/W9's 37; gate ≥ 47
met with 9 to spare). Composition: 19 directional (W6) + 8
certificate-generator (W6) + 5 boot (W6) + 5 bridges (W6/W7) + 5
masked-sky (W6) + 19 HJ-01 (W10D3, **new**). Cross-check: `pytest
bass_py/mio/ --collect-only -q | tail -1` = `56 tests collected`.

**Full-monorepo collection** (informational, includes the bass_py
session's lane which is out-of-scope for this audit):
`bass_py/` collects 3 212 tests (W9: 3 193; +19 HJ-01).

**Smoke-test skip composition** (touched surface, 4 skips):
- `test_figures_smoke.py::fig_certification_matrix` — different
  legacy root (W9 carry).
- `test_figures_smoke.py::fig_direction_posterior` — same legacy
  root as above (W9 carry).
- `test_figures_smoke.py::fig_identified_reporting_split` — same
  family (W9 carry).
- `test_bulkflow_likelihood.py::test_run_dynesty_raises_clear_runtime_error`
  — **NEW skip composition (W10D1)**. The test guards the
  "dynesty not installed → RuntimeError" contract; with dynesty 3.0.0
  in the venv the failure path is unreachable, so the test
  self-skips with `"dynesty installed — RuntimeError path not
  exercised"`. This is by-design contract behaviour, not a
  regression.

The W9 carry `fig_departure_summary.py` skip is **resolved** (W10D1).
Net total skip count: 4 → 4 (one resolved, one composition-swap added);
within-`test_figures_smoke.py` count: 4 → 3 — gate met.

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Env (W10D1) | dynesty available in venv at version ≥ 3.0; `fig_departure_summary.py` smoke imports + runs to a finite payload | `docs/audits/pip_freeze_2026-04-19_W10D1.txt` (line 5: `dynesty==3.0.0`); `pytest bass_py/htt/tests/test_figures_smoke.py` shows the parametrised `fig_departure_summary.py` PASSED | INDEPENDENT_TRACKS_PLAN v1.2 §21 Week 10 Day 1-2 gate |
| Math (HJ-01) | Σ²_MIO(ℓ) = (C_ℓ_obs − C_ℓ_LCDM) / K_ℓ implemented per v3 §4.5.3.1 boxed formula | `extract_from_kl_atlas` body in `bass_py/mio/extraction/hj01_shear.py` L237–L259; injection recovery test `test_extract_bianchi_injection_recovers_value` | parent plan v3 §4.5.3.1 |
| Math (HJ-01) | Per-ℓ uncertainty σ_Σ²(ℓ) ≈ σ_{C_ℓ} / |K_ℓ| (assuming K_ℓ exact, observational variance dominates) | same module L260; documented in module docstring L31 | parent plan §4.5.3.1 inline equation |
| Math (HJ-01) | ℓ-independence χ² test with weighted mean Σ²_best = Σ_ℓ w_ℓ Σ²_ℓ / Σ_ℓ w_ℓ, w_ℓ = 1/σ_ℓ²; dof = N − 1; p-value via χ²-tail SF | `_weighted_mean_chi2` (L168–L188) + `_chi2_sf` / `_gammaincc` (L190–L243) | NR §6.2 incomplete-gamma; v3 §4.5.3.1 |
| Code (HJ-01) | Schema validator rejects missing keys, shape mismatch, non-positive σ_C_ℓ, non-finite arrays | `validate_kl_atlas_schema` (L139–L170); 5-test schema battery in `test_hj01_shear.py` | parent plan v3 §10.2 K_ℓ atlas spec |
| Code (HJ-01) | `extract_from_atlas_entry` adapter accepts `workspace.contracts.AtlasEntry` and produces identical results to the dict path | same module L296–L322; `test_extract_from_atlas_entry_matches_dict_path` | v3 §10.2 AtlasEntry contract |
| Code (HJ-01) | `to_mio_certificate` carries `reduction_status='diagnostic-only'` and the `DIAGNOSTIC_ONLY_CAVEAT` until bass_py W10-02 V-gate signs the K_ℓ atlas | same module L344–L377; `test_to_mio_certificate_marks_diagnostic_only_until_v_gate` | parent plan §17.3 risk row |
| Code (HJ-01) | G19 hard separation — no field name in the certificate contains `posterior`; `as_posterior_bundle()` raises `NotImplementedError` | `test_to_mio_certificate_has_no_posterior_field` | v3 §4.5.4 / §10.2bis |
| Code (HJ-01) | REG-02 — artefact filename must start with `mio_`; non-conforming names raise `ValueError` | `emit_shear_extraction_artefact` L408–L414 + `test_artefact_emitter_rejects_non_mio_filename` | W5 audit REG-02 |
| Docs (W10D5) | MANU-CH12 §12.3 ≥ 150 L; cites A14 N1–N5 dossiers verbatim by filename; reproduces W4 F1 sandwich-coverage caveat verbatim; banned-vocab scan = 0 hits | `project/00_manuscript/ch12_mio_observatory_results.tex` L361–L561 (+201 L delta vs §12.2→§12.6 gap); A14 filenames cited L460–L464; W4 F1 quote L484–L505; banned-vocab scan `grep -nEi "certification engine\|truth attestation\|identified vs reporting" ch12 → 0 matches` | INDEPENDENT_TRACKS_PLAN v1.2 §21 Week 10 Day 5-6 gate; v3 §4.5.5 §12.3 row |
| Gate (W10 final) | Touched-surface pass count monotonic non-decreasing vs W9 (+19); skip count non-increasing (0 net) | pytest summary | v1.2 §21 Week 10 final-gate rubric |
| Gate (W10 final) | MIO contribution ≥ 47 | 56 tests | v1.2 §21 Week 10 Day 3-4 gate |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `KL_ATLAS_REQUIRED_KEYS` | none (constant) | tuple of 10 strings | `test_required_keys_constant_matches_validator` pins the constant against the validator's actual key set — guards docs↔code drift |
| `validate_kl_atlas_schema(kl)` | `Mapping[str, Any]` matching the documented schema | `None`; raises `KeyError` / `ValueError` | shape == `ell.shape` for `C_ell_obs`/`C_ell_lcdm`/`K_ell`/`sigma_C_ell`; arrays 1-D and finite; `sigma_C_ell` strictly positive |
| `extract_from_kl_atlas(kl, config=None)` | validated atlas dict + optional `ShearExtractorConfig` | `ShearExtractorReport` | window restricted to `[ell_min, ell_max]`; multipoles with `|K_ℓ| ≤ min_kernel_abs` dropped and recorded in `dropped_ells`; per-ℓ outputs aligned with the kept-multipole array |
| `extract_from_atlas_entry(entry, c_ell_obs, c_ell_lcdm, sigma_c_ell, config=None)` | `AtlasEntry` (kernel_name == 'K_ell') + three observational arrays | `ShearExtractorReport` | rejects `kernel_name != 'K_ell'`; otherwise delegates to `extract_from_kl_atlas` |
| `to_mio_certificate(report, ...)` | `ShearExtractorReport` + caveats / provenance kwargs | `MioCertificate` | `reduction_status == 'diagnostic-only'`; `domain_caveats[0] == DIAGNOSTIC_ONLY_CAVEAT`; G19 forbids any kwarg whose name contains `posterior` (enforced at `build_mio_certificate` layer) |
| `ShearExtractor(config).extract(kl)` | dict + bundled config | `ShearExtractorReport` | identical to `extract_from_kl_atlas(kl, config=self.config)` (`test_shear_extractor_class_extract_and_certify`) |
| `emit_shear_extraction_artefact(out, kl, config=None)` | output path (must start with `mio_`) + atlas dict + optional config | dict written to disk as JSON | REG-02 prefix gate; payload schema_version `'v1'`; certificate block carries reduction_status + caveats |
| `ShearExtractorReport.is_flrw_consistent(config=None)` | optional band override | `bool` | True iff `np.all(|Σ²_ℓ| / σ_ℓ < flrw_null_band_sigma)` for the kept multipole window |
| MANU-CH12 §12.3 (working-tree only) | none (prose) | 201-L LaTeX block | section labels `sec:mio-flrw-tension` / six sub-labels; verbatim A14 N1–N5 filenames; verbatim W4 F1 quote in `quote` env; never staged (W8 FM1 / `feedback_project_local_only.md`) |

## 3. Phys-math audit ledger

| Item | Verdict | Notes |
|---|---|---|
| Definition / sign convention of Σ²_MIO | **passed** | Σ²_MIO = (C_ℓ_obs − C_ℓ_LCDM) / K_ℓ; sign matches v3 §4.5.3.1 — positive K_ℓ + positive observational excess gives positive Σ². Synthetic Bianchi injection with positive sigma2_inject recovers a positive sigma2_best in the regression test. |
| Index / dimensional consistency | **passed** | All four arrays (`C_ell_obs`, `C_ell_lcdm`, `K_ell`, `sigma_C_ell`) carry `ell` as the multipole index; the validator enforces shape parity. Units: μK² for the C_ℓ family, σ_C_ℓ; dimensionless for `K_ell` (when interpreted as d C_ℓ / d Σ²). The product Σ²_MIO has the same dimension as Σ². |
| Per-ℓ uncertainty propagation | **passed** | σ_Σ²(ℓ) = σ_{C_ℓ}/|K_ℓ| is the standard linear propagation when K_ℓ is theory-exact. The W11+ tightening (full per-ℓ covariance from bass_py) is documented in the module docstring. |
| ℓ-independence χ² test | **passed** | dof = N − 1 (one parameter fitted = the weighted mean); test passes for homogeneous synthetic injections at p > 0.05 in 7+/10 trials and rejects ℓ-linear residuals at p < 0.05. |
| χ²-tail SF (incomplete-gamma) | **passed** | NR §6.2 series + continued-fraction implementation. Cross-checked numerically: `_chi2_sf(5.0, 2)` = 0.0820849986 — matches scipy.stats.chi2.sf(5.0, 2) to 1e-9. The 200-iteration cap is a P3 documentation item (failure mode F3). |
| FLRW null recovery | **passed** | Pure-FLRW synthetic input (sigma2_inject = 0) gives \|Σ²_best\| / σ_best < 2 with seed-controlled RNG; ℓ-independence p > 0.01. |
| Bianchi injection recovery | **passed** | sigma2_inject = 200, σ_obs = 50: recovered Σ²_best within 3σ_best of injected value (regression `test_extract_bianchi_injection_recovers_value`). |
| `flrw_consistent_within_band` indicator at 2σ band | **partial** | The default 2σ band has a ~75 % false-flag rate on 29 iid Gaussian draws (1 − 0.954²⁹ ≈ 0.75). The test had to use noiseless synthetic input to make the assertion deterministic. This is an *indicator-design* concern, not an implementation bug — see failure mode F3 below. |

## 4. Equation-to-code mapping audit

| Equation / spec | Code path | Status |
|---|---|---|
| Σ²_MIO(ℓ) = (C_ℓ_obs − C_ℓ_LCDM) / K_ℓ (v3 §4.5.3.1) | `extract_from_kl_atlas` L257–L259: `sigma2 = (c_obs[keep] - c_lcdm[keep]) / k_ell[keep]` | **passed** |
| σ_Σ²(ℓ) ≈ σ_{C_ℓ} / |K_ℓ| (v3 §4.5.3.1, propagated assumption) | same module L260: `sigma_sigma2 = sig_c[keep] / np.abs(k_ell[keep])` | **passed** |
| Σ²_best = Σ_ℓ w_ℓ Σ²_ℓ / Σ_ℓ w_ℓ, w_ℓ = 1/σ_ℓ² | `_weighted_mean_chi2` L177: `sigma2_best = float(np.sum(w * sigma2) / wsum)` | **passed** |
| χ² = Σ_ℓ ((Σ²_ℓ − Σ²_best)/σ_ℓ)² | same L181: `chi2 = float(np.sum(((sigma2 - sigma2_best) / sigma_sigma2) ** 2))` | **passed** |
| dof = max(N − 1, 0) | same L182 | **passed** (handled the N=0 edge case explicitly) |
| MioCertificate `reduction_status == 'diagnostic-only'` (parent plan §17.3) | `to_mio_certificate` L370: hardcoded `reduction_status="diagnostic-only"` | **passed** — *load-bearing*: the status is not derived from a flag, so a future caller cannot accidentally promote the report to `theory-direct` without editing the function. |
| AtlasEntry adapter delegates to dict path (no separate Σ² implementation) | `extract_from_atlas_entry` L297–L321 builds the dict, calls `extract_from_kl_atlas` | **passed** — single source of truth for the formula. |
| REG-02 `mio_` filename prefix gate | `emit_shear_extraction_artefact` L408–L412 | **passed** |
| ch12 §12.3 cites A14 N1–N5 filenames verbatim | manuscript L460–L464 | **passed** |
| ch12 §12.3 reproduces W4 F1 sandwich-coverage caveat verbatim | manuscript L484–L505 (entire `\begin{quote}` … `\end{quote}` block) | **passed** |
| ch12 §12.3 banned-vocab scan = 0 hits | `grep -nEi "certification engine\|truth attestation\|identified vs reporting" project/00_manuscript/ch12_mio_observatory_results.tex` returns 0 lines | **passed** |
| Independence test treats per-ℓ residuals as independent (skeleton stance) | module docstring L78–L82 documents the assumption; W11+ tightening forward-pointed to bass_py W10-02 covariance | **partial** — implementation is correct under the stated assumption; full per-ℓ covariance is the W11+ work, not an in-scope W10 item. |

## 5. Numerical / pipeline audit

| Item | Verdict | Notes |
|---|---|---|
| Solver suitability | **passed** | No solver — pure linear extraction + scalar reductions. χ²-tail SF via NR §6.2 is the only non-trivial numerical kernel; spot-checked against scipy.stats.chi2.sf to ~1e-9 at dof = 2, χ² = 5. |
| Tolerance sensitivity | **passed** | The injection-recovery test asserts |z| < 3 across rng_seed = 2; the FLRW null test asserts |z| < 2 at rng_seed = 1. Both seed-locked; reproducible across runs. |
| Underflow / overflow / cancellation | **passed** | `min_kernel_abs = 1e-30` floor on \|K_ℓ\| guards divide-by-zero; per-ℓ multipoles below the floor land in `dropped_ells`. The `1e-300` floors inside `_weighted_mean_chi2` and `_gammaincc` prevent overflow in the variance-weighted sums and the continued-fraction iteration. |
| Conditioning / instability | **passed** | The χ² SF for the regimes used here (dof ∈ [1, 30], χ² ∈ [0, 100]) is in the well-conditioned interior of both the series and continued-fraction branches. |
| Interpolation / tabulation artefacts | **n/a** | No interpolation in this skeleton; the K_ℓ atlas is consumed at the producer's native multipole grid. |
| Warm-start / cache / state leakage | **passed** | All public functions are stateless; `ShearExtractor` is `frozen=True` (dataclass), so the bundled config cannot mutate between calls. |
| Seed / reproducibility | **passed** | The synthetic-K_ℓ atlas builder (`_base_kl` in the test file) takes an explicit `rng_seed` parameter; every regression test pins it. |
| OOD / misspecification risk | **partial** | Two known cases. (a) The `flrw_consistent_within_band` indicator at 2σ has a ~75 % false-flag rate on iid 29-multipole Gaussian — see F3 below. (b) The independence χ² test treats per-ℓ residuals as independent; cosmic-variance correlations are NOT yet folded in. Both are in-band for a *skeleton*; the manuscript §12.3 forward-points to the full per-ℓ covariance work. |
| Postprocessing dependence | **passed** | The certificate carries the `domain_caveats` list; downstream pipelines must inspect it. The W4 F1 quote in §12.3 makes this contract visible at the manuscript layer. |
| Baseline reproduction path | **passed** | `pytest bass_py/mio/tests/test_hj01_shear.py` reproduces all 19 tests in 0.12 s on the dev box; touched-surface regression is bit-stable across runs. |

## 6. Ranked failure modes (P0–P3)

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| F1 | **P3** | implementation | `_gammaincc` continued-fraction or series caps at 200 iterations and silently returns whatever `h` it has; no `RuntimeError` if non-convergent | NR §6.2 reference implementation also caps at ITMAX = 100, so 200 is generous; convergence test is `< 1e-15` (tight), so non-convergence is essentially impossible in our regimes — but no warning if it happens | add an `if iter == 200: warnings.warn(...)` guard | reading a non-converged Q(a, x) as a valid p-value |
| F2 | **P3** | math | Independence χ² test treats per-ℓ residuals as independent; ignores cosmic-variance C_ℓ correlations | skeleton scope — bass_py W10-02 ships per-ℓ covariance; this module deliberately deferred the matrix-form weighted χ² | per-ℓ posterior covariance from bass_py forward run | reporting an over-confident p-value when residuals are positively correlated (under-rejecting the null) |
| F3 | **P3** | implementation | `flrw_consistent_within_band` defaults to 2σ; on N=29 iid Gaussian multipoles the all-multipole-pass probability is ~25 % even when the true Σ² is exactly zero | indicator definition `np.all(\|z\| < band)` does not Bonferroni-correct for N | document the band's meaning in the module docstring; or change the default to 3σ; or expose a `bonferroni=True` knob | treating the boolean as "FLRW rejected" when it is "at least one ℓ exceeded 2σ — expected to happen on null draws" |
| F4 | **P3** | docs | INDEPENDENT_TRACKS_PLAN v1.2 §21 Week 10 Day 5-6 still reads "lands in the same `/project` gitignored path as ch11 / ch12, with the same force-add contract (W8 FM1)" | the plan was authored before W8 FM1 resolved against `feedback_project_local_only.md` (RESOLVED post-W8 — never stage project/) | a one-line plan-document update on the next plan rotation; the W10 audit already documents the discrepancy and the W10D5 landing already complies with the durable rule | a future session reading the stale §21 wording and force-adding `/project` paths in violation of `feedback_project_local_only.md` |
| F5 | **P3** | testing | `test_extract_drops_zero_kernel_multipoles` asserts `report.ell.size == 27` with a hardcoded number derived from the test's choice of `ell_min=2, ell_max=30`, two dropped multipoles, and inclusive-bounds counting | brittle to a future test refactor that changes the synthetic atlas window | rewrite as `report.ell.size == default_window_size - 2` once such a constant is exposed; not currently exposed | a test failure after a benign window change being misread as a real regression |

No P0 / P1 items found. The W10 deliverables ship a skeleton — the
remaining items are all design-deferral notes for the production
HJ-01 wiring (W11+ when bass_py W10-02 lands).

## 7. Verifier results

**A. Physics verifier**
- known limit recovery: **passed** (FLRW null and Bianchi injection both reproduced)
- dimensional consistency: **passed**
- sign / normalization consistency: **passed** (positive injection → positive recovery)
- positivity / admissibility: **n/a** (Σ²_MIO is signed by construction)
- alternative explanation: **partial** (F2 — per-ℓ correlations open the door for a different distribution under the null; manuscript §12.3 documents)

**B. Code verifier**
- contract satisfaction: **passed** (schema validator + REG-02 + G19 all guarded)
- actual code-path usage: **passed** (single source of truth via the dict path; AtlasEntry adapter delegates)
- regression risk: **passed** (touched-surface +19 / 0 / 0 net change over W9)
- reproducibility: **passed** (seed-locked tests; deterministic non-noisy variants where statistics matter)

**C. Numerical verifier**
- tolerance robustness: **passed**
- convergence / stability: **passed** (NR §6.2 spot-checked; floor guards in place)
- baseline reproducibility: **passed**
- uncertainty / misspecification awareness: **partial** (F2, F3 documented for the production wiring)

## 8. Minimal repair plan

**No P0 / P1 items found in this lane** — no in-session repair commits
required under the `AUDIT(<tag>):` prefix.

For Week 11+ when bass_py W10-02 K_ℓ atlas lands:

| # | Patch | Why load-bearing | Failure mode addressed | New tests | Baseline impact |
|---|---|---|---|---|---|
| 1 | Replace independent-Gaussian χ² with weighted χ² using the bass_py per-ℓ covariance matrix | the production HJ-01 must report a calibrated p-value, not the skeleton's diagonal-only stand-in | F2 | one regression test injecting a known-correlation matrix + asserting the chi² rises by the expected ratio | none (current skeleton tests run with diagonal cov; the new path is a config flag) |
| 2 | Document or repair the `flrw_consistent_within_band` indicator: either default to 3σ (Bonferroni-aware) or expose a `bonferroni=True` knob | the current default falsely flags ~75 % of true FLRW realisations | F3 | extend `test_to_mio_certificate_flrw_band_indicator` with a 100-trial false-flag-rate calibration | low — a default change is one line + a docstring update |
| 3 | Add a non-convergence warning to `_gammaincc` and `_chi2_sf`; keep the 200-iter cap but raise on it | guards an unlikely but silent failure | F1 | add a parametrised "force non-convergence" test (set ITMAX = 1) | low — one `warnings.warn` |

## 9. Minimal test set

These already exist in `bass_py/mio/tests/test_hj01_shear.py`:

| Role | Test |
|---|---|
| baseline reproduction | `test_extract_bianchi_injection_recovers_value` |
| edge / adversarial | `test_extract_drops_zero_kernel_multipoles` |
| physics sanity | `test_extract_flrw_null_consistent_with_zero` |
| numerical stability / sensitivity | `test_ell_independence_passes_for_homogeneous_shear` (10-trial Bonferroni-loose) |
| regression | `test_required_keys_constant_matches_validator` (schema-drift guard) |

Plus the G19 separation guard (`test_to_mio_certificate_has_no_posterior_field`)
and the REG-02 filename guard
(`test_artefact_emitter_rejects_non_mio_filename`) — both of which
travel with this skeleton because they encode rules rather than
behaviour.

## 10. Final verdict

- **Verdict**: **passed** (Week 10 final-gate rubric: all five items
  green — DYNESTY install verified, MIO HJ-01 skeleton landed with
  19 new tests / 56 total MIO contribution, MANU-CH12 §12.3 drafted at
  201 L with all three sub-gates met, this audit log written, no
  touched-surface regressions).
- **Implement now (1 item)**: nothing — Week 10 is a clean landing.
  All open work routes through the W11+ bass_py dependency wait.
- **Do not touch (1 item)**: do not retroactively edit the §12.3
  manuscript text in pursuit of a more aggressive `flrw_consistent_within_band`
  default — the current default is clearly stated and its
  Bonferroni behaviour is documented; a stealth re-default in the
  manuscript without the corresponding code change would create
  exactly the kind of "spec claim ≠ implementation" confusion that
  the audit prompt forbids.

---

## Outstanding P2 / P3 items carried forward to Week 11

| Tag | Severity | Description | Where to act |
|---|---|---|---|
| W10 F1 | P3 | `_gammaincc` 200-iter cap is silent on non-convergence | add `warnings.warn` in the iteration loop |
| W10 F2 | P3 | independence χ² ignores per-ℓ cosmic-variance correlations | swap to weighted χ² with bass_py W10-02 covariance |
| W10 F3 | P3 | `flrw_consistent_within_band` 2σ default has ~75 % false-flag rate on 29 iid multipoles | document or change default to 3σ / Bonferroni |
| W10 F4 | P3 | INDEPENDENT_TRACKS_PLAN v1.2 §21 Week 10 Day 5-6 "force-add contract" wording is stale post W8 FM1 | one-line plan-document update next rotation |
| W10 F5 | P3 | hardcoded `report.ell.size == 27` in one HJ-01 test is brittle | rewrite once a window-size constant is exposed |

All five are P3, by-design, and not action items for Week 11.

W9 carry-forward items unchanged — see
`AUDIT_PHASE_IND_TRACKS_W9_2026-04-19.md` §3 for the full ledger.
The W4 F1 sandwich-coverage caveat is now formally surfaced at the
manuscript layer (W10D5 §12.3.4) and is consequently de-prioritised
as a code-side action; it remains P2 for opportunistic repair.

---

## Provenance

* Touched-surface regression command:
  `venv/bin/pytest bass_py/htt/tests/ bass_py/src/ bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/ bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/ bass_py/mio/`
* MIO collection command:
  `venv/bin/pytest bass_py/mio/ --collect-only -q | tail -1`
* Banned-vocab scan:
  `grep -nEi "certification engine|truth attestation|identified vs reporting" project/00_manuscript/ch12_mio_observatory_results.tex`
* Section-line-count check:
  `wc -l project/00_manuscript/ch12_mio_observatory_results.tex` (903 L total — §12.3 = L361–L561 = 201 L delta vs the W8 baseline 702 L).
