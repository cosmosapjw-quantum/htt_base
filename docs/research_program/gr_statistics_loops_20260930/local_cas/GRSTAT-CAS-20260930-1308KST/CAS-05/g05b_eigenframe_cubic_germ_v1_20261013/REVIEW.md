# G05-B — independent review (verbatim final report of a fresh read-only reviewer)

# G05-B independent review: isolated eigenframe IFT and cubic-germ realization

**Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`). This was a fresh, read-only review: I edited no repository files, ran no state-changing git commands and spawned no subagents. Scratch files are under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g05-b_rerun/`.

**Target:** `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/g05b_eigenframe_cubic_germ_v1_20261013/` (called T below).

## Verdict: PASS_WITH_NOTES

There are no blocking findings. Scientific admission stays at HOLD.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read first | PASS | Read `unzip -p HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip …/tasks/G05-B.json`: scope, 4 lean_steps, 4 acceptance items, 2 pitfalls. |
| 1a | Source-recovery citations | PASS | Every citation re-read. `ENERGYFRAME_THEOREMS.md` (sha dd66030a…6855): lines 7, 11, 27, 62 and 91 match verbatim. EF3 is at lines 110–163 (statement 114, construction 130, 2-jet claim 138, formula 159). `ENERGYFRAME_CLAIMS.json` sha 43d64e8b…a3e6 matches, and the EF3/EF6 entries match. Recomputed shas also match for `CAS-05.json` (424bc10c…c197), `CAS-04.json` (139c4b5b…0895; line 251 is the EF6 string), `COMMON_SPEC.md` (4714827e…1897; lines 4 and 23), `SOURCE_RECOVERY.md` (60defdcf…8ce2) and `run_compile.py` (0a2f2787…8b51). The `STATEMENT_ALIGNMENT.md` quote is verbatim at lines 49–50. |
| 1b | Frozen targets: faithful to the card and EF3 | PASS | **Card acceptance item 1 (one construction):** G1 `EF3_local_germ` puts formal jet J, actual metric `gCub` and actual IFT eigenfield `u` into one existential. **Admissibility:** every real `k` (only the 4×3 block i≠0 is used), with hypotheses b>0, Λ<3b, κ>0. The radius `r` is existential after (b,Λ,κ,k,n), so it is explicitly member-dependent, matching the EF3 card ("neighbourhood may depend on prescribed derivative"). **Signs and normalizations checked by hand:** (−+++) signature; Ricci `R_ai = ∂_cΓ^c_ia − ∂_iΓ^c_ca + ΓΓ − ΓΓ`, which matches COMMON_SPEC:23 contracted on the first and third indices; T=(G+Λg)/κ (line 11); Tu=−εu with g(u,u)=−1 and u⁰>0. The conformal baseline at the origin gives G₀₀=6b and G_ii=0, so ε=(6b−Λ)/κ, p=Λ/κ and the gap is 6b/κ. q_i=−6b k_{0i} and M_ij=−6b k_{ji}, as in source line 130. Differentiating the eigen-equation gives ∂_μu^i = −∂_μT^i_0/(6b/κ) = k_{μi}, which is formula (5). |
| 1c | Recorded choices and adjustments | PASS (notes) | These are disclosed in SOURCE_RECOVERY: finite C^n regularity instead of C^∞; rates use the coordinate frame at 0, which is proved η-orthonormal with E₀=u(0); self-adjointness is needed only at the IFT base point; global uniqueness (G2) is a separate target. AMENDMENTS.md records no changes to frozen statements. None of these is a silent weakening. The C^n choice is weaker than the source's "smooth" but is disclosed (note 1). |
| 1d | Card-specific points | PASS | **J1** uses the real `fderiv`-built `Ein` (G05-A `pd`, `ginv` as matrix inverse, `Gam`, `Ric`) and equals `CAS05C03.dEinstein (thirdJet g)`; `dEin_cub` then reaches `closedDG` through the accepted `full40_first_Einstein_coefficients`. **F3** `borderedG` uses `bil (g p.1)`, the curved metric, not η. **S1** is a genuine proof: Γ symmetry, re-indexing of the ΓΓ term, `trGam`, `pd_ginv` (∂g⁻¹ = −g⁻¹∂g g⁻¹ derived from g⁻¹g=1 near x), and Mathlib `isSymmSndFDerivAt`. **Rates:** `covD` is `fderiv ℝ u x X a + Γ^a_{ce}X^c u^e` applied to the IFT branch `u`; `rate_origin` differentiates the eigen-equation of the actual `u` on the neighbourhood V. |
| 1e | Independent numerical check | PASS | Script `num/check.py` (mpmath, 40 digits) uses the exact metric e^{2φ₀}η + H from eq. (6), the actual Christoffel/Ricci/Einstein tensors, and a direct eigen-solve of g⁻¹T. Rates come from central finite differences (h=1e−12). Three random rational members (b, Λ<3b, κ, k): u(0)=e₀ and ε(0)=(6b−Λ)/κ in all three. max\|rate − k_{μi}\| = 2.1e−21, 2.1e−21, 5.8e−22. max\|∂_μT_{0i}(0) − (q\|M)/κ\| ≤ 3.2e−21. Ricci antisymmetry ≤ 9e−41 at a generic point. |
| 1f | Negative controls | PASS (note 2) | **N1:** at b=0 the metric is flat and T^a_b = (Λ/κ)δ, so ε+p=0 and the predicate `RestGapG` really fails. This shows the gap hypothesis is not trivially true. **N2:** k≡0 versus k₀₁=1 gives the same 2-jet and the same u(0), but rates 0 versus 1. This genuinely instantiates the G1 rate clause. |
| 2 | No assumed conclusions; non-vacuity | PASS | No hypothesis assumes the eigenfield, its smoothness, the rate identity, the derivative stress or Ricci symmetry. Hypotheses of F3 (g, T C^n at x0; symmetric g; self-adjoint, eigen and gap at x0) and S1 (C², symmetric, det≠0) are all discharged in G1 and G2 from `gCub`, with det≠0 obtained from the Lorentzian property. In my own audit I instantiated G1 at b=1, Λ=0, κ=1, k≡1, n=1 and obtained `rate … 0 1 = 1` and `rate … 3 2 = 1`. N1 has an unused hypothesis `hκ` (linter warning), which is harmless. |
| 3a | Hash integrity | PASS | All 21 receipts were recomputed: snapshot, stdout and stderr shas all match their `.json`. Final sources match receipts 12, 18, 19 and 20 and `check_frozen.out.json`. All 9 `raw/imports` oleans match their receipts. Import sources match the reviewed hashes: C03 f10a9fdc…, G05-A 634d4006…/f8f593a7… (also in G05-A `RETURN.json`), G04-A 4d36cde1…, Proof 8a870e4e…. |
| 3b | Exit codes and failed attempts kept | PASS | Failures at 06, 07, 10, 11, 13 and 16 (rc=1) are preserved with their sources. 08 has rc=0 with a `sorry` warning at G05BJet:224 (`dGam_jet`). Final dependency order is IFT(12) → Jet(18) → Symm(19) → Germ(20) → audit(21). |
| 3c | Forbidden constructs | PASS | grep for sorry, admit, native_decide, axiom, set_option, implemented_by, extern, unsafe and opaque returns 0 hits in `T/lean/*.lean` and `raw/AxiomAudit.lean`. The `sorry` exists only in the snapshots of attempts 06–08. |
| 3d | Axioms | PASS | The author's audit (98 theorems) gives only [propext, Classical.choice, Quot.sound]. My audit covers 110 declarations (all 98 theorems plus 12 defs) with the same single axiom set; no `sorryAx`. |
| 3e | Freeze before compile | PASS (note 4) | FROZEN_TARGETS sha b26beecc…82fc equals `raw/FROZEN_TARGETS.sha256`. Frozen at 21:04:04Z (file mtime 21:03:58Z). The first own-module compile (06) started at 21:07:08Z. Import-only compiles 01–03 started before the freeze. |
| 3f | Frozen statements unchanged (27/27) | PASS | `check_frozen.py` reports 27/27, but it is a whitespace-normalized substring check. I closed that gap in Lean: every one of the 16 frozen theorems was restated verbatim as `chk_*` and discharged by `apply <declared> <;> assumption`, so each declared theorem is at least as strong as its frozen form. `rfl` checks pass for `covD`, `rate`, `RestGapG` and `Tmix`. |
| 4 | Independent recompile | PASS | Run from `/home/cosmosapjw/lean_oracles/viii_oracle`, Lean 4.31.0 (commit 68218e87), mathlib rev fabf563a. I rebuilt all 5 imports from their original sources into `scratch/imp`, then compiled Jet, IFT, Symm and Germ in that order with `lake env bash -c "LEAN_PATH=<scratch/imp>:$LEAN_PATH lean -R <scratch/src> -o <scratch/imp>/<M>.olean <scratch/src>/<M>.lean"`. All rc=0; only the two linter warnings in Germ appear, identical to receipt 20. `ReviewAudit.lean` rc=0 (sha 8c8b3314…; stdout sha 50edd61e…). The Jet, IFT, Symm, Cubic and G04A oleans are bit-identical to the author's; Germ, C03, Conf and Proof oleans differ (note 7). |

