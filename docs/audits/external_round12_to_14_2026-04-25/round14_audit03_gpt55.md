# V5-RUNTIME Round-14 External Audit Verdict

**Auditor**: GPT-5.5 Thinking
**Date**: 2026-04-25
**Bundle SHA**: `0536f0e`

## Verdict (one-line)

**HYBRID-RECOMMENDED** — 현재 BASS PSTF Python FLRW sub-horizon transfer path는 incremental calibration으로 production-grade 복구 불가. FLRW scalar baseline은 CAMB transfer를 직접 쓰고, BASS는 Bianchi/anisotropic residual engine으로 분리하는 게 맞다.

## Summary

Round-14의 결정적 자료는 F1/F2/F3가 서로 같은 방향을 가리킨다는 점이다. `4√2`는 per-`(k,ℓ)` transfer에서 전혀 보이지 않고, `n_output`을 늘려도 수렴하지 않으며, component ablation은 Doppler가 아니라 SW+polter와 ISW 양쪽 source path가 동시에 틀렸음을 보여준다. 이건 “상수 normalization fix” 문제가 아니라 **source extraction + metric reconstruction + source sampling/LoS assembly가 서로 엉킨 architecture-level failure**다.

감사 컨벤션: `k`는 `Mpc^{-1}`, conformal time `η`는 `Mpc`, CAMB/BASS 코드 경로는 사실상 conformal-distance 단위계를 쓴다. CAMB Notes도 conformal time과 Mpc 단위를 쓰며, source output routines가 Bessel functions에 적분될 source를 계산한다고 명시한다.  MB95 conformal Newtonian convention에서는 `θ = i k_j v_j`이고, Einstein anisotropic-stress constraint는 `k^2(φ−ψ)=12πG a^2(\barρ+\bar P)σ`다. ([arXiv][1])

## F1 / F2 / F3 검증

### F1 — `4√2`는 진짜 convention factor가 아니라 integrated accident

검증 결과: **F1은 성립한다.**

`phase_b_fix_D1D2D6D7.txt`의 D7은 `cal=1/(4√2)`를 곱했을 때 sub-horizon `D_2` ratio가 `1.0054`로 떨어지는 매우 깔끔한 결과를 낸다. 하지만 `round12_camb_comparison_n64.txt`의 direct CAMB comparison은 이 해석을 정면으로 깨뜨린다. 진짜 uniform normalization factor라면 `BASS α(k,ℓ) / CAMB Δ_T(k,ℓ)`가 모든 `k,ℓ`에서 거의 같은 상수, 예컨대 `+5.656...`, `1/5.656...`, 또는 power 기준 `32` 근방으로 나와야 한다. 실제 ratio는 `+0.2066, -0.9196, +129.6, +3.31, -27.24, +121.37, +1835.87`처럼 부호와 크기가 난장판이다.

따라서 `D_2` integrated match는 물리적 normalization 검출이 아니다. `D_2 ∝ ∫ dlnk P_R(k)|α(k)|^2`라서 부호 정보를 잃고, 특정 `k` 영역에서 작은 값과 큰 값이 가중 L2 norm 안에서 우연히 `1/32`에 가까워진 것이다. 이건 calibration이 아니라 fitting artifact에 가깝다.

### F2 — BASS는 `n_output`에 대해 수렴하지 않는다

검증 결과: **F2는 성립한다.**

`n_output=64→256→1024`에서 같은 `k,ℓ` transfer가 sign flip을 보이고, `k=5e-2, ℓ=3`은 `0.459 → 0.152 → 0.0238`로 약 19배 떨어진다. 이건 “더 조밀한 output을 쓰면 고쳐진다”가 아니라, output sampling/dense-output/PCHIP/source derivative가 transfer 자체를 바꾸고 있다는 뜻이다.

Seljak–Zaldarriaga line-of-sight method의 핵심은 source function과 geometric Bessel kernel을 분리해 source를 충분히 정확하게 sampling한 뒤 Eq. (13)류의 LoS integral을 수행하는 것이다. 특히 visibility derivative가 좁게 변하므로 recombination source sampling이 중요하고, 불충분한 temporal sampling은 spectrum-level error를 만든다고 명시되어 있다. ([ar5iv][2]) 현재 BASS처럼 solver output grid 자체를 `η_grid`로 삼고, 그 위에서 PCHIP와 finite difference로 `Φdot+Ψdot`을 만든 뒤 바로 Bessel integral에 넣는 방식은 이 요구조건을 만족하지 않는다.

