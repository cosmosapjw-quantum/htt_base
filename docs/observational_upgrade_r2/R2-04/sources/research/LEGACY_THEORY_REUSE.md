# R2: 오래된 이론을 관측 연산자로 재사용하는 설계와 새 유도

기준: 첨부 `bianchi_defect_overleaf.zip`의 실제 TeX 원문과 `HTT.zip`의 실제 Python을 읽었다. 사용자의 이번 요청에 따라 상위 수학 정리는 **ASSUMED_VALID_FOR_THIS_LOOP**로 사용한다. 이는 이전 검증 기록이나 과거 관측 posterior를 새로 승인한다는 뜻이 아니다. 이번 산출물은 관측 likelihood, 계산 가속, 정확한 함수 변환을 한 단계 진전시킨다.

가장 큰 재사용 기회는 다음과 같다. 과거의 defect·MES·tilt·Teff·거리 의존성 연구를 버릴 필요가 없다. 하나의 공동 잠재변수 모형에서 관측을 적합하고, 같은 표본에 이 함수들을 계산하면 된다. 기존 scalar channel들을 독립 관측으로 다시 곱할 필요가 없으며, 기존 plotting·weighted posterior·시나리오 비교 코드를 downstream에서 그대로 활용할 수 있다. 추가로 Teff의 200×200 구적을 8개 방향 계수의 정확한 회전 불변 다항식으로 대체했다.

## 원문에서 실제 회수한 내용

아래 TeX 경로는 `sources/bianchi_defect_overleaf/overleaf/` 상대경로, Python은 `sources/HTT/HTT/` 상대경로다.

| 재사용 대상 | 실제 원문 label / 구현 | 이번 분석에서 맡길 역할 |
|---|---|---|
| 표준화된 shear·vorticity·acceleration | `chapters/ch02_framework.tex`: `def:std-vars`, `eq:Sigstd-def`, `eq:Wstd-def`, `eq:Astd-def`; `macros.tex` | 차원 있는 국소 팽창/전단 추정량을 무차원 defect 좌표로 변환 |
| 비교 FLRW와 signed defect | 같은 파일 `eq:comparator-policies`, `eq:defect-def`, `thm:master-defect-id`, `eq:master-identity` | 비교자별 signed posterior를 별도 출력; curvature와 tilt를 shear로 잘못 읽지 않음 |
| MES 세 bound | `chapters/ch03_bianchi_bounds.tex`: `thm:MES-shear`, `eq:Bsig-def`, `eq:Bom-def`, `eq:Bud-def`, `eq:Sig2-from-Bsig`; `htt/bounds.py` | 잠재 intrinsic multipole의 함수로 bound를 계산; 가정 성립 구역에서 물리 feasible set 또는 posterior 진단에 사용 |
| 저다중극 수송 | 같은 파일 `eq:ell0`–`eq:ell3`; `chapters/ch05_teff.tex`: `eq:MDE-general-teff`, `sec:ell-coupling` | 최신 native transport의 소스/프레임/출력 계수를 해석하고 reusable response basis를 정하는 구조 |
| 세 단계 pushforward | `chapters/ch02_framework.tex`: `eq:xi-pushforward`, `eq:Q-def`, `eq:Pi-def`; `appendices/appendix_F_pushforward.tex`: `eq:app-pushforward`; `htt/departure_posteriors.py` | 공동 posterior에서 x, Q, exceedance 및 각 성분을 계산 |
| filling fraction | `chapters/ch07_results.tex`: `eq:FF-def`; `htt/bounds.py:filling_fraction` | 고정 old number를 새 관측량으로 쓰지 않고 동일 조건의 samplewise ratio로 다시 계산 |
| Teff 방향 ansatz와 variance | `chapters/ch05_teff.tex`: `eq:Theta-def`, `eq:Theta-expansion`, `eq:Sigma2-def`; `htt/teff_extended.py:TeffMomentMap.theta_field`, `.moment`, `.sigma2_analytic` | 기존 함수 입력을 arbitrary-axis dipole+STF quadrupole로 확장; 정확한 full-sky moment로 가속 |
| finite boost/모드 혼합 | `htt/teff_extended.py:EllMixingMatrix.boost_mixing`; 원문 `sec:boost-mix` | observer boost를 forward operator에 한 번만 적용; intrinsic/kinematic dipole와 quadrupole 누출 공동 전파 |
| Bianchi V momentum 연결 | `chapters/ch03_bianchi_bounds.tex`: `eq:BV-momentum-DCP`, `eq:BV-Sig2-exact`; `appendices/appendix_C_DCP_derivations.tex`: `eq:app-DCP-mom`; `htt/bounds.py:Sig2_BV` | type parameterization의 대수 제약으로 사용; 특정 curvature/transfer 숫자에 의존한 과거 exclusion은 새 데이터 결론으로 재사용하지 않음 |
| VIIh LRS shear–vorticity 연결 | `chapters/ch03_bianchi_bounds.tex`: `eq:WS-coupling` | 해당 sector/frame에서만 W²=R_WS² Sigma²를 대입하여 차원 축소; 일반 Bianchi나 다른 mode로 자동 확장하지 않음 |
| 다유체 tilt density | `chapters/ch02_sec8_multi_fluid.tex`: `eq:Otilt-multi`; `ch02_sec7_tilted_kinematics.tex`: `eq:Otilt-total` | CF4 tracer velocity·baryon·CDM·radiation tilt의 동일성 여부를 명시한 다유체 posterior 출력 |
| q/H의 거리 의존성 | `chapters/ch08_sec83_tsagas_expanded.tex`: `eq:disc-Dq`, `eq:disc-dH`, `eq:disc-H-dir`, `eq:disc-q-decomp`; `htt/tilted_flrw.py:Delta_q`, `tilted_H_perturbative`, `Delta_q_three_term` | d^-3, d^-1, host-age response를 실제 survey window에 통과시킨 비교 모형으로 사용 |
| 향후 예측 P8–P11 | `chapters/ch09_tilted_predictions.tex` | redshift/방향/host-property별 잔차 플롯의 물리적 비교축으로 사용; 예전 forecast 유의도·날짜는 이 연구의 실측 결과가 아님 |

