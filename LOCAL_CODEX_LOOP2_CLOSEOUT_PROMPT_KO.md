# Local Codex 실행 프롬프트: Loop 2 보정·PR 통합·issue 처리·종료

아래 작업을 실제로 수행해줘. 계획 제시만으로 끝내지 말고 승인된 수정·검증·commit·push·관련 PR 처리·issue 처리·반환 인계까지 진행해줘. 일반적인 가역 작업마다 승인을 반복해서 묻지 마. 실제 권한/충돌 때문에 막힌 항목은 근거와 함께 남기고 독립적인 나머지는 계속해줘.

## 목표와 출발점

저장소는 `cosmosapjw-quantum/htt_base`, 기존 checkout은 `/home/cosmosapjw/Dropbox/bianchi/htt_base`다. 목적은 Bianchi type을 고르지 않는 제한된 Loop 2 이론 패키지의 보정·정당한 판정·종료와 관련 PR/issue 정리다. 일반 spacetime kinematics, 선택적인 Einstein/Lie algebra, θ·σ·ω·A·local boost/global tilt, tensorized functional x,Q,F,Π,G_F의 기존 scope를 유지해줘. 새 solver/관측 캠페인/특정 family 식별을 마감의 새 선행조건으로 만들지 마.

감사 기준:

- commit `de3ab20219c46c2b14f1d2ec6bb87508c331634d`
- tree `8bb24302707ec57d2766c53937a08b0380eeac5e`
- parent `96c0b2cb59765c36860da2049021c25a240d0c9b`
- 근거 경로 `docs/research_program/typefree_loop2_20260928/`
- Lean `formal_mathlib/Egs3V8Mathlib/TypefreeLoop2.lean`
- Loop 1 ZIP SHA `0f896823faa03ed82b8cf484cfc893a56ea913e259dc16d59c50d5f97e68670c`
- Loop 1 SQLite SHA `6587bf88aa161ff2bd345610cdc8485c5e50095c750643359e2de4851537a4cc`
- Loop 2 최종 gzip SHA `393bdfa1a8a61a3aba54a2c64db38b93d7258e7d4802717d8b6c61fcb468c676`

첨부 `LOOP2_AUDIT_KO.md`, `PR_DISPOSITION_MATRIX.csv/json`, 독립 검토 결과와 remote 영수증을 읽어줘. 없어도 이 프롬프트와 pinned repo 근거로 시작할 수 있다. 외부 감사는 게시 blob 40/40, 원 ZIP manifest 101/101, 원문 6개, 역사적 DB 20개 테이블의 실제 행/스키마 보존, 최종 연결 19/19를 확인했다. 새 과학 엔진 실행은 없었다.

## 1. 상태 보존과 하네스

`AGENTS.md`와 하위 지침, 관련 physmath-research-loop/GPT-6 Astra 하네스, `htt-dag-orchestrator`, `htt-adversarial-review-loop`, claim firewall/provenance, SSOT handoff 지침을 읽어줘. 선택된 model router와 실제 host/effort attestation은 구분해줘.

현재 branch/HEAD/origin/main, staged/unstaged/untracked를 기록하고 기존 사용자 수정 7개와 미추적 자료를 보존해줘. 개수가 달라졌으면 현재 사실을 사용해줘. 새 clone/worktree/전체 저장소 복제/코드 DB 다운로드는 하지 마. 기존 checkout과 설치된 Wolfram+xAct, Lean+mathlib, SageMath+Singular, SymPy를 사용해줘.

무조건적인 reset/clean/stash, 전체 git add, 사용자 변경 포함 commit, force push는 금지다. 필요한 내 경로만 stage해줘. 안전하게 가능하면 기존 checkout에서 작업 branch를 쓰되 dirty 변경을 무심코 이동/덮어쓰지 마. 원격이 앞으로 갔으면 최신 차이를 평가하고 진행하며 de3ab202를 감사 기준으로 보존해줘.

