# G15-C source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member
`HTT_ALL_OBLIGATIONS_20261011/tasks/G15-C.json`. The member's sha256 is
`6e017428bda0040b7644cf4206f97614964baee817353dc9862488133e5888ed`; the zip's
sha256 is `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`.
The card's source_snapshot is `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`.

All paths below are relative to `docs/research_program/gr_statistics_loops_20260930/`.

| file | sha256 |
|---|---|
| supplements/DOSSIER_POSITIVE_BRIDGE.md | 00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd (matches CAS-15.json research_provenance_hashes) |
| cas/contracts/CAS-15.json | eccc10a3f5105970a46a73412d8c82a27a1e82a6116013bc0abc6656816f8eee |
| cas/COMMON_SPEC.md | 4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897 (matches CAS-15.json source_input_hashes) |
| supplements/TEFF_POSITIVE_BRIDGE.md | f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b |
| supplements/DOSSIER_CLAIMS.json | a42a50fbb5dfa8bb1b0a34d90571f083bc6f2eabbd388b0ef87ada32b72d0abb |

## Recovered definitions (verbatim source, then the Lean binding)

1. **Brightness normalization and energy weight.** DOSSIER_POSITIVE_BRIDGE.md:89-93:
   "Let f(x,E,e) be intensity occupation summed over polarization states and
   𝓘(x,e)=α∫_0^∞ E^3 f(x,E,e) dE, for a fixed normalization α. This is an
   energy-density angular carrier; specific intensity is c𝓘." DOSSIER_CLAIMS.json:15
   ("energy-density angular carrier; specific intensity=c times carrier").
   Lean: `bolI α f s x = α * ∫ E in Ioi 0, E^3 * f s E x`. The finite-band version
   `bandI α E1 E2 f s x = α * ∫ E in E1..E2, E^3 * f s E x` is the same weight on the
   window [E1,E2].
2. **Endpoint assumption for the bolometric case.** DOSSIER:93: "Assume finite required
   integrals and vanishing endpoint E^4 f." Lean: hypotheses `IR`/`UV` (limits of
   E^4 f at 0⁺ and +∞ are 0) plus integrability of E^3 f and E^4 ∂_E f. An
   envelope form of the hypotheses is also given (|E^3 f| bounded near 0⁺ and |E^5 f|
   bounded at large E). The BE/Planck shape 1/(e^E−1) satisfies it.
3. **Coefficient four and the band boundary flux.** DOSSIER:99: "The coefficient four
   follows from ∫E^4∂_E f=−4∫E^3 f; finite spectral windows retain boundary fluxes."
   Lean: `band_energy_ibp` gives ∫_{E1}^{E2} E^4 g' = (E2^4 g(E2) − E1^4 g(E1)) − 4∫E^3 g.
   `bandFlux α E1 E2 f t x = α(E2^4 f(t,E2,x) − E1^4 f(t,E1,x))` is that band-edge flux,
   carried with factor 𝓡.
4. **COMM-BAND.** CAS-15.json:81,103,122 has "COMM-BAND boundaryflux required" as a
   singular locus, invariant and test vector. DOSSIER:179: "Spectral bands are possible
   channels only when their energy-boundary fluxes are included in their respective
   residuals." DOSSIER_CLAIMS.json:125 ("Band boundary fluxes for spectral channel
   residuals"). TEFF_POSITIVE_BRIDGE.md:176 (the band edge, cited by the prompt) says
   "A bounded bandpass supported on a compact positive-energy interval suffices; wider
   kernels require a separate endpoint/tail domination check." Lean: the band residual
   and band (B5) carry the term `Rrate3 · bandFlux` and its quadrupole moment explicitly.
   The negative control `band_flux_required` shows that dropping the term is false.
5. **Transport derivative 𝒟.** DOSSIER:86: horizontal comparison "at fixed u-measured
   energy", 𝒟 = L^a∇^H_a. "It is not the total photon-trajectory derivative, which also
   contains the angular and energy changes in (B1)." Lean model: a horizontal chart
   (s,E,x) ↦ f s E x. Fixed (E,x) means the horizontally compared u-energy and
   rest-direction components, and 𝒟f = ∂_s f. Existence of such a chart is a modelling
   assumption and is NOT formalized (see not_claimed).
