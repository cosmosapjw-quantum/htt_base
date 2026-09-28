# State directory

미실행 연구 상태 템플릿이다. 공통 core와 `RESEARCH_STATE.md`에서 시작하고 필요한 ledger·증거만 추가로 읽는다. 중요한 계산·결정·최초 실패·tool boundary·중단 위험에 현재 상태를 저장한다.

장황한 작업 내역 대신 active assumptions, 현재 scope, claim 상태, blocker, 다음 최소 행동과 원본 증거 포인터를 유지한다. 원 로그와 실패 기록은 별도로 보존한다. `tools/init_workspace.py`는 템플릿의 프로젝트명·날짜를 채우며 기존 파일을 기본 보존한다.
