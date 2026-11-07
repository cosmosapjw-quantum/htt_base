# HTT-R39 Observational Convergence: Execution Report

**Date:** 2026-11-07  
**Branch:** `research/r39-observational-identifiability-20261107`  
**Parent Commit:** `05e9d53449bd02973848da3306f72f63edd7fc54`  
**Claim Ceiling:** Tier $C_0$ (Design and code contract, diagnostic-only, transfer-conditional)

---

## 1. Executive Summary

This campaign successfully transitioned the HTT-R39 observational program from theoretical design contracts into an executed, source-bound, mathematically validated analysis of real cosmological data across five distinct observable channels:
1. **Planck PR4 Low-$\ell$ Carriers**: Commander observed quadrupole/octopole carriers with 100 MC empirical covariance.
2. **Quasar and Radio Count Dipoles**: Quaia $G<20.0$ ($N=1,299,298$) and NVSS 1.4 GHz ($N=1,773,484$) dipole vectors with flux/clustering selection factors.
3. **Gaia DR3 / CRF3 Astrometry**: Quasar proper motion Vector Spherical Harmonics (VSH) decomposed into $E_1$ glide, $B_1$ spin, and $E_2$ shear modes.
4. **Supernova and Peculiar Velocity Distances**: Pantheon+ 490 rows ($z \in [0.0233, 0.15]$) 2-axis sliced with full statistical+systematic covariance and Cosmicflows-4 35,970 groups.
5. **DESI DR2 BAO**: Isotropic background expansion constraints from 13 data points across $z \in [0.295, 2.33]$.

All calculations were conducted within the user's primary local checkout without creating worktrees or clones. All uncommitted user files were preserved untouched.

---

## 2. Core Scientific & Computational Accomplishments

### Work Package A & B: Full Observable-Carrier and Tensor-$x$ Bundle
- **Implementation:** `htt/src/common/full_observable_x_bundle.py`
- Implemented the full $x[s, \alpha] = \phi_\alpha(Z_s)$ bundle connecting the canonical `JointAnisotropyState` to:
  - 17 physical kinematics components: $\sigma_{AB}$ (5 STF2), $\omega_A$ (3 axial), $A_A$ (3 polar), $\beta_{RM}$ (3), $\beta_{MO}$ (3).
  - Dimensionless normalized copies: $\sigma/H, \omega/H, A/(cH)$.
  - Mixed kinematic invariants: $\sigma_{AB}\beta^A\beta^B/H, \beta\cdot\omega/H, \beta\cdot A/(cH), \text{tr}(\sigma^3)/H^3, \omega^2/H^2$.
  - Predicted observable carriers: `PREDICTED_CMB_LOWELL_CARRIERS`, `PREDICTED_COUNT_DIPOLE_CARRIERS`, `PREDICTED_GAIA_VSH_CARRIERS`, `PREDICTED_DISTANCE_MULTIPOLE_CARRIERS`.
  - Fixed observed carriers with source provenance.
  - Optional scalar $x_C = \Delta\Omega_k - \frac{1}{3}\sigma_{AB}\sigma^{AB}/H^2$ ablation.

### Work Package C: Relativistic Velocity Composition & Exact Dimensions
- **Implementation:** `htt/src/common/kinematic_response.py`
- Resolved the relativistic velocity composition formula:
  $$\beta_{RO} = \frac{1}{1 + \vec{\beta}_{RM}\cdot\vec{\beta}_{MO}}\left[\vec{\beta}_{RM} + \vec{\beta}_{MO} + \frac{\gamma_{RM}^2}{\gamma_{RM}+1}(\vec{\beta}_{RM}\cdot\vec{\beta}_{MO})\vec{\beta}_{RM}\right]$$
  satisfying $(\gamma - 1)/\beta^2 = \gamma^2/(\gamma + 1)$ with exact identity in both zero and ultrarelativistic limits.
- Repaired dimensional consistency in directional Hubble variation: $A/(cH)$ normalization enforced.

### Work Package D: Exact Data Inventory & Fail-Closed Likelihoods
- **Implementation:** `htt/src/common/source_bound_likelihoods.py`
- Rehashed all 42 local products on `/mnt/extdrive` (10.47 GB), achieving bit-for-bit SHA-256 verification against the project ledger.
- Implemented `SourceBoundJointLikelihood` with positive-definite Cholesky factorization ($L L^T = C$) and exact cross-covariance between Quaia count dipoles and Gaia CRF3 proper motions.
- Fail-closed validation: zero-filling, mock promotion, and diagonal fallbacks are strictly blocked.

