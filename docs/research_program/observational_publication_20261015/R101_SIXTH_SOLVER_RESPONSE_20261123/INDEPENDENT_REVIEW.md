# Independent numerical and physical review of the R101 sixth-cycle candidate

Parent baseline `f8931fbef075d55c2c2a3caee8b8f5db5174b16b`. The reviewer had no authorship of the implementations, applied no source edits, and made no repository mutations. Errors below are absolute in the normalized variables of their respective fixtures. Owner-environment executions and the reviewer’s direct computations are distinguished.

## Findings and repairs

1. **High, resolved. Real IVP initial data discarded complex evolution.** With the constant basis `V=e1`, identity metric and generator `A=[[0,i],[i,i]]`, the original split IVP returned `(1,0)` at time one for `X(0)=e1`. The independent matrix exponential gives `(0.57670212−0.14319745i, −0.38560514+0.70584547i)`. For `X(0)=e2` the original initial-hidden-force result was `i`, compared with `i exp(i)`. SciPy inferred a real IVP dtype from the real initial state. After the repair, the maximum endpoint error is `5.28e−12` and the hidden-force error is `7.56e−12` at the default tolerances, with zero dtype warnings. A generator with a hidden block `i s` also recovers the memory factor `exp(i/2)`. Seven moving-projection test functions ran successfully.
2. **Moderate, resolved. The signed Mueller repair lost precision for nearly parallel rays in generic coordinates.** Let `n=(1,2,3)/sqrt(14)`, let `u` be the normalized transverse projection of `(.3,−1,.6)`, and set `v=n×u`. Rotate `(n,u)` through `1e−14` rad in their plane, holding `v` fixed. For input `(I,Q,U)=(1,.31,−.42)` the candidate initially returned errors `(0,−3.40e−7,+4.60e−7)` relative to the unnormalized Jones pair result `2(I,Q,U)`. Normalizing the difference of nearly cancelling Cartesian cross-product components corrupted the screen. The revised cross product uses the small difference of rays near parallel or antiparallel incidence. In 1,620 seeded comparisons over nine separations from zero to π, including `1e−14` and `π−2e−14`, the maximum discrepancy against direct Jones overlaps was `3.78e−15`. The 90° physical sign is consistent with power perpendicular to the scattering plane, giving `Q/I=−1` for an outgoing positive-Q axis in the plane.


3. **High in the deep-optical-depth limit, resolved.** The initial coupled SDIRK stage factored six Cartesian symmetric moments. At large depth, adding an O(1/s) correction to a singular order-one matrix destroyed the numerical trace pivot. For an isotropic unpolarized unit field, the exact shifted collision stage with unit diagonal leaves that field invariant for every s. The old maximum errors at s=1e8, 1e14, 1e16, and 1e17 were `1.58e−9, 2.66e−3, .0993, 6.79e48`. An explicit trace plus five STF coordinates and scaling the trace equation resolve this. Against the same analytic invariant, the repaired maximum error was `6.67e−16` over s=1e4 through 1e250. This check probes the conservative pole directly and does not depend on a possibly ill-conditioned dense solve.


4. **High for parameter-response work, resolved.** The initial coupled SDIRK default switched to independent exact subflows exactly on the parameter axes. With RNG seed 49, the 18-ray test grid, `k=(.5,−.2,.4) Mpc⁻¹` and `Δχ=5 Mpc`, the outputs for `Δτ=0` and `1e−14` differed by 1.972 in one step. At depth 5, changing distance from zero to `1e−14 Mpc` produced a jump of .470. The repaired default applies the same second-order rule through each axis; the two discrepancies fell to `2.05e−14` and `7.95e−16`. Explicit `method="strang"` retains the exact single-process subflows. SDIRK phase accuracy depends on time resolution even on the free-streaming axis.
5. **High for the normal execution entry point, resolved.** The CF4 subprocess required an output filename, while the new science-program runner invoked it without that argument and parsed standard output. The corrected CLI emits result JSON when invoked without the optional output filename. The covariance-only ordinary CLI returned valid schema `htt.r101.cf4_predictive_response/1` on the recovered R100 matrix, with endpoint replay error `5.69e−14`.

## Independent calculations and scope

