# G06-B source recovery

Paths are relative to the repository root; `D = docs/research_program/gr_statistics_loops_20260930`,
`C6 = D/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-06`.  All reads were read-only.

## Card
`HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G06-B.json`
(scope: same fixed EOS and P(X) theory, physical equations and strict DEC on each
constructed TOV germ; reuse "PR477 C03 exact P(X) stress/current/EOS/sound-speed
identities" and "G06-A actual solution"; pitfalls: do not resolve the event relation
`Pstar(q^2/2)^s=p0` by changing theory constants; real exponents only at `X>0`).

## Original statement and fixed/member split
* `D/cas/contracts/CAS-06.json` (sha256 `5b1ec8f1…59ced`)
  - line 40 / 114: C03 "With X=-g^(ab)psi_a psi_b/2>0, P=Pstar X^s, s=(1+alpha)/(2alpha), psi=q x0, Pstar(q^2/2)^s=p0 fixed, verify stress, scalar current divergence, epsilon=(2s-1)P and cs^2/c^2=alpha".
  - lines 49, 65, 88: "One Pstar>0 and fixedq".
  - lines 81, 103, 122: singular locus / invariant "TOV-ACTION Pstar,q cannot vary by member".
  - line 257: additional analytic obligation "StrictDEC persistence and normal-coordinate2jet theorem".
