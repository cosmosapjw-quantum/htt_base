# 01. SSOT — Formalism and Physics
## 1+3 gauge-invariant covariant PSTF authority language + tetrad/invariant-basis computational engine

---

## 0. scope

이 문서는 low-\ell Bianchi Einstein–Boltzmann solver의 본체 SSOT다.
여기서는 아래 네 층만 다룬다.

1. 실제 연구용 low-\ell solver를 위한 수학적 formalism
2. solver에 반드시 들어가야 할 물리현상
3. solver split / state / operator / IC contract
4. pseudocode로 내려가기 위한 authority-level equations

관측가능량 / fitting / likelihood는 `06_OBSERVABLES_AND_STATISTICS_APPENDIX.md` 로 분리한다.

---

## 1. conventions, frames, and time gauges

### 1.1 spacetime split

\[
g_{ab}=-n_an_b+h_{ab},\qquad h_{ab}=g_{ab}+n_an_b,\qquad h_{ab}n^b=0.
\]

\[
\dot X \equiv n^a\nabla_a X,\qquad
D_a X \equiv h_a{}^b \nabla_b X.
\]

### 1.2 kinematics of the background congruence

\[
\nabla_a n_b
=
-\!A_b n_a
+\frac13\Theta h_{ab}
+\sigma_{ab}
+\omega_{ab}.
\]

Homogeneous Bianchi backgrounds in the chosen normal congruence use
\[
A_a=0,\qquad \omega_{ab}=0,
\]
unless a family card explicitly requests otherwise.  Global tilt is encoded in matter species frames, not by changing the background normal congruence.

### 1.3 signature, scale, transport direction

\[
(-,+,+,+),\qquad a_m=e^\alpha,\qquad H=\dot\alpha.
\]

Photon propagation direction in the normal frame is \(e^a\), with
\[
e^a n_a = 0,\qquad e^a e_a = 1.
\]

Output sky direction is
\[
\hat n = -e.
\]

This sign is frozen package-wide.

### 1.4 time gauges

Background evolution is evolved in proper time \(t\).
Hierarchy, visibility, and line-of-sight kernels are evolved in conformal time \(\eta\) with
\[
d\eta = \frac{dt}{a_m}.
\]

#### mandatory bridge helpers
Every implementation must expose:

```text
eta_from_t(t_grid, a_m_grid) -> eta_grid
dt_dtau_background(...) -> ...
GammaT_eta(a_m, ne_phys, xe, sigmaT, c_if_needed) -> GammaT_conformal
```

### 1.5 unit freeze

The geometric core is dimensionless or geometric-unit normalized.  
Adapters may use physical SI constants, but only at the adapter boundary.

| object | frozen interpretation | implementation note |
|---|---|---|
| \(\gamma_{AB}\) | invariant-basis spatial metric | primary background state |
| \(e_i{}^A\) | derived orthonormal triad | never primary state |
| \(\sigma_T\) | physical Thomson cross section | only in visibility/collision adapter |
| \(n_e^{\rm phys}\) | physical electron density | adapter-side |
| \(\Gamma_T^{(\eta)}\) | conformal-time opacity | hierarchy/LoS side |
| \(c\) | explicit only in physical-unit adapter | otherwise absorbed into bridge |

---

## 2. 1+3 authority language and tetrad computational engine

### 2.1 invariant basis and orthonormal triad

Let \(\{E_A\}\) be a left-invariant basis on the Bianchi spatial hypersurfaces with
\[
[E_B,E_C]=C^A{}_{BC}E_A.
\]

The invariant-basis metric is \(\gamma_{AB}(t)\).  
The orthonormal triad \(e_i{}^A\) is derived from
\[
\delta_{ij}=e_i{}^A e_j{}^B \gamma_{AB}.
\]

We define the inverse triad \(e_A{}^i\) by
\[
e_A{}^i e_i{}^B = \delta_A{}^B,\qquad
e_i{}^A e_A{}^j=\delta_i{}^j.
\]

The orthonormal-frame commutators are
\[
C^i{}_{jk}=e_A{}^i e_j{}^B e_k{}^C C^A{}_{BC}.
\]

### 2.2 basis typing

This package distinguishes three tensor locations:

1. invariant basis indices \(A,B,\dots\)
2. orthonormal frame indices \(i,j,\dots\)
3. PSTF spacetime indices \(a,b,\dots\)

Implementations must not mix these silently.

### 2.3 gamma-raising / lowering and PSTF

For invariant-basis vectors,
\[
v_A = \gamma_{AB} v^B,\qquad
v^A = \gamma^{AB} v_B.
\]

For rank-2 tensors in the invariant basis,
\[
\mathrm{tr}_\gamma(X) = \gamma^{AB}X_{AB},
\qquad
\|X\|_\gamma^2 = X_{AB}X^{AB}.
\]

The \(\gamma\)-PSTF projector is
\[
X_{\langle AB\rangle_\gamma}
=
X_{(AB)}
-\frac13 \gamma_{AB}\gamma^{CD}X_{CD}.
\]

Every implementation must use a single helper layer for these operations; direct `trace` or Euclidean contractions on invariant-basis tensors are forbidden.

---

## 3. all 11 Bianchi families: canonical algebra layer

### 3.1 family table

| family | class | canonical data idea | isotropic-limit anchor | special branch note |
|---|---|---|---|---|
| I | A | \(a=0,\ n_i=0\) | yes | flat |
| II | A | one nonzero nilpotent \(n_i\) | no | Heisenberg / nil |
| III | B | class-B special branch | no | often treated as \(VI_{-1}\) branch |
| IV | B | solvable rank-1 branch | no | no FLRW anchor |
| V | B | \(a\neq0,\ n_i=0\) | yes | open |
| VI\(_0\) | A | mixed-sign \(n_i\) | no | class A intrinsic |
| VI\(_h\) | B | \(a\neq0,\ n_2n_3<0,\ h<0\) | no | \(h\)-dependent branch |
| VII\(_0\) | A | \(n_2n_3>0,\ a=0\) | yes | flat helical |
| VII\(_h\) | B | \(a\neq0,\ n_2n_3>0,\ h>0\) | yes | \(h\)-dependent helical/open |
| VIII | A | noncompact \(SL(2,\mathbb R)\)-type | no | intrinsic |
| IX | A | compact \(SU(2)\)-type | yes | closed |

### 3.2 class-B \(h\)-consistent canonical gauge

For class-B families with \(a_A=(a,0,0)\) and \(n_{AB}=\mathrm{diag}(0,n_2,n_3)\),
\[
h = \frac{a^2}{n_2 n_3}.
\]

Therefore VI\(_h\) and VII\(_h\) family cards must expose canonical data satisfying this relation.  
`h` is not a mere metadata label.

### 3.3 orthogonal, global tilt, local boost

For every family the design distinguishes:

1. **orthogonal background:** all matter species comoving with \(n^a\)
2. **global tilt:** one or more matter species have homogeneous nonzero \(v_s^A(t)\)
3. **local observer boost:** a post-processing operation on outputs only

This separation is mandatory at background, perturbation, and output layers.

---

## 4. nonperturbative homogeneous background

### 4.1 primary background state

\[
U_{\rm bg}
=
\{\alpha,\ \gamma_{AB},\ \Theta,\ \sigma_{AB},\ \Lambda,\ \rho_s,\ p_s,\ v_s^A\}_{\rm family\ branch}.
\]

Derived quantities include
\[
e_i{}^A,\quad C^i{}_{jk},\quad \Gamma^i{}_{jk},\quad {}^{(3)}R_{ij},\quad {}^{(3)}R.
\]

### 4.2 tilted matter projection in the normal frame

For each perfect-fluid species in its rest frame \((\hat\rho_s,\hat p_s)\) and homogeneous tilt \(v_s^A\),
\[
u_s^a = \Gamma_s (n^a + v_s^a),
\qquad
\Gamma_s = (1-v_s^2)^{-1/2},
\qquad
v_s^2 = \gamma_{AB} v_s^A v_s^B.
\]

Normal-frame projections are

\[
\rho_s = \Gamma_s^2(\hat\rho_s+\hat p_s)-\hat p_s,
\]

\[
q_A^{(s)} = \Gamma_s^2(\hat\rho_s+\hat p_s)\, v_A^{(s)},
\qquad
v_A^{(s)}=\gamma_{AB}v_s^B,
\]

