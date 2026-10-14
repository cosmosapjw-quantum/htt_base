# G10-D — independent review (verbatim final report of a fresh read-only reviewer)

# G10-D: independent review report (two-point testing and union/triangle probability bounds)

**Reviewer:** fresh read-only subagent. Model claude-opus-5-5 (Opus 5.5). This is the same LLM family the author requested (the author's observed model is recorded as UNKNOWN), so correlation is disclosed. I did not author G10-D. No repository file was edited and no state-changing git command was run. Scratch output is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g10d_rerun/`.

**Task directory (T):** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/g10d_two_point_testing_v1_20261014`

## Verdict: PASS_WITH_NOTES

There are no blocking findings. Every frozen target is proved, compiles independently, and depends only on the axioms `propext`, `Classical.choice` and `Quot.sound`.

Acceptance item 1 (both counterexamples belong to the original admissible class) is met at the source's own scope:
- **Cutout pair:** membership is proved inside this unit.
- **Morphology pair:** membership is met by reference to C01 (finite tuple conditions) and to the source's statistical model.

The one remaining physical residual is the smooth realization of the morphology jets (the optical-note "image theorem"). That obligation sits upstream and outside G10-D, so it should not keep G10-D uncounted. Count G10-D with the inherited residual named explicitly (see Note N1 for the record fix). Scientific admission: HOLD.

## Decision on acceptance item 1

### What the source defines as the admissible class

The source fixes a kinematic test-source class in a fixed metric. It is not an Einstein–matter class.

From `statistics/INFORMATION_LIMIT_THEOREMS.md` (sha256 `775b7d15…`, identical at the card snapshot a30d84c7):
- **Line 20:** "Every such tuple is realizable as a smooth test-source first jet in a fixed smooth metric, including Minkowski."
- **Line 42:** "Both tuples are admissible, have identical \(\mathcal P\)…"
- **Line 70:** "The image theorem supplies its normalization-compatible derivative and a smooth local realization."
- **Line 82:** "The constructions are local kinematic source fields in the same chosen metric. They are not established as two solutions of the same Einstein–matter closure."
- **Line 131:** "Block independence and isotropic covariance are hypotheses of this exact benchmark, not properties established for real catalogue estimates."
- **Line 137:** "…there are two smooth future unit test-source fields such that:"
- **Line 176:** "It is a test congruence, not an Einstein–dust solution. … The fixed-observer condition is essential."
- **Line 182:** "Suppose the measured-data model, sampling, and noise depend only on their common exterior data … Then the complete data laws are identical."

From `cas/contracts/CAS-10.json` (sha256 `03dd5c3c…`):
- **Lines 63–65 (assumptions):** "Local kinematic source; separate-sector powers only", "Independent isotropic Gaussian blocks for equal-law benchmark", "Fixed observer,a>0,M>0; no auxiliary interior input".
- **Line 74 (exclusions):** "No same-matter realization".

### Cutout pair: proved in this unit

Membership is proved in G10-D itself:
- C1: both fields are future unit.
- C1s: both are smooth (`ContDiff ⊤`) on all of E3.
- C3 and C3e: the exterior data agree for every unit direction and every r ≥ a.
- C4: the bound ≤ M holds along every ray for r ≥ 0, including the unobserved segment.
- C3l: equal laws follow for any observation map `obs : ExtData a → Measure Ω`, which is the source's line-182 kernel condition.
- The fixed observer o = (1,0,0,0) is encoded directly.

One piece is encoded rather than derived: d_A = r is entered as a field-independent component (disclosed). This is physically sound, because observer area distance depends on the metric and the observer, not on the emitter velocity.

### Morphology pair: met by reference

The G10-D morphology statements (M1–M4e) are universally quantified over (H, z0, m, z1, t, σ). The Theorem-I tuple is therefore one instance:

> z0 = 5/4, z1 = (3/4, 0, 0), m = 7H/4, t = orthonormal coordinates of T

My reviewer audit compiles M4 at exactly this instance (check R2).

The finite membership conditions are covered by C01 (`CAS10C01.u_unit`, `B1_u_zero`, `b2_norm`, equal powers; CAS_4AXIS_PASS, review PASS_FINITE_COMPONENT_REVIEW):
- u is a unit vector with γ = 5/4 ≥ 1.
- T is symmetric and trace-free.
- A = 0 for the first tuple; b² = 87525H²/16384 > 0 for the second.

The slope vectors are definitionally linked to the ones G10-B and G10-D use. In my audit, `CAS10C01.p1 H = CAS10C03.p H` and `CAS10C01.p2 H = CAS10C03.pPrime H` both close by `rfl`.

I also checked the B → (m, p, T) map with sympy: q = 19H/16, m = 7H/4, p = (15H/8, 0, 0), T = diag(3/8, −3/16, −3/16)·H. For the primed tuple, q′ = 377H/128 and b′ = (H/512)(−765, 1275, −600, 0), with b′·b′ = 87525H²/16384. All match (I3)–(I5).

G10-A does **not** supply admissibility. Its own not-proved list reads: "smooth/covariant field version", "identification of S with B_ab".

### What remains and who owns it

The remaining physical residual is the smooth local realization of the morphology jets (line 70, the optical-note image theorem). It is not proved in C01, C02, G10-A or G10-D.

This is an upstream input, not part of the G10-D two-point theorem. Logically, the G10-D conclusions depend only on law equality or the KL value, not on admissibility. Requiring Einstein–matter closure would exceed the original class, which lines 82 and 176 and the contract exclusion "No same-matter realization" rule out.

**Conclusion:** item 1 is met by reference at source scope. Count G10-D, and carry the image-theorem realization as an inherited upstream residual.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Generic two-point targets G1–G8 match (I15) | PASS | (I15) lines 184–191: P{diam ≥ D} ≥ 1−2α and E diam ≥ (1−2α)D via the union bound; max_i E_i d ≥ D/2 via the triangle inequality. The Lean statements match. Diameter uses `Metric.ediam`, which is faithful: N3 shows real `diam univ = 0`. The loss is the source metric d (as `edist`). E diam uses the lower Lebesgue integral `∫⁻`, the strong direction. |
| 1b | Recorded adjustments | PASS (strengthenings only) | 0 ≤ α < 1/2 and D > 0 are not assumed, so the hypotheses are weaker. N2 allows Θ to be any type. `noncomputable def` for `mink`, `obsVec`, `Kray`. Diff of receipt 12 vs final 15 (`diff compile_12_main.source.lean compile_15_main.source.lean`) is proof-only: same statements, edits at lines 554–557, 614–615, 622–623, 632–633, 777, 906, 908. |
| 1c | Bretagnolle–Huber (K1–K4) genuinely proved and correctly stated on the actual laws | PASS | K1: KL additivity over {A, Aᶜ}, using Mathlib `klDiv_eq_lintegral_klFun_of_ac` and restricting the RN derivative. K2: binary KL ≤ `klDiv`, using Mathlib `mul_log_le_klDiv` (Basic.lean:360) on each cell; the non-absolutely-continuous branch is `⊤`. K3: Bernoulli BH via concavity of log (Bhattacharyya ≥ e^{−K/2}), then Cauchy–Schwarz S² ≤ (x+1−y)(y+1−x) ≤ 2(x+1−y). K4: μ(A) + ν(Aᶜ) ≥ ½e^{−K}, with μ ≪ ν derived from finite KL. This is the standard BH form. Numeric sanity check: 2×10⁵ random Bernoulli pairs, minimum slack 6.2e−4 > 0. At the pin, `grep -rliE "bretagnolle\|pinsker" Mathlib` returns nothing, so self-proving it was necessary. |
| 1d | Bound covers all measurable estimators, not finite algebra | PASS | G6, G7 and K5 hold for every measurable θ̂ : Ω → Θ, with Θ any pseudo-metric space with `OpensMeasurableSpace`. G8 bounds Mathlib `minimaxRisk` (Defs.lean:60, infimum over all Markov kernels of the maximum risk), so it covers all randomized estimators. M3 covers all measurable powers-only estimators, which is the source's class. M4e covers all measurable full-data estimators via BH. |
| 1e | Loss and target metric unchanged | PASS | Cutout: rapidity distance \|·\| gives D = δ; intercept dipole Euclidean distance gives D = sinh δ ≥ δ (C5r, C5d), as the source states. Morphology: Theorem II is a testing statement; M1 (type I + type II = 1 for every powers-only randomized test) is its exact content. M2 and M3 quantify over every pseudo-metric target, which is a strengthening and not a convenience change, because the source fixes no estimation metric. The slope-dipole Euclidean metric (M2s, M4e) is a labelled worked instance; separation 15√2\|H\|/8 is checked by sympy. |
| 1f | KL constant connected to a testing bound (card pitfall) | PASS | M4: ½·exp(−225H²/(64σ₃²)) ≤ P(A) + Q(Aᶜ) for every measurable A, using G10-B `full_kl_eq` (actual `klDiv`). M4e gives the estimator form. N5 shows the full laws differ. Index σ 3 is the p block (order Z₀, Z₁, m, p, T), matching σ_p in (I10). KL ½·2(15H/8)²/σ_p² = 225H²/(64σ_p²) checked by sympy. |
| 1g | (I13) | PASS | C4a holds for every r ≥ 0 with a two-sided second derivative. The plateau neighbourhood (−a/8, a/8) handles r = 0. The bound e^δ(δ²\|q′\|² + δ\|q″\|) uses \|n_x\| ≤ 1 and χ ∈ [0, δ]. Numeric check with the C² quintic cutoff (same derivative bounds), a = 1: at δ = 0.04, max\|Z″\| = 0.9544 ≤ 0.9849; at δ = 0.01, 0.2328 ≤ 0.2347. |
| 1h | (I14) | PASS | The Lean chain 40/√3 ≤ 70/3, s² ≤ s and e^{1/25} ≤ 25/24 gives (25/24)(1147/1200) = 1147/1152. mpmath: e^{1/25}(8/(5√3) + 9/400) = 0.98488 < 1147/1152 = 0.99566 < 1; e^{1/25} = 1.04081 < 1.041667; √3 = 1.73205 > 12/7. |
| 1i | Negative controls | PASS | N1 (Dirac 0 vs Dirac 1, singleton sets) shows the floor fails without equal laws. N2 shows the coverage hypotheses are satisfiable. N3 shows `diam` vs `ediam` differ on unbounded sets. N4 shows u1 ≠ u0. N5 shows the full morphology laws differ. All are genuine. |
| 2 | No circularity and no vacuity | PASS | No hypothesis restates its conclusion. My audit file instantiates: (R2) M4 at the physical Theorem-I tuple, H = 1, σ ≡ 1; (R3) cutout floor C6r with the constant two-point set and full coverage, under an arbitrary probability observation map; (R4) C7 at a = M = 1; (R5) `deltaOf 1 1 = 1/25`; (R6) BH with KL(μ‖μ) ≤ 0. All compile. |
| 3a | Hashes | PASS | Recomputed sha256 values match AUTHOR_RETURN for: SOURCE_RECOVERY `80e88afe…`, FROZEN `f737fb38…`, main `600a96ec…`, AxiomAudit `c6a27409…`, run_compile `9692521b…`, all six oleans, and all five reused sources. The reused sources are byte-identical to the originals in c01 v2, c03 v2, g10b and g10c. For all 16 receipts, source, stdout and stderr hashes match. |
| 3b | Exit codes and preserved failures | PASS | Receipts 01–05 = 0; 06, 07 = 1; 08, 09 = 0; 10 = 1; 11 = 0; 12 = 1; 13 (probe with `sorry`) = 1; 14 = 0; 15 (final main) = 0; 16 (audit) = 0. All failed attempts are kept. |
| 3c | Axioms and forbidden tokens | PASS | `grep -nE "sorry\|admit\|native_decide\|axiom\|set_option\|maxHeartbeats\|implemented_by\|extern\|unsafe\|opaque"` over T/lean finds nothing. Recorded audit: 70 of 70 `#print axioms` lines are [propext, Classical.choice, Quot.sound]. The `sorry` in `raw/probes/P13Fix.lean` is a diagnostic probe that is not imported. |
| 3d | Resumed run | PASS_WITH_NOTE | Receipts 01–12 are retained and their hashes are valid. FROZEN's birth time equals its mtime (2026-10-14 06:49:55 KST), so it was never modified. FROZEN predates the first main compile (06, started 21:51:01Z) but not import receipts 01–05; FROZEN discloses this, and those are compiles of unchanged reviewed modules. SOURCE_RECOVERY was written after the final compile (11:43 KST) and is provenance only. FROZEN already carried the source line citations at freeze time. |
| 3e | Citations | PASS_WITH_NOTE | All Lean line citations (G10B 154/157/182/377/379/390/447/455/477/514; C03 31/32/55/58; G10C 497…672) and Mathlib citations (Basic.lean 68/138/360, Defs.lean 60, Deriv.lean 103) are correct. Three ILT line numbers in SOURCE_RECOVERY are off by two (Note N4). |
| 3f | PRs #493–#495 not re-read | NOT MATERIAL | Per `PR_INDEX_ALL.csv`: #493 = CAS10-C01 (head d5bc8a70), #494 = CAS10-C03 (deffbcff), #495 = CAS10-C04 (e372106d). All three heads exist as local commits. ALL_OBLIGATIONS reconciliation reports exact payload match (115/115, 112/112, 60/60). Grepping their added lines for estimator, loss, diam, confidence, minimax, risk, Pinsker and Bretagnolle finds only "two-point probability bound(s)" listed as a *remaining* obligation in #495. They fix no loss or target metric, which discharges the SOURCE_RECOVERY unlock condition. |
| 4 | Independent recompile | PASS | See below. |

**Recompile detail (check 4).** From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (Lean v4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, verified with `git rev-parse`), I rebuilt every import from source into scratch, then the main module:

```
lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/<M>.olean $S/src/<M>.lean"
```

Results: CAS10C01, CAS10C03, P12GaussianLaw, G10BGaussianKL, G10CSmoothCutoff and G10DTwoPoint all exit 0, with the same three linter warnings as receipt 15. The copied main source hash is `600a96ec…`. My `ReviewerAudit.lean` (70 `#print axioms` plus checks R1–R7) exits 0, and all 70 results are [propext, Classical.choice, Quot.sound].

## Blocking findings

None.

## Non-blocking notes and fixes

**N1. AUTHOR_RETURN acceptance-1 wording.** `status_scope` says item 1 is "NOT closed by this unit". Replace with:

> "Acceptance 1 met at source scope: cutout pair proved in-unit (C1/C1s/C3/C3l/C4/C7); morphology pair covered by universal quantification plus C01 finite membership (u_unit, B1u=0, b'^2>0, equal powers). Inherited upstream residual: smooth local realization of the morphology jets (ILT line 70 image theorem), not a G10-D obligation. Einstein–matter closure is excluded by the source (lines 82, 176) and the contract (`No same-matter realization`)."

**N2. Inner-measure form only exported generically.** The physical-pair specializations (C6r, C6d, M2) export only the outer-measure form of P{diam ≥ D}; G3 has the inner measurable-subset form. Optional fix: also export `(confidence_set_floor …).1` in C6r, C6d and M2.

**N3. Some estimator classes not instantiated on the physical pairs.** G8 (randomized estimators via `minimaxRisk`) is generic only. C6e and M3 cover deterministic measurable estimators. Optional fix: add a `Kernel (Fin 2) Ω` instance built from `obs` and from the compressed laws.

**N4. SOURCE_RECOVERY line drift.** Three ILT citations are off by two:
- "fixed-observer remark 178" should be 176.
- "§6 equal complete data laws 184" should be 182.
- "Corollary (I15) 186-193" should be 184-191.

**N5. `sourceRapidity` is coordinate-specific.** `sourceRapidity u := arsinh (u 0 1)` assumes a boost along e_x. It is valid for these two fields, and the invariant relative rapidity is checked separately (−g(u1(0), u0(0)) = cosh δ).

**N6. Free morphology coordinates.** In Lean the morphology means leave (z0, z1, m, t) free, and only the p block is pinned to C03, and through it to C01 by `rfl`. The Theorem-I values are an instance, not pinned constants. This is acceptable because the statements are universal, and R2 instantiates them.

**N7. Unused hypothesis.** `union_bound_both` carries an unused `h₀` (linter warning). It is harmless.

## Suggested VALIDATION_MATRIX scientific row (for the owner to apply)

| Field | Value |
|---|---|
| Task | G10-D |
| Scientific | PASS_WITH_NOTES |
| Units/normalization | (I10) KL 225H²/(64σ_p²) and separation 15√2\|H\|/8 PASS (sympy) |
| Analytic limits | (I13) and (I14) PASS (mpmath, plus numeric \|Z″\| ≤ bound at δ = 0.01, 0.04) |
| Positivity | BH PASS (2×10⁵ Bernoulli pairs) |
| Admissibility | Cutout in-unit; morphology by reference to C01; upstream residual = image-theorem realization |
| Methodology limits | Kinematic test sources in fixed metric; isotropic Gaussian benchmark; no real-survey law; no minimax sharpness |
| Admission | HOLD |

## Not proved (by G10-D or anywhere in this review)

- Scientific admission (HOLD), publication readiness, novelty.
- Smooth local realization of the morphology jets (optical image theorem): upstream residual.
- Einstein–matter or dust closure of either pair (excluded by the source).
- A comoving or varying-receiver variant.
- Real-survey equal law, masks, anisotropic or cross-block covariance, priors.
- Minimax sharpness or tightness of any bound; uniform consistency; Pinsker.
- d_A = r is encoded, not derived from a null-geodesic computation in Lean.
- Randomized-estimator (Markov kernel) bounds instantiated on the physical pairs.

