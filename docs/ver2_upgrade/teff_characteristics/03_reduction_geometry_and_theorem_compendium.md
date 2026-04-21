# Reduction Geometry and Theorem Compendium

문서 목적: 기존 theorem compendium을 claim status 중심으로 재정렬한다. numbering 자체보다 중요한 것은 어떤 정리가 무엇을 정당화하고 무엇을 정당화하지 않는지다.

---

## 1. Parent kinetic structure

Parent equation은 추상적으로 다음처럼 쓴다.

\[
\partial_t X=\mathcal G(X),
\qquad
\mathcal G=\mathcal G_{\rm str}+\mathcal G_{\rm coll}.
\]

또는 covariant notation으로

\[
\mathcal L[X]=C[X].
\]

여기서 `X`는 scalar distribution일 수도 있고, polarised tensor distribution일 수도 있으며, species direct sum일 수도 있다.

---

## 2. Reduced manifold and projection

Let `M` be a reduced manifold embedded in ambient state space `H`.

- inclusion: `i: M -> H`,
- projection/reduction map: `Pi: H -> M`,
- tangent projector at `g in M`: `P_g`,
- normal projector: `Q_g = I - P_g`.

For Teff:

\[
M_\Theta = \left\{f_\Theta(x,\hat e)=\Phi_\xi\left(\frac{x}{\Theta(\hat e)}\right)\right\},
\]

and for the two-field extension:

\[
M_{\Theta,\eta}=\left\{f_{\Theta,\eta}(x,\hat e)=\Phi_\xi\left(\frac{x}{\Theta(\hat e)}-\eta(\hat e)\right)\right\}.
\]

---

## 3. Tangency diagnostic cluster

### Theorem cluster A: per-ray tangency

For a fixed ray, the normalized collision field

\[
G_\xi=\frac{C[f]}{f(1+\xi f)}
\]

is tangent to the enlarged per-ray exponential family iff its higher Laguerre components vanish:

\[
G_{\xi,n}=0\qquad(n\ge2).
\]

### Status

Established within Paper I assumptions.

### Scope limit

This is not full Teff-manifold tangency. The angular consistency condition and constant-mode obstruction are separate.

### Physical meaning

The collision operator is trying to change only the ray's equilibrium parameters, not create spectral-shape distortion along that ray.

---

## 4. Entropy projection cluster

Paper I's entropy-projection inequality is a single-instant reduction-map statement. It decomposes the reduction entropy cost into shape mismatch and amplitude mismatch.

### Status

Established under stated assumptions.

### Scope limit

It is not a finite-time dynamical H-theorem for the reduced transport system.

### Critical distinction

The collision diagnostic and the state residual live on different objects.

- collision-side diagnostic: `C[f]` projected in energy modes,
- state-side residual: `f - Pi(f)` or equivalent off-manifold state deviation.

The first predicts production tendency. The second appears in reconstruction error bounds.

---

## 5. Two-field geometry cluster

Paper II and Paper III support the following chain.

1. The coordinate `x=E/(k_B T0)` avoids the direction-dependent domain pathology of an energy variable shifted by direction-dependent chemical potential.
2. A direction-dependent eta-dipole is not absorbable into scalar chemical potential plus temperature multipoles.
3. The two-field tangent Gram matrix is the negative entropy Hessian restricted to the tangent space.
4. The same Gram matrix acts as identifiability metric, entropy Hessian, and projection kernel.

### Status

Mostly established analytically under stated assumptions, with selected monotonicity/full-rank claims numerical over tested configurations.

### Scope limit

This does not prove transport-performance superiority or a completed Godunov solver.

---

## 6. Observable semantics cluster

For blackbody photons:

\[
T_{\rm eff}(\hat e)=T_0\Theta(\hat e)
\]

is exact brightness temperature. More generally it is an occupation-temperature coordinate.

Paper IV also supports local reconstructive adequacy of the schematic form

\[
\Delta_{\rm obs}
\le
C_{\rm loc}\frac{D_{\ge2}^{\rm state}}{\sigma_{\min}(J)}.
\]

