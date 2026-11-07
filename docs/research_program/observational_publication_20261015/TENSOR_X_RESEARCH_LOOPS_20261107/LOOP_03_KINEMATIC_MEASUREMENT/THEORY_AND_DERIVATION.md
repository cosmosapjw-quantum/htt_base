# Loop 3: Beyond-FLRW Kinematic Quantity Measurement
## Covariant 1+3 Non-Geodesic Kinematic Derivation, Ported local_cas Theorems, and Fiber Identifiability

**Document ID**: `HTT-R40-LOOP03-THEORY-DERIVATION`  
**Research Loop**: Loop 3 (Theme 3: Beyond-FLRW kinematic quantity measurement)  
**Framework**: HTT Tensor-$x$ & Five-Variable Framework (`$physmath-research-loop` v1.3.0 R1–R10 / C1–C10)  
**Date**: 2026-11-07  
**Status**: Authoritative Theoretical & Derivational Dossier  
**Claim Firewall Level**: C0–C5 Compliant (Diagnostic & Bounded Fiber Certificates; No Premature Family Identification)

---

### 1. Executive Summary & Mathematical Foundations

In standard cosmology, deviations from isotropic Hubble expansion are commonly modeled under the **geodesic dust** assumption ($A^a = 0$) and treated either as an isotropic velocity boost $\boldsymbol{v}$ or a small perturbation to FLRW. However, in generic Lorentzian spacetimes admitting anisotropic geometry or non-geodesic observer/emitter congruence flows:
1. The **complete kinematic state** consists of rank-irreducible representations of the local observer rotation group $O(3)$:
   $$\theta_K = (\sigma_{AB}, \omega_A, A_A, \beta_{RM,A}, \beta_{MO,A}) \in 0^+ \oplus 1^+ \oplus 1^- \oplus 2^+.$$
2. The **optical mapping from null geodesics to observer observables** at reception event $p$ produces directional intercepts $Z(n)$ and directional expansion slopes $H(n) = c \left.\frac{\partial z}{\partial d_A}\right|_{0, n}$, which completely determine the observer-to-emitter four-velocity $u^a$ and the symmetric rate-of-strain tensor $B_{ab} = \nabla_{(a} U_{b)}$ via the exact non-geodesic lift (Theorem OPT02):
   $$B = S + S(u, u) g, \quad A_a = 2 c B_{ab} u^b = 2 c b_a.$$
3. Vorticity $\omega_A$ ($1^+$ axial pseudovector) is **strictly unobservable** from scalar distance-redshift slopes $H(n)$ (Theorem OPT03). Its measurement requires celestial proper motions (Gaia DR3 astrometry), where it enters the magnetic dipole ($B_1$) Vector Spherical Harmonic (VSH) mode. However, in astrometric frames, physical cosmic vorticity $\omega_A$ is exactly collinear with and algebraically degenerate with the Celestial Reference Frame (CRF) triad spin $\Omega_{\mathrm{triad}, A}$. Without non-optical gyro-anchoring, $\omega_A$ cannot be identified as an isolated detection and must be bounded as a fiber quotient gauge.
4. When cosmic shear $\sigma_{AB}$ is non-zero, the conventional isotropic velocity inversion $\beta_{\mathrm{iso}} = - \frac{h_1}{2 h_0}$ is mathematically invalid and incurs a severe systematic velocity bias $\Delta \beta = \beta_{\mathrm{exact}} - \beta_{\mathrm{iso}}$. The exact, non-truncated velocity inversion is given by the matrix operator (Theorem OPT09):
   $$\beta_{O/U} = - \frac{1}{2} (h_0 I + h_2)^{-1} h_1 + \mathcal{O}(|\beta|^2).$$
5. Diagnostic scalar summaries based purely on separate-sector powers $\mathcal{P} = (\gamma^2, |v|^2, m^2, |p|^2, \operatorname{tr}T^2)$ suffer from a complete degenerate alias between geodesic ($A=0$) and highly accelerated ($A \neq 0$) physical states (Theorem STAT-INFO-1 and STAT-INFO-3). Complete identifiability requires preserving the directional cross-sector contraction diagnostic $J_{\mathrm{geo}} = \frac{A_a A^a}{4 c^2} \ge 0$ (Theorem STAT-INFO-2) and evaluating the Fisher matrix whitened by the exact STF Gram metric $G_{\mathrm{STF5}}$.

---

### 2. Full 1+3 Non-Geodesic Covariant Kinematic Decomposition

