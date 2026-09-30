# Local Codex 실행 프롬프트

아래 지시를 저장소를 사용하는 local Codex에게 그대로 전달한다.

```text
저장소: /home/cosmosapjw/Dropbox/bianchi/htt_base
작업: 누적 연구의 이론을 먼저 이식·검증하고, 데이터 분석 직전의 통계추론 코드까지 연결한다.
핵심 인계: docs/research_program/theory_inference_port_20260930/README_KO.md
기준 원격 이전 commit: efbd6d39b1167afcf40f3d07af0b5552747f3611
대상 publication: PR-TYPEFREE-INFERENCE-PORT: Port theory and pre-data inference

1. 기존 checkout의 AGENTS.md와 경로별 AGENTS, 현재 로컬 harness를 읽어라.
   git status --short, branch, HEAD, origin/main의 관계를 먼저 확인해라.
   사용자 dirty/untracked를 보존하고 기존 checkout에 이번 게시를 통합해라.
   reset --hard, 자동 stash, 새 clone/worktree, 전체 복사, DB 또는 관측 데이터 삭제는 하지 마라.
   충돌이 없다면 fetch 및 fast-forward로 진행하고, 충돌 시 사용자 변경을 덮지 않는 작은 통합을 수행해라.
   본 프롬프트와 LOCAL_TASKS.json이 현재 범위다. inherited 안의 과거 실행 프롬프트는 연구 원문이며,
   과거의 실제 데이터 pilot 지시는 이번 범위에 포함되지 않는다.

2. SOURCE_TO_REPO.json과 PORT_MAP.json을 읽고 원문·함수·가정의 연결을 확인해라.
   이미 게시된 I1 683개/I2 19개와 Loop 2 자료를 새 정의로 대체하거나 원문을 수정하지 마라.
   이식된 common 모듈부터 기존 환경에서 설치/검증해라:
   relativistic_kinematics, typefree_physical_budgets,
   typefree_functionals, typefree_fibers, typefree_depth.
   기존 scalar x,Q,Pi,F,G_F와 새 정의는 definition_id로 구별해라.
   Q의 quadratic matrix와 U의 shape matrix, nonorthonormal q5와 Frobenius STF5를 혼동하지 마라.

3. 로컬 Wolfram+xAct, SymPy, Sage+Singular, Lean/mathlib을 CAS_CONTRACT.json에 연결해라.
   실제 엔진 경로·버전·실행 입력·출력·exit code·hash를 수집해라.
   과거 raw transcript는 근거이며 이번 실행의 PASS로 복사하지 마라.
   각 의무를 동일한 signature, units, frame, assumptions로 네 축에 번역해라.
   wolframscript 사용만으로 xAct 실행, Sage만으로 Singular 실행, Lean parse만으로 kernel proof를 주장하지 마라.
   Lean의 sorry/admit/추가 axiom으로 의무를 닫지 마라.
   실제 지원되는 명제만 검증하고 나머지는 해당 의무의 HOLD/UNSUPPORTED와 구체적 다음 작업을 남겨라.
   이미 조건부로 검토된 이론과 미검증 observational inversion을 섞지 마라.

4. 다음으로 HTT endpoint_cosmography와 functional_pushforward를 연결해라.
   LOCAL_TASKS.json의 python_test_files와 focused_existing_regressions를 실행해라.
   기존 환경의 실제 interpreter를 사용하고 test dependencies가 없으면 환경 정책에 따라 설치해라.
   저장소 루트에서 기본 실행 형태:
     PYTHONPATH=htt/src:htt:htt/htt <python> -m pytest -q <명시된 테스트 파일들>
     <python> scripts/run_typefree_predata_fixture.py --output <run_dir>/synthetic_fixture.json
     <python> scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
     <python> scripts/codex_harness/sync_pr_dag_mirrors.py --check
   13개 자유 intercept/기울기, 알려진 dense covariance, fixed independent d_A, explicit remainder 범위를 유지해라.
   distance-error integration, outcome-dependent selection, estimated covariance를 문자열 표지만 바꿔 허용하지 마라.
   finite remainder는 deterministic bias bound이며 Gaussian variance 또는 calibrated confidence set이 아니다.
   noisy intercept를 강제로 정규화하여 물리적 U를 만들지 마라.
   rank, eigengap, relative span, zero denominator, undefined mass 실패는 실제 분기로 보존해라.

5. 독립 리뷰어는 실제 diff와 실행 결과를 읽고 코드 정확성 및 전제 누락을 검토한다.
   단일 production writer, 최대 4개 active agent, nested agent 금지 원칙을 따라라.
   이번 게시의 VALIDATION.json에는 PR254의 기존 registry/receipt/import 불일치가 별도 기록되어 있다.
   이를 이번 코드 회귀로 단정하거나 기존 scientific status를 조작해 green으로 만들지 마라.
   필요하면 현재 main의 원래 테스트/authority 관계를 따로 진단하고 반환해라.
   새 코드에 결함이 있으면 작은 수정과 해당 회귀 검사를 하고, mirror/DAG 변경은 실제 작업만 기록해라.

6. RETURN_SCHEMA.json에 맞는 LOCAL_RETURN.json과 한국어 요약을 작성해라.
   입력 publication SHA, local SHA, 보존한 사용자 변경, 이론/추론 테스트,
   엔진별 PASS/FAIL/HOLD/NOT_RUN, 소스·출력 hash, 미완료 의무 및 실제 분석 전 필요한 입력을 반환해라.
   코드 이식 완료와 과학적 판정 승격, 실데이터 admission을 구분해라.
   I2 DEFENDED_CONDITIONAL / I3 HOLD_INPUT_INCOMPLETE를 유지하고,
   BIC-07 및 실제 cosmic tilt/Bianchi 분류를 승격하지 마라.

여기서 멈출 지점은 관측 분석 전의 이론·통계추론 구현과 검토다.
실제 카탈로그 적합, 추가 데이터 다운로드, 새 관측 결과·우주 유형 주장,
native 또는 외부 Boltzmann solver 실행은 이번 작업에 포함되지 않는다.
```
