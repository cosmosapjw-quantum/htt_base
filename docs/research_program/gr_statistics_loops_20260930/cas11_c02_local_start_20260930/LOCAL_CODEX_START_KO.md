# 새 local Codex 스레드 실행 지시

```text
ROLE=LOCAL_CAS11_C02_FRESH_VERIFICATION
PROJECT=htt_base
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
PACKAGE=docs/research_program/gr_statistics_loops_20260930/cas11_c02_local_start_20260930
CONTRACT_SHA256=c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a
SCOPE=CAS11-C02-v3-forward-only
PRESERVED_C04_LAUNCH=cl_000fce20034122657b6cdf509703df23
```

사용자가 전달한 실제 게시 commit을 `HANDOFF_COMMIT`으로 고정한다. 이 파일의 준비 기준 commit은 `b6f6fca6f30459e27657f0a465ebe947d250507d`이며, 그 값은 이 패키지가 추가된 게시 commit을 대신하지 않는다.

## 1. 새 작업 시작과 입력 확인

기존 primary checkout에서 `AGENTS.md`, 관련 repo skill과 `docs/harness/CURRENT_CODEX_RUNTIME.md`, 현재 선택된 global authority를 읽는다. 첫 로컬 명령은 `git status --short --branch`다. 이어 HEAD와 dirty/untracked를 기록한다. 기존 수정은 사용자 소유로 보존한다. 별도 clone/worktree, reset, stash, clean을 만들지 않는다.

C04는 원자 성분의 관측 CAS PASS와 미완료 reviewer 상태를 유지한다. 기존 launch의 재등록·dispatch·identity 변경을 하지 않는다. 이 작업은 C04 검토를 다른 이름으로 다시 실행하는 작업이 아니라 CAS11-C02의 독립적인 과학 검증 단위다. 기존 CAS11 실행·비용·실패 기록을 연결하고, 이미 진행 중인 동일 C02 작업이 있으면 중복 시작하지 않는다. 실제 global policy가 차단하면 우회하지 않는다.

아직 C02 launch를 등록하지 않은 상태에서 원격을 fetch하고 고정 handoff를 읽는다. 사용자 변경과 충돌하지 않고 fast-forward 가능한 경우에만 게시 내용을 반영한다. 안전한 통합이 불가능하면 정확한 충돌을 반환한다. 임의의 최신 커밋으로 source identity를 바꾸지 않는다. 새 작업에 사용할 `BASE_HEAD`를 정하고, 등록부터 해당 launch 처리 완료까지 HEAD를 유지한다.

`INPUT_RESOLUTION.json`에 따라 계약과 모든 원 source_input_hashes를 확인한다. 원본 경로가 없을 때는 명시된 byte-identical alias만 사용하고 실제 경로를 기록한다. 필요한 `NEUTRAL_PROPOSAL.json`이 로컬에 없으면 실행을 시작하지 않는다. 누락을 0이나 설명문으로 대체하지 않는다. 원 v3 계약은 수정하지 않는다.

## 2. 현재 실행 환경과 독립 작성자

한 번 정한 새 RUN_ID와 누적 비용 정보를 continuation마다 유지한다. 원 환경 파일은 그대로 두고 현재 엔진·패키지·실행 파일·Lean toolchain/mathlib lock의 실제 관측을 별도로 기록한다. 기존 환경과 달라졌다면 차이를 공개하고 계약상 환경 정렬을 해결한 뒤 실행한다. 과거 timeout을 현재 결과로 복사하지 않는다.

`EXECUTION_PLAN.json`의 순서를 따른다. Wolfram/xAct, SymPy, Sage/Singular, Lean/mathlib 네 축을 모두 유지한다. 현재 global router가 지원하는 profile·transport·sandbox를 실제로 일치시켜 등록한다. 모델/effort의 요청값과 관측값을 구별한다. 현재 router의 할당·비용 제한과 기존 미결 작업을 존중한다. 성공으로 가정한 모델 이름을 채우지 않는다.

축별 fresh context와 별도 출력 디렉터리를 사용하고 쓰기 소유권을 나눈다. 작성자에게는 원 계약, `NEUTRAL_AXIS_BRIEF.md`, 원 계약의 허용 중립 입력만 전달한다. Host의 `HOST_COVERAGE.md`, 과거/형제 소스·결과·유도문은 adjudication 이전에 주지 않는다. 작성자들은 nested child를 만들지 않는다. 모델 계열 공유와 실제 노출은 정직하게 기록한다.

