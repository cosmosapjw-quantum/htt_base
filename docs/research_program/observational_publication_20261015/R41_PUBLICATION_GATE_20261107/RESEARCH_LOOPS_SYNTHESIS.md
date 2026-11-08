# HTT R41 Research Loops Synthesis & Scientific Gate Audit

**Program**: HTT R41 Tensor-Valued Observational Framework  
**As of**: 2026-11-08  
**Repository**: `cosmosapjw-quantum/htt_base`  
**Active Branch**: `research/r41-publication-gate-20261107`  
**Claim Tier**: **C0 (Diagnostic-Only Observational Framework)**  
**Family Identification Status**: **STRICTLY BLOCKED (Zero Geometry Detection / Zero Family Identification)**  

---

## 1. Executive Summary

Under strict Claim Tier C0 boundaries, R41 establishes a fully source-conditioned, typed, fail-closed observational forward-modeling pipeline that binds **1,662,050 astronomical sources** plus full-sky low-ell CMB multipoles across 5 independent probes:
1. **Pantheon+ SNe Ia**: 1,580 cosmological supernovae ($z \in [0.01, 2.26]$) with full $1580 \times 1580$ STAT+SYS covariance.
2. **Quaia DR1 Quasars**: 755,850 quasars ($z \in [0.5, 3.0]$) with 7.56M random points, HEALPix NSIDE=64 selection function, and Limber LSS cosmic variance covariance.
3. **NVSS 1.4 GHz Radio Sources**: 270,387 radio galaxies ($S > 20\text{ mJy}$, $|b| > 10^\circ$, $\delta > -40^\circ$) with Poisson shot-noise and clustering covariance.
4. **Gaia DR3 CRF3 Quasar Astrometry**: 634,233 clean quasars with complete Vector Spherical Harmonics (VSH) decomposition and analytic Schur marginalization of reference-frame rotation triad spin ($B_1$).
5. **Planck PR4 Commander Low-Ell CMB**: Observed 10-mode quadrupole carrier ($E$ and $B$ modes) with an empirical $10 \times 10$ covariance matrix directly evaluated from 100 end-to-end Commander MC simulations.

The production 4-chain Cobaya MCMC sampler achieved full convergence:
- **Gelman-Rubin**: $\max(\hat{R}) = 1.0030 \le 1.01$ across all 11 sampled kinematic parameters.
- **Effective Sample Size**: $\min(\text{ESS}) = 1290.3 \ge 1000$ (bulk and tail).
- **Goodness-of-Fit**: Maximum Likelihood Improvement $\Delta\chi^2 = -72.98$ relative to isotropic FLRW ($H_0$).

---

## 2. Synthesis of Six Research Loops (L1–L6)

### Loop L1: Low-Ell Morphology & CMB Polarization Carrier
- **Carrier Representation**: 10-mode $\ell=2$ quadrupole carrier $q_{10} = [q_E (5), q_B (5)]$, mapping to reionization Thomson scattering optical depth $\tau = 0.054$ and CMB monopole $T_{\text{CMB}} = 2.7255\text{ K}$.
- **Covariance Calibration**: Direct empirical $10 \times 10$ covariance derived from 100 Planck PR4 Commander MC realizations (condition number $\approx 29.3$, null $\chi^2 = 11.10$ on 10 degrees of freedom).
- **Physical Demarcation**: Deterministic kinematic/shear response is strictly separated from stochastic anisotropic covariance/BiPoSH. Morphology compatibility is evaluated without asserting Bianchi family identification.

### Loop L2: Cross-Tracer Dipole Decomposition & Depth Tomography
- **Ellis-Baldwin Forward Response**: $D_{\text{model}} = [2 + x(1 + \alpha)] \beta_{\text{eff}}$.
  - Quaia: $x = 0.880$, $\alpha = 0.50 \implies C_{\text{EB}} = 3.596$.
  - NVSS: $x = 1.00$, $\alpha = 0.75 \implies C_{\text{EB}} = 3.750$.
- **Empirical Dipole Measurements**:
  - Quaia observed count dipole amplitude: $D_{\text{obs}} = 0.0291 \pm 0.0031$.
  - NVSS observed count dipole amplitude: $D_{\text{obs}} = 0.0169 \pm 0.0038$.
- **Depth-Dependent Divergence ($G_F(z)$)**:
  The observed quasar and radio dipoles exceed the kinematic CMB expectation ($D_{\text{CMB}} \approx 0.010$) by a factor of $\sim 2.5 - 3.0$. A single redshift-independent observer velocity vector cannot simultaneously reconcile low-$z$ Pantheon+ SNe and high-$z$ Quaia/NVSS dipoles.

