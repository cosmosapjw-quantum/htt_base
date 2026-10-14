# G05-B source recovery: isolated eigenframe IFT and cubic-germ realization

Package card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` → `HTT_ALL_OBLIGATIONS_20261011/tasks/G05-B.json`
(parent GR-CAS-05; requires G05-A; status at read time `PLANNED_NOT_EXECUTED`).
All paths below are relative to `docs/research_program/gr_statistics_loops_20260930/` unless absolute.
This package is not a blind CAS axis run; like G05-A, it reads `gr/` for source recovery
(the blind-axis `forbidden_sibling_paths` of `cas/contracts/CAS-05.json` govern blind axis runs only).

## Card content (translated)

- Scope: existence of the smooth isolated eigenframe, and a real germ realizing the prescribed local rate jet.
- Lean steps: (1) define the gauge-fixed map of the normalized future eigenvector + eigenvalue
  equation and its derivative; (2) prove invertibility of the IFT derivative from the original
  spectral isolation and construct the smooth local energy eigenfield; (3) insert the cubic
  right-inverse coefficients into the actual metric family, preserving j²H = 0 and the prescribed
  derivative stress; (4) connect the energy-field derivative to the desired rates / EF6 local-germ
  conclusion.
- Acceptance: formal jet, actual metric and actual eigenfield in ONE construction; admissibility of
  every prescribed rate parameter and member-dependent radius explicit; compile + `#print axioms`.
- Pitfalls: a finite right inverse does not prove nonlinear neighbourhood existence; do not demand an
  unnecessary smooth spatial eigenbasis (spatial eigenvalues are repeated).

## Recovered statements (file:line)

| Item | Source (file:line) | Recovered content |
|---|---|---|
| Conventions | `gr/ENERGYFRAME_THEOREMS.md:7`; `cas/COMMON_SPEC.md:4,23` | signature (−,+,+,+), `u=U/c`, `g(u,u)=−1`, `h=δ+u⊗u`, future orthonormal frame `E_0=u, E_i`; Euclidean rest norms |
| Einstein-defined source | `gr/ENERGYFRAME_THEOREMS.md:11` | `T=(G+Λg)/κ` defined from a chosen metric |
| EF1 spectral set-up | `gr/ENERGYFRAME_THEOREMS.md:27` | `Tu=−εu`, `S=hT|_{u⊥}`, `L=S+εI` invertible (spectral isolation); `δ=min|ε+p_i|` |
| IFT assertion | `gr/ENERGYFRAME_THEOREMS.md:91` | "An isolated timelike eigenline depends smoothly on a smooth g-self-adjoint endomorphism near a point where L is invertible; this also follows directly from the normalized eigenvector equation and the implicit function theorem, whose spatial linearization is L. Timelikeness persists." |
| EF2 uniqueness wording | `gr/ENERGYFRAME_THEOREMS.md:62` | "...strict DEC and has a unique normalized future timelike energy eigenvector" |
| EF3 statement | `gr/ENERGYFRAME_THEOREMS.md:114-128` | fixed 2-jet of `g^(0)=e^{2φ_0}η`, `φ_0=−b(x^0)^2−(b/2)|x|^2`, `Λ<3b`; for every real 4×3 `k_{μi}` a smooth Lorentzian germ with the same 2-jet, strict DEC near 0, `u(0)=∂_0`, `g(∇_{E_μ}u,E_i)(0)=k_{μi}` |
| EF3 construction | `gr/ENERGYFRAME_THEOREMS.md:130-135` | `q_i=−6b k_{0i}`, `M_ij=−6b k_{ji}`, `S=sym M`, `W=skew M`, `g=g^(0)+H`, eq. (6) cubic `H` |
| EF3 derivative claims | `gr/ENERGYFRAME_THEOREMS.md:138,159` | `j²H(0)=0`; baseline `∂G(0)=0`; `∂_0G_0i=q_i`, `∂_jG_0i=M_ij`; formula (1) with `L=(6b/κ)I` gives (5); "Strict DEC and the isolated branch persist as in EF2" |
| EF3 claim card | `gr/ENERGYFRAME_CLAIMS.json` (EF3 entry; sha256 43d64e8b…a3e6) | hypotheses "unrestricted Einstein-defined source", "b>0,Λ<3b", "neighbourhood may depend on prescribed derivative" (member-dependent radius) |
| EF6 claim card | `gr/ENERGYFRAME_CLAIMS.json` (EF6 entry) | "...The unrestricted class permits all twelve directions"; hypotheses "fixed κ,Λ and future orientation", "nondegenerate selected stress energy eigenline", "declared local germ class" |
| CAS-05 boundary | `cas/contracts/CAS-05.json` (`full_theorem_boundary.additional_analytic_obligations`) | "Smooth isolated eigenframe via IFT; radius member-dependent" |
| CAS-04 EF6 dependency | `cas/contracts/CAS-04.json:251,269` | "EF6 local existence inherited only once CAS05/06 analytic obligations close"; EF6 depends on CAS-05, CAS-06 |
| Accepted C03 Lean | `local_cas/.../CAS-05/v3_execution_20261003/lean/CAS05C03.lean` (sha256 f10a9fdc…0521f) | `J`, `ddGamma`, `dRicci`, `dEinstein`, `dG`, `closedDG`, `full40_first_Einstein_coefficients`, `normalizedEigenvectorJet_eq_k` (finite jet algebra only; STATEMENT_ALIGNMENT.md: "The finite eigenvector equations do not establish a smooth eigenfield or an implicit-function theorem") |
| Reviewed G05-A Lean | `local_cas/.../CAS-05/g05a_neighborhood_strict_dec_v1_20261013/lean/{G05AConformalDEC,G05BCubicDEC}.lean` | actual Einstein tensor from `fderiv`/matrix inverse; `gCub`; `strict_dec_neighborhood_cubic` (B2); `Lorentzian`; `Ein_eq_of_jet` |
| Reviewed G04-A Lean | `local_cas/.../CAS-04/g04a_smooth_eigenline_v1_20261013/lean/G04AEigenline.lean` (sha256 4d36cde1…906f) | flat-η bordered IFT pattern (`bordered`, `E1_smooth_eigenline`), helpers `isInvertible_of_injective`, `quad_hasDerivAt` |

