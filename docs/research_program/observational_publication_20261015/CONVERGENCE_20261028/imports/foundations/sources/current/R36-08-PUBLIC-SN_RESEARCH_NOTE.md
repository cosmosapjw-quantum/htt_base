# R36-08 public SN released-magnitude comparator

**Status:** proposed conditional result, awaiting fresh independent scientific review. The numerical owner is HTT. This is an additional released-observable estimand; it does not fulfill the original H04/V04 or nominal SALT2 pipeline acceptance.

The input is Pantheon+SH0ES `c447f0fea703fcd0fff57de5000947b5ca81286b`, using `Pantheon+SH0ES.dat` (579,283 bytes, SHA-256 `1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8`, Git blob `cce857db0c15e9ce7a0e0ce77452b6ff62af969a`) and `Pantheon+SH0ES_STAT+SYS.cov` (33,284,960 bytes, SHA-256 `abf806d966485e64afdb359c87bffc0ecc00d05eff0a31ced66f247385df0fdc`, Git blob `d1a1498154e7ba826df14bdbef35ebcb7f5efba1`). The prepared input receipt is `/mnt/extdrive/workdir/htt_open_data/r36_public_sn_acquisition_preparation/PREPARATION_RETURN.json`; this analysis downloaded zero additional bytes. The 1,701 table rows and 1,701² finite covariance entries retain original order. `CID` is not unique: the full table has 158 repeat rows; 77 rows are flagged calibrators. Both row and covariance axes use the same original indices, retaining 62 repeat rows in the 490-row primary cohort and 114 in the 705-row sensitivity cohort. `USED_IN_SH0ES_HF` is retained as a flag, not used as an extra cut.

## Frozen estimator and covariance scope

The primary selection is `IS_CALIBRATOR=0` and `0.0233 ≤ zHD ≤ 0.15`, with low depth `zHD < 0.06`; the single sensitivity extends only the low end to `0.01`. All required columns must be finite. The fixed dimensionless reference is

\[
\mu_\mathrm{ref}=5\log_{10}\left[(1+z_\mathrm{HEL})\int_0^{z_\mathrm{HD}}\frac{dz}{\sqrt{0.3153(1+z)^3+0.6847}}\right],\qquad y=m_{b,\mathrm{corr}}-\mu_\mathrm{ref}.
\]

One global magnitude intercept and one high-bin offset are profiled. They absorb the additive calibration and depth level; neither is an independent absolute H0 measurement. The 16 angular columns are bin-specific `(n_x,n_y,n_z,nᵀE₁n,…,nᵀE₅n)` in the H03 signed Frobenius STF basis. The null uses two nuisance columns, the dipole comparator adds six dipole columns, and the full model adds all 16 angular columns. Axes are the released RA/DEC Cartesian chart. The RA/DEC physical reference frame is **UNKNOWN**.

The released STAT+SYS matrix is used once as the **marginal selected** covariance `P C Pᵀ`, including cross-CID, survey and depth blocks. No diagonal `m_b_corr_ERR_DIAG`, VPEC error, additional PV term, jitter, rescaling, symmetrization, or covariance subtraction is applied. The full 1,701-array **fails** the frozen symmetry tolerance: maximum `|C−Cᵀ|=3.0×10⁻⁸ mag²` at original rows 84,97 versus `9.45×10⁻¹² mag²`; 389 unordered pairs exceed it. Every affected pair lies outside even the 705-row selected union. Both consumed subblocks are exactly symmetric as stored and Cholesky positive definite; their smallest eigenvalues are 0.00524236 and 0.00522765 mag². This bounded validation-scope repair was approved in `/mnt/extdrive/workdir/htt_open_data/r36_public_sn_covariance_repair/REPAIR_DECISION.json` (SHA-256 `3cd28db0b16f66baef4175c5dfe80f6af0f0522465931ac4fdea315cf92e4ab3`). The full source array is **not** certified as a valid covariance. Its asymmetry's upstream cause is **UNKNOWN**. The first failing run and its original code remain preserved under `/mnt/extdrive/workdir/htt_open_data/r36_public_sn_actual/`.

Cholesky-whitened GLS projects out both nuisance columns and fits unit-column SVD. All angular rank checks are 16 at relative thresholds `10⁻¹²`, `10⁻¹⁰`, and `10⁻⁸`. The quadrature-32/64 maximum relative differences are below `5×10⁻¹⁶`. The predeclared primary statistic is `ΔT=T_null−T_full` and has a conditional `χ²₁₆` upper-tail reference only under the stipulated fixed-design Gaussian law with known selected total covariance. The nominal 0.05 threshold is 26.2962. No empirical population/null coverage is established.