#### 2.1 Spacetime Geometry & Congruence 1+3 Splitting
Let $(\mathcal{M}, g_{ab})$ be a smooth, 4-dimensional Lorentzian spacetime with metric signature $(-, +, +, +)$. Consider a future-directed, timelike fluid four-velocity $U^a = c u^a$, with unit normalization:
$$g_{ab} u^a u^b = -1.$$
The spatial projection tensor orthogonal to $u^a$ is:
$$h_{ab} = g_{ab} + u_a u_b, \quad h^a{}_c h^c{}_b = h^a{}_b, \quad h_{ab} u^b = 0.$$
The full covariant derivative of $U_a$ is decomposed into its irreducible kinematic parts:
$$\nabla_a U_b = \frac{1}{3} \theta h_{ab} + \sigma_{ab} + W_{ab} - \frac{1}{c^2} U_a A_b,$$
where:
- **Trace Expansion Rate**: $\theta = \nabla_a U^a = h^{ab} \nabla_a U_b$ ($0^+$ scalar, units $\mathrm{s}^{-1}$);
- **Symmetric Trace-Free Shear Tensor**: $\sigma_{ab} = \left( h_{(a}{}^c h_{b)}{}^d - \frac{1}{3} h_{ab} h^{cd} \right) \nabla_c U_d$ ($2^+$ symmetric trace-free, $\sigma_{ab} u^b = 0$, $\sigma^a{}_a = 0$);
- **Antisymmetric Vorticity Tensor**: $W_{ab} = h_{[a}{}^c h_{b]}{}^d \nabla_c U_d$ ($1^+$ antisymmetric, $W_{ab} u^b = 0$);
- **Four-Acceleration Vector**: $A_b = U^a \nabla_a U_b = c^2 u^a \nabla_a u_b$ ($1^-$ polar vector, $A_b u^b = 0$, units $\mathrm{m}\,\mathrm{s}^{-2}$).

In the observer rest frame, the vorticity vector is dual to $W_{ab}$:
$$\omega^a = \frac{1}{2} \epsilon^{abcd} u_b W_{cd}, \quad W_{ab} = \epsilon_{abcd} \omega^c u^d.$$

#### 2.2 Relative Drifts in the Multi-Fluid Sector
In a beyond-FLRW cosmological environment, multiple matter and radiation components need not share a common four-velocity:
1. **Matter Rest Frame $u_M^a$**: Frame defining the baryonic and cold dark matter rest system.
2. **Radiation Rest Frame $u_R^a$**: Frame in which the CMB dipole vanishes ($\int T^4 n^i d\Omega = 0$).
3. **Observer Frame $o^a$**: The physical laboratory frame of the observer (e.g. Solar System Barycenter).
The relative drift velocities are defined by:
$$\beta_{RM}^a = \frac{h_M^a{}_b u_R^b}{- u_M \cdot u_R}, \quad \beta_{MO}^a = \frac{h_M^a{}_b o^b}{- u_M \cdot o}.$$
These belong to the $1^-$ vector irrep and describe the radiation-matter drift (CMB dipole vs matter bulk flow) and matter-observer peculiar velocity.

---

### 3. Ported local_cas Theorems: Optical Lift, Inversion, and Fisher Information

We explicitly port and formalize the uncommitted mathematical proofs from `docs/research_program/gr_statistics_loops_20260930/local_cas/` (contracts CAS-01, CAS-10, modules R192-A and R194-A).

#### 3.1 Theorem OPT02 — Complete Non-Geodesic Optical Lift
Let an observation event $p$ receive null rays along past-directed light rays with affine tangent $K^a = - o^a + n^a$, where $n^a o_a = 0, n_a n^a = 1$.
The observable full-sky data at the vertex $d_A \to 0$ are:
$$Z(n) = \lim_{d_A \downarrow 0} (1 + z(d_A, n)) = u(p) \cdot K(p, n),$$
$$H(n) = c \left. \frac{\partial z}{\partial d_A} \right|_{0, n} = B_{ab} K^a K^b, \quad B_{ab} = \nabla_{(a} U_{b)}.$$
Expanding in spherical harmonics up to degree 2:
$$Z(n) = \zeta_0 + \zeta_i n^i, \quad H(n) = h_0 + h_{1i} n^i + h_{2ij} n^i n^j,$$
where $h_{2ij}$ is symmetric and trace-free.
Construct the four-dimensional symmetric tensor representative $S_{ab}$ in the observer tetrad:
$$S_{00} = h_0, \quad S_{0i} = - \frac{1}{2} h_{1i}, \quad S_{ij} = h_{2ij}.$$
**Theorem (Exact Lift)**:
$$u^\alpha = (\zeta_0, \zeta_i), \quad \text{with } \zeta_0^2 - |\boldsymbol{\zeta}|^2 = 1, \ \zeta_0 \ge 1,$$
$$\boxed{B_{ab} = S_{ab} + S(u, u) g_{ab}.}$$
*Proof*: Since $g(K, K) = 0$, $g_{ab}$ is the unique kernel of the quadratic form $T(K, K) = 0$ for all unit $n$. Normalization requires $U^2 = -c^2 \implies \nabla_a (U_b U^b) = 0 \implies B(u, u) = 0$. Since $g(u, u) = -1$, setting $B = S + \lambda g$ yields $S(u, u) - \lambda = 0 \implies \lambda = S(u, u)$. $\blacksquare$

