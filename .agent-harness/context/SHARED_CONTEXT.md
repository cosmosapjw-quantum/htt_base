# Shared Context — PR-151 background acquisition and PR-167 foreground intake

## Project objective

- Execute the registered long-horizon rescue DAG as a claim-tiered,
  manifest-backed pre-native-solver observatory. Reproducible null,
  upper-limit, conditional, and non-identification results are valid terminal
  scientific outputs; diagnostic preflight alone is not.
- `PR-167`, the dedicated advocate-track intake and parallel
  foreground/background status-model transaction, is completed after a fresh
  post-remediation adversarial replay. There is no foreground card in the
  atomic handoff gap; PR-168 is the next selected card.
- Current background card: `PR-151`, authenticated DESI DR1 acquisition of
  1000 EZmocks plus 25 AbacusSummit mocks on NVMe.
- Governing roadmap:
  `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`.
- Base revision at context refresh:
  `fe7abb6aa01fdfaf0440956bd8727ddc9e1be8e7` on
  `research/pr04-multicomponent`.

## Current DAG and execution state

- Registered DAG: 130 cards through PR-183; 101 completed, no foreground PR,
  PR-151 is the sole background acquisition, PR-155--158 remain
  gated on PR-151, and PR-159--166 plus PR-183 are dormant pending authenticated
  native delivery. The dedicated PR-167 transaction preserved semantic hashes
  for all 113 pre-intake cards and registered the 17-card advocate suffix.
- The approved replan runs PR-154 first. If PR-151 is still incomplete after
  PR-154, PR-167 formally registers PR-167--183 and the foreground sequence is
  PR-168, PR-169, PR-170, PR-171.
- If PR-151 remains incomplete after PR-171, the defensible queue is PR-172,
  PR-173, PR-180, PR-177, PR-179, PR-176. PR-174, PR-175, and PR-182 remain
  hypothesis-only; PR-181 is deferred; PR-183 remains native-dependent.
- When PR-151 becomes terminal-ready, finish the current atomic foreground PR,
  finalize PR-151, execute PR-155--158, then resume the advocate queue.

## Data and resource state

- PR-150: Planck PR3 uses all 999 usable FFP10 SMICA CMB realizations plus 300
  noise realizations. ID `00970` is officially excluded. The registered
  max-scan rank is `39/1000 = 0.039`, conditional on PR3/FFP10.
- The roughly 731 GB Planck PR3 raw ensemble remains retained. It must not be
  deleted until a future authenticated PR4 replacement-ready receipt and
  explicit storage-swap authorization exist.
- PR4 observed SEVEM is public, but matched simulations are externally blocked.
  No PR4 download, intake, reduction, or numerical analysis is authorized.
- PR-151 target:
  `/mnt/sn850x2t/htt_base_e2e/workdir/raw/desi_dr1_mocks`. It uses resumable
  aria2 acquisition in tmux, one NGC+SGC random pair per mock, and random index
  1 for a preregistered 10 EZmock + 5 Abacus audit.
- The legacy all-in-one tmux wrapper was stopped at an aria-resumable `.part`
  checkpoint without deleting payloads. Session `htt_pr151_desi_20260719` now
  runs `--phase acquire`; pane/lock owner PID was `16695` at the latest probe.
  The 2026-07-19 16:50 UTC fast probe found 60/1000 exact EZmock records,
  0/25 Abacus records, five active partial files in the new batch totalling
  about 0.87 GiB, a fresh growing log, and about 832 GiB free. Host-level tmux inspection confirmed
  session `htt_pr151_desi_20260719`, pane/lock owner PID `16695`, and the
  expected `--phase acquire` command. The writer lock itself remains held; PID
  discovery from the fast probe may report no matches inside its sandbox PID
  namespace and is therefore combined with lock evidence as the effective
  writer state. The same final probe directly observed runner PID `16709` and
  the current aria child PID `659928`. The older batch manifest still reported 30
  authenticated EZmocks until the current batch checkpoint is committed.
