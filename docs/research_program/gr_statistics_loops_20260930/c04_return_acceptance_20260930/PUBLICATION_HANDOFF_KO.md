# C04 반환 수용·유한 Gram 후속 유도 게시 인계

작성일: 2026-09-30. 저장소: `cosmosapjw-quantum/htt_base`. 게시 대상: `main`.
이번 추가 게시의 기준 commit은 `08429842d1e18671676c0deae925c5bcf9946de2`, tree는 `6b4d30e068c5255660c51b98303949d541ef0a09`다. 최종 게시 식별자는 이 파일을 추가한 commit이며, 인계 시 해당 commit을 고정한다. 기준 commit과 새 게시 commit을 혼동하지 않는다.

## 읽기 순서와 보존 범위

1. [C04 수용 보고서](C04_ACCEPTANCE_REPORT_KO.md)와 [기계 판독 상태](C04_ACCEPTANCE_STATUS.json).
2. [판정 근거](ACCEPTANCE_EVIDENCE.json), [보존 파일 manifest](BUNDLE_MANIFEST.json), [원시 반환](intake/RETURN.json).
3. [다음 local 작업의 원문](NEXT_LOCAL_HANDOFF_KO.md).
4. [유한 Gram 후속 유도](NEXT_FINITE_GRAM_DERIVATION_KO.md).
5. [동일 원문 ZIP](C04_ACCEPTANCE_AND_FINITE_GRAM_NEXT_20260930.zip).

원 archive의 24개 멤버와 ZIP 자체를 그대로 보존했다. 원 manifest의 23개 항목은 크기·SHA-256을 대조했다. 선별 근거는 원 run manifest 37개 중 12개와 RETURN/manifest를 담고 있으며, 37개 전체를 취득·검토했다는 뜻이 아니다. 이 추가 게시에 새 CAS 실행은 없다.

원문에 있는 `publication_this_turn.commit=false`, `push=false`, “추가 push하지 않았다”는 원문 작성 시점의 기록이다. 원문 바이트를 변경하지 않고 이 게시 인계와 Git 이력으로 후속 게시를 기록한다. 원문 `NEXT_LOCAL_HANDOFF_KO.md`의 “새 push는 … 필수 작업이 아니다”라는 게시 지시는 아래의 최신 사용자 지시로 대체한다. 과학적 진술과 과거 실행 결과는 대체하지 않는다.

## 유지되는 판정

- run `GRSTAT-C04-CERT-20260930-1530KST`의 동일 version 3 C04 계약에 대한 관측 aggregate는 `CAS_4AXIS_PASS`다. 계약 SHA-256은 `0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`이다.
- 대상은 실수 `0<L<=U`, 모든 `x∈[L,U]`, 모든 실수 경쟁자, 양 끝과 `L=U`를 포함한 C04 원자 성분이다. 과거 run의 `CAS_CONFLICT`는 그대로 보존한다.
- 등록 독립 reviewer는 미완료다. launch `cl_000fce20034122657b6cdf509703df23`의 최초 dispatch가 `ROUTING_REGISTRATION_REQUIRED`로 거절된 상태와 관측 기록을 보존한다.
- 상위 CAS-13 C01–C03, 관측 구간 포함, 단위·프레임·수치오차와 전체 과학적 `conditional/HOLD`는 열려 있다. catalogue fit, novelty, Bianchi 분류 승격은 없다.
- 유한 Gram 유도는 `DERIVED_NOT_CAS_EXECUTED`다. 동결 C02의 순방향과 별도 역방향 확장을 구분한다. 원 계약을 바꾸거나 C04 PASS를 다른 정리에 상속하지 않는다. 결정론적 잔차 Gram은 관측 잡음 공분산이 아니다.

## Local Codex 실행 인계

