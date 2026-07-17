# Shared-context / assignment harness 및 4축 CAS 최종 감사·수리 권고

## 문서 상태

| 항목 | 값 |
|---|---|
| 감사일 | 2026-07-17 KST |
| 기준 commit | `14fa510fa3ed9e3895340b3a78291714e1547c62` |
| 소유자 | `COMMON` |
| implementation scope | `common / codex-harness / process` |
| claim tier | `diagnostic_only` |
| transfer source | `none` |
| sky / mask | `not_applicable` |
| covariance / null mock | `not_applicable` |
| 과학적 승격 | 없음. 수학·물리 명제, Bianchi family, transfer, posterior 또는 관측 결과를 검증하지 않음 |

이 감사는 사용자가 밝힌 두 설계 전제를 판정 기준으로 고정한다.

1. shared-context/assignment harness는 한 parent 아래 subagent들이 동일 선행 자료를 반복 탐색·실행하는 낭비를 줄이기 위한 것이다.
2. computer-assisted symbolic computation(CAS)은 원칙적으로 **Wolfram Engine+xAct, SymPy, SageMath+Singular, Lean**의 네 축을 별도로 실행한다. 플랫폼 또는 계산 종류상 부적합한 경우만 명시적 예외를 허용한다.

## 1. 최종 판정

### 1.1 한 문장 결론

**shared-context의 아키텍처는 타당하며 보존해야 한다. 과설계의 핵심은 context 공유 자체가 아니라, 이를 둘러싼 “모든 PR에 7개 별도 subagent”, 프로필 미결속, run마다 초기화되는 리뷰 예산, 반복 raw 결과 영구보존, 전역 테스트 반복이다. CAS 네 축은 이 감축 대상이 아니며 별도의 필수 증거 축으로 유지해야 한다.**

### 1.2 이전 판단의 교정

이 감사는 “shared-context 자체가 overengineering”이라는 포괄적 표현을 철회한다. `.agent-harness/README.md:3-10`의 Tier-0 공통 컨텍스트, Tier-1 assignment slice, sibling-result 격리, 구조화 result envelope는 사용자의 의도에 맞다. `AGENTS.md:217-232`도 공통 CAS 계약과 결과 격리를 정확히 구분한다.

다만 현재 구현은 **좋은 프로토콜을 갖고 있으나 그 프로토콜이 실제 launch/runtime에 완전히 결속되지 않았다.** 따라서 판정은 다음과 같다.

| 영역 | 판정 | 조치 |
|---|---|---|
| Tier-0 shared context | 보존 | effective-context hash와 전달 방식만 강화 |
| Tier-1 assignment slice | 보존·수리 | 생성 시 필수 필드와 hash를 봉인 |
| blind-results / adjudication 분리 | 보존 | sibling read를 runtime에서 차단·기록 |
| custom subagent profile | 수리 필요 | 이름이 아니라 launcher receipt로 실제 선택 증명 |
| 모든 PR의 7단계=7개 agent 규칙 | 과설계 | 7단계는 lifecycle checklist로 유지하고 agent 수는 위험도별 결정 |
| 일반 리뷰 반복 | 과설계 | 동일 증거·동일 failure class의 재리뷰 금지, finding ledger 재사용 |
| 4축 CAS | 필수·비축소 | 네 toolchain의 blind evidence를 별도 보존 |
| routine raw review logs | 축소 | 요약·hash만 보존, load-bearing CAS/proof artifact만 장기 보존 |
| 장기 로드맵 | 부분 개정 필요 | 전면 재생성 금지, §4.5·§17·PR-124와 현재상태 포인터만 개정 |

## 2. 감사 방법과 독립성 한계

세 개의 `fork_turns=none`, `blind-results` assignment를 사용했다.

- shared-context 설계 의도 대 실제 enforcement
- CAS 네 축·예외·adjudication 규약
- 최소 수리 PDR과 비용 통제

세 reviewer는 모두 **generic prompted reviewer**다. task name은 역할 라벨일 뿐 custom profile 선택의 증명이 아니다. sibling 결과는 root adjudication 전 공유하지 않았다. 따라서 이 결과는 서로 다른 관점의 내부 process evidence이지 외부 독립 replication이 아니다.

