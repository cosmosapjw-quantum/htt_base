# 조사 범위와 누락

기준 비교 버전: `htt_base:efc5f30666b96782f946375551f0068bb3a30f74`.

아래 수치는 카탈로그 레코드/버전/위치의 수다. 독립 구현 수나 증명된 명제 수를 뜻하지 않는다.

| 구분 | 수 |
|---|---:|
| 현재 HTT Git 커밋 | 2,005 |
| 이력 정리 이전 커밋 | 839 |
| 구·신 커밋 대응 | 839 |
| 등록 작업트리 | 94 |
| 의존성·외부 저장소 포함 커밋 기록 | 79,880 |
| 서로 다른 커밋 객체 | 79,844 |
| 추출된 파일 버전과 자산 항목 | 305,527 |
| 서로 다른 본문 바이트 | 72,785 |
| 기준 버전 추적 파일 | 7,255 |
| 물리 파일 위치 | 526,503 |
| 물리 정규 파일 inode | 526,498 |
| 기존 코드 버전에 연결된 물리 별칭 | 431,485 |
| 의미별 레코드 | 1,675,716 |
| 참조/호출/대체 관계 | 10,901,211 |
| 별도 사유가 있는 처리 항목 | 268 |

## 파일 처리 상태

| 상태 | 수 |
|---|---:|
| `agent_context_cache_metadata_only` | 164 |
| `archive_link_metadata` | 247 |
| `archive_members_enumerated` | 400 |
| `git_symlink` | 7 |
| `lexical_partial` | 29,271 |
| `metadata_only` | 137,029 |
| `oversized_archive` | 3 |
| `oversized_text` | 104 |
| `parse_error` | 620 |
| `parsed` | 136,461 |
| `pdf_text_partial` | 1,221 |

## 레코드 종류

| 상태 | 수 |
|---|---:|
| `analysis` | 10,304 |
| `annotation` | 16,462 |
| `code` | 1,170,314 |
| `document` | 215,320 |
| `evidence` | 20,297 |
| `feature` | 93,766 |
| `file` | 45,481 |
| `plan` | 53,953 |
| `port` | 6,085 |
| `proposition` | 27,122 |
| `update` | 16,612 |

## 기준 R8 레코드

| 상태 | 수 |
|---|---:|
| `analysis` | 356 |
| `annotation` | 117 |
| `code` | 28,534 |
| `document` | 17,370 |
| `evidence` | 941 |
| `feature` | 2,257 |
| `file` | 2,398 |
| `plan` | 932 |
| `port` | 281 |
| `proposition` | 1,875 |
| `update` | 17 |

## 누락·제한 사유

| 상태 | 수 |
|---|---:|
| `archive_error` | 1 |
| `missing_source` | 20 |
| `non_commit_ref` | 8 |
| `oversized_archive` | 3 |
| `oversized_text` | 77 |
| `parse_error` | 159 |

## 관계 해석 상태

| 상태 | 수 |
|---|---:|
| `ambiguous` | 470 |
| `baseline_source_file_present` | 25 |
| `recorded_relation_unresolved` | 759 |
| `same_file_symbol_candidate` | 1,107,688 |
| `same_version_file_present` | 1,020,328 |
| `same_version_import_candidate` | 66,208 |
| `static_call_unresolved` | 7,261,606 |
| `unresolved` | 24 |
| `unresolved_at_source_version` | 1,444,103 |

## 출처별 범위

