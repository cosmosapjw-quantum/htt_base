# BASELINE FREEZE — 2026-04-16

본 문서는 BASS remediation (REMEDIATION_PLAN_v2) 의 **baseline 측정 기록**이다.
PR-00 의 산출물이며, 이후 모든 PR 은 본 문서와 `tests/fixtures/baseline_2026_04_16.json`
을 기준점으로 삼는다.

---

## 1. 무엇을 동결했는가

- **Git 시점**: commit `b654be0`, tag `baseline-2026-04-16`
- **측정 시각**: 2026-04-16 (UTC)
- **Cosmology**: `VisibilityParams::planck2018`
  - H₀ = 67.36, Ω_b h² = 0.02237, Ω_c h² = 0.1200
  - τ_reion = 0.0544, T_CMB = 2.7255 K
  - n_s = 0.9649, A_s = 2.1×10⁻⁹
  - Σm_ν = 0.06 eV, N_eff = 3.044

---

## 2. 측정된 3 개 Config

| Config key | Test | DOF | Params | Status |
|---|---|---|---|---|
| `config_24dof_no_pol_no_mnu` | `test_dl_200k` | 24 | lmax_pol=0, no mν | **VALIDATED** |
| `config_38dof_with_pol_no_mnu` | `test_dl_200k_epol` | 38 | lmax_pol=12, no mν | **BLOCKED** |
| `config_128dof_full_physics_n_k_50` | `test_dl_50k_full` | 128 | full_physics, n_k=50 | **BLOCKED** |

### 2.1 Config 24 DOF — Primary baseline (VALIDATED)

200/200 k-modes 가 모두 수렴했다. 73 초 wall time. 6 ℓ-point 측정:

```
  ℓ      BASS     CAMB    ratio
─────────────────────────────────
   2    978.8   1022.0    0.958
  10    927.4   1130.0    0.821
  30   1219.6   1070.0    1.140
 100   2917.3   2611.0    1.117
 200   4616.2   5733.0    0.805
 300   4963.5   6136.0    0.809
```

**이 config 가 본 remediation 의 primary metric 원천이다.** Progress ledger 의
D₂ ratio 열은 본 config 기준이다.

### 2.2 Config 38 DOF — Polarization ON (BLOCKED)

lmax_pol=12 를 켜자마자 recombination zone (η ≈ 2.63) 에서 모든 k-mode 가
`h_min reached` 로 실패한다. 200 개 중 57 개만 완주하고, 완주한 것들도
D_ℓ 가 ~10⁸²μK² 정도로 폭주. 원인은 **Θ₂–E₂ coupling 의 고유값이
+3κ'/5 가 되어 ODE 가 tight coupling 구간에서 발산**하는 것 (BASS_STATUS
§3.4 에 이미 기록됨).

본 config 의 baseline 은 "발산" 이다. 본 config 가 **VALIDATED 로 전환되는 시점**이
TCA 가 실제로 동작함을 증명한다. 본 plan 에서 TCA 구현은 PR-08 이후 P1-series 작업이지만,
그 전에라도 PR-04 (late-metric) 와 결합된 완화 효과가 일부 나타날 수 있다.

### 2.3 Config 128 DOF — Full physics (BLOCKED)

`ProductionConfig::full_physics()` + n_k=50 로 가장 가벼운 full-physics 측정을
시도했으나 **50 개 k-mode 가 모두 실패**. Θ₂–E₂ instability 가 massive-ν 계에서도
그대로 나타난다. Sandbox 환경에서는 timeout (> 300 s) 을 넘기고,
실제 하드웨어에서도 수렴이 보장되지 않는다.

본 config 의 unblock 은 PR-06 (massive-ν background) 와 PR-08 closure 후의
통합 재측정에서 평가된다.

---

## 3. 왜 2 개 config 가 BLOCKED 인가

Anti-hallucination 관점에서, 측정 시점에 동작하지 않는 config 를 측정 불가로
기록하는 것이 정직하다. "이후 개선 주장"이 가능해지려면 *무엇이 개선됐는지*
측정 가능한 기준점이 있어야 한다.