현재 감사에서도 유용한 실패가 한 번 발생했다. CAS reviewer가 “validator 통과”라고 보고했지만 최초 merge는 다섯 finding의 `evidence_fingerprint` 누락을 찾아 거부했다. 한 번의 표적 수정 후 `result_count=3`, `raw_finding_count=12`, `error_count=0`으로 통과했다. 이는 **reviewer의 자연어 자기확인보다 기계 gate가 우선**해야 함을 직접 입증한다.

사용한 사고 단계는 self-discover(설계 목적 재정의), step-back(독립성의 대상 분리), metacognitive self-ask(어떤 비용이 실제 증거를 늘리는가), CoVe(파일·명령 재검증), adversarial self-ask(현 규칙을 우회하는 최소 반례), CCoT(공통 사실과 독립 결론 분리), PDR(보존/수리/제거 결정)이다. 내부 chain-of-thought가 아니라 검증 가능한 결정과 증거만 이 문서에 남긴다.

## 3. shared-context가 정당한 이유

독립성은 “모두가 같은 파일을 처음부터 다시 찾는다”는 뜻이 아니다. 독립이어야 하는 것은 결론 생성 경로, 계산 스크립트, engine output과 결과 열람이다. 다음 정보는 오히려 동일해야 비교가 가능하다.

- 정확한 명제와 claim ID
- frame, signature, units, tensor/harmonic convention
- domain, positivity/nonzero 가정, branch와 singular locus
- target canonical form과 equivalence relation
- test vector, tolerance, resource limit, forbidden shortcut

따라서 올바른 구조는 다음과 같다.

```text
한 번 만든 content-addressed 공통 사실
                 │
        ┌────────┴────────┐
 Tier-1 A             Tier-1 B ...
 (필요 파일만)         (필요 파일만)
        │                   │
 blind script/result     blind script/result
        └────────┬──────────┘
             adjudicator
```

이 구조는 중복 탐색을 줄이면서도 결론의 상호 오염을 막는다. 제거할 이유가 없다.

## 4. 실제 병목과 결함

### H1 — custom profile 사용이 증명되지 않는다 (`P1`)

현재 collaboration spawn 호출에는 `task_name`, `fork_turns`, message만 있고, 선택된 `.codex/agents/*.toml`의 이름/hash를 돌려주는 launcher-owned receipt가 없다. 따라서 `pr123_audit`, `physics_stat_auditor` 같은 task name은 custom profile이 실제 로드되었다는 증거가 아니다.

추가로 `.codex/agents`에는 18개 파일, 15개 unique `name`이 있다. 다음 세 이름은 중복이다.

- `convergence_director`: hyphen/underscore 파일 두 개
- `physics_stat_auditor`: hyphen/underscore 파일 두 개
- `harness_engineer`: 두 파일의 sandbox가 각각 `workspace-write`, `read-only`

`scripts/codex_harness/test_codex_assets.py:334-350`는 `agents[data["name"]] = data`로 후행 파일이 선행 파일을 조용히 덮으므로 중복을 검출하지 않는다. 같은 테스트의 `REQUIRED_AGENT_NAMES`에는 네 CAS profile도 없다.

**판정:** 지금까지 custom profile이 “사용되었다”고 attestation할 수 없다. 사용 가능하도록 파일이 설치되었다는 것과 실제 launch에 결속되었다는 것은 다르다.

### H2 — effective context가 완전히 hash-bound되지 않는다 (`P1`)

`.agent-harness/scripts/build_context_pack.py:12-24`의 `context_version`은 `shared_files`만 hash한다. 실제 start 시 추가되는 role file, assignment JSON, `required_inputs`, injection 설정은 같은 version 아래 바뀔 수 있다. start hook은 pack/index의 존재를 확인하지만 모든 실제 입력 hash를 재검증하지 않는다.

**수리:** launch manifest가 다음을 하나의 `effective_context_sha256`으로 묶어야 한다.

- Tier-0 pack과 index의 의미 필드
- role context
- assignment JSON
- 각 `required_input`의 path+hash
- governing spec/gate snapshot
- context delivery mode와 launcher/profile receipt

하나라도 바뀌면 launch 전 차단한다.

### H3 — assignment가 생성 시점에 fail-closed가 아니다 (`P1`)

