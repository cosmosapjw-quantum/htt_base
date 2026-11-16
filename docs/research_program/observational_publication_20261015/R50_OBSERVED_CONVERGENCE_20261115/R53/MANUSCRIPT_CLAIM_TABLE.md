# R53 manuscript claim table

Scope: Planck PR3 SMICA low-ℓ temperature (FFP10-calibrated), Gaia/Quaia G<20.0 proper-motion carrier, Quaia/NVSS/RACS count dipoles, Planck 2018 solar dipole, CF4 grouped apparent-H operator. Claim tier C0. Numbers: `R53_BENCHMARK.json`, `../R51/R51_RESULT.json`, `../R52/R52_RESULT.json`. Figures: `FIGURES/F1–F5`.

Status: **derived** (follows from stated equations), **checked** (numerically verified on owned data or exact limits), **unresolved** (open input or theory).

## Results tables

**Table 1. Integrated shear from Planck PR3 SMICA T, ℓ=2–6 (finite-MC law, 300 FFP10 pairs).**

| quantity | value |
|---|---|
| Σ̂ (orthonormal STF5, Galactic) | (0.02, 0.66, −0.97, −0.20, −0.21)×10⁻⁵ |
| 1σ (LOO-calibrated) | ≈ (1.00, 0.95, 1.06, 0.96, 1.00)×10⁻⁵ |
| Σ=0 test, same-estimator LOO null | p_MC = 0.884 |
| 95% upper limit \|Σ\|_F | 3.74×10⁻⁵ |
| conditional \|σ/H\|₀,F (Bianchi I, no anisotropic stress) | < 9.5×10⁻¹⁰ |
| kinematic-quadrupole removal | UNBOUND (removal not verified); sensitivity ≤ 0.25σ |

**Table 2. Covariance law calibration on held-out FFP10 (ids 200–299; covariance from 0–199).**

| carrier / law | central 68% | central 95% | KS p |
|---|---|---|---|
| T45 finite-MC | 0.67 | 0.96 | 0.76 |
| T45 plug-in Gaussian | 0.36 | 0.68 | 9×10⁻²¹ |
| TEB135 finite-MC | 0.69 | 0.95 | 0.73 |
| TEB135 plug-in Gaussian | 0.00 | 0.00 | 0 |

**Table 3. Method comparison, same law, prior and data (T45; 3-fold held-out FFP10, 300 independent noise draws; covariance from the other 200).**

| method | 95% coverage, per component (pooled) | max \|ΔlogLR\| vs full t-law | Fisher retention (analytic) |
|---|---|---|---|
| full 45D t-law posterior | 0.92–0.94 (0.929) | 0 | 1 |
| signed tensor (F, t, Q₀) | identical to full (algebraic identity; numerical 2.8×10⁻¹⁴) | 2.8×10⁻¹⁴ | 1 |
| Gaussian score (F, t) plug-in | 0.87–0.90 (0.889) | 4.2 | 1 (local) |
| LOO-calibrated Gaussian | 0.94–0.97 (0.954) | — | 1 |
| scalar e₁ projection | own target only | 9.8 | 0 (4 of 5 directions lost) |
| power-only \|s\|² (noncentral-χ² law) | no signed interval | 6.9 vs 0; ±s indistinguishable | 0 at s=0 |

Per-component Clopper–Pearson 95% intervals are ≈±0.03 (`R53_BENCHMARK.json`). LOO sampling sd / Fisher sd = 1.25, matching the analytic covariance-noise factor 1.27 at N=200 (Hartlap et al. 2007; Dodelson & Schneider 2013; Percival et al. 2022); 1.155 vs 1.166 at N=300 (R51).

**Table 4. Joint frame decomposition (Galactic, first order).**

| quantity | value |
|---|---|
| β_MO (observer rel. matter) | (−294, −27, 329) ± (136, 139, 125) km/s |
| frame offset β_RM(0) | (−268, 218, 53) ± (136, 139, 125) km/s |
| β_RM(0)=0 Wald: measurement cov / +250 km/s bulk variance / +CF4 calibration dipole | 5.8 / 2.8 / 1.1 (3 dof) |
| counts+CMB dipole vs CF4+CMB dipole frame consistency, χ²₃ (tail): measurement cov / +150 / +250 km/s bulk / CF4 cov ×PPC / +250 km/s and ×PPC | 16.7 (8×10⁻⁴) / 12.9 (0.005) / 9.4 (0.024) / 10.5 (0.014) / 7.3 (0.06) |
| CF4 adequacy at the joint fit | χ² 84.8 / 26.6 effective dof (low-z x-dipole windows misfit, F4) |
| Gaia E2 residual at CMB-allowed shear | χ² = 110.4 / 5 |
| likelihood rank | 14/17 (ω null; A degenerate with CF4 calibration dipole) |

