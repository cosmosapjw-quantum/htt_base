# 실제 관측 분석 계속하기

현재 목표는 CF4·CMB·DESI의 실제 분석, 하나의 공동 posterior, 같은 표본에 대한 legacy 관측량, scientific plot·보고서까지 연결하는 것이다. 먼저 바로 실행할 수 있는 공개 요약량과 기술통계 그림을 완성하고, 이어서 실제 물리 적합에 필요한 관측법칙을 구현한다. DESI 한 그림이나 준비 문서 작성으로 전체 목표를 종료하지 않는다.

기존 체크아웃 `/home/cosmosapjw/Dropbox/bianchi/htt_base`에서 진행한다. 검토 기준은 감사 PR #530의 `6365e36d0ccc6acddb7f6909aacea8d766c0fc4a`, tree `02976f294a26854daee6116d34e71af0a8bce232`다. 이는 로컬 잔여 파일의 보존 스냅샷이다. 다른 열린 PR 99개를 합친 상태가 아니며, 기존 `HOLD/UNKNOWN`과 과학적 승인 상태를 변경하지 않는다. 이 인계가 게시된 후속 브랜치와 커밋은 해당 PR의 실제 head를 따른다. 현재 checkout이 더 앞서 있으면 변경분을 보존하고 읽는다.

## 시작할 파일과 즉시 실행

`AGENTS.md`, `NEXT_TASK.json`, `ANALYSIS_PLAN.json`의 현재 작업만 읽는다. 상위 증명이 모두 유효하다는 사용자의 조건부 전제는 방법 재사용에 적용하고, 실제 증명/과학 승인 기록을 소급 변경하지 않는다. 전체 증명 corpus나 679 MB 감사 스냅샷을 LLM context에 넣지 않는다.

먼저 현재 branch·HEAD·작업 상태와 이미 게시된 실행 결과를 확인한다. 완결된 같은 입력·방법 결과가 있으면 재사용한다. 새 실행이 필요한 경우에만 아래 새 출력 경로를 사용한다.

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
git status --short
git branch --show-current
git rev-parse HEAD
export PYTHONPATH=htt:htt/htt:htt/src
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
OBS_RUN_ROOT="docs/generated/observational_analysis_$(date -u +%Y%m%dT%H%M%SZ)"
/home/cosmosapjw/venv/bin/python -B scripts/prepare_observational_analysis.py --output-dir "$OBS_RUN_ROOT"
```

`readiness.json`은 이 턴의 모듈 import와 경로/크기를 기록한다. 관측법칙의 적격성 판정은 아니다. 예전 runtime 오류를 계승하지 않는다. `desi_cf4`와 `cmb` 환경을 따로 판단한다. 현재 경량 경로에는 `/home/cosmosapjw/venv/bin/python`과 `/usr/bin/python`을 쓰며 불필요한 설치는 하지 않는다.

준비 스크립트의 기본 자동 실행 대상은 DESI 한 개다. CF4/CMB의 수용된 수치 결과는 재사용한다. 다음 스크립트가 생성한 command와 현재 준비 결과를 확인한 뒤 실행한다.

```bash
bash "$OBS_RUN_ROOT/run_ready_diagnostics.sh"
/home/cosmosapjw/venv/bin/python -B scripts/build_observational_diagnostic_report.py \
  --desi-result "$OBS_RUN_ROOT/runs/desi/analysis.json" \
  --cf4-result docs/observational_upgrade_r2/R2-02/raw/diagnostic.json \
  --cmb-result docs/observational_upgrade_r2/R2-03/raw/diagnostic.json \
  --output-dir "$OBS_RUN_ROOT/runs/report"
```

DESI 실행만 따로 필요하면 다음 명령을 사용한다. 출력 폴더가 이미 있으면 덮어쓰지 않는다.

```bash
/home/cosmosapjw/venv/bin/python -B scripts/analyze_desi_bao_summary.py \
  --input workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5 \
  --output-dir "$OBS_RUN_ROOT/runs/desi"
```

생성물은 DESI `analysis.json`, `likelihood_curve.csv`, PNG/PDF, 통합 `report.md`, `report.json`, `figure_data.json`, CF4 coverage/sensitivity 및 CMB same-sky PNG/PDF다. Markdown와 독립적인 figure PDF를 제공하는 경로이며, 이 단계가 전체 물리 논문 PDF의 컴파일을 뜻하지 않는다. 보고서 그림의 값·축·단위·caption을 실제 파일로 검토한다.

입력이나 방법이 바뀌어 CF4/CMB 재계산이 필요한 경우에만 아래를 사용한다. CF4 runner에는 별도의 합성 injection 검사가 포함되어 있으며 그 부분을 실제 적합으로 보고하지 않는다. CMB runner는 현재 reduced controls뿐 아니라 세 원본 FITS header를 읽는다. 다중 GB 전체 해시는 기본 요구가 아니다.

```bash
/home/cosmosapjw/venv/bin/python -B scripts/r2_cf4_product_diagnostic.py \
  --source workdir/raw/cf4_full --output "$OBS_RUN_ROOT/runs/cf4.json"
