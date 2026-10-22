# G16-B — independent review (verbatim final report of a fresh read-only reviewer)

## G16-B fresh independent review: report

**Verdict: PASS_WITH_NOTES.** No blocking findings. Scientific admission stays **HOLD**.

- **Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`). This is self-reported and not externally attested. The card asks for gpt-6-astra/ultra. The author used the same model family, so independence is limited.
- **How the review was run:** read-only. I edited no repository file, ran no state-changing git command and spawned no subagents.
- **Scratch location:** `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g16-b_rerun2/`. The prompt file says `g16-b_rerun`; I used `g16-b_rerun2` as the caller instructed, and ignored the earlier reviewer's partial scratch.
- **Unit under review:** T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/g16b_bandlimit_degree_accounting_v1_20261014`

### Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card and source identity | PASS | Zip sha256 is `2d0b6da9…`. The `tasks/G16-B.json` member is `524c7ec4…`. DOSSIER_POSITIVE_BRIDGE.md is `00c1fcb0…`, CAS-16.json is `c8c5c20c…` and COMMON_SPEC.md is `4714827e…`. All match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 1b | Every SOURCE_RECOVERY citation | PASS | Dossier lines 74-79 (B1), 105-110 (r, B3) and 136-149 (B5 and its IBP explanation) say what is claimed. So do 208-216 (bandlimits `L, L_C, L_T`, `D*`, (C3), "surviving associated-Legendre products", "actual weak-kernel degree four"). CAS-16.json lines 37/103 (C02), 38/104 (C03), 45/60/81 (bandlimit assumption), 68 (no spin quadrature) and 250-251 also match. So do DOSSIER_CLAIMS.json 135-147 (DP06) and `htt/src/common/mes_directional_state.py:170-189` (`field_bandlimit` used as ℓ). COMMON_SPEC.md contains no bandlimit definition, as claimed. |
| 1c | Frozen targets written before the first compile | PASS | Birth times (`stat %w`): SOURCE_RECOVERY 12:01:39, FROZEN_TARGETS 12:02:17, run_compile.py 12:02:30, compile_01 12:02:30 (import step), main draft `lean/` born 12:04:38, p01 12:05:00, harness main compile 12:06:10. FROZEN_TARGETS was never modified after creation (mtime equals birth time), and its sha `0dd8b481…` matches AUTHOR_RETURN. Each Lean statement for T1–T8 and N1–N3 is character-identical to the frozen block. No adjustments were recorded and none were needed. |
| 1d | (b) Faithfulness of "scalar bandlimit" | PASS (note N3) | The dossier at line 216 says the C3 proof uses "associated-Legendre products". So the real spherical-harmonic span, with `(1-μ²)^{m/2} P_ℓ^{(m)}(μ){cos,sin}(mφ)` for `0≤m≤ℓ≤L`, is the faithful reading. sympy confirms Rodrigues `P_ℓ` equals the Legendre polynomial and `deg P_ℓ^{(m)} = ℓ−m` for ℓ≤8. The Lean radial factor equals `(−1)^m lpmv(m,ℓ,μ)` to a relative error of 1.7e-15. Dropping normalization and the Condon–Shortley sign leaves the span unchanged. `P_4^{(4)} = 105 ≠ 0`, so N3 is a genuine ℓ=m=4 harmonic. |
| 1e | B5 kernel sign and normalization | PASS | I re-derived by hand that `−∫I[(div F)eeᵀ + Feᵀ + eFᵀ] − 4∫R I eeᵀ = −∫I{[4H−σ:ee]eeᵀ + aeᵀ + eaᵀ + (σe)eᵀ + e(σe)ᵀ}`. A numerical check (sympy polynomial I of degree ≤3, symmetric trace-free σ, GL40×80) leaves a residual of 1.1e-12. `div_S F = −2a·e − 3σ:ee` holds to 6e-30. `weakKernel` and `residualIntegrand = C e_ie_j − T e_ie_j − I K_ij` match (B5) term by term, signs included. |
| 1f | Quantifiers, domain, measure, boundary branch | PASS | T1–T5 are universal in `L, LC, LT`, `H`, `a`, `σ` (all real 3×3 matrices) and `i, j`. Taking σ over all matrices is a strengthening, since the physical symmetric trace-free σ is a special case and membership does not depend on the trace-free identity. The chart is `[-1,1]×[0,2π]` with the nonnegative `Real.sqrt` branch, so the poles are included. The measure `dμ dφ/4π` is C03's, and `sphereMean(1) = quadRule(1) = 1` numerically. |
| 2 | No assumed conclusion; non-vacuity | PASS | The hypotheses are only `I ∈ shBand L` and the like. The `+4/+2/+2` increments are derived by proving span membership of the actual products; numbers are never compared. In my own Lean audit I instantiated `actual_integrands_exact_464` twice. First with I=C=T=1. Second with the genuine fields I=`shCos 4 3`, C=`shSin 6 5`, T=`shCos 4 0`, and nonzero H, a and non-symmetric σ. Both compile. N2 (K₀₀ = 1 at e=(1,0,0)) is genuine. |
| 3a | Hashes of sources and receipts | PASS | Recomputed sha256 matches every AUTHOR_RETURN value: lean `65deb11c…`; `compile_06_main.source` and `probes/p02.lean` are identical to it; AxiomAudit `29332158…`; run_compile `0ea6ff27…`; G16B olean `0cdc5e5d…`; audit stdout `ddc750f8…`; compile_03 stdout `178b0076…` (linter warnings in the C03 source only). All stderr files are empty (`e3b0c442…`). All five C03 source hashes appear in `c03_execution_evidence_v1_20261010/RETURN.json`, and C03 status is FORMALLY_CHECKED. |
| 3b | Exit codes | PASS | compile_01…07 all have exit 0, numbered contiguously. |
| 3c | Forbidden tokens | PASS | A grep of `lean/G16BBandlimit.lean` for sorry, admit, native_decide, `axiom`, set_option, maxHeartbeats, opaque, implemented_by, extern, unsafe, macro, elab and `@[` finds nothing. |
| 3d | Axioms | PASS | My own `ReviewerAudit.lean` runs `#print axioms` on all 41 `theorem`s in the source plus `CAS16C03.fullMonomialTheorem`. 40 report exactly `[propext, Classical.choice, Quot.sound]`. `dstar_464` and `c3_arith_464` depend on no axioms. Exit 0. |
| 3e | (a) Failure retention | PASS_WITH_NOTE (N1) | See N1. The failed p01 source, its merged output and its exit code are all retained. |
| 4 | Independent recompile | PASS | From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain `leanprover/lean4:v4.31.0`) I rebuilt all five C03 modules from copied unchanged sources, then G16BBandlimit, into scratch. Command form: `lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/<M>.olean $S/src/<M>.lean"`. All exit 0 with empty stderr. Oleans: SphereQuadrature, AngularModes, RadialBridge, FullBridge and **G16BBandlimit `0cdc5e5d…` are byte-identical** to the author's and the accepted ones. AngularBridge differs (`aee1c88a…`) only because its compile path differs. Recompiling it in place (`-R <c03/lean>`) reproduces the accepted `5a485d66…` byte-identically, so the difference is a path artefact. |
| (c) | Actual integrand membership and `D*` | PASS | `weakKernel_mem` decomposes the actual (B5) kernel: `[4H − σ:ee]·e_ie_j` lies in P₂·P₂, and `a e`, `(σe)e` lie in P₁·P₁ ⊆ P₄. Then `I·K ∈ P_{L+4}` follows from `shBand ≤ cartSpan` and `mul_mem_cartSpan`. Moment, collision and transport each give `· e_ie_j ∈ P_{·+2}`. `dstar_membership` lifts all four, plus the full R_ij integrand, to `P_{D*}` with `D* = max(L+4, LC+2, LT+2)`. |
| (d) | `D ≤ 8` theorem used by linearity, not re-proved | PASS (note N4) | `quadRule_exact_cartSpan8` runs span induction. Its monomial case is `CAS16C03.fullMonomialTheorem a b c hd`, used as a term from the imported olean. The add case uses continuity-based integrability (`continuous_of_mem_cartSpan` and `sphereMeanFn_add`), which is sound. `quadRule_monomial` and `sphereMeanFn_monomial` hold by `rfl` against C03's `productRule` and `sphereMean`, whose definitions I checked. |
| (e) | Spin quadrature excluded | PASS | Only scalar `ChartFn := ℝ → ℝ → ℝ`. No spin-weighted objects appear, and the exclusion is stated in the docstring and NOT_CLAIMED. |
| num | Numerical cross-check of quadRule | PASS | (1) Random degree-8 polynomials over all 165 monomials, 20 trials: max \|quad − mean\| = 3.0e-14. (2) Actual integrands with random bandlimited I (L=4), C (LC=6), T (LT=4), random H, a and general σ, 10 trials × 9 (i,j). Max errors: moment 1.2e-14, weak 9.9e-14, collision 2.0e-12 (large P₆⁶ scale), transport 1.2e-14, residual 2.0e-12. (3) The negative controls fail as they should. x¹⁰ gives 3.6e-4, z¹⁰ gives −1.5e-3, x⁹ gives 1.5e-3 (Fourier alias at Nφ=9), x⁴y⁴z² gives −3.4e-5. An L=5 weak residual gives 45.7, and I=P₆ (L=6) in the weak residual gives 2.1e-2. This confirms that the `+4` is load-bearing. |

