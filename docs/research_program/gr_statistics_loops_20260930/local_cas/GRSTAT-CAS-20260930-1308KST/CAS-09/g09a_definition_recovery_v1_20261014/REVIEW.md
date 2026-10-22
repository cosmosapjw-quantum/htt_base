# G09-A — independent review (verbatim final report of a fresh read-only reviewer)

# G09-A fresh independent review (rerun 2)

**Verdict: PASS_WITH_NOTES (scoped).** There are no blocking findings. The unit closes G09-A as a definition-recovery card. Two UNKNOWN residuals remain recorded, and I agree with how both are recorded:
- **Concrete catalogue directions and radii:** these are absent from the repository.
- **Physically realizable remainder set:** the source leaves this undefined on purpose (NATIVE l.67).

Scientific admission: **HOLD**.

**Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`). This is self-reported and not attested.

**Review conditions:**
- The review was read-only. No repository file was edited and no git state changed.
- The CAS-09 directory has no working-tree changes at HEAD `a8fd176305fb475947a46f9dacb651805d323741`.
- Scratch files are only under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-a_rerun2/`.
- I did not use any scratch left by the earlier, rate-limited reviewer.

Target directory `T`: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-09/g09a_definition_recovery_v1_20261014`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read first | PASS | `unzip -p …/tasks/G09-A.json` read: scope, 4 lean_steps, 4 acceptance items, 2 pitfalls. Card sha256 `cc96c7a4…542f` and package sha256 `2d0b6da9…af6f` were recomputed and match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 1a | Source hashes | PASS | All 13 inputs in SOURCE_RECOVERY §1 were recomputed with `sha256sum` and match exactly. These include NATIVE `e2158368…`, OPTICAL `5ae2b6a6…`, FINITE_DISTANCE `d499eb7f…`, CAS-09.json `4913de30…`, blocker RETURN `e8b4e50f…`, EXECUTION_CONTRACT, ADJUDICATION, COMMON_SPEC, CAS_TASKS, reviews, claims, NEXT_INPUT_AUDIT and check.wl. |
| 1b | Line citations | PASS, one minor error | Verified against the files: NATIVE l.9, 11, 12, 17, 29, 31–35, 52–54, 56–60, 62–65, 67, 124–128, 130–136, 138, 140, 144–148, 150, 152–155, 157, 159, 163–169 and 193–202. Also OPTICAL l.61–62 (6), l.70 (7), l.76–79 (8) and l.104; FINITE_DISTANCE l.15–18 and 29–33; COMMON_SPEC l.4–5 and 14–15; CAS_TASKS l.581; `htt/src/common/relativistic_kinematics.py:101`. **Error:** SOURCE_RECOVERY cites OPTICAL "l.75 ('dimension 3+9=12')", but l.75 is blank and the text is at **l.84**. The same symbol is also correctly cited at NATIVE l.17. |
| 1c | Blocker coverage (RETURN.json `missing_exact_input`) | PASS | C01 E4/E9 bases and determinant hypotheses are recovered: `E4`, `E9`, `Function.Injective` for the 9×9 and 4×4 blocks (NATIVE l.124, l.150). The exact two-radius directions are UNKNOWN and are replaced by universal quantification plus an explicitly labelled witness. C02 chart, Jacobian and deletion convention are recovered (`massShell`, `dEmb`, `chartDeriv`, `Jphys`; ζ0 is eliminated). C03 basis and alias identities with denominator conditions are recovered (`aliasLift`, `aliasDenom_pos`). C04 ρ_i and native means are recovered (`rhoOf`, `meanZ`, `meanMu`, `nativeZ`). |
| 1d | UNKNOWN branches are truly absent | PASS | I ran my own searches. `git log --all -S unisolvent` returns only contract, DAG and blocker copies plus this unit. `-S 'R/(1+'` returns contract and DAG copies (b16f14538 and d029e6583 are unrelated). `-S 'radial-angular alias'` returns only 11602167b. `grep -ril unisolvent` over the tree adds historical CAS-09 `sage_singular/check.py` (it says the configuration is "absent from permitted sources"), `wolfram_xact/check.wl` (own-axis fixture, already disclosed) and `PROOF_DAG.json` / `PROOF_VERIFICATION_PLAN_KO.md` (contract paraphrases). No file supplies catalogue directions or radii. For realizability, the only CAS-09 hits are NATIVE l.67 ("outer approximation … Sufficiency … has not been proved") and contract and DAG exclusions. `htt/` has no implementation; its only "native inference" hits are unrelated hash labels in `live_binding.py`. |
| 1e | E9 "any real basis" via STF coordinates | PASS (basis invariance argued, not formalized) | `stf` is a bijection onto symmetric trace-free (STF) matrices (`stf_injective`, `stf_stfCoords`, `stf_trace`, `stf_transpose`), and `quad_eq` shows the quadratic is nᵀ(stf q)n; my sympy residual is 0. On unit vectors, `dirStar_unisolvent` proves the 9 Lean functions are linearly independent on the sphere, so they form a basis of degree≤2 spherical polynomials that contains the degree≤1 basis. Any other basis differs by an invertible 9×9 matrix on the sphere, so ranks, ranges and injectivity are unchanged. I checked numerically with a second basis (the Wolfram fixture basis {1,x,y,z,xy,yz,xz,x²−y²,3z²−1}) and got identical ranks for every design below. The invariance is a meta-argument, not a Lean lemma. |
| 1f | 13-variable chart vs 12-variable mass shell | PASS | `Xmap` acts on `IPar × HPar` (rank 13 = 4+9). `massShell ζ = (√(1+|ζ|²), ζ)` uses the future branch (`one_le_zeta0`, `massShell_hyperboloid`). The Jacobian domain is all of `PhysPar` (12). `Jphys = Xmap ∘ chartDeriv`. `Jphys_apply` gives the row nᵢ·δζ + ζ·δζ/ζ0 + (rᵢ/c)H(δh,nᵢ), which is (14). `hasFDerivAt_physMean` proves this is the Fréchet derivative. By hand and in sympy, ∂(ζ0+ζ·n)/∂ζ_k − (n_k+ζ_k/ζ0) = 0. |
| 1g | Alias positive-denominator conditions | PASS | `aliasDenom_pos` takes a unit n and \|ε\|<1 and gives 1+ε n_z > 0 (|n_z|≤1). This is the only denominator cleared, and it matches the contract ("clear only positive nonzero denominators"). The \|ε\|>0 condition is kept as an unused hypothesis, which faithfully keeps the source domain. I recomputed the `aliasLift` coefficients by hand (h0=a0+εa_z/3, h1=(a_x,a_y,a_z+εa0), q=(−εa_z/3, 0, εa_x/2, −εa_z/3, εa_y/2)). Sympy confirms H − (1+εn_z)p(n) ≡ 0 modulo n_z² = 1−n_x²−n_y². |
| 1h | ρ_i, native means, Ω vs realizable (pitfall) | PASS | `NativeDomain` (r>0, Z>0), `rhoOf`, `Omega5` (eq. 5, enlarged) and `Omega6` (eq. 6) are distinct predicates. No realizability predicate is defined, and N4 is stated only into `Omega5`. `E5` matches eq. (5) and FD2, with the x-dependence through H(x,nᵢ) correct. `eta` matches the source for s>0 and handles Kc=0 as the source does. |
| 1i | N3 criterion and 9+4 design | PASS | `rank_concat_identity` is the dimension formula. `rank13_iff` matches (11). `rank13_needs_N` gives N≥13. `two_radius_injective` follows the source's coefficient elimination step by step (first nine rows give h = −(c/R1)·lift(a); the repeated four rows give (1−R2/R1)p=0). Exact sympy ranks on the witness (dirs ±e1, ±e2, ±e3, (3/5,4/5,0), (3/5,0,4/5), (0,3/5,4/5); σ=(0,1,2,4); R1=1, R2=2, c=1): det E9 = 331776/15625 (rank 9), det of the E4 sub-block = −2 (rank 4), **rank X = 13**, **rank Jphys = 12** at ζ=(1/3,−2/7,5/4). |
| 1j | Negative controls genuine | PASS | Exact sympy: R1=R2 gives rank X = 9. Angular-deficient σ=(0,1,0,1) gives rank X = 11 < 13. Alias ε=1/2 on the witness gives rank 9 with non-constant radii (1, 2/3, 2, 5/7). Alias ε=−3/4 on 13 directions gives rank 9. Constant-radius Jphys gives rank 9. In Lean, I instantiated the DESIGN-ANGULAR hypothesis myself (`angular_hyp_inst`: kernel vector (0,e2) of E4 on e1, −e1, e1, −e1) and derived `angular_neg_inst`. SLACK-BOUNDARY is a genuine counterexample but uses a degenerate envelope (E≡0); see note N3. |
| 1k | Adjustments | PASS | Every adjustment drops a hypothesis the proof does not need (unit norm in C01, R2>0 in the angular control, c>0 in N4, Z>0 in N4). These are strengthenings. N4 proves continuity of E rather than assuming it. No source hypothesis was silently weakened and no added hypothesis assumes its conclusion. |
| 2 | No assumed conclusion, no vacuity | PASS | Hypotheses are the source's determinant, rank and slack premises; none is the conclusion. Non-vacuity: `witness_rank13`, `witness_rank12` and `witness_radial_alias_rank9` from the author. From me: `n4_nonvacuous` instantiates `strict_slack_local_identification` with a non-degenerate envelope (Kc=0, M2=1, L=1, ρ*=0, E=1/2>0), and `r1r2_equal_inst`. All compile. |
| 3a | Receipt integrity | PASS | sha256 recomputed for all 7 `compile_*.source.lean`, `.stdout` and `.stderr` files, the module (`e39c42e7…`), AxiomAudit (`6b2727fa…`), run_compile.py (`c924c000…`), the olean (`3f5a19e1…`), SOURCE_RECOVERY (`d7217d3b…`) and FROZEN_TARGETS (`f11188d9…`). All match AUTHOR_RETURN. Exit codes: 01 main = 1, probes 02–04 = 1, 05 = 0, 06 main = 0, 07 audit = 0. The failed attempts are kept. `compile_06` source is byte-identical to the lean file; `compile_07` is identical to AxiomAudit. |
| 3b | Freeze before compile | PASS by content; timestamp not provable | I parsed all 114 declaration headers. The frozen block matches `compile_01_main.source.lean` with 0 mismatches, and compile_01 matches the final source with 0 changes. The only header diff is the `noncomputable` keyword on `Dmap` and `Xmap`, and the frozen text has the pre-fix `def`, which is consistent with extraction before compiling. The FROZEN_TARGETS.md file time (12:21 KST) is later than compile_01 (12:19 KST) because of the "Addendum after compile". No pre-compile snapshot or timestamp exists, unlike G08-D's `FROZEN_TARGETS_v1.snapshot.md` / `.written_utc`. See note N2. |
| 3c | Axioms and forbidden tokens | PASS | `grep -nE 'sorry\|admit\|native_decide\|^axiom\|set_option\|opaque\|implemented_by\|extern\|unsafe\|macro\|elab'` over T/lean and AxiomAudit returns no matches. The author audit covers all 68 theorems; the extra `#print` match is from a comment. |
| 4 | Independent recompile | PASS | From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain `leanprover/lean4:v4.31.0`, manifest mathlib rev `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`) I ran `lake env bash -c "LEAN_PATH=$S:$LEAN_PATH lean -R $S/src -o $S/G09ADefinitions.olean $S/src/G09ADefinitions.lean"`. Exit 0, 0 errors. The only warnings are linter warnings, the same 10 as the original; stdout is equivalent to `compile_06_main.stdout` after stripping paths. My olean sha256 is `be864551…`; it differs from the author's because embedded paths differ, which is expected. My own audit `audit/ReviewerAudit.lean` has `#print axioms` for all 68 public theorems plus my 4 checks. Exit 0, empty stderr, and all **72/72** report exactly `[propext, Classical.choice, Quot.sound]`. |

