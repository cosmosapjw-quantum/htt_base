# G11-D — independent review (verbatim final report of a fresh read-only reviewer)

# G11-D fresh independent review: uncertain moment matching and measured entropy inputs (GR-CAS-11)

**Reviewer:** claude-opus-5-5 (Opus 5.5). I did not author this unit. This was a read-only review: no repository file was edited and no state-changing git command was run. Scratch files are only in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g11-d_rerun/`.

**Target:** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-11/g11d_uncertain_moment_entropy_v1_20261014/` (written T below).

## VERDICT: PASS_WITH_NOTES

- **Mathematics:** all 25 public declarations compile, including the frozen targets D1–D5. This was confirmed by an independent from-source rebuild of the whole import chain. Axioms are only `propext`, `Classical.choice`, `Quot.sound`.
- **Application:** INPUT_REQUIRED, which is correct per the card's pitfall. It does not block counting the mathematical unit.
- **Scientific admission:** HOLD.
- No blocking findings.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read | PASS | `unzip -p HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip …/tasks/G11-D.json`. lean_steps 1–4 map to D1, D2, D3, D4. Acceptance 1 maps to D2 vs D5, acceptance 2 to D4b plus `application_status`, acceptance 3 to FROZEN_TARGETS. The pitfall (only the application becomes INPUT_REQUIRED) is honoured. |
| 1b | Source hashes (SOURCE_RECOVERY) | PASS | Recomputed sha256 of TEFF_POSITIVE_BRIDGE.md (f04d96fe…), CAS-11.json (6588ac42…), DECISIONS.json (a05b3053…), POSITIVE_EXTENSION_DECISION.json/.md (8d2a2f4d…/d2d2f02a…) and TEFF_CLAIMS.json (9654e73e…). All equal the recorded values. CAS-11.json line 29 carries the TEFF hash. |
| 1c | Line citations | PASS | Every cited line says what is claimed. S:108-114 is (A6) with the "+"; S:116 is the confidence-set support-function sentence; S:104 is the acquisition protocol, including "Retained moments or the entropy of a fitted reference alone do not certify ε"; S:106 is the nested-improvement rule; S:93-98 is (A5); S:102 is "T_max … not inferred"; S:41-46 is (A1); S:53/58 is the L²(W dν) norm; S:143 is the joint residual set; S:220 is the per-moment box. C:46/61/82, C:70 and C:76/95/111 hold the quoted strings. R:385-389 is POS-F01. Rmd:25 is the A6 sum correction. D:537-555 is TEFF-A4. |
| 1d | Freeze timing | PASS (note N1) | `FROZEN_TARGETS.md` mtime is 02:55:31Z and `raw/FROZEN_TARGETS.sha256` was stamped 02:55:38Z. Its hash 83c47151… equals the current file. The first G11-D proof compile (compile_10) started 03:01:15Z. The only earlier runs were the 7 unchanged dependency rebuilds (02:50–02:51Z) and probe01, which is `#check` only (read: API names only, no target statements). Both are disclosed in FROZEN_TARGETS. |
| 1e | Frozen statement vs Lean | PASS | I re-ran the author's `statement_freeze_check.py` on a scratch copy: 22/22 MATCH, exit 0. My own check confirms that the elided `uncertain_bound_coverage_prob` has hypothesis text identical to `uncertain_bound_coverage` plus `[IsProbabilityMeasure P]`. The only extra helpers are `coeFn_combo` and `nu_ae_energy_pos`. |
| 1f | D1: split identity with nonzero Δm kept | PASS | `moment_split` states ∫kδ = ∫(k − c·φ)δ + c·dm, where dm_a = ∫φ_a(f−g) carries the same δ sign. There is no matching hypothesis anywhere in D1/D2 except D2f. `combo_norm_sq` identifies ‖k − c·φ‖² in Lp with ∫W(k − c·φ)², which is the source (A6) norm. Numerically, the identity held to 1e-10 in 8000 random discrete cases. |
| 1g | D2a/D2b: deterministic bound plus support function | PASS | The bound is the triangle inequality plus Cauchy–Schwarz, with ‖z‖² ≤ 2ε taken from reviewed G11-C `z_norm_sq`. `suppAbs` is sup|c·d|, which is the correct symmetric form because the left side is an absolute value. `BddAbove` guards the `sSup` junk value, and S is nonempty because dm ∈ S. **Lean probe R1:** the exact printed (A6), with S = {dm} and σ = |c·dm|, is a one-line instance of `uncertain_bound`; it compiles. |
| 1h | D2c: box support | PASS | `box_support` gives σ_box(c) = Σ\|c_a\|r_a with attainment, matching S:220. Numerically, brute force over box vertices matched to 1e-10. **Lean probe R2:** a box-instantiated (A6) compiles. Numeric D2a/A6/box check over 8000 cases (MB/BE/FD; W = segment supremum × inflation in [1, 1.5]; ε ≥ D): max(LHS − RHS) = −0.0404, so no violations. |
| 1i | D2d/D2e: joint form | PASS | Hand check: e_j = ⟨r_j, z⟩ + Σ_b B_jb Δm_b, so e − BΔm is the (A4) residual vector, and a·e = a·(e − BΔm) + (Bᵀa)·Δm. The zero-channel branch (n = 0) is handled. Numerically (600 cases, 120 with a kernel inside V so R is singular): max(qᵀR⁺q − 2ε) = −0.0136 and max D2e violation = 4.4e-16, i.e. roundoff. An apparent violation in my first run was traced to my own numerics: N = m makes R ≈ 1e-30 analytically 0, and numpy pinv amplified 1e-16 noise. Confirmed separately. |
| 1j | D2f: exact matching special case | PASS | S = {0} reduces to the reviewed `G11C.single_kernel_dist_bound` and `weighted_residual_ellipsoid`, which reuses G11-C as the card requires. |
| 1k | D3a/D3b: span enlargement | PASS | φ = φ'∘ι gives V ≤ V', and infDist is antitone in the set, so the distance decreases. ι may be any map, which is a generalisation. |
| 1l | D3c: premises separated | PASS (note N2) | The common W, the refined budget ε' for (f, g'), ε' ≤ ε, and exact matching of the enlarged family are all explicit premises. None is derived. |
| 1m | D3d: discharge | PASS | Calls the reviewed `G11A.nested_budget` (Pythagorean form D(f‖k) ≤ D(f‖g)). Its convexity, domain and derivative side conditions are discharged inside the proof (`convexOn_hS`, `dom_subset_cdom`, `hasDerivAt_hS`), not assumed. Exact matching f vs k is the source's own hypothesis, as stated. |
| 1n | D4a/D4a'/D4c: envelopes | PASS | For ξ ≥ 0, z(1+ξz) is monotone on [0, F], so W = F(1+ξF). FD: z(1−z) ≤ 1/4, checked numerically (max = 0.25). Planck: W = F_b(1+F_b) with BE ξ = 1, b > 0 as an input, and both f and g under the envelope (TEFF-A4 conditions). E > 0 holds ν-a.e. (`nu_ae_energy_pos`). Numerically, sup over 0 ≤ z ≤ F of z(1+z) − F(1+F) = 0. |
| 1o | D4b: negative control | PASS (genuine) | μ = δ_true + δ_false, g ≡ 1, φ = 1_true, f = (1, e^L). This g is exactly the MB I-projection of f onto {log g ∈ span φ} with matched moment, so it is a *fitted* reference with fixed entropy. D(f‖g) = e^L(L−1)+1 exceeds every ε; numerically 8.39, 41.2, 1.8e6, 2.0e46 for ε = 0, 1, 10, 100. ε is therefore not derived from the fitted entropy or the moments, and D4b's control demonstrates that this is impossible in general. |
| 1p | D4d: necessity and non-vacuity | PASS | f = 2, g = 1, W = 2, MB, D = 2ln2 − 1 ≈ 0.386 ≤ 1, dm = 1 ≠ 0. Equality is attained and the bound without the support term is false (1 ≤ 0 fails). |
| 1q | D5: coverage kept separate | PASS | Deterministic D2 is applied pointwise on the intersection of the three declared good events, and the probabilities are combined only by the union bound (αW + αε + αm). There is no independence or product of coverages. Outer measure means no measurability is needed. The truncated ENNReal subtraction is correct for the probability form. ε̂ is an upper confidence bound used only on its coverage event. **Lean probe R3:** D5 instantiated with α = 0 on a one-point Ω compiles, so its hypotheses are jointly satisfiable. |
| 2 | Assumes-conclusion / vacuity | PASS | No hypothesis restates a conclusion. Non-vacuity was established by D4d, D4b and my R1–R3. |
| 3a | Lean source and receipt hashes | PASS | lean a7f1e068…, AxiomAudit 43747e30…, run_compile.py 12a29e3a… and SOURCE_RECOVERY 181ed606… all match AUTHOR_RETURN. All 12 receipts pass three checks: the `.source.lean` snapshot, stdout and stderr hashes match the json. Every dependency source still hashes to its receipt. compile_11 source is byte-identical to `lean/`. compile_12 source equals `raw/AxiomAudit.lean`. |
| 3b | Exit codes and failed attempts | PASS | Dependencies 01–07 exited 0. Probes 08/09 exited 1 by design (unknown-name `#check`). Failed main attempt compile_10 (exit 1) is retained. My diff shows it differs only in three API-name fixes (lines 114, 427, 572). compile_11 and compile_12 exited 0. |
| 3c | Forbidden constructs | PASS | grep of `lean/G11DUncertainMoment.lean` for `sorry`, `admit`, `native_decide`, `^axiom`, `set_option`, `maxHeartbeats`, `opaque`, `implemented_by`, `extern`: no hits. `sorryAx` count in the audit stdout is 0. All 25 lines read `[propext, Classical.choice, Quot.sound]`. |
| 4 | Independent recompile | PASS | Copied all 8 sources (hashes equal to recorded) to `g11-d_rerun/src`. From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain v4.31.0, mathlib rev fabf563a…) I ran `lake env bash -c "LEAN_PATH=<scratch>/imports:$LEAN_PATH lean -R <scratch>/src -o <scratch>/imports/<M>.olean <scratch>/src/<M>.lean"` for each module in dependency order. All exited 0. The only output for G11D is the disclosed unused-`hk` linter warning. My own `ReviewAudit.lean` (probes R1–R3 plus `#print axioms` for all 25 public theorems and the 4 definitions) exited 0, with 29/29 lines giving only the three standard axioms. |

