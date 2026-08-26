# PR-324 / recovered PR-315 joint cut-sky rerun

## Result and claim boundary

The exact 300-row SMICA robustness rerun completed on code commit
`8cca592d4c9411517e52fc10ed8f5a0f16d59f9a` and tree
`0716e44d7347cd32119b22e81fb5d5817b831dc0`. The frozen PR-314 benchmark
control remains **133/301**. The separately named joint cut-sky branch also
has a two-sided finite feature-family rank of **133/301**.

This equality does not select either operator branch, does not create an MES
result, and does not identify a local boost, global tilt, source, native
solver result, or Bianchi family. The output is a diagnostic-only
operator-order robustness comparison on one SMICA shell.

## Repaired estimator

The observed row and every primary null row use one byte-identical operator
configuration. It jointly fits the 36 real harmonics at `ell=0..5` with the
common mask weight `W`, profiles monopole and dipole in that system, retains
the 32 `ell=2..5` coefficients, and applies the beam/pixel transfer only after
the joint fit. The observed operator has condition number
`6.207503806461874`, singular floor `0.15998865113244762`, and identity
`sha256:a4713d44b6057dcd241a79391abb7f4960f7aa39b20eac51cd979627352b8061`.

The pre-repair independent audit reproduced the blocking failure numerically:
the required joint oracle had coefficient error `3.97e-14`, while the old
sequential nuisance-removal substitution had error `1.939`. The repair adds
known-harmonic, fractional-mask, zero-mask-contamination, rank/condition,
operator-identity, exact-inventory, frozen-estimand, and portable-replay
oracles.

## Frozen old/new comparison

All ranks below are written on the exact 301-point observation-inclusive grid.
The tail was frozen as two-sided for every row before executing the repaired
branch.

| Feature | PR-314 value | Joint cut-sky value | Difference | PR-314 rank | Joint rank |
|---|---:|---:|---:|---:|---:|
| `cl_l2` | 193.822460808207 | 210.461847166466 | 16.639386358259 | `75/301` | `74/301` |
| `cl_l3` | 482.815005047203 | 482.020811418058 | -0.7941936291449 | `239/301` | `283/301` |
| `cl_l4` | 221.714075299019 | 225.316269015460 | 3.60219371644078 | `224/301` | `219/301` |
| `cl_l5` | 296.098420709950 | 305.485048889817 | 9.38662817986699 | `16/301` | `19/301` |
| `parity_even_over_odd_l2_l5` | 0.533482313138072 | 0.553364918467475 | 0.0198826053294024 | `88/301` | `95/301` |
| `power_tensor_gap_l2` | 0.471552874041000 | 0.449992761519970 | -0.0215601125210304 | `133/301` | `182/301` |
| `power_tensor_gap_l3` | 0.540796806265297 | 0.560137246787802 | 0.0193404405225045 | `52/301` | `35/301` |
| `multipole_l2_absdot` | 0.0792408831611066 | 0.133173437566188 | 0.0539325544050819 | `122/301` | `177/301` |
| `multipole_l3_absdot_0` | 0.352108904751443 | 0.398744286835429 | 0.0466353820839862 | `20/301` | `16/301` |
| `multipole_l3_absdot_1` | 0.387195632640763 | 0.433857519284130 | 0.0466618866433664 | `203/301` | `155/301` |
| `multipole_l3_absdot_2` | 0.519997661158611 | 0.436828492609931 | -0.0831691685486802 | `278/301` | `174/301` |
| `multipole_plane_alignment_max_l2_l3` | 0.956041311568621 | 0.940239088821206 | -0.0158022227474145 | `115/301` | `135/301` |

The complete machine-readable comparison is embedded in
`docs/generated/pr315_planck_smica_result.json`; the original PR-314 result
remains unchanged at
`sha256:898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97`.

## Input and portable replay receipts

- Raw observed map, raw common mask, and all 300 ordered CMB/noise pairs were
  hashed before execution. Manifest identity:
  `sha256:a1007a2fc6c8e680b397d86bcf383a7f1f4e608891fe3a980e64588512a86394`;
  manifest-file hash:
  `sha256:61fc9f3b0f46b0e98ccdc094f592c4219a461cd4656917fca957ea769dc9bfa3`.
- The execution used the exact PR-314 reduced SMICA observation and 300-row
  CMB-plus-noise bundle bound to that raw manifest. It did not pool any of the
  999 CMB-only rows and did not wait for Commander.
- Source execution result:
  `sha256:e80865e8e48ff49fe72d8db40952cc1598768081526eeac30b63e6308f03a15e`.
- Portable feature package:
  `sha256:b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b`;
  metadata:
  `sha256:fba7ff60c3beaa762ba0e46247c191af59b226e1b4d2464b16f2a8174d1e454a`.
- Map-free replay reproduced covariance diagnostics, all twelve local ranks,
  and the family rank with scientific projection
  `sha256:8b0aadf1897703f32c0904ad6cc6f5db41766c896382f21e709a6cd212d81750`.

The raw manifest is retained with the attended host execution; the portable
repository package contains the feature-level consumer surface and exact
content bindings, so replay does not require those host paths or raw maps.

## Verification

- RED: the recovered current-stack matrix initially stopped at import because
  no joint estimator or joint runner surface existed; the independent oracle
  also demonstrated the sequential-fit defect above.
- GREEN: the focused PR-315 matrix passes `42` tests, including negative and
  metamorphic cases and committed map-free replay.
- Exact attended execution: 300/300 ordered paired rows, terminal `SUCCEEDED`,
  portable replay `MATCH`, wall time `2.601098403 s`.
- The five frozen PR-314 evidence files were not modified.

The existing planning-only stack-integration validator still rejects the
implementation status overlay by design. Its contract is not weakened here;
the implementation-aware CI transition remains assigned to PR-330.
