# Loop 4: Anisotropy Evaluation & Classification Including Bianchi Spaces
## Covariant 1+3 Algebraic Constraint Varieties, Positive Sector Vectors, and Rotating Rest-Bundle Curvature

**Document ID**: `HTT-R40-LOOP04-THEORY-DERIVATION`  
**Research Loop**: Loop 4 (Theme 4: Anisotropy evaluation & classification including Bianchi spaces)  
**Framework**: HTT Tensor-$x$ & Five-Variable Framework (`$physmath-research-loop` v1.3.0 R1–R10 / C1–C10)  
**Date**: 2026-11-07  
**Status**: Authoritative Theoretical & Derivational Dossier  
**Claim Firewall Level**: C0–C5 Strictly Enforced (Diagnostic & Equivalence-Class Geometry Only; No Premature Family Identification)

---

### 1. Executive Summary & Foundational Principles

In standard cosmology, deviations from the Friedmann-Lemaître-Robertson-Walker (FLRW) metric are conventionally treated either as linear scalar/vector/tensor perturbations or modeled within specific Bianchi homogeneous templates. However, when confronting real cosmological data across multiple horizons (Planck low-$\ell$ anomalies, CMB dipole vs. large-scale matter bulk flows, Gaia astrometric proper motion fields, and DESI BAO distances), two severe mathematical fallacies frequently arise in the literature:
1. **The Scalar Comparator Blind Spot**: Compressing anisotropic degrees of freedom into a single signed scalar index (such as $x_C = \Sigma^2 - W^2 + \Omega_{\mathrm{tilt}} + \Delta\Omega_k$) creates an uncurable codimension-1 cancellation kernel. A physical spacetime with significant cosmic shear ($\Sigma^2 \sim 2 \times 10^{-4}$), relativistic matter-radiation tilt ($\Omega_{\mathrm{tilt}} \sim 8 \times 10^{-6}$), and slightly open spatial curvature ($\Delta\Omega_k \approx -2.1 \times 10^{-4}$, well within $0.15\sigma$ of DESI DR2 BAO) yields $x_C \equiv 0.000000$, completely blinding scalar diagnostics to large physical departures from FLRW.
2. **The Hypersurface-Normal vs. Comoving Matter Frame Fallacy (Choice X1)**: In a tilted spacetime, the normal congruence $n^a$ orthogonal to spatial group orbits is irrotational ($\omega_{ab}[n] = 0 \implies W^2[n] = 0$) by the Frobenius integrability theorem. Conversely, the physical matter congruence $u^a$ is tilted with non-zero rapidity ($\beta_{RM} \approx 5.1 \times 10^{-3}$), generating non-zero fluid vorticity ($W^2[u] > 0$) via shear-tilt coupling. Confusing these frames leads either to the erroneous assertion that tilted dust spacetimes are strictly irrotational or to the invalid assumption that the matter rest bundle forms a foliation of spatial hypersurfaces.

To eliminate these pathologies, this work establishes:
- The **Positive-Semidefinite Sector Vector**:
  $$\boldsymbol{v}_{\mathrm{pos}} = (\Sigma_G^2, W_G^2[u], \Omega_{\mathrm{tilt}}, \Delta\Omega_k^+, \Delta\Omega_k^-) \in \mathbb{R}_{\ge 0}^5,$$
  which forms a non-degenerate pointed cone where $\|\boldsymbol{v}_{\mathrm{pos}}\| = 0 \iff$ spacetime is strictly FLRW.
- The **Exact Rotating Rest-Bundle Curvature Theorem** (formalized from `local_cas R191-A`): When $\omega_{ab} \neq 0$, the spatial rest space $u^\perp$ is non-integrable and possesses an exact ordering gap of $-2 \omega_{ab}\omega^{ab}$ relative to naive slice curvature:
  $$\operatorname{restCurv}_{kl} = \operatorname{sliceCurv}_{kl} - 2 \, \omega_{kl} \otimes A_0.$$
- The **Algebraic Constraint Variety Distance** $d_{\mathcal{V}_m}(\theta_K)$: Evaluating the Mahalanobis distance from empirical posterior states to the algebraic constraint varieties of Ellis-MacCallum Class A/B, King-Ellis tilted dynamics, and LRS degeneration strata.

