# Phase-boundary audit — Independent Tracks Week 11

**Phase tag**: `IND_TRACKS_W11`
**Date**: 2026-04-19
**Plan**: INDEPENDENT_TRACKS_PLAN.md **v1.3** §21 (Week 11 entry
added this session); day-by-day guidance from
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 11. Execution:
W10 F4/F5 closures (Days 1-2), MIO HJ-02b z-binned directional
coherence (Days 3-4), DOS-A36 + A37 dossier continuations (Days 5-6),
this audit + NEXT_SESSION rotation (Day 7).
**Pre-commit audit** per memory rule `feedback_phase_boundary_audit.md`.
**Parent-plan references**:
v3 §4.5.3.2 (HJ-02 directional coherence — row 2 `redshift_binned.py`);
v3 §16.2 FM2 (σ_cone placeholders, inherited by HJ-02b);
v3 §16.2 FM5 (probe-name ad-hoc string-join, formalised here by A37);
W10 F4 (plan-doc `/project` wording cleanup);
W10 F5 (hardcoded `report.ell.size == 27`).

**Baseline head**: `2be22e0` (`IND_TRACKS_W10: phase audit + next-session
prompt rotation`). A single bass-side landing (`48f9a26`, `FB-1.2:
Class A VIII/IX background validation + Bianchi IX recollapse event`)
intervened between W11D3 and W11D5 — out-of-lane and not part of
the W11 ledger.

**Commits this phase** (this lane):

- `W11D1` — `8aefbb8` `W11D1: AUDIT(W10-F4+F5): plan v1.3 +
  brittle-test rewrite`. Brings `INDEPENDENT_TRACKS_PLAN.md` into
  git for the first time with a v1.3 §21 Week 10 + Week 11 entry
  that spells out the post-W8-FM1 `/project` rule (never stage
  project/ paths), preventing any reintroduction of the stale
  "force-add contract" wording flagged by W10 F4. Also rewrites
  `test_extract_drops_zero_kernel_multipoles` to compute the
  expected `report.ell.size` from `ShearExtractorConfig()`
  defaults rather than hardcoding `27`, closing W10 F5.
- `W11D3` — `06de6d3` `W11D3: MIO HJ-02b z-binned directional
  coherence`. Adds `bass_py/mio/coherence/redshift_binned.py`
  (~350 L) + `bass_py/mio/tests/test_redshift_binned_coherence.py`
  (15 tests). Public surface: `RedshiftBinnedProbe`,
  `STANDARD_Z_PROBES` (5-probe SSOT with literature-anchored
  `z_eff`), `DEFAULT_Z_BINS` (3-bin default), `assign_probes_to_bins`,
  `per_bin_resultants`, `total_drift_deg`, `drift_pvalue`
  (permutation null test), `to_mio_certificate`,
  `emit_redshift_coherence_artefact`. G19 hard-separation: cert
  is `reduction_status='diagnostic-only'` and contains no
  `posterior` string. MIO contribution 56 → 71.
- `W11D5` — `5a7bf2a` `W11D5: DOS-A36 + A37 dossier continuations`.
  Two new A30-series dossier files: A36 (MIO channel weighting
  policy — three categories of weighting with allowed/forbidden
  classification + per-statistic specs) and A37 (MIO probe-name
  schema v1 with frozen BNF + registered `PROBE_ID`s).
- `W11D7` (= this audit) — pending commit: this log + NEXT_SESSION
  rotation.

**Touched-surface test count**: `bass_py/htt/tests/ bass_py/src/
bass_py/tsc/admissibility/ bass_py/tsc/diagnostics/
bass_py/tsc/charts/ bass_py/tsc/integration/ bass_py/workspace/
bass_py/mio/` → **1041 passed, 0 failed, 4 skipped**. Week 11
delta vs Week 10 (1026 / 0 / 4): **+15 tests pass (HJ-02b suite),
0 skip change, 0 regressions**.

**TSC-standalone test count**: `bass_py/tsc/` → 602 passed
(unchanged from W10 — no TSC code change this week).