## 1. 공동 잠재변수와 관측량의 연결

다음 좌표를 별도로 보존한다.

\[
\psi=\{H(z),q(z),\sigma_{ab}(z),\omega_{ab}(z),a^a(z),
\rho_s(z),\widehat v_s(z),\Omega_s,\Omega_k,
\text{type, mode, initial data, observer boost, calibration}\}.
\]

여기서 tilt rapidity를 \(\rho_s\), speed fraction을 \(b_s=\tanh\rho_s\), 속도를 \(v_s=c b_s\)로 따로 저장한다. 첨부 원문은 `beta`를 rapidity와 speed fraction 양쪽에 사용한다. 명시적 adapter가 있어야 `sinh(beta)`와 `1/sqrt(1-beta²)`에 같은 수를 실수로 넣지 않는다. 차이는 작은 tilt에서 작아도 정의는 정확히 구분한다.

공동 자료모형은 블록 관측 벡터 \(y\)와 하나의 forward map \(F\)이다.

\[
y=F(\psi,\eta)+r+\epsilon,
\qquad \epsilon\sim N(0,C),\quad r\in\mathcal B.
\]

Gaussian 블록은 그것이 실제 제품 likelihood인 경우에만 사용한다. CF4 원 거리 modulus·선택 함수 모형이나 저계수 Poisson count는 고유 likelihood를 유지할 수 있다. 공동 covariance 또는 공유 latent 변수로 자료 간 상관을 표현한다.

| 자료 | 관측 operator | 재사용되는 이론 | 직접 출력 |
|---|---|---|---|
| CF4 원 modulus·redshift·방향·group 정보 | latent d_L 및 z의 likelihood, d_A=d_L/(1+z_true)^2, endpoint cosmography | 13-column 최신 모형과 legacy tilt/q/H 해석 | 반경별 B,H,A,STF shear, covariance, calibration/selection 의존성 |
| CMB 지도·polarization·response | native type/history → intrinsic a_lm → finite observer boost → beam/mask/channel response | 저다중극 transport, Teff moments, MES | intrinsic multipole, common-sky contrast, tensor invariants, defect/MES 공동 pushforward |
| DESI clustering + window + covariance | theory multipoles → 제공 window → data vector | 배경/curvature와 방향별 확장 비교 | AP/RSD/background likelihood, CF4/CMB와 공유하는 H·curvature 제약 |
| DESI directional counts | random/selection response와 Poisson 또는 검증된 count covariance | dipole 해석과 nuisance template 분리 | tracer/redshift별 dipole 및 survey systematic 분리 |
| Union3 spline posterior | 원 likelihood 또는 올바른 prior 제거/재구성이 있을 때 background 모듈 | q/H 배경 비교 | 거리–redshift baseline. 개별 SN의 방향 적합은 이 NPZ만으로 생성하지 않음 |

