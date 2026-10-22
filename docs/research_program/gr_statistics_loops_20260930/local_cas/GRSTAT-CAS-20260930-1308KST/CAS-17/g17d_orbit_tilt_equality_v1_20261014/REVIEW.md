# G17-D — independent review (verbatim final report of a fresh read-only reviewer)

## G17-D independent review (fresh, read-only rerun)

**Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`). I did not author G17-D. I edited no repository files, ran no state-changing git commands and spawned no subagents. All scratch files are under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/`. I did not look at the earlier partial scratch.

**Target:** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-17/g17d_orbit_tilt_equality_v1_20261014`

## Verdict: **PASS_WITH_NOTES**

Nothing blocks. Scientific admission stays **HOLD**.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read first | PASS | `unzip -p …/tasks/G17-D.json`. The scope, 4 lean_steps, acceptance list and pitfall all line up with SOURCE_RECOVERY and FROZEN_TARGETS. |
| 1a | SOURCE_RECOVERY citations | PASS | Recomputed sha256 of every cited file. All match the quoted prefix and suffix: CAS-17.json `123c73d5…877e`, DOSSIER `00c1fcb0…ebd`, ADDED_BOOK_INTEGRATION `977125a6…dbf`, ADDITIONAL_REFERENCE_MAP `d02c4980…bf0`, DECISIONS `a05b3053…c6c`, POSITIVE_EXTENSION_DECISION.md `d2d2f02a…a299`, COMMON_SPEC `4714827e…7fe1897`, EXECUTION_CONTRACT `a2817237…9328`. Cited lines checked one by one: CAS-17.json 50/55/70/79/85/92/106/121/125/262/264/268/272 say what is claimed; DOSSIER 222-234 is the "Optional final step: tilt…" construction; ABI 111-113 are AB-T4/T5/T6; ARM 285-287, DECISIONS 798-800 and PED.md:113 are the AB-T6 text; COMMON_SPEC:4 gives the signature and future u; SDF:42 says "Nothing here yields a calibrated absolute acceleration scale". |
| 1b | Card step 1: is the equality case missing from C01? | PASS | Read C01.lean (sha `934e6a96…09de`, recomputed). `c01_gram_tilt_bridge` has 11 conjuncts and none is `betaSq = 0 ↔ u = N`. The author's claim holds. |
| 1c | T1 proof checked by hand | PASS | Write r = rel(u,N). Then L(r,N)=0 and L(r,r)=γ²−1. Spatial Cauchy–Schwarz gives r_t²N_t² ≤ r_t²(N_t²−1), so r_t=0, so |r⃗|=0, so r=0, so u=γN=N. Sympy confirms the residual identity L(r,r)−(γ²−1) = 0 modulo the unit constraints, and L(w,w)+det G = 0. I sampled 20k random future pairs: minimum γ−1 = 1.8e-3 > 0. The perturbation behaves as βSq ∝ ε² (ε=1e-2 → 9.8e-5, ε=1e-4 → 9.8e-9). |
| 1d | Past-branch control is real | PASS | By hand: u=(−1,0,0,0), N=e0 gives γ=−1, rel=0, βSq=0 and u≠N. Sympy agrees. The control shows the future hypothesis matters for β/βSq. Side note: `gamma=1 ↔ u=N` would hold for any unit u, so requiring FutureUnit u there is stronger than needed, not weaker. |
| 1e | Card step 2: orbit input typed; no orbit or Bianchi inference | PASS | `IndependentOrbitInput` carries X1..X3, `gram_posDef`, u and `u_future`. Spacelikeness is derived (`gram_posDef_spacelike` via `diag_pos`), not assumed. N is the C01 construction. No declaration infers an orbit or a Bianchi type. The future choice comes from C01 `futureSign`. `normal_swap12` proves the normal does not change when the first two generators are swapped, i.e. under that one orientation flip. Instantiated by `stdInput` and `boostedInput`. |
| 1f | TILT-BOOST control recomputed by hand | PASS | bx=(4/3,5/3,0,0): L(bx,bx) = −16/9+25/9 = 1, Gram = I, N = (5/3,4/3,0,0), L(N,bx)=0, L(N,N)=−1. With u=e0: γ_uN = 5/3 and β² = 1−9/25 = 16/25. With o=e0: γ_uo = 1 and β² = 0. Sympy reproduces every value exactly. No coordinate tilt or u/o tilt is substituted for u/N anywhere. |
| 1g | Card step 3: passive change vs physical replacement are distinct maps | PASS (wording note N1) | `passiveChange` sends g to g∘(L⁻¹,L⁻¹), u to Lu and N to LN. Invariance holds for every real module V and every invertible L, not only Lorentz maps. `tensor_tilt_invariant_C04` reuses the accepted C04 `mixed_tensor_contraction_invariant`. The explicit physical counterexample: tilt goes from 1 to 5/3 when (1,0,0,0) is replaced by (5/3,4/3,0,0). `observer_replacement_not_passive` is ∃c,u' ∀L, passiveChange L c ≠ observerReplacement u' c. That is the correct quantifier order; it is not a universal non-invariance claim. |
| 1h | Card step 4: AB-T6 recorded as a witness, not an identity | PASS | `g17dOperationalWitness := ⟨.notSupplied⟩` is data. No theorem mentions `OperationalWitness` or `G17DApplication.ops`; `#print axioms g17dOperationalWitness` reports no axioms. Repo search (`grep -rIl -E 'AB-T6|abT6|AB_T6'`, plus a search for calibrated metric/clock/distance, excluding legacy/.git) found only planning, contract and decision text (EXECUTION_INDEX, CAS_TASKS, PROOF_DAG, PR_PLAN, LOCAL_CAS_RETURN, POSITIVE_EXTENSION_DECISION, INFORMATION_LIMIT_THEOREMS, STATISTICS_INDEPENDENT_DECISION). All of it states a requirement; none supplies a calibration. NOT_SUPPLIED is correct. |
| 1i | Frozen statements equal final kernel types | PASS | In my own audit file I copied all 17 frozen theorem statements verbatim into `example … := G17D.<thm>`, plus `rfl` checks that `tilt`, `passiveChange`, `observerReplacement`, `IndependentOrbitInput.N`, the witness value and C01 `gamma = -lorentz u N` unfold as frozen. Everything elaborates (rc=0). |
| 1j | Recorded adjustments | PASS | `diff compile_03_main.source.lean lean/G17DOrbitTilt.lean` shows only an added import (`Mathlib.Algebra.Order.Star.Real`), `simp`→`norm_num`, removal of a redundant `ring`, and two added simp lemmas. No statement changed, so nothing was weakened. |
| 2 | No hypothesis assumes its conclusion; no vacuity | PASS | The hypotheses are exactly C01's (PosDef Gram, FutureUnit u). Witnesses exist: `orbit_input_nonvacuous_equality` (std frame) and `tilt_boost_negative_control` (boosted frame). The structure has no field shaped like a conclusion. |
| 3a | Hashes | PASS | Recomputed: SOURCE_RECOVERY `7a1286d5…34cc`, FROZEN_TARGETS `a33c8a19…8251`, main `625c439e…57d7`, AxiomAudit `1d2b71d9…0c44`, run_compile.py `f880c484…e6a5`, C01.olean `e34f0779…1f37`, PTB.olean `7bf257e3…77e0`, G17D.olean `ceec194a…66a6`. Every stdout/stderr hash matches its receipt; the stderr files are empty (e3b0…). compile_04 source equals the final file, and compile_05 source equals AxiomAudit.lean. |
| 3b | Exit codes and kept failures | PASS | Exit codes: 01=0, 02=0, 03=1 (failed attempt kept, with log), 04=0, 05=0. The only warning is the `unnecessarySeqFocus` linter at 220:75. |
| 3c | Forbidden tokens | PASS | `grep -nE 'sorry|admit|native_decide|^axiom|set_option|unsafe|implemented_by|extern|csimp'` over the lean files finds nothing. |
| 3d | Axioms | PASS | My meta audit enumerates **all 173 constants** in module `G17DOrbitTilt`, including internal and auxiliary ones. Union of axioms = {propext, Classical.choice, Quot.sound}; constants with any other axiom: none. A separate `#print axioms` over all 28 public theorems plus `stdInput`, `boostedInput` and `minkowskiBilin` gives 31× `[propext, Classical.choice, Quot.sound]`, and the witness has none. |
| 3e | Frozen-before-proof ordering | PASS (note N4) | FROZEN_TARGETS.md mtime is 03:20:05Z. The first proof compile (compile_03) started at 03:21:11Z. The import-only compiles 01/02 (03:18Z) ran earlier but only rebuilt the accepted, unchanged sources. The evidence is mtime only: the first git commit (6365e36d, 13:24 KST) came after all compiles. |
| 4 | Independent recompile | PASS | cwd `/home/cosmosapjw/lean_oracles/viii_oracle`; Lean 4.31.0 (commit 68218e87); mathlib `fabf563a…911f` per lake-manifest. I rebuilt both imports from source into scratch with `lake env bash -c "LEAN_PATH=$S/imp:$LEAN_PATH lean -R $S/src -o $S/imp/<M>.olean $S/src/<M>.lean"`. The C01.olean and PassiveTensorBridge.olean I got are **byte-identical** to the recorded ones. G17DOrbitTilt compiled with rc=0 and the same single linter warning. My olean sha is `4299ee1f…c024`, deterministic across two runs. It differs from the recorded `ceec194a…` only by the embedded absolute source path: `strings` diff shows a single line, the path, and the 56-byte size difference equals the path-length difference. Audit file rc=0. |

