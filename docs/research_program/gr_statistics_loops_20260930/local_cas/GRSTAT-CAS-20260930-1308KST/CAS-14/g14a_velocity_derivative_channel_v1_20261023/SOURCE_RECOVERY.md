# G14-A source recovery

Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G14-A.json`
(source_snapshot `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`). Repository HEAD observed at
write time: `9f0beb699afa7251fcad9f5fb559f1675a76cdda` (read-only; no git state changed).
Paths below are relative to `docs/research_program/gr_statistics_loops_20260930/` unless
absolute or repository-rooted.

## 1. Recovered definitions (what the dossier actually specifies)

| Item | Recovered content | Citation |
|---|---|---|
| Jet decomposition | `∇_aU_b = D_ab + W_ab − u_aA_b/c`, `D=(θ/3)h+σ`, `W` antisymmetric, `W u = 0` (P0) | `supplements/DOSSIER_POSITIVE_BRIDGE.md:6-9` |
| Index/sign convention | derivative-first, `U=c u`, `W_ij=ε_ijk ω_k`, `Wx=−ω×x`, source vorticity (not tetrad spin) | `supplements/DOSSIER_POSITIVE_BRIDGE.md:10-14`; `cas/COMMON_SPEC.md:2-11`; `gr/OPTICAL_THEOREMS.md:305-309` (book sign adapter) |
| Observed channel | `J(x)=h∇_xU` at the same event, for known source-spatial unit `x` | `supplements/DOSSIER_POSITIVE_BRIDGE.md:18` |
| Finite-baseline realization / transport rule / tangent direction | `J(x)=lim_{s→0} h_p[P_{q_s→p}U(q_s)−U(p)]/s`, `q_0=p`, `q̇_0=x`, "known spacetime parallel transport" (A1) | `supplements/DOSSIER_POSITIVE_BRIDGE.md:18-22` |
| Calibration requirements | paths, length calibration, source identification, transport specified independently; not available from a static remote sky; finite baselines need a derivative/remainder bound | `supplements/DOSSIER_POSITIVE_BRIDGE.md:23`; `cas/contracts/CAS-14.json:44,246` |
| Residual | `y=J(x)−Dx=−Wx=ω×x` (A2) | `supplements/DOSSIER_POSITIVE_BRIDGE.md:25-28`; `reviews/POSITIVE_EXTENSION_DECISION.md:82` |
| Exclusions | "No propermotion=J assertion", "No staticremote derivative", "No tetradspin confusion" | `cas/contracts/CAS-14.json:68-70`; `DECISIONS.json:643-644` |
| Ray vs observer-time | "Ray direction change is not observer-time image drift. Any astrometric implementation needs its own proven observation equation." | `supplements/DOSSIER_POSITIVE_BRIDGE.md:241`; `cas/COMMON_SPEC.md:18` |
| Tetrad spin | Dossier II uses `W` for rotating-tetrad components, a different object; unknown tetrad spin can contaminate rotational residuals; common transport reference essential | `supplements/DOSSIER_POSITIVE_BRIDGE.md:206,238`; `reviews/POSITIVE_EXTENSION_DECISION.md:28` |
| Positive norms | declared positive component norms only | `cas/COMMON_SPEC.md:19` |
| Covariant derivative / index layout in Lean | `nablaUp Γ u x a c = ∂_a u^c + Γ^c_{ad}u^d`, `velJet = ∂_a u_b − Γ^c_{ab}u_c`, `projUp g u = 1 + u ⊗ (g u)` | P03-A `theory_inference_port_20260930/local_execution/PORT-CAS-03/velocity_jet_decomposition_v1_20261014/lean/VelocityJetDecomposition.lean:38-39,484-491` |
| Implementation convention | `kinematics_from_velocity_jet`: supplied `D_ab=∇_a u_b`, `ω_ab=c h h D_[cd]`; "A value of beta alone supplies none of the derivatives" | `htt/src/common/relativistic_kinematics.py:336-360` |
| Ideal position-drift channel (implementation) | `ideal_position_drift_moment`: `M=<κ(n)nᵀ>=S/5+W/3`, `κ=P(S+W)n`, requires full-sky calibrated NON-ROTATING frame; "W ... not an unlabelled vorticity vector" | `htt/src/common/relativistic_kinematics.py:309-333` |

The formal channel (`Jchan`, `finiteBaselineMap`, `TransportGerm`) is a direct typing of
(A1) with the P03-A index convention; the transport rule is the parallel-transport ODE
`dΠ/ds=−Γ(q̇,·)Π` at `s=0`.  The proper-motion observation equation is NOT in the dossiers
(correction 4 says one is needed); T5 derives one in a declared flat, instantaneous,
low-velocity model, consistent with the implementation's ideal drift form `κ=P(S+W)n`.

## 2. Actual source / transport / length / clock availability (application)

Searched: the five dossier summaries (`supplements/DOSSIER_POSITIVE_BRIDGE.md:183-196`:
"They contain no new measured 𝒟ℐ, local source derivative samples, or numerical
residual-error guarantee"), `supplements/DOSSIER_CLAIMS.json`, `DECISIONS.json:629-646`
(DP01 conditions: "Independent local source derivative measurements ... Known source
identification, length and spacetime transport"), `cas/contracts/CAS-14.json:246`
("Calibrated derivative observation and finitebaseline remainder external"), CAS-14
`input_aligned_v1_20261008/RETURN.json` (`remaining_obligations`: "calibrated derivative
observation and finite-baseline remainder"), `htt/` (grep for proper_motion /
velocity_gradient / parallel_transport / tetrad_spin), and git history (`git log` grep for
487 / CAS-14 / astrometry / proper).

Only observational astrometry located: `docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/quaia_join/REPORT.md:30-38`
(commit `d256ed46`, PR-HTT-A22-ASTROMETRY): Gaia observer-time proper motions of Quaia
quasars with marginal 2×2 PM covariance and photometric redshifts.  This is remote,
observer-time image drift of distant sources without source-event identification of a
neighbourhood, transport, baseline length or a calibrated non-rotating frame — exactly the
excluded "proper motion = J" / "static remote" route.  It is NOT used as a J witness.

Result: no actual source identification, transport rule along a physical path, tangent
directions, baseline length, clock/length calibration, non-rotating-frame calibration,
optical symmetric rate at the same event, or finite-baseline derivative modulus is
supplied.  `g14aSupplyLedger` records all nine as `notSupplied`.
Unlock condition: an independently provenanced measurement of `U` at ≥2 events
`q_s` near `p` along two non-parallel source-spatial directions with (i) the source
identification, (ii) the transport (connection along the path) or a parallel/rest tetrad
with certified spin, (iii) baseline length and clock calibration (κ/ℓ), (iv) a derivative
modulus `M` for the remainder, and (v) the optical `D` at the same event.

## 3. Reused accepted / reviewed sources (imported unchanged; hashes)

| Module | Source | source sha256 | olean sha256 (this build) | review state |
|---|---|---|---|---|
| `Main` (CAS-14 C01-C03, PR #487) | `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-14/input_aligned_v1_20261008/lean/Main.lean` | `806745159bdec6ac16cdc8f7c651919ba69263b2f07db9d28414da4832147e15` (= RETURN.json lean source_sha256) | `148b84df91c1fabe34fe3f72b05649fdd08bdec548f4bbb30e73298a1a02255f` | CAS_4AXIS_PASS, PASS_FINITE_COMPONENT_REVIEW |
| `VelocityJetDecomposition` (P03-A) | `theory_inference_port_20260930/.../PORT-CAS-03/velocity_jet_decomposition_v1_20261014/lean/VelocityJetDecomposition.lean` | `f67b882235288225d81813c9a0ec87d78e0846e23349f437eb1793b0c5ce243b` | `31a5386dfa79e40d8c8b48be6cb0b5b7363d456797dbe18a65fd487bff6054ac` | FORMALLY_CHECKED_SCOPED |
| `VelocityJetRest` | `.../PORT-CAS-03/velocity_jet_rest_bridge_v1_20261011/VelocityJetRest.lean` | `0d696565adc1bac4490426e0d557c1429d3a63a873cf443ebe2b4d0ffac4b684` | `8066e19b927e31d25a7dcf67bae34626943f3b36c2e1af4aae2a367daac82356` | P03-A dependency |
| `PortCas01` | `.../PORT-CAS-01/lorentz_mass_shell_v1_20261008/lean/PortCas01.lean` | `e289039fbe8a531ccb017923d751b14c12f5c5f5f66ffdaa5dbb5d2ac91a0c7b` | `a83adac8bb588da9cb84c722821eb01243c88517378ca7c6b920960ce7c20bc8` | P03-A dependency |

P06-A (`PORT-CAS-06/endpoint_optical_invariants_v1_20261014/lean/P06AOptics.lean`) was
inspected but not imported: its null-ray/observer-change content (aberration, Doppler of one
ray under a boost at the same event) is not needed by the frozen targets; aberration and
observer-acceleration drift are kept as external remainder terms of the T5 model.
