# 새 Local Codex 스레드용 handoff

이 문서는 Host용이다. 등록될 blind 축 작성자에게 통째로 전달하지 않는다. 문서·source hash가 있다는 사실은 허용 입력이나 실제 실행 허가를 자동 생성하지 않는다.

## 시작 프롬프트

```text
ROLE=LOCAL_SEQUENTIAL_PROOF_VERIFICATION
PROJECT=htt_base
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
PUBLICATION_BRANCH=main
PACKAGE=docs/research_program/gr_statistics_loops_20260930/local_sequential_verification_20261001
MODE=THEORY_PROOFS_SERIAL_NO_OBSERVATIONAL_FIT
HANDOFF_COMMIT=<이 문서 링크의 고정 게시 commit; 최종 전달문에 제공됨>
PRESERVED_C01_TASK=GRSTAT-CAS11-C01-20261001T031553Z
PRESERVED_C04_LAUNCH=cl_000fce20034122657b6cdf509703df23

목표는 이 스레드의 연구결과를 순차적으로 증명 검증하고,
실제 결과를 해당 파일만 main에 non-force push하여 고정 commit으로 반환하는 것이다.
준비 문서 작성만 반복하지 말고, 지원된 실행 경로와 입력이 갖춰진 다음 정리를 실제로 수행하라.

1. 기존 primary checkout에서 git status --short --branch로 시작한다.
   branch/HEAD/tree/remote/dirty/untracked를 기록하고 사용자 변경을 보존한다.
   새 clone/worktree/full repository copy, reset, stash, clean, force-push는 하지 않는다.
   현재 AGENTS.md와 docs/harness/CURRENT_CODEX_RUNTIME.md,
   ~/.codex/runtime/global-execution-policy.json이 실제 선택한 authority를 읽는다.

2. git fetch origin main으로 원격 객체를 얻되 HEAD부터 바꾸지 않는다.
   git show HANDOFF_COMMIT:PACKAGE/README_KO.md 방식으로 고정 문서를 읽는다.
   실제 명령에서는 HANDOFF_COMMIT과 PACKAGE를 실제 값으로 치환한다.
   전달된 commit/tree와 원격 ancestor 관계를 확인한다.
   활성 HEAD 결합 단위의 등록과 현재 작업 상태를 먼저 대조한다.
   안전한 fast-forward가 가능하고 현재 작업 계약을 깨지 않을 때에만
   git merge --ff-only origin/main으로 동기화한다.
   불가하면 fetch된 고정 문서를 읽으며 가능한 준비를 계속하고 정확한 충돌을 적는다.

3. README, PROOF_VERIFICATION_PLAN_KO.md, PROOF_DAG.json,
   PR_LIST_KO.md, PR_PLAN.json, REPOSITORY_SNAPSHOT.json을 읽는다.
   GR-CAS-*와 PORT-CAS-*가 다른 namespace임을 유지한다.
   canonical DAG와 이 보충 계획, 원 v1과 봉인 v2/v3/v4의 정체성을 구분한다.

4. 로컬의 모든 관련 기존 run inventory를 확인한다.
   특히 local_cas/GRSTAT-CAS11-C01-20261001T031553Z/RETURN.json,
   원 manifest, 등록 argv/stdout/stderr/exit, 실제 Host runtime을 읽는다.
   원격에 없는 이 raw를 이 문서에서 복원하지 않는다.
   C01의 과거 registered=false/exit 2/no launch는 사용자 보고이며
   실제 로컬 기록으로 대조해야 한다. task ID와 실패·비용은 보존한다.
   기존 다른 CAS 완료 근거가 있으면 먼저 대조하고 중복 실행하지 않는다.

5. C01은 원 v3 입력에 별도 brief를 넣지 않는다.
   v4 후보의 구체적인 owner 채택이 이미 있으면 그 근거를 사용한다.
   없다면 이 전체 push/handoff 요청만으로 후보 승인으로 기록하지 않는다.
   승인 전 계약 추출·활성화·네 축 등록/dispatch를 하지 않는다.
   승인 후에도 현재 authority의 지원된 동일 task 계약 갱신과
   실제 저자 gpt-6.1-sol/high 등 관측 모델에 대한 정상 라우팅이 필요하다.
   모델 alias·가짜 tier·정책 편집·기록 재작성·중복 launch는 금지한다.
   v4 wrapper를 runner에 넣지 않는다. 승인된 exact proposed_contract만
   지원 절차로 봉인하며 bytes 변경이 필요하면 먼저 변경을 드러낸다.
   해결 경로가 없으면 C01과 그 의존 범위만 HOLD하고 독립 증명으로 진행한다.

6. C02/C03의 게시 CAS_4AXIS_PASS와 독립 리뷰 PASS를 유한 scope로 계승한다.
   새 finding 없이 재실행하지 않는다. C04 PASS와 reviewer 차단을 분리한다.
   C04 기존 launch의 지원 lifecycle에 새 변화가 없으면 inspect/dispatch를
   반복하지 않고 기존 관측을 보존한다. 새로운 지원 해결 경로가 있을 때만
   현재 inspect로 확인하고 등록 identity·read-only 전제가 충족된 첫 dispatch를 검토한다.
   C04를 재등록하거나 workspace_job을 임의 생성하지 않는다.

7. 우선순위는 PROOF_DAG.json의 serial_policy.priority_order를 따른다.
   한 번에 한 proof unit, 네 독립 축도 순차 실행한다.
   C01이 막혔다면 local evidence 대조 후 GR-CAS-01부터 eligible 노드를 선택한다.
   의존 명제가 막히면 독립된 GR-CAS-05/06 또는 다른 eligible 의무로 이동한다.
   차단 전파는 실제 필요한 premise에 한정하고 skip을 PASS로 쓰지 않는다.
   모든 노드가 blocked/held이면 정확한 입력·지원 절차를 반환한다.

8. 현재 전역 라우팅으로 정식 등록한 fresh-context 축 작성자만 사용한다.
   Wolfram+xAct / SymPy / Sage+Singular / Lean+mathlib 네 축을 유지한다.
   작성자에게는 해당 봉인 계약과 그 계약이 허용한 중립 입력만 준다.
   Host 보고서·이 DAG·기존 proof/reviewer verdict·형제 축 결과를
   adjudication 이전에 전달하지 않는다. 원문 source hash는 열람 허용과 다르다.
   등록 후 해당 bounded launch 처리 완료까지 HEAD를 유지한다.
   모델/effort의 요청값과 실제 관측값을 따로 적는다. nested children은 금지한다.

9. 실제 엔진 preflight와 pinned toolchain을 현재 실행으로 확인한다.
   과거 runtime 실패를 현재 실패로 계승하지 않는다.
   cas_gate.py preflight --axis를 네 축 각각 실행한다. --all은 쓰지 않는다.
   Python/C++ 능력은 독립 판정이며 필요한 경우 현재 실행 probe로 확인한다.
   tool 미노출·compiler/package 누락·실행/서비스 오류를 수학 반례와 구분한다.
   Wolfram만 돌리고 xAct라고, Sage만 돌리고 Singular라고,
   Lean parse/import만 성공하고 theorem kernel proof라고 보고하지 않는다.

10. 축별 소스·완전한 stdout/stderr·argv/cwd/exit·버전·source hash를 보존한다.
    pinned Lean/mathlib에서 전체 목표 theorem과 #print axioms를 확인한다.
    sorry/admit/new target axiom·순환 hypothesis·고정 차원 예제로 universal PASS를 금지한다.
    기존 .agent-harness/scripts/cas_gate.py run-adjudicate를 실제 실행한다.
    check-axis/adjudicate의 저장 envelope 검사만으로 새 실행 eligibility를 만들지 않는다.
    원 계약의 exact_test_obligations 키와 동일한 checks를 실제 결과로 채운다.
    상수 true, marker 조작, 결과에 맞춘 사후 가정 수정은 하지 않는다.

11. finite CAS 성분과 continuum/Hessian/ODE/측도/확률/물리 입력을 분리한다.
    남은 분석은 PROOF_VERIFICATION_PLAN_KO.md의 각 카드에 따라 실제 증명한다.
    C02의 all-a premise는 continuum residual bridge 없이 물리 오차에 적용할 수 없다.
    위상·적분가능성·경계·차원·c·부호·domain·rank와 singular limit를 명시한다.
    새로운 범위가 필요한 경우 원 고정 계약을 수정하지 말고 지원된 successor 절차를 쓴다.
    유효 반례면 명제를 수정하기 전에 원 반례와 raw 실패를 보존한다.

12. 정리별로 등록된 독립 reviewer에게 실제 candidate·계약·증거를 준다.
    이전 verdict를 주입하지 않는다. 실제 review와 runtime 관측 전 완료를 주장하지 않는다.
    한 bounded review와 필요한 targeted repair closeout으로 끝내고 메타감사를 반복하지 않는다.
    단계가 닫히면 관련 파일만 stage/commit/non-force push하고 R1을 확인한다.
    원격이 바뀌면 새 head와 diff를 대조하며 force나 무차별 merge를 하지 않는다.
    정상 R1 뒤 동일 byte redownload/reclone이나 receipt용 연쇄 commit은 하지 않는다.

13. PORT 12개와 Loop2 bridge도 진술별 재사용 또는 미증명 부분 증명으로 처리한다.
    source 계약 전체를 새 CAS runner 계약인 것처럼 실행하지 않는다.
    I2/I3, R9, BIC-07, CAS18, 실제 물리 ε/envelope·관측 law HOLD를 보존한다.
    실 데이터 fit, 신규 Boltzmann solver, Bianchi classification, production enable,
    관측 posterior/p-value나 manuscript admission은 실행하지 않는다.

14. 각 완료 단위 후 다음 eligible 증명으로 계속한다.
    새 근거 없는 같은 blocker 재시도·문서 commit을 하지 않는다.
    최종적으로 아래 반환 계약의 필드를 채우고 고정 commit/tree/R1,
    완료한 정확한 정리와 남은 의무 및 다음 한 작업을 출력한다.
```

