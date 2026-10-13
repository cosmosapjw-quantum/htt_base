# G10-B — independent review (verbatim final report of a fresh read-only reviewer)

## G10-B fresh independent review: Gaussian compression law, block rotation and KL

**Verdict: PASS_WITH_NOTES.** No blocking findings. Proof status only. Scientific admission: **HOLD**.

- Reviewer model: claude-opus-5-5 (Claude Opus 5.5). I did not author G10-B.
- Author model: recorded as `UNKNOWN` (not attested).
- I edited no repository files and ran no state-changing git commands. All scratch work is in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g10-b_rerun/`.

T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/g10b_gaussian_kl_v1_20261013`

---

### Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read first | done | `unzip -p …/tasks/G10-B.json`. Scope: C01/C03 counterexample plus actual Gaussian pushforward, equal law and KL. Four lean_steps. Pitfalls: no SPD formula on singular covariance; no inflating marginal invariance to joint invariance. |
| 1a | SOURCE_RECOVERY citations | PASS | Every hash recomputed and matches: CAS-10.json `03dd5c3c…`, COMMON_SPEC `4714827e…`, INFORMATION_LIMIT_THEOREMS `775b7d15…`. Cited lines checked: contract 39-49 (exact_statement, isotropic-blocks assumption), 79 (INFO-ANISOTROPIC), 112 (C03 definition); theory 42 (p→p′), 74 (I6), 109-117 (§4, I9), 119-124 (Theorem II, I10), 127 (proof sketch), 131 (scope limits). The Mathlib-gap claim is true at the pin: only `KullbackLeibler/{Basic,ChainRule}.lean` mention `klDiv`, with no prod, pi, map or Gaussian lemma. |
| 1b | FROZEN_TARGETS predates first proof compile | PASS (mtime evidence only) | FROZEN mtime 2026-10-13 20:56:24 KST (11:56 UTC). Only receipts 01-03 (reused imports, 11:54 UTC) precede it. Probe P1 ran at 11:56:59 UTC, after the freeze. First main compile (receipt 10) ran at 21:00:38 UTC. sha `87b73fe3…` matches AUTHOR_RETURN. T is untracked in git, so there is no commit timestamp. |
| 1c | Faithfulness to card, CAS-10 C03, Theory II and (I9)-(I10) | PASS | Details below. |
| 1d | Key identities recomputed independently | PASS | **sympy:**<br>• ∫ log(p_a/p_b)·p_a dx = (a−b)²/(2v), which is K1.<br>• Rᵀ R = I, det R = 1, R p = p′.<br>• ½·\|p−p′\|²/σ₃² = 225H²/(64σ₃²), which is A5.<br>• diag(T) = (3√6H/16)·E1; tr E1 = 0; ‖E1‖_F = 1.<br>• Powers = (25/16, 9/16, 49H²/16, 225H²/64, 27H²/128), with T power from both tCoord² and ‖Tdiag‖_F².<br>**Monte Carlo** (N = 10⁶, 13-dim data, σ = (0.7, 1.1, 0.9, 1.3, 0.8), H = 1):<br>• KS p-values for the five powers: 0.64 / 0.73 / 0.10 / 0.54 / 0.22.<br>• A nonlinear joint statistic of the powers differs by 0.81 SE.<br>• MC KL = 2.0806 ± 0.0020 against exact 2.08025.<br>(A first seed with N = 4·10⁵ gave about 2σ deviations; the rerun with a new seed and N = 10⁶ is consistent.) Script: `scratchpad/g10-b_rerun/numcheck.py`. |
| 1e | Recorded adjustments | PASS | Generalisations, all acceptable:<br>• T1–T4 and B2 hold for any σ, including σ = 0 (the theory has σ_j > 0).<br>• The A-series holds for arbitrary z0, m, z1, t and any real H; positivity needs H ≠ 0, where the theory fixes H > 0.<br>• A8 needs only σ₃ = 0.<br>Weakenings: none silent. The KL targets keep ∀j σ_j > 0, as in (I9).<br>B2 route change (direct proof instead of P12) is recorded; the statement is byte-identical to the frozen one. |
| 1f | Negative controls are genuine | PASS | **A7:** full laws differ for H ≠ 0, via B2 at coordinate pIdx.<br>**A6:** KL > 0 and KL ≠ ∞.<br>**A8:** σ₃ = 0 gives ∞ because absolute continuity fails on the set {x_pIdx = 15H/8}, which has mass 1 under one law and 0 under the other. `klDiv_of_not_ac` is used; the SPD formula is not.<br>**N1:** a real counterexample. With anisoW (variance 1 on p₀, 0 elsewhere) and μ = 0, coordinate p₁ of R·x equals x_p₀, which has law N(0,1). The target law has p₁ with law N(0,0) = δ₀. The two laws are distinct, shown via `gaussianReal_ext_iff`. |
| 2 | No hypothesis assumes the conclusion; no vacuity | PASS | My own Lean instances compile:<br>• `full_kl_eq` at H = 1, σ ≡ 1 gives `ofReal(225/64)`.<br>• `full_kl_singular_branch` with σ = (1, 1, 1, 0, 1) gives ∞.<br>• `full_laws_ne` at H = 2, σ ≡ 3.<br>• `compressed_laws_equal` at σ ≡ 0.<br>• K1 sanity: KL(N(0,1) ‖ N(1,1)) = ofReal(1/2).<br>The K1 hypothesis v ≠ 0 is necessary. I proved `klDiv (gaussianReal 0 0) (gaussianReal 1 0) = ∞`, while the formula would give `ofReal 0 = 0`.<br>`obsLaw` is definitionally the `Measure.pi` of `gaussianReal (μ i) ⟨σ_{i.1}², _⟩` (checked by `rfl`). `blockDim = (1,3,1,3,5)` and `card Idx = 13` (checked by `decide`). `rotP 3 = CAS10C03.R` and `rotP 4 = 1` (checked by `rfl`). |
| 3a | sha256 of sources, receipts and imports | PASS | All files in the AUTHOR_RETURN `sources` and `imports` blocks match. For all 13 receipts, the snapshot source, stdout and stderr hashes match their JSON. Final source `1993257d…` equals the compile_12 snapshot. Reused sources are byte-identical to the accepted originals (C01 `3cf35a9a…`, C03 `2ab3b8b9…`, P12 `5a6ce15d…`). C01 and C03 are recorded as CAS_4AXIS_PASS with PASS_FINITE_COMPONENT_REVIEW; P12 as PASS_WITH_NOTES. |
| 3b | Exit codes; failed attempts kept | PASS | Exit 1 kept for 05 and 06 (P2), 08 (P3), 10 and 11 (main), with 5, 1, 5, 7 and 1 errors. Diff from 10 to 12 touches proof lines only: the `rotP_orthogonal` tactic, the A2 `show`, the A8 set spelling and the N1 `change`. No statement changed. Exit 0 for 12 (main) and 13 (audit). |
| 3c | Axioms | PASS | Author audit: 51/51 `[propext, Classical.choice, Quot.sound]`.<br>My audit enumerated **every** constant in module `G10BGaussianKL` with `Lean.collectAxioms`, including instances, `eq_n` and `match` auxiliaries: **92 constants, 0 outside {propext, Classical.choice, Quot.sound}**. |
| 3d | Forbidden tokens in T/lean and AxiomAudit | PASS | `grep -w` for sorry, admit, native_decide, axiom, set_option, sorryAx, opaque, implemented_by, extern, unsafe, partial: none. No `@[...]` attributes. Two benign `IsProbabilityMeasure` instances. |
| 4 | Independent recompile | PASS | Copied the four sources to `scratchpad/g10-b_rerun/src`. Rebuilt every import from source with the pinned toolchain (Lean 4.31.0, mathlib `fabf563a…`, confirmed in the `viii_oracle` manifest), using `lake env bash -c "LEAN_PATH=<scratch olean>:$LEAN_PATH lean -R <src> -o <scratch>/<M>.olean <src>/<M>.lean"`:<br>• CAS10C01, CAS10C03, P12GaussianLaw: exit 0. Their oleans are **byte-identical** to `T/raw/imports`.<br>• G10BGaussianKL: exit 0, 7.1 s, 6.7 GB RSS. Stdout is identical to compile_12 modulo the path (10 lint warnings).<br>Frozen-signature conformance: `ReviewAudit.lean` and `ReviewFrozen2.lean` restate each frozen target verbatim (T1, T1b, T2, T3, T4, T4b, K1, K2, K3, B1, B2, A1, A4, A5, A8, N1, X2, X3) and close it by the author's theorem. Both exit 0. |

