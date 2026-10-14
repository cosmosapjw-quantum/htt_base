# P04-A — independent review (verbatim final report of a fresh read-only reviewer)

## P04-A independent review: flux_vector_codazzi_v1_20261014

**Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`, as stated in my system context). This was a fresh, read-only review: I did not author P04-A, edited no repository files, ran no state-changing git commands and spawned no subagents. Every scratch file is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p04-a_rerun/`.

### Verdict: PASS_WITH_NOTES (nothing blocking)

- **Proof state:** FORMALLY_CHECKED_SCOPED. It is confirmed by my independent recompile and my own axiom audit.
- **Publication:** NOT_PROMOTED.
- **Scientific admission:** HOLD.

### Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card scope and convention recovery | PASS | I checked every citation in SOURCE_RECOVERY.md line by line, and all the hashes match: CAS_CONTRACT `904d95fe…`, PORT_MAP `d0050aa3…`, geometry_findings `070ddc34…`, CLAIMS `9750221f…`, INDEPENDENT_REVIEW `f145a8fb…`, relativistic_kinematics.py `9ae767f9…`. The cited lines say exactly what is claimed: geometry_findings L7, 9-10, 39, 51, 53, 57, 59, 61, 63, 67-71, 87-92; CAS_CONTRACT L4-5 and L50-61; PORT_MAP L155-168; CLAIMS L113-139; INDEPENDENT_REVIEW L51-57; flux_tilt.wl L1-17. One mislabel, see note N6. |
| 1b | FROZEN_TARGETS written before the first compile | PASS | FROZEN mtime is 06:59:34 KST. compile_01 started 21:59:39Z (06:59:39 KST) and the first main compile (05) at 11:56 KST. sha256 `dd803c80…` equals the value in AUTHOR_RETURN, and the file was not edited in the resumed run. |
| 1c | Lean definitions match the source conventions | PASS | I checked the `#print` of every definition. `perfectFluid` is w·(g u)(g u)ᵀ + p g, i.e. T_ab = (ε+p)u_a u_b + p g_ab. `projDown` = 1 + (g n)nᵀ, i.e. h_a^b = δ + n_a n^b. `normalFlux` = -(h·T)·n, i.e. J_a = -h_a^b T_bc n^c. `extrinsicDown` = -h·∇n·hᵀ, i.e. K_ab = -h h ∇n (ADM sign, geometry_findings:53). `velJet` is ∂_a u_b - Γ^c_ab u_c. `sliceNormal` gives n^0 > 0, future directed. `ricci` is R_bd = R^a_bad. |
| 1d | Exact γ² coefficient (A1, A2, A5) | PASS | Lean proves J = wγ²(gβ), E_N = wγ² - p and γ² = 1/(1-β²). Against the repo code, over 2000 random (β, ε, p) with w > 0: `perfect_fluid_normal_projection` J vs wγ²β has max relative error 3.9e-16, E has 1.3e-15 and the rank-one S has 2.2e-14. A direct evaluation of the Lean `normalFlux` definition (matrix form, η, n = e0) vs wγ²β_a gives 3.4e-16, and J_0 = 0. |
| 1e | Scalar inverse: sqrt-denominator positivity and the r = 0 branch (B1-B7) | PASS | B1 (0 < 1+√(1+4r²) for all real r) and B2 (f(0) = 0) are in place, which meets card acceptance 1. B3 gives [0,1), B4 the solution, B5 uniqueness. `flux_to_beta(|J|,w)` vs \|β\| has max error 2.2e-16. `flux_to_beta` vs the Lean `betaOfRatio` formula also has 2.2e-16. At 50 digits, the residual of f(r)/(1-f²) - r is below 1e-39 for r from 1e-8 to 1e6. `flux_to_beta(0,1)` = 0. |
| 1f | Vector inverse, zero and nonzero branches (C1-C4) | PASS | Zero branch (C1) and nonzero-direction branch (C2) are explicit. C3 gives both β_a and β^a. C4 instantiates this for every subluminal Minkowski boost. Numerically, f(\|J\|/w)/\|J\|·J - β has residual 5.6e-17. |
| 1g | Counterflow pitfall (D1-D3) | PASS | D3 negates the full universally quantified converse, keeping every single-fluid hypothesis (w > 0, n·β = 0, u·u = -1) for both components. It does this with an explicit witness: β = ±(0, ½, 0, 0), γ² = 4/3, w = 1, p = 0. The total flux vanishes and the component flux does not. Numerically, J1 = (2/3, 0, 0) and J1 + J2 = 0. This is a genuine refutation. |
| 1h | E3 is derived, not assumed | PASS | `einstein_mixed_gaussian` comes from the definition of `ricci` through `codazzi_core`. Every hypothesis of `codazzi_core` is a proved Gaussian-chart lemma (`chr_symm`, `extrinsicMixed_gauss('/_0q/_p0)`, `dK_eq'`, `dK_0q`, `dH_eq`); none is a physics hypothesis. Independent sympy check (`sym_codazzi.py`), which mirrors every Lean definition on a random non-flat Gaussian metric: the residual G_0i + codazziLHS_i is exactly [0,0,0], while codazziLHS itself is nonzero, e.g. -2590445360039/6712113936528. The E2 residual K_ab + ½∂₀g_ab is {0}, and the E4 residual is 0. The Ricci convention is MTW: for FLRW with ȧ = ä = 1 I get R_00 = -3, R_11 = 3, G_00 = 3. The sign agrees with Gourgoulhon, γ^μ_α n^ν R_μν = D_αK - D_μK^μ_α. |
| 1i | E5: Einstein hypothesis is explicit | PASS | `hE : ∀ b d, einstein … + Λ g = κ T` appears in the theorem type. Λ drops out because g_0i = 0, which matches source L63. |
| 1j | Card lean_step 4 at chart level | PASS_WITH_SCOPE_NOTE | The identity is derived only in a Gaussian normal chart (g00 = -1, g0i = 0 on an open U). My sympy check on a general chart, with nonzero lapse and shift, found that the same Lean-defined codazziLHS equals -h_a^b n^c R_cb (and -h n G) with residual exactly 0. So the definitions are covariant and the restriction limits only what the proof covers. Any downstream use must still carry the note "Gaussian normal chart; general slicing, coordinate invariance and existence of such charts not formalized". |
| 1k | Adjustments to the frozen targets | PASS | Changes are binder presentation, `open Classical`, and D2 turned from prose into a formal statement; these are faithful. B6 assumes w ≥ 0, B8, A6 and A7 assume w ≠ 0, and κ and Λ are arbitrary. Each is a strengthening relative to the card's w > 0. I found no silent weakening. |
| 2a | Hypotheses do not assume conclusions | PASS | E5 takes the Einstein equation and derives the Codazzi side through the derived E3. In E6, `hpos` (β spacelike) is an explicit, disclosed hypothesis. |
| 2b | Non-vacuity | PASS (Lean only for the flat case) | E8 Minkowski satisfies GaussianChart, hdiff and hE (T = 0). I also proved in Lean that E8 feeds E5, giving codazziLHS = 0 (an `example` in `ReviewAudit.lean`). C4 and D2 give pointwise witnesses. There is **no Lean non-flat or tilted witness for E5/E6**. I built one symbolically instead (`sym_witness.py`): a Gaussian polynomial metric that solves G(0) = κ(w u u + p η) with w = 1, p = 1/3, β = (0, 3/5, 0, 0). It has Einstein residual {0}, is non-flat, and gives codazziLHS = [0, 15/16, 0, 0] = κwγ²β_a. Then `flux_to_beta(15/16, 1)` = 0.6. So the E6 hypotheses are satisfiable, but only outside Lean. |
| 2c | Acceptance 2: hypotheses visible in theorem types | PASS | Checked with `#check`: 0 < w, hn, hβ, hu, hpos, GaussianChart, hdiff and hE all appear in the types. In E6 the source is a single `perfectFluid`. |
| 3a | Hashes | PASS | My recomputed sha256 equals the AUTHOR_RETURN value for: the Lean source `92d0440b…`, AxiomAudit `f96e7c6a…`, run_compile.py `9bc9e7d0…`, all nine receipts' source/stdout/stderr, all five author oleans, and the four import sources. compile_08's source equals lean/FluxVectorCodazzi.lean. |
| 3b | Exit codes and failed attempts kept | PASS | 01-04 exit 0; 05, 06 and 07 exit 1 (kept, with stdout); 08 and 09 exit 0. All stderr files are empty. compile_08 has 21 warnings (unused simp args, deprecated `push_neg`, unused variables), no errors and no `sorry`. |
| 3c | Forbidden constructs | PASS | grep for sorry, admit, native_decide, axiom, set_option, sorryAx, unsafe, implemented_by and extern over the main source and all four import sources found nothing. |
| 3d | Axioms | PASS | My own audit file prints axioms for all 82 theorems in the module. All 82 report exactly [propext, Classical.choice, Quot.sound] (one line was wrapped in the output; I checked it). |
| 4 | Independent recompile | PASS | I copied the sources to scratch `src/`, rebuilt all four imports from source, then the main module, from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` with Lean v4.31.0 and mathlib `fabf563a…` (checked in lake-manifest). Command: `lake env bash -c "LEAN_PATH=$R/imports:$LEAN_PATH lean -R $R/src -o $R/imports/<M>.olean $R/src/<M>.lean"`. All five exited 0. The olean hashes for PortCas01, VelocityJetRest and FluxScalarInverse are byte-identical to the author's. VelocityJetDecomposition and FluxVectorCodazzi oleans differ in bytes. That is not a validity issue (see N7). |

### Stop-rule decision: not violated in substance

The rule says: "same substantive failure repeats twice after a real change → stop". For `gauss_ginv`:
- It failed in 05.
- 06 made a real change to it (added `Matrix.one_apply`) and it still failed. That is one repeat after a real change.
- 07 did not touch it. I confirmed that the 06→07 diff changes only `codazzi_core` and `homogeneous_core`.
- 08 made a second real change and it passed.

I also confirmed the author's explanation. `run_compile.py` prints only the last 8000 bytes of stdout. In the 06 log the `gauss_ginv` errors sit at byte offsets 2775–5343, but the printed tail starts at 7117, so the author never saw them.

Counting per lemma, there was one repeat after a real change, so the rule did not fire. A literal file-level reading could count 07 as a second repeat. The author disclosed this. It is a non-blocking process note.

### Blocking findings

None.

### Non-blocking notes and recommended fixes

- **N1 (scope).** The E-section (E1'-E7) holds only in a Gaussian normal chart. Any claim about card lean_step 4 must say: "contracted Codazzi derived in a Gaussian normal chart; general slicing (lapse and shift), coordinate invariance and existence of Gaussian charts not formalized". My numerical check suggests the definitions are already covariant. If a later task wants this generalised, the smallest step is a chart-free proof of E4 (codazziLHS = -h n Ric).
- **N2 (vacuity).** E8 is a flat witness only. The E5/E6 hypotheses with w > 0 and β ≠ 0 have no witness in Lean. Smallest fix: a Lean instance of my polynomial Gaussian metric, or `diag(-1, I + quadratic)` with a tilted perfect fluid at x = 0.
- **N3 (signature).** `hpos` (β spacelike) is assumed rather than derived, because neither GaussianChart nor the pointwise hypotheses require Lorentzian signature. It is discharged only for Minkowski (C4).
- **N4 (frame analogue).** E7 is a chart analogue of the implementation's orthonormal-frame einsum. Its hypothesis (spatial partials of the coordinate components K^p_q are zero) generally fails for non-Bianchi-I homogeneous models in coordinates. So E7 does not validate `homogeneous_codazzi_flux`; the author disclosed this.
- **N5 (units and tools).** "Inverse length" units and κ = 8πG/c⁴ > 0 are not formalized. The card's Wolfram/xAct and Sage tool tasks were not run. My sympy checks partly stand in for the xAct tensor-sign derivation.
- **N6 (citation).** SOURCE_RECOVERY §3 labels `test_relativistic_kinematics.py:81` as a "Bianchi I zero-flux test". It is actually the SU(2) (Bianchi IX) structure constants with K = I giving zero flux. Fix the label.
- **N7 (reproducibility).** The VelocityJetDecomposition and FluxVectorCodazzi oleans are not byte-reproducible across build directories. Both compile with exit 0, so record the source hash, not the olean hash, as identity.
- **N8 (harness).** `run_compile.py` truncates errors to the last 8000 bytes. Print the full error list, or at least every `error:` line, to prevent a repeat of the 07 situation.

### Not proved / not claimed (always)

- Scientific admission: HOLD.
- Publication or manuscript use.
- Covariant (any-chart) Codazzi; existence of Gaussian charts.
- The orthonormal-frame structure-constant identity.
- A Lean non-flat or tilted E6 witness.
- κ > 0 and physical units.
- Multi-fluid converse (refuted by D3).
- w ≤ 0 or imperfect fluids.
- Agreement with Python beyond my numerical spot checks.
- The card's xAct and Sage tasks.
- Requested reviewer gpt-6-astra/ultra: not performed. This review is by Claude Opus 5.5.

### Proposed VALIDATION_MATRIX scientific row (not written)

`P04-A | PORT-CAS-04 flux_vector_codazzi_v1_20261014 | proof: FORMALLY_CHECKED_SCOPED (independent recompile exit 0; 82/82 standard axioms) | science: J=wγ²β, E_N, rank-one S, f(r) inverse PASS vs repo perfect_fluid_normal_projection/flux_to_beta (≤4e-16); Codazzi sign PASS (MTW Ricci; G_0i=-D_jK^j_i+D_iK derived; sympy exact on non-flat Gaussian + general-chart metric); counterflow converse refuted | scope: Gaussian normal chart; flat-only Lean witness; hpos assumed | admission: HOLD | reviewer: claude-opus-5-5`

### Files

Reviewed, in `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-04/flux_vector_codazzi_v1_20261014/`:
- `lean/FluxVectorCodazzi.lean`
- `FROZEN_TARGETS.md`
- `SOURCE_RECOVERY.md`
- `AUTHOR_RETURN.json`
- `raw/compile_0[1-9]_*`
- `raw/AxiomAudit.lean`
- `raw/run_compile.py`

Review evidence, in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p04-a_rerun/`:
- `src/` (copied sources) and `imports/` (rebuilt oleans)
- `exits.txt`
- `audit/ReviewAudit.lean` (sha `05f2d2d8…`) and `audit/out.txt` (sha `c6c4b533…`)
- `num_flux.py`
- `sym_codazzi.py`
- `sym_witness.py`
- `sym_flrw.py`
