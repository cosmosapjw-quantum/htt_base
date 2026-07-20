# Shared Context — PR-151 background acquisition and PR-172 metamorphic battery

## Project objective

- Execute the registered long-horizon rescue DAG as a claim-tiered,
  manifest-backed pre-native-solver observatory. Reproducible null,
  upper-limit, conditional, and non-identification results are valid terminal
  scientific outputs; diagnostic preflight alone is not.
- `PR-167`, the dedicated advocate-track intake and parallel
  foreground/background status-model transaction, is completed after a fresh
  post-remediation adversarial replay. `PR-168` completed its preregistered
  failed-contract branch. `PR-169` completed with an exact `algebraic_only`
  comparator result. `PR-170` completed with a reproducible
  `CAS_BLOCKED` source-provenance audit and withheld scalar targets.
  `PR-171` completed with a class-conditional counterexample result that
  retires its blanket no-go. `PR-172` is the sole foreground card.
- Current background card: `PR-151`, authenticated DESI DR1 acquisition of
  1000 EZmocks plus 25 AbacusSummit mocks on NVMe.
- Governing roadmap:
  `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`.
- Base revision at context refresh:
  `c936fabd1527bb8c38cb13b98fc1ee608d0c5738` on
  `research/pr04-multicomponent`.

## Current DAG and execution state

- Registered DAG: 130 cards through PR-183; 105 completed, PR-172 foreground,
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
  Host-level process inspection and the 2026-07-20 00:34 UTC fast probe
  confirmed session `htt_pr151_desi_20260719`, pane/lock owner PID `16695`,
  runner PID `16709`, aria child PID `2252558`, and the expected
  `--phase acquire` command. It found 110/1000 authenticated EZmocks, 0/25
  Abacus records, 10/15 audit members, 17 fresh `.part` files totalling
  4,383,143,616 bytes, an 8.2-second-old log, and 823.04 GiB free. The live
  writer plus growth since the 00:18 UTC probe show that acquisition is active.
  The older batch manifest still reports 30 authenticated EZmocks and the
  intentional phase-migration `KeyboardInterrupt` until the current batch
  checkpoint is committed; that stale manifest state is not a restart signal
  while the lock, runner, aria child, log, and partials are live.
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

## PR-169 foreground contract boundary

- PR-169 audits the unsigned size hidden by the PR-126/127 signed comparator
  cancellation. It must distinguish the repository variable
  `V2 = omega_ab omega^ab/(6 H^2)` (historically named `W2` in the comparator)
  from the Nilsson et al. variable `W_N2`, which denotes normalized Weyl
  curvature. A map `W_N2 -> V2` is forbidden unless an exact-model derivation
  proves it; symbol-name resemblance is not evidence.
- The algebraic witness family may test
  `x_C = Sigma2 - V2 + Omega_tilt + DeltaOmega_k` at
  `(Sigma2,V2,Omega_tilt,DeltaOmega_k)=(a,a,0,0)`, `a>0`, and the registered
  unsigned carrier `M_unsigned = Sigma2 + V2 + Omega_tilt +
  abs(DeltaOmega_k)`. This can establish exact cancellation with
  `M_unsigned=2a` only on the comparator carrier.
- Constructive or physically admissible promotion additionally requires an
  exact-model provenance map plus Hamiltonian, momentum/Gauss,
  vorticity/tilt-compatibility, matter-positivity, and domain gates. The
  PR-127 parent identity and comparator-level positivity are necessary but not
  sufficient. Missing full receipts force the terminal label
  `algebraic_only`; CAS agreement cannot supply missing physical premises.
- Nilsson et al. study non-tilted Bianchi VII0 dust models and define their
  `W_N2` from electric and magnetic Weyl tensors. Their asymptotically small
  shear with nonzero Weyl curvature is not, by itself, a repository
  shear-vorticity cancellation witness. This primary-source mismatch is a
  preregistered promotion falsifier, not a post-result caveat.
