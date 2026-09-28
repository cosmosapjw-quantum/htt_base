# MES R5 독립 decision review

작성일: 2026-09-27 KST. Reviewer: `/root/r5_independent_review`.

**최종 판정: `PROMOTE_CONDITIONAL_THEORY`.** 아래 두 minor 정합성 수정이 반영됐음을 확인했다. 실관측 interval/percentage는 **`HOLD / UNRESOLVED`**다. 이 판정은 명시한 homogeneous 기하와 retained radiation algebra의 다음 이론 단계에 한정된다. Einstein–matter 적합성, 일반 비선형 MES, 자료 기반 제약으로 확대하지 않는다.

## 1. 독립성과 검토 범위

이 reviewer는 후보 생성, 검증 설계, Wolfram 코드 작성과 실행에 참여하지 않았다. 새 subagent context에서 고정 원고, 일반 유도, 실제 `.wl` 코드와 저장된 원시 출력, 등록 기록을 읽고 수식과 claim–evidence 대응을 검토했다. 새 과학 후보, 추가 CAS, 광범위 문헌 탐색을 만들지 않았다. 수정 확인은 같은 bounded review에 포함하며 리뷰의 리뷰는 요구하지 않는다.

적용 지침은 `harness/PROJECT_INSTRUCTIONS.md`, `harness/docs/MODEL_ROUTING.md`, `harness/prompts/phases/08_external_decision_gate.md`다. 모델 identity/ultra 설정을 독립 인증하지 않는다.

검토한 원본의 identity:

| 파일 | SHA-256 |
|---|---|
| `REPORT_CANDIDATE_V1_FROZEN.md` | `64748d9534e9e17f5f1815aabf61e2de01239737f24fdd46effc96947b9c9488` |
| `PREREGISTRATION.json` | `ea5b5ecff0ec988b54b71ddcd781c3baa5935c11e7f9ce2b99d5ddbf5688b3e4` |
| `verification/CAS_KINEMATIC_AFFINE.wl` | `cf803b96af7e9451622858c2045b2dac20fb18d698f6bca06c00debec936a1c1` |
| `verification/CAS_KINEMATIC_AFFINE_RAW_V1.json` | `7a0e4852a604e686910bcf550a66b4239b57b4bc1532651fe58b32e583b8435b` |
| `verification/CAS_RADIATION_AND_JOINT_DISK.wl` | `caf18eb6d6853d83a8fa3ad650df7ddda9d9a7b54f26ffffc68f91dc17bc4a55` |
| `verification/CAS_RADIATION_AND_JOINT_DISK_RAW.json` | `d396cb305f09773c9e28df8a3bf8702aa20f34c9ee5e268e1cdec22db668cd72` |
| `KINEMATIC_OPERATOR_DERIVATION.md` (minor 수정 후) | `be873a5a6f310154d431a7f502af1d24548664cd4afc2419c3389627a46d9360` |
| `REGISTRATION_CHRONOLOGY.json` | `9d52929a0ef049852155f9046f51a328f01d7d490fe80217367dd14a7ab3501c` |

추가로 `KINEMATIC_OPERATOR_DERIVATION.md`, `sources/LITERATURE_AND_REGIME_AUDIT.md`, R4의 전체 독립 판정을 읽었다. 원 논문의 원문 화면을 reviewer가 별도로 재취득한 것은 아니다. 문헌 감사의 사용 범위와 내부 부호 불일치가 채택 정리에 영향을 주는지 검토했다. Hash는 고정 입력 identity이며 과학적 타당성이나 실행 provenance 자체의 증명은 아니다.

## 2. Exact affine 기하 — PROMOTE

Geodesic normal/Fermi triad, spatially homogeneous tilt, canonical proper boost, derivative-first vorticity라는 계약하에서 rest gradient와 acceleration 식은 정확하다. Metric compatibility가 주는 `Lp=0`, `Sp=gp`, `Wp=p/g`를 사용하면 본문 Eqs. (3)–(4)가 일치한다.

역산

\[
q=g^{-1}S(B-pa^T)S-L,\qquad b=W(a-B^Tp)
\]

은 원 입력을 유일하게 복원한다. `(B,a)`와 `(Θ,σ,ω,a)` 사이 extraction도 가역이므로 12×9 map의 rank는 모든 `|p|<1`에서 정확히 9다. 이는 실제 관측응답의 식별 rank가 아니다.

