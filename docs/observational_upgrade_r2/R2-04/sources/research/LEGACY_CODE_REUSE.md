# Legacy HTT code reuse — R2

작업 전제는 사용자가 지정한 **모든 관련 증명이 성립한다는 조건부 설계**다. 이 문서는 그 전제를 다시 심사하는 보고서가 아니라, 첨부 코드에서 직접 재사용할 함수·재결합할 입출력·작동한 실행을 구분한다. 옛 계산값과 현재 관측 likelihood의 적격성은 이 전제로 새롭게 입증되는 것이 아니다.

## 확인한 원본과 실행

`sources/HTT/HTT`에는 실제 111개 파일이 있다: Python package 12개, data JSON 6개, outputs JSON 7개, figure 65개(43 PDF + 22 script), tests 6개, docs 8개와 최상위 문서다. 파일별 SHA-256과 AST상 함수/클래스 이름은 `LEGACY_CODE_REUSE.json`에 기록했다. `README.md`의 237 passed, ln B=26.4, Q=0.090 등의 수치는 **과거 아카이브 주장/결과**이며 이번 실행의 결과가 아니다.

9개 안전한 라이브러리 모듈을 `PYTHONPATH=<legacy>/htt`로 실제 import했다. 모두 import 성공. 일반 package 방식의 `import htt.bounds`는 `ModuleNotFoundError: ssot`로 실패했다. `pipeline.py`는 import 시 argparse·계산·출력 쓰기를 실행하고 `h0_sensitivity.py`는 최상위 report script이므로 import하지 않았다. 별도 adapter는 package 경로를 오염시키거나 source를 고치지 않고 실제 `bounds.py`와 `ssot.py` bytes를 로드한다. 7개 신규 의미론/경계/출처 검사 exit 0; 로그는 `evidence/LEGACY_ADAPTER_TEST.log`다. Full pipeline·nested sampling·새 관측 적합은 실행하지 않았다.

## 실제 재사용 지도

| 원본 구현 | 보존하고 사용할 부분 | 관측 분석 업그레이드의 연결점 |
|---|---|---|
| `bounds.py`: `B_sigma`, `B_omega`, `B_accel`, `B_sigma_corrected`, `x_defect` | 명시적인 ε와 표준화된 invariant를 받는 순수 대수 함수 | 새 CMB response/STF 추정 또는 posterior draw마다 실행. 이번 adapter가 직접 호출한다. |
| `departure_posteriors.py`: `DeparturePosterior`, weighted summaries | x→Q→Π 구조와 보고 형식, 비교 기준별 pushforward | 새 selected latent-law의 joint posterior를 입력. missing column→0 경로는 사용하지 않고 아래 partial pushforward로 연결. |
| `evidence_models.py`: 16 model classes, `predicted_observables`, `MODEL_AUDIT` | 모델 등록부·active parameter·기존 analytic template·transfer calibration | 현재 repo의 full response provider와 공유. 옛 summary likelihood는 역사적 reproduction mode로 남긴다. |
| `catalog_likelihood.py`: `DistanceEngine`, mock, spherical direction summaries | fixed flat-FLRW baseline distance, unit conversion, synthetic test fixture, credible-cone 보고 | `r7_cf4_law.SelectedLatentBlock`의 forward primitive로 분해. redshift/selection/calibration·그룹 공분산은 현재 repo likelihood가 소유. |
| `teff_extended.py`: `TeffMomentMap`, `EllMixingMatrix`, `NonlinearCorrection` | 순간 연산과 축대칭 boost의 저비용 regression oracle | 현재 full harmonic/window response의 제한된 m=0·작은 boost 극한을 검사. 전체 map likelihood 대체물로 쓰지 않는다. |
| `analysis_extended.py`: scenario/forecast/filling classes | 옛 S0–S3 대조군·시각화·민감도 실험 설계 | hardcoded data draw 대신 새 posterior draw를 주입. 같은 likelihood에서 나온 요약을 새 독립 채널로 곱하지 않는다. |
| `tilted_flrw.py` | homogeneous/perturbative depth 비교, 명시적인 가정 아래 derived observable 함수 | 거리·frame·rapidity convention을 계약에 고정한 후 posterior-predictive output으로 재사용. |
| figure scripts + PDF + 7 output JSON | 축·관측량·분해 순서·역사적 비교 | 새 결과에 동일 figure grammar 적용. 옛 plot을 현 자료의 결과로 재표시하지 않는다. |

