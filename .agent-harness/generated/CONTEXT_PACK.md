# Canonical Shared Context Pack

Context version: `af3ddd73dfb959994d43a990e12d5e6096f652ff4c564fb61c0dd650af258f0b`
Built at: `2026-07-19T19:20:34+00:00`

This pack contains only the shared Tier-0 context. Assignment-specific context and sibling results are intentionally excluded.

---

## Source: `.agent-harness/context/SHARED_CONTEXT.md`

SHA-256: `38831670580d2c5a01ac8cf288d1d882d9e147914000ec32ae7b7f21201d500a`

# Shared Context — PR-151 background acquisition and PR-168 failed-contract closeout

## Project objective

- Execute the registered long-horizon rescue DAG as a claim-tiered,
  manifest-backed pre-native-solver observatory. Reproducible null,
  upper-limit, conditional, and non-identification results are valid terminal
  scientific outputs; diagnostic preflight alone is not.
- `PR-167`, the dedicated advocate-track intake and parallel
  foreground/background status-model transaction, is completed after a fresh
  post-remediation adversarial replay. `PR-168` completed its preregistered
  fail branch; there is no foreground card at this atomic commit boundary.
- Current background card: `PR-151`, authenticated DESI DR1 acquisition of
  1000 EZmocks plus 25 AbacusSummit mocks on NVMe.
- Governing roadmap:
  `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`.
- Base revision at context refresh:
  `00fbadda3283c06aad33c1494a3d0781d5a53442` on
  `research/pr04-multicomponent`.

## Current DAG and execution state

- Registered DAG: 130 cards through PR-183; 102 completed, no foreground PR,
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
  The 2026-07-19 19:14 UTC fast probe found 70/1000 exact EZmock records,
  0/25 Abacus records, 32 partial files totalling about 7.87 GiB, a fresh
  growing log, and about 823.9 GiB free. Host-level tmux inspection confirmed
  session `htt_pr151_desi_20260719`, pane/lock owner PID `16695`, and the
  expected `--phase acquire` command. The writer lock itself remains held; PID
  discovery from the fast probe may report no matches inside its sandbox PID
  namespace and is therefore combined with lock evidence as the effective
  writer state. The same final probe directly observed runner PID `16709` and
  the current aria child PID `970357`. The older batch manifest still reported 30
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

## PR-168 completed failed-contract result

- PR-168 is a COMMON-owned, BASS-contributed code-integrity and conditional
  exact-mechanics card. It cannot create an observational, transfer, geometry,
  family-identification, or cosmological claim.
- Before any CAS result was produced, the dedicated spec, active-consumer
  inventory, four axis sources, and schema-v2 CAS contract were frozen. The
  contract is
  `docs/generated/pr168_cas/CAS_CONTRACT_PR168_ACCEL_KINEMATIC_SOURCE_BASIS.json`
  with SHA-256
  `d2821237e8c7cf3fc97b27dea5062cc943482d217bbc53f45157848b111a542d`
  (contract version 2). Version 1 was invalidated in full after its first blind
  wave exposed a Sage exit-propagation defect and a Lean proof-script compile
  error; no version-1 PASS result is reusable.
- The candidate identity is restricted to the linearized homogeneous
  long-wavelength (`k_eff = 0`) thermodynamic-temperature response: the
  acceleration and kinematic drives occupy the same ell=1 source-vector basis,
  with no independent ell>=2 source at that order. Streaming, finite-k,
  polarization, frequency distortions, and higher-order boost terms are
  excluded and remain falsifiers outside this domain.
- Wolfram+xAct, SymPy, SageMath+Singular, and Lean+mathlib must run blind under
  one contract hash. Any missing engine is `CAS_BLOCKED`; disagreement is never
  resolved by majority vote.
- The pre-result active-consumer inventory hash is
  `9c4a07d7f6c31d9b2368c4fbdae4df65c3cc9963fb287d16816a31efd255d86a`.
  It separates the unsupported in-house MES triple from historical TSC/obsstat
  reproduction and physically distinct BASS acceleration surfaces.
- The contract-v2 blind rerun returned exception-free computational
  `CAS_4AXIS_PASS` on all four required axes. Independent hostile review then
  found that the contract itself was scientifically invalid: with
  `S_A=(A G/3) delta_(ell,1)`, the registered fixture gives `S_A/A=5`, not the
  registered normalized target `G=15`; the negative controls also lacked
  contract-level equations and sign conventions.
- The final post-CAS adjudication is therefore `CAS_FAIL`, while the original
  engine agreement is preserved as superseded computational evidence. A fresh
  attempt requires a repaired contract hash and four new blind axes; no current
  PASS envelope is reusable.
