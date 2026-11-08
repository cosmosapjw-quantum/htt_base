# Paper Extract P3: Opacity Cosmology, Matrix Attenuation, and Directional Hubble Expansion

**Document ID:** `P3_OPACITY_COSMOLOGY.md`  
**Parent Release:** `PR-R37-05-FINAL-REPORT` (Finite Scientific Convergence Release)  
**Target Paper:** P3 — *Directional redshift-dependent expansion estimates / Opacity Cosmology & Directional Hubble*  
**Claim Tier:** C0 (Conditional Released-Observable Sensitivity & Finite Synthetic Method Control)  
**Artifact Mode:** Diagnostic Optical Distance & Expansion Extract  
**Ownership & Role:** HTT Likelihood & Inference / obsstat Feature Extraction  
**Transfer Source:** None (Direct Type Ia Supernova & Distance Indicators)  
**Baseline Commit:** `bdead6a8f51282ca647224b460b0f65de085568b`

---

## 1. Executive Summary & Physical Problem Statement

Cosmological tests of the Copernican principle and spatial isotropy frequently rely on luminosity distance measurements $D_L(z, \boldsymbol{n})$ from Type Ia Supernovae (SNe Ia) and peculiar velocity surveys like Cosmicflows-4 (CF4). However, optical propagation through cosmic dust, intergalactic plasma, or dark sector couplings can violate photon number conservation, inducing non-metric cosmic opacity $\tau(z, \boldsymbol{n})$.

Extract P3 formalizes the directional optical response and opacity-qualified expansion framework developed across R36-01, R36-08, and R37-03:
1. **Apparent vs. Physical Directional Hubble Ratios:** SNe Ia magnitude contrasts identify apparent directional expansion ratios $H_F(\boldsymbol{n}_1)/H_F(\boldsymbol{n}_2)$; mapping these to true spacetime expansion $\mathcal{H}_u(\boldsymbol{n})$ requires an explicit opacity allowance $\Delta\tau$ and distance-remainder budget $\Delta r_g$.
2. **Absolute $H_0$ Invariance:** Profiling the absolute magnitude intercept $M$ eliminates all absolute $H_0$ information from the angular carrier. The angular carrier constrains directional anisotropy, not the Hubble constant value.
3. **Grey vs. Dichroic Matrix Attenuation:** In a full polarimetric channel, complete positivity and trace-nonincreasing properties bound luminosity distances; relative Stokes channel mixing (dichroism) leaves grey extinction unconstrained.
4. **Exact Clarkson–Bassett–Lu (CBL) Opacity Control:** We derive the exact non-perturbative opacity correction to the CBL curvature invariant. In a synthetic flat control with linear opacity $\tau = 0.2z$, uncorrected curvature gives spurious positive curvature ($8.72 \times 10^{-7}\,\mathrm{Mpc}^{-2}$), whereas exact correction restores spatial flatness to machine precision ($2 \times 10^{-20}\,\mathrm{Mpc}^{-2}$).
5. **Observational Overlap Audit:** An empirical CBL test cannot be performed with current data because released cosmic chronometer $H(z)$ tables ($z \in [0.179, 1.965]$) have zero redshift overlap with the validated low-$z$ Pantheon+ sample ($z \le 0.15$).

---

## 2. Mathematical Formulation & Opacity Transformations

### 2.1 Optical Propagation with Cosmic Opacity
In an anisotropic spacetime with directional expansion rate $\mathcal{H}_u(\boldsymbol{n})$, let $d(z, \boldsymbol{n})$ denote the metric luminosity distance. Non-metric optical extinction is parameterized by optical depth $\tau_r(z, \boldsymbol{n})$, and finite-distance/peculiar-velocity perturbations by $r_g(z, \boldsymbol{n})$:
$$
D_{L,r}(z, \boldsymbol{n}) = \frac{cz}{\mathcal{H}_u(\boldsymbol{n})} \exp\left[ r_g(z, \boldsymbol{n}) + \frac{1}{2}\tau_r(z, \boldsymbol{n}) \right].
$$
Defining the apparent flux-derived expansion parameter $H_F(z, \boldsymbol{n}) \equiv cz / D_{L,r}(z, \boldsymbol{n})$, the relation to the true kinematic expansion $\mathcal{H}_u(\boldsymbol{n})$ is bounded by:
$$
H_F(z, \boldsymbol{n}) \exp\left[ -b_g + \frac{\tau_-}{2} \right] \le \mathcal{H}_u(\boldsymbol{n}) \le H_F(z, \boldsymbol{n}) \exp\left[ b_g + \frac{\tau_+}{2} \right],
$$
where $|r_g| \le b_g$ and $\tau_- \le \tau_r \le \tau_+$.

