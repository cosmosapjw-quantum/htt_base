# G12-D — independent review (verbatim final report of a fresh read-only reviewer)

# G12-D re-execution closeout: independent read-only review

**Reviewer model:** claude-opus-5-5 (Opus 5.5), running as a fresh reviewer. I did not author this unit. I edited no repository files and ran no state-changing git commands. All scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-d_rerun/`.

**Unit reviewed:** `T=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/g12d_reexecution_closeout_v1_20261014` (untracked in git).

## Verdict: PASS_WITH_NOTES

I found no blocking findings. All card items L1–L5 and X1–X3 have faithful, kernel-checked typed statements. X4 is satisfied by this review together with the build and axiom evidence. **Scientific admission: HOLD.**

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card identity | PASS | `unzip -p …zip …/tasks/G12-D.json \| sha256sum` gives `de5f8501…dda1`, matching SOURCE_RECOVERY. The zip sha256 is `2d0b6da9…c4af6f`, which also matches. |
| 1a | SOURCE_RECOVERY citations | PASS | I read every cited line. CAS-12.json:40/108 is the formal expansion with the analytic limit kept separate. :47/62/82 is "Both f,g<=F_b…, no condensate; measure CE^2dEdOmega". :75/95/113 is "BE-REF bothstates required". :89 is "One-sided IR and UV convergence". TEFF_POSITIVE_BRIDGE.md:39 is dν=CE²dEdΩ. :48-50 is (A2) with z(1+ξz). :95-98 is (A5). :100 is IR O(E⁻²), exponential UV, "bounded angular kernels times nonnegative powers". :102 is T≤Tmax, common nonpositive log-fugacity, b=1/(k_B Tmax), reference β≥b, η≤0, and Tmax not inferred from bolometric energy. TEFF_CLAIMS.json:84-92 is TEFF-A4 with the "no singular condensate" assumption. Recomputed hashes: CAS-12.json `5a682716…a6fae` and BRIDGE `f04d96fe…3ff21b` both match. Commits 20a15b77 (Planck-weight expansion), 0a20701d (PlanckIR) and 947aa837 (prior G12-D) all exist with the stated subjects. |
| 1b | Frozen targets predate the first compile | PASS (mtime evidence only) | FROZEN_TARGETS.md mtime is 21:23:31Z and compile_01 started at 21:23:36Z. A Python block comparison shows the frozen ```lean``` block is byte-identical to the type section of compile_04 (the at-freeze source `08aea666…`) and of the final source `85426b04…`. `diff compile_04 compile_05` changes only lines 179–183, which are the proof body of `uv_dominating_integrable`. |
| 1c | Faithfulness to card L1–L5 | PASS | **L1:** `CAS12PlanckIR.weight b E = exp(bE)/(exp(bE)−1)²`, a real function; the b>0, E>0 domain is carried by hypotheses. **L2:** C1 is `Tendsto (E²·W) (𝓝[>]0) (𝓝 (1/b^2))`, a one-sided literal 1/b². It is derived from the reviewed `b^(-2:ℤ)` result via `zpow_neg, zpow_ofNat`. **L3:** C2 gives `E^m W ≤ (1−e^{−ba})⁻² E^m e^{−bE}` on [a,∞), and C3 proves the dominating function integrable on `Ici a`. **L4:** density `kernelDensity = C E² W` on `(vol\|Ioi 0) ⊗ μ`, with μ finite. C4 covers `\|K\|≤M(1+E^N)`, C5 polynomial sums with c_k≥0, C6 a.e. `\|K\|≤M E^p` with real p≥0, and C7 a bounded-angular A(ω)·E^p. Each is proved in both the density form and the `withDensity` form. **L5:** C8 handles both states as independent mixtures. C10 uses T∈(0,Tmax] a.e., a constant (common) η₀≤0, and a reference with `inverseTemperature kB Tmax ≤ betaRef`, `etaRef ≤ 0`. Its conclusion is the (A2) bound for every z between the mixture and the reference. |
| 1d | Acceptance X1–X3 | PASS | **X1:** the limit is an actual `Tendsto` and integrability is stated with actual measures. The formal series (PR #499 reuse) is provenance only and is not used as a proof. **X2:** the envelope is proved for both f and g (C8, C10, and reviewed A11/A13). Condensate exclusion is kept as the regular branch: C11 shows a positive denominator for η≤0 and E>0, C12 shows {E≤0} is null in both measures (no atom at E=0), and C13 is the η>0 control. **X3:** quantifiers, measure, density, one-sided filter and boundary branches match the reviewed interface. Hypotheses are only weakened, never strengthened (real p≥0 includes ℕ; the polynomial envelope includes the monomial). |
| 1e | Card pitfall (bolometric energy) | PASS | Tmax, kB and b enter only as hypotheses in C10, C8 and A13. No theorem derives Tmax or b from any energy integral. "bolometric" appears only in comments. |
| 1f | (A2) step is the right one | PASS | BRIDGE:48-50 requires sup over z between f and g of z(1+ξz) ≤ W. Under (A5), W=F_b(1+F_b) (reviewed A1, `weight_eq_occupation`). C9 proves z(1+z) ≤ W for z∈[min f g, max f g] with 0≤f,g≤F_b, using monotonicity of z↦z(1+z) on z≥0. ξ is fixed at +1 (BE), which matches the (A5) BE envelope; for ξ≤1 and z≥0 it also dominates z(1+ξz). |
| 1g | C13 negative control is genuine | PASS | For β>0 and η>0: E=η/β gives a zero denominator (a pole; Lean's junk `0⁻¹=0` is avoided by stating the denominator rather than the occupation), and E=η/(2β) gives occupation <0. mpmath (β=1.7, η=0.4) gives denominator 0.0 and occupation −5.5167. |
| 2 | No assumed conclusions, no vacuity | PASS | Every C-target's hypotheses are strictly weaker than its conclusion; none restates the result. My `ReviewerAudit.lean` (exit 0) adds four checks. (i) `weightedKernelMeasure 1 1 (dirac ()) univ ≠ 0`, so the integrability conclusions are not trivial on a zero measure. (ii) A negative control for C9: dropping the envelope hypothesis makes `∀ … z(1+z) ≤ W` false (witness f = F_1(1)+1). (iii) C7 instantiated with `cos 1 · E^{3/2}`. (iv) C5 instantiated with the signed kernel `E^5 − 2E` via the envelope 2E+E^5. The author's own witnesses `nonvacuity_constant_kernel` and `nonvacuity_temperature_instance` also compile. |
| 3a | Hash integrity | PASS | `sha256sum` recomputed for all 4 sources, AxiomAudit.lean, the 6 compile JSONs, source snapshots, stdout/stderr, 4 oleans, the harness (`a8697d02…`), FROZEN_TARGETS (`09b54830…`) and SOURCE_RECOVERY (`40fa09b9…`). All equal the AUTHOR_RETURN values. |
| 3b | Reused sources byte-identical to reviewed ones | PASS | PlanckIR `5ae963f5…` equals `c03_planck_ir_limit_v1_20261011/PlanckIR.lean`. G12DInterface `340d348e…` and G12DUVIntegrabilityEnvelope `77fed344…` equal the files in `g12d_uv_integrability_envelope_v1_20261011/lean/`. The unit's oleans (`5e703d93…`, `94a0b293…`, `a51d8a46…`) are byte-identical to the prior unit's `lean/raw/parent_sourcebound` and `lean/raw/imports` oleans. |
| 3c | Every attempt retained | PASS | Attempts 01–06 are contiguous, each with argv, cwd, UTC start/finish, exit code, a source snapshot and stdout/stderr. Failed attempt 04 (exit 1) is kept; its stdout holds the `Invalid field mono_set … And.mono_set` error at 180:11, which matches the `first_failure` record. Exit codes: 0,0,0,1,0,0. |
| 3d | Historical logs honestly UNAVAILABLE | PASS | The prior `lean/raw/FAILURE_INDEX.json` lists 9 failures, all with stdout and stderr marked "UNAVAILABLE". AUTHOR_RETURN `historical_failure_logs.status = "UNAVAILABLE"` states they are not recovered, reconstructed or substituted, and `not_claimed` includes "recovery of historical interim failure logs". |
| 3e | Axioms and forbidden tokens | PASS | `grep -nE "sorry\|admit\|native_decide\|axiom\|set_option\|maxHeartbeats\|implemented_by\|extern\|unsafe\|opaque"` over `T/lean/*.lean` and `T/raw/AxiomAudit.lean` returns no hits. My `run_cmd` enumeration with `collectAxioms` covers every non-internal theorem in `CAS12PlanckIR`, `G12D` and `G12DClosure`: 30 public theorems plus 3 auto `eq_1` lemmas. Every one reports exactly `[propext, Classical.choice, Quot.sound]`. Private helpers are covered transitively. |
| 4 | Independent recompile | PASS | Command, from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain `leanprover/lean4:v4.31.0`; mathlib manifest and checkout both at `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`): `lake env bash -c "LEAN_PATH=$S/imp:$LEAN_PATH lean -R $S/src -o $S/imp/<M>.olean $S/src/<M>.lean"`, run in order PlanckIR → G12DInterface → G12DUVIntegrabilityEnvelope → G12DCardClosure. I rebuilt all imports from source in scratch rather than reusing the unit's oleans. All four exited 0 with empty stderr. My four oleans are byte-identical to the unit's (`5e703d93…`, `94a0b293…`, `a51d8a46…`, `0ad9c05e…`). |
| 5 | Numeric spot checks (mpmath, 50 digits) | PASS | **IR:** E²W − 1/b² at b∈{0.3, 1, 7.5} and E=1e-3, 1e-6, 1e-12 has relative error ∝E² (e.g. 8.3e-26 at E=1e-12, b=1). The next coefficient is −1/12, matching the formal series, which is not used as proof. **UV:** 20,000 random (b, a, E≥a, m≤8) give max lhs/rhs = 1.0, with equality exactly at E=a (the bound is sharp). The dominating-function integral by quadrature equals the closed form (1−e^{−ba})⁻² Γ(m+1,ba)/b^{m+1}. **Weighted norm:** ∫E²W E^{2p}dE = Γ(2p+3)ζ(2p+2)/b^{2p+3} for p∈{0, 0.5, 1.5, 3}, matching to 15 digits. **(A2):** max z(1+z)/W = 0.99494 over 20,000 samples. **Mixture with T≤Tmax and common η≤0:** max occ/F_b = 0.697. |

## Blocking findings

None.

## Non-blocking notes

1. **Freeze evidence is mtime only.** The unit is untracked in git, so "frozen before compile" rests on filesystem mtimes (21:23:31Z vs 21:23:36Z) plus my byte-identity check against the compile_04 snapshot. A commit of FROZEN_TARGETS before compiling would make this tamper-evident.
2. **One raw file is not mentioned in AUTHOR_RETURN.** `raw/probes/closure_types_excerpt.txt` (mtime 21:22:57Z, before the freeze) is a plain-text excerpt of the type block and was never compiled; no `compile_*probe*` receipt exists. Retention is not violated, but AUTHOR_RETURN should list the file.
3. **The status label "ALL" in AUTHOR_RETURN could be misread as card closure.** `status_scope` qualifies it correctly; parent adjudication remains separate.
4. **(A2) is stated pointwise, not as an a.e. statement on ν.** C9 and C10 hold for each E>0, which is stronger. Lifting to a.e. on the product measure is immediate (C12 makes {E≤0} null) but is not stated as a separate theorem.
5. **Coverage gaps that follow directly but are not stated:**
   - Signed polynomial kernels are covered only through the envelope |K| ≤ Σ|c_k|E^k. My audit instantiated this for E^5 − 2E.
   - Mixed sums of real powers are covered via C4 with N = ⌈max p⌉, but there is no theorem for them.
   - These are disclosed in `not_claimed`.
6. **C11 restates the reviewed private lemma `positive_occupation_denom` as a public theorem.** This is harmless.
7. **Minor provenance gaps:**
   - TEFF_CLAIMS.json (`9654e73e…f541` now) is cited without a recorded hash.
   - The PR #499 ↔ commit 20a15b77 mapping is asserted but not verifiable offline.
   - SOURCE_RECOVERY records HEAD `c5a683eb`; HEAD has since moved to `4571756a`. This is fine for an untracked unit.

## Not proved / out of scope

- **Scientific admission: HOLD.**
- A physical condensate-exclusion theorem. Only the regular branch is formalized: η≤0 positivity, a null {E≤0}, and the η>0 control.
- Certification of b or Tmax. These are hypotheses only; nothing is inferred from bolometric energy.
- Actual channel kernels, sphere/Funk–Hecke transport, and continuum collision-adjoint closure.
- The certified ε and entropy budget, and the downstream TEFF Propositions A and B.
- Recovery of the nine historical interim failure logs from the prior unit (they remain UNAVAILABLE).
- Historical four-axis promotion and the parent card-closure decision, which belong to the adjudicator lane.

## Reviewer artifacts (scratch, not in the repo)

- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-d_rerun/src/` (copied sources, sha-verified)
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-d_rerun/imp/*.olean` (independent rebuild, byte-identical)
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-d_rerun/audit/ReviewerAudit.lean` and `audit/out.txt` (axiom enumeration, non-vacuity, C9 negative control, C5/C7/C13 instances; exit 0)

