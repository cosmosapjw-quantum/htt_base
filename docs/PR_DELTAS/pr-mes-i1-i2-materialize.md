# PR-MES-I1-I2-MATERIALIZE — I1·I2 원문 Git 등록

2026-09-28. Owner HTT. 사용자 지정 파일 통합 과제이며 선행 `PR-MES-FULL-HANDOFF`가 완료된 뒤 수행했다. 시작 `main`/`origin/main`은 `18bf3e09a677730280481917211ac1149178cae5`, tree `0a132de06c561459ee691274e7f2ca334d56ef8e`였다. 원격을 fetch했고 기존 사용자 변경을 보존했다.

로컬 전체 ZIP과 그 안의 I1/I2 체크포인트 크기·SHA-256을 확인했다. ZIP CRC와 안전한 경로·일반 파일·중복 여부를 검사했다. I1 683개, I2 19개를 각각 지정된 `I1/`, `I2/`에 원본 바이트 그대로 추출하고 702행의 size/SHA-256/Git blob ID 매핑을 기록했다. 원문은 수정하지 않았다. `git check-ignore`가 지정 702개 중 제외한 파일은 0개였고, 지정 경로만 스테이징했다. 702개 index blob과 원본 계산 blob이 모두 같다.

README, 원본 archive/I3 검증 문서, canonical DAG/status 및 mirror에 읽기 경로를 연결했다. I2의 과거 I3 프롬프트와 현재 등록된 I3 결과를 구분했다. 검증 범위는 checkout 파일과 Git 객체·상대 링크·DAG다. 과학 계산·Wolfram·일반 finite tilt 검증 재실행과 과학 판정 승격은 `NO`다. I2 `DEFENDED_CONDITIONAL`, I3 `HOLD_INPUT_INCOMPLETE`, R9 등 기존 HOLD를 유지한다.

검증: 원본 702개 대비 worktree size/SHA-256, staged 및 commit tree blob ID, 작성 링크, DAG/status mirror, targeted DAG harness, `git diff --check`, fast-forward 게시 후 remote commit/tree와 선택 blob ID를 확인한다. 실패와 게시 식별자는 [통합 보고서](../research_program/mes_verified_checkpoints_20260928/integration/INTEGRATION_REPORT_KO.md) 및 [반환 인계](../research_program/mes_verified_checkpoints_20260928/RETURN_HANDOFF_KO.md)에 기록한다. 영향 범위 밖 scientific full suite는 실행하지 않는다.

Host 자체 검토: (1) 원본 ZIP과 경로 안전성, (2) 원문 변경·필터 적용에 따른 blob 이탈, (3) 기존 변경·production 파일 충돌, (4) 조건부 과학 문구, (5) 새 링크·mirror 유지보수를 점검한다. 실제 예외가 없으면 추가 검토 루프를 만들지 않는다.
