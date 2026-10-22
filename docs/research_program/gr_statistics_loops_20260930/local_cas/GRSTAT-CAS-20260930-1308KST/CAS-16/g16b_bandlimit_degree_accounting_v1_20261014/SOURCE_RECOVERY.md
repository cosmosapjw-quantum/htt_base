# G16-B source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip!HTT_ALL_OBLIGATIONS_20261011/tasks/G16-B.json`
(zip sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`,
member sha256 `524c7ec409b997c9b952d62d8535b466294316b8cc25b0c99f687d9fae946b00`,
card source_snapshot `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`).

Paths below are relative to `docs/research_program/gr_statistics_loops_20260930/` unless absolute.

| Source | sha256 |
|---|---|
| `supplements/DOSSIER_POSITIVE_BRIDGE.md` | `00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd` |
| `cas/contracts/CAS-16.json` | `c8c5c20c2d470a53dcf79dc8c3504e7a59874fed88a48917b8547755b37486cb` |
| `cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` |

## 1. Angular integrands (recovered verbatim, DOSSIER_POSITIVE_BRIDGE.md)

* :74-79 (B1 definitions): propagation direction `e` in the source rest space,
  `a = A/c`, `H_u = θ/3`, `R(e) = H_u + a·e + σ:ee`, `F(e) = P_e(a + σ e)`, `P_e = I - e e^T`.
* :105 residual `r = C - 𝒟I + F·∇_{S²} I - 4 R I`; :106 `r = (W e)·∇_{S²} I`.
* :107-110 (B3): `M = ∫_{S²} I e e^T dΩ`, `R = ∫_{S²} r e e^T dΩ`.
* :136-149 (B3 weak form, eq. B5): `C_2 = ∫ C e e^T dΩ`, `T_2 = ∫ (𝒟I) e e^T dΩ`, and
  `R = C_2 - T_2 - ∫ I { [4H_u - σ:ee] e e^T + a e^T + e a^T + (σe) e^T + e (σe)^T } dΩ`.
  :148 explains that the angular-derivative form was removed by integration by parts
  (`div_{S²} F = -2 a·e - 3 σ:ee`). This is the "weak residual"; its angular kernel
  has Cartesian degree four in `e` (the `σ:ee · e e^T` term), which is the "+4".
* Collision integrand: `C(e) e_i e_j` (the "+2" with bandlimit `L_C`).
* Transport integrand: `(𝒟I)(e) e_i e_j` (the "+2" with bandlimit `L_T`).
* Brightness moment integrand of (B3): `I(e) e_i e_j` (degree `L+2 ≤ L+4`).
* :208-216 (C3 paragraph): "Suppose `I`, `C`, and `𝒟I` have scalar bandlimits `L, L_C, L_T`.
  Integrands in (B3),(B5) have maximum degree `D_* = max(L+4, L_C+2, L_T+2)`";
  sufficient rule `N_μ ≥ ⌈(D_*+1)/2⌉, N_φ ≥ D_*+1`. Proof sketch :216: azimuthal sums
  eliminate nonzero Fourier orders through `D_*`; "surviving associated-Legendre products have
  integer powers of `1-μ²`"; "the actual weak-kernel degree four, not merely the state bandlimit".
  :216 also: angular tails, masks, nonpolynomial coefficients and energy quadrature require
  separate bounds (excluded here).
* The undifferentiated residual `r = (We)·∇I` of :106/(B3) contains an angular derivative; the
  card's "weak residual" is the integration-by-parts form (B5). Only (B5) is formalized.

## 2. Contract scope (cas/contracts/CAS-16.json)

* :37 / :103 CAS-16-C02: "Verify the angular polynomial degree accounting
  Dstar=max(L+4,LC+2,LT+2), the Fourier nonaliasing condition Nphi>=Dstar+1, and 2Nmu-1>=Dstar."
* :38 / :104 CAS-16-C03: (L,LC,LT)=(4,6,4), Dstar=8, Nmu=5 GL nodes, Nphi=9 azimuths.
* :45/:60/:81 assumption "Actual scalar bandlimits L,LC,LT or tail errors".
* :68 exclusion "No spin quadrature generalization" (also card pitfall). Only scalar
  integrands are treated; polarization/spin-weighted quadrature is not in scope.
* :250-251 uncontracted research targets: `Dstar=max(...)`, `Nmu>=ceil((Dstar+1)/2), Nphi>=Dstar+1 sufficient`.
* `supplements/DOSSIER_CLAIMS.json:135-147` claim DP06 restates the same.

## 3. Prior units

* `../c02_general_degree_input_blocker_v1_20261011/RETURN.json`: status
  `BLOCKED_MISSING_ANGULAR_INTEGRAND_DEFINITION`; missing inputs were (i) definition of each angular
  integrand factor contributing +4, +2, +2, (ii) bandlimit convention and product-degree lemma,
  (iii) domain/measure interface. Items (i) and (ii) are recovered above (§1) and defined in §4;
  item (iii) is supplied by the C03 chart/measure in §5.
* `../c03_cartesian_bridge_v1_20261009/lean/{SphereQuadrature,AngularModes,AngularBridge,RadialBridge,FullBridge}.lean`
  (accepted, reviewed; RETURN.json status FORMALLY_CHECKED; source sha256 recorded in
  `../c03_execution_evidence_v1_20261010/RETURN.json`). Final theorem
  `CAS16C03.fullMonomialTheorem : CAS16C03.fullMonomialClaim`
  (`∀ a b c : ℕ, a+b+c ≤ 8 → productRule a b c = sphereMean a b c`). Imported unchanged; it is
  only compiled as a dependency (its source and its theorem are not re-targeted, no raw logs
  of the original runs are re-executed or edited).
* `../g16a_coherency_l2_collision_v1_20261013/lean/G16ACoherency.lean`: concerns (C1)/(C2) collision
  norm; not needed here and not imported.

## 4. Scalar bandlimit definition (recovered; no repository definition exists)

* No Lean, contract, or COMMON_SPEC definition of "scalar bandlimit" exists
  (searched: `cas/COMMON_SPEC.md`, `cas/contracts/CAS-16.json`, `supplements/`, `gr/`,
  CAS-16 local units, `htt/` implementation). The implementation
  (`htt/src/common/mes_directional_state.py:170-189`, `htt/obsstat/mes_directional_moments.py:197`)
  uses `field_bandlimit` as a multipole order `ℓ` (0 = monopole, 1 = dipole, 2 = quadrupole),
  i.e. the standard spherical-harmonic meaning.
* Adopted definition (standard, and the one named by DOSSIER :216 "associated-Legendre"):
  scalar bandlimit `L` = real linear span of the real spherical harmonics with `ℓ ≤ L`,
  written in the chart `μ = cos θ ∈ [-1,1]`, `φ ∈ [0,2π]`:
  `Y^c_{ℓm}(μ,φ) = (1-μ²)^{m/2} (d/dμ)^m P_ℓ(μ) cos(mφ)`,
  `Y^s_{ℓm}(μ,φ) = (1-μ²)^{m/2} (d/dμ)^m P_ℓ(μ) sin(mφ)`, `0 ≤ m ≤ ℓ ≤ L`,
  with `P_ℓ` by Rodrigues' formula `P_ℓ = (2^ℓ ℓ!)^{-1} (d/dx)^ℓ (x²-1)^ℓ`.
  Normalization constants and the Condon–Shortley sign are nonzero scalars and do not change the span.
  For real-valued fields, the real span of these equals the real part of the complex span of
  `Y_{ℓm}`, `ℓ ≤ L`. `(1-μ²)^{m/2}` is `Real.sqrt (1-μ²) ^ m` (nonnegative branch, as in C03).

## 5. Domain and measure (from C03 `SphereQuadrature.lean`)

* Chart `e(μ,φ) = (√(1-μ²) cos φ, √(1-μ²) sin φ, μ)` (`sphereX`, `sphereY`, `sphereZ`).
* Normalized sphere mean `(4π)^{-1} ∫_{-1}^{1} ∫_0^{2π} f(μ,φ) dφ dμ` (= `dΩ/4π`, `dΩ = dμ dφ`).
* Product rule `(1/2) Σ_r w_r (1/9) Σ_j f(μ_r, 2πj/9)` with the explicit GL5 nodes/weights.
* G16-B lifts both from monomials to arbitrary chart functions `f : ℝ → ℝ → ℝ`
  (`quadRule`, `sphereMeanFn`); on `CAS16C03.monomial a b c` they reduce to `productRule a b c` and
  `sphereMean a b c` by `rfl`.

## 6. Missing items

None blocking for the frozen targets. Not recovered / not attempted (recorded in NOT_CLAIMED):
general-order Gauss–Legendre and Fourier exactness (`N_μ ≥ ⌈(D_*+1)/2⌉, N_φ ≥ D_*+1` sufficiency
for all `D_*`); the converse inclusion (Cartesian span ⊆ harmonic span); sharpness of the
increments (+4,+2,+2 attained as lower bounds on the sphere); spin-weighted/polarized quadrature.
