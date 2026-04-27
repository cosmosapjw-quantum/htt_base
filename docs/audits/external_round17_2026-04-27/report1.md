# Round-17 Independent Audit Report — BASS FLRW Closure Residual

범위 고지부터 할게. 나는 여기서 전체 repo의 31분 measurement를 직접 재실행한 게 아니라, 업로드된 Round-17 bundle의 문서와 포함 코드에 대한 정적 감사, 산술 검산, 결함-가설 판별 설계를 수행했다. 결론은 **D-2가 매우 그럴듯한 주 원인**이지만, 현재 bundle만으로는 “완전 확정”이 아니라 **PARTIALLY-CONFIRMED**가 맞다. 특히 문서들이 반복하는 “k-grid의 ~60%가 `x>1`”이라는 표현은 산술적으로 틀렸다.

---

## 1. Verdict

**Q1 — D-2 diagnosis: PARTIALLY-CONFIRMED.**
Lowell leading-order seed가 `x=kη_init≪1` 밖에서 무방비로 쓰이고 있다는 진단은 맞다. 다만 `η_init=261 Mpc`, `np.logspace(-4,-1.5,65)`에서 `x>1`인 점은 **24/65 ≈ 36.9%**이지 “~60%”가 아니다. “~60%”는 대략 `x>0.3`인 marginal regime을 포함할 때만 맞다. 그래서 D-2는 유력하지만, D-3 및 source-extraction 계열과 분리하는 직접 counter-test가 아직 필요하다.

**Q2 — closure mechanism: PARTIALLY-CONFIRMED.**
`η_init`을 `z≈10^9`까지 당기면 seed-validity 문제는 물리적으로 해소된다. 그러나 bundle의 `integrator.py`는 “IMEX implicit stage”라고 부르기엔 증거가 부족하고, 실제 포함 코드는 `solve_ivp(..., method="LSODA")` 경로를 보인다. 또한 DAE-relaxation이 `ℓ=2,m=0`만 pin하는 설계는 프로젝트 철학에는 맞지만, deep TCA에서 higher-ℓ photon multipole의 stiffness와 damping을 별도로 감사해야 한다.

**Q3 — missed defects: PARTIALLY-CONFIRMED.**
새로운 단일 6.43× convention factor는 보이지 않는다. 하지만 D-3, source-output sampling, deep-z opacity/background coverage, integrator-documentation drift는 여전히 실제 위험이다. 특히 D-3는 “park”하기엔 너무 싸고 너무 관련 있다.

**Q4 — sub-track ordering: PARTIALLY-CONFIRMED / current ordering should be changed.**
`α`를 먼저 닫는 것은 맞다. 그러나 `D-3`를 `δ` 뒤에 두는 것은 좋지 않다. 추천 순서는 **α → D-3 → β/δ0 diagnostics → δ full closure → γ**, 또는 γ를 병렬화하는 것이다. FLRW closure가 목표라면 `m∈{-2,…,+2}` 확장은 δ보다 앞설 이유가 약하다.

---

## 2. Reasoning

### Q1. D-2 diagnosis

D-2의 핵심은 실제 코드에서 확인된다. `_seed_formulae`는 `x = k_comoving * eta_initial`을 만든 뒤 `x²`, `x³` leading-order 항으로 regular adiabatic seed를 구성한다. `eta_cov`, `delta_gamma`, `theta_gamma`, `theta_nu`, `pi_nu`, `G_3` 모두 낮은 차수의 super-horizon expansion이다. 코드에는 `x≪1` guard나 validity warning이 없다. `code/regular_adiabatic_ic.py:142–186`

closure test는 실제로 `k_grid = np.logspace(-4.0, -1.5, 65)`를 쓴다. `η_init=261 Mpc`라면 `x=kη` 범위는 대략 `0.0261`부터 `8.25`까지다. 따라서 이 seed를 full k-grid 전체에 적용하는 건 물리적으로 정당화되지 않는다. `code/test_d2_pstf_closure.py:71–84`, `01_DETAILED_ANALYSIS.md:343–358`

