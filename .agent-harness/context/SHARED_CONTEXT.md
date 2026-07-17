# Shared Context — long-horizon rescue execution

## Project objective

- Objective: execute `PR-119..PR-183` in topological order as a claim-tiered,
  manifest-backed pre-solver observatory without fabricating native-solver or
  Bianchi-family evidence.
- Current milestone / PR: PR-123 completed at attempt 6 after attempts 1-5 were
  invalidated as false-greens; checkpoint 070 is sealed and execution is paused.
- Governing specification: `docs/research_program/long_horizon_rescue/pr123_spec.yaml`.
- Governing roadmap: `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`.
- Base revision: `e77510170424eecd49112ed6c33424ce455b154c`;
  comparison target: current worktree on `research/pr04-multicomponent`.

## Current changed surface

| Area | Files / symbols | Why relevant | Evidence artifact |
|---|---|---|---|
| Claim evidence | `common.evidence_graph`, `common.release_evidence_binding`, literal release pin | Typed closure, exact receipt consumption, fail-closed claim release | `docs/generated/pr122_claim_evidence_graph.json` |
| Test execution | `common.pytest_execution_evidence`, source-only launcher | Binds exact selector, execution, environment, source, and startup state | `docs/generated/pr122_test_execution.json` |
| MES authority | `common.mes_successor_registry`, active-consumer inventory | Inventories current consumers while preserving PR-124 blockers | `docs/generated/pr122_mes_successor_scan.json` |
| Audit consumers | publication freeze and external audit package | Audit disclosure only; current PDF gate remains blocked; policy pins are schema-checked once per build-local snapshot and hash-rechecked | `docs/generated/publication_claim_freeze.md` |
| Shared-agent harness | `AGENTS.md`, `.agent-harness/`, `.codex/hooks*`, repo-local orchestrator skill | Registers all future subagent assignments and versioned context | `.agent-harness/generated/CONTEXT_PACK.md` |
| PR-123 oracle lab | `common` oracle contracts, mutation lab, K6 catalog-independent continuum branch | Attempts 1-5 are retained as invalid; attempt 6 passed bounded C2 mechanics review with scientific status OPEN | `docs/generated/pr123_attempt_history.json` |

## Common assumptions and conventions

- Process result, evidence status, and scientific status are orthogonal axes.
- HTT owns model-dependent inference; MIO owns diagnostic-only certificates;
  OBSSTAT owns feature extraction; BASS owns transfer/atlas interfaces.
- Current external/AniCLASS transfer results are transfer-conditional and are
  never native-solver results.
- Python evidence production uses the repository venv through the tracked
  source-only launcher with `-I -S -B` and an empty external cache.
- Internal author/reviewer identities are correlated process evidence and
  cannot independently promote scientific status.
- PR-123 references must be smaller than production, use distinct algorithm
  lineage, and record shared equations, fixtures, authors, and random streams.

## Frozen scope

- In scope: analytic and manufactured references, registered known mutations,
  multi-seed properties/coverage, K6 continuum-order and upper-bound mechanics,
  oracle lineage, surviving-mutation reports, and no-empirical-consumer gates.
- Explicit non-goals: production defect remediation owned by later cards,
  observed-data inference, matched catalog/null/covariance promotion, native
  solver work, morphology compatibility, or geometry/family conclusions.
- PR3/FFP10 E2E download is complete; its analysis remains deferred to PR-150.
- PR4/NPIPE is not downloaded. PR4 download, intake, reduction, and all data
  analysis are skipped entirely by user scope; no PR4 command may run.
- All 102 remediation findings remain `OPEN`; a mechanics mutation kill does
  not mark a finding `RESCUED`.
- The integrated roadmap contains 130 actual cards through PR-183. The current
  machine-readable DAG contains 113 cards through PR-166; PR-167 is the frozen
  intake card that later registers PR-167..183, so progress reports must show
  integrated-roadmap and registered-DAG denominators separately.

## Shared evidence pointers

