# I2 독립 과학 decision review

날짜: 2026-09-28. 검토자: `/root/i2_independent_decision`.

**판정: DEFENDED_CONDITIONAL. 필수 수정 없음.** 명시한 massless collisionless Bianchi I 분기의 국소 Einstein–Vlasov 반례족과 same-state 입력에 조건부인 전단 허용집합은 방어된다. 이것은 외부 analytic continuation의 과학 판정이며 repository PROMOTE, CAS4 admission, 관측 inference 또는 일반 finite-tilt 존재 정리의 승인이 아니다.

## 검토 범위와 identity

검토자는 이 후보의 생성, 검증 설계, 원래 Wolfram 실행에 참여하지 않았다. 별도 context에서 공통 지침, I2 계약, 후보 전체, 두 Wolfram code/raw 쌍, 검증 요약, source ledger를 읽었다. I1 `TARGET_RESPONSE_THEORY_KO.md` 전체와 incoming R2 `MES_GENERALIZED_TENSOR_R2_KO.md`의 convention·광학식·weak law·residual 식 (2)–(16)을 대조했다. 기존 fixture를 재실행하거나 scientific Python·evolution을 실행하지 않았다. 추가 reviewer나 review의 review도 사용하지 않았다.

최종 검토 대상은 `PHYSICAL_RESIDUAL_AND_IDENTIFIED_SET_KO.md`, SHA256 **`4976e5785a66616180ed73ccd5e7e3065a5e7bfb6315122649a2dffd025e1d5f`**다. 최초 읽은 SHA256 `81331d18e50c758b67b7d40e61b1dd53e35c61475f03ee29aab4335ebf1b7a51` 이후 §6에 추가된 unit-sphere 검산 설명과 code/raw를 읽고 최종 바이트를 확인했다. 수학적 후보 내용은 동일하며 최종 판정은 위 최종 hash에 적용한다. hash는 identity 증거이지 수학적 정당성 증거가 아니다.

원전도 별도로 읽었다. 버전 접미사가 붙은 PDF URL은 retrieval `DisabledError`였지만, 접미사 없는 URL로 성공했다.