다만 문서의 수치 표현은 고쳐야 한다. `x>1` 경계는 `k>1/261≈3.83×10^-3 Mpc^-1`이고, 65개 log-grid 중 여기에 해당하는 점은 24개다. 비율은 약 36.9%다. `x>0.3`이면 37/65≈56.9%라서 “~60%”에 가깝다. 그러므로 올바른 표현은 **“약 37%가 명백한 `x>1` invalid regime이고, 약 57%가 이미 `x>0.3`인 marginal/asymptotic-danger regime이다”** 정도다.

D-2가 여전히 유력한 이유는 두 가지다. 첫째, Round-12–14 summary가 residual을 단일 convention factor가 아니라 D-1/D-2/D-3 구조로 수렴시켰고, D-2를 “wrongly seeded sub-horizon modes evolved forward”로 특정한다. `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:162–190` 둘째, Round-15 D-1 fix 후에도 source/projector grid 문제는 크게 줄었고, CAMB-source를 더 이른 lower-bound로 넣었을 때 low-k, low-ℓ ratios가 1에 가까워지는 정황이 있다. `reference_docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:43–83`

하지만 아직 “D-2 단독 확정”은 아니다. 같은 문서가 D-3 high-k source-convention residual을 남긴다고 명시하고 있다. `reference_docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:84–87` 또한 D-3는 synchronous-gauge `Θ_0^S`와 Newtonian `Ψ`를 섞는 source extraction 문제로 기록되어 있다. `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:199–233`

따라서 내 판정은 이렇다. **D-2는 맞는 결함이고 6.43× residual의 주원인 후보로 매우 강하다. 그러나 현 문서의 “~60% x>1” 근거는 잘못되었고, D-3를 배제하는 x-controlled counter-test 없이는 CONFIRMED가 아니라 PARTIALLY-CONFIRMED다.**

---

### Q2. Closure mechanism

`η_init`을 `~10^-3 Mpc`로 옮기면, 같은 k-grid에서 `x=kη_init`는 `10^-7–10^-4` 수준이 된다. 이 부분은 D-2를 직접 겨냥하는 올바른 방향이다. `01_DETAILED_ANALYSIS.md:368–379`

conditional inline DAE-relaxation도 코드상 존재한다. `Γ_T/H`가 threshold보다 크면 `ℓ=2,m=0`의 photon temperature quadrupole과 E-mode quadrupole RHS를 algebraic TCA value로 끌어당기는 형태다. 핵심 구현은 `Gamma_T/H_local > threshold` dispatch, free RHS source 계산, algebraic scalar solve, 그리고 `relax_rate = a_val * Gamma_T`로 현재값을 algebraic value에 relaxation시키는 부분이다. `code/integrator.py:434–498`

그러나 “IMEX implicit stage가 이 stiffness를 처리한다”는 말은 bundle 코드만으로는 검증되지 않는다. 포함된 `IntegratorConfig`의 기본 solver는 `LSODA`이고, 실제 실행은 `solve_ivp(... method=self.config.solver_method ...)`로 보인다. `code/integrator.py:121–135`, `code/integrator.py:649–658` LSODA가 stiffness를 자동 감지할 수는 있지만, 이것은 “프로젝트가 말하는 IMEX implicit stage가 deep TCA relaxation eigenvalue를 안정적으로 처리한다”는 주장과 동일하지 않다.

higher-ℓ 처리도 조심해야 한다. canonical CAMB practice는 deep tight-coupling에서 photon hierarchy 전체를 그냥 자유롭게 full hierarchy로 돌리는 방식이 아니라, tight-coupling expansion/approximation을 사용하다가 조건이 풀리면 full hierarchy로 전환하는 쪽이다. BASS는 “TCA pre-phase 금지” 때문에 conditional inline DAE만 허용한다는 정책을 갖고 있고, 그 자체는 이해된다. `reference_docs/CLAUDE_md_excerpt.md:45–49` 하지만 deep TCA에서 `ℓ≥3` photon multipole은 계층적으로 매우 작아야 한다. 그러므로 `ℓ=2,m=0`만 pin하더라도 collision operator가 higher-ℓ을 충분히 강하게 damping하고 있는지, 혹은 explicit/free-stream-like residual이 stiffness를 만들고 있는지는 별도 수치 감사가 필요하다.