MES bound는 같은 CMB 자료에서 얻은 intrinsic multipole의 deterministic 함수다. 원 CMB likelihood와 함께 별도 독립 Gaussian 관측으로 추가하면 같은 정보를 재사용한다. 물리 가정에 따른 제약 또는 downstream diagnostic 중 어느 역할인지 명시한다.

### Defect pushforward

사용자 가정 아래 상위 master identity를 다음과 같이 적용한다.

\[
x=\Sigma^2_{\rm std}-W^2_{\rm std}
  +\sum_s(1+w_s)\Omega_s\sinh^2\rho_s
  +(\Omega_k-\Omega_{k,ref}).
\]

예컨대 국소 rate tensor \(\sigma_{ab}\)가 s^-1이고 \(H\)도 s^-1이면 \(\Sigma^2_{\rm std}=\sigma:\sigma/(6H^2)\)이다. 물리 가속도 \(a\)가 m/s²인 convention에서는 dimensionless 가속도는 \(a^2/(6c^2 H^2)\)다. 원문 `c=1` 표기의 복원은 clock와 4-velocity 정규화를 함께 기록한다. 전체 signature는 (-,+,+,+)를 유지한다.

\[
B_\sigma(\psi)=\tfrac53\epsilon_1(\psi)+3\epsilon_2(\psi)+\tfrac37\epsilon_3(\psi),
\qquad Q(\psi)=\frac{x(\psi)}{(3/2)B_\sigma(\psi)^2}.
\]

정의된 비교자에서 음수 x,Q를 그대로 보존한다. denominator 0 또는 해당 가정 밖의 posterior mass를 자동 삭제·재정규화하지 않는다. 유효 구역 D의 알려진 초과질량 \(p_>=P(D\cap\{Q>q_*\})\), 미정의 질량 \(m_0=P(D^c)\)에 대해 미정의 event의 가능한 completion에 대한 outer interval은 \([p_>,p_>+m_0]\)로 출력할 수 있다. 전 영역의 물리적 초과확률로 해석할 때는 completion 모형을 명시한다. `Q|D`를 별도로 보고하려면 조건부 결과임을 명시한다. 고정 분모의 과거 그림과 비교할 때 동일 denominator mode도 별도로 제공한다.

\(3B_\sigma^2/2\)는 정의상 shear ceiling이다. 다른 양의 tilt/curvature 성분을 더한 전체 x의 절대 상한이라는 의미는 추가 제약 없이는 부여하지 않는다. 따라서 Q>1은 곧바로 모델 기각이 아니라 채택된 normalization에 대한 초과이며 어떤 성분이 원인인지 함께 보고한다.

## 2. Teff의 arbitrary-axis 정확한 모멘트: 이번 루프의 새 계산

원문 `eq:Theta-expansion`을 좌표 독립적으로 확장한다.

\[
f(n):=T(n)/T_0=1+d\cdot n+n^\mathsf TS n,
\quad |n|=1,\quad S=S^\mathsf T,\quad\operatorname{tr}S=0.
\]

d와 S는 dimensionless temperature 계수이며 국소 velocity shear와 구별한다. 구면 평균은 \(\langle\cdot\rangle=(4\pi)^{-1}\int d\Omega\)이다. d의 세 성분과 S의 다섯 성분으로 임의 dipole–quadrupole 상대방향을 유지한다. 충분한 양의 온도 조건은 \(|d|+\|S\|_{op}<1\)이다.

정확한 isotropic moment tensor를 쓰면

