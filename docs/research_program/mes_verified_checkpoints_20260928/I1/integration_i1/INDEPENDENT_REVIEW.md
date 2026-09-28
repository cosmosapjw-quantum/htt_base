# I1 외부 이론 후보 독립 결정 검토

2026-09-28. 검토자: 별도 실행 문맥 `/root/i1_independent_review`.

**판정: DEFENDED_CONDITIONAL.** 후보의 식 (1)–(12)와 명시된 양의 비등방 fixture는 선언한 순간 homogeneous branch 및 residual-known 조건 아래 방어된다. 필수 수학 수정은 발견하지 않았다. 이는 외부 분석 결과의 한정 채택이며 repository PROMOTE, CAS4 통과, 실관측 식별 또는 MES 수치 예산 승인이 아니다. Source/jet budget과 empirical 결과의 기존 HOLD는 유지한다.

## 1. 독립성 및 실제 읽은 범위

검토자는 후보 생성, fixture 선택, 검증 설계 및 최초 Wolfram 실행에 참여하지 않았다. 별도 검토 문맥에서 다음 실제 파일을 읽고 기존 항등식과 대조했다.

- `harness/research/PROJECT_INSTRUCTIONS.md`, 템플릿 `state/RESEARCH_STATE.md`, `integration_i1/RESEARCH_CONTRACT.md`.
- 후보 `TARGET_RESPONSE_THEORY_KO.md` 전체.
- R2 `MES_GENERALIZED_TENSOR_R2_KO.md`의 convention, 광학 식, exact weak law와 낮은 모멘트 식 (9)–(14), residual 및 관측 경계. 최초 전체 출력 일부는 잘렸으므로 핵심 §§2–6은 별도로 읽었다. R2 전체 부속 증명이나 원전 문헌 전체를 재검증한 것은 아니다.
- R5 `KINEMATIC_OPERATOR_DERIVATION.md` 전체, 특히 식 (7), (12), (14)–(17).
- `verification/EXACT_RESPONSE.wl`, 실패 전 버전, `WOLFRAM_RAW_V1.json`, `WOLFRAM_DIAGNOSTIC_V1.json`, `WOLFRAM_RAW_V2.json`.
- 검토 중 owner가 제시한 `SPECIAL_FUNCTIONS_TOOL_RESULT.json`. 이는 현재 턴의 기존 응답을 옮긴 기록이며 검토자가 plugin을 독립 실행한 증거가 아니다.

완료된 fixture를 재실행하지 않았다. 추가 CAS, 과학 Python 계산, 진화 solver, 외부 원격 행동 또는 production 파일 변경도 하지 않았다. 독립 검토의 추가 근거는 아래의 재현 가능한 해석 계산이다. Hash는 읽은 문서의 identity만 표시하며 과학적 타당성이나 실행 권한을 인증하지 않는다.

## 2. 핵심 대조와 독립 해석

### 2.1 부호와 STF 정규화

R2와 R5는 모두 derivative-first \(\Omega_{ij}=D_{[i}U_{j]}\), \(\omega_i=\epsilon_{ijk}\Omega_{jk}/2\)를 사용한다. 이때 \(R_\omega v=\omega\times v\)의 행렬은 \(R_\omega=-\Omega\)다. 따라서 R2의 \(V=-P_e(a+\sigma e)-\omega\times e\), weak moment의 \(+\omega\times m\), quadrupole의 \([R_\omega,M]\), R5의 \(+p\times a/2\)는 서로 일관된다. 한쪽 axial convention만 뒤집는 수정은 필요하지 않다.

\(\mathcal C_pz=\tfrac12(pz^T+zp^T)-\tfrac13(p\cdot z)I\)이며 STF \(S\)에 대해 \(\mathcal C_p^*S=Sp\)다. 직접 수축하면

\[
\mathcal C_p^*\mathcal C_p=\frac{|p|^2}{2}I+\frac{pp^T}{6},
\quad \|\mathcal C_p\|_2^2=\frac23|p|^2.
\]

