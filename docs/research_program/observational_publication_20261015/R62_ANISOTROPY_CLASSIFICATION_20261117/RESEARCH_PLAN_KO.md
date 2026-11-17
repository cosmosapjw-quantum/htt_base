# R62 수렴형 연구·논문화 계획

범위: anisotropy classification, Bianchi spaces와 tilt의 조건부 귀속. 기준은 2026-11-17 R62 실행 결과다. 이 문서는 coding-agent 재개 프롬프트가 아니라, 완료된 결과와 남은 과학적 산출물을 구분한 연구계획이다.

## 1. 선택한 한 가지 논문 경로

가제: **Tensor morphology and conditional Bianchi compatibility from anisotropic distance data**.

주 질문은 “관측 거리장의 비등방 tensor를 어느 형태 class까지 구별할 수 있고, 추가로 어떤 물리적 입력이 있어야 Bianchi 후보를 제한할 수 있는가?”다. 핵심 관측 결과는 CF4에서 4종 구조적 tensor 형태가 모두 95% 공동 신뢰영역에 남는다는 사실, 그리고 실제 survey 연산자가 source의 공통 고유틀을 apparent-window 공간에서 보존하지 않을 수 있다는 것이다. 알려진 기하 분류 정리를 재발견하거나 현재 자료에서 Bianchi family posterior를 얻었다는 논문으로 구성하지 않는다.

R62의 상태는 **제한된 방법론·관측 결과 초안 작성 가능 / Bianchi 식별 발견 및 최종 제출 준비 미완료**다. 이 경로를 기존 P5의 companion 연구로 연결한다. P5의 원래 CMB T/E/B 물리 transfer·atlas·Planck response·family recovery 요구사항과 42개 원 science node는 유지한다. solver-free companion 연구가 성립하는 데 Boltzmann solver가 보편적으로 필요하다는 추가 gate를 만들지 않으며, 반대로 companion 결과가 기존 polarized-transfer gate를 충족했다고 표시하지 않는다.

## 2. 이번 루프에서 완료한 산출물

| 작업 | 실제 산출물 | 근거 상태 |
|---|---|---|
| 과거 연구의 선택적 재구성 | R47–R61 관련 PR/branch·28개 핵심 source와 carrier identity, quarantine 경계 | implementation/source checked |
| tensor class 및 공통 calibration quotient 유도 | simultaneous diagonalization, class 포함관계, \(LVL^T\), witness/exclusion 계약 | derived; 표준 수학을 조합 |
| likelihood 구성 | 실제 \(O_mD_J\)에 기초한 21·26변수 Gaussian carrier와 precision/score | implementation verified |
| 실제 CF4 분석 | 42개 carrier, 210개 class 질의, 616개 commutator enclosure | numerically checked |
| 기존 Pantheon+ 재사용 | R36-08의 두-depth STF10·차분 STF5, 두 selection에서 zero witness와 class 교차 직접 계산 | inherited qualified law; numerically checked |
| 관측 응답의 영향 | 공통-frame source가 apparent noncommutativity를 만드는 실제-연산자 injection | constructed counterexample, numerical parity checked |
| Bianchi/tilt 제약 | actual-state momentum map, IX 반례, exceptional VI\(_{-1/9}\), V kernel 조건 | literature-supported / derived / implementation verified |
| unit/frame 복원 | geodesic normal의 Ricci reconstruction, \(c\)·stress·time/frame 조건 | known equations with explicit translation |
| 코드 검증 | 변경 경로 및 기존 관련 suite 113 passed | execution verified |
| 독립 검토 교정 | R62-F1 source-relative range 및 equation-scale residual, 추가 14개 단위 regression을 포함한 물리 경로 100 passed | targeted repair verified |

새 source covariance의 수치 rank는 모두 21/26이며 ridge를 쓰지 않았다. 기존 35,970개 source의 full covariance를 재사용했으며 catalogue-size covariance를 새로 만들지 않았다. 새 prior나 임의 transfer coefficient로 빠진 물리 대응을 대체하지 않았다.

## 3. 선행연구와 비교한 기여의 경계

