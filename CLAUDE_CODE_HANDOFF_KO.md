# Claude Code 인수인계 프롬프트 — htt_base 증명 DAG + 크레딧 라우터

사용법: 아래 파일 9개를 저장소 **밖** 폴더(예: `~/htt_proof_tools/`)에 두고, htt_base 저장소 루트에서
Claude Code를 연 다음 `text` 블록 전체를 첫 메시지로 붙여 넣는다.

| 파일 | 역할 |
|---|---|
| `proof_dag_status.py` | 읽기 전용 DAG 스캐너. 노드 상태와 다음 eligible 노드 출력 |
| `CLAUDE_CODE_SEQUENTIAL_PROOF_PROMPT_KO.md` | 노드 1개를 처리하는 host 프롬프트 (축 순차, 리뷰, 노드별 push) |
| `proof_dag_driver.sh` | 기본 dry-run. `--go`면 다음 노드 1개를 `claude -p`로 위임 |
| `cost_router.py` | 가격, 사다리, 비용 상한(ALPHA), 장부, 예산 가드 |
| `cascade_runners.py` | Batch/async 실행기와 CLI (`plan`/`run`/`report`) |
| `test_cost_router.py` | 오프라인 테스트 15개 |
| `tasks.example.jsonl` | 작업 파일 예시 |
| `README_KO.md` | 라우터 설명서 |
| `CLAUDE_CODE_HANDOFF_KO.md` | 이 문서 |

