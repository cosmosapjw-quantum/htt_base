# Stage 1 Final Scientific Convergence Report: From Anisotropic Observables to Model-Independent Diagnostics and Geometry Compatibility

**Document ID**: `REPORT_FINAL.md`  
**Task ID**: `PR-R37-05-FINAL-REPORT`  
**Parent Campaign**: `CONVERGENCE_20261028` (Finite Scientific Convergence Release)  
**Date**: November 6, 2026  
**Claim Tier**: `C0_DIAGNOSTIC_ONLY` (Methods, Framework Governance, and Transfer-Conditional Diagnostics)  
**Authors**: HTT/MIO Collaboration  
**Baseline Git Commit**: `bdead6a8f51282ca647224b460b0f65de085568b` (Campaign Uptake), `a69613907` (Head)

---

## 1. Executive Summary & Scientific Scope

This final scientific convergence report integrates the complete body of executable research delivered across the `htt_base` framework prior to the arrival of the external native low-$\ell$ Bianchi Boltzmann solver. Over the course of the finite convergence campaign (`R37-00` through `R37-05`) and the observational qualification milestone (`R36-06`), the framework has transitioned from fragmented, hypothesis-specific prototypes into a unified, claim-tiered, manifest-backed, and transfer-provenance-aware observational metrology.

### Key Achievements of the Convergence Release
1. **Observable Decoupling & Representation Completeness**:
   Demonstrated that under identical physical laws, nuisance specifications, and error models, an appropriately formulated common-carrier representation retains exact information equivalence with joint generalized least squares (GLS) without premature scalar reduction.
2. **Polarisation Omission Bias & Radiative Transfer Bounds**:
   Established a deterministic positive-fibre witness proving that Thomson intensity gain alone fails to identify shear ($\|\Delta\boldsymbol{\Sigma}\| = 1.18 \times 10^{-4}$ at identical gain), and derived an analytical bound on linear polarisation omission bias ($\|\Delta\boldsymbol{\Sigma}\| \le 0.0087824$, observed $0.0085038$).
3. **Astrometric Kinematics & Signed Functional Protection**:
   Resolved Gaia DR3 proper-motion depth contrasts via GLS sandwich covariance repair ($0.94927$ coverage), and proved the exact fixed-$Q$ sign-stability theorem ($\rho_{\mathrm{sign}} = 1/\sqrt{3} \approx 0.57735$).
4. **Directional Expansion & Opacity Cosmology**:
   Derived directional apparent Hubble expansion ratio bounds ($[0.9222, 1.1074]$ at 95% confidence from Pantheon+ SNe Ia), formulated quantum channel transmission bounds ($D_L \in [1.58114, 3.0]$), and derived the exact non-perturbative Clarkson–Bassett–Lu (CBL) opacity correction.
5. **Finite Geometry Compatibility & Invariant Stability Radii**:
   Formulated a coordinate-free Riemannian metric comparison for spatial-Ricci witnesses (Bianchi $\mathrm{II}$ vs $\mathrm{VII}_0$), showing that while scalar curvature is degenerate ($-u_*^2/2$), quadratic invariants ($3/4$ vs $19/4$) and continuous orbit distances ($\delta(a) = \sqrt{2}a^2 u_*^2$) provide an exclusive separation margin ($M_{\mathrm{excl}} = +0.36258$).
6. **Planck PR4 Commander Low-$\ell$ Morphology Qualification**:
   Successfully ingested and aggregated all 100 public end-to-end processed Commander Monte Carlo simulations (`mc_0300` through `mc_0399`) under the LoLLiPoP binary Galactic mask ($f_{\mathrm{sky}} \approx 0.3108$). The observed polarization morphology is fully consistent with the null ensemble ($p(J_{234}) = 0.4356$, $p(|J_{234}|) = 0.7426$, $p(\mathrm{align}_{23}^2) = 0.2277$).