BLOCKED 도 **baseline 의 정보**다: "이 config 는 이 상태에서 시작했다" 라는
기록이 있어야 "이 PR 이 이 config 를 unblock 했다" 는 주장이 검증 가능하다.

---

## 4. 문서 불일치 — 의도적 기록

`BASS_STATUS_2026-04-12.md` 는 24 DOF config 의 D₂ 를 **1038 (101.5% CAMB)**
로 기록한다. 그러나 본 PR-00 측정은 **978.8 (95.8% CAMB)** 이다.

이 불일치는 fixture 에도 그대로 기록된다. 가능한 원인:
- BASS_STATUS 작성 시점 이후 코드가 변경됐으나 문서가 갱신되지 않았거나
- 측정 config 가 달랐거나
- post-processing (ISW 추가 방식, E-mode wiring 등) 차이

어느 쪽이든 **본 plan 은 문서 수치가 아니라 fixture 수치를 baseline 으로 삼는다.**
PR-10 (docs reconcile) 단계에서 BASS_STATUS 차기 버전이 fixture 와 정합하도록
갱신한다.

이 불일치 자체가 PR-00 이 왜 필요했는지를 증명한다. "현재 코드 상태" 와
"문서에 기록된 코드 상태" 사이에 존재하는 gap 을 fixture 가 채운다.

---

## 5. 각 config 를 unblock / improve 시킬 PR

| Config | Unblock/Improve 책임 PR | 기대 효과 |
|---|---|---|
| 24 DOF (VALIDATED) | PR-02 → PR-04 → PR-05 → PR-08 | D₂ 0.958 → 0.95–1.05 범위 유지, 고 ℓ ratio 정규화 |
| 38 DOF (BLOCKED) | TCA 구현 (post PR-08, P1-series) | "발산" → measurable D_ℓ |
| 128 DOF (BLOCKED) | PR-06 + TCA | "발산" → measurable D_ℓ |

본 plan 에서 **38/128 DOF 의 unblock 은 primary success criterion 이 아니다.**
본 plan 은 24 DOF 의 D_ℓ/CAMB ratio 를 ±5% 안으로 가두는 것을 목표로 한다.
TCA 구현은 본 plan closure 후 별도 plan 에서 다룬다.

---

## 6. 회귀 측정법

새 PR closure 시:

```bash
python scripts/measure_dl_regression.py --primary-only   # 24 DOF 만 (빠름, ~73s)
python scripts/measure_dl_regression.py                   # 3 config 모두 (느림)
```

Output 예시:
```
[config_24dof_no_pol_no_mnu]
  baseline status : VALIDATED
  current status  : VALIDATED
  k-modes         : 200/200
    ell   baseline    current      delta     rel
      2     978.80    1005.40     +26.60   +2.72%  ← improved (closer to CAMB)
     10     927.40     940.20     +12.80   +1.38%  ← improved
    ...
```

결과는 본 문서 §7 ledger 에 기록한다.

---

## 7. Ledger (매 PR closure 시 갱신)

| 시점 | Git tag | Config 24 DOF D₂ | ratio | 비고 |
|---|---|---|---|---|
| baseline | baseline-2026-04-16 | 978.8 | 0.958 | PR-00 완료 |
| PR-PERF-01 | — (commit 33edffb) | 978.8 | 0.958 | mimalloc + CommonProfile + scratch + par_chunks. D_2 비트-동일. Sandbox wall 72.6→53s (-27%, mimalloc 단독). Mini config 추가. |
| PR-01 | — | — | — | pending |
| PR-02 | — | — | — | pending |
| PR-03 | — | — | — | pending |
| PR-04 | — | — | — | pending |
| PR-05 | — | — | — | pending |
| PR-06 | — | — | — | pending |
| PR-08 | — | — | — | pending |

---

## 8. 파일 목록

- `tests/fixtures/baseline_2026_04_16.json` — 불변 fixture (schema v1)
- `scripts/measure_dl_regression.py` — 회귀 측정 스크립트
- `BASELINE_FREEZE.md` — 본 문서
- `CHANGELOG.md` — PR 단위 변경 기록
- `logs/baseline_200k.log`, `logs/baseline_200k_epol.log`, `logs/baseline_50k_full.log` — 원본 측정 로그 (재현 가능)

---

*문서 끝.*