PCHIP `overflow encountered in divide`는 단순한 harmless warning으로 취급하면 안 된다. 원인일 수도 있고 증상일 수도 있지만, 어느 쪽이든 해당 transfer output은 검증 불가다. 특히 Phase B fixed trace에서 `k=1e-4`의 `Ψ`가 `η_*` 근처에서 `-1.25 → -2.32 → +5.13` 식으로 튀는 건 정상적인 super-horizon/near-horizon scalar potential behavior가 아니다.

### F3 — Doppler가 아니라 SW+polter와 ISW source path가 둘 다 틀렸다

검증 결과: **F3는 성립한다.**

Component ablation은 아주 유용하다. `|SW + ISW + Doppler − FULL| ≈ 1e-17`이므로 ablation 자체는 선형적으로 잘 닫혀 있다. 그런데 Doppler dominance가 모든 cell에서 `<0.5%` 수준이므로 Doppler undersampling 가설은 버려야 한다.

반대로 SW+polter와 ISW가 둘 다 CAMB와 틀린다. `ℓ=2`만 봐도 `SW/CAMB = +0.40, +1.53, +157, -118`, `ISW/CAMB = -0.19, +1.78, -36, +177`이다. 이 패턴은 “한 source term의 부호 하나”라기보다, **metric potential reconstruction, photon monopole/quadrupole mapping, visibility/κ handling, source-grid interpolation** 중 복수 지점이 동시에 오염되어 있음을 시사한다.

CAMB source interface도 단순히 `g(Θ0+Ψ+Π/4)+e^{-κ}(Φdot+Ψdot)+d(gv_b)/dη` 수준이 아니라, `phi`, `phidot`, `sigma`, `sigmadot`, `qg`, `vb`, `qgdot`, `pig`, `pigdot`, `polter`, `polterdot`, `polterddot`, `visibility`, `dvisibility`, `ddvisibility`, `exptau` 등을 명시적으로 source routine에 전달한다. ([GitHub][3]) BASS current source assembly는 diagnostic baseline으로는 유용하지만 CAMB-accurate FLRW source engine이라고 부르기엔 아직 너무 얇다.

## Q1 / Q2 / Q3 / Q4 답변

### Q1 — `4√2`가 진짜 가짜 신호인가?

내 판정은 **가짜 신호**다.

진짜 `4√2` normalization이 있다면 isolate되어야 할 quantity는 다음이다. `σ_γ^BASS / σ_γ^CAMB`, `σ_ν^BASS / σ_ν^CAMB`, `Π^BASS / polter^CAMB`, `Θ_ℓ^BASS / F_ℓ^CAMB`, source-level `S_SW^BASS / S_SW^CAMB`, 최종 `Δ_ℓ^BASS / Δ_ℓ^CAMB`. 이 중 하나라도 진짜 convention factor라면 `k`와 `ℓ`에 거의 독립적인 상수 ratio가 나와야 한다.

현재 direct CAMB table은 그 반대다. 어떤 cell도 안정적인 `4√2`를 보여주지 않고, 심지어 부호가 바뀐다. MB95 Eq. (98)의 conformal Newtonian initial condition은 `δ_γ=-2ψ`, `θ_γ=θν=...=(1/2)(k^2τ)ψ`, `σ_ν=(1/15)(kτ)^2ψ` 같은 고정된 super-horizon relation을 준다. ([arXiv][1]) 이런 기본 relation 위에서 단일 normalization mismatch라면 `k`별 sign chaos가 아니라 uniform amplitude rescaling이 보여야 한다.

`D_2`의 `1.005` match가 우연이 아닐 수 있는 유일한 경우는, BASS α의 잘못된 `k`-dependent shape가 하필 `P_R(k) j_ℓ` weighting과 Route-B anchor weighting에서 같은 L2 norm을 만들도록 구조적으로 강제되는 경우다. 하지만 그런 symmetry나 conservation law는 보이지 않는다. 오히려 `D_2` 하나에 맞춘 scalar calibration이 per-cell CAMB transfer에서는 붕괴하므로, 우연이라고 보는 게 맞다.

### Q2 — BASS가 진짜 수렴 안 하는가?

그렇다. 현재 자료 기준으로는 **transfer-function construction이 수렴하지 않는다**.

`n_output`은 ODE solver 내부 accuracy가 아니라 output sampling/postprocessing resolution일 가능성이 크다. 그래서 `n_output`을 바꾸면 PCHIP input nodes, finite-difference derivative, recombination visibility sampling, Bessel quadrature가 전부 바뀐다. 이 상황에서 `α(k,ℓ)`가 sign flip을 보인다는 것은 transfer function이 물리량이 아니라 postprocessing artifact에 묶여 있다는 뜻이다.

