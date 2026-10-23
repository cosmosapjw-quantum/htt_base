# SMICA 이후 solver-free 연구 체크포인트

소유자: R25 캠페인 호스트. 기준 시각: **2026-10-23T12:43:22.801814+00:00**. 이 문서는 실제 기록을 정리한 출판 준비물이다. 이번 검토 범위는 패키징과 주장 표현이며, 새로운 과학적 승인이나 캠페인 완료를 뜻하지 않는다.

## 완료된 조건부 연구 다섯 개

| 연구 노드 | 정확한 후보 manifest | 실제 독립 검토 |
|---|---|---|
| R25-K03-DEPTH-COVROBUST | [depth_covariance/MANIFEST.json](depth_covariance/MANIFEST.json), `bee5babe4f0610df53656beb2fd6dc69a99028d5d91e2e847e30be320ab61e9e` | [COVARIANCE_REVIEW.json](reviews/COVARIANCE_REVIEW.json) |
| R25-K03-DEPTH-BIAS-FRONTIER | [depth_bias/MANIFEST.json](depth_bias/MANIFEST.json), `04af80ce33b2258e434da7f13d3d168f906026cd92c0f7fe7ef9d9586e2db692` | [BIAS_REVIEW.json](reviews/BIAS_REVIEW.json) |
| R25-CMB-CONDITIONAL-GRAM | [cmb_conditional_gram/MANIFEST.json](cmb_conditional_gram/MANIFEST.json), `62d064cb9675453a2eca81e4c5b581f3afabaf83d3831c7399493d976fbd5845` | [CMB_REVIEW_CLOSEOUT.json](reviews/CMB_REVIEW_CLOSEOUT.json) |
| R25-DISTANCE-AUXILIARY-OVERLAP | [auxiliary_overlap/MANIFEST.json](auxiliary_overlap/MANIFEST.json), `c40f04af7296ab6ad8ea0adfb3b93fb981d87f3e3b83b35e5d14f78dc04063f5` | [AUXILIARY_REVIEW.json](reviews/AUXILIARY_REVIEW.json) |
| R25-SMICA-SPECTRAL-NULLSPACE | [smica_spectral_nullspace/MANIFEST.json](smica_spectral_nullspace/MANIFEST.json), `d89b6c381c6987ac5051b77bcd053aa5a835764718e196735c5434fc94eaace9` | [SMICA_SPECTRAL_TARGETED_CLOSEOUT.json](reviews/SMICA_SPECTRAL_TARGETED_CLOSEOUT.json) |

앞선 네 노드는 보고된 깊이 공분산 민감도, 결정론적 bias/covariance frontier, 조건부 CMB Gram 기하, auxiliary overlap을 다룬다. 새 다섯 번째 SMICA 노드는 실제 공개 가중치의 고정 선형 압축에 대한 정보 손실 감사다. 4개 E2/E3/B2/B3 연산자마다 28개 표적, 총112개 표적과 정확한 증인4개를 확인했고 전체24×168 연산자의 rank24/nullity144와144개 독립 kernel 방향을 유지한다. 이는 물리적 foreground 크기, 실제 하늘의 잡음 법칙, native atlas 또는 Bianchi family 식별 결과가 아니다.

SMICA 첫 검토는 수치 성분을 통과시켰지만 REPORT의 최소 pair-loss 설명을 HOLD했다. 저장된 올바른 값은 E2/E3 약0.7479, B2/B3 약0.8169이며 모두30–143GHz contrast다. 이후 두 숫자와 관련 manifest/return만 고친 후보 `d89b6c381c6987ac5051b77bcd053aa5a835764718e196735c5434fc94eaace9`가 [실제 targeted closeout](reviews/SMICA_SPECTRAL_TARGETED_CLOSEOUT.json)을 받았고 호스트가 그 결과를 기록했다. 생산/수치 테스트 재실행은0이다. 원래 RETURN의 PENDING 및 첫 HOLD는 당시 상태로 보존되며, 현재 완료 근거는 이후 closeout과 실제 history 기록이다. 원래 생산23.122195초·테스트4.414711초 및 독립 검토의 기존 검증을 재사용했다.

## Distance: 원래 HOLD와 별도 유한 라이브러리 결과

원래 distance 실행은 성공한 서로 다른20개 null fit에 실패 실행에서 수행한 최소1개가 더해져 **누적≥21, 고정 cap20 초과**다. 정확한 실패 실행 횟수/원래 실패 소스는 UNKNOWN이다. [기존 erratum](DISTANCE_EVIDENCE_EXECUTION_ERRATUM.md)과 [실제 blocker research](reviews/DISTANCE_EXECUTION_BLOCKER_RESEARCH.json)는 이 사실을 유지한다. 0-fit 작업이나 설명 수정으로 과거 실행을 취소할 수 없으므로 원래 acceptance는 HOLD다. 숫자가 과학적으로 거짓이라는 판정은 아니다.

[별도 독립 유한 산술 검토](reviews/DISTANCE_FINITE_LIBRARY_REVIEW.json)는 저장된8개 component와5개 고정 fold denominator에 한해서 다음을 증명한다. 각 fold에서 비음수 합1 가중치의 혼합비는 component 최대값 이하이고, 그 최대값은8배의 정확히 재구성한 equal mixture 이하이다. 고정1/5 fold 평균에서도 성립한다. 임의의 fold별 convex 재가중치에 대한 tight maximum의 인증 구간은 **[0.0006872371499359424075546278173516995795, 0.0006872371499359424075546278173516995796]**, 따라서0.001보다 작다. 같은 component library와 고정 denominator/평균만 재가중해1에 도달하는 경로는 닫힌다.

