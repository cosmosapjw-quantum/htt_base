# HTT/MES 원격 현황 및 선별 source inventory

관찰 완료 UTC: 2026-09-28T04:38:48.278921+00:00. GitHub connector GET만 사용했다. 원격 변경, 새 checkout/worktree, 과학 코드/CAS 실행은 없다. 이 보고서는 외부 ChatGPT analytic/source-subset 조사이며 canonical local harness나 production admission이 아니다.

## 현재 identity와 조사 범위

- 저장소 `cosmosapjw-quantum/htt_base`, 기본 브랜치 `main`.
- main commit `cc162c804eecb3c588efc6edadbe057a8a67301f`; 실제 tree `f14a536e7934d99bbe67489d1b81e5da0079cb09`.
- commit 시각 `2026-09-28T02:50:14Z`; 메시지 `MES-R1-R5-20260927: Integrate tensor optical handoff`.
- 전체 원격 브랜치 **195개**: 페이지당 100개, 실제 반환 100+95개. `REMOTE_BRANCHES.json`에 이름과 tip SHA를 전수 저장했다.
- main 재귀 tree **10,153 entries / 8,710 blobs**, `truncated=false`.
- catalog 재귀 tree **9,886 entries / 8,500 blobs**, `truncated=false`.
- R10 네 branch의 재귀 tree도 모두 `truncated=false`; 각 head의 전체 파일 metadata를 확보했다.
- branch 이름/identity 전수조사와 source 전문 정독은 다르다. 모든 195 branch의 모든 본문을 읽은 것이 아니다.
- 본문 취득 **56개, 56개 모두 Git blob SHA-1 일치**. `REMOTE_SOURCE_ACQUISITION.json`에 commit/ref, path, blob, SHA256, byte size와 local path를 보존했다.

## 코드·이론 DB는 현재 하나의 catalog에 통합돼 있다

명시 catalog/database 이름의 현재 branch는 `implementation/project-catalog-20260912` 하나다. 해당 tip `870bd67af159993ccde4ede9923424a475c01375`는 main의 ancestor이며 main보다 7 commits 뒤다. 실제 tree는 `415d789446e836b97e8a8f64343450c170237b2f`이다.

다음 subtree/content는 catalog branch와 main에서 같은 Git identity다.

| 경로 | Git identity |
|---|---|
| docs/project_catalog | 26e431627183cdef3ec4baf65cc8fea31b167ed3 |
| docs/project_catalog/database | 0192e4141772b3416137b0e782f68ac207138bce |
| docs/project_catalog/proofs | bd2c9bb8edd73365dc9210bb5466c683378b1152 |
| docs/project_catalog/lists | dcc5fa0a7dca38e353413b916372ddb73e24aef4 |
| scripts/catalog_lib | 6d6ce80b022b4cc948f740c6be4eb95cb09e2f81 |
| scripts/project_catalog.py | 810ec4534691620b221b29bf34b7408128c838e2 |

즉 main에 catalog가 포함돼 있어도 최신 R1–R5 통합까지 재색인됐다는 뜻이 아니다. README가 명시하는 기본 query baseline은 R8 `efc5f30666b96782f946375551f0068bb3a30f74`, 전체 조사 source는 99개이며 frozen 통계는 1,675,716 records다. code와 proposition은 같은 DB의 kind별 query다. 별도 이름의 이론 DB branch가 있다는 가설은 현재 195 refs의 이름과 이 catalog 구조에서 확인되지 않았다. 이름과 맞지 않는 별도 DB의 절대 부재를 주장하지 않는다.

DB 배포는 57개 조각, 압축 **2,352,689,771 bytes**, 복원 **10,820,591,616 bytes**다. manifest의 database SHA256은 `42942d7485d4650075b0ec6baa2059d8b8e715bea9c3d59d772c301854d20e25`이다. 이 metadata는 취득했지만 큰 DB 원본은 다운로드/복원하지 않았다. 따라서 이번 원격 조사에서 지울 DB 원본은 생기지 않았다. 원격 원본 삭제는 수행하지 않았다.

조회 경로는 `scripts/project_catalog.py query/show/history/export`, SQLite schema는 `scripts/catalog_lib/db.py`, read query는 `scripts/catalog_lib/query.py`, 배포복원은 `scripts/catalog_lib/package.py`, 직접 SQL은 `docs/project_catalog/queries.sql`이다. 이들은 모두 전문 확보했다. 첫 기본 CLI query는 DB를 자동 복원하므로 이번 선별조사에서는 실행하지 않았다.

기존 proof export의 345 confirmed / 39,937 unconfirmed는 **기존 근거 대조의 항목 묶음**이다. 독립 정리 수나 이번 재증명/실행 수가 아니다. proof-role research proposals와 auxiliary propositions, 172개 proposal synthesis index 안내를 이용해 DB 없이 후보를 좁힐 수 있다.