6. **Rates (B1).** DOSSIER:74-82: a=A/c, H_u=θ/3, 𝓡(e)=H_u+a·e+σ:ee, F(e)=P_e(a+σe),
   h∇_L e=−F(e)+We, ∇_L ln E=−𝓡(e). Lean: `G15B.Rrate3 H a σ e`, `G15B.Ffield a σ e`
   (reviewed G15-B, imported unchanged). The bridges to the reviewed G15-A outputs
   (`G15A.Rrate`, `G15A.Fcov`, H2/H3 form) are `energy_rate_of_G15A` and
   `direction_rate_of_G15A`, which use G15-B `bridge_Rrate`, `sig4`, `emb3`, `sp`.
7. **Liouville transport with collisions (B2).** DOSSIER:93-97: "With collision rate C_t
   per physical second, Liouville transport and energy integration give
   𝒟𝓘+[−F+We]·∇_{S²}𝓘+4𝓡𝓘=𝓒, 𝓒=α∫_0^∞E^3C_t[f]dE." The parameter of L=U+ce
   (COMMON_SPEC.md:17, "Source-forward propagation uses L=U+c e") has dt/ds=1 in the
   rest frame (x0=ct, COMMON_SPEC.md:5 and CAS-15.json:57), so C_t per
   physical second matches d/ds. Lean: `liouville H a σ W f t E x =
   ∂_s f − 𝓡(x)E ∂_E f + D_x f(Wx − F(x))`. `liouville_chain` proves it is the derivative
   of f along a characteristic with the (B1) rates. `liouville_of_transport` gives the
   kinetic equation from the collisional law d/ds f(γ(s)) = C_t.
8. **Residual and moments (B2-B5).** DOSSIER:105 "Form r=𝓒−𝒟𝓘+F·∇𝓘−4𝓡𝓘. Then
   r=(We)·∇𝓘." DOSSIER:138 "C_2=∫𝓒ee^T dΩ, T_2=∫(𝒟𝓘)ee^T dΩ"; (B5) at DOSSIER:140-147.
   CAS-15.json:257 ("Photontransport and energyboundary contract") and CAS-15.json:262
   ("r=C-DI+F·gradI-4RkinI=(We)·gradI; R=∫r eeT=[M,W]"). Lean: `bandResidual`,
   `band_residual_eq`, `band_residual_moment`, `band_weak_quadrupole`,
   `bol_weak_quadrupole`. They reuse the reviewed G15-B `weak_quadrupole_commutator`
   and `commutator_moments` (imported unchanged).
9. **Independence contract.** COMMON_SPEC.md:28: "The scalar brightness I and its
   spacetime derivative/collision inputs must be independent supplied quantities."
   CAS-15.json:47 ("Independentspacetime T2 and collisionC2"). Card pitfall: no circular
   inverse from a W-fitted T2. Lean: f and C_t are supplied inputs. T_2 is built from
   ∂_s f of the supplied f, never from W. Every theorem is a forward identity valid for
   the given W. No W is fitted.
10. **Smooth brightness.** CAS-15.json:48 ("Smoothbrightness; sameframe perchannel").
    Lean: the band theorems derive the C¹-ness of `bandI` from C¹ of f. The bolometric
    moment theorem assumes `ContDiff ℝ 1 (bolI α f t)` explicitly, as a stated contract
    assumption.

## Conditional dependency G12-D

The card says G12-D is needed only "when Brightness model is BE and needs these specific
IR/UV bounds". G15-C states abstract IR/UV hypotheses and proves the BE/Planck shape
satisfies the envelope form directly (`planck_envelopes`), so G12-D is not imported.

## Searched and not needed

`gr/*.md` (ENERGYFRAME, OPTICAL, FINITE_DISTANCE) has no brightness/band definitions
(grep "brightness|band|E^3"). CAS-15.json `forbidden_sibling_paths` concern blind CAS axes,
not this Lean task. The orchestrator authorized reading DOSSIER for definition recovery.

## Nothing unrecoverable

Every definition used was recovered. Modelling choices that are not source text (the
horizontal chart, ambient C¹ extension in x, `RotInv` measure) are recorded as
not_claimed.
