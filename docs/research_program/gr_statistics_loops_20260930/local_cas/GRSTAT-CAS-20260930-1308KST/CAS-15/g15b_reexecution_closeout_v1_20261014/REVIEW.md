# G15-B — independent review (verbatim final report of a fresh read-only reviewer)

# G15-B re-execution closeout review (`g15b_reexecution_closeout_v1_20261014`)

**Verdict: PASS_WITH_NOTES.** No blocking findings. Scientific admission stays **HOLD**.

- **Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), self-reported and not externally attested. I did not author this unit or the prior one.
- **Read-only:** I edited no repository file, ran no state-changing git command and spawned no subagents.
- **Scratch:** everything I wrote is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g15-b_rerun/reexec/`.

T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/g15b_reexecution_closeout_v1_20261014`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read | done | Ran `unzip -p …PACKAGE.zip …/tasks/G15-B.json`; sha256 is `7d889a28…`, which matches SOURCE_RECOVERY. Acceptance: pointwise divergence plus integral identity, no-boundary and regularity use stated, original quantifiers/domain/measure, kernel build plus `#print axioms` plus fresh review. Pitfall: no pole-hiding coordinate integration. |
| 1a | Citations in SOURCE_RECOVERY | PASS | Recomputed sha256 matches every cited value: prior FROZEN `58469ea3`, prior SOURCE_RECOVERY `ca97e9d7`, REVIEW `ddff0afe`, ADDENDUM `71b9f067`, prior AxiomAudit `43fa287c`, DOSSIER `00c1fcb0`, CAS-15.json `eccc10a3`. `grep -n` confirms DOSSIER l.149 ("Only brightness moments through rank four … are needed") and CAS-15.json l.263 ("…; onlyrank<=4"). The `prior/` copies are byte-identical to their originals. |
| 1b | Reused sources byte-identical | PASS | `G15BSphere.lean` = `d08907e9…` in T, in the prior unit, and in `compile_02.source`. `G15APhoton.lean` = `fc4d0606…` in T, in the G15-A unit, and in `compile_01.source`. |
| 1c | FROZEN_TARGETS predates first harness attempt | PASS | `stat` birth time of FROZEN_TARGETS.md is 21:43:00.318Z, and its mtime 21:43:00.320Z shows no later edit. `run_compile.py` was born 21:43:14Z and compile_01 started 21:43:19Z. `G15BUniform.lean` was born later, at 21:44:30Z (mtime equals birth). After normalizing whitespace, the four frozen Part B statements are textually identical to the Lean source (script check), and `raw/AxiomAudit.lean` retypes them as `example … := theorem`, which compiles. |
| 1d | U quantifier order | PASS | The `#check` output in `compile_04_audit.stdout` (and in my rerun) reads `∀ H a σ i j, ∃ p, p.totalDegree ≤ 4 ∧ (∀ m ∈ p.support, |m| ≤ 4) ∧ ∀ μ [IsFiniteMeasure μ], RotInv μ → ∀ I, Continuous I → …`. So p is fixed before μ and before I. |
| 1e | Moment-expansion clause | PASS | The clause is `∫ I·wB5 dμ = Σ_{m∈supp p} coeff_m(p) · ∫ I ∏_k e_k^{m_k} dμ`. Coefficients depend only on (H, a, σ, i, j), and every monomial has \|m\| ≤ 4, so these are brightness moments of rank ≤ 4. Combined with ∃p-first, this faithfully expresses DOSSIER l.149 / CAS-15 l.263 for the angular-brightness part of (B5). The C₂ and T₂ rank-two moments are separate inputs and are correctly out of scope. |
| 1f | wB5 is the boxed (B5) bracket; p is genuinely degree 4 | PASS | By hand: `wB5 = (4H − e·σe) e_i e_j + a_i e_j + e_i a_j + (σe)_i e_j + e_i (σe)_j`, which is DOSSIER (B5) term for term. Sympy (`num/pb5_and_control.py`) shows Lean's `pB5` (with `Wm σ k l = σ_kl`) equals `wB5` symbolically for all 9 (i,j), with generic total degree exactly 4. |
| 1g | Numerical uniform check (same p, two different I) | PASS | Script `num/uniform_check.py`. Quadrature: 60-point Gauss–Legendre in z × 120-point φ grid, rotated by a random orthogonal Q so nothing aligns with the coordinate poles; total mass reproduces 4π. p is extracted once per (H, a, σ, i, j) and then used for I₁ = 1 + 0.4(e₁² − e₃²) (the dossier carrier) and for the non-polynomial I₂ = exp(0.7e₀ − 0.3e₁e₂)(2 + cos(3e₂ + e₁)). Coverage: 2 parameter sets (general σ; symmetric trace-free σ) × 4 index pairs × 2 I. Worst \|lhs − rhs\| = 2.1e-14. Every case has deg = 4 and max monomial = 4. |
| 1h | Negative control `iwise_form_degenerate` | PASS (genuine) | Lean: my `ReviewAudit.lean` proves `R2_sigma_ne` (∫1 dσS ≠ 0, via `toSphere_apply_univ` and π > 0) and instantiates the control at σS, I = 1, v = 17. Numeric: a degree-0 c fitted to I₁ reproduces I₁ exactly but gives 2.912 for I₂, against the true −0.684. So the I-wise form carries no degree information, while a uniform p cannot be degree 0. |
| 1i | Recorded adjustments | PASS | `_finite` drops `RotInv`, which weakens a hypothesis and therefore strengthens the result; it is recorded. U itself does not use `RotInv` (it is introduced and discarded). Part A statement `B5_rank_le_four_moments` (I-wise) is kept and not relabelled. `deviations: []` is correct, since U was frozen before compiling. |
| 2a | Non-vacuity of U | PASS | The author's `B5_rank_le_four_uniform_σS` instantiates at σS using `σS_rotInv` and the `IsFiniteMeasure σS` instance. My `R2_sigma_ne` shows σS ≠ 0. |
| 2b | U is not degenerate | PASS | My `R1_p_pointwise` instantiates `_finite` with `Measure.dirac e0` and I = 1 to derive `wB5 e0 = eval p e0` for every e0 ∈ S². So the uniform statement pins p pointwise on S². It compiles with axioms [propext, Classical.choice, Quot.sound]. |
| 2c | Hypotheses do not assume the conclusion | PASS | Route: `wB5_degree_le_four` (reviewed in Part A), then a pointwise rewrite, then `integral_finsetSum` / `integral_const_mul`. Integrability comes from `integrable_cont` (continuous on compact S²). No formula is postulated. |
| 3a | Hashes | PASS | Recomputed sha256 matches AUTHOR_RETURN and the receipts for: sources (`242e5661` Uniform), all 4 `.source.lean` snapshots, stdout/stderr (stderr all empty `e3b0c442`), oleans (`0c15d3c2`, `3839c4df`, `23b66e80`), AxiomAudit `0b747513`, `run_compile.py` `c395f350`, FROZEN `0ae8bfb3`, SOURCE_RECOVERY `35a842c4`. |
| 3b | Exit codes and attempt retention | PASS | Four receipts, 01 to 04, each `exit_code` 0. `raw/probes/` is empty. Timeline: compile_02 ended 21:44:05Z and `G15BUniform.lean` was born 21:44:30Z. A 25 s gap is too short for a hidden failed Uniform compile, which takes about 90 s here. A filesystem-wide search of `/tmp` and `/home` for `G15BUniform*` and for the string `B5_rank_le_four_uniform` finds only T's files (plus my prompt). |
| 3c | Prior unit's lost history stated honestly | PASS | AUTHOR_RETURN `historical_failure_logs`: strict retention UNMET, streams UNAVAILABLE, count UNKNOWN, "NOT recovered, reconstructed or replaced". SOURCE_RECOVERY and FROZEN "Not claimed" say the same. |
| 3d | Axioms | PASS | All 87 `#print axioms` lines are exactly [propext, Classical.choice, Quot.sound]. Meta `collectAxioms`: G15BSphere 163 constants, G15BUniform 11 constants, 0 offenders. I reproduced this. |
| 3e | Forbidden tokens | PASS | `grep -nE "sorry|admit|native_decide|^\s*axiom|sorryAx|set_option|implemented_by|extern|opaque|unsafe|macro|elab|private"` over `T/lean/*.lean` and `raw/AxiomAudit.lean` found no matches (rc = 1). |
| 4 | Independent recompile | PASS | Copied sources to `reexec/src`. From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain `v4.31.0`, mathlib rev `fabf563a…` per `lake-manifest.json`) I ran `lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/<M>.olean $S/src/<M>.lean"` for G15APhoton, G15BSphere and G15BUniform. All exit 0 with empty stderr. Results by module: G15APhoton.olean `0c15d3c2`, byte-identical to the author's. G15BUniform.olean `23b66e80`, byte-identical to the author's. G15BSphere.olean `c69d9091`, 48 bytes shorter; this is the known embedded-absolute-path effect (prior N3: my path is 50 chars shorter). G15BSphere stdout (5 linter warnings) is identical to `compile_02_main.stdout` after path normalization. The author's `AxiomAudit.lean` run against my oleans gives stdout sha256 `481c5860…`, byte-identical to `compile_04_audit.stdout`, and its first 197 lines are byte-identical to the prior unit's `compile_03_audit.stdout`. My `audit/ReviewAudit.lean` exits 0. |

