# G13-B — independent review (verbatim final report of a fresh read-only reviewer)

# G13-B fresh independent review (read-only)

**Verdict: PASS_WITH_NOTES.** I found nothing blocking.

- **Reviewer model:** claude-opus-5-5. This is a self-report and is not attested.
- **Scope of review:** I did not author this task. I edited no repository file and ran no state-changing git command. All scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-b_rerun/`.
- **Scientific admission: HOLD.**

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read, sources resolved | PASS | `unzip -p … tasks/G13-B.json` read. Lean steps 1–5, acceptance items and the pitfall "general-p sharpness only p5/p6 until G13-C" were taken from the card. |
| 1b | SOURCE_RECOVERY citations | PASS | `TEFF_INTERVAL_SPEC.md` sha256 = `bc055d39…4fd0fe`, which equals the identity recorded at `CAS-13.json:26`. Each cited range holds what is claimed: :18-31 (common prior), :35-40 (S121), :42-50 (S122), :52-61 (S123), :75-81 (S124), :83-93 (S125), :95-100 (S126), :149-155 (negative controls). `CAS-13.json` lines 86/87/100/107/108/126 are the MOM-PRIOR / MOM-BOUNDARY strings. `TEFF_POSITIVE_BRIDGE.md:226` is the Prop. 14 paragraph. G13-A lines 88-94, 223/250, 278-279 and 810-811 match. The paper PDF sha256 is `299870d7…b5f9`. `pdftotext` on p.13 confirms "Boundary data are obtained by limits of the measures…" and "Both comparisons use the same prior". pp.20-21 confirm "single temperature and an endpoint mixture" and "exact minimax value on the stated class". |
| 1c | FROZEN_TARGETS timing | PASS (note N1) | FROZEN mtime is 2026-10-13 11:51:09Z. The first proof compile (04) started 20:50:22Z. The file is about 4 minutes later than receipts 01–03 (11:46–11:47Z), but those are compiles of the two unchanged imports plus API probe `p01_api.lean`. I read that probe: it has 16 `#check`s and one trivial `example` (rpow_natCast), and no target. The frozen file's sha `dc34b809…` matches AUTHOR_RETURN. |
| 1d | Frozen vs compiled text | PASS | My script `sigcmp.py` normalises whitespace and comments. All 26 theorem signatures and 14 definitions match the compiled source exactly (40/40). The only differences between failed attempt 04 and attempt 05 are proof scripts at lines 572, 599 and 880-881 (diff verified). |
| 1e | Faithfulness: lean_steps 1–2 (region and boundary) | PASS | `region_exact` gives NEFibre nonempty ⇔ ClosedRegion in both directions. `region_strata` gives a three-way split. The lower collapse is proved by tangent rigidity: (x−r)²(3x²+2rx+r²) = 3x⁴−4rx³+r⁴ (sympy True), whose integral is 3(m4−r⁴). The upper collapse uses the chord gap factorisation (x−a)(x−b)(b−a)·K with K>0 (sympy True). Both collapse theorems hold for **every p : ℕ**. Their only hypotheses are fibre membership plus the boundary equation; p does not appear, and there is no hidden p restriction. Neither is vacuous: the Dirac and the endpoint mixture are shown to be members. At the corner m3=a³ the two collapses agree (chordWeight=0 gives δ_a). |
| 1f | lean_step 3 (energy-only, real p>4) | PASS | Lower bound: Jensen for t^{p/4}, convex since p/4>1, applied to t=x⁴, giving m4^{p/4}. Upper bound: chord majorant of t^{p/4} on [a⁴,b⁴], integrated. Both are the correct bounds, and they use the same (a,b) and the same m4 as NEFibre. Attained by δ_{m4^{1/4}} and by the two-point measure on {a,b} with weight (m4−a⁴)/(b⁴−a⁴); the closed-form identity is sympy True. |
| 1g | lean_step 4 (inclusion, nesting) | PASS | `fibre_inclusion` holds by definition, with one (a,b) and one m4. `endpoint_strict_nesting` (real p>4) uses strict Jensen on {a⁴,u⁴} and the strict chord at d∈(a,b). `interval_nesting_p56` is stated only for p=5 or 6, as the frozen scope requires. Statistics and fugacity are abstracted out, per spec :29 ("factors removed"). |
| 1h | lean_step 5 (C04 composition) | PASS | `fibreMinimax_of_sharpInterval` lifts `grstat_cas13_minimax` with τ=2LU/(L+U) and ε=(U−L)/(U+L), matching S125. Its three clauses are the bound, attainment, and "no predictor t beats ε". The interior case uses p=5,6 only, with 0<L≤U proved. The L=U branch covers both boundaries for all p:ℕ, with ε=0 and τ=L. `closed_region_sharp_minimax` is limited to p∈{5,6}. |
| 1i | Negative controls | PASS | **N1.** sympy gives lim (x⁴−a⁴)/(x³−a³) = 4a/3, while Lean's 0/0 evaluates to 0. Grep shows `node_ratio_zero_div_zero` is referenced by no other theorem. LowerNode and UpperNode only ever appear together with StrictInterior, which forces a<r<u and d<r<b, so no denominator is zero. **N2** is a real counterexample, checked in exact rationals: m5=33/2 equals EU[1,2]=33/2, and EU[1,7/4]=16927/1144≈14.796<33/2, with (7/4)⁴=2401/256≥17/2. **N3/N4:** the interior witness (1,2,9/2,8) and the chord witness (1,2,9/2,17/2) were both verified. |
| 2 | No assumed conclusions, no vacuity | PASS | Hypotheses are only domain facts (0<a<b, region membership, node predicates, p∈{5,6}). My audit file `ReviewerAudit.lean` compiles three instantiations: (i) at the interior witness, actual nodes u,d satisfy SharpInterval(p=5), FibreMinimax(p=6) and energyLower<L₅; (ii) `lower_boundary_sharp` at m3=(3/2)³, p=7; (iii) the L=U branch of `closed_region_sharp_minimax` at the chord witness, p=6. |
| 3 | Integrity | PASS | Every recomputed sha256 matches AUTHOR_RETURN: sources, all 6 receipts (source/stdout/stderr), run_compile.py and the 3 oleans. The imports are tracked and clean in git at HEAD `4dbe5886` (no `git status` output). Exit codes are 0,0,0,1,0,0, and failed attempt 04 is kept along with its error stdout. The author's audit covers all 57 theorems, each depending only on [propext, Classical.choice, Quot.sound]. Grepping for sorry/admit/native_decide/axiom/set_option/opaque/extern/unsafe finds only the comment "axiom audit". |
| 4 | Independent recompile | PASS | `lake env lean --version` reports 4.31.0, and the manifest pins mathlib to `fabf563a…`. I rebuilt Main, MeasureExtremizerBridge and G13BBoundaryMinimax from copies into scratch; all exited 0, with only the two recorded unused-variable warnings. The rebuilt Main.olean and G13-A olean are bit-identical to the author's (`61488aba…`, `8c53c481…`). The G13-B olean from my copy path is deterministic (`5e5d1d8c…` twice). It differs from the author's only because the olean embeds the source path: building in place from the original path into scratch reproduces the author's `1e5cf7c3…` exactly. My audit has 57 `#print axioms` lines and 3 instantiation examples, all allowed axioms only, exit 0, no warnings. It gives the same result against the author's oleans. |
| N | Numerical cross-check | PASS | `numcheck.py` (mpmath, 40 digits) drew 3000 random 2-, 3- and 4-atom measures on random [a,b]. There were 0 region violations. Energy-only bounds held with 0 violations for p∈{4.3, 5, 6, 7.7, 12}. Of the 3000 draws, 3000 were in the strict interior. For those, L_p≤m_p≤U_p had 0 violations at p=5,6, and also at the untargeted p=4.3, 7.7, 12, which is consistent with G13-C but not a proof. Nesting EL<L, U<EU had 0 violations, and the minimax bound had 0 violations. At the witness, u=1.8392867552 and d=1.3438130758; both principal measures reproduce (4.5, 8.0). For p=5, L,U = 14.43750, 14.65619 inside EL,EU = 13.45434, 15.46667. Approaching each boundary, U₅−L₅ shrinks linearly in distance (8.5e-9 at 1e-8) toward r⁵=12.2655640 and the chord value 16.5. This agrees numerically with the rigidity values. |

