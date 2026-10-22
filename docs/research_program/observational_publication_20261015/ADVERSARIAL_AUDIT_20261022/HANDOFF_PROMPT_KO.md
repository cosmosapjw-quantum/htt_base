# 복사하여 실행할 Codex 인계

```text
cosmosapjw-quantum/htt_base PR#561의 최신 원격 HEAD를 확인하라. 기존 소유자 체크아웃을 사용하고 사용자의 수정과 외장 데이터 캐시를 보존하라. AGENTS.md와 현재 runtime 정책을 읽어라. 새 clone/worktree를 만들지 말고 production writer 하나로 작업하라.

목표는 6개 논문 DAG의 모든 42개 노드를 실제 수용기준까지 진행하는 것이다. 이번 캠페인에서는 native solver 구축과 ODE/Einstein–Boltzmann 수치진화를 수행하지 않는다. 없는 자료를 만들거나 기준을 몰래 낮춰 전부 완료한 것으로 표시하지 않는다. 종료 조건은 모든 노드의 실제 완료, 또는 남은 모든 가지에 대해 구체적인 외부 입력/물리 가정이 더 이상 로컬에서 해결되지 않음이 확인된 상태다. 한 가지가 막혔다고 다른 준비된 가지를 중단하지 마라.

먼저 docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/README_KO.md, V03_SCOPE_DECISION.json, EXECUTION_PLAN.json, OBSERVATIONAL_DATA_KO.md와 OPEN_INPUTS_20261018/CONTINUATION_TASKS.json을 읽어라. python scripts/htt_open_input_packet.py로 현재 계약을 확인하라. V03 제한적 해석 하위범위 기준18/42와 원래 외부 산출물 기준17/42를 구별하라. K03는 pending이고 논문6개 모두 NOT_READY_TO_SUBMIT이다.

부모 gpt-6.1-sol/high, 물리·수학 및 별도 독립 reviewer gpt-6-astra/xhigh, 작은 metadata 작업 gpt-6-luna/medium을 요청하라. 실제 이용 불가 시 지원되는 모델로 명시적 fallback하되 관측되지 않은 backend를 꾸며 기록하지 마라. 부모 포함 최대4, nested 없음, fresh bounded context, 파일 소유권 분리와 reviewer read-only를 지켜라.

A22-03(Quaia/Gaia join), A22-04(two-redshift operator), A22-06(selected-cohort likelihood), A22-07(legacy counterpairs) 중 준비된 것을 병렬로 진행하라. A22-03 완료 후 A22-05의 고차모드·redshift별 E/B joint model을 수행하라. 중단된 이전 코드나 branch 아이디어는 legacy/LEGACY_REUSE_MAPPING.json의 blob과 함수 단위로 다시 읽고 필요한 것만 이식하라.

공개 무인증 관측자료의 자발적 다운로드는 승인되어 있다. 실제 외장 mount와 free space를 확인하고 기존 캐시/receipt를 먼저 재사용하라. 새 기본 입력은 위 감사 디렉터리의 ACQUISITION_MANIFEST.json이며 python scripts/htt_fetch_open_inputs.py --manifest docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/ACQUISITION_MANIFEST.json --data-root /mnt/extdrive/workdir/htt_open_data --fetch 로 취득할 수 있다. 제품/누적/압축해제 다운로드 용량 상한은 없다. 2TB는 한도가 아니다. disk reserve2GiB와 스트리밍 공간 검사는 유지하라. 승인된 범위의 다른 공개자료도 필요에 맞춰 source와 consumer를 정한 뒤 받아라. 유료/인증 challenge를 우회하지 마라. raw대용량은 Git 밖에 둬라.

17/42를 다시 반복하지 않도록 각 작업 시작 때 (1)새로 달라지는 입력/모형/통계량 (2)기대 과학적 산출물 (3)반례/실패 기준 (4)다음 소비자를 명시하라. 기존651행 projection,97LP,Gaia1614173행 stream,SDSS64fits,PR4split ratio,54history/432optics를 변화 없이 반복하지 마라. 다운로드 hash나 회의용 문서만으로 science node를 완료하지 마라.

two-redshift passive observer reboost와 fixed-data reference-frame inference를 분리하라. 실제 SALT2 magnitude의 bolometric equivariance를 가정하지 말고 correction defect를 계산/제한하라. V03 optical history와 V02 Planck response를 자동 연결하지 마라. Gaia observer acceleration을 congruence A_a로 치환하지 마라. Quaia 상대 선택 지도를 절대 inclusion probability로 쓰지 마라. 동일 sky/source/calibrator의 중첩 공분산을 유지하고 selection·PV를 이중계산하지 마라. 미정의 질량/부호/분모와 미확인 물리 remainder를 보존하라.

각 coherent result를 실제 코드·재생 가능한 결과·그림·방법 보고서까지 완성하고, 의미 있는 검증과 별도 독립 검토 후 targeted repair 한 번으로 닫아라. 새 입력이나 구체적인 반례가 없으면 통과한 검증을 반복하지 마라. 과학적 변화와 남은 정확한 blocker를 기록하고 즉시 다음 ready action/node로 이동하라. 대화 길이 제한에서는 durable checkpoint와 다음 명령을 저장해 재개하라. main merge나 journal submission 없이 결과를 비강제 push하고 현재 PR/별도 draft PR에 공개하라. 목표는 원래 MES·signed functional·SMICA morphology·local/global intuition을 source-qualified 결과로 발전시키는 것이며, 결과가 robust null 또는 부분식별이어도 정확히 보고하라.
```
