# Commander T-quadrupole: observed tensor morphology and a scalar-axis branch switch

## Result and provenance

This is a deterministic analysis of the already-owned Commander PR3 temperature coefficients in the R51 carrier. It computes a representation of the stored observable, without a Commander likelihood, MC calibration, confidence interval or present-day shear interpretation. Source checkout HEAD was `6fe19c5139004a1f281ec85c592e5ab4c7590d5f`.

- Carrier: `docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz`, 180416 bytes.
- Carrier SHA-256: `f0c08a115854a6f287d39eddf984291f676e6f7bb79bb2324eb92cd6eb2c0dca`.
- Original source/operator contract and generating-code identities are in `commander_source_excerpt.json` and the result's `source` field.
- The raw-map hashes are inherited from the original R51 receipt. The compact carrier was read and hashed in this run; the raw maps were not rehashed or reprocessed.
- Only observed vectors, harmonic labels, STF basis and the deterministic template response were consumed. SMICA simulation covariance and Monte Carlo arrays were not used for this result.

The parent R51 estimator masks PR3 NSIDE2048 maps using the common intensity mask, applies a finite `ell<=6` coupling inverse, and deprojects monopole/dipole columns. Its inverse uses NSIDE128 synthesized coupling columns for ell>=2 and full resolution for ell<=1. It is therefore a particular retained estimator, with inherited beam, finite-resolution coupling error and high-ell leakage. Calling these results exact coefficients of an unknown full unmasked sky would exceed their source contract.

## Exact harmonic-to-STF map

The source packs modes as

\[
d=(a_{20},\sqrt2\Re a_{21},-\sqrt2\Im a_{21},
\sqrt2\Re a_{22},-\sqrt2\Im a_{22}).
\]

For the orthonormal STF basis ordered as `(xx-yy)/sqrt2`, `(xx+yy-2zz)/sqrt6`, symmetric xy, xz, yz, write

\[
T_2(\hat n)=\hat n^TQ_T\hat n,\quad Q_T=\sum_{A=0}^4q_AE_A,
\quad q=\frac{(d_{2r},-d_0,d_{2i},-d_{1r},-d_{1i})}{\sqrt{8\pi/15}}.
\]

This is an invertible change of representation of the five measured real coefficients, in Galactic Cartesian coordinates. It requires no statistical covariance or shear transfer. The normalization follows from the normalized Condon–Shortley spherical harmonics and can also be checked from

\[
\sum_m|a_{2m}|^2=\frac{8\pi}{15}\operatorname{tr}Q_T^2,
\quad C_2=\frac{8\pi}{75}\operatorname{tr}Q_T^2,
\quad\langle T_2^2\rangle=\frac{2}{15}\operatorname{tr}Q_T^2.
\]

The Commander coefficients give, in microkelvin,

\[
Q_T=\begin{pmatrix}
-6.173408&14.765972&3.210111\\
14.765972&0.881715&6.867990\\
3.210111&6.867990&5.291693
\end{pmatrix}.
\]

| Deterministic quantity | Commander value |
|---|---:|
| C2 | 207.0624434 microkelvin² |
| Quadrupole sky RMS | 9.0767576 microkelvin |
| Ordered eigenvalues | (-17.9675337, 0.8088642, 17.1586694) microkelvin |
| Frobenius norm | 24.8577244 microkelvin |
| sqrt6 tr(Q³)/tr(Q²)^(3/2) | -0.1193055 |
| Cold eigenaxis, (l,b), one of two equivalent endpoints | (320.5980766°, 4.6186399°) |
| Middle eigenaxis, (l,b) | (223.3025813°, 57.5365602°) |
| Hot eigenaxis, (l,b) | (53.4974598°, 32.0518878°) |

These are descriptor values, not uncertainty-free measurements of a cosmological background. The full ordered eigenframe is preserved in the result.

## A concrete example of why a full tensor matters

The same estimator's SMICA quadrupole has eigenvalues `(-17.5841709,-0.1450536,17.7292245)` microkelvin and C2=208.9534451 microkelvin². The Commander–SMICA tensor difference is 2.0567121 microkelvin in Frobenius norm, or 8.2739354% of the Commander norm; its sky RMS is 0.7510051 microkelvin.

Matched cold, middle and hot eigenaxes differ by only **2.0665°, 2.4303°, and 2.5077°**, respectively. Yet a summary that retains only the eigenaxis of largest absolute eigenvalue yields an apparent **88.4993°** difference. Commander selects the cold axis, while SMICA selects the hot axis. This is a branch switch in the summary, not a nearly right-angle rotation of the tensor's eigenframe.

For a traceless tensor with ordered eigenvalues lambda_-<lambda_0<lambda_+, with the extremes of opposite signs,

\[
|\lambda_-|-|\lambda_+|=\lambda_0.
\]

Thus the extremal-absolute-value axis changes branch exactly when the middle eigenvalue changes sign. Here it moves from +0.8088642 to -0.1450536 microkelvin, while the gaps between distinct eigenvalues stay large. This is an observed-data example of information lost by an axis-only reduction. It supplies no anomaly significance and makes no claim of new spectral-perturbation mathematics.

The ordered eigenaxis stability also admits a direct residual bound. If A v_i=lambda_i v_i, B has matched eigenvector w_i, and `sep_i=min_{j!=i}|lambda_i(A)-lambda_j(B)|`, expansion in B's eigenbasis gives

\[
\sin\angle(v_i,w_i)\le\frac{\|A-B\|_2}{\mathrm{sep}_i}.
\]

For these matrices the three angle bounds are 4.7604°, 5.0149°, 4.9035°, consistent with the computed matched angles. This bound is deterministic and uses no borrowed null distribution.

## Masked-template inverse and its precise scope

The stored 5x5 quadrupole template response has rank five. The script records its condition number and reconstructs the measured Commander ell2 coefficients by its exact inverse. However, R51 generated this response with **SMICA INT_BEAM × pixel window**. Its inverse coordinates therefore describe an equivalent tensor in that reference template operator; they are not a demonstrated Commander-beam deconvolution. This secondary diagnostic is explicitly labeled as such. The primary result above uses the exact harmonic-to-STF representation, not that reference inverse.

No kinematic quadrupole has been added or subtracted in this derived analysis. The upstream map's removal convention remains unresolved in the retained source contract. No current shear, integrated physical shear, global tilt or Bianchi family is inferred from the measured temperature tensor.

## Reproduction and actual checks

The reproducible script supports either the original repository carrier or the compact allowlisted data excerpt:

```bash
python commander_lowell_morphology.py --repo-root /path/to/htt_base --out commander_lowell_morphology_result.json
```

The executed run used `--source-excerpt commander_source_excerpt.json`, whose data came directly from the source carrier. It completed with exit0, NumPy2.3.5 and SciPy1.17.0.

- STF basis Gram error: 2.22e-16.
- Analytic real-harmonic map versus R51's independently synthesized ideal template: 9.24e-16 relative.
- Direct SciPy complex-harmonic synthesis versus n.Q.n: 7.11e-15 microkelvin maximum error.
- Gauss–Legendre/angular quadrature of T2² versus sum|a2m|²: 4.55e-13 microkelvin² absolute error.
- Packed coefficient roundtrip: 1.78e-15 microkelvin maximum error.

The output also includes deterministic ell2..6 powers for both maps, source and script hashes, and complete model/inference limitations. A Commander-matched stochastic calibration and a physical transfer would be separate inputs to future inference; neither was fabricated here.
