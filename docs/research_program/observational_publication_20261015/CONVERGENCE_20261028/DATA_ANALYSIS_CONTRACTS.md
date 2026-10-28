# Data-to-result contracts for the convergence slice

Scope: C2/C4 design, 28 October 2026. Current repository base is
`bdead6a8f51282ca647224b460b0f65de085568b`. The four contracts below finish
bounded scientific outputs using retained evidence. Optional inputs strengthen a
specific interpretation; their absence does not block the first report or replace
a scientific result with an acquisition memo. No computation, catalogue replay,
new download, runtime mutation or scientific status promotion was performed here.

Paths below use `B = docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products`,
`T = docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/imports/four_goals`, and
`F = docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/imports/foundations`. Old producers often write their original output paths and some enforce
one-use contracts. New consumers must read their saved results or call pure
functions; do not invoke old producer `main()` functions to manufacture fresh receipts.

The exact final filenames and product names are the `outputs` and `qualified_product_expected` fields of `FRONTIER.json`. The matching `task_id` and final `outputs` are also provided in the companion JSON. Filenames listed below describe intermediate calculations; package them into those final products rather than creating competing completion contracts.

## 1. Radiation morphology and kinematic sensitivity

**Use now.** `B/R36-05-RADIATION-RESPONSE/RESULT.json`, `VALIDATION.json`,
`PUBLICATION_STATUS.json`, and the pure functions in `radiation_core.py`:
`moments`, `response_from_moments`, `response_direct`, `stress_readout` and
`coercivity_diagnostic`. The R36 result is a qualified conditional **synthetic**
complete-temperature-sky comparison, not an empirical Planck interval. Read the
later publication status alongside the immutable candidate prose. `T/lanes/GOAL1_NUMERICS.json`
and `GOAL1_MORPHOLOGY.md` supply the independently checked 23/20 joint-carrier
construction and the polarized collision bias. `T/lanes/JOINT_REMAINDER.md` supplies
the common physical-error image.

**Small new consumer.** For a frozen positive source and explicit shared derivative
allowance, compute the signed five-dimensional shear image
`L_I Sigma = -(R_tau - C_pi)` with
`C_pi = -gamma_T (0.9 pi + P_star/5)`. Scan only a declared finite grid of
transport-remainder and polarization-omission budgets. Push the *same* joint
statistical event and deterministic error body through full and reduced adapters.
Report support in fixed STF directions, minimum coercivity, image width, and the
exact omission-bias upper bound. A sensitivity radius is an input, not a measured
radiation derivative. Direct complete-input quadrature is the reference comparator;
23/20-component and full-data answers must agree to the preregistered numeric tolerance.

**Calculation intermediates.** `shear_support.csv`, `carrier_preservation.json`,
`polarization_omission.csv`, `shear_support.pdf`, `bias_budget.pdf`, and a concise
physical results section. Reuse the existing gain counterexample plot; do not
rerun all old MC merely for appearance of progress.

**Optional observational upgrade.** Cache-first calibrated intensity plus Q/U
channels with beam, mask, spin convention, frequency/bandpass response, total
cross-channel/cross-window law and spectral completion. E-mode harmonic coefficients
are not bolometric intensity. Planck does not supply the ideal helicity/V channel
in the count experiment. A measured shear statement additionally needs the same
congruence/source/frame derivative remainder. R36-06 current MC work and R36-07
foreground budget feed a later edition only after their own qualification.

**Finish criterion.** A fully computed conditional shear-sensitivity image with
matched-baseline preservation/bias tests and dimensional explanation is sufficient
for this methods result. An unavailable empirical derivative is retained explicitly;
it does not trigger a new solver or indefinite full-kinetic programme.

## 2. Optical/astrometric kinematics and information preservation

**Use now, keeping two Gaia carriers separate.**

- `F/sources/gaia/METHOD_EXECUTION_20261023__k03_depth_moments__RESULT.json`
  (Git blob `e45d91abca9108e41136cea00ab1d641328e9537`) contains `full24_state_uasyr`
  and `full24_cov_uasyr2`, their 24-to-18 map and 12-dimensional depth contrast.
  These are **E1 polar xyz / B1 axial xyz**, three reported-redshift bins plus six
  `g(z)=z/(1+z)` slopes. `F/code/gaia_info.py` contains the checked GLS/compression
  consumer. This is not an E2 shear carrier.
- `B/R36-03-PM-HISTORY/RESULT.json` retains the separate **E2/STF5** response,
  profiled information/score and history images. `pm_history.py` supplies pure
  `endpoint_response`, `history_bound`, tensor/VSH maps and nullspace controls.
  No 755,850-row refit is necessary to use the retained fixed-design Gram law.