## Blocking findings

None.

## Non-blocking notes

- **N1 (provenance timing).** FROZEN_TARGETS.md predates the first *proof* compile (04) but not receipts 01–03, and its timing rests only on filesystem mtimes (T is untracked). The "#check-only" description of probe 03 is slightly inaccurate because of one trivial `example`. The interrupted-attempt chain is disclosed but cannot be attested.
- **N2 (boundary limits).** The card's lean_step 2 explicitly allows direct rigidity, and that is what was used. Continuity of the interior L_p, U_p and the principal measures toward the boundary values (paper p.13: "limits of the measures") is not formalised; I checked it numerically only.
- **N3 (real-p boundary).** Boundary sharpness and the L=U minimax are stated for p:ℕ via `moment`, not for real p via `rmoment`. The real-p case follows immediately from the collapse theorems but is not stated.
- **N4 (energy-only "sharp").** For EFibre, bounds and attainment are proved for real p>4. Exact image equality (every intermediate value attained) is not stated.
- **N5 (N2 strength).** The cross-prior control sits at a chord-boundary point, with a support [1,7/4] that cannot host the measure. It is valid but minimal; an interior-point control would be stronger.
- **N6 (card tool_tasks).** Wolfram, sympy and Sage were NOT_RUN by the author. My sympy checks cover the gap identity, the chord factorisation, the weights and the N1/N2 numbers, but no Sage boundary-strata certificate exists.
- **N7 (model abstraction).** "Same statistics/fugacity" is represented as the same (a,b) and the same retained (m3, m4). The ξ, η₀ factor maps are outside the model and declared not claimed.