/usr/bin/python -B scripts/r2_cmb_product_diagnostic.py \
  --controls docs/generated/tensor_joint_r8/owned_controls/cmb/cmb_controls.npz \
  --metadata docs/generated/tensor_joint_r8/owned_controls/cmb/cmb.json \
  --output "$OBS_RUN_ROOT/runs/cmb.json"
```

현재 CMB CLI는 `/mnt/extdrive/workdir/raw/planck_data`를 사용하므로 다른 환경에서는 reduced callable을 재사용하거나 header base를 작은 변경으로 매개변수화한다. 이 경로 문제를 CMB 이론 실패로 분류하지 않는다. R2-04 그림 runner는 과거 reviewed 출력을 덮어쓰므로 그대로 재실행하지 않는다.

## 실제 물리 적합으로 이어지는 순서

`ANALYSIS_PLAN.json`은 OA00–OA11의 12개 소비 가능한 작업만 둔다. OA01·02·03은 독립이고 OA04에서 현재 자료 보고서로 합쳐진다. OA05·06·07의 실제 모델 작업도 병렬 조사 가능하다. OA08에서 공동 law, OA09에서 공동 적합, OA10에서 legacy posterior image, OA11에서 최종 과학 보고서로 이어진다. 외부 native solver는 그 응답/atlas가 필요한 물리 주장에만 선행한다.

| 작업 | 반드시 만드는 과학적 진전 | 기존 구현과 핵심 남은 일 |
|---|---|---|
| OA05 CF4 | 실제 DMzp,Vh에 대한 선택된 관측법칙과 적합 | `cf4_product_provider.py`, `cf4_likelihood.py`, structured inference를 재사용. 공개된 선택/보정 정보를 찾아 지원되는 grouped subset 또는 전체 법칙을 확정하고 latent distance·속도오차·공유 보정·절대척도·유한거리 remainder를 넣는다. |
| OA06 CMB | 실제 저다중극 관측법칙과 적합 | `r7_cmb_product_response.py`, `r2_cmb_product_bridge.py` 재사용. 응답·잡음/전경·마스크 covariance를 적격 simulation/split/product 정보로 연결한다. 네 복원지도 차이를 독립 잡음 표본으로 쓰지 않는다. |
| OA07 DESI | 선택한 물리 변수의 qiso 예측과 적합 | 공개 Gaussian law에 `theta → (DV/rd)/(DV/rd)_fid`를 연결하고 rd와 fiducial/reconstruction 가정을 명시한다. 비등방 응답은 실제 window/추정량에 맞춰 유도한다. |
| OA08 공동 law | 한 번의 shared-latent 적분 | `r7_joint_experiment.py`의 typed composition 재사용. CF4 calibration·observer motion·CMB shared sky 등을 한 번만 넣고 중복 measurement를 제거한다. |
| OA09 공동 적합 | 실제 하나의 posterior와 물리/수치 불확실성 | 먼저 작은 모형을 실행하고 수렴·prior/선택/remainder sensitivity를 평가한다. 실제 profile 뒤에만 장시간 병렬 계산을 선택한다. |
| OA10 legacy | 같은 draw ID/weight의 x,Q,Pi,MES,depth 및 가능한 F4 | legacy 식·source·레이아웃을 최대한 재사용하되 현재 sampling 전용 인터페이스에서 posterior 전용 인터페이스로 정당하게 확장한다. |
| OA11 보고서 | 재현 가능한 scientific result와 논문용 그림 | 실제 joint/legacy 출력에서 표·그림·문장을 생성하고 보고서 소스와 PDF를 컴파일한다. scope에 맞는 한 번의 독립 검토 후 구체적 오류만 수정한다. |

OA05에서는 Table 3의 method presence가 `DMzp`의 혼합 계수라는 가정을 두지 않는다. 필요한 경우 실제로 지원되는 method/subset을 먼저 택한다. Table 4의 `DMzp,e_DMzp,Vh,RAdeg,DEdeg,1PGC`가 원 관측이며, `Dist/Vpec`는 추가 독립 자료가 아니다. 방사방향은 J2000 equatorial sourceward, Vh는 heliocentric이다. `affine9`, `weak12`, `endpoint13` 비교는 같은 선택/오차/보정 법칙에서 한다. 한 데이터의 depth contrast를 새 factor로 넣지 않는다. 관측만으로 결정되지 않는 절대척도·회전·tilt·curvature를 0으로 채우지 않는다.

OA06에서 현재 출력은 NSIDE64·공통 마스크·동시 ell0–5 적합 후 ell2–5를 유지한 제품 차분이다. 물리 dipole·angular-mean T0를 복원한 full-field 온도 통계와 다르다. 유한 dipole+quadrupole ansatz의 정확한 F4와 실제 전천 F4도 구분한다. 후자는 생략 모드 제어가 필요하다.

OA08의 현재 코드에는 실제 구현 작업이 남아 있다. `SelectedJointDensityProvider.build`는 fixed-count 입력만 받지만 DESI law는 `PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE`를 선언한다. 이 문자열을 몰래 바꾸지 말고 원 conditioning과 Gaussian 근사를 보존하는 혼합 관측형 adapter 또는 합성 경로를 구현한다. 연속 prior의 quadrature에는 주장한 양에 맞는 적분 오차 제어가 필요하다. finite prior 합산이 정확하다는 결과로 연속 evidence 정확성을 주장하지 않는다.

OA10의 `htt/htt/htt/infer/conditional_legacy_pushforward.py:conditional_legacy_image`는 현재 `SAMPLING` 또는 `FINITE_SET`만 허용한다. 실제 posterior를 단순히 전달하는 것은 지원되지 않는다. 별도 HTT posterior adapter 또는 근거를 가진 확장으로 source-bound 실제 posterior의 draw ID/원 weight를 보존해야 한다. `x = Sigma2 - W2 + Omega_tilt + curvature_delta`의 물리 sector, samplewise denominator, congruence·단위·comparator를 확인하고 미정 질량을 버리지 않는다. strict event `Q > threshold`의 경계질량을 보존한다. depth 공분산에는 cross term이 필요하다. F4·filling fraction·물리 H(d)/q(d)는 해당 입력을 모델이 제공하는 경우에만 계산한다.

## 누락된 R1 branch의 재사용

#530에서 `docs/observational_methods_20261013/OBS-03,04,05,07` 및 네 entrypoint는 실제로 부재함을 재확인했다. 로컬 sibling branch tree에는 남아 있다. 아래 reviewed commit의 필요한 파일만 `git show <sha>:<path>`로 읽고 현재 코드와 대조한다. 99개 PR 전체를 무차별 merge하거나 기존 수정 위에 오래된 candidate patch를 적용하지 않는다.

| 작업 | 검토 대상 commit | 소비할 runner |
|---|---|---|
| OBS-03 | `5f3fbbee1d48d348bdf889fe2e27abdcb05073f4` | `scripts/cf4_latent_modulus_validation.py` |
| OBS-04 | `85a0c9d7cc6ae98d2dad3ba8ba3c35649ded4e65` | `scripts/obs04_cmb_common_response.py` |
| OBS-05 | `6216d8c0e8a84b57a5dfdfecb9f3fd56fa240d68` | `scripts/obs05_desi_bgs_summary.py` |
| OBS-07 | `f8bc9733ded48f49788374f5626b537bcfb5a262` | `scripts/obs07_remainder_sensitivity.py` |

OBS-05의 26-vector BGS fullshape 자료와 이번 scalar reconstructed BAO H5는 서로 다른 제품이다. 서로 대신 쓰거나 독립 likelihood로 곱하지 않는다. 이 누락이 현재 R2·DESI 실행을 막지는 않는다.

## 검증·작업 분담·반환

한 production writer와 서로 다른 일을 맡은 native subagent를 쓴다. 한 명은 CF4 실자료 관측법칙, 한 명은 CMB product law, 한 명은 DESI physical response를 조사할 수 있다. 각 packet에는 원래 질문, 현재 task ID, 실제 source/function, 허용 수정 파일, 산출물, 단위·관측 convention·수용 기준만 넣는다. 전체 이력 복사, recursive reviewer, 새 governance registry는 필요 없다.

이미 수용한 수학 증명·R1/R2 검증은 반복하지 않는다. 변경한 통계 경로의 검증만 실행한다. 실제로 해당 경로를 수정했을 때 사용할 기존 테스트는 다음과 같다.

```bash
/home/cosmosapjw/venv/bin/python -B -m pytest -q tests/htt/test_cf4_product_provider.py tests/htt/test_cf4_likelihood.py
/usr/bin/python -B -m pytest -q tests/htt/test_r2_cmb_product_bridge.py tests/r7/test_cmb_product_response.py
/usr/bin/python -B -m pytest -q tests/r7/test_selected_joint_density.py tests/r7/test_joint_experiment.py
```

신규 실행/보고서 경로의 테스트는 PR card의 정확한 test 명령을 따른다. 새 과학 모형에는 같은 선택·보정·오차를 쓰는 작은 injection과 실제 적합의 수렴/민감도 검사를 붙인다. 코드 통과, 모형 타당성, 관측 결과, 게시 성공은 다른 상태다.

완료한 의미 있는 increment마다 기존 canonical DAG/status와 PR delta를 갱신하고 이미 승인된 범위에서 commit/push한다. 게시 후 remote ref/commit을 확인하고 정상 R1 확인이 닫히면 다시 clone/전체 hash하지 않는다. clean/reset/force push·새 clone/worktree를 하지 않는다. 연구/환경/구현/외부 입력 차단을 구분하고 한 경로가 막히면 독립 ready 작업으로 진행한다.

최종 반환은 현재 commit/tree/branch, 실제 실행 명령과 결과, 관측 산출물·그림·보고서 위치, 재사용한 evidence, 과학적으로 남은 task ID와 정확한 입력, 다음 명령만 담는다. OA04를 완료했으면 현재 결과를 발표할 수 있지만 OA05–OA11 전체를 완료했다고 쓰지 않는다. 이론 전제를 채택한 것과 실제 관측에 대한 검출/모형 선택을 입증한 것을 구분한다.