### Blocking findings
None.

### Non-blocking notes
- **N1. Failure retention: met, but outside the harness.** p01 was compiled with `raw/probes/probe.sh`, outside `run_compile.py`. It ran in the same Lake project against `raw/imports`, without `-o`. What survives:
  - the p01 source (`cae95dc0…`),
  - stdout and stderr merged with `2>&1` into `p01.lean.out` (`de769886…`), ending in "exit 1",
  - the fixed p02 (identical to the final source) and `p02.lean.out` "exit 0".

  What is missing: separate stdout and stderr streams, and a JSON receipt with argv and UTC times. File birth times and `probe.sh` stand in for these. The `lean/` directory was born at 12:04:38, and no compile is recorded between that and p01 at 12:05:00. That is consistent with p01 being the first main-module compile, but I cannot prove no other attempt happened elsewhere. Under the G15-B precedent, where lost streams meant UNMET but non-blocking, this unit is better: streams are retained, so it is non-blocking and the attempt counts as retained.

  AUTHOR_RETURN undercounts the failure. It says "2 errors"; the output has 6 error lines from 2 root causes: the `isDefEq` timeout at 288, a cascade of 4 "unknown constant 'G16B.eiej_mem'" errors, and "No goals" at 509.

  Suggested RETURN fields: `failure_retention: RETAINED_OFF_HARNESS_MERGED_STREAM`, `failed_attempts: {probe: 1, harness: 0}`, plus a corrected error count.
