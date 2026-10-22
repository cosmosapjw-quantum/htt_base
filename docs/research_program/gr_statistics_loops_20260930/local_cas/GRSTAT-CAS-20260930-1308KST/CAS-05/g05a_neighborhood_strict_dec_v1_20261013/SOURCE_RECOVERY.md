# G05-A source recovery: cubic H family (Part B)

The lead explicitly authorized this search of `gr/` and `supplements/` for this package.
That authorization is separate from the blind-axis `forbidden_sibling_paths` in
`cas/contracts/CAS-05.json`. This package is not a blind CAS axis run.

## Search trail

- `cas/contracts/CAS-05.json` (sha256 `424bc10c…fc197`):
  - `uncontracted_research_targets` gives the cubic `H` only: `H_ij=-δij x0 S_kl xk xl/2`, `H0i=-x0 r^2 q_i/2 - r^2 W_ij xj/5`.
  - `full_theorem_boundary.additional_analytic_obligations` lists "Lorentzian neighborhood and strictDEC continuity" and "radius member-dependent".
  - C03 excludes "Neighborhood existence and DEC persistence".
  - The contract gives neither the base metric for the cubic family nor a DEC definition.
- `gr/ENERGYFRAME_THEOREMS.md` (sha256 `dd66030a…5b9485967b2feb4577fc197`, equal to the contract's `research_provenance_hashes` entry):
  - §0 line 11: the unrestricted Einstein-source class is `T=(G+Λg)/κ` "defined from a chosen metric", and EF2 and EF3 are in this class "even with strict dominant energy condition".
  - §0 line 23: the DEC is "independently defined … using the type-I criterion ε>max_i|p_i|, ε>0".
  - EF2 (lines 51–108): `g_λ=e^{2φ_λ}η`, `T_λ=κ^{-1}(G[g_λ]+Λg_λ)`, the displayed `G_ab` formula, origin values, the neighborhood assertion through the eigenline IFT, and the radius obstruction at `s=3b/λ`.
  - **EF3 (lines 110–161) is the cubic family.** The base is `g^(0)=e^{2φ_0}η` with `φ_0=-b(x0)^2-(b/2)|x|^2` and `Λ<3b`. The metric is `g=g^(0)+H`, with `H` given in eq. (6): `H_00=0`, `H_ij=-½δ_ij x0 S_kl x^k x^l`, `H_0i=H_i0=-½x0 r^2 q_i-⅕ r^2 W_ij x^j`.
  - Line 138 says "(g) remains Lorentzian on a sufficiently small neighborhood". Line 121 says "its Einstein-defined stress obeys strict DEC on some neighborhood". Line 159 says "Strict DEC and the isolated branch persist as in EF2."
- `gr/ENERGYFRAME_CLAIMS.json` (sha256 `43d64e8b…a3e6`), EF3:
  - hypotheses "unrestricted Einstein-defined source", "b>0,Λ<3b", "neighbourhood may depend on prescribed derivative" (a member-dependent radius).
- `gr/FINITE_DISTANCE_THEOREM.md` and `supplements/*`: the "cubic" matches there are unrelated (an optics remainder order and a thermal bandpass estimator). They hold no cubic-H or DEC content for EF3.
- Accepted finite Lean `CAS05C03.lean` (sha256 `f10a9fdc…521f`): it holds the verbatim polynomial `H b k a c X`, the third-jet tensor `J`, and `H_from_third_jet`. These definitions are copied unchanged into `lean/G05BCubicDEC.lean` and re-proved there.

## Recovered statement and formalization choices

- **Metric:** `gCub b k x = e^{2 phi b 0 x} η + H b k x`. Here `phi b 0 = φ_0`; the λ-term vanishes when λ = 0.
- **Stress:** Einstein-defined, `κT = G[g] + Λg`. `G` is computed from actual derivatives of `gCub`, the actual matrix inverse, the Christoffel symbols and the CAS-05 Ricci convention. It is the same general definition used in Part A; no formula is postulated.
- **DEC:**
  - The source criterion is type I: `ε>max|p_i|` in the energy frame.
  - Lead-frozen choice: the pairing form `T(V,W)>0` for all nonzero future-directed `g(x)`-causal `V,W`, where future-directed means `V0>0`. This form does not need an energy eigenframe; the EF2 IFT eigenframe obligation is separate and is not claimed.
  - For diagonal `T=diag(ε,p,p,p)`, `|p|<ε` implies the pairing form. That is used only at the origin.
- **Lorentzian (B1):**
  - Recorded definition: `g(e0,e0)<0`, and `g(w,w)>0` for every nonzero `w` with `g(e0,w)=0`.
  - Symmetry of `gCub` is proved separately. A symmetric `g` with this property has inertia (1,3).

## Missing or unclaimed

- The type-I energy-frame criterion away from the origin (isolated eigenframe through IFT) is not formalized. Only the pairing-form strict DEC is proved.
- No family-uniform radius is claimed. The radius comes from continuity for each fixed `(b,k,Λ,κ)`, or `(b,λ,Λ,κ)` in Part A.
- The weak-DEC boundary `Λ=3b` is used only as a negative control at the origin (strict DEC fails). No persistence is claimed there.
