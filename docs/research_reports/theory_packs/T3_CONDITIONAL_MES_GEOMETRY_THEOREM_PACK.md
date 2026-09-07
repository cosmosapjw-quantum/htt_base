# T3 — Conditional MES geometry and scalar-to-tensor no-go

Date: 2026-09-03  
Evidence grades: `LITERATURE_SUPPORTED` coefficients; `DERIVED` normalization,
standard-variable conversion, one-way logic, and equivariance no-go  
Observational data used: none

## 1. Scope

This pack retains only the geodesic shear and vorticity inequalities used by
the current HTT report. It does not restore historical scalar anomaly ranks,
non-geodesic acceleration coefficients, a converse almost-FLRW theorem, or a
measurement of physical shear or vorticity.

The coefficient authority is the Maartens--Ellis--Stoeger programme:

- R. Maartens, G. F. R. Ellis, and W. R. Stoeger, *Limits on anisotropy and
  inhomogeneity from the cosmic background radiation*, Phys. Rev. D 51,
  1525 (1995), DOI `10.1103/PhysRevD.51.1525`, arXiv `astro-ph/9501016`;
- R. Maartens, G. F. R. Ellis, and W. R. Stoeger, *Improved limits on
  anisotropy and inhomogeneity from the cosmic background radiation*, Phys.
  Rev. D 51, 5942 (1995), DOI `10.1103/PhysRevD.51.5942`;
- W. R. Stoeger, M. E. Araujo, and T. Gebbie, *The Limits on Cosmological
  Anisotropies and Inhomogeneities from COBE Data*, arXiv
  `astro-ph/9904346`, which prints the equations and the harmonic/PSTF
  normalization used below.

## 2. Premise matrix

The report treats the MES output as the implication

\[
\mathcal H_{\rm MES}
\quad\Longrightarrow\quad
\left\{
\frac{|\sigma_{ab}|}{\Theta}<B_\sigma,
\frac{|\omega_{ab}|}{\Theta}<B_\omega
\right\}.
\]

`H_MES` contains the following distinct premises.

| ID | Premise | Status in Report A |
|---|---|---|
| M1 | General relativity and the Einstein--Liouville radiation description | required |
| M2 | an expanding spacetime domain | required |
| M3 | a declared fundamental matter congruence | required |
| M4 | freely falling/geodesic fundamental observers for the retained branch | required |
| M5 | almost-isotropy bounds relative to all relevant fundamental observers, not only the local observer | required Copernican extension |
| M6 | the spatial-gradient and time-derivative bounds on radiation multipoles used by the improved MES construction | required |
| M7 | the PSTF tensor norm convention for `epsilon_l` | required and rederived below |
| M8 | one common frame, congruence, epoch, and normalization for the bound and target quantity | required |
| M9 | any value assigned to the residual intrinsic dipole `epsilon_1` | scenario input, not inferred here |
| M10 | Gaussianity of matter-density fluctuations | not required by the printed deterministic inequalities |
| M11 | exact spatial homogeneity | not required by the MES construction |
| M12 | a native Bianchi family or transfer solution | not part of the theorem |

The current report makes no claim that local CMB data alone establish M5 or
M6. They remain explicit premises.

## 3. Literature-supported geodesic inequalities

With `Theta=nabla_a u^a`, the printed MES bounds are

\[
\boxed{
\frac{|\sigma_{ab}|}{\Theta}
 < \frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3
 \equiv B_\sigma,
}
\]

\[
\boxed{
\frac{|\omega_{ab}|}{\Theta}
 < \frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2
 \equiv B_\omega.
}
\]

The norms are component/PSTF norms. The coefficients are literature-supported
rather than rederived from the full Einstein--Liouville hierarchy in this
pack.

## 4. Harmonic-to-PSTF normalization

The COBE/MES bridge writes

\[
\Delta T_\ell^2=\frac1{4\pi}\sum_m|a_{\ell m}|^2
                =\frac{2\ell+1}{4\pi}C_\ell
\]

and

\[
\tau_{A_\ell}\tau^{A_\ell}
 =\frac{(2\ell+1)(2\ell)!}{2^\ell(\ell!)^2}
  \frac{\Delta T_\ell^2}{T_0^2}.
\]

For `ell=2` and `ell=3`, the factorial coefficients are respectively

\[
\frac{15}{2},\qquad \frac{35}{2}.
\]

Combining these with the T1 stored-real isometry gives

\[
\boxed{
\epsilon_2^2=\frac{75C_2}{8\pi T_0^2}
             =\frac{Q:Q}{T_0^2},
}
\]

\[
\boxed{
\epsilon_3^2=\frac{245C_3}{8\pi T_0^2}
             =\frac{O:O}{T_0^2}.
}
\]

Thus

\[
\epsilon_2=\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},
\qquad
\epsilon_3=\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}}.
\]

These are PSTF tensor norms, not sky RMS values with an omitted conversion
factor.

