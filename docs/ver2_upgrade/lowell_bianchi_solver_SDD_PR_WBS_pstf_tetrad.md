# Low-\(\ell\) 1+3 PSTF/Tetrad Bianchi CMB Solver

## SDD-based PR/WBS Development Document

**Document status:** implementation-planning baseline  
**Document role:** software design document (SDD) + PR list + work breakdown structure (WBS)  
**Baseline relationship:** this document is an update-format development plan. The original project specifications are assumed to have already been migrated into the current 1+3 gauge-invariant covariant PSTF/tetrad formulation. The document therefore does not re-litigate the original authority path; it freezes it as inherited and gives the development plan needed to implement it.

---

# 0. Executive design statement

The solver is a research code for homogeneous but anisotropic beyond-FLRW cosmologies, focused on low-\(\ell\) CMB temperature and polarization transport. The mathematical core is a **1+3 gauge-invariant covariant PSTF Einstein--Boltzmann system** evaluated in an invariant **orthonormal tetrad**. Bianchi type enters only through the spatial commutator algebra

\[
[e_\alpha,e_\beta]=C^\gamma{}_{\alpha\beta}e_\gamma,
\qquad
C^\gamma{}_{\alpha\beta}
=2a_{[\alpha}\delta_{\beta]}{}^\gamma
+\epsilon_{\alpha\beta\delta}n^{\delta\gamma}.
\]

The same algebra backend must support all eleven Bianchi types,

\[
\mathrm{I},\ \mathrm{II},\ \mathrm{III},\ \mathrm{IV},\ \mathrm{V},\
\mathrm{VI}_0,\ \mathrm{VI}_h,\ \mathrm{VII}_0,\ \mathrm{VII}_h,\
\mathrm{VIII},\ \mathrm{IX},
\]

and for each type it must support both orthogonal and tilted matter branches.

The inherited authority path is kept:

\[
\boxed{
\text{exact Bianchi transport}
+\text{ electron-frame Thomson tensor}
+\text{ explicit low-}\ell\text{ radiation multipoles}
+\text{ scalar }x_e(\tau)\text{ first pass}
+\text{ anisotropic source propagation}
}
\]

The difference from the earlier PR/WBS baseline is architectural: the solver core is no longer framed through ADM variables. It is framed through 1+3 covariant PSTF objects, while tetrad components provide the code representation.

This document deliberately avoids conservative interpretation language tied to any one observational team or template family. The scientific purpose is open exploration of beyond-FLRW homogeneous anisotropy.

---

# 1. SDD scope

## 1.1 In scope

This SDD specifies the implementation of:

1. Bianchi algebra registry for all eleven types.
2. Tetrad differential geometry backend.
3. 1+3 covariant PSTF background system.
4. Constraint generation and constraint projection from Ricci/Jacobi/Bianchi identities.
5. Orthogonal and tilted matter stress-energy decomposition.
6. Photon geodesic and polarization-basis transport in tetrad variables.
7. Low-\(\ell\) PSTF radiation hierarchy for \(I_{A_\ell}\), \(E_{A_\ell}\), \(B_{A_\ell}\).
8. Electron-frame Thomson collision tensor.
9. Isotropic scalar recombination history as first-pass microphysics, with anisotropic source evaluation.
10. Homogeneous reionization and rescattering source wiring.
11. Tier A angular transport backend and Tier B low-\(\ell\) projected backend.
12. Numerical integration, stiffness handling, convergence diagnostics, and validation gates.
13. PR-level decomposition, WBS, dependency ordering, acceptance criteria, and traceability.

## 1.2 Out of scope for this SDD

The following belong to the separated observables/statistics document or future physics extensions:

1. Map masks, pseudo-\(a_{\ell m}\), public-data ingestion, anomaly statistics, or likelihood interpretation.
2. Conservative reading of any particular data release.
3. Anisotropic recombination microphysics with direction-dependent escape probability.
4. Patchy reionization.
5. High-\(\ell\) production Boltzmann hierarchy.
6. Non-classical Compton scattering beyond Thomson.
7. Full nonlinear inhomogeneous perturbation theory.

The solver may export sky-facing quantities, but this SDD does not define statistical claims made from them.

---

# 2. Global conventions

## 2.1 Signature, units, and dimensions

Metric signature:

\[
(-,+,+,+).
\]

Unless a module explicitly declares natural units, keep

\[
c,\quad G,\quad \hbar,\quad k_B
\]

explicit. The default geometric time is

\[
\tau\equiv ct,
\]

so \(d/d\tau\) has dimension \(L^{-1}\). The Einstein coupling is

\[
\kappa\equiv \frac{8\pi G}{c^4}.
\]

If \(\rho\) is physical energy density, then

\[
\kappa\rho,
\quad
\kappa p,
\quad
H^2,
\quad
\sigma_{ab}\sigma^{ab},
\quad
{}^3R,
\quad
\Lambda
\]

all have dimension \(L^{-2}\).

## 2.2 1+3 split

The fundamental observer congruence is \(n^a\):

\[
n^an_a=-1,
\qquad
h_{ab}=g_{ab}+n_an_b,
\qquad
h_{ab}n^b=0.
\]

The projected symmetric trace-free operation is denoted

\[
X_{\langle a_1\cdots a_\ell\rangle}.
\]

The kinematic split is

\[
\nabla_a n_b
=
-n_aA_b+\frac13\Theta h_{ab}+\sigma_{ab}+\omega_{ab}.
\]

For the background Bianchi models in this solver, choose the normal congruence to be geodesic and hypersurface-orthogonal:

\[
A_a=0,
\qquad
\omega_{ab}=0.
\]

Matter may still be tilted relative to \(n^a\). Define

\[
H\equiv \frac13\Theta,
\qquad
\sigma^2\equiv \frac12\sigma_{ab}\sigma^{ab}.
\]

## 2.3 Tetrad basis

Use an orthonormal tetrad

\[
e_0=n,
\qquad
h(e_\alpha,e_\beta)=\delta_{\alpha\beta},
\qquad
\alpha,\beta,\gamma=1,2,3.
\]

Spatial tetrad indices are raised and lowered with \(\delta_{\alpha\beta}\). The volume form satisfies

\[
\epsilon_{123}=+1.
\]

Default tetrad gauge:

\[
\Omega_\alpha=0,
\]

where \(\Omega_\alpha\) is the tetrad rotation rate relative to a Fermi-propagated spatial frame. A rotating tetrad is allowed only if every derivative operator includes the induced rotation terms and the rotation convention is stored in run metadata.

## 2.4 Frame split authority

Transport is performed in the \(n^a\)-frame. Thomson collision, visibility, and scattering source evaluation are performed in the electron rest frame \(u_e^a\):

\[
\boxed{
\text{transport frame}=n^a,
\qquad
\text{collision/source/visibility frame}=u_e^a.
}
\]

For a species \(s\),

\[
u_{(s)}^a=\Gamma_s(n^a+v_{(s)}^a),
\qquad
v_{(s)}^an_a=0,
\qquad
\Gamma_s=(1-v_s^2)^{-1/2}.
\]

The orthogonal branch is the subcase

\[
v_{(s)}^\alpha=0
\quad\forall s.
\]

---

# 3. Top-level software architecture

## 3.1 Package layout

The intended package layout is:

```text
lowell_bianchi/
  algebra/
    bianchi_types.py
    structure_constants.py
    jacobi.py
  geometry/
    tetrad_connection.py
    spatial_operators.py
    spatial_ricci.py
    pstf.py
  background/
    state.py
    constraints.py
    rhs.py
    initial_conditions.py
    weyl.py
  matter/
    species.py
    tilt.py
    stress_energy.py
    conservation.py
  photons/
    geodesics.py
    screen_basis.py
    stokes.py
    pstf_radiation.py
  collision/
    electron_frame.py
    thomson_tensor.py
    multipole_projection.py
  history/
    recombination.py
    reionization.py
    visibility.py
  tca/
    quadrupole_startup.py
    stiff_closure.py
  solvers/
    tierA_angular.py
    tierB_pstf.py
    integrators.py
    checkpoint.py
  output/
    observer_export.py
    metadata.py
  validation/
    tests_algebra.py
    tests_constraints.py
    tests_background.py
    tests_photon_transport.py
    tests_collision.py
    tests_solver_limits.py
  experiments/
    configs/
    runs/
  docs/
    SDD_PR_WBS.md
```

## 3.2 Runtime data flow

The production flow is:

\[
\boxed{
\text{Bianchi type}
\rightarrow
(a_\alpha,n_{\alpha\beta},C^\gamma{}_{\alpha\beta})
\rightarrow
\text{geometry operators}
\rightarrow
\text{constraint-satisfying IC}
\rightarrow
\text{background + radiation evolution}
\rightarrow
\text{observer-export quantities}
}
\]

Code-level skeleton:

```python
def run_solver(config):
    algebra = build_bianchi_algebra(config.bianchi_type, config.algebra_params)
    geom = build_tetrad_geometry(algebra, config.tetrad_gauge)

    matter_ic = build_matter_ic(config.matter, branch=config.branch)
    bg_state = build_constraint_satisfying_background_ic(
        algebra=algebra,
        geom=geom,
        matter=matter_ic,
        shear_spec=config.shear_ic,
        constraint_policy=config.constraint_policy,
    )

    rad_state = build_radiation_ic(
        config.radiation_ic,
        bg_state=bg_state,
        matter=matter_ic,
        frame_policy=config.frame_policy,
    )

    history = build_ionization_history(config.history)
    solver = make_solver(config.solver_tier, algebra, geom, history)

    result = solver.integrate(
        t_span=config.t_span,
        background=bg_state,
        matter=matter_ic,
        radiation=rad_state,
        tolerances=config.tolerances,
    )

    validate_run(result, config.validation)
    return export_observer_quantities(result, config.output)
```

## 3.3 Tier distinction

Tier A is the angular truth/reference backend:

\[
\mathcal L_B[N_{AB}(E,e)]
=
\mathcal C_{AB}^{\rm Th}[N;u_e],
\]

where \(N_{AB}\) is the polarization brightness matrix on the screen.

Tier B is the low-\(\ell\) PSTF production backend:

\[
\mathbf X_L
=
\{I_{A_\ell},E_{A_\ell},B_{A_\ell}\}_{\ell\le L},
\qquad
\mathbf X_L'
=
\mathsf L_B[C,H,\sigma]\mathbf X_L+
\mathsf C_T[u_e]\mathbf X_L+\
\mathbf S_L.
\]

Tier B is allowed to use a controlled closure at \(L\). It must be compared against Tier A in low-resolution validation runs.

---

# 4. Functional and physics requirements

## 4.1 Functional requirements

| ID | Requirement | Verification | PR owner |
|---|---|---|---|
| F-01 | Register all eleven Bianchi types through one algebra object. | Algebra table tests and Jacobi tests. | PR-01 |
| F-02 | Generate tetrad connection, div, curl, PSTF derivative, and Ricci objects from \((a,n)\). | Operator identity tests. | PR-02 |
| F-03 | Build orthogonal ICs satisfying Hamiltonian and momentum constraints. | Constraint residual tests. | PR-03 |
| F-04 | Build tilted ICs satisfying stress-energy and Codazzi/momentum constraints. | Tilt branch residual tests. | PR-04 |
| F-05 | Evolve 1+3 PSTF background variables using Ricci/Bianchi identity-consistent RHS. | Background limit tests. | PR-05 |
| F-06 | Evolve photon geodesics and polarization screen basis in tetrad form. | Norm and redshift tests. | PR-07 |
| F-07 | Represent radiation in PSTF multipoles up to configurable \(L\). | Projection/reconstruction tests. | PR-08 |
| F-08 | Implement electron-frame Thomson tensor without reducing to an FLRW shortcut. | Linearity and isotropic-null tests. | PR-09 |
| F-09 | Wire scalar \(x_e(\tau)\), visibility, and homogeneous reionization source. | On/off and normalization tests. | PR-10 |
| F-10 | Provide Tier A and Tier B solver modes with compatible output. | Tier comparison tests. | PR-13, PR-14 |
| F-11 | Export solver-side observer quantities without embedding statistical interpretation. | Metadata and shape tests. | PR-17 |
| F-12 | Store all conventions and run metadata. | Metadata schema tests. | PR-18 |

## 4.2 Physics requirements

| ID | Requirement | Hard condition |
|---|---|---|
| P-01 | Coordinate gauge modes must not be state variables. | State variables are 1+3 covariant tensors and tetrad components only. |
| P-02 | Bianchi type is only algebra input, not separate hand-coded physics. | No type-specific RHS except algebra construction. |
| P-03 | Orthogonal and tilted branches must be first-class. | Every type has both branch metadata and IC path. |
| P-04 | Constraint equations must be evaluated throughout integration. | Constraint residuals are part of solver output. |
| P-05 | Electron-frame Thomson collision must be separated from normal-frame transport. | Collision API requires electron-frame transform. |
| P-06 | Low-\(\ell\) polarization is not post-processing only. | \(E_{A_\ell},B_{A_\ell}\) are solver states or explicit source states. |
| P-07 | FLRW is a limit, not a separate code path. | \(a=n=\sigma=v=0\) or isotropic-curvature limit recovers FLRW tests. |
| P-08 | Class B models are not rejected by construction. | \(a_\alpha\neq0\) operators and constraints must be active. |

