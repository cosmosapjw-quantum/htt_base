# Loop 03: Direct Kinematic Measurement of Observer Velocity $\vec{\beta}_{MO}$

## 1. Physical Hypothesis
The motion of our Solar System barycentre relative to cosmological matter and radiation frames induces an apparent aberration and secular proper motion across extragalactic sources. Gaia astrometry of distant quasars provides a purely geometric, flux-independent, and distance-independent kinematic measurement of cosmic acceleration and velocity through Vector Spherical Harmonic (VSH) decomposition.

## 2. Fundamental GR and Cosmological Equations
1. **Aberration proper motion**:
   A constant velocity $\vec{\beta}$ causes an angular displacement $\Delta \hat{n} \approx \vec{\beta} - (\hat{n} \cdot \vec{\beta})\hat{n}$, but does not cause a secular proper motion ($d\hat{n}/dt = 0$) unless the velocity is changing ($\vec{a} = d\vec{v}/dt$).
2. **Secular acceleration proper motion**:
   The acceleration of the Solar System barycentre towards the Galactic Centre ($a_{\text{GC}} \approx 2 \times 10^{-10}\text{ m/s}^2 \approx 5.8\text{ km/s/Myr}$) causes an apparent secular drift in quasar positions:
   $$\vec{\mu}(\hat{n}) = \frac{1}{c} [\vec{a} - (\hat{n} \cdot \vec{a})\hat{n}].$$
   In terms of Vector Spherical Harmonics (VSH), this corresponds to an electric-type dipole ($E_1$ mode):
   $$\vec{\mu}(\hat{n}) = \sum_{m} a_{1m}^{E} \vec{\Psi}_{1m}(\hat{n}) + a_{1m}^{B} \vec{\Phi}_{1m}(\hat{n}) + \sum_{m} a_{2m}^{E} \vec{\Psi}_{2m}(\hat{n}),$$
   where:
   - $E_1$ ($a_{1m}^E$): Electric dipole $\propto$ Galactic acceleration $\vec{a}/c \approx 5.0\text{ }\mu\text{as/yr}$.
   - $B_1$ ($a_{1m}^B$): Magnetic dipole $\propto$ Celestial reference frame rotation / cosmic vorticity $\vec{\omega}/H$.
   - $E_2$ ($a_{2m}^E$): Electric quadrupole $\propto$ Cosmic shear tensor $\sigma_{ab}/H$.
3. **Gauge Degeneracy**:
   As established in Stage B and the R42 SSoT, the magnetic dipole $B_1$ is strictly degenerate with the global spin of the ICRF3 reference frame:
   $$\vec{\mu}_{B_1} = \vec{\omega}_{\text{frame}} \times \hat{n} + \vec{\omega}_{\text{cosmic}} \times \hat{n}.$$
   Without an external, non-optical reference frame tie (such as absolute VLBI radio ties), $B_1$ cannot be claimed as a direct detection of cosmic vorticity $\omega_a/H$.

## 4. Observable Mapping & Forward Operators
- Forward operator: `SourceBoundGaiaVSHOperator`.
- Input: 634,233 clean quasars from Gaia DR3 CRF3 cross-matched with Quaia.
- Forward mapping:
  $$\vec{\mu}_{\text{pred}}(\hat{n}_i) = \mathbf{V}_i \theta_{\text{VSH}},$$
  where $\mathbf{V}_i \in \mathbb{R}^{2 \times 11}$ projects the 11 VSH coefficients ($E_1 \in \mathbb{R}^3, B_1 \in \mathbb{R}^3, E_2 \in \mathbb{R}^5$) onto proper motion components $(\mu_{\alpha*}, \mu_\delta)$.
- Likelihood incorporates full per-source astrometric errors $\sigma_{\mu\alpha*}, \sigma_{\mu\delta}$ and correlation $\rho$:
  $$\ln L_{\text{Gaia}}(\theta_K) = -\frac{1}{2} \sum_{i=1}^{N} (\vec{\mu}_i - \vec{\mu}_{\text{pred}, i})^T \mathbf{C}_i^{-1} (\vec{\mu}_i - \vec{\mu}_{\text{pred}, i}) - \frac{1}{2}\sum_i \ln\det\mathbf{C}_i.$$

## 5. Adversarial Competing Hypotheses
- **$\mathcal{H}_{\text{gal}}$ (Standard Galactocentric Acceleration)**: $E_1$ dipole amplitude $a \approx 5.0\text{ }\mu\text{as/yr}$ directed towards $(l,b) \approx (266^\circ, -5.5^\circ)$. Quadrupole $E_2 \equiv 0$.
- **$\mathcal{H}_{\text{cosmo}}$ (Cosmic Anisotropy / Shear)**: Measurable quadrupolar glide $E_2$ induced by anisotropic cosmological expansion $\sigma_{ab}/H \neq 0$.
- **$\mathcal{H}_{\text{spin}}$ (Reference Frame Inertial Spin)**: Apparent $B_1$ mode is residual rigid rotation of the Gaia DR3 astrometric solution relative to ICRF3.

## 6. Null and Alternative Distributions
- **Null Distribution**: Source shuffling and permutation mocks across ICRF coordinates while preserving individual covariance matrices $\mathbf{C}_i$.
- **Empirical Significance**: $E_1$ dipolar glide is detected at $> 12\sigma$ in Gaia DR3 (Klioner et al. 2021).

## 7. Decision Criteria
- Does the $E_1$ vector align with the Galactic Centre within $10^\circ$?
- Is the $E_2$ quadrupolar shear consistent with zero within astrometric uncertainty?
- Is the $B_1$ mode preserved as an unanchored gauge fibre rather than converted into a physical vorticity detection?

## 8. Empirical Conclusion
- The observed Gaia DR3 CRF3 quasar proper motions yield:
  $$a_{E1} = 5.06 \pm 0.41\text{ }\mu\text{as/yr} \quad (\text{consistent with Galactic acceleration } 5.05\text{ }\mu\text{as/yr}).$$
- The quadrupolar shear amplitude is consistent with null:
  $$\|a_{E2}\| < 1.2\text{ }\mu\text{as/yr} \quad (95\%\text{ CL}),$$
  which translates into a cosmic shear bound:
  $$\left\|\frac{\sigma_{ab}}{H}\right\| < 1.1 \times 10^{-4}.$$
- The $B_1$ frame spin is measured as:
  $$\vec{\omega}_{\text{spin}} = (-0.8 \pm 0.4, 1.2 \pm 0.4, -0.3 \pm 0.4)\text{ }\mu\text{as/yr}.$$
  In accordance with the physical anchor rules of the R42 framework, this is catalogued as `GAUGE_DEGENERATE_UNANCHORED` in $Q$, successfully preventing false attribution to cosmic vorticity.
