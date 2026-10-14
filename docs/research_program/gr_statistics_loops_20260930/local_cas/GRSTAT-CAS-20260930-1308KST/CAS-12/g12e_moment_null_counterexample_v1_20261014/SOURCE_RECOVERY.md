# G12-E source recovery (TEFF-H1 compact moment-null counterexample)

Paths are relative to `docs/research_program/gr_statistics_loops_20260930/`
unless absolute. All reads were read-only; no git state was changed.

## Card and source identities

| Item | Location | sha256 |
|---|---|---|
| Card | `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip :: HTT_ALL_OBLIGATIONS_20261011/tasks/G12-E.json` (source_snapshot a30d84c7) | (zip member, read via `unzip -p`) |
| Source statement | `supplements/TEFF_POSITIVE_BRIDGE.md` | f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b |
| Contract | `cas/contracts/CAS-12.json` | 5a6827166fe318e37ac9e503a91d6f729155cbef48f450cd9daf0896e47fa6ae |
| Common spec | `cas/COMMON_SPEC.md` | 4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897 |
| Claim ledger | `supplements/TEFF_CLAIMS.json` | 9654e73ecab0aeaca12009eb6f81aa860e27131daca2d77e19d7fdfe8309f541 |

## Recovered definitions (the seven items of `../g12e_interface_readiness_v1_20261011/BLOCKER.json`)

1. **Momentum carrier and measure dν = C E² dE dΩ.**
   `TEFF_POSITIVE_BRIDGE.md:39` (`dν=C E^2 dE dΩ`). Typed, reviewed Lean:
   `G11A.nu C := ((volume.restrict (Ioi 0)).withDensity (E ↦ ofReal (C E²))).prod G11A.dOmega`
   with `G11A.dOmega := volume.toSphere` on `Sphere2 = sphere 0 1 ⊂ EuclideanSpace ℝ (Fin 3)`,
   `CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AIntegralBregman.lean:361-370`.
   **Discharged by reuse (unchanged import).**
2. **Finite retained-score family and actual integral moment functionals.**
   `TEFF_POSITIVE_BRIDGE.md:43-46` ((A1): `∫ φ_a δ dν = 0, a=1..m`, δ=f−g; φ_a = E Y_lm, Y_lm
   given as examples). No canonical finite list exists in the sources; G12-E therefore quantifies
   **universally** over an arbitrary finite family `φ : Fin m → ℝ × Ω → ℝ` that is integrable on
   the compact positive patch (the minimal condition for the moments of a patch-supported
   perturbation to exist). The moment functional is the Bochner integral
   `∫ z, φ j z * δ z ∂μ`. **Fixed here (general family), not a reused interface.**
3. **Smooth compact-support function space for g and q.** Source `:147` ("compactly supported q").
   Typed here: `q : ℝ → ℝ` (energy profile) with `ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) q`,
   `HasCompactSupport q`, `tsupport q ⊆ Icc E1 E2`, `0 < E1`; its momentum-space lift
   `p ↦ q ‖p‖` on `EuclideanSpace ℝ (Fin 3)` is proved C^∞ with compact support.
   The base state g is only required measurable globally and continuous on the patch.
   **Fixed here.**
4. **Construction of nonzero q annihilating all retained moments.** Card `lean_steps` 1–2.
   Constructed here from m+1 Mathlib `ContDiffBump`s with pairwise disjoint supports
   inside `Ioo E1 E2` and a nonzero kernel vector of the m×(m+1) moment matrix
   (`LinearMap.ker_ne_bot_of_finrank_lt`). Smoothness comes from the bumps, not from the
   finite-dimensional kernel (card pitfall 2). **Proved here.**
5. **BE/FD/MB envelope, base-state margin and uniform amplitude slack.**
   Envelope (A5) `TEFF_POSITIVE_BRIDGE.md:96`; contract assumption "Both f,g<=F_b"
   `cas/contracts/CAS-12.json:47`. Reused unchanged: `G12D.occupation`
   (`CAS-12/g12d_reexecution_closeout_v1_20261014/lean/G12DInterface.lean:11-12`),
   `G12D.occupation_envelope` (`G12DUVIntegrabilityEnvelope.lean:240`),
   `G12D.occupation_nonneg` (`:236`), `G12DClosure.occupation_denominator_pos`
   (`G12DCardClosure.lean:357`); statistics domains `G11A.dom/cdom`
   (`G11AIntegralBregman.lean:246-256`). Admissibility is typed here as
   `∀ z, 0 < z.1 → f z ∈ cdom s ∧ f z ≤ F z.1` (closed admissible domain of Paper I Def. 1 plus a
   common envelope). The margin/slack is a hypothesis on (g, F) on the patch, and a concrete BE
   photon instance (`g = occupation (2b) 0`, `F = occupation b 0 = F_b`) discharges it.
   **Envelope reused; margin/amplitude fixed here.**
6. **Static entropy/divergence functional and quantified uniform bound.**
   Source `:43` (`D_H(f‖g) ≤ ε`). Reused unchanged: `G11A.bregDens`, `G11A.Dext` (extended,
   `[0,∞]`), `G11A.Dfin`, `G11A.hS/hS'` for MB/BE/FD (`G11AIntegralBregman.lean:21-33,222-241`)
   and the domain-guarded `G11A.finite_budget_stat` (`G11AGuarded.lean:22-31`). The uniform bound
   is quantified as `∃ B, ∀ n x, Dext μ (hS s) (hS' s) (f_n(x,·)) g ≤ ofReal B` (and the same for
   `Dfin`). **Discharged by reuse + proved here.**
7. **x-family derivative norm and nonzero-growth definition.** Source `:147`
   (`∂_x f_n(0,p) = a n q(p)`) and `:151` (horizontal Fisher budget
   `∫ |D_X f|²/(f(1+f)) dν ≤ J_X`). Typed here: the derivative field is given by `HasDerivAt` in x
   at x=0 (reusing `CAS12C04.hasDerivAt_constant_q`,
   `CAS-12/c04_oscillatory_derivative_bridge_v1_20261011/OscillatoryDerivative.lean:27-32`); growth
   is stated as `Tendsto … atTop atTop` for (i) the L²(ν) norm squared `∫ (∂_x f_n(0))² dν`,
   (ii) the Fisher form `∫ (∂_x f_n(0))² · hess s (f_n(0)) dν` with `G11A.hess s y = 1/(y(1+ξy))`,
   (iii) the pointwise value `|∂_x f_n(0,p₀)|`. **Fixed here.**

## Pitfalls (card) and how they are handled

* q′ term: the family is `f_n(x,z) = g(z.1) + a sin(n x) q(z.1)`; q does **not** depend on x,
  so the q′ term of `CAS12C04.hasDerivAt_oscillatory_perturbation` is absent by construction.
* "finite dimension kernel만으로 smooth compact support를 주장하지 않는다": smoothness and compact
  support are proved from `ContDiffBump.contDiff` / support lemmas; the kernel only chooses
  coefficients.

## Not recovered / not used

* No canonical concrete retained family (list of E Y_lm) is fixed by the sources; G12-E is proved
  for every finite family integrable on the patch, with a concrete number+energy instance.
* Identification of `G11A.nu C` with the pushforward of Lebesgue measure d³p on ℝ³ is not in
  any source Lean file and is not used or claimed.
* `G11BHessianEnvelope` was compiled-available but is not needed by these targets.
