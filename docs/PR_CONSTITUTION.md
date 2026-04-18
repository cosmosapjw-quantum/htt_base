# BASS PR Constitutional Rules

> Companion to `docs/SSOT_POLICY.md` §14.  Source: `BASS_PR_WBS_TDD_SDD_v1_0.md`.

이 문서는 BASS PR 이 merge 되기 위해 만족해야 하는 constitutional rules 와 long-range PR 목록·의존성을 고정한다.

---

## §0. Constitutional Framing (5 statements)

1. **Characteristics is the exact/full transport baseline.**
2. **Teff is a blockwise reduced chart / source bridge / diagnostic layer, not the global solver ontology.**
3. **Spin-2 / polarization remains explicit by default.**
4. **HTT is model-dependent, MIO is model-independent or weakly model-structured.**
5. **Backreaction enters as an effective tensor sector, not as a scalar fit residual.**

이 5개 statements 는 모든 PR 의 reviewer 판단 기준이다. 위반 PR 은 자동 reject.

---

## §1. Four Golden Rules

### 1.1 TDD rule

PR 의 core burden 은 **test 로 먼저 표현되지 않으면** merge 불가.

5개 test category 필수:
- **Identity tests** — 수학적/물리적 항등식 확인
- **Limit tests** — known limit recovery (see `docs/KNOWN_LIMITS.md`)
- **Channelwise tests** — TT/TE/EE/BB 각 채널 독립 검증
- **Regression tests** — 기존 validated 결과 대비 tolerance 내 유지
- **Caveat / provenance tests** — metadata/tag 가 올바르게 전파되는지

### 1.2 SDD rule

Major PR 은 short **solver design delta** 문서 동반 필수:
- 무엇이 새로 도입되는가 (object)
- 어떤 semantics 를 owns 하는가
- 어떤 파일/모듈 boundary 를 implies 하는가
- 어떤 theorem/proof obligation 이나 validation campaign 을 targets 하는가
- 무엇을 explicitly **claim 하지 않는가**

마지막 항목이 특히 중요. Claim 범위를 명시적으로 축소하는 것은 semantic drift 방지의 핵심.

### 1.3 Promotion rule

PR 은 다음을 **모두** 만족하면 promoted:
- Tests pass
- Semantic burden explicit (§1.2 SDD 대로)
- Rollback conditions known
- Channelwise burden not silently flattened (TT/EE/BB/TE 각각 독립 검증됨)

### 1.4 Critical path rule

First objective 는 "maximum feature count" 가 아니다. 순서:

1. **Preserve the FLRW denominator** (production D_2 가 흔들리지 않음)
2. **Stand up the exact anisotropic transport backbone** (characteristics 는 exact baseline)
3. **Add source ownership** (polter, Π_BASS, Doppler, quad 를 명확히 소유하는 모듈 도입)
4. **Add recombination / history realism** (HyRec-Cov)
5. **Only then** adaptive reduction, reionization, backreaction

---

## §2. Nine Programme Tracks (Track A – Track I)

| Track | Scope | 우선순위 (Critical path) |
|---|---|---|
| A | FLRW denominator hardening | ⭐⭐⭐ (가장 높음) |
| B | Exact anisotropic transport backbone | ⭐⭐⭐ |
| C | Source registry and block decomposition | ⭐⭐ |
| D | Recombination / visibility (HyRec-Cov) | ⭐⭐ |
| E | Reionization / 21cm characteristic branch | ⭐⭐ |
| F | Hybrid low/mid/high-ℓ + adaptive reduction | ⭐⭐ |
| G | EFT / backreaction effective tensor layer | ⭐ |
| H | HTT / MIO / atlas bridge hardening | ⭐ |
| I | Validation campaigns + operator workflow | (상시) |

---

## §3. Critical Path (24 PRs)

```
PR-000 → PR-010 → PR-011 → PR-020 → PR-021 → PR-022 → PR-023 →
         PR-030 → PR-031 → PR-032 → PR-040 → PR-041 → PR-042 →
         PR-050 → PR-051 → PR-052 → PR-060 → PR-061 →
         PR-070 → PR-071 → PR-072 → PR-080
```

의존성과 각 PR 의 scope 요약:

### PR-000 — Engineering constitution freeze (Track A)
**Dependency**: none (첫 PR). **SDD delta**: BASS 의 constitutional framing 5 statements 를 `docs/` 에 고정. 본 문서의 §0 이 그 결과.

### PR-010 — FLRW source/radial channel split cleanup (Track A)
**Dependency**: PR-000. SW/ISW/Doppler/pol 4 source channel 을 명시적 registry 로 분리. `source/registry.rs` 신설.

### PR-011 — FLRW denominator hardening: neutrinos, lensing, high-ℓ integration (Track A)
**Dependency**: PR-010. 현재 Phase B-1 post-audit 이 여기 해당. massive-ν, lensing, high-ℓ integration 개선.

### PR-020 — Geometry / tetrad core (Track B)
**Dependency**: PR-011. `geometry/bianchi_background.rs`, `geometry/tetrad.rs` 도입.

### PR-021 — Exact characteristics transport core (Track B)
**Dependency**: PR-020. `transport/characteristics.rs`, `transport/streaming.rs` 도입. §2.2 exact basis 구현.

### PR-022 — State block decomposition and explicit spin-2 ownership (Track B)
**Dependency**: PR-021. `state/blocks.rs`, `polarization/spin2_transport.rs`. TT/EE/BB/TE burden 을 module 단위로 분리.

### PR-023 — Linear/quadratic source registry (Track C)
**Dependency**: PR-022. `source/registry.rs` 확장, `source/bridge.rs` 도입. Polter/Π_BASS 를 explicit source primitive 로 고정.

### PR-030 — HyRec-Cov scaffold (Track D)
**Dependency**: PR-023. `recombination/history_cov.rs` 스캐폴드.

### PR-031 — Hydrogen directional Sobolev + line RT MVP (Track D)
**Dependency**: PR-030. `DirSob` branch 도입.

### PR-032 — Helium + FullChar Lyα promotion (Track D)
**Dependency**: PR-031. `FullChar` branch 도입.

### PR-040 — Reionization characteristic scaffold (Track E)
**Dependency**: PR-023, PR-030. `reionization/geometry_query.rs`.

### PR-041 — UV/X-ray/Lyα sweep + chemistry update (Track E)
**Dependency**: PR-040. 5.4 sweep order 강제.

### PR-042 — EoR refinement and lightcone production (Track E)
**Dependency**: PR-041. `EorLightconeExport` 도입.

### PR-050 — Low/mid/high-ℓ hybrid anisotropic solver (Track F)
**Dependency**: PR-022, PR-030. IMEX ARK4(3)6L[2]SA 기반.

### PR-051 — Adaptive ladder with frozen-rung slabs (Track F)
**Dependency**: PR-050.

### PR-052 — Angular UV / unresolved high-ℓ residual block (Track F)
**Dependency**: PR-051. `UnresolvedAngularExport` 도입.

### PR-060 — EFT/backreaction Tier-1 and Tier-2 implementation (Track G)
**Dependency**: PR-050. `backreaction/effective_tensor.rs`, `backreaction/averaging.rs`.

### PR-061 — Response-aware closure (Tier-3 EFT) (Track G)
**Dependency**: PR-060. `backreaction/response.rs`, `backreaction/window.rs`.

### PR-070 — HTT/MIO/atlas bridge hardening (Track H)
**Dependency**: PR-023, PR-052, PR-060. `ForwardBridge` 를 모든 export 경계에 강제.

### PR-071 — Validation campaign infrastructure (Track I)
**Dependency**: PR-070.

### PR-072 — Integrated operator/runbook outputs (Track I)
**Dependency**: PR-071.

### PR-080 — Local patch / global tilt dual-mode workflow (Track B 후속)
**Dependency**: PR-022, PR-070.

---

## §4. PR Merge Gate Checklist

PR 을 머지하기 전에 **모든** 항목 만족 확인:

### 4.1 문서 체크
- [ ] SDD delta 가 `docs/PR_DELTAS/<prxxx>.md` 에 작성됨
- [ ] 관련 SSOT 항목 (`docs/SSOT_POLICY.md` §6) 갱신됨
- [ ] 새 known-limit 가 있다면 `docs/KNOWN_LIMITS.md` 갱신됨
- [ ] `CHANGELOG.md` 에 PR entry 추가됨