- `B/R36-04-OPTICAL-JOINT/RESULT.json` and `optical_joint.py` contain `lift_matrix`,
  `joint_budget`, `joint_test`, `raw_to_target` and `residual_covariance`, including
  the finite-z, uncertain-S and shared-budget correction. The saved apparent CF4
  proxy is not a measured common-congruence acceleration/shear field.
- `T/lanes/GOAL2_KINEMATICS.*` supplies detector ranks, matrix-log checks and the
  36-to-33 unknown-spin example. `T/lanes/FIBRE_INFO.*` supplies finite count-law
  rank/sufficiency and its explicitly conservative exact confidence image.

**Small new consumers.** (a) Finish the saved E1/B1 Gaussian comparison on identical
carrier/noise/nuisance: scalar powers, signed per-bin coordinates, joint GLS and
invertibly tensorized coordinates. Report score information, signed/depth contrasts,
coverage and power at matched assumptions. Use existing outputs where unchanged.
(b) Separately map the E2 Gram to a declared finite set of endpoint/history response
models and physical-error radii, retaining spin/glide and null directions.
(c) Apply the joint optical budget to retained source examples and produce the
fixed-Q exact sign-radius supplement. Do not import executable scripts that run
MC at module import; extract/reuse tested pure functions or their saved results.

**Calculation intermediates.** `information_comparison.csv`, `E2_identified_combinations.csv`,
`optical_joint_budget.csv`, `nullspaces.json`, `physical_error_frontier.pdf`,
`chirality_radius.pdf`, and the two bridge paragraphs for the current optical paper.
The optical assembly entry is the current
`PUBLICATION_ACCELERATION_20261025/products/R32-05-P6-OPTICAL/README_CURRENT_OPTICAL.md`;
its cached-source overlay is authoritative over the historical build script.

**Optional observational upgrade.** Matching centroid-to-matter response, physical
depth/history, spatial covariance, source selection and radio frame calibration.
Do not concatenate E1/B1 and E2 as independent samples or identify either with
geometric vorticity without the matched response/cross-statistics. No generic SU(2)
converter is supplied by a photon helicity connection.

**Finish criterion.** Named identifiable combinations, quantified unresolved
combinations and matched-method statistics, plus the finite optical result, form
a finished paper section even when a stronger physical detection is unsupported.

## 3. Anisotropy-family compatibility

**Use now.** `B/R36-10-GEOMETRY-IMAGE/TABLE.json`, `LRS280.jsonl`,
`UNCERTAINTY_PROBES.jsonl`, `RESULT.json` and later `PUBLICATION_STATUS.json`.
`geometry_image.py` contains finite algebra; use saved products rather than rerun
its old contract-bound producer. `T/code/goal3_classification.py` already verifies
the pinned TABLE Git blob and constructs the Gauss bridge, rotation-orbit distances,
common LR carrier, adequacy residual and exact fixed-Q sign radius.

**Small new consumer.** Freeze the supplied II/VII0 physical parameter domains,
orientation group and norm convention. Report compatible family sets and minimum
separation as functions of noise and the *joint* response-error radius. Include
I/equal-VII0 equivalence and the FLRW-origin overlap. Keep the discarded trace
adequacy statistic: preserving listed-family likelihood ratios does not preserve
all evidence that both families are wrong. Compare scalar trace, suitable scalar
quadratic invariant, full signed tensor and minimal common response carrier.
If an E2 history-family application is included, reuse the separate R36-03 law;
do not merge it with the finite Ricci experiment as if both were observed curvature.

**Calculation intermediates.** `family_compatibility.csv`, `separation_budget.csv`,
`adequacy_residual.csv`, `sign_radius.csv`, `family_separation.pdf`, and a precise
statement of the additional electric-Weyl/stress data required by the Gauss map.

**Optional observational upgrade.** Existing external numeric full T/E/B templates
with family/mode/history, IC amplitude, polarization convention, beam and processing
metadata. R36-09 records an actual scoped input HOLD. Code, figures or chain files
are not the missing template payload. Do not execute AniLoS or a Boltzmann solver
to fill this gap. The finite geometry result does not wait for this optional intake.

**Finish criterion.** Complete the finite response-family comparison and optical
sign-radius result, with conditional statistical evidence and model equivalence
preserved. No universal type label is inferred from local shear or one Ricci tensor.

## 4. Directional Hubble and optical-distance consistency