- PR-151 partial mocks are never used for final ranks or significance. Terminal
  status requires exact 1000/25 records, observed authentication, the 15-case
  random audit, final full rehash, and producer/runner write/check.
- Foreground work must not race PR-151 tracked-artifact writes. Acquisition and
  finalization are separate phases; only acquisition may run in background.
- Fast progress probes read records, partial sizes, log age, errors, and disk
  space without repeated full-byte rehashing. No second downloader may run.

## PR-154 scientific contract

- Inputs are the authenticated PR-153 CCHP 7-host and SH0ES 13-host paired
  tables. Analyze the two source families separately; never pool overlapping
  or differently sampled source aggregates.
- Produce two distinct products: an observed host-level method-offset analysis
  and a forecast/scenario envelope for unavailable shared covariance and CF4
  overlap.
- The observed model contains latent host distance, method offsets, and
  method/calibration-group zero points. It includes Gaussian and Student-t
  sensitivity, leave-host/group-out checks, and preregistered SBC/PPC gates
  inherited from PR-138/139.
- Shared covariance is not observed. Bound it with a PSD-constrained covariance
  uncertainty set whose diagonal is fixed by reported marginal variances.
  Independence is sensitivity-only, not the primary total uncertainty.
- CF4 coordinate links are positional scenarios only. They do not establish
  physical identity and cannot support an H0, cosmological, anisotropy,
  geometry, or Bianchi-family fit.
- A stable covariance-conditional interval, no-gain result, upper limit, or
  non-identification result is an acceptable terminal result. Thresholds may
  not be tuned after seeing the outputs.

## PR-154 completed result

- The byte-reproducible write/check runner is
  `scripts/codex_harness/run_pr154_jwst_host_hierarchy.py`; numerical code is
  `htt/htt/htt/infer/jwst_host_hierarchy.py` and the preregistration is
  `docs/research_program/long_horizon_rescue/pr154_spec.yaml`.
- CCHP (JAGB minus TRGB, seven hosts) has an independence-sensitivity Gaussian
  offset median of `+0.0001143854 mag`, with 95% interval
  `[-0.06477219, +0.06293424] mag`.
- SH0ES (JWST minus HST, thirteen hosts) has an independence-sensitivity
  Gaussian offset median of `-0.03921444 mag`, with 95% interval
  `[-0.08709266, +0.00888667] mag`.
- The exact full method-level fixed-diagonal PSD mean-SE envelopes are
  `[0, 0.10471429] mag` for CCHP and `[0, 0.12538462] mag` for SH0ES; the
  narrower reduced contrast-diagonal sensitivity envelopes are also reported
  explicitly. Both structured scans are covariance-conditional, so the
  terminal result is `TOTAL_UNCERTAINTY_NOT_IDENTIFIED`, claim level C2.
- Frozen 3000-realization SBC and 5000-draw Gaussian/Student-t PPC gates pass.
  Leave-host, prior, and Gaussian-vs-Student-t sensitivity gates pass; group
  zero-point decomposition remains not identified.
- The Student-t sensitivity now keeps `u_h~Normal(0,tau_host^2)` and applies
  the variance-matched Student-t only to the measurement residual, integrating
  their convolution with a Gamma-precision quadrature. Gaussian and both
  Student-t fits pass preregistered edge-mass and independently extended/refined
  normalizer gates. A boundary review promoted the Student-t Gamma quadrature
  from 64/96 to 96/128 nodes; the largest observed relative error is now
  `6.72e-10`, with an additional 128/160 replay agreeing at `9.80e-11`.
- The CF4 product contains 2430 scenario-only cells and uses zero independently
  verified observed overlaps. Its first-half interval calibration and separate
  second-half evaluation compare adjusted and baseline estimators on matched
  draws. Material gain occurs in zero cells; CCHP has 1087 no-gain and 128
  unsafe/miscalibrated cells, while SH0ES has 1107 no-gain, 102 unsafe, and 6
  numerically unresolved cells at the current Monte Carlo budget.
