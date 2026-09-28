# HTT / MES 연구 백업 — 2026-09-28

초기 Planck/MES 연구부터 이 스레드의 마지막으로 확인되는 MES 일반화 R2까지, 복구 가능한 연구 원본·증명·코드·로그·실패·검토·DAG·인계 자료를 묶었다.

**전체 대화와 모든 과거 첨부가 빠짐없이 들어 있는 완전 백업이라고 인증할 수는 없다.** 현재 대화에는 앞부분 생략이 있고, 8월 30일 초기 아카이브 자체도 누락 자료와 부분 대화 기록을 명시한다. 없는 원문을 새 요약으로 대체하지 않았다. `index/COVERAGE_AND_GAPS.json`과 초기 아카이브의 `MISSING_ITEMS.json`을 함께 읽어야 한다.

## 다운로드할 파일

네 ZIP은 각각 독립적으로 열 수 있다. 전체 확보 자료를 보존하려면 네 파일을 모두 보관한다. 각 ZIP을 같은 디렉터리에 풀어도 payload 경로는 충돌하지 않는다.

1. `HTT_MES_THREAD_BACKUP_20260928_01_RESEARCH.zip`: 중간 HTT 이론·감사·원문선정·광학 연구, 고정 커밋 R10 계획·부분 실행·반환 검토, R1/R2 원본 ZIP과 바로 읽는 내부 파일, 연구 계보와 누락 목록.
2. `HTT_MES_THREAD_BACKUP_20260928_02_EARLY_ARCHIVE.zip`: 초기 스레드 아카이브(870개 항목)와 대형 2026-09-08 감사 증거 패킷.
3. `HTT_MES_THREAD_BACKUP_20260928_03_CATALOG.zip`: 선행 문서 탐색에 사용한 portable 카탈로그 스냅샷.
4. `HTT_MES_THREAD_BACKUP_20260928_04_SOURCE_INPUTS.zip`: 현재 제공된 프로젝트 원본 첨부 20개. Rust toolchain, offline vendor, xAct, 논문·문헌 및 프로토콜 포함. 설치나 실행은 하지 않았다.

## 읽기 순서

`index/CONVERSATION_CONTEXT_AND_RESEARCH_SEQUENCE_KO.md`에서 계보와 최신 사용자 지시를 확인한다. 첫 연구 자료는 02번 ZIP의 기존 아카이브에서 시작하고, 이후 01번 ZIP의 `history/`를 날짜순으로 읽는다. R10은 `github_historical_snapshots/` 및 `github_r10_52ab95f2/`에 있다. 마지막 이론 연구는 `readable_research/MES_FRESH_OPTICAL_TENSOR_R1/`과 `readable_research/MES_GENERALIZED_TENSOR_R2/`다.

R1/R2의 original ZIP은 `mes/`에 그대로 있다. 최초 실패와 수정 전 후보도 보존한다. R2 최신 판정은 V3이며 V1 HOLD 문서를 최신 결론으로 취급하지 않는다. 이번 백업이 과거 HTT 판정이나 이후 별도 스레드의 결과를 R1/R2의 전제로 추가하지 않는다.

## 무결성과 한계

원본 파일별 SHA-256·크기와 출처는 `index/FILE_INVENTORY.json` 및 CSV에 있다. 원본 ZIP 내부 목록은 `index/ORIGINAL_ZIP_MEMBER_INDEX.jsonl.gz`, CRC 검사는 `index/ORIGINAL_ZIP_INTEGRITY.json`, R1/R2 manifest 검사는 별도 JSON에 있다. 원격 R10 74개 파일은 Git blob identity를 확인했다. 이전 고정 커밋의 동일 blob은 재사용했다. 이는 필요한 연구 경로의 스냅샷이며 전체 Git 저장소 clone이 아니다.

초기 아카이브는 원래 백업 경로의 HTTP 502 두 번 이후 Dropbox 사본에서 복구했다. 실제 252805093 bytes 및 Dropbox block content hash를 확인했다. 함께 남아 있던 과거 `.sha256`와 receipt는 526671602-byte의 다른 바이트열을 가리킨다. 이 불일치를 숨기거나 기존 receipt를 고치지 않았다.

`BACKUP_SHA256SUMS.txt`로 외부 ZIP을 확인할 수 있다. 각 ZIP 내부에는 해당 파일들의 `MANIFEST.sha256`이 있다. 검증은 저장된 바이트의 보존과 archive 무결성에 한정한다. 과학 계산·기호 검산·통계 추론·원 repository test는 재실행하지 않았다. 과거 PASS/HOLD/철회는 역사적 원문이다.

완전한 첫 메시지–마지막 메시지 원문 보존을 닫으려면 이 스레드의 전체 export와 남은 미확보 첨부가 필요하다. 이 패킷은 그 자료를 대신하는 완전 transcript가 아니다.
