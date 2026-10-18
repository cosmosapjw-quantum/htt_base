# SF07: fixed-estimator Gaia angular covariance sensitivity

For the saved 4,756-source outcome-selected Gaia EDR3 cohort, an assumed spatial covariance family can enlarge the uncertainty of the saved spin/glide estimator substantially while keeping each source's published 2×2 covariance unchanged. This calculation holds the original linear estimator **M fixed**: the coefficient center stays fixed and its sampling covariance is recomputed as M C Mᵀ. It does not refit generalized least squares or measure Gaia's empirical angular covariance.

## Definition and PSD derivation

Let nᵢ be the ICRS unit direction and Eᵢ the 2×3 matrix with orthonormal east and north tangent rows. East is the coordinate of Gaia's already scaled proper motion μₐ cos δ; north is μδ. All proper motions and coefficient centers use mas/year. Let Cᵢ be the saved symmetric positive definite 2×2 marginal covariance, and Sᵢ=Cᵢ¹ᐟ² its unique principal symmetric square root.

For a declared half-correlation angle θₕ∈(0,180°], define

kᵢⱼ = exp{−ln(2) ‖nᵢ−nⱼ‖²/[4 sin²(θₕ/2)]}.

The scalar latent kernel is one half at separation θₕ. It is a squared exponential kernel restricted from Cartesian space to the unit sphere; see [Rasmussen and Williams, Gaussian Processes for Machine Learning, §4.2.1](https://gaussianprocess.org/gpml/chapters/RW4.pdf). This is an established covariance construction, rather than a novelty claim.

A direct proof uses t=ln(2)/(1−cos θₕ)>0 and kᵢⱼ=e⁻ᵗ exp(t nᵢ·nⱼ). For any finite real vector z,

zᵀ k z = e⁻ᵗ ∑ₚ₌₀^∞ (tᵖ/p!) ‖∑ᵢ zᵢ nᵢ^{⊗p}‖² ≥ 0.

Each tensor-power term is a Gram matrix, and the series converges absolutely for finitely many unit directions. Thus k is PSD. Now set Aᵢ=Sᵢ Eᵢ and, for 0≤ρ≤1, declare

Cᵢⱼ(ρ,θₕ) = (1−ρ) δᵢⱼ Cᵢ + ρ kᵢⱼ Aᵢ Aⱼᵀ.

The full source covariance is the sum of the PSD independent block matrix and a congruence of k⊗I₃. It is PSD. Its diagonal blocks are exactly Cᵢ because kᵢᵢ=1 and Eᵢ Eᵢᵀ=I₂. For ρ<1 the positive independent part makes it positive definite; ρ=1 can be singular in degenerate fixtures and receives no eigenvalue floor. The evaluated six-coefficient covariances are all positive definite.

Here ρ is the fraction of each marginal covariance allocated to the correlated field, whose latent amplitude is √ρ. It is **not** every observed pair's correlation coefficient. Tangent projection and unequal Sᵢ also change the observed cross correlation. The principal square root is a declared modeling convention: it makes the family equivariant under independent tangent basis changes. Specifically, Eᵢ′=RᵢEᵢ, Cᵢ′=RᵢCᵢRᵢᵀ, Sᵢ′=RᵢSᵢRᵢᵀ, Mᵢ′=MᵢRᵢᵀ imply Mᵢ′Sᵢ′Eᵢ′=MᵢSᵢEᵢ. Global Cartesian rotations preserve pairwise chord distances and the latent contractions.

## Block evaluation and fixed grid

Define Hᵢ=MᵢSᵢEᵢ (6×3). Then

V₀=∑ᵢHᵢHᵢᵀ, Vcorr(θₕ)=∑ᵢⱼkᵢⱼHᵢHⱼᵀ,

V(ρ,θₕ)=(1−ρ)V₀+ρVcorr(θₕ).

The code flattens H to an N×18 operator and applies one block of k at a time. It never builds the 9,512×9,512 source covariance or an N×N kernel in the real-data run. The default 256-source block has 1,217,536 kernel entries, about 9.74 MB per float64 block; direct chord evaluation needs up to three such arrays transiently, in addition to the small response arrays and library overhead. This is an allocation estimate, not a measured process RSS.

Before inspecting outcomes, the worker declared θₕ={1°,5°,20°,90°} and ρ={0,0.01,0.05,0.2,0.5,1}. These bracket compact to broad assumed latent coherence and 1% to full correlated marginal variance. They are fixed sensitivity scenarios. There is no empirical fitted amplitude, empirical kernel selection, or claimed physical envelope covering all Gaia laws.

## Actual numerical results

Directional uncertainty ratios are extrema over parameter direction u of √[(uᵀV u)/(uᵀV₀u)]. They are computed as square roots of generalized covariance eigenvalues. The same ratios apply to projection widths of the joint Gaussian ellipsoid because its radius q₀.₉₅=√χ²₆(0.95)=3.54846265920102 is shared. The joint region and volume are conditional on the assumed fixed-cohort Gaussian law.

The central reference law is β̂−β_ref ∼ N(0,V), with β_ref=M E[y] for the fixed estimator and declared covariance. Its ellipsoid has 95% coverage for that reference mean. Coverage for physical coefficients also needs zero or separately bounded deterministic bias; the upstream outcome selection does not supply that condition.

| Declared θₕ | Smallest directional σ ratio, ρ=0.01 | Largest directional σ ratio, ρ=0.01 | Largest directional σ ratio, ρ=0.2 |
|---|---:|---:|---:|
| 1° | 1.002076 | 1.002765 | 1.053918 |
| 5° | 1.048296 | 1.063732 | 1.905390 |
| 20° | 1.487422 | 1.656679 | 5.990971 |
| 90° | 2.005122 | 3.713361 | 16.024389 |

Every one of the 24 assumed-grid joint 95% ellipsoids contains zero. At independence, the coefficient Mahalanobis distance is 1.8996605; at θₕ=90°, ρ=0.01 it is 0.8824379. This describes the conditional geometry of the saved estimator and the declared covariance. It is not an empirical Gaia p-value or a Bianchi-family test. The result JSON contains all 6×6 matrices, component standard deviations, joint projection halfwidths and six-dimensional region volume ratios.

For this cohort and these four scales all evaluated directional variance changes increase relative to independence. The mathematical covariance construction alone does not guarantee this relation: at fixed marginal scales correlations can reduce some estimator directions in other designs. The code reports both directional extrema and does not replace the correlated covariance with a blanket inflation factor.

Generated figures: `results/gaia_correlation/angular_correlation_sensitivity.png` and `.svg`. The plot shows smallest/largest projection-width ratios across the declared grid and carries the claim tier and assumed-law qualifier. Its scratch preview was visually inspected; labels, curves and footer were readable.

## Validation and preserved evidence

The small fixture independently forms Ablock [(k⊗I₃)] Ablockᵀ plus independent source blocks, then contracts the dense 2N covariance with M. It includes nearly coincident directions, antipodal directions, coordinate poles and heterogeneous non-diagonal positive covariances.

- Synthetic dense/operator maximum relative discrepancy: 3.6583×10⁻¹⁶.
- Each source marginal maximum relative discrepancy: 7.0750×10⁻¹⁶.
- Small dense source covariance minimum eigenvalue: 3.5026×10⁻¹⁵; degenerate endpoints can be PSD rather than SPD.
- Independent tangent-basis rotation relative discrepancy: 3.0829×10⁻¹⁶.
- Global Cartesian rotation relative discrepancy: 2.1495×10⁻¹⁶.
- Block partition relative discrepancy: 1.0301×10⁻¹⁶.
- Saved V₀ covariance parity: 1.9652×10⁻¹⁵; saved coefficient parity: zero absolute difference.
- Independent dense assembly using 12 actual saved sources: 2.0637×10⁻¹⁶.
- Targeted tests: 21 passed. They also reject invalid amplitudes, angular lengths, block sizes, source covariances and frames, and test coincident-source rank and endpoint behavior.

The actual all-cohort numerical contraction completed in 2.3923 seconds with `/usr/bin/python3`, `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, block size 256. This duration excludes plot generation. The first execution log is retained. The only execution warning was Matplotlib's unused Axes3D import being unavailable; the two-dimensional PNG and SVG were generated successfully. No numerical failure occurred.

Frozen source identities:

| Source | SHA-256 |
|---|---|
| `gaia_bias_sensitivity_v1/influence_blocks.npz` | `d5384f57138f4e8ea7b986153bf0133f846e9f7806bdf82b2cb7ac4d6a676c9f` |
| `gaia_frame_v1/qualified_rows.npz` | `41b6ddcb13131b49b97efd6107816af4518fa9e23725cf3b4272c2f3a70acb8f` |
| `gaia_bias_sensitivity_v1/result.json` | `7af1f6b3508826b69f7170891146536398104779962de76d9d4355c8b9e4415d` |

Execution base was `2fb4ae497eecc6d5fd73f931f250c763ee6d266d`. Requested worker runtime was `gpt-6.1-sol/high`; independently observed model and effort remain `UNKNOWN`. A separate read-only reviewer requested as `gpt-6-astra/xhigh` independently recomputed the 4,756-source contraction with an alternative 2×2 square root and SciPy distances (maximum covariance-relative discrepancy 6.40×10⁻¹⁴; generalized-eigenvalue discrepancy 3.56×10⁻¹⁴), checked all 24 matrices positive definite, and returned scoped PASS. Observed reviewer model and effort remain `UNKNOWN`. The reviewer requested that the Gaussian reference mean be stated explicitly; the parent repaired the report and result contract, regenerated the result, and confirmed the numerical grid was unchanged. This review does not establish empirical Gaia coverage.

## Research loop and next use

R1–R5 defined the fixed-estimator question, reused exact operator/source rows, separated assumed law from empirical covariance, chose the embedded Gaussian construction and derived PSD/marginal/equivariance results. R6–R7 checked limiting/degenerate cases, coordinate conventions, independent dense assembly and actual source contraction. R8 classified the output as `DESCRIPTIVE_CONDITIONAL`. R9–R10 provide the reusable formulas, code, scoped review and this integrated report.

C1–C4 fixed base/input identity, traced M/C/directions to H and the block contraction, chose a constant-marginal scale family and fixed the grid before evaluation. C5–C8 implemented the complete CLI, performed 21 tests and dense/symmetry/rotation/partition controls, then produced the 24 numerical scenarios and plot. C9 received a separate fresh review and one targeted clarification repair. C10 is the runnable integrated handoff with preserved logs and source references.

The immediate useful extension is to replace the assumed kernel and amplitude with externally qualified Gaia cross-source covariance, or compare an independently selected cohort. The outcome-dependent cohort selection, unknown empirical joint law, and exact-direction assumption remain limitations. No native solver or ODE integration was used.