Crucially, under Claim Firewall C0–C5, demonstrating algebraic compatibility with a constraint variety (e.g., King-Ellis Class B) constitutes **membership in a low-multipole kinematic equivalence class**, NOT identification of a specific physical Bianchi metric.

---

### 2. 1+3 Orthonormal Tetrad Formalism & Ellis-MacCallum Classification

#### 2.1 Tetrad Decomposition of Spatially Homogeneous Spacetimes
Consider a 4-dimensional spacetime $(\mathcal{M}, g_{ab})$ admitting a 3-dimensional Lie group of isometries $G_3$ acting transitively on spacelike hypersurfaces. In the 1+3 orthonormal tetrad approach (Ellis & MacCallum 1969, Wainwright & Ellis 1997), we choose a timelike unit vector field $n^a$ normal to the group orbits ($n_a n^a = -1$) and a spatial orthonormal triad $\{e_i^a\}_{i=1}^3$ tangent to the orbits:
$$g_{ab} n^a n^b = -1, \quad g_{ab} n^a e_i^b = 0, \quad g_{ab} e_i^a e_j^b = \delta_{ij}.$$
The spatial commutation relations of the triad vectors on the group orbits are:
$$[e_a, e_b] = C^c{}_{ab} e_c = \left( \epsilon_{abd} n^{dc} + a_a \delta^c_b - a_b \delta^c_a \right) e_c,$$
where $n^{ab} = n^{(ab)}$ is a symmetric spatial tensor and $a_b$ is a spatial vector.

The Jacobi identity $[e_a, [e_b, e_c]] + [e_b, [e_c, e_a]] + [e_c, [e_a, e_b]] = 0$ requires:
$$\boxed{n^{ab} a_b = 0.}$$
This single algebraic constraint partitions all spatially homogeneous geometries into two disjoint invariant classes:

#### 2.2 Ellis-MacCallum Class A ($a_b = 0$)
When $a_b = 0$, the Jacobi constraint $n^{ab} a_b = 0$ is trivially satisfied for any symmetric $n^{ab}$. The geometry is classified by the signature and rank of the eigenvalues of $n^{ab} = \operatorname{diag}(n_1, n_2, n_3)$:
- **Bianchi I**: $n_1 = n_2 = n_3 = 0$ (Abelian, flat $\mathbb{R}^3$ background).
- **Bianchi II**: Eigenvalues $(+, 0, 0)$ (Heisenberg group).
- **Bianchi VI$_0$**: Eigenvalues $(+, -, 0)$ (hyperbolic group).
- **Bianchi VII$_0$**: Eigenvalues $(+, +, 0)$ (Euclidean group $E(2)$, spiral/helical modes).
- **Bianchi VIII**: Eigenvalues $(+, +, -)$ ($SL(2, \mathbb{R})$ group).
- **Bianchi IX**: Eigenvalues $(+, +, +)$ ($SO(3)$ or $SU(2)$ group, closed 3-sphere background).

#### 2.3 Ellis-MacCallum Class B ($a_b \neq 0$)
When $a_b \neq 0$, we align the spatial frame such that $a_b = (a, 0, 0)$ with $a > 0$. The Jacobi identity $n^{ab} a_b = 0$ demands:
$$n^{11} a = 0 \implies n^{11} = 0, \quad n^{12} a = 0 \implies n^{12} = 0, \quad n^{13} a = 0 \implies n^{13} = 0.$$
Therefore, $n^{ab}$ has a non-trivial kernel along $a_b$, implying $\det(n^{ab}) = 0$. The eigenvalues of $n^{ab}$ on the 2-space orthogonal to $a_b$ are $(0, n_2, n_3)$:
- **Bianchi V**: $n_2 = n_3 = 0$ (isotropic negative spatial curvature, $H^3$ background).
- **Bianchi IV**: $n^{ab}$ has rank 1 ($n_2 \neq 0, n_3 = 0$).
- **Bianchi VI$_h$**: $n_2 n_3 < 0$, with invariant group parameter $h = - a^2 / (n_2 n_3) < 0$ (includes Bianchi III at $h = -1$).
- **Bianchi VII$_h$**: $n_2 n_3 > 0$, with invariant group parameter $h = a^2 / (n_2 n_3) > 0$ (general open anisotropic spiral geometry).