\[
p_s = \hat p_s + \frac13 \Gamma_s^2(\hat\rho_s+\hat p_s) v_s^2,
\]

\[
\pi^{(s)}_{AB}
=
\Gamma_s^2(\hat\rho_s+\hat p_s)\,
v_{\langle A}v_{B\rangle_\gamma}.
\]

The total sources are
\[
\rho_{\rm tot}=\sum_s \rho_s,\quad
p_{\rm tot}=\sum_s p_s,\quad
q_A=\sum_s q_A^{(s)},\quad
\pi_{AB}=\sum_s \pi_{AB}^{(s)}.
\]

### 4.3 background constraints and evolution

The mandatory authority equations are:

\[
\mathcal C_{\rm G}
=
\frac13\Theta^2
-\kappa \rho_{\rm tot}
-\Lambda
+\frac12 {}^{(3)}R
-\sigma^2,
\qquad
\sigma^2=\frac12 \sigma_{AB}\sigma^{AB},
\]

\[
\mathcal C_{{\rm C},A}
=
D^B \sigma_{AB}
-\frac23 D_A \Theta
-\kappa q_A,
\]

\[
\dot\Theta
=
-\frac13\Theta^2
-2\sigma^2
-\frac12\kappa(\rho_{\rm tot}+3p_{\rm tot})
+\Lambda,
\]

\[
\dot\sigma_{\langle AB\rangle_\gamma}
=
-\frac23\Theta \sigma_{AB}
-\sigma_{\langle A}{}^C \sigma_{B\rangle C}
-{}^{(3)}S_{AB}
+\frac12 \kappa \pi_{AB},
\]
where \({}^{(3)}S_{AB}\) is the \(\gamma\)-PSTF spatial Ricci anisotropy.

Implementations may add equivalent family-aware forms, but must remain algebraically equivalent to these contracts.

### 4.4 constraint-preserving evolution

Background solvers must track normalized residuals:
- Gauss
- Codazzi
- dual-route curvature
- \(E/H\) diagnostics if opened

Residual unavailable is **not zero**; it is **unavailable** and must fail closed.

---

## 5. radiation kinetic theory and exact collision contract

### 5.1 transport and collision frames

Transport is expressed in the normal frame \(n^a\).  
Collision/source/visibility are evaluated in the electron frame \(u_e^a\).

### 5.2 exact anisotropic redshift

For photon four-momentum \(k^a\) decomposed with direction \(e^a\),
\[
\frac{d\ln E}{dt}
=
-\frac13\Theta
-\sigma_{ab}e^a e^b,
\]
for the homogeneous shear-driven background redshift piece relevant to the solver design.

### 5.3 polarization basis transport

The screen basis \((e_1^a,e_2^a)\) orthogonal to \((n^a,e^a)\) must be transported consistently with the chosen tier-A convention.
The phase/sign choice is frozen in `02A_HIERARCHY_LAYOUT_AND_TIERA_TRANSPORT_NOTE.md`; implementations must not invent a new phase convention locally.

### 5.4 exact electron-frame Thomson block

The electron-frame scalar and tensor source pieces are frozen as

\[
\tilde\zeta_{ab}
=
\frac34 \tilde I_{ab}
+\frac92 \tilde E^{\rm pol}_{ab}.
\]

The energy-integrated intensity source contract is

\[
\tilde{\mathcal C}_I(\tilde e)
=
-\tilde n_e \sigma_T I_{\rm dir}(\tilde e)
+\frac{\tilde n_e \sigma_T}{4\pi}
\left[
I_0 + \tilde\zeta_{ab}\tilde e^a \tilde e^b
\right].
\]

The polarization-source contract is

\[
\tilde{\mathcal C}^{\rm pol}_{ab}(\tilde e)
=
-\tilde n_e \sigma_T P_{ab}^{\rm dir}(\tilde e)
+\frac{\tilde n_e \sigma_T}{4\pi}
\left[\tilde H_a{}^c\tilde H_b{}^d \tilde\zeta_{cd}\right]^{TT}.
\]

#### mandatory API separation
The design distinguishes
- `I_dir(e)` : directional intensity
- `I0` : scalar monopole input

They must never be conflated.

### 5.5 visibility and tilt modulation

In conformal time the baseline opacity is
\[
\Gamma_T^{(\eta)} = a_m\, n_e^{\rm phys}\, x_e\, \sigma_T \, c_{\rm if\ needed}.
\]

