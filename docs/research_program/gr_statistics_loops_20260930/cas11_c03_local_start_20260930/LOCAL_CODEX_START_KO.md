# 새 local Codex 스레드: CAS11-C03

사용자가 전달한 실제 게시 commit을 HANDOFF_COMMIT으로 고정한다. 이 패키지의 조사 기준은 `f09532a5a800d01cde146190c34af51b9d8c4f1f`이며 패키지 게시 commit과 다르다.

```text
ROLE=LOCAL_CAS11_C03_WEIGHTED_PROJECTION
PROJECT=htt_base
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
PACKAGE=docs/research_program/gr_statistics_loops_20260930/cas11_c03_local_start_20260930
STATE=docs/research_program/gr_statistics_loops_20260930/cas11_c03_local_start_20260930/HANDOFF_STATE.json
CONTRACT=docs/research_program/gr_statistics_loops_20260930/cas_corr_followup_20260930/intake/contracts/CAS11-C03-WEIGHTED-PROJECTION.json
CONTRACT_SHA256=a97dc88082095ba636d326ea390cf629b86ca333577a27638c83c2b7f9a55794
PRESERVED_C04_LAUNCH=cl_000fce20034122657b6cdf509703df23
```

첫 로컬 명령은 기존 primary checkout에서 `git status --short --branch`다. HEAD·dirty/untracked를 기록하고 사용자 변경을 보존한다. AGENTS.md, 관련 repo skill, docs/harness/CURRENT_CODEX_RUNTIME.md와 현재 global policy가 선택한 authority를 읽는다. 별도 clone/worktree, reset, stash, clean을 만들지 않는다.

## 기존 결과와 새 작업의 구분

C02의 게시 run `GRSTAT-CAS11-C02-20260930T090559Z`에는 같은 계약의 관측 CAS_4AXIS_PASS와 유한 명제 독립 검토 PASS가 있다. 원시 로그와 이전 실패를 보존한다. 새 finding 없이 C02나 CAS13-C04를 재실행하지 않는다. C04 reviewer는 여전히 미완료이며 기존 launch의 재등록·dispatch·identity 변경·임의 종결을 하지 않는다. 새로 제공된 지원 identity 해결 절차가 없다면 C04 lifecycle 점검을 반복하지 않는다.

이번 목표는 기존 C03 version 3 계약의 유한 가중 직교투영·잔차 Gram·Cauchy–Schwarz 성분 검증이다. CAS-11 전체를 닫는 작업으로 확장하지 않는다. C03로 Gram의 PSD를 확보하더라도 C02가 요구하는 모든 a에 대한 오차 부등식은 별도 물리·해석적 전제다.

## 입력과 실행 상태 고정

1. 현재 저장소와 지원된 lifecycle 기록에서 동일 C03 작업이 이미 진행 중이거나 완료되었는지 확인한다. 있으면 그 RUN_ID·비용·실패·source identity를 계승하고 중복 등록하지 않는다. 새 작업인 경우에만 한 번 RUN_ID를 정한다. C02의 남은 lifecycle 처리 상태를 성공으로 추정하거나 C04 비용을 새 작업으로 옮기지 않는다.
2. 새 C03 launch 등록 전에 원격을 fetch하고 HANDOFF_COMMIT의 존재·tree·현재 HEAD 관계를 확인한다. 안전한 fast-forward일 때만 반영한다. 로컬 commit/수정과 충돌하면 보존하고 정확한 blocker를 반환한다.
3. HANDOFF_STATE.json의 원 계약 SHA와 계약 내부 source_input_hashes 7개를 실제 바이트로 확인한다. 이 조사 기준에서는 원래 경로의 NEUTRAL_PROPOSAL.json과 CAS_ENVIRONMENT.json도 게시되어 있다. 누락·변경은 실제 차이로 보고하고, 기존 SHA를 새 내용에 맞춰 고치지 않는다.
4. 실행에 쓸 BASE_HEAD를 확정하고 새 작업에 묶인 writer/reviewer launch의 지원된 완료·비실행 종결까지 HEAD를 유지한다. 미커밋 입력·소스는 별도 SHA로 봉인하되 HEAD identity의 대체물로 쓰지 않는다.
5. 현재 Wolfram/xAct, SymPy, Sage/Singular, Lean/mathlib의 실제 executable·version·toolchain·lock을 관측한다. 원 환경 파일은 불변 기록이다. 현재 관측과의 차이를 별도 기록하고 필요한 환경 정렬을 해결한다. Sage 내부 Singular와 standalone Singular는 각각 실제 실행 경로·버전을 기록한다. 과거 timeout을 현재 실패로 복사하지 않는다.

## 네 축 검증

현재 지원되는 global router와 예산·sandbox 규칙으로 각 축의 독립 작성자를 배정한다. 모델/effort는 요청값과 실제 관측값을 구별한다. 네 축은 Wolfram+xAct, SymPy, Sage+Singular, Lean+mathlib이며 축을 줄이거나 다수결을 사용하지 않는다. fresh context, 축별 디렉터리와 disjoint write ownership을 사용하고 nested child를 만들지 않는다.