```text
ROLE=LOCAL_C04_REVIEW_DISPATCH_CLOSEOUT_AND_PUBLICATION
PROJECT=htt_base
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
SOURCE_RUN=GRSTAT-C04-CERT-20260930-1530KST
SOURCE_PUBLICATION_COMMIT=08429842d1e18671676c0deae925c5bcf9946de2
CONTRACT_SHA256=0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63
EXISTING_REVIEW_LAUNCH=cl_000fce20034122657b6cdf509703df23
HANDOFF_PATH=docs/research_program/gr_statistics_loops_20260930/c04_return_acceptance_20260930/PUBLICATION_HANDOFF_KO.md

사용자가 제공한 고정 게시 commit을 HANDOFF_PUBLICATION_COMMIT으로 사용하라.
기존 primary checkout에서 AGENTS.md, 현재 선택된 global runtime authority와
이 인계를 읽고, 현재 branch/dirty/untracked 상태를 먼저 확인하라.
원격 ref를 fetch하여 고정 commit 존재를 확인하되, 사용자 변경을 덮어쓰거나
reset/stash/clean/force-push 또는 별도 clone/worktree를 만들지 말라.
자동 통합이 안전하지 않으면 고정 commit의 문서를 git show로 읽고 충돌을 보고하라.

기존 NEXT_LOCAL_HANDOFF_KO.md의 reviewer 연결 작업을 수행하라.
지원된 inspect로 기존 launch의 최신 상태부터 확인하고, 아직 미청구일 때만
등록된 primary checkout에서 지원된 첫 dispatch 연결을 해결하라.
실제 요청 필드/cwd/task_name/launch 연결을 현재 CLI/help/schema와 대조하라.
null task_name을 원인이라고 미리 단정하지 말라. 기존 run/task/launch ID와
비용·실패 기록을 유지하고, 반복 재등록이나 workspace_job.json 생성,
plan-continuation, hook/정책 우회를 하지 말라. 이미 청구되었으면 중복 실행하지 말라.

reviewer에게 정확한 계약·소스·실행 근거만 주고 host의 수용 결론을 검토 근거로
주입하지 말라. 요청한 모델과 실제 관측 runtime은 별개로 기록하고, 미확인은 UNKNOWN이다.
실제 child 결과 없이 검토 완료로 표시하지 말라. 구체적 새 finding이 없으면 C04
네 엔진을 반복 실행하지 말라. 차단이 지속되면 정확한 요청·거절·inspect를 반환하라.
CAS11 유도/구현/네 축 실행은 별도 후속 단위이며 이번 reviewer 작업에 섞지 말라.

성공 또는 차단 결과를 기존 기록을 보존하는 새 결과로 저장하라.
이번 작업에 속하는 파일만 명시적으로 stage하고 commit하여 origin/main에
fast-forward 방식으로 게시하라. 기존 로컬 변경이나 원격 전진 때문에 안전한 게시가
불가능하면 force하지 말고 실제 blocker와 미게시 파일을 보고하라.
게시가 성공하면 provider ACK/remote ref/commit/tree로 R1을 확인하고,
commit에 고정된 후속 handoff prompt를 반환하라. 불필요한 전체 clone/readback은 하지 말라.
결과에는 reviewer 처리 상태, C04 범위 finding, raw/source 보존, 변경 파일,
commit/tree/R1, 남은 blocker 및 다음 실행 작업을 포함하라.
CAS-13 전체 closure나 과학적 HOLD·novelty·관측 fit·Bianchi 분류를 자동 승격하지 말라.
```

## 이후 연구결과 게시 원칙

사용자의 2026-09-30 최신 지시: “이것도 push하고 handoff prompt를 전달해줘. 앞으로 연구결과 업데이트는 항상 push/handoff 포함해서 진행해.”

이 연구 스레드의 이후 연구결과 업데이트는 결과 작성, 범위에 맞는 검증, 관련 파일의 commit·push, 원격 R1 확인, 고정 commit handoff까지 포함한다. 반복 확인을 요청하지 않는다. 이 지시는 파괴적 덮어쓰기, 정책 우회, 과학적 판정의 자동 승격이나 타인의 변경 게시를 허용하지 않는다. 접근·정책·충돌로 게시가 막히면 성공으로 기록하지 않고 구체적인 blocker와 다음 조치를 반환한다.

## 게시 검증과 복구

변경 범위는 이 새 하위 디렉터리와 상위 [진입 문서](../C04_ACCEPTANCE_CURRENT.md)에 한정한다. 기존 계약·raw·코드·DAG 상태를 수정하지 않는다. 파일 보존과 새 상대 링크를 점검하며, 문서 게시를 이유로 CAS를 재실행하지 않는다. 새 commit의 CI 결과는 GitHub에서 별도로 확인해야 하며, 이 문서는 CI 통과를 주장하지 않는다.

게시 이전 상태가 필요하면 이 추가 게시 commit을 일반 revert하는 방식으로 복구할 수 있다. 원래 근거는 이전 commit과 이번 보존 ZIP에 남는다. reset/force-push로 이력을 지우지 않는다. 다음 local 작업의 담당자는 이 프롬프트를 받는 local Codex다.
