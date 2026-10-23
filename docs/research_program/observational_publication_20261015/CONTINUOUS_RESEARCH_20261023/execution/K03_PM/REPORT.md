# K03_PM conditional proper-motion profile experiment

**Owner:** HTT conditional estimator, using frozen obsstat proper-motion features. **Scope:** fixed 755,850-row Quaia–Gaia matched sample and reported redshifts. **Claim tier:** C0 derived conditional diagnostic. **Transfer source:** analytic flat-FLRW two-ray specialization of [Marcori et al., arXiv:1805.12121v1](https://arxiv.org/abs/1805.12121v1); no native Bianchi transfer. **Covariance:** frozen per-source 2×2 Gaia proper-motion blocks only; residual cross-source spatial covariance is unknown. **Null status:** algebra and small synthetic design checks, with no empirical coverage calibration. **Allowed use:** inspect fixed-design response separation and its failure of the small-velocity domain. **Forbidden use:** physical omega/curl detection, a dust-following quasar source law, radio combination, or original K03 admission.

## Source-bound construction

Use signature (-,+,+,+), flat `ds²=-c²dt²+a²dx²`, normal-frame velocity `β=v/c`, sourceward unit vector `n`, tangent projector `P=I-nnᵀ`, and ICRS tangent components `(μ_α cos δ, μ_δ)`. Set the independent first-order density, metric, shear and lensing perturbations to zero. The compensated history is `β_m=b/a`, `β_r=-Rb`, with `R=3 ε_m0/(4 ε_r0)=7499.25` in the frozen positive dust+radiation example. The optional local observer velocity is `ℓ`; source centroids **would have to** follow dust for this conditional source law to apply. That qualification is absent for the actual optical and radio centroids.

For a retarded source at background comoving distance `χ`, `dt_s/dt_o=a_s/a_o` at zeroth order. Its normal-frame displacement per observer time is consequently `c β_s/a_o`, not `c β_s/[a_o(1+z)]`. Including the observer displacement and first-order aberration gives `μ=P{c(β_s-β_o)/(a_oχ)+dot β_o}`. Substitute `β_s=(1+z)b`, `β_o=b+ℓ`, and `dot β_o=-H₀b+dot ℓ`. With `I=H₀χ/c`, the displayed tangent mean is

`μ(n,z)=P[H₀ (z/I-1)b-H₀ℓ/I+dot ℓ]+r_μ`.

The omitted `r_μ` is an unbounded physical/source/processing remainder here. The free `dot ℓ` appears as a common E1 glide and is profiled out. This normal-tetrad derivative is not, by itself, matter four-acceleration. At each fixed true depth the displayed field is an E1 gradient and has zero spherical curl; it supplies no `ω` response. [Gaia-CRF3](https://doi.org/10.1051/0004-6361/202243483) qualifies additive global frame rotation, which the B1 nuisance span removes under fixed rows and weights. [Truebenbach and Darling, arXiv:1710.02099v1](https://arxiv.org/abs/1710.02099) describe radio source-specific time-series slopes and NNR concerns; no common radio B1 transfer is presumed.

For the frozen synthetic `Ω_r=10⁻⁴`, `Ω_m=1-Ω_r`, `Ω_Λ=Ω_k=0`, `H₀=70 km s⁻¹ Mpc⁻¹`, set `Q=√[(1+z)(1+Ω_r z)]`. Then `I=2z/(1+z+Q)`, `k_b=z[1+(1+Ω_r+Ω_r z)/(Q+1)]/2`, `k_ℓ=-(1+z+Q)/(2z)`. `K_H=14.76646685987891 μas yr⁻¹` converts dimensionless velocity to the fit amplitudes `a_b=K_H b`, `a_ℓ=K_H ℓ`. Only positive reported `z` values enter this plug-in calculation. The exact three-depth response determinant is `det([1,z,I])/∏I_j`, nonzero for ordered depths when `I` is strictly concave; actual selected-design rank is measured below. The control `r→0` has EdS determinant `-1/2` at depths `(5/4,3,21/4)`; that limit is not a compensated nonzero-radiation model.

## Fixed-design execution

The frozen A22-05 `G_old` and `b_old` contain 102 columns. The 96-column nuisance map retains its 84 angular/template/stress columns, all nine binwise B1 columns and the three *common* E1 sums. It fixes old sky normalization and leaves the R23-Q estimator untouched. The one new full row pass computed only `A=HᵀC⁻¹H` (6×6), `K=HᵀC⁻¹X_old` (6×102), and `q_H=HᵀC⁻¹y` (6). The retained NPZ is `/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz`, SHA-256 `70fc2fee88803a7211c1c157ff87b4adb05b0807a00c03dc38d51f31b3842662`. The old 102×102 Gram and score were read unchanged. `N=TᵀG_old T`, `J=KT`, `F=A-JN⁻¹Jᵀ`, `s=q_H-JN⁻¹Tᵀb_old`, and `θ̂=F⁻¹s` were evaluated by unit-diagonal Cholesky solves, without an explicit inverse, jitter, clipping, a prior, or row dropping. The full `F`, `Cθ=F⁻¹`, spectra and controls are in [RESULT.json](RESULT.json).

| Quantity | Retained result |
|---|---:|
| Reported-z range | 0.0863450393–4.627459689 |
| `a_b` (`x,y,z`, μas/yr) | `(-1.22239, -1.04142, -0.99306)` |
| Working SD of `a_b` (μas/yr) | `(0.91333, 0.82672, 0.84926)` |
| `a_ℓ` (`x,y,z`, μas/yr) | `(0.65573, 0.26309, 0.63180)` |
| Working SD of `a_ℓ` (μas/yr) | `(0.38799, 0.35859, 0.36364)` |
| Numerical ranks, threshold `10⁻¹⁰` | history 3, local 3, joint 6 |
| Unit-diagonal `F` condition | 7.32446 |
| Unit-diagonal `N` condition | 623346.78 |
| Principal angles, degrees | `(43.8552, 44.0919, 44.2923)` |
| Profiled history information retention | `(0.48002, 0.48415, 0.48765)` |
| Canonical-pair condition | 6.17085 |

The principal angles compare the *residualized* history and local three-component spaces after the fixed nuisance projection. They establish finite-matrix separation for this working metric, not an admissible physical velocity fit. All six full-covariance entries and the 3×3 profiled history covariance are retained in RESULT.json. The latter matches the independent Schur computation to relative `7.4×10⁻¹⁶`.

## Physical domain and validation

The formal tangent point yields `R‖a_b‖/K_H=958.89`, `(1+z_max)‖a_b‖/K_H=0.71955`, and `‖a_b+a_ℓ‖/K_H=0.06964`. The working largest-axis one-SD scale gives `R√λ_max(C_bb)/K_H=476.11`. Thus the estimate and its working uncertainty are plainly incompatible with the required `R|b|≪1` small-velocity domain. These ratios do not supply a physical posterior, a velocity bound, or a certified finite remainder. The printed `a/K_H` values in RESULT.json are formal tangent coordinates only.

Focused controls passed: high-precision closed kernels at five depths, low-z limit, source clock/sign substitution, constant-H null, EdS determinant, dense whitened QR versus streaming Schur estimates and full covariance on a small synthetic fixture, same-depth nonestimability, nuisance and H injections, and tiny principal-angle matrix cases. On the final retained score model, maximum estimator algebra/control residual is below `8×10⁻¹⁵`, against the `10⁻¹⁰` identity gate; nuisance-shift errors are below `10⁻⁹(1+‖θ‖)` μas/yr. The first fixture test failure and subsequent stdout serialization failure remain in FIRST_FAILURE.txt and REUSE_FIRST_FAILURE.txt. Neither involved a second full row pass. The actual pass took 20.15 seconds wall, peak RSS 285,948 KB, exit 0; RUN_STDOUT.txt and RUN_STDERR.txt preserve its output. A matrix-only postprocess installed normalized Cholesky solves; REUSE_STDOUT.txt preserves the final fit output. The figure [PROFILE_DIAGNOSTIC.png](PROFILE_DIAGNOSTIC.png) and [PDF](PROFILE_DIAGNOSTIC.pdf) are generated by [plot.py](plot.py) from RESULT.json, without a source-row pass.

**Original K03: HOLD.** The selected optical centroid motion has no dust-following source law; reported-to-true depth and selected-source likelihood are absent; Gaia time/calibration residuals and cross-source spatial covariance are unqualified; radio NNR and session-slope transfer are absent; no finite remainder or nonradial curl/vorticity propagation law is established. This scoped conditional experiment awaits a fresh independent review before its own scoped decision. It cannot close original K03 acceptance or promote a native solver result.
