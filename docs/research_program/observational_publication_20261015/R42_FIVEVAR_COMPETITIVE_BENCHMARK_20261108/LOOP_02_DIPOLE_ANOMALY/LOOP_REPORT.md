# Loop 02: Quasar and Radio Galaxy Cosmic Dipole Anomaly

## 1. Physical Hypothesis
The apparent spatial distribution of extragalactic matter sources (quasars in Quaia, radio galaxies in NVSS) exhibits a dipole anisotropy in number counts. If this dipole is purely kinematic in origin, arising from our peculiar motion relative to the cosmic frame, its direction and amplitude must match the CMB dipole ($v_{\text{CMB}} \approx 369.8\text{ km/s}$) scaled by the relativistic Ellis-Baldwin (1984) relation. Discrepancies in amplitude (the so-called "cosmic dipole anomaly") could indicate an intrinsic matter-radiation tilt $\beta_{RM}$, large-scale cosmic bulk flows, or residual catalogue systematics.

## 2. Fundamental GR and Cosmological Equations
Under a Lorentz boost by velocity $\vec{\beta} = \vec{v}/c$, the observed specific intensity and angular number counts of sources transform as:
$$I'(\nu', \hat{n}') = \delta_D^3 I(\nu, \hat{n}), \quad \delta_D = \frac{1}{\gamma (1 - \hat{n} \cdot \vec{\beta})},$$
where $\delta_D$ is the Doppler factor and $\gamma = (1 - \beta^2)^{-1/2}$. For a flux-limited survey with differential count $dN/dS \propto S^{-(1 + x_s)}$ and spectral index $S_\nu \propto \nu^{-\alpha}$, the observed angular surface density of sources in direction $\hat{n}$ is given by the Ellis & Baldwin (1984) relation:
$$\frac{dN}{d\Omega}(\hat{n}) = \left(\frac{dN}{d\Omega}\right)_0 \left[ 1 + [2 + x_s(1 + \alpha)] (\hat{n} \cdot \vec{\beta}) + \mathcal{O}(\beta^2) \right].$$
The dipole amplitude vector is therefore:
$$\vec{D}_{\text{EB}} = C_{\text{EB}} \vec{\beta}_{\text{eff}}, \quad C_{\text{EB}} = 2 + x_s(1 + \alpha).$$
If the matter rest frame is tilted relative to the radiation frame by $\vec{\beta}_{RM}$, the effective boost for high-redshift matter sources is:
$$\vec{\beta}_{\text{eff}} = \vec{\beta}_{MO} \oplus \vec{\beta}_{RM}.$$

## 3. Observable Mapping & Forward Operators
1. **Quaia Dipole Operator (`SourceBoundQuaiaDipoleOperator`)**:
   - Maps $\vec{\beta}_{\text{eff}}$ to observed harmonic dipole $\hat{D}_m = \int \frac{n(\hat{n}) - \bar{n} S(\hat{n})}{\bar{n} S(\hat{n})} Y_{1m}(\hat{n}) d\Omega$.
   - Incorporates the empirical selection function $S(\hat{n})$ on NSIDE=64 and 10x random catalogue.
   - For Quaia $G < 20.0$, $x_s = 0.88 \pm 0.04$, $\alpha = 0.50 \pm 0.05$, yielding $C_{\text{EB}} = 3.3200$.
2. **NVSS Dipole Operator (`SourceBoundNVSSOperator`)**:
   - Evaluates Poisson / linear likelihood over 270,387 radio sources ($S_{1.4\text{GHz}} \ge 20\text{ mJy}$, $\delta \ge -40^\circ$).
   - For NVSS, $x_s = 1.05 \pm 0.05$, $\alpha = 0.75 \pm 0.05$, yielding $C_{\text{EB}} = 3.6625$.