**MIO contribution**: 71 tests (+15 vs W10's 56; gate ≥ 47 met
with 24 to spare). Composition: 19 directional-coherence (W6) +
8 certificate-generator (W6) + 5 boot (W6) + 5 bridges (W6/W7) +
5 masked-sky (W6) + 19 HJ-01 (W10D3) + **15 HJ-02b
z-binned-coherence (W11D3, new)**. Cross-check: `pytest
bass_py/mio/ --collect-only -q | tail -1` = `71 tests collected`.

**Smoke-test skip composition** (touched surface, 4 skips):
unchanged from W10 end-of-phase composition — 2 × mio.core/reporting
(W6 SKIP-02b-v3-LEGACY, unchanged until MANU-CH12-NEW figure
retirement), 1 × `test_figures_smoke.py::fig_certification_matrix`
family (W9 carry), 1 × `test_bulkflow_likelihood.py:303` dynesty
contract guard (W10D1 composition swap, by-design).

---

## 1. Audit target reconstruction

This phase ships three artefacts. Each has a distinct audit target:

### W11D1 — plan-doc + brittle test

- **Core claim**: the plan-doc should document the post-W8-FM1
  `/project` rule verbatim so that no future reader reintroduces
  the stale "force-add contract" behaviour; the brittle assertion
  `report.ell.size == 27` should be derived from config defaults.
- **Algorithm**: not applicable (documentation + test refactor).
- **Output**: plan-doc v1.3 + passing test with the new computed
  expression.

### W11D3 — HJ-02b z-binned coherence

- **Core physical claim**: under the null "probe direction is
  independent of the probe's effective redshift", the fitted
  per-bin resultant axis is an iid draw from the same spherical
  distribution regardless of bin. The drift statistic Σ sep(i, i+1)
  across populated bins is therefore invariant under a random
  permutation of `z_eff` labels.
- **Algorithm**:
  1. Partition the N probes into the K z bins.
  2. Per bin, compute the inverse-variance-weighted spherical
     mean axis via `spherical_mean` (COMMON-A SSOT helper).
  3. Sum the angular separations between consecutive populated
     bin axes → `total_drift_deg`.
  4. For `n_mock` permutations of `z_eff`, recompute step 1–3
     and count the fraction ≥ observed → `drift_pvalue`
     (Lidstone-smoothed: `(k + 1) / (n_mock + 1)`).
- **Output**: `MioCertificate(report_type='redshift_binned_coherence',
  reduction_status='diagnostic-only', ...)` + JSON artefact
  `mio_redshift_coherence_v1.json`.
- **Source of truth hierarchy**: equation (permutation invariance
  under the z-drift null) > spec (v3 §4.5.3.2 row 2) > code
  (`redshift_binned.py`) > test (`test_redshift_binned_coherence.py`).

### W11D5 — DOS-A36 + A37

- **Core claim** (A36): MIO weighting inside one statistic is free;
  weighting across MIO statistics or across MIO/HTT is forbidden by
  G19.
- **Core claim** (A37): `MioCertificate.probe_name` follows a
  frozen grammar v1 (singleton | alphabetical bundle | atlas_label).
- **Output**: documentation only; no code or test change.

---

## 2. Contract / interface table

### HJ-02b (`mio.coherence.redshift_binned`)

