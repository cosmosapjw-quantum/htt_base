# G08-C — independent review (verbatim final report of a fresh read-only reviewer)

# G08-C fresh independent review: four-way geodesicity decision (CAS-08-C03)

**Verdict: PASS_WITH_NOTES.** I found no blocking findings. I did not edit any repository file or run any state-changing git command. My scratch files are only under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g08-c_rerun/`.

**Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`). This is self-reported, not attested by the runtime. The requested gpt-6-astra/ultra runtime was not used.

**Target:** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-08/g08c_four_way_decision_v1_20261014/` (called T below).

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read first | PASS | I extracted `tasks/G08-C.json` with `unzip -p`. Its sha256 is `88722a69…3843` and the zip's is `2d0b6da9…af6f`, both matching SOURCE_RECOVERY. The pitfalls (no invented names; full-model infeasibility is not rejection of geodesicity) and the acceptance items (empty full model, boundary, feasible non-geodesic and null cases) are all checked below. |
| 1a | Source hashes | PASS | I recomputed: NATIVE_INFERENCE_THEOREMS.md `e2158368…e322`, equal to the contract's research-provenance hash and to `git show 11602167b:` of the same file. `git log -S "computationally unresolved"` on that path returns only `11602167`. CAS-08.json `3a89149e…8d3e`, EXECUTION_CONTRACT `22584699…415a`, c03 blocker RETURN `2bd30c25…3558`, OPTICAL_THEOREMS `5ae2b6a6…8c21`, STATISTICS_INDEPENDENT_DECISION `4b4f7800…a9c7`, STATISTICAL_CLAIMS_NATIVE `286e6996…97d6`. All match what SOURCE_RECOVERY cites. |
| 1b | Citations verbatim | PASS | Checked line by line against `cat -n`: eq. (1) at 11-15, (2) at 21, three constraints at 23, (7) at 79-80 with non-strict `≤`, ν=0 rule at 90, Cα,G at 107, reports 1-4 at 109-112, N2 at 114, proof at 116, certification rules at 120, union rule at 69, general law at 180. OPTICAL (8)-(9) at 77-81 and Bu=0 at 226. Review N2 at 69-71 and STAT-F03 at 212-215. Claims N2 at 56-60. The quoted text matches exactly. |
| 1c | Outcome names and criteria (pitfall) | PASS | Reports 1-3 are exactly the source predicates: "Cα nonempty and Cα,G empty", "Both nonempty", "Cα empty". Report 4 is the certificate state "Feasibility or exclusion not certified". The constructor names abbreviate the source's bold phrases; no criterion is invented. The certificate rules follow line 120 and the review condition "Alternative feasibility and null exclusion certified". |
| 1d | C_α, C_α,G, threshold | PASS | `confSet = {θ ∈ Ω ∧ Q θ ≤ q}` is non-strict, as in eq. (7). `nullConfSet = {θ ∈ confSet ∧ x θ ∈ G}` is line 107. The exclusion certificate `∃ b > q, ∀ θ ∈ Ω∩x⁻¹G, b ≤ Q θ` is equivalent to "inf > q", including +∞ on an empty set. `confSet_rank_zero` matches the ν=0 rule at line 90. |
| 1e | Concrete G (T11) | PASS (note N3) | The transcription S00=h0, S0i=−h1i/2, Sij=h2ij, u=(ζ0,ζ) contravariant, g=diag(−1,1,1,1), B=S+S(u,u)g, (Bu)_a=Σ_b B_ab u^b matches eq. (1) and OPTICAL (8)-(9). I checked it independently in SymPy (`g08-c_rerun/g11_sympy.py`, with h2 symmetric trace-free): u·g·u = −1; B(u,u) = 0 symbolically; at ζ=0, Bu = (0, −h1/2), which agrees with `mem_geodesicNull_of_zeta_zero`; the rank of ∂(Bu)/∂(h0,h1,h2) is 3 at three random rational ζ. This agrees with "three independent constraints" and dim G = 9 at the sample points; it is not a proof. |
| 1f | N2 and STAT-F03 consistency | PASS | "Rejecting … only when total set nonempty and geodesic intersection empty; total-set emptiness separately model incompatibility" is captured by `report_rejected_sound`, `emptyModel_not_rejected` and `emptyModel_report_cases`. "Four-way decision includes empty and unresolved cases" is covered by `report3_witness`, `report4_witness` and `report_unresolved_uncertified`. |
| 1g | Full-model infeasibility is never reported as rejection (pitfall) | PASS | Report 1 requires a `.feasible` certificate for Cα (by the `fourWayReport` pattern match). `emptyModel_not_rejected`: if Cα=∅, no certificate pair yields report 1. `emptyModel_report_cases`: with Cα=∅ only report 3 or 4 is possible. |
| 1h | Required case coverage | PASS | Empty full model: `report3_witness` (Ω=∅). Boundary Q=q: `mem_confSet_of_eq` and `boundary_witness` (Q≡1, q=1 accepted; the strict set is empty). Feasible non-geodesic: `report1_witness` (xDip, h1=e₀). Null: `report2_witness` (x0). Unresolved: `report4_witness`. Both witnesses have h2=0 and ζ=0, so they lie in the physical 12-dimensional slice. |
| 1i | T6 Ici/Ioi negative control | PASS (genuine) | Same Q(θ)=θ, q=0, G=univ, and the same non-strict bound 0 ≤ Q on both domains. On Ici the null set is nonempty; on Ioi it is empty yet no strict b>0 bound exists. My probe adds `sInf (Ici 0) = 0 ∧ sInf (Ioi 0) = 0` (`csInf_Ici`, `csInf_Ioi`), so an infimum equal to q is shown to be inconclusive both ways. This faithfully captures line 120. |
| 1j | T7 drops θ*∈Ω | PASS (pure strengthening) | Only a hypothesis is removed; the conclusion is unchanged. For θs∉Ω the right-hand event is all y, so it holds trivially. The `xmap θs ∈ G` hypothesis is not vacuous: my probe `nonnull_counterexample` shows that without it, the report-1 event is not contained in noncoverage (θs=xDip, Ω={xDip}). |
| 1k | T8 conditional on hcov | PASS | Named `*_of_coverage`, documented "CONDITIONAL" in the Lean docstring, FROZEN_TARGETS and AUTHOR_RETURN, and listed in not_claimed as "unconditional N2 size control". μ is an arbitrary measure; `measure_mono` needs no measurability. Non-vacuity: my `t8_instance` instantiates it on FirstJet with a Dirac law. I also derived a semantic (uncertified) variant, `semantic_size`, from T7. |
| 1l | G08-B discharges hcov (not required) | Shown in the known-C case | My probe `g08-c_rerun/bridge/BridgeProbe.lean` imports `G08CFourWay` with the reviewed G08-B oleans (G08-B RETURN status FORMALLY_CHECKED_SCOPED; source hash `472178ed…c122` matches). It proves `multivariateGaussian(m θs+Fβ, C){y | θs ∉ G08C.confSet Ωd (fun θ => Qstat W F X (m θ) y) (threshold (n−rank F) α)} = ofReal α`, assuming θs∈Ωd, C PosDef, W whitening, Moore-Penrose X, 0<α<1 and ν>0. Exit 0; axioms `[propext, Classical.choice, Quot.sound]`. So hcov is discharged with equality in that case. I used the prebuilt G08-B oleans and did not rebuild them from source. |
| 1m | T9/T10 projection, union, α+δ | PASS | `interval_event_subset` uses EReal, matching "including infinite endpoints" at line 101. `union_noncoverage_le` matches the union rule at line 69. `alpha_delta_bound` models line 69's union bound "1−α−δ" by treating the separate bound procedure as a data-dependent domain Ωy; this is an interpretation (note N4). |
| 2 | No assumed conclusion, no vacuity | PASS | No hypothesis restates a conclusion. hcov is the N1 coverage premise, not N2. hsub is supplied by `nullConfSet_subset`. All four reports have concrete witnesses on the concrete G. I checked the full 9-entry `fourWayReport` table by `rfl`/`cases` in my probe; it is consistent with SOURCE_RECOVERY item 3. The only "inconsistent" pair (excluded C, feasible CG) cannot occur when CG ⊆ C. |
| 3a | Integrity | PASS | The lean file `17a8411e…8225` equals the compile_02 source. compile_01 used a different source (`c1b442fe…`), differing only in the proof term `Set.left_mem_Ici` → `Set.self_mem_Ici` (deprecation warning); it is kept in raw/. AxiomAudit `e6186b2a…ab2b` equals the compile_03 source. Recomputed stdout/stderr hashes match the receipts; exit codes are 0/0/0. run_compile.py `c6a6426e…`, olean `349616c9…`, FROZEN `60d1e6c2…` and SOURCE_RECOVERY `60e5989d…` all match AUTHOR_RETURN. |
| 3b | Frozen before compile; signatures unchanged | PASS | FROZEN written at 2026-10-13T21:11:14Z; the snapshot is byte-identical; the first compile started at 21:14:24Z. A mechanical comparison of all 40 frozen theorem statements against the compiled ones (whitespace-normalized, `MeasureTheory.Measure` treated as `Measure`) shows 40/40 identical. The definitions also match on read-through. |
| 3c | Forbidden tokens and axioms | PASS | `grep sorry\|admit\|native_decide\|axiom \|set_option` finds nothing in T/lean or T/raw/AxiomAudit.lean; the module imports only Mathlib. Axioms: 30 theorems use {propext, Classical.choice, Quot.sound}, 9 use {propext}, 1 uses {propext, Quot.sound}, and 3 use none. |
| 4 | Independent recompile | PASS | I copied the source to `g08-c_rerun/src/`. From `/home/cosmosapjw/lean_oracles/viii_oracle` I ran `lake env bash -c "LEAN_PATH=$S:$LEAN_PATH lean -R $S/src -o $S/G08CFourWay.olean $S/src/G08CFourWay.lean"`: exit 0, empty stdout/stderr, about 8 s. The toolchain is `leanprover/lean4:v4.31.0` and the manifest mathlib rev is `fabf563a…911f`. The olean sha256 `349616c9…8d7b6` is bit-identical to the author's. My own audit `g08-c_rerun/audit/RevAudit.lean` has `#print axioms` for all 40 public theorems plus probes: exit 0, no sorryAx, and the 40 axiom lines are identical to the author's `compile_03_audit.stdout`. |