#### 3.2 Theorem OPT03 — Complete Derivative Fiber and Acceleration
Given $(u, B)$, the vector $b_a = B_{ab} u^b$ satisfies $b \cdot u = 0$.
The full velocity gradient is:
$$\boxed{Q_{ab} \equiv \nabla_a U_b = B_{ab} + b_a u_b - u_a b_b + W_{ab},}$$
where $W_{ab} = - W_{ba}$ and $W_{ab} u^b = 0$.
The physical four-acceleration is:
$$\boxed{A_a = 2 c B_{ab} u^b = 2 c b_a.}$$
The spatial rate of strain is $D_{ab} = h_a{}^c h_b{}^d B_{cd} = B_{ab} + u_a b_b + b_a u_b$, with expansion $\theta = g^{ab} B_{ab}$ and shear $\sigma_{ab} = D_{ab} - \frac{1}{3} \theta h_{ab}$.
*Fiber Invariance*: For any antisymmetric spatial 2-form $W_{ab}$, $W(K, K) = 0$. Thus, **vorticity $W_{ab}$ is completely unobservable from directional redshift and area-distance slope data at an observation event**.

#### 3.3 Theorem OPT09 — Exact Matrix Velocity Inversion
In the geodesic regime ($A_a = 0$), $B u = 0$. In the frame of the observer with relative velocity $\beta_{O/U}$, the boosted slope dipole is:
$$h_{1i} = - 2 D_{ij} \beta_{O/U}^j + \mathcal{O}(|\beta|^2), \quad \text{where } D_{ij} = \frac{1}{3} \theta \delta_{ij} + \sigma_{ij} = h_0 \delta_{ij} + h_{2ij}.$$
**Theorem**: If $D$ is invertible, the exact first-order velocity inverse without expanding in shear is:
$$\boxed{\beta_{O/U} = - \frac{1}{2} D^{-1} h_1 = - \frac{1}{2} (h_0 I + h_2)^{-1} h_1 + \mathcal{O}(|\beta|^2).}$$
The weak-shear expansion $\beta \approx - \frac{1}{2 h_0} (I - \frac{h_2}{h_0}) h_1$ incurs an error of order $\mathcal{O}(\sigma^2 \beta / h_0^2)$, which generates substantial kinematic biases in the presence of realistic large-scale shear.

#### 3.4 Theorems STAT-INFO-1, 2, 3 — Invariant Diagnostic and Information Limits
Consider the separate-sector power summary:
$$\mathcal{P} = (\gamma^2, |v|^2, m^2, |p|^2, \operatorname{tr}T^2).$$
- **STAT-INFO-1 (Exact Geodesic / Accelerated Alias)**:
  Let $u = (5/4, 3/4, 0, 0)$ and $B = H (g + u_\flat \otimes u_\flat)$.
  This has $m = 7H/4$, $p = (15H/8, 0, 0)$, $T = \operatorname{diag}(3H/8, -3H/16, -3H/16)$, and $A = 0$.
  Now rotate the dipole to $p' = (0, 15H/8, 0)$.
  Both configurations have identical separate-sector powers:
  $$\mathcal{P} = \left(\frac{25}{16}, \frac{9}{16}, \frac{49 H^2}{16}, \frac{225 H^2}{64}, \frac{27 H^2}{128}\right).$$
  Yet Tuple 1 has $A = 0$, while Tuple 2 has acceleration norm:
  $$b^2 = \frac{87525}{16384} H^2 \approx 5.342102 H^2 > 0.$$