- Before implementation, PR-169 must freeze conventions, domain, exact target,
  negative controls, source provenance, and promotion falsifiers in a
  schema-v2 CAS contract. Four blind axes are required; a missing engine is
  `CAS_BLOCKED`, disagreement is not resolved by voting, and a computational
  algebraic PASS remains `algebraic_only` unless all physical gates pass.
- The blind preimplementation physics, harness, and claim reviews found the
  algebraic `4B`/`2B` ceilings sound but blocked constructive promotion. Their
  findings are remediated in spec version 2 by an exact ordered-rational
  domain, an uncapped `a`-family obligation, eight typed same-state physical
  receipts, total terminal routing, and a hash-bound candidate-branch
  supersession receipt. The immutable PR-167 intake card is not rewritten;
  its proposed constructive branch is subject to its registered
  `algebraic_only` kill switch.
- Primary-source authentication binds arXiv v1 PDF SHA-256
  `f4f62fd488424b3396f5dbcaf0cc80554be626b560d139331b896fef2d13d4ce`.
  The provenance record SHA-256 is
  `978437e011346c396a2ad3b4f924f91d1c21afa89529576377c0f6f86530f668`.
- The immutable first schema-v2 contract is
  `docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE.json`,
  SHA-256
  `b4b2cf6a247209ff22406b7c1f493387934b9e4d2b2824b396a8f3fbc23c2781`.
  Its first blind four-axis run failed: Wolfram+xAct, SymPy, and
  SageMath+Singular independently exposed the same projection-fixture
  substitution defect, while Lean exposed a missing executable-level
  decidability instance. These failures remain evidence and no result from
  that wave is reusable as a PASS.
- Contract version 2 repairs only those registered harness defects, records
  the exact invalidation reason, requires four fresh blind axes, and retains
  the same scientific semantics, domain, expected values, promotion gates,
  and no-exception policy. Its path is
  `docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE_V2.json`,
  SHA-256
  `963e19b76eec31c74c27c0b014a80484f798528ab5c7cf5dab067f50916b5aad`.
  A completely fresh version-2 blind run now passes all nine obligations on
  Wolfram+xAct, SymPy, SageMath+Singular, and Lean+mathlib under that single
  hash. Durable versioned receipts preserve the version-1 `CAS_FAIL` and the
  version-2 `CAS_4AXIS_PASS`; no result was reused across versions.
- The exact registered result is `M_max(B)=4B` on the full capped carrier,
  `M_slice_max(B)=2B` on the shear-vorticity slice, and the uncapped rational
  family `(a,a,0,0)` with `x_C=0`, `M_unsigned=2a`. This is comparator algebra,
  not an Einstein-matter solution.
- All eight physical-promotion receipts are missing. Nilsson's normalized
  Weyl variable has no exact bridge to the repository vorticity variable.
  Therefore the preregistered terminal route is `algebraic_only`, public use is
  false, and the immutable PR-167 constructive candidate is superseded through
  its own kill switch rather than rewritten.
- The active-consumer scan inventories 250 code/current-claim files, finds zero
  unresolved active promotion claims, and all 18 registered mutations are
  detected. The current v9 table now scopes V2/W2 to a zero column in the
  registered response map and makes no order-independent or Weyl claim.
- Final hostile review found manuscript overclaim, match-window refutation
  leakage, trust-on-status CAS aggregation, and overwritten v1 source paths.
  The original FAIL envelopes remain immutable. The main-writer closeout
  corrected every concrete finding, added closed claim classification and CAS
  envelope schemas, preserved the complete v1 source snapshot, and replayed
  28 targeted, 79 related EGS, 14 PR-167/168, and 6 smoke tests. The hash-bound
  adjudication is `docs/generated/pr169_closeout_review_receipt.json`.

## PR-170 completed CAS-blocked provenance result

