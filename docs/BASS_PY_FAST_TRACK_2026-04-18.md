# BASS_py Fast-Track — Preliminary Plots Edition

**Date**: 2026-04-18
**Mission**: **플롯 먼저**. bass_py 기존 자산 (W10-01 완료, 1,637 tests, HTT 27 figure scripts prototype) 을 활용해 **가장 빠르게 overview-quality preliminary figure set** 을 산출. 전체 W11-W15 로드맵 완성은 아님.
**Companion**: [`docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md) (Rust side-track)

---

## §1. 왜 fast-track 이 가능한가

bass_py 는 **이미 14/24 prompts 완료** 상태이고, 핵심 사이언스 결과 몇 개가 준비돼 있다:

- **Route B sentinel**: `D_2(Σ²=10⁻⁸) = 0.174112 μK²` CONFIRMED ([bass_py/CHANGELOG.md v0.8.2-w8-02](../bass_py/CHANGELOG.md))
- **τ_reion = 0.054108** vs Planck 2018 0.054 ± 0.007 (Δ < 0.2%)
- **z_* = 1089.89** vs Planck 2018 1089.95 ± 0.27 (Δ = 0.06)
- **W6-04 polarization amplification 4/3** exact analytical + test-verified
- **HTT prototype v8.3.0** with 15 Bianchi evidence models, 5 null families, 27 figure scripts
- **1,637 regression tests passing**, full regression ~40 s

즉 "얼마나 새로 짜야 하나" 의 문제가 아니라, "이미 있는 걸 얼마나 빨리 rendering 하나" 의 문제. 그래서 **"plot-first" track** 이 성립.

---

## §2. 제약 (side-track scope guard)

- **ℓ ≤ 30** 만 다룬다. 고-ℓ 는 `bass_rs` ROADMAP_v3 가 담당.
- **TT + EE** 만 (B-mode 는 bass_rs, Bianchi I 에서는 구조상 0).
- **Production inference 는 하지 않는다** — preliminary 라는 것은 published claim 이 아니라 overview artifact.
- **HTT ZoA P0 재설계는 미룬다** ([BASS_PY_HTT_TSC_RESEARCH_PLAN.md §3](../BASS_PY_HTT_TSC_RESEARCH_PLAN.md) 의 작업). 대신 **Mode 0 diagnostic 만** 써서 ladder plot 만 뽑음.
- **dynesty 전체 15-model × 5-scenario = 75 runs** 는 하지 않는다. **top-3 model × mock data** 로 축소.
- **Mock calibration full suite 불필요** — smoke test 수준의 coverage histogram 만.

따라서 preliminary 는 **모든 figure 에 `diag_` / `preliminary_` 접두** 를 붙이고, 추후 production 전환 시 이름을 바꾼다.

---

## §3. 3-tier plot priority

| Tier | 소요 | 산출물 | 기반 자산 |
|---|---|---|---|
| **A** (0-3 일) | 즉시 | 6-8 개 figure | HTT 27개 script 재실행 + bass_py W10-01 데이터 |
| **B** (3-7 일) | 1주 내 | +2-3 개 figure | W10-02 V-gate (CAMB) 완성 + 렌더 |
| **C** (1-2 주) | 2주 내 | +2-3 개 figure | W14-01 minimal synthetic discriminator |
| **D** (2-3 주, 선택) | 3주 | +1-2 figure | Direction posterior mock (dynesty minimal) |

Tier D 는 scope limit 을 넘을 수 있어서 선택사항.

---

## §4. Tier A — 즉시 렌더 가능한 figure (0-3 일)

### A.1 `fig_route_b_sentinel` (NEW, 이번 세션 가능)

**내용**: D_2 Route B M-M curve  `D_2 = C_1 Σ² / (1 + C_2 Σ²)` at Σ² ∈ [10⁻¹², 10⁻⁴] overlaying sentinel point (Σ²=10⁻⁸, D_2=0.1741 μK²).

**데이터 소스**: `bass_py/bass/spectrum/cl_assembly.py` — W10-01 에 이미 구현됨.

**Chapter**: ch07 §7.1

**작업**: Python 스크립트 30-50 L. matplotlib. 이미 계산 로직이 존재.

### A.2 `fig_MES_three_bounds` (EXISTING, 렌더만)

**내용**: B_σ > B_ω > B_u̇ 계층 가시화.

**데이터**: `bass_py/htt/htt/figures/fig_MES_three_bounds.py` — prototype 존재.

**작업**: sys.path 점검 + 데이터 경로 확인 (HTT README: 일부 tests 가 sys.path 이슈).

### A.3 `fig_colin_beta` (EXISTING, 렌더만)

**내용**: Colin et al. 2025 β 제약 재현.

**데이터**: `bass_py/htt/htt/figures/fig_colin_beta.py`. `htt.core.tilted_flrw.beta_from_colin` 이미 완료.

**작업**: 렌더만.

### A.4 `fig_departure_summary` (EXISTING, 렌더만)

**내용**: x / Q / Π departure 요약 (thesis master identity x_C = Σ² − W² + Ω_tilt + Ω_k,aniso 의 각 term).

**데이터**: `htt/figures/fig_departure_summary.py`. `FLRW_tilt_results` artifact 필요 (이미 htt prototype 에서 생성됨).

### A.5 `fig_evidence_decomposition` (EXISTING, 렌더만)

**내용**: 15-model 중 fiducial FLRW_tilt 의 evidence 를 7 channel 로 분해 (b/c/d/e/f/g/h).

**데이터**: `htt/figures/fig_evidence_decomposition.py`. `FLRW_tilt_results` artifact 필요.

### A.6 `fig_type_by_type_summary` (EXISTING, 렌더만)

**내용**: 8 orth × 6 tilt = 14 Bianchi model 의 evidence grid (heatmap).

**데이터**: `htt/figures/fig_type_by_type_summary.py`.

### A.7 `fig_visibility_g` (NEW from bass_py)

**내용**: g(η) = visibility function, recombination + reionization peak 이중 구조.

**데이터**: bass_py W8-02 완료. τ_reion = 0.054108. 스크립트 20-30 L.

### A.8 `fig_sigma_omega_contour` + `fig_sigma_accel_contour` (EXISTING, 렌더만)

**내용**: σ-ω, σ-u̇ 평면에서 contour.

**데이터**: `htt/figures/fig_sigma_*_contour.py`. 순수 계산, external data 의존 없음.

---

## §5. Tier B — W10-02 FLRW V-gate (3-7 일)

### B.1 W10-02 CAMB 비교 완성

**상태**: 현재 "미착수" ([BASS_PY_HTT_TSC_RESEARCH_PLAN.md §0.3 D18](../BASS_PY_HTT_TSC_RESEARCH_PLAN.md)).

**task**:
1. CAMB Planck 2018 defaults 로 C_ℓ^TT, C_ℓ^EE at ℓ=2..30 을 reference 로 생성
   ```python
   # scripts/bench_camb_vs_bass.py 를 확장하여 저장
   venv/bin/python scripts/generate_camb_reference.py --out data/camb_ref_planck2018.npz
   ```
2. bass_py `bass.spectrum.cl_assembly` 로 동일 parameter set 의 C_ℓ 생성
3. 비교 스크립트: rel_err per ℓ + plot

**target**: rel_err < 5% at ℓ ≤ 10, < 10% at ℓ ≤ 30 ([MASTER_PROMPT_LIST_bass_py.md §2.3 V1](../bass_py/docs/design/MASTER_PROMPT_LIST_bass_py.md)).

**산출 figure**:

### B.2 `fig_flrw_cl_vs_camb`

TT (위), EE (아래) 2-panel. bass_py 와 CAMB 겹쳐 그리고 residual sub-panel 추가.

### B.3 `fig_d2_sigma2_scaling`

D_2 vs Σ² for Σ² ∈ [10⁻¹², 10⁻⁴] scaling curve. Route B M-M analytic fit overlay.

---

## §6. Tier C — W14-01 minimal synthetic (7-14 일)

### C.1 Scope 축소

Full W14-01 은 3-signature discriminator + α fit + Planck data integration 을 모두 포함하지만, preliminary 에서는:

- **Mock data only** (Planck 실데이터 비교는 full scope 에서)
- **3 templates** (local motion, cosmological tilt, tilt² cross-term) 의 **선형 regression only** — full likelihood 아님
- **recovery test on synthetic pure-signal** input 으로 자기 일관성 확인

### C.2 `fig_3_signature_templates` (W14-01 mock)

**내용**: TT 와 EE 각각에서 3-signature 의 spectral 모양.

**중요한 사이언스 주장**: pure TT 는 local vs cosmological 을 구분 못 하지만, **TT+EE 를 결합하면 separable** (R-TILT-03 §3).

### C.3 `fig_3_signature_alpha_posterior` (W14-01 mock)

**내용**: 각 template 계수 (α_local, α_cosmo, α_tilt²) 의 posterior (mock data 에 대한 recovery).

**validation**: pure signal 입력 시 해당 α 만 significant, 나머지는 0 근처. "matched-complexity" 증명 자료.

---

## §7. Tier D (선택) — Direction posterior sample (14-21 일)

### D.1 Scope

HTT 의 full 3-mode / 4-layer infrastructure 재설계 없이 가능한 **최소 posterior**:

- Mock catalog (isotropic baseline + 하나의 injected dipole S2 scenario 만)
- Mode 0 diagnostic path — lat cut 만, no completeness map, no mock calibration
- dynesty nlive=1200 × 1 run
- HPD cone + Mollweide 시각화

**주의**: 이것은 **preliminary only**, production claim 아님. Figure 파일명에 `diag_` 접두 + caption 에 "diagnostic-only" 명시.

### D.2 `diag_fig_direction_posterior_s2`

Mollweide projection 에 posterior HPD 68% cone. S2 CatWISE scenario (ε = 1.476e-3) 에 대해서만.

---

## §8. Action checklist (즉시 시작 가능)

### 오늘 / 첫날

- [ ] `cd bass_py && PYTHONPATH=. pytest bass/ tsc/ -q` — regression green 확인 (기대: 1,637 passing)
- [ ] `htt/` sys.path 정리: `conftest.py` 또는 `pytest-pythonpath` — `htt/tests` 가 돌아가도록
- [ ] 프로젝트 루트에 `scripts/make_preliminary_figures.py` 작성 (하나의 통합 entry)
- [ ] `data/` 디렉토리 + `figures/preliminary/` 디렉토리 생성
- [ ] A.1 `fig_route_b_sentinel` 렌더 (30 분 작업)

### 2-3일차

- [ ] A.2–A.8 렌더 (HTT 기존 script 6개 재실행)
- [ ] 각 figure 에 `plot_style.py` palette (Wong 2011 colourblind) 적용 — HTT 이미 제공
- [ ] Tier A 8 figure 완성 → Git commit

### 4-7일차

- [ ] B.1 W10-02 CAMB reference 생성 + bass_py 비교
- [ ] B.2, B.3 figure 렌더
- [ ] CAMB V-gate PASS/FAIL 판정 (target rel_err < 5% at ℓ≤10)

### 8-14일차

- [ ] C.1 W14-01 minimal: 3 template 선형 regression 구현 (~200 L Python)
- [ ] C.2, C.3 figure
- [ ] synthetic pure-signal recovery test
- [ ] preliminary bundle JSON 저장

### 15-21일차 (optional)

- [ ] D.1 mock catalog + dynesty minimal run
- [ ] D.2 direction posterior figure

---

## §9. 산출물 조직

```
bass_phase1_snapshot/
├── scripts/
│   ├── bench_camb_vs_bass.py          (이미 존재)
│   ├── generate_camb_reference.py     (NEW — Tier B)
│   ├── make_preliminary_figures.py    (NEW — 통합 entry)
│   └── run_w14_mock_minimal.py        (NEW — Tier C)
├── data/
│   └── camb_ref_planck2018.npz        (NEW — Tier B 산출)
└── figures/
    └── preliminary/
        ├── TIER_A/
        │   ├── fig_route_b_sentinel.{png,pdf}
        │   ├── fig_MES_three_bounds.{png,pdf}
        │   ├── fig_colin_beta.{png,pdf}
        │   ├── fig_departure_summary.{png,pdf}
        │   ├── fig_evidence_decomposition.{png,pdf}
        │   ├── fig_type_by_type_summary.{png,pdf}
        │   ├── fig_visibility_g.{png,pdf}
        │   └── fig_sigma_{omega,accel}_contour.{png,pdf}
        ├── TIER_B/
        │   ├── fig_flrw_cl_vs_camb.{png,pdf}
        │   └── fig_d2_sigma2_scaling.{png,pdf}
        ├── TIER_C/
        │   ├── fig_3_signature_templates.{png,pdf}
        │   └── fig_3_signature_alpha_posterior.{png,pdf}
        └── TIER_D/           (optional)
            └── diag_fig_direction_posterior_s2.{png,pdf}
```

각 figure 당 caption 파일 `.caption.txt` 동반 (1-2 문장, publication-ready 수준).

---

## §10. 성공 기준 (이 side-track 단독)

| 시점 | 기준 | 측정 |
|---|---|---|
| 3일차 | Tier A 8개 figure 모두 렌더 | file exists + 시각 확인 |
| 7일차 | Tier B CAMB V-gate PASS (< 5% at ℓ≤10) | rel_err plot |
| 14일차 | Tier C recovery test PASS (pure signal → 해당 α 복원 < 5%) | regression |
| 21일차 | 최소 11개 (tier A+B+C) preliminary figure bundle | commit + Zenodo/DVC |

---

## §11. 이후 main schedule 과의 연결

Tier A-C 가 끝나면 **preliminary figure bundle** 은 다음과 같이 활용:

- **즉시**: thesis chapter 초안, 학회 발표 slide, grant proposal supporting figure
- **중기 (main BASS_PY_HTT_TSC plan 진행 시)**: 각 figure 가 production 화되면 `diag_` 접두를 `fiducial_` 로 교체. Tier C 의 mock regression 은 W14-01 full 로 확장
- **long-term**: bass_rs ROADMAP_v3 의 Phase 4 (bass_py bridge) 가 완료되면, Rust 가 공급하는 full-ℓ transfer function 으로 bass_py figures 가 ℓ > 30 까지 확장 가능. Bass_py 는 여전히 ℓ ≤ 30 direction likelihood 에 집중, Rust 는 full C_ℓ 제공

---

## §12. 비상 계획 (fast-track 내부)

| 문제 | 대안 |
|---|---|
| HTT sys.path 정리 1일 이상 소요 | Tier A 중 `fig_MES_three_bounds`, `fig_colin_beta`, `fig_sigma_*_contour` 만 먼저 렌더 (external data 의존 없음) |
| W10-02 rel_err > 10% | Sobolev assumption (A1~A5) 완화 명시, manuscript 에 "first-version match" 로 언급 |
| W14-01 mock recovery rel_err > 5% | template basis 재검토, preliminary 단계에서는 "qualitative separation 확인" 수준으로 강등 |
| dynesty 수렴 실패 (Tier D) | emcee 대체 또는 Tier D 자체 skip |

---

## §13. 결정사항

- **Tier A 부터 바로 시작**: 대부분이 기존 HTT script 재실행이므로 리스크 없음.
- **Tier B 는 병렬**: CAMB reference 생성은 이미 `scripts/bench_camb_vs_bass.py` 에 있어서 확장만 하면 됨.
- **Tier C 까지 가면 preliminary bundle 완성**: thesis 초안에 삽입 가능한 figure set.
- **Tier D 는 main schedule 로 미룸**: HTT ZoA 재설계 P0 3건 해결된 뒤 Mode 2 fiducial 에서 정식 생성.

---

*End of BASS_PY_FAST_TRACK.*
*Companion: `docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` (Rust side).*
