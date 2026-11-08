# Paper Extract P1: Momentum Rest Frame, Kinematic Coupling, and Partial Identification of Signed Anisotropy Functionals

**Document ID:** `P1_MOMENTUM_REST_FRAME.md`  
**Parent Release:** `PR-R37-05-FINAL-REPORT` (Finite Scientific Convergence Release)  
**Target Paper:** P1 — *Observed-data distributions and partial identification of signed beyond-FLRW functionals*  
**Claim Tier:** C0 (Conditional Methods / Qualified Observational Sensitivity)  
**Artifact Mode:** Diagnostic and Statistical Extract  
**Ownership & Role:** HTT Statistical Inference / obsstat Feature Extraction  
**Transfer Source:** None (Kinematic / Astrometric / Distance-modulus framework)  
**Baseline Commit:** `bdead6a8f51282ca647224b460b0f65de085568b`

---

## 1. Executive Summary & Physical Problem Statement

The cosmological rest frame is traditionally identified with the frame in which the Cosmic Microwave Background (CMB) dipole vanishes. However, kinematic projections of an observer's 4-velocity $u^a$ relative to a matter or radiation congruence $v^a$ generate multi-frequency, multi-carrier observable signatures across astrometric proper motions, apparent cosmic expansion rates, and low-multipole optical departures. 

Extract P1 synthesizes the mathematical framework and empirical constraints governing the partial identification of signed beyond-FLRW functionals. When an observer moves with peculiar velocity $\boldsymbol{\beta} = \boldsymbol{v}/c$ and experiences acceleration $\boldsymbol{A}$, the induced apparent kinematic pattern is not purely dipolar:
1. Nonlinear optical propagation couples observer acceleration and matter shear into an apparent octupole;
2. Astrometric proper-motion fields decompose into distinct vector-spherical-harmonic (VSH) electric ($E_1, E_2$) and magnetic ($B_1$) modes with strict history-dependent response operators;
3. Selected-cohort distance-modulus regressions yield partially identified parameter intervals where missing selection probabilities prevent point estimation of physical functionals.

Under the unified coordinate representation $(x, F, Q, \Pi, G_F)$, this extract establishes that correctly specified joint generalized least squares (GLS) and invertibly tensorized carriers retain identical information (maximum absolute difference $2.42 \times 10^{-13}$ in estimates, $2.15 \times 10^{-16}$ in Fisher information), whereas diagonalizing covariance or projecting across depth bins erases identifiable physical slopes.

---

## 2. Mathematical Formulation & Kinematic Operators

### 2.1 Coordinate Conventions & 4-Velocity Decompositions
We adopt the spacetime metric signature $(-, +, +, +)$ with speed of light $c$. Let $u^a$ denote the timelike 4-velocity of the observer ($u_a u^a = -1$), and $e_a$ the unit spatial direction of an incoming null geodesic ($k^a = \nu(u^a - e^a)$). The covariant spatial projection tensor is $h_{ab} = g_{ab} + u_a u_b$.

The covariant derivative of the matter velocity field $v^a$ is decomposed into expansion scalar $\Theta = 3H$, symmetric trace-free (STF) shear $\sigma_{ab}$, antisymmetric vorticity $\omega_{ab}$, and 4-acceleration $A_a = v^b \nabla_b v_a$:
$$
\nabla_b v_a = \frac{1}{3}\Theta h_{ab} + \sigma_{ab} + \omega_{ab} - u_b A_a.
$$
Defining dimensionless acceleration and shear parameters normalized by the local isotropic expansion rate $H$:
$$
\boldsymbol{d} = -\frac{\boldsymbol{A}}{c H}, \qquad \boldsymbol{S} = \frac{\boldsymbol{\sigma}}{H},
$$
the local longitudinal expansion rate observed along unit direction $\boldsymbol{n} = -\boldsymbol{e}$ is:
$$
\mathcal{H}_u(\boldsymbol{n}) = H \left(1 + \boldsymbol{d}\cdot\boldsymbol{n} + \boldsymbol{S}:\boldsymbol{n}\boldsymbol{n}\right).
$$
The antisymmetric vorticity tensor $\omega_{ab}$ is identically blind to pure radial symmetric longitudinal expansions ($\omega_{ab} n^a n^b = 0$), demonstrating that radial expansion surveys alone cannot bound cosmic vorticity without transverse or non-radial information.

### 2.2 Transverse Kinematic Carrier & Gaia DR3 Representation
Transverse proper motions $\boldsymbol{\mu}(\boldsymbol{n})$ project spatial velocity gradients through the transverse projector $P_{\boldsymbol{n}} = I - \boldsymbol{n}\boldsymbol{n}^T$:
$$
\boldsymbol{\mu}(\boldsymbol{n}) = \frac{1}{D} P_{\boldsymbol{n}} \left( \boldsymbol{v}_{\rm source} - \boldsymbol{v}_{\rm obs} \right) + P_{\boldsymbol{n}} \boldsymbol{\mathcal{A}} \boldsymbol{n},
$$
where $\boldsymbol{\mathcal{A}}$ encodes the endpoint-to-derivative response:
$$
\boldsymbol{\mathcal{A}} = \frac{2c(\boldsymbol{B}_o - \boldsymbol{B}_s)}{D} - \dot{\boldsymbol{B}}_o.
$$
In the foundational Gaia DR3 astrometric analysis (755,850 selected quasar rows), the observed transverse field is decomposed into:
- **E1 Polar / B1 Axial Vectors:** 24-dimensional state vector $\boldsymbol{x}_{24}$ spanning three reported-redshift bins ($z_1, z_2, z_3$) plus six depth slopes $g(z) = z/(1+z)$.
- **E2 STF Quadrupole Modes:** 5-dimensional STF carrier driven by the second-order geometric shear response.