- The earlier adversarial findings were patched: duplicate lock contenders no
  longer remove the active PR-151 owner receipt; PR-151 terminal verification
  requires exact commands and artifact hashes and rejects extra records;
  PR-154 mutations now exercise production guards; CF4 identity errors are
  Bernoulli per claimed host and replicate; and COMMON owns the mutation report
  and artifact manifest with HTT recorded as scientific owner.
- Final blind closeout passed all numerical/statistical, harness, and claim
  assignments under context version
  `8e8b36ee2ff5994c80f9f4f9de74d5dcfd750f5f63e5c0707c7c9c0e312d81a9`.
  The numerical reviewer independently replayed the source rows, PSD extrema,
  all 2,430 CF4 classifications, an adaptive Student-t integral, and both
  96/128 and 128/160 quadrature comparisons.

## PR-167 intake contract

- PR-167 must use a dedicated transaction. The earlier long-horizon intake
  script remains fail-closed against PR-167--183 and must not be weakened or
  used to bypass its ownership boundary.
- Immediately before intake, preserve the semantic hashes and logical status
  of every existing PR-000--166 card in a receipt. Intake is refused if the
  receipt is absent, incomplete, or no longer matches the preserved cards.
- The status interface separates one `in_progress` foreground PR from a list
  of `background_in_progress` acquisition PRs. PR-151 migrates to the latter
  without changing its logical execution state.
- Advocate cards carry typed activation and execution-lane metadata. Only
  `defensible` items enter ordinary `unblocked_next`; unblocked
  `hypothesis_only` items are reported separately, and `needs_native` remains
  dormant until an authenticated native activation gate is met.
- PR-151 monitoring remains read-only and fast. It reports authenticated
  EZmock/Abacus records, random-audit membership, partial-file count/bytes,
  log age, last records and failures, disk headroom, process/lock evidence,
  and terminal eligibility without payload rehashing.
- Claim ceilings are fixed at intake: PR-173 may be numerically unresolved at
  the current Monte Carlo budget; PR-177 is an ACT release-simulation-
  conditional modulation candidate; PR-180 tests consistency with a pure
  boost; PR-176 is structurally distinct from monopole leakage; and PR-179 is
  a selection/systematics-conditional catalogue result.
- PR-171 is scheduler-eligible only because the explicit approved execution
  sequence names it; its scientific artifact mode remains `hypothesis_only`
  and `public_use=false`. PR-174, PR-175, and PR-182 are
  `REGISTERED_NOT_SCHEDULED`. PR-183 is `NATIVE_BLOCKED`.
- Exact-math cards PR-168--171 carry blind four-axis CAS contracts. PR-175 and
  PR-182 carry the same contract in case a later, separate authorization ever
  permits execution; registration alone is not authorization.

## PR-167 implemented state and closeout

- The dedicated transaction has materialized 130 cards and 352 edges while
  preserving the exact 113-card PR-000--166 semantic/status prefix. Canonical
  and machine mirrors are byte-identical and all materialized files are mode
  `0644`; the old PR-119--166 intake script remains byte-identical.
- The transaction now validates before writing, binds exact receipt bytes,
  publishes through a durable allowlisted journal with backups and fsyncs, and
  deterministically rolls forward an all-new generation or restores any mixed
  generation. Validators reject an outstanding journal.
- The PR-167 manifest reconstructs the immutable post-intake status snapshot
  from the hash-pinned baseline plus the intake transaction. It does not bind
  itself to mutable live PR status, so later foreground transitions cannot
  invalidate or rewrite intake provenance.
- Status consumers reject unknown or overlapping active IDs, terminal residue,
  unauthorized lanes, incomplete active dependencies, background contract
  drift, typed activation drift, and hypothesis/native cards in the ordinary
  queue. The PR-151 fast probe treats a held writer lock as effective running
  evidence even when process enumeration is namespace-limited.