| 비교 대상 | 이미 알려진 부분 | 본 프로젝트가 추가해야 할 실질적 가치 |
|---|---|---|
| Ferrando–Sáez 2020; Sáez–Mengual–Ferrando 2024 | metric/curvature concomitant에 의한 intrinsic homogeneous/Bianchi 분류 | noisy sky carrier에서 그 입력을 어느 부분까지 복원할 수 있는지, 불확실성과 동치류를 어떻게 유지하는지 |
| Hewitt–Bridson–Wainwright 2001 및 tilted Bianchi 문헌 | normal-frame momentum·shear·matter projection 및 state-dependent 제약 | 관측 likelihood를 그 제약 fibre에 올리는 명시적 response와 admissibility 처리 |
| Golub–Pereyra 1973 및 표준 GLS | 선형 진폭 제거, variable projection, covariance 기반 추론 | 실제 mask·depth response·cross-covariance를 보존한 분류 실험과 재현 가능한 결과 |
| 기존 Bianchi CMB 형태 연구(Pontzen 2009; Sung–Coles 2010) | near-FLRW scalar/vector/tensor freedom, focusing/twisting morphology | Boltzmann hierarchy를 거치지 않는 낮은 redshift 관측량과 조건부 기하 제약의 연결 |
| 프로젝트 R48/R54/R58/R60/R61 | tensorization, all-type algebra, 단일 tensor 축대칭, affine-depth 검정 | 다중 tensor의 공통 고유틀/형태, 공통 offset quotient, source-operator counterexample와 실제 CF4 적용 |

현재 새로 확보한 것은 프로젝트 차원의 계산·통합·오류 교정과 관측 결과다. “최초의 Bianchi classifier”, “새 Gaussian likelihood”, “5변수가 Fisher information을 늘린다”, “IX tilted dust의 존재를 처음 보였다”는 novelty 주장은 철회 대상이다. 최종 novelty는 아래의 source-to-kinematics response와 관측 적용이 완성된 뒤, 동일 목표를 가진 원 논문과 직접 비교해 판단한다. 검색 부재를 novelty의 증명으로 사용하지 않는다.

## 4. 다음 연구의 최소 과학적 작업 묶음

아래 항목은 새 연구 가지의 무제한 목록이 아니라, 같은 P5 companion 논문을 끝내기 위한 의존 순서다. 이번 10단계 종료 후 자동 실행하지 않는다.

### A. 관측 tensor와 physical normal shear 사이의 대응을 고정한다

입력은 R54의 관측량 선택 규칙, R61의 frame/calibration 구분, R62 source likelihood, 그리고 R49의 교정된 normal/species/observer state다. \(u_N,u_s,u_O\), sourceward direction, proper time, redshift frame, distance indicator, zero-point를 명시한다. \(K_j\)를 정의만으로 \(\sigma_{ab}/H\)라고 부르지 않고, 선택한 낮은 redshift·약한 비등방 근사에서 \(D_L(z,\hat n)\) 또는 log-distance response를 직접 유도한다.

최소 후보는 geodesic-normal, isotropic normal stress를 갖는 Bianchi I와 untilted V다. 이 경우 \(\sigma=b^{-3}S_*\)이고 V에는 \(S_*a=0\)가 추가된다. Type I에서 single homogeneous perfect fluid에 임의 tilt를 추가하면 운동량 제약에 어긋나므로, tilt가 필요한 비교는 보상되는 다중 source 또는 실제 admissible한 다른 family로 명시한다.

완료 산출물은 response 식·단위·부호·유효 redshift/비등방 범위, 생략항의 크기, actual operator를 통과한 \(X_{\rm phys}\)와 추정 가능한 parameter combination이다. FLRW 극한, 회전 covariance, \(c\) 차원, 기존 선형 response와의 일치를 검산한다. nuisance와 physical quantity의 열이 정확히 퇴화하면 해당 조합을 conditional/identified quotient로 남기고 추가 prior로 측정을 만들어 내지 않는다.

### B. 필요한 경우 직접 광학 적분으로 근사를 닫는다

Boltzmann hierarchy 없이 homogeneous background의 null geodesic과 Jacobi/Sachs 광학 방정식을 적분해 distance·redshift·direction response를 계산할 수 있다. 기존 BASS geometry 및 admissible state를 재사용하고, 후보를 먼저 I/V와 명시적인 tilted constraint-consistent 예로 제한한다. 일반적인 all-family posterior를 먼저 여는 순서를 피한다.

완료 기준은 background constraint 보존, FLRW 및 이용 가능한 analytic endpoint와의 일치, step refinement, sky-frame 회전, actual source operator를 거친 평균값의 안정성이다. 기존 R49의 임의 probe coefficients나 격리된 24D posterior는 이 경로의 calibration 자료가 아니다. 어떤 물리 quantity가 불확실하면 그 nuisance/source law를 joint likelihood에 명시한다. 실제 자료의 class 구별에 영향을 주지 않는 높은 차수 atlas까지 확장하지 않는다.

### C. 현재 결론을 바꿀 calibration·covariance 입력을 확보한다