- **N2. The c02 blocker's third missing input is only partly discharged.**
  - Inputs (i) (the angular factors behind +4/+2/+2) and (ii) (the bandlimit convention and product-degree lemma) are genuinely discharged.
  - Input (iii) asks for a domain/measure interface "that makes the stated Fourier and radial exactness implications applicable". The chart and measure are supplied, and the implication is proved only for the fixed GL5×Nφ9 rule at D*=8. The general C3 sufficiency (`Nφ ≥ D*+1`, `2Nμ−1 ≥ D*` for every D*) and c02's "next_exact_obligation" (the two quadrature-order implications) remain open.
  - This is honestly listed in NOT_CLAIMED, but the phrases "all three now supplied" (SOURCE_RECOVERY §3) and "missing_items: []" overstate it.
  - The general Fourier-nonaliasing part of CAS-16-C02 remains HOLD.
- **N3. Bandlimit as a global function equality.** `I ∈ shBand L` requires `I` to equal a finite combination of spherical harmonics on all of ℝ², including μ outside [−1,1], where `Real.sqrt` is clamped to 0. Both functionals only evaluate on the chart domain, so this is a harmless choice of representative. It is still a modelling convention the author introduced, because the repository has no definition of "scalar bandlimit".
- **N4. "Not re-executed".** The author rebuilt the five C03 modules from unchanged sources as dependency compiles (compile_01–05), which kernel-rechecks the 165-monomial proof. The olean byte-identity shows nothing changed, and the original C03 raw logs were not touched or re-targeted, so the pitfall's intent is met. Using the accepted oleans directly would have been cleaner.
- **N5. Weak form only.** Only the (B5) integration-by-parts form is formalized. The angular-derivative form `r = (We)·∇I` in (B3) is not, as declared. The increments are upper bounds; sharpness is not shown.
- **N6. CAS tool tasks not run.** The card's wolfram_xact, sympy and sage_singular tasks were not executed by the author; Lean replaced them. My sympy and numpy checks partly cover them independently.

### Not proved / not claimed
- Scientific admission: HOLD.
- General C3 sufficiency for any D* other than 8, and general-order Gauss–Legendre and Fourier exactness.
- The converse inclusion cartSpan ⊆ shBand, and sharpness of +4/+2/+2.
- The (B3) angular-derivative residual form.
- Spin-weighted or polarized quadrature.
- Angular tails, masks, nonpolynomial coefficients, energy quadrature and spectral-window boundary fluxes.
- Physical identification of I, C and 𝒟I with data.
- Any change to the CAS-16 four-axis status (historical CAS_CONFLICT is preserved).
- External attestation of the reviewer runtime.

### Suggested VALIDATION_MATRIX scientific row (not written)
`G16-B | real-SH bandlimit ⊆ Cartesian span; actual (B3)/(B5) integrand membership +4/+2/+2; D*=max(L+4,LC+2,LT+2) membership ∀L,LC,LT; GL5×Nφ9 exact on P_8 by linearity of C03 fullMonomialTheorem → (4,6,4) actual integrands | Lean src 65deb11c…, independent recompile exit 0, G16B olean byte-identical 0cdc5e5d…, 41 theorems axioms ⊆ {propext,Classical.choice,Quot.sound}; B5 IBP identity numeric 1.1e-12; Rodrigues/assoc-Legendre vs scipy 1.7e-15; random deg-8 / actual-integrand quad errors ≤2e-12; controls deg-9/10, L=5, L=6 fail | PASS_WITH_NOTES | notes: failure retained off-harness (merged stream), c02 input (iii) only D*=8 instance, general C3 open | admission HOLD`

### Relevant files
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/g16b_bandlimit_degree_accounting_v1_20261014/lean/G16BBandlimit.lean`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/g16b_bandlimit_degree_accounting_v1_20261014/AUTHOR_RETURN.json`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/g16b_bandlimit_degree_accounting_v1_20261014/raw/probes/p01.lean.out`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/c02_general_degree_input_blocker_v1_20261011/RETURN.json`
- Scratch evidence:
  - `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g16-b_rerun2/ReviewerAudit.lean` and `ReviewerAudit.out`
  - `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g16-b_rerun2/imports/` (the rebuilt oleans) and `abtest/` (the AngularBridge path test)
  - `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g16-b_rerun2/py/num.py`, `py/b5.py`, `py/rod.py`
