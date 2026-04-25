# V5-RUNTIME Round-13 External Audit Verdict

**감사자**: 외부 독립 감사자
**Date**: 2026-04-25
**Bundle SHA**: `0536f0e` (HEAD per `COMMIT_LOG.md`)
**Scope**: Phase A 진단 5종 검증 + Option A (k_min clipping) 의 Phase B fix 적정성 + 32× sub-horizon 잔여의 root cause 추정

---

## Verdict (one-line)

**REFUTED** — Option A (k_min clipping) 은 진짜 버그를 가리는 numerical patch 입니다. Phase A 진단 5종 중 D1+D2 는 **샘플링 버그**를 포함하고 있고, D3 는 **C_ℓ 적분 영역의 의미 있는 부분을 제거**하는 것을 super-horizon spike 제거와 혼동하고 있으며, D4 의 bit-identical 결과는 **constraint projection 이 sub-precision 으로 작동하고 있다**는 직교 가설과 구분되지 않습니다. 가장 강력한 단일 root-cause 가설은 **`integration_result.eta` 가 `[η_init=260.14, η_today=14147.35]` 에 64 점 균일-선형 그리드 (Δη = 220.43 Mpc) 라는 사실**이며, 재결합 폭 ~30 Mpc, η_* = 281 Mpc 에 해당하는 grid 점은 **단 1개 (η[0]=260.14, 즉 η_init 자체)** 입니다.

---

## Executive Summary

세 가지 핵심 사실:

**(1) η-output grid 구조** — 진단 transcript 의 `sample_idx=[0,16,32,48,63]` 값을 역산하면 `integration_result.eta` 는 `np.linspace(260.14, 14147.35, 64)` 와 수치적으로 0.01 Mpc 이내 일치합니다 (아래 §검증 1). Δη = 220.43 Mpc 의 균일 선형 그리드입니다.

**(2) 재결합 zone 미해상도** — η_* = 281 Mpc 의 가시도 함수 g(η) 는 폭 ~19 Mpc (FWHM) 의 sharp peak 입니다. BASS 그리드에서 η_* 에 가장 가까운 점은 η[0] = 260.14 (즉 η_init), 다음 점 η[1] = 480.6 은 g(η_*)의 ~1e-135 배. 재결합 영역 전체가 그리드 한 칸 안에 들어갑니다.

**(3) D1+D2 의 idx_star 샘플링 버그** — 진단 스크립트의 `idx_star = argmin(|eta - 281|)` 가 `idx_init = 0` 과 동일합니다. 즉 진단이 "Ψ at η_*" 라고 부르는 양은 사실 **Ψ at η_init** 이며, IC 가 아직 정착하지 않은 (rad→mat 전이 중) 시점의 값입니다. transcript 에서도 직접 확인 가능 — `η_init = 260.1 Mpc` 와 `η_* = 260.1 Mpc` 가 동일한 line value 로 출력됩니다 (`Ψ=-3.3562e-01` 동일).

이로부터: D1+D2 의 결론 ("Ψ ≈ -0.34, k-independent, sign convention pathology") 은 η_* 가 아닌 η_init 의 IC 잔류 값을 측정한 것이며, 1/k² Einstein-constraint failure 가설을 REFUTE 하지 못합니다.

---

## §검증 1 — η-grid 구조 직접 검산

```
BASS grid: n=64, Δη = 220.43 Mpc
Linear-grid prediction vs observed (transcript sample points):
  observed=260.14    linear=260.14    diff=+0.00
  observed=3787.05   linear=3787.05   diff=-0.00
  observed=7313.96   linear=7313.96   diff=-0.00
  observed=10840.87  linear=10840.87  diff=-0.00
  observed=14147.35  linear=14147.35  diff=+0.00

eta_*=281 Mpc, closest grid index = 0 (즉 idx_init), eta[0]=260.14
재결합 폭 Δη_recomb ≈ 30 Mpc
Number of grid points within 30 Mpc of η_*=281: 1
```

---

## Step 1 — Phase A 진단 방법론 검증

### Q1.1 — D5 (seed amplitude trace)

`projected_seed.amplitude = 1.39e-4` at k=1e-4 (정확히 100배 비율로 k=1e-3 에서 1.39e-2) 는 **k² 스케일링이 맞습니다**. 그러나 `compute_flrw_d_ell_linear_probe` 가 `unit_amplitude_normalization=False` 를 강제하므로 (line 1272 of `flrw_pipeline.py`), 이 amplitude 는 D_2 결과에 들어가지 않습니다. **D5 는 D_2 잔류와 직접적 관계가 없으므로 irrelevant** 합니다 (BASS 팀의 결론과 일치).

