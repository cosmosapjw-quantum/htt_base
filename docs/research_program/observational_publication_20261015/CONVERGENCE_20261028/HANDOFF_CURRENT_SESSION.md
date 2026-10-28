# Existing-session handoff: finite report convergence

이 메시지를 현재 작업의 우선순위 변경으로 적용하라. 세션·checkout·runtime STATE·진행 중 packet·task ID·사용량·one-use/ultra 이력·R9/UNKNOWN을 유지한다. 목표는 연구범위 확장이 아니라 이미 확보한 결과를 최종 연구 산출물로 수렴시키는 것이다.

## 1. 변경본 취득과 현재 작업 보호

기존 primary checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`에서 다음 브랜치를 fetch한다. 새 clone/worktree를 만들지 않는다.

```bash
git fetch origin research/htt-converged-deliverables-20261028
git show origin/research/htt-converged-deliverables-20261028:docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/HANDOFF_CURRENT_SESSION.md
```

현재 branch/HEAD, dirty files, 진행 중 worker와 current STATE를 읽는다. fetch는 실행 코드 채택이 아니다. 현재 source-bound 작업이 안전한 checkpoint/return에 도달한 뒤 이 브랜치의 변경을 기존 작업 브랜치에 merge하거나 해당 변경 commit만 cherry-pick한다. 사용자 편집과 더 최신 local commit을 보존한다. 강제 reset, clean, checkout 강제 전환, runtime 복원은 금지한다. 충돌은 실제 변경 내용에 따라 해결한다. main으로 merge하지 않는다.

진행 중 R36-06 acquisition의 source·cache·partial·worker·reservation을 보존한다. 보고서 우선 실행을 위해 writer를 반환하려면 기존 `checkpoint-acquisition` 계약의 실제 worker receipt와 host 증거를 사용한다. 살아 있는 프로세스를 종료했다고 추정하거나 가짜 checkpoint를 만들지 않는다. 작업 완료/안전한 checkpoint 이전에는 새 writer를 시작하지 않는다.

새 hook을 전역 재설치하거나 세션을 초기화하지 않는다. 이 handoff를 현재 사용자 지시로 직접 적용한다. 소스 반영과 실제 CLI 사용을 확인하되 hook reload나 live activation을 추정하지 않는다.

## 2. 기존 state에 한 번만 연결

아래 `HTT_STATE`는 **현재 세션이 실제 사용 중인 경로**로 설정한다. 이전 기록의 경로를 추정해 사용하지 않는다. `HTT_PY`는 현재 검증된 Python 실행파일이다.

```bash
HTT_CONV=docs/research_program/observational_publication_20261015/CONVERGENCE_20261028
"$HTT_PY" scripts/codex_harness/research_controller.py --state "$HTT_STATE" summary
"$HTT_PY" scripts/codex_harness/publication_frontier_preflight.py --state "$HTT_STATE" --frontier "$HTT_CONV/FRONTIER.json" --manifest "$HTT_CONV/EVIDENCE_MANIFEST.json"
```

`APPEND_READY`일 때만 다음을 한 번 실행한다. `ALREADY_APPENDED`면 재등록하지 않는다. frozen frontier identity가 다르면 원인을 조사하고 같은 ID를 덮어쓰거나 새 ID로 복제하지 않는다.

```bash
"$HTT_PY" scripts/codex_harness/research_controller.py --state "$HTT_STATE" append-frontier --frontier "$HTT_CONV/FRONTIER.json" --authorization "Owner 2026-10-28: finish the finite convergence release and continue existing scoped work; preserve original acceptance and runtime history"
```

## 3. 보고서부터 실행하고 자동 확장을 끝낸다

기존 router에서 실제 사용 가능한 profile만 전달한다. 다음 예시의 네 profile은 가능할 때 사용하며, unavailable을 사용 가능하다고 기록하지 않는다.

```bash
"$HTT_PY" scripts/codex_harness/research_controller.py --state "$HTT_STATE" next \
  --prefer-task R37-00-FIRST-REPORT \
  --prefer-task R37-01-RADIATION \
  --prefer-task R37-02-KINEMATICS \
  --prefer-task R37-03-HUBBLE \
  --prefer-task R37-04-CLASSIFICATION \
  --defer-task R37-05-FINAL-REPORT \
  --no-discovery \
  --available-profile gpt-6.1-sol/medium \
  --available-profile gpt-6-sol/high \
  --available-profile gpt-6-astra/xhigh \
  --available-profile gpt-6-astra/ultra
