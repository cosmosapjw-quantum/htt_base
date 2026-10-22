# G13-D — independent review (verbatim final report of a fresh read-only reviewer)

# G13-D fresh independent review (read-only)

Reviewer model: Claude Opus 5.5 (`claude-opus-5-5`). I did not author this package. I edited no repository file and ran no state-changing git command. All my scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-d_rerun/`.

Task dir T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/g13d_bandpass_cubic_v1_20261014`. It is untracked in git.

## Verdict: PASS_WITH_NOTES (formal status PARTIAL is accurate)

- **What is proved:** the conditional C³ theorem and the admissible-kernel-class verification, connected to each other.
- **What is not done:** the card's "actual calibrated kernel" step. It is honestly recorded as external input EXT-G13D-K.
- **Blocking findings:** none.
- **Scientific admission:** HOLD.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read | PASS | Card member sha256 `301902a3…` and package sha256 `2d0b6da9…` recomputed; both match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 1b | Source citations | PASS (one imprecision) | Recomputed: BRIDGE `f04d96fe…`, SPEC `bc055d39…`, CONTRACT `4e8bdb6c…`, all matching. BRIDGE:164-222 (B1–B4, the non-claims, moment uncertainty, relative bound, sky/beam text), BRIDGE:102 (nonpositive fugacity), SPEC:157-165 (S127 plus the "needs Taylor + support" remark), and CONTRACT:55,70,83-87 plus `additional_analytic_obligations` ("C3 Taylor/integration and kernel domination") all read as quoted. Imprecision: the cited `src/observable/spectral_distortion.rs:30`, `cl.rs:5` and `flrw_cl_pipeline.rs:43` lines are about "spectrum" and do not contain "bandpass". This is harmless (they are labelled "unrelated") but the citation is not reproducible as a search hit. |
| 1c | Frozen-target fidelity: definitions | PASS | Checked by hand. q(1)=c0+c3+c4=v, q'(1)=3c3+4c4=d1, q''(1)=6c3+12c4=d2, q'''=6c3+24c4·y, so h'''=ψ'''−6c3−24c4y as in (B3). Energy-only: q_E(1)=ψ(1), q_E'(1)=ψ'(1), q_E''=3ψ'(1)y² as in (B4). Power case: c0=(p−3)(p−4)/12, c3=p(4−p)/3, c4=p(p−3)/4, i.e. S127. `power_coeffs` is tied to the unchanged PR #501 definitions. |
| 1d | Quantifiers, domains, measures | PASS (adjustments are strengthenings) | Arbitrary probability measure on ℝ with a.e. support in [1−s,1+s]. Moments are true Bochner integrals. The sup in (B3)/(B4) is an arbitrary bound M on the same interval [1−s₀,1+s₀]; `bandpass_M_exists` shows a finite M exists, and the least such M gives (B3) exactly. 0≤s≤s₀ is weaker than the card's 0<s≤s₀<1, and s₀<1 is used only where y>0 is needed (BE corollary, power case). The kernel class needs only `IntegrableOn K [E1,E2]`, which is weaker than the card's "bounded bandpass". |
| 1e | Hypothesis form vs card's "ψ∈C³([1−s₀,1+s₀])" | CONCERN (non-blocking) | `hd` asks for two-sided `HasDerivAt` at the closed endpoints, and T9(a) asks for C³ on an open `Ioo A B ⊃ [1−s₀,1+s₀]`. That is formally stronger than one-sided C³ on the closed interval. T9(a) records this, but the fidelity notes do not list it as a deviation. There is no mathematical loss: C³ on a closed interval extends to an open neighbourhood, and the kernel class is smooth on an open neighbourhood. On the other side, the core theorems need only a bounded third derivative, not continuity, which is weaker than C³. |
| 1f | Fencing route instead of integral Taylor | PASS | `taylor_step_right` uses Mathlib `image_norm_le_of_norm_deriv_right_le_deriv_boundary` with comparison function B(x)=c/(n+1)·(x−1)^{n+1} and B(1)=0=f(1). The left side is handled by reflection t=2−y. It is chained three times with constants M, M/2, M/6. This is a genuine proof of \|h\|≤M\|y−1\|³/6 and is acceptable. |
| 1g | Three derivative–integral interchanges | PASS (genuinely dominated) | `bandIntegral_hasDerivAt` applies `hasDerivAt_integral_of_dominated_loc_of_deriv_le` on `volume.restrict (Icc E1 E2)`. The dominating function is ‖K E‖·M, where M bounds \|∂_yG\| on the compact set [A,B]×[E1,E2] (`exists_bound_of_continuousOn`), and K is integrable. It is applied to G, ∂_yG and ∂²_yG; continuity of the third integral comes from a fourth application, which is why G∈C⁴ is required. The thermal factor E²/(e^{E/(θy)−η0}−ξ) is C⁴ on the open set `regDomain`. `bandResponse_B1_form` proves equality with the (B1) integral over (0,∞) when K vanishes off [E1,E2] with E1>0. `hreg_of_nonpos_fugacity` checks out: e^{x−η0} ≥ 1+x−η0 > 1 ≥ ξ. |
| 1h | Mixture, moment uncertainty, retained span | PASS | Checked by hand: O−Ô(m3,m4) = (O−Ô(true)) + c3Δm3 + c4Δm4. `retained_span` recovers (a0,a3,a4) exactly and gives a zero cubic residual; numerically reproduced (−1.2, 0.7, 0.3). `zero_width_exact` covers MOM-ZEROWIDTH. |
| 1i | Corollaries | PASS | Energy-only (B4) is proved for the same prior and target. `relative_bound` divides by ψ_min>0 only, using integral ≥ ψ_min. `beam_abs` / `beam_uniform` integrate the absolute weight \|b\| and never divide. |
| 1j | Negative controls genuine? | PASS (one minor) | `same_prior_gap`: for ψ=y³ with ½δ_{1−s}+½δ_{1+s}, the cubic estimator is exact and the energy-only error is −(3/2 s²+3/4 s⁴). Verified with sympy. `signed_mode_no_relative`: true signed integral 0, estimate δ≠0, so no constant c gives a relative bound. This is genuine. `radial_data_do_not_fix_dipole`: every functional ∫g d(sky-summed mixture) is unchanged under an N↔S swap while the dipole flips sign whenever ψ(yN)≠ψ(yS). It is genuine but minimal: "radial data" is modelled as all functionals of the angle-summed y-distribution, and the second conjunct follows from the first. The minor point: `radial_witness` (1/2≠3/2 for the identity map) is a separate trivial fact, not an instantiation of the theorem. |
| 1k | Not proved by any theorem: MOM-NOTC3 | NOT_TESTED (no negative control) | Contract invariant "MOM-NOTC3 invalid" has no negative control. The hypotheses are explicit, so nothing is silently assumed. |
| 2 | No hypothesis assumes the conclusion; non-vacuity | PASS | `bandResponse1..3` are definitions (integrals of ∂_y^k G), not hypotheses; derivative status is proved. `bandpass_BE_nonvacuous` (K≡1 on [1,2], θ=1, η0=0, ξ=1, π=δ₁) instantiates the full kernel chain. M≥0 is derived, not assumed. My probe below confirms that the (b)→(a) link `deriv bandResponse = bandResponse1` on Ioo A B holds. |
| 3a | Hash integrity | PASS | All 11 receipts: the stored source, stdout and stderr sha256 equal the recomputed values. The current main source `c7feeff5…` equals compile_10's source and AUTHOR_RETURN. FROZEN `c715f7ca…`, SOURCE_RECOVERY `e837ab0c…`, AxiomAudit `6db88b6b…` and run_compile `5d35fb45…` all match. |
| 3b | Imports unchanged | PASS | G13-A source `a64f6c3c…` equals the HEAD blob and the G13-A RETURN/REVIEW candidate sha. PowerJet `a4334945…` equals `git show 00384ac1:…/PowerJet.lean` (commit "CAS-13-C01: verify power-response jet"). |
| 3c | Exit codes and kept failures | PASS | Failures kept: 03 probe (exit 1, the `ω` auto-bound issue), 04 probe (exit 1), 07 main (exit 1: `simp` no progress; un-beta-reduced norm goal in `beam_abs`). Successes: 01, 02, 05, 06, 08, 09, 10, 11 (exit 0). Diff 07→08 is proof-only (`show` replacing `simp only`; one `show` in `beam_abs`). Diff 08→10 adds only `bandpass_BE_nonvacuous` and `zero_width_exact`, both labelled post-freeze; frozen statements are unchanged. |
| 3d | FROZEN predates first proof compile | PASS (mtime evidence only) | FROZEN mtime is 17:56:46 UTC. The first compile at 17:56:52 is an import build; the first proof compile (probe 03) is at 18:04:11 UTC. The directory is untracked, so this ordering is not tamper-evident. |
| 3e | Forbidden tokens and axioms | PASS | `grep sorry\|admit\|native_decide\|axiom\|set_option\|unsafe\|opaque\|@[…` finds only the prose word "external" on line 23. The audit covers all 45 `theorem`s (names diffed). All 45 show exactly `[propext, Classical.choice, Quot.sound]`, both in compile_11 and in my independent audit. |
| 4 | Independent recompile | PASS | Run from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` with Lean v4.31.0 and mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` (manifest). G13A, PowerJet and main were rebuilt from copied sources into `…/g13-d_rerun/imp`: EXIT_G13A=0, EXIT_PJ=0, EXIT_MAIN=0, no warnings or errors in the main module. The main olean `f4189d70…` and G13A olean `8c53c481…` are bit-identical to the author's. My PowerJet olean is `dbef7bd5…` (built with `-R src`). Rebuilding with the author's exact `-R …/c01_power_jet_v1_20261008/lean` reproduces the author's `f37700e6…`, so the difference is root-path dependence, not a content change. My `ReviewerAudit.lean` (two probes plus `#print axioms` for all 45) exits 0 with 45 standard-axiom lines. |
| 5 | Numerical check on Planck-weighted compact band kernels | PASS | Script `…/g13-d_rerun/num/cubic_check.py`: ψ(y)=∫ν²K(ν)/(e^{hν/(kT* y)}−1)dν with T*=2.72548 K, derivatives taken under the integral. Interchange check: relative finite-difference error is 2e−9 to 4e−9 on ψ' and 1e−5 to 3e−4 on ψ'''. Kernels: 150 GHz 30% top-hat; cos² band at 100 GHz; tabulated CLASS 40 GHz coadd (illustrative only, no calibration convention applied). Over 400 random 1–5-atom mixtures each, at s=s₀ ∈ {0.01, 0.05, 0.2}: zero violations of the cubic or energy-only bounds. Maximum \|err\|/bound is 0.98 (cubic) and 0.99 (energy-only), so the bounds are fairly tight. The cubic bound beats energy-only by about 10–4000× (e.g. CLASS at s=0.05: 1.7e−4 vs 5.6e−3 relative to ψ(1)). |