## Blocking findings

None.

## Non-blocking notes (suggested fixes)

- **N1 (naming in T3).** `observerReplacement` replaces the first contraction slot, which the struct calls `u`. Formally the theorem says: replacing one physical vector while holding g and N fixed is not a passive change, and it can change the contraction. That is correct, and it matches C04's observer-slot convention (`obsCfg` puts the observer in the u slot). It must not be read as "the orbit-normal tilt γ_uN depends on the physical observer o". In the TILT-BOOST setting, o does not enter γ_uN at all. Suggested fix: in the T3 docstring and the AUTHOR_RETURN note, say "physical replacement of the vector in the first slot (observer o, or source u); not a statement that γ_uN depends on o".
- **N2 (orientation coverage).** Only the (12) transposition is proved (`normal_swap12`). The phrase "future choice independent of epsilon orientation" holds for the full S3; I checked all 6 permutations numerically on 50 random PosDef triples. The Lean proof covers one orientation-reversing swap, not all permutations. Optional addition: `normal_swap23`.
- **N3 (contract singular locus not exercised).** No G17-D target, and nothing in CAS-17 local, tests the CAS-17 boundary/singular locus "TILT-GRAM nonspacelike invalid". The G17-D card does not require it. Note that with a non-PosDef Gram, Lean's `x/0 = 0` makes `normal` the zero vector rather than raising an error. If wanted, add a control showing that a non-PosDef Gram does not give `FutureUnit (normal …)`.
- **N4 (provenance).** The frozen-before-proof ordering rests on filesystem mtimes and receipt timestamps, not on a commit made before compiling.
- **N5 (card tool axes).** The card's `wolfram_xact` (meaning correspondence for orbit/observer/tetrad) and `sympy` axes have no author receipts. My sympy checks (identities, TILT-BOOST, past branch) cover the sign and normalization part only. The xAct axis was not executed.
- **N6 (scope).** All statements are at a single event. A domain statement follows pointwise only if the supplied orbit distribution and recovered field are given over the domain, as DOSSIER:234 says. This is explicitly listed as not claimed, so no weakening is hidden.