\[
\langle n_{i_1}\cdots n_{i_{2m}}\rangle
=\frac{1}{(2m+1)!!}\sum_{\text{pairings}}\delta\cdots\delta,
\quad\langle\text{odd monomial}\rangle=0.
\]

\(t=f-1\), \(D=d^\mathsf Td\), \(J_2=\operatorname{tr}S^2\), \(J_3=\operatorname{tr}S^3\), \(K_1=d^\mathsf TSd\), \(K_2=d^\mathsf TS^2d\)라 두면

\[
\begin{aligned}
\langle t^2\rangle&=D/3+2J_2/15,\\
\langle t^3\rangle&=2K_1/5+8J_3/105,\\
\langle t^4\rangle&=D^2/5+4DJ_2/35+16K_2/35+4J_2^2/105.
\end{aligned}
\]

따라서, angular ansatz에 대해서 근사차수를 자르지 않은 정확한 식은

\[
\boxed{F_4:=\langle f^4\rangle=
1+2D+\frac45J_2+\frac85K_1+\frac{32}{105}J_3
+\frac15D^2+\frac4{35}DJ_2+\frac{16}{35}K_2+\frac4{105}J_2^2.}
\]

이 표현은 고정 비용의 작은 벡터·행렬 연산이다. 기존 `TeffMomentMap.moment`의 200×200 방향 grid를 매 posterior sample마다 계산할 필요가 없다. 일부 특별 축에 정렬되지 않은 dipole/quadrupole의 간섭도 보존한다. 오직 이 finite ansatz의 full-sky moment를 대체하며, 원 방향 map, mask likelihood, arbitrary alpha moment 또는 full polarized transport를 대체하지 않는다.

### 기존 인터페이스와 정확한 호환

기존 `theta_field(A,W,Q,V)`와 같은 field는

\[
d=(W,0,A),\qquad
S=\begin{pmatrix}-Q/2&0&V/2\\0&-Q/2&0\\V/2&0&Q\end{pmatrix}
\]

으로 생성한다. 그러면 \(\langle t^2\rangle=A^2/3+W^2/3+Q^2/5+V^2/15\)가 정확히 재현된다. A와 Q만 있을 때

\[
F_4=1+2A^2+\frac65Q^2+\frac85A^2Q+\frac8{35}Q^3
+\frac15A^4+\frac{22}{35}A^2Q^2+\frac3{35}Q^4.
\]

첨부 ch05의 일부 표시식은 비정규화된 적분을 평균처럼 사용해 A²Q 계수를 16/5로 썼지만, 정규화된 구면 평균과 실제 legacy .moment 구현에 맞는 값은 8/5다. 정규화된 구면 평균과 실제 field 정의로 계수를 고정하므로, 첨부 TeX의 `g224` 정규화 설명 또는 코드의 상수 반환 helper를 새 추론의 권위로 삼을 필요가 없다. 기존 수치 구적 `.moment`는 임의 alpha 검증/reference 경로로 유지한다.

### 온도, covariance, model remainder

Bolometric intensity-equivalent full-sky temperature는 \(T_{bol}=T_0 F_4^{1/4}\)다. 방향 의존 \(T_{eff}(n)\)와 명칭을 구분한다. \(\theta=(d_1,d_2,d_3,s_1,\ldots,s_5)\)에서 S를 Frobenius-orthonormal STF basis로 표현할 때, 코드가 analytic Jacobian을 반환한다. Delta method는

\[
\operatorname{Var}(F_4)\simeq J_F C_\theta J_F^\mathsf T,
\quad J_{Tbol}=\tfrac14T_0F_4^{-3/4}J_F.
\]

이는 covariance 전파의 1차 근사이며, posterior 표본에서 F4,Tbol을 직접 계산하면 이 근사를 피한다. T0도 불확실하면 그 covariance 및 교차항을 함께 포함한다. 새 F4는 기존 a_lm에서 유도되므로 추가 독립 자료 likelihood가 아니다.

finite ansatz 바깥의 angular remainder r이 \(\|r\|_\infty\le\varepsilon\), \(M=1+|d|+\|S\|_{op}\)이면 직접 binomial bound로

\[
|\langle(f+r)^4\rangle-F_4|
\le4M^3\varepsilon+6M^2\varepsilon^2+4M\varepsilon^3+\varepsilon^4.
\]

