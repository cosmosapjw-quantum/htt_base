# R25 publication checkpoint

Owner: R25 campaign host. Scope: portable source/review and conditional-result checkpoint captured at **2026-10-23T10:22:30.725950+00:00**. This is publication preparation; no commit, push, fresh-session activation, or broader scientific admission is asserted.

The [artifact map](provenance/ARTIFACT_MAP.json) resolves original ignored runtime paths to byte-preserving portable copies. The [exact proposed Git path list](provenance/GIT_ADD_ALLOWLIST.txt) excludes unrelated dirty CAS work, caches and the ongoing frequency acquisition implementation. Absolute paths inside original receipts remain historical bindings; use the map to locate portable copies.

## Reviewed source composition

The 15-file composition `6fd6df6fa7c38b87989b305ce940940b1ecb31dc8e001b20bf419176a914f569` combines reviewed baseline `4c3ff07ac861ad17334c5d6418d4ff21bf032c13f9eee9364e33dcaf9e329c45` and reviewed three-file delta `68ac582536eaa35d99ec8dc16cc24f751f9fdc72ebbff34afbfe797f02ff792a`; 12 files retain their baseline bytes. [Baseline source review](reviews/CODE_REVIEW_CLOSEOUT.md) and [concurrency/freshness closeout](reviews/REVIEW_ONLY_SOURCE_CLOSEOUT.json) grant scoped source PASS. Actual requested review profile was gpt-6-astra/xhigh; observed runtime is UNKNOWN. Source review does not establish scientific acceptance.

| Source | SHA-256 |
|---|---|
| [scripts/codex_harness/research_controller.py](../../../../scripts/codex_harness/research_controller.py) | `27adf2717c5f2ca192b6035af7d45d46b20822533c5b81470d29bffe746bd04e` |
| [scripts/codex_harness/test_research_controller_adaptive.py](../../../../scripts/codex_harness/test_research_controller_adaptive.py) | `bd4eff453d91025618eaa6da000ef0bfdb67a70e88d1034eb33f4fb74bd76f10` |
| [scripts/codex_harness/test_context_isolation.py](../../../../scripts/codex_harness/test_context_isolation.py) | `d5a6099ed3fc42309578efe8cf2e8333de7e350b375ea0a0eb799c751b2ea6ad` |
| [docs/harness/CONTINUOUS_RESEARCH_CONTROLLER.md](../../../harness/CONTINUOUS_RESEARCH_CONTROLLER.md) | `941e8b4903266f7d3d1757920c0cec6ac421b24402d98df4bea3698d6d0a0338` |
| [.agents/skills/htt-dag-orchestrator/SKILL.md](../../../../.agents/skills/htt-dag-orchestrator/SKILL.md) | `d7d2dead1524bb62fb7746c23dbe12cae68e763752954f0f3ae1db0859820d4b` |
| [.agents/skills/htt-harness-engineering/SKILL.md](../../../../.agents/skills/htt-harness-engineering/SKILL.md) | `8027d8d7ab42fb9cb306d06622b3194ca24eac850f763f0d4f64c9fcbbe67f39` |
| [.agents/skills/htt-scientific-code-validation/SKILL.md](../../../../.agents/skills/htt-scientific-code-validation/SKILL.md) | `a5a49d3844594a01f391ce06026488b38df2e10aa208b065c2835f2abfc72cdd` |
| [.agents/skills/htt-xqpi-fg-formalism/SKILL.md](../../../../.agents/skills/htt-xqpi-fg-formalism/SKILL.md) | `11458a2d3d414f9efed8b66b7a763082dfd11c0324c7f187a4f21aa0d15d5e98` |
| [.agent-harness/context/CURRENT_SYMBOLS.md](../../../../.agent-harness/context/CURRENT_SYMBOLS.md) | `e9c958e056e96934b112d57108cdbf0fe8d4a74716e4147e1694c257b3efcdfa` |
| [.agent-harness/context/CURRENT_CONTEXT_INDEX.json](../../../../.agent-harness/context/CURRENT_CONTEXT_INDEX.json) | `d7e834580fc31c6fa00b2df0926cef6821991b125fb94b1a648ac4f760b4ad7f` |
| [.agent-harness/generated/CURRENT_CONTEXT_PACK.md](../../../../.agent-harness/generated/CURRENT_CONTEXT_PACK.md) | `4303ad1d54770eb824b5274ec6a4126c98fed22a1c01e57c55d959fd75b0ac9a` |
| [.agent-harness/scripts/_harness.py](../../../../.agent-harness/scripts/_harness.py) | `87bf83770eea508c77fb68a2de541e398b5a1cc4dbef565263f5905db42cc042` |
| [.agent-harness/scripts/build_context_pack.py](../../../../.agent-harness/scripts/build_context_pack.py) | `fd4fae901f36129cbfdcef2c2a67ebb9d1a40b1074f7ce7ffa07f4484ccb322e` |
| [.codex/hooks/session_start_context.py](../../../../.codex/hooks/session_start_context.py) | `6d761b6163726d1a6b04182c9f3d60a235f8d4b596f410b1f26d3812b5068d50` |
| [scripts/codex_harness/test_research_controller_frontier.py](../../../../scripts/codex_harness/test_research_controller_frontier.py) | `8b05ce56429de46849f1bb5e71a5577c5c703ffecf7b7fc4d49895ea797d1e85` |