With global electron tilt,
\[
\tilde\Gamma_T^{(\eta)}(e)
=
\Gamma_T^{(\eta)}\, \Gamma_e \, (1-v_e\cdot e),
\]
where the sign convention is package-wide frozen.

### 5.6 quadrupole / polarization source

The solver must explicitly represent photon quadrupole content and the polarization source it induces.  
Tier-B implementations may express this via hierarchy multipoles, while tier-A may express it via angular transport variables, but the contract is the same: the polarization source must be generated from actual quadrupolar anisotropy, not from an ad hoc scalar proxy.

---

## 6. perturbations, hierarchy, and IC provenance

### 6.1 perturbation split

The perturbative solver evolves spatial/temporal fluctuations on top of the homogeneous Bianchi background.  
The background is nonperturbative in time; the perturbations carry the spatial structure through family-aware backends.

### 6.2 tier split

- **tier A:** exact/reference ray and basis transport
- **tier B:** projected production hierarchy for low-\(\ell\)

tier B is not a disguised full exact solver.  
It is the production solver once the exact contracts have been projected into the chosen low-\(\ell\) truncation.

### 6.3 perturbation state contract

At design level the minimum low-\(\ell\) projected state is

\[
U_{\rm pert}
=
\{
\delta_{\rm matter},
v_{\rm matter},
I_{\ell m},
E_{\ell m},
B_{\ell m},
N_{\ell m},
x_e,\Gamma_T^{(\eta)},g,\Pi_{\rm src},\dots
\}_{\mu,\ell,m,\text{sector}}.
\]

Flattening order, sector order, and sparse block layout are frozen in `02A_HIERARCHY_LAYOUT_AND_TIERA_TRANSPORT_NOTE.md`.

### 6.4 family-specific backends

Every family backend must expose:

```text
build_backend(family_spec, truncation, chart_options) -> backend
backend.operator_factory(background_state) -> GeometryOps, ModeOps
backend.seed_factory(seed_request) -> SeedPack
backend.backend_residuals(...) -> dict
backend.label_translator(...) -> storage labels
```

### 6.5 isotropic-limit vs intrinsically anisotropic families

- isotropic-limit families: I, V, VII\(_0\), VII\(_h\), IX
- intrinsically anisotropic families: II, III, IV, VI\(_0\), VI\(_h\), VIII

Regular FLRW-like seeds may be used only in the isotropic-limit set.  
Intrinsic families must use family-adapted seed provenance.

### 6.6 tilted IC provenance

The tilted IC authority path is

1. build regular seed in the electron frame,
2. inverse-boost to the chosen normal-frame hierarchy variables,
3. project to constraint-compatible initial data,
4. reject if residuals are not below the IC gate.

---

## 7. must-have physical ingredients list

The following are mandatory for a genuine low-\ell Bianchi Boltzmann solver design:

1. background anisotropic redshift
2. polarization-basis transport
3. exact electron-frame Thomson scattering
4. photon quadrupole / polarization source
5. baryon-electron-photon slip and TCA handling
6. neutrino free streaming / anisotropic stress
7. recombination visibility
8. homogeneous reionization
9. global tilt modulation of collision/visibility
10. local observer boost separation
11. anisotropic-background-induced mode mixing
12. constraint-preserving background evolution

If any of these are absent from the design package, the package is incomplete.

---

## 8. what is mandatory now vs deferred

### mandatory now
- all items in sections 1–7
- all 11 family design-contract coverage
- orthogonal / global tilt / local boost split
- family-specific backend contract and IC provenance rules
- tier-A vs tier-B role split
- gate-before-fitting

### deferred
- patchy reionization
- anisotropic recombination microphysics beyond isotropic-history adapter
- full high-\(\ell\)
- unavailable analytic family backends beyond generic fallback
- full covariance-likelihood implementation detail

---

## 9. one-line summary

이 SSOT의 핵심은  
**1+3 PSTF authority language로 물리를 고정하고, tetrad/invariant-basis engine으로 all 11 family를 동일한 geometry/backend interface 아래 계산 가능하게 만든 뒤, exact collision/tier split/IC provenance를 구현 가능한 수준으로 연결하는 것** 이다.