## Blocking findings
None.

## Non-blocking notes
- **N1 – stale statement about G08-B.** SOURCE_RECOVERY and AUTHOR_RETURN `imports.note` say G08-B has no reviewed RETURN.json. G08-B RETURN.json and REVIEW.md (PASS_WITH_NOTES) are dated 06:09:45 KST, 39 seconds after SOURCE_RECOVERY was written (06:09:06). The statement was true when written but is now stale.
  - Minimal fix: add a dated addendum saying G08-B is now FORMALLY_CHECKED_SCOPED.
  - Optionally record the bridge in 1l as the known-C discharge of hcov.
  - Keep T8 labelled conditional regardless.
- **N2 – scope.** The contract text for C03 places "measurable projection/union theorems" outside this component. T8, `union_noncoverage_le` and `alpha_delta_bound` are trivial measure-monotonicity corollaries with no measurability claims. They are not overclaims, but they should not be counted toward C03 or toward unconditional N1/N2.
- **N3 – T11 domain and coverage of G.** `FirstJet.h2` is a general 3×3 matrix, so the type has 16 reals; the symmetric trace-free restriction is deferred to Ω, as documented. G is characterized only on the ζ=0 slice. The rank-3 constraint and dim G = 9 claims at line 23 are not formalized; my SymPy rank check is only numerical support at sample points. The line-120 sentence "strictly positive lower bound on Iα is sufficient for exclusion" is not formalized either.
- **N4 – α+δ interpretation.** `alpha_delta_bound` represents line 69's "separate confidence procedure with failure probability δ" as a data-dependent domain Ωy with μ{θs∉Ωy} ≤ δ. This is a reasonable reading but it should be labelled an interpretation.
- **N5 – weak negative control.** `intersection_negative_control` is genuine but minimal: it shows set membership fails for the intersection, not a loss of coverage probability.
- **N6 – other CAS axes.** The card's Wolfram/xAct, SymPy and Sage/Singular tasks are not done in this unit. AUTHOR_RETURN correctly lists them as not claimed.

