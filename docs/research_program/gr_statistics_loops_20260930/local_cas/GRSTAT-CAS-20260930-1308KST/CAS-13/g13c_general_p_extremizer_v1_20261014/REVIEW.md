# G13-C — independent review (verbatim final report of a fresh read-only reviewer)

# G13-C fresh independent review (read-only)

**Verdict: PASS_WITH_NOTES.** Nothing blocking.

- **Reviewer model:** claude-opus-5-5. This is a self-report and is not attested.
- **Scope:** I did not author G13-C. I edited no repository file and ran no state-changing git command. All scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-c_rerun/`.
- **Scientific admission: HOLD.**

Target dir: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/g13c_general_p_extremizer_v1_20261014/` (T below)

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read | PASS | `unzip -p … tasks/G13-C.json` was read. The card requires five lean_steps; acceptance items (i) a separate analytic implication from the Wronskian to the full theorem, (ii) no ℕ or finite-list restriction on p, (iii) the original quantifiers, domain, measure and boundary branches, (iv) kernel build, `#print axioms` and fresh review. Its pitfall says to write the special theorem if Mathlib lacks Chebyshev systems. Package sha256 is `2d0b6da9…af6f` and card sha256 is `e31d34b8…b15e`; both match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 1b | SOURCE_RECOVERY citations | PASS | Recomputed sha256: `TEFF_INTERVAL_SPEC.md` `bc055d39…0fe`, `CAS-13.json` `4e8bdb6c…89b`, `COMMON_SPEC.md` `4714827e…897`, `TEFF_POSITIVE_BRIDGE.md` `f04d96fe…21b`, Paper II PDF `299870d7…5f9`. All match. The cited spec lines say what is claimed: :31 (p>4 target), :35-61 (S121–S123), :75-81 (S124 plus "equality attained"), :83-100 (S125/S126), :103-108 (SE2 and "a Wronskian alone is not a proof"), :147-154. `CAS-13.json:49/:120` name "General real p>4" as an open obligation. `TEFF_POSITIVE_BRIDGE.md:226` restates Prop. 14. `pdftotext` of PDF p.13 shows "Proposition 14 … For p > 4", "attained by the indicated two-point" and "Boundary data are obtained by limits". p.21 shows "extended Chebyshev", "lower-order Wronskians are also positive", "principal-representation result [31]" and "Q_{p,a,u} … interpolate y^p". |
| 1c | FROZEN_TARGETS timing | PASS (note N1) | FROZEN mtime is 21:11:24Z. The first proof-bearing compile (05, p02_wronskian) started at 21:11:43Z. Receipts 01–03 are compiles of the unchanged imports. I read `raw/probes/p01_api.lean` (receipt 04): it contains 18 `#check`s and the two frozen defs only, with no theorem. sha256 of FROZEN is `f83e01fb…b81`, matching AUTHOR_RETURN. |
| 1d | Frozen vs compiled text | PASS | My own `sigcmp.py` normalizes comments and whitespace. It found all 38 frozen declarations (10 defs, 28 theorems) verbatim in the final source, and every theorem statement is followed immediately by `:=`, so the compiled statements are neither weakened nor extended. Diffs 05→06 (probe) and 07→08 (main) change proof scripts or lint only. |
| 1e | p ranges over all real p>4 | PASS | Every interior theorem takes `p : ℝ` and `hp : 4 < p`. `rmoment μ p = ∫ x^p ∂μ` uses `Real.rpow`. There is no ℕ or finite-list restriction anywhere. My audit instantiates the theorems generically for arbitrary real p>4 (R1), at the irrational p=π+1 (R2) and at the near-threshold p=4+1/1000 (R3). All compile. |
| 1f | Wronskian | PASS | **By hand:** the first column is (1,0,0,0), so W equals the 3×3 determinant of derivatives 1–3 of y³, y⁴, y^p. That equals y^{p+1}·det[[3,4,p],[6,12,p(p−1)],[6,24,p(p−1)(p−2)]]. The determinant expands to 36p(p−1)(p−2) − 72p(p−1) − 24p(p−1)(p−2) + 24p(p−1) + 72p = 12p(p²−7p+12) = 12p(p−3)(p−4). The y exponent is 3+4+p−6 = p+1. **sympy 1.14.0** (my `revcheck.py`) gives W = 12p(p−3)(p−4)y^{p+1} (True), and W(p=−1) = −240. In Lean, `wronskian` is a genuine `deriv^[i]` determinant: `wronskian_negative_exponent` shows it can be negative. |
| 1g | Analytic implication W>0 ⇒ sign ⇒ moment theorem (acceptance i) | PASS | `reduced_deriv2_wronskian` proves (p·y^{p−3})''·12y⁶ = W for y>0. `reduced_convex_of_wronskian_pos` takes ∀y>0, W>0 as a hypothesis and concludes StrictConvexOn (0,∞) of p·y^{p−3} (Mathlib `strictConvexOn_of_deriv2_pos`). `minorant_core`/`majorant_core` then use Rolle (`exists_hasDerivAt_eq_zero`) to place a zero ξ of H=φ−3c3−4c4y strictly between the two residual zeros. Together with H(node)=0 and the strict three-point convexity inequality, this gives the + / − / + sign pattern of H, and hence monotonicity pieces of g=y^p−Q. I checked both cases by hand. **Lower** (A=a simple, U=u double, ξ∈(a,u)): g≥0 on [a,ξ] because it increases from g(a)=0; on [ξ,u] because it decreases to g(u)=0; on [u,∞) because it increases from g(u)=0. **Upper** (A=b simple, U=d double, ξ∈(d,b)): g≤0 on (0,d], on [d,ξ] and on [ξ,b] by the mirror argument. T3 (`reduced_convex`) discharges the hypothesis only through `wronskian_chain_pos`. The implication is therefore a genuine, separate lemma; it is not a restated Wronskian. |
| 1h | Hermite interpolant nodes and multiplicities | PASS | `interp A U p` lies in span{1,y³,y⁴}. `interp_conditions` and `interp_slope` give Q(A)=A^p, Q(U)=U^p and Q'(U)=pU^{p−1}: simple contact at a (lower) and b (upper), double contact at u (lower) and d (upper), matching the principal supports {a,u} and {d,b}. I solved the system independently with `sp.solve`; c3 and c4 equal the Lean closed forms (True). interpDet = −(U−A)²(U²+2AU+3A²) ≠ 0. |
| 1i | Same retained moments in integration | PASS | `interior_real_bounds` integrates Q against μ through `integral_hermite` with μ's own m3 and m4 (`hμ.2.2.1/2`). The closed form of L_p and U_p is matched to c0+c3·m3+c4·m4 through G13-A `lower/upper_weight_moments` (the same m3, m4). One (a,b) and one (m3,m4) are used throughout. |
| 1j | Image = [L_p,U_p] by mixtures | PASS | `rsharpInterval_of_extremes` uses G13-B `mix`/`mix_mem`/`integral_mix` with θ=(U−m)/(U−L) and handles L=U separately. This is a real construction of a measure in the fibre for every m in [L,U]. |
| 1k | Strict nesting inside the energy-only interval | PASS | `interior_real_nesting` gives energyLower < L_p ≤ U_p < energyUpper and the Icc inclusion for real p>4. It uses the reviewed G13-B `endpoint_strict_nesting`, which is already stated for real p, with the same a, b and m4. |
| 1l | Boundary branches for real p | PASS (note N3) | `lower_boundary_rsharp` and `upper_boundary_rsharp` hold for every real p, by G13-B Dirac and endpoint rigidity: the boundary fibre is a single measure, and its membership is proved. `closed_region_real_sharp_minimax` covers the whole closed region for real p>4. R5 instantiates the lower boundary at p=−3/2. |
| 1m | Minimax (S125) | PASS | `rfibreMinimax_of_rsharpInterval` lifts C04 `grstat_cas13_minimax` (bound, attainment, and no-better-predictor) with L>0 and L≤U proved (`interior_real_sharp`). |
| 1n | Negative control p=−1 | PASS | W(−1) = −240 < 0 (Lean and sympy). `minorant_fails_negative_exponent`: with nodes 1 (simple) and 2 (double), the interpolant at 3/2 is 2059/2816 ≈ 0.7312 > 2/3 = (3/2)^{−1}; I confirmed this exactly in sympy. 3/2 lies inside the support, so the minorant conclusion genuinely fails there. Extra numerical control (mine): at p=3.5, where W<0, L≤m≤U failed in 600 of 600 fibres. |
| 1o | Witness p=9/2 | PASS | `real_witness` uses the G13-B strict-interior witness (1,2,9/2,8) with p=9/2 ∉ ℕ. By hand: 1 < 4.5 < 8; 4.5^{4/3} ≈ 7.43 < 8 < chord = 8.5. |
| 1p | Consistency with G13-B p=5,6 | PASS | R4 derives G13-B `SharpInterval` (ℕ form) at p=5 and p=6 from `interior_sharp_nat`. R4b shows that G13-B `interior_sharp_minimax` (moment of the lower principal measure at p=5) and G13-C `interior_real_sharp` (rmoment at p=5) give the same `lowerEnd a m3 u 5`. Both compile. |
| 2 | No assumed conclusions, no vacuity | PASS | The interior hypotheses are StrictInterior, 4<p and the node predicates. `interior_real_exists` proves the nodes exist and are unique, and R2/R3 and `real_witness` instantiate the theorems. `hφ` in T2 is a genuine hypothesis: it is discharged for p>4 (R6 at p=9/2) and its conclusion fails at p=−1. |
| 3 | Integrity | PASS | Recomputed sha256 match AUTHOR_RETURN for: lean source `63d777b5…af1`, AxiomAudit `62f7599d…8c2`, run_compile.py, sympy_check.py, SOURCE_RECOVERY, FROZEN, the four oleans, and import sources C04 `5be0cd66…`, G13-A `a64f6c3c…`, G13-B `6d9a9d68…`. For all 9 receipts the source, stdout and stderr hashes match their JSON. Exit codes are 0,0,0,0,1,0,0,0,0, and failed attempt 05 is kept with its error stdout. The final source equals compile_08's source and the audit file equals compile_09's. C04 and G13-A are git-tracked and clean; G13-B is untracked but hash-bound. A grep of T/lean for sorry/admit/sorryAx/native_decide/axiom/set_option/opaque/unsafe/extern/implemented_by/macro/elab/instance finds nothing. |
| 4 | Independent recompile | PASS | Toolchain: `lake env lean --version` reports 4.31.0 (commit 68218e87), and the manifest pins mathlib to `fabf563a…`. From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` I rebuilt Main, MeasureExtremizerBridge, G13BBoundaryMinimax and G13CGeneralPExtremizer from copies in `…/g13-c_rerun/src` into `…/g13-c_rerun/imports`. All exited 0; G13-C produced no output (no warnings). Main olean `61488aba…` and G13-A olean `8c53c481…` are bit-identical to the author's. The G13-B olean differs (`48b21dff…` vs `1e5cf7c3…`) only because it embeds the source path, as the G13-B review already established. **My G13-C olean `d05bbc5c…` is bit-identical to the author's.** My `ReviewerAudit.lean` (sha256 `3630d78c…`) has 45 `#print axioms` lines, one per public theorem, plus 7 instantiation examples (R1–R6). It exited 0 with no warnings, and all 45 theorems depend only on [propext, Classical.choice, Quot.sound]. Run against the author's `raw/imports` oleans, it gives byte-identical output. |
| N | Numerical cross-check (my own script) | PASS | `revcheck.py` (mpmath) drew 600 random 2-, 3-, 5- and 8-atom strict-interior fibres on random [a,b], with nodes found by bisection. At p ∈ {4.001, 4.37, e+2, 5.5, √41, 9.25, 30.3} there were 0 violations of L_p ≤ m_p ≤ U_p (4200 checks). Retained-moment mismatch of the principal measures was ≤ 5.5e−28. At 40 digits the support-grid sign check flagged 6 hits, all at the touch node y=a with p=30.3 and relative size about 1e−25 (cancellation). Rerun at 90 digits: touch error 1.35e−74 and 0 sign violations on the [a,b] grid. Controls: p=3.5 (W<0) gives 600 of 600 violations, as expected. p=2.5 gives 0 violations, which is consistent because W>0 for 0<p<3; that range is not claimed. |