### Faithfulness details (check 1c)

- **(I9) observation law.** Independent X_j ~ N(μ_j, σ_j² I_{d_j}) is equivalent to the product of all 13 coordinates with variance σ_{j(i)}². `obsLaw` encodes exactly that. B1 proves it equals `multivariateGaussian` with the block-diagonal covariance diag(σ_{i.1}²).
- **Joint law, not marginal (pitfall 2).** T1 is a full measure equality on `Idx d → ℝ`. It is obtained from `charFun_eq_pi_iff`, whose pin statement is "∀t, charFun(ν.map toLp) t = ∏ charFun(μ i)(t i) ↔ ν = Measure.pi μ", applied to ν = the whole pushforward. T3 is the joint law of all J powers. The pitfall is respected.
- **Isotropy is used exactly where needed.** It enters only at `hquad`, where σ_j² is factored out of the sector sum through `coordVar` being constant on each sector together with `sum_sq_blockMap` for Rᵀ. N1 shows the step fails without it.
- **Theorem II, compressed laws and tests.** A3 states the joint compressed law. A4/T4 cover every measurable powers-only statistic, so every randomized test with values in [0,1]. T4b gives "size ≤ α implies power ≤ α" in the right direction: size under the geodesic first tuple, power under the accelerated second tuple, since `blockMap rotP (ofMean first) = ofMean second` (A2).
- **(I10) KL.** A5 is KL(first ‖ second) = ofReal(225H²/(64σ₃²)), with direction D(P_μ ‖ P_μ′). A5b ties it to the accepted `CAS10C03.KLQuadratic`, which is card lean_step 4.
- **Singular branch (pitfall 1).** A8 is separate from the SPD formula.
- **C03 equal-covariance KL and blockwise rotation invariance.** Both are proved, and the measure-theoretic step is proved rather than cited, as the contract requires.

