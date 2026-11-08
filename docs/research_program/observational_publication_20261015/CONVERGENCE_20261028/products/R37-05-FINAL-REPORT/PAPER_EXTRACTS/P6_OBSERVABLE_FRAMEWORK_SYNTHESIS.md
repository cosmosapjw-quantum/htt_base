# Paper Extract P6: Observable Framework Synthesis, Architectural Firewalls, and Solver-Ready Interfaces

**Document ID:** `P6_OBSERVABLE_FRAMEWORK_SYNTHESIS.md`  
**Parent Release:** `PR-R37-05-FINAL-REPORT` (Finite Scientific Convergence Release)  
**Target Paper:** P6 — *Beyond-FLRW kinematics / Observable Framework Synthesis*  
**Claim Tier:** C0 (Structural Architecture, Metric Governance, and Synthesis Framework)  
**Artifact Mode:** Synthesis Specification & Architectural Blueprint  
**Ownership & Role:** HTT Core Architecture / MIO Framework Integration / common Contracts  
**Transfer Source:** None (Foundational Metrology & Governance Specification)  
**Baseline Commit:** `bdead6a8f51282ca647224b460b0f65de085568b`

---

## 1. Executive Summary & Physical Problem Statement

Astrophysical searches for anisotropic expansion, cosmic shear, and non-FLRW geometry span disparate observational domains—from CMB temperature and polarisation multipoles, to Gaia stellar proper motions, to supernova luminosity distances. Historically, research programs in this domain have suffered from severe methodological pitfalls:
1. Conflating model-independent observational features with model-dependent posterior probabilities;
2. Misinterpreting uncalibrated external Boltzmann codes (such as AniCLASS or legacy TSC) as native general-relativistic solutions;
3. Erasing parameter nullspaces through premature scalar projections;
4. Making unwarranted claims of cosmic family detection based on localized statistical anomalies.

Extract P6 synthesizes the architectural, mathematical, and statistical framework developed within `htt_base` to resolve these challenges. We establish a rigorous decoupling between:
- **Model-Independent Observatory (MIO):** Evaluates diagnostic certificates, directional/depth coherence, and $(x, F, Q, \Pi, G_F)$ metric spaces without assuming a cosmological model;
- **Hypothesis Testing & Tomography (HTT):** Evaluates model-dependent likelihoods, posterior bundles, Bayesian evidence, and local/global mixture inference;
- **Observable Statistics (`obsstat`):** Extracts harmonic coefficients, templates, BiPoSH features, and null distributions without performing inference;
- **BASS Pre-Solver Interface:** Governs transfer provenance, external adapters, and `AtlasEntryLite` specifications awaiting the external native low-$\ell$ Bianchi Boltzmann solver.

---

## 2. The Five-Coordinate Metric Formalism $(x, F, Q, \Pi, G_F)$

To prevent information loss across reduction pipelines, all observational and synthetic states are embedded in the 5-coordinate metric representation:

$$
\mathcal{S} = \left( x, \; F, \; Q, \; \Pi, \; G_F \right),
$$

where each coordinate fulfills a strictly delineated mathematical role:

1. **Carrier Coordinate $x$:**  
   Retains the signed, unreduced representation coefficients, celestial coordinate frame, units, and multipole indices. For example, in Gaia astrometry, $x_{24}$ retains all 24 signed polar/axial components across redshift bins; in radiation transfer, $x_{20}$ retains $(\rho, \boldsymbol{\pi}, \boldsymbol{H}_4, \boldsymbol{P}_*)$.
2. **Support Function $F(W)$:**  
   Measures the directional extent of a convex physical parameter body $\mathcal{C}$ along direction $W$:
   $$
   F(W) \equiv \sup_{x \in \mathcal{C}} \langle W, x \rangle.
   $$
   Support functions preserve outer confidence sets under linear projections and nuisance marginalization without requiring parametric assumptions.
3. **Gauge Coordinate $Q$:**  
   Measures displacement relative to a specified, centered reference body $\mathcal{C}_0$. A positive cone or an uncentered slice is explicitly prohibited from serving as a gauge body.
4. **Probability Record $\Pi$:**  
   Encodes the probability measure exclusively under a declared, qualified sampling law or posterior distribution. A diagnostic certificate must never populate $\Pi$ with a pseudo-posterior.