## Blocking findings
None.

## Non-blocking notes (with exact fixes)
- **N1 (citation).** SOURCE_RECOVERY.md §3 shared table, row "physical parameter x…dim 12": change `OPTICAL l.75` to `OPTICAL l.84`.
- **N2 (freeze provenance).** Pre-compile freezing is shown by content (header identity with compile_01), not by a timestamp. For future units, keep a `raw/FROZEN_TARGETS_v1.snapshot.md` with its sha256 and UTC write time before the first compile, as G08-D does.
- **N3 (SLACK-BOUNDARY control).** `slack_boundary_no_neighbourhood` uses M2=Kc=0, so E≡0. It is valid but degenerate. Optionally add a boundary instance with E>0 and \|ρ*\|=E, moving x in the direction that increases \|ρ\|.
- **N4 (basis invariance).** "Any real basis" is justified informally. An optional one-line Lean lemma would make it formal: range (E9 ∘ M) = range E9 for any linear equivalence M : HPar ≃ₗ HPar.
- **N5 (scope).** Not proved, and correctly recorded as such:
  - Surjectivity of `massShell` onto the future sheet.
  - The physical-chart N≥12 remark.
  - The projector form rank[(I−P4)DE9]=9.
  - Ω6 ⊆ Ω5.
- **N6.** `Omega5` does not contain Z>0. This is harmless for N4 because Z is held fixed, but downstream users must combine it with `NativeDomain` explicitly.

