# G13-D source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member
`HTT_ALL_OBLIGATIONS_20261011/tasks/G13-D.json` (package sha256
`2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`, member sha256
`301902a3b3d120f304c73f95ac5632257bdcd898f6796960c41e666a64ede074`). Card status on read:
`PLANNED_NOT_EXECUTED`, `statement_kind = PROPOSED_LEMMA_DAG_NOT_COMPILED`,
`scope_original = "TEFF Proposition B의 B1–B4"`.

All paths below are relative to the repository root
`/home/cosmosapjw/Dropbox/bianchi/htt_base`. Abbreviations:
`BRIDGE = docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_POSITIVE_BRIDGE.md`
(sha256 `f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b`, identical to the
hash recorded in the CAS-13 contract), `SPEC = docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md`
(sha256 `bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe`, identical to the
contract hash), `CONTRACT = docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-13.json`
(sha256 `4e8bdb6c3d0c789e8dc7fbb647a982849ac13653bcabe41820c41be0c360b89b`).

## 1. Recovered definitions (Proposition B, B1-B4)

| Item | Source | Recovered content |
|---|---|---|
| Prior class | BRIDGE:164 | fixed statistics, one common admissible log-fugacity, fixed normalization, probability measure `π` of temperature ratios `y ∈ [1−s,1+s]`, `0<s≤s₀<1` |
| Retained moments | BRIDGE:166 | `m₃=∫y³dπ`, `m₄=∫y⁴dπ` |
| Band kernel (B1) | BRIDGE:168-173 | `ψ(y)=C∫₀^∞ E²K(E)dE/(exp[E/(k_B T_* y)−η₀]−1)` (BE photon example) |
| Regularity / support | BRIDGE:176 | "Require ψ∈C³([1−s₀,1+s₀]). A bounded bandpass supported on a compact positive-energy interval suffices; wider kernels require a separate endpoint/tail domination check." `O=∫ψ dπ` |
| Coefficients | BRIDGE:178-185 | `c₃=ψ'(1)−ψ''(1)/3`, `c₄=ψ''(1)/4−ψ'(1)/2`, `c₀=ψ(1)−ψ'(1)/2+ψ''(1)/12`, `q=c₀+c₃y³+c₄y⁴` |
| Estimator (B2) | BRIDGE:188 | `Ô=c₀+c₃m₃+c₄m₄` |
| Cubic bound (B3) | BRIDGE:190-196 | `|O−Ô| ≤ (s³/6) sup_{[1−s₀,1+s₀]} |ψ'''(y)−6c₃−24c₄y|` |
| Proof sketch | BRIDGE:199 | jets match at 1; Taylor remainder; integrate against probability measure |
| Power reduction | BRIDGE:201-206 | `ψ=y^p` gives II (127) = SPEC (S127), SPEC:157-165 |
| Non-claim | BRIDGE:208 | sharp minimax optimality for every band kernel is not claimed |
| Energy-only (B4) | BRIDGE:210-215 | `q_E=ψ(1)−ψ'(1)/4+[ψ'(1)/4]y⁴`; `|O−Ô_E| ≤ (s²/2) sup|ψ''(y)−3ψ'(1)y²|` |
| Same-prior comparison | BRIDGE:218 | generally quadratic-to-cubic gain under same prior and target; retained-span kernels exact |
| Moment uncertainty, relative, signed | BRIDGE:220 | add `|c₃|d₃+|c₄|d₄`; division by `ψ_min>0` valid; signed angular multipoles need absolute errors |
| Sky / beam | BRIDGE:222 | raywise estimator, integrate absolute error against absolute beam/angular weight; extra radial data do not identify an unmeasured angular mode |
| Fugacity sign used for BE envelope | BRIDGE:102 | "nonpositive common log-fugacity" |
| Contract obligations | CONTRACT:55,70,83-87 | `psiC3 for bandpass`; invariants MOM-RETAINED exactspan, MOM-ZEROWIDTH collapse, MOM-NOTC3 invalid, MOM-PRIOR samecomparisonprior, MOM-BOUNDARY |
| Remaining analytic obligation | CONTRACT `full_theorem_boundary.additional_analytic_obligations` | "C3 Taylor/integration and kernel domination" |
| Interval spec remark | SPEC:165 | the integrated cubic remainder needs a Taylor theorem and support assumptions |
| Review disposition (context only) | `docs/research_program/gr_statistics_loops_20260930/reviews/POSITIVE_EXTENSION_DECISION.md`:39,56-58 | TEFF-B1 `PROMOTE_ANALYTIC_CONDITIONAL` under "calibrated C³ response"; not used as proof evidence |

