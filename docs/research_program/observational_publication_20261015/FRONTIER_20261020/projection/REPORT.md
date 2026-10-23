# F04/F05 conditional projection on retained selected sky and depth

Date 2026-10-20. Owner `htt`; `C0`, `CONDITIONAL_DESIGN_ONLY`, non-claim-bearing. Requested parent runtime `gpt-6.1-sol/high`; observed model and effort `UNKNOWN`. This is a new solver-free calculation in draft PR #561. Original V03, S02, H02 and K04 acceptance states are unchanged.

## Inputs and calculation

The calculation reads the retained D03 `host_SN.npz` at the exact SHA-256 in [RESULT.json](RESULT.json). It uses 651 selected rows, their original row indices, RA/DEC, CMB-frame catalogue redshifts `zCMB` (0.00122–0.10142), the 18-column D03 survey/calibrator/method nuisance design (rank 16), and the selected **public Pantheon total** covariance subblock. It neither reads `y_mag` nor fits the Pantheon–CF4 differences: that difference would require an unknown cross-catalogue covariance. The released total covariance is used as one working metric. There is no second stochastic peculiar-velocity covariance, latent-PV convolution or subtraction.

At a declared flat fiducial background $(\Omega_m,\Omega_r,\Omega_\Lambda)=(0.3,9\times10^{-5},0.69991)$, a one-dimensional background distance quadrature evaluates $A=(1+z)/(E\int_0^z dz'/E)$ and $h=1+z-zA$. This quadrature is not an Einstein or Boltzmann evolution solve. The optical design in magnitudes is $(5/\ln10)[A\boldsymbol n,h\boldsymbol n]$ for dimensionless endpoint velocities. The distinct redshift-distance source model is evaluated only in its declared frozen-flow branch $u=\partial_z u=0$: $K=-(5/\ln10)(1+A)/c$ in mag/(km/s). Its calibration, constant-flow and distance-shaped flow columns are $\boldsymbol n$, $K\boldsymbol n$, and $K[\chi/\operatorname{median}(\chi)]\boldsymbol n$. The last basis is an illustrative fixed radial shape, not an observed velocity field. A nonzero underlying flow requires the radial-gradient denominator in [CONDITIONAL_MODEL.md](../distance/CONDITIONAL_MODEL.md).

Every design is whitened by the one covariance Cholesky factor, then projected off the same D03 nuisance column space. Principal angles compare the resulting three-dimensional column spaces. Conditions below use individually unit-normalized columns so velocity units do not set the reported number. Rank uses relative $10^{-10}$ threshold and is checked against the exact frozen-flow identity; the raw singular values are retained in the JSON.

## Actual selected-design result

| Projected design | Rank | Smallest principal angle or condition | Meaning |
|---|---:|---:|---|
| Optical local $A\boldsymbol n$ and history $h\boldsymbol n$ | 6/6 | angles 60.35°, 63.49°, 78.52°; condition 2.45 | Finite selected-design separation under the declared covariance/nuisance/background only. |
| Calibration versus constant flow | each 3D | angles 36.05°, 39.42°, 55.00° | These declared response shapes are distinct after D03 nuisance projection. |
| Calibration versus distance-shaped flow | each 3D | angles 1.40°, 1.46°, 1.63° | Nearly confounded within this selected depth range; the nine-column calibration/flow design condition is 165.54. |
| Calibration after profiling both declared flow bases and D03 nuisance | 3/3 | residual whitened singular values 2.246, 1.455, 1.148; smallest is 1.00% of the largest unprofiled calibration singular value | Formally nonzero conditional quotient, with weak remaining response. It is not a calibrated error bar. |
| All five three-vector blocks together | 12/15 | three zero directions, remaining smallest unit-column singular value 0.000549 | Exact cross-model degeneracy, with additional weak directions. |
| Optical columns after calibration and both flow bases treated as nuisance | 3/6 | local residual norms below $2.3\times10^{-11}$; history singular values 0.0465, 0.0313, 0.0235 | The local three-vector is absorbed exactly to numerical precision; history retains three design directions. |

The exact algebraic falsifier is $K\boldsymbol n=-[(5/\ln10)\boldsymbol n+(5/\ln10)A\boldsymbol n]/c$. Thus a free calibration dipole plus a free constant-flow dipole spans the local optical dipole in this frozen source model. This is a comparison of **different declared forward models** on the same fiducial rows. Their joint 12/15 rank is a conditional design warning, not a physically validated common-congruence likelihood.

The [plot](PROJECTION.png) displays actual selected $z_{CMB}$ versus $h/A$ and the smallest nuisance-projected angles; [PDF](PROJECTION.pdf) is the vector export. Its source and allowed use are bound in [PLOT_RECEIPT.json](PLOT_RECEIPT.json). No amplitude, posterior, p-value, source-null coverage, or physical global tilt is estimated.

## Limits and validation

The cached CMB-frame `zCMB` is a **fiducial depth coordinate** here. It is not proved to be the analytic kernel's observed normal-frame redshift. The optical and source-model kernels lack a source-matched frame/IC and full GR optical-to-kinematic relation. Selected Pantheon sky/depth and the D03 nuisance set do not supply the parent selection law, the Pantheon–CF4 cross-covariance, or finite optical/selection/calibration remainder bounds. At the shallowest selected depth, the first-order redshift-displacement domain especially needs a velocity bound. Rank does not imply stable physical identification or calibrated significance. `K` omits beaming, aberration and source/observer luminosity-distance terms; it must not be called the complete GR optical response.

The frame mismatch can change the first-order optical column itself. If observed flux remains in observer frame $\beta_o$ while redshift is corrected to a reference observer $\beta_R$, the same endpoint calculation gives $\delta d_L/\bar d_L(z_R)=\boldsymbol n\cdot[(1-A)\beta_s-\beta_o+(1+A)\beta_R]$. It reduces to the original $A\beta_o+(1-A)\beta_s$ only when $\beta_R=\beta_o$. The actual release's joint magnitude/redshift correction convention has not been bound to this formula; thus the measured-sample projection is expressly a fiducial template diagnostic.

Narrow validation: `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m unittest discover -s docs/research_program/observational_publication_20261015/FRONTIER_20261020/projection -p 'test_*.py' -v` passed 3/3 after a recorded first synthetic test failure. Its initial deterministic sky coordinates were both tied to depth, causing the extended synthetic history design to have only two surviving directions. The fixture was corrected to use independently seeded sky coordinates; no production result or tolerance changed. `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/FRONTIER_20261020/projection/compute.py` exited zero on the retained NPZ and generated the JSON/PNG/PDF. Exact cache SHA, row-index digest, response singular values and declared limits are in the JSON. The original D03 catalogue analysis was not rerun.

Next physical gates are a qualified normal/CMB frame map, source and selection law, finite remainder bounds, and a joint calibration/flow covariance if a combined inference is sought. No original scientific node is marked complete by this result.
