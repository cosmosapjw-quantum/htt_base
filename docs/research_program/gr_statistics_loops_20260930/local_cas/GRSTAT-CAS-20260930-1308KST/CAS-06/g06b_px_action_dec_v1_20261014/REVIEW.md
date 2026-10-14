# G06-B — independent review (verbatim final report of a fresh read-only reviewer)

# G06-B independent scientific review: fixed P(X) action on the G06-A TOV germs, with strict DEC persistence

**Reviewer:** Claude Opus 5.5 (model id `claude-opus-5-5`). I did not author this package. I worked read-only and edited no repository file. Scratch work is in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g06-b_rerun/`.

**Target directory (T):** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-06/g06b_px_action_dec_v1_20261014`

## Verdict: PASS_WITH_NOTES

There are no blocking findings. All 37 frozen declarations are faithful to the original obligation; some are strengthenings, none is a silent weakening. Everything compiles independently with only `propext`, `Classical.choice` and `Quot.sound`. The key identities hold in my own sympy and mpmath runs. Scientific admission remains HOLD.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read | PASS | `unzip -p …PACKAGE.zip …/tasks/G06-B.json`. Scope: same fixed EOS and P(X) theory on each constructed TOV germ. Pitfalls: do not fix the event relation `Pstar(q²/2)^s=p0` by changing theory constants; use real exponents only at X>0. |
| 1b | Source citations | PASS | All of these lines were checked directly and say what SOURCE_RECOVERY claims: `CAS-06.json` lines 40, 49, 65, 81, 88, 103, 114, 122, 257; `ADMITTED_INPUTS.json` lines 27, 31–34, 39, 54–57, 62–63, 69; `ENERGYFRAME_THEOREMS.md` lines 23, 205–223, 264, 338–368; `COMMON_SPEC.md` lines 21–25. Every Lean file:line citation (C03Action :118, 148, 174, 194, 206, 225, 258, 280, 357, 391, 418, 428, 442, 470, 531, 681, 762; Foundation :122, 192, 220, 1444, 1515, 1912; Scalar :10, 71, 81, 86; Bundles :71; G06ATOV :38–52, 198, 308) points to the named declaration. |
| 1c | Theory constants bound outside the member quantifier | PASS | My `#check` of both capstones shows `∀ {κ Λ α Pstar q : ℝ}` (germ) and `∀ {κ Λ α Pstar q ε0 μ : ℝ}` (family) bound before `∀ (r0 …)`. The action density, `s = exponent α` and `ψ = scalarGradient q` cannot depend on the member. The family relation `hN : Pstar*(q²/2)^s = α*ε0` is one hypothesis on fixed constants, stated before `∀ r0`. |
| 1d | Per-member matching at r0 | PASS | **Family capstone:** matching follows from the fixed relation `hN` with ν0=0 (proof: `exp 0 = 1`). Nothing is chosen per member. **Germ capstone:** `PXMatched Pstar α q ν0 ε0` is a genuine restriction on member data, and `N1` shows it is necessary. |
| 1e | Is the N3 rigidity a hidden narrowing? | PASS (faithful) | `N3_contract_density_rigidity` says the contract family is non-empty for only one ε0 per (Pstar, q, α). That is exactly what the contract says: ADMITTED_INPUTS:39 fixes `epsilon0,p0,Pstar,q`, :54 has `p0=alpha epsilon0`, :57 has `Pstar(q^2/2)^s=p0`, and EF5c (ENERGYFRAME:353) says q is "fixed … chosen so that P*(q²/2)^s=p0". This restates the source's fixed relation; it does not narrow it. |
| 1f | Hypothesis weakenings relative to the contract | PASS (strengthening) | The family capstone drops `C=2μ+Λ/3>0` and `B≠0` (ADMITTED_INPUTS:55; these are only needed by C02/C04). It also accepts every r0>0 with F0>0, a superset of r0∈(0,C^{-1/2}). Both make the theorem stronger. |
| 1g | Stress and current identities by variation | PASS | **sympy:** ε−(2s−1)P = 0; (2s−1) = 1/α; P−αε = 0; X on the metric = q²e^{−2ν}/2; frame T = diag(2XP_X−P, P, P, P) with zero off-diagonal. **mpmath (40 digits, 5 random points, random symmetric H and η):** the metric-variation residual d/dt[√−g P(X)] + (√−g/2)ΣT_ab H^ab is ≤ 9e−41; the scalar-variation residual is ≤ 6e−37. The convention T_ab = −(2/√−g)δS/δg^{ab} matches ADMITTED_INPUTS:62. |
| 1h | Sound speed | PASS | sympy: P_X/(P_X+2XP_XX) − α = 0, (P_X+2XP_XX)/P_X = 1/α, and P_X = Pstar·s·X^{s−1} > 0. |
| 1i | Fluid identification and conservation | PASS | sympy: d/dν(E·e^{2sν}) = 0; dP/dν + (E+P) = 0; 2s = (1+α)/α; E_PX' − (−(1+α)E_PX ν'/α) = 0 under the TOV ν'. Matching closed form residual = 0. |
| 1j | Einstein–matter equations on the same (metric, scalar) pair | PASS | **Independent sympy run:** I built the Christoffel symbols, Ricci and Einstein tensors from g = diag(−e^{2ν}, 1/F, r², r²sin²θ) with F = 1−2m/r−Λr²/3, then substituted the TOV system (m', ν', ν'', ε'). Frame residuals G + Λη − κ·diag(ε, αε, αε, αε) = [0, 0, 0, 0] and off-diagonal G = {0}. **Lean:** `PXFieldEquationsAt κ Λ α Pstar q m ν r θ` uses the same `ν` and `massLapse m Λ` that appear in `IsTOVSolutionOn`. The Einstein tensor is `chartEinsteinFromMetric ν (massLapse m Λ) (deriv ν) (deriv …)`. This is one constructed pair, not a separate instance. |
| 1k | Scalar equation | PASS (see note N5) | `HasDerivAt 0` holds for every line density, the divergence is 0, and J⁰ ≠ 0, so the statement is not vacuous. J^i = 0 by the diagonal metric. This matches EF5c "holds identically". |
| 1l | Strict DEC | PASS | The margin is E − \|P\| = (1−α)E with 0<α<1 (`AdmissibleParams`), as in ENERGYFRAME:264. The flux form j^a = −η^{aa}T_ab k^b is the correct index contraction. Numerical check: 200,000 random future-causal k (null included), 0 violations, minimum (j0²−\|j\|²)/j0² = 1.0e−5 near α→1, consistent with the 1−α² bound. DEC is proved on the whole interval (T5_strictDEC_at). The uniform margin > (1−α)ε0/2, X > X0/2 and F > F0/2 persist on (r0−η, r0+η) ⊂ I (T5_margin_persists). |
| 1m | Real powers only at X>0 | PASS (see note N4) | Every rpow manipulation in the main proofs has base X > 0 (`actionRadialX_pos`, q≠0) or uses `mul_rpow` with non-negative bases. `zero_rpow` at X=0 appears only in the boundary-branch controls N1 (q=0 case) and N2. |
| 1n | Negative controls | PASS | **N1** (no matching ⇒ the P(X) Einstein–matter equation fails at r) is genuine: it is derived from the (0,0) component plus the barotropic identity, and its hypotheses are satisfiable (my `example`: Pstar=0 never matches ε0>0). **N2** shows q=0 (X=0) cannot match. **N3_matched_gauge_exists** is genuine. My `example` instantiating it shows the germ capstone is non-vacuous for ν0≠0. |
| 1o | Is μ=0 in `W_family_nonvacuous` admissible? | CONCERN (see note N1) | μ=0, Λ=0, r0=1 gives TOVDomain data (1, 0, 0, ε0) with F0=1>0 and ε0>0. That is valid for G06-A and for the family theorem as proved, and is not degenerate. But C = 2μ+Λ/3 = 0, which lies outside the contract's C>0 stratum. I compiled a witness inside the stratum (`review_contract_stratum_witness`: μ=1/4, C=1/2, B≠0, r0=1, F0=1/2), and it closes with the same capstone and standard axioms. |
| 2 | Hypotheses do not assume conclusions; no vacuity | PASS | No hypothesis states a field equation, the fluid identification, a DEC inequality, or interval-wide matching. T3 takes single-event matching only. The capstones are instantiated by W, by my contract-stratum witness, and by the ν0≠0 example. |
| 3a | Hash integrity | PASS | Recomputed sha256 matches AUTHOR_RETURN for all of these: SOURCE_RECOVERY `ee636e9f…`, FROZEN `255897f9…`, source `805bf3fd…`, olean `982d6c43…`, harness `48cb2f40…`, AxiomAudit `a99374c6…`, all 5 import oleans and sources, and adjudication `a504f52c…`. Every receipt's source, stdout and stderr hash matches its recorded value (compile_01 through compile_09). Import sources are byte-identical to `git show 1a375536:` and to HEAD; G06ATOV is identical at `edee3a84` and HEAD. |
| 3b | Exit codes and failed attempts kept | PASS | compile_06 (exit 1) and compile_07 (exit 1) are kept with their stdout. compile_08 exited 0 with one unused-variable warning. compile_09 (audit) exited 0. |
| 3c | Frozen targets predate the first proof compile | PASS (mtime evidence only) | FROZEN_TARGETS mtime is 06:30:30 KST (21:30:30Z). Import compiles ran 21:26–21:28Z, and the first main compile (compile_06) started 21:36:44Z. My whitespace-normalised check finds all 37 frozen declarations verbatim in the final source and in the compile_06 and compile_07 snapshots, so statements did not change across attempts. The `{r0 : ℝ}` binder edit is semantically neutral under autoImplicit and precedes compile_06 by mtime. |
| 3d | Forbidden tokens | PASS | `grep` for sorry, admit, native_decide, axiom, set_option, maxHeartbeats, opaque, implemented_by, extern and unsafe over T/lean and AxiomAudit.lean returns no hits. Recompiling a copy with `autoImplicit false` and `relaxedAutoImplicit false` exits 0, so there are no auto-bound variables. |
| 4 | Independent recompile | PASS | I rebuilt all 5 imports from git-HEAD sources into `…/g06-b_rerun/imports`, then the main module, from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (Lean v4.31.0, mathlib `fabf563a…`). Every step exited 0 with empty stderr; main stdout has only the `hα` unused-variable warning. My audit file `…/g06-b_rerun/audit/ReviewAudit.lean` enumerates all 45 `G06BPX.*` constants from the environment, including defs and eq-lemmas, and runs `#print axioms` on each. All 45, plus my witness, depend only on `[propext, Classical.choice, Quot.sound]`. There are no axiom or opaque declarations. |

## Blocking findings

None.

## Non-blocking notes

- **N1.** `W_family_nonvacuous` uses μ=0, Λ=0, so C=0, outside the contract's C>0 stratum (ADMITTED_INPUTS:55). Non-vacuity inside the contract stratum is not exhibited in the package.
  - Suggested fix: add or replace the witness with μ=1/4 (C=1/2, B=1/4+κp0/2≠0, r0=1, F0=1/2). My compiled `review_contract_stratum_witness` shows this closes directly from `G06B_family_capstone`.
- **N2.** The family relation `hN` is taken as a hypothesis on (Pstar, q, ε0). The converse is not formalised: for any ε0>0 and Pstar>0 there exists q>0, namely q = (2(αε0/Pstar)^{1/s})^{1/2}. That converse is what makes EF5c's "choose q" reading equivalent. This is a trivial optional lemma.
- **N3.** The stress/current identities (T2) and the scalar equation (T4_scalar_equation) hold for any static diagonal metric. "Same pair" is achieved by instantiating them with the G06-A (ν, massLapse m Λ). This is physically correct (EF5c "holds identically"), but these two components do not themselves use the TOV equations. Only the Einstein–matter equations and the fluid identification do.
- **N4.** N1 (q=0 branch) and N2 use mathlib's `0^s = 0` at X=0. That is consistent with continuous extension since s>1, and it appears only in boundary-branch controls, never in a positive claim.
- **N5.** The frame and DEC statements require θ∈(0,π), so the axis is excluded as a coordinate artefact. Spherical symmetry covers axis events, but no theorem states that.
- **N6.** Evidence that the targets were frozen first rests only on file mtimes, because the whole T directory is untracked in git.
  - SOURCE_RECOVERY.md was last modified at 06:40:45, after compile_08 succeeded. It defines no targets.
  - Commit `1a375536` (PR #477) is not an ancestor of HEAD (`git merge-base --is-ancestor` fails). The adopted sources are nonetheless byte-identical at HEAD.
  - The accepted `ADJUDICATION_STDOUT_REPAIRED.json` (hash matches) is untracked on this branch. This predates G06-B.
- **N7.** The frozen signature `T3_integrating_factor` keeps an unused `hα : α ≠ 0`. It is harmless (linter warning only).
- **N8.** My rebuilt oleans are not byte-identical to `raw/imports` (sizes differ by 72–80 bytes, presumably build-path metadata). This was expected and does not affect validity.
- **N9.** AUTHOR_RETURN honestly records the observed runtime model, effort and billing as UNKNOWN.

## Not proved / not claimed

- **Scientific admission: HOLD.**
- C^∞ regularity of the solution functions. Only P(X) is C^n/analytic at X>0.
- Global solutions, regular-centre stars, the maximal interval, and members with F=0, r=0, α=0 or X=0.
- Hyperbolicity, UV behaviour, global stability. c_s²=α is shown only as the finite derivative ratio.
- A unique timelike energy frame and the normal-coordinate 2-jet theorem (CAS-06:257, a separate obligation).
- C02/C04 curvature matching and acceleration divergence (these need C>0 and B≠0).
- Non-vacuity inside the contract C>0 stratum, in the package itself (only in this reviewer's scratch witness).
- Historical four-axis acceptance, and publication/PR state.

## VALIDATION_MATRIX scientific row (proposed text; I did not edit the file)

`G06-B | GR-CAS-06 | fixed P(X) action on G06-A TOV germs + strict DEC persistence | Lean 4.31.0/mathlib fabf563a; source 805bf3fd…; independent rebuild exit 0, 45/45 decls axioms ⊆ {propext, Classical.choice, Quot.sound} | sympy: ε=(2s−1)P=P/α, c_s²=α, frame T=diag(E,P,P,P), E e^{2sν} const, Einstein G+Λη=κT^{PX} on TOV (residual 0); mpmath variation residual ≤1e−36; DEC MC 2e5/0 violations | constants outside member ∀ verified; N3 rigidity = contract fixed relation (faithful) | notes: W witness μ=0 outside C>0 stratum (reviewer witness μ=1/4 compiles), freeze evidence mtime-only | review PASS_WITH_NOTES (claude-opus-5-5, fresh) | scientific admission HOLD`

## Files

- Reviewed: T/FROZEN_TARGETS.md, T/SOURCE_RECOVERY.md, T/lean/G06BPXAction.lean, T/AUTHOR_RETURN.json, T/raw/compile_0{1..9}_*, T/raw/AxiomAudit.lean, T/raw/run_compile.py
- Rebuild and audit: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g06-b_rerun/` (`build.sh`, `build.log`, `main.stdout`, `audit/ReviewAudit.lean`, `audit.stdout`, `noauto/`, `py/frozen_check.py`, `py/sym_check.py`, `py/tov_einstein.py`)