## 2. Reused, previously reviewed Lean (imported unchanged)

| Reuse | Path | Role |
|---|---|---|
| G13-A | `.../CAS-13/g13a_measure_extremizer_bridge_v1_20261011/MeasureExtremizerBridge.lean` | `CAS13MeasureComposition.hermite`, `moment`, `integral_hermite`, `twoDirac`, `integral_twoDirac`, `moment_twoDirac`, `twoDirac_supported` |
| PR #501 | `.../CAS-13/c01_power_jet_v1_20261008/lean/PowerJet.lean` (added by commit `00384ac123fb52e2093a4937235f63fd4f19fa99`, "CAS-13-C01: verify power-response jet"; PR number from `.../ALL_OBLIGATIONS_20261011_SOURCE_RECONCILIATION/RETURN.md`:53) | value/first/second matching and third-derivative finite algebra for `ψ=y^p`: `Cas13C01.psi/dpsi1/dpsi2/dpsi3/c0/c3/c4/dq3` |

G13-B (`g13b_boundary_minimax_v1_20261013`) and G13-C (`g13c_general_p_extremizer_v1_20261014`)
are about sharp interval/minimax and general-p extremizers; none of their theorems is needed
for Proposition B, so they are not imported (no dependency is claimed on them).
Import source and olean hashes are recorded in `AUTHOR_RETURN.json`.

## 3. Actual calibrated band kernel: NOT FOUND in the repository (named external input)

Searched:

* `htt/` (Python implementation): `grep -rli bandpass --include=*.py htt` returned nothing.
* `src/` (Rust): only unrelated word matches (`src/observable/spectral_distortion.rs:30`, `src/observable/cl.rs:5`, `src/solver/flrw_cl_pipeline.rs:43`); no frequency transmission kernel.
* Research docs: `docs/observational_reboot_20261014/results/physical_dipole_v2/result.json`:85 records
  `"frequency_scope": "single-frequency examples; actual bandpass and component weights not supplied"`.
* GR-statistics loop docs (BRIDGE, SPEC, CONTRACT, CAS_TASKS.json, PROOF_DAG.json, reviews): kernel only as the symbolic (B1).
* `git log` / PR history: PR #501 (commit `00384ac1`) is the power-response `y^p` jet only.
* Filesystem: `workdir/raw` is a symlink to external storage (not tracked by git;
  `git ls-files` reports the path is beyond a symbolic link). It contains instrument
  bandpass tabulations `workdir/raw/class_dr1/class_dr1_40GHz_bandpass_coadd.csv`
  (sha256 `304ba60776d7f18c66c6dd66cdb045ac6f3666a1b28912c883e740e9a6b89a97`) and
  `workdir/raw/quijote_mfi_dr1/rimo_quijote_mfi_bandpass_dr1.fits`
  (sha256 `09fb68c7b0775d5c7b99e489da235fccf03d8d141af73bced09487fb79200f5a`).
  These are raw instrument transmission curves, not a calibrated TEFF band kernel: no binding
  to `C`, `k_B T_*`, `η₀`, statistics, unit convention (frequency vs energy, `E²` measure,
  RJ/CMB/flux calibration) or to a declared observable exists anywhere in the repository.
  They were not used, interpolated or fitted.

Disposition (per card pitfall and caller instruction): the actual calibrated kernel is recorded as
the named external input `EXT-G13D-K` = "calibrated band kernel `K` with its
calibration constant `C`, reference temperature `k_B T_*`, statistics `ξ`, log-fugacity `η₀`,
compact positive support `[E₁,E₂]`, and integrability on that support". No kernel is invented.
Unlock condition: a repository-owned, hash-bound kernel declaration supplying those items;
then `G13D.bandpass_cubic_certificate` (or `G13D.bandpass_cubic_BE` for BE photons with `η₀≤0`)
applies verbatim once `IntegrableOn K (Icc E₁ E₂)` and the support/regularity hypotheses are
discharged for that concrete kernel. A tabulated bandpass with bounded values on a compact
positive frequency interval (as the files above appear to be) would fall in the proved
admissible class after unit conversion and calibration; that conversion is not performed here.

## 4. Statistics convention

The occupation in SPEC §1 is `1/(exp[E/(k_B T_* y)−η₀]−ξ)`. The kernel theorem is proved for
general real `ξ` with the explicit occupation-regularity condition
`ξ < exp(E/(θy)−η₀)` on the compact domain (`θ = k_B T_* > 0`). BE photons (B1) are `ξ=1`;
the corollaries discharge regularity for `ξ≤0` (MB/FD) always and for `ξ≤1, η₀≤0` (BRIDGE:102).
