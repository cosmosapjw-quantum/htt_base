# 02. Architecture Spec — HyRec-Cov-RT

## 0. Purpose

1. This file is the self-contained architecture spec for physics and software design.

## 1. Governing geometry

1. The solver works on a tetrad-based `1+3` covariant background.
2. The photon characteristic equations are:
```math
\frac{dx^a}{d\lambda}=p^a,
\qquad
\frac{dp^{\hat\alpha}}{d\lambda}
=
-\omega^{\hat\alpha}{}_{\hat\beta\hat\gamma}p^{\hat\beta}p^{\hat\gamma}.
```
3. The energy drift law is:
```math
\frac{dE}{d\lambda}
=
- E^2\left(
\frac13\Theta + A_{\hat i}n^{\hat i}+\sigma_{\hat i\hat j}n^{\hat i}n^{\hat j}
\right).
```
4. The line-of-sight expansion scalar used in directional Sobolev diagnostics is:
```math
\Xi_\parallel(x,n)=n^a n^b \nabla_a u_b = \frac13\Theta + \sigma_{ab}n^a n^b.
```

## 2. Radiation representation

1. Each key line `L` carries an authoritative discrete state `N[L,q,m,cell]`.
2. `q` indexes a line-centered frequency grid.
3. `m` indexes a discrete ordinate from the `S_N` quadrature.
4. Only key bottleneck lines carry full line state.
5. Continuum blocks may remain compressed or streaming-buffered if they do not degrade authoritative line updates.

## 3. Line transport equation

1. The authoritative line transport equation is:
```math
\left[
\partial_\ell
+
\frac{d\ln\nu}{d\ell}\,\nu\partial_\nu
+
\frac{dn^{\hat i}}{d\ell}\,\nabla^{(\Omega)}_{\hat i}
\right]
\mathcal N_L
=
\eta_L
-
\chi_L\mathcal N_L
+
\partial_\nu(D^{(L)}_{\nu\nu}\partial_\nu \mathcal N_L)
+
\mathcal S_{2\gamma}^{(L)}
+
\mathcal S_{\rm Raman}^{(L)}
+
\mathcal S_{\rm fb}^{(L)}.
```
2. Spatial-angle transport is solved by short-characteristics.
3. Frequency diffusion is solved implicitly in the line solver.
4. Strong source-function coupling is handled by ALI.

## 4. Effective multilevel atom layer

1. Hydrogen interface states solve a linear or quasi-linear effective system:
```math
0
=
 n_H x_e x_p \, \alpha_i^{\rm eff}
+
\sum_j x_j R_{j\to i}^{\rm eff}
+
x_{1s}\beta^{\rm eff}_{1s\to i}
-
x_i\left(
\beta_i^{\rm eff}
+
\sum_j R_{i\to j}^{\rm eff}
+
\Gamma^{\rm eff}_{i\to1s}
\right).
```
2. Helium interface states solve an analogous system with explicit H-continuum-opacity coupling.
3. Effective line-to-ground rates depend on escape operators and not on scalar FLRW-only factors.

## 5. History equations

1. The free-electron fraction obeys:
```math
u^a\nabla_a x_e = \mathcal F_H + \mathcal F_{He}.
```
2. Matter temperature obeys:
```math
u^a\nabla_a T_m + \frac23\Theta T_m
=
\Gamma_C(T_r^{(0)}-T_m)
+
\frac{2}{3k_B n_{\rm tot}}
(\dot Q_{\rm ff}+\dot Q_{\rm bf}+\dot Q_{\rm bb}+\dot Q_{\rm inj}).
```
3. Visibility obeys:
```math
\frac{d\tau}{d\lambda}=\sigma_T n_e(-u_a k^a),
\qquad
g(\eta)=\dot\tau e^{-\tau}.
```

## 6. Escape operators

1. The authoritative line escape object is a nonlocal operator `E_L`.
2. Directional Sobolev may be computed as:
```math
\tau_{S,L}(x,n)=
\frac{A_{ul}\lambda_L^3}{8\pi}
\frac{((g_u/g_l)n_l-n_u)}{|\Xi_\parallel(x,n)|},
\qquad
\beta_{S,L}(x,n)=\frac{1-e^{-\tau_{S,L}}}{\tau_{S,L}}.
```
3. `beta_S` is never an authoritative replacement for `E_L`.

## 7. Orthogonal and tilted branches

1. Orthogonal Bianchi uses `u^a = n^a`.
2. Tilted Bianchi uses `u^a = Γ(n^a + v^i e_i^a)`.
3. Any baryon-frame microphysics on the tilted branch must use explicit frame transforms.
4. The first-order energy transform is:
```math
E_{(u)}=\Gamma E_{(n)}(1-v_i n^i).
```

## 8. Architectural freeze rule

1. No module may cross-call another module except through the public APIs defined in `03_DATA_MODEL_AND_APIS.md`.