| Cohort | low / high rows | `T_null` | `T_dipole` | `T_full` | joint `ΔT` | conditional upper-tail `p` |
|---|---:|---:|---:|---:|---:|---:|
| Primary | 342 / 148 | 433.4585 | 426.4087 | 416.2519 | 17.2066 | 0.37235 |
| Lower-z sensitivity | 557 / 148 | 608.5020 | 598.8732 | 591.9479 | 16.5541 | 0.41500 |

Both joint statistics are below the stipulated nominal threshold; the primary comparison does not reject its isotropic two-level nuisance model under that conditional law. The two cohorts overlap and are not independent confirmations. Sixteen leave-one-survey primary fits all retain rank 16; `ΔT` ranges 14.0415–18.9251. These deletions are descriptive and correlated. The maximum whitened design leverage is 0.3545 (0.3570 in sensitivity); this is not an influence-adjusted null calibration.

The primary signed magnitude coordinates `(n_x,n_y,n_z,E₁,E₂,E₃,E₄,E₅)` are

| Depth | Dipole [mag] | STF coordinates [mag] |
|---|---|---|
| Low | `(0.01758, 0.03002, 0.01848)` | `(-0.02498, -0.00347, -0.02821, 0.03248, -0.03670)` |
| High | `(0.00223, 0.02426, 0.05879)` | `(0.00732, 0.10264, -0.03053, -0.03636, -0.05776)` |
| High minus low | `(-0.01534, -0.00576, 0.04031)` | `(0.03230, 0.10611, -0.00232, -0.06884, -0.02106)` |

For physical readability, the **apparent-magnitude STF matrices**, in the same released chart and in mag, are

\[
Q_\mathrm{low}=\begin{pmatrix}-0.019077&-0.019947&0.022968\\-0.019947&0.016246&-0.025954\\0.022968&-0.025954&0.002832\end{pmatrix},\quad
Q_\mathrm{high}=\begin{pmatrix}0.047081&-0.021590&-0.025709\\-0.021590&0.036724&-0.040845\\-0.025709&-0.040845&-0.083805\end{pmatrix}.
\]

The complete signed 16-vector, its **full 16×16 covariance**, the exact cross-bin covariance, the high-minus-low eight-vector and its covariance are in [RESULT.json](RESULT.json). In the primary fit, all 50,616 low/high covariance entries are nonzero, with maximum absolute entry 0.01998029 mag². The simultaneous 95% 16-dimensional coefficient ellipsoid has squared Mahalanobis radius 26.2962 under the stipulated law. Bin and contrast coordinates are descriptive; no additional binwise testing rule was prespecified. [Figure](PUBLIC_SN_SIGNED_COORDINATES.pdf) shows signed coordinates with marginal one-standard-deviation bars; it is **not** a simultaneous acceptance plot.

At fixed released redshifts, the observer-chart conversion subtracts `10 log10(1+zHEL)` from **both** the observed magnitude and reference mean. Thus `y`, selected covariance, coefficients and coefficient covariance are invariant (maximum real-data coefficient difference below `10⁻¹⁴` mag). A one-sided subtraction changes the residual by more than `10⁻³` mag and fails the explicit falsifier. This is the `dL/(1+zHEL)²` chart conversion; it is not a physical boosted-observer fit. A physical boost also changes photon redshift, aberration/direction, distance response, selection and possibly uncertainty. `zHD` already incorporates released VPEC corrections, while `zCMB` is retained but is not substituted for the photon redshift. Signature is `(-,+,+,+)` and `c=299792458 m/s`; no time-rate or shear tensor is inferred from these magnitude coordinates.

**Claim audit:** The observed conditional apparent-magnitude vectors and likelihood comparison belong to HTT at C1/CONDITIONAL, with `RESULT.json`, full raw result, figure and source-bound consumer as evidence. Physical observer frame, raw-to-congruence response, shared-PV CF4 covariance, nominal SALT2 training parity, empirical source-population coverage, and Bianchi-family or acceleration/shear interpretation remain **UNKNOWN/HOLD**. This result supplies no MIO inference, native solver output, or original 42-node acceptance. The figure and this note are candidate evidence pending independent review.

Reproduce with `.venv/bin/python consumer.py`, `.venv/bin/python test_consumer.py`, `.venv/bin/python survey_robustness.py`, and `.venv/bin/python plot_result.py` from this directory (set `OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`). The consumer writes the full row-indexed raw result to `/mnt/extdrive/workdir/htt_open_data/r36_public_sn_actual/RESULT_RAW.json` and the compact result here. The first failing run, final command outputs, exact selected row IDs, source hashes and full-source asymmetry report are retained in the same external scratch directory. No network access or native solver is used.