- PR-170 must first authenticate the external Buchert, Wiegand--Buchert, and
  Barrow--Tsagas provenance anchors and freeze conventions, averaging domain,
  spatially constant-expansion assumptions, exact target identities, and
  falsifiers before any engine sees a result.
- The proposed `Omega_Q^(D)=-Q_D/(6H^2)=Sigma2_std` bridge is a candidate
  externally attributed conditional identity. Its normalization and domain
  must be derived from the cited definitions; four-engine agreement cannot
  repair an incorrect or underdefined contract.
- The two-patch construction must distinguish a valid algebraic cancellation
  from a physically admissible averaged-domain witness. Patch weights,
  expansion variance, shear terms, matching assumptions, constraints, and
  curvature conventions remain explicit promotion gates.
- Type V versus VII_h curvature handling is not interchangeable: any
  trace-free `^3S_ab` correction and the isotropic three-curvature case must be
  typed and verified rather than inferred by label.
- Wolfram+xAct, SymPy, SageMath+Singular, and Lean+mathlib remain four blind,
  non-collapsible axes under one schema-v2 contract. A missing engine is
  `CAS_BLOCKED`; disagreement is `CAS_CONFLICT` or `CAS_FAIL`, never voting.
- Even a successful result is an externally attributed conditional identity
  and witness, not a new theorem, observational result, family identification,
  or native-transfer validation. If any registered type or provenance bridge
  fails exact closure, the terminal result retains `x_C` without a Buchert home.
- Primary-source authentication now binds the four arXiv v2 source archives by
  SHA-256 plus normalized equation records. The total Buchert `Q_D_B` and the
  Barrow--Tsagas residual `Q_D_BT` are distinct typed symbols.
- The frozen scalar target is
  `Omega_Q_D_B=Sigma2_D_rms-Var_D(theta)/(9 H_D^2)`. Therefore
  `Omega_Q_D_B=Sigma2_D_rms` requires `Var_D(theta)=0`; it is not true on the
  nontrivial two-patch cancellation fixture.
- The exact cancellation fixture uses `lambda=1/2`, `H_1=3`, `H_2=1`, and
  `sigma_sq_1=sigma_sq_2=3`, giving `H_D=2`, `Var(theta)=9`, `Q_D_B=0`,
  `Omega_Q_D_B=0`, and `Sigma2_D_rms=1/4`. This is an algebraic
  candidate non-identification example only; it is not emitted as a PR-170
  result because the required four-axis seal is blocked.
- Eleven canonical type labels receive the same type-independent scalar CAS
  row. External curvature closure is authenticated only for one registered
  type-V construction. Type I is definitionally flat in the internal exact
  registry but is not counted as externally authenticated; nine rows,
  including generic VII_h, remain unresolved. Thus four-axis scalar agreement
  cannot establish an eleven-type physical bridge or a Buchert home for x_C.
- The frozen contract is
  `docs/generated/pr170_cas/CAS_CONTRACT_PR170_BUCHERT_TWO_PATCH.json`.
  Four fresh blind axes must be registered only after this context rebuild;
  their receipts must bind the pre-axis authorization root.
- The first four receipts passed the scalar obligations, but independent
  closeout review invalidated that authorization generation: the runner's
  contract validator allowed vacuous source/tool inventories and the collector
  did not rebind assignments to the authorization root. The result generator
  also trusted forgeable collection summary fields. Those receipts are not
  reusable for closeout.
- Remediation generation 2 strengthens non-vacuous contract validation,
  authorization/assignment/context binding, full collector replay, executed
  claim mutations, active-consumer inventory, Barrow--Tsagas physical moment
  guards, and local claim qualifiers. Because the spec, provenance, module,
  runner, and contract changed, four fresh blind axes are mandatory before any
  replacement result pack may be generated.