또 하나의 큰 위험은 background/opacity table 범위다. `gamma_T_override` 문서에는 HYREC fixture의 `z_max=8000` 밖 테스트를 위한 override라고 적혀 있다. `code/integrator.py:156–160` 그런데 `z≈10^9`로 가려면 Thomson opacity, baryon/electron density, radiation-era background가 table clipping이나 fixture override가 아니라 production-grade callable로 닫혀 있어야 한다. 현재 `build_visibility_and_kappa_callables`는 recombination table 범위 밖 z를 clip한다. `code/flrw_pipeline.py:292–302` visibility LoS 자체는 recombination 근처가 중요하니 clip이 항상 치명적이라고 할 수는 없지만, deep-start integrator의 `Γ_T`/background source까지 같은 식으로 처리되면 안 된다.

마지막으로 source interpolation 문제가 있다. D-1은 LoS quadrature grid를 개선했지만, source 자체는 integrator output grid에서 추출되어 PCHIP로 들어간다. `flrw_pipeline.py`는 `integration_result.eta`를 source domain으로 삼고, LoS grid는 그 domain 안에서만 평가된다. `code/flrw_pipeline.py:319–364`, `code/los_grid_builder.py:43–46` `η=10^-3→14147`을 `n_output=64` 같은 식으로 저장하면 deep era와 recombination 주변 source sampling이 터진다. 실제 full repo에 dense source reconstruction이 있다면 괜찮지만, 이 bundle만으로는 그 보장이 안 보인다.

따라서 closure mechanism은 방향이 맞다. 하지만 “그대로 multi-month δ로 들어가면 닫힐 것”이라고 보기엔 위험하다. 먼저 deep-TCA stiffness, higher-ℓ damping, source-output resolution, opacity coverage를 작은 diagnostic으로 통과시켜야 한다.

---

### Q3. Missed defects

#### 3.1 Source-extractor sign/gauge convention: still live

D-3는 여전히 실제 결함 후보다. summary에 따르면 source extractor는 synchronous-gauge `Θ_0^S`를 가져와 Newtonian `Ψ`와 함께 `θ0+ψ+π/4` 형태의 source에 넣고 있다. 이 경우 `Θ_0^N = Θ_0^S + h_S'/6`류의 gauge correction이 필요하다는 주장이 문서화되어 있다. `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:199–233`

이게 6.43× 전체를 설명한다고 보지는 않는다. 하지만 δ measurement budget에 섞이면, “η_init을 당겼더니 남은 residual이 seed 때문인지 source gauge 때문인지”를 다시 분리해야 한다. 특히 Round-15 D-1 summary가 high-k residual은 D-3 신호로 남는다고 적은 점이 중요하다. `reference_docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:84–87`

#### 3.2 PSTF normalization at LoS projector: weak candidate

PSTF normalization이 단일 factor로 6.43×를 만들었다는 가설은 약하다. 기존 감사가 `4√2`, `2√π`, 기타 단일 convention factor들을 per-(k,ℓ) scatter 때문에 반박했다는 기록이 있다. `01_DETAILED_ANALYSIS.md:323–328`, `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:235–251`

다만 이번 bundle에는 `flrw_bessel_projector.py` 자체가 포함되지 않았다. 따라서 “projector normalization은 완전히 무죄”라고 말할 수는 없다. 현재 말할 수 있는 건 “단일 multiplicative normalization factor로는 관측된 residual pattern을 설명하기 어렵다”는 정도다.

#### 3.3 Polarization quadrupole basis: probably not the 6.43× cause

SSOT는 `Π_BASS = Θ_2 + E_0 + E_2`와 observable polter `2Θ_2/5 + 3E_2/5`를 구분하고, production polter에서는 `E_0`를 쓰지 않는다고 명시한다. `reference_docs/CLAUDE_md_excerpt.md:38–42` 이건 TT `D_2`의 6.43× residual을 직접 설명할 가능성이 낮다.