- **Electron-rest collision.** For each pair of oriented screens, the reviewer formed the Jones overlap `D=B_out B_in^T`, applied `D ρ D^T` to the complex Hermitian incoming density, then summed with `3 w/(8π)`. The convention `ρ_uv=(U−iV)/2` fixes the circular sign. On an independent 4×9 quadrature and a seeded random full-Stokes field, the maximum differences from the native gain were `3.33e−16, 2.78e−16, 1.94e−16, 1.39e−16` in I,Q,U,V. The finite-step rank-nine construction follows from gains 1 for the trace, 7/10 for the symmetric trace-free moment and 1/2 for the antisymmetric moment. A single optical-depth increment multiplies this fixed rest-frame collision generator. Seven coherency test methods ran in the selective-source harness with the pinned dependency functions.
- **Cellwise reaction network.** For homogeneous class A, `dt_b/dN=1/(Γ_b H_n)` on the matter worldline and `n_H,rest Γ_b a³=N_H`. The optical-depth coefficient of `x_e` along a ray is `σ_T c N_H exp(−3N)(1−β·e)/H_n`, dimensionless per e-fold. The implementation obeys both relations. An independent generic five-state eigendecomposition and weighted reward integration agreed with the propagated population and charge to `5.1e−14` and `5.8e−15` over the tested rates. In an additional three-state scale-separated network, the fast pair interconverts at rate M with both states losing population to the third at rate one. At cell width one the exact fast-pair sum is `exp(−1)` and its electron reward is `(1−exp(−4))/4`. Maximum discrepancies were `2.22e−16` for the population and `1.12e−16` for the reward in trials up to M=1e240. Ten chemistry test methods ran successfully. Charge yields and transition rates are supplied inputs. This finite network establishes no anisotropic atomic line-escape solution.
- **Joint history.** On the supplied 64-cell fixture the code gave total depth `13.6364409219578`, derivative `−7.26773762193276`, and maximum sky central-difference discrepancy `2.45e−11`. Independently applying the cell propagators in order differed from the single total-depth action by `1.56e−15`. The chain rule is `δS_f=exp(κC)δS_i+C S_f δκ`. It applies to a fixed common rest frame with no intervening forces or streaming. The joint driver rejects nonzero fiducial β and nonzero β tangent. Two joint test methods ran successfully.
- **Apparent CF4 covariance and selected marks.** For contrasts `T,W`, the conditional innovation `B=W−W C Tᵀ (T C Tᵀ)⁻¹ T` obeys `B C Tᵀ=0`, which makes the covariance derivative `B δC Bᵀ`. The selected-mark denominator marginalizes each object's Gaussian inclusion probability at fixed field before summing over the common field. A negative inclusion observation contributes its integrated miss probability in both component sums. Seven tests exercised GLS, mask conditioning, Gaussian integrals, Jacobians and finite differences. On R100 covariance input SHA-256 `7d5ecd55b776b8b9b97ae32385fd4573db8916846bb4c0a6dc5eca85eab18093`, the endpoint changes in χ² and log density were `−1.1886554949492858` and `−0.7681113812646174`. The discrepancies with integrated analytic derivatives were `1.60e−14` and `4.59e−14`. The covariance interpolation is conditioned on the published compressed input. The release-match probit and finite field represent a same-cohort conditional sensitivity model. Independent selection calibration, full physical covariance, physical Π and G_F remain separate scientific obligations.
- **Moving projection.** Differentiating `L V=I` gives `(L′+L A)V=L A V−L V′`. With `Q=I−VL`, the resolved-to-hidden drive is `Q A V−Q V′`; the hidden generator is `Q′+Q A`. These are the implemented blocks. Their Volterra representation retains the initial hidden-state force. Evidence concerns the supplied finite-dimensional evolution and full-rank chart.

## Fourier transport

For an independent dense oracle the reviewer formed each four-channel gain block from `G_ab=w_b[3/(16π)] Tr(σ_s D_ab σ_t D_abᵀ)`, using the identity and the three Stokes Pauli matrices in I,Q,U,V order. The upper-left block of the affine exponential was `−i Δχ diag(n·k)⊗I₄ + Δτ(G−I)`. Each of the 15 rays used one weight from a 3×5 GL/azimuth quadrature. With `k=(.05,−.04,.12) Mpc⁻¹`, `Δχ=13 Mpc`, and random complex initial data and forcing (NumPy generator seed 25325), the explicit Strang optical-depth-zero result agreed with the oracle to `1.25e−15`. At `Δτ=3`, symmetric-split errors for 16, 32 and 64 substeps were `1.4173e−3, 3.5454e−4, 8.8647e−5`. At `Δτ=60`, the one-step error was `0.241`; the 32-to-64 error ratio reached 3.82. This confirms second-order fixed-cell refinement and quantifies loss of accuracy from an unresolved thick-cell split. For the actual HyRec table interval z=950–1150, the reconstructed comoving path is 41.02159085 Mpc. The independent flat-FLRW integral of c dz/H(z) using the table header matter, radiation and vacuum densities gives 41.02001261 Mpc, a fractional discrepancy of 3.85e−5. The spacetime is prescribed flat FLRW for this calculation and propagation follows the `exp(+ik·x)` convention.