## Reviewed research plan and contracts

[Current research plan](RESEARCH_PLAN_KO.md), [DAG](ADAPTIVE_DAG.json) and [frozen checkpoint](PROGRESS_CHECKPOINT_KO.md) are bound by the [checkpoint fact closeout](reviews/CHECKPOINT_FACT_REVIEW_CLOSEOUT.json). [Theorems](THEOREMS.md) and [method/source notes](METHOD_SOURCE_NOTES.md) have the [scoped theorem supplement review](reviews/THEOREM_SUPPLEMENT_REVIEW.json). Earlier plan/contract reviews retain their frozen-time scopes; they do not certify later live execution. Source/intake contracts and their actual closeouts are retained in [reviews](reviews/). The map carries prepatch candidate evidence needed to resolve historical review bindings.

## Actual completed conditional nodes

| Node | Candidate manifest | Actual independent review |
|---|---|
| R25-K03-DEPTH-COVROBUST | [Manifest](depth_covariance/MANIFEST.json) | [Scoped review](reviews/COVARIANCE_REVIEW.json) |
| R25-K03-DEPTH-BIAS-FRONTIER | [Manifest](depth_bias/MANIFEST.json) | [Scoped review](reviews/BIAS_REVIEW.json) |
| R25-CMB-CONDITIONAL-GRAM | [Manifest](cmb_conditional_gram/MANIFEST.json) | [Scoped review](reviews/CMB_REVIEW_CLOSEOUT.json) |
| R25-DISTANCE-AUXILIARY-OVERLAP | [Manifest](auxiliary_overlap/MANIFEST.json) | [Scoped review](reviews/AUXILIARY_REVIEW.json) |

These four completed nodes concern reported-depth covariance sensitivity, deterministic bias/covariance frontiers, conditional CMB Gram geometry, and conditional auxiliary overlap. They do not promote original K03/physical-calibration acceptances or establish a native solver result, Bianchi family identification, physical Pi, or a calibrated outcome law. The auxiliary review corrects author accounting to 32.97 seconds and identifies label overlap requiring a redraw before standalone figure reuse; original artifacts remain untouched.

## Distance HOLD and unfinished branches

**Distance is not a fifth completed result.** The [actual distance review](reviews/DISTANCE_EVIDENCE_REVIEW.json) returned HOLD: 20 distinct successful fits versus at least 21 cumulative performed fits exceeded the unchanged cap of 20; the exact failed-attempt count is UNKNOWN. The [execution erratum](DISTANCE_EVIDENCE_EXECUTION_ERRATUM.md) corrects the false cumulative-compliance claim without editing the [archived candidate](distance_conditional_evidence/MANIFEST.json), granting a waiver, or rerunning fits. Numerical identities support the conditional diagnostic within explicit review limits; selected/adaptive-law and outward supremum certification remain unqualified.

The [live snapshot](provenance/snapshots/STATE_LIVE.json), captured at 2026-10-23T10:22:30.725950+00:00 after that review was recorded, has distance research READY, SMICA execute READY, and PR3 acquisition RUNNING with packet `014cb70b115b051a27cf126089c1e7f270363aa236d69320c2f777f738dca00d`. PR3 outcome is UNKNOWN while its actual agent runs; do not replay it. Normal next waits for the native outcome. The [actual acquisition dispatch](provenance/runtime_r25/FREQUENCY_ACQUISITION_DISPATCH.json) is evidence of dispatch only. The [actual mirror resume decision](reviews/FREQUENCY_MIRROR_RESUME_DECISION.json) is pending conditional transport advice for one bounded trial; product-specific parity and full qualification have not been established by that advice. Per-product qualification and scientific tensor consumption remain later decisions. Gaia pair-separation and source-property intake are reviewed planning/contracts, without acquired results or execution PASS.

## Preserved historical boundaries

The original 42-node acceptance accounting remains 17/42 primary and 18/42 alternate reporting, with unresolved original claims unchanged. R9 UNKNOWN, the frozen 48-task campaign, the [62-task baseline](provenance/snapshots/STATE_BEFORE.json), and existing one-use packet histories are preserved. The captured state contains 69 tasks; new conditional nodes do not increase the original acceptance numerator. Both consumed ultra allowances (R23-COMMON-E1 and inherited R23-Q) remain consumed. No new ultra allowance or dispatch is claimed.

Portable copies preserve actual dispatch/review receipts, bounded test outcomes and first failures. Earlier activation receipts describe their own time: manual hook exercise is not fresh-session activation. Publication, local installation, actual host execution and scientific admission remain distinct. The host alone owns live STATE; this snapshot is recovery evidence and must not be replayed as a replacement state.