For two lines of sight $\boldsymbol{n}_1, \boldsymbol{n}_2$, the apparent logarithmic expansion difference relates to the magnitude difference $\Delta m = m(\boldsymbol{n}_1) - m(\boldsymbol{n}_2)$ via:
$$
\Delta \ln H_F = -\frac{\ln 10}{5} \Delta m.
$$
The physical local Hubble ratio satisfies:
$$
\ln \frac{\mathcal{H}_u(\boldsymbol{n}_1)}{\mathcal{H}_u(\boldsymbol{n}_2)} = -\frac{\ln 10}{5} \Delta m + \Delta r_g + \frac{1}{2}\Delta \tau.
$$

### 2.2 Quantum Optical Matrix Attenuation & Choi Channel Bounds
When incorporating transverse polarization, optical transmission through an astrophysical medium is represented by a completely positive, trace-nonincreasing quantum channel $\mathcal{A}: \mathcal{M}_2(\mathbb{C}) \to \mathcal{M}_2(\mathbb{C})$:
$$
\mathcal{A}(\rho) = D_L^{-2} \sum_k K_k \rho K_k^\dagger, \qquad \sum_k K_k^\dagger K_k \le \boldsymbol{I}_2.
$$
Under the Choi–Jamiołkowski isomorphism, the channel corresponds to a positive semi-definite matrix $\Lambda_{\mathcal{A}} \ge 0$. Decomposing the transmission generator:
- The traceless generator components determine polarimetric birefringence (rotation of linear polarization angles) and dichroism (differential attenuation between orthogonal polarization modes);
- The scalar trace component determines grey extinction $\tau_{\rm grey}$.

Because differential Stokes transformations fix only the normalized channel shape $\mathcal{P} = \mathcal{A}/\operatorname{tr}(\mathcal{A})$, polarimetric channel observations cannot break the degeneracy with grey attenuation.  
In the executed synthetic filter benchmark:
- Setting Kraus operator $\boldsymbol{K} = \operatorname{diag}(1/3, 1/5)$ with input covariance $\boldsymbol{Q}_{\rm in} = \operatorname{diag}(1/9, 1/25)$:
- The trace-nonincreasing condition alone establishes the outer geometric bound $0 < D_L \le 3$ in arbitrary length units.
- Introducing an external calibration constraint $t_{\min} \boldsymbol{I} \le \boldsymbol{T} \le \boldsymbol{I}$ with $t_{\min} = 0.1$ sharpens the identified luminosity distance interval to:
  $$
  D_L \in \left[ \sqrt{\frac{t_{\min}}{1/25}}, \; 3 \right] = \left[ \sqrt{2.5}, \; 3 \right] \approx [1.58114, \; 3.00000].
  $$

