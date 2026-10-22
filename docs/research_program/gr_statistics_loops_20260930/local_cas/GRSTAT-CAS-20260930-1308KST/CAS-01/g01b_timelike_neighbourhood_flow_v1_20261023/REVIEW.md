# G01-B — independent review (verbatim final report of a fresh read-only reviewer)

# G01-B independent review: `g01b_timelike_neighbourhood_flow_v1_20261023`

**Verdict: PASS_WITH_NOTES.** The unit passes at chart level. I found no blocking issue. Scientific admission stays HOLD.

**Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`). This was a fresh, read-only review; I did not author the unit. I edited no repository file and ran no state-changing git command. Scratch files are only under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g01-b_rerun/`.

T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/g01b_timelike_neighbourhood_flow_v1_20261023`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read | PASS | `unzip -p …/HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip …/tasks/G01-B.json`: scope, 4 lean_steps, 4 acceptance items, 2 pitfalls (no uniform radius; local flow must not become global completeness). |
| 1a | Source hashes | PASS | Recomputed sha256 matches every citation: OPTICAL_THEOREMS `5ae2b6a6…8c21`, CAS-01.json `9f1bbb01…9b57`, COMMON_SPEC `4714827e…97`, SOURCE_SIGNATURE `ec2fc840…210a`, C04 Main.lean `a24b3499…9b7` (both `completion/lean` and `rerun_20261003/lean`), SOURCE_RECOVERY `9f8372fd…5fa`, FROZEN_TARGETS `28765a3d…e940`, lean `ea2359cd…2ec5`, AxiomAudit `bd2f2cc2…49c8`, run_compile.py `2107078a…9ec7`. OPTICAL and CAS-01.json at card snapshot `a30d84c7` hash to the same values. |
| 1b | Line citations | PASS | OPTICAL:9 (setting), 147 (Thm 3), 149–154 (Eq. 17 proof), 156 (scope limits). CAS-01.json:110 (C04 "not an existence theorem") and :255 (open obligation). Main.lean:96, 144, 163, 390, 492/494/496/498/504/513 all point at the named declarations. |
| 1c | Frozen before first compile | PASS (mtime evidence only) | FROZEN_TARGETS mtime is 18:03:10Z. compile_01 (an import-only C04 build) started 18:03:15Z. The first proof compile, compile_02, started 18:10:07Z. The directory is untracked in git, so there is no commit anchor. |
| 1d | Final statements equal frozen statements | PASS | `diff compile_02.source compile_03.source` shows proof-script changes only (eval_eta, finsetSum rename, G_line, normSq hterm, covDeriv field_simp, T14 redundant `ring`, N3 `set`). No statement changed. My audit `#check` of T14 matches the frozen text; `let` is displayed as `have`. |
| 1e | Card step 1: regularity, value and 1-jet premises | PASS | `NormalChartMetric` has ContDiff n, symm, `G 0 = η`, `HasFDerivAt G 0 0`, which are exactly the source proof's facts (OPTICAL:149). The seed is the accepted C04 `fullSeed`; v^b = u^b + c⁻¹ε_b Q_ab x^a = u^b + c⁻¹η^{bd}Q_ad x^a, which is Eq. (17). |
| 1f | Card step 2 / T1–T6: open set, ball, C^n positive root, unit, future | PASS | T1 is `isOpen_lt ∩ isOpen_lt`. T2 at 0 gives g(u,u)=−1<0 and g(u,e0)=−u⁰<0. **T3 gives an actual ∃ε>0 ball ⊆ N** (acceptance #1 met; ε depends on the data). T4 is ContDiffOn n for every n via `ContDiffAt.sqrt` at N>0, so the square-root normalization is genuinely C^n. T5 is exact, from eval_div_both and sq_sqrt. T6 holds by positivity of √. |
| 1g | Card step 3 / T7–T9: link to C04 | PASS | T8 is proved on a curved chart; the only metric premises used are `G 0=η` and `∂G(0)=0`, plus `Q u=0`. T9 uses the imported `fullNormalized_coordinate_derivative` and `fullNormalized_origin` unchanged. N2 shows the flat-chart field *is* the C04 field. |
| 1h | Card step 4 / T10–T14: covariant 1-jet, flow, observables | PASS | **T10:** ∇_aU_b(0)=Q_ab for U=c·u; this keeps prior review repair (i). **T11:** Picard–Lindelöf local integral curve through every x0∈N that stays in N. **T12:** local flow, eventually in 𝓝x0×𝓝0. **T13:** local uniqueness via a local Lipschitz bound. No global or completeness statement appears; pitfall 2 is respected. |
| 1i | T14: same field, same flow (acceptance #2) | PASS | One `unitField G u Qd c` / `physField G u Qd c` with Qd = Q(B(S,u),W,u) from Eqs. (8), (9), (11). It satisfies: open N, ball, C^n, unit, future, value, coordinate 1-jet, ∇U(0)=Qd, integral curves in N, and Z, H by Eq. (4). The (Z,H) proof chains `covDeriv` → `Q_symmetric_part` → `eval_B_null` (g(K,K)=0) → `general_sourceward_harmonics`. Hypotheses are exactly Thm 1's admissibility (shell, ζ0≥1, STF) and Thm 2's fibre (W skew, Wu=0). |
| 1j | Quantifiers, signs, units, branches | PASS | **Quantifiers:** ∀ admissible data, ∀ W, ∀ C^n normal-chart G, ∀ continuous T with T(0)=e0. **Signature:** (−+++). **Positive root:** only the √ branch, and ζ0≥1 excludes the past branch. **Units:** c>0 carries the c-factor (∇u=Q/c, ∇U=Q). **Recorded adjustments are all strengthenings:** future is defined relative to any continuous T (not only a true time orientation), nondegeneracy away from 0 is not assumed, and the claim holds for every n≥1 rather than only smooth. I found no silent weakening. |
| 1k | Negative controls | PASS (genuine) | N3 sits inside T14's own admissible family: ζ=(1,0,0,0), h0=λ/3, h2=diag(2λ/3,−λ/3,−λ/3) (traceless), W=0, Minkowski. By hand: B=S+h0η, B11=λ, Bu=0, so Q=B. With λ=2c/r and x=(0,r/2,0,0) (in the sup-norm r-ball) the seed is (1,1,0,0), which is null, so x∉N. A python recheck gives g(v,v)=0.0 for three (c,r) pairs. Pitfall 1 is respected: no uniform radius is claimed. N1 is the flat witness. |
| 2 | No assumed conclusion; non-vacuity | PASS | The premise `Qu=0` is derived inside T14 from the fibre (`Q_right_null` with `B_unit`), not assumed. `HasFDerivAt G 0 0` is the source's normal-coordinate premise, not the conclusion. My audit instantiates the **full T14** on two charts: the Minkowski chart at n=∞ (`((⊤:ℕ∞):WithTop ℕ∞)`), and a **curved** chart `Gc x = η + (x0·x0)•I`. For Gc I proved `NormalChartMetric Gc n` for all n and `Gc ![1,0,0,0] ≠ η`. Both instantiations compile, so the curved-chart hypotheses are satisfiable. |
| 3a | Receipts, exit codes, failed attempts | PASS | Every compile_* source/stdout/stderr sha recomputes to its recorded value. Exit codes are 01=0, 02=1 (failure kept, errors at 241/256/361/455/513 as disclosed), 03=0, 04=0. All stderr files are empty. compile_03.source equals the lean file byte for byte. |
| 3b | Forbidden constructs | PASS | `grep -nE "sorry\|admit\|native_decide\|^\s*axiom\|set_option\|sorryAx\|implemented_by\|extern\|unsafe\|opaque\|@\["` over the lean file and the imported C04 copy found nothing (rc=1). |
| 3c | Axioms | PASS | Author: 39/39 use `[propext, Classical.choice, Quot.sound]`. In my audit, all 39 G01B declarations plus my `Gc_normal` use exactly those three, with no sorryAx. |
| 4 | Independent recompile | PASS | See the commands and results below. |
| N | Numerical check of T8/T10 (sympy, exact rationals) | PASS | See the numerical results below. |

### Recompile commands and results (check 4)

All commands ran from `/home/cosmosapjw/lean_oracles/viii_oracle`: Lean 4.31.0 (commit 68218e87), mathlib rev `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` (from lake-manifest).

- **C04 rebuilt from a byte copy of the source:** `lake env bash -c "LEAN_PATH=<S>/imports:$LEAN_PATH lean -R <S>/imports -o <S>/imports/CAS01C04Accepted.olean <S>/imports/CAS01C04Accepted.lean"` gave exit 0.
- **Copied module:** `lean -R <S>/src -o <S>/imports/G01BTimelikeFlow.olean <S>/src/G01BTimelikeFlow.lean` gave exit 0, no errors, and 8 lint warnings (the same set as the author's).
- **Audit file:** `<S>/ReviewAudit.lean` (sha `d28cc0aa…df67`) gave exit 0; its stdout sha is `166b6905…9c0a`.
- **Why the copy's olean hashes differ:** the copies give `78f1265f…` and `3fc2b2be…`, because the path is embedded in the olean. Compiling the in-place sources to scratch reproduces the author's oleans **byte-identically**: `0bdda460…953d` and `c557ad8e…ce35f`.

### Numerical results (check N; `<S>/py/check_jet.py`)

- **Test metric:** a curved normal chart g = η + Σ symmetric quadratic terms + a cubic term, with no linear term.
- **Test data:** boosted u=(5/3,4/3,0,0), c=3, general S with STF h2, and a nonzero spatial skew W. Assertions confirm Wu=0 and Qu=0.
- **Results:**
  - T7: value = u.
  - T8: ∂_k u^b(0) = ε_b Q_kb/c for all k, b (exact), and ∂N(0)=0.
  - T10: chart ∇_aU_b(0) = Q_ab (exact).
  - The `covDerivLower` definition equals ∂_aU_b − g^{ed}Γ_{d,ab}U_e at a point x≠0, with max diff 0. So it is the true coordinate Levi-Civita formula, not just correct at the origin.
  - Unit norm = −1 and future holds at x≠0.
  - H(n), Z(n) harmonic formulas hold exactly.
- **Negative controls:** adding a linear term (∂g(0)≠0) gives max|∇U(0)−Q| = 5.56. Using Q with Qu≠0 gives ∂N(0) = (0,−10/9,0,0). Both premises are therefore load-bearing.

## Blocking findings

None.

## Non-blocking notes (suggested fixes; none needed for this verdict)

1. **Status label.** `AUTHOR_RETURN.json` has `"status": "ALL"`, which is a nonstandard token. Suggest `FORMALLY_CHECKED_SCOPED`, consistent with P03-A and P04-A.
2. **Regularity label.** `AUTHOR_RETURN` T4 says "n = ⊤ smooth". In `WithTop ℕ∞`, ⊤ is ω (analytic); smooth is `((⊤:ℕ∞):WithTop ℕ∞)` = ∞. The theorem is ∀n, so both cases are covered; only the label is wrong. My audit proves `((⊤:ℕ∞):WithTop ℕ∞) ≠ ⊤` and instantiates T14 at ∞.
3. **T12/T13 outside the bundle.** The T12 flow map and T13 uniqueness are not inside T14. They are separate theorems about the identical `physField G u Qd c` with hypotheses T14 already supplies. T14 itself carries T11 integral curves, which suffices for acceptance #2. Optionally add the two conjuncts.
4. **Scope of N3.** N3 refutes a uniform radius for *this* construction and the sup-norm ball. It says nothing about other possible extensions, and nothing more is claimed.
5. **Partial derivatives vs Fréchet derivative.** T8 states the 1-jet as coordinate-line derivatives. Together with C^n≥1 on the open N (also in T14), this determines the Fréchet derivative. That is fine, but it is not stated as `HasFDerivAt`.
6. **Freeze evidence.** The freeze-before-compile ordering is mtime-only; the unit is untracked in git.

## Counting recommendation (explicit)

**Count G01-B as FORMALLY_CHECKED_SCOPED (chart level).** That is the same tier and the same way P03-A (chart-level) and P04-A ("Gaussian normal chart", FORMALLY_CHECKED_SCOPED) were counted. Do not count it as PARTIAL like G01-A, and do not count it as card-level COMPLETE or as a promotion of source Theorem 3.

Rationale:

- **The normal chart is the source proof's own setting.** OPTICAL:149 says "Choose normal coordinates at p…". All four card lean_steps are discharged in that setting, and both acceptance criteria #1 (T3) and #2 (T14) are met.
- **R1 and R2 are standard geometric bindings.** R1 is the existence of tetrad-matched normal coordinates. R2 is the chart Levi-Civita formula versus a manifold API, plus T as a global orientation. These are absent from pinned mathlib and are of the same kind as P04-A's Gaussian-chart residual. My sympy check shows the chart formula is the correct coordinate Levi-Civita expression.
- **G01-A was different.** It was PARTIAL because its own core content (affine null ray, screen bundle, geometric Jacobi equivalence) was missing. G01-B's core content (open neighbourhood, smooth positive-root normalization, jet transport, local ODE flow) is all proved.
- **However, the source Theorem 3 sentence "Its ideal optical pair is exactly (Z,H)" is not closed.** It needs the identity (2)=(4), which is R3, owned by G01-A R1/R2. The earlier reviewed signature (SOURCE_SIGNATURE.md) says a conditional local-coordinate lemma "is not G01-B completion and must not be used to promote the source theorem". So the ledger should record:
  - G01-B chart content: FORMALLY_CHECKED_SCOPED.
  - Thm 3 optical-pair conclusion: CONDITIONAL on G01-A R1/R2.
  - R1/R2: declared geometric residuals.

## Not proved (carried forward)

- **R1:** existence of tetrad-matched normal coordinates on a Lorentzian manifold.
- **R2:** identification with the manifold Levi-Civita connection and a global time orientation.
- **R3:** the optical identity (2)=(4), with null geodesics and vertex Jacobi normalization (G01-A R1/R2).
- **R4:** uniform radius (refuted by N3), finite-distance remainder, global flow or completeness.
- **R5:** Einstein/material realization.
- **CAS axes:** the wolfram/sympy/sage axes and any four-axis CAS status change. My sympy run is reviewer evidence only, not a CAS-axis receipt.
- **Scientific admission: HOLD.**

## VALIDATION_MATRIX scientific row (proposed text; I did not edit the file)

`G01-B | CAS-01 g01b_timelike_neighbourhood_flow_v1_20261023 | proof: FORMALLY_CHECKED_SCOPED (independent recompile exit 0; oleans byte-identical in-place; 39/39 + reviewer decls standard axioms) | science: Eq.(17) seed = C04 fullSeed; open timelike-future N with ∃ε-ball PASS; C^n positive-root normalization PASS; unit/future PASS; 1-jet ε_bQ_kb/c and ∇U(0)=Q PASS (sympy exact on curved normal chart, boosted u, W≠0; chart Γ formula = coordinate Levi-Civita at x≠0); negative controls ∂g(0)≠0 and Qu≠0 break jet; local integral curves/flow/uniqueness PASS; Z,H via Eq.(4) PASS; N3 no-uniform-radius genuine | scope: normal chart (R1/R2 geometric residuals), (2)=(4) conditional on G01-A R1/R2, no uniform radius/global flow | admission: HOLD | reviewer: claude-opus-5-5 PASS_WITH_NOTES`

## Relevant paths

- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/g01b_timelike_neighbourhood_flow_v1_20261023/lean/G01BTimelikeFlow.lean`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/g01b_timelike_neighbourhood_flow_v1_20261023/AUTHOR_RETURN.json`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/g01b_timelike_neighbourhood_flow_v1_20261023/FROZEN_TARGETS.md`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g01-b_rerun/ReviewAudit.lean`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g01-b_rerun/c3.out`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g01-b_rerun/py/check_jet.py`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g01-b_rerun/run.sh`