## Blocking findings
None.

## Non-blocking notes
- **N1.** The evidence that FROZEN predates the first proof compile is filesystem mtime only; the directory is untracked in git. The order is consistent (19 s before compile_05) and the content hash is bound in AUTHOR_RETURN.
- **N2.** The analytic implication is a special-case reduction (W = 12y⁶·φ''), not a general ECT/Karlin–Studden theorem. This is allowed by the card pitfall and declared. The lower-order Wronskians W1–W3 are computed and shown positive but are not used in the implication. This is harmless, since only W4 is needed for this system.
- **N3.** Boundary branches use rigidity, not the source's "limits of measures". Weak-limit continuity toward the boundary is not proved. This was declared, and G13-B review accepted the same approach.
- **N4.** `interior_real_nesting` omits G13-B's fibre-image inclusion clause into `EFibre`. It follows trivially from `fibre_inclusion` and was not a frozen target.
- **N5.** The author's `sympy_check.py` and my scripts are ancillary diagnostics, not proofs. The author's own numerics used 40 digits; at large p, high precision is needed near the touch nodes.
- **N6.** The observed runtime and model of the author are unattested (AUTHOR_RETURN says UNKNOWN).

## Not proved / not claimed (scientific admission HOLD)
- Uniqueness of the extremal measures.
- Strict non-degeneracy L_p < U_p in the interior.
- Any theorem for p ≤ 4 (only the p=−1 negative control).
- A general Chebyshev/principal-representation theorem.
- Weak-limit continuity to the boundary.
- Statistics-factor maps between N, E and m3, m4; bandpass/CMB kernels (G13-D); physical or observational relevance.
- Publication or commit state.
- **Scientific admission: HOLD.**

## Suggested VALIDATION_MATRIX scientific-row update (not applied)
`G13-C | all-real p>4 principal extremizer | PROOF: PASS_WITH_NOTES (fresh review, Lean 4.31.0/mathlib fabf563a, olean d05bbc5c reproduced bit-identical, 45 thms axioms ⊆ {propext, Classical.choice, Quot.sound}) | numerics: 0/4200 violations at non-integer p, controls p=3.5 fail / p=−1 fail as expected | scientific admission: HOLD`

## Reviewer scratch files
`/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-c_rerun/`
- `ReviewerAudit.lean` / `.out` / `_authorOleans.out`
- `sigcmp.py`
- `revcheck.py` / `.out`
- `revcheck_dps90.py` / `.out`
- `src/`
- `imports/`