- In remediation generation 2, SymPy, SageMath+Singular, and Lean+mathlib pass
  all 15 obligations. Wolfram+xAct produces no payload and exits 255 on two
  same-assignment attempts; both failure-result SHA-256 values are preserved.
  A sandboxed standalone Wolfram version probe has the same exit. The strict
  adjudication is therefore `CAS_BLOCKED`, not `CAS_FAIL` and not a majority
  pass. The scalar identity and two-patch measurement are withheld.
- The terminal reproducible result is a source-provenance audit only: 1/11
  externally authenticated type closure, one internally exact definitional
  type, nine unresolved types, and all same-state physical receipts missing.
  `docs/generated/pr170_result_card.json` has process status `BLOCKED`, null
  identity/measurement fields, and public use false. The status token is
  narrowed to
  `NO_CURRENTLY_AUTHENTICATED_X_C_WIDE_BUCHERT_HOME`, explicitly an epistemic
  evidence status rather than an existence theorem.
- Three independent closeout reviewers and the final adjudicator preserve their
  original FAIL and `FAIL_NOT_READY` envelopes under
  `docs/generated/pr170_reviews/`. The main writer subsequently fixed every
  concrete finding, including live blocked-route claim mutations and the
  type-I provenance erratum, without relabeling those frozen verdicts. The
  closeout evidence is `docs/generated/pr170_closeout_review_receipt.json`;
  28 targeted and 118 related tests pass.

## PR-171 completed result boundary

- PR-171 is authorized by the explicit approved sequence despite its
  `hypothesis_only` scientific artifact mode. It remains conditional/C2,
  internal, and `public_use=false`.
- Before any result is viewed, freeze the exact dynamical class, time variable,
  equation-of-state and closure domain, 3/4 background relaxation ODE, 2x2
  linearized subsystem, stability target, suppression functional, and a
  physically admissible persistent-tilt falsifier. No numerical suppression
  value, including `1e-6`, may be fixed as a conclusion.
- The Coley--Hervik--Lim mechanism must be externally attributed. Khronon or
  non-comoving dark-sector dressing is a loophole/counterexample lane, not an
  assumed closure or a new theorem.
- Wolfram+xAct, SymPy with high-precision checks, SageMath+Singular, and
  Lean+mathlib must run blind under one schema-v2 contract. A missing engine is
  `CAS_BLOCKED`; disagreement is `CAS_CONFLICT` or `CAS_FAIL`, never
  majority voting.
- A stability statement may be only class-conditional. A physically admissible
  persistent-tilt counterexample retires the proposed no-go claim. Missing
  physical admissibility or source-space closure may terminate as
  `algebraic_only`, `non_informative`, or a registered blocked/failure
  result rather than being promoted.
- PR-151 was probed at PR-171 start and end and remained non-terminal. No
  partial mock entered PR-171.
- The pre-axis spec is now frozen at
  `docs/research_program/long_horizon_rescue/pr171_spec.yaml`. It supersedes
  the roadmap's unvalidated `10^-6..10^-7` candidate as an expected answer or
  threshold; the suppression value remains null unless all frozen inputs exist.
- Five raw arXiv archives and normalized records are authenticated by
  `docs/generated/pr171_source_verification.json`. The restricted flat-RW
  non-interacting equation relaxes for constant `w<1/3`, but Hervik--Lim's
  tilted Bianchi-VIII `gamma=5/4`, `w=1/4`, `Gamma=0` source class tends
  generically to extreme tilt and therefore retires the blanket no-go.
- The exact CAS target is limited to the RW identity, a stipulated near-FLRW
  two-fluid drag matrix with local linear stability, a generic persistent-mode
  negative control, and the counterexample's exact domain mapping. CAS does
  not prove the external asymptotic theorem, nonlinear shear closure, or a
  numerical suppression ceiling.
- CAS generation 1 is permanently preserved as
  `PROCESS_EVIDENCE_INVALID`: Wolfram+xAct passed, SymPy and Sage exposed
  serialization/substitution harness defects, and the Lean timeout path
  exposed a bytes-serialization defect before writing an envelope. None of
  those receipts may be reused. Contract v2 contains the repairs and requires
  four fresh blind axes.