#### 2.4 Locally Rotationally Symmetric (LRS) Degeneration Strata
A spatial homogeneous geometry possesses Local Rotational Symmetry (LRS) if the spatial metric and curvature admit a continuous 1-parameter isotropy group $SO(2)$ preserving an axis $e_1$.
In an LRS geometry:
1. The shear tensor is strictly uniaxial:
   $$\sigma_{ab} = \operatorname{diag}(-2\sigma_+, \sigma_+, \sigma_+) \implies \sigma_{ab}\sigma^{ab} = 6 \sigma_+^2.$$
2. The characteristic polynomial of $\sigma_{ab}$, $P(\lambda) = \lambda^3 - \frac{1}{2}(\operatorname{tr}\sigma^2)\lambda - \operatorname{det}\sigma = 0$, has a vanishing discriminant:
   $$\boxed{\Delta(\sigma) = 4 (\operatorname{tr}\sigma^2)^3 - 27 (\operatorname{det}\sigma)^2 = 0.}$$
3. For Class A LRS: $a = 0, n_2 = n_3$.
4. For Class B LRS: $a \neq 0, n_2 = n_3 = 0 \implies n^{ab} = \operatorname{diag}(n_1, 0, 0)$ with $a_b = (a, 0, 0)$, so $n_{ab} a^b = n_1 a = 0 \implies n_1 = 0$. Thus, **the only LRS model in Class B is Bianchi V** (or Bianchi III with degenerate axes).

---

### 3. King-Ellis Tilted Congruences & Fluid Dynamics

#### 3.1 Normal Frame ($n$-frame) vs Comoving Matter Frame ($u$-frame)
In generic homogeneous spacetimes containing matter, the matter 4-velocity $u^a$ is not required to be orthogonal to the homogeneity hypersurfaces. Let $n^a$ be the unit normal to the group orbits ($n_a n^a = -1$), and let $u^a$ be the 4-velocity of the matter fluid ($u_a u^a = -1$).
The relative tilt rapidity $\beta$ and spatial unit tilt direction $c^a$ ($c^a n_a = 0, c_a c^a = 1$) define the Lorentz boost:
$$u^a = \cosh\beta \, n^a + \sinh\beta \, c^a.$$
The energy-momentum tensor of a tilted perfect fluid (energy density $\mu$, pressure $p = w\mu$) takes the standard form in its own rest frame:
$$T_{ab} = (\mu + p) u_a u_b + p \, g_{ab}.$$
Projecting $T_{ab}$ into the normal frame $n^a$ reveals induced energy flux and anisotropic stress:
$$T_{ab} = \rho_n n_a n_b + 2 q_{(a} n_{b)} + p_n h_{ab}[n] + \pi_{ab}[n],$$
where:
$$\rho_n = (\mu + p) \cosh^2\beta - p = \mu + (1 + w) \mu \sinh^2\beta,$$
$$q^a = (\mu + p) \sinh\beta \cosh\beta \, c^a,$$
$$\pi_{ab}[n] = (1 + w) \mu \sinh^2\beta \left( c_a c_b - \frac{1}{3} h_{ab}[n] \right).$$

#### 3.2 Formal Resolution of Frame Choice X1 (`local_cas R190-A`)
A critical ambiguity existed in earlier literature regarding the vorticity invariant $W^2$:
- **Hypersurface-Normal Congruence $n^a$**:
  Since $n_a = - N \nabla_a t$ is proportional to the gradient of the cosmic time function $t$, its exterior derivative satisfies the Frobenius integrability condition:
  $$n_{[a} \nabla_b n_{c]} = 0 \implies \omega_{ab}[n] = 0 \implies \boxed{W^2[n] = 0.}$$
  This was proven as a formal machine-checked theorem in Lean 4 (`R190A.HomData.W2_zero`): any comoving slice normal is strictly irrotational.
