# R51: source-bound 응답 교정과 PR3 저-ℓ 관측 likelihood

기준: 브랜치 `research/r50-observed-convergence-20261115`, base `82360535625cde7113c42ad1c9d448df002170f2`.
기준일 2026-11-15 (Asia/Seoul). claim tier C0, transfer source = 1차 Bianchi-I 적분 shear ISW (native solver 아님).
상세 수치: `R51_PR3_LOWELL_RESULT.json`, 계약: `R51_SOURCE_OPERATOR_CONTRACT.json`, 사전등록: `PREREGISTRATION.json`.

## 0. Baseline 재현 (새 성과로 집계하지 않음)

- R50 회귀 39 passed (exit 0), `logs/baseline_pytest.txt`.
- R50 Gaia benchmark 재실행 exit 0, 커밋된 값과 최대 절대차 3.9e-12 (BLAS 반올림). R50 receipt 바이트는 git 복원으로 보존.

## 1. 응답 계수: 원전 연결 또는 격리

코드 소유 registry `RESPONSE_TERM_REGISTRY` (`htt/htt/htt/infer/r51_source_bound_response.py`)가 R49의 모든 응답 항을 분류한다.

| 항 | 상태 | 근거/이유 |
|---|---|---|
| CMB T, type-I 경계 | SOURCE_BOUND | $\delta T/T(\hat n)=-\hat n^a\hat n^b\Sigma_{ab}$, $\Sigma_{ab}=\int_{t_*}^{t_0}\sigma_{ab}dt$ (Collins–Hawking 1973; Barrow–Juszkiewicz–Sonoda 1985). 정확한 Bianchi-I 적색편이 $T\propto(\hat n^Te^{2\Sigma}\hat n)^{-1/2}$의 1차항임을 검사, 잔차 $O(\Sigma^2)$ (비 4.000). |
| shear history | CONDITIONAL | $\Sigma=I_{\rm hist}(\sigma/H)_0$, $I_{\rm hist}=\int_{a_*}^1a^{-4}/E\,da=3.927\times10^4$ (Planck18 ΛCDM). $\sigma a^3$=const, 비등방 stress 없음(자유흐름 중성미자가 위반) 가정. 물질 단독 닫힌형 $\tfrac23(a_*^{-3/2}-1)$ 일치. |
| 편광 gain 0.18, 유한곡률 focus/twist(0.25/0.35, tanh 0.6x, 0.6+0.4n_z …), 공분산 excess 1e-8 | WORKING_MODEL | 유도 없음. 물리 likelihood에서 제외. |
| count dipole $c_{EB}\beta_{MO}$ | SOURCE_BOUND | Ellis & Baldwin 1984. |
| count dipole $0.1A$, CF4 $0.1zA$, Gaia $H_0(\beta+A)$, $H_0\omega$, $H_0\sigma+0.25Q(\beta)$, Pantheon $0.5A$·$O(z)$ shear, DESI contrast×0.02 | WORKING_MODEL | 등속은 정적 aberration만 만든다(drift 없음); E2는 R50의 endpoint-history $A_{\rm PM}$; Pantheon 1차 Heinesen 항은 $O(z^0)$의 $(\hat n\cdot a-\sigma_{nn})/H$ 등. |
| DESI BAO 등방 | SOURCE_BOUND | 배경 거리. |

**새로 확인한 구체 결함:** R49 선형 CMB 경로는 `sigma_N`을 $\Sigma$(시선 적분 shear)로 쓰는데(`x_curvature=1`), 같은 상태 벡터의 `sigma_AB_stf5`를 Gaia/DESI에서는 오늘의 $\sigma/H_0$로 쓴다. history operator를 1로 둔 셈이고 물리값 $\approx3.9\times10^4$와 다르다. 따라서 R49 24D 공동 posterior의 shear 차원은 서로 다른 epoch의 양을 한 좌표로 묶었다.

**코드 처리:** `R49GeneralBianchiLikelihood(response_policy="source_bound")`만 `physical_inference_admissible=True`. 이 정책은 CMB(T, type-I/FLRW, history operator 경유), Quaia/NVSS/RACS(Ellis–Baldwin), DESI(BAO만)를 허용하고, Gaia/Pantheon+/CF4는 R52로 미루며 활성화 시 `WorkingModelResponseError`. 유한곡률 family는 예외. 기본 `r49_working_model`은 과거 receipt 재현 전용. transfer 출력에 `response_provenance` 태그 추가(수치 불변).

## 2. 공동 Gaussian과 유한 MC law