### Self-proved Mathlib-gap lemmas: genuinely proved and correctly stated

- **`klDiv_map_of_measurableEmbedding`** (finite μ, ν). Absolute continuity is transferred both ways via `f '' s`. The non-ac branch gives ∞ on both sides; the ac branch uses `rnDeriv_map` and `lintegral_map`. Restricting to finite measures is correct, because `klDiv`'s mass terms `ν.real univ − μ.real univ` are preserved under map.
- **`klDiv_prod` (probability measures only).** This restriction is correct: for general finite measures the mass terms break additivity. The proof goes via `compProd_const`, the chain rule `klDiv_compProd_eq_add`, a swap embedding and `klDiv_compProd_left`. Top values in ℝ≥0∞ are handled by the chain-rule lemma itself.
- **`klDiv_pi_fin` / `klDiv_pi`.** Induction via `piFinSuccAbove`; the empty case (dirac, KL 0 = empty sum) is handled. The `X : Type` universe restriction is harmless here.
- **K1 `klDiv_gaussianReal_same_var`.** Explicit `rnDeriv`, then llr = ((x−b)² − (x−a)²)/(2v), then integrability via an affine form, then `klDiv_of_ac_of_integrable`. This is the actual relative entropy (`klDiv` is defined through `llr = log rnDeriv`).

### Blocking findings

None.

### Non-blocking notes

