# Paper I-V Upgrade Ledger

문서 목적: 각 Paper의 original scope를 보존하면서, 과장 문장과 용어 충돌을 제거한다. 이 파일은 논문별 introduction, abstract, discussion 수정의 기준 ledger다.

---

## 0. 전체 시리즈의 revised narrative

기존 narrative가 `Teff를 점점 full closure로 승격한다`처럼 읽히면 위험하다. revised narrative는 다음이어야 한다.

1. Paper I-III: Teff manifold의 geometry와 diagnostic을 만든다.
2. Paper IV: Teff variables의 observable semantics와 local reconstructive adequacy를 밝힌다.
3. Paper V: polarised transfer 안에서 Teff가 parameterise하는 것은 scalar trace/intensity block이며, spin-2 polarisation hierarchy는 independent하다는 scope boundary를 세운다.
4. Characteristics architecture: full state transport는 closure-free characteristics가 맡고, Teff는 selected block의 chart/diagnostic/source semantics로 남는다.

---

## 1. Paper I - Tangency criterion and entropy-projection inequality

### Established core

Paper I establishes a one-field Teff manifold in which angular nonequilibrium is encoded by a direction-dependent effective temperature. Along each ray, the spectrum retains a fixed equilibrium shape. The tangency diagnostic projects the entropy-normalised collision field onto a generalized Laguerre basis and reads off the `n >= 2` energy-mode content.

### Correct scope

- per-ray,
- instantaneous,
- collision-side,
- energy-mode diagnostic,
- necessary for collision-side tangency,
- not sufficient for full Teff-manifold tangency unless angular consistency and constant-mode obstructions are separately handled,
- not a global kinetic adequacy theorem,
- not a standalone PDE solver.

### Upgrade action

Use:

> Paper I provides a collision-side defect-of-invariance diagnostic for the ray-wise equilibrium ansatz.

Do not use:

> Paper I proves Teff as a full transport closure.

### Physical meaning

The diagnostic says whether the collision forcing tries to push a ray out of the local equilibrium spectral family. It does not say that free streaming, metric redshift, angular transport, or finite-time accumulation remain small.

---

## 2. Paper II - Direction-dependent chemical potential

### Established core

Paper II extends the state from `Theta(e)` to `(Theta(e), eta(e))` and shows that a direction-dependent chemical-potential dipole carries independent number/energy information. The important observable signature is the number-to-energy flux fraction ratio `f_N/f_E`.

### Correct scope

- structural non-redundancy,
- identifiability within the tested/minimal two-field manifold,
- scalar chemical potential is insufficient for the joint number-energy moment structure,
- full rank of the 5x5 moment-map Jacobian is partly numerical over tested configurations,
- no transport-performance advantage is claimed.

### Upgrade action

Use:

> Paper II establishes that the eta-dipole is a genuine reduced coordinate for joint number-energy anisotropy.

Do not use:

> Paper II proves a globally superior transport closure.

### Physical meaning

A single temperature field locks number and energy anisotropies too tightly. The eta-dipole is the minimal way to represent a number-flux anisotropy that cannot be absorbed into temperature multipoles.

---

## 3. Paper III - Entropy geometry and two-field tangency

### Established core

Paper III proves that the Gram matrix of the two-field tangent inner product is the negative entropy Hessian restricted to the tangent space. It also shows that the Paper I tangency diagnostic survives in the two-field setting and decomposes the one-field residual into eta-tangent and genuine spectral-distortion pieces.

### Correct scope

- entropy geometry,
- tangent-space identifiability,
- strict entropy concavity on the manifold under stated conditions,
- thermodynamic convexity groundwork,
- not a completed Godunov solver,
- not a proof of global symmetric hyperbolicity for the transport implementation.

### Upgrade action

Use:

> Paper III supplies information-geometric and entropy-convexity groundwork for reduced-block modelling.

Do not use:

> Paper III completes the production Godunov formulation.

### Physical meaning

The same matrix plays three roles: identifiability metric, entropy Hessian, and projection kernel. This is a strong structural unification, but it remains a manifold-geometry result unless coupled to a full PDE/transport theorem.

---

## 4. Paper IV - Observable semantics and reconstructive adequacy

### Established core

Paper IV gives operational meaning to `T0 Theta(e)`. For blackbody photons, it is exact brightness temperature. For FD/BE settings, it is an occupation temperature and coincides with brightness temperature only in the appropriate tail regime. It also derives a conditional local observable reconstruction bound.