- ℓ-overlap 금지 제거: 하나의 정규화 Gaussian에서 $\mu(\theta)$, $C(\theta)$가 같은 모드에 있어도 logdet 1회. 중복 계상은 `DataBlockRegistry`(같은 byte identity가 두 독립 factor에 들어가면 거부)로 차단.
- 유한 MC: Sellentin & Heavens (2016) 정규화 t-law. p=1 적분 1.0, p=2 수치적분 1−7e-10, $N\to\infty$에서 Gaussian 일치.
- **사전등록 heldout 검증** (FFP10 SMICA 0–199 train, 200–299 heldout; Bonferroni 0.05/12):

| carrier / law | 68% coverage [CP 95%] | 95% coverage [CP 95%] | KS p | 판정 |
|---|---|---|---|---|
| T45 finite-MC | 0.67 [0.57,0.76] | 0.96 [0.90,0.99] | 0.76 | 보정됨 |
| T45 plug-in Gaussian | 0.36 [0.27,0.46] | 0.68 [0.58,0.77] | 9e-21 | 기각 |
| TEB135 finite-MC | 0.69 [0.59,0.78] | 0.95 [0.89,0.98] | 0.73 | 보정됨 |
| TEB135 plug-in Gaussian | 0.00 [0,0.036] | 0.00 [0,0.036] | 0 | 기각 |

R49가 쓴 plug-in(+jitter) 공분산 처리는 실제 MC 앙상블에서 과소포괄한다. R49 receipt의 CMB χ²/dof≈2.0과 같은 규모가 Σ=0 관측값과 FFP10 복제 모두에서 나타난다: 135모드 관측 $Q_0=296.2$ (2.19/dof), 같은 추정량 LOO 복제 중 112/300이 그 이상 (p=0.375). 새 독립 실현의 유한 MC 기대치 $p(N-1)/(N-p-2)=247.6$과 같은 규모다. 따라서 그 χ² 수준만으로는 모델 부적합을 뒷받침하지 못하며 sample-covariance plug-in으로 설명 가능하다 (R49-A06; R49 posterior 잔차 자체는 재계산하지 않음; 범위: SMICA 진단 lane).

## 3. 보유 PR3 계약

- SMICA map/mask SHA256이 R49 rehash와 일치. 관측 135-벡터 R49 캐시와 차 0.0 μK. FFP10 캐시 0, 299번을 독립 astropy reader로 재추출: 상대차 5e-11, 9e-11.
- Mask: PR3 common Int/Pol (f_sky 0.779/0.781); 추정량은 ℓ=0,1 열을 포함한 결합 역행렬로 monopole/dipole를 deproject.
- Beam: SMICA HDU2 `INT_BEAM`×pixwin(2048) = 1.00028–1.00034 (ℓ=2–6) template에 적용.
- 응답 J는 원자료와 **동일한** mask 추정량 통과. 이상 template 대비 2.9e-4 (mask 해상도 차), T→E/B 누설 0, R49 transfer 경로 대비 1.7e-15 (mode packing convention 일치).
- **Commander primary calibration: UNAVAILABLE.** 지도는 있으나 matching MC가 cmb_mc 완전 파일 2개+partial, noise_mc 없음. SMICA lane은 이름 그대로 진단 lane. Commander−SMICA T45 차 rms 0.63 μK(SMICA 잡음 sd의 7.3배)이나 $\hat\Sigma$ 이동 ≤0.055σ (uncalibrated diagnostic).
- **Removed-mode:** kinematic quadrupole(KQ) 제거 여부는 FITS header·로컬 문서로 확인 못함 → UNBOUND. KQ는 $\Sigma_{KQ}=-b_\nu\beta^2(\hat\beta\hat\beta-I/3)$로 정확히 Σ 방향에 사영된다. $b_\nu\in[1,2]$에서 최대 이동 0.25σ.
- PR4/NPIPE, 신규 다운로드 사용 없음.

## 4. 관측 결과 (T-only, S: 300 pairs, finite-MC law)

추정량: 정규직교 STF5 기저의 $\Sigma_{ab}$, Galactic frame, 무차원, $z_*=1089.94\to0$ 시선 적분.

- $\hat\Sigma=(0.02,\,0.66,\,-0.97,\,-0.20,\,-0.21)\times10^{-5}$. Fisher sd $\approx(0.86,0.83,0.91,0.83,0.87)\times10^{-5}$; 같은 추정량 LOO 표본 sd는 Fisher의 1.15–1.16배 → **보정 sd $\approx(1.00,0.95,1.06,0.96,1.00)\times10^{-5}$**.
- 구간 보정(독립 심사 RV01): finite-MC law는 **예측 자료 law**를 보정할 뿐 모수 구간은 아니다. Σ=0 LOO 300 복제에서 명목 95% 성분 구간 포괄률: Fisher 폭 0.90–0.92, finite-MC posterior 폭(1.07×Fisher) 0.92–0.94, LOO 표본공분산 폭 0.94–0.96. 따라서 주 결과는 LOO 보정 폭을 쓴다.
- Σ=0 검정: Wald 2.11, 같은 추정량 LOO null에서 265/300 이상, $p_{MC}=0.884$. 관측 shear 신호 없음.
- 95% 상한 (LOO 보정) $|\Sigma|_F<3.74\times10^{-5}$ (보정 전 posterior 값 3.54e-5는 과소포괄).
- **조건부** $|\sigma/H|_{0,F}<9.5\times10^{-10}$ (95%, LOO 보정). 비등방 stress 없음·Bianchi-I·T-only 조건부. $I_{\rm hist}$의 67%가 z>500에서 오고 그 구간에 복사(z_*에서 밀도 24%)와 자유흐름 중성미자 stress가 작용하므로 정량화되지 않은 계통오차가 있다. 기존 Bianchi 제약(예: Saadeh et al. 2016)과 정규화·모델·자료가 달라 직접 비교하지 않는다.
- PPC: T45 $Q_0=40.8$, LOO p=0.857.

