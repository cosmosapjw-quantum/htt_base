# 02. Numerical Architecture and Algorithms
## solver decomposition / integrator choices / time-gauge bridge / pseudocode

---

## 0. scope

이 문서는 low-\ell Bianchi solver의 numerical SSOT다.
여기서는 아래를 고정한다.

1. block decomposition
2. state layout and basis typing
3. proper-time / conformal-time bridge
4. solver split and integrator defaults
5. adaptive step control and interpolation
6. residual normalization and fail-closed policy
7. implementation order that avoids mock fitting and local minima

---

## 1. top-level decomposition

The solver is divided into:

1. `registry`
2. `geometry_core`
3. `background_core`
4. `transport_collision_core`
5. `hierarchy_core`
6. `source_history_core`
7. `output_layer`
8. `workflow_gate_layer`

Each block owns a fixed interface and cannot silently absorb work belonging to another block.

---

## 2. state-layer contracts

### 2.1 background state

```text
BackgroundState(
    t,
    alpha,
    gamma_AB,
    theta,
    sigma_AB,
    family_spec,
    species_hat,
    species_tilt
)
```

### 2.2 geometry diagnostics

```text
GeometryDiagnostics(
    triad_iA,
    triad_Ai,
    C_ortho,
    Gamma_ortho,
    Ricci_routeA,
    Ricci_routeB_or_nan,
    Ricci_scalar,
    S_AB,
    residuals
)
```

### 2.3 hierarchy state

Hierarchy packing is fixed in `02A_HIERARCHY_LAYOUT_AND_TIERA_TRANSPORT_NOTE.md`.
This document only freezes the split:

```text
HierarchyState =
    MatterBlock
  + PhotonIntensityBlock
  + PhotonPolarizationBlock
  + NeutrinoBlock
  + SourceHistoryBlock
```

---

## 3. proper-time / conformal-time bridge

### 3.1 background in proper time
The homogeneous Einstein–matter core is evolved in \(t\).

### 3.2 hierarchy in conformal time
The projected hierarchy and visibility source history are evolved in \(\eta\).

### 3.3 mandatory bridge API

```text
eta_grid = eta_from_t_grid(t_grid, a_m_grid)
GammaT_eta = opacity_from_physical_inputs(a_m, ne_phys, xe, sigmaT, c_flag)
background_interp = background_interpolator(t_grid, state_grid)
background_on_eta = sample_background_on_eta(background_interp, eta_grid)
```

### 3.4 mixed-unit adapter table

| API | input units | output units | frozen note |
|---|---|---|---|
| `eta_from_t_grid` | \(t\), \(a_m\) | \(\eta\) | obey \(d\eta=dt/a_m\) |
| `opacity_from_physical_inputs` | \(n_e^{\rm phys},x_e,\sigma_T\) | \(\Gamma_T^{(\eta)}\) | explicit physical adapter |
| `sample_background_on_eta` | proper-time background | hierarchy-time states | no silent interpolation in mixed gauge |

---

## 4. integrator defaults

### 4.1 background
Default: adaptive explicit RK for nonstiff branches.  
Fallback: Rosenbrock-W or fully implicit method when residual growth or stiffness indicators require it.

### 4.2 hierarchy
Default: IMEX additive Runge–Kutta split
\[
M(y)\dot y = f^E(t,y) + f^I(t,y),
\]
with free-streaming/mode-mixing in \(f^E\) and collision/TCA-stiff terms in \(f^I\).

### 4.3 not-allowed integrator shortcuts
- no monolithic explicit stepper through stiff Thomson/TCA regime,
- no production claim using development-only low cutoff,
- no family-specific hardcoding inside generic integrator core.

---

## 5. adaptive step control

### 5.1 scale-aware controller

Recommended control scales:
\[
\Delta t_H \sim H^{-1},\qquad
\Delta t_\sigma \sim |\sigma|^{-1},\qquad
\Delta \eta_T \sim (\Gamma_T^{(\eta)})^{-1},\qquad
\Delta \eta_{\rm geo}\sim \|\mathsf M_{\rm geo}\|^{-1}.
\]