### 4.2 Test 체크
- [ ] Identity tests (최소 1개)
- [ ] Limit tests (해당 Track 의 known-limit)
- [ ] Channelwise tests (TT/TE/EE/BB 영향 있을 시)
- [ ] Regression tests (`dump_dl_spectrum_*` baseline 유지)
- [ ] Caveat/provenance tests (metadata tag 검증)

### 4.3 SSOT 체크
- [ ] 새 매직 넘버는 `core::ssot::constants` 에 등록
- [ ] 새 source term 은 `core::ssot` 헬퍼 경유
- [ ] 새 export 는 `StatusMetadata` carry + `ForwardBridge<T>` 래핑
- [ ] `#[deprecated]` / stale path 호출 없음
- [ ] Audit grep (`docs/SSOT_POLICY.md` §9) 통과

### 4.4 Build 체크
- [ ] `cargo check --lib --release` 통과
- [ ] `cargo build --lib --release` 통과
- [ ] `cargo test --lib --release` 통과 (skip list 명시)

### 4.5 Semantic 체크
- [ ] BASS/HTT/MIO ownership boundary 준수 (§0-4)
- [ ] Claim 범위 명시 (§1.2 SDD)
- [ ] Rollback 조건 known

---

## §5. Rollback / Kill Criteria

### 5.1 Rollback triggers

다음 중 하나라도 해당되면 즉시 rollback:
- Regression test fail
- D_2 bit-identical guard violation (예상 범위 밖)
- Stale path 호출 panic
- SSOT audit grep 위반 신규 발생

### 5.2 Kill criteria (전체 PR 폐기)

- SDD delta 와 실제 구현이 일치하지 않음 (reviewer 판단)
- Stack ownership boundary 위반 (§0-4)
- 다수 PR (3+) 에 걸쳐 같은 bug 재등장 — 근본 설계 재검토 필요

---

## §6. Versioning

각 PR 은 **하나의 구체적 object 를 도입**하고, **하나의 구체적 test gate 를 통과**해야 한다. 다중 object 를 한 PR 에 묶지 말 것 (review 난이도 폭증).

이상적 PR diff size: 500-2000 LOC + 해당 tests.

긴 PR 은 반드시 sub-PR 로 분할:
- `PR-030-a-scaffold`
- `PR-030-b-core-rhs`
- `PR-030-c-tests`

---

## §7. Reviewer Responsibility

Reviewer 는 다음을 확인해야 merge approval 제공:
1. SDD delta 문서 존재 + 명확함
2. Test category 5종 모두 존재
3. SSOT audit grep 통과
4. 본 문서 §4 체크리스트 모두 check
5. §0 constitutional framing 5 statements 중 어느 것도 위반하지 않음

Reviewer 판단은 audit trail 에 기록된다. 동일 reviewer 가 구성상 결함을 반복 승인하면 reviewer 자격 reassess.

---

## §8. Long-Range Phase 지도 (요약)

| Phase | Duration | Tracks | 성공 기준 |
|---|---|---|---|
| Phase B-1 post-audit (현재) | 2026-04-17 | A (SSOT hardening) | D_2 = 1005.73 bit-identical 유지, SSOT 프레임워크 완성 |
| Phase B-2 | ~3주 | A (lensing, massive ν completion) | Track A 전체 완료, CAMB 대비 <3% RMS |
| Phase C | ~2개월 | B, C | Exact transport MVP, source registry v1 |
| Phase D | ~1개월 | D | HyRec-Cov 도입, DirSob branch |
| Phase E | ~2개월 | E | Reion char scaffold |
| Phase F | ~2개월 | F | Hybrid solver 생산 |
| Phase G | ~3개월 | G | Backreaction tier-1/2, optional tier-3 |
| Phase H+ | ongoing | H, I | Bridge hardening, validation campaigns |

---

## §9. 4-Gate Check with Score Caps (2026-04-17 추가)

모든 PR 은 4-gate check 를 받는다. 각 gate 의 pass/fail/N/A 상태가 score cap 을 결정한다. 출처: BASS Implementation Plan v6.0 §6.1 (방법론 참조).