## Claims by lane

| lane | claim | status | evidence |
|---|---|---|---|
| L1 low-ℓ morphology | Type-I CMB temperature response δT/T = −n·Σ·n is the first-order term of the exact Bianchi-I redshift | derived; checked | O(Σ²) remainder ratio 4 (tests/r51 `test_linear_isw_is_first_order_of_exact_bianchi_i_redshift`); transfer route agrees to 1.7×10⁻¹⁵ (R51 checks) |
| L1 | SMICA PR3 T shows no integrated shear; \|Σ\|_F < 3.74×10⁻⁵ (95%) | checked | Table 1 |
| L1 | Polarization and finite-curvature (V, VII₀, VII_h, IX) low-ℓ responses | unresolved | no source-bound transfer |
| L1 | Commander-primary result | unresolved | matched Commander MC absent |
| L2 dipole anomaly | Count dipoles (Ellis–Baldwin, measured/assumed c_EB) and CMB dipole + CF4 bulk prefer different matter frames | working law only; not robust to bulk-flow variance and CF4 misfit (p 8×10⁻⁴ → 0.06) | Table 4 |
| L2 | Count-dipole systematics budget and same-estimator velocity null | unresolved | no mocks |
| L3 PM history | Gaia E2 response to Bianchi-I shear: s = H₀K(z)σ/H₀ with K(z)=2J/χ−1 (K_eff = 4.49) | derived (conditional) | small-z limit K→1 |
| L3 | Gaia E2 residual is not cosmological shear allowed by CMB | checked | χ² 110.4/5 at σ≈0 |
| L3 | ω (vorticity) | unresolved | degenerate with Gaia frame spin |
| L4 classification | Only FLRW/I are evaluable with source-bound transfer; V/VII₀/VII_h/IX equal I only at the abelian zero-curvature boundary; II/III/IV/VI₀/VI_h/VIII and VI_h (h=−1/9) not evaluable | derived | `R53_BENCHMARK.json#bianchi_observational_equivalence` |
| L5 directional H | CF4 apparent-H dipole/STF responses (Heinesen 2021 first order) | derived; checked | `cf4_h03_design` regression |
| L5 | Matter 4-acceleration A from CF4 | unresolved | column-identical to a distance-calibration dipole |
| L6 boost vs tilt | First-order composition CMB = β_MO − β_RM, counts = c_EB β_MO, CF4 bulk = −cβ_RM | derived; checked | composition test |
| L6 | Global homogeneous tilt | not supported | Wald ≤ 2.8 with bulk-flow variance |
| methods | Signed tensor carrier ties the exact likelihood; under the finite-MC law the carrier needs Q₀ | checked | Table 3; R51 (F,t)-only error 104 |
| methods | Finite-MC law calibrates the predictive data law; parameter intervals need the known covariance-noise inflation (LOO ≈ analytic) | checked; known effect | Tables 2–3 |
| methods | Superiority of the HTT tensor over optimal score/GLS | not claimed | tie |

## Nearest prior art

- Sellentin & Heavens (2016, MNRAS 456, L132): finite-simulation covariance likelihood (used here; the PR3 held-out demonstration is an application).
- Hartlap, Simon & Schneider (2007, A&A 464, 399); Dodelson & Schneider (2013, PRD 88, 063537); Percival et al. (2022, arXiv:2108.10402): inflation of parameter errors from noisy simulation covariances (our LOO factor).
- Alsing & Wandelt (2018, arXiv:1712.00012): score compression preserves Fisher information (our tensor/score tie).
- Saadeh et al. (2016, arXiv:1604.01024; PRL arXiv:1605.07178): Bianchi CMB constraints with full transfer and polarization; stronger than the T-only type-I bound here.
- Ellis & Baldwin (1984, MNRAS 206, 377); Secrest et al. (2021, ApJL 908, L51): count-dipole kinematics and excess.
- Heinesen (2021, arXiv:2010.06534): directional Hubble parameter.
- Kalbouneh et al. (2024, arXiv:2401.12291); Maartens et al. (2024, arXiv:2312.09875): expansion-rate multipoles and boost (identifiers as listed in the R50 report; not re-verified here).