**Olean hashes:**
- Five of my oleans are bit-identical to the author's.
- Three differ (FiniteGram, G11AIntegralBregman, G11DUncertainMoment). The cause is the path: recompiling FiniteGram with `-R` set to its original directory reproduces the author's hash 2bdf78a8… exactly. My build is also deterministic: two rebuilds gave the same 47c68376….

## Blocking findings

None.

## Non-blocking notes

- **N1:** `SOURCE_RECOVERY.md` says "written before … any proof compile", but it cites compile_01..07 and its mtime (02:54Z) is after them. Those were unchanged dependency rebuilds, not G11-D proofs. Suggested wording: "before any G11-D proof compile".
- **N2:** D3c requires W to be an envelope only for the refined pair. The coarse side `√(2ε)·dist(K,V)` is a number, not a claim about (f, g). This is logically a strengthening. However, no single theorem composes D3d's discharged budget (ε' := ε) into D3c. It is trivial to do but not done. D3d yields no strict decrease (that would need D(k‖g) > 0), and AUTHOR_RETURN does not claim one.
- **N3:** D5 keeps W, φ, k and K data-independent. A data-estimated envelope parameter b(ω) is outside D5. This is consistent with the source requiring b/T_max as independent prior information, but should be stated if a data-driven envelope is ever proposed.
- **N4:** The domain branch is inherited from G11-B/C: the reference g must be in the open domain, while f may be at endpoints. The source says "admissible f, g", with endpoints handled "by a limit". This narrowing for g at endpoints was already accepted in G11-C. It is physically harmless for a Planck-like reference (g > 0).
- **N5:** The TEFF-A4 condition "no singular condensate is included" (D:547) is not listed in SOURCE_RECOVERY. It holds implicitly because f is a function, not a measure. Suggest recording it.
- **N6:** `nested_budget_discharge` keeps an unused `hk : Measurable k` to match the frozen signature. This is a slightly superfluous premise, not a weakness.
- **N7:** The external input fields are recorded in prose (AUTHOR_RETURN `application_missing_inputs`, SOURCE_RECOVERY §3). Their typed form exists only implicitly in the D5 signature (ε̂, αε, S, αm, W/b, K, φ). A machine-readable field list (name, type, unit, required coverage) would make "exact external input fields" fully literal.
- **N8:** T is untracked in git (`??`). The oleans are not committed (stated). `observed_runtime` is UNKNOWN (stated).
- **N9:** Earlier numeric hint is not a defect: the apparent D2d violation in my first numeric pass was a numpy pinv artifact (R ≈ 1e-30, residual ≈ 1e-16). It is recorded here only so that nobody re-reads `numcheck.py` output out of context.

