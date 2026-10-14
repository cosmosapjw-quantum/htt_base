# G03-A — independent review (verbatim final report of a fresh read-only reviewer)

## G03-A fresh independent review (read-only)

**Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), a fresh in-session subagent that did not write the package. I changed no repository files and ran no state-changing git commands. Scratch work is in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g03-a_rerun/`.

### Verdict: **PASS_SCOPED**
- **Blocking findings:** none.
- **What passes:** the formal content, within its declared scope.
- **Conditional part:** the D-branch is a theorem for *any* C^n family. It is correctly not applied to the optical S(q).
- **Scientific admission:** HOLD.

### Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Source citations | PASS | All six cited sha256 values match on disk (OPTICAL_THEOREMS 5ae2b6a6…8c21, OPTICAL_CLAIMS 93cb4afc…28e1, CAS-03.json e1218901…26c1, COMMON_SPEC 4714827e…1897, ENERGYFRAME dd66030a…6855, relativistic_kinematics.py 9ae767f9…9d5e). The cited lines say what SOURCE_RECOVERY claims: Theorem 5 at :231, eq. 24 at :228, eq. 25 at :233, dim 1+r at :235, proof at :237, "not guaranteed" at :241, smoothness wording at :259. OPT07 says "Not every real S has a timelike eigenvector". CAS-03.json :43/:50–51/:81/:109 hold the GEO-NOTIMELIKE text. The python lift at :116–160 takes geodesicity as a supplied premise and requires a separated timelike eigenvalue. The prior BLOCKER.md does say the family is unbound. |
| 1b | Import identity | PASS | C01.lean = 979a2cce… and is identical to `git show f7f6231c:` ("GR-CAS-03-C01: Verify finite eigen and kernel identities", on branch proof/cas03-c01-codex-only-20261005). Proof.lean = 8a870e4e…, G04AEigenline.lean = 4d36cde1…, Cas03C02.lean = f1898d2e… (cited, not imported). |
| 1c | Freeze predates proofs | PASS | FROZEN_TARGETS.md mtime is 06:24:03 KST (21:24:03Z), before the first proof compile compile_08 at 21:28:55Z. The frozen Lean block is byte-identical to `probes/Sig.lean` (= compile_07 source, 21:22:36Z) once `sorry` is replaced by `<proof>`: `diff` is empty. The compile_04–07 sources contain only `sorry` stubs plus one trivial `map_smul'` `by simp`. |
| 1d | Final statements match frozen text | PASS | My own name-keyed check (`my_frozen_check.py`) compares each theorem's text up to `:=` and each def's prefix: 69 frozen declarations, 0 differences. The author's check_frozen also gives 66/66. The one textual change is `@[reducible]` on `restCore`, which is disclosed in AUTHOR_RETURN (see note N1). |
| 1e | A1: premise is supplied | PASS | `TimelikeEigenPremise` appears only as a definition and as an iff target. It is never assumed in A–C. D1/D3 take the eigenpair at q0 as an explicit hypothesis. A1 proves premise ⇔ ∃ future-unit u with C01 `bAct s u u = 0` (Bu=0) ⇔ the mixed-matrix form. |
| 1f | A3 counterexamples (checked by hand and with SymPy) | PASS | **sRot:** S_cov has only S01=S10=1, so it is symmetric. Mixed ηS = [[0,−1],[1,0]] ⊕ 0, eigenvalues ±i, 0, 0. The real eigenspace is span(e2,e3), and its Gram matrix is positive, so there is no timelike eigenvector. **sNull:** the t–x block of S_cov is [[1,1],[1,1]] and d=diag(1,0,0). Mixed = [[−1,−1],[1,1]], which is nilpotent (non-diagonalizable). The real eigenspace is {v0+v1=0}, where mass = v2²+v3² ≥ 0, so again no timelike eigenvector. SymPy: both are self-adjoint (ηM symmetric), real eigenspace timelike? = False; sNull `is_diagonalizable` = False. |
| 1g | B1/B2 rest space | PASS | B1 holds for any timelike u; there is no unit assumption, and the Cauchy–Schwarz/Lagrange-identity proof is correct. In my audit: `noncomputable example : InnerProductSpace ℝ (RestSpace τ) := inferInstance` elaborates; `@inner … InnerProductSpace.toInner x y = lorentzDot x.val y.val := rfl`; and `‖x‖² = lorentzDot x x`. B2_finrank = 3 is proved by rank–nullity on the surjective form. A NumPy check of a boosted, non-unit u (|u|²=−6.25) gives a positive rest Gram matrix. |
| 1h | C1 spectral theorem | PASS | Uses Mathlib `IsSymmetric.eigenvectorBasis`/`eigenvalues` on the invariant restriction (`restOp_mem` uses self-adjointness and S u = s u). The result is Lorentz-orthonormal, ⊥u, and consists of eigenvectors. It is bridged to G04A `RestEigenbasis`. |
| 1i | C2/C3 dimension and isolation | PASS | dim E_t = 1 + #{p_i = s}, with b_i = p_i − s_t, which is faithful to eq. 25 "1+r". A NumPy check with random boosts gives dim E_t = 3,2,3,2,3 against 1+# = 3,2,3,2,3. C3 is stated for non-unit τ but is still correct: w and Sw both lie in u⊥, so `restProj` acts as the identity (`restProj_tangent`). |
| 1j | C4/C5/C6 against C01 | PASS (scoped) | C4_C01_fibre is literally C01 `fibre_chart` (`rw; rfl`) under C01's own hypotheses (hrest, hexp). kerD equals the rest eigenspace of S − s_t at e0, linearly and bijectively (`kerMap`). C5: isolation ⇔ fibre = {e0}, both directions proved. C6: qPoint (1,1,−2), with a repeated nonzero eigenvalue, is isolated. qLine (0,1,−1) is not isolated and has dim E_t = 2. This agrees with SymPy and with "repeated nonzero eigenvalues do not destroy uniqueness". |
| 1k | D1/D2/D3 conditional branch | PASS | Hypotheses: CompleteSpace E, an open D, a C^n family with finite n ≥ 1, self-adjointness on D, a future unit eigenpair at q0, and `RestGapInjective` at q0. None of them encodes the conclusion. The proof is a genuine bordered IFT: the injectivity of the inr-derivative comes from G04A `bordered_inj`. Isolation persists because invertibility is an open condition. Uniqueness comes from `E1u_unique`. D2 reuses G04A `E1_smooth_eigenline` unchanged. D3 converts dim E_t = 1 into isolation via C3. My audit re-elaborates the D1 frozen statement independently against `D1_branch`. |
| 1l | E1 isolation cannot be dropped | PASS | Srot(q) = q₁·Rrot: ηRrot is symmetric, and t·Rrot has eigenvalues ±it, 0, 0 (SymPy). At q=0 every D1 hypothesis except isolation holds, and every neighbourhood of 0 has points with no timelike eigenvector, so no branch can exist. |
| 1m | E2 collision vs isolation | PASS | Scol(0) rest block = I₃ (a triple collision at 1), while s_t = 0, so timelike isolation holds. The branch is obtained from D1 itself, which also shows D1 is not vacuous. |
| 1n | E3 no continuous rest eigenvector | PASS | Checked by hand. Along t·e1, 2t·x1x2 = 0. Along t·e2, t(x2²−x1²) = 0. Along t·e3, t(x3²−x2²) = 0. In the limit x1=x2=x3=0, contradicting unit norm. SymPy eigenvectors along each axis confirm: {axes}, {(0,±1,1,0)/√2, e3}, {(0,0,±1,1)/√2, e1}. No single rest vector satisfies all three relations. This correctly avoids overclaiming at the degenerate point. |
| 2 | No assumed conclusions, no vacuity | PASS | The premise is satisfiable: in my audit, `TimelikeEigenPremise (diagonalExample qPoint)` is constructed via A1. hrest+hexp are satisfied by qPoint/qLine. D1 hypotheses are satisfied by Scol (E2). B has a non-trivial instance at e0T (finrank 3). |
| 3a | Receipt integrity | PASS | For all 12 receipts, the recomputed source/stdout/stderr sha256 match the JSON. The final source 8035ebf5… equals compile_11. AxiomAudit b02bb519… equals compile_12. SOURCE_RECOVERY 3c41e0e4… and FROZEN 878303cc… match AUTHOR_RETURN. head_part+tail_part = final; head_part+tail_stub = compile_09. |
| 3b | Exit codes and failed attempts kept | PASS | 04/05 = 1, 06/07 = 0 (signatures), 08 = 1, 09 = 0 (12 `sorry` stubs, disclosed as a development state), 10 = 1, 11 = 0, 12 = 0. All attempts are kept. |
| 3c | Forbidden tokens | PASS | `grep sorry|admit|native_decide|^axiom|set_option|sorryAx|maxHeartbeats` on the final lean returns nothing. The compile_09 stubs are gone. |
| 3d | Axioms | PASS | Author audit: 76/76 `[propext, Classical.choice, Quot.sound]`, covering all 68 theorems. My namespace scan with `Lean.collectAxioms` over all 151 non-internal `G03A.*` constants found 0 with non-standard axioms. All 31 explicit `#print axioms` lines are standard. |
| 4 | Independent recompile | PASS | Toolchain: lean4 v4.31.0, mathlib fabf563a…. (a) The scratch copy rebuilt C01, Proof and G04A from source (all exit 0), then G03ARestspace (exit 0, 15.7 s, one linter warning only). (b) Compiling from the original source path reproduces olean **25113d8f…** bit-for-bit, and C01.olean 2081c604… bit-for-bit. The olean hash depends on the `-R` path: the scratch-path builds give 62b6a443… and 217c3ee9…, which is benign. Reviewer audit `ReviewAudit.lean`: exit 0. |