상위 transport/remainder 정리의 epsilon을 이 식으로 통과시키면 새 관측 모멘트의 deterministic model-error 예산이 된다. 실제 CMB map은 unit·bandpass·component response를 가진다. mask map에서 단순 평균을 낸 수를 이 full-sky 식과 동일시하지 않고, 해당 response likelihood가 추정한 latent full-sky d,S에 적용한다.

검증: Wolfram 일반 8변수 symbolic monomial 적분 residual 0; stdlib Fraction의 별도 monomial oracle 네 rational case 통과; rotation 불변성 residual 0; analytic gradient finite-difference 최대오차 1.143e-10. `code/teff_invariants.py`, `code/verify_teff_invariants.py`와 두 JSON receipt 참조. SymPy는 현재 runtime에 설치되지 않았고, 대신 정확한 rational oracle을 직접 작성했다.

## 3. 기존 H(d),q(d) 그림을 실제 조사 window로 업그레이드

기존 보고서는 대표 거리 d 한 값에 \(\Delta H\propto d^{-1}\), \(\Delta q\propto d^{-3}\)를 대입한다. 모델의 radial dependence는 그대로 재사용하되, 실제 estimator의 response를 계산하면 그림을 관측 예측으로 바꿀 수 있다.

예를 들어 fixed-distance conditional 선형 모형

\[
y_i=cz_i=n_i\cdot B+r_i[H+n_i\cdot A+n_i^\mathsf T\sigma n_i]+r_i^{rem}
\]

에서 isotropic weighted least-squares H summary를 \(\widehat H=\sum w_i r_i y_i/\sum w_i r_i^2\)로 정의하면, 선형성으로 정확히

\[
\widehat H_{\rm mean}=H+k_B\cdot B+k_A\cdot A+K_\sigma:\sigma,
\]

\[
k_B=\frac{\sum w_i r_i n_i}{\sum w_i r_i^2},\quad
k_A=\frac{\sum w_i r_i^2n_i}{\sum w_i r_i^2},\quad
K_\sigma=\frac{\sum w_i r_i^2 n_in_i^\mathsf T}{\sum w_i r_i^2}.
\]

B has velocity units, A and sigma have expansion-rate units, so all correction terms have H units. STF sigma contracts only the STF part of K_sigma. Full angular symmetry gives k_B=k_A=0 and K_sigma=I/3, hence a pure dipole does not shift this monopole estimator. On the actual mask these terms need not vanish. This directly separates physical dipole amplitude from survey leakage into H.

Legacy \(\widehat\Theta/3\) and the observed radial-redshift estimator are different observables. A factor 1/3 in a congruence expansion formula is not inserted into the radial term \(n\cdot B/r\) without deriving the observable map. This is resolved by an explicit survey operator, not by discarding the legacy model.

More generally, any retained old scalar plot can be regenerated as

\[
t_W=L_Wy,\quad\mu_W(\psi)=L_WF(\psi),\quad
C_W=L_WCL_W^\mathsf T.
\]

For bounded pointwise remainder \(|r_i|\le b_i\), the jth summary bias is bounded by \(\sum_i |(L_W)_{ji}|b_i\). Keep cross-window covariance when multiple radial bins share galaxies. The old d^-1/d^-3 functions become response templates integrated through the actual angular/redshift/selection window, with their stated valid range retained. No new fit is claimed here; full CF4 modulus uncertainty belongs inside its latent-distance likelihood, not in a fixed-r exact GLS claim.

This window approach enables immediate useful plots: (i) bulk/expansion-dipole contribution and their leakage to H for each CF4 depth cut; (ii) shared sky CMB tensor invariants versus CF4 shear tensor after a physically specified history/response map; (iii) d^-1/d^-3/host-age template contrasts with joint covariance; (iv) signed defect decomposition and comparator sensitivity on the same posterior samples.

## 4. Robust variable projection for maximal code reuse

기존 transfer, spectrum, map templates, survey windows를 공통 선형 블록으로 모으면 expensive nonlinear parameter를 훨씬 적게 탐색할 수 있다. 정해진 nonlinear history/type/geometry \(\psi\)에서

