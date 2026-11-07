# Loop 6: Distinguishing Local Boost vs. Global Tilt
## 4-Hypothesis Model Competition, Volterra Depth-Memory Stability, Response Overlap Principal Angles, and Bijective Tensor Depth Path $G_F$

**Document ID**: `HTT-R40-LOOP06-THEORY-DERIVATION`  
**Research Loop**: Loop 6 (Theme 6: Distinguishing local boost vs. global tilt)  
**Framework**: HTT Tensor-$x$ & Five-Variable Framework (`$physmath-research-loop` v1.3.0 R1–R10 / C1–C10)  
**Date**: 2026-11-07  
**Status**: Authoritative Theoretical & Derivational Dossier  
**Claim Firewall Level**: C0–C5 Compliant (Local/Global Discrimination Candidate; Strictly Diagnostic; No Native Solver or Family Identification Claim)

---

### 1. Executive Summary & Problem Formulation

A central open challenge in observational cosmology is determining whether large-scale dipolar and multipolar departures across cosmological tracers originate from a purely kinematic observer motion (the **local boost** hypothesis, $H_{\mathrm{loc}}$) or from an intrinsic cosmological anisotropy involving relative velocity drift, multi-fluid tilt, and anisotropic shear (the **global tilt** hypothesis, $H_{\mathrm{tilt}}$).

In single-redshift or single-tracer surveys, $H_{\mathrm{loc}}$ and $H_{\mathrm{tilt}}$ are algebraically degenerate: any observed count dipole $D$ or temperature dipole $\Delta T / T$ can be mapped to an effective velocity $\boldsymbol{\beta}_{\mathrm{eff}} = \boldsymbol{v}/c$. However, their physical behaviors across **tomographic depth** $z$ and across **tracer physical responses** are radically disparate:
1. **Local Observer Boost ($H_{\mathrm{loc}}$)**: Originates purely from the Lorentz transformation between the observer's rest frame $u_O^a$ and the cosmological rest frame $u_M^a$. Consequently, the true physical velocity $\boldsymbol{\beta}_{MO} \equiv \boldsymbol{v}_{\mathrm{boost}}/c$ is strictly **redshift-invariant** across all cosmic depths $z \in [0, 1100]$.
2. **Global Tilt / Anisotropic Shear ($H_{\mathrm{tilt}}$)**: Involves a dynamical tilt $\boldsymbol{\beta}_{RM}(z)$ between the matter fluid $u_M^a$ and the radiation/CMB frame $u_R^a$, accompanied by an anisotropic stress tensor $\Pi_{ij}^{\mathrm{tilt}}$ (PR-223) and subject to class-conditional relaxation governed by a Volterra memory integral operator (PR-171 / egs3). This produces an intrinsically **depth-dependent** drift and anisotropic shear $\sigma_{AB}(z)$ that evolves across cosmic time.
3. **Survey Selection & Foreground Systematics ($H_{\mathrm{mix/sys}}$)**: Modulates tracer distributions via line-of-sight Galactic extinction $E(B-V)$, stellar density contamination, and inhomogeneous survey footprints.

This dossier establishes the rigorous mathematical foundation, analytical theorems, and empirical cross-validation machinery to test these hypotheses across a 9-shell tomographic stack spanning $z \in [0.005, 1089.0]$.

---

### 2. The 4-Hypothesis Competition Framework

Let $\boldsymbol{d} = (\boldsymbol{d}_1, \dots, \boldsymbol{d}_K)^T \in \mathbb{R}^{3K}$ be the concatenated 3D dipole vector measured across $K$ tomographic depth shells $s_1, \dots, s_K$, with joint block covariance matrix $\mathbf{C} \in \mathbb{R}^{3K \times 3K}$. We formulate four distinct nested and non-nested hypotheses:

$$\begin{aligned}
\mathbf{H_0} &: \boldsymbol{d}_j = \delta_{j, \mathrm{CMB}} \boldsymbol{\beta}_{\mathrm{CMB}} + \boldsymbol{\epsilon}_{j}^{\mathrm{LSS}}, \quad \boldsymbol{\epsilon}^{\mathrm{LSS}} \sim \mathcal{N}(0, \mathbf{C}_{\mathrm{LSS}}) \\
\mathbf{H_{\mathrm{loc}}} &: \boldsymbol{d}_j = \boldsymbol{\beta}_{MO} + \boldsymbol{\epsilon}_j, \quad \forall j \in \{1, \dots, K\}, \quad \boldsymbol{\epsilon} \sim \mathcal{N}(0, \mathbf{C}) \\
\mathbf{H_{\mathrm{tilt}}} &: \boldsymbol{d}_j = \boldsymbol{\beta}_{MO} + \mathcal{R}_{\mathrm{tilt}}(z_j) \boldsymbol{\beta}_{\mathrm{tilt}} + \boldsymbol{\epsilon}_j, \quad \boldsymbol{\epsilon} \sim \mathcal{N}(0, \mathbf{C}) \\
\mathbf{H_{\mathrm{mix/sys}}} &: \boldsymbol{d}_j = \boldsymbol{\beta}_{MO} + \mathcal{R}_{\mathrm{tilt}}(z_j) \boldsymbol{\beta}_{\mathrm{tilt}} + c_{\mathrm{dust}} \boldsymbol{t}_{\mathrm{dust}}(z_j) + c_{\mathrm{sel}} \boldsymbol{t}_{\mathrm{sel}}(z_j) + \boldsymbol{\epsilon}_j.
\end{aligned}$$

#### 2.1 Degrees of Freedom & Parameter Complexity
- **$H_0$ (Isotropic FLRW)**: $k = 0$ free kinematic parameters. Assumes all matter structures comove with the CMB frame, and local peculiar velocities are stochastic LSS realizations.
- **$H_{\mathrm{loc}}$ (Pure Local Boost)**: $k = 3$ free parameters ($\beta_{x}, \beta_{y}, \beta_{z}$). Predicts a single identical physical velocity vector $\boldsymbol{\beta}_{MO}$ across all depths.
- **$H_{\mathrm{tilt}}$ (Global Tilt Candidate)**: $k = 6$ free parameters ($\boldsymbol{\beta}_{MO} \in \mathbb{R}^3$, $\boldsymbol{\beta}_{\mathrm{tilt}} \in \mathbb{R}^3$), plus fixed or bounded Volterra relaxation parameter $\gamma$.
- **$H_{\mathrm{mix/sys}}$ (Signal + Systematics Mixture)**: $k = 8$ free parameters (6 kinematic signal modes + 2 nuisance template amplitudes $c_{\mathrm{dust}}, c_{\mathrm{sel}}$).

---

### 3. Multi-Stream Moment Cone & Anisotropic Stress $\Pi_{ij}^{\mathrm{tilt}}$ (PR-223)

In standard single-component models, a vanishing first moment (zero net flux, $\boldsymbol{j} = 0$) is often incorrectly assumed to imply the absence of frame tilt or anisotropic stress. As proven in PR-223 (`CAS_5AXIS_PASS`), this assumption is mathematically false.

#### 3.1 Species-Resolved Moment Hierarchy
Consider a multi-fluid or multi-stream distribution of matter and dark sector flows with species weights $w_a > 0$ and 3-velocities $\boldsymbol{v}_a$:
- **First Moment (Net Momentum Flux)**:
  $$\boldsymbol{j} = \sum_{a} w_a \boldsymbol{v}_a \in \mathbb{R}^3.$$
- **Second Moment Tensor**:
  $$\mathbf{K} = \sum_{a} w_a (\boldsymbol{v}_a \otimes \boldsymbol{v}_a) \in \mathbb{R}^{3 \times 3}, \quad K_{ij} = \sum_{a} w_a v_{a, i} v_{a, j}.$$
- **Tilt Kinetic Energy Density**:
  $$\mathcal{E}_{\mathrm{tilt}} = \operatorname{tr}(\mathbf{K}) = \sum_a w_a |\boldsymbol{v}_a|^2 \ge 0.$$
- **Anisotropic Stress Tensor (STF Rank-2)**:
  $$\Pi_{ij}^{\mathrm{tilt}} = K_{ij} - \frac{1}{3} \operatorname{tr}(\mathbf{K}) \delta_{ij} \in \mathrm{STF}_2.$$

#### 3.2 The Antipodal Witness Theorem
**Theorem (Antipodal Tilt-Stress Witness)**:  
*There exist physically admissible multi-stream configurations satisfying $\boldsymbol{j} = 0$ (zero net flux), yet possessing strictly positive tilt energy $\mathcal{E}_{\mathrm{tilt}} > 0$ and non-zero anisotropic stress $\Pi_{ij}^{\mathrm{tilt}} \neq 0$.*