이는 후보 (8), (11), (12)의 정규화와 일치한다. STF의 5좌표에는 Frobenius-orthonormal basis가 필요하며 실제 코드가 그 basis를 사용한다.

### 2.2 정확한 9차원 응답

R2의 \((J_0,J_1,J_2)\)에 \(\omega=w_0+p\times a/2\)를 넣고 \((0,w_0\times m,[R_{w_0},M])\)를 빼면 후보 (4)가 바로 나온다. 알려진 \(w_0\)를 unknown column으로 중복 포함하지 않았고, normalization \(1/(4\rho),3/(4\rho),15/(8\rho)\)가 출력 세 부문에 각각 맞는다. \(\rho>0\), fixed target-frame moments 및 fixed \(p\)에서 이는 \(\mathbb R\oplus\mathbb R^3\oplus\mathrm{STF}_2\) 사이의 명시적인 9×9 선형 사상이다.

등방일 때 \(M=\rho I/3\), \(M_4:S=2\rho S/15\)이므로 \(L_B(S)=8\rho S/15\). 따라서 \(\mathsf A=I_9\)이고 후보 (7)의 계수와 음의 acceleration 보정이 맞다. Scalar residual은 이 등방 target에 필요하지 않다. Singular operator에서 \(\mathsf P_p\ker\mathsf A=0\)는 ambient linear domain의 target 유일성 조건이며, 후보는 physical feasible domain을 별도로 유지하고 있다.

### 2.3 고정 q의 time jet과 누락 dipole 모호성은 서로 다른 변화다

고정 \((C,h,q,p)\)에서 \(b\)만 바꾸면 R5에 의해

\[
\delta X=(p\cdot z/3,z,\mathcal C_pz),\qquad\delta Z=0.
\]

하지만 등방 \(r_2\)를 고정하면서 \(a\)를 바꾸는 모호성은 \(\delta\sigma=0\)이므로 이 고정-q family가 아니다. 후보는 이 차이를 명시했다. 더 강한 독립 witness로 \(r_0\)도 고정해 \(\delta H=0\), \(\delta a=z\), \(\delta\sigma=0\), \(\delta\omega=p\times z/2\)를 택할 수 있다. R5의 deformation matrix를 여기서는 \(D\)로 쓰면

\[
\delta D=\operatorname{skew}(pz^T),\qquad
\delta q=-g^{-1}S\operatorname{sym}(pz^T)S,
\qquad
\delta b=T\{z-(\delta D)^Tp\}.
\]

이 \(\delta q\)는 symmetric이고 R5 inverse를 만족한다. 같은 \((C,h,p)\), 같은 등방 brightness와 같은 \((r_0,r_2)\)를 유지하면서 \(\delta Z=-\mathcal C_pz\) 및 \(\delta r_1=4\rho z/3\)가 된다. 따라서 누락 dipole의 rank-3 target 모호성은 자유 symmetric-q/geometric-jet domain에서 실제로 성립한다. 고정 Einstein–matter 조건, 고정 시간폭 또는 별도 bounded-domain 조건까지 통과한 cosmology family라는 주장은 아니다.

\(p\ne0\)일 때 \(\mathcal C_p\)는 injective이므로 target quotient 차원은 2다. \(p\)를 세 번째 축으로 잡으면 \(S p=0\)인 STF 행렬은 \(S_{xz}=S_{yz}=S_{zz}=0\), \(S_{xx}=-S_{yy}\)인 두 성분이며 후보의 transverse 해석이 맞다. \(p=0\)에서는 \(\mathcal C_p=0\)이므로 projection의 역행렬 표현을 쓰지 않고 전체 5성분을 회복한다. 후보는 이 edge case를 분리했다.

### 2.4 오차 norm과 물리적 정보의 한계