PCHIP overflow는 cause/symptom 양쪽 가능성이 있다. 하지만 실무 판정은 같다. `np.all(np.isfinite(source arrays))`, `np.all(np.diff(η)>0)`, `max|Ψ|`, `max|Φdot+Ψdot|`, `∫g(η)dη`, `g` peak/FWHM, `κ` monotonicity를 통과하지 못하면 PCHIP output은 폐기해야 한다.

올바른 `n_output` 정책은 uniform-linear가 아니다. 최소한 다음처럼 분리해야 한다.

1. ODE solver 내부 step/adaptive tolerance
2. source evaluation grid
3. visibility/recombination-refined grid
4. late-ISW log-`a` grid
5. Bessel quadrature grid

Seljak–Zaldarriaga Eq. (12)–(13)류의 LoS 접근은 source function을 정확히 샘플링하고 Bessel projection을 따로 수행하는 구조다. recombination source는 visibility와 그 derivative 때문에 별도 refinement가 필요하고, late ISW는 다른 sampling policy를 가져야 한다. ([ar5iv][2])

### Q3 — SW+polter와 ISW가 모두 wrong인 root cause는 무엇인가?

현재 1순위 root cause는 **Newtonian-gauge potential reconstruction + source sampling/PCHIP derivative path**다. 단일 후보로 좁히면 `tier_b_source_extraction.py`가 1차 suspect이고, `flrw_bessel_projector.py`의 source assembly가 2차 suspect다.

가장 의심되는 구체 지점은 다음이다.

첫째, `tier_b_source_extraction.py:299–302`의 anisotropic-stress sign. 코드/주석은 `Ψ−Φ = +12πG a²/k²(ρ+p)σ`처럼 쓰고 `psi = phi + psi_minus_phi`를 한다. 그런데 MB95 Eq. (23d)는 `k²(φ−ψ)=12πG a²(\barρ+\bar P)σ`다. ([arXiv][1]) 만약 BASS의 `phi`가 MB의 `φ`, `psi`가 MB의 `ψ`라면 sign이 반대다. 다만 이름 mapping이 뒤집혀 있을 가능성도 있으므로, 이건 “확정 버그”가 아니라 **즉시 검증해야 할 line-level suspect**다.

둘째, `tier_b_source_extraction.py:291`의 momentum bracket. MB95는 `θ`를 velocity divergence로 둔다. ([arXiv][1]) BASS extractor는 radiation velocity를 `v_r=3Θ_1`로 해석한다. 이 자체는 temperature dipole convention에서는 가능하지만, tower slot에 들어간 `ℓ=1` 변수가 실제로 `Θ_1`인지, MB `θ`, heat flux `q`, 또는 `θ/k`인지가 완전히 닫혀 있어야 한다. CAMB Notes도 `ℓ=1` moment를 heat flux `q_i`로 다루며 `ρ_i q_i=(ρ_i+p_i)v_i`라고 적는다.  이 mapping이 한 번만 틀려도 `1/k` 또는 `1/k²`형 blow-up이 생기고, 지금 관측된 `k`-dependent chaos와 잘 맞는다.

셋째, `_fd4_derivative`는 “non-uniform grid에서도 된다”고 주석을 달았지만 실제 bulk stencil은 uniform-grid 4th-order formula다. 현재 `np.linspace`면 직접 원인은 아닐 수 있으나, adaptive/dense output이나 recombination-refined grid로 넘어가는 순간 틀어진다. 더 중요한 점은 `Φ+Ψ`를 sparse output 위에서 reconstruct한 뒤 finite difference로 ISW를 만든다는 구조 자체가 취약하다는 것이다.

넷째, `flrw_bessel_projector.py:424–453`의 source assembly는 CAMB source에 비해 너무 단순하다. 특히 polarization source의 derivative terms, visibility derivative terms, opacity derivative terms, and exact Doppler integration-by-parts convention이 닫혀 있지 않다. CAMB source interface가 `polterdot`, `polterddot`, `dvisibility`, `ddvisibility`까지 받는다는 사실은 이 차이가 단순 미관 문제가 아니라 accuracy path의 일부임을 보여준다. ([GitHub][3])

추가 isolation은 이렇게 해야 한다.

`CAMB variables → BASS projector`를 먼저 돌려라. CAMB에서 `Θ0`, `Ψ`, `Φdot+Ψdot`, `Π/polter`, `g`, `κ` 또는 equivalent source arrays를 뽑아 BASS projector에 넣었을 때 CAMB `Δ_ℓ`이 재현되면 projector는 일단 살아남는다. 실패하면 projector/source formula가 먼저다.