Antisymmetric slot의 convention을 유지하면 `L_[ij]=−cf^k_ij p_k/2`이고 congruence 변환의 axial identity에서

\[
\omega-\frac12p\times a=Sw_C
\]

가 나온다. 부호와 1/2 계수는 일치한다. `q=q^T`의 세 조건과 동치이며 inverse 때문에 이외의 숨은 선형 제약은 없다. `p=0`에서 `B=q,a=b,ω=0`인 극한도 맞다.

실제 kinematic CAS는 비가환 하나의 Lie algebra에서 두 nonzero tilt와 zero tilt를 검사했다. 모든 q의 대칭 6성분과 b의 3성분은 symbolic이다. 직접 4D tetrad projection, 부호·역산·trace·ray 항등식이 참이고 rank/left nullity는 각각 9/3이다. 일반성을 이 세 fixture에서 추정하지 않고 analytic inverse에 둔 증거 배분은 적절하다.

자유 b의 image는 `δa=z, δB=pz^T`이므로 본문 Eq. (10)의 세 결합량이 b-free인 것도 정확하다. p≠0에서 가속도와 전단에 무제한 방향이 남고, 와도는 p에 수직한 두 방향만 변한다. 한 사건 근방의 국소 기하 실현과 Einstein–matter 적합성/고정 시간구간 budget을 구별한 제한도 유지돼 있다.

## 3. 부분 target과 radiation jet — PROMOTE, stated domains only

`J=J0+N`, J0 nonempty compact, N unconstrained linear subspace인 domain에서는 `P A N={0}`이 target boundedness의 필요충분 조건이다. 필요성은 허용된 선형 ray, 충분성은 compact image에서 직접 따른다. 일반 nonconvex set의 recession cone만으로 확장하지 않은 점은 중요하다. 원고는 infeasible empty set를 강한 bound로 해석하지 않는다. Companion에도 nonempty 조건의 동기화를 확인했다.

Frame connection 변환은 미분된 boost와 원 연결을 모두 포함한다. Homogeneous rest-tensor 성분에 대해 `e'_0(t)=gE0(t)`, `e'_i(t)=gp_iE0(t)`이며 각 covariant slot에 연결을 빼므로 본문 Eq. (13)의 time/spatial adapter는 맞다. Normal spatial homogeneity를 rest-space spatial derivative가 0이라는 말로 바꾸지 않았다. 이 부분은 정의에서의 직접 유도이며 별도의 모든 성분 CAS를 실행한 것으로 보고하지 않는다.

Retained R3 radiation 식에 그 adapter를 대입하면 자유 coefficient time jets `(v1,v2)`의 block이

\[
F_{12}(x,Y)=(x+2Yp/5,\;Y+\operatorname{STF}(px^T))
\]

이다. STF 수축은 `STF(px^T)p=p²x/2+(p·x)p/6`이므로 Schur complement는 `(1−p²/5)I−pp^T/15`. 고유값, determinant, `|p|<1`에서의 가역성은 모두 정확하다. 저장된 symbolic CAS의 residual 0과 finite fixture rank 8도 이 증명을 뒷받침한다.

따라서 두 coefficient jets가 전공간에서 자유로운 **retained algebraic model**에서는 그 8개 식이 kinematics에 추가 제약을 주지 않는다는 결론이 맞다. Signed source 8성분이 자유로운 경우도 동일하다. Positivity, weak-regime, finite-time observation, matter constraints가 실제 domain을 제한하면 이 no-additional-constraint 결론의 전제가 달라진다. 원고가 finite-tilt adapter를 exact nonlinear radiation law로 격상시키지 않고 remainder/domain gate를 유지하므로 물리적 과장은 없다.

Quotient nuisance 소거는 자유 nuisance가 linear image라는 계약하에서 맞다. 모든 jet norm을 개별 제한하는 것보다 target에 전달되는 조합을 제한하면 충분할 수 있다는 설명은 기존 원래 동기를 보존하며, 자기 식으로 역산한 jet를 독립 데이터로 재사용하는 순환도 명시적으로 차단한다.

## 4. 공동 원판, reference, 통계 carrier — PROMOTE as sensitivity fixture

Class B Lie bracket, `p=(0,3/5,0)`의 q, b, B와 와도 offset은 서로 일치한다. q는 대칭이며 `gW(q+L)W=H_*I+Ω0`이다. 동일 `(x,z)`가 a,σ,ω를 함께 결정하므로 세 독립 norm-ball을 섞은 계산이 아니다. Θ와 β는 고정된 joint-state 성분으로 남는다.