local 활성 R9 run과 누적 budget을 먼저 확인해줘. 정상 종료/재결속 절차를 사용하고 과거 실패·STOP_BUDGET·raw를 보존해줘. 단지 budget/gate를 통과하려고 같은 work-unit을 새로 만들지 마. subagent는 context build→assignment 등록→실제 launch 순서로 사용하고 작성자와 reviewer를 분리해줘. 외부 수기 검토를 observed-run 증거로 소급 변환하지 마. 한 승격이 막혀도 가능한 수정·검증·분류를 계속해줘.

## 2. 기존 40개 근거는 보존하고 새 보정본을 추가해줘

`docs/research_program/typefree_loop2_closeout_20260928/` 같은 새 위치에 정오표·보정 명제·안전한 migration·후속 독립 판정·claim 표를 추가해줘. 기존 raw/DB gzip/receipt/원 ZIP/역사 상태는 덮어쓰거나 삭제하지 마. 이미 새 위치가 있다면 읽고 이어가줘.

**F1: W1 kernel 조건의 적용 영역.** 기존 TF_W1_INPUT 마지막 절의 “ker(B)⊆ker(P)인 target만 유계 가능”은 무제약 선형/affine variation domain에서만 필요조건이다. bounded/curved physical feasible set에는 그대로 적용할 수 없다.

정확한 유한차원 명제: 모든 v∈V에 대해 `||Pv||≤C||Bv||`인 유한 C 존재 ⇔ `ker B⊆ker P`. 순방향은 kernel 대입, 역방향은 `L(Bv)=Pv`의 well-definedness와 유한차원 연속성으로 `P=L∘B`를 얻는다. affine `k0+V`에서는 `ker B∩V⊆ker P`와 기준점 항을 사용한다. 일반 K에서는 `P(K∩B⁻¹{y})` 또는 noise/nuisance/source까지 포함한 joint feasible image를 직접 쓴다. 반례 `B=0, P=id, K=[−1,1]`은 kernel 조건 없이 target이 유계다. 유계성·유일 식별성·confidence calibration을 구분해줘.

이 짧은 증명과 음성 대조를 새 보정본에 넣어줘. 기존 R2 계수 4/1/2, monopole 와도 열 0, finite-window 적분/오차식은 독립 수기 감사에서 지지됐다. source/time law와 joint anchor가 없어서 수치 Q,F,Π,G_F, MES percentage/p-value는 UNAVAILABLE이다.

**F2: DB 재실행 안전장치.** 기존 `apply_append.py`는 ROOT/THEORY_INHERITANCE.sqlite 한 경로만 거부하므로 다른 위치의 원본을 --db-copy로 잘못 주면 쓰기가 가능하다. gzip 출력 충돌 검사도 DB commit 뒤다. 현재 DB가 손상된 것은 아니며 20개 역사 테이블은 보존됐다.

기존 스크립트는 역사 자료로 두고 새 entrypoint를 만들어줘. --source를 알려진 SHA의 읽기 전용 입력으로 열고, --output/gzip/receipt의 충돌을 쓰기 전에 검사하고 exclusive create해줘. 동일 path/inode 및 symlink/hardlink alias를 거부해줘. 새 복사본에서만 transaction/append/검증하며 성공·실패 모두 입력 원본과 기존 산출물을 보존해줘. 자신이 만든 미완성 임시 출력만 정리해줘.

역사 테이블·schema와 기존 Loop2 evidence/lineage를 전부 보존하고 새 correction/review를 별도 테이블/행으로 append해줘. pinned commit/source hash와 supersedes 관계를 명시해줘. 새 deterministic gzip과 receipt에 실제 SHA·command·검증 결과를 기록해줘. 원본 불변 여부를 무검증 상수로 기록하지 마.