공동 residual 집합의 선형 image인 (10)은 상관을 보존한다. (11)은 triangle inequality에 따른 안전한 상계다. \(\mathsf P_p\mathsf P_p^*=I+\mathcal C_p\mathcal C_p^*\)이므로 \(\|\mathsf P_p\|_2=\sqrt{1+2|p|^2/3}\). \(\|\mathsf A-I\|_2<1\)의 Neumann bound와 합치면 (12)가 성립한다.

이 norm은 수학적 Euclidean/Frobenius 직합 norm이며 데이터 likelihood의 whitening이나 신뢰구간이 아니다. \(B,p,w_0,\rho\)가 변하는 경우 fixed-operator bound만으로 전체 불확실성을 제어할 수 없다는 후보의 제한도 맞다. 실제 source/time/space derivative residual 예산은 제시되지 않았다.

## 3. 실행 증거 감사

실제 코드에서 weak form 직접 적분과 moment formula 조립은 서로 다른 표현이지만 같은 sphere monomial routine을 공유한다. 따라서 완전히 독립된 두 수치 구현이나 독립 CAS 축이라고 부르지 않는다. R2 일반식과의 해석 대조가 코드 공유에 따른 한계를 보완한다.

V2 raw에는 9개 weak-minus-moment residual 0, 등방 identity True, fixture rank 9, 후보 (14)의 exact determinant와 Frobenius norm 제곱, 일반-symbolic \(\mathcal C_p\) norm/Gram residual 0이 실제로 기록되어 있다. 실제 출력 내용을 확인했으며 `isError=false`만으로 성공을 판정하지 않았다.

코드의 `brightness_positive_lower_bound -> 7/10`은 계산한 최소값이 아니라 선언한 값이다. 그러나 별도 해석으로 \(x=e_z\)에 대해

\[
1+x/5+(3x^2-1)/10
=\frac3{10}(x+1/3)^2+\frac{13}{15}
\ge\frac{13}{15}>\frac7{10}
\]

이므로 주장된 positivity는 방어된다. 같은 sphere moments로 \(m=(0,0,1/15)\), \(M=\operatorname{diag}(8/25,8/25,9/25)\)가 되어 V2 행렬의 monopole row와 dipole block 부호·계수를 독립 대조할 수 있다. 여기서는 \(\rho\)를 나눈 normalized moments다. Fixture 하나로 모든 positive anisotropic brightness의 invertibility를 주장할 수 없고 후보도 그렇게 주장하지 않는다.

V1 raw는 `Export::jsonstrictencoding`과 `$Failed`를 포함한다. 실패 전후 코드를 diff한 결과 마지막 `ExportString`의 출력값 string 변환만 달라졌다. V1은 실패로 유지하며 V2 성공이 이를 소급 삭제하지 않는다. 진단은 sphere-average routine의 기본 \(1,1/3\) 값과 expression structure를 확인한다. Special Functions 기록은 요청 정밀도 60과 60개 유효숫자 응답을 보존하며 Wolfram 표시값을 같은 자릿수로 반올림한 값과 일치한다. 이는 scalar normalization 확인에만 해당한다.

## 4. Claim별 판정