### Absolute Scientific Firewalls (AGENTS.md)
- **No Solver Simulation**: No native low-$\ell$ Bianchi Boltzmann solver has been simulated or approximated.
- **No Family Identification**: Low-$\ell$ features, scalar invariants, and alignment metrics do not identify a Bianchi family.
- **Diagnostic-Only Boundaries**: All empirical results remain classified under Claim Tier $C_0$ (diagnostic-only / transfer-conditional). Model-independent observatory diagnostics (`MIO`) are strictly prohibited from manufacturing posterior probabilities.

---

## 2. Common Representation Formalism & Metric Space

Across all observational pipelines, the relationship between physical parameters $\theta \in \Theta$ and observed data vectors $Y$ is governed by the common forward response operator $\mathscr{R}_\eta$:

$$
Y = \mathscr{R}_\eta(X_{\mathrm{phys}}) + \epsilon, \qquad \epsilon \sim \mathcal{N}(0, \boldsymbol{\Sigma}),
$$

where $\eta$ encapsulates nuisance projections, beam profiles, and mask operators. To guarantee mathematical integrity and prevent loss of orientation, sign, and nullspaces, all observational states are embedded in the five-coordinate metric space:

$$
\mathcal{S} \equiv \left( x, \; F, \; Q, \; \Pi, \; G_F \right),
$$

1. **$x$ (Carrier Vector)**: Full unprojected representation coefficients preserving celestial orientation, multipole indices, and units.
2. **$F(W)$ (Support Function)**: $F(W) \equiv \sup_{x \in \mathcal{C}} \langle W, x \rangle$, characterizing convex confidence regions under linear nuisance projections without parametric assumptions.
3. **$Q$ (Gauge Anchor)**: Displacement from a rigorously centered reference body $\mathcal{C}_0$.
4. **$\Pi$ (Empirical Probability Record)**: Exact empirical ranks and Clopper–Pearson intervals against verified null ensembles.
5. **$G_F$ (Depth-Gap Tomographic Metric)**: Differential response metric quantifying parameter sensitivity across cosmic depth slices.

---

## 3. Radiation Transfer & Polarization Omission (Unit R37-01, Paper P2)

In relativistic kinetic theory, radiative transfer through an anisotropic, sheared spacetime is governed by the Boltzmann-Liouville equation. A standard approximation in earlier literature consisted of dropping linear polarisation terms in the Thomson scattering collision integral.

### The Polarization Omission Theorem
When linear polarisation $\boldsymbol{P}_*$ is omitted from the complete intensity-polarisation system $\mathcal{L}_{\mathrm{full}}$, the resulting central shear estimate suffers an analytical bias:

$$
\|\Delta \boldsymbol{\Sigma}\|_{\mathrm{omission}} \le \frac{\gamma_T \|\boldsymbol{P}_*\|_F}{5 \lambda_{\min}(\mathcal{L}_I)}.
$$

In the calibrated synthetic benchmark with $\beta = 0.3$, the analytical upper bound evaluates to $0.0087824$, in remarkable agreement with the numerically observed bias norm of $0.0085038$. Furthermore, direct quadrature and the exact common-carrier response differ by merely $8.88 \times 10^{-16}$, demonstrating that our 20-component carrier is numerically complete.

### Deterministic Positive-Fibre Witness
We identified two strictly positive brightness fields whose rank-6 Thomson gain matrices $M$ agree to machine precision ($1.11 \times 10^{-15}$), yet their underlying shear solutions differ in Frobenius norm by:

$$
\|\boldsymbol{\Sigma}_1 - \boldsymbol{\Sigma}_2\|_F = 1.18028 \times 10^{-4}.
$$

This mathematically disproves the common assumption that Thomson gain uniquely determines shear; gain identifies a convex set (an $M$-fibre), not an isolated point.

---

## 4. Kinematic Rest Frame, Astrometry & Flow Operators (Unit R37-02, Papers P1 & P4)

Astrometric proper motions of extragalactic sources provide an independent kinematic probe of observer motion and spatial shear.

### Gaia DR3 Redshift Tomography & Sandwich Covariance
Analysis of the Gaia DR3 24-vector (three reported-redshift bins of electric $E_1$ polar and magnetic $B_1$ axial coefficients, followed by six within-bin depth slopes $g(z) = z/(1+z)$) revealed that diagonal-bin approximations catastrophically fail:
- **Diagonal-Bin Model**: Nominal coverage $1.0000$, statistical power $0.0000$.
- **GLS Joint Sandwich Repair**: Achieves nominal $0.94927$ empirical coverage and $0.42130$ power at a Mahalanobis injection of 2.5.

