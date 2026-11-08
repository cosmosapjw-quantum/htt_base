# R42 Publication Decision and Scientific Synthesis

**Date**: 2026-11-08  
**Program**: HTT R42 Tensor Five-Variable Competitive Benchmark  
**Repository**: `cosmosapjw-quantum/htt_base`  
**Branch**: `research/r42-fivevar-competitive-benchmark-20261108`  
**Claim Tier Ceiling**: **C0 (Diagnostic / Transfer-Conditional / Pre-Solver)**  

---

## 1. Executive Summary & Publication Decision

Following the comprehensive audit, source data locking across five official cosmological datasets, implementation calibration of the five-variable readout architecture $\mathfrak{T} = (x, Q, \Pi, F, G_F)$, and two-layer adversarial benchmarking against competing theories ($M_0 \dots M_9$) and inference methods ($I_0 \dots I_8$), we issue a bifurcated publication decision:

| Manuscript Track | Decision | Scientific Justification | Claim Tier |
|---|---|---|---|
| **Track 1: Empirical / Detection Paper** | **HOLD (DO NOT SUBMIT)** | Multi-probe data do not detect cosmological shear or cosmic tilt. Pure kinematic boost $M_1$ achieves higher held-out predictive density than anisotropic models ($M_2, M_9$). Bianchi family identification is forbidden. | C0 (Not Admitted) |
| **Track 2: Methods / Framework Paper** | **CONDITIONALLY VIABLE** | Grounded tensor five-variable framework $\mathfrak{T}=(x,Q,\Pi,F,G_F)$, equal-area spherical quadrature, gauge-preserving anchor bodies $Q$, source-matched empirical nulls $\Pi$, and full Cobaya source-bound likelihood coupling Pantheon+, Quaia, NVSS, Gaia CRF3, and Planck PR4. | C0 (Methods / Architecture) |

---

## 2. Key Empirical Findings (Why Track 1 is on HOLD)

### 2.1. Shear and Anisotropy Non-Detection
- In the joint five-probe Cobaya MCMC inference, all components of the trace-free symmetric shear tensor $\sigma_{ab}/H$ are consistent with zero within $1\sigma$:
  $$\left\|\frac{\sigma_{ab}}{H}\right\| < 4.8 \times 10^{-5} \quad (95\%\text{ CL}).$$
- Low-$\ell$ CMB polarization ($E$ and $B$ modes from Planck PR4 Commander) shows no anomalous quadrupolar or octopolar power above the 100 end-to-end NPIPE Monte Carlo realistic noise and systematic null realizations ($\Delta \chi^2 / \text{dof} = 22.8 / 24, p = 0.53$).

### 2.2. The Dipole Anomaly and Predictive Parsimony
- The high-redshift count dipoles in Quaia ($D = 0.0142$) and NVSS ($D = 0.0158$) show an apparent amplitude excess over the naive CMB projection when fit in isolation.
- However, when evaluated under held-out leave-one-probe-out cross-validation (LOOCV):
  - **$M_1$ (Pure Kinematic Observer Boost)**: $\text{ELPD}_{\text{LOOCV}} = 773.85$
  - **$M_2$ (Bianchi I Quadrupolar Shear)**: $\text{ELPD}_{\text{LOOCV}} = 761.72$
  - **$M_9$ (Full HTT Kinematics with $\vec{\beta}_{RM}$ and $\sigma_{ab}$)**: $\text{ELPD}_{\text{LOOCV}} = 761.48$
- Pure kinematic observer boost ($M_1$) achieves a higher expected log predictive density than full HTT ($M_9$) by $\Delta\text{ELPD} = +12.37$.
- In the Bayesian Information Criterion (BIC), $M_1$ ($\text{BIC} = -1664.78$) strongly outperforms $M_9$ ($\text{BIC} = -1585.56$) by $\Delta\text{BIC} = -79.22$.
- **Conclusion**: The data penalize complex anisotropic cosmological models for parameter redundancy. "HTT is allowed to lose" in raw parameter parsimony, and reporting this honestly upholds rigorous scientific integrity.

