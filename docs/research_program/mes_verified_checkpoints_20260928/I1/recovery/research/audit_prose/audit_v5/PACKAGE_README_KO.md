# HTT 전 이력 독립 감사 R5

2026-09-08. R4의 후속 정적 감사다. 전체 전수 정독 완료본이 아니다.

- 새 고유 전문 읽기 52개, 누적 265개. 전 이력 고유 blob 목록 18,885개.
- 과학 코드, CAS, 모의실험, 관측자료 분석을 실행하지 않았다.
- 저장된 수치는 원본 JSON의 과거 산출값이며 이번 재실행 값이 아니다.
- 원저장소와 업로드 원본을 수정하지 않았다.

읽을 순서:

1. `outputs/HTT_MES_AND_OBSERVED_LINEAGE_AUDIT_R5_KO_20260908.pdf`
2. `audit_v5/FINDINGS_R5.csv` - 판정과 적용 범위
3. `audit_v5/coverage.json`, `read_ledger_increment.json`, `read_ledger_cumulative.json`
4. `audit_v5/HISTORICAL_READING_STATUS.csv` - 전 이력 내용별 FULL / PARTIAL_OR_DELTA / UNREAD
5. `audit_v5/sources/` - 새로 읽은 Git blob 보존본과 lane별 receipt
6. `prior/HTT_HISTORY_AND_SUCCESSOR_AUDIT_R4_20260908.zip` - 이전 보고서·census·근거 보존본

`report-source.md`는 PDF의 원문이다. `SOURCE_INDEX.csv`는 이번 읽기 58행의 path, ref, Git blob, local cache, read level을 연결한다. 부분 읽기 2행과 이전 전문 읽기 4개는 신규 전문 읽기 수에 포함하지 않는다. 중간 FETCH_BATCH 파일은 증거 집계에 쓰지 않으며 최종 패키지에서 제외한다.

원장 중 과거 cache 상대경로는 R4 및 그 안에 보존된 압축 checkpoint에서 이어진다. 같은 내용을 여러 경로·브랜치·검토자가 읽어도 고유 blob은 한 번만 센다. 목록이나 해시 검사만 수행한 파일은 정독으로 계산하지 않았다. 목록에는 binary도 포함되며, Git 밖의 원자료와 외부 관측 실행 directory는 별도다.

정적 독립 검토는 MIO·MES와 DESI·JWST 두 경로에서 수행했다. 주 심사자는 근거를 합성하고 중요 반례·호출 경계를 교차 확인했다. 읽은 테스트 코드를 실행한 것으로 보고하지 않았다. `INDEPENDENT_REVIEW_NOTES_KO.md`는 검토 범위와 교정사항을 기록한다.

후속 우선순위는 (a) 미독 역사적 BASS·MIO·obsstat와 오래된 JSON·보고서의 정독, (b) 관측 결과의 producer·실제 입력 연결, (c) MES 물리 response 및 공동 null·likelihood의 이론적 완결이다. 이번 좁은 수리 계약은 전체 THEORY_FREEZE를 대신하지 않는다.
