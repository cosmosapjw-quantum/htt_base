# R24 optical STF image of the reviewed distance fits

Owner: HTT observational scenario analysis. Claim tier: **C0 conditional tensor scenario**. The consumed input is `R24-OPTICAL-SHEAR_INPUT.json`, SHA-256 `af216d8bd92fcc4814294e785abdcb72b4576f685ca5ca18808841b5779d09e0`. The reviewed distance candidate is `distance/ARTIFACT_MANIFEST.json`, SHA-256 `1e1e0b6fabdc535bae1060b1ba3d1c61b2b1302001119c67d4a43f035dec521b`. All six declared source hashes and five declared byte counts matched before analysis. No upstream fit was rerun or altered. The source cohort contains 274 released distances of 628 selected objects; the other 354 distance outcomes remain undefined.

## Interpreted result

The stored `B_optical_STF` and `C_union` fits contain five magnitude-residual STF coordinates in a Frobenius-orthonormal J2000 basis. For each of four declared covariance shapes, `RESULT.json` carries the full fit coefficient vector and covariance, the five-dimensional STF covariance, its cross-covariance with every other fit coordinate, the reconstructed 3×3 magnitude tensor, and the conditional normalized optical tensor. Model A has no STF coordinates; its full coefficient state is retained with an explicit **undefined** tensor status, never filled with zeros. At fixed redshift, for a small anisotropy of a single chosen optical response, the *scenario* conversion is

\[
B(n)=B_{ab}n^an^b,\qquad (\sigma_{\rm eff}/H)_{ab}=-(\ln 10/5)B_{ab}.
\]

The angular direction points from observer to source; no vorticity term enters this STF conversion. The `eff` subscript is essential: the distance-model coefficients are selected-window magnitude residuals. They have not been mapped to local kinematic shear of a registered congruence. The conversion is a linearized fixed-redshift scenario, and its large reference upper endpoints do not verify the small-anisotropy approximation.

We form one declared algebraic reference region for **all** coefficients in each stored fit: `(beta-beta_hat)^T C_full^{-1}(beta-beta_hat) <= chi2_{p,0.95}`, with `p=12` for B and `p=15` for C. The full covariance and the stored training ML plug-in scale enter before the STF projection. The exact five-dimensional projected ellipsoid supplies the maximum tensor norm through a secular equation; the origin is inside every projected ellipsoid. The label `0.95` defines the fixed-Gaussian reference quantile only. It is **not** an observed 95% confidence event or calibrated survey coverage: the distance product omits fit-coefficient/scale uncertainty from its prediction law, and its calibration/PV covariance, selection law, and finite-redshift optical response are not source qualified.

| Authored covariance `(a,b)` mag | Model | Point `||sigma_eff/H||_F` | Reference norm interval | Conditional `Sigma_eff²` upper, `r=0` | Upper, `r=.25` |
|---|---|---:|---:|---:|---:|
| `(0,0)` | B | 0.359637 | `[0,1.048135]` | 0.183098 | 0.500426 |
| `(0,0)` | C | 0.386692 | `[0,1.148916]` | 0.220001 | 0.560330 |
| `(0,.29)` | B | 0.301808 | `[0,1.051248]` | 0.184187 | 0.502225 |
| `(0,.29)` | C | 0.295550 | `[0,1.120075]` | 0.209095 | 0.542841 |
| `(.055,0)` | B | 0.365472 | `[0,1.050904]` | 0.184066 | 0.502026 |
| `(.055,0)` | C | 0.396764 | `[0,1.155737]` | 0.222621 | 0.564506 |
| `(.055,.29)` | B | 0.302750 | `[0,1.051046]` | 0.184116 | 0.502109 |
| `(.055,.29)` | C | 0.296920 | `[0,1.120260]` | 0.209164 | 0.542952 |

Here `r` is a **declared**, dimensionless full-sky `L²(h₂/H)` remainder sensitivity radius, not a measured optical error. The recorded radii are `0,.05,.10,.25`; the table shows the endpoints. For each reference tensor, `||h₂/H||_{L²}=sqrt(2/15)||sigma_eff/H||_F` and the reported algebraic upper is `(5/4)(||h₂/H||_upper+r)²`. The lower is zero for every radius because the full joint reference region already permits a zero quadrupole. Thus no strictly positive shear-sector lower bound is obtained, even with zero declared remainder. Group-dependence choice `b` shifts the point tensor appreciably (for C, `0.387` to `0.296` at `a=0`); the full tensor/covariance arrays, not only these norms, are the result. The point estimates and upper endpoints are sensitive to the model and authored covariance assumptions. They are not physical G-shear measurements.

## Physical boundary and missing input

The exact local T2 identity is `Sigma_u²=(sigma_u:sigma_u)/(6H_u²)=(5/4)<(h₂/H_u)²>`. Its interval theorem requires one simultaneous event for the *local* quadrupole error and positive `0<H_minus<=H_u<=H_plus`, with finite-redshift, boost, selection, and calibration errors included in the radius. No such event or absolute `H_u` was supplied. The free magnitude intercept cannot measure `H_u`. The `H_minus<=0` stratum has an unbounded T2 upper quotient, rather than a fabricated finite limit. The map from the selected optical window to the registered G congruence and a measured finite-z remainder are **HOLD**. No dipole, vorticity, global tilt, Bianchi family, or physical `x_C` is inferred. Original 17/42 external status (alternate analytic 18/42) and the R9/one-use/ultra histories are unchanged.

The next physical input is a source-matched optical/Jacobi and finite-redshift response, including calibration and flow/selection error on the same selected objects and an independently registered common congruence with a positive joint H interval. These would define a new qualified event and radius; they cannot be filled from the existing magnitude intercept or declared sensitivity values. For T7 consumers, the stored full coefficient state and all cross-blocks permit a future joint tensor functional projection; `RESULT.json` is a `tensor_scenario` input, never a confidence bundle or a scalar-only shear norm.

## Validation and claim audit

`python -B analyze.py` completed eight defined images and four explicit undefined Model-A strata. Tensor reconstruction, trace, frame-rotation covariance spectrum, orthogonality and proper-rotation checks were all below `1e-12`; the exact secular boundary residual was below `1e-9`. Three focused independent tests passed: an exact-product full-sky fourth-moment quadrature, a separate SLSQP ellipsoid optimization plus full-Jacobian/cross-covariance reference, and radius nesting/undefined-strata checks. The plotted PNG/PDF were generated from `RESULT.json` without a refit. Matplotlib emitted only its unrelated optional Axes3D import warning, preserved in `PLOT_STDERR.txt`; there was no analysis or test failure. No report/manuscript claim or original DAG acceptance is promoted. Scientific admission remains **HOLD** pending independent review and the missing physical inputs.