### Blocking findings
None.

### Non-blocking notes
- **N1 (amendment not recorded in the frozen file).** `restCore` gained `@[reducible]` after the freeze. AUTHOR_RETURN discloses it, but the "Amendments" section of FROZEN_TARGETS.md still reads "(none at freeze time)". Fix: add an amendment entry there (attribute only; data and statement unchanged), or record it in the ledger.
- **N2 (A1 wording overstates).** A1 proves premise ⇔ C01's Bu=0 encoding (`bAct`). The step A(p)=0 ⇔ Bu=0 (source eq. 24 / Theorem 2 with b=0) is inherited from the source and the C01 contract, not formalised here. The theorem name `A1_premise_iff_geodesic` and the FROZEN phrase "exactly Theorem 5's A(p)=0 condition" should say "Bu=0 (C01 encoding of A(p)=0)".
- **N3 ("simple" means geometric multiplicity).** In D3 and C3, "simple" means geometric multiplicity 1. Algebraic and geometric multiplicity coincide here because C1/C2 give a full eigenbasis, but algebraic multiplicity is not formalised.
- **N4 (C4/C5 scope).** They carry C01's `zeroExpansion` hypothesis, which C01's own `fibre_chart` does not use. This is faithful to C01 but narrower than necessary. They are also limited to the rest frame e0. A general boosted-u fibre chart is not proved (disclosed). C2 does give dim E_t for any timelike u.
- **N5 (freeze evidence).** The freeze-before-proof evidence is file mtimes plus the receipt timeline and the Sig.lean byte identity. There is no commit or hash anchor at freeze time. That is consistent, but weaker than a committed freeze.
- **N6 (tool axes).** The card's Wolfram/xAct and Sage/Singular axes and the author-side SymPy axis were not run by the author (disclosed). My SymPy/NumPy checks (`sym_checks.py`) are reviewer-side corroboration only and do not discharge those axes.
- **N7 (E1 phrasing).** E1 proves that timelike eigenvectors are absent near 0. That ⇒ no `TimelikeBranch` is an immediate corollary, not a separate stated theorem.