- Every path in the pre-axis active-consumer inventory is byte-identical to its
  frozen hash. `B_accel`, `A2_max_MES`, active consumers, manuscript, and legacy
  figure generators remain unchanged. The provisional typed-status source,
  success-only stale/mutation artifacts, and PR-168 two-bound figure are absent.
- The final result is the reproducible internal failure outcome
  `CAS_FAIL_CONTRACT_INVALID_PRODUCTION_UNCHANGED`, with a withheld theorem
  signature, full manifest, production-integrity receipt, and hash-bound
  physics/code/claim FAIL reviews. It is not a derivation or physical result.

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
| E-PR168-CONTRACT | `docs/generated/pr168_cas/CAS_CONTRACT_PR168_ACCEL_KINEMATIC_SOURCE_BASIS.json` | frozen conditional exact identity and falsifiers |
| E-PR168-CAS-RECEIPTS | `docs/generated/pr168_cas/harness_receipts/` | durable blind-axis assignments and outer envelopes |
| E-PR168-ORIG-ADJ | `docs/generated/pr168_cas_adjudication.json` | preserved computational four-axis agreement only |
| E-PR168-FINAL-ADJ | `docs/generated/pr168_contract_failure_adjudication.json` | scientific-contract CAS_FAIL and supersession of provisional authorization |
| E-PR168-REVIEWS | `docs/generated/pr168_reviews/` | durable physics, code, and claim FAIL assignments/results |
| E-PR168-RESULT | `docs/generated/pr168_result_card.json` | failed-contract result and unchanged-production disposition |
| E-PR168-MANIFEST | `docs/generated/pr168_artifact_manifest.json` | hash-bound failure closeout artifact set |
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
- A four-engine agreement under an underdefined or internally inconsistent
  contract is not sufficient. Post-CAS scientific-contract review is required;
  contract repair changes the hash and requires four fresh blind axes.

---

## Source: `.agent-harness/context/SYMBOLS.md`

SHA-256: `5c51f848f93430c8b49d46bd66219162409f06b35fdf778ea9f44c0bf5d214cb`

# Symbol and Interface Table