## Proposed VALIDATION_MATRIX.md scientific row (not written; for the caller)

`G17-D | scientific | PASS_WITH_NOTES (independent rerun, Opus 5.5) | T1 equality branch (reverse Lorentz CS, future branch essential: past control genuine); T2 typed orbit input, spacelike derived, TILT-BOOST γ=5/3, β²=16/25 vs u/o γ=1 recomputed; T3 passive∀L invariant vs explicit physical replacement ∃-counterexample; T4 AB-T6 = NOT_SUPPLIED data (repo search: no supply) | kernel: recompiled rc=0, imports byte-identical, 173 consts axioms ⊆ {propext, Classical.choice, Quot.sound} | notes N1–N6 | scientific admission HOLD`

## Not proved (always)

- **Scientific admission: HOLD.**
- Actual orbit or Bianchi identification of X1..X3 (typed input only).
- Domain or field-level tilt beyond one event.
- Uniqueness of the future unit normal among unit vectors orthogonal to the X_i.
- Normal invariance under all generator permutations (only swap12 is proved).
- The TILT-GRAM non-spacelike-invalid control.
- AB-T6 calibration availability (NOT_SUPPLIED; recorded, not a theorem).
- Universal physical non-invariance (only an existential counterexample is proved).
- CAS17-C02/C03, four-axis adjudication, historical environment seal.
- Wolfram/xAct meaning correspondence.

## Scratch artifacts

- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/main.log` (recompile)
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/audit/ReviewAudit.lean` and `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/audit/audit.log` (enumeration of all 173 constants, axiom union, frozen-type matching)
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/audit/PrintAxioms.lean` and `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/audit/printaxioms.log`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/check.py` (sympy and numeric checks)
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-d_rerun2/imp/` (rebuilt oleans)
