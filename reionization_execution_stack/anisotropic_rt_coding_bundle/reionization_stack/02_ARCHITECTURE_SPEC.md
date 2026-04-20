# 02. Architecture Spec — Anisotropic Reionization RT

## 0. Purpose

1. This file is the self-contained architecture spec for transport, chemistry, and 21-cm output.

## 1. Governing geometry

1. Transport occurs on a tetrad-based `1+3` covariant background.
2. Photon characteristics are:
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
-E^2\left(
\frac13\Theta + A_{\hat i}n^{\hat i}+\sigma_{\hat i\hat j}n^{\hat i}n^{\hat j}
\right).
```

## 2. Radiation sectors

1. Ionizing UV continuum is authoritative and group-discretized.
2. X-ray continuum is authoritative and group-discretized.
3. Lyα is authoritative and uses a scattering-aware solver.
4. Diffuse recombination radiation is optional and enters as an additive emissivity block.
5. The line-heavy Lyα sector is not merged into the continuum solver if that would remove ALI support.

## 3. Continuum transport

1. For each frequency group `b` and ordinate `m`, the continuum transport equation is:
```math
\left[
\partial_t
+ c n_m^{\hat i} e_{\hat i}{}^a \nabla_a
+ \dot E_{bm}\partial_E
+ \dot n_{bm}^{\hat i}\nabla^{(\Omega)}_{\hat i}
\right] I_b(x,n_m)
=
\eta_b - \chi_b I_b.
```
2. The production solve is a short-characteristics sweep.
3. The reference solve is a long-characteristics solve.

## 4. Lyα transport

1. The Lyα master equation is:
```math
\left[
\partial_t
+ c n^{\hat i} e_{\hat i}{}^a \nabla_a
+ \dot\nu\partial_\nu
+ \dot n^{\hat i}\nabla^{(\Omega)}_{\hat i}
\right] I_\alpha
=
\eta_\alpha
-\chi_\alpha I_\alpha
+\partial_\nu(D_{\nu\nu}\partial_\nu I_\alpha)
+\mathcal S_{\rm redist}.
```
2. ALI is authoritative for this sector.

## 5. Authoritative ionization kernel

1. The authoritative photon-budget law is:
```math
\sum_{m,b} w_m
\int_0^{s_{\max}} ds\,
\Phi_{bm}(x_m^{\rm ret}(s),t_m^{\rm ret}(s))
e^{-\tau_{bm}(s)}
\ge
n_H \Delta V \left[(1-x_{\rm HII})+N_{\rm rec}^{\rm eff}\right].
```
2. This law is a diagnostic and thresholded update aid.
3. The continuous update still proceeds through the chemistry equations.

## 6. Local chemistry and heating

1. Hydrogen ionization evolution is:
```math
u^a\nabla_a x_{\rm HII}
=
(1-x_{\rm HII})\Gamma_{\rm HI}
-
\alpha_B(T_k) C_{\rm eff} n_H x_{\rm HII}^2
-
\Lambda_{\rm shld}.
```
2. Helium is treated analogously.
3. Recombination counter evolution is:
```math
u^a\nabla_a N_{\rm rec}
=
\alpha_B(T_k) C_{\rm eff} n_H x_{\rm HII}^2.
```
4. Kinetic temperature evolves by:
```math
u^a\nabla_a T_k + \frac23 \Theta T_k
=
\frac{2}{3k_B n_{\rm tot}}
(\mathcal H_X + \mathcal H_{UV} + \mathcal H_{Compt} - \Lambda_{cool}).
```

## 7. Spin temperature

1. Lyα coupling coefficient is built from transported Lyα intensity.
2. Spin temperature obeys:
```math
T_s^{-1}
=
\frac{T_\gamma^{-1}+x_c T_k^{-1}+x_\alpha T_c^{-1}}
{1+x_c+x_\alpha}.
```

## 8. Geometry-aware 21-cm output

1. The line-of-sight expansion scalar is:
```math
\Xi_{21}(x,s)=s^a s^b \nabla_a u_b.
```
2. Optical depth is:
```math
\tau_{21}(x,s)
=
\frac{3 c^3 h_P A_{10} n_{HI}}
{16 k_B \nu_{21}^2 T_s |\Xi_{21}(x,s)|}.
```
3. Brightness temperature is computed from `tau_21`, `T_s`, and `T_gamma` without collapsing geometry into a pure FLRW scalar unless the explicit limit branch is selected.

## 9. Orthogonal and tilted branches

1. Orthogonal branch uses `u^a = n^a`.
2. Tilted branch uses `u^a = Γ(n^a + v^i e_i^a)`.
3. All local chemistry must be evaluated in the baryon frame.
4. Any transport in another frame must be explicitly transformed before rate compression.

## 10. Architectural freeze rule

1. No module may hide transport-to-chemistry compression inside an undocumented helper.