- CAS generation 2 is also preserved as `CAS_FAIL`: Wolfram+xAct passed while
  SymPy, Sage, and Lean exposed three remaining representation/proof-script
  defects. Contract v3 fixed those defects without changing the mathematical
  statement.
- Four fresh blind generation-3 axes passed all 15 frozen obligations, yielding
  `CAS_4AXIS_PASS` without exception, majority vote, or prior-generation reuse.
  The independent adjudicator found that old prose named `gamma=7/6` while the
  registered fixture was `gamma=5/4`; the additive hash-bound erratum makes
  only `5/4` CAS-sealed and leaves `7/6` source-only. Any exact promotion of the
  latter requires four fresh axes.
- The terminal result is
  `CLASS_CONDITIONAL_NO_GO_RETIRED_BY_COUNTEREXAMPLE`. Restricted RW
  relaxation and the stipulated drag-matrix stability are exact
  class-conditional results. Generic closure, khronon shear leakage, and a
  numerical suppression ceiling remain unidentified. The complete result is
  internal, `hypothesis_only`, and `public_use=false`.

## PR-172 foreground boundary

- PR-172 is the next defensible lane: a metamorphic symmetry
  self-consistency battery. Passing it is software/model self-consistency and
  never physical validation, observational support, or family identification.
- PR-151 must be probed at PR-172 start and end. If it becomes terminal-ready,
  finish the atomic PR-172 result, review, and commit before starting PR-173;
  then finalize PR-151 and return to PR-155--158.

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
| E-PR169-CONTRACT-V1 | `docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE.json` | immutable first contract and failed blind-wave authority |
| E-PR169-CONTRACT-V2 | `docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE_V2.json` | repaired contract requiring four fresh blind axes |
| E-PR169-CAS | `docs/generated/pr169_cas_collection_receipt.json` | preserved v1 failure and fresh v2 four-axis agreement |
| E-PR169-RESULT | `docs/generated/pr169_result_card.json` | exact comparator result and algebraic-only terminal route |
| E-PR169-MANIFEST | `docs/generated/pr169_artifact_manifest.json` | hash-bound inputs and result artifacts |
| E-PR169-REVIEWS | `docs/generated/pr169_reviews/` | preserved independent FAIL assignments and result envelopes |
| E-PR169-CLOSEOUT | `docs/generated/pr169_closeout_review_receipt.json` | main-writer remediation adjudication and verification record |
| E-PR170-SPEC | `docs/research_program/long_horizon_rescue/pr170_spec.yaml` | frozen conventions, domain, fixtures, falsifiers, and terminal routing |
| E-PR170-PROVENANCE | `docs/research_program/long_horizon_rescue/pr170_primary_source_provenance.yaml` | source archives, equation locators, symbol crosswalk, and partial type closure |
| E-PR170-CONTRACT | `docs/generated/pr170_cas/CAS_CONTRACT_PR170_BUCHERT_TWO_PATCH.json` | frozen four-axis scalar obligations and eleven type labels |
| E-PR170-CAS | `docs/generated/pr170_cas_collection_receipt.json` | generation-2 four-axis scalar adjudication after authorization hardening |
| E-PR170-ERRATUM | `docs/research_program/long_horizon_rescue/pr170_spec_erratum.yaml` | non-reuse correction separating external V from internal-definitional I |
| E-PR170-RESULT | `docs/generated/pr170_result_card.json` | CAS-blocked source-provenance audit with scalar targets withheld |
| E-PR170-MANIFEST | `docs/generated/pr170_artifact_manifest.json` | hash-bound blocked-result pack |
| E-PR170-REVIEWS | `docs/generated/pr170_reviews/` | preserved FAIL and FAIL_NOT_READY review envelopes |
| E-PR170-CLOSEOUT | `docs/generated/pr170_closeout_review_receipt.json` | post-review remediation and terminal blocked adjudication |
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