## Counting judgement

Count G11-D as a **FORMALLY_CHECKED_SCOPED** mathematical unit (review PASS_WITH_NOTES), with **application_status = INPUT_REQUIRED** carried separately.

- Card pitfall: missing measurements make only the application INPUT_REQUIRED and do not stop the mathematics. The author did exactly that.
- No ε is derived from fitted entropy or moments anywhere, and D4b's control demonstrates that this is impossible in general.
- The W witnesses (D4a/a'/c) were recovered from the source envelopes. The ε, S, b and kernel inputs are recorded as external.

## Not proved / not claimed

- **Scientific admission: HOLD.**
- Any actual acquisition: certified ε or ε̂ with coverage, a simultaneous moment confidence set, a certified b/T_max with the fugacity check, actual channel kernels and their L²(W dν) membership.
- Nested-divergence decrease under uncertain matching; Paper II (29)–(31) beyond `G11A.nested_budget`.
- Closed-form non-box (e.g. ellipsoidal) support functions.
- Independence-based coverage; measurability of the coverage events.
- Planck-envelope integrability and infrared/exponential tail claims (TEFF-A4 integrability).
- Endpoint references g ∉ dom.
- (A7) collision variant, the kinematic inverse, and Proposition B.
- Wolfram/SymPy/Sage axes and CAS_4AXIS status.
- The full CAS-11 parent theorem and TEFF claim admission.
- Publication, merge or lifecycle acceptance.

## Suggested validation-matrix scientific row

There is no `SCIENTIFIC_CONTRACT.md` or `VALIDATION_MATRIX.md` at the repo root; the governing contract is CAS-11.json plus TEFF. Not written by me:

`G11-D | (A6) uncertain-moment bound + support fn + joint e−BΔm ellipsoid + span monotonicity + envelopes + union-bound coverage | Lean kernel PASS (independent rebuild, 3 std axioms), numeric D1/D2a/D2c/D2e PASS (8000+600 cases), negative controls D4b/D4d genuine | application INPUT_REQUIRED | review PASS_WITH_NOTES (claude-opus-5-5, 2026-10-14) | scientific admission HOLD`

## Files

- Reviewed unit: the T directory above (`lean/G11DUncertainMoment.lean`, `FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `raw/compile_*`, `raw/AxiomAudit.lean`).
- Reviewer scratch, in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g11-d_rerun/`:
  - `src/` — copied sources
  - `imports/` — rebuilt oleans
  - `ReviewAudit.lean` and `ReviewAudit.out` — probes R1–R3 and `#print axioms`
  - `numcheck.py` — numeric checks
  - `<Module>.out` — compile outputs
  - `rep/` — olean determinism and path tests