* `C6/codex_only_continuation_20261004/adopted_successor_v1/ADMITTED_INPUTS.json` (sha256 `711de321…793eb`, PR #477 commit `1a375536`)
  - lines 31–34: `definitions.C03` action "Same Pstar>0,q>0,0<alpha<1,s=(1+alpha)/(2alpha); X=…>0, P=Pstar X^s, psi=q x0, Pstar(q^2/2)^s=p0 fixed"; stress/current must be derived by variation.
  - line 39: `C04.family_candidate` "Fix c,kappa,alpha,epsilon0,p0,Pstar,q,mu,Lambda …; vary r0 …, m0=mu r0^3; nu0=0 each germ … no F0=0 member".
  - line 57: assumption "X>0,Pstar>0,q>0,s=(1+alpha)/(2alpha),Pstar(q^2/2)^s=p0".
  - lines 62–63: neutral stress definition `T_ab=-(2/sqrt(-det g)) δS/δg^{ab}` at fixed psi and scalar Euler–Lagrange current `J^a=P_X g^{ab}∂_b psi`.
  - line 69: obligation "Strict DEC persistence and normal-coordinate 2-jet theorem".
* `D/cas/COMMON_SPEC.md` lines 21–25: energy frame `T^a_b u^b=-ε u^a`, rest pressures; fixed action `X=-g^(ab)psi_a psi_b/2>0, P=Pstar X^s, Pstar>0, s=(1+alpha)/(2alpha), q>0 and Pstar(q^2/2)^s=p0; psi=q x0`.
* `D/gr/ENERGYFRAME_THEOREMS.md` (theory doc, sha256 `dd66030a…55e5` per contract)
  - line 23: DEC convention = type-I criterion `ε > max_i |p_i|`, `ε > 0`.
  - lines 205–223: EF5 family statement (fix `ε0, α, p0, μ, Λ`; each `r0` with `F0>0`; item 4 "Each member has strict DEC … throughout a sufficiently small open neighborhood").
  - line 264: "strict-DEC criterion is immediate: ε>|p|=αε for ε>0".
  - lines 338–368: EF5c "One fixed scalar Lagrangian realizes the same family": `T_ab=P_X ∂ψ∂ψ+P g_ab`, `∇_a(P_X∇^aψ)=0`, `ψ=q x0` with the fixed `q>0` chosen so that `P*(q²/2)^s=p0`; `X=(q²/2)e^{-2ν}`, `p=P`, `ε=2XP_X-P=(2s-1)P=P/α`, `ε=ε0 e^{-2sν}`; "one fixed P(X) theory, not a parameter-dependent matter action".

Interpretation used: theory constants `κ, Λ, α, Pstar, q` (and for the contract family
`ε0, μ` with the fixed relation `Pstar (q²/2)^s = α ε0`) are quantified outside the
member quantifier; members vary `r0` (contract family) or the G06-A germ data
`(r0, m0, ν0, ε0)` subject to the single-event compatibility `PXMatched`.

## Reused Lean (imported unchanged; compiled into `raw/imports`)
PR #477 = commits `43e3f727` ("Verify scalar calculus and adopt successor inputs") and
`1a375536` ("Verify owner-adopted finite TOV and action components"); accepted
adjudication `C6/codex_only_continuation_20261004/adopted_successor_v1/ADJUDICATION_STDOUT_REPAIRED.json`
(sha256 `a504f52c…5b19d`, not `ADJUDICATION.json`).

| module | path | sha256 |
|---|---|---|
| CAS06ScalarAccepted | `C6/codex_only_continuation_20261004/adopted_successor_v1/lean/CAS06ScalarAccepted.lean` | `83352ea65bb391d2bd17bf4e25e6149dc5f1cff14f75c28de1a7f30b1d12f46e` |
| CAS06Foundation | `…/adopted_successor_v1/lean/CAS06Foundation.lean` | `c096ac3b7cdee628d867d6f5c194715343a4f1d9f4e276d1a5f7275714670c91` |
| C03Action | `…/adopted_successor_v1/lean/C03Action.lean` | `26bdf418ebace05d5f2d45b68841e09b2cda6d7979498bd7ebae84e83bb410e6` |
| CAS06Bundles | `…/adopted_successor_v1/lean/CAS06Bundles.lean` | `c5ed960d096124d6ca3280af4dd5c34cfbc7b64cfc0ac3ebd52400bc71a53bb8` |
| G06ATOV (reviewed G06-A, commit `edee3a84`) | `C6/g06a_tov_local_ode_v1_20261013/lean/G06ATOV.lean` | `9cebc43277078ce356a931d86891dfb77df34f40a4a0184e85fcb0fbacb034b9` |

Definitions used (file:line):
* `CAS06ScalarAccepted.lean:10-14` `exponent`, `pressure`, `first`, `second`, `energy`; `:71` `energy_identity`; `:81-86` `exponent_pos`, `exponent_gap_pos`.
* `C03Action.lean:148` `kinetic` (X = -g^{ab}ψ_aψ_b/2); `:118` `volumeDensity` (√-g); `:174-184` `actionPressure`, `actionFirst`, `actionEnergy`; `:194` `action_barotropic_identity`; `:206` `action_sound_ratio`; `:225` `actionDensity`; `:258` `actionStress` (T_ab = P_X ψ_aψ_b + P g_ab); `:280` `actionDensity_metric_stress_variation`; `:357` `actionCurrent`; `:391` `actionDensity_scalar_hasDerivAt`; `:418` `scalarGradient` (ψ = q dx0); `:428` `chart_scalar_kinetic`; `:442` `chartCurrentDensityOnLine`; `:470-481` `chartScalarCurrentDivergence` and its zero lemma; `:531-584` `actionRadialX`, `actionRadialPressure`, `actionRadialEnergy`, `actionRadialPressure_hasDerivAt`; `:681` `chartActionStressHat` (matched event ν=0); `:762` `C03_action_event_bundle` (event-only, ν r = 0).
* `CAS06Foundation.lean:122` `massLapse`; `:192` `massLapse_derivative`; `:220-231` `chartMetric`, `chartInverse`; `:1444` `chartEinsteinFromMetric`; `:1515` `tovNuFunction`; `:1912` `chartFrameScale` (orthonormal frame e0=e^{-ν}∂0, e1=√F∂r, e2=r^{-1}∂θ, e3=(r sinθ)^{-1}∂φ).
* `CAS06Bundles.lean:71` `C01TOVEinstein` (frame Einstein equations with `T=diag(ε,αε,αε,αε)` and zero off-diagonal coordinate components).
* `G06ATOV.lean:38-52` `AdmissibleParams`, `TOVDomain`, `IsTOVSolutionOn`; `:198` `T3_local_existence`; `:308` `T5_einstein_on_solution`.

## What was new relative to the reuse
C03 proved the stress/current/EOS identities only at the matched event (`ν r = 0`,
fixed `F`).  G06-B evaluates the action stress, current and scalar equation on the
actual G06-A metric `(ν(r), F(r)=massLapse m Λ r)` for every `r` in the existence
interval, proves the P(X) energy density equals the TOV `ε` on the whole interval
(integrating-factor uniqueness), and derives the Einstein–matter equations with the
P(X) stress from G06-A's Einstein equations on the same fields.

## Missing items
None blocking.  Not recovered as a formal definition in the sources: a tensorial DEC
definition — the theory doc fixes the type-I criterion (ENERGYFRAME_THEOREMS.md:23);
G06-B states both the type-I margin and the frame flux form (`StrictDEC`) and proves both.
