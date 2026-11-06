# Paper Extract P2: Bianchi Radiation Transfer, Polarisation Coupling, and Shear Identifiability

**Document ID:** `P2_BIANCHI_RADIATION_TRANSFER.md`  
**Parent Release:** `PR-R37-05-FINAL-REPORT` (Finite Scientific Convergence Release)  
**Target Paper:** P2 — *Bianchi Radiation Transfer & Polarisation / Large-angle Planck morphology under calibrated processing*  
**Claim Tier:** C0 (Conditional Synthetic Methods & Controlled Observational Sensitivity)  
**Artifact Mode:** Diagnostic Radiation & Shear Extract  
**Ownership & Role:** HTT Observational Likelihood / obsstat Feature Extraction  
**Transfer Source:** External/AniCLASS-calibrated transfer (pre-native solver baseline)  
**Baseline Commit:** `bdead6a8f51282ca647224b460b0f65de085568b`

---

## 1. Executive Summary & Physical Problem Statement

In an anisotropic or inhomogeneous spacetime, cosmic radiation propagation couples geometric shear $\sigma_{ab}$ and vorticity $\omega_{ab}$ to the angular intensity and linear polarisation multipoles of the Cosmic Microwave Background (CMB). Rigorous reconstruction of geometric shear from microwave observations requires solving the polarized radiative transfer equation along null geodesics in the presence of Thomson scattering.

Extract P2 presents the finite radiation transfer and shear sensitivity framework developed in R36-05 and R37-01. We demonstrate:
1. **Bolometric Nonlinearity:** The physical radiation stress tensor scales as $T^4$; applying a linear temperature-to-stress adapter introduces catastrophic coverage failure under relativistic or moderate observer boosts (collapsing coverage from 96.0% to 0.0% at $\beta=0.3$).
2. **Gain vs. Collision Incomplete Identifiability:** Thomson scattering gain $\mathscr{G}$ alone identifies only an equivalence class (fibre) of shear tensors; two positive intensity fields with identical Thomson gain generate distinct physical shear solutions ($\|\Delta \boldsymbol{\Sigma}\| = 1.18 \times 10^{-4}$).
3. **Polarisation Omission Bias:** Ignoring linear polarisation Stokes parameters ($Q, U$) introduces an irreducible systematic bias in the recovered shear tensor, analytically bounded by $\|\Delta\boldsymbol{\Sigma}\| \le \gamma_T \|P_*\| / [5 \lambda_{\min}(\mathcal{L}_I)]$.
4. **Exact Operator Completeness:** The joint radiation carrier requires at most 23 dimensions (20 at zero circular polarisation $V=0$), with moments $\ell \in \{0, 2, 4\}$ completing the shear operator $\mathcal{L}_I$ to machine precision ($8.88 \times 10^{-16}$).

All results are transfer-conditional synthetic methods demonstrations; no empirical cosmic shear detection or native Bianchi identification is claimed.

---

## 2. Mathematical Formulation & Radiation Operators

### 2.1 Covariant Boltzmann Equation & Radiative Moments
Following the $1+3$ covariant approach (Challinor 2000, Tsagas et al. 2008), the photon distribution function $f(x^a, p^a)$ is projected onto irreducible trace-free symmetric tensors on the observer's celestial 2-sphere. The energy density $\rho$, energy flux $q^a$, and anisotropic stress $\pi^{ab}$ are given by the $\ell = 0, 1, 2$ moments:
$$
\rho = \int \nu^3 f \, d\nu \, d\Omega, \qquad q^a = \int \nu^3 f e^a \, d\nu \, d\Omega, \qquad \pi^{ab} = \int \nu^3 f e^{\langle a} e^{b\rangle} \, d\nu \, d\Omega.
$$
The instantaneous shear-response operator $\mathcal{L}_I$ maps the 5-dimensional symmetric trace-free (STF) spatial shear tensor $\Sigma_{ab} = \sigma_{ab}/H$ to the radiation anisotropic stress source:
$$
\mathcal{L}_I \boldsymbol{\Sigma} = -(\boldsymbol{R}_\tau - \boldsymbol{C}_\pi),
$$
where $\boldsymbol{R}_\tau$ denotes the transport derivative residual, and $\boldsymbol{C}_\pi$ is the Compton collision term.