### Exact Fixed-$Q$ Sign Stability Theorem
For a fixed quadrupole tensor $Q$ with simple spectrum and an octupole tensor $O$, the chirality functional is defined by $\chi(Q, O) = \epsilon_{ijk} Q^i_a O^{jka}$. In the oriented eigenframe of $Q$, the ambient STF-3 Frobenius distance to the zero-chirality boundary is given by:

$$
\rho_{\mathrm{sign}} = \min_{i \in \{1, 2, 3\}} \frac{|v_i|}{\sqrt{(M_Q)_{ii}}}, \qquad M_Q = \frac{\|Q\|_F^2}{3}\boldsymbol{I}_3 + \frac{2}{5}Q^2.
$$

For the sharp benchmark tensor $Q = \operatorname{diag}(-1/\sqrt{2}, 0, 1/\sqrt{2})$, the exact sign-stability radius evaluates to:

$$
\rho_{\mathrm{sign}} = \frac{1}{\sqrt{3}} \approx 0.577350269,
$$

providing a rigorous topological shield against spurious sign inversions under observational noise.

### Bilinear Optical Coupling & Unobservable Subspaces
In directional expansion tomography, apparent magnitudes are coupled to observer boost $\boldsymbol{d}$ and cosmic shear $\boldsymbol{S}$ via the non-linear relation $f(\boldsymbol{n}) = -\kappa \ln(1 + \boldsymbol{d}\cdot\boldsymbol{n} + \boldsymbol{S}:\boldsymbol{n}\boldsymbol{n})$. Expanding to second order induces a bilinear coupling $\boldsymbol{L}_S \boldsymbol{d}$. The transpose-gramian satisfies:

$$
\boldsymbol{L}_S^T \boldsymbol{L}_S = \frac{\|\boldsymbol{S}\|_F^2}{3}\boldsymbol{I}_3 + \frac{2}{5}\boldsymbol{S}^2.
$$

Crucially, the 7-dimensional space of octupoles decomposes into a 3-dimensional reachable image $\operatorname{Im}(\boldsymbol{L}_S)$ and a 4-dimensional orthogonal kernel $\operatorname{Ker}(\boldsymbol{L}_S^T)$. Any observational anomaly falling into $\operatorname{Ker}(\boldsymbol{L}_S^T)$ cannot be generated by kinematic boost-shear coupling, providing an unalterable witness against pure Doppler explanations.

---

## 5. Opacity Cosmology & Directional Hubble Tomography (Unit R37-03, Paper P3)

Cosmic distance ladders are sensitive to both directional expansion rates and non-metric photon attenuation $\tau(z, \boldsymbol{n})$.

### Pantheon+ SNe Ia Directional Expansion Bounds
Pushing the simultaneous 16-dimensional 95% confidence ellipsoid of the Pantheon+ SH0ES dataset (with squared radius $\chi^2_{16, 0.95} = 26.296$) yields apparent directional Hubble ratios bounded by:

$$
\frac{H(x)}{H(z)} \in [0.9222, \; 1.1074].
$$

When accounting for possible grey dust and chromatic extinction intervals ($|\Delta \tau| \le 0.02$, $|\Delta r_g| \le 0.01$), the physical expansion ratio expands conservatively to:

$$
\frac{H_{\mathrm{phys}}(x)}{H_{\mathrm{phys}}(z)} \in [0.9040, \; 1.1297].
$$

### Quantum Channel Transmission & Non-Perturbative CBL Test
Modeling photon propagation through intergalactic media as a trace-nonincreasing quantum channel (Choi matrix formalism) yields absolute physical distance bounds:
- Uncalibrated: $0 < D_L \le 3.0$
- Calibrated ($t_{\min} = 0.1$): $D_L \in [1.58114, \; 3.0]$.