5. **Transport & Tomography Operator $G_F$:**  
   Retains cross-window covariances, transfer matrices, and redshift-dependent mapping operators needed to track an observable through cosmological depth.

---

## 3. Mathematical Foundations: Deterministic Joint Error Propagation

When observational data are subject to deterministic truncation or approximation errors (e.g., higher-multipole truncation, unmodeled foregrounds, or optical depth allowances), treating these errors as stochastic noise invalidates confidence coverage.

### 3.1 The Deterministic Error Body
Let the true physical parameter vector be $X$, subject to a quadratic constraint matrix $G$:
$$
e^T G e \le \epsilon_X^2, \qquad e = X - X_0.
$$
Under a linear response map $b = B e$, the maximum bias along any directional vector $v$ is bounded by:
$$
\sup_e v^T B e = \epsilon_X \sqrt{v^T B G^{-1} B^T v}.
$$
The ellipsoid matrix $E = B G^{-1} B^T$ defines a deterministic joint error body. Rather than inflating marginal error bars independently, this formulation preserves the shared correlation structure of systematic errors.

### 3.2 Finite Gaussian Coverage Calibration
In the validated 5-parameter Gaussian benchmark (R37-00 / E2):
- A systematic bias vector of radius $r_{\rm bias} = 1.5$ in Fisher information units was injected into 100,000 synthetic draws.
- **Ordinary Nominal 95% Ball:** Collapses to an exact empirical coverage of **82.7209%**, severely failing nominal coverage due to unmodeled bias.
- **Bias-Aware Joint Construction:** Incorporating the deterministic error body $E$ achieves an exact theoretical coverage of **95.0000%** and an empirical Monte Carlo coverage of **95.0980%** (100,000 draws).

This proves that bounding joint deterministic remainders within the $(x, F, Q, \Pi, G_F)$ framework guarantees statistical validity even in the presence of unmodeled physical truncations.

---

## 4. Architectural Separation & Subsystem Responsibilities

The codebase enforces strict functional boundaries between five primary subsystems:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REPOSITORIES & SUBSYSTEM MAP                          │
├───────────────────┬─────────────────────────────────────────────────────────┤
│ Subsystem         │ Exclusive Scientific Ownership & Scope                  │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ common/contracts  │ SSoT schemas, artifact manifests, claim-tier firewalls, │
│                   │ transfer provenance, semantic guards.                   │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ obsstat           │ Feature extraction only: alms, templates, BiPoSH,       │
│                   │ low-ell scalar statistics, morphology axes.             │
│                   │ FORBIDDEN: Likelihoods, posteriors, certificates.       │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ mio               │ Model-independent diagnostics, MioCertificate,          │
│                   │ directional/depth coherence, (x,F,Q,Pi,GF) reports.     │
│                   │ FORBIDDEN: Posterior odds, truth certificates, evidence.│
├───────────────────┼─────────────────────────────────────────────────────────┤
│ htt               │ Model-dependent inference: likelihoods, posterior       │
│                   │ bundles, Bayes factors, null competition, PPC, LOOCV.   │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ bass_py (Pre-Solv)│ Transfer provenance, AniCLASS/external adapters,        │
│                   │ AtlasEntryLite schemas, future native solver interface. │
└───────────────────┴─────────────────────────────────────────────────────────┘
```

### 4.1 Diagnostic Certificates vs. Bayesian Posteriors
- **MioCertificate:** A strictly deterministic or fixed-design diagnostic document that certifies whether an observed dataset is mathematically compatible with an observable feature (e.g., an STF quadrupole or an optical contrast). It does not compute a posterior probability or certify physical truth.
- **HTT Posterior Bundle:** A Bayesian statistical product that conditions on a specific cosmological model, prior distribution, and likelihood function. It requires full simulation-based calibration, predictive checks (PPC), and leave-one-out cross-validation (LOOCV).

---

## 5. Claim-Tier Firewall & Methodological Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLAIM-TIER BOUNDARY                                │
├────────────────────────────────────────┬────────────────────────────────────┤
│ PERMITTED (Validated Diagnostic / C0) │ FORBIDDEN (Overclaim / Blocked)    │
├────────────────────────────────────────┼────────────────────────────────────┤
│ • "claim-tiered observational framework"│ • "Bianchi geometry detected"      │
│ • "transfer-conditional inference"     │ • "Bianchi family identified"      │
│ • "diagnostic-only certificate"        │ • "model-independent truth cert"   │
│ • "local/global discrimination candidate"│ • "MIO posterior"                 │
│ • "morphology compatibility"           │ • "TSC full solver"                │
│ • "external-transfer path"             │ • "external transfer validated"   │
└────────────────────────────────────────┴────────────────────────────────────┘
```

