# G10-B source recovery

Package card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip :: HTT_ALL_OBLIGATIONS_20261011/tasks/G10-B.json`
(read with `unzip -p`; `source_snapshot` a30d84c7918b54238a48fa62e2ef482f7e6d36fa).
All paths below are relative to the repository root unless absolute.

## Resume / origin record

This run is a resumption. Previous attempts of the same single-author G10-B task were cut off by
credit/rate limits. At resume time, T already contained:

* `FROZEN_TARGETS.md` (sha256 `87b73fe3d852a53ff6993a98e5a4f25355b395a36ed3db494f763cbc8f9ab4bf`,
  mtime 2026-10-13 20:56 KST = 11:56 UTC), authored by the earlier attempt of this task. Its
  own "Origin" paragraph describes that earlier attempt (it says "authored fresh in this run";
  "this run" there means the earlier, interrupted attempt). It was written after only the three
  unchanged reused modules had been compiled (receipts 01-03, 11:54-11:55 UTC) and before any
  compile of `lean/G10BGaussianKL.lean` (first main compile: receipt 10, 21:00 UTC).
* `lean/reused/*.lean`, `raw/run_compile.py`, `raw/imports/{CAS10C01,CAS10C03,P12GaussianLaw}.olean`,
  `raw/probes/P1.lean` and four receipts `raw/compile_01..04` (last exit 0).

Resume decision: all four receipts are kept unmodified. `FROZEN_TARGETS.md` was re-checked against
the card, contract and theory text below and found faithful (no strengthened assumptions; T1/B2
are stated for arbitrary `σ`, i.e. they *weaken* the theory's `σ_j > 0`; KL targets keep
`σ_j > 0`; the singular branch is a separate target A8). It was therefore kept byte-identical and
not re-frozen. Receipts 05-13 were produced in this resumed run.

## Original statement sources

| item | source (file:line) | sha256 |
|---|---|---|
| card scope / lean_steps / pitfalls | `tasks/G10-B.json` (package zip) | — |
| CAS-10 contract, C03 component and assumptions ("Independent isotropic Gaussian blocks for equal-law benchmark"; "INFO-ANISOTROPIC noise invalidates equal-law proof") | `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-10.json:39-49,79,112` | `03dd5c3c8e3d8c30cf75058b48138a5208ac5f664a51533fb5d945ffee06f43f` |
| common spec | `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` (matches contract `source_input_hashes`) |
| Theorem I tuples (p → p' = (0,15H/8,0)), powers (I6) | `docs/research_program/gr_statistics_loops_20260930/statistics/INFORMATION_LIMIT_THEOREMS.md:42,74` | `775b7d151d894dc33e3896e9e00674a8de6e2432c7bf96ad5ee70d64f2b63b1a` (matches contract `research_provenance_hashes`) |
| observation law (I9): `X_j ~ N(μ_j, σ_j² I_{d_j})`, independent, `d=(1,3,1,3,5)`, orthonormal sector coordinates, `P_j=|X_j|²` | same file `:109-117` | same |
| Theorem II, (I10) `D_KL = ½ Σ_j |μ_j-μ'_j|²/σ_j² = 225H²/(64σ_p²)` | same file `:119-124` | same |
| proof sketch (blockwise orthogonal R_j, isotropy, independence) | same file `:127` | same |
| scope limits (anisotropic covariance, masks, cross-block errors invalidate) | same file `:131` | same |

## Reused, accepted Lean sources (imported unchanged)

| module | original path | sha256 (source) | olean sha256 (compiled here) | receipt |
|---|---|---|---|---|
| CAS10C01 | `.../CAS-10/c01_tuple_separation_v2_20261008/lean/CAS10C01.lean` (RETURN aggregate CAS_4AXIS_PASS, review PASS_FINITE_COMPONENT_REVIEW) | `3cf35a9ad4c2d1fbea430de200ef783b3f8655298392591419e6692c95985f0a` | `607e6d55d623055680bade21cca38df746d0fa92f01105af95b8bbc31c9b9a2a` | compile_01 (exit 0) |
| CAS10C03 | `.../CAS-10/c03_block_rotation_kl_v2_20261008/lean/CAS10C03.lean` (RETURN aggregate CAS_4AXIS_PASS, review PASS_FINITE_COMPONENT_REVIEW) | `2ab3b8b9d86ffbb3a994d74b24fd124d98fa55a58a7283dbbe2089fab8b7fab6` | `2e816f602117bc5df3389096efee3912a5fc3a1cb3fe051c2d5ebc727185c54e` | compile_02 (exit 0) |
| P12GaussianLaw | `docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-12/gaussian_law_equality_v1_20261013/lean/P12GaussianLaw.lean` | `5a6ce15dea4ef78c987a73bdc15af796a7a9c9fc214045501a24c5e5ba08ca0c` | `89829b57c81b6923a8a9d0f541306c3e594d56c08934749869133d4fd0177b6d` | compile_03 (exit 0) |

Copies in `lean/reused/` are byte-identical to the originals (sha256 verified in this run).

Definitions taken from the reused modules (no re-definition): `CAS10C03.R`, `R_orthogonal`,
`p`, `pPrime`, `R_maps_p`, `Mean`, `first`, `second`, `KLQuadratic`, `weightedQuadratic`,
`sqNorm`, `kl_formula`; `CAS10C01.p1`, `p2`, `Tdiag`, `expectedPowers`.

P12 usage note: `P12GaussianLaw` is imported (frozen import list) and compiled, but none of its
theorems is invoked: its `law_eq_iff` is stated on `EuclideanSpace ℝ (Fin n)` only, while the G10-B
index type is the sigma type `Idx d`. B2 (`obsLaw_eq_iff`) is therefore proved directly from
one-dimensional marginals (`measurePreserving_eval`, `gaussianReal_ext_iff`); the frozen B2
statement is unchanged, only the planned proof route differs.

## Mathlib at the pin (fabf563a7c95a166b8d7b6efca11c8b4dc9d911f, Lean 4.31.0)

Searched `Mathlib/InformationTheory/KullbackLeibler/{Basic,ChainRule,KLFun}.lean` and
`Mathlib/Probability/Distributions/Gaussian/*`:

* present: `klDiv` (actual relative entropy via `llr = log rnDeriv`), `klDiv_of_not_ac`,
  `klDiv_eq_lintegral_klFun_of_ac`, `klDiv_eq_zero_iff`, chain rule `klDiv_compProd_eq_add`,
  `klDiv_compProd_left`; `rnDeriv_gaussianReal`, `charFun_gaussianReal`, `charFun_pi`,
  `charFun_eq_pi_iff`, `charFun_multivariateGaussian`, `MeasurableEmbedding.rnDeriv_map`.
* absent (gap closed in this module, not postulated): KL of two Gaussians; KL invariance under a
  measurable embedding; KL tensorization for `Measure.prod` and `Measure.pi`. Proved here as
  `klDiv_map_of_measurableEmbedding`, `klDiv_prod`, `klDiv_pi_fin`, `klDiv_pi`,
  `klDiv_gaussianReal_same_var` (equal positive variance only).

## Unrecoverable items

None blocking. Not formalized (recorded in FROZEN_TARGETS "Not targeted"): completion of `E1`
to a full orthonormal basis of trace-free symmetric matrices; anisotropic compressed-law
inequality; Gaussian KL with unequal or singular covariances in sectors other than `p`.
PR #493/#494 (card `source_paths`) are GitHub links; no remote/`gh` auth is available in this
checkout, so their content was taken from the accepted local units above (whose RETURN.json
records `head f1007dd3e41c07eccd64024dd6b44fb5a40a3612`). No state-changing git command was run.
