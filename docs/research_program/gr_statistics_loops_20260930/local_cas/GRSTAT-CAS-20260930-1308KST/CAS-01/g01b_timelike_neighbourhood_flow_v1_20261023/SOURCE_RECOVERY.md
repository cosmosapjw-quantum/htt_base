# G01-B source recovery — timelike neighbourhood, smooth normalization, local flow

Package card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip :: tasks/G01-B.json`
(source snapshot `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`, status `PLANNED_NOT_EXECUTED`).
All paths below are relative to the repository root unless absolute.

## 1. Original statement (bound source)

`docs/research_program/gr_statistics_loops_20260930/gr/OPTICAL_THEOREMS.md`
(SHA-256 `5ae2b6a65a5704247bed3d7dc5f01924318063ee5443cfa95c30c452b0ea8c21`):

| Item | Location | Recovered content |
|---|---|---|
| Setting | lines 9 | smooth time-oriented Lorentzian spacetime, signature (-+++), `U=c u`, `u^2=-1`, future pointing; source field smooth near `p`; length-valued coordinates `x^0=ct`; observer tetrad `e_0=o` |
| Derivative-first tensors | lines 28-33, Eq. (3) | `Q_ab = ∇_a U_b`, `B = Q_(ab)` |
| Optical identity | lines 37-41, Eq. (4) | `Z(n)=u(p)·K(p,n)`, `H(n)=B_ab K^a K^b`, `K=-o+n` (line 14, Eq. (1)) |
| Admissible pair | lines 66-81, Eqs. (6)-(9) | `u=(ζ0,ζ_i)`, `ζ0²-|ζ|²=1`, `ζ0≥1`; `S00=h0`, `S0i=-h1_i/2`, `Sij=h2ij` STF; `B=S+S(u,u)g` |
| Fibre | lines 108-113, Eq. (11) | `Q=B+b⊗u-u⊗b+W`, `W` skew, `W u=0` |
| **Theorem 3** | lines 147-154, Eq. (17) | normal coordinates at `p` with `g(p)=η`, `∂g(p)=0`, matched to observer tetrad; `v^b(x)=u^b+c⁻¹η^{bd}Q_ad x^a`; `u^b(x)=v^b/√(-g(x)(v,v))`; seed future timelike "on a sufficiently small neighbourhood by continuity"; denominator one at `p` with vanishing first derivative (uses `Q u=0`, `∂g(p)=0`); integral curves give a local congruence; Eq. (4) gives the data |
| Scope limits | line 156 | no fixed-size neighbourhood, no finite-distance bound, no global extension, no homogeneity, no Einstein/material realization |

Prior reviewed signature recovery:
`docs/.../CAS-01/g01b_local_realization_signature_v1_20261011/SOURCE_SIGNATURE.md`
(SHA-256 `ec2fc840f7e596d0a6d360c79ec3e60475fced3709bed19903d9ac3215a7210a`, REVIEW `PASS_SCOPED`,
`3b1c9a0f153029c71710498c80bd28f8da5dee20a81a5d164bf0d341c7210627`). Its two review repairs are kept:
(i) `∇u(0)=Q/c` for the unit field, `∇U(0)=Q` for the physical field `U=c u`; (ii) the
geometric mapping to the ideal optical pair `(Z,H)` defined by limits (Eq. (2)) is a separate
obligation owned by the optical identity (4), i.e. by G01-A R1/R2, and is not closed here.

Contract: `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-01.json`
(SHA-256 `9f1bbb018e211b4d50c50532b57cf708acffdd6a01f06a24f5cb8cbb21709b57`), line 110 (C04 is "at the
jet, not an existence theorem") and line 255 (open obligation "Smooth timelike neighborhood/local flow
and source extension not proved by origin algebra"). `cas/COMMON_SPEC.md` line 4 (signature, `U=c u`, `c>0`)
(SHA-256 `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`).

Meaning of "source extension" (recovered from the contract wording at CAS-01.json:255 and
OPTICAL_THEOREMS.md:147-154): extension of the prescribed source 1-jet `(u(p), ∇U(p))` to an actual
smooth unit source field on a neighbourhood of `p`. No other meaning is found in the
contract, CAS_TASKS.json:88, PROOF_DAG.json:143, or the axis PROOF.md files.

## 2. Reused accepted Lean (imported unchanged)

| Module | Source | SHA-256 | Used items |
|---|---|---|---|
| `CAS01C04Accepted` (byte copy of accepted C01-C04 source) | `docs/.../CAS-01/completion/rerun_20261003/lean/Main.lean` (= `completion/lean/Main.lean`), accepted `CAS_4AXIS_PASS` for C01-C04 in `completion/rerun_20261003/RETURN.json` | `a24b349982cb5401d8086b3432caf76b1f277793c056083276eb30bcde72e9b7` | `V`, `Form`, `eps`, `g`, `eval`, `cov`, `B`, `Q`, `sym`, `skew`, `spatial`, `symPart`, `rest`, `K`, `sourceS`, `fullSeed` (Main.lean:492-493, the affine candidate of Eq. (17)), `fullNormalized` (494-495), `coordinateLine` (496), `fullSeed_coordinateLine` (498), `fullNormalized_coordinate_derivative` (513), `B_symmetric` (96), `Q_right_null` (144), `Q_symmetric_part` (163), `general_sourceward_harmonics` (390) |

Not imported (checked, not needed): G01-A `G01AJacobiVertex.lean`
(`6c1f7a66...cde57`, frame-level Jacobi/optical-identity owner; its R1/R2 remain the owner of the optical
identity (4)); P03-A `VelocityJetDecomposition.lean` (PORT-CAS-03; different matrix conventions,
kinematic decomposition already covered for this purpose by C02 `Q_symmetric_part`).

## 3. Chart-level formalization choices (stated scope)

* Chart `V = Fin 4 → ℝ` (sup norm), metric components `G : V → Form` with `ContDiff ℝ n G`,
  symmetric, `G 0 = η = diag(-1,1,1,1)`, `HasFDerivAt G 0 0` (the normal-coordinate facts used by the
  source proof, OPTICAL_THEOREMS.md:149). Existence of such normal coordinates on a Lorentzian manifold
  is NOT proved (manifold residual, as in G01-A).
* Time orientation: an arbitrary continuous reference field `T` with `T 0 = rest = e_0 = o`; "future"
  at `x` means `g_x(w, T x) < 0`.
* Covariant derivative: chart formula `∇_a U_b = ∂_a(g_bc U^c) − Γ_{e,ab} U^e` with
  `Γ_{e,ab} = ½(∂_a g_eb + ∂_b g_ea − ∂_e g_ab)`; partials are `fderiv` along `Pi.single a 1`.
  Agreement with the manifold Levi-Civita connection is the standard coordinate formula and is not
  re-derived from a manifold API (residual).
* Optical observables: computed from the constructed field by formula (4) at the chart origin.
  The identity (2)=(4) (redshift-limit definition equals formula (4)) is not proved here.

## 4. Missing items

None of the chart-level targets require an unrecoverable definition. Manifold-level items
(normal-coordinate existence, Levi-Civita API, time-orientation bundle, null-geodesic optical identity)
are absent from the pinned Mathlib as a bound project interface (searched
`.lake/packages/mathlib/Mathlib/Geometry/Manifold`, no pseudo-Riemannian/Lorentzian metric or normal
coordinate API); unlock condition: a reviewed Lorentzian-manifold layer or G01-A R1/R2 closure.