## 이번에 구현한 작은 연결부

`code/legacy_adapter.py`는 세 가지 기능을 제공한다.

1. `multipole_rms`는 `C_ell` 또는 `D_ell=ell(ell+1)C_ell/(2π)`와 `K2/uK2`, `T0_K`를 필수로 받는다. 
   \[
   \epsilon_\ell=\frac1{T_0}\sqrt{\frac{(2\ell+1)C_\ell}{4\pi}}.
   \]
   이는 harmonic RMS convention이다. PSTF norm은 별도 증명된 adapter를 통해야 한다. 원본 `ssot.eps_ell`는 입력 이름은 D_ell인데 내부 식은 C_ell에 해당하므로 그대로 호출하지 않는다. 이 수정은 관측 product 의미를 보존하기 위한 입출력 교정이다.
2. `LegacyAdapter.bounds_from_epsilon`는 세 ε를 모두 명시해 원본 함수를 호출한다. `frame_correction`도 명시한다. 결과의 `Sigma2_shear_ceiling`을 전체 signed x의 ceiling으로 자동 재명명하지 않는다. x에는 curvature/tilt/negative vorticity가 있으므로 해당 전제를 만족하는 별도 `x_ceiling`을 제공해야 한다.
3. `departure_pushforward`는 필수 성분 `Sigma2,W2,Omega_tilt,curvature_delta`와 양의 ceiling, 측도 가중치, identifiability mask를 받아 x의 부호와 미관측 질량을 보존한다. `congruence, comparator_id, proof_scope_id, measure_id`가 빈 값이면 계약을 거부한다.

정규화된 입력 가중치를 p_i, Q가 정의되고 식별되는 표본 집합을 K라 하자. 다음 경계는 입력 측도와 미지 event의 가능한 completion에 대한 보수적 outer bound다. 미지 event에 아무 추가 제약도 없는 completion 모형에서는 sharp하다.
\[
 L(q)=\sum_{i\in K}p_i\mathbf1_{Q_i>q},\qquad
 U(q)=L(q)+\sum_{i\notin K}p_i.
\]
미지 부분의 threshold event를 독립적으로 거짓/참으로 완성할 수 있을 때 두 끝점이 달성된다. 이미 알려진 x의 부호나 positive ceiling support가 completion을 제한하면 이 구간은 더 좁아질 수 있다. 실제로 quotient가 미정의인 mass에는 completion 가정과 정의역 조건부 결과를 별도로 기록한다. strict event이므로 Q_i=q인 알려진 질량은 별도로 보고한다. 입력이 posterior면 posterior probability 구간이며, 이 식만으로 모집단의 빈도 또는 frequentist coverage가 되지 않는다.

테스트 예는 p=(0.2,0.3,0.5), x=(-0.4,0.2,undefined), ceiling=1이다. Π(Q>0)∈[0.3,0.8], Π(Q>0.2)∈[0,0.5], q=0.2의 알려진 boundary mass=0.3이다. 이 예는 합성 검산이며 실제 관측 결론이 아니다. 부호가 음수인 x를 강제로 0으로 만들지 않았고, 미지 0.5를 버리고 나머지를 재정규화하지 않았다.

## 재사용하면서 유지할 해석 계약