### Status

Conditional theorem.

### Required hypotheses

- state residual controls relevant off-manifold spectral content,
- local Jacobian has nonzero minimum singular value,
- observable map is locally regular,
- calibration constant remains controlled on the sample.

### Scope limit

No global-in-time adequacy follows without dynamical residual production and propagation estimates.

---

## 7. Polarisation source cluster

If the trace/intensity block is on the Teff manifold, then the intensity quadrupole sourcing Thomson polarisation is

\[
I_{\langle ab\rangle}
=
 c_\xi T_0^4\left\langle \Theta^4 e_{\langle a\rangle}e_{\langle b\rangle}\right\rangle_\Omega.
\]

### Status

Established as an intensity-side source bridge in Paper V.

### Scope limit

The Teff variables do not parameterise the spin-2 polarisation block. `E_{A_l}` and `B_{A_l}` remain independent transport degrees of freedom.

---

## 8. Ambient vs projected defect theorem

This is the central correction in the md upgrade.

Let `U_t(g)` be the exact ambient evolution and `S_t(g)` be the reduced tangent evolution on `M`.

### Ambient defect

\[
\Delta_t(g)=U_t(g)-S_t(g).
\]

Then

\[
\left.\frac{d}{dt}\Delta_t(g)\right|_{t=0}
=Q_g\mathcal G(g).
\]

Thus first-order normal leakage is exactly the normal component of the parent generator.

### Projected defect

\[
\mathcal E_t(g)=\Pi(U_t(g))-S_t(g).
\]

Generally

\[
\left.\frac{d}{dt}\mathcal E_t(g)\right|_{t=0}=0,
\]

because the projection kills first-order normal displacement. Projected error usually opens at second order.

### Consequence

Do not identify a nonzero first-order normal leakage with first-order projected-coordinate error. The two defects answer different questions.

---

## 9. Direct-sum block theorem, corrected language

Let

\[
\mathscr H=\mathscr H_{\rm res}\oplus \mathscr H_{\rm red}.
\]

If `H_res` is transported as a resolved state by characteristics, it is not a closure-failure locus. Closure or reduction error can only arise in `H_red` where a projection to a reduced chart is applied.

### Correct statement

> Fully resolved characteristic blocks do not require moment closure. Reduction failure is localised to blocks where a reduced chart is imposed.

### Incorrect statement

> Characteristics is the full closure.

---

## 10. Dependency graph

\[
\text{per-ray Teff geometry}
\to
\text{tangency diagnostic}
\to
\text{state residual control obligation}
\to
\text{observable reconstruction}
\to
\text{spectrum-level validation}.
\]

\[
\text{two-field eta extension}
\to
\text{Gram-Hessian identity}
\to
\text{projection kernel / entropy geometry}
\to
\text{candidate reduced-block numerics}.
\]

\[
\text{closure-free characteristics}
\to
\text{full-state transport reference}
\to
\text{blockwise Teff semantics}
\to
\text{source bridge and diagnostics}.
\]

---

## 11. Claim status table

| Claim | Status | Required caution |
|---|---|---|
| Paper I tangency diagnostic | Established | collision-side, per-ray, instantaneous |
| Paper II eta non-redundancy | Established/partly numerical | not transport-performance claim |
| Paper III Gram-Hessian identity | Established | not completed solver hyperbolicity |
| Paper IV observable bound | Conditional | state residual, local Jacobian, calibration assumptions |
| Paper V source bridge | Established in trace block | not spin-2 closure |
| characteristics backbone | Architecture/synthesis | closure-free, not closure |
| full-Boltzmann-class implementation | Programmatic | needs actual resolution and convergence validation |
| TT/TE/EE/BB adequacy | Programmatic validation | channelwise tests required |

---

## 12. Recommended theorem-compendium title

Use:

> Teff-Characteristics Program: Reduction Geometry, Source Semantics, and Closure-Free Transport Architecture

Avoid:

> Full Closure Theorem Compendium.