| Symbol / interface | Definition | Domain / type | Units / dimensions | Sign / branch convention | Source of truth |
|---|---|---|---|---|---|
| `EvidenceAxes` | Orthogonal process, evidence, and scientific status tuple | typed enum triple | dimensionless | no axis may promote another | `htt/src/common/evidence_graph.py` |
| `EvidenceGraph` | Typed acyclic content-addressed claim/evidence graph | immutable graph record | dimensionless | SHA-256 canonical JSON identity | `htt/src/common/evidence_graph.py` |
| `TestExecution` | Exact collected/executed/outcome/environment receipt | typed pytest evidence record | counts and SHA-256 refs | skipped/xfail are not passes | `htt/src/common/evidence_graph.py` |
| `ReleaseEvidencePin` | Typed view of literal-only fixed-point fields | repository-relative paths and SHA-256 refs | dimensionless | parsed without importing pin module | `htt/src/common/release_evidence_binding.py` |
| `AuthorityRegistry` | Exact principal/role/scope verifier registry | immutable principal records | dimensionless | correlated internal identities cannot promote science | `htt/src/common/remediation_state.py` |
| `MatchedNullCompetitionReport` | Canonical HTT matched-null adequacy report | exact typed report | report-defined | caller scalar or duck type is non-authoritative | `htt/htt/htt/infer/null_competition.py` |
| PR4 scope firewall | User-directed ban on PR4 download/intake/reduction/analysis | execution policy | zero commands | complete skip, not inferred completion | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` |

Record overloaded symbols explicitly. A CAS axis may introduce internal names,
but its result must map them back to this table.

---

## Source: `.agent-harness/context/FROZEN_DECISIONS.md`

SHA-256: `434a49176ce2afe84c07a61302563321d0d16169e0300e3ee87cb010a5bb5b72`

# Frozen Decisions and Rejected Alternatives

| Decision ID | Decision | Rationale/evidence | Scope | Reopen condition |
|---|---|---|---|---|
| D-PR4-SKIP | Skip PR4 download, intake, reduction, and all data analysis | Explicit user instruction; PR4 data is absent | Entire roadmap execution | New explicit user direction plus authenticated inputs |
| D-NATIVE-BOUNDARY | Do not implement or simulate the future native low-ell solver | Repository mission and claim firewall | Pre-solver roadmap | Independently authenticated external delivery |
| D-PIN-LITERAL | Keep PR-122 release-pin fields literal-only and parse without module execution | Breaks verifier/graph fixed-point cycle while exposing a reviewable trust root | PR-122 release consumption | A stronger acyclic trust-root design with equivalent exact tests |
| D-AUTH-SNAPSHOT | Consume an immutable PR-122 exact-scope authority snapshot | Later global principal registration must not invalidate historical receipts | PR-122 only | Explicit migration with preserved historical verification |
| D-SINGLE-WRITER | Main agent alone edits production code, specs, shared gates, and shared context | Shared-context harness write-ownership rule | All multi-agent runs | Never within a run; only ownership reassignment before work |
| D-CLAIM-OPEN | Keep all 102 remediation findings OPEN and claim release false | PR-122 supplies mechanics, not scientific authority | PR-122 | Downstream gate evidence under its owning PR |
| D-PR150-RAW-RETAIN | Retain the roughly 731 GB PR3 raw ensemble | Compact replay is green, but PR4 replacement is not authenticated and no storage-swap authorization exists | PR-150/PR4 storage | Authenticated `PR4_REPLACEMENT_READY` receipt plus explicit deletion authorization |
| D-PR151-TWO-PHASE | Run PR-151 acquisition and tracked-artifact finalization as separate phases | Prevents a background downloader from racing the single foreground writer while preserving resumable `.part` files | PR-151 while another PR is foreground | PR-151 is terminal-ready and no foreground PR is being edited |
| D-PR154-SEPARATION | Keep CCHP and SH0ES observed analyses separate and keep unavailable covariance/CF4 overlap in a scenario product | Their sampling units and shared covariance differ; positional CF4 links do not establish physical identity | PR-154 | New authenticated common-covariance and identity data under a versioned scenario |
| D-PR154-T-CONVOLUTION | Keep the host effect Normal in every likelihood lane; Student-t applies only to the measurement residual and is convolved by an explicit Gamma-precision mixture | This is the registered hierarchical model and prevents a robust-measurement sensitivity from silently changing the host population model | PR-154 | A new preregistered model-comparison card with separate estimand and calibration |
| D-PR154-CF4-MATCHED | Require matched baseline coverage, width, and RMSE plus MC guards before any CF4 material-gain scenario | Earlier width-only classification produced false gains, including a zero-slope cell and worse RMSE | PR-154 | New prospective scenario specification with independent calibration data |
| D-ADVOCATE-ORDER | If PR-151 remains incomplete, run PR-167 then PR-168--171 and only the selected defensible queue | Explicit user-approved replan; hypothesis-only and native-dependent lanes remain quarantined | PR-167--183 scheduling | New explicit replan or terminal PR-151 switchback |
| D-ADVOCATE-CLAIM-CEILING | Treat PR-174/175/182 as internal hypothesis-only and PR-183 as native-dependent | Pre-native family/geometry claims remain forbidden | Advocate intake | Native atlas and registered external gates, or explicit scope change that preserves claim firewall |

Agents must not silently reopen a frozen decision. A proposed reversal is a
meta-finding with new evidence and an explicit reopen condition.

---

## Source: `.agent-harness/context/GATE_REGISTRY.json`

SHA-256: `5d42f3e116296516728dfa35f9e3133e524aea9330c8c4c5b85a4eb231bf8284`

{
  "schema_version": 1,
  "gates": [
    {
      "gate_id": "G-PR122-TEST",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr122_spec.yaml#mutation_execution_matrix"
      ],
      "statement": "Every registered PR-122 mutation maps to an exact executed passing node in the source-only receipt.",
      "required_evidence": [
        "E-PR122-TEST"
      ],
      "pass_condition": "132 collected, 132 executed, 132 passed, and 56/56 exact mutation mappings.",
      "fail_condition": "Any missing, non-executed, non-passing, or semantically mismapped node.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR122-FIXED-POINT",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr122_spec.yaml#release_policy"
      ],
      "statement": "Graph, receipts, closure, manifest, verifier, and literal pin form one exact fixed point.",
      "required_evidence": [
        "E-PR122-GRAPH",
        "E-PR122-RECEIPT"
      ],
      "pass_condition": "Source-only graph --check and audit-disclosure consumption pass while claim release is false.",
      "fail_condition": "Any stale hash/ref or claim_release_allowed=true.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-HARNESS-INSTALL",
      "spec_refs": [
        "AGENTS.md#mandatory-shared-context-protocol-for-subagent-workflows"
      ],
      "statement": "The shared-context harness is installed, versioned, and valid before new subagent work.",
      "required_evidence": [
        "E-HARNESS-ZIP"
      ],
      "pass_condition": "Context pack builds; validate_harness reports ok; all future assignments are registered with four-field headers.",
      "fail_condition": "Stale context, unregistered assignment, invalid result envelope, or budget violation.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR4-SKIP",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr122_spec.yaml#data_scope"
      ],
      "statement": "PR4 download, intake, reduction, and analysis remain entirely skipped.",
      "required_evidence": [
        "E-PR122-SPEC",
        "E-PR122-GRAPH"
      ],
      "pass_condition": "PR4 commands_run=0 and no PR4-derived artifact or claim.",
      "fail_condition": "Any PR4 data command, derived value, or inferred joint PR3+PR4 result.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR122-FINAL-CONSUMERS",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr122_spec.yaml#acceptance"
      ],
      "statement": "Harness integration leaves quarantine, freeze, package, and consumer tests current.",
      "required_evidence": [
        "E-PR122-GRAPH"
      ],
      "pass_condition": "Harness validation, CF4 quarantine, freeze, package, smoke, collection, and PR-122 integration checks pass with only the documented PDF blocker.",
      "fail_condition": "Any unexpected failure, stale artifact, claim drift, or PR4 execution.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR123-SPEC",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr123_spec.yaml"
      ],
      "statement": "PR-123 has a reviewed, claim-bounded acceptance and mutation contract before implementation.",
      "required_evidence": [
        "E-PR123-CARD",
        "E-PR123-SPEC"
      ],
      "pass_condition": "Four-role divergence closes scope, lane ownership, properties, mutation IDs, independence fields, and kill switches in a tracked spec.",
      "fail_condition": "Implementation starts before the reviewed spec or absorbs later production-remediation ownership.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR123-ORACLE-INDEPENDENCE",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr123_spec.yaml#oracle_lineage_contract"
      ],
      "statement": "Every PR-123 reference records algorithm, source, equation, fixture, author, and random-stream lineage.",
      "required_evidence": [
        "E-PR123-SPEC",
        "E-PR123-LINEAGE",
        "E-PR123-ATTEMPTS"
      ],
      "pass_condition": "Reference code is smaller than production and shared lineage is explicit; file-path separation alone is insufficient.",
      "fail_condition": "A self-oracle or unrecorded correlated reference is counted as independent.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR123-MUTATIONS",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr123_spec.yaml#mutation_registry"
      ],
      "statement": "All preregistered defect mutations are executed and killed lane by lane.",
      "required_evidence": [
        "E-PR123-SPEC",
        "E-PR123-MUTATIONS",
        "E-PR123-ATTEMPTS"
      ],
      "pass_condition": "The exact mutation matrix has no survivor; any survivor blocks only its lane and remains reported.",
      "fail_condition": "A registered mutation survives, is skipped, or is replaced after results are known.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR123-K6-CONTINUUM",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr123_spec.yaml#k6_continuum_contract"
      ],
      "statement": "The K6 branch is catalog-independent and checks analytic fields, convergence, decomposition, and the sqrt(2) residual lock.",
      "required_evidence": [
        "E-PR123-SPEC",
        "E-PR123-K6",
        "E-PR123-MANIFEST"
      ],
      "pass_condition": "At least four grids and two stencil orders pass registered continuum/order/upper-bound properties with zero empirical consumers.",
      "fail_condition": "Any catalog input enters, convergence/order fails, or the analytic residual lock is not reproduced.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR124-CAS-4AXIS",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr124_spec.yaml#cas_contract"
      ],
      "statement": "The MES geodesic reduction statement is verified by four independent engine implementations under one contract hash.",
      "required_evidence": [
        "E-PR124-SPEC",
        "E-PR124-ADJUDICATION"
      ],
      "pass_condition": "cas_gate adjudicate returns CAS_4AXIS_PASS bound to the on-disk contract hash with all four axis envelopes PASS, matching check keysets, and identical computed exact rationals.",
      "fail_condition": "Any axis blocked/failed/misaligned, a stale contract binding, a missing computed value, or drifted axis-script bytes."
    },
    {
      "gate_id": "G-PR124-LINEAGE-ORACLE",
      "spec_refs": [
        "docs/research_program/long_horizon_rescue/pr124_spec.yaml#lineage_contract"
      ],
      "statement": "Derivation independence is counted by fingerprint-collapsed lineages, never by engine agreement.",
      "required_evidence": [
        "E-PR124-LINEAGE",
        "E-PR124-AUTHORITY"
      ],
      "pass_condition": "Geodesic branches carry >= 2 byte-verified lineages; MES_NG branches stay UNVERIFIED_PRINT_ONLY; claimed counts never exceed collapsed counts.",
      "fail_condition": "Any same-fingerprint inflation, unresolved in-repo lineage source, or non-geodesic promotion."
    }
  ]
}