| Field | Value |
|---|---|
| **Input types** | `probes: Sequence[RedshiftBinnedProbe]` (frozen dataclass: name, l_deg, b_deg, sigma_cone_deg, z_eff, weight=1.0); `bins: Sequence[Tuple[float, float]]` |
| **Output types** | `List[ZBinResult]` (frozen), `float` drift (deg), `float` p-value ∈ (0, 1], `MioCertificate` |
| **Units** | angles in **degrees** (internal `lb_to_unitvec` converts to radians and back); `sigma_cone_deg` > 0; `z_eff` ≥ 0 |
| **Shape** | per-bin resultants list of length `len(bins)`; axes shape `(M, 3)` for M populated bins; separation matrix shape `(M, M)` |
| **Sign / normalization** | `resultant_R ∈ [0, 1]`; drift deg ∈ [0, 180°·(K-1)] where K = number of populated bins |
| **Domain / admissible range** | bin lower bound < bin upper bound (raises `ValueError`); `sigma_cone_deg > 0` (raises `ValueError`) |
| **Boundary / initial** | empty bins flagged with `n_probes=0` + NaN axis, contribute 0 to drift; single-probe input short-circuits `drift_pvalue → 1.0` |
| **Invariants** | (a) permutation of probe ordering within a bin does not change the resultant (`spherical_mean` is symmetric); (b) two identical probes in one bin give R = 1 exactly (tested); (c) all-aligned probes across all bins give drift = 0 exactly (tested) |
| **Solver assumption** | none (pure linear algebra + rng-permutation Monte Carlo) |
| **Regime assumption** | permutation null valid when probe count N ≥ 2 (A36.5 caveat: N < 8 with 2 bins can have degenerate permutation distribution; not tested with automatic enforcement, documented in F3 below) |
| **Test oracle** | all 15 tests in `test_redshift_binned_coherence.py` green; full touched-surface 1041 / 0 / 4 |

### W11D1 test rewrite

| Field | Value |
|---|---|
| **Replaced**| `assert report.ell.size == 27` |
| **With**    | `assert report.ell.size == expected_window - len(dropped)` where `expected_window = cfg.ell_max - cfg.ell_min + 1` from `ShearExtractorConfig()` defaults |
| **Invariant** | test now tracks any future change to `ShearExtractorConfig` defaults without a dangling literal |

---

## 3. Phys-math audit ledger

| Item | Verdict | Evidence |
|---|---|---|
| **Definition / notation** (`z_eff` vs `z_min/z_max`) | **pass** | `z_eff` is the effective measured redshift of each probe; `z_min / z_max` are the bin edges. Named differently in the dataclass and the bin tuples; no symbol collision. |
| **Index / trace consistency** | **pass** | Per-bin resultant uses `spherical_mean` (COMMON-A SSOT, already audited in W1–W2); no PSTF content at this level. |
| **Sign / normalization** | **pass** | `resultant_R` inherited from COMMON-A; drift sum is non-negative (arccos ∈ [0, π]); p-value ∈ (0, 1] by Lidstone smoothing. |
| **Units / dimensions** | **pass** | Inputs degrees → `lb_to_unitvec` converts to radians internally → `arccos` in radians → `rad2deg` on return. No unit leak. |
| **Known-limit recovery** | **pass** | `test_total_drift_deg_zero_when_all_bins_share_axis`: 3-bin all-aligned input gives drift ≈ 0. `test_drift_pvalue_high_when_directions_are_random_wrt_z`: isotropic probes with random z_eff give `p > 0.05` (no false detection). `test_drift_pvalue_low_when_z_is_perfectly_correlated_with_direction`: 3-axis-orthogonal injection gives `p < 0.05`. |
| **Boundary / regularity / positivity** | **pass** | Empty-bin handling: `per_bin_resultants` returns `n_probes=0, l_deg=NaN, resultant_R=0.0`; `_populated_axes` filter drops these before the drift sum. Single-probe short-circuit in `drift_pvalue` → `1.0`. |
| **Hidden assumptions** | **see F3** | Permutation null assumes z_eff can be exchanged across probes without changing the marginal direction distribution; degenerate with small N + 2-bin design, documented in F3 below. |
| **Adversarial special case** | **pass** | `test_assign_drops_probes_outside_all_bins`: probes with `z_eff` outside all bins silently excluded — tested and expected. |

---

## 4. Equation-to-code mapping audit