CF4의 7개 처리에서 zero 판정이 달라지고 공통 offset을 제거한 성분에서는 zero가 모두 남는다. 따라서 우선순위는 더 많은 local axis 최적화가 아니라 distance-indicator 및 survey zero-point, angular/depth selection, peculiar velocity covariance의 검증이다. 필요한 자료는 source/indicator별 overlap과 calibration 공분산이며, 현재의 grouped catalog와 32D carrier만으로 그 외부 정보를 새로 측정할 수 없다.

새 calibration field \(b(z,\hat n)\)는 endpoint 값만으로 제어하지 않고 실제 bias operator \(B\,O_m b\)를 통해 tensor contrast에 전달한다. 공통 angular offset은 분석적으로 제거하고, depth-dependent 부분은 외부 근거가 있는 body/prior 또는 명시적 nuisance span으로 둔다. 거리오차·selection·cosmic law 변화에 대한 coverage는 이 물리·통계 계약이 고정된 뒤 검증한다. Monte Carlo의 성공 기준은 특정 발견을 재현하는 것이 아니라, 선언한 joint confidence procedure의 포함률과 잘못된 class 배제율을 확인하는 것이다.

### D. 기존 SN 자산을 source-matched 비교로 확장한다

R36-08-PUBLIC-SN은 이미 원 Pantheon+ source와 STAT+SYS covariance, global intercept·high-bin offset을 profile한 두-depth signed 16D carrier, leave-one-survey 결과를 보존한다. 현재 product는 `FORMALLY_QUALIFIED_RELEASED_MAGNITUDE_CONDITIONAL_COMPARATOR`다. 원자료를 처음부터 확보하는 작업은 필요하지 않다. 이번 R62에서도 primary490행과 lower-z705행의 STF10 및 차분 STF5를 재사용했고, 모두 zero witness가 신뢰영역 안에 있음을 실제로 계산했다.

남은 작업은 source-level 물리 response와 frame을 확정하여 같은 estimand를 비교하는 것이다. SN은 magnitude residual·zHD/zHEL/VPEC 처리이며, physical sky frame과 CF4 shared-PV law는 기존 contract에서 UNKNOWN이다. 두-depth 차분은 한 tensor만 남으므로 calibration을 제거한 뒤의 비가환성 검정에는 정보가 없다. 기존 raw source·consumer를 재사용해 필요할 때만 세 개 이상 깊이 response 또는 연속 source basis를 구성하고, rank·covariance·selection 및 source injection을 검증한다. 아무 방향 비교나 두 survey likelihood의 독립 곱을 물리적 재현으로 사용하지 않는다.

결과물은 같은 물리 response에서의 tensor likelihood, class confidence-set 비교, calibration·source/host 중복·shared peculiar-velocity 공분산의 명시적 처리다. 기존 survey robustness도 재사용한다. 두 자료에서 같은 class가 배제되거나 유지되는지 보고하고, 발견이 없더라도 허용되는 tensor 형태·진화의 범위를 닫는다. R36-10-GEOMETRY-IMAGE와 R32-07-P5-ALGEBRA의 한정 geometry/constraint atlas는 이 다음 물리 해석의 prior theory이며, 자체에 empirical covariance나 frozen observed response가 있다고 보지 않는다.

### E. Bianchi candidate set을 계산한다

물리적 normal-frame \(H,\sigma,D_t\sigma\)와 normal density/stress가 확보되면 Hamiltonian 및 shear evolution으로 \({}^{3}R,{}^{3}S\)의 likelihood를 유도한다. 그 상태에서 actual-state momentum map과 Jacobi \(na=0\)를 강제한 \((a,n,\beta_s)\) 후보 집합을 계산한다. unknown stress·source·observer boost는 제거되었다고 가정하지 않고 joint fibre에 남긴다.

generic Bianchi type까지 나아가려면 spatial connection/curvature derivative 입력이나 이를 대신할 명시적인 homogeneous evolution closure가 필요하다. I/VII0, V/VIIh처럼 action 동치가 남는 경우에는 집합으로 결과를 반환한다. tilt가 허용되는 초기 상태의 존재와 해당 tilted history가 관측 자료를 설명한다는 주장을 구분한다. 이 단계의 성공은 반드시 단일 type 선택일 필요가 없으며, **가정이 명확한 후보 배제 또는 식별 가능한 동치류**도 완결된 결과다.

## 5. 원고 구조와 현재 쓸 수 있는 주장

