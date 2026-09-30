# Independent review — GR/statistics publication and local CAS handoff

Date: 2026-09-30. Reviewer task: `/root/publication_handoff_review`.

**Decision: ACCEPT_FOR_DOCUMENT_PUBLICATION. No unresolved blocking finding in the bounded scope.**

This reviewer did not author the publication or CAS contracts. The review covers source preservation, repository-state changes, execution-contract fidelity and claim boundaries. It is not a new proof review, CAS run, Lean build, scientific promotion, peer review, or native local-harness lifecycle admission. Actual hosted model identity was not observed and is UNKNOWN. No repository source was changed by this reviewer; only this report was written.

## Evidence boundary and baseline

- Repository: `cosmosapjw-quantum/htt_base`.
- Remote baseline commit: `bc45fb9292a4cfb095d7b61d4e5c02a32fb39c5c`.
- Remote baseline tree: `a7c81846ef711396ce4bd51de6b4653bef834c0c`.
- Canonical baseline DAG blob: `34b3403899dd0eba0703f1c20fa9c8f7041452e4`.
- Canonical baseline status blob: `771c215c69be909d9f20121278cd823be6c65368`.
- Original research archive SHA-256: `f8a8785bea496bffd07d387e5ab5c23fbd0943c06526abaae6dda18d5aa5ee9d`.
- Inspected current `cas_gate.py` SHA-256: `fcaaa08083221fa69ff22066d6fb9f769913bd774b15628dbf684544c69f0744`.

Baseline materialization initially contained one extra trailing LF in each canonical YAML. Removing exactly that trailing byte yielded the remote Git blob identities above. The implementer corrected these baseline files; final comparison used byte-authenticated remote baselines. This was a materialization discrepancy, not a scientific or repository-state change.

## Checks and findings

1. **Original preservation:** independently compared all 39 ZIP entries with the destination files: 39/39 byte-identical. The 39 source-map rows have matching size, SHA-256 and Git blob hashes; the archive hash also matches. No PDFs, extracted full texts, images, databases or compressed runtime payloads were copied into the new package.
2. **Repository semantics:** parsed baseline/candidate DAG and status. Existing nodes, dependencies and status values are unchanged. The only additions are `PR-GR-STATISTICS-CAS-HANDOFF`, its topological/strict-extension list entries, its completion entry and its document-only execution resolution. Existing completion ordering is preserved. Canonical/YAML mirrors are byte-identical; backlog JSON is semantically identical. Root README adds only the new research entry paragraph/heading. Actual independent command `python3 -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` exited 0 and reported `OK: 213 PRs, DAG valid`.
3. **CAS coverage:** 17 schema-v2 contracts contain 61 explicitly named component obligations; every obligation has a matching component definition. All 46 original claim IDs are mapped, with TEFF-H2 held in CAS-18 and no fake executable contract. Six book checks are separately mapped. Source-binding and execution-index contract hashes match actual candidate files.
4. **Bounded scope:** contract components preserve explicit conventions, singular/branch conditions and controls. Every contract explicitly states that component success is not full-theorem success and retains the larger analytical obligations. Prepared local-environment seals are not represented as already observed toolchains. TOV local existence, continuum entropy inequalities, coverage laws, observation availability and novelty are not silently closed by polynomial checks. The neutral TEFF interval specification supplies mathematical source statements, not historical CAS answers.
5. **Actual runner compatibility:** inspected the existing runner source and tested only its pure `_required_axes` and `_contract_obligations` functions against the 17 contracts. These structural checks accepted the canonical four axes and all 61 obligation IDs. No preflight, `run-adjudicate`, scientific engine or proof assistant was executed. Handoff `RUN_SPEC` and payload instructions match schema version 1, exact axis keys, distinct argv arrays, repo-relative existing cwd, positive timeout, no shell key, one JSON payload, exact boolean check coverage, `domain_assumption_diff` and `counterexample`. Stored-envelope inspection is explicitly excluded as execution authority.
6. **Independence and claim boundaries:** fresh-context axis authors receive only contracts/neutral inputs; historical scripts, proof texts, previous verdicts and sibling results are excluded. Actual xAct/Singular use and faithful Lean theorem statements/axioms must be evidenced locally. Same-LLM correlation must be disclosed. Publication carries no CAS_PASS, formal-proof, observed-data or Bianchi-identification promotion. TEFF manuscript usage does not reinstate legacy TSC ownership.
7. **Local safety:** the handoff uses the existing owner checkout, records status/HEAD/origin first, preserves dirty/untracked work, forbids automatic reset/clean/stash and new clone/worktree, and permits fast-forward integration only when safe. It separates mathematical, numerical, implementation, runtime/license/resource and missing-input failures. No destructive command or credential disclosure is requested.

### Corrected review finding H1

The initial `EXECUTION_INDEX.json` listed CAS-17 before its dependency CAS-07. This was an execution-order inconsistency, not a mathematical error. The implementer replaced the order with a stable topological ordering. The reviewer rechecked the final list: all dependency sets precede their tasks. **H1 is resolved.**

The final CAS-08 contract explicitly permits rank-deficient nuisance F via the pseudoinverse projector. CAS-16 now supplies an explicit finite grid and underresolution controls. These clarifications were inspected after the final ready notification. The return schema requires exactly four axis objects. Draft-2020-12 meta-schema validation was not run by this reviewer; JSON parsing and relevant structural constraints were checked. This limitation is not represented as successful schema-library validation.

## Limits and next action