1. **Freeze provenance.** FROZEN_TARGETS' "Origin" paragraph says "authored fresh in this run; T did not exist". This is literally inconsistent with the resume. SOURCE_RECOVERY reconciles it: the paragraph refers to the earlier interrupted attempt. Evidence that the freeze predates the proof is file mtime only, since T is untracked by git. Suggested fix: commit T, or append an origin-correction note to SOURCE_RECOVERY or AUTHOR_RETURN rather than editing the frozen file.
2. **B2 route and P12 import.** The FROZEN B2 row says "via P12 law_eq_iff". The actual proof uses 1-D marginals (`measurePreserving_eval` plus `gaussianReal_ext_iff`, valid also for v = 0). This is a real proof of the same statement, equivalent to the P12 special case with common diagonal covariance through B1. P12 is imported and compiled but unused (dead import); harmless.
3. **N1 uses degenerate weights.** N1 is a proof-route control with degenerate anisotropic weights (variance 0 on 12 coordinates). A nondegenerate example would be cleaner. My Monte Carlo with nondegenerate sector-p variances (1,4,1) shows the compressed P_p law actually differs (KS p ≈ 0). That supports the contract's INFO-ANISOTROPIC locus but is not formalized, and is correctly listed as not targeted.
4. **Card tool_tasks not run in T.** Wolfram/xAct, sage_singular and sympy were not run for G10-B. Only Lean receipts exist; the scalar certificate is inherited from C03's 4-axis pass. My sympy and Monte Carlo checks above partially cover this gap; they are not package receipts.
5. **E1 basis completion.** Completion of E1 to an orthonormal trace-free basis is not formalized. No law or KL result depends on it, because they hold for arbitrary t. It affects only the coordinate identification of the explicit T-sector mean (X2/X3).
6. **"Fixed conditioning".** Encoded as the absence of any conditioning variable. This is a documented interpretation consistent with the contract's "fixed observer; no auxiliary interior input".
7. **KL hypotheses.** K3 and A5 require all σ_j > 0, matching the theory. The case σ_j = 0 with σ₃ > 0 and j ≠ 3 is not targeted.
8. **Tests and integrals.** A Theorem II application-level "size ≤ α implies power ≤ α" is not packaged; it is immediate from A2 and T4b. Externally randomized tests reduce to measurable φ = E_U ψ. The Bochner convention for non-integrable φ (both sides 0) is harmless because the laws are equal.
9. **Cosmetic.** Lint warnings (unused section variables, an unused simp argument, unnecessary `<;>`).
10. **Olean hash.** The main olean hash differs between author and reviewer builds (`f219e5b6…` vs `31cadbde…`, 48 bytes), most likely from the embedded path. Import oleans are byte-identical. Not a proof issue.

### Not proved / not claimed (always)

- Scientific admission: HOLD. Publication admission: not claimed.
- Physical admissibility or same-matter realization of the tuples (owned by C01/C02/G10-A).
- Real-survey equal law, masks, cross-block errors, priors.
- Whether anisotropic noise makes the compressed laws differ (only the N1 proof-route control is proved).
- Gaussian KL for unequal covariances, or singular covariances beyond A8.
- Orthonormal-basis completion of E1.
- Uniform consistency, minimax sharpness, and the Φ(−|Δ|/(2σ_p)) remark.
- Any conditioning operator.

### Suggested VALIDATION_MATRIX scientific row (not written by me)

`G10-B | scientific | PASS_WITH_NOTES (fresh independent review, claude-opus-5-5) | joint-law pushforward T1/T3, actual klDiv A5 = 225H²/(64σ₃²), singular A8 = ∞, N1 control; 92/92 constants clean axioms; independent recompile exit 0; sympy + MC (N = 1e6) agree | notes: freeze evidence mtime-only, P12 unused, tool_tasks Lean-only, E1 completion open | scientific admission HOLD`

### Relevant files

- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/g10b_gaussian_kl_v1_20261013/lean/G10BGaussianKL.lean`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/g10b_gaussian_kl_v1_20261013/FROZEN_TARGETS.md`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/g10b_gaussian_kl_v1_20261013/SOURCE_RECOVERY.md`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/g10b_gaussian_kl_v1_20261013/AUTHOR_RETURN.json`

Reviewer artifacts in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g10-b_rerun/`:
- Lean: `ReviewAudit.lean`, `ReviewFrozen2.lean`
- Logs: `audit.stdout`, `frozen2.stdout`, `main.stdout`
- Numerics: `numcheck.py`
- Oleans: `olean/`