## 4.3 Numerical requirements

| ID | Requirement | Target |
|---|---|---|
| N-01 | Constraint residual monitoring. | Relative residuals configurable, default fail above \(10^{-8}\) in background tests. |
| N-02 | Stable stiff treatment near recombination. | TCA or implicit/IMEX branch available. |
| N-03 | Reproducible runs. | All algebra, units, cutoffs, tolerances, frame conventions saved. |
| N-04 | Cutoff convergence. | \(L=4,6,8\) supported for development; larger \(L\) allowed. |
| N-05 | Type-generic tests. | Smoke tests run over all eleven Bianchi types in both branches. |
| N-06 | Separation of solver and observer statistics. | Solver output is statistical-analysis neutral. |

---

# 5. Mathematical design foundation

## 5.1 Bianchi algebra

Spatial commutators are

\[
[e_\alpha,e_\beta]
=
C^\gamma{}_{\alpha\beta}e_\gamma,
\qquad
C^\gamma{}_{\alpha\beta}=-C^\gamma{}_{\beta\alpha}.
\]

Use

\[
\boxed{
C^\gamma{}_{\alpha\beta}
=
2a_{[\alpha}\delta_{\beta]}{}^\gamma
+
\epsilon_{\alpha\beta\delta}n^{\delta\gamma}
}
\]

with

\[
n_{\alpha\beta}=n_{\beta\alpha}.
\]

The Jacobi identity imposes

\[
\boxed{n_{\alpha\beta}a^\beta=0.}
\]

Class A:

\[
a_\alpha=0.
\]

Class B:

\[
a_\alpha\neq0,
\qquad
n_{\alpha\beta}a^\beta=0.
\]

### 5.1.1 Canonical algebra table

Use the canonical orientation

\[
a_\alpha=(a,0,0),
\qquad
n_{\alpha\beta}=\mathrm{diag}(n_1,n_2,n_3),
\]

where applicable. Axis permutations are allowed tetrad choices but must be stored as metadata.

| Type | Class | \(a_\alpha\) | \((n_1,n_2,n_3)\) | Parameter domain | Orthogonal branch | Tilted branch |
|---|---:|---:|---:|---|---|---|
| I | A | \((0,0,0)\) | \((0,0,0)\) | none | \(q_\alpha=0\), \({}^3R_{\alpha\beta}=0\) | tilt allowed only if total \(q_\alpha\) is balanced by Codazzi; otherwise solve shear off-diagonal or compensating species tilt |
| II | A | \((0,0,0)\) | \((n,0,0)\) up to permutation | \(n\neq0\) | \(D^\beta\sigma_{\alpha\beta}=0\) | \(D^\beta\sigma_{\alpha\beta}=\kappa q_\alpha\) fixes allowed tilt/shear combination |
| VI\(_0\) | A | \((0,0,0)\) | \((0,n,-n)\) | \(n\neq0\) | trace-free class-A curvature; orthogonal branch has zero total flux | tilt source enters only through \(q_\alpha,\pi_{\alpha\beta}\) and constraints |
| VII\(_0\) | A | \((0,0,0)\) | \((0,n,n)\) | \(n\neq0\) | helical class-A algebra without class-B vector | tilt handled by same Codazzi closure, no special template assumption |
| VIII | A | \((0,0,0)\) | sign pattern \((-n,n,n)\) up to permutation | \(n>0\) | non-compact semisimple algebra; orthogonal allowed | tilted allowed with class-A momentum constraint |
| IX | A | \((0,0,0)\) | \((n,n,n)\) | \(n>0\) | compact positive-curvature algebra; orthogonal allowed | tilted allowed subject to global/model-domain restrictions chosen by user config |
| V | B | \((a,0,0)\) | \((0,0,0)\) | \(a>0\) | open isotropic limit exists when shear vanishes | tilt couples strongly to class-B vector through divergence operators |
| IV | B | \((a,0,0)\) | one nonzero eigenvalue, e.g. \((0,0,n)\) | \(a,n>0\) | orthogonal branch requires class-B Codazzi residual zero | tilted branch solves \(q_\alpha\) from class-B divergence |
| III | B | \((a,0,0)\) | VI\(_h\) special case with conventional \(h=-1\) | convention stored | named alias retained for clarity | same equations as VI\(_h\) with alias metadata |
| VI\(_h\) | B | \((a,0,0)\) | \((0,n_2,n_3)\), \(n_2n_3<0\) | sign convention for \(h\) stored | orthogonal allowed if constraints close | tilted allowed; do not hard-code VII-style simplifications |
| VII\(_h\) | B | \((a,0,0)\) | \((0,n_2,n_3)\), \(n_2n_3>0\) | \(h>0\) under chosen convention | orthogonal allowed | tilted allowed; treated as one of eleven types, not privileged |

Implementation rule: no RHS module is allowed to branch on a type name except inside `build_bianchi_algebra`. All later modules consume only \(a_\alpha\), \(n_{\alpha\beta}\), and \(C^\gamma{}_{\alpha\beta}\).

### 5.1.2 Algebra construction pseudocode

```python
def build_structure_constants(a_vec, n_mat):
    C = zeros((3, 3, 3))  # C[gamma, alpha, beta]
    for gamma in range(3):
        for alpha in range(3):
            for beta in range(3):
                term_a = a_vec[alpha] * delta[beta, gamma] - a_vec[beta] * delta[alpha, gamma]
                term_n = sum(eps[alpha, beta, d] * n_mat[d, gamma] for d in range(3))
                C[gamma, alpha, beta] = term_a + term_n
    return C


def check_jacobi(a_vec, n_mat, atol):
    residual = n_mat @ a_vec
    assert norm(residual) < atol
```

## 5.2 Tetrad connection and spatial curvature

Define spatial connection coefficients by the Koszul formula:

\[
2\Gamma_{\gamma\alpha\beta}
=
C_{\alpha\beta\gamma}
-C_{\beta\gamma\alpha}
+C_{\gamma\alpha\beta},
\]

where

\[
\Gamma^\gamma{}_{\alpha\beta}
\equiv
\langle \nabla_{e_\alpha}e_\beta,e_\gamma\rangle.
\]

With homogeneous tetrad coefficients, derivative terms vanish and the spatial Riemann tensor is computed algebraically:

\[
{}^3R^\delta{}_{\gamma\alpha\beta}
=
\Gamma^\epsilon{}_{\beta\gamma}\Gamma^\delta{}_{\alpha\epsilon}
-
\Gamma^\epsilon{}_{\alpha\gamma}\Gamma^\delta{}_{\beta\epsilon}
-C^\epsilon{}_{\alpha\beta}\Gamma^\delta{}_{\epsilon\gamma}.
\]

Then

\[
{}^3R_{\gamma\beta}
={}^{3}R^\alpha{}_{\gamma\alpha\beta},
\qquad
{}^3R=\delta^{\gamma\beta}{}^3R_{\gamma\beta},
\]

and the trace-free spatial Ricci tensor is

\[
{}^3S_{\alpha\beta}
={}^{3}R_{\langle\alpha\beta\rangle}
={}^3R_{\alpha\beta}-\frac13{}^3R\delta_{\alpha\beta}.
\]

Pseudocode:

```python
def spatial_connection(C):
    Gamma = zeros((3,3,3))  # Gamma[gamma, alpha, beta]
    C_low = C.copy()        # Euclidean spatial metric
    for gamma in range(3):
        for alpha in range(3):
            for beta in range(3):
                Gamma[gamma, alpha, beta] = 0.5 * (
                    C_low[gamma, alpha, beta]
                    - C_low[alpha, beta, gamma]
                    + C_low[beta, gamma, alpha]
                )
    return Gamma


def spatial_riemann_ricci(C, Gamma):
    Riem = zeros((3,3,3,3))  # Riem[delta, gamma, alpha, beta]
    for delta in range(3):
        for gamma in range(3):
            for alpha in range(3):
                for beta in range(3):
                    term = 0.0
                    for eps_i in range(3):
                        term += Gamma[eps_i, beta, gamma] * Gamma[delta, alpha, eps_i]
                        term -= Gamma[eps_i, alpha, gamma] * Gamma[delta, beta, eps_i]
                        term -= C[eps_i, alpha, beta] * Gamma[delta, eps_i, gamma]
                    Riem[delta, gamma, alpha, beta] = term
    Ric = zeros((3,3))
    for gamma in range(3):
        for beta in range(3):
            Ric[gamma, beta] = sum(Riem[alpha, gamma, alpha, beta] for alpha in range(3))
    Rscalar = trace(Ric)
    S = stf2(Ric)
    return Riem, Ric, Rscalar, S
```

## 5.3 PSTF differential operators

For a scalar \(f\) homogeneous on group orbits,

\[
D_\alpha f=0.
\]

For a spatial vector \(V_\alpha\),

\[
D_\alpha V_\beta
=
e_\alpha(V_\beta)-\Gamma^\gamma{}_{\alpha\beta}V_\gamma.
\]

For homogeneous tetrad components, \(e_\alpha(V_\beta)=0\), so

\[
D_\alpha V_\beta=-\Gamma^\gamma{}_{\alpha\beta}V_\gamma.
\]

Divergence and curl:

\[
D^\alpha V_\alpha
=-\Gamma^\gamma{}_{\alpha\alpha}V_\gamma,
\]

\[
(\mathrm{curl}\,V)_\alpha
=\epsilon_{\alpha\beta\gamma}D^\beta V^\gamma.
\]

For a PSTF rank-2 tensor \(X_{\alpha\beta}\),

\[
D_\gamma X_{\alpha\beta}
=-\Gamma^\mu{}_{\gamma\alpha}X_{\mu\beta}
-\Gamma^\mu{}_{\gamma\beta}X_{\alpha\mu},
\]

\[
(D^\beta X_{\alpha\beta})
=\delta^{\beta\gamma}D_\gamma X_{\alpha\beta},
\]

\[
(\mathrm{curl}\,X)_{\alpha\beta}
=
\epsilon_{\gamma\delta\langle\alpha}D^\gamma X_{\beta\rangle}{}^\delta.
\]

Pseudocode:

```python
def covariant_derivative_rank2_homogeneous(X, Gamma):
    D = zeros((3,3,3))  # D[gamma, alpha, beta]
    for gamma in range(3):
        for alpha in range(3):
            for beta in range(3):
                D[gamma, alpha, beta] = -sum(Gamma[mu, gamma, alpha] * X[mu, beta]
                                             + Gamma[mu, gamma, beta] * X[alpha, mu]
                                             for mu in range(3))
    return D


def div_rank2(X, Gamma):
    D = covariant_derivative_rank2_homogeneous(X, Gamma)
    out = zeros(3)
    for alpha in range(3):
        out[alpha] = sum(D[beta, alpha, beta] for beta in range(3))
    return out


def curl_rank2_stf(X, Gamma):
    D = covariant_derivative_rank2_homogeneous(X, Gamma)
    Y = zeros((3,3))
    for alpha in range(3):
        for beta in range(3):
            raw = 0.0
            for gamma in range(3):
                for delta_i in range(3):
                    raw += eps[gamma, delta_i, alpha] * D[gamma, beta, delta_i]
            Y[alpha, beta] = raw
    return stf2(sym(Y))
```

## 5.4 1+3 background variables

The minimal background state is

\[
\mathcal X_{\rm bg}
=\{H,\sigma_{\alpha\beta},\rho,p,q_\alpha,\pi_{\alpha\beta},a_\alpha,n_{\alpha\beta}\}.
\]

The Weyl components are either diagnostic or evolved in an extended system:

\[
E_{\alpha\beta},
\qquad
H_{\alpha\beta}^{\rm Weyl}.
\]

To avoid notation collision with the Hubble scalar \(H\), the magnetic Weyl tensor in code must be named `Hweyl` or `Bweyl`, never plain `H`.

## 5.5 Constraint equations

### 5.5.1 Jacobi constraint

\[
\boxed{n_{\alpha\beta}a^\beta=0.}
\]

### 5.5.2 Gauss/Hamiltonian constraint

\[
\boxed{
3H^2
=
\kappa\rho+\Lambda+\sigma^2-\frac12{}^3R.
}
\]

This is not an ADM formulation in the software architecture; it is the scalar Gauss relation written in 1+3 variables. It is used as a constraint residual and as an IC closure equation.

### 5.5.3 Codazzi/momentum constraint

For homogeneous geodesic irrotational normal congruence,

\[
\boxed{
D^\beta\sigma_{\alpha\beta}=\kappa q_\alpha.
}
\]