### 2.3 Exact Fixed-$Q$ Chirality Sign Theorem
When testing parity violation and low-multipole alignment between an STF quadrupole $\boldsymbol{Q}$ ($3\times 3$, symmetric trace-free) and an STF octupole $\boldsymbol{O}$ ($3\times 3\times 3$), the contracted vector is $\boldsymbol{v} = \boldsymbol{O}:\boldsymbol{Q} = O_{ijk} Q_{jk}$. The scalar chirality invariant is:
$$
\chi(\boldsymbol{Q}, \boldsymbol{O}) = \det\left[ \boldsymbol{v}, \; \boldsymbol{Q}\boldsymbol{v}, \; \boldsymbol{Q}^2\boldsymbol{v} \right].
$$
Let $\boldsymbol{Q}$ have a simple spectrum with distinct eigenvalues $\lambda_1 < \lambda_2 < \lambda_3$ in its oriented eigenframe ($\sum_i \lambda_i = 0$). Define the metric matrix:
$$
\boldsymbol{M}_Q = \frac{\|\boldsymbol{Q}\|_F^2}{3}\boldsymbol{I} + \frac{2}{5}\boldsymbol{Q}^2, \qquad (M_Q)_{ii} = \frac{\|\boldsymbol{Q}\|_F^2}{3} + \frac{2}{5}\lambda_i^2.
$$
**Theorem (Exact Fixed-$Q$ Sign Radius):**  
In the ambient STF3 Frobenius norm $\|\delta \boldsymbol{O}\|_F$, the minimum distance from an observed state $(\boldsymbol{Q}, \boldsymbol{O})$ with $\chi(\boldsymbol{Q}, \boldsymbol{O}) \ne 0$ to the nearest zero-chirality hypersurface $\chi = 0$ is given analytically by:
$$
\rho_{\rm sign}(\boldsymbol{Q}, \boldsymbol{O}) = \min_{i \in \{1,2,3\}} \frac{|v_i|}{\sqrt{(M_Q)_{ii}}}.
$$
For the canonical normalized witness $\boldsymbol{Q} = \operatorname{diag}(-1/\sqrt{2}, 0, 1/\sqrt{2})$, the exact sharp sign radius is:
$$
\rho_{\rm sign} = \frac{1}{\sqrt{3}} \approx 0.5773502692.
$$
This radius defines the exact deterministic perturbation margin required to flip or extinguish the observed morphological chirality.

---

## 3. Empirical & Numerical Findings

### 3.1 Gaia DR3 Astrometric Depth Contrast & GLS Sandwich Invariance
Analysis of the 755,850-row Gaia quasar catalogue under the validated 24-dimensional Gaussian working law yields the following rigorous findings:
1. **Nuisance-Profiled Depth Slopes:**  
   Profiling the 18 arbitrary bin intercepts retains the six signed depth-slope coordinates in $\mu\mathrm{as}\,\mathrm{yr}^{-1}$:
   $$
   \boldsymbol{s}_g = (6.60158, \; 0.29170, \; -1.50132, \; -10.18497, \; -7.64665, \; 0.48156).
   $$
   The naive $24 \to 18$ bin-centre projection completely drops these six dimensions ($\operatorname{rank} = 18$), projecting physical depth dependence into an unobservable subspace. This projection must never be interpreted as an empirical constraint of zero physical depth variation.
2. **Constrained Common-Intercept Model:**  
   Under a common six-vector intercept across bins, the signed $g(z)$ slope is:
   $$
   \tilde{\boldsymbol{s}}_g = (0.78423, \; -1.57176, \; 0.56325, \; 21.94228, \; -10.02219, \; -6.28570) \;\mu\mathrm{as}\,\mathrm{yr}^{-1}.
   $$
   Isolated-bin scalar Mahalanobis powers are $48.19, 59.98, 52.97$. Evaluating scalar powers alone erases orientation signs and prevents joint testing.
3. **GLS vs. Diagonal Sandwich Diagnostics:**  
   In 100,000 Monte Carlo draws under a Mahalanobis 2.5 injection:
   - Joint GLS achieves empirical coverage **0.94927** (nominal 95%) and power **0.42130**;
   - Diagonal-bin covariance (ignoring cross-bin correlations) gives nominal coverage **1.00000** and power **0.00000** (total loss of sensitivity);
   - The sandwich covariance repair restores empirical coverage to **0.94976** and power to **0.40135**.