- 원본 `DeparturePosterior`가 없는 `W2`, `Sigma2`, curvature column을 0으로 대체하는 것은 특정 모델이 그 값을 **구조적으로** 고정할 때만 허용한다. 관측 불가능과 물리적 0은 다르다. 이번 adapter에는 default-zero 인수가 없다.
- 원본 beta는 모듈마다 뜻이 다르다. `departure_posteriors`는 v=c tanh(beta)의 rapidity를 쓰고, `EllMixingMatrix`는 γ=(1−beta²)^−1/2의 speed fraction을 쓴다. 새 provider 필드는 `rapidity`와 `speed_over_c`로 나누어 변환한다.
- `CatalogLikelihood`의 `1+beta cosθ`는 1차 boost 모델이다. exact라는 주석에 의존하지 말고 현재 repo exact observer/source response로 교체한다. fixed-z error 모델의 유용한 regression case는 남긴다.
- `EinsteinTeffODE.rhs`에는 `include_teff` flag와 달리 실제 T_eff source가 없다. 작은 linear decay fixture로 남기고 새 비선형 동역학에 이름만으로 연결하지 않는다.
- `analysis_extended.EvidenceComparison`의 lazy import 이름 `evidence_models_R03a`는 첨부 파일 이름 `evidence_models.py`와 맞지 않는다. full runner를 바로 호출하는 대신 함수를 현재 package layout에 명시적으로 이식한다.
- legacy `ssot.py`는 자기 옆 `obs_defaults.json`을 찾지만 실제 파일은 `data/`에 있다. 이번 adapter는 관측 관련 기본값을 사용하지 않아 이 문제를 우회했다. 새 runtime importer는 파일 identity와 data path를 인수로 받는 편이 맞다.

## 기존 모델들을 보존하며 sampler 비용을 줄이는 경로

`MODEL_AUDIT`는 16 labels 중 orth_1D 6개와 tilt_flat 3개의 동일 summary response를 이미 표시한다. likelihood가 active response s(θ)에만 의존하고 각 모델 prior의 pushforward ν=s_*π가 같으면
\[
Z=\int L(s(\theta))\,\pi(d\theta)=\int L(u)\,\nu(du)
\]
이므로 같은 클래스의 Z와 active posterior는 한 번만 계산할 수 있다. 해당 전제가 충족되는 현재 summary model이면 16개 sampler를 최대 9개 대표로 줄이고, 모델별 derived parameter는 조건부 prior로 재구성한다. 이것은 실행시간 측정이 아니라 등가분류에 따른 계산 제거다. 새 full harmonic response 또는 다른 active-prior가 클래스를 분리하면 바로 분할한다. 옛 label을 없애거나 서로 다른 prior의 evidence를 복사하지 않는다.

실제 class 구현을 읽으면 위 두 그룹의 active `_logu` prior가 각각 동일하고 inactive prior가 분리되어 있음을 확인할 수 있다. 세 active prior 위치와 두 inactive 위치를 사용한 총 54개 경량 check에서 active-prior 값과 log likelihood가 모두 일치했다(`evidence/LEGACY_EQUIVALENCE_CHECK.json`). 이는 이 source 구현의 제한된 실행 검산이며 일반 모델에 대한 새 형식증명을 뜻하지 않는다.

## 현재 repo에 연결할 최소 작업

2026-10-13 조회된 `d53c9ddd` 기준 현재 repo는 `r7_cf4_law` selected latent law, `r7_cmb_product_response` full response, `planck_lowell_irrep_projection` STF mapping, `r9_depth_law` joint covariance, `r7_joint_experiment` overlap 소유권을 이미 제공한다. 따라서 새 likelihood를 하나 더 만드는 대신:

1. 이 law들의 posterior 또는 식별집합을 sample contract로 export한다.
2. fixed congruence/comparator에서 증명된 invariant mapping을 적용한다.
3. 이번 adapter로 x, 적용 가능한 Q, Π interval을 계산한다.
4. old scenario/ablation/figure skeleton을 새 likelihood 표본으로 다시 채운다.
5. 동일 CF4 원자료에서 나온 bulk flow·Hubble-depth·defect 요약을 추가 독립 likelihood로 곱하지 않는다.

실행:
```bash
python -m unittest discover -s HTT_OBSERVATIONAL_UPGRADE_R2_20261013/code -p test_legacy_adapter.py -v
```

근거 상태: legacy source inspection=직접 확인; 신규 adapter=implementation-verified; partial probability 경계와 equivalence compression=derived under stated assumptions; 모든 증명의 실제 완료 상태=이번 요청의 조건부 가정; 새 scientific observation inference=NOT_RUN.