focused tests: 원본/alias 거부, 기존 출력 충돌, 중간 실패 때 원본 불변, 정상 append 때 모든 역사 행/스키마 보존, 새 행 수/해시 연결 일치. 새 gzip의 durable 저장 방식은 repo 용량 정책에 맞게 정하되 기존 원본/압축본을 삭제하지 마.

**F3: Lean 범위 표현.** `gap_column3`는 3성분 열 하나의 diagonal gap estimate다. 별도 정리가 명시적 3×3 Frobenius identity다. RESULTS, ENGINE_RUNS, INDEPENDENT_DECISION_LOOP2 self-review, append_final_evidence.py와 최종 TF-P2/lean_mathlib DB caveat의 “3열/3-column”을 새 정오표/supersession에서 바로잡아줘. 기존 행/raw/receipt는 보존해줘. 문구 보정을 새 kernel proof라고 하지 마.

TF-S2/S4는 set inclusion/measure monotonicity/diameter/실수 union-bound 구성요소다. full-law·측도가능성·calibration·typed unavailable까지 결합된 전체 통계 정리가 형식화됐다고 하지 마.

## 3. 독립 판정과 이번 이론 범위 종료

작성자가 아닌 reviewer가 F1–F3를 확인하게 해줘. 외부 두 검토자의 strict 결과 형식은 통과했지만 launch=unverified/execution=self_declared이며 four-axis admission이 아니다. 이번 검토에서 핵심 TF-P2/P3 식과 S2/S4/C1의 좁은 범위, W1 window는 지지됐다.

출처 PASS / 수기 DERIVED·CONDITIONAL / 실제 kernel statement / CAS 실행·독립성 / 관측 admission을 분리해줘. 변경된 statement/코드에 필요한 local 실행만 수행해줘. 서로 다른 claim을 실행한 네 엔진 기록을 합쳐 four-axis PASS라 하지 마. 승격에 필요한 동일 contract·실제 axis 실행·independent adjudication을 못 채운 범위는 HOLD로 명시해줘.

I2 DEFENDED_CONDITIONAL, I3 HOLD_INPUT_INCOMPLETE는 별도 근거 없이 바꾸지 마. P3는 total Einstein source의 국소 명제이며 dust EOS/global cosmology 결과가 아니다. 관측 law나 joint budget을 발명하지 마.

## 4. 기존 PR 전체를 분류하고 관련 증분을 통합해줘

현재 열린 PR을 pagination까지 다시 조회해 감사의 57행 표와 대조해줘. 최신 base/head, diff, review threads/checks를 확인하고 각 PR에 MERGE / ALREADY_INTEGRATED / SUPERSEDED_WITH_EVIDENCE / HOLD / OUT_OF_SCOPE와 근거를 부여해줘. 분류 완료를 전부 병합 완료라고 쓰지 마.

현재 canonical DAG는 감사 시점 **211 cards**다. 과거 195-card DAG로 덮어쓰지 마. GitHub 번호와 `PR-xxx` card ID는 별개이며 여러 GitHub PR이 같은 PR-248을 가리킨다.