`new_assignment.py:10-28`에는 `required_inputs`, `allowed_tools`, `required_outputs`, allowed writes, governing gates를 채우는 인자가 없다. 이번 감사도 생성 뒤 JSON을 수동 보완해야 했다. 더 심각하게 현재 validator에 unknown `agent_type`, 빈 `claim_ids`, 빈 세 목록을 넣은 negative probe가 `[]`를 반환했다.

**수리:** assignment v2는 생성 명령 하나로 완성·봉인되고, 다음이 비면 등록 자체를 거부한다.

- bounded claim IDs와 risk tier
- required inputs+hashes
- allowed tools/reads/writes
- required output schema
- profile kind, correlation group, launch attestation
- independence/discovery rationale
- CAS이면 axis ID와 `CAS_CONTRACT` hash

### H4 — instruction injection과 runtime enforcement가 혼재한다 (`P1`)

start hook은 좋은 지침을 주고 stop hook은 result를 검증하지만, 실행 도중 undeclared broad scan, disallowed tool, sibling result read, production write를 차단하지는 않는다. 실제 reviewer 한 명이 allowed tool 목록에 없던 `wc`를 사용해도 실행 중 차단되지 않았다.

**수리:** pre-tool access control 또는 동등한 sandbox를 두고, 차단된 시도까지 content-addressed access ledger에 기록한다. 단, 일반 코드 탐색을 지나치게 봉쇄하지 않도록 `targeted`와 사전 승인된 `independent_discovery`를 구분한다.

### H5 — context가 이중 전달될 수 있다 (`P2`)

start hook은 pack 본문을 최대 24,000자로 주입하지만, spawn prompt와 README는 agent에게 다시 pack을 읽으라고 한다. hook 주입이 성공했는데 파일을 또 읽으면 토큰을 이중 소비한다.

**수리:** `context_delivery_mode=hook_injected|file_fallback`를 receipt에 기록한다. hook이 전체 hash를 주입했으면 재독을 금지하고, truncation이면 파일 fallback을 한 번만 수행한다.

### H6 — merge와 stop의 세부 규약이 정책과 어긋난다 (`P2`)

- `AGENTS.md:208`의 dedup key는 `(claim_id, evidence_fingerprint, verdict)`인데 `merge_results.py`는 `evidence_refs`까지 key에 넣어 같은 finding을 남길 수 있다.
- stop marker regex는 marker 뒤 trailing text를 허용할 수 있다.
- symlink는 `resolve()` 뒤 검사되어 declared path 자체의 link 여부를 잃을 수 있다.
- stop event가 launch-bound assignment identity를 증명하지 않는다.

각 항목은 작은 unit/negative test로 고칠 수 있으며 새 대형 framework가 필요하지 않다.

### H7 — timestamp churn과 run-local budget가 반복 비용을 만든다 (`P2`)

동일 context 내용이어도 `build_context_pack.py:21-39`는 `built_at`을 바꾸고 pack/index를 재작성한다. 또 `max_total`은 run별로만 세어 새 run을 만들면 PR 누적 예산이 초기화된다. cross-run finding ledger가 없어 이미 해결된 공격이 새 이름으로 되풀이된다.

**수리:** 내용이 같으면 write하지 않고, 예산은 `work_unit_id`(보통 PR) 누적으로 계산한다. `(claim_id, evidence_fingerprint, verdict, resolution_commit)` ledger로 해결된 finding을 재사용한다.

### H8 — 과도한 반복은 실제로 관측되었다 (`P1 process`)

PR-119--123 이름을 가진 parent-session spawn은 107회였다.

| PR | spawn 수 |
|---|---:|
| PR-119 | 12 |
| PR-120 | 29 |
| PR-121 | 12 |
| PR-122 | 34 |
| PR-123 | 20 |

그중 65회가 `fork_turns=all`이었다. 즉 shared-context가 설치·정착되기 전에는 각 agent에 긴 parent history가 복제되었다. PR-122 commit은 `.agent-harness`에 4,121 lines, PR-123은 7,297 lines를 추가했다. PR-123에는 intake부터 attempt6까지 8개 run directory가 versioned되었다.

이는 shared-context의 목적이 잘못되었다는 증거가 아니다. 반대로 **공통 context를 짧게 공유하려는 설계가 실제 spawn 경로와 retention 정책에 적용되지 않았다는 증거**다.