## 5. 비교 (같은 자료·prior box·N·law)

| 비교 | 결과 | 판정 |
|---|---|---|
| raw 45D finite-MC vs tensor $(F,t,Q_0)$ | 최대 logLR 오차 9.9e-14 (500점, $N(\hat s,25F^{-1})$) | TIE (정확) |
| Gaussian law에서 $(F,t)$ | 1.7e-13 | TIE |
| finite-MC law에서 $(F,t)$만 ($Q_0$ 누락) | 104.4 | $(F,t)$는 불충분; scalar $Q_0$ 필요 |
| optimal linear score | 동일 $(F,t)$ | TIE |
| scalar 고정축 $e_1$ | 일반화 Fisher retention (1,0,0,0,0); $e_1$ marginal만 동률 | 5D target에서 LOSS |
| power-only $|s|^2$ | ±1e-5 대안 logLR=0; full은 0.36, 1.92, −2.17, −0.90, −0.63 | LOSS |
| finite-MC law vs plug-in Gaussian 공분산 | 위 heldout 표 | finite-MC가 보정, plug-in 기각 |

HTT tensor carrier는 정확한 GLS/score와 동률이다. 우월성은 주장하지 않는다. 결과가 실제로 바뀐 것은 공분산 law 선택이다.

## 6. 다섯 변수·null

- x는 signed STF5 $\Sigma$와 $(F,t,Q_0)$ 공동 carrier로 유지. scalar $x_C$로 대체하지 않음.
- σ(오늘, 물질 congruence, σ/H₀), Σ(시선 적분), ω(ω/H₀), A(A/(cH₀), Class-B $a_a$와 구분), β_RM(z_*), β_MO(z=0), frame spin(ICRS, μas/yr)을 contract에 분리 기재.
- Σ=0 null은 같은 추정량 LOO 복제로 계산 (근사 교환가능: 관측은 300개, 복제는 299개 S). β_MO 같은 추정량 joint null은 만들지 않았다 → `BETA_MO_MATCHED_NULL` 출력 없음, 옛 `null_beta`/`ffp10_null_beta` 키 미사용.

## 7. 독립 심사

한 번의 독립 심사(`INDEPENDENT_REVIEW.json`): critical 없음, major 2 (모수 구간 과소포괄, 0<n_mc≤p에서 숨은 Gaussian fallback), minor 9. 모두 수정 후 재실행·회귀(74 passed). 수정 결과의 재심사는 하지 않았다(1회 심사 규약).

- 사전등록 정정: E/B 제외는 Gaussian law에서만 free-mean 주변화와 같다; 사전등록은 같은 스크립트 첫 실행에서 기록됐고 SMICA 벡터는 R49에서 이미 분석됐으므로 blind 분석이 아니다.
- source-bound CMB 평가는 방출·관측자 운동학적 ℓ≥2 항을 제외(속도 0), SSOT T_CMB=2.72548 사용, ΔΩ_k≠0이면 거부. source_bound 정책은 모든 활성 probe의 data-block identity를 요구한다(DESI 포함). 파생 중첩(Quaia←Gaia DR3, NVSS/RACS)은 byte identity로 감지할 수 없다.

## 8. 남은 의무

1. Commander matching MC 부재 → primary calibration unavailable (PR4 불필요; Commander FFP10 MC 완결 시 재실행).
2. KQ 제거 계약 미결합 (≤0.25σ 민감도).
3. 편광: source-bound Thomson 응답 없음 → E/B는 free-mean nuisance로 제외.
4. history operator: 자유흐름 중성미자 비등방 stress 미포함; Bianchi-I 외 family는 working model.
5. Gaia E2 history operator, Pantheon 저-z jet, CF4 grouped likelihood, β_MO/β_RM 분리와 같은 추정량 velocity null → R52.
6. Cobaya Likelihood/Theory provider 확장은 R52(공동 likelihood) 범위.

다음 노드: R52 (`LOCAL_AGENT_RESTART_PROMPT.txt`).