### 2.2 Cold-Electron Thomson Gain & Fibre Non-Uniqueness
Let $\mathsf{F}(n)$ be the $2\times 2$ transverse polarisation brightness matrix, $P_{\boldsymbol{n}} = \boldsymbol{I} - \boldsymbol{n}\boldsymbol{n}^T$, and $\boldsymbol{M} = \int \mathsf{F}(\boldsymbol{n})\,d\Omega$. The Thomson scattering gain operator is:
$$
\mathscr{G}\mathsf{F}(\boldsymbol{n}) = \frac{3}{8\pi} P_{\boldsymbol{n}} \boldsymbol{M} P_{\boldsymbol{n}}.
$$
The total collision operator is $\mathcal{C}[\mathsf{F}] = -\gamma_T (\mathsf{F} - \mathscr{G}\mathsf{F})$, where $\gamma_T = n_e \sigma_T$ is the Thomson scattering rate. While the gain $\mathscr{G}\mathsf{F}$ depends only on the rank-6 matrix $\boldsymbol{M}$, the shear response $\mathcal{L}_I$ depends on the full angular intensity distribution up to hexadecapole order ($\ell=4$):
$$
\mathcal{L}_I \boldsymbol{\Sigma} = \int_{S^2} I(\boldsymbol{n}) \, (\boldsymbol{n} \otimes \boldsymbol{n}) \, (\boldsymbol{\Sigma} : \boldsymbol{n}\boldsymbol{n}) \, d\Omega.
$$
Consequently, brightness fields with identical gain $\boldsymbol{M}$ can generate distinct shear responses $\mathcal{L}_I$, proving that gain measurements alone define an underdetermined fibre rather than a unique shear tensor.

### 2.3 Polarisation Omission Bias Theorem
When the linear polarisation quadrupole $P_*^{ab} = \int \nu^3 (Q + iU) m^{\langle a} m^{b\rangle} d\nu d\Omega$ is neglected, the collision term $\boldsymbol{C}_\pi$ is approximated by its unpolarized surrogate:
$$
\boldsymbol{C}_\pi^{\rm true} = -\gamma_T \left(\frac{9}{10}\boldsymbol{\pi} + \frac{1}{5}\boldsymbol{P}_*\right), \qquad \boldsymbol{C}_\pi^{\rm unpol} = -\frac{9\gamma_T}{10}\boldsymbol{\pi}.
$$
**Theorem (Polarisation Omission Upper Bound):**  
Let $\mathcal{L}_I$ be positive and invertible with minimum eigenvalue $\lambda_{\min}(\mathcal{L}_I) > 0$. The difference between the true shear $\boldsymbol{\Sigma}_{\rm true}$ and the unpolarized reconstruction $\boldsymbol{\Sigma}_{\rm unpol}$ satisfies:
$$
\boldsymbol{\Sigma}_{\rm true} - \boldsymbol{\Sigma}_{\rm unpol} = -\frac{\gamma_T}{5} \mathcal{L}_I^{-1} \boldsymbol{P}_*,
$$
$$
\|\boldsymbol{\Sigma}_{\rm true} - \boldsymbol{\Sigma}_{\rm unpol}\|_F \le \frac{\gamma_T \|\boldsymbol{P}_*\|_F}{5 \lambda_{\min}(\mathcal{L}_I)}.
$$