A safe controller uses
\[
\Delta s_{\rm trial}
=
\min(
c_H \Delta t_H,
c_\sigma \Delta t_\sigma,
c_T \Delta \eta_T,
c_{\rm geo}\Delta \eta_{\rm geo}
),
\]
with package-fixed safety factors.

### 5.2 default safety factors
```text
c_H    = 0.05
c_sigma= 0.05
c_T    = 0.10
c_geo  = 0.10
```

These are defaults, not immutable constants; a branch may tighten them, not loosen them without documenting why.

### 5.3 acceptance rule

A step is accepted only if
1. local integration estimate passes,
2. normalized residual pack remains finite,
3. no gate variable crosses invalid state.

---

## 6. interpolation and tabulation

### 6.1 background interpolation
The background interpolator must preserve:
- positive-definite \(\gamma_{AB}\),
- continuity of \(a_m\),
- finite residual metadata.

### 6.2 source-history tabulation
Visibility/history tables must store:
- grid variable used,
- interpolation order,
- monotonicity guarantee for optical depth,
- adapter units.

### 6.3 fail-closed rule
If a table contains NaN, negative optical depth where forbidden, or broken monotonicity, the gate fails instead of silently clipping.

---

## 7. residual normalization and NaN fail

Residuals of different dimensional origin must be normalized before comparison to thresholds.

### mandatory rule
```text
if any residual is NaN or Inf:
    gate = FAIL
```

### residual pack structure
```text
ResidualPack(
    gauss,
    codazzi,
    dual_route_curvature,
    electric_weyl,
    magnetic_weyl,
    collision_isotropy,
    inverse_boost,
    notes
)
```

---

## 8. background pseudocode

```text
function background_rhs(t, U_bg, family_spec, eos_model):
    gamma_AB, theta, sigma_AB, species_hat, species_tilt = unpack(U_bg)
    geom = build_geometry(family_spec, gamma_AB, theta, sigma_AB)

    matter = project_species_to_normal_frame(species_hat, species_tilt, gamma_AB)
    rho_tot, p_tot, q_A, pi_AB = total_matter_projection(matter, gamma_AB)

    S_AB = geom.S_AB
    theta_dot = raychaudhuri_rhs(theta, sigma_AB, rho_tot, p_tot, Lambda)
    sigma_dot_AB = shear_rhs(theta, sigma_AB, S_AB, pi_AB)

    gamma_dot_AB = metric_rhs_from_shear(theta, sigma_AB, gamma_AB)
    species_dot = background_species_rhs(...)

    residuals = background_constraint_residuals(...)
    return pack(gamma_dot_AB, theta_dot, sigma_dot_AB, species_dot), residuals
```

---

## 9. hierarchy pseudocode (high-level)

```text
function hierarchy_rhs_eta(eta, U_hier, background_sampler, backend, source_tables):
    bg = background_sampler(eta)
    ops = backend.operator_factory(bg)
    collision = exact_thomson_block(bg, U_hier, source_tables)
    explicit_piece = free_stream_and_mode_mix(ops, U_hier)
    implicit_piece = collision_and_tca(ops, U_hier, source_tables)
    sources = build_visibility_sources(bg, source_tables, U_hier)
    return explicit_piece + implicit_piece + sources
```

Detailed packing and block layout are frozen in `02A_HIERARCHY_LAYOUT_AND_TIERA_TRANSPORT_NOTE.md`.

---

## 10. implementation-order constraints

The allowed order is

1. tensor helper layer
2. family registry
3. geometry core
4. matter projection
5. background core
6. exact collision
7. visibility/reionization adapter
8. family backend contracts
9. hierarchy layout
10. output layer
11. fitting gate

Mock fitting before steps 1–10 is forbidden.

---

## 11. one-line summary

numerical SSOT의 핵심은  
**background proper-time core + hierarchy conformal-time core + explicit bridge + IMEX stiff split + normalized residual fail-closed policy** 를 먼저 고정하고, 그 위에 family-aware operators를 얹는 것이다.