## 5. CAS 네 축 최종 정책

### 5.1 축은 reviewer persona가 아니라 계산·증명 계열이다

필수 축은 다음 순서를 canonical display order로 쓴다.

1. Wolfram Engine + xAct
2. SymPy
3. SageMath + Singular
4. Lean + mathlib 또는 project proof libraries

네 축은 같은 명제·가정을 공유하되 서로의 script, derivation, output을 adjudication 전 읽지 않는다. 같은 LLM family가 스크립트를 만들었다면 process correlation을 기록하되, 서로 다른 engine/proof artifact의 기술적 증거를 없던 것으로 하지는 않는다. 반대로 네 개의 agent 이름만 다르고 같은 계산을 복사했다면 네 축 증거가 아니다.

### 5.2 현재 host의 준비 상태

2026-07-17의 bounded probe 결과다. 설치 여부는 준비 상태일 뿐 claim 검증이 아니다.

| 축 | 현재 상태 | 확인 근거 |
|---|---|---|
| Wolfram+xAct | ready | Wolfram 15.0.0, xPerm 1.2.4, xTensor 1.3.0; `Needs["xAct`xTensor`"]` 성공, exit 0 |
| SymPy | ready | Python 3.12.3, SymPy 1.14.0 exact factor probe 성공 |
| SageMath+Singular | ready | SageMath 10.9, Singular 4.3.2 exact factor probe 성공 |
| Lean | ready when repo-pinned | `formal/lean-toolchain`의 Lean 4.31.0, Lake 5.0.0; `formal` build 6 jobs 성공 |

한 reviewer는 unpinned elan이 v4.32 install lock에 걸린 것을 Lean axis blocker로 보고했다. root 재검증은 repository-pinned v4.31.0 toolchain으로 build 성공을 확인했으므로 그 blocker 판정은 폐기한다. **toolchain은 항상 repo pin으로 실행**해야 한다.

### 5.3 현재 CAS scaffold의 간극

좋은 부분:

- `AGENTS.md:217-226`에 네 축과 blind rule이 이미 있다.
- `.agent-harness/context/roles/cas_*.md`는 각 engine의 domain·branch·artifact 주의사항을 잘 분리한다.
- `.codex/agents/cas_*.toml` 네 개가 존재한다.
- `.agent-harness/templates/CAS_CONTRACT.json` 템플릿이 존재한다.

수리할 부분:

- 실제 claim에 bind된 `CAS_CONTRACT.json` instance가 하나도 없다.
- 현재 template은 axis applicability, exception, required artifact, adjudication, invalidation을 담지 않는다.
- CAS profiles가 asset test의 required/unique registry에 포함되지 않는다.
- `scripts/run_egs3_v9_seals.py:226-353`은 Lean lane과 contract binding이 없고, 여러 `ImportError`를 조용히 무시하며, Sage/Wolfram blocker code 2를 aggregate exit 0으로 바꾼다. 이 runner를 4축 gate로 간주하면 안 된다.

### 5.4 `CAS_CONTRACT` 최소 필드

계약은 다음 필드를 가져야 한다.

```text
identity:
  schema_version, contract_id/version, claim_id, statement_class,
  source/input hashes, claim ceiling, adjudicator
semantics:
  exact statement, symbol/type/domain map, frame/signature/units/conventions,
  assumptions, positivity/nonzero conditions, branches, exclusions,
  singular loci, order of limits
target:
  canonical form, equivalence relation, invariants, test vectors,
  precision/tolerances, forbidden shortcuts
axes:
  per-axis applicability and obligation, required scripts/proofs/outputs,
  pinned toolchain/package versions, resource limit
independence:
  blind-results, permitted inputs, forbidden sibling paths,
  script/result ownership and correlation disclosure
exceptions/adjudication:
  preregistered exception request, evidence, approver, expiry/retry,
  aggregate status rule, invalidation triggers
```

각 axis result는 contract hash, 실제 command/exit, tool versions, source/output hash, domain/assumption diff, exact-vs-numerical evidence class를 기록한다. contract가 바뀌면 네 결과를 모두 invalidate한다.

### 5.5 상태기계

Axis status:

- `PASS`
- `FAIL`
- `MISALIGNED_ASSUMPTIONS`
- `BLOCKED_PLATFORM_OR_LICENSE`
- `BLOCKED_PACKAGE_UNAVAILABLE`
- `BLOCKED_RESOURCE_LIMIT`
- `NOT_APPLICABLE_COMPUTATION_CLASS`
- `INCONCLUSIVE`

Aggregate status:

| 상태 | 조건 |
|---|---|
| `CAS_4AXIS_PASS` | 네 축 모두 같은 contract/domain/branch로 PASS |
| `CAS_PASS_WITH_REGISTERED_EXCEPTION` | 결과 열람 전에 승인된 예외가 있고 나머지 의무가 모두 PASS. “4-axis pass” 표현 금지 |
| `CAS_CONFLICT` | 정규화 뒤 결과 불일치. 다수결 금지, 최소 counterexample로 재판정 |
| `CAS_BLOCKED` | 필수 축 미실행, 미승인 예외, uniquely load-bearing 축 부재 |
| `CAS_FAIL` | 한 축이라도 유효한 반례 또는 proof failure 제시 |

### 5.6 예외 규칙

예외는 결과를 보기 전에 등록해야 하며 다음을 포함한다.

- 정확한 플랫폼/라이선스/계산부적합 사유와 bounded probe
- 해당 축의 고유 능력을 잃는지 여부
- 가능한 substitute obligation과 claim downgrade
- 승인자, expiry/retry condition

예:

- scalar algebra라면 xAct tensor subsystem은 `NOT_APPLICABLE`일 수 있지만 Wolfram 축 전체를 자동 면제하지 않는다.
- polynomial ideal/variety 문제가 아니면 Singular 고유 의무는 `NOT_APPLICABLE`일 수 있으나 Sage exact algebra 의무는 남을 수 있다.
- Lean에서 과학 명제를 충실히 formalize할 수 없으면 더 약한 theorem을 몰래 증명하지 않고 scope mismatch를 기록한다.
- 엔진 미설치나 timeout은 계산부적합이 아니라 platform/resource blocker다.

## 6. agent·review 예산 정책

7단계 lifecycle와 실제 agent 수를 분리한다.

| 위험도 | 예시 | 기본 agent 예산 | 테스트 예산 |
|---|---|---:|---|
| R0 mechanical | 문구, 비실행 metadata | 0 optional | changed-file lint/schema |
| R1 harness | hook, assignment, packaging | 최대 2 targeted | harness unit/negative + 1 E2E receipt |
| R2 scientific non-CAS | numerical/statistical contract | 최대 4, 서로 다른 claim/failure class | targeted property/mutation + smallest smoke |
| R3 CAS mandatory | CAS가 필요한 수학·물리 명제 | **4 axis slot 예약**, optional review와 별도 | 4 axis receipts + targeted checks + snapshot당 1 integrated gate |

R3의 네 축은 비용 압력 때문에 한 agent로 합치거나 세 축으로 줄이지 않는다. 대신 일반 mapper/reviewer를 줄여 slot을 확보한다.

review wave는 다음 조건에서만 추가한다.

1. 새 evidence class가 생겼다.
2. unresolved P0/P1의 failure hypothesis가 달라졌다.
3. patch가 해당 finding의 evidence fingerprint를 바꿨다.

같은 diff와 같은 질문으로 “final”, “recheck”, “attempt N”을 반복하지 않는다. 두 번째 wave 후에도 같은 P1이 반복되면 reviewer를 더 붙이지 않고 root가 scope 축소·revert·block 중 하나를 결정한다.

## 7. 테스트·artifact 비용 정책

### 테스트

- 한 designated runner가 selector별 receipt를 한 번 만든다.
- reviewer는 receipt를 소비하고, 반박할 구체적 failure가 있을 때만 최소 reproducer를 실행한다.
- reuse key는 source/worktree hash, exact selector, test/config/launcher hash, Python/dependency environment, seed, hardware/data hash를 포함한다.
- key가 같고 deterministic pass면 재실행하지 않는다.
- full collect/smoke는 every-PR 고정 의무가 아니라 packaging/collection 변화, five-PR checkpoint, release snapshot에서 한 번 실행한다.
- failing, flaky, remote, unseeded test는 cache하지 않는다.