하지만 SW+polter source가 과거에 문제 후보였고, low-ℓ에서는 polarization source의 basis convention이 작은 잔차를 만들 수 있다. 따라서 D-2/D-3 이후 남는 percent-level residual을 볼 때는 다시 감사해야 한다.

#### 3.4 Background interpolation: current 6.43×보다 δ-risk에 가깝다

현재 261→today 경로에서 HYREC visibility가 Rust/Python 공유라면, interpolation 차이만으로 6.43×를 만들 가능성은 낮다. 그러나 `z≈10^9` 확장에서는 완전히 다른 문제다. table clipping, `z_max=8000` fixture, `Γ_T` production callable 미비는 δ closure를 실패시킬 수 있다. `code/integrator.py:156–160`, `code/flrw_pipeline.py:292–302`

#### 3.5 내가 추가로 보는 under-budgeted defect

가장 위험한 추가 결함은 **source-output sampling**이다. D-1은 LoS grid를 고쳤지만, source가 64개 integrator output point에서만 만들어진다면 더 촘촘한 LoS grid는 빈 껍데기일 수 있다. `code/integrator.py`는 `eta_out=np.linspace(...)`와 `t_eval=eta_out`를 사용한다. `code/integrator.py:629–658` δ에서 12 decades를 커버하면 이 문제는 더 심해진다. source extraction은 dense-output 또는 physics-adaptive output grid와 함께 재설계되어야 한다.

---

## 3. Counter-tests

### Test A — x-cut cumulative closure test

새 파일 제안: `scripts/v5_round17_d2_xcut_ablation.py`

기반 파일: `code/v5_round17_linear_probe_measurement.py`, 특히 k-grid와 pipeline config를 만드는 부분. `code/v5_round17_linear_probe_measurement.py:88–103`

실험 설계:

```python
eta_init = 261.0
x_cuts = [0.3, 0.5, 1.0, 2.0, np.inf]

for x_cut in x_cuts:
    if np.isfinite(x_cut):
        k_sub = k_grid[k_grid * eta_init <= x_cut]
    else:
        k_sub = k_grid

    # Simpson을 쓸 경우 odd length가 필요하면 마지막 점 하나 drop
    if len(k_sub) % 2 == 0:
        k_sub = k_sub[:-1]

    d2_bass = compute_flrw_d_ell_linear_probe(..., k_grid_mpc=k_sub, ...)
    d2_oracle = assemble_oracle_restricted_d2_from_rust_or_camb_transfer(k_sub)

    print(x_cut, len(k_sub), d2_bass, d2_oracle, d2_bass / d2_oracle)
```

판별 기준:

D-2가 맞으면 `x_cut≤0.3` 또는 적어도 `x_cut≤0.5`에서 restricted ratio가 1 근처로 내려가고, `x_cut`을 키울수록 residual이 증가해야 한다. 반대로 low-x restricted integral에서도 6×가 유지되면 D-2 주원인설은 크게 약해지고 D-3/source/projector 쪽으로 가야 한다.

중요한 점은 full anchor `1002.086744`와 비교하면 안 된다는 것이다. 반드시 같은 restricted k-domain의 Rust/CAMB oracle integral과 비교해야 한다.

---

### Test B — per-k transfer ratio versus `x=kη_init`

새 파일 제안: `scripts/v5_round17_seed_validity_perk.py`

목표는 `D_2` 적분값 하나가 아니라 per-k transfer response를 직접 보는 것이다.

출력 column:

```text
k, x, Delta_T2_BASS, Delta_T2_oracle, ratio, integrand_BASS, integrand_oracle
```

판별 기준:

D-2가 맞으면 ratio 또는 integrand residual이 `k` 자체보다 `x=kη_init`와 더 강하게 상관되어야 한다. 특히 `x≲0.3`에서 안정, `x≈1` 이후 급격한 drift가 보여야 한다. D-3나 projector normalization 문제라면 low-x와 high-x가 같은 방식으로 틀리거나, `x` collapse가 약할 것이다.

