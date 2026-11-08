# Loop 01: Low-$\ell$ CMB Morphology and Bianchi Template Competition

## 1. Physical Hypothesis
The low-$\ell$ CMB temperature and polarization anisotropies ($\ell \in [2, 4]$) contain non-statistical directional alignments (e.g., quadrupole-octopole alignment, low variance, planar symmetry) that could originate from a large-scale homogeneous but anisotropic cosmological geometry (e.g., Bianchi $\mathrm{VII}_h$ or Bianchi $\mathrm{I}$ models with residual primordial shear $\sigma_{ab}/H$). Under the tensor five-variable framework, this is parameterized by the trace-free symmetric shear tensor $\sigma_{ab}/H$ and its resulting carrier modes $x_{\text{CMB}}$, bounded by physical anchor bodies $Q$, tested against matched empirical simulations $\Pi$, evaluated across directional support $F$, and mapped to early-universe depth $G_F$.

## 2. Fundamental GR and Cosmological Equations
In an anisotropic Bianchi model with metric
$$ds^2 = -dt^2 + g_{ab}(t) \omega^a \omega^b,$$
photon geodesic propagation through shear yields an integrated Sachs-Wolfe-like temperature anisotropy:
$$\frac{\Delta T}{T}(\hat{n}) = \left(\frac{\Delta T}{T}\right)_{\text{SW}} + \int_{t_{\text{rec}}}^{t_0} \sigma_{ab}(t) \hat{n}^a \hat{n}^b dt.$$
In terms of spherical harmonic coefficients $a_{\ell m}$:
$$a_{\ell m}^{\text{Bianchi}} = \sum_{a,b} \sigma_{ab}(t_0) \mathcal{T}_{\ell m}^{ab}(\Omega_m, \Omega_\Lambda, x),$$
where $\mathcal{T}_{\ell m}^{ab}$ is the transfer tensor coupling cosmic shear to multipole moments $\ell = 2, 3, 4$. For Bianchi $\mathrm{I}$, this is purely quadrupolar ($\ell = 2$); for spiral Bianchi $\mathrm{VII}_h$, spatial curvature and spiral structure induce higher multipole coupling ($\ell = 2, 3, 4$).
Polarization $E$ and $B$ modes are generated at reionization ($z \sim 6-8, \tau \approx 0.054$):
$$E_{\ell m} \propto \tau \sigma_{ab} \mathcal{K}_{\ell m}^{E, ab}, \quad B_{\ell m} \propto \tau \sigma_{ab} \mathcal{K}_{\ell m}^{B, ab}.$$

## 3. Observable Mapping & Forward Operators
The forward operator `SourceBoundPlanckLowEllOperator` maps $\theta_K = (\sigma_{ab}/H, \dots)$ to low-$\ell$ CMB carriers:
$$\mu_{\ell m}(\theta_K) = \mathcal{W}_{\ell m}^{ab} \left(\frac{\sigma_{ab}}{H}\right),$$
where $\mathcal{W}_{\ell m}^{ab}$ incorporates reionization optical depth $\tau = 0.054$ and beam/filtering transfer functions. The observed data vector $d \in \mathbb{R}^{24}$ contains real and imaginary components of $(E_{2m}, E_{3m}, E_{4m}, B_{2m}, B_{3m}, B_{4m})$ extracted from Planck PR4 (NPIPE) Commander component-separated maps.
The likelihood is Gaussian under the empirical covariance matrix $\mathbf{C}_{\text{Planck}} \in \mathbb{R}^{24 \times 24}$ derived from 100 end-to-end NPIPE Monte Carlo realistic simulations:
$$\ln L_{\text{Planck}}(\theta_K) = -\frac{1}{2} (d - \mu)^T \mathbf{C}_{\text{Planck}}^{-1} (d - \mu) - \frac{1}{2}\ln \det \mathbf{C}_{\text{Planck}} - \frac{N}{2}\ln(2\pi).$$

## 4. Adversarial Competing Hypotheses
- **$\mathcal{H}_0$ (Isotropic $\Lambda\mathrm{CDM}$ null)**: Cosmic shear $\sigma_{ab} \equiv 0$. Low-$\ell$ patterns are cosmic variance realizations drawn from isotropic angular power spectrum $C_\ell^{EE}, C_\ell^{BB}$.
- **$\mathcal{H}_1$ (Pure Bianchi I Quadrupole)**: Cosmic shear is axisymmetric or triaxial with no spatial curvature ($h=0$). Couplings are strictly confined to $\ell = 2$.
- **$\mathcal{H}_2$ (Spiral Bianchi $\mathrm{VII}_h$)**: Shear couples across $\ell=2,3,4$ with spiral pitch parameter $x = \sqrt{1 - \Omega_{\text{tot}}}/h$.
- **$\mathcal{H}_{\text{sys}}$ (Galactic Foregrounds / Residual Systematics)**: Low-$\ell$ $E/B$ power is residual thermal dust or synchrotron emission not captured by Commander component separation.

## 5. Null and Alternative Distributions
- **Null Distribution**: 100 Planck PR4 NPIPE end-to-end MC simulations containing realistic noise, beam asymmetry, scanning pattern, and Commander foreground separation residuals.
- **Empirical Significance $\Pi$**: The test statistic $\Delta \chi^2 = \chi^2(\sigma=0) - \chi^2(\hat{\sigma})$ evaluated against the MC null distribution yields an empirical exceedance probability $p = 0.41$.

## 6. Source Data and Selection Criteria
- **Source**: Planck PR4 (NPIPE) Commander polarization maps (`observed_lowell_EB.npz`, SHA-256: `56da085ee5cceb0d...`).
- **Modes**: $\ell \in [2, 4]$, $m \in [-\ell, \ell]$, totaling 24 independent degrees of freedom.
- **Masking**: 80% polarization sky fraction mask with apodization.

## 7. Decision Criteria
- **Detection Gate**: Requires $\Delta \chi^2 > 25$ ($> 5\sigma$), $\Delta\mathrm{BIC} < -10$, and held-out cross-validation preference over $\Lambda\mathrm{CDM}$.
- **Family Identification Gate**: Conditioned on external-transfer validation; requires non-zero spatial curvature identification distinct from instrumental beam ellipticity.

## 8. Empirical Conclusion
- In the two-layer competitive benchmark across Planck PR4 low-$\ell$ modes, the null hypothesis $\sigma_{ab} = 0$ achieves $\chi^2 / \text{dof} = 22.8 / 24$ ($p = 0.53$).
- The maximum-likelihood anisotropic shear is constrained to:
  $$\left\|\frac{\sigma_{ab}}{H}\right\| < 1.4 \times 10^{-4} \quad (95\%\text{ CL}).$$
- The Bayesian Information Criterion strongly favors isotropic $\Lambda\mathrm{CDM}$ ($\Delta\mathrm{BIC} = +28.4$ against Bianchi shear).
- **Adjudication**: **NULL CONSISTENT / NO ANISOTROPY DETECTION**. Low-$\ell$ CMB polarization does not support a global shear detection. Bianchi family identification is forbidden under Claim Tier C0.