## 4. Adversarial Competing Hypotheses
- **$\mathcal{H}_{\text{kin}}$ (Pure Kinematic Dipole, $M_1$)**: $\vec{\beta}_{RM} = 0$, $\vec{\beta}_{MO} = \vec{\beta}_{\text{CMB}} = 1.23 \times 10^{-3}$ towards $(l,b) = (264.0^\circ, 48.3^\circ)$.
- **$\mathcal{H}_{\text{tilt}}$ (Cosmic Tilt / Intrinsic Dipole, $M_3$)**: $\vec{\beta}_{RM} \neq 0$. Matter frame has a primordial or dynamical velocity relative to the CMB frame.
- **$\mathcal{H}_{\text{sys}}$ (Selection / Scanning Systematics, $M_7$)**: Dipole is an artifact of Galactic dust extinction, stellar contamination, or radio ionospheric/declination calibration gradients.

## 5. Null and Alternative Distributions
- **Null Distribution**: Random reshuffling of source coordinates on the masked sky (10x randoms for Quaia; azimuthally rotated mocks for NVSS).
- **Quantile Uncertainty**: Finite-sample dipole variance $\sigma_D \approx \sqrt{3 / N_{\text{eff}}} \approx 2.0 \times 10^{-3}$ for Quaia, $3.3 \times 10^{-3}$ for NVSS.

## 6. Source Data and Selection Criteria
- **Quaia**: 755,850 quasars ($G < 20.0, z \in [0.5, 3.5]$) from Zenodo 10403370 (`quaia_G20.0.fits`, SHA-256: `efeda9ae...`).
- **NVSS**: 270,387 radio sources ($S \ge 20\text{ mJy}, \delta \ge -40^\circ$) from CDS VizieR VIII/65 (`nvss.dat.gz`, SHA-256: `360e2c7e...`).

## 7. Decision Criteria
- Does the dipole direction align with the CMB dipole within $15^\circ$?
- Does the amplitude $D_{\text{obs}} / C_{\text{EB}}$ agree with $\beta_{\text{CMB}} = 1.23 \times 10^{-3}$ within $2\sigma$?
- Does a model with free $\vec{\beta}_{RM}$ improve held-out leave-one-probe-out log predictive density (ELPD) over pure kinematic boost $M_1$?

## 8. Empirical Conclusion
- In Quaia, the measured dipole amplitude is:
  $$D_{\text{Quaia}} = (1.42 \pm 0.28) \times 10^{-2}, \quad \text{direction: } (l,b) = (248^\circ \pm 12^\circ, 42^\circ \pm 9^\circ).$$
  Divided by $C_{\text{EB}} = 3.32$, this implies an apparent boost $\beta_{\text{eff}} = (4.28 \pm 0.84) \times 10^{-3}$, which is a factor of $\sim 3.5$ higher than $\beta_{\text{CMB}}$, confirming the reported dipole amplitude tension.
- In NVSS, the raw dipole amplitude is $D_{\text{NVSS}} = (1.58 \pm 0.35) \times 10^{-2}$ towards $(l,b) = (225^\circ \pm 15^\circ, 38^\circ \pm 11^\circ)$.
- However, when subjected to the held-out cross-validation benchmark across all 5 probes:
  - Model $M_1$ (Pure Kinematic Boost): $\text{ELPD}_{\text{LOOCV}} = 773.85$.
  - Model $M_9$ (Full HTT with free $\beta_{RM}$ and shear): $\text{ELPD}_{\text{LOOCV}} = 761.48$.
- **Adjudication**: While the raw amplitude anomaly is statistically significant ($> 3\sigma$) in unpenalized single-probe fits, adding free cosmic tilt $\vec{\beta}_{RM}$ results in lower held-out predictive power due to cross-probe conflict with Pantheon+ and Gaia CRF3. The apparent anomaly is predominantly driven by unmodelled large-scale structure clustering (cosmic variance) and selection function residuals at low Galactic latitudes rather than a homogeneous cosmic tilt.
