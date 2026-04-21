# Teff-Characteristics Constitution

문서 목적: 전체 프로그램의 claim language를 고정한다. 이 파일은 abstract, introduction, conclusion, grant proposal, response letter에서 재사용할 수 있는 상위 문장과 금지어를 제공한다.

---

## 1. 헌법 문장

최종 채택 문장은 다음이다.

> The method of characteristics provides a closure-free full-state transport backbone/reference for the resolved distribution or tensor state. Teff does not replace the transport law. It supplies a blockwise statistical chart, trace/intensity semantics, an exact source bridge where the relevant block is on-manifold, and diagnostics for reduced-block failure.

한국어 압축형:

> characteristics는 closure가 아니라 full state를 직접 운반하는 closure-free transport backbone이다. Teff는 full solver가 아니라 trace/intensity block의 reduced semantic chart, source bridge, diagnostic layer다.

---

## 2. 왜 `full transport closure`가 틀린 표현인가

`closure`는 보통 다음 구조를 뜻한다.

\[
\text{low moments} \quad \longrightarrow \quad \text{unresolved high moments의 constitutive replacement}.
\]

예를 들어 two-moment radiation scheme에서 pressure tensor나 Eddington tensor를 energy density와 flux의 함수로 주면 closure다.

반면 characteristics는 parent kinetic equation의 phase-space trajectory를 따라 full distribution/tensor state를 운반한다.

\[
\mathcal L[f]=C[f]
\quad\leadsto\quad
\frac{d}{d\lambda} f(x(\lambda),p(\lambda)) = C[f].
\]

여기에는 higher moment를 lower moment의 함수로 대체하는 constitutive step이 없다. 따라서 characteristics는 closure가 아니라 closure-free representation이다.

---

## 3. 허용 문장과 금지 문장

| 주제 | 금지 문장 | 허용 문장 |
|---|---|---|
| characteristics | `characteristics is the full closure` | `characteristics is the closure-free full-state transport backbone` |
| Boltzmann solver | `characteristics is the full Boltzmann hierarchy solver` | `a resolved characteristic implementation is full-Boltzmann-class in the full phase-space limit` |
| Teff | `Teff is a full transport closure` | `Teff is a reduced statistical chart and diagnostic layer` |
| polarisation | `Teff parameterises full E/B polarisation` | `Teff parameterises the scalar intensity trace; spin-2 modes remain independent` |
| Paper IV | `diagnostic proves global adequacy` | `diagnostic supports a conditional local observable-reconstruction bound` |
| Paper III | `Godunov solver is complete` | `Gram-Hessian structure gives convexity/symmetrisation groundwork` |
| Paper V | `dipole-squared dominates at (A,Q)=(0.30,0.15)` | `dipole-squared is comparable to the linear quadrupole and strongly enhances the source` |

---

## 4. Status vocabulary

Use four labels consistently.

### Established

A result already proved or explicitly demonstrated in the current Paper I-V manuscript set.

Example:

> Paper I establishes a per-ray, instantaneous, collision-side tangency diagnostic under its stated assumptions.

### Conditional

A result whose theorem statement is valid under explicit hypotheses that must travel with the claim.

Example:

> Paper IV gives a conditional local observable-error bound under state-residual control, Jacobian non-degeneracy, and local calibration assumptions.

### Programmatic

A future theorem, architecture, or validation item not yet established.

Example:

> TT/TE/EE/BB spectrum-level adequacy of a hybrid characteristics/Teff pipeline is a validation program, not a Paper I-V theorem.

### Forbidden as written

A sentence that conflates the above levels.

Example:

> Papers I-V prove a full Boltzmann hierarchy solver.

---

## 5. State-space ontology

Let the parent state be

\[
X\in \mathscr H,
\qquad
\mathscr H=\bigoplus_{s\in \mathcal S}\mathscr H_s.
\]

For photons or polarised radiation, use at least

\[
\mathscr H_\gamma
=
\mathscr H_{\rm tr}
\oplus
\mathscr H_{\rm sp2}
\oplus
\mathscr H_{\rm high}.
\]

- `tr`: scalar trace/intensity block.
- `sp2`: spin-2 polarisation block, including E/B degrees of freedom.
- `high`: high spectral/angular residuals not represented by the reduced chart.

The Teff chart may act on `tr`. It does not eliminate `sp2` or `high` unless an explicit reduction, error bound, and switching policy are supplied.

---

## 6. Reduced chart language

One-field Teff manifold:

\[
f_\Theta(x,\hat e)=\Phi_\xi\!\left(\frac{x}{\Theta(\hat e)}\right).
\]

Two-field Teff-eta manifold:

\[
f_{\Theta,\eta}(x,\hat e)=\Phi_\xi\!\left(\frac{x}{\Theta(\hat e)}-\eta(\hat e)\right).
\]

This is a ray-wise equilibrium spectral-shape ansatz. It is not a general distribution function. Its value is that it supplies interpretable coordinates, realizability domain, source formulas, and residual diagnostics.

---

## 7. Full-Boltzmann-class condition

A characteristic implementation may be called `full-Boltzmann-class` only if all relevant components of the target problem are actually represented:

1. spacetime and momentum-space characteristics,
2. frequency/energy resolution or an exact energy law,
3. angular resolution sufficient for the target observables,
4. species degrees of freedom,
5. collision/source kernel used by the target equation,
6. tensor/polarisation degrees of freedom if the target includes them,
7. convergence tests against analytic, semi-analytic, or higher-resolution references.

Even then, avoid `full Boltzmann hierarchy solver` unless the method actually evolves the moment hierarchy. Characteristics and hierarchies are different representations of the parent kinetic equation.

---

## 8. Recommended abstract-level wording

> We use characteristics as a closure-free full-state transport reference and apply Teff only as a reduced trace-sector chart. The Teff variables provide observable semantics, an exact nonlinear intensity-source bridge, and residual diagnostics; they do not constitute a full closure for the polarised Boltzmann hierarchy.

---

## 9. One-line reviewer defense

If challenged on closure:

> We do not call characteristics a closure. The closure, if any, occurs only when a block is projected to a reduced Teff manifold; the characteristic layer itself is the unreduced transport reference.
