# HTT P3: FLRW 거리곡선과 CF4 method-mix 분해, 2026-10-15

현재 실험은 실제 CF4 grouped-source 35,970개 및 사용자가 유지해 온 P3 논문 연구 DAG의 H02 경로를 이용한다. 판정은 **ACTUAL_SOURCE_CONDITIONAL_DIAGNOSTIC**이며 물리적 H(z), cosmological shear, anisotropy detection 또는 완성된 group selection likelihood가 아니다. 이전 H01 관측 결과를 덮어쓰지 않고 중요한 관측량 해석을 교정했다.

## 1. 필수 물리적 기준선

Source group의 관측 redshift proxy z_i=V_CMB,i/c, DMzp_i, eDMzp_i를 읽어 D_i=10^((DMzp_i-25)/5) Mpc, y_i=ln(cz_i/D_i)로 정의한다. km/s/Mpc 수치 로그를 취한다. 물리적 H(z)와 달리 이것은 redshift-dependent **apparent** quotient이다.

기준 모형은 H0=74.6 km/s/Mpc, Omega_m=0.3153, flat LambdaCDM이며

    dL_ref(z)=(c/H0)(1+z) ∫_0^z [Omega_m (1+z')^3+1-Omega_m]^(-1/2) dz'.

모든 그룹의 실제 redshift z_i에서 y_ref,i=ln(cz_i/dL_ref(z_i))를 계산한 뒤 고정 sample weights로 평균한다. Mean redshift에 dL을 대입하는 단순화가 아니다. Wolfram symbolic expansion:

    H0*dL(z)/c = z + (1-3 Omega_m/4) z^2 + O(z^3),
    q0 = 3 Omega_m/2 - 1,
    (1-q0)/2 = 1-3 Omega_m/4 = 0.763525 (Omega_m=.3153).

CAS difference equals exactly zero. 따라서 물리적으로 isotropic FLRW에서도 cz/dL는 z가 증가하며 감소한다. H01 raw depth trend를 cosmological H(z) 또는 beyond-FLRW signal로 직접 취급하는 해석은 부적절하다.

## 2. 실제 source 결과

원본 NPZ exact SHA-256:
86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c.

Four fixed non-overlapping z windows (km/s/Mpc):

| z-bin | N groups | Observed apparent H_eff | reference FLRW c z/dL | residual mean log ratio |
|---|---:|---:|---:|---:|
| .01-.03 | 8581 | 74.08727 | 73.44320 | +.00873141 |
| .03-.05 | 7833 | 73.68044 | 72.45938 | +.01671133 |
| .05-.075 | 8818 | 71.31156 | 71.22964 | +.00114946 |
| .075-.10 | 10738 | 68.88624 | 70.17124 | -.01848202 |

Near-to-far delta log H_eff:
- Observed apparent data: -0.0727872412.
- Isotropic FLRW reference in same source window: -0.0455738112.
- Source residual after FLRW reference removal: -0.0272134300.

정규적인 FLRW luminosity-distance redshift curve가 raw 변화의 상당 부분을 설명하므로, 처음 H01의 감소량 전체를 비등방적 팽창, H0 tension 또는 tilt로 해석하지 않는다. 이 기준 모형은 physical source velocities/selection를 포함한 맞춤 likelihood가 아니다.

## 3. 정확한 방법별 회계와 공통가중 표준화

Method family m∈{FP,OTHER,SN,TF}에 대해 bin j의 source-weight sum W_jm, f_jm=W_jm/Sum_m W_jm, within-method mean u_jm을 정의하면 ybar_j=Sum_m f_jm u_jm. Far/near 대칭 분해:

    delta ybar =
      Sum_m (f_far,m-f_near,m) (u_far,m+u_near,m)/2
      + Sum_m (f_far,m+f_near,m)/2 (u_far,m-u_near,m).

Wolfram 2-method symbolic identity residual zero, NumPy actual-source residual decomposition closure 3.47e-18.

| quantity | far-near total | method-composition | within-method |
|---|---:|---:|---:|
| raw apparent log H | -.07278724 | +.00846705 | -.08125429 |
| isotropic FLRW log c z/dL | -.04557381 | -.00215480 | -.04341901 |
| after sourcewise FLRW subtraction | -.02721343 | +.01062185 | -.03783528 |

이 케이스의 method-mix 항은 apparent H 감소를 증폭하지 않고 일부 **상쇄**한다. 내부 residual은 FP -.0598858, SN +.00114894, TF +.01891780, OTHER -.13364943이다. 이는 causal decomposition이 아니라 observational accounting이다. 특히 far bin TF 14개, OTHER 8개와 method/redshift/survey selection 때문에 물리적 단정은 불가능하다.

동일 method mixture pi를 모든 bin에 고정하면 상수 method별 modulus zero-point는 shell contrast에서 정확히 소거되지만, method-by-z selection/cosmic flow는 제거하지 못한다. Source residual far-near:
- raw survey: -.02721343;
- minimum-share common method mixture: -.04314543;
- FP/SN equal halves: -.02936843;
- FP-only: -.05988580.

Minimum-share pi in FP/OTHER/SN/TF order: [.71959494,.00438256,.26382840,.01219410]. Far standardized source Kish effective N ~594.3, not an effective independent cosmological sky count.

## 4. 가정상 calibration envelope과 background sensitivity

기존 H02의 수학적으로 정확한 영점 편향 민감도를 재사용한다. 이는 실제 CF4 calibration 측정값이 아니라 **가정상 per-method absolute modulus zero-point box**이다.

| assumed bound on each | residual logH far-near support | contains zero |
|---|---|---|
| 0.03 mag | [-.04870474,-.00572212] | no |
| 0.05 mag | [-.06303229,+.00860542] | yes |
| 0.10 mag | [-.09885114,+.04442428] | yes |

위 support는 95% 신뢰구간이 아니고 실제 데이터의 확률적 calibration 오차나 detection robustness를 입증하지 않는다. Fixed source weights와 sample membership 가정하의 algebraic sensitivity이다.

동일 Omega_m을 고정하고 H0만 74.6에서 70으로 변경하면 residual shell 차이는 1.25e-15 수준에서 동일하다. Omega_m 값을 [.20,.25,.3153,.40]으로 가정 변경하면 far-near residual은 [-.02159815,-.02405250,-.02721343,-.03124069]로 변한다. Omega_m posterior는 추론하지 않았다.

## 5. 이론-코드-관측 증거의 연결

코드:
- htt/obsstat/cf4_flrw_method_decomposition.py: sourcewise flat LCDM dL, exactly matched windows, numerical-stable symmetric two-term accounting, method poststandardization and diagonal-only propagated variance.
- tests/obsstat/test_cf4_flrw_method_decomposition.py: manufactured isotropic flat LCDM exact null, reference change invariance, method-mix closure, constant zeropoint shift, unique source IDs, real 35,970 group H01 regression, disjoint redshift support, linear variance propagation.
- scripts/run_htt_cf4_flrw_decomposition_20261015.py: original 35,970 group source actual refit, all reference scenarios, plot and reports, create-only, original data untouched.

Canonical output:
docs/research_program/observational_publication_20261015/results/H02_flrw_method_decomposition_v2/result.json
docs/research_program/observational_publication_20261015/results/H02_flrw_method_decomposition_v2/cf4_flrw_method_decomposition.png

Earlier v1 is a numerically valid scoped precursor; v2 adds explicit hypothetical method calibration scenario envelopes. Scientific/claim status remains source-conditioned diagnostic.

Source comparators:
- Tully et al., Cosmicflows-4, ApJ 944:94, https://doi.org/10.3847/1538-4357/ac94d8.
- Stiskalek et al., no evidence for local H0 anisotropy, 2026, https://doi.org/10.1093/mnras/staf2048.
- Duangchan et al., prior-free CF4 forward modelling, 2026, https://doi.org/10.1051/0004-6361/202556645.
- Desmond et al., distance prior and selection 2025, https://arxiv.org/abs/2511.03394.
- Karim et al., CF4 directional H0 study, https://arxiv.org/abs/2512.02526.
- CF4 peculiar velocity correlation and method/sky imbalance analysis (2026), https://arxiv.org/abs/2604.08314.

This by itself does not establish novelty over the listed works, even if technically reproducible.

## 6. Physical gap and next meaningful action

Remaining P3 H02 admission condition: source-qualified catalogue inclusion/selection and forward distance-modulus likelihood, group/method zero-point covariance, correlated peculiar velocity fields and observer/source frame redshift corrections; independent tracer holdout or matched mocks for false anisotropy. A full regression of physical H(z,n) additionally needs to distinguish radial flow and geometric source effects. P4/P6 and Bianchi type inference must not consume this H_eff scalar as geometry-frame shear.

Original owner checkout at /home/cosmosapjw/Dropbox/bianchi/htt_base stays read-only, prior HEAD 13d8d85f with 57 original dirty paths. No local Codex used; native subagent absent (NOT_RUN).
