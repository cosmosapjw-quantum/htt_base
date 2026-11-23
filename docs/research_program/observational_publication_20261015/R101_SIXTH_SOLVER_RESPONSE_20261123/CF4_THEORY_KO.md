# CF4에서 공분산 경로와 선택법칙을 실제 관측량까지 미분하기

**R1 | 연구 단위.** R100의 첫 두 깊이창이 마지막 두 창을 예측하는 18차원 Gaussian 통계량을 고정한 채, R5 WF 공분산에서 Fourier band를 복원할 때 **예측 평균과 분산이 각각 얼마나 움직이는지** 계산했다. 별도로 6dFGSv 공개 표본의 CF4 table 2 고유 매칭 확률에 R100이 추정한 mark 계수를 넣어, 같은 행·같은 장에 대한 정규화된 likelihood를 계산하는 함수를 구현했다. HTT가 소유하는 조건부 apparent 관측 법칙이다. 새 transfer, 독립 관측 split, 물리적 strict-tail null의 입력은 없다.

**R2 | 근거.** 출발점은 `f8931fbef075d55c2c2a3caee8b8f5db5174b16b`의 다음 세 자료다.

- `scripts/r99/cf4_source_law.py`의 `schur`는 첫 18성분만으로 공통 9개 평균을 추정한다. 잔차 공분산에 추정된 평균의 불확실성을 더한다. 같은 파일의 `joint_selected_logpdf`는 고정된 대상들이 모두 포함된 사건에 대해 finite shared-field를 공동 정규화한다.
- `scripts/r100/cf4_upstream_and_kband.py` A3는 4×9 요약과 두 개의 36×36 공분산을 기록했다. 사용한 `CF4_FULL_KBAND_COVARIANCES.npz`의 SHA-256은 `7d5ecd55b776b8b9b97ae32385fd4573db8916846bb4c0a6dc5eca85eab18093`이다. A4는 8,885개 6dFGSv 행에서 고유 매칭 여부를 probit에 적합하고, 7,190개 고유 매칭 행에서 별도로 지정한 soft magnitude cut으로 likelihood를 예시했다. 4개 ambiguous 및 1,691개 미매칭 행은 고유 매칭 집합 밖에 있다.
- Springob et al. §4.1 및 table 1은 관측 mark를 `η=log10(Dz/DH)`와 그 폭으로 정의하고 추가 skew를 기록한다. 아래 계산은 R100의 Gaussian 폭 근사를 유지한다. CF4의 table 2는 여러 측정법을 합친 release이다. 공개 FP 행간 매칭 확률은 upstream survey의 target 선택과 CF4 전체 rejection의 결합 확률과 서로 다른 사건에 관한 양이다. [6dFGSv](https://doi.org/10.1093/mnras/stu1743) · [CF4 release](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJ/944/94)

**R3 | 이전 두 보조연구와 두 legacy 연구의 적용 조건.** DP–MZ 연구 §3.4의 object-wise selection과 shared field 정규화를 유지한다. parameter-flow §7의 36차원 고정 zero-mean 응답을 실제 9개 nuisance 평균을 포함한 예측 실험으로 확장한다. legacy 첫 연구 D/G의 조건부 mark·관측 연산자 response와 두 번째 연구 N7·§5의 동일 사건측도 및 변화하는 통계적 내적의 미분을 이 두 계산에 적용한다. 여기서 α는 공분산 보간 좌표다. 시간동역학, Markov 생성자와 memory closure를 도입할 가정은 사용하지 않았다. 명시적으로 주어진 R100 Gaussian model, 고정된 창/관측점, 고정 설계, full-rank training design과 양정치 C가 전제다.

**R4 | 두 계산 표현.** 훈련자료의 GLS β와 그 공분산을 명시적으로 미분하는 방법과, β에 불변인 error contrasts를 먼저 구성하고 예측하는 방법은 동일한 Gaussian 조건부 법칙을 준다. 후자를 계산에, 전자를 독립적인 수치 oracle에 썼다. Error contrast와 flat fixed-effect measure의 대응은 알려져 있다. 아래 미분은 이 자료의 train/test 설정에서 직접 유도한다. [Harville (1974)](https://doi.org/10.1093/biomet/61.2.383)

**R5 | 예측법칙의 유도.** 훈련·평가순으로 쌓은 요약 $y=(y_t,y_s)$에 대해 $Ey_t=X\beta, Ey_s=H\beta$이다. $U$의 열을 $X^\top$ 영공간의 직교정규기저로 두고 $L X=H$인 $L=HX^+$를 택한다. 행연산자 $T=(U^\top,0), W=(-L,I)$는 모두 미지 공통 평균을 소거한다. $V=TCT^\top, K=WCT^\top V^{-1}, B=W-KT$로 두면 $BCT^\top=0$이다. 따라서 $Ty$와 $By$는 독립 Gaussian이고 $e=By=y_s-m, S=BCB^\top$이다. 예측 평균 $m=Ly_t+KTy$에는 훈련값만 들어간다. 이와 동등한 flat-β 예측은 $\hat\beta$를 훈련자료에만 적합하고 그 오차를 주변화하여 얻는다.

$D=\partial_\alpha C=C_1-C_0$에 대해
$$
K'=BDT^\top V^{-1},\qquad m'=BDT^\top V^{-1}Ty,\qquad S'=BDB^\top.
$$
세 번째 식에서 $B'=-K'T$가 들어가는 두 항은 $BCT^\top=0$ 때문에 소거된다. $v=S^{-1}e, q=e^\top v, \ell=-[q+\log\det S+n_s\log(2\pi)]/2$이면
$$
q'=-2m'^\top v-v^\top S'v,\qquad
\ell'=-\tfrac12\{q'+\mathrm{tr}(S^{-1}S')\}.
$$
오차대조 공간에서 $S'\succeq0$여도 $m'$의 부호는 데이터·설계에 의존한다. 기존 36차원 전체 영평균 score에서 독립적으로 얻을 수 없는 항이다.

**R5 | 선택법칙의 유도.** 장 지표 $h$와 고정 공변량 $g_i$를 조건으로 $\eta_i\sim N(m_{hi},s_i^2)$가 독립이며 선택확률이 $\Phi(a_i+b_i\eta_i)$라 하자. 독립 표준정규 변수 $E_i$를 도입하면 포함 사건은 $E_i-b_i\eta_i\le a_i$다. 따라서 $\pi_{hi}=\Phi[(a_i+b_i m_{hi})/\sqrt{1+b_i^2s_i^2}]$. 장의 prior $p_h$ 아래 전체 표적 집합이 모두 포함되었을 때
$$
\ell_{\rm sel}
=\log\sum_h p_h\prod_i N(\eta_i;m_{hi},s_i^2)\Phi(a_i+b_i\eta_i)
-\log\sum_h p_h\prod_i\pi_{hi}.
$$
분자·분모의 정규화된 장 가중치를 각각 $w_h^N,w_h^D$, $t_{hi}=\Phi^{-1}(\pi_{hi}), u_i=\sqrt{1+b_i^2s_i^2}$라 하면 고정 selection coefficient 및 폭에서
$$
\ell_{\rm sel}'=\sum_h w_h^N\sum_i
 (\eta_i-m_{hi})m'_{hi}/s_i^2
 -\sum_h w_h^D\sum_i[\phi(t_{hi})/\Phi(t_{hi})] b_i m'_{hi}/u_i .
$$
선형 template amplitude의 score에는 $m'_{hi}=m_{hi}$를 사용한다. R100의 finite-redshift `bolometric` 출력으로 구성한 mean template의 배율이다. 6dFGSv의 native mark 정의는 comoving distance ratio이며, 여기서는 두 선택법칙을 같은 예시에서 비교하도록 R100이 사용한 bolometric field template를 고정했다. 물리적 rapidity 자체를 미분하는 경우 $m'_{hi}$를 그 좌표에 맞게 제공해야 한다. 각 행은 장 하나를 공유하며 $w_h^D$와 표본 mark를 관측한 뒤의 $w_h^N$을 별도로 반환한다.

관측된 8,885개 release-parent 전체의 매칭 패턴을 고정하는 두 번째 실험도 구현했다. $I$는 고유 매칭된 7,190개, $J$는 그렇지 않은 1,695개다. $J$의 mark는 적분하여 소거한다. 각 장의 분자와 분모 항에 동일한
$$
R_h=\prod_{j\in J}\Phi(-t_{hj})
$$
를 곱하고, 위의 양의 사건 곱은 $I$에 대해서만 취한다. $R_h$는 장에 의존하여 두 합에서 보통 상쇄되지 않는다. 각 장의 양쪽 score에 $-\sum_{j\in J}[\phi(t_{hj})/\Phi(-t_{hj})]t'_{hj}$를 더한다. 누락된 하나의 mark를 직접 적분한 뒤 얻은 field weight 및 관측밀도와 일치했고, 중심차분으로 두 score를 검산했다. 모든 행이 음의 사건이면 관측할 mark가 없으므로 pattern 확률을 조건으로 한 mark의 log density와 그 score가 모두 0이다. 실제 데이터 실행은 공개 6dFGSv 단계의 매칭 실패만 이 음의 사건으로 사용한다.

**R6 | 부호·차원·경계조건.** $\mu=\mu_0-5\eta$이므로 magnitude에서의 공동 log density는 dex 값에서 $N\log 5$를 뺀 값이다. R100 empirical probit의 $\eta$ 계수는 −0.98517524다. magnitude당 probit 선형지수 기울기는 +0.19703505이고 기존 fixed-cut 예시의 값은 −3.33333333이다. $cz=11{,}000$ km/s, ungrouped에서 $\eta=-0.1,0,+0.1$ dex의 fitted 매칭 확률은 0.82575, 0.79926, 0.77049이며 기존 예시의 포함 확률은 0.56618, 0.96662, 0.99977이다. 이는 같은 $\mu$ 관례로 환산한 두 **서로 다른 선택법칙**의 비교다. 고유 매칭 확률에 적합된 계수 자체가 galaxy의 distance-ratio convention 오류라는 해석은 성립하지 않는다. 일반식은 $b=0$, 단일 장, nuisance 0개, 훈련 설계 포화, $C'=C$인 scale covariance의 극한을 갖는다. $C'=C$일 때 $m'=0, S'=S, q'=-q$. $C$의 전체 양정치성 및 훈련 rank를 검사한다.

**R7 | 실행.** `b_published_4x9`를 window 순으로 펼쳐 R100 보간 $C(\alpha)=C_0+\alpha D$에서 계산했다. 예측 잔차는 무차원, density 단위는 R100의 고정 18성분 좌표 기준이다. 18차원 관측벡터의 같은 Gaussian 좌표계에서만 log density 차이를 비교한다.

| α | q | 평균이 주는 q′ | 공분산이 주는 q′ | log density | log density′ |
|---:|---:|---:|---:|---:|---:|
| 0 | 12.116321 | +0.306130 | −1.946947 | 65.698956 | −0.839223 |
| 0.5 | 11.435438 | +0.359483 | −1.507964 | 65.294925 | −0.769811 |
| 1 | 10.927665 | +0.332656 | −1.239675 | 64.930844 | −0.687509 |

공분산 확장만 보면 중점에서 $q'=-1.50796$이지만 평균 이동을 포함하면 −1.14848이다. R99/R100의 양 끝 $q,\ell$ 최대 절대 오차는 $5.69\times10^{-14}$. 12점 Gauss–Legendre 적분으로 복원한 $(\Delta q,\Delta\ell)=(-1.18865549,-0.76811138)$의 오차는 각각 $1.60\times10^{-14},4.59\times10^{-14}$였다. 세 선택기울기에서 직접 mark 밀도를 수치적분한 2행·3장 fixture로 공동 정규화와 score를 검산했다. 양 부호의 기울기, 0기울기, training/test 분리, 좌표변환을 포함한 7개 unittest 메서드가 통과했다.

**R8 | 판정.** 예측 평균·공분산 tangent와 공동 probit 분모는 위 가정 아래 직접 유도했고 구현 및 수치 검산을 마쳤다. R100 실측 요약의 공분산 경로를 평가했다. 고정 9개 평균을 같은 훈련 구간에서 추정하는 것과 원시 catalogue에 대한 새 독립 holdout을 만드는 것은 서로 다른 실험이다. R100 기원 five-field는 같은 radial shift를 모든 행에 부여하는 finite scenario다. 독립 3차원 velocity field, full-union calibration 및 selection/progenitor law, physical `Pi`와 `GF`는 미해결이다. 예측 chi-square의 감소와 log density의 감소는 동일 자료에서 공존한다. volume 항을 포함하면 이 범위에 대해 설명할 수 있다.

**R9 | 코드와 성능.** `htt.infer.cf4_predictive_response`가 fixed-design contrast, conditional Gaussian tangent 및 normalized selected mark API를 제공한다. `scripts.r101.cf4_predictive_response`가 실제 R100 입력을 읽는다. `--source-marks`는 두 원표 SHA, 15 arcsec/500 km s⁻¹ 교차매칭, 입력 행수, 기존 magnitude 고정 cut의 likelihood 재현 오차까지 확인하고 fitted match law를 같은 행에 적용한다. Gaussian 격자에서 covariance tangent의 matched-accuracy benchmark는 21개 α 지점에서 평균·공분산·q·ℓ 및 모든 1차 미분을 비교했다. 최대 절대 편차 $6.17\times10^{-9}$, 목표 $10^{-7}$. 단일 BLAS 스레드와 미리 계산한 고정 설계에서 직접 GLS 3회의 중앙값 126.2 µs, 해석식 중앙값 86.3 µs, 비율 1.46이었다. 환경·재현 명령은 아래에 있다. 36×36 압축 통계량에 대한 시간이다.

**R10 | 재현과 남은 문제.** 자료 생성/조정 없이 종전 CF4 R100 상태를 유지한다. source mark 실행의 분모는 알려진 6dFGSv 공개 표본에서 CF4 고유 매칭 여부이다. 독립 매칭 검증 표본, FP shape/원보정 covariance, full-union 대상·거절 모수, 중복 측정의 의존성을 확보해야 물리법칙 범위를 넓힐 수 있다. 전역 R78 노드 승격은 0이다. 재현 명령은 저장소 루트에서 다음과 같다.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m scripts.r101.cf4_predictive_response --source-marks --output /tmp/CF4_R101.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m scripts.r101.benchmark_cf4_response
python -m unittest discover -s htt/htt/tests -p test_cf4_predictive_response.py -v
```

코딩 루프의 C1–C4에서는 현재 R99/R100 함수의 부호·관측좌표·nuisance 경계를 파악하고 정확한 mark, 행 배열 및 공분산 입력으로 고정했다. C5–C7에서는 HTT 함수와 producer를 구현하고, 기존 양 끝점·독립 GLS·직접 적분·중앙차분·극한을 실행했다. C8의 속도 비교는 정확도 조건을 먼저 충족시켰다. C9–C10에서는 위 결과를 동일 R100 입력으로 재생산할 수 있게 남기고 source-qualification에 필요한 실제 모집단 입력을 특정했다.

**원표 재실행 | R7–R8.** 소유자 환경에서 같은 7,190개 6dFGSv mark로 계산한 조건부 혼합장 대 영장 log density 차이는 R100 예시 컷에서 −224.664087, 같은 행의 fitted match probit에서 −11.942159였다. 같은 fitted probit에서 나머지 1,695개 행의 관측된 음의 매칭 상태까지 조건으로 주고 그 mark를 소거하면 +27.341020으로 부호가 바뀐다. 단일 영장의 조건부 log density는 두 fitted 분석에서 −5727.256929로 같고 혼합장 값만 39.283180 이동한다. 단일 장에서는 음의 상태확률이 분자·분모에서 동일하게 소거되며, 혼합장에서는 장에 따라 재가중되기 때문이다. 8,885개의 상태만 관측할 때 −300, −100, 0, +100, +300 km/s 시나리오의 가중치는 각각 0.297447, 0.272115, 0.220215, 0.157459, 0.052764다. 여기에 7,190개 거리 mark가 들어가면 +100과 +300 km/s에 0.400791과 0.599209가 놓인다. 고정 컷 재현 오차는 2.01×10⁻¹¹ 이하, 전체 패턴의 template 배율 score −24.827022에 대한 중앙차분 오차는 1.12×10⁻⁶였다. 원표·교차매칭·동일 Gaussian scenario에 조건부인 결과다. 수치 표와 두 원표 식별자는 `CF4_RAW_SOURCE_RESULTS_KO.md`에 있다.