The final coupled default is stiffly accurate SDIRK(2,2) with γ=1−1/√2. At depth 3 on the fully complex 61-dimensional augmented oracle above, errors for 16/32/64 time subdivisions were `7.9873e−4, 1.9802e−4, 4.9309e−5`. At depth 1000, one step gave error `2.3608e−2`, and 16 and 64 subdivisions gave `4.8063e−11` and `2.9889e−12`. On the finite-resolution free-streaming axis, SDIRK gave `1.0087e−4` at 64 subdivisions. These figures concern the explicit test state, source and wavevector. Thirteen collision/Fourier test methods passed after the trace and axis repairs.

## Execution map and resources

All 60 output IDs were joined directly to the pinned R78 DAG and R100 overlay. Every scientific acceptance string equals the R78 string, and every inherited status and hard-dependency list equals its R100 counterpart. The 129 canonical edges and original-42 digest `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d` are preserved. The map has 18 inherited scoped completions and 42 inherited blocked rows, with zero new scientific acceptances. Its next node remains SQ-CF4. The five conditional jobs are shared across nodes. Running them cannot establish 60 new physical results. The frozen graph input SHA-256 is `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11` and the actual predecessor overlay SHA-256 is `41fdd3851ae6902d62fb37fd1ac17c7c6a2beb3f110f3f6aa863d141fcc09287`.

The recovery configuration's three Git member paths and byte hashes match the recorded source inventory, and all five atomic table hash targets occur in the recovered manifest. Identity and scientific calibration have different evidence. The active project instruction admits this native numerical work and preserves inherited physical acceptances; the SI clock and rest-frame restrictions in the SSOT are consistent with the implemented paths.

Reviewer runtime was CPython 3.12.14, NumPy 2.3.5, SciPy 1.17.0, using one OpenBLAS thread. The local solver harness uses selected pinned dependencies, with separate comparisons against the candidate function definitions. Package-wide test execution, original observational inputs and resource installations are attributed to the owner environment when available.


## Owner-execution evidence, independently read

The reviewer read the original owner-side run records and obtained SHA-256 directly on that host. The owner source files corresponding to all 25 reviewed entries below matched the candidate byte for byte. Context assembly, graph preparation, all-job analysis, scoped tests, the R100 validator and whitespace checks each returned zero. The full five-job conditional batch took 8.98 s. Its five subprocess receipts included the ordinary `CF4_RESPONSE --source-marks` route, returned zero and named result files. The owner pytest log records 55 tests plus 26 subtests in 57.41 s. This was a scoped battery.

On the 7,190 release matches, the signed five-field mixture minus zero-field *conditional* log densities were `−224.66408677` under the historical cut and `−11.94215950` under the fitted match probit. Adding all 1,695 observed nonmatch/ambiguous indicators from the 8,885-member released 6dFGSv cohort gave `+27.34102020`. At a single fixed zero field, the latter two log densities agree to about `1e−12`, as they must when the extra negative factors cancel. The historic same-row replay differed by `2.01e−11` or less. The full-pattern amplitude score was `−24.82702237` and its central-difference discrepancy was `1.12e−6`. These values come from owner execution on the two source files identified in the result. The reviewer independently inspected the result and its internal identities and ran the Gaussian/probit method controls on local data; raw catalogue reduction was executed once on the owner host. The reported change of sign depends on observed inclusion conditioning, finite field support, supplied mark widths and fixed fitted coefficients. The scope remains apparent release-match sensitivity.

The resource receipt reported eight installed payloads with matching observed and expected SHA-256, three Git objects and five atomic tables, plus six available baseline commit objects. It explicitly records `physics_qualified=false`. Resource identity recovery is complete for those eight inputs.

| Owner-side evidence file | SHA-256 |
|---|---|
| OWNER_RUN_RECEIPT.json | `5198f221434912def0bb8f7b959ea7972bd0da09f39c3fb4a4a63ceecefe8dcc` |
| CF4_PREDICTIVE_RESPONSE.json | `ea3c7e1aa94dc46c07fb4b808e6df8af3213bef35ce39ef8758020bdae16a44f` |
| RESOURCE_RECOVERY.json | `3606e381b23f536859ff56b20ea6df6cda336d08b98cf03a79bb8c1ec305fbd9` |
| EXECUTION_RECEIPT.json | `d5ca9108fa09b30f9a5e4f28da9fa52d268b0c255350bce5cbb9c587cb2ebf88` |
| scoped_tests.log | `39a13675926fab8b78af82bedaf90d9a287e997fb2482f096c7cc0b2310247da` |