| Equation (prose) | Module function | Test evidence |
|---|---|---|
| `R = \|Σ_i w_i v̂_i\| / Σ_i w_i` (inverse-variance spherical mean) | `per_bin_resultants` → `spherical_mean` (common.sky_geometry) | `test_per_bin_resultants_match_manual_spherical_mean` (two identical probes → R=1; single probe → R=1) |
| `drift = Σ_{i=1}^{M-1} arccos(v̂_i · v̂_{i+1})` | `total_drift_deg` | `test_total_drift_deg_zero_when_all_bins_share_axis` |
| `p = (k + 1) / (n_mock + 1), k = #{mocks with drift_mock ≥ drift_obs}` | `drift_pvalue` | `test_drift_pvalue_{high,low,single_probe}_...` |
| MIO probe_name grammar v1 (A37.2) | `to_mio_certificate(...).probe_name = "+".join(p.name for p in probes)` | structural compliance by construction (no dedicated test, deferred to Week 12+ per A37.6) |

**Approximation / regime compliance**: no approximations beyond the
`arccos` domain clip at ±1.0 (guards floating-point slop); the
spherical-mean routine is exact in closed form.

**Production-path check**: the production entry point
`emit_redshift_coherence_artefact` uses the same function chain as
the tests (`per_bin_resultants → total_drift_deg → drift_pvalue →
to_mio_certificate`). No surrogate / helper path.

---

## 5. Numerical / pipeline audit

| Item | Assessment |
|---|---|
| Solver suitability | N/A — no ODE / no quadrature |
| Tolerance sensitivity | `arccos` domain clip `np.clip(..., -1.0, 1.0)` prevents NaNs from tiny fp overshoot. `resultant_vector` tests assert at `abs=1e-10` — tight but passing. |
| Underflow / overflow | None expected; all quantities are O(1). |
| Conditioning | Degrades only when probes cancel (R → 0) → NaN axis; explicitly handled by `_populated_axes` filter. |
| Cache / state leakage | RNG is always passed as a parameter; no module-level state. |
| Seed / reproducibility | All tests pass `rng=np.random.default_rng(seed=...)`. Emitter uses a fixed seed `20260419` when `rng=None`. |
| Baseline reproduction | `pytest bass_py/mio/tests/test_redshift_binned_coherence.py` reproduces all 15 tests in ~0.5 s on the dev box; touched-surface regression bit-stable across runs. |
| OOD / misspecification | `n_mock` default 5 000 works for N ≤ 20 probes. For N > 20 (not currently a concern; the SSOT is 5 probes), the test would become computationally expensive; no guard emitted. |

---

## 6. Ranked failure modes (P0–P3)

| # | Severity | Type | Symptom | Root cause | Cheapest discriminator | Misinterpretation risk |
|---|---|---|---|---|---|---|
| F1 | **P3** | testing | `drift_pvalue` Monte-Carlo has default `n_mock=5 000`; no exact-enumeration path | small-N cases where `N! / (N_per_bin!)^K` is tractable could use exact enumeration for bit-identity reproducibility | add an `exact: bool = False` kwarg that switches to `itertools.permutations` when the count is < 10 000 | using a 5 000-permutation Monte-Carlo p-value when an exact p-value is affordable |
| F2 | **P3** | design | permutation distribution is degenerate with small N + 2-bin, antipodal-injection design (discovered during test authoring — see W11 §7) | combinatorics: with N=8, K=2, the distribution of "# low-axis probes in bin 0" only has 5 distinct values (k ∈ {0..4}), so the drift statistic takes very few values | use ≥ 3 bins or N > 12 when designing significance claims | a failed injection test being read as "drift test doesn't work" when it is in fact a malformed test |
| F3 | **P3** | physics | HJ-02b inherits v3 §16.2 FM2 σ_cone placeholders from HJ-02a (Radio / CF4++ / BiPoSH values are plan-suggested, not literature-published) | same upstream issue as HJ-02a; HJ-02b SSOT `STANDARD_Z_PROBES` holds the same σ values | resolved when MANU-CH12-NEW §12.2 cites published σ numbers with DOIs | CMB-dominated HJ-02b result being read as "5-probe agreement" when σ_CMB = 0.5° dominates the inverse-variance weighting |
| F4 | **P3** | docs | A37 acceptance tests (`test_probe_name_is_alphabetical_bundle`, `test_probe_name_matches_grammar_v1`) are deferred to Week 12+ | requires the CONTRACTS-01 v2 hash-digest infrastructure (W7 FM3 pattern) not yet in place | land the two tests once the v2 bump is scoped | ad-hoc string-join drift across MIO modules (e.g. a future module joining with `","` instead of `"+"`) |
| F5 | **P3** | interface | `emit_redshift_coherence_artefact` does not log a provenance SHA beyond `MioCertificate.git_commit` (set at instantiation time — same behaviour as HJ-02a) | inherited from MIO-HJ-06a `build_mio_certificate` helper | not a blocker; W6 FM6 already documents this as expected behaviour | reader expecting "artefact SHA" to match the commit at read-time |

