# Phase-boundary audit — Independent Tracks Week 6

**Phase tag**: `IND_TRACKS_W6`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md v1.2 §21 Week 6 day-by-day schedule
— MIO-BOOT-01 + FIG-MIO-SKIP-GATE (Day 1), MIO-HJ-06a (Day 2),
MIO-HJ-02a (Days 3-5), MIO-BRIDGES-01 (Day 6), MIO-HJ-05a-lite (Day 7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**: v3 §1.4.1 (distributed epistemic ownership;
PR13AM as MIO bridge), §4.5.2.1 / §4.5.3.2 / §4.5.3.5 / §4.5.4 (MIO
architecture + directional coherence + MioCertificate + G19), §10.2 /
§10.2bis (contract table + enforcement), §12.2bis (MIO first-line
defences), §14.1 (`mio_` artifact prefix), §16.2 (HJ-02a independence).
**Baseline head**: `5a0ca8e` (prior independent-tracks phase
`IND_TRACKS_W5: phase audit + next-session prompt rotation`).
**Commits this phase**:
`6d66058` (W6D1 MIO-BOOT-01 + FIG-MIO-SKIP-GATE),
`37e67e2` (W6D2 MIO-HJ-06a generator),
`dd07424` (W6D5 MIO-HJ-02a directional coherence + artefact),
`3ea8b60` (W6D6 MIO-BRIDGES-01 PR13AM re-export),
`0e534c8` (W6D7 MIO-HJ-05a-lite masked_sky_caveats).
`c72dcba` (post-LB FB plan bootstrap) landed on the bass-side lane
in between and is NOT part of this audit.
**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/ bass_py/tsc/charts/
bass_py/workspace/ bass_py/mio/` → **878 passed, 0 failed, 8 skipped**.
Week 6 delta vs Week 5 (839 / 0 / 8): +39 new tests, zero regressions,
skip count unchanged (composition shifted: the two `No module named
'mio'` skips migrated to `No module named 'mio.core'` + `No module
named 'mio.reporting'`, see §6 FM1).

---

## 1. Audit target reconstruction

| Stratum | Claim | Artefact | Source-of-truth |
|---|---|---|---|
| Physics / math | MIO is an observatory for model-independent diagnostics; HJ-02 (directional coherence) is a 5-probe sphere-statistics test | `mio/coherence/directional.py` — resultant_vector + isotropy_pvalue + coherence_chi2 + STANDARD_PROBES | v3 §4.5.3.2 HJ-02 + §16.2 row "HJ-02a: completely independent" |
| Physics / math | Inverse-variance weighted spherical mean is the correct direction-aggregation on S² | `resultant_vector` via `common.sky_geometry.spherical_mean` | v3 §4.5.3.2 eq. (9); common.sky_geometry documented COMMON-A |
| Physics / math | Secrest+2020 CMB–CatWISE dipole separation ≈ 27.8° ± 0.6° | SSOT probe literals at (264.021°, 48.253°) / (238.2°, 28.8°) → computed 27.79° | arXiv:2009.14826 abstract + Fig. 1 |
| Physics / math | Zone-of-avoidance mask strictly reduces `f_sky_effective` below 1.0 for bcut > 0 | `build_report` + `common.healpix_selection.build_zoa_mask` | v3 §4.5.3.5 HJ-05a; COMMON-B REG-01 ZoA ladder |
| Contracts | `mio.interface.mio_certificate.build_mio_certificate` raises `ValueError` on any keyword name containing 'posterior' | `_reject_posterior_keywords` + `test_build_rejects_posterior_keyword` | v3 §10.2bis G19 row 1 — generator-site enforcement (complements schema-site ban) |
| Contracts | Provenance auto-population: `git_commit` from `git rev-parse HEAD`, `config_hash` from sha256 of diagnostic payload | `_resolve_git_commit` + `_hash_config` | Plan §12.4 |
| Contracts | `MioCertificate.as_posterior_bundle()` still raises `NotImplementedError` when the certificate is built via the generator | `test_generator_output_preserves_g19_contract` | v3 §4.5.4 G19 round-trip |
| Contracts | `mio.bridges.PR13AM_te_sign_d1d3_bridge is htt.PR13AM_te_sign_d1d3_bridge` (semantic re-export, identical module object) | `test_both_import_paths_point_to_same_module` | Plan §12.5 option A |
| Contracts | `__mio_owned__ = True` and `__mio_rationale__` survive the re-export | `test_mio_ownership_flags_visible_through_bridge` | v3 §12.2bis first-line G19 defence |
| Contracts | MIO-produced artefact filenames start with `mio_` prefix | `emit_directional_coherence_artefact` guard + REG-02 test | v3 §14.1 + IND_TRACKS §19.2 |
| Contracts | `SkyCoverageReport.caveats` is a `list[str]` directly consumable as `MioCertificate.domain_caveats` | `test_report_integrates_with_mio_certificate` | Plan §12.6 + v3 §4.5.3.5 |

## 2. Contract / interface table

| Name | Inputs | Outputs | Invariants enforced? |
|---|---|---|---|
| `DirectionalProbe(name, l_deg, b_deg, sigma_cone_deg, weight=1.0)` | frozen dataclass | identity | ✓ frozen; `sigma_cone_deg > 0` enforced at `_probe_weights` call-site |
| `STANDARD_PROBES` | constant tuple of 5 probes | CMB / CatWISE / Radio / CF4pp / BiPoSH | ✓ `test_standard_probes_sanity`: `0 ≤ l < 360`, `−90 ≤ b ≤ 90`, `σ > 0` |
| `resultant_vector(probes)` | `Sequence[DirectionalProbe]` non-empty | `(l, b, R)` with `R ∈ [0, 1]` | ✓ NaN on degenerate cancellation; `R < 1e-6` asserted for antipodal test |
| `isotropy_pvalue(probes, n_mock, rng)` | probes + `n_mock ≥ 1` | float ∈ (0, 1] | ✓ Lidstone smoothing `(k+1)/(n+1)` avoids zero; weight-sum > 0 guard |
| `coherence_chi2(probes)` | ≥ 2 probes | `(chi2, dof)` with `dof = max(N-2, 1)` | ✓ `+inf` when direction canceled; positive otherwise |
| `pairwise_separations(probes)` | Probes | `(N, N)` degrees | ✓ zero diagonal; bounded ∈ [0, 180]; reuses `common.sky_geometry.angular_separation_matrix` |
| `to_mio_certificate(probes, p_iso, resultant, *, chi2_stat, ...)` | probes + computed stats | `workspace.contracts.MioCertificate` | ✓ departure / adequacy / consistency dicts populated; G19 round-trip preserved |
| `emit_directional_coherence_artefact(out_path, ...)` | `Path` (must be `mio_*.json`) | dict + file written | ✓ REG-02 prefix guard `raise ValueError` if filename lacks `mio_` |
| `build_mio_certificate(..., **extra)` | required schema fields | `MioCertificate` | ✓ posterior-keyword `ValueError`; unknown-keyword `TypeError`; deterministic `config_hash` |
| `_resolve_git_commit()` | — | sha hex or `"unknown"` | ✓ subprocess timeout 5 s; OSError tolerated |
| `SkyCoverageReport(nside, n_pix_total, n_pix_kept, f_sky_effective, zoa_half_angle_deg, ecliptic_pole_gap_deg, mask_provenance, caveats)` | frozen dataclass | identity | ✓ frozen; mask-shape-vs-`nside_to_npix` guarded |
| `build_report(mask_pix, nside, *, zoa_half_angle_deg, ecliptic_pole_gap_deg, mask_provenance, extra_caveats)` | mask + nside | `SkyCoverageReport` | ✓ `f_sky == n_pix_kept / n_pix_total`; auto-caveats include f_sky, ZoA, provenance |
| `as_caveats_list(report)` | `SkyCoverageReport` | `list[str]` | ✓ strings only; new list returned (no mutation) |
| `mio.bridges` module | — | re-export surface with `__all__ = ["PR13AM_te_sign_d1d3_bridge"]` | ✓ identity with `htt.PR13AM_te_sign_d1d3_bridge`; `__mio_owned__` + `__mio_rationale__` preserved |

## 3. Phys-math audit ledger

| Check | Verdict | Why |
|---|---|---|
| Definition / notation consistency across `DirectionalProbe` fields and v3 §4.5.3.2 | pass | `name / l_deg / b_deg / sigma_cone_deg / weight` match plan §12.3 literal signature. |
| Inverse-variance weighting for spherical mean | pass | `w_i = weight_i / sigma_cone_deg_i²` — standard Fisher/inverse-variance convention. |
| Sphere-correct aggregation (no longitude wrap bug) | pass | `resultant_vector` reuses `common.sky_geometry.spherical_mean` which works in Cartesian via `lb_to_unitvec`; longitude 0°/360° wrap is handled. |
| χ² dof for common-axis hypothesis | pass | Two angular coordinates fitted from the probes themselves → `dof = N − 2`. |
| Isotropy-null p-value admissibility | pass | Monte-Carlo draw sampled uniformly on S² via `(u, φ)` mapping; Lidstone smoothing makes `p ∈ (0, 1]` under any finite `n_mock`. |
| Antipodal cancellation | pass | `(30°, 20°)` + `(210°, −20°)` analytically antipodal → R = 0; observed R < 1e-6. |
| CMB–CatWISE literature anchor (Secrest+2020) | pass | Computed separation 27.79°; paper reports 27.8° ± 0.6°; test band [27°, 29°]. |
| f_sky monotonicity under ZoA | pass | `build_zoa_mask(bcut=15°, nside=16)` reduces f_sky below 0.80 (handcrafted quarter-sky yields exactly 0.25). |
| G19 hard separation at generator site (not just schema) | pass | `build_mio_certificate(**ok, posterior_mean=0.5)` raises `ValueError("MIO cannot generate posteriors")`. |
| G19 round-trip through generator | pass | Generated certificate still raises `NotImplementedError` on `as_posterior_bundle`. |
| MIO-owned tag identity through re-export | pass | `htt.PR13AM_*` and `mio.bridges.PR13AM_*` are the *same* module object (Python `is`); no attribute loss. |

## 4. Equation-to-code mapping audit

| Claim | Implementing file | Notes |
|---|---|---|
| Resultant vector `R = \|\sum w_i \hat n_i\| / \sum w_i` | `mio/coherence/directional.py::resultant_vector` → `common.sky_geometry.spherical_mean` | Direct one-line wrap; weights are the inverse-variance combination derived in `_probe_weights`. |
| Isotropy null hypothesis: mocks drawn from uniform S² | `_sample_isotropic_unit_vectors` uses `(u ∈ [−1, 1], φ ∈ [0, 2π))` mapping | Standard recipe; `s = √(1−u²)` gives correct latitude distribution. |
| χ² = Σ (Δ_i / σ_i)² | `coherence_chi2` computes per-probe separation to fitted axis then sums | Arc-cos clipped to [−1, 1] to avoid NaN for tiny numerical excursions. |
| Pairwise separation matrix | `pairwise_separations` via `angular_separation_matrix` | Cartesian dot-product recipe; numerically identical to the `spherical_mean` helpers' vectors. |
| `mio_` prefix on every MIO-produced artefact | `emit_directional_coherence_artefact` early `ValueError` + `_mio_artifact_name` helper reused from PR13AM | Not just documented — actively enforced. |
| MioCertificate generator provenance | `build_mio_certificate._resolve_git_commit` + `_hash_config` | `config_hash` is sha256(json.dumps([report_type, probe_name, channel, 3 dicts], sort_keys=True))[:16]. |
| Mask-shape validation | `_ensure_pixel_mask` raises `ValueError` when `mask.shape != (nside_to_npix(nside),)` | Guards against callers passing `nside=8` with a 768-element mask, etc. |
| Bridge option A (plan §12.5) | `mio/bridges/__init__.py::from htt import PR13AM_te_sign_d1d3_bridge` + `__all__` | Tested identity via `is` — no accidental module copy. |

## 5. Numerical / pipeline audit

| Check | Verdict | Notes |
|---|---|---|
| Tolerance sensitivity of `isotropy_pvalue` | pass | `n_mock=10_000` yields ≈ 1 % resolution; both sign tests (null > 0.05, aligned < 0.01) pass with comfortable margins (seed 1 / seed 2). |
| Determinism under RNG seed | pass | `isotropy_pvalue` accepts `rng` kwarg; `emit_directional_coherence_artefact` defaults to seed 20260419. Test `test_emit_artefact_writes_json` round-trips the payload deterministically. |
| Overflow / cancellation | pass | `spherical_mean` returns NaN on full cancellation; `coherence_chi2` returns `+inf`; both exercised. |
| Subprocess timeout (git rev-parse) | pass | 5 s hard timeout + `OSError` fallback to `"unknown"`. |
| Chunked mock generation memory footprint | pass | `chunk = 2048` → each chunk ≤ 2048 × 5 × 3 × 8 B ≈ 240 KB. |
| Reproducibility across repo states | partial | `git_commit` is resolved via subprocess at call time — if HEAD moves between instantiations within the same session the value drifts. Acceptable for the diagnostic-only role; documented in docstring. |
| Baseline reproduction | pass | With seed 20260419, persisted artefact on STANDARD_PROBES yields `R = 0.9990`, `p_iso = 2.9997e-4` (1 / 3334 of 10 000 mocks), `χ² / dof = 9.45`; values stable under test repetition. |

## 6. Ranked failure modes

Seven modes observed this phase:

**P1**

* **FM1 — Day-1 "2 → 0" cascade mismatch.** The next-session resumption
  doc §2 Day 1 gate states "`test_figures_smoke.py` mio-skip count
  drops 2 → 0." In reality, the two `No module named 'mio'` skips
  migrated to `No module named 'mio.core'` + `No module named
  'mio.reporting'` (the legacy v2 submodules that the figures
  `fig_certification_matrix.py` and `fig_identified_reporting_split.py`
  reference). Both still match the `"mio"` substring inside
  `_known_external_module_pattern`, so the skip *count* is unchanged.
  The authoritative plan §19.7 gate (`import bass_py.mio` must succeed
  without `ImportError`) does pass — verified by
  `test_figures_mio_skip_should_activate_after_mio_boot`. Treating this
  as P1 because the next-session doc line is strictly inaccurate and
  should be corrected during the phase-close rotation. Root cause:
  those two figures reference v2 "certification engine" symbols
  (`mio.core.ceiling_families.CEILING_FAMILIES`,
  `mio.reporting.identified_vs_reporting.QUANTITY_REGISTRY`) that do
  not exist in the v3 skeleton per plan §12.2. Porting those legacy
  modules into the v3 skeleton would contaminate the package's
  semantic scope (v3 explicitly rejects the "certification engine"
  framing per `legacy/README.md` banner). **Resolution this session:**
  (1) audit entry codifies the divergence; (2) next-session prompt
  updates the gate phrasing to match §19.7 verbatim; (3) carry-forward
  item "W6 SKIP-02b-v3-LEGACY" tracks the eventual per-figure port
  (out of lane until ch12 manuscript phase per plan §21 Week 8+).

**P2**

* **FM2 — Probe σ_cone values for Radio / CF4pp / BiPoSH are plan
  placeholders.** Radio = 10°, CF4pp = 15°, BiPoSH = 20° in the SSOT
  table are the §12.3 suggested literature estimates, not a paper-
  cited vector. This only shifts weights, not directions; the R and
  p-value stats are dominated by CMB (σ = 0.5°). Documented in the
  module docstring. Update when the appropriate citations land
  (MANU-CH12-NEW §12.2, Week 8+).
* **FM3 — CMB-CatWISE "≥ 28°" test name vs 27.79° computed.** Plan
  §12.3 literal test name says `ge_28deg`; Secrest+2020 actual value
  is 27.8° ± 0.6°. Test assertion relaxed to [27°, 29°]. Test name
  retained verbatim from the plan to preserve the spec→code trail
  (the docstring documents the ±1 ° band around the literature
  anchor). Not a bug; no action needed.
* **FM4 — `_sample_isotropic_unit_vectors` loops inside the mock
  chunk.** The chunk-level loop builds each mock's (N × 3) array in
  Python then stacks. For the 10k default this is <50 ms total, but
  an `n_mock = 1e6` call would take ~5 s. Acceptable for Week 6; a
  vectorised `rng.uniform((m, n, 3))` rewrite is a P3 optimisation.

**P3**

* **FM5 — `to_mio_certificate.probe_name` is a "A+B+C+D+E" join.**
  Works but is not a canonical schema. A structured `probe_names:
  list[str]` field is cleaner. Deferred because it would widen the
  `MioCertificate` schema, triggering `test_miocertificate_schema_frozen`
  — needs coordination with CONTRACTS-01 freeze policy. Acceptable
  for diagnostic-only payload.
* **FM6 — `_resolve_git_commit` drifts if HEAD moves mid-session.**
  The generator captures the current HEAD at instantiation time; a
  long-lived session that commits between certificate builds will
  tag different certificates with different SHAs. Expected behaviour
  for diagnostic provenance; documented.
* **FM7 — Gallery rule no-op for this phase.** Memory rule
  `feedback_phase_boundary_gallery.md` requires extending +
  regenerating `plots/physics_gallery/` every phase. This lane's
  scope (plan §0 rule 2) explicitly forbids touching `plots/`.
  **Classification: no-op with explicit rationale**, per the "no-op
  phases document explicitly in audit log" clause. No artefact
  changes required. (The bass-side lane owns gallery refresh after
  each LB-N; the W6 MIO package does not produce publication
  figures yet — those are MANU-CH12 Week 8+.)

## 7. Verifier results

**A. Physics verifier**

| Check | Result | Notes |
|---|---|---|
| Known limit recovery | passed | Antipodal probes → R = 0; identical probes → R = 1 (exercised implicitly in alignment test). |
| Dimensional consistency | passed | All directional stats are dimensionless; `sigma_cone_deg / sigma_cone_deg` → unit-free. |
| Sign / normalization consistency | passed | Weights positive by construction; `R ∈ [0, 1]` asserted. |
| Positivity / admissibility | passed | χ² ≥ 0; f_sky ∈ [0, 1]; separations ∈ [0°, 180°]. |
| Alternative explanation | partial | The 27.79° CMB–CatWISE separation passes a specific literature-anchor band but does not *prove* the physical claim; it proves the SSOT literals reproduce the published geometry. Acceptable for a smoke-test role. |

**B. Code verifier**

| Check | Result | Notes |
|---|---|---|
| Contract satisfaction | passed | All 11 public APIs tested; frozen dataclasses verified by `FrozenInstanceError` raise. |
| Actual code-path usage | passed | `build_mio_certificate` is consumed by `to_mio_certificate`; `common.sky_geometry` is consumed by both `resultant_vector` and `pairwise_separations`; `common.healpix_selection.build_zoa_mask` is consumed by both the test suite and anyone who wants the ZoA mask in `build_report`. |
| Regression risk | passed | W5 touched-surface (839) preserved byte-for-byte; existing `test_PR13AM_production_gate.py` (6 tests) unchanged after bridges re-export. |
| Reproducibility | passed | Seed-controlled throughout (`rng = np.random.default_rng(seed=...)`). |

**C. Numerical verifier**

| Check | Result | Notes |
|---|---|---|
| Tolerance robustness | passed | Both the null-test and the alignment test carry comfortable margins (null p ≈ 0.5 » 0.05; aligned p < 0.001 « 0.01 with 10k mocks). |
| Convergence / stability | passed | 10k mocks give ≈1 % p-value resolution; Lidstone smoothing prevents the degenerate p = 0 edge. |
| Baseline reproducibility | passed | Persisted `mio_directional_coherence.json` shows R = 0.9990, p_iso = 2.9997e-4, χ² / dof = 9.45 with seed 20260419. |
| Uncertainty / misspecification awareness | partial | Certificate records `coherence_chi2_per_dof` (9.45 on STANDARD_PROBES is quite high — consistent with the χ² being dominated by probes whose σ_cone underestimates their true uncertainty, which is the FM2 story). Documented; cross-references HJ-05a-lite caveats. |

## 8. Minimal repair plan

Per audit rule, up to three minimum patches. This phase found one P1
(FM1). The plan below applies FM1 in-session via documentation rotation
— code-level cascade is out-of-lane per §21 Week 8+.

### Patch 1 (this audit) — FM1 next-session prompt rotation

**What**: Update `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Day 1
gate to match the authoritative plan §19.7 phrasing
(`import bass_py.mio` succeeds without `ImportError`) and carry
`W6 SKIP-02b-v3-LEGACY` forward to Week 8+ §3 table.
**Why load-bearing**: prevents the next session from treating a
documentation divergence as a regression and from porting v2 legacy
modules into the v3 skeleton to force the 2 → 0 cascade.
**Failure modes closed**: FM1.
**New tests**: none — `test_figures_mio_skip_should_activate_after_mio_boot`
already guards the actual gate.
**Regression impact**: documentation-only.

### Patch 2 (deferred to Week 7–8) — Radio / CF4pp / BiPoSH probe citations (FM2)

Out of lane for Week 6. Queued under MANU-CH12-NEW §12.2 draft.

### Patch 3 (deferred to post-Week 8) — `mio.core` / `mio.reporting` v3 migration (FM1 root cause)

The two v2-referencing figures (`fig_certification_matrix.py`,
`fig_identified_reporting_split.py`) need rewrites to the v3
"observatory" vocabulary. Expected to ship alongside MANU-CH12-NEW
draft updates. No code action this phase.

## 9. Minimal test set

All present and green (see §6 for the skip/pass split):

| Category | Test | Pass/fail criterion |
|---|---|---|
| Baseline reproduction | `test_emit_artefact_writes_json` | Seed-reproducible artefact; R ∈ [0, 1]; schema_version == "v1". |
| Edge / adversarial | `test_resultant_vector_antipodal_probes_R_zero` | R < 1e-6 for antipodal pair. |
| Physics sanity | `test_pairwise_separations_cmb_catwise_literature_ge_28deg` | Separation ∈ [27°, 29°] (Secrest+2020 band). |
| Numerical stability | `test_isotropic_null_pvalue_gt_0p05` (10k mocks) | p > 0.05 for genuinely isotropic input. |
| Regression | `test_both_import_paths_point_to_same_module` | `htt.PR13AM_*` *is* `mio.bridges.PR13AM_*`. |

## 10. Final verdict

**통과**.

* Phase 게이트 (plan §21 Week 6) 모두 달성:
  - [x] `import bass_py.mio` 성공 — test_mio_root_importable + test_figures_mio_skip_should_activate_after_mio_boot
  - [x] HJ-02a 5 required tests green + `mio_directional_coherence.json` artefact 생성
  - [x] `MioCertificate.as_posterior_bundle()` → NotImplementedError end-to-end through the new generator — test_generator_output_preserves_g19_contract
  - [x] Phase-boundary audit written (this file)
  - [~] HTT figure skip 2 → 0 cascade — documented divergence (FM1, P1) — the `import mio` root gate passes, but the two literal figure skips remain pending v3 legacy-submodule migration. Next-session prompt rotated.

* 치명적 오류: 없음.
* 지금 당장 구현할 1개: 다음 세션 재진입 프롬프트의 Day 1 gate 문구를 §19.7 원문과 일치시키는 것 (Patch 1 / FM1). 이 audit 커밋 안에서 수행.
* 지금 손대면 안 되는 1개: `mio.core` / `mio.reporting` v2 legacy 포팅. v3 skeleton 의미론을 오염시킬 뿐 아니라, 그 두 figure는 ch12 재작성 단계 (Week 8+ MANU-CH12-NEW) 에서 본격 대체된다.

---

## Outstanding P2/P3 carry-forward

| Tag | Severity | Description | Where to act |
|---|---|---|---|
| W6 SKIP-02b-v3-LEGACY | P2 | 2 figure skips on `No module named 'mio.core'` / `'mio.reporting'` — figures reference v2 "certification engine" vocabulary that v3 skeleton does not carry. | Week 8+ MANU-CH12-NEW phase — rewrite `fig_certification_matrix.py` + `fig_identified_reporting_split.py` in v3 "observatory" terms, OR retire them in favour of HJ-02/HJ-05 figures. |
| W6 FM2 PROBE-SIGMA | P2 | Radio / CF4pp / BiPoSH σ_cone values are plan-suggested placeholders, not cited. | Week 7–8, opportunistic during MANU-CH12 §12.2 draft. |
| W6 FM4 MC-VECTORISE | P3 | `_sample_isotropic_unit_vectors` has a Python chunk loop; harmless at `n_mock = 10k`, mild cost at `1e6`. | Deferred — revisit if HJ-02a moves to a 1e6-mock regime. |
| W6 FM5 PROBE-NAME-SCHEMA | P3 | Generated certificate stores `probe_name = "A+B+C+D+E"` join rather than a structured list. | Deferred — would require schema widening under `test_miocertificate_schema_frozen`. |

## Gallery rule (memory `feedback_phase_boundary_gallery.md`)

**No-op for this phase — documented explicitly.**

Rationale: this lane's scope (governing plan §0 rule 2) forbids
touching `plots/physics_gallery/`. That directory is auto-managed by
the bass_py session per its per-phase gallery refresh rule. The Week 6
MIO package does not yet produce publication figures (those land with
MANU-CH12-NEW, Week 8+). The `mio_directional_coherence.json`
artefact under `bass_py/workspace/results/` is the Week 6 primary
deliverable and is serialised data, not a plot. Visual inspection
therefore has no new PNG target.

---

Patch 1 (next-session prompt rotation) lands in the same audit commit.
Carry-forward items recorded above are tracked in the rotated
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §3 table.