### 2.4 Dimension of the Joint Radiation Carrier
Near an unpolarized isotropic reference, the complete joint linear carrier decomposes as:
$$
\boldsymbol{x}_{\rm rad} = (\rho, \; \boldsymbol{\pi}, \; \boldsymbol{H}_4, \; \boldsymbol{P}_*, \; \boldsymbol{A}_*),
$$
with dimensionalities:
- $\rho$ (monopole): $\dim = 1$
- $\boldsymbol{\pi}$ (anisotropic stress, $\ell=2$): $\dim = 5$
- $\boldsymbol{H}_4$ (hexadecapole, $\ell=4$): $\dim = 9$
- $\boldsymbol{P}_*$ (linear polarisation STF, $\ell=2$): $\dim = 5$
- $\boldsymbol{A}_*$ (circular polarisation sector, $V$): $\dim = 3$

Total carrier dimension is $1 + 5 + 9 + 5 + 3 = 23$. At zero circular polarisation ($V=0$, standard cosmology), the carrier dimension is exactly **20**.

---

## 3. Quantitative Numerical Findings (R36-05 & R37-01)

### 3.1 Operator Precision & Spectral Coercivity
Using the positive synthetic $a=0.02, \beta=0.3$ sky profile with minimum physical eigenvalue $0.41555$:
- **Quadrature Precision:** Direct numerical quadrature and the reduced 20-component carrier $(\rho, \boldsymbol{\pi}, \boldsymbol{H}_4)$ agree to:
  $$
  \|\mathcal{L}_{I, \rm quad} - \mathcal{L}_{I, \rm carrier}\| = 8.88 \times 10^{-16},
  $$
  surpassing the preregistered convergence tolerance ($2.0 \times 10^{-10}$).
- **Operator Spectrum:** The five eigenvalues of $\mathcal{L}_I$ on STF5 are:
  $$
  \operatorname{spec}(\mathcal{L}_I) = [0.539469, \; 0.539473, \; 0.637188, \; 0.638056, \; 0.664453],
  $$
  yielding a condition number $\kappa = \lambda_{\max}/\lambda_{\min} = 1.2317$.
- **Moment Truncation:** Truncating at $\ell=2$ (dropping $\boldsymbol{H}_4$) changes the operator norm by $6.54 \times 10^{-3} \rho_0$; retaining $\boldsymbol{H}_4$ reduces operator discrepancy to $3.34 \times 10^{-16} \rho_0$.

### 3.2 Omission Bias & Positive Fibre Witness
- **Polarisation Omission:** Setting $\boldsymbol{P}_* = \boldsymbol{0}$ produces an empirical STF5 bias norm of **0.0085038**, strictly bounded by the theoretical limit:
  $$
  \frac{\gamma_T \|\boldsymbol{P}_*\|_F}{5 \lambda_{\min}(\mathcal{L}_I)} = 0.0087824.
  $$
- **Deterministic Fibre Witness:** Constructing two distinct positive intensity fields $I_1, I_2$ with identical rank-6 Thomson gain $\boldsymbol{M}$ ($\|\boldsymbol{M}_1 - \boldsymbol{M}_2\| = 1.11 \times 10^{-15}$) yields true shear solutions differing by:
  $$
  \|\boldsymbol{\Sigma}_1 - \boldsymbol{\Sigma}_2\|_F = 0.000118028.
  $$
  This confirms numerically that Thomson gain alone does not isolate a unique physical shear.

### 3.3 Linear vs. Exact Nonlinear Adapter Coverage
In 8,191 calibration skies and 4,096 test skies under the validated R36 noise law:
- **Low Boost ($\beta = 0.00123$):** Exact adapter achieves **94.53%** coverage on the tensor target; linear adapter degrades to **74.10%**. For the scalar rest-frame stress target, exact coverage is **95.56%** vs. **37.72%** for the linear adapter.
- **Moderate Boost ($\beta = 0.3$):** Exact adapter maintains **96.05%** tensor coverage and **95.39%** scalar coverage; linear adapter achieves **0.00%** coverage (complete collapse).
- **Simultaneous 20-Mode Event:** Centered simultaneous coverage across all 20 mode-coordinate pairs on 4,096 test draws is **3,888 / 4,096 = 94.9219%** at threshold 1.27089.

