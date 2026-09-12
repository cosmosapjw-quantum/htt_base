# PR-CATALOG-001 — 전체 이력·기능·분석·명제 검색 카탈로그

Owner: COMMON. Scope: user-requested static project navigation, non-claim-bearing.
Base: R8 `efc5f30666b96782f946375551f0068bb3a30f74`.

## 문제와 결과

수많은 버전·작업트리·연결 자산에 분산된 구현과 설계, 분석, 명제와 저장된 근거를
한 곳에서 찾기 어려웠다. 전체 선언 이력과 정적 자료를 SQLite로 연결하고,
`scripts/project_catalog.py`의 scan/query/show/history/export/check 및 복원 경로와
[한국어 길잡이](../project_catalog/README.md)를 추가했다.

원문 상태, 정적 선언·호출 후보, 저장된 실행 기록, 증명 주장과 참조 파일 존재를
구분한다. 같은 명제 ID라도 버전·가정·소스가 다르면 합치지 않는다. 과거 파일이나
제안 상태만으로 현재 실행 가능성, 증명 완료, 이식 완료를 판정하지 않는다.

## 구현

- Git 객체·경로·버전, 작업트리 별칭과 미커밋 자료, 아카이브 내부 항목을 수집.
- Python AST, 기타 언어의 선언, registry/prose/노트북/PDF 텍스트를 정적 추출.
- 출처·파일·심볼·기능·분석·명제·계획·이식 언급·업데이트·누락을 SQLite와 FTS로 연결.
- 기본 R8, 기본 원격 브랜치, 다른 브랜치·커밋과 전체 버전을 분리 조회.
- 내용 캐시를 이용한 증분 수집과 별도 DB의 전체 재생성, 대량 CSV/JSON 스트리밍 출력.
- 40 MiB 이하 gzip 조각과 manifest로 DB를 배포하고 원본 없이 복원·조회.

## 검토와 검증

[작업 기록](../project_catalog/EXECUTION.md), [DB 검사](../project_catalog/checks.json),
[독립 검토와 수정](../project_catalog/REVIEW.md)에 실제 결과를 보존한다.
카탈로그 테스트 27개 및 DAG 195개 구조 검증이 통과했다.

독립 검토의 5개 결함을 수정했다. 특히 Git clean filter가 실행될 수 있는 diff 기반
감지를 제거했다. 추가로 중복 선언 보존과, 증분 수집에서 길잡이의 명시적 버전
연결을 유지하는 fixture를 확인했다. 원래 검토 FAIL은 그대로 보존한다.

연구 코드·연구 테스트 수집·분석·증명 도구는 실행하지 않았다. 외부 API 의미론에
의존하는 변경은 없으며 소스와 설치 도구를 조사했다. 원격 기본 브랜치는 Git으로
조회했다. 새로운 과학적 claim tier, native solver 검증, MIO posterior 또는 family
identification 판정은 생성하지 않는다.

## 한계와 전달

Lexical 추출, PDF 텍스트, 기록에만 남은 상태에는 해석 한계가 있다. 사라진 임시
작업트리와 읽기·파싱·크기 제한은 [범위 문서](../project_catalog/COVERAGE.md)에
남긴다. 파일 존재와 참조의 버전 대응이 증명 타당성을 대신하지 않는다.
기존 원본 체크아웃의 73개 변경 항목을 보존했으며 이 PR에는 사용자 원문이나
외부 원자료를 별도 payload로 추가하지 않는다.

원격 게시·독립 체크아웃 복원 확인이 끝나면 DAG에서 이 사용자 요청 PR만 완료한다.