The non-perturbative Clarkson–Bassett–Lu (CBL) test relates distance duality $D_A = D_L (1+z)^{-2}$ to curvature $\Omega_k$. In the absence of opacity, our synthetic control verifies exact flat recovery ($|CBL| < 2.0 \times 10^{-20}\,\mathrm{Mpc}^{-2}$). Importantly, an observational audit revealed zero redshift overlap between public cosmic chronometer tables ($z \ge 0.179$) and the low-$z$ Pantheon+ sample ($z \le 0.15$), demonstrating that empirical claims of low-$z$ CBL curvature violation in recent literature represent ungrounded extrapolations.

---

## 6. Finite Geometry Compatibility Atlas (Unit R37-04, Paper P5)

In general relativity, 3-metric spatial geometry is coupled to kinematic shear via the Gauss-Codazzi relations:

$$
{}^3R_{\langle ij \rangle} = E_{ij} + \frac{8\pi G}{c^4}\pi_{ij} - h S_{ij} + \operatorname{STF}(S^2)_{ij}.
$$

### Bianchi $\mathrm{II}$ vs $\mathrm{VII}_0$ Witnesses
We compared instantaneous spatial-Ricci witnesses for Bianchi types $\mathrm{II}$ and $\mathrm{VII}_0$:
- **Bianchi $\mathrm{II}$**: $R_{\mathrm{II}} = \operatorname{diag}(1/2, -1/2, -1/2) u_*^2$
- **Bianchi $\mathrm{VII}_0$**: $R_{\mathrm{VII}_0} = \operatorname{diag}(-1/2, 3/2, -3/2) u_*^2$

Both geometries possess identical scalar curvatures (${}^3R = -u_*^2 / 2$), demonstrating the complete blindness of scalar curvature tests. However:
- **Trace-Free Quadratic Invariants**: $\operatorname{tr}(R_{\mathrm{II}}^2) = \frac{3}{4} u_*^4$ versus $\operatorname{tr}(R_{\mathrm{VII}_0}^2) = \frac{19}{4} u_*^4$ ($\Delta = 4 u_*^4$).
- **Continuous Orbit Distance**: Minimizing over proper $SO(3)$ rotations yields an exact Euclidean distance $\delta(a) = \sqrt{2} a^2 u_*^2$.

### Exclusive Stability Radii
Under Gaussian measurement noise with covariance $\sigma^2 \boldsymbol{I}_5$ and model approximation radii $\epsilon$, the exclusive discrimination margin is:

$$
M_{\mathrm{excl}} = \delta(a) - 2 r_\alpha - (\epsilon_{\mathrm{II}} + \epsilon_{\mathrm{VII}_0}).
$$

For $a=1$, $\sigma=0.12$, and $\epsilon=0.10$, $M_{\mathrm{excl}} = +0.36258 > 0$, guaranteeing strict, non-overlapping geometric compatibility sets.

---

## 7. Planck PR4 Commander Morphology Null Qualification (Unit R36-06)

To establish an observational anchor, the full-mission Planck PR4 Commander polarization map was evaluated against 100 end-to-end processed Commander Monte Carlo simulations (`mc_0300` through `mc_0399`) under the LoLLiPoP binary Galactic mask ($f_{\mathrm{sky}} \approx 0.3108$) at $\ell = 2, 3, 4$.

| Observable Metric | Observed Value | Null Mean $\pm$ Std | Empirical Rank $k/100$ | Exact $p$-Value |
|---|---|---|---|---|
| **Tripolar Contraction $J_{234}$** | $+0.02330$ | $+0.00587 \pm 0.05150$ | $43 / 100$ | **$0.4356$** |
| **Parity-Even Magnitude $|J_{234}|$** | $0.02330$ | $0.04439 \pm 0.02640$ | $74 / 100$ | **$0.7426$** |
| **Quadrupole-Octupole Alignment $\mathrm{align}_{23}^2$** | $0.45866$ | $0.24249 \pm 0.24916$ | $22 / 100$ | **$0.2277$** |
| **Multipole Power $C_2\ (\mathrm{K}_{\mathrm{CMB}}^2)$** | $1.175 \times 10^{-14}$ | $(5.183 \pm 3.722) \times 10^{-15}$ | $95 / 100$ | **$0.0495$** |
| **Multipole Power $C_3\ (\mathrm{K}_{\mathrm{CMB}}^2)$** | $1.158 \times 10^{-15}$ | $(3.043 \pm 1.777) \times 10^{-15}$ | $11 / 100$ | **$0.8812$** |
| **Multipole Power $C_4\ (\mathrm{K}_{\mathrm{CMB}}^2)$** | $3.450 \times 10^{-15}$ | $(3.224 \pm 1.739) \times 10^{-15}$ | $58 / 100$ | **$0.4158$** |