**No P0 / P1 items found.** All five findings are P3 / by-design.
W11 shipped a clean diagnostic-only skeleton that is test-covered and
G19-compliant; the open items are documentation follow-ups or
upstream-blocked upgrades.

---

## 7. Verifier results

**A. Physics verifier**
- **known-limit recovery**: **passed** — all-aligned → drift 0; no-correlation → p > 0.05; perfect 3-axis injection → p < 0.05.
- **dimensional consistency**: **passed** — degrees throughout the public API; radians internal only.
- **sign / normalization**: **passed** — resultant R ∈ [0, 1]; drift non-negative; p-value ∈ (0, 1].
- **positivity / admissibility**: **passed** — every internal arccos domain clip tested by construction (all-aligned edge).
- **alternative explanation**: the low p-value under a strong 3-axis injection is consistent only with a real z-axis correlation; the alternative "random noise in direction" is ruled out by the high-p test on the same probe count.

**B. Code verifier**
- **contract satisfaction**: **passed** — `RedshiftBinnedProbe` is frozen; `ZBinResult` is frozen; `drift_pvalue` raises on `n_mock < 1`; `assign_probes_to_bins` raises on empty/degenerate bins.
- **actual code-path usage**: **passed** — test invokes `emit_redshift_coherence_artefact` (production path) and verifies the same payload that would be consumed by a downstream MANU-CH12 draft.
- **regression risk**: **low** — no existing module touched except `mio.coherence.__init__.py` (docstring-only update); touched-surface 1026 → 1041, zero failures.
- **reproducibility**: **passed** — rng seeds in every test; artefact emitter deterministic under fixed seed.

**C. Numerical verifier**
- **tolerance robustness**: **passed** — `arccos` domain clip tested.
- **convergence / stability**: **passed** — no iterative solver; permutation Monte Carlo converges at √n rate, n=5 000 is ample for α=0.05 detection.
- **baseline reproducibility**: **passed** — touched-surface regression bit-stable.
- **uncertainty / misspecification**: **partial** — σ_cone placeholders noted in F3 above; not a verifier failure, documented.

**D. Dossier verifier**
- **A36 + A37 references exist**: **passed** — both files reference A32 / A34 / A35 / A38 / A39 / A40 where applicable; anchored to the existing file paths.
- **Policy consistency**: **passed** — A36 channel-weighting table aligns with the A34 cross-check catalogue; A37 probe-name grammar is forward-compatible with a future `probe_names: list[str]` schema bump (matches W6 FM5 migration note).

---

## 8. Minimal repair plan

No P0/P1 repair needed. Two opportunistic P3 patches, optional for
Week 12+:

| # | Patch | Load-bearing? | Failure mode avoided | New test | Baseline impact |
|---|---|---|---|---|---|
| R1 | Add `exact: bool = False` path in `drift_pvalue` that switches to `itertools.permutations` when `math.factorial(N) < 10_000` | no (P3) | F1 — avoids non-determinism for small-N edge reproducibility | `test_drift_pvalue_exact_matches_montecarlo_at_small_N` | zero — MC path remains default |
| R2 | Add `test_probe_name_matches_grammar_v1` (A37.2 regex enforcement across `to_mio_certificate` of HJ-01 / HJ-02a / HJ-02b) | no (P3) | F4 — prevents drift across modules | one regex test per module | zero |