```text
ROLE=HTT_BASE_PROOF_CAMPAIGN_CONTINUATION (Claude Code, 사용자 로컬 머신)
REPO=<htt_base 저장소 루트, 현재 작업 디렉터리>
TOOLS=~/htt_proof_tools          # 위 9개 파일 위치. 저장소에 복사·커밋하지 않는다.
BUDGET_USD=5                     # 이번 세션 API 크레딧 사용 한도. 사용자가 바꾸기 전엔 넘지 않는다.
PKG=docs/research_program/gr_statistics_loops_20260930/local_sequential_verification_20261001

이 작업은 두 트랙이다.
  트랙 A: PROOF_DAG.json 증명 검증. 직렬 전용. 등록된 경로가 있을 때만 실행한다.
  트랙 B: 증명 준비 작업(분석 메모, successor 계약 요구사항 초안, 형식 점검). 크레딧 라우터로 병렬 실행한다.
두 트랙의 산출물을 섞지 않는다. 트랙 B 결과는 항상 비권위(non-authoritative) 초안이다.

0. 시작 점검 (변경 없음)
 - git status --short --branch, HEAD, dirty/untracked 기록. 사용자 변경 보존.
   reset/stash/clean/force-push/새 clone 금지.
 - AGENTS.md, CLAUDE.md, docs/harness/CAS_LOCAL_ASSISTANCE_CONTINUATION.md,
   PKG/README_KO.md, PKG/PROOF_VERIFICATION_PLAN_KO.md, PKG/LOCAL_CODEX_HANDOFF_KO.md,
   PKG/PROOF_DAG.json을 읽는다. 충돌하면 AGENTS.md와 DAG가 이 프롬프트보다 우선한다.
 - cd $TOOLS && python3 test_cost_router.py  → 15개 통과 확인. 실패하면 트랙 B 중단.
 - python3 -I $TOOLS/proof_dag_status.py . 실행, 결과 표를 기록한다.
   스캐너 한계: 노드 단위 상태라서 하위 C0x 통과가 있어도 노드 BLOCKED로 보일 수 있다(GR-CAS-11).
   GR-CAS-13의 증거 경로 매핑은 휴리스틱이다. 실제 ADJUDICATION/RETURN과 대조한다.
 - claude --help로 proof_dag_driver.sh의 플래그(-p, --permission-mode, --max-turns)를 확인하고,
   다르면 드라이버만 고친다.
 - 툴체인 확인: Wolfram+xAct, SymPy, Sage+Singular, Lean+mathlib.
   .agent-harness/scripts/cas_gate.py preflight --axis <축>을 축마다 실행한다(--all 금지).
   없는 축은 "툴체인 부재"로 기록한다. 수학적 실패로 쓰지 않는다.

1. 경로 등록 확인 (트랙 A의 선결 조건)
 - ~/.codex/runtime/global-execution-policy.json과 현재 등록 lifecycle에서
   Claude Code가 축 작성자/리뷰어 경로로 허용되어 있는지 확인한다.
 - 허용되어 있지 않으면 트랙 A는 실행하지 않는다. 정확한 정책 블로커(파일, 키, 현재 값)만 보고한다.
   정책 파일 편집, 다른 모델/tier 이름 사용, 기록 재작성으로 우회하지 않는다.
 - 허용되어 있으면 $TOOLS/proof_dag_driver.sh . 로 dry-run 후,
   사용자가 승인한 경우에만 --go로 노드 1개씩 진행한다.
   노드 내부 절차는 CLAUDE_CODE_SEQUENTIAL_PROOF_PROMPT_KO.md를 따른다.

2. 사람 결정 노드 — 자동으로 풀지 않는다 (아래 "결정 패킷"만 만든다)
 - GR-CAS-11 / C01: v4 후보 계약 채택은 owner 승인 사항이다. 승인 기록이 없으면
   계약 추출·활성화·dispatch 금지. LOCAL_CODEX_HANDOFF_KO.md 5항을 따른다.
   C02/C03 PASS는 유한 scope로 계승하고 재실행하지 않는다.
 - GR-CAS-04: C04(perfect-fluid conservation → Euler 가속 A=-c^2 Dp/(ε+p)) 투영 연결이
   계약 입력에 없다. 어떤 투영·가정으로 연결할지는 물리적 선택이므로 owner가 정한다.
 - GR-CAS-18: 실행 가능한 계약이 없다(HOLD_INPUT_NO_EXECUTABLE_CONTRACT).
   비선형 collision/observation kernel 입력이 없으므로 가짜 CAS target을 만들지 않는다.
 - NEEDS_SUCCESSOR 노드: 봉인된 원 계약은 수정하지 않는다. successor 계약은 초안까지만 만든다.
   진술(명제) 자체를 바꾸는 변경이 들어가면 봉인 전에 owner 승인을 받는다.
 - 유효한 반례가 나오면 최소 반례를 원문 그대로 보존하고, 명제 수정은 owner에게 넘긴다.
 - scientific admission, manuscript 반영, novelty 승격은 언제나 HOLD_UNCHANGED.
 결정 패킷 형식(노드당 1개, $TOOLS/decisions/<node>.md, 저장소 밖):
   현재 상태와 근거 경로 / 결정해야 할 질문 1개 / 선택지 2~3개와 각 결과 /
   선택지별로 바뀌는 계약 bytes(diff) / 추천과 그 이유 / 결정 전 금지 행동.

3. 트랙 B — 크레딧 라우터로 준비 작업 병렬 실행
 - 키: ANTHROPIC_API_KEY 환경변수만 사용(크레딧이 있는 Console 조직의 키).
   출력·로그·커밋에 키를 남기지 않는다. 없으면 트랙 B를 건너뛰고 보고한다.
 - 작업 파일 생성: 스캐너 --json 출력과 각 노드의 ADJUDICATION.json/RETURN.json 핵심 필드
   (aggregate, 실패 분류, exact_test_obligations 키, 차단 사유)로 $TOOLS/runs/<날짜>/tasks.jsonl을 만든다.
   필요하면 $TOOLS/proof_prep_tasks.py로 생성기를 작성한다(읽기 전용, 저장소 수정 없음).
   클래스 지정:
     mechanical — 경로·필드 정리, 형식 점검 (검증기: JSON schema/정규식 검사 명령)
     analysis   — 노드별 실패 원인 요약, successor 요구사항 목록 (검증기 없음 → 1회 실행)
     hard       — 사람 결정 노드의 선택지 분석 초안 (검증기 없음 → 1회 실행)
   모델이 모델을 채점하는 검증기는 만들지 않는다. 검증기는 실행 가능한 명령만.
 - 순서: python3 cascade_runners.py plan tasks.jsonl --budget $BUDGET_USD
         → worst-case가 한도 이하인지 확인
         → python3 cascade_runners.py run tasks.jsonl --budget $BUDGET_USD --mode batch
         → python3 cascade_runners.py report
   장부(ledger.jsonl)와 results.jsonl은 $TOOLS/runs/<날짜>/에 둔다. 중단되면 --resume.
 - 처음 실행이면 BUDGET_USD를 2 이하로 시작하고, report로 단계별 통과율을 본 뒤에만 늘린다.
 - BUDGET_USD를 스스로 올리지 않는다. 더 필요하면 필요 금액과 근거를 보고하고 멈춘다.
 - 결과물 머리말에 "NON-AUTHORITATIVE DRAFT — not CAS evidence, not adjudication input"을 단다.
   결과를 local_cas/ 증거 경로, 계약, ADJUDICATION에 넣지 않는다.
   트랙 A의 축 작성자에게 트랙 B 결과를 주지 않는다(fresh-context·형제 격리 위반).

4. 금지
 - 증명 축을 라우터나 병렬 subagent로 돌리기(serial_policy 위반).
 - 정책/등록/기록 편집으로 경로 만들기, 모델 alias, 가짜 tier.
 - sorry/admit/새 axiom, 상수 true check, 결과에 맞춘 사후 가정 수정, skip을 PASS로 기록.
 - 실데이터 fit, 새 Boltzmann solver, Bianchi 분류, production enable, scientific admission.
 - 같은 blocker를 새 근거 없이 두 번째로 시도하기.

5. 종료 보고 (한국어, 짧게)
 - 트랙 A: 처리 노드, 축별 관측 결과, commit/push 여부, 막힌 노드와 정확한 사유.
 - 트랙 B: 실행 작업 수, 상태별 개수, 지출액/한도, 단계별 통과율, 산출물 경로.
 - 결정 패킷 목록과 각 노드의 질문 1줄.
 - 다음 한 작업.
```