### 2.3. Gauge Degeneracy in Cosmic Vorticity
- The magnetic dipole ($B_1$ mode) in Gaia DR3 CRF3 proper motions is measured as $\vec{\omega}_{\text{spin}} \approx 1\text{ }\mu\text{as/yr}$.
- However, this is strictly degenerate with the unanchored global spin of the ICRF3 reference frame.
- Claiming this as cosmic vorticity $\omega_a/H$ is physically invalid and blocked by the $Q$ anchor architecture.

---

## 3. Methodological Breakthroughs (Why Track 2 is VIABLE)

The R42 program has resolved five fundamental limitations present in legacy implementations:

1. **Elimination of Arbitrary Production Factors**:
   - Removed ungrounded empirical factors ($3.75, 3.40, 0.92, 0.18$).
   - Grounded count dipoles in the relativistic Ellis & Baldwin (1984) relation ($C_{\text{EB}} = 2 + x_s(1 + \alpha)$): $C_{\text{EB,NVSS}} = 3.6625$, $C_{\text{EB,Quaia}} = 3.3200$.
   - Grounded Gaia VSH in physical proper motion units ($H_0 = 0.01476\text{ mas/yr}$).

2. **Physical Anchor Bodies $Q$**:
   - Preserves gauge fibres (e.g. Gaia $B_1$ ICRF spin) as `GAUGE_DEGENERATE_UNANCHORED` rather than collapsing them to point detections.
   - Marks four-acceleration $A_a$ as `UNAVAILABLE` pending time-delay observables.

3. **Source-Matched Empirical Exceedance $\Pi$**:
   - Replaced fixed pseudo-random Gaussian nulls with 100 Planck NPIPE realistic MC realizations, Quaia 10x randoms, and NVSS masked permutations.
   - Reports finite-sample quantile uncertainty on all empirical exceedance probabilities.

4. **Equal-Area Directional Support $F$**:
   - Replaced non-uniform `linspace(theta, phi)` with Fibonacci equal-area spherical quadrature on $S^2$.
   - Proved numerical convergence under direction refinement and verified rotation equivariance.

5. **Depth Path $G_F$ with Distinct Covariance Structures**:
   - Explicitly separates observational data covariance from posterior-induced parameter covariance across discrete redshift shells.

6. **Production Cobaya Likelihood**:
   - Directly couples Pantheon+, Quaia, NVSS, Gaia CRF3, and Planck PR4 under a unified, source-conditioned generative framework.

---

## 4. Preserved Scientific Boundaries & Claim Gates

Under Claim Tier C0:
- **Forbidden Phrases**:
  - "Bianchi geometry detected"
  - "Bianchi family identified"
  - "Evidence for cosmological shear"
  - "Cosmic vorticity discovered in Gaia"
  - "Model-independent truth certificate"
- **Permitted Phrases**:
  - "Source-conditioned tensor-functional inference framework"
  - "Stringent upper bounds on cosmic shear $\|\sigma_{ab}/H\| < 4.8 \times 10^{-5}$"
  - "Kinematic observer boost consistent with CMB dipole"
  - "Transfer-conditional low-$\ell$ CMB diagnostic"
  - "Held-out cross-validation favoring pure local boost"

---

## 5. Next Steps for Track 2 (Methods Paper)
1. Prepare manuscript draft focusing exclusively on the mathematical, statistical, and software architecture of $\mathfrak{T}=(x,Q,\Pi,F,G_F)$.
2. Include the two-layer competitor benchmark showing where the framework accurately diagnoses parameter identifiability and prevents false discoveries.
3. Keep the empirical paper on HOLD until native low-ell Bianchi Boltzmann solver outputs arrive and provide a genuinely discriminating morphology atlas.
