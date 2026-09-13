# SDSS PV 실제 다중 깊이 실행 — 관측법칙 수용은 보류

기준 커밋은 `c532862651235ed0586a0677b61a43b2e09b3c85`다. 이 작업은
기존 R9 adapter에 실제 SDSS PV 행과 동일 카탈로그 단위의 mock 벡터를 연결한다.
소유자는 obsstat이며, 결과는 관측 feature 진단이다. HTT likelihood, MIO 확률,
local/global 물리 구별 또는 state–jet–anchor 신뢰영역을 생성하지 않는다.

## 입력과 실행 범위

새로 확보한 제품은 [Howlett et al.의 공개 v1.1.0](https://zenodo.org/records/6824749)이다.
기존 CF4 quarantine 결과를 재사용하거나 CF4와 독립인 추가 검정으로 취급하지 않는다.
관측 파일의 공개 MD5는 `b5b6e31caf7ea469c2ac2cb775fa8d14`, 전체 mock archive의
공개 MD5는 `9ba3e8876f6f08a2af00d30cbf1c6cd9`다. runner는 두 값을 확인하고
새 출력에 SHA256을 기록한다. 대용량 원본은 Git 외부에 둔다.

[원 논문](https://arxiv.org/html/2201.03112)의 §2.5/3.2.1은 관측의 `in_mask`
표시와 mock의 동일 DR7 창을 설명한다. §5.3/5.4 및 release 설명에 따르면
권장 관측값 `logdist_corr`는 group-richness별 FP 적합과 외부 영점 보정이 필요하다.
공개 mock에는 그 보정의 대응 열·Tempel group-richness·CF3 calibration 반복이 없다.
따라서 양쪽에 있는 기본 `logdist`를 진단에만 사용하며, 권장값의 차이는 별도 control로
저장한다. §3.1–3.2의 자료에 맞춘 생성기·오차·선택함수도 여기서 재추정하지 않는다.

`analysis.json`은 실행기가 읽는 고정 설정이다. 네 누적 창은
`0.0033 < z_CMB < (0.025, 0.05, 0.075, 0.1)`이며 자료의 `in_mask=1`을 사용한다.
관측 `zcmb`와 mock `z_obs`를 사용하고, group redshift로 조용히 교체하지 않는다.
발표된 적경·적위에서 단위벡터 n을 만들고 다음 9개 열을 단위 가중으로 적합한다:

```
1, nx, ny, nz, nx²−nz², ny²−nz², 2nxny, 2nxnz, 2nynz
```

계수 단위는 모두 log10 거리비의 dex다. 이는 log-distance의 각도별 feature이며
velocity, 물리적 shear 또는 radiation Q/O가 아니다. 각 창의 실제 SVD와 행 수를
보존한다. 공개 mock ID가 반복되므로 원 ID와 파일 내 행 번호를 함께 보존하고,
중복 ID를 이유로 위성/관측 행을 삭제하지 않는다. 최초 reader 실패와 수정 확인은
`reader_initial_failure.json`, `reader_repair_smoke.json`에 남긴다.

## 평균·반응·전체 covariance

동일한 전체 mock 카탈로그에서 네 깊이의 36성분 Y를 함께 얻는다. 짝수 simulation
box는 학습, 홀수 box는 평가에 사용하며 한 box의 8개 observer를 분리하지 않는다.
이 분할은 공통 box의 누출을 피하지만 iid나 원시 survey coverage를 입증하지 않는다.

학습 벡터에서 평균과 전체 sample C를 계산한다. 평가 자료로 평균·C를 다시 맞추지
않고, 평가 residual을 저장한다. fitted-minus-truth의 평균/C는 total mock variation과
별도로 저장한다. 이는 개별 은하의 원시 C_ik를 복원한 것이 아니다.

응답 R은 redshift shell마다 독립인 9개 **additive eta angular field**에 대한 실제
창 반응이다. 각 mock에서도 추출·R을 다시 계산한다. 물리적 local boost/global tilt
응답은 여전히 unavailable이다. 공통 additive eta 영점은 모든 shell monopole과
정확히 퇴화하며, `SharedStateEmbedding`에 자유 nuisance로 남는다.

기존 `DepthRepresentation`의 K=I를 써서 r=HY, V=HCHᵀ와 (Y0,r)의 전체 평균,
covariance, 응답을 저장한다. off-diagonal Cjk를 버렸을 때의 V 변화와 직접 변환한
mock sample covariance와의 일치도를 함께 기록한다. Gaussian 법칙을 호출하지 않으며,
최종 `ProductIntake.law_kind`는 `ESTIMATED_REQUIRES_CALIBRATION`이다.

## 재실행

출력 디렉터리는 존재하지 않는 새 경로여야 한다. 원본 전체 archive 검증 후
전체 member를 순차 처리하며 압축을 모두 풀어 저장하지 않는다.

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 scripts/observed_runs/run_sdss_pv_depth.py \
  --data /mnt/sn850x2t/htt_base_e2e/workdir/raw/sdss_pv_zenodo_6824749/SDSS_PV_public.dat \
  --mocks /home/cosmosapjw/.cache/htt-r9/sdss_pv_zenodo_6824749/mocks.tar.gz \
  --analysis docs/research_program/tensor_joint_r9/revision2/multidepth/analysis.json \
  --output /tmp/r9-sdss-new
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/r9/test_sdss_pv_depth.py
```

## 아직 필요한 입력

원시 관측법칙을 완성하려면 선택 전 parent population 및 선택/오차/FP 생성·적합
절차, group-richness 보정의 동일 반복, 실제 CF3 group-level calibration과 공유
nuisance 법칙이 필요하다. 추정된 단계들을 같은 전체 모의자료에서 반복하고
해당 관측 target의 크기·coverage·power를 기존 제품 예산 안에서 검증해야 한다.
물리 image에는 같은 calibrated state–jet–anchor 사건이 별도로 필요하다.

새 확률·신뢰구간·p-value는 없고 alpha 소비는 0이다. Family 1/20, 제품별 1/80,
CMB 내부 1/160을 유지한다. R8 STOP_INVALID, 25 unresolved pools, CF4 quarantine,
PR4 skip, production/empirical/novelty/four-axis HOLD와 Fibre의 ambient-STF 방향
고정 의무도 유지한다. 이 실행만으로 R9-25/26/27 capability를 수용하지 않는다.


## 최종 실제 실행 결과

`final_execution.json`의 전체 실행은 exit 0, 약 358초이며 `final.stderr`는 비어 있다.
공식 archive 10,643,218,721바이트의 MD5가 일치했고 SHA256은
`eaac95f323e6dcb6c3626122793d734790f8b27cb0b231f31e60cdd6255b0536`이다.

| 항목 | 결과 |
|---|---|
| 전체 mock / simulation box | 2,048 / 256; 누락·실패 0 |
| 학습 / 평가 | 각 1,024 mock, 각 128 box |
| 관측 깊이별 행 수 | 890 / 7,277 / 19,160 / 33,121 |
| 전체 Y covariance | 36×36, 수치 rank 36 |
| 공통 state 응답 | 36×37, rank 36; 영점 퇴화 유지 |
| C의 교차 깊이 block Frobenius norm | 0.04472349635816802 dex² |
| 교차 항을 지웠을 때 V 변화의 Frobenius norm | 0.07089266648282475 dex² |
| 직접 변환한 mock covariance와 TCTᵀ의 최대 차이 | 2.7755575615628914e-17 dex² |
| 초기 block을 포함한 관측 복원 최대 오차 | 1.474514954580286e-17 dex |

수치 원본은 [final/result.json](final/result.json), 전체 벡터와 각 mock의 응답은
`final/mock_features.npz`, 평균·전체 covariance 및 변환은 `final/moments.npz`다.
`final/mock_members.json`은 모든 member와 원본 행 수·ID 수·hash를 보존한다.
`final/provenance.json`의 실제 실행 source/config hash와 현재 source가 일치한다.
독립 검수의 초기 결과와 수정 검수는 아래 run의 별도 result로 보존한다:
`.agent-harness/runs/R9-MULTIDEPTH-20260913/results/`.

이 표는 고정된 추출 절차의 실행 및 수치 변환 결과다. 관측 residual의 유의도나
preferred FP correction의 물리 효과를 정량화하지 않는다. 북쪽 angular window에서
얻은 monopole/dipole 계수도 전천 bulk velocity의 측정치로 해석하지 않는다.


독립 검수의 수정 closeout은 PASS다. 저장된 전체 벡터에서 학습 mean/C,
HCHᵀ/TCTᵀ, 평균·응답·평가 residual, fitted-minus-truth moments를 독립 재계산했고
box 분할과 source/intake binding도 확인했다. `PR_DELTA.md`가 root의 범위 한정
판정이다. 초기 검수의 FAIL과 그 source snapshot은 보존한다. 초기 input seal은
수정 전 소스를 가리키므로 현재 run 전체의 aggregate PASS를 주장하지 않는다.