## Not proved / not claimed
- Scientific admission: **HOLD**.
- Unconditional N2 size control: proved only conditional on hcov. It is discharged by G08-B in the known-C Gaussian case with ν>0 and θ*∈Ω, which this review demonstrated but the authors did not claim.
- N1 Gaussian law, χ² quantile and coverage (8) in this unit, and the measurability of any event.
- Optimizer or numerical exclusion certificates for any real catalogue; any real-data fit.
- A general characterization of G beyond ζ=0, the rank-3 / dim-9 claim, the physical interpretation of G, and the Iα-based exclusion criterion.
- The Wolfram/xAct, SymPy and Sage axes, CAS_4AXIS_PASS for CAS-08, and publication state.

## Suggested VALIDATION_MATRIX scientific-row update (not applied)
`G08-C | CAS-08-C03 four-way decision | proof: FORMALLY_CHECKED_SCOPED (Lean 4.31.0/mathlib fabf563a; 40/40 theorems; axioms ⊆ {propext, Classical.choice, Quot.sound}; independent recompile olean bit-identical 349616c9…) | review: fresh independent PASS_WITH_NOTES (claude-opus-5-5, self-reported) | source: NATIVE_INFERENCE_THEOREMS.md e2158368… §5 l.105-120 verbatim | conditional: T8 size control needs hcov (discharged by G08-B coverage, known-C ν>0 θ*∈Ω, reviewer probe) | not done: Wolfram/SymPy/Sage axes, general G rank-3 | scientific admission: HOLD`

## Reviewer scratch files
All under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g08-c_rerun/`:
- `G08CFourWay.olean`, `rerun_module.stdout`, `rerun_module.stderr` — independent recompile output
- `audit/RevAudit.lean`, `rev_audit.stdout` — my axiom audit and probes
- `bridge/BridgeProbe.lean`, `bridge.stdout` — the G08-B hcov bridge probe
- `g11_sympy.py` — the SymPy kinematics check

