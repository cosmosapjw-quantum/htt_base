# G17-D source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member
`HTT_ALL_OBLIGATIONS_20261011/tasks/G17-D.json` (source_snapshot
`a30d84c7918b54238a48fa62e2ef482f7e6d36fa`). Paths below are relative to
`docs/research_program/gr_statistics_loops_20260930/` unless absolute.

## Original statement (scope_original)

"원상위 gamma/beta zero iff u=N, actual independently known orbit와 AB-T6 scope
condition." Recovered from:

| Item | Citation | sha256 |
|---|---|---|
| Uncontracted target `gamma=-u·N, beta^2=1-gamma^-2; zero iff u=N` | `cas/contracts/CAS-17.json:268` | `123c73d5…877e` (file) |
| Analytic obligation `ReverseLorentzCauchy/futurebranch` | `cas/contracts/CAS-17.json:262` | same |
| `AB-T6 calibration is scope condition not identity` | `cas/contracts/CAS-17.json:264`; `local_cas/…/CAS-17/EXECUTION_CONTRACT.json:329` | contract `a2817237…9328` |
| Assumption `Independently known actual spacelike orbit X1,X2,X3 with positive Gram; future orientation` | `cas/contracts/CAS-17.json:55,70,92` | same |
| Exclusion `No orbit/Bianchi inference` | `cas/contracts/CAS-17.json:79` | same |
| Singular locus / test vector `TILT-BOOST u/o differs from u/N` | `cas/contracts/CAS-17.json:85,106,125` | same |
| C04 text: passive synchronization map vs physical observer replacement; calibration availability is a scope condition | `cas/contracts/CAS-17.json:50,121` | same |
| `Same physical fields under coordinate synchronization preserve scalars; physical observer replacement changes measurements` | `cas/contracts/CAS-17.json:272` | same |
| Construction `v^a=ε^{abcd}X1_b X2_c X3_d`, `N=±v/√(-v²)` future sign, `γ_uN=-u·N`, `β²=1-γ⁻²`; "not an inference of the generators from optical data or a Bianchi classification"; single event gives relative tilt there | `supplements/DOSSIER_POSITIVE_BRIDGE.md:222-234` | `00c1fcb0…ebd` |
| AB-T4 synchronization diffeo preserves scalar/relative rapidity; AB-T5 physical observer o→o' changes measurements; AB-T6 metric representative/distance scale not supplied ⇒ no unique absolute dimensionful output | `ADDED_BOOK_INTEGRATION.md:111-113` | `977125a6…dbf` |
| AB-T6 test text "reject unique absolute dimensional result when scale unspecified" | `ADDITIONAL_REFERENCE_MAP.json:285-287` | `d02c4980…bf0` |
| AB-T6 decision `PASS_SCOPE`: absolute dimensional outputs require calibrated metric/clock/distance inputs | `DECISIONS.json:798-800`; `reviews/POSITIVE_EXTENSION_DECISION.md:113` | `a05b3053…c6c`; `d2d2f02a…a299` |
| Signature (-,+,+,+), future u with g(u,u)=-1 | `cas/COMMON_SPEC.md:4` | `4714827e…7fe1897` |
| No calibrated absolute output exists in CAS-17 interfaces | `local_cas/…/CAS-17/c02_c03_source_definition_freeze_v1_20261011/SOURCE_DEFINITION_FREEZE.md:42` | — |

## Reused accepted Lean (imported unchanged)

| Unit | Path | Source sha256 | Status |
|---|---|---|---|
| CAS17-C01 | `local_cas/…/CAS-17/c01_gram_tilt_bridge_v1_20261010/lean/C01.lean` | `934e6a960ceec5720d3e3784b705184dac66997d967ecf2a5f04c175ee5309de` (matches its AUTHOR_RETURN.json) | independent review no-blocking (`REVIEW.md`) |
| CAS17-C04 | `local_cas/…/CAS-17/c04_passive_tensor_bridge_v1_20261010/PassiveTensorBridge.lean` | `49f371401016466361d7f02012ba840de0f5d600327722ac4e843602c95da8fb` (matches README/receipt) | review `PASS_WITH_SCOPE_LIMITS` |

PORT-CAS-06 (`theory_inference_port_20260930/local_execution/PORT-CAS-06/*/raw/imports/PassiveTensorBridge.olean`,
olean sha256 `7bf257e3…77e0`) compiled the same C04 source (see its
`compile_02_imp_cas17.json`, source sha `49f37140…8fb`); our import compile
produced the identical olean sha256, so it is the same module, not a separate one.

C01 definitions used verbatim (C01.lean): `Vec`, `lorentz` (line 22), `spatial`,
`scale`, `wedge`, `gram`, `futureSign`, `normal`, `FutureUnit`, `gamma = -lorentz u N`,
`relativeSpatial = u - gamma N`, `betaSq = lorentz(rel,rel)/gamma²`, `beta = √betaSq`.
C01's final theorem `c01_gram_tilt_bridge` does NOT contain the equality case
`betaSq = 0 ↔ u = N`; it is proved here (target T1).

C04 definitions used verbatim: `Tensor`, `Slot`, `tensorChange`, `argumentChange`,
`mixed_tensor_contraction_invariant`, `minkowski`.

## Not recoverable / not supplied

- AB-T6 calibration supply: no calibrated metric representative, clock, or distance
  scale input is supplied to CAS-17 anywhere searched (`cas/contracts/CAS-17.json`,
  `local_cas/…/CAS-17/**`, `ADDED_BOOK_INTEGRATION.md`, `DECISIONS.json`,
  `SOURCE_DEFINITION_FREEZE.md:42`). Status recorded as `NOT_SUPPLIED`
  (operational witness, not a theorem). Unlock condition: an independently supplied
  calibrated metric/clock/distance input with provenance.
- Actual orbit identification: no independent orbit generator field is supplied; it
  is a typed input (`IndependentOrbitInput`) and never inferred.