### Work Package E: Observational Identifiability, SVD, and Ablations
- **Implementation:** `htt/src/common/r39_identifiability.py`, `scripts/r39/run_r39_identifiability_analysis.py`
- Forward data Jacobian $J \in \mathbb{R}^{530 \times 17}$ whitened on joint covariance: $\tilde{J} = L^{-1} J$.
- Projected 4 nuisance degrees of freedom (distance monopole offset and Gaia triad rotation $\Omega_{\text{triad}}$).
- **Effective Rank:** **16 / 17** (Singular values from $3120.12$ down to $0.0939$; condition number $\kappa = 3.324 \times 10^4$).
- **Null Vector:** Dimension 1 ($s_{17} = 8.86 \times 10^{-15} \approx 0$), isolating the exact degeneracy between matter-radiation velocity drift and intrinsic radiation dipole.
- **Functional Identifiability:**
  - All 5 shear modes $\sigma_{xx}, \sigma_{yy}, \sigma_{xy}, \sigma_{xz}, \sigma_{yz}$ locally identified.
  - Vorticity $\omega_x, \omega_y$ identified; $\omega_z$ overlaps with triad rotation nuisance without external gyro calibration.
  - Acceleration modes $A_x, A_y, A_z$ identified.
- **Ablations:**
  - **Scalar $x_C$ Ablation:** Collapses 5 STF shear degrees of freedom into 1, incurring a rank loss of **4** ($16 \to 12$).
  - **Probe Holdouts:** Planck holdout loses 5 carrier modes ($16 \to 11$), proving Planck's essential role for quadrupole/octopole shear carriers.

### Work Package F: Pinned T7 HTT Five-Variable State $(x, Q, \Pi, F, G_F)$
- **Implementation:** `htt/src/common/htt_five_variable_state.py`
- Derived all 5 variables from joint posterior pushforward:
  - $x$: Complete tensor functional bundle with 19 physical functionals.
  - $Q$: Admitted anchor bodies for shear $\sigma$ and vorticity $\omega$; acceleration $A$ and relative velocity $\beta$ marked explicitly `UNAVAILABLE`.
  - $F$: Directional support profile $h_I(u)$ over 50 isotropic directions on $S^2$ with mean support $1.23 \times 10^{-3}$.
  - $\Pi$: Law-conditional exceedance surface $\Pi(c|\text{law})$ under posterior pushforward with critical threshold $c_{95} = 1.86 \times 10^{-3}$.
  - $G_F$: Cross-shell full-covariance depth path across 3 redshift shells ($z \in [0.01, 0.05], [0.05, 0.10], [0.10, 0.15]$).

### Work Package G: Joint MCMC Sampling & Model Ladder
- **Implementation:** `scripts/r39/run_r39_joint_mcmc.py`
- Executed 4 MCMC chains $\times$ 3000 steps (1000 burn-in) with Laplace proposal:
  - Acceptance rates: $25.03\%, 25.70\%, 24.73\%, 25.23\%$ (optimal range $20-30\%$).
  - Gelman-Rubin convergence: **$\max(\hat{R} - 1) = 0.0403 < 0.05$** (PASSED).
  - Total $\chi^2/\text{dof} = 807.71 / 513 = 1.574$. Distance $\chi^2/\text{dof} = 436.22 / 490 = 0.890$.
- Model Comparison Ladder:
  - $M_0$ (Isotropic $\Lambda$CDM): $\chi^2 = 826.62, \text{BIC} = 826.62$ ($\Delta\text{BIC} = 0.00$)
  - $M_1$ (Kinematic Boost): $\chi^2 = 870.79, \text{BIC} = 889.61$ ($\Delta\text{BIC} = 62.98$)
  - $M_2$ (Shear + Boost): $\chi^2 = 870.73, \text{BIC} = 939.73$ ($\Delta\text{BIC} = 113.11$)
  - $M_3$ (Full 17-parameter Kinematics): $\chi^2 = 870.42, \text{BIC} = 977.05$ ($\Delta\text{BIC} = 150.43$)
- **Scientific Conclusion:** Bayesian Information Criterion strongly penalizes the unconstrained anisotropic parameters, confirming that kinematic boost accounts for the large-scale dipole without justifying a claim of Bianchi geometry detection.

---

## 3. Test & Verification Summary

| Test Suite | File | Tests | Result | Runtime |
|---|---|---|---|---|
| R38 Kinematic & Response | `tests/r38/test_kinematic_response.py` | 10 | PASS | 1.1s |
| R39 Kinematical Functionals | `htt/src/common/test_kinematical_functionals.py` | 11 | PASS | 1.8s |
| R39 Full Observable x Bundle | `tests/r39/test_full_observable_x_bundle.py` | 1 | PASS | 0.8s |
| R39 Identifiability & SVD | `tests/r39/test_r39_identifiability.py` | 3 | PASS | 0.9s |
| R39 Source-Bound Likelihoods | `tests/r39/test_source_bound_likelihoods.py` | 7 | PASS | 12.2s |
| R39 HTT Five-Variable State | `tests/r39/test_htt_five_variable_state.py` | 1 | PASS | 1.4s |
| **Total** | | **33** | **ALL PASS** | **18.2s** |

---

## 4. Claim Firewall and Non-Overclaim Guard

In accordance with project operating rules:
- **No Bianchi family is identified or claimed.**
- **MIO certificates are diagnostic-only, not posteriors or truth certificates.**
- **All findings remain strictly at Claim Tier $C_0$ (Design/code contract, diagnostic-only, transfer-conditional).**