- First closeout findings concerning exact receipt coverage, transaction
  recovery, write-before-check behavior, package imports, frozen PR-119--166
  activation, file modes, byte provenance, active-state authorization, unknown
  IDs, the stale 65-card phrase, and dual/two-engine prose are patched.
- Post-fix verification records 113 tests in the registered six-file
  targeted suite, six smoke tests,
  strict 130-card/352-edge DAG validity, byte-identical mirrors, package import
  success, and zero targeted claim-language issues. A fresh hash-bound final
  replay, not any stale pre-fix envelope, governs PR-167 closeout. The first
  fresh replay found and caused remediation of shared typed-status validation
  for intake refresh, native dormancy, lane projection, and execution receipts;
  its FAIL envelope remains immutable evidence. The second fresh replay at
  `.agent-harness/runs/pr167-final-replay2-20260719/results/A-PR167-FINAL-REPLAY2.json`
  passed with no unresolved P0/P1/P2 and no claim promotion.

## Ownership and claim boundaries

- HTT owns the PR-154 hierarchical model, predictive checks, and scenario
  analysis. OBSSTAT owns authenticated source-table feature inputs. COMMON
  owns harness, status, artifact manifest, mutation report, and semantic gates.
- MIO certificates remain diagnostic-only and do not enter HTT evidence.
- External/AniCLASS outputs are transfer-conditional and never native BASS
  evidence. Scalar or directional results cannot identify a Bianchi family.
- Every result carries owner, scope, claim tier, artifact mode, allowed and
  forbidden uses, transfer source, input/config hashes, sky/mask status,
  covariance/null status, caveats, generation command, runtime, and Git state.
- All 102 remediation findings and the two CF4 P0 findings remain OPEN unless a
  later owning card supplies the registered independent adjudication evidence.

## Shared evidence pointers

| Evidence ID | Path | Supports |
|---|---|---|
| E-PR150-DELTA | `docs/PR_DELTAS/pr-150.md` | PR3 result and raw-retention boundary |
| E-PR150-RETENTION | `docs/generated/pr150_compact_retention_receipt.json` | compact replay and no-deletion gate |
| E-PR151-SPEC | `docs/research_program/long_horizon_rescue/pr151_spec.yaml` | exact DESI support and terminal conditions |
| E-PR151-REVIEW | `.agent-harness/runs/wave19-concrete-results-amend-20260719/results/A-W19-DESI-ARIA.json` | acquisition safety findings |
| E-PR152-DELTA | `docs/PR_DELTAS/pr-152.md` | ACT release-simulation result and raw-QE boundary |
| E-PR153-DELTA | `docs/PR_DELTAS/pr-153.md` | authenticated JWST rows and observed consistency |
| E-PR153-MANIFEST | `docs/generated/pr153_artifact_manifest.json` | source hashes and result provenance |
| E-PR154-SPEC | `docs/research_program/long_horizon_rescue/pr154_spec.yaml` | frozen model, thresholds, and claim ceiling |
| E-PR154-MANIFEST | `docs/generated/pr154_artifact_manifest.json` | concrete result and provenance summary |
| E-PR154-CAL | `docs/generated/pr154_sbc_ppc.json` | frozen SBC/PPC gate outputs |
| E-PR154-COV | `docs/generated/pr154_covariance_envelope.json` | PSD non-identification result |
| E-REPLAN | `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md` | PR-154 and advocate card intent |

## Open questions and kill switches

- If a PR-151 fast probe shows no log growth and no `.part` growth across two
  checks 15 minutes apart, inspect the exact tmux/PID tree before any restart.
- Do not launch new NVMe-heavy work below 300 GiB free; below 200 GiB, defer all
  new large jobs. Never stop DESI merely to make room for an advocate analysis.
- PR-154 is downclaimed to covariance-conditional or non-identification if
  shared covariance cannot be bounded, PPC/SBC fails, or group deletion is
  unstable. Do not replace failed observed analysis with a synthetic success.
- Advocate mathematical claims later require the repo-mandated four-axis CAS
  state. Missing engines yield `CAS_BLOCKED`, never an inferred pass.