The dimension label "EF6" does not occur in `gr/ENERGYFRAME_THEOREMS.md`; it is recovered from
`gr/ENERGYFRAME_CLAIMS.json`. The only EF6 component in this task's scope is the
unrestricted-class twelve-direction local-germ statement supplied by EF3, plus its consequence that
the metric 2-jet does not determine the energy-frame first jet in this class.

## Formalization choices (recorded, not hidden assumptions)

1. **Curved adaptation of G04-A (choice: g(x)-self-adjointness, not an orthonormal frame).**
   The bordered (gauge-fixed) map is `(x,(v,m)) ↦ (T^a_b(x) v^b − m v^a, g_x(v,v)+1)` with the actual
   metric `g(x)`; normalization `g_x(v,v)=−1` fixes the scale gauge and `v^0>0` the sign.
   Mixed stress `T^a_b = g^{ae}T_eb` uses the actual matrix inverse. The spectral-isolation
   hypothesis is the source's "L invertible" in injective form
   `∀w, g(u,w)=0 → h(Tw)+εw=0 → w=0` with `h(v)=v+g(u,v)u`. Self-adjointness is required
   only at the base point (it is used for the IFT derivative); gap persistence away from the base
   point needs no self-adjointness.
   G04-A is imported unchanged for two generic helpers only; its flat-η theorems are not reused as
   curved statements.
2. **Covariant rates.** `rate g u x E μ i = g_x(∇_{E_μ}u, E_i)` with the Levi-Civita connection of
   the actual metric, `∇_X u^a = X(u^a) + Γ^a_{ce} X^c u^e`, `Γ` = G05-A `Gam`. The frame at 0 is the
   coordinate frame; it is proved `g(0)`-orthonormal with `E_0=u(0)`.
3. **Regularity.** finite `C^n`, `1 ≤ n` (as G04-A). C^∞ on a single neighbourhood is not claimed.
4. **Strict DEC / Lorentzian** are the reviewed G05-A predicates (pairing-form strict DEC with respect to
   the cone of `g(x)`, time orientation `V^0>0`); reused unchanged.
5. **Uniqueness ("isolated branch").** Two levels are separated: (a) IFT local uniqueness of the branch
   near `(0,(e_0,−ε_0))`; (b) global uniqueness of the future unit timelike eigenvector at every point
   of the ball (EF2 line 62 wording), which needs symmetry of the actual Einstein-defined stress and the
   Lorentzian rest-space positivity; (b) is a separate target.
6. **Radius.** All radii are existential per member `(b,k,Λ,κ,n)`; no uniform radius is claimed.

## Missing / not recoverable

Nothing required by the frozen targets is missing. Not recovered and not claimed: a uniform radius,
the EF2 radius obstruction for the cubic family, EF5/EF5c fixed-matter statements, the CAS-06 part of
EF6, and the "metric 3-jet determines the first jet" half of EF6 beyond what the formulas here imply.