## Blocking findings

None.

## Non-blocking notes

1. **Regularity is finite C^n with an n-dependent radius.** The source says "smooth". C^∞ on one ball follows mathematically from G2 uniqueness plus the IFT at every ball point, but it is not formalized. This is disclosed in `not_claimed`.
2. **N1 is a weak control.** It works at the degenerate b=0 flat metric, outside the admissible regime, and shows only that the gap hypothesis can fail, not that the IFT conclusion fails without it. A stronger optional control would show non-uniqueness of the future eigenvector at b=0.
3. **`check_frozen.py` is substring-based.** It could be satisfied by text inside a comment or by a prefix of a longer type. My Lean restatements settle this for the current sources. Suggested harness fix: add `example`/`chk_` restatements to `AxiomAudit.lean`.
4. **The freeze timestamp rests only on file mtime and an in-directory sha file.** The directory is untracked in git, so there is no external anchor. The freeze predates every own-module compile but not import compiles 01–03; this is harmless because no target content was involved.
5. **Not formalized (and not claimed):**
   - saturation of (1) at (0) ("Each member saturates");
   - "every (θ,σ,ω,A)" as a stated equivalence;
   - rates relative to an arbitrary orthonormal spatial frame at 0 (only the coordinate frame);
   - the Bianchi "no lost direction" sentence (automatic, since the source is an actual metric).