| 출처 | 종류 | Git 커밋 기록 | 경로 |
|---|---|---:|---|
| `e2e_assets` | filesystem | 0 | `/mnt/sn850x2t/htt_base_e2e` |
| `external_0d181b3e152b` | git_dependency_metadata | 59,475 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/mathlib` |
| `external_24f86cad1972` | git_dependency_metadata | 165 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/Cli` |
| `external_4728f04483c3` | git | 1 | `/mnt/sn850x2t/htt_base_e2e/workdir/external_fusion_round3_20260722_envs/sources/concept-1.0.1` |
| `external_4a23497a75c3` | git_dependency_metadata | 12,632 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/batteries` |
| `external_51e5b7987dca` | git | 51 | `/mnt/sn850x2t/htt_base_e2e/workdir/external_fusion_round3_20260722_envs/sources/nanoCMB` |
| `external_72c7259f1ea8` | git_dependency_metadata | 591 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/proofwidgets` |
| `external_7a66cf5597f3` | git_dependency_metadata | 86 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/LeanSearchClient` |
| `external_83976a0a36b7` | git_dependency_metadata | 199 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/plausible` |
| `external_849fffd5fe91` | git_dependency_metadata | 421 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/Qq` |
| `external_94568b0ed629` | git_dependency_metadata | 380 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/importGraph` |
| `external_b325ef8edc49` | git | 1,074 | `/mnt/sn850x2t/htt_base_e2e/workdir/obs_bundle/spt3g_y1_v11_obs01/official_runtime/clik_16.0b1` |
| `external_bf0463fa645e` | git_dependency_metadata | 1,926 | `/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/aesop` |
| `external_fff8a5f83550` | git | 35 | `/mnt/sn850x2t/htt_base_e2e/workdir/obs_bundle/spt3g_y1_v11_obs01/official_code/spt3g_y1_dist` |
| `htt_base` | git | 2,005 | `/home/cosmosapjw/Dropbox/bianchi/htt_base` |
| `htt_pre_rewrite` | git | 839 | `/mnt/sn850x2t/htt_rewrite_20260717/git_dir_pre_rewrite` |
| `main_overlay` | filesystem | 0 | `/home/cosmosapjw/Dropbox/bianchi/htt_base` |
| `navigation_annotations` | curated_navigation | 0 | `docs/project_catalog/curation.json` |
| `worktree_055ec7dc9a7f` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-local-global-pr256-20260729` |
| `worktree_05b8b0c24142` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-irrep-intake-20260828` |
| `worktree_0731b5b58c2d` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr298-repository-integrity-20260820` |
| `worktree_1094015090d1` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-premise-anchor-20260728` |
| `worktree_15ff10c500ba` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr287-functional-spine-r2-20260809` |
| `worktree_169b080c6100` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr328-mes-local-global-identifiability-20260831` |
| `worktree_1800beb5c619` | filesystem | 0 | `/tmp/htt-pr408-survivor-closeout-repair-20260825` |
| `worktree_1ae4fe94faab` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr292-spin2-preactivation-20260809` |
| `worktree_281073cfc25f` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-wu007-smica999-20260829` |
| `worktree_283f5d972a39` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-wu006-admission-20260829` |
| `worktree_28e882c107e5` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr273-20260730` |
| `worktree_2ea4366743fc` | filesystem | 0 | `/tmp/htt-pr312-cf4-superseding-repair-20260823` |
| `worktree_361c956cd10f` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-mes-integration-20260826` |
| `worktree_38a33bd0f10b` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-theory-promotion-audit-20260824` |
| `worktree_39233dc87e58` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-coordinate-audit-20260828` |
| `worktree_39818a17b22a` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-process-inflation-recovery-pr283-20260810` |
| `worktree_4069f86d2d69` | filesystem | 0 | `/tmp/htt-pr310-hsc-kids-closure-20260824` |
| `worktree_44f38a89c1b1` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr259-20260730` |
| `worktree_4bd4d3025035` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr274-20260730` |
| `worktree_51981e1c214d` | filesystem | 0 | `/tmp/htt-pr308-act-closure-20260823` |
| `worktree_5b924dcd38af` | filesystem | 0 | `/tmp/htt-pr320-hsc-kids-cross-covariance-20260825` |
| `worktree_5dbe65a8458c` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr280-main-20260804` |
| `worktree_5e52aea10a82` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr287-functional-spine-20260809` |
| `worktree_5ed17ce8b96a` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-low-ell-pr257-20260729` |
| `worktree_6288e4908eae` | filesystem | 0 | `/tmp/htt-pr311-desi-successor-closure-20260824` |
| `worktree_659457793992` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-hard-cap-assurance-20260820` |
| `worktree_6cf762054c7c` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr267-20260730` |
| `worktree_713f030c1e15` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr281-orbit-type-acceptance-20260809` |
| `worktree_739311744d4d` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr279-retrace-20260804` |
| `worktree_78efc3c9b8ec` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr268-20260730` |
| `worktree_7c3326359486` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-paired300-evidence-repair-v2-20260829` |
| `worktree_7cace60301ec` | filesystem | 0 | `/tmp/htt-pr317-desi-existing-data-analysis-20260825` |
| `worktree_80ca6260a9b2` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-wu009-full-replay-local-20260830` |
| `worktree_84aacaf650b3` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr269-20260730` |
| `worktree_86c6cea97c6e` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-anchored-response-pr255-20260729` |
| `worktree_896705f4ee70` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr272-20260730` |
| `worktree_89a8d0d54d5c` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-mes-bound-current-research-report-20260829` |
| `worktree_8bb663063a75` | filesystem | 0 | `/tmp/htt-pr307-cf4-closure-20260823` |
| `worktree_8ea04aaaaa69` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-lowell-e-sector-20260830` |
| `worktree_8ea4ea9988a2` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr285-pillar-t-20260809` |
| `worktree_94361ec1f523` | filesystem | 0 | `/tmp/htt-pr305-trusted-launcher-transaction-preprovisioning-20260822` |
| `worktree_99662c0f61f0` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-post-pr275-20260802` |
| `worktree_9a3e92b3401a` | filesystem | 0 | `/tmp/htt-pr309-jwst-sn-closure-20260823` |
| `worktree_9a943b482122` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr295-external-boundary-20260808` |
| `worktree_9aede208107f` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-irrep-extended-data-execution-20260829` |
| `worktree_9e751497c3a9` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr290-preactivation-after-pr289-20260809` |
| `worktree_9f85d399a9b8` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-irrep-global-20260827` |
| `worktree_a3b167c99875` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr270-20260730` |
| `worktree_a4682674dd2a` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr292-spin2-preactivation-r2-20260809` |
| `worktree_a9a1bc391a8f` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-mes-scalar-methods-referee-r3-20260830` |
| `worktree_aa85e02acf2a` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr277-capability-engine-20260803` |
| `worktree_abf39ba2e124` | filesystem | 0 | `/tmp/htt-observational-acquisition-20260825` |
| `worktree_b09cbeb361e4` | filesystem | 0 | `/tmp/htt-pr314-planck-pr3-analysis-20260824` |
| `worktree_b30ecf95f2f5` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-premise-anchor-pr254-20260728` |
| `worktree_b4610845f730` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr280-hermetic-20260804` |
| `worktree_b4a67836a5d0` | filesystem | 0 | `/tmp/htt-pr304-admission-bound-human-authorization-20260822` |
| `worktree_b65ac85f54d2` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr286-pillar-s-20260809` |
| `worktree_bb48ffef366b` | filesystem | 0 | `/tmp/htt-pr319-jwst-2mrs-neural-field-20260825` |
| `worktree_bc64c729f281` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr278-tier-a-adjudication-20260804` |
| `worktree_bdc18aabe36c` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-observable-irrep-analysis-20260829` |
| `worktree_c17d04a561af` | filesystem | 0 | `/tmp/htt-pr321-hsc-sacc-fast-analysis-20260825` |
| `worktree_c411d660d283` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr291-preactivation-after-pr290-20260809` |
| `worktree_c6d08d5f45d9` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr288-bayesian-semantics-20260809` |
| `worktree_c70e037c141e` | filesystem | 0 | `/tmp/htt-pr310-lane-registry-compat-20260824` |
| `worktree_c8449ff0412e` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr284-depth-path-20260809` |
| `worktree_ca343c0927cb` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr283-weak-identification-20260809` |
| `worktree_cfbc6afb1907` | filesystem | 0 | `/tmp/htt-pr318-desi-input-preparation-20260825` |
| `worktree_d2baaf6aa364` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-stat-foundations-20260727` |
| `worktree_d55a751d9dc4` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-post-pr275-pr276-20260803` |
| `worktree_d7189d65500e` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr289-data-identity-v2-20260809` |
| `worktree_daffeb871d19` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr151-portable-resume-20260808` |
| `worktree_e31f69724c49` | filesystem | 0 | `/tmp/htt-pr406-theory-hardening-20260825` |
| `worktree_e36a15fe0b82` | filesystem | 0 | `/tmp/htt-pr313-cf4-status-provenance-closeout-20260823` |
| `worktree_e5b47df7352f` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr266-20260730` |
| `worktree_e95949b9cbbc` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr282-exact-parity-readiness-20260809` |
| `worktree_ea7e3a059257` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-vector-tensor-pr271-20260730` |
| `worktree_ed11f782a1b0` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-planck-mes-latest-irrep-report-20260829` |
| `worktree_ed162a01fe76` | filesystem | 0 | `/tmp/htt-pr306-planck-operator-closure-20260822` |
| `worktree_ef96fa837cc2` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr285-after-pr284-20260809` |
| `worktree_f402858c3ec2` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-open-set-pr258-20260730` |
| `worktree_f66c80200412` | filesystem | 0 | `/home/cosmosapjw/worktrees/htt-pr280-content-review-20260804` |