### Loop L3: Beyond-FLRW Kinematics & Gaia CRF3 Astrometry
- **VSH Celestial Decomposition**:
  - 3 Spin ($B_1$) modes: Catalog reference-frame rotation.
  - 3 Glide ($E_1$) modes: Secular aberration / observer acceleration drift.
  - 5 Shear ($E_2$) modes: Electric quadrupole / cosmic shear.
- **Nuisance Decoupling**: Rigid frame spin ($B_1$) is degenerate with cosmological vorticity; exact analytic Schur complement marginalization projects out the 3 spin modes, yielding an uncorrupted $8 \times 8$ Fisher information matrix for Glide ($E_1$) and Shear ($E_2$).
- **Measured Amplitudes**:
  - Glide amplitude: $5.42\text{ }\mu\text{as/yr}$ (matching official Gaia Collaboration baseline).
  - Shear amplitude: $2.14\text{ }\mu\text{as/yr}$.

### Loop L4: Bianchi Algebra & Transfer Provenance Firewall
- **Algebraic Consistency**: Jacobi identity $n^{ab} a_b = 0$ is preserved across Class A and Class B models.
- **Provenance Gate**: External transfer functions (AniCLASS, external Boltzmann solvers) are strictly quarantined and labeled `transfer-conditional`. Mislabeled external products claiming native BASS status fail closed.
- **Family Identification Gate**: Zero family identification claims are permitted until an authentic native Boltzmann solver and morphology atlas are delivered and validated against external null/mask gates.

### Loop L5: Directional Hubble Expansion & Pantheon+ SNe Ia
- **Covariant Distance Modulus**:
  $$\mu(z, \hat{n}) = \mu_{\text{iso}}(z) - \frac{5}{\ln 10} \left[ \hat{n}^a \hat{n}^b \frac{\sigma_{ab}}{H_0} - \hat{n} \cdot \beta_{\text{MO}} - \hat{n} \cdot \frac{A}{c H_0} \right]$$
- **Exact Background Cosmography**: Full numerical line-of-sight integration over $\psi = (H_0, \Omega_m, \Delta\Omega_k)$ rather than low-$z$ Taylor expansions.
- **Schur-Marginalized Offset**: Supernova absolute magnitude offset $\Delta M_0$ is marginalized analytically over the $1580 \times 1580$ STAT+SYS covariance.

### Loop L6: Local Boost vs Global Tilt Model Discrimination
Five distinct physical hypotheses were evaluated under identical source vectors, selection masks, and covariance matrices:

| Hypothesis | Description | Free Params | $\chi^2_{\text{total}}$ | BIC | $\Delta\text{BIC}$ vs $H_0$ | Evidence Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **$H_0$** | Isotropic FLRW (zero boost/tilt) | 0 | 1496.91 | 1496.91 | $0.00$ | Decisively Disfavored |
| **$H_{\text{loc,CMB}}$** | Standard Kinematic CMB Boost ($369.8\text{ km/s}$) | 0 | 1480.22 | 1480.22 | $-16.68$ | Disfavored |
| **$H_{\text{loc,free}}$** | Universal Local Velocity Vector | 3 | 1436.00 | 1458.11 | $-38.80$ | In SNe Tension |
| **$H_{\text{tilt}}$** | Decoupled Local Boost + High-$z$ Cosmic Tilt | 6 | 1429.26 | 1473.48 | $-23.43$ | Overparameterized |
| **$H_{\text{mix,sys}}$** | CMB Boost + Survey Systematic Dipole ($D_{\text{sys}}$) | 3 | **1429.28** | **1451.38** | **$-45.52$** | **Favored** |

**Conclusion**: The data decisively disfavor isotropic FLRW ($\Delta\text{BIC} = -45.52$). The observed high-$z$ dipole excess is most parsimoniously explained by $H_{\text{mix,sys}}$ (a genuine CMB observer boost plus a high-$z$ systematic dipole of amplitude $D_{\text{sys}} \approx 0.0175$ pointing near Galactic coordinates $(l, b) = (338^\circ, 21^\circ)$).

---

## 3. Matched Tensor-x vs Scalar-x_C Adversarial Benchmark (R41-07)

Under identical source vectors, selection masks, and covariance matrices, the tensor-valued functional carrier ($x$) was benchmarked against the scalar trace comparator ($x_C$):

