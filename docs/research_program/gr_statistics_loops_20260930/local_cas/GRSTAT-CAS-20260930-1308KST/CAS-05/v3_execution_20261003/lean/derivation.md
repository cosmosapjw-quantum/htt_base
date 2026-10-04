# Finite derivation checked by the Lean axis

For `g_ab=E eta_ab`, `E=exp(2 phi)>0`, the source defines
`g^ab=E^-1 eta^ab` and `partial_c g_ab=2 E phi_c eta_ab`. The metric
Christoffel sum proves

```text
Gamma^a_bc = delta^a_b phi_c + delta^a_c phi_b - eta_bc eta^aa phi_a.
```

Differentiating the *metric and inverse metric jets* in the source and
substituting into `R_ab=R^c_acb` gives

```text
R_ab = -2 phi_ab + 2 phi_a phi_b
       - eta_ab (Box_eta phi + 2 eta^cd phi_c phi_d),
G_ab = -2 phi_ab + 2 phi_a phi_b
       + 2 eta_ab Box_eta phi + eta_ab eta^cd phi_c phi_d.
```

`phi_exact_taylor` is the exact cubic Taylor identity for the neutral
`phi_lambda`; `jPhi_cubic` fixes its repeated third coefficients. At the
origin, `phi_a=0`, `phi_00=-2b`, and `phi_ii=-b`. The derived tensor has
`G_00=6b`, `G_ii=0`. The first coordinate Einstein jet is obtained from
the exact `origin_G_exact_first_jet` polynomial identity, whose residual is
explicitly proportional to the square of the displacement parameter. Its
only nonzero entries are `partial_0 G_01=partial_0 G_10=-2lambda` and
`partial_1 G_ii=-2lambda` for spatial `i`. The first metric jet vanishes,
so the cosmological term contributes no stress derivative at the origin.
The spatial differentiated eigenvector equation divides by the proven gap
`6b/kappa` and yields `partial_0 u^1=lambda/(3b)` with all other rates zero;
`u^0` has zero first jet by normalization. Physical acceleration is
`c^2 lambda/(3b)` because `x0` is length-valued. For `lambda!=0`, the
density first jet vanishes while a pressure gradient does not.

On the specified ray, `2phi=-b s^2`. The orthonormal frame contributes
`E^-1=exp(b s^2)` to both stress contractions. The metric part of
`Lambda g` cancels between the `00` and `22` entries, leaving the checked
`kappa(epsilon+p2)=exp(b s^2)(6b-2lambda s)`. Its zero at `3b/lambda`
requires `lambda!=0`; the `lambda=0` branch is a separate theorem.

For C03 the source builds exactly the supplied symmetric homogeneous cubic
`H`, including `H00=0`, from `q_i=-6b k_0i`, `M_ij=-6b k_ji`,
`S=(M+M^T)/2`, and `W=(M-M^T)/2`. The checked identity
`H(X)=J_abcde X_d X_e X_f/6` is the finite polynomial jet convention.
The checked homogeneity identity shows no value, first, or second Taylor
coefficient at the origin. In the generic second connection-jet product rule,
the terms involving `dg(0)` or `d(g^-1)(0)` vanish. Hence the perturbative
second connection jet is the inverse-metric contraction of `J`; connection
product terms then vanish at first Ricci order because `Gamma(0)=0`.
The metric and inverse first jets vanish in the scalar-trace product rule.
These substitutions derive the 40 closed coefficients in
`full40_first_Einstein_coefficients`; the formula appears in
`STATEMENT_ALIGNMENT.md`. Their four Bianchi contractions vanish by the
separately checked `origin_bianchi_four` theorem.

For each of the twelve row/column basis choices, the same universal 40-entry
theorem applies. The target `0i` entries have coefficient `-6b` exactly
when derivative row and output column match the basis; all other target
coefficients are zero. The explicit right inverse divides arbitrary target
`q_i,M_ij` by `-6b` under `b>0`, and the normalized spatial eigenvector jet
recovers every arbitrary real `k_mu_i`. This concerns only the homogeneous
first Einstein jet and finite differentiated eigenvector equations at the
origin.