**Use now.** `B/R36-01-CF4-OPERATOR/RESULT.json` directly carries the four-window
36-vector `theta4x9`, `covariance36x36`, `AN_36x3_inverse_Mpc`, units and frame.
The original exported operator is external cache
`/mnt/extdrive/workdir/htt_open_data/r36_cf4_exact_operator_actual/A_RAW_36x35970.npz`
(12,435,409 bytes; SHA256 `e835df014bf0eb96fd715994c823eec9c8449f98d3f132b1dc736b760fd2772e`).
Use it only if applying a genuinely new source covariance, not to refit frozen
CF4 means. `B/R36-02-CF4-CORRELATED/RESULT.json`, `SENSITIVITY.json` and `CONTROLS.json`
retain the already qualified correlated-response comparison.

`B/R36-08-PUBLIC-SN/RESULT.json` contains the two-bin signed 16-vector and **full
16x16 coefficient covariance**, cross-depth blocks and 490-row primary/705-row
sensitivity comparisons. Reuse those coefficients immediately. The full 1701-row
STAT+SYS array failed the frozen symmetry test; the approved selected subblocks
are exactly symmetric and positive definite. Expanding the selected domain requires
new subblock qualification, not silent symmetrization or assumption of full-source
certification. The old prose says pending; the later `PUBLICATION_STATUS.json`
records qualified conditional use.

**Small new consumer.** On each retained SN depth bin use one simultaneous
coefficient event to obtain the directional magnitude contrast between n and a
specified reference direction. Map it to an apparent local Hubble ratio through
`Delta ln H_F = -(ln 10)/5 Delta m`. For the physical local-Hubble sensitivity
add the declared differences of finite-distance/response remainder and `tau/2`.
A fitted additive magnitude intercept does not provide absolute H0. Retain the
released redshift conventions, source-chart status and correlated bins. Plot
CF4 apparent H_W separately; comparison is qualitative/conditional until a common
source and covariance exist. Use the new scalar/matrix CBL identities in an analytic
control and bounded-opacity identified-region demonstration.

**Calculation intermediates.** `directional_logH_ratio.csv`, `joint_depth_contrasts.csv`,
`opacity_remainder_envelope.csv`, `CF4_retained_H_windows.csv`,
`directional_H_ratio.pdf`, `opacity_frontier.pdf`, and a separate CBL data-readiness
row identifying which derivatives are measured and which are supplied assumptions.

**Optional empirical CBL upgrade, not a prerequisite.** It needs a radial distance
curve plus its derivative law and independently qualified H(z) over overlapping z,
not merely the two angular-bin coefficient estimates. A targeted primary-source
lookup found the author's public `https://gitlab.com/mmoresco/CCcovariance` and
`data/HzTable_MM_BC03.dat`. The inspected table has 15 rows, z=0.1791–1.965, while
both current SN selections end at z=0.15. There is **no direct redshift overlap**.
Do not extrapolate it into the current low-z sample and call that an empirical CBL
measurement. The author repository explains statistical/metallicity/young-population/
SPS/stellar-library contributions and a correlated model-error construction; `errHz`
alone is not its complete covariance. Its notebook is a method/example, requiring
release/row/model binding before use. Download only if a newly qualified overlapping
distance curve is available within this convergence scope. Otherwise finish the
current directional-ratio result and retain this as the precise optional input.

**Finish criterion.** Report the actual retained angular data result, its joint
uncertainty and explicitly bounded optical/Hubble sensitivity; complete the analytic
CBL control. Do not relabel these as an observed curvature test.

## Acquisition and resource contract

The first report and all four conditional finishing routes require **zero new raw
downloads**. Cache-first public downloads remain authorized without per-file or
cumulative byte caps; verify the actual external mount and maintain the existing
2 GiB reserve, streaming and no-overwrite rules. Keep raw maps/catalogues outside
Git. Bind every selected product's release, row order, frame, units, mask/beam,
covariance and consumed support before upgrading its claim.

Current R36-06 is an ongoing MC/streaming branch: the new reviewed transfer-helper
source/lifecycle tests are not MC100 qualification, measured throughput, scientific
completion or a live-adoption receipt. Preserve its active packets, exact source,
partial outputs, count/seed and remote-provider conditions. Consume a completed
qualified science result into the later report; never restart or change its target
because the manuscript scheduler changed.

## Source and validation record

Read: work packet; AGENTS; current R36 source scripts/results/statuses; current optical
assembly README; prior foundation Gaia24 source and consumer; new four-goal source
notes and scripts; existing DATA_ATLAS. Targeted Exa search and full-page fetch read
the author CCcovariance README and table on 28 October 2026. No broader literature
search, SciSpace claim, Wolfram execution, numerical replay or data qualification
is claimed for this design task. Prior Wolfram/independent numerical receipts are
reused through the imported evidence. The missing H(z) overlap was identified by
comparing the actual author table endpoints with the frozen SN selection.

`skill_context_used`: PhysMath Research Loop 1.3.0 selected C2/C4 excerpts and
integrated finite/progress-first policies in WORK_PACKET.md; repository AGENTS.