선언한 sector radii와 equal-block `1/√3` convention에서 J의 두 열은 정규직교한다. Full shear matrix의 Frobenius 내적이 off-diagonal 성분을 두 번 세는 것도 코드에 반영됐다. `F=x²+z²`, disk support, `D=[0,100]`은 이 sensitivity reference의 정리이며 관측 percentage가 아니다. 비영 와도 기준 w0에 대한 displacement임을 숨기지 않았고, reference 선택을 보편 MES ceiling으로 제시하지 않는다.

Uniform area law라는 추가 계약하에서 반지름 제곱은 [0,1]에서 균등하고 각도 projector의 평균은 `JJ^T/2`다. 따라서 `Π_tail=(1−q0)JJ^T/2`와 trace `1−q0`가 정확하다. 확률법칙 없는 deterministic set에서 Π를 만들지 않는다. `F=0` branch와 cutoff endpoints도 처리한다.

같은 frame/reference의 identity transport에서 G의 outer product와 Hilbert norm 비율은 정확하다. 분모 상태가 0이면 정의하지 않고 다른 redshift의 물리적 transport를 요구한다. Signed T를 보존하여 Q의 global-sign 소실을 보완한다.

## 5. 발견 사항과 등록/실행 구분

- **Critical: 0.** 채택된 일반 정리나 계산을 무효화하는 문제를 찾지 못했다.
- **Major: 0.** 근사영역 및 empirical claim ceiling이 원고에 충분히 명시돼 있다.
- **Minor M1 — resolved:** Companion §6의 compact J0가 nonempty라는 조건 누락. Main §3.1은 이미 정확했다. 빈 J0이면 target image는 empty/bounded이지만 `P A N≠0`일 수 있으므로 companion에도 조건을 추가했다. 수정된 문장을 직접 확인했다.
- **Minor M2 — resolved:** `PREREGISTRATION.json`의 총괄 registration_type은 일부 선행 검산이 있었다는 예외를 자체적으로 표현하지 않았다. 원 기록의 동일 hash와 `REGISTRATION_CHRONOLOGY.json`을 직접 확인했다. Kinematic CAS는 BEFORE, radiation/disk는 AFTER이며 동일 코드의 raw-capture 재실행은 두 번째 독립 replication으로 세지 않는다. Main §9와 companion도 이 순서를 구분한다.

Kinematic 검산의 일반 Lorentz-factor 중간 설명 누락은 boxed inverse나 실제 코드의 오류가 아니라 수정된 문서 중간식 오류로 기록돼 있다. Radiation/disk의 동일 코드 재실행은 raw 보존을 위한 것이며 독립 검산 횟수를 늘린 것으로 세지 않는다. 새 CAS나 기준 변경은 이 reviewer가 요구하지 않는다.

문헌 Eq. (71)의 국소 부호 불일치와 신규 exact quadrupole/finite-electron Thomson 후보는 채택 theorem의 근거가 아니다. 해당 미검증 후보에 관한 판정은 **HOLD**이며, 이번 리뷰가 그 후보를 승인한 것으로 재사용하면 안 된다. 원 논문 전체의 정오나 공식 erratum 존재도 이 리뷰의 판단 대상이 아니다.

## 6. 승격 범위와 종료

승격 대상은 정확 homogeneous affine 기하, compact-plus-free-subspace target 정리, retained radiation의 time-jet rank, 선언된 joint disk와 통계 carrier의 계산이다. 일반 선형대수/boost 기법 자체의 신규성을 주장하지 않으며, 연구 기여는 현재 추론 문제에 맞춘 명시적 operator와 가정 계약이다. 이 결과를 다음 bounded 이론/관측응답 연구의 입력으로 사용할 수 있다.

실제 selected data와 joint likelihood, time/source/remainder의 물리적 bound, frame/거리/transport 계약, premise-matched MES denominator는 여전히 미완료다. 실제 우주의 interval 또는 percentage를 보고할 empirical gate는 HOLD다. 새 exact radiation closure, 전체 hierarchy evolution closure, Einstein–matter admissibility, 보편 비선형 MES 정리는 이번 승격에 포함되지 않는다.

두 minor 수정이 닫혔으므로 이 decision review를 종료한다. 추가 reviewer나 동일 CAS 반복을 요구하지 않는다. Open critical/major/minor issue는 0개다.