Not recommended for this phase: no P0/P1 risk.

---

## 9. Minimal test set (landed or referenced)

- **Baseline reproduction**: `pytest bass_py/mio/tests/test_redshift_binned_coherence.py` → 15/15 green in ~0.5 s.
- **Edge / adversarial**: `test_assign_drops_probes_outside_all_bins` (outside-range probes silently filtered); `test_drift_pvalue_single_probe_returns_one` (short-circuit).
- **Physics sanity**: `test_total_drift_deg_zero_when_all_bins_share_axis` (all-aligned known limit); `test_drift_pvalue_low_when_z_is_perfectly_correlated_with_direction` (3-axis injection recovery).
- **Numerical stability / sensitivity**: `test_per_bin_resultants_match_manual_spherical_mean` (asserts at `abs=1e-10` and `abs=1e-12`).
- **Regression**: full touched-surface `1041 / 0 / 4` (+15 over W10 baseline).

---

## 10. 최종 판정

- **통과** — 치명적 오류 없음. W11 세 landings 모두 contract ↔ equation ↔ code ↔ test 일관.
- **지금 당장 구현/수정할 1개**: 없음. 모든 발견 사항(F1–F5)은 P3 / by-design / 상류 의존 대기.
- **지금 손대면 안 되는 1개**: HJ-01 production wiring (`reduction_status='theory-direct'` 승격 + per-ℓ covariance χ² 교체). 이 항목은 bass_py W10-02 K_ℓ atlas V-gate를 기다리는 것이 계획(부모 §17.3) — 선제적으로 건드리면 diagnostic-only 계약을 깨뜨린다.

---

## Week-11 final gate (per NEXT_SESSION §2 Week 11)

- [x] W10 F4 + W10 F5 closed (W11D1 `8aefbb8`). Plan-doc v1.3 shipped; brittle test rewritten and green.
- [x] HJ-02b landed (W11D3 `06de6d3`); MIO contribution monotonically increased (56 → 71); 15 new tests; touched-surface 1026 → 1041.
- [x] At least one new A3x dossier file landed (W11D5 `5a7bf2a` — A36 + A37, two files, both ~130–140 L).
- [x] Phase-boundary audit log written (this file).
- [x] No touched-surface regressions (1041 passed / 0 failed / 4 skipped; skip composition unchanged from W10 end-of-phase).

---

## Outstanding P2 / P3 carry-forward items (full list at `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §3 post-rotation)

New W11 additions, all P3:

| Tag | Severity | Description | Where to act |
|---|---|---|---|
| W11 F1 | P3 | `drift_pvalue` has no exact-enumeration path for small-N reproducibility | opportunistic; Week 12+ if a use case appears |
| W11 F2 | P3 | permutation distribution degenerate for (N ≤ 8, K = 2, antipodal injection) test designs | documentation-only; enforced culturally via the "≥ 3 bins or N > 12" guidance in this audit §6 |
| W11 F3 | P3 | HJ-02b inherits σ_cone placeholders from HJ-02a (v3 §16.2 FM2) | same resolution path as HJ-02a — MANU-CH12-NEW §12.2 literature citations |
| W11 F4 | P3 | A37 grammar acceptance tests deferred to Week 12+ pending CONTRACTS-01 v2 hash-digest infrastructure | land two regex tests when the v2 bump is scoped |
| W11 F5 | P3 | `emit_redshift_coherence_artefact` provenance SHA = cert.git_commit (instantiation-time; inherited from MIO-HJ-06a, already documented as W6 FM6 expected behaviour) | no action — by design |

W10 carry-forward items unchanged — see
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §3 for the full P0–P3
ledger. W10 F4 and W10 F5 are now closed.

---

**Last audited**: 2026-04-19 (W11D7)
