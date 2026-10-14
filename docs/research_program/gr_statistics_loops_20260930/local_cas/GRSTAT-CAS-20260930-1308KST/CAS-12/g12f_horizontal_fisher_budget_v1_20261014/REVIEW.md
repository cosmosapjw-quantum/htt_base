# G12-F — independent review (verbatim final report of a fresh read-only reviewer)

## G12-F fresh independent review (read-only)

Reviewer model: Claude Opus 5.5 (`claude-opus-5-5`), as self-reported; nothing independently attests it. I did not author G12-F. I changed no repository file. All scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-f_rerun/`.

### VERDICT: PASS_WITH_NOTES
- Nothing blocks. Every check below passed.
- Scientific admission stays **HOLD**.

Task dir T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/g12f_horizontal_fisher_budget_v1_20261014`

---

### Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card identity | PASS | Card sha256 from `unzip -p … tasks/G12-F.json \| sha256sum` is `43e787f2…5c5b`. Package sha256 is `2d0b6da9…af6f`. Both match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 1b | Source citations | PASS (line numbers drift slightly) | `TEFF_POSITIVE_BRIDGE.md` (sha `f04d96fe…`):<br>• :39 is dν = C E² dE dΩ<br>• :145-151 is the budget ∫\|𝒟_X f\|²/(f(1+f)) dν ≤ J_X<br>• :153-158 is "In a parallel local tetrad … after controlling kernel and measure differentiation … \|𝒟_X∫Kf dν\| ≤ √J_X[∫K²f(1+f)dν]^{1/2}"<br>• :160 and :238 are as cited<br>`DECISIONS.json:603-604` and `POSITIVE_EXTENSION_DECISION.json:191-192` are verbatim ("actual horizontal Fisher budget" / "vanish in the stated parallel local construction, or are added separately").<br>`DOSSIER_POSITIVE_BRIDGE.md:86` (sha `00c1fcb0…`) is as cited. The "independent nearby-event information" text is at **:101**, not :104.<br>`COMMON_SPEC.md:22,28-29`, `TEFF_CLAIMS.json:133-138` and `CAS-12.json:48,63,83,258` are as cited. The "q existence and derivative integral conditions" item is at :251; the recovery doc says 250-254.<br>Import line citations are correct: G11A :216/:243/:364/:368. The G12DCardClosure citations point to the `_type` Prop statements; the theorems themselves are at 315/340/365. |
| 1c | Frozen targets match source quantifiers, domain, measure, sign, weight | PASS | T6 is the source statement over an arbitrary measure μ = dν, which generalizes it. It uses the literal BE weight `f x0 z * (1 + f x0 z)` and requires f ≥ 0. Its budget hypothesis is on `f' x0`, which `h_diff` ties to the actual t-derivative a.e., so J_X is a spacetime input and never a static or angular functional (card pitfall met). The `HasDerivAt` conjunct identifies ∫K f' with d/dt ∫K f_t, so the conclusion really is \|𝒟_X∫Kf\| ≤ √J√W.<br>`hKw` (finite weighted norm) loses nothing: when the norm is infinite the source's right side is ∞ and the statement is vacuous.<br>T12 instantiates the source carrier: (Lebesgue on E > 0) × dΩ with density C E², per stress component, under the BE envelope (A5). |
| 1d | Extended Fisher density convention | PASS | `fisherDens d w = if 0<w then ofReal(d²/w) else if d=0 then 0 else ⊤`. I checked this by `rfl` in my audit.<br>• Both remaining cases checked: `fisherDens 0 0 = 0` and `fisherDens 1 0 = ⊤`.<br>• Lean's junk value `hess .BE 0 = 0` is confirmed, and `junk_hess_control` shows the real-valued form would wrongly allow d = 1 at f = 0.<br>• T2 bridges to the reviewed G11A real form, but only on the open domain `dom s`, where the junk value never occurs.<br>• T4 shows an admissible differentiable family has d = 0 wherever f(1+ξf) = 0 (local min at f = 0, local max at FD f = 1). So the d/0 = ⊤ convention adds no restriction on admissible families. It is the standard Fisher convention and the only one under which Cauchy–Schwarz holds. |
| 1e | Derivative–integral interchange | PASS (genuine) | T5, T6, T7 and T12 apply Mathlib `hasDerivAt_integral_of_dominated_loc_of_deriv_le` with explicit domination hypotheses. This is the card's step 2 ("지배함수/regularity"). T13 discharges the domination concretely with `nvBound = C E² W_b (1+E²)`, which is integrable by the G12-D lemmas. |
| 1f | Kernel and measure correction terms (T7/T8) | PASS | O(t) = ∫K_t f_t ρ_t dμ. Its derivative is ∫(K f′ρ + K′fρ + K fρ′), with the product rule proved by `HasDerivAt.mul` and `ring`. Only the kernel term's integrability is assumed (`hkern`); the measure term's integrability is derived. T8 bounds each correction by an envelope integral. This matches the "or are added separately" condition in DECISIONS:604. |
| 1g | Negative controls | PASS (some are weak) | T9 is the sharp equality case: J = 1/2, W = 2, derivative 1 = √(1/2)·√2.<br>T10(a) is genuine at the abstract T1 level.<br>T10(b)/(c) correctly show that dropping a correction term breaks the bound. However, their third conjuncts are trivially true because √0 = 0, and they are not instances of T7. See note N4. |
| 1h | Numerical reference check (T6/T7), BE family on dν with C = 1.7, b = 1.3 | PASS | Scripts: `num_t6.py` and `num_t7.py` (scipy dblquad, axisymmetric dΩ = 2π dμ). Family f_t = F_b(E(1 − t·a(μ))), F = 1/(eˣ − 1).<br>• Analytic derivative vs central finite difference: relative error 3e-8 to 1.1e-7 in all 8 cases.<br>• Dipole a = μ with K = Eμ (T^{0z}): \|D\| / (√J√W) = **1.000000**. This is the predicted equality case, K ∝ f′/w. Hand check: D = C(4π/3)·4!ζ(4)/b⁴ = 64.76, matching 64.7638.<br>• Other kernel and family pairs give ratios of 0.974, 0.633, 0.500, 0.226, 0.169 and 0, all ≤ 1.<br>• T7 with ρ_t = C E²(1 + 0.5tμ) and K_t = E(1+μ)(1 + 0.2t): the finite-difference derivative is 102.002996 and the three-term sum is 102.002990 (relative error 5e-8). The terms are horizontal 84.19, kernel 9.71, measure 8.10. The T7 bound is 150.79 and the T8 envelope bound (b′ = b/1.1) is 164.98, so both hold.<br>• In the dipole case with a measure term, the finite-difference derivative is 72.86, which exceeds the parallel-only right side of 64.76. This is a non-trivial physical example that the measure term is required. |
| 2 | No assumed conclusion; non-vacuity | PASS | No hypothesis restates its conclusion. T1 derives the integrability of K d ρ rather than assuming it. The T6 hypotheses are jointly satisfiable: my audit instantiates T6 directly (one-point measure, f_t = 1 + t, K = 1, J = 1/2), and it compiles. T13 instantiates T12 on the photon envelope f_t = (1+t)F_{2b} with a finite J, and its proof goes through T12. |
| 2b | Consistency with G12-E (T14) | PASS (genuine) | T14 uses the reviewed `G12E.fisher_unbounded`. The G12-E family is g + a sin(nx)q, whose derivative at x = 0 is a·n·q, so that is the correct derivative. For every finite J the family eventually violates the budget hypothesis, so there is no contradiction. T14 works on the `G11A.nu C` carrier, the same one G12-E uses. |
| 3a | Hashes | PASS | `verify.py` recomputed all 4 AUTHOR_RETURN sources, both new oleans, 10 import sources and 10 import oleans: 0 mismatches. In all 20 receipts the source snapshot, stdout and stderr sha256 match. Every receipt whose exit was 0 has a matching olean hash. |
| 3b | Exit codes and kept failures | PASS | Final compiles exit 0: FisherBudget #15, Instances #17, audit #20. Failed attempts are all kept: #12 (probe), #13 and #14 (FisherBudget), #16 (Instances), #18 (audit). The diff from #16 to #17 is only `zero_add` → `add_zero`. |
| 3c | Frozen before first compile | PASS (filesystem timestamps only) | FROZEN_TARGETS.md was modified at 03:01:34Z and its sha file written at 03:01:44Z. The first G12F proof compile (#13) started at 03:07:16Z. Probe01 (02:58Z) is pre-freeze but contains only `#check` and name examples. The current sha (`0265c300…`) equals the recorded freeze sha. |
| 3d | Forbidden constructs and axioms | PASS | `grep -nE "sorry\|admit\|native_decide\|^axiom\|set_option\|implemented_by\|extern\|unsafe\|opaque\|csimp"` over T/lean and AxiomAudit.lean finds nothing. The author's audit shows 31/31 public theorems on [propext, Classical.choice, Quot.sound]. |
| 3e | Statement alignment | PASS | `sigdiff.py` finds all 22 frozen definition and theorem blocks verbatim (whitespace-normalised) in the Lean sources. The author's AxiomAudit re-elaborates each signature as `example … := @name`. |
| 4 | Independent recompile | PASS | I copied all 12 sources to `g12-f_rerun/src` and rebuilt everything from source into `g12-f_rerun/imp` in dependency order. The command, run from `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain v4.31.0, mathlib `fabf563a…`), was `lake env bash -c "LEAN_PATH=<imp>:$LEAN_PATH lean -R <src> -o <imp>/<M>.olean <src>/<M>.lean"`. All 12 exit 0 with no errors; the only warnings are unused-variable lints.<br>The G12FInstances olean is byte-identical (`e7c9161d…`).<br>The G12FFisherBudget olean differs (`b590419a…`). Cause: the G11AIntegralBregman olean embeds its source path. My two rebuilds are deterministic, and rebuilding G11A with the author's `-R` root reproduces the author's hash `432b626a…` exactly. This is not an integrity issue.<br>My audit `src/ReviewAudit.lean` exits 0:<br>• `rfl` checks of all 4 frozen definitions<br>• convention checks<br>• the verbatim T6 signature<br>• a direct T6 instantiation<br>• `#print axioms` for all 31 public theorems: **31/31 = [propext, Classical.choice, Quot.sound]**<br>• enumeration of the G12F namespace: 37 theorem constants = 31 user theorems + 6 auto-generated `eq_1` lemmas, none unaudited. |

---

### Blocking findings
None.

### Non-blocking notes
- **N1. M1 (parallel-tetrad modelling).**
  - I accept this as the modelling scope for G12-F. The source states the bound only "in a parallel local tetrad", and DECISIONS:604 allows the terms to be "added separately", which T7/T8 do exactly.
  - Residual for the downstream energy-frame card: DOSSIER:86 defines 𝒟 via the *projected rest-bundle connection at fixed u-measured energy*. This differs from a fully parallel tetrad whenever ∇_X u ≠ 0.
  - In that case D_X = h(∇_X T)u (COMMON_SPEC:22) brings connection, boost and energy-rescaling contributions. These must be supplied as concrete K′ and ρ′ in T7; none are derived here.
  - Classification: a limitation of the method, not a code defect.
- **N2. M2 (the constant C and factors of c).**
  - Card step 5 is met for the kernel: K^{ab} = E n^a n^b follows from T^{ab} = ∫p^a p^b f d³p/p⁰ with p = E(1, e), and I confirmed this by hand.
  - The inequality has degree 1 in C on both sides: the left side, J, and W each scale like C, so √(JW) does too. In an orthonormal tetrad with x⁰ = ct, every component shares the same factor of c.
  - So the normalisation cannot affect validity; it only matters for absolute physical values, which belong downstream.
  - The units check exists only in prose (SOURCE_RECOVERY §6) and is not formalised. Treat this as a documented residual, not a gap in G12-F.
- **N3.** T13 is stated as `∃ J`, which is a weak statement. It is still genuine non-vacuity because the proof goes through T12. Optional improvement: state the explicit J (the toReal of the budget lintegral).
- **N4.** T10(b)/(c) are logically trivial once √0 = 0 and do not instantiate T7. No Lean instance of T7/T8 has nonzero corrections. My numerical case covers this (dipole plus measure term: 72.86 > 64.76). Optional improvement: add a one-point Lean instance of T7 with ρ_t = 1 + t.
- **N5.** T10(a) uses d = 1 at f = 0. By T4 this is not an admissible differentiable family, so the control is meaningful only at the abstract T1 level, which is how it is framed.
- **N6.** Freeze ordering rests on filesystem modification times; the task directory is untracked in git (`??`). Line drift in the recovery doc: DOSSIER :104 should be :101, and CAS-12.json 250-254 should be 251.
- **N7.** The card's CAS axes (wolfram_xact, sympy) were not executed by the author. My scipy checks partly stand in for the sympy Leibniz-coefficient check: the T7 three-term decomposition matches the finite difference to 5e-8. Nothing ran for xAct or horizontal transport.

### Not proved
- **Scientific admission: HOLD.**
- The differential-geometric construction of the parallel local tetrad, and the identification 𝒟_X = ∂_t (M1).
- Concrete K′ and ρ′ for a non-parallel frame, such as the rest-bundle connection with ∇_X u ≠ 0.
- The constant C, the factors of c, and the units as a formal statement (M2; prose check only).
- The identification of `energyAngularMeasure dOmega` with density C E² and `G11A.nu C`.
- The energy-frame spectral-gap bound that would consume these derivative inputs.
- Any certified physical value of J_X; J is always a hypothesis.
- The CAS-axis derivations (xAct, sympy).
- The parent-card closure decision, which belongs to the adjudicator.

### VALIDATION_MATRIX scientific row (proposed text; I did not edit the file)
`G12-F | TEFF-A4 horizontal Fisher budget ⇒ |D_X∫Kf dν| ≤ √J_X·√∫K²f(1+f)dν (+ exact kernel/measure terms) | Lean 4.31.0/mathlib fabf563a: T0–T14 PROVED, independent rebuild exit 0, 31/31 axioms ⊆ {propext, Classical.choice, Quot.sound}; extended Fisher density (0/0=0, d/0=∞) avoids hess-junk; interchange by domination; numeric BE-Doppler check: CS ratio ≤1 (equality 1.000000 in sharp case), T7 decomposition vs FD rel 5e-8 | fresh review PASS_WITH_NOTES (claude-opus-5-5, self-reported) | residuals: M1 rest-bundle vs parallel tetrad K′/ρ′ downstream; M2 C/c (bound is C-homogeneous) | scientific admission HOLD`

### Relevant paths
- Card: `/home/cosmosapjw/Dropbox/bianchi/htt_base/HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (`tasks/G12-F.json`)
- T/FROZEN_TARGETS.md, T/SOURCE_RECOVERY.md, T/AUTHOR_RETURN.json, T/lean/G12FFisherBudget.lean, T/lean/G12FInstances.lean, T/raw/AxiomAudit.lean, T/raw/compile_*.json
- Scratch, in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-f_rerun/`:
  - `src/ReviewAudit.lean` and `ReviewAudit.out`
  - `build.sh` and the `*.out` build logs
  - `verify.py`, `sigdiff.py`, `num_t6.py`, `num_t7.py`
  - `det/` (olean determinism and path-dependence check)