6. **The card's tool axes (Wolfram/xAct, sympy block inverse, Sage 12-basis) were not executed by the author.** My mpmath check partly covers the jet → eigenfield-rate mapping only.
7. **Olean outputs are not fully bit-reproducible** (4 of 9 differ on rebuild, sources identical). This does not affect validity; record it so a mismatched olean sha is not later read as tampering.
8. **The author's observed runtime and model are unattested**, as the author's own return already states.

## VALIDATION_MATRIX scientific row (suggested content; I did not write it)

`G05-B | EF3 cubic-germ + curved isolated-eigenframe IFT | PASS_WITH_NOTES (fresh review, claude-opus-5-5, 2026-10-14) | formal: 27/27 frozen verbatim, 16/16 theorem restatements typecheck, axioms {propext, Classical.choice, Quot.sound}, independent recompile rc=0 | numerical: exact-metric mpmath rate check max|rate−k|≤2.1e−21 (3 random members), ∂T_0i=(q|M)/κ ≤3.2e−21, Ricci asym ≤9e−41 | limits: finite C^n, member-dependent radius, coordinate frame at 0, no saturation/uniform radius/C^∞ | scientific admission HOLD`

## Not proved (out of scope or open)

- Scientific admission: **HOLD**.
- C^∞ eigenfield on a single neighbourhood; analytic regularity.
- A uniform (member-independent) radius; the EF2 radius obstruction for the cubic family; persistence at or beyond Λ=3b.
- Saturation of EF1 inequality (1) at (0); the explicit (θ,σ,ω,A) parametrization.
- The CAS-06 part of EF6; "metric 3-jet determines first jet" as a general theorem; EF5/EF5c fixed-matter statements.
- Four-axis tool acceptance (Wolfram/sympy/Sage); the full CAS-05 parent theorem; novelty/priority.

## Files

- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/g05b_eigenframe_cubic_germ_v1_20261013/lean/{G05BJet,G05BIFT,G05BSymm,G05BGerm}.lean`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/g05b_eigenframe_cubic_germ_v1_20261013/{FROZEN_TARGETS.md,SOURCE_RECOVERY.md,AMENDMENTS.md,AUTHOR_RETURN.json,raw/}`
- My audit file: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g05-b_rerun/src/ReviewAudit.lean`
- Compile logs and audit output: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g05-b_rerun/logs/`
- Numerical check: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g05-b_rerun/num/check.py` and `check.out`

