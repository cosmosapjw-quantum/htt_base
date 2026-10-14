# P06-A source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member
`HTT_ALL_OBLIGATIONS_20261011/tasks/P06-A.json` (member sha256
`debd1cd7672d84df5b888cb9e0e86fddfb1f78bfe50059083af6435db25b0b15`, zip sha256
`2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`).
Card scope (translated): on the same physical ray, prove the observer-change /
aberration transformations of redshift, solid angle, d_A, d_L and the scalar
inverse temperature.  Pitfalls: never compare different rays; never extend the
scalar temperature result to polarization or spin-2 transfer.

All paths below are relative to the repository root
`/home/cosmosapjw/Dropbox/bianchi/htt_base`.  Read-only; no source edited.

## Card source_paths

| File | sha256 | Lines | Recovered item |
|---|---|---|---|
| `docs/research_program/theory_inference_port_20260930/CAS_CONTRACT.json` | `904d95fe…389fad` | 75-78 | CAS-06 identity `(1+z_new)*dA_new=(1+z)*dA; dL_new=dL/D; scalar inverse T affine`; assumptions `same physical ray; aberration mapping; no polarization assertion` |
| `docs/research_program/theory_inference_port_20260930/PORT_MAP.json` | `d0050aa3…ce5e0` | 170-192 | TBO-06 -> `endpoint_boost` (limit: same physical ray, aberration-remapped directions, no spin-2); TBO-07 -> `inverse_temperature_boost` (absolute scalar blackbody only) |

## Definitions and conventions

| Item | Source (file:line) | Lean object |
|---|---|---|
| Signature (-,+,+,+), orthonormal frame, `c=1`, `u=U/c` | `htt/src/common/relativistic_kinematics.py:3`; `gr_statistics_loops_20260930/cas/COMMON_SPEC.md:3-4` (sha256 `4714827e…7fe1897`) | `mink := CAS17C04.minkowski` (GR-17 C04, reused) |
| Spatial vectors point toward sources (sourceward `n`) | `relativistic_kinematics.py:4`, `:219` ("old-frame source direction"); `observations_findings.md:17` | `photon E n = E(1,-n)` |
| Photon momentum `p=(ε/c)(u-n)`, `n=-e` | `inherited/tilt_boost_loop_20260930/inherited/T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md:15-17` (sha256 `4fab2be9…94c385286`) | `photon` |
| Boosted observer `ũ=γ(u+β)` | T5 pack `:22-26`; `relativistic_kinematics.py:54-61` (`four_velocity`) | `PortCas01.fourVelocity` |
| Lorentz boost and inverse `boost(-β)` | `relativistic_kinematics.py:64-73`; PORT-CAS-01 `lean/PortCas01.lean` | `Bst`, `Binv` |
| Measured energy `E_V=-p·V`, `D=γ(1+β·n)` | `observations_findings.md:15,17` (sha256 `a4d21f94…a1d8d1`); T5 pack `:40-43`; implementation `relativistic_kinematics.py:229` (`d = u[0]+u[1:]@n`) | `energy`, `doppler`, `energy_new`, `doppler_eq_energy_ratio` |
| Reciprocal form `D=1/(γ(1-β·ñ))` | T5 pack `:45-48` | `doppler_reciprocal` |
| `1+z'=(1+z)/D`, `d_A'=D d_A`, `d_L'=d_L/D` (endpoint map) | `relativistic_kinematics.py:230`; `observations_findings.md:25-27`; CLAIMS TBO-06 statement (`CLAIMS.json:141-165`, sha256 `9750221f…c7b6`) | imported `zNew`, `dANew`, `dLNew` |
| Aberration solid angle `dΩ'=D^{-2}dΩ` | T5 pack `:63-67`; `observations_findings.md:27`; INDEPENDENT_DECISION TBO-06 reasons | `ab`, `D1`, `solid_angle_jacobian`, `solid_angle_change_of_variables` |
| Area distance from fixed source screen and observed solid angle | `observations_findings.md:27` ("holding the source event and narrow bundle fixed … hence d_A'=D_o d_A") | `areaDist dS dΩ = sqrt(dS/dΩ)`, `areaDist_aberration` |
| Reciprocity explicit: "For transparent metric propagation and Etherington reciprocity" / "dL=(1+z)^2 dA requires reciprocity/transparency" | `observations_findings.md:27`; `COMMON_SPEC.md:18`; CLAIMS TBO-06 assumptions | hypotheses `hrecOld`, `hrecNew` |
| `ε/T` invariant along corresponding rays (Planck occupation) | T5 pack `:50-61` | `planckOcc`, `temperature_transform` |
| Inverse-T criterion `1/T_o(n)=a+b·n`, `a>|b|`, `β=-b/a`, `T0=(a^2-|b|^2)^{-1/2}` | `prior_stats_findings.md:89-108` (sha256 `7be6983b…46d7`); CLAIMS TBO-07; `relativistic_kinematics.py:235-245` (`u = four_velocity(-b/a)`, rest T `u[0]/a`) | `inverse_temperature_affine`, `inverse_temperature_inversion`, `isotropic_blackbody_criterion` |
| Exact-algebra evidence (Wolfram, not a proof) | `inherited/tilt_boost_loop_20260930/evidence/endpoint_temperature.wl:1-12` (sha256 `5f0e5c2c…278e`) | cross-check of conventions only |

