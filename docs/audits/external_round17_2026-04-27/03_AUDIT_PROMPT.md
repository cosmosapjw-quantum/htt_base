# BASS Phase-1 Closure — External Audit Prompt
**Date prepared:** 2026-04-27.   **Bundle commit:** `02cb6c0`.

This document is the **prompt to send to an external auditor** (LLM or human) along with the full audit bundle. Two language variants below — pick whichever fits the recipient. The English version is canonical; the Korean version is paraphrased for native-Korean reviewers.

---

## English (canonical)

> You are an independent reviewer asked to audit a closure problem in the
> BASS (Bianchi Anisotropy Solver) cosmology code. The repo is dual-track:
> a Rust path (`bass_rs/src/sync_gauge_camb.rs`, MB-95 synchronous-gauge
> production, 7363 lines) currently produces the FLRW Planck-2018 anchor
> `D_2 = 1002.086744 μK²` bit-identically; a Python "PSTF primary" path
> (1+3 covariant tetrad-PSTF formulation, ~20 modules under `htt/bass/`)
> must reproduce that anchor to within 1 × 10⁻⁹ fractional tolerance for
> Phase 1 of the project to close. The Python path's two entry points
> currently produce:
>
> | Path | D_2 (μK²) | Ratio vs anchor |
> |---|---:|---:|
> | Rust MB-95 anchor | 1002.086744 | 1.00 |
> | Python canonical (`compute_flrw_d_ell`) | 2.0451 × 10¹⁰ | 2.04 × 10⁷ |
> | Python linear-probe (`compute_flrw_d_ell_linear_probe`) | 6.4395 × 10³ | 6.43 |
>
> The 7-orders-of-magnitude canonical-vs-linear-probe gap is fully
> attributable to a `max(|Σ_±|, 1e-6) = 1e-6` floor that the canonical
> path's `unit_amplitude_normalization=True` toggle applies in the FLRW
> limit (boosts `|α|²` by ~10¹²); closure of that gap is mechanical.
> The open question is the **6.43× linear-probe-vs-anchor residual**.
>
> Three audit cycles (10 external auditor verdicts; Rounds 12–14) plus
> 6 internal investigation rounds have triangulated the residual to a
> single architectural defect — **D-2**: the Lowell §13.2 leading-order
> regular-adiabatic seed (`_seed_formulae` at
> `htt/bass/perturbation/regular_adiabatic_ic.py:104–209`) is valid only
> for `x = k · η_init ≪ 1`; at `η_init = 261 Mpc` the validity boundary
> is `k ≈ 4 × 10⁻³ Mpc⁻¹`; the regression-test k-grid
> `np.logspace(-4.0, -1.5, 65)` has ~60 % of points in `x > 1` invalid
> territory; the IMEX integrator faithfully evolves the wrongly-seeded
> sub-horizon modes forward; over-amplification of `Φ, Ψ, Θ_0` at
> recombination produces the observed 6.43× residual. The proposed
> closure is to push `η_init` back to `z ≈ 10⁹` using the conditional
> inline DAE-relaxation already implemented at
> `htt/bass/hierarchy/integrator.py:434–498` (which pins `ℓ = 2 m = 0`
> to its algebraic Thomson-coupled value when
> `Γ_T / H > closure.gamma_threshold_over_H`). This is multi-month work.
>
> **What we want from you (in priority order):**
>
> 1. **Validate or refute the D-2 diagnosis.** Read
>    `02_AUDIT_FOCUSED_SUMMARY.md` (15 min) and
>    `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` (10 min).
>    Then read the seed code (`code/regular_adiabatic_ic.py:104–209`)
>    and the closure-test config (`code/test_d2_pstf_closure.py`).
>    Is the diagnosis (Lowell asymptotic-series breakdown at
>    sub-horizon `x = k · η_init`) correct? If yes, give the most
>    direct counter-test we could run to rule out alternative
>    explanations. If no, what is your alternative diagnosis, and
>    what observable distinguishes it from D-2?
>
> 2. **Validate or refute the closure mechanism.** The proposed
>    fix (`δ` sub-track) is to extend `η_init` from 261 Mpc to ~10⁻³ Mpc
>    (z ≈ 10⁹) and rely on the conditional inline DAE-relaxation at
>    `code/integrator.py:434–498` to handle the radiation-era TCA
>    regime. Read `01_DETAILED_ANALYSIS.md §11, §18, §29` for context.
>    Concerns we need you to weigh:
>     - The IMEX integrator is proven stable across 5 decades
>       (η = 261 → 14147 Mpc) post Round-15. Extending to 12 decades
>       (η = 10⁻³ → 14147 Mpc) requires per-decade conservation-law
>       audit. Is there a physics reason this would *not* extend
>       smoothly?
>     - The DAE-relaxation pins **only** ℓ = 2 m = 0 algebraically.
>       Free-stream ℓ ≥ 3, evolve ℓ = 0, 1 normally. In deep TCA
>       (`Γ_T / H ~ 10⁹` at z = 10⁹), should higher-ℓ photon
>       multipoles also be pinned? Does the BASS choice match
>       canonical CAMB practice?
>     - The relax-rate is `a · Γ_T`. At `Γ_T / H ~ 10⁹` the rate
>       becomes very stiff. Does the IMEX implicit stage handle this
>       robustly, or do we need a smoother dispatch?
>
> 3. **Identify defects we may have missed.** The R12-14 cycle
>    converged on D-1 / D-2 / D-3 as the three-defect set. D-1 is
>    closed (Round-15 P0); D-3 is documented but parked. Are there
>    *other* architectural defects in the FLRW pipeline that could
>    contribute to a 6.43× residual with the observed N_k-trajectory
>    and per-(k, ℓ) variance pattern? Specifically check:
>     - Source-extractor sign convention at
>       `tier_b_source_extraction.py:225`
>     - PSTF normalization at the LoS projector
>       (`flrw_bessel_projector.py`)
>     - Polarization quadrupole basis convention (Π_BASS = Θ_2 + E_0 + E_2
>       vs polter = 2Θ_2/5 + 3E_2/5; see `docs/SSOT_POLICY.md §2.3`)
>     - Background-table interpolation strategy (HYREC visibility is
>       shared between Rust and Python paths; interpolation strategies
>       differ)
>
> 4. **Sub-track ordering judgment.** Current planning has the order
>    α (a-switch, 1-2d) → β (real-IC, 1-2d) → γ (m∈{-2..+2}, 3-5d) →
>    δ (D-2, multi-month). D-3 is parked behind these. Is this the
>    right ordering? Should D-3 (sub-week) be closed before δ
>    (multi-month) to avoid conflating its effect with seed-validity
>    in any δ measurement budget?
>
> **Forbidden moves (these have been litigated; do NOT propose them):**
>
> - Doppler `(g v_b)′ → (1/k) d/dη[g v_b]` rewrite — empirically falsified
>   2026-04-26 (0.012 % effect, not the spec-claimed 0.5 %), retracted in
>   Round-16 P2; banned by the in-tree regression-armor test
>   `code/test_flrw_bessel_projector.py::test_sharp_visibility_doppler_analytic_protects_no_over_k_patch`
>   (not included in this bundle for size; the test is in the repo at
>   `htt/bass/los/test_flrw_bessel_projector.py`).
> - Single multiplicative `calibration_factor` for the 6.43× — refuted
>   by R14 finding F1 (per-(k, ℓ) std/|mean| 108–357 % across all
>   candidates).
> - Higher-x correction terms in `_seed_formulae` (D-2b sub-option) —
>   non-viable; series asymptotic, ~20 orders required at `x = 14`,
>   then divergent.
> - TCA *pre-phase* (unconditional analytic replacement of the photon
>   hierarchy in an initial η-window) — banned per
>   `CLAUDE.md §6` "approximation-free truth engine" mandate. The
>   *conditional inline* DAE-relaxation is the permitted mechanism.
> - HYBRID architecture (CAMB transfer for FLRW limit, BASS PSTF for
>   Bianchi correction) — recommended 4/4 by Round-14 auditors,
>   user-rejected 2026-04-25 because production code must remain
>   self-contained without external CAMB runtime dependency. CAMB
>   stays as audit oracle only.
>
> **Bundle layout:**
>
> ```
> 00_README.md                    — bundle map + usage notes
> 01_DETAILED_ANALYSIS.md         — ~25 KB self-contained tech analysis
> 02_AUDIT_FOCUSED_SUMMARY.md     — 15-min audit brief (read first)
> 03_AUDIT_PROMPT.md              — this prompt
> code/                           — 7 source files (small enough to inline)
> reference_docs/                 — 6 internal investigation docs + CLAUDE_md_excerpt.md
> ```
>
> **What you should output:**
>
> A markdown report (no length limit, but be focused). Structure
> suggestion:
>
> - **Verdict** (1 sentence per question Q1–Q4; clear CONFIRMED /
>   PARTIALLY-CONFIRMED / REFUTED labels matching prior audit
>   convention).
> - **Reasoning** (per-question, link to evidence in the bundle by
>   relative path).
> - **Counter-tests** (concrete diagnostic scripts or measurements
>   that would distinguish your verdict from the alternatives).
> - **Risks** (specific technical risks in the proposed closure
>   path that we should plan around).
> - **Confidence** (your subjective confidence in each verdict on a
>   1–5 scale, with the reasoning you'd update on).
>
> Use file-path-and-line-number citations
> (`code/regular_adiabatic_ic.py:142–186`) so we can navigate
> directly. If you propose a counter-test, give the exact
> diagnostic-script delta (modify which file at which line; or write
> a new script to which path).
>
> Reproduction note: the 31-minute reference measurement is
> reproducible via `python scripts/v5_round17_linear_probe_measurement.py`
> from the repo root after a venv is set up (Python 3.11, numpy + scipy
> + numba). The bundle's `code/` directory contains the script for
> reference; running it requires the full repo, not just the bundle.

---

## Korean (paraphrase)

> 당신은 BASS (Bianchi Anisotropy Solver) 우주론 코드의 closure 문제에
> 대한 독립 감사를 의뢰받은 reviewer입니다. 이 repo는 이중 경로
> 아키텍처를 가지고 있습니다: Rust 경로(`bass_rs/src/sync_gauge_camb.rs`,
> Ma-Bertschinger 1995 synchronous-gauge production, 7363줄)는 현재
> FLRW Planck-2018 anchor `D_2 = 1002.086744 μK²` 를 bit-identical로
> 생산 중이고, Python "PSTF primary" 경로 (1+3 covariant tetrad-PSTF,
> `htt/bass/` 아래 ~20개 모듈) 는 같은 anchor를 1 × 10⁻⁹ fractional
> tolerance 이내로 재현해야 Phase 1이 닫힙니다. Python 경로의 두 entry
> point의 현재 결과:
>
> | 경로 | D_2 (μK²) | anchor 대비 비율 |
> |---|---:|---:|
> | Rust MB-95 anchor | 1002.086744 | 1.00 |
> | Python canonical (`compute_flrw_d_ell`) | 2.0451 × 10¹⁰ | 2.04 × 10⁷ |
> | Python linear-probe (`compute_flrw_d_ell_linear_probe`) | 6.4395 × 10³ | 6.43 |
>
> canonical 대비 linear-probe의 7 orders-of-magnitude gap은 canonical
> 경로의 `unit_amplitude_normalization=True` 토글이 FLRW limit
> (Σ_± = 0)에서 적용하는 `max(|Σ_±|, 1e-6) = 1e-6` floor (|α|² 를 ~10¹²
> 부풀림)로 완전히 설명됩니다; 그 부분은 mechanical 수정 (1-2일).
> **남은 open question은 6.43× linear-probe-vs-anchor 잔차** 입니다.
>
> 3차에 걸친 audit 사이클 (10 외부 auditor verdict, Rounds 12-14) +
> 6회 내부 조사 라운드에서 잔차는 단일 architectural defect — **D-2**:
> Lowell §13.2 leading-order regular-adiabatic seed
> (`htt/bass/perturbation/regular_adiabatic_ic.py:104-209` 의
> `_seed_formulae`) 가 `x = k · η_init ≪ 1` 일 때만 유효한데,
> `η_init = 261 Mpc` 에서 validity boundary 가 `k ≈ 4 × 10⁻³ Mpc⁻¹` 이고
> regression test k-grid `np.logspace(-4.0, -1.5, 65)` 의 약 60% 가
> `x > 1` invalid territory에 위치 — 로 triangulated 되었습니다. IMEX
> integrator 가 잘못 seed 된 sub-horizon mode 들을 그대로 evolve 시켜
> recombination 에서 `Φ, Ψ, Θ_0` 가 over-amplify 되어 6.43× 잔차가
> 나타납니다. 제안된 closure 는 `η_init` 을 `z ≈ 10⁹` 까지 뒤로 밀고,
> `htt/bass/hierarchy/integrator.py:434-498` 에 이미 구현된 conditional
> inline DAE-relaxation (조건 `Γ_T / H > closure.gamma_threshold_over_H`
> 일 때 `ℓ = 2 m = 0` 을 algebraic Thomson-coupled value 에 pin) 을
> 사용해 radiation-era TCA regime 를 처리하는 것입니다.
> Multi-month 작업입니다.
>
> **부탁드리는 것 (우선순위 순):**
>
> 1. **D-2 진단 검증 또는 반박.** `02_AUDIT_FOCUSED_SUMMARY.md` (15분) 와
>    `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` (10분) 를
>    먼저 읽고, seed code (`code/regular_adiabatic_ic.py:104-209`) 와
>    closure test config (`code/test_d2_pstf_closure.py`) 를 봐주세요.
>    진단(Lowell asymptotic-series breakdown at sub-horizon
>    `x = k · η_init`)이 맞습니까? 맞다면, 대안 가설을 배제할 가장 직접적인
>    counter-test 는 무엇입니까? 틀리다면, 대안 진단과 D-2 와 구별되는
>    observable 은 무엇입니까?
>
> 2. **Closure mechanism 검증 또는 반박.** 제안된 fix (`δ` sub-track) 는
>    `η_init` 을 261 Mpc 에서 약 10⁻³ Mpc (z ≈ 10⁹) 까지 확장하고
>    `code/integrator.py:434-498` 의 conditional inline DAE-relaxation 에
>    의지해 radiation-era TCA regime 을 처리하는 것입니다.
>    `01_DETAILED_ANALYSIS.md §11, §18, §29` 를 참고해주세요. 검토 포인트:
>     - IMEX 가 5 decade 범위 (η = 261 → 14147 Mpc) 에서 안정 확인됨
>       (Round-15 후). 12 decade (η = 10⁻³ → 14147 Mpc) 까지 확장 가능?
>       Per-decade conservation-law audit 필요. 매끄럽게 확장 *되지 않을*
>       물리적 이유가 있나요?
>     - DAE-relaxation 은 **오직 ℓ = 2 m = 0** 만 algebraic pin. ℓ ≥ 3
>       자유 free-stream, ℓ = 0, 1 정상 evolve. Deep TCA 에서
>       (`Γ_T / H ~ 10⁹` at z = 10⁹) higher-ℓ photon multipole 도 pin
>       해야 하나요? BASS 선택이 canonical CAMB practice 와 일치하나요?
>     - relax-rate 는 `a · Γ_T`. `Γ_T / H ~ 10⁹` 에서 매우 stiff.
>       IMEX implicit stage 가 robust 하게 처리하나요, 아니면 부드러운
>       dispatch 가 필요한가요?
>
> 3. **놓친 defect 식별.** R12-14 cycle 은 D-1 / D-2 / D-3 으로 수렴했고,
>    D-1 은 닫혔으며 (Round-15 P0), D-3 는 문서화되었지만 보류 중입니다.
>    관측된 N_k-trajectory 와 per-(k, ℓ) variance pattern 과 일관된
>    *다른* architectural defect 가 FLRW pipeline 에 있을 수 있나요?
>    구체적으로:
>     - `tier_b_source_extraction.py:225` 의 source-extractor 부호 convention
>     - LoS projector (`flrw_bessel_projector.py`) 의 PSTF normalization
>     - 편광 quadrupole basis convention (`Π_BASS = Θ_2 + E_0 + E_2` vs
>       `polter = 2Θ_2/5 + 3E_2/5`, `docs/SSOT_POLICY.md §2.3`)
>     - 배경 table 보간 strategy (HYREC visibility 는 Rust/Python 공유,
>       interpolation strategy 다름)
>
> 4. **Sub-track 순서 판단.** 현재 계획: α (a-switch, 1-2일) → β (real-IC,
>    1-2일) → γ (m∈{-2..+2}, 3-5일) → δ (D-2, multi-month). D-3 는 이들
>    뒤에 보류. 올바른 순서인가요? D-3 (sub-week) 를 δ (multi-month)
>    이전에 닫아 δ measurement budget 에 효과가 섞이지 않게 해야 하나요?
>
> **Forbidden moves (이미 litigate 되었음; 절대 제안 마세요):**
>
> - Doppler `(g v_b)′ → (1/k) d/dη[g v_b]` 재작성 — 2026-04-26 경험적
>   반박 (0.012 % 효과, spec 주장 0.5 % 아님), Round-16 P2 retracted;
>   in-tree regression armor test 가 보호 중.
> - 6.43× 에 대한 단일 multiplicative `calibration_factor` — R14 finding F1
>   (모든 후보에 대해 per-(k, ℓ) std/|mean| 108-357%) 가 반박.
> - `_seed_formulae` 에 higher-x correction term 추가 (D-2b 옵션) —
>   비현실적; series 가 asymptotic, `x = 14` 에서 ~20 차 필요, 그 다음
>   divergent.
> - TCA *pre-phase* (initial η-window 에서 photon hierarchy 의 무조건
>   analytic 대체) — `CLAUDE.md §6` "approximation-free truth engine"
>   mandate 로 금지. *Conditional inline* DAE-relaxation 만 허용.
> - HYBRID architecture (FLRW limit 에 CAMB transfer 사용) — Round-14
>   auditor 4/4 추천이었으나 사용자 거부 (2026-04-25): production code
>   는 외부 CAMB runtime dependency 없이 self-contained 여야 함. CAMB
>   는 audit oracle 로만 사용.
>
> **Bundle 구조:**
>
> ```
> 00_README.md                    — 번들 안내 + 사용 노트
> 01_DETAILED_ANALYSIS.md         — ~25 KB self-contained 기술 분석
> 02_AUDIT_FOCUSED_SUMMARY.md     — 15분 감사 brief (먼저 읽으세요)
> 03_AUDIT_PROMPT.md              — 이 prompt
> code/                           — 7개 소스 파일 (인라인 가능한 크기)
> reference_docs/                 — 6개 내부 조사 문서 + CLAUDE_md_excerpt.md
> ```
>
> **출력 형식:**
>
> Markdown 보고서 (분량 제한 없음, 다만 focus 유지). 구조 제안:
>
> - **Verdict** (Q1-Q4 각 1문장; CONFIRMED / PARTIALLY-CONFIRMED /
>   REFUTED 라벨, 기존 audit convention 일치)
> - **Reasoning** (질문별, 번들 내 evidence 를 relative path 로 link)
> - **Counter-tests** (verdict 를 대안과 구분할 구체적 diagnostic
>   script 또는 measurement)
> - **Risks** (제안된 closure 경로의 구체적 기술 risk; 미리 계획해야
>   할 것)
> - **Confidence** (각 verdict 에 대한 1-5 척도 주관적 confidence,
>   업데이트 신호 포함)
>
> File-path-and-line-number 인용
> (`code/regular_adiabatic_ic.py:142-186`) 사용해 직접 navigate
> 가능하게 해주세요. counter-test 제안 시 정확한 diagnostic-script
> delta 제공 (어느 파일 어느 line 수정; 또는 어느 path 에 새 script
> 작성).
>
> 재현 노트: 31분 기준 measurement 는 venv (Python 3.11, numpy +
> scipy + numba) 설치 후 repo root 에서
> `python scripts/v5_round17_linear_probe_measurement.py` 로 재현
> 가능. 번들의 `code/` 디렉토리에 참고용 script 가 있으나 실행은
> 번들이 아닌 전체 repo 가 필요합니다.

---

## Notes for the human dispatching this prompt

1. The bundle (this directory + parent files) zips to ~250 KB; can be sent inline as text in most LLM channels. If sending to a vendor with binary upload (Anthropic web, OpenAI Codex, etc.), upload the zip and reference it in the prompt.

2. Prior audits in this series produced ~5–15 KB markdown reports each; budget 10–30 minutes of model wall-clock per request. `Round-14 audit04 (Claude Opus 4.7)` was the most precise single analysis from prior cycles — recommended baseline against which to compare any new auditor's output.

3. Multiple parallel auditors are valuable; this codebase has historically converged via consensus (4/4, 3/3) rather than via single oracle. Recommended cycle: 3 auditors in parallel; cross-compare verdicts before acting on any single one.

4. After receiving the audit, capture the verdict at `docs/audits/external_round17_2026-04-27/verdicts/<auditor>.md` (matching the convention of `docs/audits/external_round12_to_14_2026-04-25/`) before acting on it.