## 확인된 runner 호출 형식

아래 형식은 이 게시 기준의 runner 소스를 읽어 확인했다. local에서는 먼저 현재 `--help`와 원 봉인 validator를 확인한다. `{python}`, `{contract}`, `{run_spec}`, `{out}`는 실제 경로로 바꾸는 자리표시자이며 자동 실행 명령이 아니다.

```text
{python} -B .agent-harness/scripts/cas_gate.py preflight --axis wolfram_xact
{python} -B .agent-harness/scripts/cas_gate.py preflight --axis sympy
{python} -B .agent-harness/scripts/cas_gate.py preflight --axis sage_singular
{python} -B .agent-harness/scripts/cas_gate.py preflight --axis lean
{python} -B .agent-harness/scripts/cas_gate.py run-adjudicate --contract {contract} --run-spec {run_spec} --out {out}
```

RUN_SPEC은 `schema_version=1`, `axes` 아래 네 정확한 key와 각 `argv` 문자열 배열·존재하는 `cwd`·양의 정수 `timeout_seconds`를 둔다. stdout은 `checks`, `domain_assumption_diff`, `counterexample`을 포함하는 하나의 JSON이다. 상세 로그는 별도 보존한다. runner의 stdout tail만을 완전한 raw evidence로 부르지 않는다.

