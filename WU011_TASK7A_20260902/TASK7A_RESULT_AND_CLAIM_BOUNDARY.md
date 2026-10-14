# PMG-WU-011 Task-7A deterministic evidence result

## Exact authority

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Source head: `b2422d9435eafbebd2584b747cb4b4ef9716caaf`
- Artifact branch: `artifact/wu011-task7a-b2422d9435eafbebd2584b747cb4b4ef9716caaf`
- Artifact commit: `db8c0f4a1bbce86a0fa82ba5941aaef0e6f040cf`
- Manifest SHA-256: `eb9617d1d0947cc4bb2c87c2d4f5e22f9804af55a7d26f4db731f6cbbea763f0`
- Report content ID: `sha256:1a8fcf04ac2ea3da4b92512ad51d25e680682e035b0d3cd4fe5783dcb9b690db`

## Terminal

`PASS_TASK7A_CORE_EVIDENCE`

This terminal means that the synthetic evidence runner, exact-head binding,
mutation gates, matrices, tables, figures, and checksums are reproducible. It
does **not** mean that the bounded reference cut-sky operator is suitable for
inference.

## Full-sky oracle and convergence

The exact nonzero singular sectors obey

`Sigma_ell^2 = {8/3, 27/5, 13, 21, 125/11, 216/13}`,

with multiplicities `{3,5,7,9,11,13}`, rank `48`, structural physical-`T0`
nullity `1`, nonzero condition `sqrt(63/8)=2.806243040080...`, total metric
Frobenius square `656`, and source-`ell=6` physical-neighbour Frobenius norm
`6 sqrt(6)`.

The finite-HEALPix response converges rather than matching the continuum
operator exactly at development resolution:

| nside | max spectrum error | trace error | ell7 alias / ell5 neighbour |
|---:|---:|---:|---:|
| 8 | 8.680242e-3 | 1.322087e-5 | 5.338692e-3 |
| 16 | 2.046596e-3 | 7.773862e-7 | 1.285804e-3 |
| 32 | 5.044222e-4 | 4.786966e-8 | 3.186572e-4 |

Spectrum orders are `2.0845,2.0205`; raised-alias orders are
`2.0538,2.0126`; the matrix drift is approximately second order and the trace
approximately fourth order. At `nside=32`, changing `processing_lmax` from `7`
to `12` changes the metric-whitened matrix by `2.570432e-11`.

## Other gates

- finite-minus-linear slope: `2.0014819336`
- wrong-sign retained slope: `1.0139904479`
- omitted-ell1 pixel slope: `0.9999999089`
- omitted-ell1 retained relative norm: `5.400954e-11`
- FWL/full-solve residual: `2.726907e-12`
- historical fixed-axis relative residual: `1.475331e-7`
- historical sign mutation: `1.9998588736`
- transfer-order mutation difference: `4.019354e-2`

## Load-bearing negative result

For `CUT_N16_L12_REFERENCE`:

- metric-whitened nonzero condition: `407.914947`
- FWL Schur condition: `15415.6425`
- physical `ell=6->5` neighbour norm: `11.9668365`
- raised-`ell=7` processed alias norm: `257.027636`
- alias/neighbour ratio: `21.4783276`

The current reference cut-sky configuration is therefore deterministic and
algebraically consistent but strongly alias-dominated and poorly conditioned.
No data fitting or empirical velocity estimate is admitted.

## Exact-head workflows

- WU011 `#29 / 33591195000`: SUCCESS
- Task7A `#5 / 33591195018`: SUCCESS, `4 passed in 37.14s`
- PR04 `#489 / 33591195001`: SUCCESS
- PR07 `#483 / 33591195015`: SUCCESS
- Repository integrity `#723 / 33591195050`: SUCCESS

A separate portable-replay determinism anomaly is tracked as GitHub issue
`#445` and Jira `BASS-25`.

## Claim boundary

The result concerns a synthetic processed local-observer scalar boost only.
It does not admit a Planck absolute-temperature product, observed rank,
empirical beta, boost subtraction, global matter-frame tilt, polarization,
foreground exclusion, Bianchi-family attribution, causal identification, or
the unavailable P01--P27 formal-dossier replay. PR #444 remains draft and
unmerged.