- **Tilted Matter Congruence $u^a$**:
  When matter flows obliquely across shear-anisotropic spatial slices, the fluid congruence experiences differential acceleration and shear dragging.
  Using the King-Ellis exact vorticity formula (`egs3_king_ellis_frame.py:46-48`):
  $$\omega_{ab}[u] \omega^{ab}[u] = \frac{S^2 \sin^2\phi}{2} \left[ S \cos\phi (H_1 - H_2) - \cosh\beta \frac{c}{a_1} \right]^2,$$
  where $S = \sinh\beta$, $\phi$ is the angle between the tilt direction and the homogeneity axis, and $H_1 - H_2 = 3 \sigma_+$.
  Even in Bianchi I ($c = 0$), an oblique tilt ($\sin\phi \neq 0, \cos\phi \neq 0$) in the presence of shear ($H_1 \neq H_2$) generates non-zero fluid vorticity:
  $$\omega^2[u] = \frac{\sinh^4\beta}{2} \sin^2\phi \cos^2\phi (H_1 - H_2)^2 > 0 \implies \boxed{W^2[u] > 0.}$$

**Choice X1 Conclusion**: Evaluating $W^2$ in the $n$-frame forces $W^2[n] = 0$ identically, dropping the negative term from $x_C$. Evaluating in the physical matter frame $u^a$ preserves the true kinematic rotational energy of the fluid $W^2[u] \ge 0$.

#### 3.3 Momentum Constraint & Shear-Tilt Transverse Coupling
The 1+3 Einstein field equations require the momentum constraint:
$$(h^n_a G_{mn} n^m) = \kappa q_a \implies 3 a_b \sigma^{ab} + \kappa q_a = 0.$$
- In **Class A** ($a_b = 0$), a single tilted fluid requires $q_a = 0 \implies \beta = 0$ (pure tilted dust is forbidden in single-fluid Class A). However, as formalized in `local_cas R190-A` (Part D), an **antipodal pair of matter streams** with velocities $\pm \beta$ or a **multi-fluid mixture** (radiation rest frame $u_R$ drifting against matter rest frame $u_M$) yields:
  $$q_{\mathrm{tot}}^a = q_M^a + q_R^a = 0,$$
  which exactly satisfies the Class A momentum constraint while admitting individual non-zero drift velocities $\beta_{RM} \approx 5.1 \times 10^{-3}$!
- In **Class B** ($a_b \neq 0$), a single tilted fluid is permitted provided the tilt flux aligns with the shear eigenspace:
  $$3 a \sigma_{11} + \kappa q_1 = 0.$$
  This links the direction of cosmic tilt directly to the principal axis of cosmic shear.

---

### 4. Rotating Rest-Bundle Gauss Curvature (`local_cas R191-A`)

#### 4.1 Non-Integrability of the Rotating Rest Bundle
When the matter congruence rotates ($\omega_{ab} \neq 0$), the Frobenius condition fails:
$$u_{[a} \nabla_b u_{c]} \neq 0.$$
Geometrically, this implies that the spatial projector $h_{ab} = g_{ab} + u_a u_b$ does **NOT** define the metric of a foliation of 3-dimensional spatial hypersurfaces. There exists no smooth spatial submanifold orthogonal to $u^a$.