1. **#440 #449 #460 #461 #463 #465 #466 #467:** 이 8개 head는 de3ab202의 조상이었다. 최신 head를 재확인하고 main 도달 commit 근거를 남겨 이미 통합된 PR로 정리해줘. 과거 base branch에 불필요하게 다시 merge하지 마. GitHub의 closed/unmerged와 실제 merge commit을 구분해줘.
2. **#468**, head `5e4e899c0dfa2028d81a82ca68ccd11203947470`: 40개 delta 중 24개는 현재 같은 경로 blob 일치, 10개는 다른 경로에 동일 blob 보존. 현재 R9 후속 결과와 의미 단위로 대조해 미계승 요구만 통합하거나 근거 있는 superseded close를 해줘.
3. **#470**, head `c8bd214a61088b684cad1d08873f05227cf5bfb0`, base #468: 25개 delta blob 모두 역사 보존 경로에 존재하지만 활성 경로 일치는 0개였다. 보존과 활성 통합을 구분해줘. 현재 typefree scope에 유효한 optical 요구를 211-card DAG에 계승하고 원 PR을 처리해줘. 옛 pr_backlog/status 전체를 복원하지 마.
4. **#469/#444:** 다음 절의 blocker를 먼저 해결해줘. #469는 #444 위의 PR이다. main에 merge하면 3파일만 들어온다고 가정하지 마. 감사 시점 main과 PR-side 591개 commit 차이가 있었다. 필요한 3파일 수정과 회귀 보정을 현재 main에 제한적으로 계승하는 후속 PR이 안전하면 그 경로를 택해줘. 원 PR 종료에는 통합 위치와 같은 계약의 근거가 필요하다.
5. **#428:** 현재 delta 2,131개 중 삭제 2,106개, 수정 24개, 추가 1개다. 과거 대량 삭제를 이번 Loop2 마감에 섞지 마. 별도 HOLD/OUT_OF_SCOPE로 기록해줘.
6. **#427:** 본문은 marker 한 파일이나 실제 현재 diff는 337개(추가 274, 수정 57, 삭제 6)다. scope/base 차이를 해결하기 전 smoke merge로 처리하지 마.
7. 나머지 분기 PR은 제목이나 파일 존재만으로 통합/폐기를 판단하지 마. base별 실제 증분·미해결 리뷰·요구 계승을 확인해 현재 유효한 것만 검토·검증해 병합하고, 이미 대체된 것은 구체적인 source/commit/요구 매핑 후 종료해줘. 과거 과학 상태와 raw 근거를 보존해줘.

각 merge 전에 최신 head SHA, 의도한 base, 실제 branch policy의 필수 check, review, DAG 의존성과 claim scope를 확인해줘. 부모 미완료면 먼저 처리하거나 formal replan을 명시해줘. admin override/force/필수 gate 우회는 하지 마. 완료 5개마다 저장소 checkpoint 절차를 적용해줘.

## 5. Issue #445 / #448의 실제 blocker

### #445와 PR #469

외부 감사는 전체 실제 job log를 읽고 첫 실패를 확인했다:

- head `ef47cf3a4359c0876f4cd8002cd5f33a569ed3d3`
- run `35051091315`, Repository contracts job `104651420491`
- runner/checkout/설치/테스트가 실행됨.
- `tests/contracts/test_human_execution_authorization.py:1445`
- `test_ci_coverage_001_runs_every_pr304_policy_command_on_pull_requests`
- 옛 `python -m pip install 'pytest>=8,<9' 'PyYAML>=6,<7' 'numpy>=1.26,<3'` 문자열 검사 실패. **1 failed, 63 passed**.
- 실제 workflow는 여러 줄 설치와 Python 3.12.14 / NumPy 2.5.2 / SciPy 1.18.1 / healpy 1.19.0 / threadpoolctl 3.6.0 pin을 사용함.
- 뒤의 PR-315 결정성 checker는 **skipped**.

첫 blocker를 재현하고 PR-304의 필수 명령 전부 실행·설치 순서·실제 pin을 검사하도록 테스트를 수정해줘. 옛 문자열을 주석에 넣거나 테스트/필수 명령/환경 pin을 삭제해서 통과시키지 마. canonical locale/hash/thread/OpenBLAS 환경, 두 fresh-process replay와 cmp를 보존해줘.

다음 freeze identity는 바꾸지 마:

- feature package SHA `b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b`
- scientific projection SHA `8b0aadf1897703f32c0904ad6cc6f5db41766c896382f21e709a6cd212d81750`

focused local regression 후 수정된 **동일 head**에서 최소 두 번의 독립 Repository integrity 실행을 확인해줘. 한 job 안의 fresh process 두 번과 독립 CI 실행 두 번은 별개다. 성공/실패 모두 complete projection, canonical ASCII preimage, package/metadata identity와 runtime/OpenBLAS receipt를 보존해줘. timestamp 등 비과학 metadata의 비교 정책을 명시하고 비교 대상 의미를 임의로 바꾸지 마.