## 자동으로 풀면 안 되는 항목과 이유

| 항목 | 자동화하면 생기는 문제 | Claude Code가 대신 하는 일 |
|---|---|---|
| Claude Code의 축 작성자 경로 등록 | `serial_policy.native_registration`은 "현재 지원되는 등록 경로만"을 요구한다. 현재 등록된 저자는 Codex 쪽 관측 모델이다. 에이전트가 정책 파일을 고쳐 자기 자신을 허용하면 감사 기록의 신원이 무의미해진다. | 정책 블로커(파일, 키, 값)만 보고 |
| GR-CAS-11 / C01 v4 후보 채택 | 어떤 계약을 검증할지를 검증자가 고르게 된다. 통과하기 쉬운 진술을 고르는 쪽으로 기울 수 있다. 저장소 문서도 owner 승인 전 추출·활성화·dispatch를 금지한다. | 후보 v3/v4 차이와 영향 범위를 결정 패킷으로 정리 |
| GR-CAS-04 conservation→Euler 투영 | 연결 공식이 계약에 없다. 이를 만들면 증명 대상 명제에 물리 가정(유체 모형, 투영 방식)을 새로 넣는 셈이다. 그건 검증이 아니라 이론 선택이다. | 가능한 투영 선택지와 각 선택이 바꾸는 가정 목록 |
| GR-CAS-18 | 실행 가능한 계약도, 비선형 커널 입력도 없다. 계약을 직접 만들고 직접 통과시키면 자기 채점이 된다. | HOLD 유지, 필요한 입력 목록만 |
| successor 계약 봉인 (NEEDS_SUCCESSOR) | 원 계약은 봉인되어 있다. 진술을 바꾸는 successor를 에이전트가 봉인하면 실패한 명제가 조용히 다른 명제로 바뀐다. | 초안과 원 계약 대비 diff 작성, 진술 변경 여부 표시 |
| 반례 후 명제 수정 | 반례가 명제를 깨뜨렸는지, 계약 오류인지는 수학적 판단이다. 자동 수정은 결과에 맞춘 사후 가정 수정이 된다. | 최소 반례를 원문 그대로 보존하고 보고 |
| scientific admission / manuscript 반영 | CAS PASS는 유한 성분만 보증한다. 연속체·Hessian·측도 같은 해석 의무와 독립 심사는 별도다. | 항상 HOLD_UNCHANGED로 기록 |
| 예산 증액 | 크레딧은 월 단위이고 소진되면 요청이 멈춘다. 지출은 되돌릴 수 없다. | 필요 금액과 근거를 보고하고 멈춤 |
| 증명의 병렬 실행 | `one_foreground_proof_unit`과 순차 축 실행 규칙을 위반한다. 축끼리 결과가 섞이면 네 축이 독립 확인이라는 의미가 사라진다. | 병렬은 트랙 B 준비 작업에만 사용 |

툴체인 부재(Wolfram/Sage/Lean)는 결정 사항이 아니라 환경 문제다. Claude Code는 설치를 시도하지 않고, 해당 축을 "툴체인 부재"로 기록한 뒤 다음 단계로 넘어간다.