### 3.4 Exploratory Commander FULL005a Processed-Map Diagnostic
In a scoped exploratory examination of 48 Commander FULL005a processed-map realizations (IDs 300–347; 42 real $E/B$ coordinates, condition number 58,283.91):
- Conditional mean norm: **$0.07020\,\mu\mathrm{K}$** (conservative 95% norm interval $[0, \; 0.82832]\,\mu\mathrm{K}$).
- Under an assumed i.i.d. Gaussian law, Hotelling $T^2 = 3877.47$ (critical value 1240.13, nominal tail $p = 0.00254$).
- *Caveat:* Retrospective selection and unvalidated i.i.d. exchangeability prevent this diagnostic from serving as a cosmic anomaly detection; it is retained strictly as a pipeline processing diagnostic.

---

## 4. Claim-Tier Firewall & Methodological Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLAIM-TIER BOUNDARY                                │
├────────────────────────────────────────┬────────────────────────────────────┤
│ PERMITTED (Validated Diagnostic / C0) │ FORBIDDEN (Overclaim / Blocked)    │
├────────────────────────────────────────┼────────────────────────────────────┤
│ • "transfer-conditional radiation test"│ • "Bianchi geometry detected"      │
│ • "polarisation omission bias bound"   │ • "cosmic shear tensor measured"   │
│ • "diagnostic-only processed-map norm" │ • "cosmic parity violation proved" │
│ • "20-component carrier completeness"  │ • "native solver validation"       │
│ • "Thomson gain fibre non-uniqueness"  │ • "model-independent truth bound"  │
└────────────────────────────────────────┴────────────────────────────────────┘
```

1. **Synthetic Methods Ceiling:** All shear-support intervals are evaluated relative to an assumed central derivative budget $\boldsymbol{R}_\tau$. No empirical cosmic shear is reported.
2. **Foreground & MC100 Hold:** Original acceptance tasks R36-07 (physical foreground budget) and PR4/P2 (MC100 simulation ensemble) remain on **HOLD**. Processing diagnostics cannot substitute for empirical null calibration.

---

## 5. Residual Obligations & Solver Handoff Interface

Before empirical CMB observations can be interpreted as Bianchi or anisotropic geometry constraints:
1. **Native Solver Handoff:** Replace AniCLASS/external transfer with the native low-$\ell$ Bianchi Boltzmann solver, propagating metric shear and Weyl curvature directly into $C_\ell^{TT, TE, EE, BB}$.
2. **Instrumental Beam & Bandpass Integration:** Convolve the 20-component carrier with frequency-dependent beam profiles and bandpass transmission functions across all Planck HFI/LFI channels.
3. **Full Foreground Covariance:** Integrate the qualified R36-07 foreground error budget into the noise covariance matrix $\boldsymbol{\Sigma}_{\rm rad}$.

---

## 6. Primary Literature & Citation Ledger

1. **A. Challinor**, *Microwave background polarization in cosmological models*, Phys. Rev. D **62**, 043004 (2000), [arXiv:astro-ph/9911481](https://arxiv.org/abs/astro-ph/9911481).
2. **C. G. Tsagas, A. Challinor, and R. Maartens**, *Relativistic cosmology and large-scale structure*, Phys. Rep. **465**, 61–147 (2008), [arXiv:0705.4397](https://arxiv.org/abs/0705.4397).
3. **J. Chluba, J. C. Hill, and M. H. Abitbol**, *Rethinking CMB foregrounds: systematic extension of foreground parameterizations*, Mon. Not. R. Astron. Soc. **472**, 1195–1213 (2017), [arXiv:1701.00274](https://arxiv.org/abs/1701.00274).
4. **Planck Collaboration**, *Planck 2018 results. III. High Frequency Instrument data processing and frequency maps*, Astron. Astrophys. **641**, A3 (2020).
5. **D. Saadeh et al.**, *How isotropic is the Universe?*, Phys. Rev. Lett. **117**, 131302 (2016), [arXiv:1605.07178](https://arxiv.org/abs/1605.07178).
