# R24 selection envelope on the reviewed distance cohort

Owner: HTT numerical research. Claim tier: C0 empirical diagnostic. Frozen selection input: `sha256:b02fc724d3a6360617392ad1d9deee3934d09e1a42eeb4dff535ad3fcfdaeae0`. The consumed distance candidate has manifest `sha256:1e1e0b6fabdc535bae1060b1ba3d1c61b2b1302001119c67d4a43f035dec521b` and independent scoped exploratory review. Scientific admission and original physical acceptance remain **HOLD**.

The reference law is uniform over the 274 released rows, separately for each of the four covariance scenarios and A/B/C model fits. At every threshold `t`, the event is `|OOF_signed_residual_mag| > t` with strict ties. For density ratios `w_i in [1/Gamma,Gamma]` and `sum_i w_i/274=1`, the sharp event bounds for empirical event fraction `e=m/274` are

`L=max(e/Gamma,1-Gamma*(1-e))`, `U=min(Gamma*e,1-(1-e)/Gamma)`.

Constant event and non-event class weights attain both endpoints. The calculation uses every distinct absolute residual as a step-function breakpoint, plus fixed display thresholds `0, 0.1, 0.3, 0.5, 1, 2` mag, at Gamma `1, 1.25, 1.5, 2, 4`. `SURFACE.csv` has all 16,800 scenario/model/threshold/Gamma rows; `RESULT.json` carries all fixed-threshold rows. `SELECTION_ENVELOPE.png` and `.pdf` plot the 628-frame interval width at Gamma 2 across all twelve scenario/model combinations. The complete signed OOF row matrix remains in `../distance/OOF_ROWS.csv`; the full tensor, nuisance coefficients, and covariance remain in `../distance/RESULT.json`. This envelope does not replace either source.

For the 628 known selection-frame targets, 354 binary event outcomes are undefined. The only justified extension here is `[274 L/628, 274 U/628 + 354/628]`. The fraction `274/628` is availability within this known frame, **not** a measured selection propensity or a ratio for a 5,460-object parent. At `t=.5` mag, the event counts across twelve cases are 71–80. The resulting interval widths are:

| Gamma | 274-row cohort width | 628-frame width |
|---:|---:|---:|
| 1 | 0 | 0.5637 |
| 1.25 | 0.1166–0.1314 | 0.6146–0.6210 |
| 1.5 | 0.2159–0.2433 | 0.6579–0.6699 |
| 2 | 0.3887–0.4380 | 0.7333–0.7548 |
| 4 | 0.7500 | 0.8909 |

The fixed threshold does not select a favorable model: all cases are present in the saved surface. At Gamma 1 the 628-frame interval can never be narrower than `354/628=0.563694`, even when the released-cohort event rate is known exactly. At finite Gamma and interior event fractions its mathematical width remains below one, but Gamma 4 makes the fixed-threshold frame interval nearly vacuous. As Gamma grows without bound, the unrestricted density-ratio limit is `[0,1]`. This is a conditional sensitivity analysis, not a calibrated confidence interval or probability of physical geometry. No R9 alpha calibration enters.

The unrestricted missing-data physical mean has an explicit unbounded witness: hold the 274 signed residuals and all released records fixed, set each of the 354 undefined signed residuals to an arbitrary common value `M`, and take `M` to positive or negative infinity. The 628-frame mean contains `(354/628) M`. This establishes nonidentification under that unrestricted completion model; it is not a universal physical impossibility claim. The original physical unknown-mass status remains one. A physical mean would need justified coordinate support or boundedness, source-qualified selection or overlap information, and missing outcomes or a defensible law for them. The next observable discriminator for the binary event is the 354 missing event outcomes plus inclusion/overlap evidence on the same frame.

The frozen input and every listed source hash and size matched. For the 60 fixed `t=.5` cells, 120 independent HiGHS endpoint optimizations agreed with the analytic formula within `1e-9`; maximum primal residual was `4.67e-15`, maximum dual/KKT residual `1.00e-15`. Gamma-1 parity error was zero after the bounded correction, Gamma nesting violation was zero, and explicit endpoint witness errors were below `1e-9`. Three focused tests passed, including independent small LP comparisons, strict tie semantics, and full actual-source breakpoint coverage. A first finite-width display defect and its repair are retained in `FIRST_FAILURE.txt`. Matplotlib emitted a nonfatal optional Axes3D import warning in the raw logs.