부수 관측: 1.39e-4 = 1.39e+4 × (1e-4)². 이 1.39e+4 ≈ 13900 ≈ η_init=260 의 ~53.5배. 정확한 prefactor 추적은 `seed_factory` 소스가 번들에 없어 (auditor #4 의 R12 요청대로) 불가능합니다 — README §"What is NOT in this bundle" 에 명시된 잔여 갭입니다.

### Q1.2 — D1+D2 (Φ/Ψ behavior) — **샘플링 버그**

이 진단의 가장 결정적인 결함입니다.

번들의 D1+D2 코드 line 224:
```python
eta_star_actual = float(species.bg_table.eta_at_a(1.0 / 1090.94))  # ≈ 281 Mpc
idx_star = int(np.argmin(np.abs(eta - eta_star_actual)))
```

`eta = integration_result.eta = np.linspace(260.14, 14147.35, 64)`. 따라서 `|eta - 281|` 의 최솟값은 `|260.14 - 281| = 20.86` (idx 0) vs `|480.57 - 281| = 199.57` (idx 1). **idx_star = 0 = idx_init**.

진단 transcript 가 출력한 `Ψ at η_* ≈ -0.34` 는 사실 **Ψ at η_init**, 즉 `extract_flrw_sources_from_tier_b` 가 IC 직후의 상태에서 추출한 Newtonian Ψ 입니다. 이 시점 (η_init = 260, z ≈ 1200) 은 matter-radiation 전이 한가운데로, super-horizon Ψ 의 자동 정착이 아직 일어나지 않았습니다. transcript 에서 같은 k=1e-4 에서 η=3787 Mpc (idx=16) 의 Ψ = +0.39 가 분석적 +0.6 에 훨씬 가깝다는 사실이 이를 뒷받침합니다.

따라서:

- "Ψ ≈ -0.34 vs analytic +0.6" 의 sign + factor 0.56 mismatch 는 **η_* 에서의 Ψ 값에 대한 진술이 아닙니다.**
- "k-independent (-0.336, -0.338, -0.365)" 는 IC formula `eta_cov = 2·amplitude·(1 - x²/12·(...))` 가 super-horizon (x ≪ 1) 에서 amplitude 에 의해 set 되는 것의 자연스러운 귀결이며, 정상입니다.
- **C-c (1/k² Einstein-constraint cancellation failure) 가설은 D1+D2 로는 reject 도 confirm 도 안 됩니다.**

추가 관측: same k=1e-4 에서 transcript 의 `Ψ(η)` 추이는

```
η=  260   Ψ=-0.336
η= 3787   Ψ=+0.393
η= 7314   Ψ=+0.0695
η=10840   Ψ=+0.0217
η=14147   Ψ=+0.00739
```

η=260 에서 η=3787 로 0.73 의 swing — 이것이 `_fd4_derivative` 로 Ψ̇ 를 계산하면 **거대한 spurious 값**을 줍니다 (아래 Step 2 참고).

### Q1.3 — D3 (k_min sweep) — **혼합된 효과**

D3 의 결과 (760 → 32 as k_min: 1e-4 → 1e-3) 는 BASS 팀 해석 ("super-horizon spike contributes 95%") 과 다른 해석이 가능합니다.

ℓ=2 의 SW C_ℓ 적분의 integrand 는 `P_R(k) · |Δ_2(k)|² / k` 로, |Δ_2(k)| 는 j_2(k(η_0-η_*)) 으로 가중됩니다. j_2(x) 의 첫 번째 peak 는 x ≈ 3 근처에 있으며, k(η_0-η_*) ≈ 14000·k 이므로 **k_peak ≈ 3/14000 ≈ 2.1e-4 Mpc⁻¹** — 정확히 D3 가 cut off 하는 영역입니다.

따라서 k_min=1e-3 으로 raising 하면:

- **physical**: ℓ=2 SW peak 의 ~80% 를 통째로 적분에서 제거합니다.
- **artificial**: 동시에 BASS 의 잘못된 super-horizon 영역도 제거합니다.

두 효과가 분리되지 않습니다. "ratio 760 → 32" 가 "spike artefact 가 96% 였다" 를 의미하지 않습니다 — **physical SW peak 와 spurious super-horizon contribution 이 동시에 사라진 것**입니다. 정확한 분리를 위해서는 Route-B Rust 로 동일한 `k_min ∈ {1e-5, 3e-5, ..., 1e-3}` 5점 비교 (즉 D_2^{Route-B}(k_min) 도 sweep) 가 필요합니다 — 번들에 그 자료는 없습니다.

또한 N_k=12 fixed: k_min 을 올리면 같은 12점이 더 좁은 영역을 sample 합니다. `dlnk_(k_min=1e-3) = 0.42` vs `dlnk_(k_min=1e-5) = 0.84` — **두 quadrature 의 정확도 자체가 다릅니다**. Round-12 auditor 들이 지적한 N_k 의존성 (5e+04 → 1.5e+04 → 1.4e+04) 은 quadrature 수렴 부족의 흔적이며, k_min sweep 결과를 quadrature artefact 만으로 설명할 수 없습니다.

### Q1.4 — D4 (every_n_steps toggle, BIT-IDENTICAL) — **약한 진단**

D4 코드는 `_pipeline_runtime_controls` 를 monkey-patch 하지만, `compute_flrw_d_ell_linear_probe` 가 호출하는 path 는 `compute_transfer_function_grid` → fork 된 worker pool 입니다. Fork 후 worker 들이 patched module 을 보는지 (POSIX fork copy-on-write 로 patch 가 보임이 일반적) vs 원본을 import 하는지는 코드만 보고 단언하기 어렵습니다. transcript 의 wall time 이 default 53.4 s, tight 53.4 s 로 동일한 것은 patch 가 적용되긴 했다는 약한 증거이긴 합니다 (만약 적용 안 됐으면 두 runs 가 동일한 길이의 work 를 하므로 시간 차이 없는 게 자연스러우니, 시간만으로는 분간이 안 됩니다).

가정: patch 가 effective. 그렇다면 bit-identical 의 의미는:

- (a) constraint projection 이 이미 매 step 거의 작동 안 함 (sub-precision)
- (b) constraint 가 IMEX scheme 의 algebraic 부분에서 이미 강제되어 있어 explicit projection 이 무의미

`build_cosmological_integrator_config` 와 IMEX scheme 의 internal 구조는 번들에 없으므로 (a) vs (b) 를 구분할 수 없습니다. **D4 가 IMEX drift 를 reject 하기에는 약합니다** — bit-identical 은 "drift 가 없다" 가 아니라 "이 toggle 이 drift 를 측정하지 못한다" 일 수 있습니다.

---

## Step 2 — 32× 잔여 root cause 분석

### 가장 강력한 단일 가설: η-output grid 의 LoS 적분 미해상도

핵심 사실 chain:

(a) `flrw_pipeline.py` line 326-328 에서 LoS 가 사용하는 grid 는 `integration_result.eta` 를 그대로 받습니다 — sub-sampling 도, dense remesh 도, recombination 근처 refine 도 없습니다.

(b) Default `n_output = 64` (line 123 of `flrw_pipeline.py`). 이 64점이 [η_init, η_today] 의 균일 선형 그리드. Δη = 220 Mpc.

(c) `tier_b_source_extraction.py` line 304-306 은 `_fd4_derivative(eta, phi_plus_psi)` 로 Φ̇+Ψ̇ 를 같은 64점 grid 에서 계산.

(d) `flrw_bessel_projector.py` line 450 의 `ISW = np.exp(-kappa) * phi_psi_dot_arr`. η_init=260 에서는 e^{-κ} 가 작지 않습니다 (재결합 직전, κ ~ 1-2).

### §검증 2 — η-grid 미해상도의 정량적 magnitude

표준 ΛCDM 의 visibility function g(η) 는 η_* ≈ 281 Mpc 를 peak 로 하는 width Δη_g ≈ 19 Mpc (FWHM) 의 좁은 Gaussian-like 분포 (∫g dη = 1, σ_g ≈ 8.07 Mpc, peak height g(η_*) ≈ 0.0494 Mpc⁻¹). 이를 BASS-grid trapezoid 로 적분하면:

```
True ∫ g(η) dη (analytic norm) = 1.0000
BASS-grid trapezoid ∫ g(η) dη  = 0.1927   (≈ 19% retention)
g(η[0]=260.14) = 1.7486e-03 Mpc⁻¹  (peak 의 3.5%)
g(η[1]=480.57) = 6.99e-135           (사실상 0)
Number of grid points where g > 1e-3 of peak: 1
```

같은 그리드로 SW 적분을 평가:

```
True ∫ g·S dη with S=0.4 (분석적 SW)        = 0.4000
BASS grid 추정 with S=0.4                    = 0.0771
Trapezoid/True ratio (분석적 source 유지)    = 0.193

만약 source 가 η_init 에서 측정된 -0.336 (transcript 값) 으로 잘못 sampled:
BASS grid 결과 = -0.0648
vs 분석적 SW = +0.4000  →  ratio = -0.162  (부호 반전 + magnitude 0.16)
```

이는 transcript 의 `post_R11_per_k_diagnostic.txt` 에서 k=1e-4, ℓ=2 의 `α_meas = -2.56` vs `α_SW = -0.022` (ratio 115) 와 정성적으로 정합합니다. α_SW 자체가 같은 BASS-grid trapezoid 로 분석적 SW formula 를 평가한 것이라면 (스크립트 부재로 단정 못함), α_meas / α_SW 의 ratio ~115 의 일부는 **분석적 비교 자체가 같은 그리드 결함을 공유** 하는 데서 옵니다. 즉 Round-12 의 760× 와 D3 의 32× 모두 **같은 η-grid 의 다른 manifestation**.

수치 자체로 32× exact 를 재현하지는 못합니다 — grid alignment, j_ℓ(kr) oscillation, FD-derivative compounding 의 상호작용은 닫힌 형태 추정이 어렵습니다. 그러나 **O(10-100×) 의 magnitude artefact 가 64-uniform grid 에서 생긴다는 점은 확정** 입니다.

### Q2.1, Q2.2 — Sign + magnitude 차이 0.56 / 1.79

위 Q1.2 에서 논증한 바와 같이, BASS 팀 (또한 진단 script) 가 비교한 "Ψ ≈ -0.34" 는 η_init = 260 Mpc 에서의 Newtonian Ψ 추출값이고, 비교 대상 +0.6 은 **deep matter-domination asymptotic** 입니다. η_init = 260 Mpc 는 z ≈ 1200, 이는 z_eq ≈ 3400 직후의 **rad→mat 전이 한가운데** 입니다. 분석적 deep-MD asymptotic 를 적용하는 것 자체가 부적절합니다.

또한 `tier_b_source_extraction.py` line 280-291 의 추출 공식

```
phi = (4πGa²/k²) · [δρ_tot − 3ℋ·mom/k]
```

은 comoving-density gauge-invariant 조합으로, sync 와 Newt gauge 모두에서 같은 Φ_Bardeen 을 줍니다 (MB-95 §3.4 의 gauge transformation rule 직접 검산). 즉 **공식 자체에 sign convention 버그는 없습니다.** sign 차이는 BASS 의 `b_k_sq=1` 이 어떤 conventional sign 의 R 또는 ζ 에 대응하는지의 문제이며, 이는 IC formula `δ_γ = +(amplitude/3)·x²` (BASS) vs `δ_γ = -(2/3)·C·x²` (MB-95 eq. 96) 의 **편의적 sign reversal** 입니다 — 진짜 버그가 아닙니다.

따라서 Q2.1, Q2.2 의 BASS 팀 가설 (sign convention error 의 sub-horizon 잔류) 는 **성립하지 않습니다**. 0.34 / 0.6 의 magnitude mismatch 는 (i) 분석적 +0.6 의 domain mismatch (deep MD asymptotic vs early MD η_init=260) + (ii) BASS 의 `b_k_sq=1` 이 절대적 ζ=1 이 아닐 가능성, 두 가지의 산술적 잔여로 설명 가능합니다.

### Q2.3 — Doppler / sub-horizon

`post_R11_per_k_diagnostic.txt` 에서 k=1e-1 의 ratio `α_meas/α_SW` = 3500-83000 은 **α_SW 가 전혀 적용 안 되는 영역** (sub-horizon, Doppler+acoustic 지배) 의 의미 없는 비율입니다. 이는 BASS 의 sub-horizon 처리에 진짜 문제가 있다는 증거가 아닙니다 — 그 비율로 root cause 를 추정하지 마십시오.

다만 build_temperature_source 의 line 453 `doppler = np.gradient(g·v_b, eta_grid, edge_order=2)` 은 같은 220-Mpc 균일 그리드에서 (g·v_b) 의 미분을 계산합니다. g·v_b 의 실제 분포는 재결합 zone 폭 30 Mpc 안에 집중되지만, 220 Mpc 그리드는 이 분포 전체를 1 점으로 압축합니다. **k≥1e-3 영역에서도 같은 grid 가 사용되므로 ISW + Doppler 의 grid-FD 처리가 over-amplification 을 유발**하며, 이것이 32× sub-horizon 잔여의 dominant contribution 으로 추정됩니다.

### Q2.4 — sqrt(32) 정량 후보 비교

R_ν = 0.4087 (Planck-2018) 을 대입한 정량값:

```
R_ν = 0.4087, denom = 4·R_ν+15 = 16.6348

Candidate factors that could match sqrt(32) ≈ 5.657 or 32 = 5.657²:
  4·sqrt(2)        = 5.6569      [sqrt(32) exact algebraic match]
  16/3             = 5.3333      [Π = (16/15)·... ?]
  (4R_ν+15)/3      = 5.5449      [denom/3, factor 5.55]
  (4R_ν+15)/2.93   = 5.6774      [denom/2.93]
  R_ν/(1+R_ν)      = 0.2901      [neutrino fraction]
  3/(1+R_ν)        = 2.1296
  pi² / √3         = 5.6982

Magnitude of D1+D2 0.336/0.6 = 0.560:
  R_ν/(1+R_ν)      = 0.2901   vs  0.560  → no
  (1+R_ν)/2        = 0.7044   →  closer but still no
```

단일 sig-fig 의 32 (정확히는 transcript 의 32.17) 에 5-6 사이 O(1) 의 다양한 algebraic combination 이 모두 우연히 매칭됩니다. **물리적으로 동기화된 깔끔한 후보 없이 factor-fitting 은 post-hoc numerology** 입니다. 결정적으로, BASS 팀이 0.6/0.336 = 1.79 의 magnitude mismatch 를 sign-convention or polter factor 의 신호로 읽었던 것은 (Q1.2 에서 논증한 대로) **η_* 가 아닌 η_init 의 값을 잘못 비교한 것**이므로, 이 비율 자체가 root-cause 신호가 아닙니다.

따라서 Q2.4 에 대한 답: **"32 의 정확한 분해는 η-grid 를 정상화한 후 의미 있게 측정 가능. 현재 number 들로부터 factor-fitting 은 권장하지 않음."**

---

## Step 3 — Option A (k_min clipping) 검증

### Q3.1 — k_min clipping: legitimate physics 가 아닌 numerical patch

표준 CMB Boltzmann 코드 (CAMB, CLASS) 의 super-horizon 처리:

- CAMB `equations_ppf.f90` 는 `kmin` 으로 sub-percent precision 을 위한 integrand 적분 lower bound 를 사용합니다 — 그러나 이는 (1) k·η_0 가 너무 작아 j_ℓ(kη_0) ≈ 0 인 영역의 numerical underflow 회피, (2) `k → 0` 에서 transfer function 의 analytic SW continuation 의 numerically-stable 결합 — **BASS 의 ratio 760 → 32 같은 거대한 effect 를 절대 만들지 않습니다**.
- CAMB 는 super-horizon analytic SW formula 와 numerical full-Boltzmann 결과를 자연스럽게 합치는 메커니즘 (`do_long_wavelength_int = T`) 을 가지고 있고, switch 후 결과는 numerical 결과와 sub-percent 수준에서 일치합니다.

따라서 "raising k_min from 1e-4 to 1e-3 가 ratio 를 24× drop 시킨다" 는 BASS 의 super-horizon 처리에 24× 의 **체계적 over-amplification** 이 있다는 신호이지, k=1e-4 를 적분에서 제외하는 것이 옳다는 신호가 아닙니다.

### Q3.2 — N_k 의존성

(N_k=12 의) ratio 가 5e+4 → 1.5e+4 → 1.4e+4 (Round-12 auditor 들의 보고) 은 부분적으로 quadrature 수렴 부족의 흔적입니다. 그러나 dense N_k (예: 100, 256) 으로 가도 **재결합-zone-undersampling 은 그대로** — N_k 는 k-적분의 grid 이고, η-grid (n_output) 는 별개 dimension. **이 둘이 혼동되어서는 안 됩니다.**

### Q3.3 — k_min_cutoff 의 위치

세 가지 후보 ((a) wrapper 에서 k_min 미만 제거, (b) trapezoid weight 0, (c) 분석적 SW continuation) 모두 **번들 안의 진짜 문제 (η-grid 미해상도) 를 해결하지 못합니다**. (c) analytic SW continuation 추가는 super-horizon mode 만 separately 처리하는 hybrid 방식이지만, 32× sub-horizon 잔여는 그대로 남습니다. (a)+(b) 는 적분 범위만 바꾸므로 (c) 보다 약합니다.

### Q3.4 — 올바른 k_min_cutoff value

이 질문의 전제 자체가 잘못되었습니다 — **올바른 fix 는 k_min_cutoff 가 아닙니다**. 후술 Step 4 의 (P0) 참조.

---

## Step 4 — 최종 판정 + Round-12 closure 권장

**REFUTED**. Phase A 결론을 기반으로 한 Option A 는 진짜 버그를 mask 합니다. Round-12 closure 를 보류하고 다음 우선순위로 진행을 권장합니다:

**(P0) `integration_result.eta` 의 grid 정책 확인**

- `build_cosmological_integrator_config` (번들에 없음 — auditor #4 R12 요청 기 반복) 의 `output_times` 생성 코드 확인
- 64 균일 선형이 맞다면 → 즉시 (i) `n_output` 을 256+ 로 raise, **and** (ii) η_init~η_*~η_today 영역에 logarithmic 또는 multi-zone 비균일 그리드로 변경
- 변경 후 D3 와 동등한 k_min sweep 재실행 — 만약 ratio 가 1 근처로 collapse 하면 **이것이 진짜 fix**

**(P1) D1+D2 의 idx_star 버그 수정**

- script line 224-227 에서 `idx_star = argmin(|eta - eta_star|)` 가 idx_init 와 같은 경우 명시적 warning 또는 `eta_star + Δη_recomb/2` (재결합 후 절반 위치) 를 sample 하도록 수정
- 새로 측정한 Ψ at η_*+15 와 분석적 +0.6 비교가 0.56× factor 이고 sign 반대인지 재확인 — 만약 factor + sign 모두 정상화되면 **D1+D2 결론은 무효였음을 confirm**

**(P2) Round-12 closure 게이팅 조건**

- `n_output = 256`, η-grid = "log-spaced or recombination-refined" 로 한 후 실행한 D_2 (Route-A vs Route-B) ratio 가 **1.0 ± 0.05** 이내일 때만 closure 권장
- 만약 그 후에도 ~32× 가 남아있으면 **그것이 진짜 별도 root cause** (sign convention 또는 missing physics) — Round-13/14 에서 chase

---

## Step 5 — 교차 검증

### Q5.1 — Route-B Rust D_2 = 1002.086744 μK²

**0% 영향**. README L142 + COMMIT_LOG 가 "Rust binary `bass_rs dump_dl_spectrum_sparse` 출처" 를 기록 — Python pipeline 변경과 독립. **Phase B fix 가 무엇이든 (Option A, n_output 변경, etc.) Route-B 는 영향 없음**.

### Q5.2 — 43 CAMB cross-check tests at b_k_sq=1.0

**Option A 적용 시 0% 영향** (가정: cross-check 가 transfer function 의 b_k_sq linearity 만 testing 한다면). Phase B 는 pipeline assembly level 변경이지 seed level 변경이 아니므로.

그러나 **n_output 을 raise 하면 모든 43 tests 의 numerical output 이 변합니다**. `bit-identical` 보장이 깨지므로 (P0) 의 fix 를 적용할 때는 모든 anchor (Route-B 제외) 를 **golden update** 해야 합니다. 이것이 R12 closure 를 단순 patch 가 아닌 SSOT-coordinated rollout 으로 만드는 진짜 이유입니다.

### Q5.3 — `_d2_anchor_golden.json`

README L142-148 + `SSOT_NU_SEED_DRIFT_2026-04-25.md` L125-130 의 명시:

- Route-B Rust `D_2 = 1002.086744 μK²` anchor: 0% — Rust path 독립
- Route-B Python golden (`route_b_d2_lookup` MM-curve): 0% — analytic Michaelis-Menten formula

두 anchor 모두 Phase B 변경의 영향 밖이지만, **n_output 변경은 PSTF Python path 의 모든 비-anchor regression test 를 shift 시킵니다**. SSOT-coordinated rollout 필수.

---

## §부록 A — Round-13 단일 진단 스크립트 사양 (P0 fix 검증용)

```python
# scripts/v5_round13_eta_grid_diagnostic.py
# 목적: η-output grid 미해상도가 D_2/Route-B ratio 의 root cause 인지 결정.
# 실행 시간: 8-worker pool 에서 ~30-60 분 (n_output=1024 의 IMEX 비용 dominant).

import numpy as np
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig, compute_flrw_d_ell_linear_probe,
)

ROUTE_B_D2 = 1002.086744
species = SpeciesBackgroundRegistry.from_planck2018()

# 1차원: n_output ∈ {64, 128, 256, 512, 1024}
# 2차원: η-grid type ∈ {"uniform-linear", "log-spaced", "recombination-refined"}
#   (현재는 균일 선형만 지원되는 듯하므로, log-spaced 와 refined 는
#    build_cosmological_integrator_config 의 output_times kwarg 를 patch 해서 구현 필요)
# 3차원: k_grid ∈ {N_k=12 standard, N_k=24 dense, N_k=48 ultra-dense}
#   (각 k_grid 는 k_min=1e-4, k_max=1e-1, log-spaced)

results = []
for n_out in [64, 128, 256, 512, 1024]:
    for grid_type in ["uniform-linear", "log-spaced", "recombination-refined"]:
        for N_k in [12, 24]:
            cfg = FLRWPipelineConfig(
                L_max_tower=4, ell_max_transfer=4,
                n_output=n_out,
                # eta_grid_type kwarg 추가 필요 (P0 patch 의 일환)
            )
            k_grid = np.logspace(-4, -1, N_k)
            bundle = compute_flrw_d_ell_linear_probe(
                species, k_grid_mpc=k_grid,
                pipeline_config=cfg, probe_b_k_sq=1.0,
            )
            d2 = bundle["d_tt"][2]
            ratio = d2 / ROUTE_B_D2
            results.append((n_out, grid_type, N_k, d2, ratio))

# 출력: ratio matrix, n_output × grid_type × N_k
# 기대 결과:
#   (a) "uniform-linear" 64 → ratio ≈ 760 (재현)
#   (b) "uniform-linear" 1024 → ratio: 만약 ~1 이면 P0 가설 confirmed,
#                                만약 여전히 ~30+ 이면 P0 만으로 부족, 다른 root cause 도 있음
#   (c) "recombination-refined" 256 → 만약 ~1 이면 grid 형태가 핵심
#   (d) N_k 12↔24 의존성: "log-spaced" 그리드에서 N_k 의존성이 사라지면 quadrature-converged
```

---

## §부록 B — Round-13 closure 게이팅 조건

Round-12 closure 와 Phase B fix rollout 을 다음 게이트로 묶을 것을 권장합니다:

**Gate-1**: 위 진단 스크립트 실행 결과, "uniform-linear, n_output=1024, N_k=24" 의 ratio 가 < 5 이면 (P0 = η-grid 미해상도) 가 root cause 의 dominant 부분이라는 confirmation. **이 경우 Option A 폐기, n_output 기본값을 적절한 값으로 raise + grid-type 옵션 추가가 진짜 fix**.

**Gate-2**: D1+D2 진단 script 의 idx_star 버그 수정 후 (`idx_star = argmin(|eta - eta_star|)` → η_init 와 같지 않도록 추가 조건), 새로 측정한 Ψ at "η_*+Δη_recomb/2" 가 ~0.5 ± 0.1 (분석적 +0.6 의 80-100%) 이면 **C-c (Einstein constraint failure) 가설이 confirmed REFUTED** — 이 경우 D1+D2 의 결론은 ratification 됨. 만약 여전히 large-magnitude sign-flipped 이면 **C-c 가 다시 살아남** — 이 경우 source extractor 의 4πG·a²/k² 항을 조사.

**Gate-3**: Gate-1 + Gate-2 통과 후 Route-A vs Route-B agreement 가 5% 이내이면 Round-12 closure 가능. 그 이상이면 잔여 factor 는 별도 Round-14 에서 chase (이때는 진짜 sub-percent residual 이므로 sign convention, polter factor 의 정밀 비교가 의미 있게 됩니다).

**Gate-4** (necessary for any of the above): `seed_factory` / `project_packed_regular_seed` 소스 disclosure (auditor #4 R12 + 본 감사가 반복 요청). 이 코드 없이는 D5 의 1.39e+4 prefactor 의 정확한 분해, 또는 IMEX 의 patch effectiveness 검증 (D4) 이 불가능합니다. README §"What is NOT in this bundle" 의 "BASS team has NOT included them because they were unable to localize the relevant excerpt cleanly" 는 받아들이기 어려운 갭 — **next round 번들에는 반드시 포함되어야 합니다**.

---

## §부록 C — 최종 행동 권고

| 우선순위 | 작업 | 비용 |
|---------|------|------|
| P0 | §부록 A 진단 스크립트 실행, n_output × grid_type × N_k matrix 측정 | ~1 시간 |
| P0 | D1+D2 의 idx_star 버그 수정 + Ψ at η_*+Δη_recomb/2 재측정 | ~30 분 |
| P1 | seed_factory + ver2_native_integrator 의 출력 시간 그리드 생성 코드 disclosure | 즉시 |
| P1 | n_output 의 default 를 확정하기 전, η-grid 가 출력 시간 그리드인지 IMEX 적분 그리드인지 명확화 (둘이 다를 수 있음) | 분석적 |
| P2 | Option A (k_min_cutoff) 폐기 — kwarg 추가 자체는 backward-compat 이지만 default 없는 한 사용 권장 안 함 | 즉시 |
| P3 | Round-12 closure: Gate-1+2+3 통과까지 hold | conditional |

---

## Confidence and Caveats

### 확신

- η-grid 가 64-point 균일 선형 (Δη=220 Mpc) 인 사실 (transcript-derived, Python 직접 검산으로 확인): **확신도 99%**
- D1+D2 의 idx_star=idx_init buggy sampling (직접 코드 검토 + transcript 의 동일 line 출력으로 확인): **확신도 100%**
- Option A 가 numerical patch 이지 root-cause fix 가 아닌 점 (논리적): **확신도 90%**
- O(10-100×) magnitude artefact 가 visibility undersampling 에서 나온다는 점 (정량 검산으로 ratio=0.193 확인): **확신도 95%**

### 약점 / 불확실성

1. **η-grid 미해상도 가설이 760× 의 모든 magnitude 를 quantitative 하게 설명하는지는 numeric simulation 없이 확정 못함**. 만약 n_output=512 로 raise 후에도 760× 이 남아있다면 이 가설이 부분적으로 틀린 것. 가장 유력한 다음 후보: source extractor 의 4πG·a²/k² 인자 normalization, 또는 PchipInterpolator 의 `extrapolate=False` 가 LoS grid 의 일부 점에서 NaN 을 만들고 그 NaN 이 어딘가에서 0 처리되는 silent bug.

2. **`build_cosmological_integrator_config` 의 output_times 생성 로직 미확인** — η-grid 가 정말 `np.linspace(η_init, η_today, n_output)` 인지 vs IMEX adaptive stepper 가 n_output 점을 cubic interpolation 으로 dense_output 해서 만든 grid 인지 (후자라면 grid 점들은 여전히 linspace 처럼 보일 수 있지만 interpolation 정확도는 다름) 단정 못함. transcript 의 sample point 가 정확히 linspace 와 일치한 사실은 적어도 출력 grid 가 linspace 임을 강하게 시사.

3. **D4 의 monkey-patch 가 fork worker 에 effective 한지 직접 확인할 코드 (full ver2_native_integrator.py) 가 번들에 없음**. 이는 auditor #4 가 R12 에서 요청했고 여전히 누락된 갭으로, 본 감사도 동일하게 단정 불가.

4. **BASS 의 `b_k_sq=1` ↔ ζ 의 정확한 sign + factor 매핑은 seed_factory 소스 없이 단정 불가** — auditor #4 가 R12 에서 요청했고 여전히 누락.

5. **CAMB 의 `equations_ppf.f90` 직접 인용 못함** — 본 감사 환경에서 CAMB source 를 fetch 하지 않았습니다. CAMB/CLASS 의 η-grid 정책에 대한 진술은 Lewis-Challinor 2002 + 일반적 기억에 의존.

6. **32× sub-horizon 잔여의 정확한 분해는 (P0) fix 적용 후에야 의미 있게 측정 가능**.

이런 약점에도 불구하고, **D1+D2 의 idx_star = idx_init buggy sampling 사실** 과 **64-point uniform grid 가 width-19-Mpc visibility peak 를 1점만 sample 하는 사실** 은 직접 검산 가능했고, 이 두 사실만으로도 Phase A 의 결론 + Option A 의 정당성을 REFUTE 하기에 충분합니다.

---

## 종결

Phase A 진단의 idx_star 버그는 Round-12 의 4-auditor 만장일치 직후 BASS 팀이 디자인한 후속 진단에 새로 도입된 것이며, 그 결과로 도출된 Option A 는 진짜 root cause 를 가립니다. 본 감사 결과를 Round-12 Phase B fix rollout 의 게이팅 자료로 사용해 주십시오.

권장 closure path: §부록 C 의 (P0) → (P1) → §부록 B 의 Gate-1 → Gate-2 → Gate-3 → Round-12 closure.