이 인증은 archived binary64 log scalar를 정확한 유리수로 해석한 유한 pointwise 산술이다. 저장된 fitted log-density/denominator의 정확도, optimizer 인증, selected-source law, null domination 또는 e-validity를 인증하지 않는다. held-out 자료에 의존한 가중치도 점별 부등식은 만족하지만, 그것만으로 normalized training-only density나 유효한 e-value가 되지 않는다. full tensor/covariance carrier는 기존 sealed RESULT에 남는다. four-axis CAS 또는 더 넓은 물리적 결론도 아니다. [독립 proof/script/raw](provenance/POST_SMICA_CHECKPOINT/evidence/r25_blind_distance_envelope/REVIEW.md)는 원본 바이트로 동봉했고 재계산하지 않았다.

## 현재 상태와 다음 실행

실제 canonical STATE를 한 번 읽은 2026-10-23T12:43:22.801814+00:00 기준으로 총69개 controller task는 completed 40, held 8, ready 20, checkpointed 1다. 이40 completed를 원래42-node 과학 acceptance와 혼동하지 않는다. 원래17/42, alternate18/42, R9 UNKNOWN, frozen48 task 및62-task baseline, one-use history와 consumed ultra는 그대로다. baseline62 task object와 frozen campaign/ultra는 실제 값 비교로 동일함을 확인했다.

PR3 all-seven acquisition은 원래 packet `014cb70b115b051a27cf126089c1e7f270363aa236d69320c2f777f738dca00d`의 비종결 checkpointed 상태다. source 승인과 실제 resume는 다르다. 원래 agent의 durable reservation → 실제 WAIT-only followup → ACK 저장 → sealed grant 뒤에만 재개한다. 143/353 full-size partial의 실제 FITS 검증과217 잔여 전송은 아직 실행 완료/독립 qualification으로 표시하지 않는다. 현행 max2 scheduling에서는143 검증과217 전송이 겹칠 수 있고353 검증은 다음 slot을 쓴다. 기존 completed 입력은 다시 다운로드하지 않는다.

Gaia pair-separation, source-property intake와 staged30/44/70/100 native tensor contrast는 검토된 준비 계약이며, 이 기준 시각에는 대응하는 실행 task/candidate가 없다. staged4의96차원 carrier·6개 full24 contrast와4개 product qualification은 실제 구현/실행/독립 검토가 남아 있다. 계약 검토는 raw product의 최종 qualification이나 production 결과가 아니다.

실제 진행 중인 read-only discovery: `c5dbca4ecf557e3675a623eb4b2de4218122b67f1a40422e73dd9c36de862466` (running, agent /root/discovery_c5dbca4ecf557e36). 준비된 독립 branch를 다음 실행으로 내리는 작업이며, 완료 결과로 세지 않는다.

## 검토된 소스와 저장 위치

[Cooperative controller closeout](reviews/COOPERATIVE_CONTROLLER_SOURCE_CLOSEOUT.json), [manifest/review freshness closeout](reviews/REVIEW_FRESHNESS_SOURCE_CLOSEOUT_14C88.json), [future helper closeout](reviews/COOPERATIVE_HELPER_SOURCE_FINAL_04FD.json)은 각각 해당 정확한 소스 범위의 PASS다. 최종 controller SHA는 `d682f64d9aefba6251dc75037588669c0d193fc1ac12bf348bdfc02094cb46e5`, frontier test SHA는 `592370decfb33e36e1e49f8ca82df012d59075d9614abbe98c89a8a2457369f4`다. 독립 검토 requested profile은 gpt-6-astra/xhigh이며 observed runtime은 UNKNOWN으로 유지한다. 기존 published plan/theorem/progress 문서는 수정하지 않았다.

ENOSPC 이후 canonical STATE alias는 외장 저장소의 `/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/LIVE_STATE.json`을 가리키는 symlink다. 호스트는 alias를 보존하도록 `rc.save(canonical.resolve(), s)`를 사용한다. [active-pointer 조정](provenance/POST_SMICA_CHECKPOINT/evidence/storage_reconciliation/ACTIVE_POINTER_RECONCILIATION.json)과 [독립 검토](provenance/POST_SMICA_CHECKPOINT/evidence/storage_reconciliation/ACTIVE_POINTER_BLIND_REVIEW.json)는 실제 campaign binding과 startup advisory의 resolved-path 제한 ValueError를 설명한다. 즉시 hook 수정이나 전역 activation 완료를 주장하지 않는다. 이 패키지에는 live STATE/active pointer를 복사하지 않았다.

[정확한 출판 allowlist](provenance/POST_SMICA_CHECKPOINT/GIT_ADD_ALLOWLIST.txt)와 [원본→휴대용 복사본 hash map](provenance/POST_SMICA_CHECKPOINT/ARTIFACT_MAP.json)이 이번 검토/복구의 소비 대상이다. unrelated CAS, runtime/state, bulk data, cache와 미검토 Gaia numerical output은 제외한다. 동봉한 raw 실패/패치의 공백과 당시 PENDING/HOLD는 원본대로 유지한다. 소스 출판, 설치/활성화, 실제 native 실행, 조건부 node 완료 및 원래 scientific admission은 각각 별도 단계다.