## main의 최신 delta

catalog tip 대비 main blob diff는 **추가210 / 변경20 / 삭제0**이다. `REMOTE_MAIN_VS_CATALOG_DELTA.json`은 두 완전 tree의 path/blob 비교다. 최신 핵심은 `docs/research/mes_r1_r5_integration_20260927/` 8개 통합문서, R1–R5 incoming 원문, MES R7 conditional source-image 구현, R9 D2 상태 및 정책 갱신이다.

R1–R5 통합 상태는 `DOCUMENTED_WITH_ORIGINAL_CONDITIONS`; 이번 integration의 구현 검증은 `NOT_RUN_THIS_INTEGRATION`, empirical admission은 `HOLD_NOT_RUN`이다. R1/R2 exact shear positivity/residual inverse를 R5 신규 finite-boost/source 후보의 HOLD 때문에 일괄 철회하지 않는다. R5 appendix와 R1/R2의 normalization 차이를 정리한 exact shear 재사용을 보존한다.

가장 최근 RETURN_HANDOFF는 하나의 b-free target 또는 calibrated shear target에서 R1/R2 exact weak law와 R5 retained adapter의 source/frame/remainder 대응을 좁히고 실제 budget 하나를 확보하도록 지시한다. historical broad exact-radiation 재유도를 새 work unit으로 반복하지 않는다.

현재 코드의 선택 전문을 취득했다. `nuisance_rank.py`와 `r9_confidence_image.py`는 재사용 가능한 projection/common-event 부품이다. `conditional_source_image.py`는 BOX4 시나리오이며 R5 physical joint disk와 다르다. `mes_theorem_authority.py`, `three_bound_hierarchy.py`, `planck_mes_bounds.py`의 존재는 exact R1–R5 residual operator 구현의 증거가 아니다. coefficient/source 논쟁은 현 integration의 CONFLICT를 유지한다. 이 조사는 테스트를 실행하지 않았다.

**문서 freshness 충돌:** README는 R9 다음 단일 과제를 D2 singular Gaussian support로 표기하지만 canonical `docs/research_program/tensor_joint_r9/RESEARCH_STATE.json`의 현재 상태는 `R9_REV2_D2_SUPPORT_BRIDGE_COMPILED_FULL_DEPTH_BLOCKED`이며 2026-09-22 D2 support/actual-moment/HCHᵀ/off-support/Dirac Host Lean compilation을 보존한다. D2를 새 미실행 과제로 반복하면 안 된다. four-axis admission, D4/full FORMAL_DEPTH와 physical/empirical HOLD는 여전히 별도다. 이번에 원문 기록을 읽었으며 Lean 재실행은 없다.

## main 밖 science branch

analysis/docs/handoff/implementation/research prefix의 **29개** tip commit/date/message와 main ancestry를 확인했다. **10 behind / 19 diverged**다. old history/rewrite divergence의 ahead count는 main에 없는 새로운 과학 결과 수가 아니다. GitHub compare의 file 목록은 300개 제한 가능성이 있으므로 전체 diff 완전성을 주장하지 않는다. R10은 별도의 완전 recursive tree를 확보하여 본문 선별에 사용했다.

