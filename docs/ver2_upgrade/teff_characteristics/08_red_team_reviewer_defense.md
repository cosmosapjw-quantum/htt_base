# Red-Team Reviewer Defense

문서 목적: 가장 공격적인 reviewer가 물을 질문을 미리 세우고, 방어 가능한 답변과 반드시 피해야 할 답변을 분리한다.

---

## 1. Reviewer objection: `You call characteristics a closure. That is wrong.`

### Concede and correct

맞다. `closure`라는 단어는 부정확하다. 개정본에서는 characteristics를 closure라고 부르지 않는다.

### Defensible response

> We agree that the method of characteristics is not a closure in the moment-hierarchy sense. We use it as a closure-free full-state transport reference. The only reduction occurs when a selected block is projected onto the Teff manifold.

### Never say

> Characteristics is a full closure because it solves everything.

---

## 2. Reviewer objection: `Is this a full Boltzmann hierarchy solver?`

### Short answer

No, not as stated.

### Defensible response

> It is not a Boltzmann hierarchy solver unless the hierarchy variables are the evolved representation. A characteristic implementation can be full-Boltzmann-class only in the resolved phase-space/tensor/species/collision limit and only after convergence validation. Our present claim is architectural: characteristics provide the full-state transport reference, and Teff provides blockwise trace-sector semantics and diagnostics.

### Never say

> Characteristics are automatically the full Boltzmann hierarchy.

---

## 3. Reviewer objection: `Your Teff diagnostic is collision-side. Why does it control observables?`

### Defensible response

> It does not directly control observables. Paper I gives a collision-side production diagnostic. Paper IV gives a conditional local observable bound in terms of a state-side residual. A dynamical residual-production estimate or validation is required to connect the two.

### Required revision

Always distinguish:

- `D_coll`: diagnostic on collision/source field,
- `D_state`: residual of the state relative to the reduced manifold,
- `Delta_obs`: observable reconstruction error.

---

## 4. Reviewer objection: `Paper III is just information geometry, not a solver.`

### Defensible response

> Correct. We present Paper III as entropy-geometric and convexity groundwork. It supplies the Gram-Hessian identity and projection structure; it does not by itself establish a production Godunov solver or global symmetric hyperbolicity.

### Never say

> Paper III completes the solver.

---

## 5. Reviewer objection: `Paper V does not solve polarisation.`

### Defensible response

> Correct. Paper V is an intensity-side source theorem inside polarised transfer. It identifies what Teff parameterises—the scalar trace—and what it does not parameterise—the spin-2 E/B sector. The nonlinear bridge computes the Thomson source from the trace block when that block is on the Teff manifold.

### Never say

> Teff controls E/B polarisation.

---

## 6. Reviewer objection: `Your Q convention is inconsistent.`

### Defensible response

> We have fixed the convention. The table uses `Theta=1+A mu+Q(mu^2-1/3)`, equivalently `Theta=1+A P1+(2Q/3)P2`. Under this convention the linear term is `8Q/3`, and the table values are reproduced. We removed language that simultaneously assumes `theta=A P1+Q P2` with linear `4Q`.

### Required revision

Put the convention near the table and state explicitly whether angle brackets denote a full integral or normalized angular average.

---

## 7. Reviewer objection: `The novelty is overstated.`

### Strong but safe novelty claims

1. Per-ray equilibrium-family tangency diagnostic for spectral-shape failure.
2. Direction-dependent eta-dipole as a non-redundant number/energy anisotropy coordinate.
3. Gram-Hessian unification of identifiability, entropy curvature, and projection kernel in the two-field manifold.
4. Operational brightness/occupation-temperature semantics for Teff variables.
5. Exact nonlinear trace-sector Thomson source bridge and explicit dipole-squared contribution.
6. Architecture-level separation of full-state characteristic transport from blockwise reduced semantics.

### Weak or unsafe novelty claims

- `new full Boltzmann solver`,
- `complete polarisation closure`,
- `universal superiority over M1/Monte Carlo/PSTF`,
- `global dynamical adequacy from local diagnostic`,
- `BB control from trace Teff`.

---

## 8. Reviewer objection: `This is only exact on the manifold.`

### Defensible response

> Yes. Exact source reconstruction is an on-manifold statement. Off-manifold use is controlled only through residual diagnostics and validation. This is a feature of the framing, not something to hide.

### Recommended wording

> exact on the trace manifold; diagnostic and conditional off the manifold.

---

## 9. Reviewer objection: `Why not just use full characteristics and ignore Teff?`

### Defensible response

> Full characteristics give transport honesty but not automatically semantic compression, source decomposition, or reduced-block failure localization. Teff adds interpretable trace-sector coordinates, an exact nonlinear source map when admissible, realizability diagnostics, and a structured way to decide when a reduced chart should be abandoned.

This is the best positive case for Teff after dropping full-closure language.

---

## 10. Abstract patch, defensive version

> We formulate Teff as a reduced trace-sector chart embedded in a closure-free characteristic transport architecture. The characteristic layer transports the resolved distribution/tensor state; the Teff layer supplies thermodynamic semantics, an exact nonlinear intensity-source bridge, and residual diagnostics for selected blocks. This avoids treating Teff as a full polarised closure or as a substitute for the Boltzmann transport law.

---

## 11. Conclusion patch, defensive version

> The correct conclusion is not that Teff replaces Boltzmann transport. The correct conclusion is that, inside a full-state characteristic transport framework, Teff gives a controlled and physically interpretable reduced language for the scalar trace/intensity sector. Its failures are diagnosable and localised; its successes are exact on the trace manifold and conditionally useful off it.
