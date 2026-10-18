# Codex continuation prompt — 그대로 복사하여 실행

```text
cosmosapjw-quantum/htt_base의 여섯 논문 연구를 계속 실행하라.
이번 continuation branch는 research/htt-sixpaper-goals-robustness-20261018 이다.
기준 ancestor는 #559의 967ef7c8f0b132ecaaba343045d333d4ebf299c1이며,
먼저 remote branch HEAD와 이후 새 PR을 확인하고 실제 최신 source를 고정하라.

최상위 goal: canonical PUBLICATION_DAG.json의 42개 노드를 각각 원래
acceptance에 맞게 완성하고, P1–P6에 대해 실제 분석·그림·원고와 근거 있는
publication readiness decision까지 진행한다. 현재14/42, 모두 NOT_READY_TO_SUBMIT다.
완료율을 높이려고 acceptance를 낮추거나 blocker를 지우지 마라.

기존 primary checkout /home/cosmosapjw/Dropbox/bianchi/htt_base에서 AGENTS.md,
docs/harness/CURRENT_CODEX_RUNTIME.md 및 다음 순서로 읽어라:
1. docs/research_program/observational_publication_20261015/CONTINUATION_20261018/README.md
2. 같은 디렉터리의 VERIFICATION.md, INDEPENDENT_REVIEW.md,
   PUBLICATION_ASSESSMENT_KO.md, EXECUTION_GOALS.json, GOAL_DAG_KO.md
3. 해당 task의 source/report/acceptance만 읽고 과거 완료 실험을 반복하지 마라.

첫 명령은 python scripts/htt_sixpaper_goal_packet.py --frontier 이다.
그다음 --task L01과 --task S02로 bounded task packet을 만든다.
L01은 P2/run_native_matched_splits.sh와 guard의 명시적 expected ref를 사용해
기존 full/HM/OE native 파일에서 fixed-window matched split stream을 실행한다.
이미 복구한 FITS를 다시 받지 마라. full RHS replay가 통과해야 split을 해석한다.
S02는 P1의 2048 coupled draws와 실제 selection/floor 민감도를 재사용하되,
물리 mapping/selected law를 확보하기 전 q_app를 physical x/Q/F/G로 바꾸지 마라.
H02는 P3 conditional calibration-radius frontier에서 실제 method별 centers와
calibration/selection 자료를 확보해 observed identified intervals로 전진하라.

각 단계에서 스스로 다음 falsifiable goal, 산출물, 완료조건을 지정하고 실행하라.
한 goal이 검증되면 frontier를 다시 계산해 다음 ready goal로 즉시 이동한다.
막힌 lane에서는 정확한 missing input과 재개조건을 남기고 다른 runnable lane을
계속한다. downstream independent preparation은 가능하지만 prerequisite가
끝나기 전 canonical completion을 기록하지 않는다. negative/null 결과도 포함한다.
P4/P5/P6는 검증된 외부 transfer/analytic response/실제 nonradial source를 써라.
solver를 구축하거나 ODE를 풀지 마라. 외부 입력 없음을 synthetic 성공으로 대체하지 마라.

Subagent-driven: parent 포함 최대4 active, fresh packet<=12000자, nested agents 금지,
경로별 단일 writer, parent sole integration/publisher. 구현 gpt-6.1-sol high,
어려운 유도·심사 gpt-6-astra xhigh를 권장한다. 저비용 보조는 gpt-6-luna medium을
쓰되 최종 과학 판단을 위임하지 마라. 실제 사용 가능한 모델/사고모드를 확인하고
requested와 observed를 구분하라. 결과별 primary verification과 fresh reviewer
한 번으로 구체 결함을 고친 뒤 다음 과학 goal로 이동하라.

선택된 파이프라인/통계량의 전체 선택 과정을 null에도 동일하게 적용하라.
동일 하늘, 중첩 창, method calibration을 독립으로 가정하지 마라.
physical unknown mass, empty/unbounded/unresolved를 보존하고 0으로 채우지 마라.
물리 p, posterior, Bianchi family identification은 실제 적격 근거가 있을 때만 쓴다.

매 실질 결과마다 code/tests/results/plots/report를 coherent branch commit으로 push하고
draft PR을 만들거나 갱신하라. main merge와 journal submission은 별도 지시 전 하지 마라.
사용자 파일과 기존 HOLD/UNKNOWN을 보존하고 새 clone/worktree를 만들지 마라.
이 세션의 RDC 월 quota가 계속 막히면 재시도/재연결로 우회하지 말고, 사용할 수 있는
다른 승인된 실행환경의 데이터/충분통계 연구를 계속하라. 실행하지 않은 것은 NOT_RUN이다.

계획이나 문서 작성만으로 턴을 끝내지 말고 실제 runnable research를 진행하라.
문맥 한계 전 최소 resume note를 남겨 같은 goal에서 이어라. 모든 허용된 노드가
완료되거나, 남은 실행 가능한 lane 전부가 실제 외부 입력/접근에 막힌 때에만
정확한 완료/미완료 목록과 다음 명령을 남겨 종료하라. HOLD 판정은 제출 승인도,
미완료 과학 노드를 완료시키는 수단도 아니다. 중간의 일상적 구현 선택마다 확인을
요청하지 말고 이미 승인된 연구·검증·push를 계속하라.
```
