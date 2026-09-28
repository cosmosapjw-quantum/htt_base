# Local Codex — R1–R5 통합 인계

ROLE=LOCAL_CODEX_THEORY_HANDOFF_INTEGRATOR
PROJECT=MES_TENSOR_OPTICAL_COMPARISON
WORK_UNIT=INTEGRATE_CURRENT_THREAD_R1_TO_R5_20260927

첨부 MES_R1_R5_HANDOFF_20260927.zip 하나를 입력으로 삼아 현재 local repository에 R1–R5 연구 결과를 통합하라. 계획만 제시하지 말고 승인된 문서 반영과 반환 handoff까지 완료하라.

## 1. 입력과 현재 repo

현재 cwd, repo root, branch, HEAD commit/tree, git status, 적용 AGENTS.md를 먼저 읽어라. 기존 사용자 변경을 보존하고 reset/clean, 자동 branch 전환, 새 worktree 생성을 하지 마라. 과거 보고서의 commit은 historical source이지 현재 HEAD가 아니다.

ZIP을 안전한 intake 경로에 풀고 00_READ_FIRST_KO.md, INPUT_INVENTORY.json, PACKAGE_VALIDATION.json, MANIFEST.sha256을 읽어라. 외부 ZIP hash는 동봉 파일과 별도로 전달된 값이 있으면 대조하고 내부 manifest를 확인하라. 동일 경로에 다른 내용이 있으면 덮어쓰지 말고 구별하라.

materials/에는 단계별 원본 패킷의 펼친 내용, originals/에는 byte-preserved 원본 ZIP/보고서가 있다. reports/에는 주요 보고서의 동일 byte 사본이 있다. 임의로 전부 재압축해 과거 archive identity를 대체하지 마라.

이번 주 대상:
- R1: MES_FRESH_OPTICAL_TENSOR_R1, 2026-09-20.
- R2: MES_GENERALIZED_TENSOR_R2, 2026-09-20.
- R3: MES_R3_OBSERVABLE_JET_AND_SOURCE_BOUNDS, 2026-09-27.
- R4: MES_R4_ALGEBRAIC_CLOSURE_AND_COMPENSATED_OBSERVABLES, 2026-09-27.
- R5: MES_R5_FINITE_TILT_JOINT_OPERATOR, 2026-09-27.

2026-09-20의 MES_GENERALIZED_TENSOR_R3/R4/R5는 위 R3–R5와 다른 계열의 자료다. 번호만으로 대체하거나 덮어쓰지 마라. 단계 식별키는 연구계열+날짜+work-unit+hash다.

R3는 보고서 원문을 제공한다. 별도 실행 raw/독립 판정 파일을 이번 패킷에서 확보하지 못했다. 보고서에 기록된 실행/판정과 raw를 직접 확보한 상태를 구별하라. 이 누락으로 나머지 통합을 멈추거나 R3 원문을 읽지 않은 것으로 취급하지 마라. 다만 모든 단계의 원시 증거가 완비됐다고 선언하지 마라.

## 2. 필수 읽기와 단계별 보존

각 단계의 최종 보고서, 상세 증명, 독립 판정, 수정 기록, code/raw, provenance를 실제 확보 범위에서 읽어라. 요약으로 원문을 대체하지 않는다.

R1:
- 정확한 5×5 shear operator L_B, 자기수반성·양성/coercivity의 조건.
- Brightness의 l=0,2,4 의존성과 residual inverse image.
- 별도 Bianchi I branch의 끝점 광학 K 복원 및 응력 적분식.
- 누적 광학 변형, 현재 전단, 전역 almost-FLRW의 구별.
- 전단 통계량과 기존 signed x의 관계.

R2:
- 전 운동학 tensor bundle과 polar/axial parity.
- Exact local optical R(e),V(e), inverse와 안정성.
- All-kinematics bolometric weak transport와 residual body.
- Local boost/global tilt 및 미분의 구별.
- MES 원전 bound, repo 계수, 선언한 reference의 authority 구분.
- Morphology-preserving gauge, 식별 부분공간의 투영, nuisance likelihood.
- 같은 데이터 numerator/denominator의 공동 불확실성.
- T,Q_outer,F_amp,Pi_tail,G_tensor와 legacy 통계량의 정의.

R3:
- 실제 nearby-source 거리–적색편이/proper-motion leading response.
- Photon generator와 직접 관측량의 구별.
- Nongeodesic/collision source와 derivative budget.
- 유계 잔차를 가진 joint inference와 기존 repo convention adapter.
- 본문 채택과 사후 exploratory 확장의 상태 차이.

R4:
- Lie algebra+metric의 공간 미분 연산자 및 metric scale 필요성.
- Exact homogeneous tilted 1-jet adapter.
- 세 거리 보상식, sharp remainder, noise, 실제 shell/source/frame 조건.
- 첫 CAS 구현 실패와 수정된 결과의 보존.

R5:
- Exact 12×9 affine map/rank9.
- omega - beta × (A/c)/2 = S w_C.
- Free beta timejet의 rank3 image와 이를 소거하는 joint combinations.
- Nonempty compact section+free subspace의 target boundedness 정리.
- Retained radiation timejet block rank8.
- 비가환 finite-tilt 공동 원판, 같은 latent state의 tensor statistics.
- Kinematic CAS 등록 이전 / radiation-disk 등록 이후의 실행 순서.

## 3. 필수 정합성 대조

