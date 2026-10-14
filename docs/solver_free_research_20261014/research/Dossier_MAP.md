# Dossier map and bounded scientific return

Owner: dossier_theory_r2; exploratory mathematical research; scientific HOLD unchanged.
Requested runtime: gpt-6.1-sol/high; observed model and effort: UNKNOWN.
No production edits, native solver, ODE integration, or nested agents.

All line numbers below refer to the supplied archive chapter snapshot, preserved byte-for-byte under `../sources/dossier/`. Archive/member SHA256 values are in `../SOURCE_IDENTITY.json`. Only the four theory chapters actually consulted are included; no archive code was executed. Its actual chapter files use `vii:*` labels for volume VI and `v:*` for volume VII. Standalone wrapper filenames are not equation identities.

| Source | Actual label / line anchor | Role in this result | Missing empirical/physical input |
|---|---|---|---|
| volume_I.tex | `geo:codazzi`, 60–66; `geo:constraint_tangent`, 223–240 | Physical perturbations must remain tangent to an admissible constrained family. Arbitrary independent response columns are not a physical family. | Actual same-congruence geometry/matter family |
| volume_I.tex | `geo:hamiltonian`, `geo:feasibility`, `geo:tilted_stress`, 250–286 | Shear, density, curvature and total tilt flux are coupled. In Bianchi I zero total flux does not require every individual tilt to vanish. | Realizable matter stress and geometric initial data |
| volume_II.tex | `ii:kinetic_moments`, `ii:source_clock`, `ii:event_conservation`, 55–85 | Number current, stress tensor, event conservation and proper-second/normal-length conversions must use the same source. | Source population and shared event/clock law |
| volume_VI.tex | `vii:normalisation`, `vii:energy_direction`, 8–19 | Observer-normalized affine length and propagation-direction sign convention. Redshift is relative to an emitter congruence. | Actual frame/endpoint convention |
| volume_VI.tex | `vii:local_boost_connection`, `vii:tilted_energy`, 54–64 | Passive tetrad boost transforms connection; physical species tilt changes a velocity. These operations cannot be identified. | Spatial derivative and actual species velocity data |
| volume_VI.tex | `vii:exact_redshift_rate`, `vii:normal_redshift_rate`, `vii:tilted_endpoint_redshift`, 66–98 | An exact endpoint ratio contains the normal-history integral and endpoint Doppler factors. It does not supply a global physical response column. | Shear/direction history, emitter and observer variation |
| volume_VI.tex | `vii:cone_count`, `vii:count_abundance`, `vii:redshift_pushforward`, 179–200 | The population measure is current flux times angular area times affine length; use all redshift roots. | Empirical current/selection/completeness, overlaps |
| volume_VI.tex | `vii:observer_scalings`, `vii:count_invariance`, `vii:observer_generator`, `vii:detector`, 202–227 | Counts are invariant for a matched apparatus. Fixed numerical apertures in different physical frames select different photons. Do not add an endpoint boost generator twice. | Actual detector/CF4/CMB processing |
| volume_VI.tex | `vii:moving_boundary`, `vii:finite_bin_tangent`, `vii:finite_bin_bound`, `vii:sharp_bin_tangent`, `vii:second_bin_tangent`, 300–339 | Affine finite-response derivatives avoid inverse redshift slopes; sharp-root derivatives need root motion and Jacobian motion. | Error kernel and selection boundaries |
| volume_VII.tex | `v:gram_trace_norm`, `v:dual_norm`, 699–715 | Observable error must use aligned physical variables and compatible dual norm. | State discrepancy budgets, physical units |
| volume_VII.tex | `v:finite_parameter_remainder`, `v:observable_hessian`, 791–805 | Finite response remainder needs actual bounded second derivatives over a common domain. | Actual Hessian/domain bounds; unavailable here |
| volume_VII.tex | `v:hit_time`, `v:redshift_fold`, 808–830 | Transverse branch and swept-boundary mass; finite smooth observables remain usable at redshift folds. | Transversality or actual boundary-strip mass |
| volume_VII.tex | `v:detector_bound`, 864–876 | Separate aligned state, detector, instrument and endpoint contributions. | Physical discrepancy and instrument estimates |

## Narrow progress

`THEOREM.md` adds an explicit measurement-error/selection/normalizer bridge to the dossier finite-bin formula. It proves a finite selected-observable discrepancy bound, and a fixed-nuisance contrast criterion robust to quantified physical-response and covariance uncertainty. This supplies an analytic sub-obligation for E1/E2 (RB08–RB12). It does not close the actual PHYSICAL_RESPONSE or PHYSICAL_JOINT_LAW blocker.

The operations are standard differentiation under an integral, a quotient rule, Gaussian convolution, singular-value perturbation, and positive-matrix ordering. The useful research contribution is their concrete composition with this dossier's current-flux measure and with the existing preselection shared-prior semantics. No new mathematical theorem priority is claimed.

The primary-source lookup [Challinor and Lewis, arXiv:1105.5292v2](https://arxiv.org/abs/1105.5292v2), DOI 10.1103/PhysRevD.84.043516, was read at abstract/metadata level on 2026-10-14. It supports the need to combine density, velocity, redshift distortion, magnification and displacement terms in observed counts; it is a linearized GR result, not a full finite-tilt law or CF4 completeness estimate. No detailed equation from that paper is used as a proof premise.

## Inputs actually reused

Repository `AGENTS.md`, `docs/harness/CURRENT_CODEX_RUNTIME.md`, and `docs/observational_reboot_20261014/{BLOCKERS.json,RETURN.md,EXTERNAL_RESEARCH_HANDOFF_KO.md}` and the dossier chapters above. Existing CF4 `selected_v2/{report.md,result.json}` and `physical_dipole_v2/report.md` are summarized-data evidence, not raw object observations. The CF4 result's scope is 24 frozen SNIa-only selected groups, conditional Gaussian calibration/population/width scenarios, with no cosmological H0 or global-tilt interpretation.

The initial worker summarized only existing fit summaries; integrated output-derived calculations are preserved in `../ADDITIONAL_CALCULATIONS.json` and generated by `scripts/summarize_solver_free_publication.py`. A Wolfram kernel check verifies the Gaussian derivatives and selected-mean normalization derivative. The first Wolfram numeric attempt returned unresolved derivatives of Abs introduced by symbolic integration; the corrected check used an explicit Gaussian first-moment formula and is successful. Raw outputs preserve both attempts.
