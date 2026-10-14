# 두 차례 관측 이식과 감사 스냅샷 검토

2026-10-14 실제 기본 체크아웃을 읽은 검토다. 원격/로컬 source를 변경하지 않고 준비 경로, 관측법칙, 재사용 범위와 남은 실제 분석 일을 확인했다. 기준 branch는 `audit/open-pr-local-remainder-20261014`, HEAD `6365e36d0ccc6acddb7f6909aacea8d766c0fc4a`, tree `02976f294a26854daee6116d34e71af0a8bce232`다. 첫 확인의 git status는 clean이었다. 이후 구현·테스트·게시 사실은 해당 PR의 실행 evidence를 따른다.

두 이식의 핵심 구현은 보존되어 있고 실제 관측 요약량/기술통계에 바로 쓸 수 있다. 남은 핵심 작업은 CF4·CMB·DESI의 구체적 물리 응답과 관측법칙을 완성해 공동 posterior에 연결하는 것이다. 모든 상위 증명이 성립한다는 조건부 전제를 채택해도 자료의 선택·오차·공유 nuisance·forward response가 자동으로 결정되지는 않는다.

| 검토 항목 | 실제 상태 | 이번 준비/후속 조치 |
|---|---|---|
| 감사 PR #530 | 로컬 잔여 3,388개 파일의 보존 snapshot. 다른 99 PR의 합본이 아님. | 기존 과학 판정 보존. 현재 source와 필요한 sibling commit만 읽음. |
| R1 OBS-03/04/05/07 | #530에서 네 문서 디렉터리와 entrypoint 모두 없음. 로컬 sibling branch tree에는 있음. | 각 작업을 소비할 때 exact reviewed commit의 필요한 surface를 선별 통합. 현재 DESI/R2 path의 선행조건으로 만들지 않음. |
| R2-01 structured core | 반복 큰 공분산 없이 같은 조건부 Gaussian 계산을 하는 재사용 경로가 있음. | CF4/joint에서 실제 오차모형이 이 구조를 만족하는지 확인 후 사용. |
| R2-02 CF4 | 원 grouped loader, latent law/provider, 실제 coverage/sensitivity, 분리된 synthetic injection 있음. | 실제 posterior에는 selected source model·속도오차·보정·척도·remainder가 필요. |
| R2-03 CMB | 공통 마스크에서 같은 하늘의 4개 제품·6개 차분과 exact finite-ansatz F4 도구 있음. | 차분은 기술통계. 물리 law에는 map response/covariance와 해당 모드·dipole·생략모드 처리가 필요. |
| R2-05 joint | proper shared latent를 한 번 적분하는 normalized selected density 구현 있음. | DESI summary conditioning과 fixed-count conditioning을 정당하게 함께 수용하는 adapter 필요. |
| R2-04 legacy | 원 source에 bound된 signed x·samplewise Q·strict Pi·depth image 구현 있음. | 현재 `conditional_legacy_image`는 POSTERIOR를 거부. 실제 posterior 인터페이스가 후속 구현 항목. |
| DESI scalar release | 작은 원 H5, hash-bound reader, fixed Gaussian law 모두 있음. | 첫 실제 공개 요약량·상대 likelihood·DV/rd 그림·보고서 경로로 즉시 소비. |

## 실행 가능한 첫 결과

DESI source는 `workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5`다. 앞선 source 직접 조회에서 22,845 bytes, SHA256 `836a2107c1edfb655f7a5c41701607dd8542efe4dae4309737658829cfe63ba3`를 확인했다. 이 검토는 그 read-only source 확인을 재사용한다. 새 runner의 reader가 소비 시 같은 lock을 검사한다.

`qiso = 0.9828804416839027`, covariance `0.00034950706479147084`, `zeff = 0.2952346949471036`, fiducial `DV/rd = 8.062742859742729`를 공급하는 자료다. 기존 reader `obsstat.r9_product_intake.read_desi_qiso`와 law `htt.infer.r7_desi_law.build_compressed_bao_law`를 재사용한다. 결과는 공개된 하나의 scalar 관측에 대한 재표현이다. 실제 catalogue 재적합이나 새로운 우주론적 검출은 아니다.

