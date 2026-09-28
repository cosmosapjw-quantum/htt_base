# Start Here — GPT-6 Astra v4.0.0

1. `docs/MODEL_ROUTING.md`에서 모델과 연구/코딩 루프를 확인한다.
2. `PROJECT_INSTRUCTIONS.md`와 `state/RESEARCH_STATE.md`를 읽는다.
3. 현재 목표·원래 동기·scope·완료기준·가용 source/tool·이미 승인된 행동을 짧게 기록한다.
4. `prompts/00_integrated_work_run.md` 또는 필요한 quick prompt를 사용한다.
5. 필요한 phase와 정책만 읽고 승인된 목표를 끝까지 진행한다.
6. 실제 증거·실패·결정 포인터와 `state/CLOSEOUT.md`를 갱신한다.

`python3 tools/validate_workspace.py`는 패키지 구조를 검사한다. 포함된 state는 미실행 템플릿이고 이전 연구 결과가 아니다.

`.agents/skills/`는 원본 보존 참고자료다. 호스트가 이를 읽더라도 국소 skill의 stop은 해당 phase 종료를 뜻한다. 이 패키지로 개인 skill 설치나 호스트 설정 변경이 수행되지는 않는다. 실행 계약과 상위 지시가 기존 승인 범위에서 전체 작업의 연속 수행을 정한다.