| Claim | 판정 | 근거 상태와 한계 |
|---|---|---|
| R5 fixed-q time-jet 불변 target \(Z\) | DEFENDED_CONDITIONAL | derived; R5 (7),(15),(16) 직접 대조. Physical shear와 동일하지 않음 |
| 정확한 normalized 9×9 응답과 offset | DEFENDED_CONDITIONAL | derived; R2 (11)–(13)와 R5 (14) 합성. 지정 fixture raw 감사 |
| 가역일 때 target inverse, singular target criterion | DEFENDED_CONDITIONAL | derived; 선형대수 조건부. Physical feasibility 별도 |
| 등방식, \(r_0\) 불필요성 | DEFENDED_CONDITIONAL | derived; exact fixture raw와 독립 계수 계산 |
| missing dipole의 rank 3 및 quotient 2 | DEFENDED_CONDITIONAL | derived; 가변-q witness 명시. 고정-q no-go로 확대 금지 |
| \(p=0\) 전체 target 회복 | DEFENDED_CONDITIONAL | derived; \(\mathcal C_0=0\). 역 Gram 표현은 사용하지 않음 |
| residual error image와 (11),(12) | DEFENDED_CONDITIONAL | derived; fixed operator의 수학 norm. 확률 보장 아님 |
| 명시 양의 비등방 fixture의 invertibility | DEFENDED_CONDITIONAL | exact-symbolic raw 감사 + positivity 해석 증명. 일반 brightness 정리 아님 |
| V1 실패 및 V2 serialization 수정 | DEFENDED | 원시 응답과 코드 diff로 확인. 물리식 수정 아님 |
| plugin gamma 일치 | DEFENDED_SCOPED | 기존 도구 응답의 transcript 사본 대조. 검토자 독립 실행 아님 |
| 학술적 신규성 또는 새로운 MES 보편정리 | HOLD | 후보도 주장하지 않음; 문헌 전수/신규성 검토 없음 |
| 광학 문헌의 세부 attribution | NOT_REVIEWED | 제공 source subset 밖의 원전은 이번 검토에서 열지 않음. 핵심 대수 판정에 사용하지 않음 |
| 수치 source/jet 예산, 실관측 D/Pi/G 또는 empirical percentage | HOLD | unresolved / not run. 잔차를 아는 조건이 관측을 생성하지 않음 |
| production 구현 및 repository CAS4 admission | NOT_RUN | 등록 assignment/PR/harness 실행 아님. 기존 gate 변경 없음 |

## 5. 필요한 수정과 종료 조건

**필수 수정: 없음.** 처음 지정된 파일들에는 plugin 비교의 별도 응답 기록이 없었으나 검토 중 기존 응답 사본이 추가되어 좁은 실행 주장에 필요한 근거가 확보되었다. 그 증거 수준은 위와 같이 한정한다. 외부 문헌의 세부 attribution이나 논문 신규성은 이번 결정에 포함하지 않는다.

후속 단계에서 유지해야 할 조건은 fixed-q invariance와 varying-q ambiguity의 분리, target-rest-frame bolometric moment 계약, 같은 물리 상태의 joint residual, fixed-operator norm과 statistical uncertainty의 구분이다. 유용한 source/jet budget이 없으므로 관측 interval 또는 MES percentage로 승격하지 않는다. 완료된 fixture를 반복할 필요가 없으며, 본 검토는 이 한정 판정으로 종료한다.

검토 대상 후보 SHA256: `780f659a88ec86a8e86f5656d0a7afe62ec17a33d86470ae9e65218ef9fd74e1`. 전체 evidence identity는 `INDEPENDENT_DECISION.json`에 기록한다.

## 6. 문서 identity 추가 확인 — 인용 locator 정정

2026-09-28. 최초 검토 후 owner가 Heinesen–Korzyński 인용 locator 한 곳을 정확히 `§II–IV,IX`에서 `§II–III,IX`로 정정했다. 현재 후보 SHA256은 `666db799914911ba5824d6dd46e4ae01296106e67c1c4c7a433d846a2786d161`이다. 현재 바이트에서 새 locator의 출현은 정확히 1회이며 이를 이전 locator로 역치환한 바이트의 SHA256은 최초 검토 hash `780f659a88ec86a8e86f5656d0a7afe62ec17a33d86470ae9e65218ef9fd74e1`와 일치한다.

따라서 이 변경은 인용 절 번호 metadata 정정만이며 수식·가정·조건·판정의 변경이 없음을 확인했다. 최초 검토 identity를 보존하고 현재 identity에도 같은 `DEFENDED_CONDITIONAL` 판정을 적용한다. 전체 수학 검토나 fixture 실행은 반복하지 않았으며, 해당 외부 문헌의 세부 attribution 자체는 기존처럼 `NOT_REVIEWED`다. 기존 CAS4/production `NOT_RUN` 및 source/empirical `HOLD`도 유지한다.
