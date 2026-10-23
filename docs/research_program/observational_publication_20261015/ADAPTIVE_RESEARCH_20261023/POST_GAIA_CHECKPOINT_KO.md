# Gaia 이후 조건부 연구 체크포인트 — 게시 후보

실제 커밋·푸시·scientific admission 또는 캠페인 완료를 뜻하지 않는 조립 후보이다. 기준 커밋은 `d93605e66adfececa89b90681124b232a5f90220`이다. 조립 담당 요청은 gpt-6.1-sol/medium, 관측 런타임은 UNKNOWN이다.

## 실제 상태

읽기 시각 `2026-10-23T14:15:56.898030+00:00`: 총 74개 작업, {"completed": 42, "held": 8, "ready": 22, "checkpointed": 1, "running": 1}. canonical STATE는 `/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/LIVE_STATE.json`로 연결되며 읽은 바이트 SHA256은 `ebd21e3515bd54fabd5512d28343cdc3bee0d0850ba625a64005b0594bf5bad6`이다. 라이브 STATE는 게시하지 않는다. 보조 controller 작업 수와 원래42개 과학적 수용 기준은 다르다.

완료된 R25 작업은 기존 K03 covariance, depth-bias, CMB conditional Gram, auxiliary-overlap, SMICA 다섯 노드와 새 Gaia pair 및 metadata intake 두 작업이다. 원래17/42, 대안18/42, 과거48, one-use/소진된 ultra 기록, R9 UNKNOWN은 유지된다. 거리 실행의20-fit cap 초과(최소21회, 정확한 실패 시도 수 UNKNOWN) HOLD는 별도 finite-library bound 검증과 구분하여 유지한다.

## 독립 리뷰를 통과한 이번 결과

[Gaia pair 보고서](gaia_pair_separation/REPORT.md), [실제 독립 리뷰](provenance/POST_GAIA_CHECKPOINT/gaia_pair_blind_review/RETURN.json): semantic candidate `sha256:0baef3b6b3fe45f459c1eb2476fbaa67ff47e4e824456ad7c67843da622c67c7`. MANIFEST 바이트 SHA256 `441df34cae65acac1157e01809148a0a2d1010a51335a1a6d5e67bc7897e0d69`는 별도 식별자이다. 원본 pending-review 문구는 당시 기록으로 보존하고 최종 scoped 판단은 별도 리뷰 영수증으로 제공한다.

4756개 선택 소스의11,307,390개 각도쌍에 대한 조건부 진단이며, 전체 벡터/STF와 공동 covariance,117개 carrier 모드와88개 projection 모드를 유지한다. 리뷰 수치는 T_E1=87.00260228836888, T_full13=75.07862294730027, Delta=11.923979341068602이다. full-model tail은 TAIL_UNRESOLVED, projected-mean ball은 수치근사만 허용된다. 실제 cross-source covariance와 선택법칙은 미보정이며 물리적 검출이나 유한 coefficient confidence region을 주장하지 않는다. 원래7명령43.16초와 실제 리뷰3.84초를 합해47.00초/300초를 사용했다. [raw carrier·첫 실패·타이머](provenance/POST_GAIA_CHECKPOINT/gaia_pair_execution_raw/)를 보존했고 재계산하지 않았다.

[메타데이터 보고서](gaia_source_properties/REPORT.md), [독립 입력 qualification](provenance/POST_GAIA_CHECKPOINT/gaia_properties_blind_review/RETURN.json): semantic candidate `sha256:005aa5cf96fe1350ef7690a275edd4ae61e9b30092266e8900c8b3d86b482568`, MANIFEST 바이트 SHA256 `005aa5cf96fe1350ef7690a275edd4ae61e9b30092266e8900c8b3d86b482568`. exact4756-ID left join과 원본 VOTable/wire masks 검증으로 `gaia_source_properties` 입력만 qualified됐다. AGN3216 대 wire-null1540은 AGN/non-AGN이나 가변/비가변 구분이 아니다. host1–2 노출0으로 기존 host1–2 versus3는 ZERO_EXPOSURE_SUPPORT/NOT_EVALUABLE이다. 원본 author-stage pending 문구는 그대로 보존한다. [실제 host record adapter](provenance/POST_GAIA_CHECKPOINT/host_receipts/GAIA_PROPERTIES_REVIEW_RECORD_ADAPTER.json)는 successor_blocker를 controller success enum으로 번역하면서 downstream blocker와 과학적 판단을 유지한다.