## Blocking findings
None.

## Non-blocking notes
- **N1 (proof provenance).** The tactic body of `G15BU.B5_rank_le_four_uniform_finite` (the `hpt`/`hint`/`rw` lines) is a near-verbatim adaptation of the prior reviewer's `scratchpad/g15-b_rerun/audit/UniformFix.lean`. That file was born 21:38Z and compiled outside any harness. This is disclosed indirectly (REVIEW.md N2 says the reviewer compiled a uniform version; SOURCE_RECOVERY cites N2). It also explains why the new module succeeded on its first attempt. It is not an author compile outside the harness, so `compiles_outside_harness: 0` stands. Suggested fix: add one AUTHOR_RETURN line crediting the reviewer's demonstration as the proof template.
- **N2 (retention evidence is not absolute).** A compile from stdin, or from a temp file that was later deleted, cannot be excluded forensically. Birth times, the 25 s gap and the empty `probes/` directory are all consistent with zero hidden attempts.
- **N3 (hypothesis class).** U requires I to be continuous on all of E3, not just on S². By Tietze extension, and because the integrals only see I on S², this loses nothing.
- **N4 (negative-control form).** The control `iwise_form_degenerate` is stated for the pointwise-integral form (`∫ I·p = v`), not for the moment-expansion form of Part A's `B5_rank_le_four_moments`. The two are equivalent by the same linearity, and the prior reviewer's example covered the expansion form. Adequate as is.
- **N5 (record-keeping).** SOURCE_RECOVERY.md was written after the compiles (born 21:47:38Z). This is fine because the U binding is already in the pre-compile FROZEN_TARGETS. The `requested_runtime` billing discrepancy is noted honestly. `status: "ALL"` is terse, but `status_scope` qualifies it.
- **N6 (prior caveat).** The G15BSphere olean differs only by its embedded path, same as prior N3. Identical audit output against both oleans confirms they have the same content.