지원 경로가 있으면 준비 단계에서 끝내지 말고 각 축의 전체 범위 소스를 작성·검사한다. 고정 n 예제만으로 전체 PASS를 내지 않는다. 계산기가 확인한 부분과 해석적으로 남은 부분을 분리하고, 임의 차원·rank 또는 의사역행렬 의미론이 닫히지 않으면 그 gap을 기록한다. Lean은 전체 진술과 dependency/axiom을 점검한다.

## 3. 실제 네 축 실행

새 run 디렉터리 아래 own-axis 소스와 완전한 raw 로그 경로를 정하고 소스 해시를 봉인한다. `RUN_SPEC.json`은 확인한 실제 argv, repo 내부 cwd, 명시된 timeout으로 채운다. 네 축 argv는 서로 구분되어야 하며 shell 필드를 사용하지 않는다. 예전 C04 RUN_SPEC나 raw PASS를 복사하여 새 결과로 사용하지 않는다.

현재 repo 실행기의 `--help`와 인터페이스를 확인한 뒤, repo root에서 다음 형태를 사용한다. 아래 변수는 실제 로컬 경로로 정의해야 하며 `${...}` 문자열 자체를 실행기에 전달하지 않는다.

```bash
"${GRSTAT_CAS11_PYTHON}" -B .agent-harness/scripts/cas_gate.py run-adjudicate \
  --contract "${GRSTAT_CAS11_CONTRACT_REL}" \
  --run-spec "${GRSTAT_CAS11_RUN_SPEC_REL}" \
  --out "${GRSTAT_CAS11_ADJUDICATION_REL}"
```

`GRSTAT_CAS11_PYTHON`은 확인된 host interpreter다. `GRSTAT_CAS11_CONTRACT_REL`은 이 패키지의 `contracts/CAS11-C02-FINITE-GRAM.json`이다. 나머지 두 경로는 새 run의 repo-relative 경로다. 현재 telemetry binding이 요구되면 지원된 인터페이스로 감싸며 exporter 실패와 과학 실행 실패를 구분한다.

runner stdout/stderr와 종료 상태, 각 엔진의 완전한 로그를 보존한다. 저장된 결과를 읽는 `adjudicate`로 관측 실행을 대체하지 않는다. 원시 aggregate는 수정하지 않고 별도 coverage/수용 판정과 함께 반환한다. wrapper 오류·marker 부재·미증명을 수학적 false check로 꾸미지 않는다.

## 4. 검토, 게시, 반환

이 새 C02 단위에 대한 지원된 독립 검토를 한 번 수행한다. 검토에는 정확한 계약·봉인 소스·실행 근거를 주고 Host의 선행 판정을 주입하지 않는다. 구체적 finding은 관련 범위만 수정하고 이전 실패를 보존한다. 실제 reviewer가 생성·완료되지 않으면 그 상태를 그대로 반환한다. 다른 곳의 문서 검토를 등록 reviewer 완료로 대체하지 않는다.

이번 C02의 HEAD에 묶인 writer/reviewer launch가 모두 지원된 완료·비실행 종결 상태에 도달한 뒤 게시한다. 미결 launch를 둔 채 commit하여 다시 HEAD 불일치를 만들지 않는다. 지원된 종결 경로가 없어 게시가 막히면 로컬 결과와 정확한 blocker를 반환한다. 과거 C04 launch를 임의 종결할 권한은 없다.

`LOCAL_RETURN.schema.json`에 맞춘 RETURN.json과 raw evidence manifest를 만든다. 새 검증 결과와 이번 작업 파일만 명시적으로 stage하여 commit·non-force push한다. 기존 dirty/untracked 파일을 포함하지 않는다. 원격 전진이 있으면 실제 안전한 통합 절차를 따르고 force하지 않는다. 원격 ref/commit/tree를 R1으로 확인하고 실제 commit에 고정된 반환 링크·프롬프트를 출력한다. 내용 없는 반복 commit은 만들지 않는다.

반환 메시지는 다음을 포함한다: RUN_ID, 실제 BASE_HEAD와 게시 commit/tree, 계약 SHA, 네 축의 실제 상태, raw aggregate와 범위 판정, 독립 reviewer 상태, 새 finding 및 해석적 gap, 원본 보존, raw manifest 경로·SHA, 다음 최소 작업. 전체 CAS-11, 물리·관측·novelty·Bianchi 분류 및 과학적 HOLD의 승격은 없다.

지원된 경로가 없을 때만 정확한 blocker로 종료한다. 별도 C04 lifecycle 디버깅, CAS11-C03 또는 역방향 확장을 이번 단위에 섞지 않는다.
