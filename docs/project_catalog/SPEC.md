# PR-CATALOG-001 — 전체 이력 정적 카탈로그

Owner: COMMON. Scope: repository navigation; non-claim-bearing static inventory.
Base: efc5f30666b96782f946375551f0068bb3a30f74 (R8).

사용자가 승인한 전체 Git 이력·연결 자산의 정적 조사를 SQLite, CLI,
한국어 길잡이로 제공한다. 연구 코드·분석·증명 도구를 import/실행하지 않는다.
기존 상태 원문과 이번 정적 조사 상태를 분리하고, 코드 존재·실행 기록·증명
근거·과학적 admission을 혼합하지 않는다. 테스트 대상은 카탈로그 도구뿐이다.

## Acceptance

- AC1: 이력/경로/아카이브/스텁/상충 상태/증분 갱신의 카탈로그 전용 테스트.
- AC2: 모든 선언된 자료의 처리 상태, SQLite integrity, 분모가 있는 coverage.
- AC3: 대표 query/show/history/export와 버전·출처·근거·후속 조치 연결.
- AC4: 압축 DB 배포, non-force push, 새 원격 체크아웃의 복원·조회.

읽을 수 없거나 정적으로 결정할 수 없는 항목은 누락 목록에 남긴다.
문서에 쓰인 ACTIVE/PASS/PROVEN을 이번 작업의 검증 결과로 승격하지 않는다.
미커밋/외부 원문은 이동·수정·추가 커밋하지 않는다.
