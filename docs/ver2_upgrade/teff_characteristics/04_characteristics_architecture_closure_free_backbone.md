# Closure-Free Characteristics Architecture

문서 목적: 기존 solver architecture note의 방향은 살리되, `full closure`라는 표현을 제거하고 characteristics의 정확한 수학적 지위를 고정한다.

---

## 1. Architecture one-liner

> Full tensor/species state is transported by characteristics as a closure-free reference. Teff is applied only as a blockwise reduced chart on selected trace/intensity sectors.

---

## 2. Scope

This architecture targets:

- anisotropic/inhomogeneous 1+3 covariant compatibility,
- distribution/tensor-state transport,
- species direct-sum formulation,
- polarised photon transport,
- TT/TE/EE/BB observable pipeline,
- trace-block information geometry and diagnostics.

It does not yet claim:

- closed-form exact solvability of all nonlinear backreaction,
- production-level well-posedness for every gauge, species, and collision kernel,
- equivalence between Teff reduced variables and the full distribution/tensor state,
- trace-only control of BB or full spin-2 observables,
- full Boltzmann hierarchy solver status without implementation and convergence proof.

---

## 3. Global state space

Use species direct sum:

\[
\mathscr H=\bigoplus_{s\in\mathcal S}\mathscr H_s.
\]

Each `H_s` may contain:

- scalar distribution `f_s(x^\mu,p^\mu)`,
- polarised tensor distribution `P^{(s)}_{ab}(x^\mu,p^\mu)`,
- auxiliary residual blocks,
- collision/source variables.

For photons:

\[
\mathscr H_\gamma
=\mathscr H_{\rm tr}\oplus\mathscr H_{\rm sp2}\oplus\mathscr H_{\rm high}.
\]

The architecture is honest only if `H_sp2` and relevant high residuals are either explicitly transported or adaptively resolved when their diagnostics exceed tolerance.

---

## 4. Characteristic layer

The characteristic layer solves the parent transport equation along phase-space curves.

Schematic massless transport:

\[
\frac{dx^a}{d\lambda}=p^a,
\qquad
\frac{Dp^a}{d\lambda}=0
\]

or in local tetrad form,

\[
\frac{Dp^{\hat\alpha}}{d\lambda}
= -\omega^{\hat\alpha}{}_{\hat\beta\hat\gamma}
  p^{\hat\beta}p^{\hat\gamma}+\cdots.
\]

Polarised transport additionally requires screen-basis transport and tensor projection. This is not optional if the target observable includes E/B modes.

---

## 5. Reduced Teff layer

The Teff layer is a map from a resolved or reconstructed trace block to reduced coordinates:

\[
\Pi_{\rm tr}:\mathscr H_{\rm tr}\to M_{\Theta}
\quad\text{or}\quad
\Pi_{\rm tr}:\mathscr H_{\rm tr}\to M_{\Theta,\eta}.
\]

The layer supplies:

1. semantic variables: `T0 Theta(e)`, `eta(e)`,
2. exact on-manifold source formulas,
3. residual diagnostics,
4. switching triggers,
5. observable reconstruction maps.

It does not supply full transport by itself.

---

## 6. Minimal algorithmic loop

At each macro step:

1. Transport full resolved state by characteristics.
2. Apply collision/source update to resolved blocks.
3. Extract trace/intensity block.
4. Project trace block to Teff coordinates if admissible.
5. Compute trace diagnostics: `D_coll`, `D_state`, `theta_min`, Jacobian conditioning.
6. Use Teff source bridge only where diagnostics pass.
7. Keep spin-2 block independently transported.
8. If diagnostics fail, switch the affected block to higher-resolution/full representation.
9. Compute observables from the resolved/reconstructed state.
10. Log residuals and channelwise errors.

---

## 7. Responsibility map by observable channel

| Channel | Required state | Teff role | Non-negotiable extra |
|---|---|---|---|
| TT | trace/intensity | semantics and reconstruction | state residual control |
| TE | trace + spin-2 | trace source semantics | independent E propagation |
| EE | spin-2 sourced by trace quadrupole | nonlinear source bridge | full E hierarchy/transport |
| BB | spin-2 and lensing/tensor/rotation effects | no trace-only control | full spin-2 necessity |

---

## 8. Full-Boltzmann-class criterion

A code using characteristics can be called full-Boltzmann-class only after the following are true.

### Representation criterion

The code retains all target degrees of freedom:

\[
(x^a,E,\hat e,s,\text{tensor/polarisation},\text{collision channels}).
\]

### Convergence criterion

Refinement in ray, angle, energy, timestep, screen-basis transport, and collision quadrature must converge for the observables of interest.

### Reference criterion

At least these references are required:

- Minkowski straight-line transport,
- FLRW redshift limit,
- Bianchi/anisotropic background stress test,
- known Thomson source test,
- polarisation screen-basis consistency test,
- high-resolution Boltzmann/Monte Carlo/analytic comparison where available.

Until then, use:

> characteristic transport architecture,

not:

> full Boltzmann solver.

---

## 9. Closure-free block theorem in architecture language

Let `X_exact(t)` be the full characteristic solution and `X_hyb(t)` a hybrid solution in which only trace block sources are replaced by Teff-reconstructed sources.

If propagation operators are the same and source differences are localised to the trace block, then the leading source error is also localised to the trace block. Spin-2 propagation error is not caused by Teff unless spin-2 variables are themselves reduced or incorrectly sourced.

This supports a clean engineering statement:

> Teff failure is a reduced-block source/diagnostic failure, not a failure of the resolved characteristic transport layer.

---

## 10. Failure modes

### F1. False full-closure language

Symptom: manuscript says `characteristics is full closure`.

Fix: replace with `closure-free full-state transport backbone`.

### F2. Trace-spin conflation

Symptom: Paper V source bridge is used to claim control over BB.

Fix: explicitly state spin-2 transport remains independent.

### F3. Diagnostic overpromotion

Symptom: collision-side `D_{>=2}` is treated as direct observable error.

Fix: insert state-residual/dynamical accumulation theorem or validation.

### F4. Solver overclaim

Symptom: method is called `full Boltzmann hierarchy solver` without hierarchy evolution or full phase-space implementation.

Fix: call it `closure-free characteristic reference` or `full-Boltzmann-class only in the resolved limit`.

---

## 11. Architecture conclusion

The architecture is stronger after demotion of language. It no longer tries to sell Teff as a full solver. It uses characteristics to keep the full state honest and Teff to expose meaningful trace-sector thermodynamics, source nonlinearities, and failure diagnostics.