---

### Test C — eta-boundary collapse test

새 파일 제안: `scripts/v5_round17_eta_boundary_collapse.py`

가능한 범위에서 `η_init = 261, 100, 50, 20 Mpc` 같은 sweep을 돌리고, residual을 `k`가 아니라 `x=kη_init`에 대해 plot한다.

판별 기준:

D-2면 서로 다른 `η_init` 곡선들이 `x`축에서 collapse해야 한다. D-3면 `η_init`을 바꿔도 source gauge convention residual은 같은 방식으로 남기 때문에 `x`-collapse가 깨진다.

주의: 이건 `η_init`을 아주 이른 `10^-3 Mpc`까지 바로 미는 full δ가 아니다. 현재 background table과 integrator가 감당하는 작은 범위에서 seed-validity scaling만 보는 cheap diagnostic이다.

---

### Test D — deep TCA DAE stiffness audit

새 파일 제안: `scripts/v5_round17_deep_tca_stiffness_audit.py`

대상 코드: `code/integrator.py:434–498`, solver info `code/integrator.py:684–692`

실험:

`Gamma_T/H` effective ratio를 `{10^2, 10^4, 10^6, 10^8, 10^9}`로 만들고, 각 ratio에서 다음을 기록한다.

```text
ratio, nfev, nlu, status, max_abs(Pi2-Pi2_alg), max_abs(E2-E2_alg),
max_l_ge_3_photon_norm / max_l1_norm,
energy_constraint_residual,
momentum_constraint_residual
```

판별 기준:

`Γ_T/H`가 커질수록 `Π2`와 `E2`는 algebraic value에 더 잘 붙어야 한다. `ℓ≥3` multipole은 계층적으로 작아야 한다. `nfev`나 `nlu`가 폭발하거나 threshold 근처에서 discontinuity가 보이면 hard switch 대신 hysteresis/smooth dispatch가 필요하다.

---

### Test E — source-output resolution audit

새 파일 제안: `scripts/v5_round17_source_output_resolution_audit.py`

실험:

D-1 이후 같은 LoS grid를 유지하되 `n_output={64,128,256,512,1024}`로 BASS source를 다시 만들고 per-k, per-ℓ transfer를 비교한다.

판별 기준:

D-1이 완전히 해결된 상태라면 source-output resolution을 올려도 low-ℓ transfer가 안정적이어야 한다. 만약 residual이 계속 움직이면 남은 문제는 seed만이 아니라 source sampling/PCHIP domain 문제다.

---

## 4. Risks

가장 큰 위험은 D-2 자체가 아니라 **D-2를 고치는 긴 δ 작업에 들어간 뒤, D-3와 numerical stiffness가 섞여서 measurement budget이 불투명해지는 것**이다.

구체적 위험은 다음과 같다.

첫째, `x>1` 비율을 잘못 말하고 있다. 이건 작은 문서 오류처럼 보이지만, audit culture에서는 위험하다. 실제 수치는 `x>1: 37%`, `x>0.3: 57%`로 고쳐야 한다.

둘째, deep TCA에서 `ℓ=2,m=0`만 algebraically pin하는 설계는 원칙적으로 가능하지만, `ℓ≥3`이 실제로 강하게 damping되는지 확인해야 한다. canonical CAMB와 “철학적으로 유사”하다고 해서 “동일한 안정성”이 자동으로 따라오지는 않는다.

셋째, bundle 코드 기준으로는 native IMEX implicit stage가 보이지 않는다. 현재 보이는 건 LSODA 경로다. 이 mismatch는 문서/코드 중 하나가 낡았다는 뜻이다. `code/integrator.py:121–135`, `code/integrator.py:649–658`

넷째, `z≈10^9`에서는 HYREC visibility table을 공유한다는 말만으로 부족하다. `Γ_T`, `H`, `a`, `n_e`, baryon loading, radiation-era thermodynamics가 table clipping 없이 production callable로 닫혀야 한다. `code/integrator.py:156–160`, `code/flrw_pipeline.py:292–302`

