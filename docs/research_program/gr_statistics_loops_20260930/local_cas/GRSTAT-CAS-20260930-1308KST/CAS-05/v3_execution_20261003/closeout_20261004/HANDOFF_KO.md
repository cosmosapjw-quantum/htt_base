# 후속 세션 실행 프롬프트

작업 위치는 `/home/cosmosapjw/Dropbox/bianchi/htt_base`다. 이 프롬프트 옆의 `RETURN.json`과 durable 유지보수 `/mnt/sn850x2t/local_ai_foundry/70_experiments/cuhg_review_delivery_repair_20261004/RETURN.json`, 저장소의 `CAS-05/v3_execution_20261003/closeout_20261004/RETURN.json`, `independent_review.json`부터 읽어라. 먼저 `git status --short`와 설치된 `~/.codex/runtime/global-execution-policy.json`의 source/commit을 확인하고 사용자 변경 4개와 보호 파일을 보존하라. 긴 Codex JSONL 전체를 새 문맥에 넣지 말고 RETURN에 결속된 정확한 turn·launch·파일 범위만 사용하라.

CAS05 v3 C01–C03는 실제 네 엔진과 고정 adjudicator에서 `CAS_4AXIS_PASS`, 기존 F1 독립 검토는 `PASS_FINITE_COMPONENT_REVIEW`다. launch `cl_924187ce811ac659c9a6ddff77cdf0fc`, reviewer `01a1022f-3bb5-7892-befe-4ee2482e8a73`의 공식 `REVIEW_RETURNED`를 게시했다. 같은 reviewer, 전달, gate 또는 완료된 엔진을 다시 실행하지 마라. 최초 실패·FINDINGS·STOP_BUDGET·이전 반환과 누적 비용은 역사적 증거로 유지하라. 과학 child 5개 누적 51,220,031 tokens와 parent 제어 추가 2,228,422는 별도이며 cached input을 중복 합산하지 마라.

다음 단일 과학 작업은 **GR-CAS-06의 허용 입력·정의·의존 준비성 확인**이다. 승인된 중립 원문에서 실제 위치·정확한 식·가정·범위를 후속 계약에 결속하라. 다른 캠페인의 `LOCAL_CAS_CURRENT.md`를 이 실행의 우선순위로 사용하지 마라. 누락된 정의를 만들어 넣지 마라. CAS04 conservation→Euler projection, eigenfield 존재/IFT, spectral norm, EF6와 전체 해석적·물리·관측 의무는 별도 미해결 상태다. 이 작업의 유한 PASS를 `scientific_admission=HOLD` 해제로 확대하지 마라.

Local 모델을 실제로 사용해 Host의 반복 입력·초안 비용을 줄여라. 전체 CAS 분야 적합성이 없다는 이유로 일괄 배제하지 말고, Host가 정확한 입력·가정·출력 스키마·외부 validator를 정한 좁은 helper로 진행하라. 먼저 최종 RETURN의 역할별 실제 모델·lease·inference·검증 결과와 재사용 가능한 정확한 성공 영수증을 읽어라. 이미 성공한 Devstral Sage 부호/미분 helper와 Lean eta-contraction helper는 새 검증 호출 없이 해당 범위에서 재사용하라. 다른 모델의 결과를 해당 모델의 성공으로 표시하지 마라.

현재 설치 authority의 `docs/CAS_LOCAL_ASSISTANCE.md`와 `src` PYTHONPATH의 `python -m cuhg.models.local_assistance`를 사용하라. 기존 logical task·누적 회계를 이어가라. Catalog digest 변경으로 spec/store를 버전 분리해야 한다면 이전 spec·store를 동결 보존하고 historical_evidence와 외부 누적 회계로 연결하라. 새 store의 subtotal은 전체 task 비용이 아니며, 원래 비용을 0으로 시작했다고 표시하지 마라. 모델에는 필요한 식·기호·가정·허용 tactic·출력 예만 전달하고 저장소 전체나 긴 대화 이력을 넘기지 마라. 수정 요청에는 실제 이전 assistant 답안과 실제 validator 오류를 넣어라. Devstral은 user/user 연속 메시지가 아니라 assistant 답안을 사이에 둔 교대 메시지가 필요하다. 기계 판정 enum `evidence_class`는 `exact`를 사용하고 설명문을 그 필드에 넣지 마라. 잘못된 답안은 구체적 부호·인덱스·자료형·tactic 오류를 좁혀 프롬프트를 고친 뒤 고정 CAS/Lean 검사를 실행하라. Host가 정답 방향의 힌트를 줬다면 그 사실을 기록하라.

