# GR-CAS-05 v3 C01–C03 반환 — 유한 엔진 PASS, 종료 검토·게시 미완료

동일 logical task `GRSTAT-CAS-20260930-1308KST-CAS-05`, run `GRSTAT-CAS-20260930-1308KST`를 유지했다. 먼저 게시된 중립 입력 판정과 commit `3f100db94e008766ebfc5901321123692b0d6824`를 확인했고, v3 세 허용 입력과 v2 predecessor byte 결속을 실제 검사했다. 기존 원문 유도/진단 결과를 새 blind author에게 전달하지 않았다.

실제 Wolfram 15/xAct, SymPy 1.14, Sage 10.9/실행된 bundled Singular 4.4.1(44100), pinned formal_mathlib Lean 4.31의 C01–C03가 통과했다. 고정 gate의 최종 관측 실행 집계는 `CAS_4AXIS_PASS`다. C03 전체 40개 Einstein 1차 성분, 12개 전체 성분 basis, 원점 Bianchi 4개와 명시적 right inverse를 포함한다. Lean의 43개 theorem axiom 출력은 표준 propext/Classical.choice/Quot.sound만이며 유한 Taylor convention에 정합한다. Host의 세 CAS 축 비교 1,040개 잔차는 0이며 독립 네 번째 축으로 계산하지 않았다.

네 author는 실제 `cuhg_gpt6_sol_worker / gpt-6-sol/high / danger-full-access`였고 새 맥락에서 독립 제출했다. 같은 모델 계열의 상관은 남는다. 독립 reviewer는 실제 `cuhg_gpt6_astra_reviewer / gpt-6-astra/xhigh / danger-full-access`다. 최초 검토는 유일한 HIGH F1(Singular 실제 4.3.2 versus frozen 44100)을 발견했다. 기존 Sage author의 같은 launch로 실행 경로를 수정하고 실제 4.4.1 엔진과 최종 네 축 집계를 재검증했다. 기존 잘못된 버전 raw·코드·첫 검토는 보존했다.

수정 후 같은 reviewer의 F1 종료 검토는 **실행되지 않았다**. 공식 CLI의 동일 launch closeout 예약/brief 결속은 성공했고 예약은 `RESERVED`, consumption은 null이다. 그러나 실제 followup은 최초 `REVIEW_CLOSEOUT_NOT_RESERVED`, 예약 후 정확한 참조와 정확한 원문 모두 `REVIEW_PROMPT_CHANGED`로 거부됐다. Codex 로그·call/thread/turn ID·dispatcher source/sha·미소비 예약을 durable routing/review에 보존했다. Client의 opaque/encrypted message 전달과 plaintext 비교의 불일치가 유력하나 실제 hook 입력 bytes가 공개되지 않아 확정 원인으로 주장하지 않는다. `hook/completed`의 실제 protocol status/sourcePath/command/exit/stdout/stderr는 확보된 JSONL/SQLite에서 노출되지 않았다. 설정 경로나 validator 결과로 해당 이벤트를 꾸미지 않았다. 과거 blocked2/failed6 기록도 변경하지 않았다.

Devstral managed CPU helper는 새 좁은 전개/문법/Lean 요청으로 실제 사용했다. SymPy 전개 helper는 최초 형태 실패, 수정 payload의 outer fence 제거를 명시한 adapter 후 고정 oracle 144개 성분 PASS로 제한 적격이다. Sage와 Lean helper는 실제 validator 실패와 backend 실패를 남겨 적격으로 승격하지 않았다. 모든 inference/lease ID, 요청·응답·validator·reconciliation은 RETURN.json 및 raw 경로에 있다. 이전 locator/중립 transcription receipt는 모델 재호출 없이 참고했고 science PASS로 재사용하지 않았다. Qwen/DeepSeek/Kimina의 과거 실패는 별도다.

네 author 누적 44,275,998 tokens(그 안에 cached input 43,538,560 포함), reviewer 초기 누적 3,205,584 tokens다. 이번 다섯 개 서로 다른 child 합계 47,481,582 tokens이며 Host/겹침 미확정 과거 창은 포함하지 않는다. 새 local 측정 2,112 tokens, 기존 알려진 6,038 + neutral 1,625와 합친 알려진 subtotal은 9,775다. 추가 backend 요청 3건과 과거 unknown usage는 NOT_MEASURED이며 0이 아니다. 전체 역사·통화 비용·Host 정합 누계·절감 효과는 NOT_MEASURED다. Advisory 초과는 같은 task로 실제 유용한 repair를 계속했고, 누적량을 초기화하거나 과거 STOP_BUDGET를 고치지 않았다. Native hard-cap enforcement는 입증하지 않았다.

사용자 dirty tracked 4개와 보호된 과거 과학 파일 1,724개, frozen gate·세 입력·predecessor·25개 closeout candidate hash 모두 현재 PASS다. 기존 미추적 자료는 보존했다. 완료된 다른 CAS campaign은 재실행하지 않았다. 최초 실패/수정 raw, launch/usage/lifecycle, CAS04 CAS_BLOCKED, v2 HOLD, C01/C02/C03/C04/R9를 유지했다. PR-DAG rescue-card의 기존 base 실패를 이번 hook/helper 실패로 재분류하지 않았다.

`scientific_admission=HOLD`다. smooth selected eigenfield/IFT, Lorentzian/DEC neighborhood, 전체 해석적 정리, 물리·관측 적용, CAS04의 Wolfram conservation→Euler projection 연결, EF6/CAS06 입력/의존 의무는 별도 미해결이다.

현재 HEAD는 그대로다. **최종 독립 closeout 미완료로 이번 단위를 commit/push하지 않았고 R1도 NOT_RUN**이다. 다음 하나는 같은 `cl_924187ce811ac659c9a6ddff77cdf0fc` 미소비 closeout의 client/dispatcher brief 전달 정합 복구 후 F1 종료 검토다. 계산 재실행·새 등록·비용 초기화 없이 완료하면 관련 파일만 commit·non-force push·R1을 수행한다. 그 다음 과학 단위는 CAS06 허용 입력/정의/의존 준비성 확인이다.

상세 근거: `RETURN.json`, `ADJUDICATION.json`, `independent_review.json`; durable `/mnt/sn850x2t/local_ai_foundry/70_experiments/cuhg_cas05_v3_execution_20261003/`의 routing/helpers/source-history/hook_failure_lean, FOUR_AUTHOR_ACCOUNTING.json, FINAL_THREE_AXIS_NORMALIZATION.json, PRESERVATION.final-unpublished.json. 모든 완료/미완료 층을 분리해 기록했다.