1. **질문과 대상:** scalar anisotropy amplitude만으로는 여러 tensor의 상대 orientation을 복원할 수 없다는 구체적 문제.
2. **통계 방법:** signed tensor carrier, source operator, full covariance, singular class의 confidence-set witness/exclusion, common calibration quotient.
3. **실제 자료:** CF4 sample/selection/frames/working covariance, 7개 nuisance 처리, 21·26변수 response.
4. **결과:** 42개 carrier의 class 교차, zero·depth 성분 민감도, actual-operator injection.
5. **물리적 해석:** 제한된 I/V의 shape-history 조건, actual-state Bianchi/tilt constraint fibre, 기하 입력과 동치류.
6. **방법 비교와 한계:** exact Gaussian score와 정보량 동일, known intrinsic classification과 역할 구분, 외부 calibration·response 요구사항.
7. **부록:** IX constructor 및 Jacobian 오류의 정정, Wolfram algebra, 수치 검증과 재현 파일.

현재 사용할 수 있는 영문 초록 초안:

> We construct covariance-preserving classifications of finite series of symmetric trace-free distance-response tensors. Common eigenframes, axial shapes, general fixed shapes and fixed shapes with a vanishing eigenvalue are tested through explicit intersections with a shared Gaussian confidence ellipsoid. Signed commutator images provide necessary-condition exclusions, while nonlinear fits are retained as feasible witnesses rather than assigned uncalibrated likelihood-ratio laws. An exact common-offset quotient removes arbitrary constant tensor calibration. Applying the procedure to four overlapping Cosmicflows-4 estimators and their source-bound quadratic and cubic redshift responses, we find that all four structured classes remain compatible at the stated confidence level across seven nuisance treatments. Constant and varying tensor hypotheses have different calibration sensitivities. A noise-free injection through the actual survey operators demonstrates that a commuting source can produce noncommuting apparent-window tensors. We then formulate conditional Bianchi compatibility through state-dependent momentum constraints and distinguish it from direct family identification. These results provide a reproducible interface between observed tensor morphology and geometric candidate sets, without requiring a Boltzmann hierarchy for the stated calculation.

이 초록은 covariance calibration의 조건과 source response의 현상론적 지위를 본문에서 명시하는 전제다. 실제 Bianchi 식별이나 physical shear 검출을 초록에 추가하려면 A–E의 해당 관측 대응과 검증이 먼저 있어야 한다.

## 6. 제출·중단 조건

**현재 충족:** 수학적 분류 대상의 정의, common-offset quotient 증명, 실제 source/covariance 구현, 보존된 prior work와의 차이, 관측 결과, 수정 코드 검증, 계산 provenance.

**최종 제출 전에 필요한 핵심 항목:** 논문의 주장 수준에 맞는 physical response 또는 명시적으로 제한된 observable 해석, covariance/calibration 근거, 같은 목표에 대한 표준 방법과의 정확한 비교, 자료·코드 접근성과 독립 재현. Bianchi 귀속을 중심 주장으로 삼을 때에는 실제 constraint-compatible physical forward likelihood 및 남는 action/source 동치류가 추가로 필요하다.

외부 calibration이나 physical response를 확보하지 못하면, 결과를 현상론적 CF4 tensor 분류와 actual-operator 반례로 제한한다. 그 범위의 독립적인 과학적 유용성이 약하면 R58/R61 기반 논문의 방법·한계 절로 통합하고, 양의 Bianchi 발견을 만들기 위해 가설 가지를 계속 늘리지 않는다. 어떤 조건에서 어떤 class를 배제할 수 있는지를 정량적으로 닫는 것이 종료 목표다.

## 원전 및 데이터 출처

- [Ferrando–Sáez 2020](https://arxiv.org/abs/2004.01877v1), intrinsic homogeneous three-geometry classification.
- [Sáez–Mengual–Ferrando 2024](https://arxiv.org/abs/2409.15854v1), perfect-fluid spatial homogeneity and intrinsic Bianchi labeling.
- [Hewitt–Bridson–Wainwright 2001](https://arxiv.org/abs/gr-qc/0008037v1), 일반 homogeneous normal equations가 있는 Appendix A.
- [Kwidzinski–Piechocki 2019](https://doi.org/10.1140/epjc/s10052-019-6701-z), general tilted-dust IX.
- [Golub–Pereyra 1973](https://doi.org/10.1137/0710036), separable nonlinear least squares.
- [Pontzen 2009](https://arxiv.org/abs/0901.2122v2), near-isotropic Bianchi CMB freedoms.
- [Sung–Coles 2010](https://arxiv.org/abs/1004.0957v2), anisotropic temperature/polarization morphology.
- [Pantheon+SH0ES 공개 release](https://github.com/PantheonPlusSH0ES/DataRelease), 기존 R36-08의 pinned release와 carrier를 재사용; CF4와의 공동 likelihood는 구성하지 않았음.

모든 문헌의 적용 가정과 버전 확인 범위는 [literature_map.md](REVIEW/literature_map.md)에 기록했다.