그 다음 `BASS variables → CAMB-like source formula`를 해라. BASS의 raw `Θ0`, `Θ1`, `Θ2`, `E2`, `Φ`, `Ψ`, `g`, `κ` time series를 CAMB-style source equation에 넣어서 source-level mismatch를 본다.

마지막으로 replacement test를 해라. `Ψ/Φ`만 CAMB로 교체, `Θ0`만 CAMB로 교체, `g/κ`만 CAMB로 교체, `Φdot+Ψdot`만 CAMB로 교체. 예측은 명확하다. `Ψ/Φ`가 root면 SW와 ISW가 동시에 크게 회복된다. `Θ0`가 root면 SW만 크게 회복되고 ISW는 남는다. `g/κ`가 root면 recombination SW amplitude가 주로 바뀌고 ISW는 제한적으로만 바뀐다. Bessel projection이 root면 모든 component가 비슷한 방식으로 망가져야 하는데, 현재 자료는 그쪽보다는 source 변수 쪽을 더 강하게 지목한다.

### Q4 — incremental fix path인가, architectural rework인가?

**Production path로는 architectural rework가 필요하다.** 다만 당장 연구 pipeline을 멈추지 않으려면 Option C 단독보다 **Option B: hybrid**가 낫다.

내 권장 판정은 다음이다.

`Option A: incremental fix`는 거부. `ψ−φ` sign, velocity/momentum convention, visibility normalization, finite-difference derivative 같은 line-level suspect가 있긴 하다. 하지만 F2의 non-convergence와 F3의 dual-source failure가 동시에 있는 상태에서는 한 줄 수정으로 production-grade `D_2`를 회복한다고 주장하면 안 된다.

`Option B: hybrid`는 채택. FLRW scalar baseline은 CAMB transfer를 직접 import하고, BASS PSTF는 Bianchi/anisotropic correction 또는 residual operator에 집중시켜라. 즉 `Δ_total = Δ_CAMB_FLRW + δΔ_BASS_aniso` 구조로 가야 한다. FLRW limit에서는 `δΔ_BASS_aniso → 0`을 regression gate로 둔다.

`Option C: re-derive from scratch`는 병행. Lewis–Challinor–Lasenby의 1+3 covariant line-of-sight implementation은 gauge-invariant variables와 PSTF multipoles를 쓰되, 안정성을 위해 constraint-violating variable choices를 피한다는 점을 강조한다. 특히 Newtonian gauge에서 constraint violation이 acute할 수 있다고 지적하고, CDM frame/synchronous-equivalent variables를 택한다. ([arXiv][4]) BASS가 PSTF-native solver를 진짜 만들려면 이 방향으로 source extraction을 다시 세워야 한다.

## 권장 fix path

### Phase 0 — 비교 기준 자체 봉인

먼저 CAMB direct comparison의 normalization caveat를 닫아라. CAMB `get_cmb_transfer_data`의 `delta_p_l_k`로 CAMB `C_ℓ`을 재조립해서 CAMB native `C_ℓ`과 맞는지 확인해야 한다. 이 테스트가 실패하면 F1의 절대 ratio는 재해석해야 한다. 하지만 이 경우에도 F2 non-convergence와 F3 component failure는 남으므로 BASS production 판정은 바뀌지 않는다.

동시에 analytic projector test를 추가해라. `S(η)=δ(η−η_*)`에 대해 `Δ_ℓ=j_ℓ[k(η0−η_*)]`가 나와야 한다. Gaussian narrow source, constant source, pure ISW toy source까지 넣어서 `flrw_bessel_projector.py` 자체를 분리 검증해야 한다.

### Phase 1 — source extractor line-level triage

첫 번째 실험은 `tier_b_source_extraction.py:299–302` sign test다. `anisotropic_stress=False`와 `True`, 그리고 `psi = phi - psi_minus_phi` variant를 놓고 MB95 Eq. (23d) residual

[
R_\pi = k^2(\phi-\psi)-12\pi G a^2(\rho+p)\sigma
]

를 직접 찍어라. 이 residual이 줄어드는 쪽이 올바른 sign이다. MB95의 식 번호 기준으로는 Eq. (23d)가 기준이다. ([arXiv][1])

두 번째 실험은 `ℓ=1` convention audit이다. `theta1_g`, `theta1_nu`, `vb`, `vc`가 각각 `Θ1`, `θ`, `v`, `q` 중 무엇인지 단위와 scaling으로 확인해야 한다. `k`를 바꿔가며 `v ∼ θ/k`인지 `v∼3Θ1`인지 직접 CAMB time evolution과 비교해라. 이게 틀리면 `φ = factor*(δρ - 3H*mom/k)` bracket이 `1/k` 또는 `1/k²` 오염을 만든다.