작성자에게는 원 계약, NEUTRAL_AXIS_BRIEF.md 및 원 계약이 허용한 중립 입력만 전달한다. Host용 상태·기존 C02 증명·형제 C03 증명을 선행 입력으로 주지 않는다. 과거 또는 형제 해법에 노출되었다면 그 사실을 기록한다.

지원된 실행 경로가 있으면 준비 문서에서 멈추지 말고 실제 소스 작성과 전체 계약 범위 검사를 진행한다. 고정 차원 예제만으로 보편 PASS를 내지 않는다. 각 축이 닫은 해석적 의무와 대수 인증 범위를 명시한다. Lean은 전체 진술과 허용 axiom을 검사하고 sorry/admit/custom axiom으로 목표를 대체하지 않는다.

새 run 디렉터리에서 소스를 봉인하고 실제 argv·repo 내부 cwd·timeout을 넣은 RUN_SPEC.json을 작성한다. 현재 실행기의 도움말과 실제 인터페이스를 확인한다. 원 실행기의 승인 없는 수정으로 통과시키지 않는다. repo root에서 확인한 host interpreter로 다음 형태를 실행한다.

```bash
"${GRSTAT_CAS11_PYTHON}" -B .agent-harness/scripts/cas_gate.py run-adjudicate \
  --contract "${GRSTAT_CAS11_CONTRACT_REL}" \
  --run-spec "${GRSTAT_CAS11_RUN_SPEC_REL}" \
  --out "${GRSTAT_CAS11_ADJUDICATION_REL}"
```

네 변수는 실제 검증한 interpreter와 repo-relative 경로로 정의한다. 계약 경로는 위 CONTRACT다. 축별 argv는 구분되어야 하며 shell 필드를 사용하지 않는다. 단일 JSON payload의 `checks` 키는 정확히 `CAS11-C03-WEIGHTED-PROJECTION`을 사용하고 `domain_assumption_diff`, `counterexample`을 포함한다. 증명 gap은 숨기지 않는다. wrapper 오류·timeout·marker 부재를 과학 check=false로 위조하지 않는다.

실제 run-adjudicate 출력·exit와 엔진별 완전한 raw 로그를 보존한다. 저장된 envelope를 읽는 adjudicate로 실제 실행을 대체하지 않는다. 원시 aggregate와 별도 범위 수용 판정을 분리한다. telemetry가 요구되면 지원된 wrapper를 사용하되 exporter 실패와 계산 실패를 구별한다.

## 검토·게시·반환

한 번의 지원된 독립 검토에 계약·봉인 소스·관측 근거를 전달하고 Host의 선행 verdict를 주입하지 않는다. 구체적 finding만 좁게 수정하고 이전 실패를 보존한다. 실제 child 결과가 없으면 reviewer 미완료로 기록한다. 여기의 handoff 문서 검토는 로컬 과학 reviewer를 대신하지 않는다.

이번 C03의 HEAD에 묶인 launch가 지원된 절차로 처리된 뒤, 해당 결과 파일만 명시적으로 stage하여 commit·non-force push한다. 기존 사용자 수정이나 다른 run을 섞지 않는다. 원격 전진은 안전하게 통합하고 force하지 않는다. 지원된 lifecycle 경로가 없어 게시가 막히면 로컬 결과와 정확한 blocker를 반환한다. C04 launch는 그대로 둔다.

RETURN.json과 raw evidence manifest에는 다음을 실제 값으로 기록한다.

- RUN_ID, BASE_HEAD, 계약 SHA, source/input seals, 실제 argv/cwd/version/exit와 전체 로그 경로.
- 네 축의 상태, 관측 aggregate, 정량자·차원·퇴화 가지·증명 범위와 남은 gap.
- 작성자·reviewer의 requested/observed runtime, 실제 검토 완료 여부, 실패·비용 기록. 미측정 값은 NOT_MEASURED.
- C02와 C04의 보존 상태, parent CAS-11/CAS-13 및 과학적 HOLD 유지, catalogue fit 미실행.
- 게시 commit/tree와 원격 R1 확인, manifest 경로·SHA, 한 가지 다음 최소 작업.

자기 commit SHA를 담기 위한 반복 commit을 만들지 않는다. 게시 전 결과 파일은 준비 상태를 정확히 기록하고, 게시 후 실제 commit/tree·R1은 최종 반환 메시지나 기존 지원 receipt로 전달한다.

C03가 닫히면 다음 단계는 기존 C01 및 보편적 오차 부등식을 실제 물리 잔차와 연결하는 입력·해석적 의무를 결정하는 것이다. 이를 C03 성공에서 자동 추론하지 않는다. 지원된 경로가 없는 경우에만 정확한 blocker로 종료하며, 데이터 분석이나 새로운 Bianchi 분류 주장으로 범위를 넓히지 않는다.