### 2.3 Non-Perturbative Clarkson–Bassett–Lu (CBL) Curvature Identity
The classical CBL curvature test for spatial homogeneity evaluates:
$$
C[d](z) = 1 + \frac{H^2(z)}{c^2} \left[ d(z) d''(z) - d'^2(z) \right],
$$
where $C[d] \equiv 1$ in any FLRW geometry with arbitrary constant spatial curvature $\Omega_k$.  
Under non-metric opacity $d_r(z) = d(z) e^{\tau(z)/2}$, the observed invariant satisfies:
$$
C[d_r](z) = 1 + e^{\tau(z)}\left( C[d](z) - 1 \right) + \frac{d_r^2(z)}{2c^2} \left[ H^2(z) \tau''(z) + H(z) H'(z) \tau'(z) \right].
$$
Any violation $C[d_r] \ne 1$ can be produced either by broken spatial homogeneity ($\Omega_k \ne \mathrm{const}$) or by nonzero opacity derivatives ($\tau', \tau'' \ne 0$).

---

## 3. Empirical & Numerical Findings (R36-08 & R37-03)

### 3.1 Pantheon+ SNe Ia Directional Expansion Carrier
The primary analysis utilizes 490 selected SNe Ia from Pantheon+SH0ES across two redshift bins:
- Low-depth bin: $0.0233 \le z_{\rm HD} \le 0.06$ (342 SNe, including duplicate-CID rows);
- High-depth bin: $0.06 < z_{\rm HD} \le 0.15$ (148 SNe, including duplicate-CID rows);
- The primary cohort contains 62 duplicate-CID rows; the 705-row lower-cut sensitivity contains 114 duplicate-CID rows.
- Full $16 \times 16$ coefficient covariance matrix (dipole + STF quadrupole per bin) validated for exact symmetry and positive-definiteness ($\operatorname{spec} > 0$). Outside this 490-row subblock, the released 1,701-row array fails numerical symmetry.

**Primary Directional Results ($\boldsymbol{x} = (1,0,0)$ vs. $\boldsymbol{z} = (0,0,1)$):**
- **Low-bin Magnitude Contrast:** $\Delta m = -0.022814 \pm 0.038735$ mag (marginal $1\sigma$).
- **Signed Multipole Contributions:** The dipole and STF quadrupole contribute $+0.000417$ and $+0.010089$ to $\Delta \ln H_F$ respectively.
- **Simultaneous 16D 95% Confidence Ellipsoid ($r_{95}^2 = 26.2962$):**  
  Apparent expansion ratio:
  $$
  \frac{H_F(\boldsymbol{x})}{H_F(\boldsymbol{z})} \in [0.9222, \; 1.1074].
  $$
- **Physical Ratio Interval ($|\Delta r_g| \le 0.01, |\Delta \tau| \le 0.02$):**  
  Conditioned on declared opacity and distance error bounds:
  $$
  \frac{\mathcal{H}_u(\boldsymbol{x})}{\mathcal{H}_u(\boldsymbol{z})} \in [0.9040, \; 1.1297].
  $$
- **Depth Contrast (High minus Low):**  
  $\Delta m_{\rm high} - \Delta m_{\rm low} = +0.097139 \pm 0.077377$ mag. Retaining the 50,616 nonzero cross-depth covariance elements is essential; dropping cross-bin covariance yields an incorrect standard error of $0.077829$ mag.
- **Omnibus Angular Significance:** Residual $\chi^2$ improvement from adding 16 angular parameters is $\Delta\chi^2 = 17.2066$ ($p = 0.372$, below the 95% threshold of 26.296). The data are fully consistent with statistical isotropy.

### 3.2 Cosmicflows-4 (CF4) Operator Comparison
The exact R36-01 CF4 operator acts on 35,970 galaxy groups across four $z_{\rm CMB}$ shells ($R = 5\,h^{-1}\mathrm{Mpc}$ smoothing).
- Apparent expansion rate $H_W(\boldsymbol{x})$ ranges from $72.59$ to $72.65\,\mathrm{km}\,\mathrm{s}^{-1}\,\mathrm{Mpc}^{-1}$ in the inner two shells.
- Conditional covariance trace across the 36 coordinates is $17.68057\,(\mathrm{km}\,\mathrm{s}^{-1}\,\mathrm{Mpc}^{-1})^2$.
- *Methodological Independence:* CF4 and Pantheon+ use distinct selection functions, peculiar-velocity flow models, and coordinate charts. No joint statistical significance can be asserted without a unified cross-survey covariance.

### 3.3 Synthetic CBL Opacity Control & Redshift Disconnection
- **Flat Synthetic Control:** Setting $H = 70\,\mathrm{km}\,\mathrm{s}^{-1}\,\mathrm{Mpc}^{-1}$, $d = cz/H$, and transparent-at-vertex linear opacity $\tau(z) = 0.2z$ at window centers $z \in \{0.025, 0.04, 0.06, 0.08\}$:
  - Naive uncorrected first-derivative curvature $(H^2 d_r'^2/c^2 - 1)/d_r^2$ yields apparent positive curvature ranging from $+8.718 \times 10^{-7}$ to $+2.721 \times 10^{-7}\,\mathrm{Mpc}^{-2}$.
  - Applying the exact opacity correction restores true flat curvature to $2.0 \times 10^{-20}\,\mathrm{Mpc}^{-2}$ across all windows.
- **Observational Overlap Audit:** Inspecting public cosmic chronometer data (`CCcovariance`, Moresco et al.) reveals 15 measurements spanning $z = 0.1791$ to $1.965$. Because the validated Pantheon+ sample ends at $z = 0.15$, there is **zero direct redshift overlap**. Extrapolating across this redshift gap is unphysical and forbidden.

---

## 4. Claim-Tier Firewall & Methodological Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLAIM-TIER BOUNDARY                                │
├────────────────────────────────────────┬────────────────────────────────────┤
│ PERMITTED (Validated Diagnostic / C0) │ FORBIDDEN (Overclaim / Blocked)    │
├────────────────────────────────────────┼────────────────────────────────────┤
│ • "apparent directional Hubble ratio"  │ • "absolute H0 measured"           │
│ • "opacity-conditioned physical bounds"│ • "spatial curvature determined"   │
│ • "exact CBL opacity correction"       │ • "cosmic opacity detected"        │
│ • "CF4 operator window comparison"     │ • "joint SN/CF4 unified detection" │
│ • "cross-bin covariance preservation"  │ • "Copernican principle refuted"   │
└────────────────────────────────────────┴────────────────────────────────────┘
```

1. **No Absolute $H_0$ Inference:** The magnitude intercept $M$ is profiled out. Any claim that the angular 16-vector constrains the absolute expansion rate $H_0$ is false.
2. **Curvature Test Gate:** An empirical CBL test requires overlapping, calibrated $d(z)$ and $H(z)$ datasets with complete covariance. This condition is currently unmet.

---

## 5. Residual Obligations & Solver Handoff Interface

1. **Empirical Overlapping Chronometers:** Acquire and qualify an independently calibrated $H(z)$ dataset covering the low-redshift window $z \in [0.02, 0.15]$ with complete off-diagonal systematic covariance.
2. **Unified SN-Peculiar Velocity Covariance:** Formulate a joint likelihood framework incorporating correlated peculiar-velocity flows between Pantheon+ host galaxies and the CF4 density field.
3. **Solver Handoff Schema:** Directional expansion carriers $(\boldsymbol{x}_{16}, \boldsymbol{\Sigma}_{16})$ and opacity envelopes are exported via `ObservableVector` to calibrate background geodesic integration in the forthcoming Boltzmann solver.

---

## 6. Primary Literature & Citation Ledger

1. **C. Clarkson, B. A. Bassett, and T. H.-C. Lu**, *A general test of the Copernican Principle*, Phys. Rev. Lett. **101**, 011301 (2008), [arXiv:0712.3457](https://arxiv.org/abs/0712.3457).
2. **D. Brout et al.**, *The Pantheon+ Analysis: Cosmological Constraints*, Astrophys. J. **938**, 110 (2022), [arXiv:2202.04077](https://arxiv.org/abs/2202.04077).
3. **R. Stiskalek, H. Desmond, and G. Lavaux**, *No evidence for local H0 anisotropy from Tully–Fisher or supernova distances*, Mon. Not. R. Astron. Soc. **534**, 2048–2062 (2024), [arXiv:2509.14997](https://arxiv.org/abs/2509.14997).
4. **M. Moresco et al.**, *Unveiling the Universe with Emerging Cosmological Probes*, Living Rev. Relativ. **25**, 6 (2022), [arXiv:2201.07241](https://arxiv.org/abs/2201.07241).
5. **R. B. Tully et al.**, *Cosmicflows-4*, Astrophys. J. **944**, 94 (2023), [arXiv:2209.11238](https://arxiv.org/abs/2209.11238).