### 9.1 Gate 정의

| Gate | 이름 | 충족 조건 | 증거 형식 |
|---|---|---|---|
| **G1** | COMPILE | `cargo build --lib --release` 성공 + 해당 PR 의 신규 test + 기존 test 슈트 regression 없음 | 터미널 output paste: "Finished N.Ns, 0 errors", "N passed; 0 failed" |
| **G2** | FLRW (quantitative) | FLRW 극한 수치 target 달성 (예: MB-95 ↔ PSTF D_ℓ 일치 ≤0.5%) | 구체 숫자 paste: "D_2 = 1002.086744 vs oracle 1002.086744, rel err 0e0" |
| **G3** | PHYS (physical consistency) | scaling / conservation / sign / dimensional consistency 검증 | 테스트 이름 + 검증 대상 identity 명시 |
| **G4** | CROSS (independent cross-check) | 독립 구현 / oracle 과의 cross-check | Oracle 명시 (CAMB, MB-95 Rust, v6.0 Python Path A 등) + 비교 결과 |

### 9.2 Score cap 규칙

| Score 허용 상한 | 조건 |
|---|---|
| ≤ 4 | G1 pass 안 됨 (code 가 실행되지 않음) |
| ≤ 6 | G1 pass, G2 pass 안 됨 또는 N/A (quantitative FLRW gate 없음) |
| ≤ 7 | G1/G2 pass, G3 pass 안 됨 |
| ≤ 8 | G1/G2/G3 pass, G4 pass 안 됨 |
| 9 | 4 gate 모두 pass, 다만 convergence figure / publication-ready 상태는 미완 |
| 10 | 4 gate + convergence campaign + publication-ready figure / table |

N/A 처리: 해당 gate 가 PR 의 성격상 적용 불가인 경우 (예: PR-020 같은 scaffolding PR 은 G2/G4 가 N/A). N/A 는 fail 과 동일하게 cap 에 반영한다 — scaffolding PR 의 최대 score 는 6. 이것은 정당한 결과이며, scaffolding 은 완성품이 아니므로 더 높은 점수를 받을 이유가 없다.

### 9.3 PR closure template 갱신

모든 PR closure delta 는 4-gate evidence block 을 포함해야 한다:

```markdown
## Gate evidence

| Gate | 상태 | 증거 |
|---|---|---|
| G1 COMPILE | ✅ / ❌ / N/A | [cargo output, test count] |
| G2 FLRW    | ✅ / ❌ / N/A | [numerical value, oracle comparison] |
| G3 PHYS    | ✅ / ❌ / N/A | [conservation/scaling test names] |
| G4 CROSS   | ✅ / ❌ / N/A | [oracle name + agreement metric] |

Score: N/10 (cap applied: [reason])
```

---

## §10. Anti-Local-Minimum Rule (2026-04-17 추가)

v6.0 §6.2 를 AI-session 단위로 환산하여 도입. 이것은 과거 "D_2 82→95% 나선" 처럼 한 이슈에 복수 세션이 투입되고 결과적으로 잘못된 approach 였음이 드러나는 패턴을 방지.

### 10.1 Rule statement

> **어떤 접근 (approach) 이 2회 연속 실패 (test fail, numerical mismatch, 예상과 다른 결과) 하고, 세 번째 시도가 이전 두 시도와 본질적으로 같은 논리를 사용한다면, STOP 한다.**

STOP 이후 mandatory actions:

1. **Document the stuck state**: 무엇을 시도했는지, 왜 실패했는지, 현재 가설 상태를 `docs/STUCK_LOG.md` (신설) 에 기록
2. **Move to next PR on critical path**: ROADMAP §9 의 "즉시 다음 행동" 에 나열된 다음 PR 로 이동
3. **Return in a fresh session**: 같은 세션에서 즉시 재시도 금지. 다음 세션에서 새 context 로 재진입

### 10.2 "Essentially same logic" 의 정의

다음은 "같은 logic" 으로 간주한다:

- Assertion tolerance 를 완화하는 것 (이전 실패를 tolerance 로 숨김)
- 같은 구현 경로에서 parameter / constant 만 바꾸는 것
- 실패 metric 의 해석을 바꾸어 "실은 문제 없다" 로 재분류하는 것

다음은 "새 logic" 으로 간주한다:

- 실패 원인의 근본 가설을 재정의하는 것 (예: "ULP 차이" → "공식 자체 오류")
- 다른 layer 에서 접근하는 것 (예: runtime assert → compile-time check)
- 다른 oracle / reference 로 비교 대상 을 바꾸는 것

### 10.3 예외

다음의 경우 rule 면제:

- **Typo / syntax error** — 이것은 재시도 횟수 카운트 안 함
- **Build system / tooling issue** — 본질적 물리 / 수학 문제 아님
- **User 가 명시적으로 같은 approach 계속 지시** — L1 지시가 L5 rule 보다 우선

### 10.4 PR-020 세션 retrospective

PR-020 에서 `flrw_norm_ratio_down` helper 가 ℓ=1 에서 factor-9 error 를 낸 시점이 이 rule 의 trigger 가 될 수 있었다. 실제로는 **1회 실패 후 즉시 helper 를 삭제하고 scope 를 축소** (PR-025 로 이관) 하여 STOP 기준에 도달하지 않았다. 이것은 rule 의 exemplary 동작 — 2회 반복 시도 전에 approach 자체를 재평가.

---

## §11. Hallucination Detection Checklist (2026-04-17 추가)

모든 PR closure 이전, 그리고 score 변경 시, 다음 checklist 를 통과해야 한다. 출처: v6.0 §6.4.

### 11.1 Mandatory evidence checklist

- [ ] **Code 가 실제로 실행되었다** — "it works" 주장 아닌, 이번 세션의 terminal output paste
- [ ] **FLRW gate 값이 이번 세션 run 에서 나왔다** — 기억 / 이전 세션 로그에서 복사 아님
- [ ] **새 test 가 실제로 주장된 기능을 testing 한다** — test 이름과 assertion 이 일치
- [ ] **새 module 이 import / call 가능하다** — 별도 import/call 확인 output paste
- [ ] **Figure / file 이 실제로 생성되었다** — 파일 사이즈 / 경로 paste, 주장만으로는 불충분

### 11.2 Score 상향 증거 요구

| Score 변경 | 필요 증거 |
|---|---|
| 3 → 4 | 식 / 규약 동결 문서 |
| 5 → 6 | `cargo build` 성공 + 기본 구조 존재 |
| → 7 | G1 + G2 + G3 evidence paste |
| → 8 | G2 의 구체 수치 (D_ℓ 비율, RMS, etc.) |
| → 9 | G4 cross-check 결과 (oracle 명시 + agreement metric) |
| → 10 | Convergence figure 또는 publication-ready deliverable + 파일 경로 |

### 11.3 AI-session 특이 주의사항

AI 보조 세션 (Claude 등) 에서 특히 주의:

- **긴 세션에서 summary 시 복제 금지** — 매 PR closure 마다 새로 측정. "앞서 확인한 바와 같이" 로 skip 금지.
- **연속 PR 간 numerical value 복사 금지** — PR-010 의 D_2 와 PR-020 의 D_2 가 bit-identical 이라 해도, 각 PR 의 closure 에서 각각 측정하여 paste.
- **"이 정도면 충분" 금지** — tolerance 를 구체 숫자로 명시. `1e-12` 대신 "12자리 일치" 라고 쓰지 않는다.

### 11.4 Self-audit template

PR closure delta 작성 전 self-check:

```markdown
## Self-audit (§11)

- [x] cargo output 이 이 세션의 실제 output 인가?  line [N] 에서 확인
- [x] D_ℓ value 가 이 세션에서 재측정 되었는가?  run time [elapsed s] 확인
- [x] 기존 test 슈트 N 개가 이 세션에서 실제 재실행 되었는가?  output paste 확인
- [x] 신규 test 가 주장하는 기능을 실제 test 하는가?  test name & assertion pair 확인
- [x] Score cap 이 §9 의 gate 결과와 일관되는가?
```

---

*Source: PR WBS TDD SDD v1.0. 마지막 갱신: 2026-04-17.*
