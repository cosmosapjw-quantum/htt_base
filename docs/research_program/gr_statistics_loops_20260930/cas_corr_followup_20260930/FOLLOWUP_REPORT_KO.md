# GRSTAT 정정 반환 수용과 C04 보편 인증 보완

기준 반환: `GRSTAT-CAS-CORR-20260930-1420KST`.
기준 게시 커밋: `11602167b64e4f0c50c1f57c37fe9df2292f9725`.
근거 상태: 반환 원본·검사 소스·실행 로그 대조, 직접 수학적 유도, 실행 준비 코드. 여기서 새로운 네 축 CAS 실행은 수행하지 않았다.

## 이번에 닫은 범위

| 대상 | 결정 | 유지하는 한계 |
|---|---|---|
| CAS-03 정의역 정정 | 수용. 가역 D의 정확한 선형 역관계에 H_D=0을 허용하고 절단식만 H_D≠0으로 제한한 것이 맞다. | 반환의 Wolfram 검사는 일부 대각 성분, SymPy는 일반 행렬 항등식과 controls이다. 전체 CAS-03, C01의 Lorentz fibre, 물리적 잔여항은 열려 있다. |
| CAS-03-C02 구현 | 수용. 실제 소스가 spacelike r_chi와 B u=0, timelike-dyad negative control을 검사한다. | 관측에서 geodesicity를 검출했다는 뜻은 아니다. |
| CAS-11 실행 오류 | 원인 재현과 해당 수정 경로 수용. 자기참조 정의는 clean kernel에서 재귀를 일으키고 분리 symbol은 정상이다. | 고정 차원 진단을 임의 차원 Bregman/Gram 정리의 증명으로 인정하지 않는다. |
| CAS-13-C04 | Wolfram의 보편 실수 양화 검사와 Lean의 형식증명이 정확한 원자 명제에 정렬됨을 확인했다. | 현재 SymPy/Sage는 일부 항등식만 검사하므로 기존 aggregate CAS_CONFLICT를 보존한다. |
| 런타임 | 비고정 Lean probe의 timeout과 고정 toolchain의 성공을 구분한 반환 기록을 수용한다. | 비고정 probe 실패를 Lean 전체의 불능으로 해석하지 않는다. |

새 계약 11개와 축 소스 14개, 합계 25개를 다운로드하여 반환에 연결된 해시와 모두 대조했다. 추가로 선택한 원시 기록 11개의 해시도 맞았다. C04 adjudication은 runner stdout과 바이트가 같고, 계약 SHA-256 `0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`에 연결된다. 전체 과거 466개 파일은 이번에 반복 다운로드하지 않았다.

등록된 로컬 독립 reviewer의 `NO_SUPPORTED_WORKER_WITHIN_DECLARED_COST_SCOPE`는 아직 남아 있다. 이번 대화의 별도 읽기 검토는 `CORRECTION_RETURN_REVIEW.md`에 보존하지만 이를 로컬 등록 검토 완료로 대체하지 않는다. 기존 scientific conditional/HOLD, 관측 fit 없음, novelty·Bianchi 판정 비승격을 유지한다.

## CAS-13-C04의 남은 증명은 추가 가정 없이 완결된다

실수 \(0<L\le U\), \(x\in[L,U]\)를 가정하고
\[
s=L+U>0,\quad d=U-L\ge0,\quad
t_*={2LU\over s},\quad e_*={d\over s},\quad
\rho_*(x)={t_*-x\over x}
\]
라 두자. \(L,U,x,t_*\)는 같은 단위이고, \(e_*\)와 \(\rho_*\)는 무차원이다.

### 전 구간 상계

\[
e_*-\rho_*(x)={2U(x-L)\over sx}\ge0,
\qquad
e_*+\rho_*(x)={2L(U-x)\over sx}\ge0.
\]
분모 \(sx\)는 양수이고, 각 분자는 구간 조건에서 비음수다. 따라서 모든 \(x\in[L,U]\)에서 \(|\rho_*(x)|\le e_*\)이다. 끝점에서는 각각 \(\rho_*(L)=e_*\), \(\rho_*(U)=-e_*\)이므로 상계가 달성된다.

### 모든 실수 경쟁자에 대한 하계

임의의 \(a\in\mathbb R\)에 대해
\[
r=\max\left(\left|{a-L\over L}\right|,\left|{a-U\over U}\right|\right)
\]
로 정의하면, 절댓값과 최댓값의 정의에서
\[
Lr-a+L\ge0,\qquad Ur+a-U\ge0.
\]
두 부등식을 더하면
\[
(L+U)r-(U-L)=(Lr-a+L)+(Ur+a-U)\ge0,
\]
따라서 \(r\ge e_*\)이다. 경쟁자 \(a\)의 양성은 가정하지 않았다. 또한 \(U-L\)로 나누지 않으므로 \(L=U>0\)도 그대로 포함된다.

이로써 원자 계약의 세 목표가 직접 유도로 닫힌다. 새로운 발견 또는 새 Lean 실행으로 표기하지 않는다. 보존된 형식증명과 같은 정리를 SymPy·Sage가 확인할 수 있는 유한 대수·부호 인증으로 표현한 것이다.

