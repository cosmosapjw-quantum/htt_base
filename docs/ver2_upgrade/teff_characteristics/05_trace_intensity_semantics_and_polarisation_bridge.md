# Trace/Intensity Semantics and Polarisation Bridge

문서 목적: Paper IV-V를 하나의 bridge 문서로 정리하되, trace sector와 spin-2 sector를 절대 섞지 않는다. 특히 Paper V의 Q-normalization을 correction ledger로 고정한다.

---

## 1. Distribution matrix and block split

Polarised radiative transfer acts on a screen-space distribution matrix or tensor `P_ab(e)`.

Its trace is scalar intensity:

\[
I(\hat e)=\operatorname{tr}P(\hat e).
\]

Its traceless screen part contains linear polarisation and decomposes into E/B hierarchy variables.

Therefore:

\[
P_{ab}
=\frac12 I\,S_{ab}+P^{\rm TF}_{ab},
\]

schematically, where `S_ab` is the screen metric/projector and `P^{TF}_{ab}` carries spin-2 structure.

Teff applies to `I`, not to `P^{TF}_{ab}`.

---

## 2. Trace-sector Teff semantics

For blackbody photons:

\[
T_{\rm eff}(\hat e)=T_0\Theta(\hat e)
\]

is exact brightness temperature at all frequencies.

For FD/BE distributions with chemical potential or degeneracy, Teff is more safely called occupation temperature unless the brightness-temperature interpretation is restricted to the appropriate regime.

---

## 3. Exact nonlinear Thomson source bridge

If the scalar trace is on the one-field Teff manifold, then the intensity quadrupole entering Thomson polarisation is

\[
I_{\langle ab\rangle}
=
 c_\xi T_0^4
 \left\langle \Theta(\hat e)^4 e_{\langle a\rangle}e_{\langle b\rangle}\right\rangle_\Omega.
\]

This bridge is exact on the trace manifold. It is nonlinear because intensity scales as `Theta^4`.

Linear approximation:

\[
\Theta=1+\theta,
\qquad
\Theta^4=1+4\theta+O(\theta^2).
\]

The nonlinear terms generate quadrupole contributions from lower Teff multipoles, especially dipole-squared terms.

---

## 4. What this bridge does not do

It does not:

- parameterise `E_{A_l}` or `B_{A_l}`,
- replace the polarised Boltzmann hierarchy,
- predict observed-sky EE/BB spectra by itself,
- control lensing/tensor/vector-induced B modes,
- remove the need for screen-basis transport,
- prove that Teff is a polarisation closure.

Correct sentence:

> Teff is an intensity-side source formalism inside polarised radiative transfer.

Incorrect sentence:

> Teff is a polarisation formalism.

---

## 5. Axisymmetric Q convention: canonical correction

Adopt

\[
P_1(\mu)=\mu,
\qquad
P_2(\mu)=\frac{3\mu^2-1}{2}.
\]

To preserve the current Table II values, use

\[
\Theta(\mu)=1+A\mu+Q\left(\mu^2-\frac13\right)
=1+A P_1(\mu)+\frac{2Q}{3}P_2(\mu).
\]

Then

\[
\frac{I_2}{c_\xi T_0^4}
=
\frac52\int_{-1}^{1}\Theta(\mu)^4P_2(\mu)\,d\mu.
\]

The expansion is

\[
\begin{aligned}
\frac{I_2}{c_\xi T_0^4}
=&\frac83 Q+4A^2+\frac{16}{21}Q^2
+\frac{88}{21}A^2Q+\frac47A^4 \\
&+\frac{64}{63}A^2Q^2+\frac{32}{63}Q^3
+\frac{320}{6237}Q^4.
\end{aligned}
\]

Thus at `(A,Q)=(0.30,0.15)`:

\[
I_{2,\rm lin}/(c_\xi T_0^4)=\frac83Q=0.400,
\]

and

\[
I_{2,\rm exact}/(c_\xi T_0^4)\approx0.84214.
\]

This gives the stated 52.5 percent linear underestimate.

---

## 6. If using `theta = A P1 + Q P2`

If instead the manuscript defines

\[
\theta=A P_1+Q P_2,
\]

then the linear term is

\[
I_{2,\rm lin}/(c_\xi T_0^4)=4Q,
\]

not `8Q/3`. In that convention, Table II must be recomputed.

Recommendation: retain the current Table II and change the text to the `Q(\mu^2-1/3)` convention.

---

## 7. Corrected physical interpretation of dipole-squared term

At `(A,Q)=(0.30,0.15)` under the table convention:

\[
4A^2=0.36,
\qquad
\frac83Q=0.40.
\]

So the dipole-squared contribution is comparable to, but slightly smaller than, the linear quadrupole contribution. It strongly enhances the source, but does not strictly dominate the linear quadrupole at this point.

At `(A,Q)=(0.40,0.20)`:

\[
4A^2=0.64,
\qquad
\frac83Q\approx0.533.
\]

There `dominates` is defensible.

Recommended text:

> At `(A,Q)=(0.30,0.15)`, the dipole-squared contribution is already nearly as large as the linear quadrupole contribution and drives a large nonlinear correction. At stronger dipole amplitudes it can dominate.

---

## 8. Two-field eta extension

For

\[
f_{\Theta,\eta}=\Phi_\xi\left(\frac{x}{\Theta(\hat e)}-\eta(\hat e)\right),
\]

statistics independence of the one-field source bridge is generally broken because `eta` changes energy integrals. A pure eta dipole decouples from the Thomson source at linear order, while first corrections enter schematically at

\[
O(A^2_\eta),\quad O(A A_\eta),
\]

or with the manuscript's specific convention, the stated smallness condition should be carried explicitly:

\[
2C_\xi \frac{A_\eta}{A}\ll1.
\]

Do not claim eta corrections are always negligible. Claim only smallness under the stated parameter condition.

---

## 9. Channel responsibility table

| Object | Teff controls? | Exact when? | Needs independent transport? |
|---|---:|---|---:|
| scalar trace `I` | yes | trace block on Teff manifold | no, for semantics; yes, for actual transport |
| intensity quadrupole source `I_ab` | yes | trace block on Teff manifold | source only |
| E-mode propagation | no | not applicable | yes |
| B-mode propagation | no | not applicable | yes |
| Stokes `Q,U` basis dependence | no | not applicable | yes |
| observed EE/BB spectra | no direct control | only through full pipeline | yes |

---

## 10. Paper V abstract patch

Replace any sentence like:

> Teff gives a polarisation closure.

with:

> Teff gives an intensity-side source bridge inside the polarised hierarchy. The scalar trace inherits the Teff semantics, while the spin-2 polarisation sector remains independently transported.

Replace:

> the dipole-squared term dominates at `(A,Q)=(0.30,0.15)`

with:

> the dipole-squared term is already comparable to the linear quadrupole contribution at `(A,Q)=(0.30,0.15)` and can dominate at stronger dipole amplitudes.