```

이 옵션을 **매번 next에 유지**한다. 기존 planned/running packet은 우선순위보다 우선한다. `--no-discovery`는 새 discovery 생성만 억제하며 이미 발급된 packet의 상태와 이력을 지우지 않는다. 기존 discovery가 있으면 현재 계약과 수렴 범위를 확인해 실제 결과를 마무리하고, 새로운 탐색 주기를 자동 시작하지 않는다.

host가 반환 packet에 따라 실제 native spawn→ack→raw result record→별도 독립 검토→next를 수행한다. 실행하지 않은 모델 라우팅을 실제 호출로 기록하지 않는다. 현재 문제에 필요한 상위 모델 연구/repair는 기존 router와 누적 할당을 사용한다. task 별 한 번의 의미 있는 검증/독립 검토와 concrete repair 이후 다음 산출물로 이동한다. 확정된 결과를 같은 입력으로 반복 검토하지 않는다.

## 4. 구체적 연구와 보고서 계약

먼저 `baseline/BASELINE_REPORT.md/.pdf` 후보를 현재 R32/R36의 실제 qualification과 대조하여 S0 보고서를 낸다. 원자료 적합이나 기존 정리의 재증명부터 시작하지 않는다. `imports/`의 두 상세 보고서·코드·수치 결과·MF02·main.pdf와 `SOURCE_REUSE.json`을 사용한다. 새 측정 결과와 finite/synthetic 검증을 구분한다. 마지막으로 반영한 upstream `679f2c5`의 R36-11 PR4 manuscript preparation도 `UPSTREAM_DELTA.json`으로 확인한다. 그 closeout_02는 코드 결함 F1/F2만 닫았으며 실제 MC source나 최종 원고를 과학적으로 승인한 것이 아니다.

S0에서 기존 campaign의 task ID 목록을 `products/R37-00-FIRST-REPORT/LEGACY_SCOPE.json`으로 고정한다. 이는 state 사본이나 새 실행 DAG가 아니라 이번 최종 보고서가 소비할 기존 작업 목록이다. 이미 완료한 task는 재실행하지 않는다.

그 다음 네 분석은 `DEVELOPMENT_PLAN.md`, `DATA_ANALYSIS_CONTRACTS.md`, `FRONTIER.json`의 실제 입력·계산·도표·통과조건을 따른다. 각 결과가 승인되면 해당 장의 `REPORT_DELTA.md/.pdf`와 표·그림을 즉시 생성한다. 새 논문 수를 늘리지 않고 기존 네 물리 목표와 여섯 논문으로 통합한다.

- 복사: 같은 입력에서 full/common23(or20)/gain-only/unpolarized를 비교하고 편광·미분잔차의 전단영역 영향을 계산한다.
- 운동학: 실제 광학 joint budget과 PM 응답을 재사용한다. Gaia24D E1/B1 carrier와 R36 E2/STF5 response를 혼동하거나 임의 독립 결합하지 않는다.
- 허블: 검증된 SN selected-block covariance와 signed16을 사용한다. 전체1701 covariance의 미검증 범위를 임의 보정하거나 angular carrier에서 절대 H0·redshift derivative를 만들지 않는다. CBL에는 실제 같은-z distance/H 입력이 필요하며 없으면 현재 자료의 방향별 sensitivity 결과를 먼저 완결한다.
- 분류: 공급된 family와 하나의 joint event에서 호환집합·물리적 오차·out-of-family residual을 계산한다. 실제 T/E/B atlas 없는 CMB Bianchi identification을 만들지 않는다.

외부 입력은 기존 receipt/hash/cache 우선으로 공개·무인증의 정확한 제품만 자발적으로 다운로드할 수 있다. 파일별·누적 용량 상한은 없다. 실제 `/mnt/extdrive` mount와 여유 공간을 확인하고 2GiB reserve, 스트리밍·release/schema/units/frame 검사를 유지한다. raw data는 Git 밖에 둔다. 새 인증이나 저자 연락은 포함하지 않는다.

## 5. 기존 연구를 마무리하고 종료

새 분석 사이에 기존 ready/research-needed/source-unblocked 작업을 원래 ID·계약으로 계속 실행한다. 원래42 acceptance를 낮추거나 기존 HOLD를 보고서 완료와 바꾸지 않는다. 부족한 외부 입력은 해당 가지에만 남긴다. source-gap만 제출해 새 분석을 완료 처리하지 않는다.

최종 보고서 task는 다른 실행 가능한 알려진 작업 뒤에 선택된다. 단, summary만 보지 말고 frozen legacy 목록의 구체적인 acquisition/repair/resume 가능성도 확인한다. 실행 가능한 것이 있으면 먼저 처리한다. 해결되지 않는 실제 외부 입력·능력·소진된 할당은 정확한 잔여 의무로 기록한다.

마지막으로 수정·확장된 결과를 정제하여 `REPORT_FINAL.md/.tex/.pdf`, 실질 내용이 있는 논문별 발췌본, vector figure·수치표·재현 명령·claim/evidence map·잔여 의무를 생성한다. 원래 과학 진행률, 각 분석 완료, 보고서 release 완료, 논문 제출 준비도를 별도 기록한다. 관련 검증과 한 번의 최종 scoped review에서 열린 실질적 결함을 닫고 commit/push한다. 새 frontier·새 이론 루프·추가 assurance-only PR을 자동 생성하지 말고 이번 release를 종료하라. journal 제출과 main merge는 하지 않는다.
