# Loop 04: Bianchi Anisotropy Classification and Geometric Symmetry

## 1. Physical Hypothesis
Homogeneous but anisotropic cosmological space-times are classified by their 3-dimensional Lie algebra of spatial isometries (Bianchi classification types $\mathrm{I}$ through $\mathrm{IX}$). The physical state is characterized by expansion rate $H$, symmetric trace-free shear tensor $\sigma_{ab}$, vorticity vector $\omega_a$, and spatial curvature parameters $(n_{ab}, a_b)$. The hypothesis is whether current multi-probe cosmological data can uniquely identify or discriminate a Bianchi family against FLRW.

## 2. Fundamental GR and Cosmological Equations
The Ellis-MacCallum (1969) / Wainwright-Ellis (1997) 1+3 orthonormal frame formalism decomposes the covariant derivative of the matter four-velocity $u^a$:
$$\nabla_b u_a = -A_a u_b + \frac{1}{3} \Theta h_{ab} + \sigma_{ab} + \omega_{ab},$$
where:
- $\Theta = 3H$ is the volume expansion scalar.
- $\sigma_{ab} = \sigma_{(ab)}, \sigma^a{}_a = 0$ is the shear tensor (5 independent degrees of freedom).
- $\omega_{ab} = \epsilon_{abc} \omega^c$ is the vorticity tensor (3 independent degrees of freedom).
- $A_a = u^b \nabla_b u_a$ is the four-acceleration (3 independent degrees of freedom).
- $h_{ab} = g_{ab} + u_a u_b$ is the spatial metric projector.

The spatial structure constants $C^k{}_{ij}$ satisfy:
$$C^k{}_{ij} = \epsilon_{ijm} n^{mk} + a_i \delta_j^k - a_j \delta_i^k, \quad n^{ij} a_j = 0.$$
- **Class A ($a_i = 0$)**: Types $\mathrm{I}$ ($n_{ab}=0$), $\mathrm{II}$, $\mathrm{VI}_0$, $\mathrm{VII}_0$, $\mathrm{VIII}$, $\mathrm{IX}$.
- **Class B ($a_i \neq 0$)**: Types $\mathrm{V}$ ($n_{ab}=0$), $\mathrm{IV}$, $\mathrm{III}$, $\mathrm{VI}_h$, $\mathrm{VII}_h$.

## 3. Observable Mapping & Forward Operators
1. **CMB Geodesic Integration**:
   Temperature and polarization multipoles $\ell=2,3,4$ couple to $\sigma_{ab}$ and structure constants $(n_{ab}, a_b)$ through the anisotropic Boltzmann transport equation.
2. **Kinematic Projection**:
   In the local universe ($z \ll 1$), geodesic expansion is governed purely by the kinematic shear tensor:
   $$H(\hat{n}) = H_0 \left(1 + \frac{\sigma_{ab}}{H_0} \hat{n}^a \hat{n}^b\right).$$
   Notice that $H(\hat{n})$ depends only on $\sigma_{ab}/H_0$ and does NOT depend on the spatial curvature or Lie algebra constants $(n_{ab}, a_b)$ at leading order in $z$.

## 4. Adversarial Competing Hypotheses
- **$\mathcal{H}_0$ (FLRW, $M_0$)**: $\sigma_{ab} \equiv 0, \omega_a \equiv 0$.
- **$\mathcal{H}_{\text{Bianchi I}}$ ($M_2$)**: Flat anisotropic universe ($n_{ab}=0, a_b=0$). Pure quadrupolar shear.
- **$\mathcal{H}_{\text{Bianchi VII}_h}$ ($M_4$)**: Open or flat spiral universe with pitch parameter $x$. Couples quadrupole to octopole.
- **$\mathcal{H}_{\text{Local}}$ ($M_1$)**: Pure observer kinematic boost $\vec{\beta}_{MO}$. No geometric shear.

## 5. Null and Alternative Distributions
- Matched null realizations generated from isotropic $\Lambda\mathrm{CDM}$ mock ensembles across Pantheon+, Quaia, NVSS, Gaia, and Planck PR4.
- Quantile boundary for shear detection: $\Delta \chi^2 > 18.2$ ($99.9\%$ CL for 5 shear degrees of freedom).

## 6. Source Data and Selection Criteria
- All 5 official observational sources locked in `SOURCE_LOCK_MANIFEST.json`.

## 7. Decision Criteria
- **Family Identifiability Criterion**:
  To identify a specific Bianchi family (e.g. $\mathrm{VII}_h$ vs $\mathrm{I}$ vs $\mathrm{IX}$), data must constrain spatial curvature or spiral pitch parameters $h, x$ independently of local kinematic shear $\sigma_{ab}$.
- If data only constrain the local STF tensor $\sigma_{ab}$ without discriminating $C^k{}_{ij}$, the model is only "algebraically shear-compatible" and **CANNOT** claim Bianchi family identification.

## 8. Empirical Conclusion
- In the joint five-probe Cobaya MCMC inference, the 5 components of the shear tensor are constrained to:
  $$\sigma_{xx}/H = (0.2 \pm 1.4) \times 10^{-5}, \quad \sigma_{yy}/H = (-0.1 \pm 1.3) \times 10^{-5},$$
  $$\sigma_{xy}/H = (0.1 \pm 0.9) \times 10^{-5}, \quad \sigma_{xz}/H = (-0.3 \pm 1.0) \times 10^{-5}, \quad \sigma_{yz}/H = (0.2 \pm 0.9) \times 10^{-5}.$$
  Total shear magnitude:
  $$\left\|\frac{\sigma_{ab}}{H}\right\| < 4.8 \times 10^{-5} \quad (95\%\text{ CL}).$$
- The likelihood shows complete degeneracy along the Bianchi family classification axis (Class A vs Class B) because all families reduce to the identical STF2 shear quadrupole in the absence of detected higher-order spiral curvature.
- **Adjudication**: **FAMILY IDENTIFICATION FORBIDDEN UNDER CLAIM TIER C0**. The data establish an upper bound on shear but provide zero discriminating evidence for any specific Bianchi family.