## Actual kernel (EXT-G13D-K): independent search

- `htt/`: no files match bandpass/band_pass/transmission.
- `src/`: no `bandpass` hits; `tests/`: no hits.
- `git log --all -i --grep=bandpass`: empty.
- `physical_dipole_v2/result.json:85`: "single-frequency examples; actual bandpass and component weights not supplied" (confirmed; produced by `scripts/run_reboot_physical_dipole.py:95`).
- Other docs (V02 METHOD_AND_ACCEPTANCE:96, V02_FINITE_RESPONSE.json:225, `scripts/observed_runs/*`) list the bandpass as absent or HOLD.
- External `workdir/raw`: CLASS `class_dr1_40GHz_bandpass_coadd.csv` (sha `304ba607…`) and QUIJOTE `rimo_quijote_mfi_bandpass_dr1.fits` (sha `09fb68c7…`) match SOURCE_RECOVERY. These are raw transmission tables with no binding to C, T*, η0, ξ or a units/calibration convention.
- No Planck RIMO bandpass is present under `planck_data`, `planck_pr3_component_controls`, `wmap_9yr` or `cosmoglobe_dr1`. The `BP_*` files in `beyondplanck_v2` are BeyondPlanck maps, not bandpasses.

So PARTIAL is confirmed.

**Counting recommendation:**
- Count G13-D as 1 PARTIAL (FORMAL_CLASS_PROVED / EXTERNAL_INPUT_BLOCKED), not CLOSED.
- The conditional theorem and the class-level certificate count as formally compiled.
- The card's actual-kernel item stays open until a repository-owned, hash-bound kernel declaration exists. It must supply K, C, k_BT*, ξ, η0, compact [E1,E2] with E1>0, and the unit convention. Then only `IntegrableOn K (Icc E1 E2)` and `hreg` need discharging; `hreg` is automatic for ξ≤0, or for ξ≤1 with η0≤0.