## 분모와 처리 한계

- Git 이력은 선언된 로컬 객체에서 조사했다. 설치된 일반 Lean 의존성은 커밋·참조·버전 정보이며 내부 구현을 HTT 코드/명제로 세지 않는다.
- 아카이브 내부 경로는 `archive.zip!/member`로 표시한다. 제한·암호화·손상·구문 오류는 원문을 수정하지 않고 남긴다.
- 텍스트 상한 8,388,608 bytes, 아카이브 상한 2,147,483,648 bytes, 중첩 깊이 4이다. 상한 초과는 파일 존재 목록에 남는다.
- PDF는 텍스트만 추출했다. 도형·수식의 정확성, OCR, 렌더링은 검수하지 않았다.
- Python 외 언어는 선언 중심 lexical 추출이다. 매크로·주석·복잡한 스코프의 해석 한계가 있으며 컴파일 성공을 의미하지 않는다.
- 미커밋 자료는 조사 시점의 원문과 메타데이터다. 재수집 때 변할 수 있으며 원문은 이 배포에 복사하지 않는다.
- 파일 수집 완료율과 명제 의미 해석의 완전성은 다르다. 선언을 추출하지 못한 파일도 상태와 경로로 찾을 수 있다.
- 생성 카탈로그와 캐시를 다시 읽지 않도록 이번 카탈로그 작업 디렉터리를 제외했다. 도구 자체 소스는 배포 Git 브랜치에서 확인한다.
- 오래된 소스의 실제 구문 오류·누락 참조는 원문 상태로 보존했다. 이 카탈로그 작업에서 연구 코드를 고치거나 재실행하지 않았다.

전체 사유는 `coverage_gaps.csv`, 모든 물리 위치는 DB `filesystem`, 파일 버전은 `files`에서 조회한다.