1. **Native Solver Boundary:** No native general-relativistic Bianchi Boltzmann solver exists within this repository. All transfer-dependent results are strictly **transfer-conditional** on external approximations (AniCLASS).
2. **Family Identification Ban:** No combination of low-$\ell$ scalar statistics, directional expansion ratios, or astrometric proper motions can claim empirical identification of a Bianchi family prior to native solver validation.

---

## 6. Solver Handoff Interface & Future Implementation

The infrastructure is designed as an observatory and inference framework ready to consume native solver outputs cleanly upon arrival:

```mermaid
flowchart LR
    A["Native Bianchi Boltzmann Solver\n(External 1+3 PSTF / Tetrad)"] -->|AtlasEntryLite\nJSON / HDF5| B["bass_py Adapter\n(Transfer Provenance Gate)"]
    B -->|Verified All-m Templates\nTT, TE, EE, BB| C["obsstat\n(Feature Extraction & Covariance)"]
    C -->|ObservableVector\nx_rad, x_opt| D["HTT Inference Engine\n(Likelihoods & Posterior Bundles)"]
    C -->|Carrier Projections\n(x, F, Q, Pi, G_F)| E["MIO Observatory\n(MioCertificate & Coercivity)"]
    D --> F["Final Scientific Claim Ledger"]
    E --> F
```

### 6.1 `AtlasEntryLite` Protocol Specification
The external solver must deliver pre-computed anisotropic transfer functions complying with the `AtlasEntryLite` schema:
- **Geometry Specification:** Bianchi type ($\mathrm{I}, \mathrm{II}, \mathrm{VII}_0, \mathrm{VII}_h, \mathrm{VIII}, \mathrm{IX}$), group parameters $(x_B, h_B)$, expansion rates $(H_0, \sigma/H)$, matter content $(\Omega_m, \Omega_r, \Omega_\Lambda)$;
- **Harmonic Spectra:** $C_{\ell, m, \ell', m'}^{XY}$ for all multipoles $2 \le \ell \le \ell_{\max}$ across temperature and polarisation ($X, Y \in \{T, E, B\}$);
- **Coordinate Integrity:** Explicit celestial orientation Euler angles $(\alpha, \beta, \gamma)$ linking Bianchi symmetry axes to galactic coordinates $(l, b)$;
- **Integrity Seal:** SHA-256 cryptographic digest of the complete numerical dataset.

Once received, the `bass_py` adapter verifies the schema, checks energy conservation and frame invariance, and passes the templates to `htt` for rigorous model comparison against Planck and future high-resolution CMB surveys.

---

## 7. Primary Literature & Citation Ledger

1. **A. Challinor**, *Microwave background polarization in cosmological models*, Phys. Rev. D **62**, 043004 (2000), [arXiv:astro-ph/9911481](https://arxiv.org/abs/astro-ph/9911481).
2. **C. G. Tsagas, A. Challinor, and R. Maartens**, *Relativistic cosmology and large-scale structure*, Phys. Rep. **465**, 61–147 (2008), [arXiv:0705.4397](https://arxiv.org/abs/0705.4397).
3. **G. F. R. Ellis, R. Maartens, and M. A. H. MacCallum**, *Relativistic Cosmology*, Cambridge University Press (2012).
4. **D. Saadeh et al.**, *How isotropic is the Universe?*, Phys. Rev. Lett. **117**, 131302 (2016), [arXiv:1605.07178](https://arxiv.org/abs/1605.07178).
5. **C. Clarkson, B. A. Bassett, and T. H.-C. Lu**, *A general test of the Copernican Principle*, Phys. Rev. Lett. **101**, 011301 (2008), [arXiv:0712.3457](https://arxiv.org/abs/0712.3457).