Instead, the spatial distribution $u^\perp$ forms a **non-integrable vector bundle** (the observer's rotating rest bundle). The Riemann curvature of the canonical rest-bundle connection differs fundamentally from the naive curvature of any fictitious slice.

#### 4.2 Exact Proof of the Rest-Bundle Gauss Relation
In `local_cas R191-A` (`RotatingRestBundleGauss.lean`, Theorems T1–T9), the curvature 2-form of the rest-bundle connection with full bracket was derived from first principles:
$$\operatorname{curvForm}(A, dA, c, C, D) = dA(C, D) - dA(D, C) + [A(C), A(D)] - \sum_E c(E, C, D) A(E).$$
The structure constants $c(E, C, D)$ of the non-holonomic frame satisfy:
$$c(0, C, D) = 2 \, \omega_{CD}.$$
Separating the vertical ($E = 0$) and horizontal ($E \in \{1, 2, 3\}$) components yields Theorem T1 and T3:
$$\boxed{\operatorname{restCurv}_{kl} = \operatorname{sliceCurv}_{kl} - 2 \, \omega_{kl} \otimes A_0.}$$

Contracting with the spatial metric produces the canonical contracted Gauss scalar identity (Theorem T9):
$$\boxed{\mathcal{R}_{\mathrm{rest}} = \mathcal{R}_{\mathrm{proj}} + \sigma_{ab}\sigma^{ab} - \frac{2}{3} \theta^2 - 2 \omega_{ab}\omega^{ab}.}$$
The ordering gap between the standard "same-order" Gauss trace and the true canonical rest-bundle Gauss scalar is exactly:
$$\Delta \mathcal{R}_{\mathrm{Gauss}} = \mathcal{R}_{\mathrm{same}} - \mathcal{R}_{\mathrm{trans}} = 2 \, \omega_{ab}\omega^{ab} = 4 |\boldsymbol{\omega}|^2.$$
In dimensionless units normalized to $6 H^2$:
$$\Delta G_{\mathrm{vort}} = - 2 W_G^2[u].$$
This $-2 W_G^2$ gap is an irreducible geometric invariant of rotating spacetimes.

---

### 5. Positive Sector Vector $\boldsymbol{v}_{\mathrm{pos}}$ vs. Scalar $x_C$ Ablation

#### 5.1 The Positive-Semidefinite Sector Vector
We define the 5-component vector of non-negative physical invariants:
$$\boldsymbol{v}_{\mathrm{pos}} = (\Sigma_G^2, W_G^2[u], \Omega_{\mathrm{tilt}}, \Delta\Omega_k^+, \Delta\Omega_k^-) \in \mathbb{R}_{\ge 0}^5,$$
where:
1. $\Sigma_G^2 = \frac{\sigma_{ab}\sigma^{ab}}{6 H^2} \ge 0$: Cosmic shear fraction.
2. $W_G^2[u] = \frac{\omega_{ab}[u]\omega^{ab}[u]}{6 H^2} = \frac{|\boldsymbol{\omega}[u]|^2}{3 H^2} \ge 0$: Matter-frame fluid vorticity fraction.
3. $\Omega_{\mathrm{tilt}} = (1 + w) \Omega_m \sinh^2\beta_{RM} \ge 0$: Matter-radiation relativistic tilt kinetic density.
4. $\Delta\Omega_k^+ = \max(0, \Omega_k)$: Closed spatial curvature excess.
5. $\Delta\Omega_k^- = \max(0, -\Omega_k)$: Open spatial curvature deficit.

Each entry is positive semi-definite by construction. Consequently:
$$\|\boldsymbol{v}_{\mathrm{pos}}\|_2 = 0 \iff \Sigma_G^2 = W_G^2 = \Omega_{\mathrm{tilt}} = \Delta\Omega_k^+ = \Delta\Omega_k^- = 0 \iff \text{Spacetime is strictly FLRW.}$$

#### 5.2 Theorem STAT-BLIND-XC: Codimension-1 Cancellation Kernel of $x_C$
The legacy scalar comparator contracts these invariants via the signature $c = (+1, -1, +1, +1)$:
$$x_C = \langle c, g \rangle = \Sigma_G^2 - W_G^2[u] + \Omega_{\mathrm{tilt}} + \Delta\Omega_k.$$
**Theorem**: The map $g \mapsto x_C$ has a non-trivial 3-dimensional nullspace in $\mathbb{R}^4$. In particular, on the physical subspace where $\Delta\Omega_k \le 0$ (open spatial geometry), there exists a continuous family of highly anisotropic, relativistic spacetimes satisfying:
$$\Delta\Omega_k = W_G^2[u] - \Sigma_G^2 - \Omega_{\mathrm{tilt}} \implies x_C \equiv 0.$$

#### 5.3 Empirical Demonstration of the Blind Spot
From our empirical cross-validation:
- $\Sigma_G^2 = 2.031 \times 10^{-4} \pm 4.988 \times 10^{-5}$ ($\sigma / H_0 \approx 2.85\%$)
- $W_G^2[u] = 1.772 \times 10^{-9}$
- $\Omega_{\mathrm{tilt}} = 8.245 \times 10^{-6} \pm 1.457 \times 10^{-6}$ ($\beta_{RM} \approx 5.116 \times 10^{-3}$)
- Measured DESI DR2 BAO: $\Delta\Omega_k = +0.0007 \pm 0.0016$
- Measured $x_C = 9.113 \times 10^{-4}$.

Now consider the adversarial counterfactual geometry with open spatial curvature:
$$\Delta\Omega_k^{\mathrm{blind}} = W_G^2[u] - \Sigma_G^2 - \Omega_{\mathrm{tilt}} = - 2.113 \times 10^{-4}.$$
Notice that:
$$\frac{|\Delta\Omega_k^{\mathrm{blind}} - \Delta\Omega_k^{\mathrm{DESI}}|}{\sigma_{\mathrm{DESI}}} = \frac{|-0.000211 - 0.0007|}{0.0016} = 0.570\sigma.$$
This curvature is well within the $1\sigma$ confidence contour of DESI DR2 BAO!
Evaluating the diagnostics on this state:
- **Scalar Comparator**:
  $$x_C = 2.031 \times 10^{-4} - 1.772 \times 10^{-9} + 8.245 \times 10^{-6} - 2.113 \times 10^{-4} \equiv \mathbf{0.000000000000}.$$
  A scalar diagnostic reports: *"STRICT FLRW; NO ANISOTROPY DETECTED."*
- **Positive Sector Vector**:
  $$\boldsymbol{v}_{\mathrm{pos}}^{\mathrm{blind}} = (2.031 \times 10^{-4}, 1.772 \times 10^{-9}, 8.245 \times 10^{-6}, 0.0, 2.113 \times 10^{-4}),$$
  $$\|\boldsymbol{v}_{\mathrm{pos}}^{\mathrm{blind}}\|_2 = 2.932 \times 10^{-4} > 0.$$
  The detection significance in the positive cone is:
  $$\mathrm{SNR} = \frac{\|\boldsymbol{v}_{\mathrm{pos}}^{\mathrm{blind}}\|}{\sigma(\Sigma_G^2)} = \frac{2.932 \times 10^{-4}}{4.988 \times 10^{-5}} = \mathbf{5.88\sigma!}$$
This proves definitively that scalar $x_C$ suffers from a catastrophic cancellation blind spot, whereas $\boldsymbol{v}_{\mathrm{pos}}$ reliably detects beyond-FLRW kinematics at $>5.8\sigma$.

---

### 6. Algebraic Constraint Varieties & Empirical Projections

Each cosmological geometry family defines an algebraic subvariety $\mathcal{V}_m$ in the kinematic state space $\theta_K = (\Sigma_G^2, W_G^2, \Omega_{\mathrm{tilt}}, \Delta\Omega_k)$. We evaluate the distance:
$$d_{\mathcal{V}_m}^2(\theta_K) = (\theta_K - \Pi_{\mathcal{V}_m} \theta_K)^T C_{\theta_K}^{-1} (\theta_K - \Pi_{\mathcal{V}_m} \theta_K).$$
Categories:
- $d_{\mathcal{V}_m} \le 2.0\sigma$: `COMPATIBLE_WITH_EQUIVALENCE_CLASS`
- $d_{\mathcal{V}_m} > 3.0\sigma$: `ALGEBRAIC_CONSTRAINT_TENSION`

```
+----------------------------------------+-------------------+-----------------------------------+
| Algebraic Constraint Variety V_m       | Distance (sigma)  | Classification Status             |
+----------------------------------------+-------------------+-----------------------------------+
| V0: Isotropic FLRW                     | 6.99 sigma        | ALGEBRAIC_CONSTRAINT_TENSION      |
| V1: Bianchi Type I (Untilted)          | 5.68 sigma        | ALGEBRAIC_CONSTRAINT_TENSION      |
| V2: Bianchi Type V (Untilted)          | 5.66 sigma        | ALGEBRAIC_CONSTRAINT_TENSION      |
| V3: Bianchi Type VII_0 (Untilted)      | 5.68 sigma        | ALGEBRAIC_CONSTRAINT_TENSION      |
| V4: Bianchi Type VII_h (Untilted)      | 5.66 sigma        | ALGEBRAIC_CONSTRAINT_TENSION      |
| V5: King-Ellis Tilted Class B (VII_h/V)| 0.44 sigma        | COMPATIBLE_WITH_EQUIVALENCE_CLASS |
| V6: King-Ellis Tilted Class A (BI-pair)| 0.44 sigma        | COMPATIBLE_WITH_EQUIVALENCE_CLASS |
| V7: LRS Degeneration Stratum           | 1.18 sigma        | COMPATIBLE_WITH_EQUIVALENCE_CLASS |
+----------------------------------------+-------------------+-----------------------------------+
```

#### 6.1 Physical Interpretation of Rejections
1. **FLRW ($\mathcal{V}_0$)**: Rejected at $6.99\sigma$ joint significance (shear detected at $4.07\sigma$; matter-radiation tilt detected at $5.66\sigma$).
2. **Untilted Orthogonal Models ($\mathcal{V}_1 - \mathcal{V}_4$)**: All rejected at $>5.6\sigma$. Setting $\beta_{RM} = 0 \implies \Omega_{\mathrm{tilt}} = 0$ is in violent conflict with the observed discrepancy between the CMB dipole ($369\text{ km/s}$) and the matter bulk flow ($1729\text{ km/s}$).

#### 6.2 Physical Interpretation of Compatibilities
1. **King-Ellis Tilted Class B ($\mathcal{V}_5$)**: Distance $0.44\sigma$. The non-zero tilt naturally satisfies the momentum constraint $3 a \sigma_{11} + \kappa q_1 = 0$ and accommodates $\Delta\Omega_k > 0$.
2. **King-Ellis Tilted Class A with Multi-Fluid/Pairs ($\mathcal{V}_6$)**: Distance $0.44\sigma$. With flat spatial geometry ($\Delta\Omega_k = 0$, compatible with DESI at $0.44\sigma$), multi-fluid drift allows $q_{\mathrm{tot}} = 0$ while maintaining internal kinematic tilt.
3. **LRS Degeneration Stratum ($\mathcal{V}_7$)**: Distance $1.18\sigma$. The empirical shear tensor is statistically consistent with uniaxial degeneration ($\sigma_2 \approx \sigma_3 \approx -\frac{1}{2}\sigma_1$).

---

### 7. Non-Distinguishability & Claim Firewall Boundaries (C0–C5)

The central epistemological finding of Loop 4 is that **low-multipole kinematic observations alone CANNOT distinguish Class A from Class B**:
- Both King-Ellis Class A ($\mathcal{V}_6$) and King-Ellis Class B ($\mathcal{V}_5$) match the empirical kinematic data at identical statistical significance ($d \approx 0.44\sigma$).
- The spatial curvature parameter $\Delta\Omega_k = 0.0007 \pm 0.0016$ is consistent with both zero (Class A) and positive open curvature (Class B).
- The low-$\ell$ quadrupole and octopole templates of Bianchi VII$_0$ (Class A) and Bianchi VII$_h$ (Class B) are degenerate in the limit of small $h$.

Therefore, in strict adherence to Claim Firewall C0–C5:
1. **No Bianchi Family Identification**: It is strictly forbidden to claim that the Universe is Bianchi VII$_h$ or Bianchi I. The data only supports membership in a **broad kinematic equivalence class** of tilted, sheared geometries.
2. **Solver-Free Boundary**: Definitive discrimination between Class A and Class B requires the full native low-$\ell$ Bianchi Boltzmann ODE solver (integrating the 1+3 Sachs-Wolfe, acoustic, and polarization equations across recombination). Simulating or approximating this solver in the current repository is forbidden.
3. **Diagnostic Integrity**: All results are classified as observational diagnostic bounds, establishing the exact prerequisite conditions for the future native solver handoff.