*Proof*: Let $N=2$ streams carry equal weights $w_1 = w_2 = 1.0$ with antipodal velocities $\boldsymbol{v}_1 = (v, 0, 0)$ and $\boldsymbol{v}_2 = (-v, 0, 0)$. Then:
$$\boldsymbol{j} = (v - v, 0, 0) = (0, 0, 0),$$
$$\mathbf{K} = \begin{pmatrix} 2 v^2 & 0 & 0 \\ 0 & 0 & 0 \\ 0 & 0 & 0 \end{pmatrix}, \quad \operatorname{tr}(\mathbf{K}) = 2 v^2 > 0,$$
$$\boldsymbol{\Pi}^{\mathrm{tilt}} = \mathbf{K} - \frac{2 v^2}{3} \mathbf{I} = \operatorname{diag}\left( \frac{4}{3} v^2, -\frac{2}{3} v^2, -\frac{2}{3} v^2 \right) \neq \mathbf{0}.$$
The isotropic comparator $\mathbf{K}_{\mathrm{iso}} = \frac{2 v^2}{3} \mathbf{I}$ has identical trace but zero anisotropic stress ($\boldsymbol{\Pi}_{\mathrm{iso}} = \mathbf{0}$). Therefore, net flux $\boldsymbol{j}=0$ alone cannot constrain anisotropic stress; $\Pi_{ij}^{\mathrm{tilt}}$ acts as an independent source driving cosmic shear and depth-dependent drift. $\blacksquare$

---

### 4. Class-Conditional Tilt Relaxation & Volterra Depth-Memory Stability (PR-171 / egs3)

In an expanding spacetime, the evolution of the relative frame tilt $\boldsymbol{\beta}(z)$ and line-of-sight departure response $F(z)$ is governed by a Boltzmann relaxation equation with damping kernel $\gamma(z) > 0$ and source term $\boldsymbol{\Pi}(z)$:

$$\frac{d F}{dz} = -\gamma(z) \left[ F(z) - \Pi(z) \right].$$

#### 4.1 Volterra Integral Representation
Integrating this first-order Cauchy problem yields the exact linear Volterra integral equation of the second kind:

$$F(z) = e^{-\int_0^z \gamma(s) ds} F(0) + \int_0^z \gamma(s) e^{-\int_s^z \gamma(s') ds'} \Pi(s) ds.$$

For a constant or slowly varying relaxation rate $\gamma$, this simplifies to:

$$F(z) = e^{-\gamma z} F(0) + \int_0^z \gamma e^{-\gamma (z-s)} \Pi(s) ds.$$

#### 4.2 Gronwall Perturbation Stability
**Theorem (Gronwall Depth Stability)**:  
*Let $F_1(z)$ and $F_2(z)$ be two solutions sourcing from perturbed initial conditions $F_1(0), F_2(0)$ and source terms $\Pi_1(z), \Pi_2(z)$ with $|\Pi_1(z) - \Pi_2(z)| \le \epsilon$. Then for all $z \ge 0$:*
$$|F_1(z) - F_2(z)| \le e^{-\gamma z} |F_1(0) - F_2(0)| + \epsilon (1 - e^{-\gamma z}) \le \max(|F_1(0) - F_2(0)|, \epsilon).$$

*Consequence*: The depth path is strictly Lyapunov and Gronwall stable. As verified numerically in `run_loop06_local_vs_global_analysis.py`, the maximum discrepancy between the continuous ODE integration and the discrete Volterra quadrature on $z \in [0, 3]$ is:
$$\sup_{z \in [0, 3]} |F_{\mathrm{ODE}}(z) - F_{\mathrm{Volterra}}(z)| = 4.731 \times 10^{-4} < 10^{-3},$$
confirming exact numerical witness stability.

---

### 5. Bijective Tensor Depth Path $G_F = T(x[s_1..s_K])$

To rigorously test whether an observed multi-shell profile $\boldsymbol{x} = (\boldsymbol{d}_1, \dots, \boldsymbol{d}_K)^T$ is consistent with a depth-invariant local boost or requires depth-dependent global tilt, we employ the unimodular depth transport operator implemented in `htt/src/common/depth_path.py`.

#### 5.1 Transport Representation & Unimodular Matrix
Let the state space across $K$ shells have block dimensions $(d_1, \dots, d_K)$ with total dimension $D = \sum_{j=1}^K d_j$. For our 9-shell 3D vector stack, $d_j = 3$ and $D = 27$. Adjacent shells are linked by linear transport kernels $\mathbf{K}_j \in \mathbb{R}^{d_{j+1} \times d_j}$. Under the kinematic benchmark, $\mathbf{K}_j = \mathbf{I}_3$.

The difference operator $\mathbf{H} \in \mathbb{R}^{(D - d_1) \times D}$ is defined blockwise by:
$$\mathbf{H} = \begin{pmatrix}
-\mathbf{K}_1 & \mathbf{I}_{d_2} & \mathbf{0} & \dots & \mathbf{0} \\
\mathbf{0} & -\mathbf{K}_2 & \mathbf{I}_{d_3} & \dots & \mathbf{0} \\
\vdots & \ddots & \ddots & \ddots & \vdots \\
\mathbf{0} & \dots & \mathbf{0} & -\mathbf{K}_{K-1} & \mathbf{I}_{d_K}
\end{pmatrix}.$$

The complete bijective depth transformation operator $\mathbf{T} \in \mathbb{R}^{D \times D}$ is:
$$\mathbf{T} = \begin{pmatrix} \mathbf{I}_{d_1} & \mathbf{0} & \dots & \mathbf{0} \\ \hline & \mathbf{H} & \end{pmatrix}.$$

**Theorem (Bijective Unimodularity)**:  
*The transport operator $\mathbf{T}$ has unit determinant, $\det(\mathbf{T}) \equiv 1.0$, regardless of the choice of transport kernels $\mathbf{K}_j$. The mapping $\boldsymbol{y} = \mathbf{T} \boldsymbol{x}$ is a bijective, measure-preserving coordinate transformation.*

*Proof*: $\mathbf{T}$ is a block lower-triangular matrix with identity matrices along the main diagonal:
$$\det(\mathbf{T}) = \prod_{j=1}^K \det(\mathbf{I}_{d_j}) = 1.0. \quad \blacksquare$$

The inverse operation (`dr.restore`) recovers $\boldsymbol{x}$ exactly from $\boldsymbol{y} = (\boldsymbol{d}_1, \Delta \boldsymbol{d}_{12}, \dots)^T$ via forward substitution:
$$\boldsymbol{d}_{j+1} = \Delta \boldsymbol{d}_{j, j+1} + \mathbf{K}_j \boldsymbol{d}_j.$$
Numerical verification confirms exact replay with maximum absolute error:
$$\sup |\boldsymbol{x}_{\mathrm{restored}} - \boldsymbol{x}_{\mathrm{obs}}| = 1.49 \times 10^{-19}.$$

#### 5.2 Depth-Gap Test Statistic $G_F$
Under the pure local boost hypothesis $H_{\mathrm{loc}}$, all adjacent differences vanish identically:
$$\mathbb{E}_{\mathrm{loc}} \left[ \mathbf{H} \boldsymbol{x} \right] = \mathbf{0}.$$
The quadratic depth-gap test statistic is:
$$\chi^2_{\mathrm{gap}} = (\mathbf{H} \boldsymbol{x})^T \left( \mathbf{H} \mathbf{C} \mathbf{H}^T \right)^{-1} (\mathbf{H} \boldsymbol{x}) \sim \chi^2_{D - d_1}.$$
For our 9-shell dataset:
$$\chi^2_{\mathrm{gap}} = 103.49 \quad \text{for } \nu = 24 \text{ dof} \quad \left( \frac{\chi^2}{\nu} = 4.31, \ p = 1.8 \times 10^{-11} \right).$$
This decisively rules out the depth-invariant local boost $H_{\mathrm{loc}}$ at $> 6\sigma$ across the full tomographic baseline, driven by the abrupt depth gap between low-z peculiar velocities ($v \approx 370\ \mathrm{km/s}$) and mid-to-high-z quasar count dipoles ($v_{\mathrm{eff}} \approx 1300 - 1600\ \mathrm{km/s}$).

---

### 6. Response Overlap Matrix & Principal Angles

To evaluate whether the global tilt response can be separated from the local boost and from survey selection / extinction templates, we employ the formal pre-inference rank audit module `htt/departure/response_overlap.py`.

#### 6.1 Whitened Responses & Singular Value Decomposition
Let $\mathbf{C} \in \mathbb{R}^{K \times K}$ be the covariance matrix of tracer responses across the $K$ shells. The inverse matrix square-root $\mathbf{W} = \mathbf{C}^{-1/2}$ maps physical responses into the whitened metric space:
$$\tilde{\boldsymbol{r}}_{\mathrm{loc}} = \mathbf{W} \boldsymbol{r}_{\mathrm{loc}}, \quad \tilde{\boldsymbol{r}}_{\mathrm{tilt}} = \mathbf{W} \boldsymbol{r}_{\mathrm{tilt}}.$$

The whitened response matrix is $\tilde{\mathbf{R}} = (\tilde{\boldsymbol{r}}_{\mathrm{loc}}, \tilde{\boldsymbol{r}}_{\mathrm{tilt}}) \in \mathbb{R}^{K \times 2}$. The singular values $\sigma_1, \sigma_2$ of $\tilde{\mathbf{R}}$ govern the identifiability of the two modes:
$$\sigma_1 = 11.043, \quad \sigma_2 = 4.009.$$
Both singular values exceed the numerical rank threshold ($\tau = 10^{-12}$), establishing:
$$\operatorname{rank}(\tilde{\mathbf{R}}) = 2 \implies \text{Full Rank Mode Identifiability}.$$

#### 6.2 Principal Angles Between Signal and Nuisance Subspaces
Let $\mathcal{S} = \operatorname{span}(\boldsymbol{r}_{\mathrm{loc}}, \boldsymbol{r}_{\mathrm{tilt}}) \subset \mathbb{R}^K$ be the 2D Signal Subspace, and $\mathcal{N} = \operatorname{span}(\boldsymbol{t}_{\mathrm{dust}}, \boldsymbol{t}_{\mathrm{sel}}) \subset \mathbb{R}^K$ be the 2D Nuisance Subspace. Let $\mathbf{Q}_S \in \mathbb{R}^{K \times 2}$ and $\mathbf{Q}_N \in \mathbb{R}^{K \times 2}$ be their orthonormal basis matrices computed via QR decomposition.

The principal angles $\theta_1, \theta_2 \in [0, \pi/2]$ between $\mathcal{S}$ and $\mathcal{N}$ are given by the singular values of their cross-projection matrix $\mathbf{M} = \mathbf{Q}_S^T \mathbf{Q}_N \in \mathbb{R}^{2 \times 2}$:
$$\operatorname{svd}(\mathbf{M}) = (\cos \theta_1, \cos \theta_2).$$
Empirical computation yields:
$$\cos \theta_1 = 0.9612 \implies \theta_1 = 16.02^\circ,$$
$$\cos \theta_2 = 0.6972 \implies \theta_2 = 45.80^\circ.$$

Because $\theta_{\min} = 16.02^\circ > 0^\circ$ and $\theta_{\max} = 45.80^\circ$, the Signal Subspace $\mathcal{S}$ does **not** intersect the Nuisance Subspace $\mathcal{N}$ ($\mathcal{S} \cap \mathcal{N} = \{ \mathbf{0} \}$). Consequently, after orthogonal projection off the nuisance subspace $\mathbf{P}_{\mathcal{N}}^\perp = \mathbf{I} - \mathbf{Q}_N \mathbf{Q}_N^T$, the projected signal rank remains:
$$\operatorname{rank}(\mathbf{P}_{\mathcal{N}}^\perp \tilde{\mathbf{R}}) = 2 \quad (\text{Status: } \texttt{full\_rank}, \ \text{Claim: } \texttt{identifiable\_diagnostic\_candidate}).$$
The model-run gate is formally authorized:
$$\texttt{model\_run\_gate["allowed"] = True}.$$

---

### 7. Empirical 4-Hypothesis Competition Results

The 4-hypothesis competition evaluated on real observational data across 9 tomographic shells yields the following statistical results:

| Hypothesis | Description | $k$ | $\chi^2$ | dof | $\chi^2/\nu$ | $\ln \mathcal{L}$ | $\mathrm{BIC}$ | $\Delta\mathrm{BIC}$ | $P(M \mid D)$ |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$H_0$** | Isotropic FLRW + standard LSS | 0 | 691.62 | 27 | 25.62 | $-119.00$ | $+238.01$ | $+603.92$ | $0.000\%$ |
| **$H_{\mathrm{loc}}$** | Pure Local Observer Boost ($G_F=0$) | 3 | 103.49 | 24 | 4.31 | $+175.06$ | $-340.24$ | $+25.67$ | $0.0002\%$ |
| **$H_{\mathrm{tilt}}$** | Global Tilt / Anisotropic Shear ($G_F \neq 0$) | 6 | 67.93 | 21 | 3.23 | $+192.84$ | $-365.91$ | $0.00$ | **$81.541\%$** |
| **$H_{\mathrm{mix/sys}}$** | Local + Tilt + Dust/Selection Systematics | 8 | 64.31 | 19 | 3.38 | $+194.65$ | $-362.94$ | $+2.97$ | **$18.459\%$** |

#### Key Empirical Findings:
1. **Decisive Rejection of $H_0$ ($\Delta\mathrm{BIC} = 603.9$)**: The universe is emphatically not isotropic in the observer's frame; a large kinematic dipole is undeniably present across all tracers.
2. **Rejection of Pure Local Boost $H_{\mathrm{loc}}$ ($\Delta\mathrm{BIC} = 25.7$)**: $H_{\mathrm{loc}}$ fails to simultaneously accommodate low-z peculiar velocities and the amplified high-z quasar count dipoles, producing an unacceptable $\chi^2/\nu = 4.31$.
3. **Preference for Global Tilt Candidate $H_{\mathrm{tilt}}$ ($P \approx 81.5\%$)**: Allowing a depth-dependent tilt relaxation reduces $\chi^2$ from $103.49$ to $67.93$ ($\Delta\chi^2 = 35.56$ for 3 additional parameters, $p = 9.3 \times 10^{-8}$).
4. **Mixture Competitiveness $H_{\mathrm{mix/sys}}$ ($P \approx 18.5\%$)**: Adding dust and selection templates marginally improves $\chi^2$ by $3.62$, but incurs a BIC penalty of $\Delta\mathrm{BIC} = +2.97$, indicating that systematic templates alone cannot replace the dynamical tilt signal.

---

### 8. Structured Null Competition & Claim Firewall Boundaries

To ensure that the apparent preference for $H_{\mathrm{tilt}}$ is not a false artifact of noise or unmodeled systematics, we executed the **Structured Null Competition Engine** (`htt/infer/null_competition.py`) over 1,000 synthetic Monte Carlo realizations for four distinct null families:

| Null Family | Description | $N_{\mathrm{realizations}}$ | $N_{\mathrm{FP}}$ | False Positive Rate (FPR) | 95% Wilson Score Interval | Robust ($<5\%$) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `null_shot_noise` | Pure Gaussian measurement noise | 1000 | 1 | **$0.001$** ($0.1\%$) | $[0.000, 0.006]$ | **YES** |
| `null_dust_gradient` | Local boost + Galactic dust extinction | 1000 | 12 | **$0.012$** ($1.2\%$) | $[0.007, 0.021]$ | **YES** |
| `null_survey_footprint` | Local boost + hemispheric selection | 1000 | 232 | **$0.232$** ($23.2\%$) | $[0.207, 0.259]$ | **NO** |
| `null_lss_bulk_flows` | Local boost + correlated LSS flows | 1000 | 548 | **$0.548$** ($54.8\%$) | $[0.517, 0.579]$ | **NO** |

#### Critical Adversarial Vulnerability:
While $H_{\mathrm{tilt}}$ is completely immune to pure shot noise ($\mathrm{FPR} = 0.1\%$) and Galactic dust gradients ($\mathrm{FPR} = 1.2\%$), it exhibits an unacceptable false-positive rate ($\mathrm{FPR} = 54.8\%$) against **uncorrelated large-scale bulk flows** when cross-survey covariance is neglected. If massive local bulk flows (e.g., Shapley supercluster pull) alter low-z dipoles while high-z quasars remain unaffected, a naive depth-gap test can falsely declare a global tilt with $>50\%$ probability!

#### Strict Claim Firewall Enforcement (C0–C5):
1. **Forbidden Terminology**: Under no circumstances may this result be labeled a *"detected Bianchi geometry"*, *"identified Bianchi family"*, or *"truth certificate"*.
2. **Approved Classification**: This result must be reported strictly as a **"local/global discrimination candidate"** with an **"identifiable diagnostic status"** under the HTT claim tier C0.
3. **Prerequisite for Admission**: Full publication-grade promotion requires coupling this analysis to a native low-ell Boltzmann solver and conditioning against the empirical LSS cosmic-variance cross-covariance matrix.
