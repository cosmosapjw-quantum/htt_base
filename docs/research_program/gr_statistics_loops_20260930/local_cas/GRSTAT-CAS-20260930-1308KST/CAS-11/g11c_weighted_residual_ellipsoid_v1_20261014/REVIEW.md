# G11-C — independent review (verbatim final report of a fresh read-only reviewer)

# G11-C fresh independent review (GR-CAS-11, TEFF-A2: weighted Hilbert residual to singular ellipsoid)

**Verdict: PASS_WITH_NOTES (scoped).** I found no blocking finding. Scientific admission: **HOLD**.

**Reviewer runtime:** claude-opus-5-5 (Opus 5.5). This is self-reported and not attested. The card's review_policy asked for gpt-6-astra/ultra, and that model was not used. I ran in a fresh context, read-only. I did not edit any repository file and ran no state-changing git command. Scratch files are only under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g11-c_rerun/`.

Target directory T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-11/g11c_weighted_residual_ellipsoid_v1_20261014`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read | done | `unzip -p HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip .../tasks/G11-C.json`: 5 lean_steps, 4 acceptance items, 2 pitfalls ("Gram not noise covariance", "finite C03 PASS ≠ weighted Hilbert existence"). |
| 1a | Source hashes and citations | PASS | `TEFF_POSITIVE_BRIDGE.md` sha256 `f04d96fe…ff21b` matches the CAS-11.json provenance entry (line 29). `CAS-11.json` sha256 `6588ac42…0025` matches SOURCE_RECOVERY. I checked every citation in SOURCE_RECOVERY §1 against the files: S:37-39 dν; S:41-44 (A1); S:46-51 (A2); S:53 L²(W) kernels; S:55-58 (A3); S:61-66 r, R, e; S:68-74 (A4), Moore-Penrose, singular R; S:76-87 proof; S:108-114 (A6); C:68-69 exclusions; C:73-77/92-96/108-112 ENT loci; C:245-255 analytic obligations and uncontracted targets. All are accurate. |
| 1b | Main.lean discrepancy | PASS | `CAS-11/lean/Main.lean` (sha `71d4dc6c…`) holds only `grstat_cas11_bregman`. Its `result.json` marks C01/C02/C03 `false`. The author's relocation of the inputs is correct. |
| 1c | C02/C03 are the accepted sources | PASS | `FiniteGram.lean` sha `af91ec60…` equals C02 `completion/SOURCE_MANIFEST.json`:8. C02 `RESULT.md` records CAS_4AXIS_PASS and an Astra review PASS. `WeightedProjection.lean` sha `94f8b213…` equals C03 `SOURCE_MANIFEST.json`:69 and `RAW_EVIDENCE_MANIFEST.reviewed.json`:99. C03 `RETURN.json` has `aggregate_status: CAS_4AXIS_PASS`, and its `REVIEW.md` says PASS. Both files are clean in git (last commits bcdd8ee3 / ec1384fa). |
| 1d | G11-A/B/C01 imports unchanged | PASS | Shas `12f3dd68…`, `85993ce7…`, `92758d9a…`, `ba1bc644…` equal the dep receipt snapshots compile_01–04. The files are clean in git (commits 58935197 / b4f944dd). G11-B is FORMALLY_CHECKED_SCOPED, with review PASS_WITH_NOTES and no blockers. |
| 1e | Frozen targets predate the proof compile | PASS (mtime evidence only) | FROZEN_TARGETS.md mtime is 21:09:40Z, and `raw/FROZEN_TARGETS.sha256` (`88cc8325…`) matches the file. The first main compile (compile_10) started at 21:13:01Z. Before the freeze only three things ran: the six dep recompiles; probe01 and probe02, which I read and which contain only `#check` lines and two trivial `example`s; and nothing else. probe03 ran after the freeze. |
| 1f | Faithfulness of each target to source quantifiers, domains, measure, signs, normalization | PASS with notes | See "Faithfulness detail" below. Every adjustment is either a strengthening or an inherited, declared domain guard. I found no silent weakening. |
| 1g | Key identities by hand | PASS | `integral_wmeas` gives ⟪u,v⟫_{L²(W)} = ∫W·u·v dμ. ∫kδ = ∫W·k·z, with z = δ/W and W>0 a.e. The Gram quadratic form satisfies aᵀRa = ‖Σaⱼrⱼ‖². In the nonvacuity witness (one point, W=2, K=(1,1), m=0): R=[[2,2],[2,2]], det 0, e=(1,1), R†=11ᵀ/8, so eᵀR†e = 1/2 ≤ 2ε = 2. That equals ‖P_span(r) z‖² = 1/2, and ‖z‖² = 1/2 ≤ 2·D_MB(2‖1) = 2(2ln2 − 1) ≈ 0.773. |
| 1h | Numeric cross-check | PASS | `numcheck.py` in scratch: mpmath, 50 digits, random discrete measures, MB/BE/FD. W is the exact sup of z(1+ξz) on the segment, times a random factor in [1, 1.5]. δ is matched exactly (μ-orthogonal to φ). Modes covered: generic, duplicated K, one kernel retained, all retained, duplicated φ (singular φ-Gram), and m=0 / n=0. **270 matched cases, 0 failures.** Each case checked: ‖z‖²_W ≤ 2D; eᵀR⁺e ≤ ‖z‖²; ‖e − RR⁺e‖ < 1e-25; eⱼ = ⟪rⱼ,z⟫; all four Penrose equations < 1e-25; (A3). The largest eᵀR⁺e/(2D) was 0.658. All-retained gave rank R = 0 and ‖e‖ < 1e-25. **Negative control:** 30 of 30 unmatched cases with a retained kernel violate range or the ellipsoid. |
| 2a | No hypothesis assumes a conclusion | PASS | z ∈ L²(W) and ‖z‖² ≤ 2ε are derived in T1 from `G11B.B2_integral`. That in turn uses `G11A.finite_budget_stat`, the guarded wrapper: f ∈ cdom, g ∈ open dom, Bregman nonnegativity derived. No extra budget hypothesis is added. Integrability of Kδ and φδ is derived in `kernel_moment_integrable`. So the Bochner integrals in `hmatch` and `evec` are genuine, not junk zeros. The C02 universal all-a premise is discharged at G11C line 357 by `fun a => (cauchy_all_a … a).1`, which is the real-integral bound. It is not assumed. |
| 2b | Infinite-dimensional projection | PASS | V is a `Submodule.span` inside `Lp ℝ 2 (wmeas μ W)`, with no finite-dimensionality assumed on the ambient space. Closedness and completeness come from `FiniteDimensional.span_of_finite`. The projection is `starProjection` via `HasOrthogonalProjection`. C03's finite-dimensional-only definitions (`residual`, `gram`) are not used. Only `weighted_cauchy_schwarz` is used, and its source has `omit [FiniteDimensional ℝ E]`. Card pitfall 2 is respected. |
| 2c | Coverage: every n, m, rank; singular R | PASS | T5 has no rank hypothesis. n=0 is handled separately (Subsingleton); m=0 gives V=⊥. The T6 theorems `gramR_zero_imp_evec_zero`, `all_retained` (ENT-R0: R=0 ∧ e=0) and `duplicated_kernels` (ENT-SINGULAR: det R = 0, R(eᵢ − eⱼ) = 0, eᵢ = eⱼ, conclusion still holds) cover the singular cases. |
| 2d | R† is Moore–Penrose (T9) | PASS | `spectralPinv_penrose` proves all four Penrose equations for `CAS11C02.spectralPinvMatrix` and any Hermitian R. Identification with the Moore–Penrose inverse then follows from the standard uniqueness theorem, which is not formalized here. |
| 2e | Negative control genuine | PASS | One point, Dirac, MB, f=2, g=1, W=2, ε=1, φ=K=1. All budget and envelope hypotheses hold: D = 2ln2 − 1 ≤ 1, and z ≤ 2 on [1,2]. The moment is not matched (∫φδ = 1). R = 0, e = (1) ∉ range 0. Only the matching hypothesis is dropped, and the conclusion fails, so the hypothesis is necessary. |
| 2f | Nonvacuity genuine | PASS with note | All T5 hypotheses hold with f ≠ g, duplicated kernels, R ≠ 0 singular and e ≠ 0. Note: the witness uses m=0 (see N3). |
| 2g | Gram not reinterpreted as noise covariance | PASS | R is only `Matrix.gram` of the L²(W) residuals. No covariance reading appears anywhere. |
| 3a | Receipt integrity | PASS | For all 20 receipts I recomputed the sha256 of the `.source.lean`, `.stdout` and `.stderr` snapshots; all match the JSON (0 bad). Final source `lean/G11CWeightedEllipsoid.lean` sha256 `732645ad…6081` equals the compile_19 snapshot and AUTHOR_RETURN. `AxiomAudit.lean` sha `eb051538…` equals the compile_20 snapshot. Hashes of run_compile, statement_freeze_check, the sympy script and its stdout all match AUTHOR_RETURN. Failed attempts are kept: compile_07–10, 12, 15 and 16 have exit 1. Final compile_19 and audit compile_20 have exit 0. |
| 3b | Forbidden tokens | PASS | I grepped for sorry, admit, native_decide, axiom, set_option, implemented_by, extern, unsafe and csimp in `lean/` and `AxiomAudit.lean`. No hits (grep exit 1). |
| 3c | Statement freeze | PASS | `statement_freeze_check.out` reports ALL_MATCH 23/23. I also compared the T1–T9 headers by eye against FROZEN_TARGETS: identical. The declared deviations (`noncomputable abbrev`, `open Matrix`, unfrozen helper lemmas) are benign. |
| 4a | Independent recompile | PASS | I copied all seven sources to `g11-c_rerun/src` (shas re-verified) and rebuilt every import into `g11-c_rerun/imports` from source, in dependency order. From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` I ran `lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/<M>.olean $S/src/<M>.lean"`. All seven exited 0. The toolchain is Lean 4.31.0 (commit 68218e87); lake-manifest mathlib rev is `fabf563a…`. The only messages were 2 deprecation warnings, at lines 697 and 699. My G11CWeightedEllipsoid.olean sha256 `4324f9ed…` is byte-identical to the author's. |
| 4b | Own axiom audit | PASS | `g11-c_rerun/ReviewAudit.lean` uses a meta command that enumerates every constant in namespace G11C from module G11CWeightedEllipsoid, so the list cannot be incomplete. It found 51 constants: all definitions, instances, equation lemmas and theorems. Every one depends on exactly [Classical.choice, Quot.sound, propext] (exit 0). |