### Not proved (not claimed)
- **Scientific admission:** HOLD.
- That the physical optical slope field S(q) is a C^n, self-adjoint family satisfying isolation. The source binds no family; D1 stays conditional.
- C^∞ or analytic regularity, global continuation, or a uniform neighbourhood radius.
- Continuity or smoothness of individual rest eigenvectors at collisions. E3 refutes it.
- A branch without timelike isolation (E1 is a counterexample).
- The boosted-u fibre chart beyond e0, and the curved-metric/covariant version (flat η, orthonormal frame only).
- The formal derivation A(p)=0 ⇔ Bu=0.
- Algebraic-multiplicity simplicity.
- The Wolfram/xAct, SymPy and Sage/Singular tool axes.
- Historical four-axis acceptance.

### VALIDATION_MATRIX scientific row (proposed text; I did not edit the file)
`G03-A | restspace PD (any timelike u), Mathlib InnerProductSpace with inner=lorentzDot, spectral theorem on S|u⊥, dim E_t=1+#{p_i=s_t}, C01 kerD/fibre bridge (e0 frame), conditional C^n IFT branch under RestGapInjective; premise supplied (A3 ×2 genuine counterexamples); E1/E2/E3 controls genuine | FORMAL PASS_SCOPED (fresh review claude-opus-5-5, recompile olean 25113d8f bit-identical, 151 consts std axioms) | family S(q) unbound → D1 conditional; tool axes open; notes N1–N7 | scientific admission HOLD`

### Relevant paths
- Package: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-03/g03a_restspace_spectral_v1_20261014/` (`lean/G03ARestspace.lean`, `FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `raw/compile_*`, `raw/AxiomAudit.lean`)
- Reviewer scratch: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g03-a_rerun/` (`ReviewAudit.lean` / `.out`, `build_main.out`, `det/` for the bit-identical olean, `my_frozen_check.py`, `sym_checks.py`)