Orthogonal branch:

\[
q_\alpha=0
\quad\Rightarrow\quad
D^\beta\sigma_{\alpha\beta}=0.
\]

Tilted branch:

\[
q_\alpha=\sum_s q_\alpha^{(s)}
\quad\Rightarrow\quad
D^\beta\sigma_{\alpha\beta}=\kappa\sum_s q_\alpha^{(s)}.
\]

### 5.5.4 Magnetic Weyl constraint

\[
\boxed{
H^{\rm Weyl}_{\alpha\beta}
=(\mathrm{curl}\,\sigma)_{\alpha\beta}
}
\]

for the chosen \(A_\alpha=\omega_\alpha=0\) background congruence.

### 5.5.5 Electric Weyl diagnostic

A useful algebraic diagnostic is

\[
E_{\alpha\beta}
=
-\dot\sigma_{\alpha\beta}
-2H\sigma_{\alpha\beta}
-\sigma_{\gamma\langle\alpha}\sigma_{\beta\rangle}{}^\gamma
+\frac12\kappa\pi_{\alpha\beta},
\]

where dot denotes \(d/d\tau\). This equation is not used as the primary shear RHS if the code evolves shear via the Ricci-form equation below; it is used to check internal consistency.

## 5.6 Background evolution equations

### 5.6.1 Raychaudhuri equation

\[
\boxed{
\dot H
=
-H^2
-\frac23\sigma^2
-\frac16\kappa(\rho+3p)
+\frac13\Lambda.
}
\]

Equivalently,

\[
\dot\Theta
+\frac13\Theta^2
+2\sigma^2
+\frac12\kappa(\rho+3p)
-\Lambda=0.
\]

### 5.6.2 Shear propagation equation

The tetrad background solver evolves

\[
\boxed{
\dot\sigma_{\alpha\beta}
+3H\sigma_{\alpha\beta}
=
-{}^3S_{\alpha\beta}
+\kappa\pi_{\alpha\beta}.
}
\]

Checks:

1. Bianchi I perfect fluid: \({}^3S_{\alpha\beta}=0\), \(\pi_{\alpha\beta}=0\), so
   \[
   \dot\sigma_{\alpha\beta}+3H\sigma_{\alpha\beta}=0.
   \]
2. FLRW: \(\sigma_{\alpha\beta}=0\), \({}^3S_{\alpha\beta}=0\), \(\pi_{\alpha\beta}=0\).

### 5.6.3 Matter conservation in normal frame

Total conservation \(\nabla_bT^{ab}=0\) gives, in 1+3 form,

\[
\dot\rho
+3H(\rho+p)
+D^\alpha q_\alpha
+2A^\alpha q_\alpha
+\sigma^{\alpha\beta}\pi_{\alpha\beta}=0.
\]

With \(A_\alpha=0\),

\[
\boxed{
\dot\rho
+3H(\rho+p)
+D^\alpha q_\alpha
+\sigma^{\alpha\beta}\pi_{\alpha\beta}=0.
}
\]

The momentum equation is

\[
\dot q_{\langle\alpha\rangle}
+4Hq_\alpha
+(\rho+p)A_\alpha
+D_\alpha p
+D^\beta\pi_{\alpha\beta}
+A^\beta\pi_{\alpha\beta}
+\sigma_{\alpha\beta}q^\beta
=0
\]

for the irrotational case. With \(A_\alpha=0\) and homogeneous scalar pressure,

\[
\boxed{
\dot q_{\langle\alpha\rangle}
+4Hq_\alpha
+D^\beta\pi_{\alpha\beta}
+\sigma_{\alpha\beta}q^\beta=0.
}
\]

In code, species-level conservation may be used instead of total-fluid conservation, but the total residual must still be checked.

### 5.6.4 Curvature algebra update

The Bianchi algebra can be represented in either physical or H-normalized variables.

Physical algebra variables scale with the spatial tetrad. If the tetrad is co-expanding and anisotropically deformed, \(a_\alpha\) and \(n_{\alpha\beta}\) evolve. To reduce convention risk, the first implementation should use a tetrad gauge with explicit scale/shear update rules and store them in metadata.

A robust implementation path is:

1. Store a constant abstract Lie algebra \((\bar a_\alpha,\bar n_{\alpha\beta})\) in a group-invariant coframe.
2. Store the physical orthonormal triad map \(E^i{}_{\alpha}(\tau)\).
3. Recompute physical \(C^\gamma{}_{\alpha\beta}(\tau)\), \(a_\alpha(\tau)\), \(n_{\alpha\beta}(\tau)\), connection, and \({}^3R_{\alpha\beta}\) from the triad map.

Minimal first-pass approximation for low anisotropy may use H-normalized variables:

\[
A_\alpha\equiv \frac{a_\alpha}{H},
\qquad
N_{\alpha\beta}\equiv \frac{n_{\alpha\beta}}{H},
\qquad
\Sigma_{\alpha\beta}\equiv\frac{\sigma_{\alpha\beta}}{H}.
\]

If normalized variables are used, the code must explicitly implement the corresponding normalized RHS rather than silently mixing normalized and physical variables.

## 5.7 Stress-energy decomposition with tilt

For species \(s\), define rest-frame density and pressure

\[
\hat\rho_s,
\qquad
\hat p_s=w_s\hat\rho_s.
\]

Normal-frame decomposition:

\[
T^{ab}_{(s)}
=
\rho_s n^an^b
+2q_s^{(a}n^{b)}
+p_s h^{ab}
+\pi_s^{ab}.
\]

With

\[
u_s^a=\Gamma_s(n^a+v_s^a),
\qquad
\Gamma_s=(1-v_s^2)^{-1/2},
\]

one gets

\[
\boxed{
\rho_s=(\hat\rho_s+\hat p_s)\Gamma_s^2-\hat p_s,
}
\]

\[
\boxed{
p_s=\hat p_s+\frac13(\hat\rho_s+\hat p_s)\Gamma_s^2v_s^2,
}
\]

\[
\boxed{
q_\alpha^{(s)}=(\hat\rho_s+\hat p_s)\Gamma_s^2v_\alpha^{(s)},
}
\]

\[
\boxed{
\pi_{\alpha\beta}^{(s)}=(\hat\rho_s+\hat p_s)\Gamma_s^2v_{\langle\alpha}^{(s)}v_{\beta\rangle}^{(s)}.
}
\]

Total quantities:

\[
\rho=\sum_s\rho_s,
\qquad
p=\sum_s p_s,
\qquad
q_\alpha=\sum_s q_\alpha^{(s)},
\qquad
\pi_{\alpha\beta}=\sum_s\pi_{\alpha\beta}^{(s)}.
\]

Small-tilt check:

\[
q_\alpha^{(s)}=(\hat\rho_s+\hat p_s)v_\alpha^{(s)}+O(v^3),
\]

\[
\pi_{\alpha\beta}^{(s)}=(\hat\rho_s+\hat p_s)v_{\langle\alpha}^{(s)}v_{\beta\rangle}^{(s)}+O(v^4).
\]

Pseudocode:

```python
def tilted_species_to_normal_frame(rho_hat, p_hat, v):
    v2 = dot(v, v)
    Gamma = 1.0 / sqrt(1.0 - v2)
    enthalpy = rho_hat + p_hat
    rho = enthalpy * Gamma**2 - p_hat
    p = p_hat + enthalpy * Gamma**2 * v2 / 3.0
    q = enthalpy * Gamma**2 * v
    pi = enthalpy * Gamma**2 * stf2(outer(v, v))
    return rho, p, q, pi
```

## 5.8 Constraint-satisfying initial conditions

### 5.8.1 Inputs

At \(\tau_i\), user supplies:

\[
\text{Bianchi type},
\quad
\text{algebra scale},
\quad
H_i,
\quad
\Lambda,
\quad
\{\hat\rho_{s,i},w_s,v_{s,i}^\alpha\},
\quad
\sigma_{\alpha\beta,i}^{\rm shape}.
\]

The shear shape is trace-free:

\[
\sigma^\alpha{}_{\alpha}=0.
\]

Often parameterize

\[
\sigma_{\alpha\beta,i}=H_i\Sigma_i S_{\alpha\beta},
\qquad
S^\alpha{}_{\alpha}=0,
\qquad
\frac12S_{\alpha\beta}S^{\alpha\beta}=1.
\]

### 5.8.2 Orthogonal branch

Set

\[
v_{s,i}^\alpha=0,
\qquad
q_{\alpha,i}=0,
\qquad
\pi_{\alpha\beta,i}=0
\]

for perfect-fluid matter.

Then enforce

\[
D^\beta\sigma_{\alpha\beta,i}=0.
\]

The Hamiltonian constraint closes one scalar degree:

\[
3H_i^2
=
\kappa\rho_i+\Lambda+\sigma_i^2-\frac12{}^3R_i.
\]

The code must allow at least three closure policies:

1. `solve_H`: solve for \(H_i\).
2. `solve_curvature_scale`: solve the algebra scale.
3. `project_shear_amplitude`: adjust \(\Sigma_i\).

### 5.8.3 Tilted branch

Compute \(\rho_i,p_i,q_{\alpha,i},\pi_{\alpha\beta,i}\) from species tilts. Enforce

\[
D^\beta\sigma_{\alpha\beta,i}=\kappa q_{\alpha,i}.
\]

Supported closure policies:

1. `solve_tilt_component`: solve one species velocity component from Codazzi.
2. `solve_shear_offdiag`: solve shear components from Codazzi.
3. `compensated_tilts`: solve a compensating species velocity so \(q_\alpha\) has desired value.
4. `least_squares_project`: project \((\sigma,v_s)\) to the nearest constraint surface.

Pseudocode:

```python
def build_constraint_satisfying_background_ic(algebra, geom, matter_spec, shear_spec, policy):
    matter = build_total_stress_energy(matter_spec)
    sigma = make_tracefree_shear(shear_spec)

    if policy.branch == "orthogonal":
        assert norm(matter.q) < atol
        sigma = project_to_momentum_constraint(sigma, target_q=zeros(3), geom=geom, policy=policy)
    else:
        sigma, matter = project_tilted_codazzi(
            sigma=sigma,
            matter=matter,
            geom=geom,
            target="D_sigma_equals_kappa_q",
            policy=policy,
        )

    R3 = geom.spatial_R_scalar()
    sigma2 = 0.5 * contract2(sigma, sigma)

    H, algebra_scale, sigma = close_hamiltonian_constraint(
        H=policy.H_initial,
        rho=matter.rho,
        Lambda=policy.Lambda,
        sigma=sigma,
        R3=R3,
        solve_for=policy.hamiltonian_closure,
    )

    state = BackgroundState(H=H, sigma=sigma, matter=matter, algebra=algebra)
    assert_constraints(state, geom, policy.tolerances)
    return state
```

## 5.9 Photon geodesic transport

A photon momentum is

\[
k^a=E(n^a+e^a),
\qquad
e^ae_a=1,
\qquad
e^an_a=0.
\]

In tetrad components:

\[
k^A=E(1,e^\alpha).
\]

The implementation authority equation is the tetrad geodesic equation:

\[
\frac{dk^A}{d\lambda}+\Gamma^A{}_{BC}k^Bk^C=0,
\]

with

\[
\frac{d\tau}{d\lambda}=E.
\]

The derived energy equation, used as a hard check, is

\[
\boxed{
\frac{d\ln E}{d\tau}=-H-\sigma_{\alpha\beta}e^\alpha e^\beta,
}
\]

or equivalently

\[
\boxed{
\frac{d\ln(aE)}{d\tau}=-\sigma_{\alpha\beta}e^\alpha e^\beta.
}
\]

The direction equation is generated from the same geodesic equation by

\[
e^\alpha=\frac{k^\alpha}{E}.
\]

Pseudocode:

```python
def photon_rhs(tau, y, bg, geom):
    # y = [lnE, e_alpha]
    lnE, e = unpack(y)
    H = bg.H(tau)
    sigma = bg.sigma(tau)

    dlnE = -H - contract2(sigma, outer(e, e))

    # safer production route: build full spacetime connection and geodesic rhs
    Gamma4 = build_spacetime_connection(bg, geom, tau)
    k = exp(lnE) * concatenate(([1.0], e))
    dk_dlambda = -contract_connection(Gamma4, k, k)
    dtau_dlambda = exp(lnE)
    dk_dtau = dk_dlambda / dtau_dlambda

    dE_dtau = exp(lnE) * dlnE
    de = (dk_dtau[1:4] * exp(lnE) - k[1:4] * dE_dtau) / exp(2 * lnE)
    de = project_tangent_to_sphere(de, e)

    return pack(dlnE, de)
```

Normalization check:

\[
\frac{d}{d\tau}(e_\alpha e^\alpha)=0.
\]

## 5.10 Polarization screen-basis transport

Define screen basis vectors \(s_A^\alpha\), \(A=1,2\):