## Blocking findings

None.

## Non-blocking notes and suggested fixes

1. **Hypothesis form (1e):** add a fidelity line to FROZEN_TARGETS / AUTHOR_RETURN. It should say that `hd` uses two-sided derivatives on the closed interval (and T9(a) an open neighbourhood) instead of one-sided C³([1−s₀,1+s₀]), and why this loses nothing.
2. **Explicit (a)/(b) link:** add a small lemma `deriv (bandResponse …) = bandResponse1 …` (and the iterated versions) on `Ioo A B`. My probe shows it is a one-liner from `bandResponse_C3`. Then `bandpass_cubic_certificate` reads literally as an instance of `cubic_mixture_of_contDiffOn`; today both are routed through `cubic_mixture`.
3. **MOM-NOTC3:** no negative control exists. Optionally add one: a ψ with an unbounded or absent third derivative, e.g. \|y−1\|^{5/2} or \|y−1\|, for which the estimator error is not O(s³).
4. **Beam composition:** `beam_abs` takes an arbitrary raywise ε. No theorem composes it with `cubic_mixture` over a measurable ray family with ε(ω)=s(ω)³M/6. This is acceptable for the card's "separate corollary", but should be stated as not composed.
5. **`bandpass_cubic_BE` existence:** it gives ∃M for the cubic bound but not ∃M2 for the energy-only bound. That is trivial to add via the same continuity argument.
6. **SOURCE_RECOVERY src citations (1b):** these should be corrected or reworded.
7. **Frozen-before-compile evidence:** this rests on mtimes of untracked files. Commit or hash-anchor FROZEN_TARGETS to make it tamper-evident.
8. **CLASS numeric use:** my use of the CLASS table is a numerical illustration only. It is not a verification of EXT-G13D-K.

