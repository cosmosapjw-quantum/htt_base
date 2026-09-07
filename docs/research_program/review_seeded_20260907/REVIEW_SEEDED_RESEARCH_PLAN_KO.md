# HTT 후속 계획 완결 — PR462/463 연속성과 추가 코드·자료 검토

작성일: 2026-09-07
역할: SUPPORTING_ADDENDUM_TO_PR462_PR463
상태: PLANNING_COMPLETE / THEORY_FREEZE_PENDING_M1_M2_M3 / EXECUTION_RELEASE_FALSE

## 1. 활성 계획은 하나다

최종 원격 동기화에서 중단 전 연구가 이미 PR462에, 그 계획 완결판이 PR463에 게시돼 있음을 확인했다. 이 파일의 초기 독립 계획 표기는 그 사실을 회수하기 전에 작성됐다. 이를 세 번째 연구 프로그램으로 유지하지 않고, 지금부터 **PR462의 기존 이론과 PR463의 통합 master/DAG를 활성 기준**으로 사용한다.

- 원 연구: PR462, commit `b4d04e62d664997eb9e1858b6195c35e4ece3378`, tree `ea95984f5f1b1d977ca625dfde9a34d71202b115`, `docs/research_program/post_review_20260907/`.
- 활성 통합 계획: PR463, commit `0e2d6e3a890ae44303440e8534fb6080d1dac881`.
- [활성 한국어 master](https://github.com/cosmosapjw-quantum/htt_base/blob/0e2d6e3a890ae44303440e8534fb6080d1dac881/docs/research_program/referee_seeded_20260907/00_MASTER_PLAN_KO.md).
- [활성 DAG](https://github.com/cosmosapjw-quantum/htt_base/blob/0e2d6e3a890ae44303440e8534fb6080d1dac881/docs/research_program/referee_seeded_20260907/03_PROGRAM_DAG.yaml), blob `1dfe55d6228841c14c547cdaf8364758c8bcddea`.

실제로 활성 master, 전체 DAG, PR 설명과 PR462 `THEORY_RESULTS.md`의 관련 유도를 다시 읽었다. 원 결과·검증 oracle·데이터/코드 역할을 재사용한다. 본 PR464는 추가 source finding과 설명용 계산의 보완판이다. PR462/463 refs를 이동하거나 원 문서를 덮지 않는다.

초기 상세 계획과 JSON은 commit `f6ee52673dbd1566b0c76c700f34fa326d01f7b6`에 보존돼 있으나, 더 이상 독립 실행 일정의 권위가 아니다. 현재 `RESEARCH_DAG.json`은 활성 DAG를 가리키는 label crosswalk이며 별도 실행 graph가 아니다. 결과적으로 남은 MAIN 연구는 늘어나지 않는다.

## 2. 유지되는 목표와 산출물

Low-ell morphology, local boost/global tilt 구분, 조건부 physical kinematical bounds, dipole와 다른 low multipole의 anomaly, redshift/depth 의존성이라는 장기 다섯 축을 유지한다. 55쪽 입문서는 동반 해설판으로 보존하고, 집중 연구 결과는 다음 두 축으로 정리한다.

**CMB morphology와 nuisance-conditioned information.** 전체 관측 tensor, mask/noise/foreground와 같은 sky의 고다중극 제약, observer response 및 matched null을 결합한다. 완전한 표현 자체가 원자료보다 정보를 늘리거나 기존 multipole-vector 연구를 대체하는 것은 아니다.

**조건부 운동학적 상한과 깊이별 frame consistency.** 원거리 자료·선택함수가 있는 number counts·joint calibration을 사용해 식별되는 bulk/symmetric-affine/dipole 성분과 식별되지 않는 방향을 분리한다. ShellSourcePole, CumulativeObserverPole, RemoteDipolePole, RemoteQuadrupolePole을 같은 축 추정치로 합치지 않는다. Global-tilt 가설은 유지하되 실제 dynamical transfer 없이 phenomenological depth profile을 native Bianchi 결과로 이름 붙이지 않는다.

편광·remote kSZ/pSZ·추가 survey acquisition·새 native Bianchi solver·일반 비선형 almost-EGS 증명은 현재 유한 campaign의 무조건적인 선행과제가 아니다. 해당 물리적 응답을 갖춘 뒤 별도 확장한다.

## 3. 회수한 수학은 더 강한 형태로 재사용한다

PR462의 T1–T10을 `DERIVED_NOT_NEW_NATIVE_EXECUTION`으로 재사용한다. [본 보완의 수학 문서](THEORY_RESULTS_AND_CORRECTIONS.md)에 겹치는 유도는 재설명이지 새로운 열 개 성과나 재실행이 아니다.

특히 원 연구에 이미 있는 다음 결과를 보존한다.

- 기존 비영 minors와 block-column 상한은 axial 최소 cutoff L=10을 준다. 방향에 선형인 응답의 비영 homogeneous minor로 almost-every-direction rank를 논증할 수 있지만, every-direction 또는 uniform singular-value bound는 아니다.
- Spherical Gaussian STF3 또는 명시적 uniform-sphere 방향 아래의 projection fraction은 Beta(3/2,2)다. SO(3) isotropy만으로 그 법칙을 부여하지 않는다. 제출 심사의 약 0.38, 0.07 tail은 그 법칙과 맞는다.
- Conditional LS covariance와 trace bound는 제출한 예시 D2/D3에서 rms 0.88235–0.88785를 주며 0.8435가 아니다. 큰 오차를 모든 low-ell estimator의 보편적 no-go로 승격하지 않는다.
- STF derivative contraction의 정확 operator norm은 sqrt(7/5)다. 원 연구의 shear bound는 epsilon2_star + epsilon1_prime + 3/sqrt(35) epsilon3_prime이며, 같은 characteristic estimates 아래 (epsilon1+epsilon2)/3 + epsilon3/sqrt(35)가 된다. 본 보완의 sqrt(3) 대조는 안전하지만 덜 날카로운 중간 상계이므로 이것으로 기존 결과를 약화하거나 재개하지 않는다.
- Vorticity도 원 연구에서 background cancellation을 먼저 처리해 3 epsilon1_prime_star + epsilon1_prime + (6/5) epsilon2_doubleprime를 얻었다. 전통적 literature branch와 명시적 1차 모형의 더 강한 sufficient branch를 구별한다.
- Bounded nuisance의 기준점 상쇄 반지름은 R이지만 두 admissible state의 pairwise ambiguity에는 2R이 들어간다. 같은 sky auxiliary conditioning, soft-mask scaling, observer/free-shell gauge와 radial rigid-rotation null도 기존 결과다.
- Deterministic error enclosure가 실제로 정당하면 양의 singular margin은 계산 후 보고할 수 있다. 확률적 calibration/selection과 이 수학적 slack을 혼동한 기존 문구는 새 정오표에서 수정한다.

심사자의 재검산 주장은 원 실행물을 읽지 않은 한 그 작성자의 보고로 남긴다. 기존 문서 artifact 수용은 새 과학적 교정에 대한 면책이 아니다. 원 PDF·receipt는 보존하면서 정오표/후속 논문에 변경의 이유를 밝힌다.

## 4. 이 보완판이 추가하는 실제 source finding

[REUSE_AND_DATA_MAP.md](REUSE_AND_DATA_MAP.md)는 broad repository discovery와 선택된 함수 본문 검토를 정리한다. 모든 branch의 모든 bytes를 실행·감사했다는 뜻은 아니다. default ref와 accepted methodological donor를 구분하며, exact boost/processed donor의 우선 source pin은 활성 PR463 DAG가 보존한 것을 따른다. 본 지도에 기재한 오래된 branch locators는 그 최신 donor를 대체하지 않는다.

DESI 경로에서 실제 읽은 파일은 다음이다.

- `dl_pipeline/scripts/extract_desi_compact.py`, blob `02120d7413f8a3b6d6a998f9c0209bdb780cb981`.
- `scripts/desi_dipole_measure.py`, blob `3ca7c465364322ece5afb6633367f811c691c4d2`.
- 두 파일의 조회 source: default commit `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`.

Compact와 random 방향은 RA/Dec로 만들어지는데 비교 CMB 방향은 Galactic 성분이다. 읽은 연산 경로에는 그 사이의 좌표변환이 없다. 또 같은 선택 표본에서 평균 정규화를 맞춘 뒤 Dhat=3<delta n>_R를 계산하면 그 선형 response는 일반적으로 I가 아니라 3 Cov_R(n)이다. 균일한 북반구에서는 diag(1,1,1/4)여서 축방향 진폭을 네 배 억제한다. 이는 source-level 반례이며 실제 데이터의 영향 크기를 측정한 결과는 아니다.

재사용할 것은 reader·random-count primitive·명시된 metadata이고, 교체할 것은 좌표계 혼합과 자동 window-deconvolution이라는 해석이다. 회귀는 full sky, hemisphere, 양쪽을 함께 회전한 알려진 벡터, per-cap 평균, masked quadrupole leakage, zero-amplitude undefined direction을 포함한다. 기존 15개 oracle과 이번 사례를 이름·의미로 대조해 중복 없이 M2/M3와 C1/C2에 연결한다. Native patch/test는 아직 수행하지 않았다.

PR463에서 이미 확인한 constrained-realisation의 H=0 대 d=0 차이, full/half shear norm adapter, affine rank와 cell-bootstrap 문제를 그대로 유지한다. 메타데이터 support score, 'bound' 문자열 또는 diagonal-whitening scaffold를 실제 물리적 Jacobian·joint covariance·posterior로 승인하지 않는다. CF4 P0 quarantine과 폐기된 scalar-MES 결과도 복권하지 않는다.

## 5. 남은 이론은 정확히 M1·M2·M3다

| 활성 계약 | 이번 초안의 옛 이름 | 종료할 실제 과학적 내용 |
|---|---|---|
| M1_CMB_MODEL | T1 | 주 CMB product와 처리 순서, monopole/anisotropy 차수, full low/high/foreground/noise joint law, primary statistic·null·chart 처리와 response |
| M2_REDSHIFT_MODEL | T2 | 원 distance/redshift likelihood, survey selection/calibration/frame, shell windows, 실제로 식별되는 physical functional과 null directions |
| M3_EXPERIMENT | T3 | M1/M2를 exact estimand/input/algorithm/output, masks/bins/prior, calibration/test, error budget·source/API·실패 분기까지 갖춘 한 실행명세로 결합 |

M1과 M2는 독립적으로 진행 가능하고 M3가 둘을 합친다. 이번 초안의 직렬 T1→T2→T3 표기는 추가 제약이 아니다. THEORY_FREEZE 뒤에만 Codex의 전체 구현·자료분석을 시작한다. 현재 `execution_release=false`는 계획 미완료가 아니라 선택한 과학 명세가 아직 닫히지 않았다는 실제 상태다.

Codex에는 physical model, prior, null, 통계량 tail, product substitution, survey cut 또는 numerical tolerance의 과학적 선택을 남기지 않는다. 동결된 semantic predicate에 따라 실제 경로·realisation ID·설치 import를 기계적으로 확인할 수는 있다. 진짜 model contradiction은 MAIN으로 반환하지만 같은 승인 범위의 구현·fixture·runtime 오류는 원 실패를 보존하고 자율 수정한다.

## 6. 후속 실행 경로도 기존 C0–C5를 따른다

THEORY_FREEZE → C0_INTEGRATION → C1_IMPLEMENTATION → C2_SYNTHETIC_VALIDATION.
C0에서 C3_SELECTED_DATA_INTAKE를 병행할 수 있으며 C2와 C3가 C4_OBSERVED_ANALYSIS로 합쳐진다. C4 안에 CMB와 DEPTH 자료 branch가 있고 C5_GIT_RETURN을 거쳐 MAIN이 실제 결과를 해석한다.

어느 local node에서든 실패·부분 결과를 C5로 반환할 수 있다. Downstream 관측분석 성공을 기다려야만 실패를 보낼 수 있는 graph로 만들지 않는다. 본 초기 초안의 C1–C4·V0/V1·D1/D2·J0는 이 단계들의 세부작업 이름이며 독립적인 새 gate가 아니다.

Primary CMB 경로는 기존 PR3와 실제 matched FFP10를 우선으로 한다. 비어 있는 NPIPE 경로, 따로 있는 PR4 파일, incomplete Commander, WMAP7 simulation과 WMAP9 map, ACT lensing과 temperature의 차이를 보존한다. 179개 자산 및 약 1.499TB라는 목록은 소유·접근 metadata이지 분석 admission이나 독립표본 수가 아니다. 기존 inventory에서 선택 product만 확인하며 전체 저장소를 재복사·재다운로드·재해시하지 않는다.

## 7. 이번 작업의 종료와 검증 한계

중단 전 계획·유도를 회수했고, 활성 계약을 하나로 통일했으며, 추가 source-level 결과와 데이터 선택 기준을 Git에 보존했다. **계획 작업은 완료**다. 다음은 M1/M2/M3의 실제 연구이지 또 다른 재계획이나 하네스 작성이 아니다.

새 native Python/CAS/Monte Carlo/관측 실행은 없다. Scalar illustration은 웹 계산기로 확인했고, source/diff와 문서의 원격 읽기를 수행했다. DAG의 native parser 실행은 주장하지 않는다. 초기 사본을 고정 commit에 보존한 뒤 이 문서와 crosswalk만 정합화했으며 PR462/463, accepted report/evidence, production source와 canonical ledger는 수정하지 않았다.

Budget은 실제 진전과 누적 사용에 맞춰 조정하되 사용자 hard cap, platform limit, 새로운 외부 비용/권한과 사전등록 실험 예산은 별개다. 수동 ZIP relay와 WORK_THREAD는 기본 단계가 아니다. 최종 실행명세와 실제 결과는 Git의 고정 링크로 교환한다. Merge·ready·public visibility·scientific/canonical promotion은 이번 계획 완결에 포함되지 않는다.