## 5. Conversion to standard dimensionless kinematic variables

Use

\[
H=\frac{\Theta}{3},
\qquad
\Sigma^2=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},
\qquad
W^2=\frac{\omega_{ab}\omega^{ab}}{6H^2}.
\]

If `|sigma_ab|^2=sigma_ab sigma^ab` and similarly for vorticity, then

\[
\Sigma^2
 <\frac{\Theta^2B_\sigma^2}{6H^2}
 =\frac32B_\sigma^2,
\]

\[
W^2
 <\frac{\Theta^2B_\omega^2}{6H^2}
 =\frac32B_\omega^2.
\]

Define the report functionals

\[
\boxed{U_\sigma=\frac32B_\sigma^2},
\qquad
\boxed{U_\omega=\frac32B_\omega^2}.
\]

For the declared scenario `epsilon_1=0`,

\[
U_\omega
 =\frac32\left(\frac{2}{15}\epsilon_2\right)^2
 =\frac{C_2}{4\pi T_0^2}.
\]

This is an algebraic closure check. It does not make `epsilon_1=0` an
observation: the COBE application explicitly adopted it by attributing the
observed dipole to peculiar motion while acknowledging a possible non-Doppler
residual.

## 6. One-way logic

The valid statement is

\[
\mathcal H_{\rm MES}
\Longrightarrow
\Sigma^2<U_\sigma,\quad W^2<U_\omega.
\]

None of the following converses follows:

\[
\Sigma^2<U_\sigma\Longrightarrow\mathcal H_{\rm MES},
\qquad
W^2<U_\omega\Longrightarrow\mathcal H_{\rm MES},
\]

or

\[
(\Sigma^2,W^2)\approx(0,0)
\Longrightarrow\text{FLRW}.
\]

The inequalities are necessary consequences under a premise set, not a
characterization of that premise set. The scalar values also discard tensor
direction, eigenframe, phase, parity, and higher-multipole information.

## 7. Scalar-to-vector/STF equivariance no-go

Let a scalar input space `S` carry the trivial SO(3) action, and let
`F:S->V` be an SO(3)-equivariant map into a nontrivial vector or STF
representation. For every scalar input `s` and rotation `R`,

\[
F(s)=F(R\cdot s)=R\cdot F(s).
\]

Therefore `F(s)` must lie in the rotation-fixed subspace `V^{SO(3)}`.

For a vector, invariance under the three rotation generators forces all three
components to vanish. For a symmetric rank-two tensor, rotational invariance
forces a multiple of the identity; the trace-free condition then forces zero.
The same representation argument applies to every irreducible `ell>0`
sector.

Hence

\[
\boxed{
F(\epsilon_1,\epsilon_2,\epsilon_3)=0
}
\]

for every SO(3)-equivariant attempt to manufacture a nonzero vector, STF2, or
STF3 tensor solely from the MES scalars. Additional directional data or a
symmetry-breaking model is mathematically necessary.

This does not forbid evaluating scalar functions of measured tensors. It
forbids reversing that many-to-one map without extra information.

## 8. Dimensional and boundary checks

- `epsilon_l`, `B_sigma`, `B_omega`, `U_sigma`, and `U_omega` are
  dimensionless.
- `C_l` and `T_0^2` must use the same temperature unit.
- The coefficients are nonnegative for nonnegative `epsilon_l`; squaring does
  not introduce a sign ambiguity because the source inequalities bound norms.
- A zero quadrupole or octupole is regular for the scalar functionals, although
  a normalized orbit chart may be unavailable.
- The retained vorticity inequality refers to the geodesic congruence and
  cannot be moved to a tilted or accelerated congruence without a new
  derivation.

## 9. Independent Wolfram checks

Fresh exact arithmetic reproduced

```yaml
MES_factorial_coefficient_l2: 15/2
MES_factorial_coefficient_l3: 35/2
epsilon2_squared: 75 C2/(8 pi T0^2)
epsilon3_squared: 245 C3/(8 pi T0^2)
Uomega_epsilon1_zero_minus_C2_over_4piT0sq: 0
SO3_fixed_vector_subspace: zero
SO3_fixed_STF2_subspace: zero
```

The machine-readable receipt is `T3_WOLFRAM_AND_SOURCE_RECEIPT.json`.

## 10. T3 terminal

```text
PASS_CONDITIONAL_MES_GEOMETRY_AND_EQUIVARIANCE_FIREWALL
```

Evidence status is deliberately split:

```yaml
MES_coefficients: LITERATURE_SUPPORTED
PSTF_harmonic_normalization: DERIVED_AND_WOLFRAM_CHECKED
standard_variable_conversion: DERIVED_AND_WOLFRAM_CHECKED
one_way_logic: ESTABLISHED
scalar_to_tensor_no_go: DERIVED_AND_WOLFRAM_CHECKED
observational_or_physical_measurement: NONE
```