- Rendall, [gr-qc/9505017](https://arxiv.org/pdf/gr-qc/9505017): 반환 PDF는 `gr-qc/9505017v1, 15 May 1995`로 식별된다. §2 식 (2.1)–(2.14), Lemma 2.1, 식 (2.19)–(2.22) 주변의 유한 ODE 설명을 읽었다. 도구 refs: `turn18view0`, `turn20view1`, `turn20view3`.
- Ellis–van Elst, [gr-qc/9812046](https://arxiv.org/pdf/gr-qc/9812046): §8.5.1 식 (283)–(284)와 §8.5.2 식 (291) 주변을 읽었다. 도구 refs: `turn19view1`, `turn20view0`. 이번 반환 자료 자체의 전체 PDF byte identity나 v5 여부를 별도 hash 검증하지 않았다.

이것은 문헌 전수조사나 신규성 심사가 아니다. Ledger의 나머지 optical 문헌은 본 판정의 핵심 근거로 쓰지 않았다.

## 1. Einstein source, 부호와 단위

Rendall은 평균곡률을 `tr k`로 정의하고, Gaussian time에서 metric evolution을 `dot g=-2k`로 쓴다. 후보의 팽창률과는 `k^i_j=-H_i delta^i_j`, `tr k=-3H`로 연결된다. 혼합 지수의 진화식에서는 inverse metric 미분으로 quadratic k 항이 소거된다. 질량 없는 응력의 `tr T=rho`를 적용하면 후보의 `dot H_i=-3H H_i+kappa P_i`가 나온다. Momentum constraint도 radial f의 홀함수 적분 때문에 0이다.

별도 단위 점검에서, 후보의 rho는 질량 밀도가 아닌 J m^-3이고 H_i는 s^-1이다. 따라서 `kappa=8 pi G/c^2`일 때 `kappa rho`와 `kappa P_i`는 s^-2이다. 같은 결과는 trace-free matter에 대해 `R^i_i=(dot H_i+3H H_i)/c^2=(8 pi G/c^4)P_i`로 직접 확인된다. Einstein tensor 계수 `8 pi G/c^4`와 rate 계수를 혼동하지 않았다. Constraint는 `3H^2=kappa rho+||S||_F^2/2`이고 shear scalar와 Frobenius norm의 2배 관계도 일관된다.

Covariant spatial momentum이 보존되므로 `f(t,q)=F(|q|)`는 실제 Vlasov 해 형태다. 물리 momentum으로의 Jacobian은 `(b1 b2 b3)^-1`, energy는 `c sqrt(sum q_i^2/b_i^2)`이며 후보 (3)의 rho·P_i 및 `sum P_i=rho`를 준다. 초기만 isotropic pressure이고 이후 pressure를 rho/3으로 고정하지 않은 점이 중요하다.

근거 상태: 기본 Einstein–Vlasov 식은 **literature-supported**, 해당 단위 adapter와 후보 branch 환원은 **derived**.

## 2. 국소 존재와 초기자료의 충분성

후보의 annulus 조건은 massless momentum 원점의 비매끄러움을 피한다. 임의의 `b_i>0` 초기점 주변에서 b_i가 위아래로 유계인 작은 compact box를 택하면, 고정 q support 위의 `sum q_i^2/b_i^2`는 양의 하한을 가진다. 그러므로 rho·P_i의 모든 b 미분을 적분 안으로 옮길 수 있고, stress 함수는 매끄럽다. 여섯 변수 `(b_i,H_i)`에 대한 벡터장은 국소 Lipschitz여서 각 유한 초기자료에 대해 유일한 국소 해가 존재한다.

문헌의 §2 후반 analytic-coefficient 설명은 명시적으로 m=1에 대한 것이다. 이를 massless 정리라고 그대로 인용하지 않는다. 이번 massless smoothness는 위 annulus 논증으로 직접 방어된다. Lemma 2.1의 전역적 결과도 이 국소 판정에 필요하지 않다.

Constraint 전파를 독립적으로 대조했다. `theta=sum H_i`, `Q=sum H_i^2`라 두면

\[
\dot\theta=-\theta^2+\kappa\rho,\qquad
\dot Q=-2\theta Q+2\kappa\sum_iH_iP_i,\qquad
\dot\rho=-\theta\rho-\sum_iH_iP_i.
\]

따라서 `C=theta^2-Q-2 kappa rho`는 정확히 `dot C=-2 theta C`를 만족한다. 초기 C=0은 보존된다. Reflection symmetry가 off-diagonal stress와 momentum을 제거하므로 나머지 constraint/evolution도 충족한다. 임의 STF 초기 S는 회전으로 대각화할 수 있고 radial F와 초기 g=I는 이 회전 아래 불변이다. 따라서 고정 H·rho에서 norm constraint를 만족하는 모든 STF S에 국소 구성이 적용된다.

근거 상태: **derived**, constraint algebra는 제출된 **exact-symbolic checked** 증거와도 일치. 공통 시간폭, 전역 진화, 관측 과거광추는 증명하지 않는다.

## 3. Brightness, time jet와 no-go

고정 orthonormal 방향 e에서 `q_i=b_i p e_i`, `p=E/c`를 대입하면 `f=F(p sqrt(A))`, `A=sum b_i^2 e_i^2`이다. Energy-density angular integral의 radial 부분은 `integral p^3 F(p sqrt(A)) dp=A^-2 integral q^3 F(q)dq`가 되어 후보 (6)을 준다. 별도 volume factor는 물리 momentum measure 안에 이미 포함되어 있다. 전체 spectral f도 초기 g=I에서는 모든 반례족 구성원에게 같으므로 단지 bolometric 일치에 의존하는 주장이 아니다.

단위구면에서 초기 `dot A=2(H+S:ee)`이므로 `dot B=-4B0(H+S:ee)`이다. 구면 4차 moment의 STF 투영은 `2S/15`이어서

\[
\dot\pi=-4\rho_0\frac{2S}{15}=-\frac{8\rho_0}{15}S.
\]

Geodesic homogeneous nonrotating normal frame에서는 `r2=-dot pi`이므로 `r2=8 rho0 S/15`; I1/R2의 등방 weak law와 부호가 맞다. Collision과 공간미분이 없다는 사실은 time derivative를 0으로 만들지 않는다.

반례족에서 `||S_lambda||^2=6 lambda^2`이며 `3H_lambda^2=kappa rho0+3lambda^2`이다. 또한

\[
H_\lambda-\lambda=\frac{\kappa\rho_0/3}{H_\lambda+\lambda}>0,
\]

이므로 모든 초기 방향 팽창률이 양수다. 각 유한 lambda에 국소 Einstein–Vlasov 해가 있고, 동일한 완전 초기 복사분포에서 dimensional shear가 무한히 커진다. 따라서 **이 선언된 domain에서 정적 복사 snapshot만의 함수인 유한 절대 shear 상한은 불가능**하다.

`||S||/H<sqrt(6)`라는 constraint 상한은 유지되며 반례족이 그 값에 접근한다. Theta 정규화의 한계 `sqrt(2/3)`도 맞다. 결과를 normalized shear의 무한 발산, 고정 H 반례, 공통 source history 반례 또는 실재 CMB 적합성으로 확장하면 안 된다. 후보는 이러한 확장을 명시적으로 배제한다. 원전 (283)–(284)의 derivative 전제와 식 (291)의 quadrupole coupling도 단일 snapshot이 almost-EGS 가정을 충족하지 못한다는 해석을 지지한다.

근거 상태: **derived**, moment 계수와 family constraint는 제출된 **exact-symbolic checked** 증거와 일치; EGS 범위 구분은 **literature-supported**.

## 4. 조건부 identified set과 최소 추가 정보

Constraint가 norm을 고정하고 §2의 임의 초기 S 실현 논증이 충분성을 제공하므로 후보 (11)은 필요조건만이 아니라 **선택한 순간 등방 branch의 정확한 tensor 집합**이다. Positive radius는 5차원 STF 공간의 4-sphere이며 orientation과 eigenvalue shape는 식별되지 않는다. 음의 radicand는 empty, 0은 singleton {0}이다. 모든 방향 팽창을 요구할 때 `HI+S` positive definite 조건을 추가해야 한다는 제한도 옳다.

Uncertain joint D에 대한 union은 H·rho 상관을 보존한다. Rectangle bound는 feasible state가 존재할 때의 외접 bound이며, radicand clipping은 물리적으로 부적합하다. 양의 rectangle radicand만으로 실제 joint D의 비공집합성이 따라오지도 않는다.

최소 정보에 관한 해석도 명확히 한다. 완전 snapshot의 energy calibration으로 rho0가 이미 알려졌다면, **추가적인 독립 유한 H 상한 하나**로 norm의 유한 상계가 닫힌다. rho가 불확실하면 후보의 joint `(H,rho)` 정보로 전파한다. Norm의 유한성 자체에는 양의 rho 하한까지 반드시 필요한 것은 아니며, nonnegative rho와 H 상한만으로도 더 약한 `||S||<=sqrt(6)H+`를 얻는다. 후보 (13)은 양의 rho 하한을 사용할 때의 더 강한 충분 상계이지 정보 최소성의 유일성 정리는 아니다. 이는 후보의 수정이 필요한 오류가 아니라 후속 입력 선택에서 보존할 해석이다.

별도 empirical H 자료를 이번에 취득한 것은 아니다. Same-state·same-congruence 조건과 해당 Bianchi I matter model의 적합성을 확인해야 하며, FLRW posterior를 무검토 이식하거나 radiation equation에서 역산한 jet를 독립 관측처럼 중복 사용하는 것은 허용되지 않는다.

## 5. 제출 검산 감사와 남는 경계

`EXACT_BIANCHI_I_WITNESS.wl`의 일반 STF parameterization, isotropic moment 평균, family/constraint 계산을 raw와 대조했다. 원 raw의 sphere residual `-4 H(e.e-1)`은 단위구면에서만 0이다. 이를 주변공간 항등식으로 승격하지 않는다.

추가 `UNIT_SPHERE_REDUCTION.wl`은 full rational residual의 numerator를 `e.e-1`로 나눠 remainder 0을 산출하고 denominator `(e.e)^3`를 출력했다. 이것으로 구면에서의 동일성이 검산된다. JSON의 `denominator_on_sphere` 값 `"1"`은 code에서 입력한 설명 문자열이며 독립 CAS 평가 출력은 아니다. 다만 실제 denominator가 단위구면에서 1이라는 사실은 즉시 대수적으로 확인되므로 결과의 결함은 아니다. 최초 raw를 보존하고 검산 범위를 구별한 처리도 적절하다.

이 review는 제출 code/raw의 읽기와 독립 수식 대조다. 원격 tool 실행의 암호학적 attestation, Wolfram 재실행 또는 evolution 검증을 새로 했다는 뜻은 아니다.

최종 방어 범위는 **collisionless source closure만으로 snapshot residual이 닫히지 않음을 보이는 국소 물리 반례**와 **독립 expansion/energy 입력에 조건부인 exact 순간 허용집합**이다. 실관측 residual budget, tensor morphology 측정, 보편 MES 정리, 신규성, 일반 finite-tilt Einstein 실현, repository/production admission은 별도이며 기존 gate를 바꾸지 않는다. 모든 material claim 위험이 이 범위에서 해소되었으므로 추가 재검산이나 두 번째 독립 review를 요구하지 않는다.