## Code defect versus method limitation
- **Code defects:** none found.
- **Method limitation:** U shows that a degree ≤ 4 polynomial is sufficient. It does not show that the degree-4 bound is sharp. Sympy shows the generic degree is exactly 4, but this is not formalized and is not claimed.

## Not proved / not claimed
- Scientific admission: **HOLD**.
- Recovery of the prior unit's lost development failure history: UNAVAILABLE and not recovered.
- Sharpness of the degree-4 bound.
- (B2) transport, Liouville and energy integration, and the horizontal derivative: hypothesis only.
- Existence of C¹ ambient extensions.
- Identifying σS with Hausdorff measure, or its total mass as 4π, in Lean. Numerically the quadrature reproduces 4π, and my R2 only shows σS ≠ 0.
- C₂ and T₂ derivative/collision moments; gap/inversion; stacked commutant; any CAS axis; publication readiness; parent-card closure.

## Suggested VALIDATION_MATRIX scientific row (not written)
`G15-B reexec closeout | Part A 32 stmts re-executed from unchanged d08907e9 + G15-A fc4d0606; new G15BUniform 242e5661: U = ∃p(deg≤4) ∀μ finite RotInv ∀I cont, ∫I·wB5 = ∫I·p = Σ coeff·rank≤4 moments | fresh recompile exit0 (Uniform/G15A olean byte-identical; Sphere path-only diff), audit stdout 481c5860 byte-identical, axioms ⊆ {propext,Classical.choice,Quot.sound} (163+11 consts, 0 offenders); Dirac probe pins p=wB5 on S²; σS≠0 non-vacuity; neg control instantiated (σS, I=1); S² quadrature (rotated GL×φ) same-p two-I max |Δ|=2.1e-14; sympy pB5≡wB5, deg exactly 4 | PASS_WITH_NOTES | notes: proof template from prior reviewer UniformFix (disclose); prior-unit history UNAVAILABLE | admission HOLD`

## Files
- Reviewed unit: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/g15b_reexecution_closeout_v1_20261014/` (`lean/G15BUniform.lean`, `FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `raw/compile_0{1..4}_*`, `raw/AxiomAudit.lean`)
- My reviewer artifacts, under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g15-b_rerun/reexec/`:
  - `audit/ReviewAudit.lean`
  - `review_audit.stdout`
  - `authaudit.stdout`
  - `num/uniform_check.py`
  - `num/pb5_and_control.py`
- Template referenced in N1: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g15-b_rerun/audit/UniformFix.lean`
