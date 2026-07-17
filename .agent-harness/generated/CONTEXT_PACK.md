# Canonical Shared Context Pack

Context version: `22068e0a3bf9911078a73d57ed28c107f44f9babe00d8dc9375db0a7bd99c34e`
Built at: `2026-07-17T21:10:03+00:00`

This pack contains only the shared Tier-0 context. Assignment-specific context and sibling results are intentionally excluded.

---

## Source: `.agent-harness/context/SHARED_CONTEXT.md`

SHA-256: `5a6be254dda96e28ee3c952b6b3f5f535e3d0fc6ad893fc7cb75c183824dcb70`

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
| E-PR134-SPEC | `docs/research_program/long_horizon_rescue/pr134_spec.yaml` | reviewed repository edit (specification-first) | `cfe684f08ab5d560b2dd3e62aa123932b61fa09cb4afecf1165cf0eb1f7d5444` | C-PR134-ESTIMAND-REGISTRY |
| E-PR134-REGISTRY | `docs/generated/pr134_contract_registry.json` | PR-134 runner (five typed representative contracts) | `885a3a972ffed53d40f4ffdcd2b2709bf555037eea3f882e63039b5cf87228c7` | C-PR134-ESTIMAND-REGISTRY |
| E-PR134-GRAPH | `docs/generated/pr134_dependency_graph.json` | PR-134 runner (named dependence clusters) | `10db8ee186f4dfdddb5609d2ea48476694efb1c857fd0d9a324118705104bda8` | C-PR134-ESTIMAND-REGISTRY |
| E-PR134-BRANCHES | `docs/generated/pr134_branch_separation.json` | PR-134 runner (template/covariance branch separation) | `ef1d9e07830efeb612d6659287b5967fd697d955b042294ffd9fad215dcc15b8` | C-PR134-ESTIMAND-REGISTRY |
| E-PR135-SPEC | `docs/research_program/long_horizon_rescue/pr135_spec.yaml` | reviewed repository edit (specification-first) | `ac1fef7232cce95bb63aed79d8dd2686df5f69d724f30e0cfb849386997c35cf` | C-PR135-FINITE-NULL-RANK |
| E-PR135-ENUM | `docs/generated/pr135_exact_enumeration.json` | PR-135 runner (real exact enumeration exercising the estimator) | `846d90d73bff86a800f9f5b168f9387167152f263f8ff2c6513d79967fdc7846` | C-PR135-FINITE-NULL-RANK |
| E-PR135-SIM | `docs/generated/pr135_type_i_simulation.json` | PR-135 runner (super-uniform type-I + b/N negative control) | `8240df0f24dc5d355424ae73cf4d05ebb93ee4d16ae562d8301db3e32f7e6a78` | C-PR135-FINITE-NULL-RANK |
| E-PR135-SCAN | `docs/generated/pr135_max_scan.json` | PR-135 runner (dependence-preserving scan + split) | `c80ad41f95ecad3ef5231cfd1ad364c5d80f18f4e85d174a561b093fbe814631` | C-PR135-FINITE-NULL-RANK |
| E-PR136-SPEC | `docs/research_program/long_horizon_rescue/pr136_spec.yaml` | reviewed repository edit (specification-first) | `23b012ed21e0e7bc11f07d707805d36c0dee5226b2fabab00e97a0a8f49fbe88` | C-PR136-IDENTIFIED-SET |
| E-PR136-SETS | `docs/generated/pr136_identified_sets.json` | PR-136 runner (four fixtures, exact + numeric) | `f0cf8791af0154994881d07b70b30477013b8c4e5005f633f17c47c7e8fffde0` | C-PR136-IDENTIFIED-SET |
| E-PR136-CROSS | `docs/generated/pr136_cross_engine.json` | PR-136 runner (dual-engine agreement) | `92a0119536c1a327095590c5ac014d95dc5991535a373614ccd8ab80f27317eb` | C-PR136-IDENTIFIED-SET |
| E-PR136-SUBVECTOR | `docs/generated/pr136_subvector.json` | PR-136 runner (full vs subvector projection) | `e173119339449b1909240a05b83b6fe0c94135f65db033a84af2eb8711875143` | C-PR136-IDENTIFIED-SET |

## Known disputes and open questions

| Question ID | Question | Required discriminating evidence | Owner |
|---|---|---|---|
No unresolved PR-123 P1 dispute remains inside the finite registered contract.
The static scanner remains a bounded fail-closed check plus disclosed manual
adjudication, not a proof of arbitrary Python-program independence.

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

SHA-256: `82be3a48c424f2f831705f66214b616ac875d6a209e648c6c4d75dd68ee0dd9c`

# Frozen Decisions and Rejected Alternatives

| Decision ID | Decision | Rationale/evidence | Scope | Reopen condition |
|---|---|---|---|---|
| D-PR4-SKIP | Skip PR4 download, intake, reduction, and all data analysis | Explicit user instruction; PR4 data is absent | Entire roadmap execution | New explicit user direction plus authenticated inputs |
| D-NATIVE-BOUNDARY | Do not implement or simulate the future native low-ell solver | Repository mission and claim firewall | Pre-solver roadmap | Independently authenticated external delivery |
| D-PIN-LITERAL | Keep PR-122 release-pin fields literal-only and parse without module execution | Breaks verifier/graph fixed-point cycle while exposing a reviewable trust root | PR-122 release consumption | A stronger acyclic trust-root design with equivalent exact tests |
| D-AUTH-SNAPSHOT | Consume an immutable PR-122 exact-scope authority snapshot | Later global principal registration must not invalidate historical receipts | PR-122 only | Explicit migration with preserved historical verification |
| D-SINGLE-WRITER | Main agent alone edits production code, specs, shared gates, and shared context | Shared-context harness write-ownership rule | All multi-agent runs | Never within a run; only ownership reassignment before work |
| D-CLAIM-OPEN | Keep all 102 remediation findings OPEN and claim release false | PR-122 supplies mechanics, not scientific authority | PR-122 | Downstream gate evidence under its owning PR |

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
