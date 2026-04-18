# BASS Stuck Log

> **Companion**: `docs/PR_CONSTITUTION.md` §10 (Anti-Local-Minimum Rule)
> **Purpose**: Rule §10 trigger 발동 시 (2회 연속 실패 + 같은 logic 3번째 시도 회피) stuck state 를 기록하여 다음 세션 재진입 시 context 복원.

---

## §1. Entry format

각 stuck event 는 다음 구조로 기록:

```markdown
### YYYY-MM-DD / Session-N / PR-NNN — [Short title]

**Attempts** (2 attempts before STOP):
1. [Attempt 1]: [what was tried] → [why it failed] → [numerical evidence]
2. [Attempt 2]: [what was tried] → [why it failed] → [numerical evidence]

**Hypothesis state at STOP**:
- Current working hypothesis: [...]
- Alternative hypotheses to explore: [...]
- What oracle / reference might resolve this: [...]

**STOP decision**:
- Moved to: [next PR on critical path]
- Resume planned: [session or PR that will return to this]
```

---

## §2. Active stuck entries

(No active entries as of 2026-04-17.)

---

## §3. Resolved stuck entries

### 2026-04-18 / PR-024a session / PSTF E-mode layout mismatch with MB-95 CambLayout

**Below-threshold fix** (did NOT reach 2-failure threshold — 1 iteration 으로 해결):

**Attempt 1** (panic on first run): `pstf_extract_source_inputs` 이 `layout.i_photon_e_m0(0)` 호출 → PSTF layout 의 E-mode accessor 가 ℓ≥2 만 허용 (assertion `"i_photon_e_m0: ell={} must be ≥ 2"`). 9/10 tests panic (pol-off caveat test 만 통과).

**Root cause**:
- PSTF `LmLayout`: `n_photon_e = (lg+1)² − 4` excludes ℓ∈{0,1} slots (E-mode 가 scalar perturbation 에서 ℓ<2 는 identically zero — structural optimization).
- MB-95 `CambLayout`: retains `e_mode(0)` slot for PiBass convention (`Π_BASS = Θ_2 + E_0 + E_2`).
- PR-010 production path 는 Polter convention (`polter = 2Θ_2/5 + 3E_2/5`) — **E_0 미사용**.

**Resolution**: `e0 = 0.0` unconditional. Polter convention 에서 E_0 가 source output 에 기여하지 않으므로 MB-95 production 과 bit-identical 유지.

```rust
// BEFORE (panicked):
let (e0, e2) = if layout.has_pol() {
    (state[layout.i_photon_e_m0(0)], state[layout.i_photon_e_m0(2)])
} else {
    (0.0, 0.0)
};

// AFTER:
let e0 = 0.0;  // Polter convention unused; PiBass future PR will handle
let e2 = if layout.has_pol() && layout.ell_max_gamma >= 2 {
    state[layout.i_photon_e_m0(2)]
} else { 0.0 };
```

**Verification**: 10/10 tests pass (2nd attempt), D_2 = 1002.086744 14th consecutive bit-identical. `regression_source_total_matches_mb95` 가 bit-identical 검증.

**Lesson**: Pre-audit §4 가 10 tests 를 열거했으나 **layout accessor range assumption** 은 검토 안 됨. Future pre-audit 에 다음 항목 추가:

> **Layout accessor range check** — 새 파일이 호출하는 모든 `i_*_m0(ell)` accessor 에 대해 허용 ell range 를 pre-audit design doc 에 명시. 특히 E-mode/B-mode 가 ℓ≥2 만 허용함을 인지.

Streak impact: PR-022b/c, PR-023a/b/c 의 5 PR 연속 first-try success streak 이 PR-024a 에서 1회 iteration 으로 끊김. PR-024b 부터 streak 재시작.

---

### 2026-04-17 / PR-020 session / PstfFlrwLayout normalization

**Preemptive resolution** (did NOT reach 2-failure threshold):

**Attempt 1**: `flrw_norm_ratio_down(ℓ) = (2ℓ+1)/(2ℓ−1)` 로 PSTF `coupling::free_streaming_down(ℓ) = ℓ/(2ℓ−1)` 를 MB-95 `ℓ/(2ℓ+1)` 로 변환하는 identity test 설계.

Test ran: `ell=1` 에서 `PSTF-down · norm = 1 · 3 = 3` 이지만 MB-95 기대값은 `1/3`. **factor-9 error**.

**Resolution path chosen** (2nd attempt 시도 전에 접근 재평가):

이것은 "tolerance 를 완화" 하거나 "parameter 만 바꾸는" 같은 logic 의 반복이 아니라, **approach 자체의 근본 재평가** 가 필요한 상황이라 판단. PSTF ↔ MB-95 FLRW equivalence 는 단순 per-coefficient 비율 아니라 STF-to-spherical-harmonic projection + normalization 의 complete chain 이 필요하며, 이는 PR-020 (scaffolding) 의 scope 을 벗어남.

조치:
- `flrw_norm_ratio_down` helper 삭제
- Identity test #1 의 claim 을 "PSTF coupling values are self-consistent with their own doc-string definitions" 로 축소
- 정식 FLRW equivalence 유도는 PR-025 로 이관 (이미 ROADMAP v2.0 §4 에 명시되어 있었음)

**Lesson**: Rule §10 의 exemplary 사례. 2회 반복 전에 approach 재평가가 정답. Pre-audit design doc (`pr-020-design.md §8`) 에서 "Metric sector — code 로 옮길 때 sign/factor 주의" 경고가 있었던 것이 조기 탐지에 기여.

---

## §4. 분석 지표

### 4.1 Stuck event frequency

- 2026-04-17: preemptive resolution 1건 (PR-020 norm ratio), 실제 STOP 0건
- 2026-04-18: below-threshold fix 1건 (PR-024a E-mode layout mismatch, 1 iteration), 실제 STOP 0건
- **Cumulative**: 2 events (both resolved < 2 iterations), 0 STOP events. §10 rule 이 정확히 작동 — 2회 실패 전에 root cause 를 찾아 resolve.

### 4.2 Resolution latency

실제 STOP event 가 아직 없음. 향후 event 발생 시 resolution 이 몇 세션 / 며칠 걸렸는지 여기 기록하여 governance 효과 측정.

---

## §5. 관계된 문서

- `docs/PR_CONSTITUTION.md` §10 — rule 정의
- `docs/ROADMAP_PHASE_I_TO_L.md` §9 — "즉시 다음 행동" 목록 (STOP 시 이동 대상)
- 개별 `docs/PR_DELTAS/pr-NNN-design.md` §8 — pre-audit risks (pre-emptive flagging)