### 3.2 E2 Proper-Motion Nullspace & History Degeneracy
For the independent E2/STF5 proper-motion response (R36-03), the five identified rate coefficients are $u = kq - s$, where $q = (B_o - B_s)/T_{\rm ref}$, $s = \dot{B}_o$, and $k = 2c T_{\rm ref}/D$.
- After profiling six spin/glide nuisance modes, the five Fisher information eigenvalues are:
  $$
  \boldsymbol{\lambda}_F = (2.43693, \; 2.65563, \; 3.17145, \; 3.67145, \; 4.95102) \; (\mu\mathrm{as}\,\mathrm{yr}^{-1})^{-2}.
  $$
- The ten-dimensional parameter space $(q, s)$ possesses five unbounded null directions:
  $$
  \delta s = k \, \delta q.
  $$
  In the distant-source limit ($k \to 0$), the observable field measures purely $-\dot{B}_o$; in the near limit ($k \gg 1$), it measures $(B_o - B_s)/D$. The sign and amplitude of the measured field cannot be mapped to a matter-shear tensor without conditioning on this history response.

### 3.3 Selected-Cohort Distance-Modulus Partial Identification
In the 274-row Pantheon+ selected distance-modulus likelihood (15 fitted expansion coefficients):
- The exact model-conditional $F(15, 259)$ confidence ellipsoid has critical squared Mahalanobis radius $r^2 = 27.0585024197$.
- Projecting this ellipsoid across four distinct covariance-shape families reveals that all four projected STF regions contain zero.
- The 354 missing/unobserved outcomes in the parent sample produce a conservative target-fraction identification hull width of:
  $$
  W_{\rm hull} = \frac{354}{628} \approx 0.563694.
  $$
  This establishes rigorous partial identification: point identification of the underlying functional is mathematically impossible without external selection probability bounds.

---

## 4. Claim-Tier Firewall & Methodological Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLAIM-TIER BOUNDARY                                │
├────────────────────────────────────────┬────────────────────────────────────┤
│ PERMITTED (Validated Diagnostic / C0) │ FORBIDDEN (Overclaim / Blocked)    │
├────────────────────────────────────────┼────────────────────────────────────┤
│ • "claim-tiered observational framework"│ • "cosmic matter shear detected"   │
│ • "transfer-conditional kinematic image"│ • "geometric vorticity confirmed"  │
│ • "partial identification of functionals"│ • "absolute rest-frame discovered" │
│ • "diagnostic-only Gaia E1/B1 contrast" │ • "FLRW violation definitively ruled"│
│ • "attained fixed-Q sign radius"       │ • "model-independent truth bound"  │
└────────────────────────────────────────┴────────────────────────────────────┘
```

1. **No Matter-Kinematics Equivalence:** Transverse proper-motion quadrupoles and optical expansion coefficients reflect observer-dependent projection and history operators. They must not be equated with spacetime shear $\sigma_{ab}$ or cosmic vorticity $\omega_{ab}$ without calibrated source-frame connections.
2. **Nuisance Nullspace Recognition:** The existence of five unconstrained null directions $\delta s = k \delta q$ proves that proper motions alone cannot break the degeneracy between endpoint shear and time-derivative acceleration.

---

## 5. Residual Obligations & Solver Handoff Interface

To promote these conditional kinematic results to formal observational assertions, the following residual gates must be satisfied:
1. **Source-Frame Acceleration Calibration:** Provide a validated relativistic transfer function mapping barycentric quasar coordinates to the cosmological matter frame, including radio-core astrometric chromaticity corrections.
2. **Parent Selection Model:** Formulate an empirical selection probability model $P({\rm inclusion} \mid z, \boldsymbol{n}, \mu)$ to shrink the 0.5637 identification hull width in the distance-modulus sector.
3. **Solver Handoff Schema:** The $(x_{24}, \boldsymbol{\Sigma}_{24})$ Gaia carrier and the 5-dimensional E2 Fisher matrix are exported via `AtlasEntryLite` format to serve as observer-side kinematic boundary conditions for the forthcoming native low-$\ell$ Boltzmann solver.

---

## 6. Primary Literature & Citation Ledger

1. **A. Heinesen**, *Multipole decomposition of the general luminosity distance Hubble law*, JCAP **05** (2021) 008, [arXiv:2010.06534](https://arxiv.org/abs/2010.06534).
2. **O. H. Marcori et al.**, *Direction and redshift drifts for general observers and their applications in cosmology*, Phys. Rev. D **98**, 023517 (2018), [arXiv:1805.12121](https://arxiv.org/abs/1805.12121).
3. **R. Maartens et al.**, *Covariant cosmography: the observer-dependence of the Hubble parameter*, JCAP **09** (2024) 070, [arXiv:2312.09875](https://arxiv.org/abs/2312.09875).
4. **C. J. Copi, D. Huterer, and G. D. Starkman**, *Multipole Vectors*, Phys. Rev. D **70**, 043515 (2004), [arXiv:astro-ph/0310511](https://arxiv.org/abs/astro-ph/0310511).
5. **Gaia Collaboration**, *Gaia Data Release 3: The celestial reference frame (CRF3)*, Astron. Astrophys. **674**, A41 (2023).