- **STAT-INFO-2 (Observer Acceleration Fisher Information $J_{\mathrm{geo}}$)**:
  The non-geodesic cross-sector diagnostic is defined by:
  $$\boxed{J_{\mathrm{geo}} = (S u)^T g^{-1} (S u) + (u^T S u)^2 = \frac{A_a A^a}{4 c^2} \ge 0.}$$
  On the mass shell, $J_{\mathrm{geo}} = 0$ if and only if $A_a = 0$.
  In terms of sky components:
  $$q = m \gamma^2 - \gamma \boldsymbol{p} \cdot \boldsymbol{v} + \boldsymbol{v}^\top T \boldsymbol{v}, \quad \boldsymbol{w} = T \boldsymbol{v} + q \boldsymbol{v} - \frac{\gamma}{2} \boldsymbol{p},$$
  $$J_{\mathrm{geo}} = |\boldsymbol{w}|^2 - \frac{(\boldsymbol{v} \cdot \boldsymbol{w})^2}{\gamma^2} = \frac{|\boldsymbol{A}|^2}{4 c^2}.$$
- **STAT-INFO-3 (Loss of Statistical Discriminability)**:
  Under separate-power summaries $\mathcal{P}$, Gaussian probability laws for Tuple 1 and Tuple 2 are identical ($D_{\mathrm{KL}}(\mathcal{P}_1 \parallel \mathcal{P}_2) = 0$), whereas the full-coefficient data vector possesses a positive Kullback-Leibler divergence:
  $$D_{\mathrm{KL}}(\text{Full}) = \frac{225 H^2}{64 \sigma_p^2}.$$
  Summarizing data into separate angular powers incurs a **100% information loss** on non-geodesic acceleration.

---

### 4. Gaia DR3 Proper Motion Vector Spherical Harmonics (VSH)

On the celestial sphere $S^2$, the proper motion field $\boldsymbol{\mu}(\hat{n}) = \mu_{\alpha*} \hat{e}_\phi + \mu_\delta \hat{e}_\theta$ is decomposed into orthogonal Vector Spherical Harmonics:
$$\boldsymbol{\mu}(\hat{n}) = \sum_{\ell=1}^\infty \sum_{m=-\ell}^\ell \left( a_{E, \ell m} \boldsymbol{Y}^E_{\ell m}(\hat{n}) + a_{B, \ell m} \boldsymbol{Y}^B_{\ell m}(\hat{n}) \right),$$
where:
$$\boldsymbol{Y}^E_{\ell m}(\hat{n}) = \frac{1}{\sqrt{\ell(\ell+1)}} \boldsymbol{\nabla}_{\!S^2} Y_{\ell m}(\hat{n}), \quad \boldsymbol{Y}^B_{\ell m}(\hat{n}) = \frac{1}{\sqrt{\ell(\ell+1)}} \hat{n} \times \boldsymbol{\nabla}_{\!S^2} Y_{\ell m}(\hat{n}).$$

#### 4.1 Mode Identification
1. **Electric Dipole $E_1$ ($\ell=1$ Glide / Acceleration)**:
   $$\boldsymbol{\mu}_{E_1}(\hat{n}) = \frac{\boldsymbol{a}_\perp}{c d} = - \hat{n} \times (\hat{n} \times \boldsymbol{g}) = \boldsymbol{\nabla}_{\!S^2} (\boldsymbol{g} \cdot \hat{n}).$$
   - Physical origin: Solar System Barycenter acceleration towards the Galactic Center produces a secular aberration drift $\boldsymbol{g}_{\mathrm{gal}} \sim 5.4\ \mu\text{as/yr}$.
   - Redshift dependence: For pure observer acceleration, $\boldsymbol{g}$ is independent of distance $d$. For true cosmic bulk flow / secular parallax, $\boldsymbol{\mu} \propto 1/d(z)$.
2. **Magnetic Dipole $B_1$ ($\ell=1$ Spin / Vorticity / Triad Rotation)**:
   $$\boldsymbol{\mu}_{B_1}(\hat{n}) = \boldsymbol{\Omega} \times \hat{n}.$$
   - Represents a rigid rotation of the velocity field on the sphere.
   - Degeneracy: $\boldsymbol{\Omega} = \boldsymbol{\Omega}_{\mathrm{triad}} - \boldsymbol{\omega}_{\mathrm{matter}}$.
3. **Electric Quadrupole $E_2$ ($\ell=2$ Shear)**:
   $$\boldsymbol{\mu}_{E_2}(\hat{n}) = \boldsymbol{\nabla}_{\!S^2} (S_{ij} n^i n^j), \quad S_{ij} \in \mathrm{STF}_3.$$
   - Directly maps to the 5 degrees of freedom of the cosmic shear tensor $\sigma_{ij}$.

---

### 5. Gram-Whitened Fisher Matrix and Typefree Fiber Bounds