두 좌표의 값·분산은 `D = f q`, `Var(D) = f² Var(q)`로 변환한다. observed data density를 변환하면 `p_D(d|theta)=p_q(d/f|theta)/f`이고, prediction 좌표만 바꾼 상대 likelihood에는 Jacobian을 삽입하지 않는다. 95% pointwise conditional interval은 historical R9의 alpha=1/80을 수정하지 않는다.

CF4·CMB는 수용된 R2 JSON을 읽어 즉시 실제 자료 그림에 쓴다. 이것이 원자료 또는 결과의 재계산을 의미하지는 않는다. CF4의 실제 표본/조건수와 synthetic recovery를 분리한다. CMB 같은 하늘 복원법 차이를 독립 관측·calibration covariance·통계적 유의성으로 승격하지 않는다.

## 확인한 구현상 남은 두 연결

1. `htt/htt/htt/infer/r7_joint_experiment.py:SelectedJointDensityProvider.build`는 `FIXED_OBSERVED_COUNT` 또는 `SELECTED_JOINT_BLOCK_GIVEN_LATENT_FIELD_AND_COUNT`만 지원하며 shared conditioning 일치도 요구한다. DESI scalar law의 원 conditioning은 `PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE`다. 문자열 변조 없이 의미를 보존하는 합성 확장이 실제 joint 분석 작업이다.
2. `htt/htt/htt/infer/conditional_legacy_pushforward.py:conditional_legacy_image`는 `SAMPLING`/`FINITE_SET`만 허용하고 `POSTERIOR`를 거부한다. 실제 posterior draw를 보존하는 별도 HTT adapter 또는 검증된 확장이 필요하다. 현재 fixture의 수치 0은 시나리오 입력이며 실제 물리 sector의 관측값 0이 아니다.

이 둘은 현재 DESI likelihood나 실제 CF4/CMB 기술통계 산출을 막지 않는다. 다만 “joint와 legacy는 이미 있으므로 실제 posterior를 연결하기만 하면 완료”라는 해석은 틀리다. 계획 OA08/OA10이 이 작업을 직접 배정한다.

## 실행과 과학의 분리

앞선 읽기 전용 probe에서는 Python 3.10 환경이 numpy/scipy/matplotlib/h5py를 제공했고 `/usr/bin/python`은 astropy/healpy를 제공했다. 이 기록은 과거 실행의 증거다. 준비 스크립트는 이 턴의 실제 import를 다시 시도한다. 컴파일러나 무거운 Rust/Boltzmann runtime은 현재 경량 출력의 의존성이 아니다.

CMB 현 runner의 원본 FITS header base는 `/mnt/extdrive/workdir/raw/planck_data`로 고정되어 있다. reduced controls만 읽는 callable 자체와 별개로 CLI에는 이 경로가 필요하다. 준비 입력에 이를 포함해 경로가 없는 환경을 실행 가능으로 오인하지 않는다. 기본 경로는 accepted R2 결과의 재사용이므로 원본 multi-GB를 다시 읽거나 hash하지 않는다.

CF4/CMB/공동 적합을 위한 source/selection/보정 입력 부재는 과학 모델 작업 또는 자료 입력 작업이다. Python package/path 실패와 구분한다. family identification은 native morphology atlas의 별도 의무이며, 조건부 single-probe/joint 추정량 및 기술통계 전체의 선행 의무가 아니다.

## 범위와 실제 검증 수준

이 문서는 `physmath-research-loop` 1.3.0의 C4 실행 의존성·자원 분리와 C10 재개 가능한 인계에 해당한다. 사용한 근거는 현재 `AGENTS.md`, R1/R2 RETURN, 핵심 loader/provider/composition source, 이전 read-only map 및 #530의 현재 branch/tree/path 확인이다. 신규 물리 증명, 신규 전체 데이터 fit, 99 PR 통합, 전체 감사 payload 재검증은 수행했다고 주장하지 않는다.

12개 후속 작업은 `ANALYSIS_PLAN.json`, 현재 시작 packet은 `NEXT_TASK.json`, 정확한 명령과 구현 지시는 `CODEX_HANDOFF_KO.md`에 있다. 최종 목적은 OA11의 물리 결과·그림·보고서이며 OA04의 현재 자료 보고서는 그 중간 산출물이다.
