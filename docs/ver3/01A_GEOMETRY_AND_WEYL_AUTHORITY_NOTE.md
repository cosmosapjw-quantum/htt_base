# 01A. Geometry and Weyl Authority Note
## dual-route curvature / constraint operators / electric-magnetic Weyl diagnostics

---

## 0. purpose

이 문서는 geometry and diagnostic layer를 implementation contract 수준으로 더 직접적으로 고정한다.
다음 네 항목만 다룬다.

1. invariant basis \(\rightarrow\) orthonormal frame geometry assembly
2. dual-route Ricci authority equations
3. background constraint operators as implementation contracts
4. \(E_{ab},H_{ab}\) diagnostic and residual route

---

## 1. invariant basis to orthonormal commutators

Given \(C^A{}_{BC}\), derived triad \(e_i{}^A\), inverse \(e_A{}^i\),

\[
C^i{}_{jk}=e_A{}^i e_j{}^B e_k{}^C C^A{}_{BC}.
\]

### implementation note
The scaling test
\[
\gamma_{AB}=a^2\delta_{AB}
\quad\Longrightarrow\quad
C^i{}_{jk}\propto a^{-1}
\]
is mandatory for the commutator pushforward helper.

---

## 2. connection contract

A geometry-ready backend must expose a single route

```text
connection_from_commutators(Cortho_ijk) -> Gamma^i_{jk}
```

that is reused everywhere.  No local ad hoc reconstructions are allowed.

The connection must be interpreted as the torsion-free Levi-Civita connection compatible with the orthonormal frame and its commutators.

---

## 3. dual-route Ricci contract

Every geometry-ready branch must provide two numerically comparable routes for the spatial Ricci tensor/scalar.

### route A — Cartan / connection route
\[
{}^{(3)}R_{ij} = {}^{(3)}R_{ij}[\Gamma^k{}_{mn}, C^k{}_{mn}].
\]

### route B — compact family-aware route
\[
{}^{(3)}R_{ij} = {}^{(3)}R_{ij}[\text{family canonical data}, \gamma_{AB}, e_i{}^A].
\]

The implementation must expose

```text
spatial_ricci_from_connection(...)
spatial_ricci_from_compact_formula(...)
dual_route_curvature_residual(...)
```

### residual policy
If route B is unavailable for a family/branch, the residual status is `UNAVAILABLE`, not zero.

---

## 4. Ricci anisotropy split

Define
\[
{}^{(3)}S_{AB}
=
{}^{(3)}R_{\langle AB\rangle_\gamma},
\qquad
{}^{(3)}R=\gamma^{AB}{}^{(3)}R_{AB}.
\]

The background shear equation must consume \({}^{(3)}S_{AB}\), not a family-specific proxy unless explicitly documented as algebraically identical.

---

## 5. derivative operators each backend must provide

At minimum, each backend contract must specify how it provides the following maps:

```text
Div_sigma_A(background_state, sigma_AB) -> vector_A
Grad_theta_A(background_state, theta) -> vector_A
ModeMix_ops(background_state, truncation) -> sparse block operators
SeedRegularity_ops(seed_request) -> local regularity objects
```

This may be analytical or collocational, but it must be explicit per family.

---

## 6. background constraint operators

### Gauss
\[
\mathcal C_{\rm G}
=
\frac13\Theta^2-\kappa\rho_{\rm tot}-\Lambda+\frac12{}^{(3)}R-\sigma^2.
\]

### Codazzi
\[
\mathcal C_{{\rm C},A}
=
D^B \sigma_{AB}-\frac23 D_A\Theta-\kappa q_A.
\]

### implementation rule
`Codazzi != ||q||`.  
A backend must specify how \(D_A\Theta\) and \(D^B\sigma_{AB}\) are evaluated in its chosen representation.

---

## 7. electric and magnetic Weyl diagnostics

The package does not require \(E_{AB},H_{AB}\) to drive the minimal background solver, but once the diagnostic gate opens, the following route is mandatory:

1. derive or evaluate the spatial curvature and shear terms,
2. construct \(E_{AB}\) and \(H_{AB}\) using the chosen 1+3 identities for the homogeneous branch,
3. record normalized residuals against the constraint/evolution identities selected for that branch.

### implementation recipe
Every backend that opens the Weyl gate must provide:

```text
electric_weyl(background_state, geom) -> E_AB
magnetic_weyl(background_state, geom) -> H_AB
weyl_residuals(background_state, geom, E_AB, H_AB) -> dict
```

### normalized residual policy
Residuals must be dimensionless.  The implementation must specify the normalizing scale used for each diagnostic.

---

## 8. geometry diagnostic recipe (one-page authority recipe)

```text
input:
    family_spec, gamma_AB, theta, sigma_AB, sources

1. derive triad e_i^A from gamma_AB
2. push canonical C^A_{BC} to orthonormal C^i_{jk}
3. compute Gamma^i_{jk}
4. compute Ricci via route A
5. compute Ricci via route B if available
6. compute dual-route curvature residual
7. compute S_AB = PSTF_gamma(R_AB)
8. compute Gauss and Codazzi residuals
9. if Weyl gate open:
       compute E_AB, H_AB, and normalized residuals
output:
    GeometryDiagnostics bundle
```

---

## 9. one-line summary

geometry-ready는 단순히 \(C^A{}_{BC}\) 를 저장하는 것이 아니라,  
**pushforward \(\rightarrow\) connection \(\rightarrow\) dual-route Ricci \(\rightarrow\) \(S_{AB}\) and residuals** 가 문서상 implementation contract로 닫혀 있다는 뜻이다.