## Not proved / not claimed
- Scientific admission: **HOLD**.
- CAS-09 four-axis status: the historical CAS_CONFLICT is unchanged, and this unit is not blind-axis independent because it read `statistics/`, `gr/` and `reviews/`.
- Inverse-function-theorem local injectivity from rank 12, and the converse rank 12 ⇒ rank 13.
- Global nonlinear (non)identifiability and the manifold dimension of the degeneracy family.
- Membership of true catalogues in Ω, and the physical realizability of any Ω point.
- N1, N2 and N-SCALE; rank(PWJphys); any conditioning or precision statement.
- Any catalogue-specific design. The witness `dirStar` is an author-supplied certificate, the same point set as the historical check.wl, not a recovered source definition.
- Wolfram, SymPy and Sage axis receipts for this unit: none were produced. My sympy run is a review cross-check, not an axis receipt.

## VALIDATION_MATRIX scientific-row update (for the caller to apply; I did not edit it)
`G09-A | scientific | PASS_WITH_NOTES (scoped; HOLD) | fresh reviewer Claude Opus 5.5 rerun2 2026-10-23 | independent recompile exit0, 72/72 standard axioms, exact sympy ranks 13/12/9/9/11 reproduced in two bases; residual UNKNOWN: catalogue directions, realizable remainder set; notes N1 citation l.75→l.84, N2 freeze snapshot, N3 non-degenerate boundary control`

Files are in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-a_rerun2/`:
- `src/G09ADefinitions.lean`
- `G09ADefinitions.olean`
- `recompile.stdout` (sha `11c2db55…`)
- `recompile.stderr`
- `audit/ReviewerAudit.lean` (sha `db93e500…`)
- `audit/audit.stdout` (sha `79fb4d18…`)
- `ranks.py` (sha `19fdf4e1…`)
- `ranks.out` (sha `fa820361…`)