## 로컬 반환 계약

기존 task가 이미 반환 schema를 고정했으면 그것을 우선한다. 아래는 Host 종합 필드이며 기존 schema를 교체하거나 renderer를 통과시키기 위한 가짜 PASS template가 아니다.

| 필드 | 필요한 내용 |
|---|---|
| identity | repo·branch·base/final commit/tree·run/task·contract ID/version/hash·authority identity |
| source | 허용 입력과 exact source hash, 이전 결과와의 관계, 새 finding 유무 |
| axes | 각 실제 command/cwd/version/exit, raw path, 소스 hash, 관측 모델/effort, PASS/FAIL/BLOCKED/NOT_RUN |
| result | raw aggregate, 범위 수용, 유한 theorem 목록, 닫힌/열린 analytic 의무 |
| reviewer | 등록·launch·실제 child/runtime·verdict·repair를 분리 |
| preservation | C01 원 v3/task/cost, C02/C03, C04 launch, R9, 사용자 변경 |
| publication | 실제 commit/tree/ref·provider 성공/R1; 미게시 파일과 이유 |
| remaining | 사용자 채택·지원 lifecycle·물리 입력·실행환경·수학 공백을 분리 |
| next_action | 다음 eligible node의 정확한 첫 작업 또는 더 진행할 수 없는 최소 사유 |

```json
{
  "schema": "htt.sequential_proof_campaign.return.v1",
  "example_only": true,
  "handoff_commit": null,
  "base_commit": null,
  "work_units": [],
  "proof_scope_closed": [],
  "unresolved_analytic_obligations": [],
  "blocked_nodes": [],
  "independent_review": {"status": "NOT_RUN"},
  "publication": {"status": "NOT_RUN", "commit": null, "tree": null, "r1": false},
  "scientific_admission": "HOLD_UNCHANGED",
  "next_action": null
}
```

이 예시는 실행 전 필드 설명이다. 실제 반환에서 빈 배열을 “모두 완료”로 해석하면 안 된다. 기존 C01 raw 또는 등록 evidence가 없으면 파일 경로·부재를 명시하고 만들어내지 않는다. 현재 source handoff에는 의도적으로 자기 게시 commit을 넣지 않았으며 최종 전달문과 고정 URL이 그 정체성을 제공한다.