## Faithfulness detail

- **(A1)** The source requires D_H ≤ ε < ∞. Lean uses `Dext ≤ ofReal ε` with 0 ≤ ε, which is the same condition. Matching is ∫φₐδ dμ = 0 for every a in `Fin m`, with m arbitrary including 0.
- **(A2)** WEnvelope requires W measurable, W > 0 a.e., and z(1+ξz) ≤ W for every z in `uIcc f g` a.e. This is equivalent to the source's sup condition.
- **(A3)** Lean uses `Metric.infDist` in `Lp ℝ 2 (W dμ)`, and the proof shows it equals ‖k − P_V k‖. This is exact.
- **R and e** are defined exactly as in the source. R is also proved equal to ∫W rᵢ rⱼ dμ on Lp representatives.
- **(A4)** The statement is e ∈ range(toLin' R) and eᵀR†e ≤ 2ε, over all n, m and every rank.
- **(A6)** `mismatch_bound` holds for every c ∈ ℝᵐ with no matching hypothesis. It matches the source exactly.
- **Measure:** the result is proved for a general μ, plus the instance on `G11A.nu C`.
- **Strengthening:** the source assumes the observable integrals are finite; Lean derives this instead.
- **Inherited guard:** g must lie in the open domain. This comes from G11-A, matches CAS-11 ENT-DOMAIN, and is declared in the FROZEN "Discipline" section, so it is not silent.

## Blocking findings
None.

## Non-blocking notes
- **N1.** The freeze-before-compile evidence is file mtimes plus the receipt timestamps. T is untracked in git, so nothing stronger exists. Suggest committing FROZEN_TARGETS and SOURCE_RECOVERY before the proof receipts in future runs.
- **N2.** A boundary reference (g at 0, or at 1 for FD) is excluded through G11-A's open-domain guard. The source line S:83, "at physical endpoints the same statement follows by a limit", is not formalized here. It is correctly not claimed.
- **N3.** The nonvacuity witness has m=0, so the matching/projection step is trivial in that witness. The negative control has m=1 but is unmatched. My numeric check covers the matched case with m≥1, a nontrivial projection and e≠0 (270 cases). Optional improvement: add a Lean witness on a two-point space with m=1 matched, f≠g, P_V ≠ 0 and e ≠ 0.
- **N4.** `duplicated_kernels` takes K i = K j pointwise. A.e.-duplicated kernels still get range and ellipsoid from T5, but not the explicit det=0 statement. A.e. equality would be a slight generalization.
- **N5.** T9 proves the four Penrose equations. "Equals the Moore–Penrose inverse" then rests on standard uniqueness, which is not formalized.
- **N6.** Olean hashes depend on the `-R` root path. My rebuild with `-R src` gave different hashes for G11AIntegralBregman and FiniteGram; rebuilding FiniteGram with `-R` set to its original directory reproduced the author's `2bdf78a8…` exactly. My own rebuild is deterministic (same hash twice). This is not an integrity problem.
- **N7.** There are 2 deprecation warnings (`Matrix.toEuclideanLin_apply`); cosmetic.
- **N8.** The sympy ancillary is a finite symbolic export only (4 points, 3 kernels). It is correctly labelled as not a proof.
- **N9.** The author runtime is UNKNOWN or unattested, as AUTHOR_RETURN records. The review-model requirement (gpt-6-astra/ultra) is not met by this review either.

## VALIDATION_MATRIX scientific row (proposed text; I have not edited the file)
`G11-C | TEFF-A2 (A3)/(A4)/(A6), ENT-R0/ENT-SINGULAR/ENT-MISMATCH | Lean T1–T9 compiled fresh (4.31.0/fabf563a), 51/51 constants axioms ⊆ {propext, Classical.choice, Quot.sound}; independent mpmath 50-digit cross-check 270/270 matched PASS, 30/30 unmatched negative controls violate | PASS_WITH_NOTES (fresh review, claude-opus-5-5 self-reported) | scientific admission HOLD`

## Not proved / not claimed (always)
- **Scientific admission: HOLD.**
- Not covered:
  - physical certification of ε, of the envelope W (including the (A5) BE envelope), of the retained moments and of the channel kernels;
  - the endpoint/boundary-reference limit (g on ∂dom), and W = 0, W = ∞ or D = ∞;
  - the collision variant (A7) and the kinematic inverse;
  - any noise-covariance reading of R;
  - a formalized Moore–Penrose uniqueness;
  - Wolfram/Sage axes and any CAS_4AXIS status for G11-C;
  - the full CAS-11 parent or TEFF claim;
  - publication, merge or lifecycle acceptance;
  - a review by the requested gpt-6-astra/ultra model.

## Relevant paths
- `T/lean/G11CWeightedEllipsoid.lean`, `T/FROZEN_TARGETS.md`, `T/SOURCE_RECOVERY.md`, `T/AUTHOR_RETURN.json`, `T/raw/compile_19_main.json`, `T/raw/compile_20_audit.json`, `T/raw/AxiomAudit.lean`
- Scratch (in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g11-c_rerun/`): `src/`, `imports/`, `ReviewAudit.lean`, `ReviewAudit.out`, `numcheck.py`, `G11CWeightedEllipsoid.out`