Implementation identity: `htt/src/common/relativistic_kinematics.py` sha256
`9ae767f9cec93358e4ca9b1a63abacf909fb1b770699c7e31be9b82ee2959d5e`, last
touched by commit `bc45fb92` (read-only `git log`).

Convention check against the implementation (exact, by the Lean theorems):
`endpoint_boost` returns `((1+z)/d-1, d*da, dl/d, d)` with `d = γ(1+β·n)`, `n`
the old-frame sourceward direction.  `energy_new`/`doppler_eq_energy_ratio`
prove `d = E_new/E_old` for one fixed null `k`; `endpoint_optical_same_ray`
proves the redshift and area maps equal `zNew` and `dANew` of the imported
reviewed prior unit.  `inverse_temperature_boost(a,b)` returns
`(γ(-b/a)/a, -b/a)`; `inverse_temperature_inversion` proves
`γ(-b/a)/a = 1/sqrt(a^2-|b|^2)` and the affine reconstruction.

## Reused reviewed Lean (imported unchanged)

| Module | Path | sha256 |
|---|---|---|
| `PortCas01` | `docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-01/lorentz_mass_shell_v1_20261008/lean/PortCas01.lean` | recorded in `raw/compile_*_imp_port01.json` |
| `PassiveTensorBridge` (`CAS17C04`, GR-17 passive contraction) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-17/c04_passive_tensor_bridge_v1_20261010/PassiveTensorBridge.lean` | recorded in `raw/compile_*_imp_cas17.json` |
| `EndpointScalarInvariant` (prior P06 unit, PASS_SCOPED) | `docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-06/endpoint_scalar_invariant_v1_20261011/EndpointScalarInvariant.lean` (sha256 `6e2ba677…aed83`, matches its RETURN.json) | recorded in `raw/compile_*_imp_prior.json` |

The G15-A photon module (CAS-15) was inspected; it concerns the velocity-jet
ray derivative and is not needed for these endpoint statements, so it is not
imported.  The GR-17 passive theorem is used through its metric definition and
its observer-replacement counterexample; the passive frame invariance actually
used for the Lorentz case is `mink_boost`, derived from PORT-CAS-01
`metric_identity`.

## Items not recoverable as formal objects

* A chart-free sphere surface measure statement is not supplied by any source;
  the sources state `dΩ'=D^{-2}dΩ` only as a density law.  This unit proves it
  as an explicit change of variables in the polar chart with axis `β̂`, linked
  to the general-β closed form (`chart_link`).  Unlock: a chart-free
  `Measure.toSphere` pushforward theorem (new target, not claimed here).
* The physical premises "same narrow bundle / same source screen area `dS`",
  "Planck occupation invariant along the ray" and "reciprocity +
  transparency" are physics premises of the sources, encoded as definitions
  (`areaDist` with the same `dS`) or hypotheses (`hocc`, `hrecOld`,
  `hrecNew`); they are not derived.