INTEGRATION_NOTES_KO.md를 읽어라. R1은 exact shear operator/positivity, R2는 exact all-kinematics weak form을 이미 포함한다.

R5 문헌 부록의 신규 후보 HOLD를 앞선 결과 전체의 미검증으로 확대하지 마라. 반대로 비슷한 이름의 새 source/finite-velocity 후보를 앞선 판정으로 자동 승인하지 마라.

식·가정·normalization·source·frame·편광·finite velocity·판정 대상 hash를 대조하여 각 관계를 기록하라:
REUSED / EXTENDED / SPECIALIZED / CORRECTED /
SUPERSEDED_WITH_EVIDENCE / DISTINCT / UNRESOLVED_CONFLICT.

뒤에 쓰였다는 이유로 앞선 결과를 폐기하지 않는다. 원 판정/원고를 소급 수정하지 말고 통합 정정은 별도 문서로 남겨라. 통합 전에는 exact radiation을 처음부터 다시 유도하는 다음 연구를 확정하지 마라.

## 4. 공통 scientific contract

원래 목표는 Theta,sigma,omega,A,beta의 방향·부호·형태·상관을 보존하여 동일 관측조건/물리 전제의 reference로 비교하는 것이다.

보존할 convention:
- (-,+,+,+), 필요한 c,hbar,k_B, a=A/c의 rate 단위.
- Derivative-first omega, epsilon123=+1; outward n과 propagation e=-n.
- Brightness와 temperature multipole, 각평균과 전체 적분의 차이.
- Normal/tilted, geodesic/nongeodesic, exact/retained approximation.
- Tensor-vorticity Frobenius norm과 axial-vector norm의 sqrt(2).
- Local beta와 congruence beta/derivatives, electron-relative beta.

K(끝점 광학/extrinsic curvature), T(boost matrix/normalized tensor),
Pi(radiation quadrupole/statistic) 등 충돌 기호의 대응표를 작성하라.

Reference upper bound / attainable maximum / declared scale를 구별한다.
Theta/H=3을 팽창 이탈 측정으로 쓰지 않는다.
Theta,beta의 보편 MES ceiling을 만들지 않는다.
Product bound를 근거 없이 ellipsoid로 바꾸지 않는다.
Projection과 미관측 성분을 0에 두는 intersection을 구별한다.
Signed T와 원 harmonic carrier를 보존한다.
Legacy signed x,Q_gauge,F_support,G_path를 새 positive norm으로 덮어쓰지 않는다.
Deterministic set, confidence set, posterior/sampling law를 구별한다.

## 5. 주장·코드 대응

관련 repo 문서·코드만 좁게 탐색한다. 각 claim에 다음을 기록하라:
최초/후속 출처, 정의/가정/범위, proof 위치, 실제 check와 identity,
독립 판정 범위, 현재 대응 문서/코드, 구현 상태, 열린 문제.

근거 상태:
established / literature-supported / derived / numerically checked /
implementation-verified / conjectural / unresolved / blocked.

Repo 대응:
MATCH / ADAPTER_NEEDED / CONFLICT / NOT_IMPLEMENTED / UNVERIFIED.

이론 채택, 구현 검증, 실관측 admission은 별도 필드다.
R5 최종 판정을 모든 이전 주장에 일괄 적용하지 마라.
현재 repo의 R7/R9 등은 별도 namespace로 필요 부분만 연결하라.
함수명 유사성만으로 구현됐다고 판정하지 마라.

## 6. 실제 반영과 산출물

기존 문서 구조를 우선하며 없으면
docs/research/mes_r1_r5_integration_20260927/을 사용한다.
원본과 통합 설명을 분리하고 관련 index/context에 연결하라.

필수 산출물:
- IMPORT_RECEIPT.json
- R1_R5_SYNTHESIS_KO.md
- CLAIM_LEDGER.json
- CONVENTION_AND_SYMBOL_MAP_KO.md
- THEORY_CODE_MAPPING_KO.md
- SUPERSESSION_AND_CONFLICT_LOG_KO.md
- CLAIM_GATES_AND_NEXT_STEPS_KO.md
- RETURN_HANDOFF_KO.md

Synthesis는 단순 이어붙이기가 아니라
물리 목표 → optical/radiation identity → residual/jet 조건
→ joint feasible set → 관측 식별공간 → reference normalization
→ tensor statistics/likelihood → 해석/claim ceiling의 연결을 설명한다.
Bianchi I 예제는 별도 branch이며 일반 이론의 필수 전제가 아니다.

## 7. 검증과 종료

Hash/manifest, 주장 추적성, convention, 반영 diff를 확인한다.
완료된 CAS나 전체 suite를 intake 때문에 반복하지 마라.
구체적 충돌에만 최소 판별 검산을 적용한다.
Byte identity, semantic consistency, scientific validity를 구별한다.

미확보 R3 raw를 포함한 evidence gap을 보존한다.
실제 data likelihood, physical residual/source budget,
Einstein–matter compatibility, empirical percentage는
원래 근거 범위를 넘겨 완료로 선언하지 않는다.

새 연구루프, production 구현, full numerical suite, commit/push를
자동 시작하지 않는다. 확보된 문서 통합을 완료하고 종료한다.

최종 응답에는 단계별 반영 상태, 계승/정정/중복,
남은 충돌·증거 gap, 변경 파일, 실제 검증,
다음 최소 작업 및 RETURN_HANDOFF_KO.md 경로를 보고하라.
