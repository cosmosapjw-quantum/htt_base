# HTT R10 — geometrical-optics extension of the R9 research campaign

Date: 2026-09-19 UTC. Work unit: `HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH_PLAN`.
Status: **SPECIFIED_FOR_LOCAL_RESEARCH**. This delivery is a plan and source review, not completed optical research, a T9 repair, four-axis admission, or new observed inference.

## Start here

1. [PLAN_KO.md](PLAN_KO.md): integrated objective, iterations, dependencies and stopping rules.
2. [SCIENTIFIC_CONTRACT.md](SCIENTIFIC_CONTRACT.md): definitions, convention issues, independent oracles and limits.
3. [campaign_dag.json](campaign_dag.json): the 24 inherited R9 nodes plus explicit optical actions; capabilities require evidence, not node completion labels.
4. [LOCAL_CODEX_HANDOFF.md](LOCAL_CODEX_HANDOFF.md): immediate local research and return instructions.
5. [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json): inspected commits, blobs and attachment bytes.
6. [PLAN_REVIEW.md](PLAN_REVIEW.md): findings incorporated and validation scope.

The attached September 7 handoff is historical context. Its PR463-only frontier and global pre-freeze Local prohibition are not the present starting point: PR466/R7, PR467/R8 and PR468/R9 already followed it. This extension is based on **R9 commit `5e4e899c0dfa2028d81a82ca68ccd11203947470`, tree `dbfcdc9abc2298534b65f50ae6a19ab0012aa999`**, containing R8 implementation parent `efc5f30666b96782f946375551f0068bb3a30f74`. The fresh metadata/source read did not find a ref under `heads/implementation/tensor-joint-r9`; that bounded check is not a claim that no local/unpublished work exists.

The user now explicitly requests research in Local Codex and publication of its plan. Local can begin source/convention work, derivations, prototype fixtures and existing R9 actions immediately. Each production mathematical component and observed method still earns its own pre-existing admission. This document does not issue a blanket empirical release or restore invalidated results.

The original 29/55-page reports, R8 `STOP_INVALID`, old 25 unresolved pools, failed history settings, CF4 quarantine, PR284 deferral and canonical T9 v4/30 ledger are preserved. **Hierarchy term `T9_shear_down` is not the canonical ledger's T9 version identifier and is not automatically PR462's ninth theorem.** These identifiers must remain separate.

## What the added work delivers

The added contribution is a usable, convention-complete factorization from local ray generators and curvature through central rays, Jacobi derivatives and radiation transport to observed Q/O, accompanied by an honest test of what the available data can identify. Its first deliverable is a synthetic end-to-end ray/temperature/STF fixture and T9 diagnosis, not another roadmap.

The optical subgraph is **not a prerequisite** for independent full-Q/O ranks, CF4/JWST calibration or DESI results. It connects only to a method that actually consumes an optical forward model or radiation-jet response. It does not reinstate the excluded general BASS matter–radiation–optics benchmark.

Imported source files are preserved verbatim under [source_addition/](source_addition/). Their Wolfram PASS and book-sign claims are author-reported: the ZIP contains no raw CAS receipts or book extracts. The new contract records what must be resolved before using them.

## Structural verification

From a complete checkout containing this commit:

```bash
python3 docs/research_program/optical_mapping_r10_20260919/validate_plan.py
python3 scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
```

The first command checks attachment integrity, exact inheritance of the R9 science graph, capability/action references, acyclicity and failure isolation. It does not run the optical equations or admit empirical science. Do not rerun old R9 mock calculations solely to complete this planning increment.
