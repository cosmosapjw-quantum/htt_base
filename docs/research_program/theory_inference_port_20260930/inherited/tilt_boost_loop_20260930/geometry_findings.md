# Tilt, homogeneous normals, and local observer boosts

Status: derived conditional results; literature support identified; independent adjudication and observational implementation not performed by this subtask. Date: 2026-09-30 KST.

## 1. Distinct geometric objects

Take signature (-,+,+,+). Let N, U, O be future physical four-velocities, each with squared norm -c^2. N is normal to a specified family of spacelike homogeneous group orbits; U is a specified material flow; O is the observer at the observation event. Write n=N/c, u=U/c, o=O/c. For a spatial dimensionless vector beta relative to n,

    u = gamma (n + beta), n.beta=0,
    gamma = -u.n = (1-beta^2)^(-1/2).

Non-tilted means U=N on the domain under consideration. Tilted means gamma_UN>1 somewhere on that domain. A local observer boost refers to O differing from a reference velocity at an event. It is not an exclusive third cosmological category: a non-tilted or a tilted spacetime may be observed by a boosted observer.

If o=gamma_O(n+b), then

    gamma_UO = gamma_UN gamma_ON (1-beta.b).

The scalar gamma_UN is unaffected by changing O. Specifying only gamma_UO leaves the two relative velocities with respect to N undetermined. An instantaneous boost also does not specify a congruence's kinematics: differentiation of U=gamma(O+c beta_O) introduces the first derivatives of beta_O and of O. A local boost parameter alone cannot determine theta_U, sigma_U, omega_U or A_U.

Literature definition: King & Ellis (1973), DOI 10.1007/BF01646266; publisher abstract inspected. Sandin (2009), arXiv:0901.0800v1, introduction and section 2 full HTML inspected. These define tilt against the normal to homogeneous hypersurfaces, rather than against the CMB dipole frame.

## 2. A conditional geometric classifier from a curvature clock

Assume an open region admits a G3 acting transitively on spacelike hypersurfaces. Let I be a scalar constructed covariantly from the metric, with nonzero timelike gradient at p. Every Killing generator X tangent to an orbit satisfies X(I)=0. Consequently grad I spans the one-dimensional timelike orthogonal complement to the orbit. Choosing the future sign fixes

    n^a = +/- grad^a I / sqrt(-grad I.grad I).

Thus the normal is intrinsically determined even if there are multiple transitive subgroups with the same orbits. For any selected material U,

    Xi_I(U) = gamma_UN^2 - 1
            = (U^a grad_a I)^2/[c^2 (-grad I.grad I)] - 1
            = h_U^{ab} grad_a I grad_b I/[-grad I.grad I] >= 0,
    h_U^{ab}=g^{ab}+U^a U^b/c^2.

This is an observer-independent dimensionless scalar. Xi=0 iff U=N at p; Xi>0 iff tilted there. If U inherits the group symmetry, the scalar is constant on each connected homogeneous orbit: one event then determines tilt on that orbit. This is not by itself a claim about all times or a global extension of the foliation.

Under Einstein gravity, a single perfect-fluid source

    T_ab = (epsilon+p) u_a u_b + p g_ab

has a unique timelike eigenline when epsilon+p != 0: its timelike eigenvalue is -epsilon and the three spatial eigenvalues are p. The Ricci tensor has the same eigendirections because the trace and Lambda terms are proportional to the identity. Future normalization identifies U. If I depends on metric derivatives through order two, this gives a conditional metric-3-jet classifier. Ricci and its first derivative suffice for a Ricci-built I; a general algebraic curvature scalar can require the full Riemann tensor and its first derivative. It does not prove that observational data determine such a jet.

Examples and limitations: I=R fails for a pure trace-free radiation source with constant Lambda; another scalar such as R_ab R^ab may work. Constant scalar invariants, zero gradients, the epsilon+p=0 degeneracy, ambiguous matter species, or absent SH hypotheses invalidate this particular construction. They do not prove that every possible alternative classifier fails. Approximate data require quantified timelike-gradient and eigengap margins.

Two related exact necessary conditions for spacelike homogeneity are immediate: every nonzero invariant-scalar gradient is timelike, and dI wedge dJ=0 for every pair of such scalars. Violating either condition rejects the spacelike-SH hypothesis locally, rather than selecting a Bianchi type.

Evidence: direct elementary derivation above. No novelty claim, formal proof-assistant certificate, or observational reconstruction claim.

## 3. Einstein momentum constraint is a solver-free tilt discriminator

Let h_ab=g_ab+n_a n_b and use the explicit ADM sign

    K_ab = -h_a^c h_b^d nabla_c n_d.

K has inverse-length units. Define the normal-frame momentum-energy vector

    J_a = -h_a^b T_bc n^c.

J has energy-density units; physical energy flux is c J and momentum density is J/c. With kappa=8 pi G_N/c^4, the contracted Codazzi equation is

    D_b K^b_a - D_a K = kappa J_a.

The sign can be checked in Gaussian coordinates x^0=ct: K_ij=-(1/2)partial_0 h_ij and G_0i=-D_j K^j_i + D_i K, whereas J_i=-T_i0. Lambda makes no contribution to this mixed projection.