\[
s_A^\alpha e_\alpha=0,
\qquad
s_A^\alpha s_{B\alpha}=\delta_{AB}.
\]

The screen projector is

\[
S_{\alpha\beta}=\delta_{\alpha\beta}-e_\alpha e_\beta.
\]

The polarization basis should be propagated by projected parallel transport:

\[
\frac{D s_A^\alpha}{d\lambda}
\quad\text{projected into the screen, with re-orthonormalization if needed.}
\]

Numerically:

```python
def transport_screen_basis(y, bg, geom):
    e, s1, s2 = unpack_basis(y)
    # compute covariant derivative along k from tetrad connection
    ds1 = projected_parallel_transport(s1, e, bg, geom)
    ds2 = projected_parallel_transport(s2, e, bg, geom)
    # enforce constraints softly after each solver step
    s1, s2 = gram_schmidt_screen(e, s1, s2)
    return pack_basis(de, ds1, ds2)
```

The polarization phase \(\psi\) obeys

\[
(Q\pm iU)'\supset \mp 2i\psi'(Q\pm iU),
\]

with sign convention recorded in metadata. A run is invalid if the sign convention for \(Q/U\), spin harmonics, and screen rotation is not stored.

## 5.11 Radiation PSTF expansion

For brightness scalar \(I(E,e)\), use

\[
I(E,e)=\sum_{\ell=0}^{L}I_{A_\ell}(E)e^{\langle A_\ell\rangle}.
\]

Projection normalization:

\[
\int d\Omega\ e_{\langle A_\ell\rangle}e^{\langle B_\ell\rangle}
=
\frac{4\pi}{2\ell+1}\frac{\ell!}{(2\ell-1)!!}
\ h_{\langle A_\ell\rangle}^{\langle B_\ell\rangle}.
\]

Therefore

\[
I_{A_\ell}
=
\left[
\frac{4\pi}{2\ell+1}\frac{\ell!}{(2\ell-1)!!}
\right]^{-1}
\int d\Omega\ I(E,e)e_{\langle A_\ell\rangle}.
\]

Polarization is represented by PSTF electric and magnetic multipoles:

\[
E_{A_\ell},
\qquad
B_{A_\ell},
\qquad
\ell\ge2.
\]

Minimum low-\(\ell\) production state:

\[
\mathcal X_{\rm rad}^{(L=4)}
=
\{I_0,I_\alpha,I_{\alpha\beta},I_{\alpha\beta\gamma},I_{A_4},
E_{\alpha\beta},E_{\alpha\beta\gamma},E_{A_4},
B_{\alpha\beta},B_{\alpha\beta\gamma},B_{A_4}\}.
\]

Development cutoffs:

\[
L=4\quad\text{minimal},
\qquad
L=6\quad\text{production low-}\ell,
\qquad
L=8\quad\text{convergence check}.
\]

Higher \(L\) must be possible by configuration.

## 5.12 Electron-frame Thomson collision

In the electron frame, define a screen-projected polarization brightness matrix \(N_{AB}(E,\tilde e)\), where \(A,B=1,2\) are screen indices. Let the scattering Jones projection from incoming direction \(\tilde e'\) to outgoing \(\tilde e\) be

\[
J_{AB}(\tilde e,\tilde e')
=
\tilde s_A(\tilde e)\cdot \tilde s'_B(\tilde e').
\]

The classical Thomson operator is

\[
\boxed{
\tilde{\mathcal C}_{AB}^{\rm Th}(E,\tilde e)
=
-\tilde n_e\sigma_T N_{AB}(E,\tilde e)
+\frac{3\tilde n_e\sigma_T}{8\pi}
\int d\Omega'\
J_{AC}N_{CD}(E,\tilde e')J^*_{BD}.
}
\]

This is exact at the level of classical Thomson scattering. It is linear in \(N_{AB}\). It is not a nonlinear Compton kernel.

Equivalent PSTF source form may use

\[
\tilde\zeta_{\alpha\beta}
=
\frac34\tilde I_{\alpha\beta}
+
\frac92\tilde E_{\alpha\beta},
\]

with collision skeleton

\[
\tilde{\mathcal C}_I(E,
\tilde e)
=
-\tilde n_e\sigma_T I(E,\tilde e)
+
\frac{\tilde n_e\sigma_T}{4\pi}
\left[
\tilde I(E)+\tilde\zeta_{\alpha\beta}(E)\tilde e^\alpha\tilde e^\beta
\right],
\]

\[
\tilde{\mathcal C}_{\alpha\beta}(E,\tilde e)
=
-\tilde n_e\sigma_T P_{\alpha\beta}(E,\tilde e)
+
\frac{\tilde n_e\sigma_T}{4\pi}
\left[
\tilde S_\alpha{}^{\gamma}\tilde S_\beta{}^{\delta}
\tilde\zeta_{\gamma\delta}(E)
\right]^{TT}.
\]

Pseudocode:

```python
def thomson_collision_electron_frame(N_grid, dirs, screen_bases, ne_tilde, sigma_T):
    C = zeros_like(N_grid)
    for i, e_out in enumerate(dirs):
        C[i] -= ne_tilde * sigma_T * N_grid[i]
        source = zeros((2,2), dtype=complex)
        for j, e_in in enumerate(dirs):
            J = jones_projection(screen_bases[i], screen_bases[j])
            source += quad_weight[j] * J @ N_grid[j] @ J.conj().T
        C[i] += (3.0 * ne_tilde * sigma_T / (8.0 * pi)) * source
    return C
```

## 5.13 Tilted optical depth and electron-frame source

Photon propagation direction in the normal frame is \(e^\alpha\). Electron velocity is \(v_e^\alpha\). Electron-frame photon energy is

\[
\tilde E
=\Gamma_e E(1-v_{e\alpha}e^\alpha).
\]

Thus the direction-dependent scattering rate along the ray is

\[
\boxed{
\tilde\Gamma_T(e)
=a\tilde n_e x_e\sigma_T\Gamma_e(1-v_e\cdot e)
}
\]

if \(e^\alpha\) is the photon propagation direction. If an observer sky direction \(\hat n_{\rm sky}=-e\) is used instead, this becomes

\[
\tilde\Gamma_T(\hat n_{\rm sky})
=a\tilde n_e x_e\sigma_T\Gamma_e(1+v_e\cdot\hat n_{\rm sky}).
\]

Both conventions are allowed only if the metadata records which direction variable is used.

## 5.14 Recombination and reionization source wiring

First-pass ionization history is scalar:

\[
x_e=x_e(\tau).
\]

Normal-frame scalar visibility:

\[
\Gamma_T(\tau)=a(\tau)n_e(\tau)x_e(\tau)\sigma_T,
\]