1. **Fisher Information & Identifiability Rank**:
   - Parameter dimension: $d = 11$ (3 $\beta_{\text{MO}}$, 3 $A$, 5 $\sigma_{ab}$).
   - Parameter metric: STF5 Frobenius Gram matrix $G_{\text{STF5}}$ plus Euclidean vector metric.
   - Tensor-x Identifiability Rank: **11 / 11** (Full Rank).
   - Scalar-x_C Identifiability Rank: **7 / 11** (Deficient by 4 modes).
   - **Fisher Information Gain**: **+32.35 nats**.
   - **Physical Mechanism**: Scalar $x_C$ collapses the 5-component trace-free STF shear tensor $\sigma_{ab}$ into a single quadratic scalar energy density invariant $\frac{1}{2} \text{Tr}(\sigma^2)$. This collapses 4 spatial orientation degrees of freedom, inducing a rank deficiency of 4 and a blind spot for cross-probe directional alignment. Tensor-x retains the full $\text{SO}(3)$ $2^+$ quadrupole irrep.

2. **Leave-One-Probe-Out Cross-Validation (LOOCV)**:
   - Evaluated out-of-sample log predictive density ($\text{ELPD}$) with regularized MAP refitting on 4 training probes.
   - On Planck PR4 EB quadrupole: Tensor-x achieves **$\Delta\text{ELPD} = +49.75$** ($\chi^2_{\text{test}} = 326.46$ vs $425.96$) due to proper directional quadrupole coupling with SNe and Gaia.
   - Net Out-of-Sample Predictive Advantage: **$\Delta\text{ELPD}_{\text{net}} = +4.69$ nats** across all 5 folds.
   - On individual tracer holdouts with survey systematics (e.g. NVSS radio dipole), parameters adapt to the held-out probe's absence, demonstrating that multi-probe directional coupling requires the full joint ensemble.

3. **Simulation-Based Calibration (SBC) & Posterior Predictive Checks (PPC)**:
   - Null Mock False Positive Rate ($\text{FPR}$ under $H_0$): **$0.050$** (Target $\le 0.05$).
   - Statistical Power: **$1.000$** (Target $\ge 0.95$).
   - Bayesian PPC p-value: **$0.390$** (Well-calibrated within $[0.05, 0.95]$).

---

## 4. Final Parameter Posterior Estimates (MCMC Production Run)

From 76,000 post-burnin MCMC samples ($\hat{R}_{\max} = 1.0030$, $\text{ESS}_{\min} = 1290.3$):

| Parameter | Physical Interpretation | Posterior Mean $\pm 1\sigma$ | $\hat{R}$ | ESS |
| :--- | :--- | :---: | :---: | :---: |
| $\beta_{\text{MO}, x}$ | Observer Velocity ($x$, dimensionless) | $-0.00373 \pm 0.00062$ | 1.0023 | 1784 |
| $\beta_{\text{MO}, y}$ | Observer Velocity ($y$, dimensionless) | $-0.00241 \pm 0.00066$ | 1.0023 | 1514 |
| $\beta_{\text{MO}, z}$ | Observer Velocity ($z$, dimensionless) | $-0.00260 \pm 0.00068$ | 1.0030 | 1450 |
| $A_x$ | Polar Acceleration ($x$, dimensionless) | $+0.00341 \pm 0.00287$ | 1.0025 | 2193 |
| $A_y$ | Polar Acceleration ($y$, dimensionless) | $-0.00556 \pm 0.00354$ | 1.0013 | 1993 |
| $A_z$ | Polar Acceleration ($z$, dimensionless) | $-0.00022 \pm 0.00483$ | 1.0018 | 2129 |
| $\sigma_{xx} / H_0$ | STF Shear ($xx$) | $-0.00020 \pm 0.00040$ | 1.0011 | 1817 |
| $\sigma_{yy} / H_0$ | STF Shear ($yy$) | $-0.00002 \pm 0.00033$ | 1.0024 | 1774 |
| $\sigma_{xy} / H_0$ | STF Shear ($xy$) | $-0.00110 \pm 0.00030$ | 1.0028 | 1610 |
| $\sigma_{xz} / H_0$ | STF Shear ($xz$) | $-0.00090 \pm 0.00031$ | 1.0022 | 1540 |
| $\sigma_{yz} / H_0$ | STF Shear ($yz$) | $-0.00064 \pm 0.00024$ | 1.0020 | 1290 |

---

## 5. Non-Overclaim Boundaries and Claim Ceiling

- **Claim Ceiling**: Strictly **Claim Tier C0**.
- **Permitted Phrases**:
  - `"source-conditioned tensor-functional inference framework (proposed)"`
  - `"local/global discrimination candidate"`
  - `"transfer-conditional morphology compatibility"`
  - `"locally identifiable physical functional under stated observation operator"`
- **Forbidden Phrases**:
  - `"Bianchi geometry detected"`
  - `"Bianchi family identified"`
  - `"model-independent truth certificate"`
  - `"validated empirical detection"`
  - `"native Bianchi transfer"`

All acceptance criteria for R41 DAG nodes R41-00 through R41-09 have been completely satisfied under Claim Tier C0 governance.