통합과 종료 조건을 만족하면 #445에 원인·fix commit·두 run·receipt hash를 남기고 닫아줘. 못 채우면 정확한 잔여 blocker를 기록하고 열어둬. 순수 typefree 수기 명제 마감의 불필요한 선행조건으로 확대하지 마.

### #448

원 #444 head `de73549c16ac6ceb63f924c86611e0a5ceb4711d`의 최신 A4 기록은 run `33718012456`, attempt 2, job `100532290372`, runner_id=0, steps=[]였다. 이후 #469의 2026-09-16 실행에서는 runner와 테스트가 시작됐다. 모든 현재 작업을 runner 미배정이라고 반복하면 안 되지만, #444 동일 head의 회복이 증명된 것도 아니다.

현재 요건/운영 상태를 확인하고 허용된 bounded same-head rerun으로 실제 checkout/steps 실행을 확인해줘. prestart 장애와 새로운 source-test failure를 구분해줘. 원 인프라 blocker가 해소됐으면 해당 범위의 근거로 issue를 닫고 코드 실패는 맞는 작업에 연결해줘. 권한/계정/결제 정책 때문에 불가하면 실제 annotation과 담당자가 해야 할 행동을 남기고 열린 상태를 유지해줘. threshold 변경이나 빈 commit으로 probe하지 말고 계정/결제 설정을 임의로 바꾸지 마.

## 6. 검증·게시·반환과 완료 기준

- 바뀐 범위의 의미 있는 focused 검증과 독립 후속 리뷰를 수행해줘. 필요한 local 엔진만 실행하고 불필요한 전체 과학 suite를 새 gate로 만들지 마.
- raw transcript의 보존 공백 경고와 새 작성 파일의 diff --check를 구분해 정확히 기록해줘.
- canonical DAG/mirror/handoff/claim ledger를 동기화하고 저장소 validator를 실행해줘. completed 수를 수동으로 부풀리지 마.
- 기존 사용자 변경이 staged commit에 포함되지 않았음을 확인하고 계획된 경로만 commit/push해줘. 실제 승인 범위의 관련 PR을 처리하고 새 remote commit/tree 및 결정적 blob을 제한적으로 확인해줘.
- 새 보정본에 RETURN_HANDOFF_KO.md, CLOSEOUT.md, PR_DISPOSITION.json, ISSUE_DISPOSITION.json, CLAIM_CLOSEOUT.json을 남겨줘. 역사 자료는 보존하고 현재 권위 문서에서 새 보정본으로 연결해줘.

반환할 내용:

1. 게시 commit/tree, 변경 경로 수, F1/F2/F3 fix와 실제 검증/독립 판정.
2. MERGED / ALREADY_INTEGRATED_CLOSED / SUPERSEDED_CLOSED / OPEN_HOLD / OUT_OF_SCOPE별 PR 번호와 개별 근거. 수행하지 않은 merge를 수행했다고 쓰지 말 것.
3. #445/#448 최종 상태와 head/run/job/receipt 근거, 남은 blocker.
4. 출처/수기/형식 증명/실행 admission/관측 admission을 분리한 claim 표.
5. 원본 ZIP/DB/raw 및 사용자 변경 보존 여부, 실제 필요한 외부 입력.

완료 기준은 제한된 이론 패키지의 보정과 정당한 판정, 관련 PR의 근거 있는 처리, issue의 사실에 맞는 처리다. 외부 입력/운영 blocker는 별도 명시하고 `CLOSED_SCOPED_WITH_EXTERNAL_BLOCKERS`로 이번 범위를 닫을 수 있다. 이것을 모든 과학 명제의 증명, 57개 PR 전부의 병합, 전체 관측 추론의 완성이라고 표현하지 마. 마감 대신 새로운 포괄 연구 루프로 작업을 되돌리지 마.