## 이번에 준비한 최소 실행 보완

`c04_sympy_certificate.py`와 `c04_sage_certificate.py`는 각각 계약 진술만 받은 별도 작성자에게 맡긴 프로그램이다. 두 작성자는 상대 소스·결과 또는 위 공통 유도문을 읽지 않고 작성했다. 동일 모델 계열일 수 있으므로 모델 다양성이나 강한 통계적 독립성은 주장하지 않는다. 통합 검토자는 완료된 두 소스를 읽는다.

코드는 원자 계약의 정확한 SHA-256을 요구하고, 전 구간의 부호·양의 분모·절댓값/최댓값 연결까지 검사하도록 작성한다. 항등식 몇 개가 0이라는 이유만으로 전체 명제를 true로 만들지 않는다. 인증 규칙의 건전성과 명제 연결은 명시된 신뢰 경계이며, 이는 Lean kernel 검증과 다른 종류의 증거다.

현재 대화 환경의 Python에는 SymPy/Sage가 없고 Sage·Wolfram·Lean 실행 파일도 확인되지 않았다. 의존성 설치나 로컬 CAS 재실행은 하지 않는다. 실제 시행 여부와 준비 코드의 검사 범위는 `FOLLOWUP_STATUS.json`에 기록한다. 새 코드의 실행 결과를 미리 PASS로 기록하지 않는다.

두 소스의 구문 검사, 잘못된 계약 거절, 엔진 부재 시 오류 반환 등 6개 준비 검사는 통과했다. 이것은 수학적 인증 실행이 아니다. 통합 과정에서 SymPy의 실패 처리를 수정하여 인증 거절과 예외 모두 stdout의 과학 Boolean 없이 비영 종료하도록 했다. 최종 SymPy 소스는 이 source-informed 수정까지 포함한다. 새 소스 읽기 검토는 `NEW_C04_SOURCE_REVIEW.md`, 준비 검사 기록은 `PREPARATION_CHECKS.json`에 있다.

## 다음 로컬 실행의 종료 조건

1. 원자 C04 계약과 소스 해시를 확인하고 새 run 디렉터리에 두 보완 소스를 배치한다. 기존 run과 raw conflict는 그대로 둔다.
2. 두 소스의 자체 반례·변조 거절 검사를 먼저 실행한다. 잘못된 부호, 잘못된 후보, 비양의 분모를 수용하는 코드이면 여기서 수정한다.
3. C04 한 건을 기존 runner로 새로 관측한다. 집계가 네 축의 현재 실행을 요구하므로 Wolfram·Lean도 이 작은 원자 명제만 실행하고, 과거 stdout을 새 결과로 복사하지 않는다.
4. 명제 범위·인증 규칙을 검토한 뒤 실제 aggregate를 기록한다. 독립 reviewer admission은 별도 상태로 유지한다. 네 엔진 일치만으로 관측 적용이나 전체 CAS-13을 승격하지 않는다.
5. C04가 이 범위에서 닫히면 반복 검증을 끝내고 일반 유한 Gram 정리(CAS-11) 또는 CAS-03의 물리적 잔여항으로 이동한다. 다른 17개를 다시 돌리지 않는다.

세 수학 인터페이스 중 양의 구간 minimax가 가장 먼저 구현으로 이어질 수 있다. 다만 참인 구간을 입력받는다는 조건과 부동소수점 구현을 분리해야 한다. 수학적 후보식만으로 관측 구간 포함·coverage·likelihood를 얻지 않는다. 나머지 두 인터페이스는 기존 입력 명세를 유지하며 gap, range 조건과 관측 오차를 별도로 다룬다.

## 후속 연구에 필요한 입력

반환의 `NEXT_INPUT_AUDIT.json`에 따라 아래 정의를 먼저 완성한다. 도출할 결과를 입력 가정에 넣지 않는다.

| 대상 | 실행 전에 필요한 입력 |
|---|---|
| CAS-08 | 전체 feasible set, geodesic null set, 네 결과 집합의 논리적 정의, 임계값 등호 포함 여부 |
| CAS-09 | 양쪽 공간의 기저, mass-shell intercept chart와 부호, Ndir·zeta·zeta0의 정의와 차원, 전체 native mean, unisolvent point 규약 |
| CAS-15 | E·I·DI·T2·C2·M, 각도 측도와 horizontal derivative, H의 frame 의미, CAS-01 normalized jet을 허용 입력으로 연결하는 출처 |
| CAS-16 | 차수 계산에 쓸 실제 integrand, L·L_C·L_T의 정의역, CAS-15 weak integrand의 허용 입력 연결 |
| CAS-17 | 두 congruence, null tangent rescaling, affine parameter·면적 정규화, source/observer 끝점, A prime·h의 지표 위치, 전체 native-offset mean |

CAS-11의 continuum Hessian/Taylor/integrability, CAS-03의 물리적 잔여항과 관측 D의 정확성은 미완료 해석적 증명 의무다. 이들은 프로그램을 다시 실행하는 것만으로 채워지지 않는다. 세 인터페이스는 여전히 `SPECIFIED_NOT_IMPLEMENTED`이며, 이번 인증 프로그램을 관측용 구현으로 취급하지 않는다.