**Verdict.** The reported implementation, numerical checks and conditional results are supported at the scopes described above. Each reproduced implementation defect was repaired and its stated regression rerun. This numerical review supplies no new observational source qualification, Bianchi family assignment, coupled Einstein–Boltzmann atlas or original DAG node admission.

## Reviewed-file SHA-256

Paths in the intended owner repository. These byte identities apply to the candidate inspected.

```text
4a688eac43ead850a5e619cc4f1b2edf599bb63c334d32b00129c37c30c55977  htt/htt/htt/infer/cf4_predictive_response.py
f323bb7be1da866dffce9c1e464321f8fca67c37d6b5fa0d7e1d9d6604a79e5e  htt/htt/tests/test_cf4_predictive_response.py
ad89429ade17be42cf34221f7d924a6c189b3956fb41c2d897bb26eb22c1603e  scripts/r101/cf4_predictive_response.py
099bac66e683d1bd65a6ea702a80b181f20effe33680909f3a12ffcc4dffab84  scripts/r101/benchmark_cf4_response.py
f6bb175315f64266f5f82e6b6649d3f56d8bee7f4913af39aac1a67ed810a74c  htt/bass/collision/coherency.py
9f460bb6fddde3ce7250fd1326b4117e4ae1b113266a0760096f5c6080d52b7a  htt/bass/collision/electron_frame.py
50b062a69f2a79a7ed239a9af209f405ccc8b24003f64eec6781f58cf68f06a5  htt/bass/collision/__init__.py
951139e76bd4d8c853b4dddeb5f1e06e68be88bd92803f0fdf09a96f82964fd6  htt/bass/collision/test_coherency.py
86755c53ad87e477dad8496f346d3dee4acc1185def8dc14a963b9f58d61010b  htt/bass/collision/test_full_stokes_thomson.py
552f7078423227582764c7806e2e307c5b20de0736ddd8376b7650b3538af84b  htt/bass/transport/stokes_fourier.py
bc84ab69c9bf7b9d85ee678d6959a561333851d12dcbc4d6f19dc2eacc513c18  htt/bass/transport/test_stokes_fourier.py
917705b470d0f3206c6a735c972ebebd2ee30eba13bf55e0ec7f17d7230d0b61  scripts/r101/coherency_history.py
555ea8a43acffded480d5df89807bb18008765d9cf7c29534e9bf5b99f0b6f64  scripts/r101/coherency_checks.py
5cbc1f5382e76e33dc2126c60fbada56a1c65c9c981ec4926de5a3a9806d281c  htt/bass/recombination/clocked_chemistry.py
08b10de9bdda82c6f609472a5a5589cbf2511ab3d91583db3611397b2e5e92f4  tests/obsstat/test_r101_clocked_chemistry.py
d6d4030d5c320597b329870705f6b5b5397fa8441406e47bd79374887618765d  htt/bass/kinetic/moving_projection.py
be622fbb8de1c9f95fa1e0cdf9dfe90b8b186d74be4fe78ccfaca7a2bf6b3383  tests/bass/test_r101_moving_projection.py
74b6e80de0372ed5c68b66dd6b5bffdd793767af5e89d5222621d39f4459b3de  scripts/r101/chemistry_coherency.py
0b3ac35d22fcd429a6843f3956667084ad3f728a3359dd7545673169acbc7e92  tests/bass/test_r101_chemistry_coherency.py
913fe7a648703f79266c8ab26ea1e011646a3c09e2635e3e5e680b3b427ad502  scripts/r101/moving_projection_checks.py
10f9dd49a479b8016ad4b56bfd97342992c238871fe02fda9494894aec6a11b2  scripts/r101/program.py
ee6b2d5cedc11f1c7cb3be4ef106b0f4842ca6bd4a883151f9444a670caa6e95  scripts/r101/recover_legacy_resources.py
6b63d110888dd638b2947028773f9d2ed65130ae234eb9fdd62c38eebfb46493  configs/r101/legacy_recovery.json
a5867e1266166e5d7d2c9d19a0a1e01b09855a5beb1b30defa2a91a5290e7fea  AGENTS.md
876d5660158f5694b9a889d38ddeff19eee5aaf42a92783e424969fb11cc2db3  docs/SSOT_POLICY.md
```