### Correct scope

- observable semantics,
- local invertibility at generic configurations,
- conditional local bound of the form

\[
\Delta_{\rm obs}
\le
C_{\rm loc}\frac{D_{\ge2}^{\rm state}}{\sigma_{\min}(J)},
\]

under explicit hypotheses,
- diagnostic-observable bridge,
- not a global dynamical adequacy theorem,
- collision-side residual and state-side residual must not be conflated.

### Upgrade action

Use:

> Paper IV establishes a conditional local bridge from state-side off-manifold residual to observable reconstruction error.

Do not use:

> Paper IV proves that Teff diagnostics guarantee accurate transport observables globally.

### Physical meaning

The diagnostic can explain when observable reconstruction is expected to be reliable, but only after one has a state residual or a justified estimate connecting collision-side residual production to accumulated state residual.

---

## 5. Paper V - Intensity semantics inside polarised radiative transfer

### Established core

Paper V places Teff inside polarised radiative transfer by restricting it to the scalar intensity trace. The trace inherits Teff semantics. The intensity quadrupole sourcing Thomson polarisation is an exact nonlinear functional of `Theta` when the trace block is on-manifold:

\[
I_{\langle ab\rangle}
=
 c_\xi T_0^4\left\langle \Theta^4 e_{\langle a\rangle}e_{\langle b\rangle}\right\rangle_\Omega.
\]

### Correct scope

- Teff is an intensity-side source formalism,
- polarisation multipoles `E_{A_l}` and `B_{A_l}` are not parameterised by Teff,
- spin-2 transport remains in the standard hierarchy or full tensor transport,
- no observed-sky E/B phenomenology claim follows directly,
- no full polarisation closure is claimed.

### Upgrade action

Use:

> Paper V gives a trace-sector source bridge into the polarised hierarchy.

Do not use:

> Paper V gives a Teff closure of the full polarised Boltzmann hierarchy.

---

## 6. Paper V Q-normalization correction

If Table II is retained, the axisymmetric example must use

\[
\Theta(\mu)=1+A\mu+Q\left(\mu^2-\frac13\right)
=1+A P_1(\mu)+\frac{2Q}{3}P_2(\mu).
\]

Then

\[
\frac{I_2}{c_\xi T_0^4}
=
\frac52\int_{-1}^{1}\Theta(\mu)^4 P_2(\mu)\,d\mu
\]

has expansion

\[
\frac{I_2}{c_\xi T_0^4}
=
\frac83Q
+4A^2
+\frac{16}{21}Q^2
+\frac{88}{21}A^2Q
+\frac47A^4
+\frac{64}{63}A^2Q^2
+\frac{32}{63}Q^3
+\frac{320}{6237}Q^4.
\]

At `(A,Q)=(0.30,0.15)`, this gives linear term `0.400` and exact value about `0.84214`. Thus the table is consistent with this convention.

But if the manuscript writes `theta = A P_1 + Q P_2`, the linear term is `4Q`, not `8Q/3`, and the table no longer matches. The manuscript must choose one convention.

Recommended replacement:

> In the table convention, the dipole-squared contribution is nearly as large as the linear quadrupole term at `(A,Q)=(0.30,0.15)` and exceeds it only at stronger dipole examples such as `(A,Q)=(0.40,0.20)`.

---

## 7. Cross-paper consistency rules

### Rule 1: collision residual vs state residual

Paper I diagnostic monitors collision forcing. Paper IV observable bound uses state residual. Any bridge between them is a dynamical theorem or validation obligation.

### Rule 2: scalar trace vs spin-2 sector

Paper V gives trace-side source semantics. It does not reduce the spin-2 sector.

### Rule 3: local geometry vs solver claim

Paper III gives geometry; it does not complete transport hyperbolicity or production solver stability.

### Rule 4: exact on-manifold vs adequate off-manifold

Exact source formulas are exact only when the relevant block is on the reduced manifold. Off-manifold use requires residual control.

---

## 8. Revised series-level contribution statement

> Papers I-V construct a Teff reduced-manifold language for the scalar trace/intensity sector of relativistic radiation: tangency diagnostics, chemical-potential extension, entropy geometry, observable semantics, and an exact nonlinear Thomson source bridge. The correct full-transport architecture is not Teff as a full closure, but closure-free characteristic transport of the full state with Teff applied blockwise to the trace sector for semantics, source reconstruction, and diagnostics.