| Evidence ID | Path | Produced by | SHA-256 | Supports claims |
|---|---|---|---|---|
| E-PR122-SPEC | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` | reviewed repository edit | `eab2fc002d85522a33f83a3039144fc66d3cb4b5cfafc16fb66efe653d671e87` | C-PR122-MECHANICS, C-PR4-SKIP |
| E-PR122-TEST | `docs/generated/pr122_test_execution.json` | source-only graph builder | `3c93fb772c3e7cc2a78c162ac6d83a49ebcdc223c26f752f857cb8bcd2318a5f` | C-PR122-MECHANICS |
| E-PR122-GRAPH | `docs/generated/pr122_claim_evidence_graph.json` | source-only graph builder | `aba2a4285105e85720dc560e08ccbc7f9f6a384f9ffc23e4aa6872d8674e45d6` | C-PR122-MECHANICS, C-PR122-NONPROMOTION |
| E-PR122-RECEIPT | `docs/generated/pr122_release_receipt.json` | source-only graph builder | `3c40f202e6e9c46853bea1e03ffffa9881cdffaa210ed480cb2c7be45ec65012` | C-PR122-NONPROMOTION |
| E-HARNESS-ZIP | `codex_shared_context_harness_v1.zip` | user-supplied installation packet | `1f020bf290476491b07869ed40eb4d05fb99b6f38efe420453a02faf243ff94f` | C-HARNESS-INSTALL |
| E-PR122-PERF | `.agent-harness/runs/pr122-closeout-20260716/results/A-PR122-PERF.json` | registered read-only performance audit | `6c4fedbaa86667af449e70c9a8eb58712b41030def2ba4fd70655083b771cc53` | C-HARNESS-INSTALL, C-PR122-MECHANICS |
| E-PR123-CARD | `docs/codex_handoff/pr_backlog.yaml` | PR-119 DAG intake | `dec20a60c32a15c1e65bbaff859e52cf51d89299e33dacc1fa60efbcbf16eb50` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-SPEC | `docs/research_program/long_horizon_rescue/pr123_spec.yaml` | four-role intake, five invalidating hostile reviews, and main-thread v6 adjudication | `6356835da8099c4714a847864b849f8885a2bccda5e536f0f4c8dc508e282184` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-LINEAGE | `docs/generated/pr123_oracle_lineage_manifest.json` | source-only PR-123 builder | `dffb8851397cd713ff8240fd832feb3c28771b0a71bf9ffaa7b5d2c331a95ee6` | C-PR123-MECHANICS |
| E-PR123-MUTATIONS | `docs/generated/pr123_mutation_lab_report.json` | source-only PR-123 builder | `9f9a69382427082d424bd260543d006b0fbf72e18be7e9c19e30946e98f51e14` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-K6 | `docs/generated/pr123_k6_continuum_card.json` | source-only PR-123 builder | `4d1e15919259e67ba856a8b2e0966147f3c293a2756c080b795c1a65d72c7b54` | C-PR123-MECHANICS |
| E-PR123-ATTEMPTS | `docs/generated/pr123_attempt_history.json` | source-only PR-123 builder | `e19dd322c2d3435ecbed9193ef22880fe8acc733e033ab6cff74ce1c0f90aac2` | C-PR123-MECHANICS |
| E-PR123-MANIFEST | `docs/generated/pr123_artifact_manifest.json` | source-only PR-123 builder | `a1e2ce4eecb22ec43b947ec0b95f88d9e3d271be78cdd7bd06454636c7705869` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-REVIEW2 | `.agent-harness/runs/pr123-final-hostile-review-20260716/MERGED_RESULTS.json` | registered blind hostile replay | `12c7316f435251810956d2f4b6c641977364abc96f5366737a057a732ddca076` | C-PR123-MECHANICS |
| E-PR123-REVIEW3 | `.agent-harness/runs/pr123-attempt3-final-review-20260716/MERGED_RESULTS.json` | registered blind hostile replay | `b30f9039af6b2cec157f8e4881957ef3294c1631db0fb70cd702aae35c2615ff` | C-PR123-MECHANICS |
| E-PR123-REVIEW4 | `.agent-harness/runs/pr123-attempt4-closeout-review-20260717/MERGED_RESULTS.json` | registered blind hostile replay | `976605182c888f278dc6d6f02275e1cdb0bfac744433ddcfb5cb598ea07732f1` | C-PR123-MECHANICS |
| E-PR123-REVIEW5 | `.agent-harness/runs/pr123-attempt5-closeout-review-20260717/MERGED_RESULTS.json` | registered blind hostile replay | `6c6f5f1499400a410ad46cfc00a5900fb09d435b6df5814faffb4be0d84327f2` | C-PR123-MECHANICS |
| E-PR123-REVIEW6 | `.agent-harness/runs/pr123-attempt6-final-scanner-review-20260717/MERGED_RESULTS.json` | registered bounded hostile replay | `0999233e21828a9cbffa99eda2ea061a3f140f91c5cf0b163b976ec1d61ade99` | C-PR123-MECHANICS |
| E-PR124-SPEC | `docs/research_program/long_horizon_rescue/pr124_spec.yaml` | reviewed repository edit (contract-first, mutations preregistered) | `3e02502edd0ca152eae3d1971f1ec17a34ce4bf754e4b3c8b45a1565d5207d51` | C-PR124-CAS-LINEAGE |
| E-PR124-ADJUDICATION | `docs/generated/pr124_cas_adjudication.json` | cas_gate four-axis adjudication | `59ab201c65a55a5e22286be394aa4b4e9caaa9fdbda4ced9eb59a1d98607fcd7` | C-PR124-CAS-LINEAGE |
| E-PR124-AUTHORITY | `docs/generated/pr124_mes_authority_table.json` | PR-124 runner (receipt bytes = successor authorization) | `81ad8c382fbe481eaf715b971680199fed5142e2498928cff57ae9d847cc20f3` | C-PR124-CAS-LINEAGE |
| E-PR124-LINEAGE | `docs/generated/pr124_lineage_receipt.json` | PR-124 runner (fingerprint-collapsed lineage oracle) | `7c6ac4bcb612fc1b8240cc22cdf9fe4e579fa94fc33e8bedbd45ef5bf0a10bb5` | C-PR124-CAS-LINEAGE |
| E-PR124-D2 | `docs/generated/pr124_d2_authority_receipt.json` | PR-124 runner --run-rust (nonzero executed target) | `d0d11f95e006da19f4c56239a273d58e8354757f007fff2e187cba47e1754db3` | C-PR124-CAS-LINEAGE |
| E-PR124-MUTATIONS | `docs/generated/pr124_mutation_report.json` | PR-124 runner (8/8 mutants killed by real validators) | `28ed5beabeeb644de144f1beba3052d9f3a0673e5666a134fbdf3e264d2b3f67` | C-PR124-CAS-LINEAGE |
| E-PR125-SPEC | `docs/research_program/long_horizon_rescue/pr125_spec.yaml` | reviewed repository edit (contract-first) | `ce27cdc39686e39aaf74d51947e662513c36af8f12cb8d4a6a63c2306a2f9970` | C-PR125-FRAME-CONTRACT |
| E-PR125-GRAPH | `docs/generated/pr125_theorem_frame_graph.json` | PR-125 runner (12 CHECKED bindings) | `25d948ada964ebc9cb2d2589a51fbe015349b23759662ef52c58142c756fb743` | C-PR125-FRAME-CONTRACT |
| E-PR125-WITNESS | `docs/generated/pr125_kinematic_witness_report.json` | PR-125 runner (exact-Fraction witnesses) | `ed6103238253c834927cfe0572681ada98f3c243667bb871b3362d4039a63a3d` | C-PR125-FRAME-CONTRACT |
| E-PR125-MUTATIONS | `docs/generated/pr125_mutation_report.json` | PR-125 runner (6/6 killed by real validators) | `53d05eb630da62cbf0a65de9a5660f62ace1554aa6de49b0fb4df9cba9eddb8b` | C-PR125-FRAME-CONTRACT |
| E-PR126-SPEC | `docs/research_program/long_horizon_rescue/pr126_spec.yaml` | reviewed repository edit (contract-first) | `65ac5e9bb9077bb2977daa59360d163fbcaf7a1b8c423d742947566084e0fe6c` | C-PR126-EGS-ONEWAY |
| E-PR126-WITNESS | `docs/generated/pr126_oneway_witness_report.json` | PR-126 runner (sealed one-way pair) | `e6e29c0332b3d88819243e0492b7f1410caefbf69eb477be1f44c84672cf3d39` | C-PR126-EGS-ONEWAY |
| E-PR126-COUNTEREXAMPLES | `docs/generated/pr126_counterexample_registry.json` | PR-126 runner (converse counterexamples) | `ef7fd04fae5e05caba56a8db3c0b7efd24872411898e164603e0a8a147af0bf8` | C-PR126-EGS-ONEWAY |
| E-PR126-MUTATIONS | `docs/generated/pr126_mutation_report.json` | PR-126 runner (5/5 killed by real validators) | `d0fa7d455dca3b9c1d80604323772a9cb06fe6646c2ac4e8291e203aa1286a19` | C-PR126-EGS-ONEWAY |
| E-PR127-SPEC | `docs/research_program/long_horizon_rescue/pr127_spec.yaml` | reviewed repository edit (contract-first) | `03531b745869459866e382d82499f0f6f5a4e06c5ec6ebdbfed39c190d9b67b7` | C-PR127-GRADED-NONID |
| E-PR127-KERNEL | `docs/generated/pr127_response_kernel.json` | PR-127 runner (two-engine agreement) | `f9d16b3ecf3296344e78cd22457c3ff7ad638b1826c53a01b8d810911c660092` | C-PR127-GRADED-NONID |
| E-PR127-WITNESSES | `docs/generated/pr127_nonid_witnesses.json` | PR-127 runner (set-valued equivalence witnesses) | `f739d0274aaed85cd1b03ff04c8f5c649a282c98fa3ab9464c6b7ee6da14ec85` | C-PR127-GRADED-NONID |
| E-PR127-MUTATIONS | `docs/generated/pr127_mutation_report.json` | PR-127 runner (6/6 killed by real validators) | `2973313841bac9e6d7818b5ae8a62469abacf7b0fff4182afa8fddf9c53088b8` | C-PR127-GRADED-NONID |
| E-PR128-SPEC | `docs/research_program/long_horizon_rescue/pr128_spec.yaml` | reviewed repository edit (specification-first) | `c72846cb27acaa1f7331eb83aa1512f0c29a8e56b16827ae59459f7921ab8475` | C-PR128-NT2-AUTHORITY |
| E-PR128-AUTHORITY | `docs/generated/pr128_coefficient_authority.json` | PR-128 runner (dual-engine authority) | `0ba98954eb146da2682c54095d630c821d817c5d604f853030f0b8726bf88775` | C-PR128-NT2-AUTHORITY |
| E-PR128-RANDOMIZED | `docs/generated/pr128_randomized_bracket_report.json` | PR-128 runner (64 contained draws) | `5b7a9467520f723ba7939d69e84e5b8599ffbf984651407810a2a0d1d068dcb2` | C-PR128-NT2-AUTHORITY |
| E-PR128-INVALIDATION | `docs/generated/pr128_invalidation_table.json` | PR-128 runner (before/after invalidation) | `67f3f08f25463a45001ba037c121943e9ddcc69955cef04999b95b46caf5bdd6` | C-PR128-NT2-AUTHORITY |

| E-PR129-SPEC | `docs/research_program/long_horizon_rescue/pr129_spec.yaml` | reviewed repository edit (specification-first) | `6281aacd49f926ec623947376b97f5ef9add9698903f043c0f22797b4e4f73f8` | C-PR129-NTA3-REGISTRY |
| E-PR129-REGISTRY | `docs/generated/pr129_estimator_registry.json` | PR-129 runner (three-way exact verification) | `5bd311f9fedf321e7a2748ee71e967b6566883049a89124126ffe54808ff8761` | C-PR129-NTA3-REGISTRY |
| E-PR129-MC | `docs/generated/pr129_mc_report.json` | PR-129 runner (estimator-level seeded MC) | `75c704e03a38f1f122032bad3bf875580939ba3c7287d5d62bc95bdadc901971` | C-PR129-NTA3-REGISTRY |
| E-PR129-SCAN | `docs/generated/pr129_negative_scan.json` | PR-129 runner (8-target pinned negative scan) | `cd217cb7438ab32a473381a7c179b0f235ffd62f40600d7836830efc792f409e` | C-PR129-NTA3-REGISTRY |
| E-PR130-SPEC | `docs/research_program/long_horizon_rescue/pr130_spec.yaml` | reviewed repository edit (specification-first) | `2c32d8a16ac4a35ef2833fb54a8e6c1bcbb69edc4860f0ef391618662ba447a9` | C-PR130-NT2-TAIL |
| E-PR130-THEOREM | `docs/generated/pr130_tail_theorem.json` | PR-130 runner (exact tail theorem + gate exercises) | `d5e5c8754898754ce41d8d9763074eb4f691093c444f523d1e0d6ab42e3af716` | C-PR130-NT2-TAIL |
| E-PR130-PRECISION | `docs/generated/pr130_precision_report.json` | PR-130 runner (three-engine enclosure) | `6b67f781424b4ad461c00ddf0b256af1bbcd51d67b2b5f02ac4d9f61a9928572` | C-PR130-NT2-TAIL |
| E-PR130-LEGACY | `docs/generated/pr130_legacy_invalidation.json` | PR-130 runner (byte-frozen pin + relabeled surfaces) | `6f0e707c27cad5d53666bd9d3c3c16b54610988a0454dfcf3b592574c4eea014` | C-PR130-NT2-TAIL |
| E-PR131-SPEC | `docs/research_program/long_horizon_rescue/pr131_spec.yaml` | reviewed repository edit (specification-first) | `7dae9316200d1f5baf9adc31e980083d892870e3c18aa30d3bea332638f935c0` | C-PR131-OMK-NEARFLRW |
| E-PR131-TWOPATH | `docs/generated/pr131_two_path_report.json` | PR-131 runner (metric-level reduction, both signatures) | `e9809a19f964f28404734435a3ee4c1ac92b7de04f43a06d753a67a6554ba637` | C-PR131-OMK-NEARFLRW |
| E-PR131-FD | `docs/generated/pr131_fd_plateau.json` | PR-131 runner (both-branch FD plateau) | `9b29205725859d86fd3c5a43a2239d6c3630fea2d43d7f59cd1bdba2400c9823` | C-PR131-OMK-NEARFLRW |
| E-PR131-SINGULAR | `docs/generated/pr131_singular_map.json` | PR-131 runner (exact singular map + domain) | `2b0b4610429205efcc86c4596991a25575a9362b5c89527e7546828ae09f4ae8` | C-PR131-OMK-NEARFLRW |
| E-PR132-SPEC | `docs/research_program/long_horizon_rescue/pr132_spec.yaml` | reviewed repository edit (specification-first) | `12f30178f8bd3329685b1be7c3aa89fbbeb2f5bb5748860fa9dd01e89f4c8d46` | C-PR132-OMK-REMAINDER |
| E-PR132-CERT | `docs/generated/pr132_trapping_certificate.json` | PR-132 runner (exact interval trapping certificate) | `f360299d78f993da54da6fc053b4a58507db17b2a457869514e9b39f701973b2` | C-PR132-OMK-REMAINDER |
| E-PR132-BUDGET | `docs/generated/pr132_uncertainty_budget.json` | PR-132 runner (component-separated propagation) | `8f5a9afddbc76c5f4aaddfe455f2bd63a7aa21d6af590ca721a3b48556b7f8c4` | C-PR132-OMK-REMAINDER |
| E-PR132-BOUNDARY | `docs/generated/pr132_boundary_states.json` | PR-132 runner (boundary states + FD probes in-trap) | `f549166444dd08804bce8547a678276bc9076a8db8ebd727a59f3a4a4d90d720` | C-PR132-OMK-REMAINDER |
| E-PR133-SPEC | `docs/research_program/long_horizon_rescue/pr133_spec.yaml` | reviewed repository edit (specification-first) | `a75c27d3882cb1d4bc72315125d67b6048106a68a87c162ab1bb04dfc5cbf72d` | C-PR133-SOURCE-RESPONSE-TYPES |
| E-PR133-TYPES | `docs/generated/pr133_typed_quantities.json` | PR-133 runner (typed firewall + provenance audit) | `95e521c4b738d297bfafcf4f439cac67e855410c1185af1b841ceca3c474cb47` | C-PR133-SOURCE-RESPONSE-TYPES |
| E-PR133-GRAPH | `docs/generated/pr133_response_graph.json` | PR-133 runner (PR-127-consistent response graph + ladder) | `8420d3cd69bc8a29764b548b23a983d9d59a4a1e22cc6de6bf3eb10fb5155901` | C-PR133-SOURCE-RESPONSE-TYPES |
| E-PR133-BOOST | `docs/generated/pr133_harmonic_boost.json` | PR-133 runner (pure-monomial order counting) | `28713da790f7cf53e1b0ff6c95e9c94a8f1229737e18e4fe35cbcf386d74bafc` | C-PR133-SOURCE-RESPONSE-TYPES |

## Known disputes and open questions

| Question ID | Question | Required discriminating evidence | Owner |
|---|---|---|---|
No unresolved PR-123 P1 dispute remains inside the finite registered contract.
The static scanner remains a bounded fail-closed check plus disclosed manual
adjudication, not a proof of arbitrary Python-program independence.