Native token/cost 목표는 advisory이며 초과 시 동일 누적 계정으로 다음 유용한 행동을 재계획하고 계속한다. Local 작업 전체의 token·시도 상한을 새로 만들지 마라. 기계적인 context/output/CPU/RAM/no-swap 제한은 유지한다. 절단된 출력은 continuation 또는 더 좁은 요청으로 처리한다. UNKNOWN 요청은 정확한 lease·프로세스 종료를 확인하고 공식 reconcile을 남긴 뒤 진행하며, 종료됐다는 이유로 unknown spend를 0으로 바꾸지 마라. 관리되지 않은 서버를 띄우거나 RAM 검사를 낮추지 마라.

결과는 실제 실행/외부 검증/독립 검토/게시/설치/과학적 admission으로 나누어 반환하라. 전체 역사·통화 비용과 반사실적 Codex 절약량은 측정하지 않았다면 `NOT_MEASURED`로 유지하라. 이번 후속 작업에서도 전역 하네스 자체를 수정할 필요가 생기면 기존 owner 예외에 따라 clean Codex를 사용하라. 문서·계약만 늘리며 멈추지 말고 다음 검증 가능한 계산 또는 입력 결속을 실제로 수행하라.

전역 소스는 PR #117의 `f09d211ba01dba54790707875a4ebde2041a1a7e`까지 설치됐다. Gemma `cpu-inventory-18302`는 실제 두 번의 256-token 절단을 근거로 프로필 max_tokens만 1024로 조정했다. n_ctx=2048, CPU/RAM 예약·no-swap·기본 역할 선택은 그대로다. `runtime/gemma-output-replan/catalog-installed.json`과 설치 명령을 보존하고, 이후 설치에서 오래된 catalog로 이 선택을 덮어쓰지 마라. 실제 응답 크기는 고정 validator에 맞는 최소 유용 크기로 정하고, 절단되면 raw와 측정 비용을 남긴 뒤 구체적으로 이어가라. Gemma의 thinking 옵션은 현재 프로필에 capability 결속이 없으므로 템플릿 문자열만 보고 강제로 설정하지 마라.

명시적인 추론 0건 context 사전 거부는 현재 설치본에서 `REVISE_REQUEST_CONTINUE`로 이어진다. 옛 qualification에 `RECONCILE_IN_FLIGHT`가 남아 있어도 원본을 고치거나 존재하지 않는 lease를 만들지 말고 canonical `route`로 현재 판정을 읽어라. 반대로 실제 dispatch/lease 증거가 있으면 정확한 reconciliation이 여전히 필요하다. 빈 final 출력의 알려진 raw/usage는 이제 보존된다.

검증된 역할별 helper는 general `exaone-1.2b-cpu`의30개 SymPy 잔차, coder Devstral의 Sage·Lean, prover Mathstral의 Lean이다. `live/QUALIFIED_HELPERS_FINAL.json`의 원래 request·model·lease·oracle 결속으로 재사용하라. EXAONE에는 Host가 첫 STF 행과 최종 trace=[1,1,1] 수정을 지도했고 단일 JSON fence만 제거했다. 이 사실을 독립 수학 능력으로 과장하지 마라. Gemma는 raw의 정확한 계수를 Host가 별도 추출해 검사한 후보만 PASS이고 원래 final 출력은 INCOMPLETE다. Qwen은 이번에도 추론 전 RAM pin 검사에 실패했다. 그 모델을 전체 general 역할의 필수 전제조건으로 두지 말고, 검증된 작은 프로필을 정확히 지정해 진행하라. 복구된 상주 모델에는30초 재교체 보호 시간이 있고, always-on 모델의 수동 unload 거부는 그 자체로 버그가 아니다.

알려진 local 누적은22,452 tokens이며 unknown 사용량은 별도다. 유지보수 clean3개 thread의 최신 누적은83,872,764 tokens(`token_usage_record` 계열), 대체 `token_count` 계열81,054,906과 혼합하지 마라. Coordinator 전체 thread와 과학 child는 별도 계정이다. 실제 Codex 절약량·통화 비용은 측정하지 않았다. 이후에는 이미 검토된 범위를 다시 열지 말고, 정확한 파일/오류 발췌와 재사용 영수증으로 짧은 helper부터 진행하라.
