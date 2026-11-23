# R99 independent C9 numerical review

The CF4, optical and Gaia calculations implement their stated production scenarios within the finite checks below. Three helper-domain defects reproduced on the reviewed source. The file hashes in `commands.json` identify the pre-repair implementations. This receipt records the original review and does not adjudicate later repairs.

## Computations and evidence

| Original remote PID | Discriminator | Observed result |
|---|---|---|
| 3868373 | Three R99 numerical test modules | 30 passed in 4.27 s, exit 0 |
| 3869481 | Coordinate optical oracle, limiting cases and direct joint Gaia covariance | Completed, exit 0 |
| 3870732 | First independent native-rapidity integration | Endpoint CDF rounded to 1, resulting in infinite moments and a failed assertion, exit 1 |
| 3870930 | Adjusted finite-domain native-rapidity integral and Gaia delete-one SVD | Completed, exit 0 |

**Optics.** For diagonal Bianchi I with directional scale factors `a_i=exp(h_i N)`, `h=(.86,1.04,1.10)`, and constant H, conserved covariant spatial momenta P give the energy `||P/a||`. The observer boost fixes P at unit observer-frame photon energy. For each perturbed observed sky direction the oracle solved the emitter-frame energy condition at measured z=.51 and integrated its spatial coordinates. The transverse area from centered angular differences tests the angular and position variations, observer angle normalization and emission event simultaneously. At angular steps 1e-4 and 1e-5 rad the coordinate distances were 0.3752559796017155 and 0.375255980086078 Mpc. Fractional discrepancies against the variational solver were 1.3074010762892385e-9 and 1.6648682432673922e-11. The root in N differed by 3.3306690738754696e-16. Both observer and emitter were moving in distinct, oblique directions.

**CF4.** Differentiating the Doppler relation at fixed observed redshift gives `dzbar/dr=−(1+z)` at zero rapidity. The three signed responses are `K+1/c, K, K−1/c`. A fixed-design modulus change gives `−(ln 10/5) AGd`. In the nonlinear first chaos the response per unit latent velocity is the first orthonormal coefficient divided by its marginal scale. Projected coherent covariance and the independent 150 km/s diagonal occur once each. The 250 km/s working weight is used to construct A. The modulus-error covariance enters once in the linear reference score. The nonlinear product supplies a projected first-chaos covariance and bounds for omitted terms. Joint selection uses field weights proportional to the joint inclusion probability.

For a constant-H distance, z=.002, scale 300 km/s and the bolometric convention, the independent adaptive quadrature in standardized native rapidity gave `[.12576701,.60422944,.23881306,.07122259]` (mean, first coefficient, second coefficient, beyond-first variance). The corrected integration used endpoint gap `t=cap−r/(sigma/c)` on `[1e-12,cap+11]`. The largest absolute discrepancy against GH48 was 2.455966874315152e-9. Both attempts used this same variable. The changed lower bound protected the independent inverse CDF calculation at the close endpoint. The comparison includes this finite truncation; it makes no certified quadrature-error claim.

**Gaia.** With fixed weights, the perturbed normal equations give `J_p=F^{-1} F_p E` for every fit. One common latent sky gives all cross blocks of the joint covariance and induces the contrast response `J_a−J_b`. A dense flattened Kronecker product agreed with the implementation to 1.4210854715202004e-14 on the 3-fit, 5-patch, 4-coefficient, 2-field example (NumPy seed 309). Direct SVD on the centered real 48×160 delete-one estimates gave rank 47, supported quadratic 524.5928366832607, unsupported norm 14.410872486713433 µas/yr, and unsupported squared norm fraction .18837362792548287. The coherent scenario and empirical patch covariance are separate outputs. A calibrated source-overlap/noise model remains an external physical input.

## Reproduced boundaries

| Object | Actual pre-repair behavior | Lowest-impact correction |
|---|---|---|
| Flat optical beam near observer | Positive target z=1e-15 returned actual z=0, distance=0 and parity=0. The z=1e-12 control returned positive distance and parity. | Resolve a nonvertex root or signal that it is numerically unresolved. |
| CF4 zero latent variance | A one-source positive-redshift input with sigma=0 raised ValueError. The deterministic limit has four zero moments for each response type. | Handle zero-variance rows explicitly. |
| Gaia relative spectral cutoff | For y=t(1,2,5), C=t² diag(1,2,0), ranks were 2 and 0 at t=1 and 1e-21. | Scale by the actual positive maximal eigenvalue and handle a zero matrix explicitly. |

## Reproduction context

Exact stdin bodies, remote shell wrappers, interpreter versions, test paths and reviewed file hashes are preserved alongside this report. Compose the command strings as specified by `commands.json`. These original executions predate the repairs. Running the same probes on later source can change the printed boundary diagnostics. The focused probes used the existing checkout and R98 sufficient-statistic cache. This review did not rerun the full historical campaign or full catalogue products, inspect acquisition completeness, or execute four-axis CAS.
