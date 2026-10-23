# R25-K03-DEPTH-COVROBUST: reported-depth covariance sensitivity

This is a new selected reported-redshift contrast, not the earlier six-slope-zero test. The null sets all three E1/B1 six-vectors equal, giving twelve restrictions. For the retained full24 mean and covariance, `M` maps bin intercepts and the shared six-slope with rational reported-z centers `(1/4, 7/12, 26/33)`; `A=H M` takes adjacent-bin contrasts. The full 24-coordinate covariance, including all cross-bin and slope blocks, is used in `Vτ=A(C24+τ²I24)Aᵀ`. No cross block is deleted, and no jitter or pseudoinverse is used. Units of the 24 coefficients, contrasts, and τ are µas/year; covariance units are (µas/year)².

| τ (µas/year) | T₁₂ | Gaussian χ²₁₂ reference survival | Distribution-free moment upper bound |
|---:|---:|---:|---:|
| 0 | 381.199232 | 3.60205e-74 | 0.031480 |
| 0.1 | 365.703533 | 6.78851e-71 | 0.032813 |
| 0.3 | 277.269896 | 2.73919e-52 | 0.043279 |
| 1 | 78.081312 | 9.57251e-12 | 0.153686 |
| 3 | 11.075522 | 0.522458 | 1 |
| 10 | 1.032367 | 0.999983 | 1 |

At standalone α=0.05 the moment threshold `12/α=240` is crossed at τ=**0.377552 µas/year**; the Gaussian χ²₁₂ threshold `21.026070` is crossed at τ=**2.139565 µas/year**. For scale comparison only, α=1/80 gives Gaussian threshold `25.530418` crossed at τ=**1.926255 µas/year**. Its moment threshold is 960, already above T₁₂ at τ=0, so there is no nonnegative crossing. The reported root residuals are below 1e-8 and the brackets are in [RESULT.json](RESULT.json). [figure.png](figure.png) shows the actual curves, thresholds, and finite crossings; it uses a log scale for T₁₂ so the absent 960 crossing remains visible.

The Gaussian tail is a centered Gaussian reference under covariance dominated by `Vτ`. The moment bound follows from zero contrast mean, deterministic `Cov(d) ⪯ Vτ`, `E[T] ≤ 12`, and Markov's inequality. These are conditional reference laws, not observed calibrated p-values. A data-selected method choice makes this application exploratory. The old slope6 zero statistic is 12.140206 with a working-tail scenario 0.058913; it concerns a different null and does not resolve this contrast. Neither α level reuses an R9 budget.

The output carries the complete full24 mean and covariance, `M`, `A`, every tabulated `Vτ`, and the full transformed `G_F=(Y0,δ1,δ2)` covariance. `F` defines exact linear support of each full24 ellipsoid by `h(v;τ,ρ)=vᵀµ24+ρ√(vᵀU24(τ)v)`; ρ is a named reference radius with no survey coverage claim. `Qref=10 µas/year` remains computational, while the physical MES anchor is unavailable. The original 4,096-row conditional Gaussian empirical `Pi` law is referenced unchanged; the new robust tail bound is not `Pi` and no new empirical law was calibrated.

The deterministic checks recomputed `M` from rational centers, verified rank 12 at tolerances 1e-8/1e-10/1e-12, Cholesky/eigen agreement, common-mode cancellation, full24 permutation consistency, proper rotation and polar/axial parity, cross-block retention, and support-function geometry. Test and production commands, resource observations, and first-failure status are in [RAW_RECEIPT.json](RAW_RECEIPT.json). The original K03 physical acceptance remains **HOLD**: true-depth law, physical source response, spatial covariance qualification, and physical anchor are unavailable. This result supports only a conditional covariance-sensitivity discriminator; it does not identify a Bianchi family or validate a native solver.