다섯째, D-1은 LoS quadrature를 고쳤지만 source extraction output grid가 충분하다는 보장은 아니다. 12 decades integration에서 sparse `t_eval` 기반 PCHIP는 다시 주요 결함이 될 수 있다. `code/integrator.py:629–658`, `code/los_grid_builder.py:43–46`

여섯째, `primordial_b_k_sq` 의미가 코드 문서 사이에서 아직 흔들린다. `regular_adiabatic_ic.py`와 `flrw_pipeline.py`는 corrected linear-amplitude semantics를 말하지만, `integrator.py` 쪽 설명은 여전히 “amplitude squared / A_s”처럼 보인다. `code/regular_adiabatic_ic.py:111–135`, `code/flrw_pipeline.py:143–158`, `code/integrator.py:145–155` 실행 경로가 맞더라도 문서 drift는 다음 버그의 씨앗이다.

---

## 5. Sub-track ordering judgment

현재 계획의 `α → β → γ → δ`는 closure 관점에서는 비효율적이다.

내 추천은 다음이다.

```text
α  →  D-3  →  β' / δ0 diagnostics  →  δ full closure  →  γ
```

`α`는 canonical-vs-linear gap을 닫는 mechanical fix라서 먼저 하는 게 맞다. `D-3`는 sub-week이고, 이미 문서화되어 있으며, δ 결과 해석을 오염시킬 수 있으므로 δ 전에 닫아야 한다. 이건 기존 Round-15 plan의 방향과도 더 잘 맞는다. `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:297–331`, `reference_docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:113–123`

`β`는 “real IC”라는 이름 그대로라면 δ의 초기조건 현실화와 묶어서 가야 한다. 단, `z≈10^9` radiation-era IC에 맞게 β의 scope를 다시 써야 한다.

`γ`, 즉 `m∈{-2,…,+2}` 확장은 Bianchi physics에는 중요하지만 FLRW anchor closure의 직접 blocker는 아니다. 연구 로드맵상 병렬로 돌릴 수는 있어도, closure-critical path에서는 δ보다 앞에 둘 이유가 약하다.

---

## 6. Confidence

| 항목                   | Confidence | 업데이트 조건                                                                                                                             |
| -------------------- | ---------: | ----------------------------------------------------------------------------------------------------------------------------------- |
| Q1 D-2 diagnosis     |        4/5 | x-cut restricted oracle test에서 `x≤0.3`도 6×로 틀리면 2/5로 낮춤. 반대로 residual이 `x_cut`에 따라 단조 증가하면 5/5.                                     |
| Q2 closure mechanism |        3/5 | deep TCA stiffness audit, higher-ℓ damping audit, opacity/background coverage audit 통과 시 4–5/5. LSODA/IMEX mismatch가 남으면 3/5 이하 유지. |
| Q3 missed defects    |        3/5 | `tier_b_source_extraction.py`와 `flrw_bessel_projector.py` 본문이 빠져 있어 완전 판정 불가. D-3 patch 전후 per-k residual을 보면 confidence 상승.        |
| Q4 ordering          |        4/5 | D-3 patch가 실제로 <1% effect라면 δ 전 필수성은 낮아진다. 하지만 현재 문서 증거상 D-3를 δ 뒤에 두는 건 불필요한 혼선이다.                                                  |

---

## Final judgment

D-2는 **실제 결함**이고, `η_init`을 훨씬 이른 시각으로 당기는 δ 방향은 물리적으로 맞다. 하지만 현재 상태에서 “D-2 단독 원인 확정 → multi-month δ 착수”로 바로 가면 안 된다. 먼저 `x`-controlled restricted-k oracle test와 D-3 closure를 해야 한다.

가장 냉정한 결론은 이거다.

**D-2 is probably the dominant remaining architectural defect, but the present evidence is not yet clean enough to spend a multi-month δ budget without first closing D-3 and running the cheap x-scaling counter-tests.**