## 추가됐지만 아직 실행되지 않은 질문

[실제 append 영수증](provenance/POST_GAIA_CHECKPOINT/host_receipts/GAIA_TWO_FRONTIERS_ACTUALLY_APPENDED.json)의 두 작업은 이 시점 READY/execute이며 실행 history가 없다.

- [Source quotient INPUT](provenance/POST_GAIA_CHECKPOINT/r25_gaia_source_quotient_proposal/INPUT.json): H*=H[I−B(BᵀB)⁻¹Bᵀ]의 source law, complete FULL13/E1 image와 엄밀한 조건부 경계 의무. [독립 계약 리뷰](provenance/POST_GAIA_CHECKPOINT/r25_blind_source_quotient_contract/REVIEW.md)는 prospective contract만 승인한다. 원래 Gaia pair의300초 누적 cap을 공유하며 이후 실제 리뷰 비용을 반영해야 한다. 새 pairpass/old fit replay/ultra는 없다.
- [Release-tag association INPUT](provenance/POST_GAIA_CHECKPOINT/r25_gaia_tag_association_proposal/INPUT.json): literalAGN 대 wire-null FULL13 angular mean-field contrast. [METHOD](provenance/POST_GAIA_CHECKPOINT/r25_gaia_property_method/METHOD.md)와 [독립 수치기준](provenance/POST_GAIA_CHECKPOINT/r25_blind_tag_association_contract/REVIEW.md)을 보존한다. M0 32열/M1 80열 두 관측 fit만 허용되는 새로운 tag observable이며 별도300초 누적 질문이다. M1-only rank/support HOLD는 eligibleM0를 막지 않는다. 실제 support/rank/계수 결과는 아직 없다.

S4는 독립 리뷰 진행 중이므로 완료/승인 결과로 포함하지 않고 후보 출력도 이번 allowlist에서 제외한다. all-seven acquisition은 checkpointed이며 완료/재개를 주장하지 않는다. [FULL7 prospective review](reviews/FULL7_PROSPECTIVE_CONTRACT_REVIEW.md)는 두 계약 수정이 필요한 설계 리뷰로서 실행 승인/full7 결과가 아니다. 원본 초안은 상속되고 여기서 수정/실행하지 않았다.

## 게시 경로와 한계

[ARTIFACT_MAP](provenance/POST_GAIA_CHECKPOINT/ARTIFACT_MAP.json)은 원본 절대 경로→게시 경로, SHA256/크기/mode를 연결한다. 고정 manifest/receipt/계약 바이트와 내부 경로를 재작성하지 않고 이 map으로 해석한다. `arrays.npz` 로컬 symlink는 실제 외부 target의8601430바이트/SHA256 `d391a5c49b9205229717d1bc9c900e180be4bea8440023bb52b2517352e8ffe5`를 regular100644 파일로 복사했다. 절대 symlink 문자열을 게시하지 않는다. 원본 raw carrier와 첫 실패는 보존한다. 대용량 Planck/FITS 지도, liveSTATE/runtime 전체, .git, 캐시, unrelatedCAS, S4 pending 결과와 미래 Gaia 수치출력은 제외한다.

새 numerical run/query/download/Git 변경은 없다. exact bundle 독립 리뷰와 명시적 게시 승인 이후에만 실제 publication을 진행한다. 소스 게시·로컬 활성화·과학적 승인은 별개다. 캠페인은 계속된다.
