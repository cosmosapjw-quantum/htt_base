# 새 로컬 Codex 스레드 인계: C01 차단 해결

이 문서는 Host용이다. 축 작성자에게 전달하지 않는다. 실행 준비 제안이며 네 축 결과나 독립 과학 심사 결과가 아니다.

```text
ROLE=LOCAL_C01_SUPPORTED_RESOLUTION
PROJECT=htt_base
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
RUN_ID=GRSTAT-CAS11-C01-20261001T031553Z
TASK_ID=GRSTAT-CAS11-C01-20261001T031553Z
SOURCE_HEAD=2423cb6a362e43a844462cad63605a5955fe2e4d
SOURCE_TREE=549b21242bc3c574d4ae1edf09ab57f93cb0792e
V3_SHA256=57202993c9305a15deda1fc142c538473ec17e93453471063f04a5e04bb36624
PROPOSAL=docs/research_program/gr_statistics_loops_20260930/cas11_c01_resolution_20261001/C01_SUCCESSOR_PROPOSAL.json
PROPOSED_V4_SERIALIZED_SHA256=e586ee8766f2f6215f74499ef7f9d64bef66bc2747a6159ebf4abd3ee1d013c7
OWNER_ADOPTION=NOT_GRANTED_BY_THIS_DOCUMENT
```

인계의 게시 commit은 호출자가 제공한 고정 `HANDOFF_COMMIT`으로 확인한다. `SOURCE_HEAD`는 차단 당시 기준이며 최신 main과 같아야 한다는 요구가 아니다. 고정 인계 commit과 현재 main의 관계를 확인하고 사용자 변경을 보존한다. 새 checkout/worktree를 만들거나 과거 HEAD로 강제 되돌리지 않는다.

1. 기존 로컬 run의 `RETURN.json`, raw manifest, 실제 등록 argv와 stdout, Host runtime 기록을 읽는다. 대화에 붙여넣은 요약을 원시 기록으로 대체하지 않는다. 기존 manifest가 지정한 범위만 대조하고 누락은 누락으로 남긴다. v3와 7개 source-input 해시를 보존한다. 기존 task·실패·비용을 계승하고 등록 실패를 성공으로 덮어쓰지 않는다.

2. 이번 제안은 v3에 별도 brief를 주입하는 경로를 철회한다. 사용자가 **이 후보의 v4 채택을 명시적으로 승인했는지** 먼저 확인한다. 이 문서 자체는 승인이 아니다. 승인 전에는 계약 추출·활성화, 네 축 등록/dispatch, CAS, reviewer 재시도를 하지 않는다. 이미 세션에서 구체적으로 승인했다면 다시 묻지 않는다.

3. 승인 후에도 현재 `~/.codex/runtime/global-execution-policy.json`이 선택한 설치 authority의 문서·지원 CLI에서 기존 task/run/cost를 유지하는 계약 version 갱신 경로와 모델 라우팅 경로를 확인한다. 알려진 차단의 조건이 바뀌기 전에는 같은 실패 명령을 반복하지 않는다. `global_hook.py` 등의 명령을 추측하거나 과거 authority SHA를 고정하지 않는다.

4. 라우팅 수리는 실제 원인에 한정한다. 이전 실제 Host 저자는 `gpt-6.1-sol/high`이며 이를 지우지 않는다. 설치 모델표의 미지원 여부와 실패를 낸 정확한 command/authority version을 확인한다. 공식 지원 갱신 또는 실제 지원된 parent-decision 경로가 있으면 그 범위에서 해결한다. 모델명 alias, 임의 tier, policy/hook 편집, 다른 모델로의 과거 저자 재기록은 금지한다. 지원 변경이 필요하면 정확한 누락 모델·호출·오류와 요구 동작을 담은 authority 유지관리자용 전달문을 준비해 반환한다. 다른 사람에게 실제로 메시지를 보내는 것은 기존 세션의 명시적 전송 승인이 있을 때만 한다. 요구 동작은 '실제 모델 정체성을 보존한 명시적 라우팅 또는 명시적 차단'이며 특정 tier를 이 인계가 정하지 않는다. 과거 미지원 모델은 계속 거절되는 회귀 조건과 실제 라우팅 결과를 검증해야 한다. 프로젝트 코드가 global authority를 덮어쓰지 않는다.

5. 입력 계약 갱신과 라우팅 모두 지원되는 경우에만 승인된 `proposed_contract`를 별도 경로에 추출하고 봉인한다. 지정 직렬화의 해시는 위 값과 같아야 한다. 기존 v3는 수정하지 않는다. 승인 기록·지원 lifecycle 기록으로 같은 task의 successor임을 연결하며 새로운 task나 중복 launch를 임의로 만들지 않는다. 환경 재봉인 등으로 후보 bytes를 더 바꿔야 하면 변경 내용을 먼저 명시하고 고정 해시를 다시 결정한다. 승인한 후보를 조용히 수정하지 않는다. 지원된 동일 task 갱신이 없으면 그 정확한 제한을 반환한다.

6. 미래 축 작성자에게는 봉인된 계약 자체와 그 계약이 허용한 네 외부 입력의 고정 bytes만 전달한다. 추가 brief, 이 인계, proposal wrapper, 부모 풀이·결과, sibling 자료는 전달하지 않는다. 네 독립 축 모두 동일 계약 아래 임의 유한 차원의 세 점 항등식과 두 전제에 의한 소거를 검증해야 한다. 작성자 모델·effort는 관측값을 기록하고 현재 라우팅·비용 한도를 지킨다. 숫자 예시나 고정 차원 계산만으로 전체 PASS를 만들지 않는다.

7. 실제 축 증명·실행 이후에만 관측 `run-adjudicate`와 지원된 독립 reviewer를 진행한다. 등록 성공은 reviewer 완료가 아니다. 실행 오류를 수학적 반례로 바꾸지 않는다. 미정렬·부분 증명·모델 라우팅 실패는 정확히 구분한다. proposal의 문서 검토를 로컬 독립 CAS 심사로 재사용하지 않는다.

8. 새로운 근거나 실제 변경이 생긴 경우 해당 파일만 검토하고 commit·non-force push한다. 차단 해소 없이 같은 상태를 반복하는 commit을 만들지 않는다. 로컬 정책상 미완료 기록을 게시할 수 없다면 원시 기록은 로컬에 보존하고 그 제약을 명시한다. 허용되는 경우에도 BLOCKED 기록을 완료 결과로 게시하지 않는다. routine publication은 provider 성공과 remote ref/commit/tree의 R1을 확인하고 고정 commit으로 인계한다. publication receipt를 만들기 위한 연쇄 commit은 하지 않는다.

보존 사항: C02/C03 재실행 금지(새 finding 없이는), C04 launch `cl_000fce20034122657b6cdf509703df23` 불변, R9 불변, 부모 CAS-11/CAS-13 및 과학적 conditional/HOLD 불변. 관측 fit, novelty, Bianchi 분류를 승격하지 않는다.

반환에는 owner adoption의 실제 근거, 지원된 계약 갱신 경로의 관측 결과, authority version·실제 모델·등록/dispatch 결과, 축별 NOT_RUN/PASS/부분 범위, 사용한 계약 hash, 원시 기록 위치, 게시 commit/tree 및 R1을 분리하여 적는다. 없는 결과는 NOT_RUN/UNRESOLVED로 남긴다.