## Not proved (always)

- Scientific admission: HOLD.
- Verification of the actual calibrated band kernel (EXT-G13D-K absent).
- Tail-domination route for non-compact kernels.
- Sharp minimax optimality for every band kernel, and optimality of the s³/6 constant.
- That radial data determine angular modes. Only the negative is shown.
- Relative bounds for signed modes. Their impossibility is shown.
- Unit conversion or calibration of any instrument bandpass.
- CMB observation relevance, the line-of-sight mixing model, publication or lifecycle acceptance.

## VALIDATION_MATRIX scientific row (proposed text; not written)

`G13-D | scientific | PASS_WITH_NOTES (formal PARTIAL) | B1–B4 Prop B: cubic/energy-only certificates, moment uncertainty, retained span, relative (ψ_min>0), signed-beam absolute weighting, three dominated derivative–integral interchanges for integrable K on compact positive band; independent rebuild Lean 4.31.0/mathlib fabf563a, main olean f4189d70 bit-identical, 45/45 theorems std axioms; numeric Planck-weighted band check 0 violations (max ratio 0.98); actual calibrated kernel EXT-G13D-K absent → HOLD; notes: closed-interval C³ form, explicit (a)/(b) deriv link, MOM-NOTC3 control missing | reviewer claude-opus-5-5 2026-10-23`

## Relevant paths

- Card: `/home/cosmosapjw/Dropbox/bianchi/htt_base/HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (member `HTT_ALL_OBLIGATIONS_20261011/tasks/G13-D.json`)
- Lean source: `…/g13d_bandpass_cubic_v1_20261014/lean/G13DBandpassCubic.lean`
- Planning and return files: `…/FROZEN_TARGETS.md`, `…/SOURCE_RECOVERY.md`, `…/AUTHOR_RETURN.json`
- Receipts: `…/raw/compile_*.json`
- My rebuild log: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-d_rerun/build.log`
- My audit file: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-d_rerun/src/ReviewerAudit.lean`
- My audit output: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-d_rerun/audit.out`
- Rebuilt oleans: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-d_rerun/imp/`
- Numeric script: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g13-d_rerun/num/cubic_check.py`

Here `…` = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13`.