\[
\kappa(\tau)=\int_\tau^{\tau_0}\Gamma_T(\tau')d\tau',
\]

\[
g(\tau)=\Gamma_T(\tau)e^{-\kappa(\tau)}.
\]

Tilted source evaluation replaces \(\Gamma_T\) by \(\tilde\Gamma_T(e)\) and evaluates the collision tensor in the electron frame.

Homogeneous reionization may be parameterized by a tanh model:

\[
x_e^{\rm rei}(z)=\frac{x_{e,\rm after}+x_{e,\rm before}}{2}
+\frac{x_{e,\rm after}-x_{e,\rm before}}{2}
\tanh\left(\frac{y_{\rm rei}-y(z)}{\Delta y}\right),
\]

where \(y=(1+z)^{3/2}\) is a common choice. The exact parameterization is a configuration-level history model, not hard-coded physics.

## 5.15 Tight-coupling and quadrupole startup

The explicit low-\(\ell\) state must contain \(I_{\alpha\beta}\) and \(E_{\alpha\beta}\). In a scalar FLRW limit, the conventional source combination is

\[
\Pi^m=\Theta_2^m-\sqrt6E_2^m.
\]

A stable TCA startup may place photon quadrupole and polarization on the approximate tight-coupling manifold:

\[
\pi_\gamma
=\frac{32}{45}k\tau_c(v_b+\sigma),
\qquad
E_2=\frac14\pi_\gamma.
\]

In the fully anisotropic PSTF code this becomes a tensor startup rule:

\[
\pi_{\gamma,\alpha\beta}
\sim
\frac{32}{45}\tau_c\,\mathcal S_{\alpha\beta}^{\rm shear+velocity},
\qquad
E_{\alpha\beta}\sim\frac14\pi_{\gamma,\alpha\beta},
\]

where \(\mathcal S_{\alpha\beta}^{\rm shear+velocity}\) must reduce to the scalar expression in the FLRW perturbative limit. The scalar expression is a limit test, not the full anisotropic authority equation.

---

# 6. Initial condition strategy

## 6.1 Background IC summary

Orthogonal branch:

\[
v_{s,i}^\alpha=0,
\qquad
q_{\alpha,i}=0,
\qquad
\pi_{\alpha\beta,i}=0
\]

unless a species has intrinsic anisotropic stress, such as a deliberately modeled anisotropic radiation component.

Tilted branch:

\[
v_{s,i}^\alpha\neq0
\]

is allowed for any chosen species. The total flux and anisotropic stress are then computed, not guessed:

\[
q_{\alpha,i}=\sum_s(\hat\rho_s+\hat p_s)\Gamma_s^2v_{s\alpha},
\]

\[
\pi_{\alpha\beta,i}=\sum_s(\hat\rho_s+\hat p_s)\Gamma_s^2v_{s\langle\alpha}v_{s\beta\rangle}.
\]

Then enforce Hamiltonian and Codazzi constraints.

## 6.2 Perturbative FLRW regular seed compatibility

The inherited solver specification requires the FLRW limit to recover regular adiabatic initial conditions used by standard Einstein--Boltzmann solvers. In a superhorizon startup \(x=k\tau\ll1\), the seed variables must reduce to the selected standard convention. The current baseline keeps the following symbolic contract:

\[
\delta X_i^{\rm solver}
\xrightarrow[\sigma,a,n,v\to0]{}
\delta X_i^{\rm FLRW,reg}.
\]

If the CAMB-compatible covariant variables are used, the implementation must include the corresponding series for

\[
\eta_{\rm cov},\quad
\Delta_\gamma,\quad
\Delta_\nu,\quad
\Delta_c,\quad
\Delta_b,\quad
q_\gamma,\quad
q_\nu,\quad
\pi_\nu,\quad
G_3,
\quad
Z.
\]

The code must keep these in a separate module:

```text
background/initial_conditions_flrw_regular.py
```

so that beyond-FLRW IC construction can reuse them without confusing them with Bianchi background anisotropy.

## 6.3 Tilted perturbation seed rule

For tilted baryon/electron matter, the clean first-pass prescription is:

1. Assign the regular seed in the electron frame.
2. Boost the radiation and matter perturbations to the normal frame.
3. Enforce constraints in the normal frame.

Symbolically:

\[
\delta\tilde X_i=X^{\rm FLRW,reg}_i,
\qquad
\delta X_i=\mathrm{Boost}^{-1}_{\bar v_e}\delta\tilde X_i.
\]

Leading-order PSTF boost rules must be implemented in a dedicated boost module, not scattered through collision code.

---

# 7. Numerical integration strategy

## 7.1 ODE/DAE form

The full state is

\[
Y=(Y_{\rm bg},Y_{\rm matter},Y_{\rm rad},Y_{\rm history}).
\]

The evolution equations have the form

\[
\dot Y=F(Y,\tau;\mathcal A),
\]

where \(\mathcal A\) is the Bianchi algebra and tetrad metadata.

Constraints are

\[
\mathcal C(Y,\tau)=0.
\]

The first release may use ODE evolution plus constraint projection:

\[
Y_{n+1}\leftarrow \Pi_{\mathcal C=0}(Y_{n+1}).
\]

A later release may expose an index-reduced DAE path.

## 7.2 Integrator choices

Recommended integrators:

1. Non-stiff background/ray transport: high-order adaptive explicit Runge--Kutta, e.g. DOP853.
2. Stiff Thomson/recombination era: implicit BDF/Radau or IMEX.
3. Tier A angular PDE: method-of-lines with angular spectral/grid discretization, then stiff ODE integration.
4. Tier B low-\(\ell\) PSTF: ODE/IMEX with collision block implicit and transport block explicit.

## 7.3 Constraint projection

Projection problem:

\[
\min_{\Delta Y}\|W\Delta Y\|^2
\quad\text{such that}\quad
\mathcal C(Y+\Delta Y)=0.
\]

Linearized step:

\[
J_C\Delta Y=-\mathcal C(Y),
\]

where

\[
(J_C)_{ij}=\frac{\partial C_i}{\partial Y_j}.
\]

Weighted least squares:

\[
\Delta Y=-W^{-1}J_C^T(J_CW^{-1}J_C^T)^{-1}\mathcal C(Y).
\]

Pseudocode:

```python
def project_constraints(Y, constraint_fn, weight_matrix, tol):
    C = constraint_fn(Y)
    if norm(C) < tol:
        return Y
    J = finite_or_autodiff_jacobian(constraint_fn, Y)
    Winv = inv(weight_matrix)
    A = J @ Winv @ J.T
    delta = -Winv @ J.T @ solve(A, C)
    return Y + delta
```

## 7.4 Cutoff and closure

Development cutoffs:

\[
L=4,
\quad
L=6,
\quad
L=8.
\]

Production low-\(\ell\) runs should not make a claim from \(L=2\) alone. \(L=2\) is diagnostic-only.

Closure options:

1. Zero closure: \(X_{A_{L+1}}=0\). Diagnostic only.
2. Free-streaming closure: approximate \(X_{L+1}\) from neighboring multipoles.
3. Tier-A calibrated closure: fit closure coefficients from angular truth runs.

---

# 8. PR list and WBS

The PR list below is the canonical development sequence. Each PR is a mergeable unit with a narrow purpose, required files, WBS tasks, tests, kill criteria, and done definition.

Scoring rule:

\[
\mathrm{Progress}(\%)=\sum_iw_i\frac{s_i}{10},
\]

where \(w_i\) is the PR weight and \(s_i\in[0,10]\) is the score.

Score interpretation:

- 0--2: notes only.
- 3--4: equations and interfaces frozen.
- 5--6: partial implementation.
- 7--8: smoke tests pass.
- 9--10: validation and diagnostics pass.

---

## PR-00 — SDD migration and authority freeze

**Weight:** 5  
**Depends on:** none  
**Requirement IDs:** F-12, P-01, P-05, N-03

### Purpose

Freeze the inherited project authority path in SDD form and declare the ADM-to-1+3 PSTF/tetrad migration complete.

### Must preserve from inherited baseline

\[
\text{exact Bianchi transport},
\quad
\text{electron-frame Thomson tensor},
\quad
n^a\text{-frame transport},
\quad
u_e^a\text{-frame collision/source},
\quad
\text{explicit }(\Theta_2,E_2),
\quad
\text{scalar }x_e(\tau)\text{ first pass},
\quad
\text{anisotropic propagation}.
\]

### WBS

1. Create `docs/SDD_PR_WBS.md`.
2. Create `docs/CONVENTIONS.md`.
3. Create `docs/FRAME_POLICY.md`.
4. Create `docs/TRACEABILITY.md`.
5. Mark observational/statistical discussion as external to solver SDD.

### Deliverables

```text
docs/SDD_PR_WBS.md
docs/CONVENTIONS.md
docs/FRAME_POLICY.md
docs/TRACEABILITY.md
```

### Tests

- Documentation lint: every module has a convention owner.
- Search test: no ADM-primary terminology appears as the solver architecture.
- Frame test: transport/collision frame split appears in exactly one authority section and is referenced elsewhere.

### Kill criteria

- ADM variables are reintroduced as the primary solver state.
- Collision and transport frames are ambiguous.
- Observational interpretation is mixed into solver-core requirements.

### Done definition

The SDD is the authoritative implementation document and later PRs can link to specific requirement IDs.

---

## PR-01 — Bianchi algebra registry for all eleven types

**Weight:** 8  
**Depends on:** PR-00  
**Requirement IDs:** F-01, P-02, P-03, P-08, N-05

### Purpose

Implement all Bianchi types through one algebra object.

### Mathematical contract

\[
C^\gamma{}_{\alpha\beta}
=2a_{[\alpha}\delta_{\beta]}{}^\gamma
+\epsilon_{\alpha\beta\delta}n^{\delta\gamma},
\qquad
n_{\alpha\beta}a^\beta=0.
\]

### WBS

1. Implement `BianchiAlgebra` dataclass.
2. Implement canonical constructors for I, II, III, IV, V, VI\(_0\), VI\(_h\), VII\(_0\), VII\(_h\), VIII, IX.
3. Store class label A/B.
4. Store \(h\)-parameter convention.
5. Store axis permutation metadata.
6. Validate antisymmetry of \(C^\gamma{}_{\alpha\beta}\).
7. Validate Jacobi identity.
8. Add branch metadata: `orthogonal_allowed`, `tilted_allowed`, and `constraint_policy_required`.

### Deliverables

```text
algebra/bianchi_types.py
algebra/structure_constants.py
algebra/jacobi.py
tests/test_all_bianchi_types.py
tests/test_jacobi_identity.py
```

### Pseudocode

```python
for type_name in ALL_ELEVEN_TYPES:
    alg = build_bianchi_algebra(type_name, params=default_params(type_name))
    assert antisymmetric_in_lower_indices(alg.C)
    assert norm(alg.n @ alg.a) < atol
    assert alg.supports_branch("orthogonal")
    assert alg.supports_branch("tilted")
```

### Smoke tests

- Every type builds.
- Every type returns finite \(C^\gamma{}_{\alpha\beta}\).
- Jacobi residual below tolerance.
- Class A has \(a_\alpha=0\).
- Class B has nonzero \(a_\alpha\) and satisfies \(n_{\alpha\beta}a^\beta=0\).

### Kill criteria

- Any Bianchi type is treated as a special solver backend.
- VII\(_h\) or I is privileged in the architecture.
- Tilted branch is disabled for a type without a mathematical reason encoded in config.

### Done definition

A single algebra API can instantiate all eleven types and pass Jacobi tests.

---

## PR-02 — Tetrad geometry operators

**Weight:** 9  
**Depends on:** PR-01  
**Requirement IDs:** F-02, P-02, N-05

### Purpose

Generate connection, Ricci, divergence, curl, and PSTF derivative operators from the Bianchi algebra.

### Mathematical contract

\[
2\Gamma_{\gamma\alpha\beta}
=C_{\alpha\beta\gamma}-C_{\beta\gamma\alpha}+C_{\gamma\alpha\beta}.
\]

\[
{}^3R^\delta{}_{\gamma\alpha\beta}
=
\Gamma^\epsilon{}_{\beta\gamma}\Gamma^\delta{}_{\alpha\epsilon}
-
\Gamma^\epsilon{}_{\alpha\gamma}\Gamma^\delta{}_{\beta\epsilon}
-C^\epsilon{}_{\alpha\beta}\Gamma^\delta{}_{\epsilon\gamma}.
\]

### WBS

1. Implement `spatial_connection(C)`.
2. Implement `spatial_riemann_ricci(C,Gamma)`.
3. Implement `stf_rank_l` utilities for \(\ell=1\ldots8\).
4. Implement divergence and curl of rank-1 and rank-2 tensors.
5. Implement generic homogeneous covariant derivative for PSTF arrays.
6. Add operator identity tests.
7. Add type sweep tests over all eleven algebras.

### Deliverables

```text
geometry/tetrad_connection.py
geometry/spatial_operators.py
geometry/spatial_ricci.py
geometry/pstf.py
tests/test_spatial_connection.py
tests/test_spatial_ricci.py
tests/test_pstf_operators.py
```

### Pseudocode

```python
alg = build_bianchi_algebra("VI_h", params)
Gamma = spatial_connection(alg.C)
Riem, Ric, R, S = spatial_riemann_ricci(alg.C, Gamma)
assert is_symmetric(Ric, atol)
assert abs(trace(S)) < atol
```

### Smoke tests

- Type I Ricci scalar is zero.
- Symmetric part of Ricci is symmetric to tolerance.
- \({}^3S_{\alpha\beta}\) is trace-free.
- Curl of an isotropic tensor vanishes.

### Kill criteria

- Connection sign convention is undocumented.
- Ricci calculation is copied separately per type.
- PSTF trace removal fails at rank 2.

### Done definition

Geometry operators are algebra-generated, type-generic, and tested across all eleven types.

---

## PR-03 — Orthogonal background IC and constraints

**Weight:** 8  
**Depends on:** PR-02  
**Requirement IDs:** F-03, P-04, P-07, N-01

### Purpose

Construct orthogonal initial conditions satisfying Gauss/Hamiltonian and Codazzi constraints.

### Mathematical contract

\[
q_\alpha=0,
\qquad
\pi_{\alpha\beta}=0
\]

for perfect fluids,

\[
D^\beta\sigma_{\alpha\beta}=0,
\]

and

\[
3H^2=\kappa\rho+\Lambda+\sigma^2-\frac12{}^3R.
\]

### WBS

1. Implement `BackgroundState`.
2. Implement trace-free shear parameterization.
3. Implement orthogonal matter state builder.
4. Implement Hamiltonian residual.
5. Implement Codazzi residual.
6. Implement `solve_H`, `solve_curvature_scale`, `project_shear_amplitude` policies.
7. Add all-type orthogonal IC smoke tests.

### Deliverables

```text
background/state.py
background/constraints.py
background/initial_conditions.py
tests/test_orthogonal_ic_constraints.py
```

### Pseudocode

```python
for type_name in ALL_ELEVEN_TYPES:
    alg = build_bianchi_algebra(type_name, default_params(type_name))
    geom = build_geometry(alg)
    state = build_orthogonal_ic(geom, matter, shear_shape, closure="solve_H")
    res = constraint_residuals(state, geom)
    assert res.hamiltonian < tol
    assert norm(res.codazzi) < tol
```

### Smoke tests

- All eleven types construct an orthogonal IC or fail with a clear user-configuration error.
- Type I with \(\sigma=0\) gives FLRW flat constraint.
- Type V with isotropic curvature and \(\sigma=0\) gives open-FLRW-like constraint.

### Kill criteria

- Shear is inserted without constraint projection.
- Hamiltonian closure silently changes matter density without metadata.
- Orthogonal branch leaves nonzero total flux.

### Done definition

Orthogonal ICs are generated on the constraint surface and produce machine-readable residuals.

---

## PR-04 — Tilted species and tilted IC closure

**Weight:** 10  
**Depends on:** PR-03  
**Requirement IDs:** F-04, P-03, P-04, P-05, P-08

### Purpose

Implement tilted matter as a first-class branch for every Bianchi type.

### Mathematical contract

\[
u_s^a=\Gamma_s(n^a+v_s^a),
\qquad
\Gamma_s=(1-v_s^2)^{-1/2}.
\]

\[
q_\alpha^{(s)}=(\hat\rho_s+\hat p_s)\Gamma_s^2v_{s\alpha},
\qquad
\pi_{\alpha\beta}^{(s)}=(\hat\rho_s+\hat p_s)\Gamma_s^2v_{s\langle\alpha}v_{s\beta\rangle}.
\]

\[
D^\beta\sigma_{\alpha\beta}=\kappa\sum_s q_\alpha^{(s)}.
\]

### WBS

1. Implement species dataclass with rest-frame variables.
2. Implement normal-frame stress-energy decomposition.
3. Implement total matter assembler.
4. Implement tilted Codazzi projection policies.
5. Implement electron/baryon/CDM tilt separation.
6. Implement small-tilt expansion tests.
7. Implement all-type tilted IC smoke tests.

### Deliverables

```text
matter/species.py
matter/tilt.py
matter/stress_energy.py
background/tilted_initial_conditions.py
tests/test_tilt_stress_energy.py
tests/test_tilted_ic_constraints_all_types.py
```

### Pseudocode

```python
species = [CDM(rho_c, v=v_c), Baryon(rho_b, v=v_b), Electron(rho_e, v=v_e)]
matter = sum_species_stress_energy(species)
sigma, matter = project_tilted_codazzi(sigma_guess, matter, geom, policy="solve_shear_offdiag")
assert norm(div_rank2(sigma, geom.Gamma) - kappa * matter.q) < tol
```

### Smoke tests

- \(v_s=0\) exactly recovers orthogonal stress-energy.
- Small tilt recovers \(q_\alpha\simeq(\rho+p)v_\alpha\).
- Electron tilt can differ from CDM tilt.
- All eleven types support tilted IC construction or return a controlled constraint-projection failure.

### Kill criteria

- All species are forced to share one tilt.
- Transport frame is changed to the matter frame.
- Tilt is included in visibility but not in stress-energy constraints.

### Done definition

Tilted branch produces constraint-satisfying initial data with species-resolved velocities and frame metadata.

---

## PR-05 — 1+3 PSTF background RHS

**Weight:** 10  
**Depends on:** PR-03, PR-04  
**Requirement IDs:** F-05, P-04, P-07, P-08, N-01

### Purpose

Evolve \(H\), \(\sigma_{\alpha\beta}\), matter variables, and algebra/geometry quantities consistently in the 1+3 PSTF/tetrad formulation.

### Mathematical contract

\[
\dot H
=-H^2-\frac23\sigma^2-\frac16\kappa(\rho+3p)+\frac13\Lambda.
\]

\[
\dot\sigma_{\alpha\beta}
=-3H\sigma_{\alpha\beta}-{}^3S_{\alpha\beta}+\kappa\pi_{\alpha\beta}.
\]

\[
\dot\rho
=-3H(\rho+p)-D^\alpha q_\alpha-\sigma^{\alpha\beta}\pi_{\alpha\beta}.
\]

### WBS

1. Implement background RHS for orthogonal perfect fluids.
2. Implement tilted total-fluid RHS.
3. Implement species-level conservation optional path.
4. Implement geometry recomputation at each RHS call.
5. Implement constraint residual output at each time sample.
6. Implement FLRW, Bianchi I, and all-type smoke tests.

### Deliverables

```text
background/rhs.py
matter/conservation.py
background/evolution.py
tests/test_background_rhs_flrw.py
tests/test_background_rhs_bianchiI.py
tests/test_background_rhs_all_types_smoke.py
```

### Pseudocode

```python
def background_rhs(tau, Y, alg_model, matter_model):
    state = unpack_background(Y)
    alg = alg_model.physical_algebra(state)
    geom = build_geometry(alg)
    matter = matter_model.normal_frame_state(state)

    sigma2 = 0.5 * contract2(state.sigma, state.sigma)
    Hdot = -state.H**2 - (2.0/3.0)*sigma2 - (kappa/6.0)*(matter.rho + 3*matter.p) + Lambda/3.0
    sigmadot = -3*state.H*state.sigma - geom.S3 + kappa*matter.pi
    rhodot = -3*state.H*(matter.rho + matter.p) - div_vector(matter.q, geom.Gamma) - contract2(state.sigma, matter.pi)

    return pack(Hdot, sigmadot, rhodot, other_species_rhs)
```

### Smoke tests

- FLRW limit remains isotropic.
- Bianchi I perfect fluid gives \(\dot\sigma+3H\sigma=0\).
- Constraint residuals do not grow catastrophically in short runs.
- Class B runs exercise nonzero \(a_\alpha\) operators.

### Kill criteria

- Class B terms are effectively ignored.
- Shear equation uses ADM-specific state variables as primary input.
- Constraint residuals are not computed.

### Done definition

The background RHS is type-generic, branch-generic, and passes analytic limit checks.

---

## PR-06 — Weyl tensor and Bianchi-identity diagnostics

**Weight:** 6  
**Depends on:** PR-05  
**Requirement IDs:** P-04, N-01

### Purpose

Add diagnostics derived from Ricci and Bianchi identities to catch sign, connection, and constraint errors.

### Mathematical contract

\[
H^{\rm Weyl}_{\alpha\beta}=(\mathrm{curl}\,\sigma)_{\alpha\beta}.
\]

\[
E_{\alpha\beta}
=-\dot\sigma_{\alpha\beta}
-2H\sigma_{\alpha\beta}
-\sigma_{\gamma\langle\alpha}\sigma_{\beta\rangle}{}^\gamma
+\frac12\kappa\pi_{\alpha\beta}.
\]

Additional divergence constraints may be added as optional diagnostics once sign conventions are frozen.

### WBS

1. Implement `weyl_from_shear_rhs`.
2. Implement `Hweyl_from_curl_sigma`.
3. Add consistency comparison to any evolved Weyl variables.
4. Add diagnostic plots/logs.
5. Add all-type smoke tests.

### Deliverables

```text
background/weyl.py
validation/weyl_diagnostics.py
tests/test_hweyl_curl_sigma.py
```

### Smoke tests

- FLRW gives \(E_{\alpha\beta}=0\), \(H^{\rm Weyl}_{\alpha\beta}=0\).
- Bianchi I gives \(H^{\rm Weyl}_{\alpha\beta}=0\) for homogeneous diagonal shear in a compatible frame.
- Trace-free checks pass.

### Kill criteria

- Magnetic Weyl tensor is named ambiguously as `H`.
- Weyl diagnostics use a different connection convention from geometry module.

### Done definition

Weyl diagnostics are available in validation packets and catch deliberate sign perturbations in tests.

---

## PR-07 — Photon geodesic and polarization basis transport

**Weight:** 10  
**Depends on:** PR-05  
**Requirement IDs:** F-06, P-05, P-07

### Purpose

Implement exact tetrad photon transport on Bianchi backgrounds.

### Mathematical contract

\[
k^a=E(n^a+e^a),
\qquad
e^\alpha e_\alpha=1.
\]

\[
\frac{dk^A}{d\lambda}+\Gamma^A{}_{BC}k^Bk^C=0.
\]

Hard redshift check:

\[
\frac{d\ln(aE)}{d\tau}
=-\sigma_{\alpha\beta}e^\alpha e^\beta.
\]

### WBS

1. Build spacetime tetrad connection from \(H\), \(\sigma\), and spatial connection.
2. Implement geodesic RHS for \(E,e^\alpha\).
3. Implement sky-direction and propagation-direction metadata.
4. Implement screen basis transport.
5. Implement \(Q/U\) phase convention metadata.
6. Add norm-preservation tests.
7. Add FLRW redshift test.
8. Add Bianchi I analytic redshift test.

### Deliverables

```text
photons/geodesics.py
photons/screen_basis.py
photons/stokes.py
tests/test_photon_norm.py
tests/test_flrw_redshift.py
tests/test_bianchiI_redshift.py
```

### Smoke tests

- \(e_\alpha e^\alpha=1\) preserved.
- Screen basis remains orthonormal and transverse.
- FLRW gives \(aE=\) constant.
- Bianchi I redshift matches the covariant-momentum analytic check.

### Kill criteria

- Direction variable sign is not recorded.
- Polarization phase convention is implicit.
- Ray transport uses FLRW geodesic kernels.

### Done definition

Photon and screen-basis transport are type-generic and pass norm/redshift checks.

---

## PR-08 — PSTF radiation multipole representation

**Weight:** 8  
**Depends on:** PR-02, PR-07  
**Requirement IDs:** F-07, P-06, N-04

### Purpose

Implement low-\(\ell\) radiation state representation in PSTF multipoles.

### Mathematical contract

\[
I(E,e)=\sum_{\ell=0}^{L}I_{A_\ell}(E)e^{\langle A_\ell\rangle}.
\]

\[
E_{A_\ell},B_{A_\ell}\quad \ell\ge2.
\]

Projection normalization is fixed by

\[
N_\ell=\frac{4\pi}{2\ell+1}\frac{\ell!}{(2\ell-1)!!}.
\]

### WBS

1. Implement PSTF tensor storage by rank.
2. Implement projection from angular samples to PSTF coefficients.
3. Implement reconstruction from PSTF coefficients to angular samples.
4. Implement \(E/B\) PSTF storage.
5. Implement rank truncation policy.
6. Add \(L=4,6,8\) shape tests.

### Deliverables

```text
photons/pstf_radiation.py
collision/multipole_projection.py
tests/test_pstf_projection_reconstruction.py
tests/test_radiation_state_shapes.py
```

### Pseudocode

```python
rad = RadiationPSTFState(L=6)
rad.I[0] = scalar_monopole
rad.I[2] = quadrupole_tensor
assert abs(trace(rad.I[2])) < atol
samples = reconstruct_on_sphere(rad, dirs)
rad2 = project_from_sphere(samples, dirs, weights, L=6)
assert close(rad, rad2, rtol)
```

### Smoke tests

- Rank-2 tensors are trace-free.
- Projection/reconstruction is exact for polynomial test functions up to \(L\).
- \(L=2\) is allowed only as diagnostic unless explicitly overridden.

### Kill criteria

- Polarization is added only as post-processing.
- PSTF normalization is undocumented.
- Rank truncation silently discards required source terms.

### Done definition

Radiation multipoles are represented, projected, reconstructed, and truncated with explicit metadata.

---

## PR-09 — Electron-frame Thomson tensor

**Weight:** 10  
**Depends on:** PR-04, PR-08  
**Requirement IDs:** F-08, P-05, P-06

### Purpose

Implement exact classical Thomson scattering in the electron frame and project it into the solver representation.

### Mathematical contract

\[
\tilde{\mathcal C}_{AB}^{\rm Th}
=
-\tilde n_e\sigma_TN_{AB}
+\frac{3\tilde n_e\sigma_T}{8\pi}
\int d\Omega' J_{AC}N_{CD}J^*_{BD}.
\]

Electron-frame source tensor:

\[
\tilde\zeta_{\alpha\beta}
=\frac34\tilde I_{\alpha\beta}+\frac92\tilde E_{\alpha\beta}.
\]

### WBS

1. Implement normal-to-electron frame photon direction and energy transform.
2. Implement screen-basis transformation.
3. Implement angular-grid Thomson operator.
4. Implement PSTF projected Thomson source.
5. Implement linearity tests.
6. Implement isotropic-null polarization test.
7. Implement pure quadrupole response test.

### Deliverables

```text
collision/electron_frame.py
collision/thomson_tensor.py
collision/multipole_projection.py
tests/test_thomson_linearity.py
tests/test_thomson_isotropic_null.py
tests/test_thomson_quadrupole_response.py
```

### Pseudocode

```python
def collision_normal_frame(rad_state, electron_velocity, history, geom):
    rad_tilde = boost_radiation_to_electron_frame(rad_state, electron_velocity)
    C_tilde = thomson_collision_electron_frame(rad_tilde, history.ne_tilde)
    return boost_collision_to_normal_frame(C_tilde, electron_velocity)
```

### Smoke tests

- \(C[aN_1+bN_2]=aC[N_1]+bC[N_2]\).
- Isotropic unpolarized radiation produces no polarization source.
- Orthogonal electron frame with scalar quadrupole recovers standard source combination under FLRW limit.

### Kill criteria

- Collision is implemented only by a hard-coded FLRW \(\Pi\) shortcut.
- Electron-frame transform is skipped when \(v_e\neq0\).
- Thomson operator changes photon number in isotropic equilibrium.

### Done definition

The collision operator is electron-frame exact, reusable by Tier A and Tier B, and tested against limiting cases.

---

## PR-10 — Ionization history, visibility, and reionization source

**Weight:** 7  
**Depends on:** PR-09  
**Requirement IDs:** F-09, P-05, P-06

### Purpose

Wire scalar ionization history and homogeneous reionization into the anisotropic source machinery.

### Mathematical contract

\[
\Gamma_T=a n_ex_e\sigma_T,
\qquad
\kappa(\tau)=\int_\tau^{\tau_0}\Gamma_Td\tau',
\qquad
g=\Gamma_Te^{-\kappa}.
\]

Tilted:

\[
\tilde\Gamma_T(e)=a\tilde n_ex_e\sigma_T\Gamma_e(1-v_e\cdot e).
\]

### WBS

1. Implement external recombination-history adapter.
2. Implement simple internal history for tests.
3. Implement visibility integration.
4. Implement homogeneous tanh reionization option.
5. Implement tilted visibility source path.
6. Add visibility normalization tests.
7. Add reionization on/off low-\(\ell\) source tests.

### Deliverables

```text
history/recombination.py
history/reionization.py
history/visibility.py
tests/test_visibility_normalization.py
tests/test_reionization_source_onoff.py
```

### Smoke tests

- \(g(\tau)\) is nonnegative.
- Optical depth decreases toward observer under the chosen convention.
- Reionization on/off changes the polarization source.
- Tilted visibility reduces to scalar visibility when \(v_e=0\).

### Kill criteria

- Direction-dependent atomic recombination is treated as required in first release.
- Tilted optical-depth sign convention is ambiguous.
- Reionization source is absent while low-\(\ell\) polarization is claimed.

### Done definition

History and visibility are source-ready, branch-aware, and convention-logged.

---

## PR-11 — Quadrupole-aware tight-coupling startup

**Weight:** 7  
**Depends on:** PR-08, PR-10  
**Requirement IDs:** P-06, N-02

### Purpose

Provide stable startup for explicit \(I_{\alpha\beta}\), \(E_{\alpha\beta}\), and related low-\(\ell\) radiation moments.

### Mathematical contract

Scalar limit:

\[
\pi_\gamma=\frac{32}{45}k\tau_c(v_b+\sigma),
\qquad
E_2=\frac14\pi_\gamma.
\]

Anisotropic startup uses tensor source \(\mathcal S_{\alpha\beta}^{\rm shear+velocity}\) with this scalar limit.

### WBS

1. Implement explicit quadrupole state initialization.
2. Implement scalar-limit TCA test.
3. Implement anisotropic shear-source startup placeholder.
4. Implement stiff switching criteria based on \(\Gamma_T/H\).
5. Add diagnostics for initial transients.

### Deliverables

```text
tca/quadrupole_startup.py
tca/stiff_closure.py
tests/test_tca_scalar_limit.py
tests/test_quadrupole_startup_stability.py
```

### Smoke tests

- Startup does not introduce large unphysical transients.
- FLRW scalar limit reproduces expected hierarchy ordering.
- Setting quadrupole to zero is available only as diagnostic mode.

### Kill criteria

- \(E_2\) is omitted from startup.
- Quadrupole is hidden inside a post-processing shortcut.
- TCA branch ignores shear terms in anisotropic mode.

### Done definition

Explicit quadrupole and polarization startup are stable and documented.

---

## PR-12 — Initial perturbation seed compatibility module

**Weight:** 6  
**Depends on:** PR-11  
**Requirement IDs:** P-07, N-03

### Purpose

Ensure the solver recovers regular adiabatic perturbation seeds in the FLRW limit while allowing beyond-FLRW background anisotropy.

### Mathematical contract

\[
\delta X_i^{\rm solver}\to\delta X_i^{\rm FLRW,reg}
\quad\text{as}\quad
\sigma,a,n,v\to0.
\]

Tilted branch:

\[
\delta X_i=\mathrm{Boost}^{-1}_{\bar v_e}\delta\tilde X_i.
\]

### WBS

1. Implement FLRW regular seed module.
2. Implement frame selection for seed assignment.
3. Implement leading-order PSTF boost rules.
4. Implement constraint projection after seed insertion.
5. Add FLRW-limit seed tests.

### Deliverables

```text
background/initial_conditions_flrw_regular.py
photons/pstf_boosts.py
background/perturbation_seed.py
tests/test_flrw_regular_seed_limit.py
tests/test_tilted_seed_boost.py
```

### Smoke tests

- Orthogonal FLRW limit reproduces selected regular seed convention.
- Tilted seed with \(v_e\to0\) recovers orthogonal seed.
- Constraint projection after seed insertion is finite.

### Kill criteria

- Bianchi anisotropy is mistaken for an FLRW scalar perturbation gauge mode.
- Seed frame is unspecified.
- Boost rules are implemented only inside Thomson collision code.

### Done definition

Initial perturbation seed generation is modular, frame-aware, and FLRW-compatible.

---

## PR-13 — Tier A angular transport solver

**Weight:** 10  
**Depends on:** PR-07, PR-09, PR-10  
**Requirement IDs:** F-10, P-05, P-06, N-02

### Purpose

Implement the angular reference solver for brightness matrix transport.

### Mathematical contract

\[
\mathcal L_B[N_{AB}(E,e)]
=
\mathcal C_{AB}^{\rm Th}[N;u_e].
\]

The transport operator includes:

1. photon direction advection,
2. energy/redshift derivative,
3. polarization basis rotation,
4. collision/source in the electron frame.

### WBS

1. Choose angular representation: quadrature grid first, spectral optional.
2. Implement angular advection from ray transport.
3. Implement energy-bin or brightness-temperature representation.
4. Implement polarization-basis rotation term.
5. Wire exact Thomson operator.
6. Add reference serialization.
7. Add low-resolution all-type smoke tests.

### Deliverables

```text
solvers/tierA_angular.py
solvers/angular_grid.py
solvers/time_integrators.py
tests/test_tierA_isotropic_static.py
tests/test_tierA_bianchi_smoke.py
```

### Smoke tests

- Isotropic unpolarized radiation remains collision equilibrium.
- FLRW free streaming behaves as expected.
- Bianchi anisotropic run completes at low angular resolution.
- Tier A output can be projected to PSTF moments.

### Kill criteria

- Energy/redshift term is omitted for specific intensity variables.
- Polarization rotation is ignored.
- Collision and transport use inconsistent direction conventions.

### Done definition

Tier A can act as a reference backend for low-resolution validation.

---

## PR-14 — Tier B low-\(\ell\) PSTF solver

**Weight:** 10  
**Depends on:** PR-08, PR-09, PR-11  
**Requirement IDs:** F-10, P-06, N-04

### Purpose

Implement the production low-\(\ell\) PSTF hierarchy.

### Mathematical contract

\[
\mathbf X_L'
=
\mathsf L_B\mathbf X_L+
\mathsf C_T\mathbf X_L+
\mathbf S_L,
\qquad
\mathbf X_L=\{I_{A_\ell},E_{A_\ell},B_{A_\ell}\}_{\ell\le L}.
\]

### WBS

1. Implement multipole state vector flatten/unflatten.
2. Implement geometric transport coupling in PSTF basis.
3. Implement Thomson collision projection.
4. Implement source vector assembly.
5. Implement \(L=4,6,8\) cutoffs.
6. Implement closure policies.
7. Compare against Tier A.

### Deliverables

```text
solvers/tierB_pstf.py
solvers/pstf_state_vector.py
solvers/pstf_closure.py
tests/test_tierB_shapes.py
tests/test_tierB_vs_tierA.py
```

### Pseudocode

```python
def tierB_rhs(tau, X_flat, bg_solution, history, config):
    X = unpack_pstf_state(X_flat, L=config.L)
    bg = bg_solution.eval(tau)
    geom = build_geometry(bg.algebra)
    transport = pstf_transport_operator(X, bg, geom)
    collision = pstf_thomson_collision(X, bg.electron_velocity, history.eval(tau))
    source = pstf_source_vector(X, bg, history.eval(tau))
    return flatten(transport + collision + source)
```

### Smoke tests

- \(L=4\), \(L=6\), \(L=8\) all run.
- \(L=2\) requires diagnostic override.
- Tier B agrees qualitatively with Tier A on low moments.
- FLRW limit recovers standard decoupling structure under chosen normalization.

### Kill criteria

- Production path uses only \(C_\ell\)-style isotropic summaries internally.
- \(E/B\) states are absent.
- \(L\)-closure is undocumented.

### Done definition

Tier B is the default production solver and is benchmarked against Tier A.

---

## PR-15 — Anisotropic source-to-observer propagator

**Weight:** 8  
**Depends on:** PR-07, PR-14  
**Requirement IDs:** F-11, P-05, P-06

### Purpose

Export source-integrated observer quantities without assuming FLRW scalar Bessel kernels.

### Mathematical contract

The anisotropic propagator is represented abstractly as

\[
\mathcal G^{XX'}_{\ell m,\ell' m'}(\tau_0,\tau)
\]

or, in PSTF variables,

\[
X_{A_\ell}(\tau_0)
=
\int d\tau\ \mathcal G_{A_\ell}{}^{B_{\ell'}}(\tau_0,\tau)S_{B_{\ell'}}(\tau).
\]

The code must not replace this by a single FLRW \(j_\ell\) kernel except in explicit FLRW validation mode.

### WBS

1. Implement forward propagation of source moments.
2. Implement optional adjoint propagation for efficient source integration.
3. Implement observer tetrad and screen basis at \(\tau_0\).
4. Implement export to \(T,Q,U\) samples or harmonic coefficients.
5. Add FLRW-kernel recovery test as a limit.
6. Add anisotropic propagation metadata.

### Deliverables

```text
output/observer_export.py
solvers/source_propagator.py
solvers/adjoint_propagator.py
tests/test_flrw_kernel_limit.py
tests/test_anisotropic_propagator_shapes.py
```

### Smoke tests

- Observer output shape is correct.
- FLRW validation mode recovers scalar kernel behavior.
- Anisotropic mode produces mode coupling rather than forced diagonal \(\ell m\).

### Kill criteria

- FLRW \(j_\ell\) is used as production propagator.
- Polarization rotation is absent from propagation.
- Observer output lacks convention metadata.

### Done definition

Source-to-observer propagation is anisotropic by construction and exports neutral solver outputs.

---

## PR-16 — Integrators, stiffness handling, and checkpointing

**Weight:** 7  
**Depends on:** PR-05, PR-13, PR-14  
**Requirement IDs:** N-01, N-02, N-03

### Purpose

Provide robust integration infrastructure for background, photon transport, and radiation hierarchy.

### WBS

1. Implement explicit RK wrapper.
2. Implement implicit BDF/Radau wrapper.
3. Implement IMEX splitting for transport/collision.
4. Implement constraint projection hooks.
5. Implement checkpoint/restart.
6. Implement runtime metadata and tolerances.
7. Add stiffness regression tests.

### Deliverables

```text
solvers/integrators.py
solvers/imex.py
solvers/checkpoint.py
output/metadata.py
tests/test_integrator_restart.py
tests/test_stiff_collision_block.py
```

### Pseudocode

```python
while tau < tau_final:
    Y = explicit_transport_step(Y, dt)
    Y = implicit_collision_step(Y, dt)
    if step % project_every == 0:
        Y = project_constraints(Y, constraint_fn, W, tol)
    write_checkpoint_if_needed(Y, metadata)
```

### Smoke tests

- Restart gives bitwise or tolerance-level reproducibility.
- Stiff collision test remains stable.
- Constraint projection can be toggled and logged.

### Kill criteria

- Integrator silently changes units or time variable.
- Stiff solver branch does not expose tolerances.
- Checkpoints omit algebra/frame metadata.

### Done definition

Long runs can be restarted, reproduced, and diagnosed.

---

## PR-17 — Solver-output API and observer-neutral exports

**Weight:** 6  
**Depends on:** PR-15  
**Requirement IDs:** F-11, F-12, N-03, N-06

### Purpose

Define the output API from solver core to external observables/statistics layer.

### Output objects

Allowed outputs:

\[
T(\hat n),\quad Q(\hat n),\quad U(\hat n),
\]

\[
a_{\ell m}^{T},\quad a_{\ell m}^{E},\quad a_{\ell m}^{B},
\]

\[
I_{A_\ell},\quad E_{A_\ell},\quad B_{A_\ell},
\]

and metadata.

No p-values, anomaly labels, or data-release interpretation are produced by the solver core.

### WBS

1. Define `SolverOutput` schema.
2. Define convention metadata schema.
3. Define unit metadata schema.
4. Define branch/type metadata schema.
5. Implement HDF5/NPZ/Zarr export.
6. Add reader tests.

### Deliverables

```text
output/schema.py
output/writers.py
output/readers.py
tests/test_output_schema.py
tests/test_metadata_complete.py
```

### Smoke tests

- Output round-trips through writer/reader.
- Missing convention metadata fails validation.
- Solver output can be consumed by a dummy observables layer.

### Kill criteria

- Statistical interpretation is embedded in solver output.
- Metadata does not include Bianchi type and frame convention.
- Harmonic/spin convention is missing when harmonic output is written.

### Done definition

Solver outputs are portable, self-describing, and observer-analysis neutral.

---

## PR-18 — Validation matrix over types and branches

**Weight:** 10  
**Depends on:** PR-17  
**Requirement IDs:** P-03, P-04, P-07, P-08, N-01, N-05

### Purpose

Create a validation matrix covering all eleven Bianchi types and both orthogonal and tilted branches.

### Required validation dimensions

\[
11\ \text{types}
\times
2\ \text{branches}
\times
\{\text{background},\text{photon},\text{collision},\text{Tier B smoke}\}.
\]

### WBS

1. Implement all-type orthogonal background validation.
2. Implement all-type tilted IC validation.
3. Implement photon redshift/norm validation sweep.
4. Implement Thomson collision validation sweep.
5. Implement Tier B short-run sweep.
6. Implement reports with residual tables.
7. Implement failure classification.

### Deliverables

```text
validation/run_type_branch_matrix.py
validation/reporting.py
reports/VALIDATION_MATRIX.md
tests/test_validation_matrix_smoke.py
```

### Smoke tests

- Every type/branch has a row in the report.
- Failures are explicit, not silent skips.
- Constraint residuals are recorded.
- Runtime and tolerances are recorded.

### Kill criteria

- Validation covers only Type I or VII\(_h\).
- Tilted branches are not included.
- Constraint failures are downgraded to warnings without user override.

### Done definition

A full type/branch validation matrix is generated by one command.

---

## PR-19 — Cutoff and convergence campaign

**Weight:** 6  
**Depends on:** PR-18  
**Requirement IDs:** N-04

### Purpose

Quantify low-\(\ell\) cutoff behavior for \(L=4,6,8\) and optionally larger \(L\).

### WBS

1. Run Tier B at \(L=4\), \(6\), \(8\) for selected type/branch grid.
2. Compare background-independent numerical quantities.
3. Compare radiation multipole norms.
4. Compare source-to-observer exports.
5. Generate convergence report.

### Deliverables

```text
experiments/run_cutoff_convergence.py
reports/CUTOFF_CONVERGENCE.md
figures/convergence_multipole_norms.png
```

### Smoke tests

- All configured cutoffs run.
- Multipole norm differences are finite.
- Runtime/memory are logged.

### Kill criteria

- \(L=4\) alone is treated as converged.
- Higher \(L\) changes output wildly without diagnosis.
- Closure policy is not recorded.

### Done definition

A convergence report justifies the selected default cutoff for development and production runs.

---

## PR-20 — Performance, vectorization, and reproducibility

**Weight:** 5  
**Depends on:** PR-19  
**Requirement IDs:** N-03, N-05

### Purpose

Make the research solver practical for parameter exploration.

### WBS

1. Profile geometry recomputation.
2. Cache type-dependent algebraic tensors.
3. Vectorize PSTF contractions.
4. Add optional JAX/Numba backend if useful.
5. Add deterministic random seed and config hashing.
6. Add CI runtime limits.

### Deliverables

```text
performance/profile_geometry.py
performance/profile_pstf.py
utils/cache.py
utils/config_hash.py
reports/PERFORMANCE_BASELINE.md
```

### Smoke tests

- Cached and uncached geometry agree.
- Config hash changes when physical conventions change.
- Performance report is generated.

### Kill criteria

- Optimization changes numerical results beyond tolerance.
- Cached tensors ignore time-dependent tetrad scaling.
- Reproducibility metadata is incomplete.

### Done definition

The solver is fast enough for systematic type/branch scans and every run is reproducible.

---

## PR-21 — Release candidate packaging

**Weight:** 5  
**Depends on:** PR-20  
**Requirement IDs:** F-12, N-03, N-06

### Purpose

Package the solver as a research release candidate.

### WBS

1. Freeze public API.
2. Freeze config schema.
3. Write user guide.
4. Write developer guide.
5. Include validation matrix artifacts.
6. Include minimal examples for all types and both branches.
7. Create release checklist.

### Deliverables

```text
docs/USER_GUIDE.md
docs/DEVELOPER_GUIDE.md
docs/CONFIG_SCHEMA.md
examples/all_types_orthogonal.py
examples/all_types_tilted.py
reports/RELEASE_VALIDATION.md
```

### Smoke tests

- Fresh clone can run Type I orthogonal example.
- Fresh clone can run one class-B tilted example.
- Documentation examples execute.

### Kill criteria

- Examples cover only one Bianchi type.
- Tilted examples are absent.
- Release notes make observational claims outside solver scope.

### Done definition

The package is ready for internal research use and external technical review.

---

# 9. WBS dependency graph

Recommended implementation order:

```text
Phase 0 — SDD and authority
  PR-00

Phase 1 — Algebra and geometry
  PR-01 -> PR-02

Phase 2 — Background and matter
  PR-03 -> PR-04 -> PR-05 -> PR-06

Phase 3 — Photon and radiation representation
  PR-07 -> PR-08

Phase 4 — Collision, history, startup, seeds
  PR-09 -> PR-10 -> PR-11 -> PR-12

Phase 5 — Solvers and propagation
  PR-13 -> PR-14 -> PR-15 -> PR-16

Phase 6 — Output, validation, convergence
  PR-17 -> PR-18 -> PR-19

Phase 7 — Performance and release
  PR-20 -> PR-21
```

A compact dependency expression:

\[
\mathrm{PR00}
\rightarrow
(\mathrm{PR01}\rightarrow\mathrm{PR02})
\rightarrow
(\mathrm{PR03}\rightarrow\mathrm{PR04}\rightarrow\mathrm{PR05}\rightarrow\mathrm{PR06})
\rightarrow
(\mathrm{PR07}\rightarrow\mathrm{PR08})
\rightarrow
(\mathrm{PR09}\rightarrow\mathrm{PR10}\rightarrow\mathrm{PR11}\rightarrow\mathrm{PR12})
\rightarrow
(\mathrm{PR13},\mathrm{PR14})
\rightarrow
\mathrm{PR15}\rightarrow\mathrm{PR16}\rightarrow\mathrm{PR17}\rightarrow\mathrm{PR18}\rightarrow\mathrm{PR19}\rightarrow\mathrm{PR20}\rightarrow\mathrm{PR21}.
\]

---

# 10. Traceability matrix

| Requirement | PRs |
|---|---|
| F-01 all Bianchi types | PR-01, PR-18, PR-21 |
| F-02 tetrad geometry | PR-02, PR-06 |
| F-03 orthogonal IC | PR-03, PR-18 |
| F-04 tilted IC | PR-04, PR-18 |
| F-05 background RHS | PR-05, PR-06 |
| F-06 photon transport | PR-07, PR-15 |
| F-07 PSTF radiation | PR-08, PR-14 |
| F-08 Thomson tensor | PR-09, PR-13, PR-14 |
| F-09 history/visibility | PR-10, PR-11 |
| F-10 Tier A/B solvers | PR-13, PR-14, PR-16 |
| F-11 observer-neutral export | PR-15, PR-17 |
| F-12 metadata/docs | PR-00, PR-16, PR-17, PR-21 |
| P-01 no coordinate gauge states | PR-00, PR-05 |
| P-02 type via algebra only | PR-01, PR-02, PR-05 |
| P-03 orthogonal and tilted branches | PR-03, PR-04, PR-18, PR-21 |
| P-04 constraints monitored | PR-03, PR-04, PR-05, PR-06, PR-18 |
| P-05 frame split | PR-00, PR-07, PR-09, PR-10, PR-15 |
| P-06 polarization as solver state | PR-08, PR-09, PR-11, PR-14 |
| P-07 FLRW limit | PR-03, PR-05, PR-07, PR-12, PR-18 |
| P-08 class-B support | PR-01, PR-02, PR-05, PR-18 |
| N-01 constraint residuals | PR-03, PR-04, PR-05, PR-16, PR-18 |
| N-02 stiffness | PR-10, PR-11, PR-13, PR-16 |
| N-03 reproducibility | PR-00, PR-16, PR-17, PR-20, PR-21 |
| N-04 cutoff convergence | PR-08, PR-14, PR-19 |
| N-05 type-generic tests | PR-01, PR-02, PR-18, PR-21 |
| N-06 solver/statistics separation | PR-00, PR-17, PR-21 |

---

# 11. Validation gates

## 11.1 Algebra gate

Must pass:

\[
C^\gamma{}_{\alpha\beta}+C^\gamma{}_{\beta\alpha}=0,
\]

\[
n_{\alpha\beta}a^\beta=0,
\]

for all eleven types.

## 11.2 Geometry gate

Must pass:

1. Type I \({}^3R_{\alpha\beta}=0\).
2. \({}^3S^\alpha{}_{\alpha}=0\).
3. Ricci tensor symmetry within tolerance.
4. Operator convention consistency for div/curl.

## 11.3 Constraint gate

Must pass:

\[
\mathcal C_H
\equiv
3H^2-\kappa\rho-\Lambda-\sigma^2+\frac12{}^3R=0,
\]

\[
\mathcal C_\alpha
\equiv
D^\beta\sigma_{\alpha\beta}-\kappa q_\alpha=0.
\]

## 11.4 Background gate

Must pass:

1. FLRW limit remains FLRW.
2. Bianchi I perfect-fluid shear decays as \(\dot\sigma+3H\sigma=0\).
3. Class-B models run with nonzero \(a_\alpha\) terms active.
4. Tilted branch reduces to orthogonal branch as \(v_s\to0\).

## 11.5 Photon gate

Must pass:

\[
e_\alpha e^\alpha=1,
\]

\[
\frac{d\ln(aE)}{d\tau}=-\sigma_{\alpha\beta}e^\alpha e^\beta,
\]

and screen-basis orthonormality.

## 11.6 Collision gate

Must pass:

1. Thomson linearity.
2. Isotropic unpolarized equilibrium.
3. Pure quadrupole source response.
4. Tilted electron-frame transform reduces to orthogonal transform as \(v_e\to0\).

## 11.7 Solver gate

Must pass:

1. Tier A low-resolution angular run.
2. Tier B \(L=4,6,8\) runs.
3. Tier A/B low-moment comparison.
4. Constraint residual logging during full run.

## 11.8 Release gate

A release candidate must include:

1. All-type branch matrix.
2. Cutoff convergence report.
3. Reproducibility metadata.
4. User examples for orthogonal and tilted branches.
5. No observer-statistical interpretation inside solver release notes.

---

# 12. Configuration schema

Minimal YAML-like config:

```yaml
units:
  c_explicit: true
  time_variable: tau_ct
  kappa: 8piG_over_c4

frame:
  transport_frame: normal_n
  collision_frame: electron_u_e
  tetrad_gauge: fermi_propagated
  sky_direction_convention: photon_propagation_e

bianchi:
  type: VII_h
  class: auto
  params:
    algebra_scale: 1.0e-4
    h: 0.2
  h_convention: project_internal
  axis_permutation: [0, 1, 2]

branch:
  matter_tilt: tilted
  species:
    cdm:
      rho_hat: ...
      w: 0.0
      v: [0.0, 0.0, 0.0]
    baryon:
      rho_hat: ...
      w: 0.0
      v: [1.0e-4, 0.0, 0.0]
    electron:
      tied_to_baryon_velocity: true
    photon:
      rho_hat: ...
      w: 0.333333333333

initial_conditions:
  H_closure: solve_H
  shear_shape: diagonal
  shear_amplitude_Sigma: 1.0e-5
  codazzi_policy: solve_shear_offdiag
  perturbation_seed: flrw_regular_limit
  seed_frame: electron_frame_if_tilted

history:
  recombination: external_table
  reionization: tanh
  visibility_frame: electron_frame

solver:
  tier: tierB
  L: 6
  integrator: imex
  rtol: 1.0e-8
  atol: 1.0e-10
  project_constraints_every: 10

output:
  format: hdf5
  include_pstf: true
  include_harmonic: true
  include_maps: false
  include_metadata: true
```

---

# 13. Scoreboard template

| PR | Title | Weight | Score /10 | Weighted progress |
|---:|---|---:|---:|---:|
| 00 | SDD migration and authority freeze | 5 | __ | __ |
| 01 | Bianchi algebra registry | 8 | __ | __ |
| 02 | Tetrad geometry operators | 9 | __ | __ |
| 03 | Orthogonal IC and constraints | 8 | __ | __ |
| 04 | Tilted species and IC closure | 10 | __ | __ |
| 05 | 1+3 PSTF background RHS | 10 | __ | __ |
| 06 | Weyl/Bianchi diagnostics | 6 | __ | __ |
| 07 | Photon and polarization transport | 10 | __ | __ |
| 08 | PSTF radiation representation | 8 | __ | __ |
| 09 | Electron-frame Thomson tensor | 10 | __ | __ |
| 10 | History/visibility/reionization | 7 | __ | __ |
| 11 | Quadrupole-aware TCA startup | 7 | __ | __ |
| 12 | Perturbation seed compatibility | 6 | __ | __ |
| 13 | Tier A angular solver | 10 | __ | __ |
| 14 | Tier B PSTF solver | 10 | __ | __ |
| 15 | Anisotropic source-to-observer propagator | 8 | __ | __ |
| 16 | Integrators/checkpointing | 7 | __ | __ |
| 17 | Output API | 6 | __ | __ |
| 18 | Validation matrix | 10 | __ | __ |
| 19 | Cutoff convergence | 6 | __ | __ |
| 20 | Performance/reproducibility | 5 | __ | __ |
| 21 | Release candidate packaging | 5 | __ | __ |

Total weight:

\[
W=171.
\]

Progress:

\[
\mathrm{Progress}(\%)
=100\times\frac{1}{171}\sum_iw_i\frac{s_i}{10}.
\]

---

# 14. Implementation priorities

The shortest path to a scientifically useful internal solver is:

1. PR-00 to PR-05: algebra, geometry, constraints, background.
2. PR-07 to PR-09: photon transport, PSTF radiation, Thomson tensor.
3. PR-14: Tier B production solver.
4. PR-18: type/branch validation matrix.
5. PR-19: cutoff convergence.

Tier A is essential for authority validation, but a minimal research path may implement Tier B first if PR-09 collision projection is carefully tested. In that case, Tier A becomes the first major validation upgrade rather than the first executable solver.

---

# 15. Hard non-negotiables

A merge request must not be accepted if it violates any of the following:

1. Bianchi type enters anywhere other than algebra construction and metadata.
2. A class-B term is silently dropped.
3. Tilt is included in visibility but not in stress-energy constraints.
4. \(E\)-mode polarization is treated as post-processing rather than source/state information.
5. The electron-frame Thomson tensor is replaced by an FLRW-only shortcut in authority code.
6. Constraint residuals are not computed.
7. Direction convention \(e\) versus \(\hat n_{\rm sky}\) is not recorded.
8. Solver output includes observational interpretation rather than neutral quantities.
9. FLRW limit tests are absent.
10. Any run lacks unit, tetrad, frame, cutoff, and Bianchi algebra metadata.

---

# 16. Final development target

The first research-grade release is reached when the following command family is possible:

```bash
lowell-bianchi run --config examples/type_I_orthogonal.yaml
lowell-bianchi run --config examples/type_V_tilted.yaml
lowell-bianchi run --config examples/type_VII_h_tilted.yaml
lowell-bianchi validate --matrix all_types_all_branches
lowell-bianchi converge --L 4 6 8 --config experiments/baseline_beyondflrw.yaml
```

and produces:

1. constraint-satisfying background runs for all eleven Bianchi types;
2. orthogonal and tilted branches;
3. photon redshift and screen-basis diagnostics;
4. low-\(\ell\) PSTF radiation evolution;
5. electron-frame Thomson collision diagnostics;
6. neutral observer-side exported quantities;
7. reproducible metadata and validation reports.

The scientific posture of the code is deliberately open: anisotropy is not treated as a nuisance template to be minimized away, but as the primary object of exploration. The software boundary is equally deliberate: the solver computes beyond-FLRW CMB transport; separate analysis layers decide how to compare those outputs to low-\(\ell\) observables or any other data product.
