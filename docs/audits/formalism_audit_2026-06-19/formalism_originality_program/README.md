# Statistical Formalism — 독창성 심사 + 발전/개선/확장 프로그램

`x_C / Q / Π / F / G_F` 형식론의 **독창성(originality)** 을 적대적 감사 위에서 심사하고, 실제 novelty가 사라지지 않도록 개편/방어/업그레이드 + 추가 수치실험을 묶은 패키지입니다.

---

## TL;DR (한국어)

- **핵심 논지 (novelty inversion):** 감사는 형식론을 *건전하다* 고 판정했습니다. 따라서 이 형식론의 독창성은 *탐지(detection)* 가 아니라 **아키텍처/방법론** 입니다 — 부호 있는 departure 좌표 + **기계검증 가능한 semantic firewall**(과대주장 시 객체 생성 자체를 거부) + fail-closed 인증 + typed 진단↔추론 경계. "detection" 문구를 빼는 비용은 0이고, 그래야 진짜 기여가 드러납니다.
- **flagship (F1):** *과대주장을 구조적으로 거부하는* 진단 통계 — reserved-language 거부 + owner/tier 고정 + fail-closed 게이트, 적대적 테스트로 검증. blinding/사전등록/multiverse는 *분석 선택*을 보호하지만, 진단을 *증거로 잘못 라벨링하는 것*을 막지는 못합니다. 그것이 이 형식론의 빈틈을 메우는 지점입니다.
- **감사가 만들어낸 새 기여 3개:** F7 sector-resolved departure vector + cancellation 1급 보고(=`x_C≈0`은 등방성이 아님), F8 total-anisotropy magnitude companion(="filling fraction" 오해 차단), F9 firewall 명세 + adversarial fuzzer.
- **방법론 포지셔닝:** 독립적인 *methods 논문* ("A Claim-Tiered, Contract-Enforced Diagnostic Algebra for Quantifying FLRW Departure") 또는 물리 논문의 방법론 backbone. 어떤 detection도 주장하지 않습니다.
- **최소 검증 세트:** E1(cancellation 정직성) + E2(fail-closed 검증) + E6(firewall 적대적 증명). `code/`의 모든 실험은 의존성 없는 `reference_formalism.py` 위에서 `run_all.py`로 즉시 실행됩니다 (6/6 통과 확인).
- **주의:** `code/`의 생성 모델/prior는 *예시(illustrative)* 이며 관측치가 아닙니다. 메커니즘(상쇄/인증/등록/깊이-기울기 판별)을 보이기 위한 것이고, 수치 자체는 자리표시자입니다.

---

## 무엇이 진짜 새로운가 (요약)

| ID | 기여 | 새 산출물 |
|----|------|-----------|
| F1 ★ | 과대주장 거부 semantic firewall (기계검증) | 보장(거부) |
| F2 | 부호 있는 comparator-projection `x_C` + cancellation_index | cancellation_index |
| F3 | fail-closed 인증 filling fraction `F` (clipping 없음) | — |
| F4 | registered-threshold exceedance `Π` (post-hoc 거부) | — |
| F5 | 분모-진화 분리 depth gap `G_F` | denominator split |
| F6 | typed 진단↔추론(MIO↔HTT) 경계 | — |
| F7 ✦새 | sector-resolved departure vector + cancellation 1급 | 부호 sector profile |
| F8 ✦새 | `F`의 비부호 total-anisotropy magnitude 동반자 | magnitude M |
| F9 ✦새 | firewall 명세 + adversarial fuzzer + label linter | 명세+fuzzer+linter |

`06_PRIOR_ART_POSITIONING.md` 의 결론: blinding(DES)·사전등록·multiverse/specification-curve(Steegen 2016; Gelman & Loken)는 *관행* 으로서 분석 선택을 보호. 이 형식론은 그 아이디어를 **타입화된 기계검증 계약** 으로 인코딩하고, 거의 선례가 없는 두 가지를 더함: (1) 과대주장 객체 생성을 거부하는 semantic firewall, (2) 진단을 증거로 세탁하지 못하게 하는 typed 경계.

---

## Contents (English)

| File | Purpose |
|------|---------|
| `00_STRATEGIC_OVERVIEW.md` | Novelty inversion; the originality is the architecture; honesty↔novelty pairing; delete/demote/keep/upgrade; risk register |
| `01_NOVELTY_LEDGER.md` | F1–F9 ranked, each with tier, novelty vs prior art, audit status, one-line defense |
| `02_REFRAME_AND_REORG.md` | Methods-paper framing: model abstract, contribution paragraph, claim ladder, section plan, titles, cover note |
| `03_UPGRADE_PLAN.md` | U1–U5: turn audit findings into stronger contributions, with acceptance criteria |
| `04_EXPERIMENT_PROGRAM.md` | E1–E7 numerical experiments (hypothesis / method / produces / success / effort) |
| `05_DEFENSE_DOSSIER.md` | Anticipated objections O1–O11 → concede-and-defend responses; response-letter template |
| `06_PRIOR_ART_POSITIONING.md` | CRAG novelty map: reproducibility-methodology axis + anisotropy-statistics axis; per-neighbor delta; citations |
| `experiment_tracker.xlsx` | Novelty Ledger (F1–F9), Upgrades (U1–U5), Experiments (E1–E7), Summary (zero formula errors) |
| `code/reference_formalism.py` | Dependency-free reference impl of `x_C/Q/Π/F/G_F` + F7 `DepartureProfile` + F8 magnitude + F9 firewall/registry |
| `code/exp01_cancellation_null.py` | E1 — cancellation null distribution |
| `code/exp02_F_failclosed_coverage.py` | E2 — `F` fail-closed coverage |
| `code/exp03_Pi_threshold_bias.py` | E3 — `Π` threshold-registration bias |
| `code/exp04_GF_matched_null_boost_vs_tilt.py` | E4 — `G_F` matched-null + boost-vs-tilt depth discriminant |
| `code/exp05_comparator_sensitivity.py` | E5 — comparator multiverse for `x_C/Q` |
| `code/semantic_firewall_fuzz.py` | E6 firewall fuzz + E7 MIO↔HTT leakage audit |
| `code/run_all.py` | Run E1–E7 end to end |

## Run

```bash
cd code
python3 run_all.py          # all experiments (stdlib only, Python 3.10+)
python3 exp01_cancellation_null.py    # or any single experiment
```

No third-party packages required for the experiments. (`experiment_tracker.xlsx` was built with `openpyxl` and recalculated with LibreOffice; the experiments themselves need neither.)

---

## What this is / isn't

- **Is:** an originality assessment + a concrete program (reframe, defense, upgrades, experiments, runnable reference code) that preserves the formalism's genuine novelty while implementing the audit's honesty corrections.
- **Isn't:** a detection, evidence, posterior, family-ID, or native-solver claim. The contribution is the architecture and its machine-checked guarantees. The `code/` generative models are illustrative placeholders, not observational results.