\[
y=f(\psi)+A(\psi)\alpha+E(\psi)u+\epsilon,
\quad\|u\|\le\rho,\quad\epsilon\sim N(0,C),\ C\succ0.
\]

\(\alpha\)는 unrestricted linear signal/calibration/nuisance amplitudes이며, Eu는 정리로 bounded된 model remainder다. W C W^T=I인 whitened coordinates에서 \(P=I-(WA)(WA)^+\), z=PW(y-f), G=PWE라 두면

\[
\min_{\alpha,\|u\|\le\rho}\|W(y-f-A\alpha-Eu)\|^2
=\min_{\|u\|\le\rho}\|z-Gu\|^2.
\]

고차원 data fit은 작은 trust-region 문제로 줄어든다. unconstrained 최소 norm solution이 ball 안이면 그대로 쓴다. 바깥이면

\[
u_\lambda=(G^\mathsf TG+\lambda I)^{-1}G^\mathsf Tz,
\quad\lambda>0,\quad\|u_\lambda\|=\rho
\]

를 scalar secular equation으로 푼다. ball 중심이 0이고 λ>0이면 inverse는 SPD다. rank-deficient 경우도 λ=0의 Moore–Penrose branch를 따로 처리한다. 이 profile score는 주어진 오차 예산 안에서 **가장 잘 맞는** 모형을 찾는 것이므로, score가 큰 경우 강건한 부적합 판정에 유용하다. 작은 score가 모든 allowed remainder에 대해 좋은 적합을 보장하지는 않는다.

이것은 profile criterion이다. Bayes evidence에는 prior와 marginalization determinant가 필요하므로 기존 nested sampler의 evidence를 이 최솟값으로 그대로 치환하지 않는다. 구속된 물리 amplitude에는 unconstrained projection을 적용하지 않고 가능한 subspace 또는 제약 solver를 사용한다. 추정 covariance와 selection-normalized likelihood는 별도 contract 그대로 유지한다.

## 5. 코드 재사용 결정과 다음 실행 순서

1. `TeffMomentMap.theta_field`, `.moment`, boost adapter, tensor/time-history source를 유지한다. alpha=4 full-sky moment만 새 정확한 kernel로 dispatch한다. 옛 특수축 그림도 같은 adapter로 재현할 수 있다.
2. `bounds.py`의 선형 bound·signed defect·tilt 함수를 array posterior에 적용한다. deprecated fixed defaults를 명시적 samplewise inputs로 승격한다. 단위, rapidity, covariance/selection contract를 함수 입력에 부착한다.
3. `departure_posteriors.py`의 세 단계 구조와 plot layout은 유지하되, same-sample denominator·다유체·signed components·unknown mass를 추가한다. 과거 weighted statistics helper 자체의 정확성은 검증된 최신 구현을 호출한다.
4. CF4 primitive likelihood와 latest endpoint kernel로 raw-data response를 만들고, 위 survey H kernels를 산출한다. 첫 plot은 실제 survey leakage/identifiability이며, 단일 amplitude를 global tilt로 바로 승격하지 않는다.
5. CMB common response/boost 후 d,S posterior를 얻어 F4와 전체 defect/MES pushforward를 계산한다. 원 sky의 physical tensor history 연결이 없는 동안 d,S는 CMB temperature tensors로 출력한다.
6. DESI window likelihood를 같은 background/type/history 입력으로 호출한다. 관측 product의 sample/selection에 맞는 kinematic count response를 구성하고 old Ellis–Baldwin coefficient를 무조건 DESI에 이식하지 않는다.
7. 최종 한 공동 posterior의 component decomposition·radial window plots·type-constrained predictions를 생성한다. old evidence, filling fraction, exclusion, forecast 숫자는 historical reference 패널로만 유지하며 이번 실제 fit으로 재계산한 값과 구분한다.

이 순서는 모든 상위 증명이 끝났다는 가정 아래 곧바로 관측 분석을 진행한다. 새 정리 검토를 위해 기존 의무 전체를 다시 열지 않는다. 새 kernel은 실제 검증된 구현이며, 신뢰할 수 있는 전체 관측 inference는 local 실행에서 data likelihood와 연결하는 다음 계산이다.