### artifact retention

장기 보존:

- claim-load-bearing CAS scripts와 engine outputs
- compiled Lean proof와 import/toolchain receipt
- decisive counterexample/falsifier
- 최종 adjudication과 manifest

짧게 보존 또는 요약 후 폐기:

- generic reviewer 대화 원문
- 중복된 assignment/result envelope
- 이미 해소된 같은 finding의 attempt별 merged JSON
- 전체 stdout/stderr의 반복 사본

result JSON은 raw log를 inline하지 않고 `{path, sha256, bytes, producer, command_fingerprint}`만 둔다. routine result는 64 KiB 상한을 권고한다. 실패 raw output은 content-addressed blob 하나만 보존한다.

## 8. 장기 로드맵 개정 판정

`docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`는 **부분 개정이 필요하지만 전면 재작성하면 안 된다.** 1,289-line 계획을 매 PR 다시 생성하는 것은 또 다른 비용이다.

필수 수정은 네 곳뿐이다.

1. **§4.5 (`:185-217`)**: 7단계를 7개 별도 subagent 의무가 아니라 lifecycle checklist로 바꾼다. 위험도별 최소 agent 수, custom-profile attestation, shared-context once-delivery를 참조한다.
2. **PR-124 (`:304-313`)**: 제목과 DoD의 “Dual-engine”을 “four-axis CAS contract + derivation-lineage oracle”로 바꾼다. 네 engine agreement와 최소 두 개의 실제 독립 derivation은 서로 다른 지표임을 명시한다.
3. **§17 (`:1167-1195`)**: every-PR full collect/smoke를 targeted PR tests + smallest relevant smoke로 낮추고, 전체 collect/smoke는 checkpoint/collection-affecting change/release에 둔다. 4축 CAS는 예외로 네 receipt를 모두 요구한다.
4. **§20·closeout (`:1252-1289`)**: PR-119 intake 이전 문구는 historical plan으로 고정하고 active 상태는 backlog/status SSoT로 링크한다. 이후 progress를 이 장문에 반복 삽입하지 않는다.

권고 형식은 원문 전체 재생성이 아니라 작은 versioned amendment 한 개와 필요한 line edit다. routine PR 진행상황은 `pr_status.yaml`과 짧은 PR delta에만 기록한다.

PR4/NPIPE 데이터가 아직 내려받아지지 않았으므로 PR4 데이터 분석을 전부 skip한다는 기존 사용자 제약은 이 감사로 변경되지 않는다. 해당 입력 부재를 다른 synthetic/proxy 성공으로 대체하지 않는다.

## 9. 최소 수리 PDR

### Phase 0 — 의도 보존과 즉시 비용 차단

- 모든 새 일반 assignment는 `fork_turns=none`을 기본으로 한다.
- context는 hook 또는 file fallback 중 정확히 한 번만 전달한다.
- 같은 work unit의 cumulative spawn/test budget를 적용한다.
- routine run directory와 raw generic review log를 더 이상 commit하지 않는다.

Exit:

- targeted agent가 공통 pack을 재스캔하지 않음
- duplicate repo-wide scan 0
- 같은 selector의 exact-fingerprint test 실행 1회

### Phase 1 — assignment/profile fail-closed

- assignment/result schema v2
- unique profile registry; duplicate name 즉시 fail
- four CAS profiles를 required registry에 추가
- launcher-owned `{requested_profile, actual_profile, config_sha256, model, sandbox, fork_mode, attested}` receipt
- attestation이 없으면 자동으로 `generic_prompted`, 동일 correlation group 처리

Exit:

- unknown/duplicate profile, 빈 Tier-1, 수동 mutation, profile spoof가 모두 negative test에서 fail
- task name만 다른 generic agent가 독립 reviewer로 중복 계상되지 않음

### Phase 2 — CAS contract와 adjudication

- `CAS_CONTRACT` schema/template 보강
- axis result와 aggregate adjudication schema 추가
- platform/computation exception state machine 구현
- repo-pinned tool preflight와 blind path enforcement
- `run_egs3_v9_seals.py`는 legacy diagnostic runner로 명시하고 4축 gate에서 분리

Exit:

- synthetic claim 하나가 동일 contract hash 아래 네 별도 envelope를 생성
- 3축만으로 `CAS_4AXIS_PASS` 생성 불가
- assumption mismatch, post-hoc exception, weaker Lean theorem이 pass 불가

### Phase 3 — retention, dedup, test receipt

- write-if-content-changed context build
- normative dedup key 교정과 conflict object
- cross-run finding ledger
- content-addressed raw evidence 한 벌
- exact test receipt reuse

Exit:

- 동일 bytes 두 번 저장 시 blob 1개
- 동일 finding+다른 refs는 1개로 merge
- opposite verdict는 자동 conflict
- 같은 context rebuild에서 tracked diff 0

### Phase 4 — roadmap의 작은 amendment 후 PR-124 복귀

위 네 군데만 고치고 장기 계획 전면 재생성은 금지한다. 이 repair는 새 과학 framework나 새 PR fleet을 만들기 위한 것이 아니라 PR-124 이후의 비용과 증거 품질을 바로잡는 bounded prerequisite다.

## 10. 필수 acceptance tests

1. role file, assignment, required input, injection config 중 하나를 바꾸면 launch 전 stale-context fail.
2. unknown/duplicate agent name과 conflicting sandbox fail.
3. requested custom profile과 actual profile receipt가 다르면 fail; receipt가 없으면 generic 처리.
4. blind assignment의 sibling result read와 undeclared broad scan fail.
5. hook-injected context를 다시 읽으면 duplicate-delivery violation.
6. empty Tier-1 assignment 등록 fail.
7. 동일 dedup tuple+다른 refs는 하나로 합치고 refs만 union.
8. marker 뒤 text, symlink result path, launch identity mismatch fail.
9. CAS contract 변경 시 네 axis receipt 모두 stale.
10. 세 축 PASS+한 축 missing은 `CAS_BLOCKED`; 네 축 PASS만 `CAS_4AXIS_PASS`.
11. post-hoc exception과 자기 axis가 승인한 exception fail.
12. repo-pinned Wolfram/xAct, SymPy, Sage/Singular, Lean preflight 각각 version/artifact receipt 생성.
13. exact test fingerprint 재사용은 실행 1회; source/toolchain/seed 변경 시 재실행.
14. content가 같은 context rebuild는 tracked file을 바꾸지 않음.

## 11. kill switches

- effective-context hash mismatch: agent 시작 전 중단
- custom profile 미attestation: 독립 credit 제거, generic으로 강등
- sibling result read: 해당 result의 independent-support 자격 박탈
- CAS required axis missing/blocked: aggregate gate `CAS_BLOCKED`
- cross-axis sign/coefficient/domain conflict: consumer 전부 block, 다수결 금지
- 두 review wave 뒤 같은 P1 반복: 추가 reviewer spawn 중단, scope 축소/revert/block 결정
- full suite exact receipt가 current인데 재실행 요청: 새 invalidation 근거 없으면 거부
- 두 연속 PR이 schema/manifest/log만 늘리고 executable falsifier를 만들지 못함: DAG step-back

## 12. 자기적대적 최종 평가

이 harness의 가장 위험한 실패는 “너무 엄격해서 느리다” 하나가 아니다. **엄격한 것처럼 보이는 문서 표면과 실제 enforcement 사이의 간극**이다. 현재 구조는 많은 역할명, result JSON, review wave를 만들 수 있지만 다음을 아직 자동 보장하지 못한다.

- 그 역할이 실제 custom profile로 실행되었는가
- agent가 필요한 context를 정확히 한 번만 받았는가
- blind-result 경계를 실행 중 지켰는가
- 같은 test와 같은 finding을 다시 소비하지 않았는가
- 네 CAS 축이 같은 명제에 대해 실제로 실행되었는가

반대로 shared-context를 제거하면 이 문제를 해결하지 못하고 반복 스캔만 되살린다. 올바른 수리는 **공유할 사실은 강하게 공유하고, 독립이어야 할 계산·결론·결과는 강하게 격리하며, 이름과 문서가 아니라 launch receipt와 proof artifact에 비용을 쓰는 것**이다.

최종 권고는 `PRESERVE CORE / REPAIR ENFORCEMENT / REDUCE ORCHESTRATION / NEVER COLLAPSE CAS-4`다.
