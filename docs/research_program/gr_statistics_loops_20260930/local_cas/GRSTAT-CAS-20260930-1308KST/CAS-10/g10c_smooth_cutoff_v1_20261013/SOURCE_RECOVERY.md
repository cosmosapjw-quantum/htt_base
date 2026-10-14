# G10-C source recovery (cutoff mollifier, smooth radial extension, derivative bound)

Repo HEAD at recovery: `00e547daffbf2c8e2f444c5651203f3a32e99d74` (working tree dirty; the files cited
below were hashed as found on disk, 2026-10-13).

## Cited sources (sha256)

| role | path (repo-relative) | sha256 |
|---|---|---|
| task card | `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` :: `HTT_ALL_OBLIGATIONS_20261011/tasks/G10-C.json` | card bytes `609124c44b2fed0dc93b0c033e837a298ec5fe441ba5752c77493a4ff4aefe07`; zip `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f` |
| CAS-10 contract (C04 statement) | `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-10.json` | `03dd5c3c8e3d8c30cf75058b48138a5208ac5f664a51533fb5d945ffee06f43f` |
| common spec | `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` (matches the contract's source_input_hashes) |
| original analytic statement (research provenance named in CAS-10.json) | `docs/research_program/gr_statistics_loops_20260930/statistics/INFORMATION_LIMIT_THEOREMS.md` §5, Theorem III, lines 137-176 | `775b7d151d894dc33e3896e9e00674a8de6e2432c7bf96ad5ee70d64f2b63b1a` (matches CAS-10.json research_provenance_hashes) |
| accepted C04 execution contract | `.../CAS-10/c04_cutoff_extrema_v1_20261008/EXECUTION_CONTRACT.json` | `8f2f5e387e8130f605073c650c9c0174253dd70e34ae4d4fbb23c697b53ead3a` |
| accepted C04 admitted inputs | `.../c04_cutoff_extrema_v1_20261008/ADMITTED_INPUTS.json` | `1df59b533e32a7f21d3a7a1ee90c39cf6451b42bcd10d4ec580bdb031a47e992` |
| accepted C04 Lean source | `.../c04_cutoff_extrema_v1_20261008/lean/CutoffExtrema.lean` | `ab2f98d27e4d00694c428258e78a81dd438d38066b5d28c08090fd2c12b7c1f3` |
| accepted C04 return | `.../c04_cutoff_extrema_v1_20261008/RETURN.json` (aggregate `CAS_4AXIS_PASS`, review `REVIEW_RETURNED_REPAIR_CLOSED`, scientific_admission `HOLD`) | `ee7c024145f36f1a7adcf7a356b0ef4e58c8d284cd453723db722633422847e2` |
| C04 Sage proof note | `.../c04_cutoff_extrema_v1_20261008/sage_singular/PROOF.md` | `06ba8d7e5f8960c564e5e1b1287912f2b005814faa1aa61402d2f8d519f363d7` |

PR #495 (card `source_paths`) was not fetched (gh is unauthenticated in this environment); its
content is represented by the accepted local C04 run above, which the card names as
`existing_reuse` ("PR495 exact endpoint derivatives/extrema 15/8,10/sqrt3,1147/1152<1").

Note on access: CAS-10.json marks INFORMATION_LIMIT_THEOREMS.md as
`orchestrator_identity_only` for the C04 CAS axes. G10-C is a different task whose card asks
to "confirm the original cutoff regularity, support, plateau and radial domain"; that text exists
only in this file, so it was read for G10-C. Recorded here for the reviewer.

## Recovered C04 object (CAS-10.json C04; ADMITTED_INPUTS.json; CutoffExtrema.lean)

- `F(t) = 1 - 10t^3 + 15t^4 - 6t^5`, real `t` in `[0,1]`.
- `F' = -30 t^2 (1-t)^2`, `F'' = -60 t (1-t)(1-2t)`; endpoint jets
  `F(0)=1, F(1)=0, F'(0)=F'(1)=F''(0)=F''(1)=0`.
- `max_[0,1]|F'| = 15/8` at `t=1/2`; `max_[0,1]|F''| = 10/sqrt 3` at `t=(3±sqrt 3)/6`.
- `(25/24)(14/15+9/400) = 1147/1152 < 1` (with stated inputs `exp(1/25)<25/24`, `sqrt 3>12/7`).
- C04 exclusions / remaining obligations: "no mollifier existence or smooth radial extension",
  "two-point probability bounds", "science". G10-C targets the first one only.

## Recovered original cutoff statement (INFORMATION_LIMIT_THEOREMS.md, Theorem III, line 148-153)

Verbatim content (LaTeX stripped):

> Use the C^2 cutoff q0(r)=1 for r <= a/4, q0(r)=F(2r/a-1/2) on [a/4,3a/4], and q0=0
> afterwards. It is defined on the whole real line. Since max|F'|=15/8, max|F''|=10/sqrt3,
> we have ||q0'||_inf <= 15/(4a) and ||q0''||_inf <= 40/(sqrt3 a^2). Convolve with any
> nonnegative unit-integral C^inf mollifier supported in [-a/8,a/8]. The resulting q is smooth,
> remains in [0,1], is one on r <= a/8, zero on r >= 7a/8, and has the same derivative bounds.
> The function q(|x|) is smooth even at x=0, because it is constant nearby.

Radial domain: `a > 0`; `q0` on all of `R`; the physical radial variable is `r = |x| >= 0`,
`x in R^3` (the source uses Minkowski spatial slices; we prove the radial statement for an
arbitrary real inner-product space, which includes `R^3` / `EuclideanSpace R (Fin n)`).

Regularity as stated in source: `q0` is called **C^2** (correct: `F'''(0) = -60 != 0`, so `q0`
is not C^3). Only the mollified `q` is called smooth.

## Which "original bound" the card means

The card's "원래 bound" / "원래 numerical margin" is the pair of sup-norm derivative bounds that
the source asserts survive mollification ("has the same derivative bounds"):

- `sup_r |q'(r)|  <= 15/(4a)`        (= (2/a) * 15/8)
- `sup_r |q''(r)| <= 40/(sqrt 3 a^2)` (= (2/a)^2 * 10/sqrt 3)

together with `0 <= q <= 1`, plateau `q = 1` on `r <= a/8`, support `q = 0` on `r >= 7a/8`.
These constants are exactly the ones fed into (I13): `|chi''| + |chi'|^2 <=
(40/sqrt3) delta/a^2 + (225/16) delta^2/a^2` with `chi = delta q`, and through (I14) into the
rational margin `1147/1152 < 1` (C04). Because G10-C proves the bounds with the *identical*
constants (no `+delta` loss), the downstream strict margin is not consumed. The margin
inequality itself (and the I13/I14 chain) is not re-proved here.