#### 5.1 STF Rank-2 Gram Metric $G_{\mathrm{STF5}}$
To ensure coordinate-independent, rotation-equivariant inference on the 5-dimensional STF shear space, we map between Cartesian coordinates $v_{\mathrm{cart}} = (S_{xx}, S_{yy}, S_{xy}, S_{xz}, S_{yz})$ (with $S_{zz} = -S_{xx} - S_{yy}$) and the Frobenius inner product:
$$\operatorname{Tr}(S \cdot S) = v_{\mathrm{cart}}^T G_{\mathrm{STF5}} v_{\mathrm{cart}}.$$
From `htt/src/common/stf_metric_bridge.py`:
$$G_{\mathrm{STF5}} = \begin{pmatrix} 2 & 1 & 0 & 0 & 0 \\ 1 & 2 & 0 & 0 & 0 \\ 0 & 0 & 2 & 0 & 0 \\ 0 & 0 & 0 & 2 & 0 \\ 0 & 0 & 0 & 0 & 2 \end{pmatrix}, \quad G_{\mathrm{STF5}}^{-1} = \begin{pmatrix} 2/3 & -1/3 & 0 & 0 & 0 \\ -1/3 & 2/3 & 0 & 0 & 0 \\ 0 & 0 & 1/2 & 0 & 0 \\ 0 & 0 & 0 & 1/2 & 0 \\ 0 & 0 & 0 & 0 & 1/2 \end{pmatrix}.$$
Given the raw Fisher matrix $F_{\mathrm{shear}} = X_{\mathrm{shear}}^T W X_{\mathrm{shear}}$, the **Gram-whitened Fisher matrix** is:
$$\widetilde{F}_{\mathrm{shear}} = G_{\mathrm{STF5}}^{-1/2} F_{\mathrm{shear}} G_{\mathrm{STF5}}^{-1/2}.$$
The eigenvalues of $\widetilde{F}_{\mathrm{shear}}$ yield true physical variances in Frobenius-orthonormal tensor space $\delta \sigma^2 = \operatorname{Tr}(\delta S^2)$.

#### 5.2 Bounded Fiber Sets via `typefree_fibers.py`
In the presence of unobservable or degenerate directions (such as $\boldsymbol{\omega}$ vs $\boldsymbol{\Omega}_{\mathrm{triad}}$), the parameter space cannot be collapsed into an unjustified single point. Instead, we compute:
1. **Quotient Gauge**:
   $$g(v) = \min \{ \|x\| : P x = v \},$$
   via `ellipsoid_quotient_gauge(shape, projection, value)`.
2. **Fiber Image**:
   $$\mathcal{F} = \{ T x : P x = v, \ x^T \Sigma^{-1} x \le R^2 \},$$
   via `ellipsoid_fiber_image(shape, projection, value, target_map)`.
This certifies exact mathematical domain bounds on unobservable parameters without overclaiming.

---

### 6. Claim Firewall Protocols (C0–C5)

- **C0 (Bianchi Family Identification Gate)**: Low-$\ell$ kinematic features ($E_1, B_1, E_2, h_1, h_2$) are purely observer-plane kinematics. They do NOT uniquely identify a Bianchi group structure without a validated native low-$\ell$ Boltzmann solver and global null testing.
- **C1 (Vorticity vs Triad Rotation Marginalization)**: Gaia $B_1$ proper motion measures only the difference $\boldsymbol{\Omega}_{\mathrm{triad}} - \boldsymbol{\omega}$. Reporting an isolated detection of cosmic vorticity without marginalizing over CRF triad spin is strictly prohibited.
- **C2 (Galactic Acceleration Subtraction)**: Gaia $E_1$ glide points towards $(\mathrm{RA}, \mathrm{Dec}) = (267.8^\circ, -18.8^\circ)$ with amplitude $5.44\ \mu\text{as/yr}$, aligning with the Galactic Center. It is an observer kinematic effect, not cosmic acceleration.
- **C3 (Shear Concordance)**: Proper motion shear ($\le 2.64\ \mu\text{as/yr}$) and radial Hubble expansion shear ($\sigma_H / H_0 \approx 2.7\text{--}3.0\%$) are mutually consistent and bounded.
- **C4 (Information Firewall)**: Separate-power summaries lose $J_{\mathrm{geo}}$ and relative orientation; all claim-bearing inference must retain directional tensor Fisher structures.
- **C5 (Bounded Fiber Certificate)**: All unidentifiable degrees of freedom are certified as bounded fibers under `typefree_fibers.py`.