세 번째 실험은 visibility normalization이다. `build_visibility_and_kappa_callables`가 반환하는 `g(η)`에 대해 `∫ g(η)dη ≈ 1`, peak `z_*≈1090`, FWHM scale, `κ(η)` monotonicity를 검사해라. 만약 `query_visibility(z)`가 `dτ/dz e^{-τ}`류인데 `η` source로 그대로 쓰고 있다면 `|dz/dη|` Jacobian이 빠졌을 수 있다. 이 경우 SW amplitude가 크게 틀어진다.

### Phase 2 — sampling architecture 교체

`n_output`을 solver accuracy parameter처럼 쓰지 마라. `integration_result.eta`를 그대로 LoS grid로 쓰는 구조를 끊어야 한다.

권장 구조는 다음이다.

`ODE internal adaptive solve` → `validated dense state evaluator` → `source grid construction` → `source evaluation` → `Bessel quadrature`

source grid는 uniform-linear 하나가 아니라 recombination-refined grid, late-ISW log-`a` grid, reionization grid, endpoint-safe grid를 합친 composite grid여야 한다. `Φdot+Ψdot`은 sparse finite difference가 아니라 ODE RHS, automatic dense derivative, 또는 validated differentiable spline에서 얻어야 한다. `_fd4_derivative`의 “non-uniform works” 주석은 제거하거나 Fornberg non-uniform finite difference로 교체해라.

### Phase 3 — production hybridization

바로 쓸 production route는 다음이다.

FLRW scalar TT/EE/TE transfer는 CAMB에서 가져온다. BASS PSTF는 anisotropic background, Bianchi correction, tilt/residual response만 계산한다. 모든 inference-facing observable은

[
\Delta_\ell^{\rm total}(k)
==========================

\Delta_\ell^{\rm CAMB,FLRW}(k)
+
\delta\Delta_\ell^{\rm BASS,aniso}(k)
]

형태로 정의한다. regression gate는 `β→0`, `Σ→0`, `W→0`, `Ω_{k,aniso}→0`에서 `δΔ_BASS→0`이어야 한다. Route-B Rust `D_2=1002.086744 μK²` anchor는 그대로 보존한다.

BASS-native FLRW reproduction은 별도 long-track으로 돌려라. 그 트랙은 “CAMB를 대체한다”가 아니라 “1+3 PSTF equations에서 CAMB-level FLRW scalar transfer를 독립 재현한다”는 검증 프로젝트로 취급해야 한다.

## Confidence and caveats

Confidence: **0.82**.

가장 큰 caveat는 내가 여기서 CAMB/BASS를 새로 재실행하지 않고, 번들의 transcript와 static code inspection을 기준으로 판정했다는 점이다. 따라서 CAMB `delta_p_l_k`의 exact normalization closure test는 아직 필요하다. 하지만 그 caveat는 `4√2` 절대 ratio 해석에만 영향을 준다. `n_output` non-convergence와 SW/ISW dual failure는 CAMB convention 하나로 설명되지 않는다.

두 번째 caveat는 `tier_b_source_extraction.py:299–302`의 anisotropic stress sign을 “확정 버그”로 부르면 아직 이르다는 점이다. BASS 내부 `Φ/Ψ` 명명법이 MB95와 뒤집혀 있으면 sign 자체는 살아남을 수 있다. 그래서 내가 권하는 건 즉시 patch가 아니라 Eq. (23d) residual test다.

최종 결론은 분명하다. 현재 상태에서 `4√2`, `k_min clipping`, `n_output increase`, `Doppler fix` 류의 incremental patch를 더 쌓는 건 시간 낭비에 가깝다. FLRW scalar transfer는 CAMB로 고정하고, BASS는 anisotropic residual solver로 살려라. Native PSTF FLRW path는 constraint-residual 기반으로 재설계해야 한다.

[1]: https://arxiv.org/pdf/astro-ph/9506072 "arXiv:astro-ph/9506072v1  11 Jun 1995"
[2]: https://ar5iv.labs.arxiv.org/html/astro-ph/9603033 "[astro-ph/9603033] A LINE OF SIGHT INTEGRATION APPROACH TO COSMIC MICROWAVE BACKGROUND ANISOTROPIES"
[3]: https://github.com/cmbant/CAMB/blob/master/fortran/equations.f90 "CAMB/fortran/equations.f90 at master · cmbant/CAMB · GitHub"
[4]: https://arxiv.org/pdf/astro-ph/9911177 "arXiv:astro-ph/9911177v2  1 Jun 2000"