The publication commit and remote ref have not yet been observed by this reviewer; the publisher must attach actual post-write identity evidence. This report is scoped publication review and does not attest a local registered reviewer lifecycle. The next substantive action is local four-axis environment sealing followed by independent implementation and runner-observed execution of the bounded contracts. Any newly found source error must be preserved as a correction with a counterexample; the 39 historical originals must remain unchanged.

## Reviewed candidate identities

These hashes bind this review to the publication/handoff snapshot. They do not replace mathematical validation.

| Path | SHA-256 |
|---|---|
| `README.md` | `8c3f65ae417a3d3e17b7d015b48113fcb268ec55550181a1939e8e43c608b6b0` |
| `docs/PR_DELTAS/pr-gr-statistics-research-cas-handoff.md` | `7ea178d8d3380cff60883ba7227680671ce9629914f0fbec4e104e8436fce9bb` |
| `docs/codex_handoff/pr_backlog.yaml` | `b204c187a5b5f54e157f85994a0b13cbdc79d2193344e8789dba1edd9c78f3d7` |
| `docs/codex_handoff/pr_status.yaml` | `0a85e06dafa9bce4052f71886f70fb518f0a3bffbb46494f5399eefb00c9d77a` |
| `machine_readable/pr_backlog.yaml` | `b204c187a5b5f54e157f85994a0b13cbdc79d2193344e8789dba1edd9c78f3d7` |
| `machine_readable/pr_backlog.json` | `59984daa6eacf0d0cdec5bd9dd20b4e0d1777e64c3dc571287846f1667ca87ac` |
| `machine_readable/pr_status.yaml` | `0a85e06dafa9bce4052f71886f70fb518f0a3bffbb46494f5399eefb00c9d77a` |
| `docs/research_program/gr_statistics_loops_20260930/REPOSITORY_INTEGRATION_KO.md` | `c4aba9ab3b9c04485e735a4ac977b7b800a4162d59524d95f25849960eb96a89` |
| `docs/research_program/gr_statistics_loops_20260930/LOCAL_CODEX_PROMPT_KO.md` | `b10757e01ece38ee787fa4bb69534f460ba1631e9a3cf7ab4e8d70a72718db65` |
| `docs/research_program/gr_statistics_loops_20260930/LOCAL_CODEX_RETURN_PROMPT_KO.md` | `24e1a662db5030bdafb29317d78270e3647d01ba4a48e1654f2850bedd5c2fb5` |
| `docs/research_program/gr_statistics_loops_20260930/LOCAL_CODEX_RETURN_SCHEMA.json` | `963228aeaeb52f9bdc9d369512e43b7bb84ff5a31c57a4829d511b3f85a84f5b` |
| `docs/research_program/gr_statistics_loops_20260930/publication/SOURCE_TO_REPO.json` | `4b33596f5db7ed5a799f0b337377bfbebecd0573ef88ce7388b7559e1d4403b8` |
| `docs/research_program/gr_statistics_loops_20260930/cas/CAS_TASKS.json` | `b5655092cc859b0a9aa410984aa3c82249b476696fcccffb95d94ff7a0bed511` |
| `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` |
| `docs/research_program/gr_statistics_loops_20260930/cas/EXECUTION_INDEX.json` | `9565395c677b23b01202f0f37e460e658bf636a684e7801f1c5bc28e75da7321` |
| `docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md` | `bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-01.json` | `9f1bbb018e211b4d50c50532b57cf708acffdd6a01f06a24f5cb8cbb21709b57` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-02.json` | `71283a74d0fc4a0f632e13b7361c407bdddaf9fa4486044dd30a64cb68b057a3` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-03.json` | `e12189010d0da32212c45a3371001058da368a086527945a121e03a74f6526c1` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-04.json` | `139c4b5bce3069b3f8e265f3fcf7f74992be6fc6b1b535d68d2bf9cdcce40895` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-05.json` | `424bc10c2ef40c1d718d35fddc21e54d0c7e50d265b9485967b2feb4577fc197` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-06.json` | `5b1ec8f1fa8d033039d21678b685ae76a630547cf3dfd679333cef5ea7b59ced` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-07.json` | `f95739683fefa13b40cf29e20d0b6aa0f3449663fc769834cda2cd8959eda808` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-08.json` | `3a89149e4e025298b35e5db550142c5b25351dc5aef5ee1071f29977030f8d3e` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-09.json` | `4913de308fc006f3658a45a88cd1d8400b1aaf3d1249927e677cca74842e4a3b` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-10.json` | `03dd5c3c8e3d8c30cf75058b48138a5208ac5f664a51533fb5d945ffee06f43f` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-11.json` | `6588ac42ca6724e58b2f673b0ee2c3234b7a3a6ab1df35a6d1f942c03f860025` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-12.json` | `5a6827166fe318e37ac9e503a91d6f729155cbef48f450cd9daf0896e47fa6ae` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-13.json` | `4e8bdb6c3d0c789e8dc7fbb647a982849ac13653bcabe41820c41be0c360b89b` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-14.json` | `bbf1f726083ec577016a3fe73223c669b83fd52aa30e303bbaa7c6094237c15d` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-15.json` | `eccc10a3f5105970a46a73412d8c82a27a1e82a6116013bc0abc6656816f8eee` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-16.json` | `c8c5c20c2d470a53dcf79dc8c3504e7a59874fed88a48917b8547755b37486cb` |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-17.json` | `123c73d56cf1c4d85acfce8536161011d4cb42b91f93e7bc0e3e67780296877e` |