## VALIDATION_MATRIX scientific-row update (to be applied by the owner)

`G13-B | scientific | proof: KERNEL_CHECKED (author compile_05 exit 0; independent fresh rebuild exit 0, Main/G13A oleans bit-identical, G13B olean reproduced bit-identically from original path) | axioms: propext/Classical.choice/Quot.sound only (57/57, author + reviewer audit) | faithfulness: 40/40 frozen items textually identical; T2 all p:ℕ by rigidity; T3 real p>4 same (a,b,m4); T4/T5 interior p∈{5,6} only | numerics: 3000 random 2–4-atom measures, 0 violations | review: fresh independent PASS_WITH_NOTES (N1–N7), reviewer claude-opus-5-5 self-reported | scientific admission: HOLD`

## Not proved / not claimed

- Scientific admission (HOLD).
- General real p>4 sharpness of [L_p, U_p] (G13-C).
- Interior sharp interval and minimax for p∉{5,6}.
- Weak or limit continuity from interior principal measures to the boundary.
- Real-p (`rmoment`) boundary sharpness statement.
- Image equality for the energy-only fibre.
- Statistics-factor maps N,E ↔ m3,m4.
- Bandpass and observation kernels (G13-D).
- Publication or commit.
- Observed runtime identity of the author and of this reviewer.

## Relevant paths

- Task directory: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/g13b_boundary_minimax_v1_20261013/` (`FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `lean/G13BBoundaryMinimax.lean`, `raw/compile_0[1-6]_*`, `raw/AxiomAudit.lean`, `raw/imports/*.olean`)
- Imports: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/lean/Main.lean` and `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/g13a_measure_extremizer_bridge_v1_20261011/MeasureExtremizerBridge.lean`
- Spec: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md`
- Reviewer scratch, all under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-b_rerun/`:
  - `ReviewerAudit.lean`, `audit.out`, `audit_authorolean.out`
  - `sigcmp.py`, `numcheck.py`
  - `imp/` (rebuilt oleans), `imp4/` (original-path rebuild)
  - `rb_*.out`