| Branch | Tip UTC date | main 대비 | 앞/뒤 commits |
|---|---|---|---|
| `analysis/mes-methodology-recovery-20260825` | 2026-08-25T07:44:58Z | diverged | 360/215 |
| `analysis/mes-methodology-stack-integration-20260826` | 2026-08-26T00:15:56Z | diverged | 377/215 |
| `analysis/planck-mes-extended-data-execution-20260826` | 2026-08-27T16:39:56Z | diverged | 427/215 |
| `analysis/planck-mes-observable-irrep-execution-20260827` | 2026-08-26T17:55:18Z | diverged | 402/215 |
| `analysis/planck-mes-wu011-processed-local-boost-response-20260902` | 2026-09-01T17:06:43Z | diverged | 509/215 |
| `analysis/pr408-wu001-registered-survivor-triage-20260903` | 2026-09-03T13:58:51Z | diverged | 393/215 |
| `analysis/theory-promotion-audit-20260824` | 2026-08-24T12:42:09Z | diverged | 353/215 |
| `docs/htt-pedagogical-render-20260907-r1` | 2026-09-07T06:06:57Z | behind | 0/56 |
| `docs/htt-report-a-pedagogical-20260907-r1` | 2026-09-07T05:24:53Z | behind | 0/59 |
| `docs/htt-report-a-r3-render-20260907-r1` | 2026-09-07T03:58:07Z | diverged | 2/70 |
| `docs/htt-tensorized-mes-response-synthesis-20260903` | 2026-09-07T03:25:22Z | behind | 0/69 |
| `handoff/htt-lowell-postreview-20260907-r1` | 2026-09-07T10:27:55Z | behind | 0/49 |
| `implementation/htt-authority-citation-reconciliation-20260905-r1` | 2026-09-05T13:36:20Z | diverged | 3/78 |
| `implementation/htt-t2-token-assertion-repair-20260905-r1` | 2026-09-06T00:13:08Z | diverged | 4/78 |
| `implementation/project-catalog-20260912` | 2026-09-16T05:05:54Z | behind | 0/7 |
| `implementation/tensor-joint-r7-20260908` | 2026-09-08T15:40:56Z | behind | 0/39 |
| `implementation/tensor-joint-r8-20260909` | 2026-09-12T10:45:22Z | behind | 0/31 |
| `research/htt-optical-mapping-r10-20260919-r1` | 2026-09-19T18:35:40Z | diverged | 2/31 |
| `research/htt-postreview-theory-first-20260907-r1` | 2026-09-07T08:34:05Z | diverged | 8/56 |
| `research/htt-referee-seeded-program-20260907-r1` | 2026-09-07T09:37:59Z | behind | 0/50 |
| `research/htt-review-seeded-theory-plan-20260907-r1` | 2026-09-07T09:57:47Z | diverged | 6/56 |
| `research/pr04-multicomponent` | 2026-08-20T15:13:16Z | diverged | 254/215 |
| `research/r10-checkpoint-continuation-20260919-r1` | 2026-09-19T21:33:18Z | diverged | 5/31 |
| `research/r10-optical-mapping-local-20260920` | 2026-09-21T02:29:19Z | diverged | 9/31 |
| `research/r10-return-review-48e77f8d-r1` | 2026-09-19T23:35:33Z | diverged | 7/31 |
| `research/tensor-joint-r7-design-20260908` | 2026-09-08T11:24:39Z | behind | 0/48 |
| `research/tensor-joint-r8-design-20260908` | 2026-09-08T16:25:11Z | behind | 0/38 |
| `research/tensor-joint-r9-design-20260912` | 2026-09-12T17:12:13Z | diverged | 1/31 |
| `research/wu011-task7c-external-verifiers-20260903` | 2026-09-02T19:03:42Z | diverged | 593/215 |

R10 optical/local/continuation/review 네 갈래는 R8에서 분기했고 아직 main ancestry에 병합되지 않았다. 최신 local tip `0ce1d755...`의 2026-09-21 followup을 별도 source prefix로 취득했다. R10의 optical source가 현재 main 경로에서 안 보인다고 과거 연구가 없다고 판정하면 안 된다.

그 최신 R10 반환은 RC03 shear-ray / RC07 결과를 재사용하고 ambient-gradient `-(m+4)`와 tangent-gradient `-4` 동치를 명시한다. 저장된 finite test는 P1=x의 ell3 upper harmonic에서 올바른 -5와 잘못된 -6을 분리한다. 이것은 general-ell four-axis 증명이 아니다. full/packed와 mixed negative 계약은 `DRAFT_NOT_FROZEN_NOT_ELIGIBLE`; 네 CAS 축은 모두 NOT_EXECUTED, positive T9 consumer eligibility false다. mixed rank-loss obstruction을 부호 전체 반전만으로 수리하거나 positive admission으로 바꾸지 않는다.

R10의 과거 local client/registration blocker는 해당 실행의 증거다. 이번 외부 ChatGPT analytic 작업의 runtime failure 또는 불가능 판정으로 승계하지 않는다.

## 이번 선별 결과 파일

| 파일 | 내용 |
|---|---|
| REMOTE_MAIN_FILE_INVENTORY.csv | 현재 main 8,710 blobs의 path/size/blob identity 전수 |
| REMOTE_MAIN_CODE_LIST.csv | extension 기준 code/formal 후보 2,336개 |
| REMOTE_MAIN_THEORY_EVIDENCE_CANDIDATES.csv | 문서·구조화 evidence 후보 5,188개; 이론/증명으로 자동 분류하지 않음 |
| REMOTE_SELECTED_DEEP_READ_LIST.csv | 이번 후속 target에 관련된 취득 전문 목록, source identity, 용도 |
| REMOTE_SCIENCE_BRANCH_TRIAGE.json / csv | 29 science heads의 commit metadata와 ancestry |
| REMOTE_R10_BRANCH_DIFFS.json | R10 각 complete tree와 main의 path/blob 차이 |
| REMOTE_SOURCE_ACQUISITION.json | 선택 56개 전문의 byte/Git blob 검증 |

Claim 상태는 current metadata inventory와 source-byte recovery에 대해 implementation-verified 수준의 검증을 제공하지만 과학적 validity/implementation PASS로 전이하지 않는다. remote mutation 0, full clone/worktree 0, large database restore 0. 추가 감사를 반복할 필요 없이 이 source 목록에서 선택된 다음 국소 이론 유도로 진행할 수 있다.