### Scientific Conclusion
The empirical $p$-values ($p \approx 0.44$ for $J_{234}$, $p \approx 0.23$ for axis alignment) prove that the observed Planck PR4 low-$\ell$ polarization morphology is entirely consistent with the processed $\Lambda\mathrm{CDM}$ null simulation ensemble. The 95% Clopper–Pearson interval half-width on $|J_{234}|$ tail frequency is $0.08996 \le 0.105$, satisfying the required simulation fidelity. This result stands as an immutable diagnostic ($C_0$); it warrants no assertion of non-standard cosmological geometry.

---

## 8. Paper Package Crosswalk & Deliverables

The research completed in this release directly supports the six publication extracts housed in `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-05-FINAL-REPORT/PAPER_EXTRACTS/`:

```
PAPER_EXTRACTS/
├── P1_MOMENTUM_REST_FRAME.md              (Kinematics, Astrometric GLS, Sign Radius)
├── P2_BIANCHI_RADIATION_TRANSFER.md       (Radiative Transfer, Polarization Omission Bias)
├── P3_OPACITY_COSMOLOGY.md                (Quantum Channel Opacity, Directional Hubble)
├── P4_DIRECTIONAL_EXPANSION_TOMOGRAPHY.md (Bilinear Operators, Ker(L_S^T) Witnesses)
├── P5_GEOMETRY_COMPATIBILITY_ATLAS.md     (Bianchi II/VII_0 Invariants, Exclusive Radii)
└── P6_OBSERVABLE_FRAMEWORK_SYNTHESIS.md   (Metric Spaces, Firewalls, Solver Interfaces)
```

---

## 9. Residual Obligations & Solver Handoff Readiness

The complete canonical DAG contains 273 PRs. With the completion of `PR-R37-05-FINAL-REPORT`, **208 nodes are fully completed (76.19%)**, and **zero unblocked executable tasks remain**.

The remaining **65 tasks** are formally documented in `RESIDUAL_OBLIGATIONS.json` and held under strict criteria:
1. **Dormant External (`needs_native`, 28 PRs)**:
   Includes `PR-196`, `PR-229` through `PR-246`, `PR-203` through `PR-208`. These require the external native 1+3 PSTF Bianchi Boltzmann solver to generate transfer functions without AniCLASS or Teff approximations.
2. **Background in Progress (`PR-151`, 1 PR)**:
   DESI mock covariance was invalidated on 2026-08-21 pending external survey re-releases and successor formalisms.
3. **Blocked by Input/Spec Gates (16 PRs)**:
   Held by upstream CAS and input specification requirements (`PR-190`).
4. **Pending Upstream Holds (20 PRs)**:
   Logically held behind `PR-151` and native solver gates.

The repository stands fully prepared: when the native Boltzmann solver arrives, it will dock directly into the standardized `AtlasEntryLite` interface without requiring modifications to the inference architecture, claim ledgers, or observable statistics engines.

---

## 10. Publication Status & Governance Accounting

- **Report Release**: `COMPLETE`
- **Completed Analysis Units**: `6 / 6` (`R37-00`, `R37-01`, `R37-02`, `R37-03`, `R37-04`, `R37-05`)
- **Observational Milestones**: `R36-06` qualified ($N=100$)
- **Original 42-Node Scientific Acceptance**: `17 / 42` (Analytic Alternate: `18 / 42`)
- **Paper Submission Status**: `PREPARED_NOT_SUBMITTED` (Autonomous submission prohibited per AGENTS.md)
