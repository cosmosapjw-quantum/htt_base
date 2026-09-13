# SDSS–CF3 공개 입력 연결

`51ed1e913ac358f9a2569fce8ccb5dc3c1650305`에서 이어지는 입력 확보 작업이다.
HTT가 보정 추정과 공통 nuisance를, obsstat가 기존 깊이 feature를 소유한다.
공개 은하 대응과 보정 계산의 실행을 다루며 selected survey law, 물리적 local/global
반응, state–jet–anchor coverage는 계속 `UNAVAILABLE`이다. 새 alpha 소비는 0이다.

## 확보한 입력과 남은 입력

[SDSS PV v1.1.0](https://zenodo.org/records/6824749)의 34,059개 행에는
FP 변수·오차·Sn, Tempel 그룹 ID·richness와 개별/그룹 적색편이가 있다.
`logdist_corr`는 richness별 FP 적합값이며, release 설명은 이를 사용할 때 그룹 수준
영점 보정을 요구한다. 기본 `logdist`와 보정값을 서로 바꿔 사용하지 않는다.

[CF3 J/AJ/152/50](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/AJ/152/50)의
개별 은하 표를 확보했고, PGC로 296개의 공통 행을 찾았다.
[Tempel 2017 J/A+A/602/A100](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/A+A/602/A100)의
공개 584,449행 그룹 자료도 확보했다. SDSS objID로 33,641행이 연결되고 해당 행의
그룹 ID·richness는 모두 일치했다. 미연결 418행은 별도로 남겼다.
`tempel_sdss_join.json`과 `tempel_sdss_rows.npz`가 대응 결과다.
SDSS objID와 CF3 PGC는 서로 다른 식별자다.
일부 공통 은하에 그룹이 붙었다고 해서 CF3의 모든 보정 은하에 대한 대응표가 완성되지는 않는다.
그룹 ID 0인 은하들을 하나의 그룹으로 합치지 않는다.

| 단계 | 이번에 확보한 범위 | 전체 반복에 필요한 입력 |
|---|---|---|
| 선택 전 모집단 | 최종 선택된 SDSS 행과 발표된 선택 조건 | 원래 superset 행·SQL·Portsmouth 대응·결측 및 시각 분류 규칙 |
| FP 생성·적합 | 관측 FP 열, mock FP 참값·관측값·오차, 발표된 방법 | 선택 전 halo/subhalo와 할당, 생성·적합·제외 코드와 자료에서 맞추는 함수 |
| 창·redshift 선택 | 관측 in_mask와 random 제품 식별 | 수정된 mangle polygons, fitted spline 및 그 재추정 절차 |
| group-richness 보정 | 관측 그룹·richness와 최종 logdist_corr | 정확한 bin·그룹 대응·각 bin의 생성·적합을 같은 mock에서 반복하는 절차 |
| CF3 영점 | 공개 거리·tracer·PGC 중첩 | 공식 그룹 보정의 전체 대응·평균 규칙 및 공유 거리사다리·영점·cosmic-variance 법칙 |

[원 논문 Data Availability](https://arxiv.org/html/2201.03112)는 정확한 SDSS query와
추가 코드·자료를 저자 요청 대상으로 명시한다. 관련 공개 DESI FP 코드도 확인했지만
이를 원본 SDSS 생성기로 대체하지 않았다. 저자에게 연락하지 않았다.
세부 입력 상태는 다음 세션이 소비할 `input_inventory.json`에 남긴다.
random catalogue 다운로드는 공식 두 URL에서 HTTP 504로 실패했다. 이 파일은
확보되더라도 선택 전 은하 모집단이나 fitted spline 자체를 대신하지 못한다.

## 공유 영점과 전체 깊이 연결

입력 벡터를 `x=(eta_SDSS, eta_CF3)`, 같은 자료에서 계산한 영점을 `delta=lᵀx`,
기존 네 깊이의 36성분 추출을 `M`이라고 두면 보정 후 관측은 다음과 같다.

```
Y_cal = G x
G = [M, 0] + (M 1) lᵀ
Cov(Y_cal) = G C_joint Gᵀ
```

마지막 식은 해당 행 순서의 **전체 joint covariance가 주어진 경우**에만 계산할 수
있다. CF3와 SDSS의 교차 항 및 영점 추정에 다시 쓰인 SDSS 행의 자기 의존성을
포함한다. 공개 개별 거리분포 폭을 raw survey covariance의 대각 성분으로 간주하지
않으며, 없는 교차 항을 0으로 채우지 않는다. 보정은 전체 은하에 같은 offset을 더한다.
각 깊이의 monopole에 공통으로 들어가므로 H contrast에서는 소거되지만 초기 Y0에는
남는다. 초기 block을 포함한 T 변환을 계속 보존한다.

이 함수는 새로 공급된 완전한 실현마다 입력·가중·영점을 다시 계산할 수 있다.
현재 공개 mock에는 대응하는 CF3 자료와 Tempel 보정 그룹이 없어 그 전체 반복을
실행하지 못했다. 작은 합성 자료의 cross-term 검사는 이 대수적 연결만 검증한다.
공개 자료 실행의 가중 point estimate 역시 신뢰구간이나 관측법칙 적격성 판정이 아니다.

## 실행과 결과

CF3의 공개 tracer H/I 규칙으로 TF 2행(PGC 39712, 59838)을 제외하면 294행이
남는다. 전체 296행과 제외 mask를 모두 보존했다. 거리 변환은 CF3 luminosity
distance modulus와 SDSS 개별 zcmb, flat Ωm=0.31, H0=75 km/s/Mpc를 사용한다.
가중값 `1/(logdist_err²+(e_DM/5)²)`는 여기서 선택한 point estimator 규칙이다.
이 폭들로 covariance나 표준오차를 구성하지 않는다.

| 저장된 실행 결과 | 값 |
|---|---|
| 294행 진단 영점 | +0.00043862234757611747 dex |
| TF 제외 전 296행 진단 영점 | −0.0002351021362352942 dex |
| 공통 입력 → 깊이 연산자 G | 36 × 34,355 |
| 깊이별 관측 수 | 890 / 7,277 / 19,160 / 33,121 |
| 기존 깊이 실행의 Y와 새 projection의 최대 차이 | 4.440892098500626e−16 dex |

`final/result.json`과 `final/rows_and_coefficients.npz`를 수치 원본으로 사용한다.
논문의 개별 영점 −0.0028 dex와 일치한다고 주장하지 않는다. 위 표는 공개 입력과
명시된 거리·가중 규칙의 실행이며, 원저자의 변환·가중 코드 재현은 미확인이다.
특히 공식 292개 그룹 영점 −0.0037 dex를 이 개별 은하 결과로 대체하지 않는다.

원본 CF3 파일은 `acquired_inputs.json`의 공개 URL과 SHA256으로 고정했다.
아래 출력 경로는 존재하지 않아야 한다.

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 scripts/observed_runs/run_sdss_cf3_calibration.py \
  --data /mnt/sn850x2t/htt_base_e2e/workdir/raw/sdss_pv_zenodo_6824749/SDSS_PV_public.dat \
  --cf3 /home/cosmosapjw/.cache/htt-r9/cf3_tempel_2017/CF3_table3.dat \
  --cf3-sha256 8acd4718ffe370e58d9747ffa3d8aeafcf3f554c698c82c00f29f5dec270aa19 \
  --output /tmp/r9-cf3-new
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/r9 htt/src/common/test_r9_depth_path.py htt/src/common/test_r9_tensor_functionals.py
```

초기 통합 검증은 관련 테스트 35개가 통과했다. 테스트는 교차 covariance의 독립
스칼라 분산 계산, 동일 실현에서 영점을 다시 추정했을 때의 의존성, 초기값 보존,
기존 R7 PSD 경계와 독립 적분기를 통한 거리 계산 비교를 포함한다.

## 물리 연결과 보존 상태

여기서의 eta와 angular coefficient는 dex 단위다. local boost/global tilt의
운동학적 응답은 기준계·거리 정의·시간/깊이 kernel·선택과 nuisance를 포함해 별도로
주어져야 한다. 기존 additive eta shell 응답을 물리 응답으로 간주하지 않는다.
물리적 신뢰집합 사상에는 동일한 calibrated state–jet–anchor 사건이 필요하다.

기존 DESI 조건부 scalar 실행과 SDSS 2,048-mock 실행은 재실행하지 않았다.
R8 STOP_INVALID, 25 unresolved pools, CF4 quarantine, PR4 skip,
production/empirical/novelty/four-axis HOLD와 모든 기존 오차 예산을 유지한다.
Fibre의 동일 ambient-STF 방향 비교는 이번 작업 범위에 포함하지 않는다.
