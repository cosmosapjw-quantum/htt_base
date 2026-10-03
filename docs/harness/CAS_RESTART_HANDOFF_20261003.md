# CAS 재개용 handoff — 2026-10-03 hook 복구 이후

아래 프롬프트를 htt_base의 새 세션에 전달한다. 이 문서는 연구 결과의 승격이나 기존 실행의 재시작 지시가 아니다. 기준 과학 커밋은 `30f07dfc532e4355ea68aabde23bf28e05e80ca9`, 선행 handoff는 `0db3cad2ae6e7da42c80f0fd2d4a3c9af9a82234`이다. 이후 하네스 수정의 merge/install 증거는 `/home/cosmosapjw/.local/state/codex-cuhg-clean/audits/htt-hookstat-20261003/FINAL_RESULT.json`을 확인한다.

## 새 세션에 전달할 프롬프트

작업 루트는 `/home/cosmosapjw/Dropbox/bianchi/htt_base`다. 기존 사용자 변경·미추적 데이터, 연구 계약, raw 실패 기록, launch ID, 누적 비용을 보존하면서 남은 CAS를 진행하라. 먼저 현재 Git HEAD/status, 설치된 global descriptor, `docs/harness/CURRENT_CODEX_RUNTIME.md`, 아래 인계 자료를 읽고 실제 상태를 확인하라. 설치 확인을 이유로 완료된 과학 실행을 반복하지 마라.

필수 인계 자료:

- `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/completion/rerun_20261003/RETURN.json`
- 같은 run의 `CAS-04/EXECUTION_CONTRACT.json`
- 같은 run의 `CAS-04/completion_20261003/RETURN.json`, `PRESERVATION.json`, `routing/sympy/`, `routing/wolfram_xact/`, 각 축의 raw 출력과 검증 결과
- 위 유지보수 감사 디렉터리의 `runtime-evidence.md`, `runtime-evidence.json`, `handoff-facts.md`, `owner-provided-cas04-return.json`, `HARD_MAXIMUM_REVIEW_KO.md`

현재 상태와 재개 경계:

1. 최신 GR-CAS-01에는 유한 범위 4축 PASS가 있다. 과거 `CAS_CONFLICT` 기록과 원래 Lean author lifecycle의 미종결 상태는 별도 역사로 유지한다. 최신 유한 PASS를 전체 해석적 증명·물리/관측 적용·과학적 admission으로 확대하지 않는다. 완료된 C02/C03는 재실행하지 않는다.
2. 다음 작업은 **GR-CAS-04 EF1/EF4 finite의 남은 Sage/Singular·Lean 축**이다. 기존 단위의 `STOP_BUDGET`를 유지하고 별도로 범위를 고정한 remaining-axis 실행 계획을 작성한다. 계약 SHA256은 `058da4a8716fd06bc67100b8490df88a6783b780ac0ff66bf1221a02ab7e8741`이다. 과학 계약과 허용오차를 수정하지 않는다.
3. 기존 SymPy·Wolfram을 재시작하지 않는다. 두 축의 C01–C04 true 출력은 아직 adjudication되지 않은 candidate다. 최초 실패와 수정된 raw를 모두 보존하고 기존 결과를 재사용할 수 있는 범위를 검증한다. Sage와 Lean은 실제 미완료 증명 의무이며, 없던 결과를 채우지 않는다.
4. 기존 author cap은 각 500,000 cumulative total tokens였다. SymPy actual은 1,200,589, cached input은 1,115,904; Wolfram actual은 656,286, cached input은 620,416이다. `history_usage=NOT_MEASURED`를 그대로 유지한다. cached token을 빼서 과거 상한 초과를 없애거나 누적량을 초기화하지 않는다. 과거 두 native launch에는 `continuation_context`와 `harness_contract`가 결속되지 않아 준비된 숫자가 실제 hard cap으로 집행됐다고 볼 수 없다. 새 계획에서는 측정할 자원 단위와 집행 경로를 확인하고, 선언만으로 enforcement를 주장하지 않는다. 같은 단위의 예산·retry·repair 한도를 늘리지 않는다. 새로 범위를 한정한 남은 축 계획은 기존 logical task와 이전 사용량을 참조하고 실제 필요한 자원을 구체적으로 산정한다.
5. 각 남은 축은 명시된 가정·의존 입력·산출물·외부 validator·자원 계획을 확정한 뒤 현재 하네스의 준비/등록 명령을 사용한다. 등록 결과의 정확한 `agent_type`, 모델, effort, 실제 sandbox를 사용한다. `cas_sympy` 같은 프로젝트 역할명은 전역 등록 프로필을 대신하지 않는다. CAS 전문 역할은 task 메시지에 유지한다. 거부되면 반환된 recovery fields를 확인하고 같은 유효 launch 등록을 재사용한다. 재등록으로 비용이나 실행 횟수를 초기화하지 않는다.
6. local 실행은 구분해 기록한다. 이전 turn에는 Bonsai 문맥 요약 추론 3건(총 1,472 tokens)이 실제 실행됐다. 해당 작업의 일반 coder 후보는 작업별 적격성 미확립으로 제외됐고, local 과학 reasoning·prover LLM 추론은 관측되지 않았다. Kimina/Pythagoras 등 formal prover 대안은 `NOT_ASSESSED`이므로 평가 후 탈락한 것으로 해석하지 않는다. 로컬 CAS/Lean 엔진 실행은 별도로 확인됐다. 모델 목록·allocation·ready 상태만으로 추론을 했다고 기록하지 않는다. local candidate가 적격이면 요청/응답/모델·엔진 ID/usage/외부 검증을 남기고, 아니면 정확한 제외 이유와 사용할 native/Host 경로를 기록한다. 적격성이나 과학 결과를 임의로 승격하지 않는다.
7. 남은 축 실행 후 원래의 frozen adjudicator를 통해 집계하고 필요한 독립 검토를 수행한다. `.agent-harness/scripts/cas_gate.py`의 frozen source binding을 바꾸지 않는다. 네 축의 요건을 실제 충족한 경우에만 해당 유한 계약의 결과를 갱신한다. 기존 CAS-04 aggregate와 independent review는 각각 NOT_RUN 상태였음을 보존한다.
8. GR-CAS-11/C01의 입력 admission HOLD, 원래 v3/task/cost/adoption 경계, 별도 GR-CAS-13/C04 review launch `cl_000fce20034122657b6cdf509703df23`, R9를 건드리지 않는다. GR-CAS-04의 smooth selected eigenfield existence/IFT와 spectral norm, EF6의 CAS05/06 의존성은 미해결이다. `scientific_admission=HOLD`를 유지한다.
9. GR-CAS-04의 유한 범위 집계/검토가 끝나면 기존 sequential campaign의 준비된 다음 CAS(우선 CAS05/06 의존성)를 선택한다. 기존 계획의 입력·계약·dependency readiness를 먼저 확인하고 새 연구 범위를 무제한으로 확대하지 않는다. 완결된 단위만 별도 변경으로 게시하고 현재 publication verification 절차를 따른다.

hook 장애가 다시 발생하면 turn/thread/call ID와 실제 `hook/completed`의 status, sourcePath, command, exit code, stdout/stderr를 즉시 보존하고 Codex 로그와 `/mnt/sn850x2t/local_ai_foundry/70_experiments` 및 연결된 `60_runtime` 데이터에 결속하라. 과거 `blocked 2`는 잘못된 역할명에 대한 정상 거부였고 복구 안내가 불충분했다. 과거 `failed 6` 상세 이벤트는 창 재시작 후 소실되어 원인 미확정이다. 이 과거 숫자를 0으로 덮거나 현재 실패로 재구성하지 않는다.

보고에는 수행한 실제 엔진/모델 실행, 재사용한 증거, 검사하지 못한 항목, 각 남은 의무와 다음 실행 하나를 구분해 적는다. 준비 문서만 반복하는 루프를 만들지 않는다.