For a single perfect fluid,

    E_N = T_ab n^a n^b = (epsilon+p) gamma^2 - p,
    J_a = (epsilon+p) gamma^2 beta_a,
    beta_a = J_a/(E_N+p).

For epsilon+p != 0, J=0 iff beta=0. This implication fails for general imperfect matter and for unseparated mixtures: the total J may vanish while individual component fluxes cancel.

In a homogeneous orthonormal invariant frame, the spatial components of K are constant on a slice, while the connection is algebraic in the Lie brackets C^k_ij:

    2 Gamma^k_ij = C^k_ij - C^i_jk + C^j_ki,
    D_b K^b_a = Gamma^b_bd K^d_a - Gamma^d_ba K^b_d,
    D_a K = 0.

Here nabla_{e_i} e_j = Gamma^k_ij e_k; repeated spatial indices are summed. Therefore C and K determine J algebraically, without solving an evolution or photon hierarchy. This statement requires the genuine symmetry-adapted frame and the intrinsic spatial Levi-Civita connection; arbitrary tetrad anholonomy is not a substitute.

For Bianchi I, C=0, so Gamma=0 and J=0. A homogeneous Bianchi I Einstein solution sourced solely by one perfect fluid with epsilon+p !=0 (plus Lambda) must be non-tilted relative to its homogeneous normal. Tilted Bianchi I matter is possible with multiple fluids whose fluxes cancel, or appropriate imperfect stresses; it is not universally forbidden.

Primary support: Sandin (2009), section 2, equations (8b), (13), discussion following (14), and equation (20b). The author explicitly derives vanishing total flux for Bianchi I while allowing counter-tilted components. A recent existence/stability extension is Fournodavlos, Marshall & Oliynyk, arXiv:2508.15155v2 (2026 revision), DOI 10.1007/s00023-026-01727-7; only abstract and bibliographic metadata inspected here, so no details of their proof imported.

## 4. Quantitative tilt bounds without a forward radiation solver

For enthalpy w=epsilon+p>0 and j=sqrt(J_a J^a),

    r = j/w = beta/(1-beta^2),
    beta = f(r) = 2r/[1+sqrt(1+4r^2)].

The stable rationalized expression has f(0)=0 and tends to 1 as r tends to infinity. It is strictly increasing. Given sound simultaneous intervals j in [j_minus,j_plus], w in [w_minus,w_plus], with j_minus>=0 and w_minus>0,

    f(j_minus/w_plus) <= beta <= f(j_plus/w_minus).

Ignoring dependence between j,w makes this bound conservative, not falsely precise. A strictly positive lower j excludes non-tilt in the assumed single-fluid model. A small upper j alone does not bound tilt if enthalpy can become arbitrarily small. Inference of J from the geometry needs uncertainty in C,K and their frame to be propagated jointly. Norm bounds discard direction; keep vector or tensor uncertainty when testing alignment with principal axes or observer boosts.

## 5. Kinematical shortcuts and their limitations

A homogeneous normal n is hypersurface orthogonal, hence omega_N=0. With a G3-invariant lapse it is geodesic: A_N=0. Nonzero omega_U or A_U therefore excludes equality U=N as fields throughout a neighbourhood, not merely equality of their values at one event. A rotating Minkowski congruence can coincide with N at its rotation centre while retaining vorticity. If U explicitly inherits the spatial symmetry, nonzero omega_U additionally excludes equality on that orbit. Acceleration has a stronger limitation: even a homogeneous U(t) can cross N at one time with nonzero A_U; it does not by itself imply pointwise tilt. Neither converse holds. For example a one-dimensional tilted velocity ansatz with dual one-form f(t)dt+g(t)dx satisfies U_flat wedge dU_flat=0 for arbitrary f,g, while beta can be nonzero. Tilted counterflows in Bianchi I provide the appropriate multi-fluid context; this algebraic ansatz alone is not an independently solved Einstein-Euler solution.

The scalar Xi and the flux criterion test actual matter tilt. Dipoles caused by changing O test observer motion relative to some independently specified physical frame. Labeling a best-fit radiation-isotropy frame as the homogeneous normal requires an extra relation and cannot be inferred by nomenclature.

## Sources actually inspected

- King, A. R. & Ellis, G. F. R. (1973), Tilted homogeneous cosmological models, Communications in Mathematical Physics 31, 209-242. Publisher abstract, bibliographic metadata: https://link.springer.com/article/10.1007/BF01646266 . Search ref turn96view1 / turn98view2. Full article not retrieved.
- Sandin, P. (2009), Tilted two-fluid Bianchi type I models, General Relativity and Gravitation 41, 2707-2724, DOI 10.1007/s10714-009-0799-5. Full original-author HTML: https://arxiv.org/html/0901.0800v1 . Search ref turn92view0 / turn96view3. Core exact equations 8b and 20b inspected.
- Fournodavlos, G., Marshall, E., & Oliynyk, T. A. (2025/2026), Future Stability of Tilted Two-Fluid Bianchi I Spacetimes, arXiv:2508.15155v2, revised 7 July 2026, DOI 10.1007/s00023-026-01727-7. Abstract only: https://arxiv.org/abs/2508.15155 . Search ref turn98view0.

No numerical evolution, external Boltzmann calculation, Lean/mathlib compilation, or actual-data classification was performed in this subtask.
