# 원전 대조: 상대론적 광학·운동학·물질 폐쇄

작성일 2026-09-30. 이 문서는 원전의 적용 범위와 규약 정정만 기록한다. 새로운 정리의 최종 채택, 우선권, 투고 준비도 또는 통계적 식별성을 판정하지 않는다. 이전 `theory_blind_review_20260930/REPORT_KO.md`와 `inputs/C.md`를 비교 대상으로 읽었다. 이전 보고서를 일차 문헌으로 계산하지 않는다.

## 1. 실제 읽은 자료와 출처

주된 원전은 사용자가 제공한 `18-literatures.zip`의 R01, Ellis–Maartens–MacCallum, *Relativistic Cosmology* (2012)이다. 파일 식별자, 원본 archive member, SHA-256은 `SOURCE_MANIFEST.json`과 `REFERENCE_MAP.json`에 연결했다. 아래 PDF 페이지는 **1부터 센 실제 파일 페이지**이며 인쇄 페이지와 다르다. 일곱 책을 완독했다고 주장하지 않는다.

| 자료 | 실제 확인 범위 | 이번 작업에 적용되는 부분 / 적용하지 않는 부분 |
|---|---|---|
| R01 Ellis–Maartens–MacCallum | 목차; §§4.2–4.6, 5.1–5.4의 관련 부분, §§7.1–7.4, §11.1; 아래 식 단위 항목 | 기본 규약, 광선 미분, endpoint 적색편이, 거리 쌍대성, 유체 frame, 복사 hierarchy와 almost-EGS의 핵심 원전 |
| R02 David Tong, *Kinetic Theory* (2012 lecture notes) | 목차 PDF 3–4; §2.4.2 PDF 47 / 인쇄 42 | (2.57)–(2.61)의 국소평형 **가정에 의한** 유체 폐쇄. 비상대론적 자료이므로 일반 상대론적 관측 역산의 증거로 쓰지 않음 |
| R03 Kolb–Turner, *The Early Universe* (1990; supplied reprint) | 목차 PDF 12–17; §5.1 PDF 158–159 / 인쇄 115–116 | (5.1)의 상호작용률/팽창률 구분, (5.2)–(5.7)의 Boltzmann과 FRW 축약. FRW의 등방 분포 가정을 일반 비등방 복사장에 이식하지 않음. OCR 수식은 일부 불완전하여 여기서는 그 식을 전사하지 않음 |
| R04 O. Piattella, *Lecture Notes in Cosmology*, arXiv:1803.00070v1 | 목차 PDF 3–7; §3.7.3 PDF 78–79 / 인쇄 67–68 | (3.142)–(3.145)의 affine Liouville 연산자와 질량껍질; (3.146)부터는 FLRW 전용 축약. perturbation/CMB 통계 장은 이번에 연구하지 않음 |
| R05 P. & U. Romatschke, *Relativistic Fluid Dynamics In and Out of Equilibrium* | 앞부분·목차 PDF 1,7–8; §3.1 PDF 69–70 / 인쇄 59–60 | (3.1)–(3.6): 준입자·약한 장거리 힘 조건, collision term, stress moment와 보존. 핵충돌 수치 결과를 우주론 잔차의 상계로 가져오지 않음 |
| R06 Andersson–Comer, *Relativistic fluid dynamics: physics for many different scales*, arXiv:2008.12069v1 | 초록 PDF 1–2, 목차 3–4; §5.1 PDF/인쇄 49–50; §16.1 PDF/인쇄 196–197 | stress 분해와 미시물리 폐쇄의 차이; Eckart/Landau frame과 입자 확산. 목차상 §8.3 다성분 우주론은 관련 후속 읽기 대상으로만 선택 |
| R07 Cercignani–Kremer, *The Relativistic Boltzmann Equation: Theory and Applications* | 제목·목차·서문 PDF 4,6–10; §§4.3–4.4 PDF 112,115–116 / 인쇄 102,105–106; §12.3 PDF 337–338 / 인쇄 330–331 | 입자 frame와 에너지 frame, 곡률을 포함하는 streaming과 collision. **서명 (+---), U²=+c²**여서 R01/R2의 부호를 그대로 복사할 수 없음 |

PDF skill의 시각 대조 방법을 사용했다. R01 PDF 97,101,121,173,303 및 R07 PDF 115,338을 렌더링하여 직접 확인했다. 나머지 위치는 텍스트 추출과 인쇄 페이지 머리말을 대조했다. 렌더는 `reference_audit_tmp/`에 남겼다. 렌더를 했다는 사실이 그 책의 모든 증명을 검증했다는 의미는 아니다.

## 2. R01의 식 단위 근거

| 논점 | 인쇄 페이지 / PDF 페이지 | 정확한 원전 위치 | 적용 경계 |
|---|---|---|---|
| unit 4-velocity, 가속도, projector | 74,76 / 90,92 | (4.2), (4.8)–(4.10) | 책은 c=1; 물리 proper-time 변수로 변환 필요 |
| 상대속도 gradient와 와도 인덱스 | 80–82 / 96–98 | (4.29)–(4.34), 특히 p81의 정의 문장 | D_b u_a 행렬을 분해함. D_[a U_b]와 반대 순서 |
| 전체 1-jet와 norm | 85 / 101 | (4.38)–(4.40) | θ,σ,ω,a의 12개 성분; σ²는 Frobenius norm²/2 |
| 보존과 유체 가속도 | 92,96–97 / 108,112–113 | (5.10)–(5.12), (5.37)–(5.39) 및 p96 frame 논의 | 보존만으로 일반 constitutive law가 닫히지 않음; dust의 geodesic 성질은 물질 가정 |
| observer boost와 다유체 | 94,101–103 / 110,117–119 | (5.18)–(5.22), (5.54)–(5.73) | 종별 energy frame와 total-stress frame를 구별 |
| photon energy/direction의 ray 미분 | 104–106 / 120–122 | (5.76)–(5.84), 특히 (5.79),(5.80) | photon 경로에 따른 미분. 관측자 시간에 따른 같은 source의 drift가 아님 |
| hierarchy 비폐쇄와 brightness moments | 107–108 / 123–124 | (5.94)–(5.101), p108의 비폐쇄 설명 | collisionless라고 시공간 분포 미분이 알려지는 것이 아님 |
| geometric optics / endpoint 적색편이 | 154–158 / 170–174 | (7.9),(7.13),(7.17)–(7.21) | 동일 source·photon·event의 대응 필요; 모든 redshift 기여의 분리가 자동 관측되는 것은 아님 |
| 광학 focusing | 160 / 176 | (7.25)–(7.28) | Ricci/Weyl 및 null shear는 유한 거리 오차 제어에 필요 |
| 거리 정의와 쌍대성 | 163–165 / 179–181 | (7.38)–(7.48), Theorem 7.1 | D_A=r_O, D_L=(1+z)r_G=(1+z)²D_A; photon conservation 등 광학 가정 유지 |
| 복사 evolution과 almost-EGS | 283–287 / 299–303 | (11.1),(11.2), Theorems 11.1–11.3 | 한 관측자의 작은 CMB anisotropy만으로 결론을 얻지 않음 |

## 3. 필요한 규약 정정

### 3.1 와도와 시간 단위

R01은 다음 **인덱스 순서**를 사용한다:

\[
V^{\rm E}_{ab}=D_bu_a,\qquad
\omega^{\rm E}_{ab}=D_{[b}u_{a]},\qquad
\nabla_bu_a=\omega^{\rm E}_{ab}+\sigma^{\rm E}_{ab}
+\tfrac13\Theta^{\rm E}h_{ab}-u_b\dot u_a.
\]

이는 R01 p81/PDF97의 정의 및 p85/PDF101 (4.38)에서 시각 확인했다. 이전 `inputs/C.md`의 R2 convention은 U=cu, U²=−c²,
\(\omega^{\rm R2}_{ab}=D_{[a}U_{b]}\)이다. 따라서

\[
\Theta^{\rm E}=\theta/c,\quad \sigma^{\rm E}_{ab}=\sigma_{ab}/c,
\quad\omega^{\rm E}_{ab}=-\omega^{\rm R2}_{ab}/c,
\quad\dot u_a=A_a/c^2.
\]

같은 spatial orientation을 사용할 때 axial vector도 같은 부호 반전이 필요하다. R01 (4.34)는 Newtonian curl의 **음의 절반**이고, R2의 vector는 양의 rigid rotation Ω와 같은 방향이다. norm은 부호에 영향을 받지 않지만 signed morphology·curl은 영향을 받는다.

R01 (4.33)의 nearby connecting-vector 방향 변화는 \(P_e(\sigma^{\rm E}+\omega^{\rm E})e\)다. 이를 초당 rate로 바꾸면

\[
\kappa_0=P_e(\sigma-\omega^{\rm R2}_{\rm matrix})e.
\]

그러므로 \(P_e(\sigma+W)e\) 표기를 유지하려면 **rate 행렬 W=−ω_R2=cω_E**이다. 초기 원문의 W=ω_R2와 함께 쓰면 부호 오류다. 이 변환은 이미 이전 심사 보고서에 지적된 정정을 원전에서 확인한 것이다. 또한 (4.33)은 simultaneous nearby separation 식이며 유한 거리의 실제 position drift로 넘어가는 광학 증명이 별도로 필요하다.

### 3.2 진행 방향과 하늘 방향, ray 미분과 drift

R01 (7.13)의 e는 미래방향 photon의 **진행 방향**이다. 하늘을 보는 방향을 n이라 하면 n=−e다. R01 (7.19)는 길이당 변화이므로 물리 단위에서는

\[
\frac{d\ln\lambda_{\rm wave}}{dl}
=\frac{\theta}{3c}+\frac{\sigma_{ab}e^ae^b}{c}
+\frac{A_ae^a}{c^2}.
\]

따라서 source frame의 관측방향 Hubble rate는
\(H(n)=\theta/3+\sigma_{ab}n^an^b-A_an^a/c\)이다. R2에서 \(\mathscr D=(U+ce)^a\nabla_a\)이면 R와 V는 s⁻¹이다. \(d/d\lambda_{\rm affine}\), \(\mathscr D\), \(d/d\tau_o\)를 동일 기호로 바꾸지 않는다. R01 (5.79),(5.80)과 (7.18),(7.19)는 한 광선을 따른 변화이고, redshift/position drift는 관측자 worldline의 여러 사건에서 **같은 source**를 추적하는 변화다.

### 3.3 절편과 slope, 거리 선택

다음은 R01 endpoint 식 (7.17)과 normalization에서 직접 얻는 **본 대조의 유도**다. 관측자 unit vector o, 관측자 하늘 n, 과거방향 null vector K=−o+n를 두어 K·o=1로 정규화한다. 매끄러운 source congruence u가 관측 사건까지 정의되어 있으면, 거리 0의 절대 절편은

\[
I(n):=\lim_{d_A\to0}(1+z)=K\cdot u
=m+b\cdot n,\quad u=mo+b,
\quad m>0,\quad m^2-|b|^2=1.
\]

완전 하늘의 정확한 절편으로 m=⟨I⟩, b=3⟨In⟩이며 source/observer 상대속도는 b/m이다. **자유 절편을 둔다**는 것은 이 물리적 0거리 절편을 fit에서 보존한다는 뜻이다. 임의 방향별 additive nuisance까지 무제한 허용한다는 뜻이 아니다. redshift를 먼저 강제로 0에 맞추면 필요한 정보를 지울 수 있다. 절편의 절대 관측은 충분조건이며 모든 calibration nuisance가 곧바로 비식별성을 만든다고 주장하지 않는다; calibration family의 실제 작용을 계산해야 한다.

observer-normalized affine 길이 r에서 \(dr\)의 vertex 단위는 \(dd_A\)와 같다. \(B_{ab}=\nabla_{(a}U_{b)}\)이면
\(c\,\partial z/\partial d_A|_0=B(K,K)\)다. null sky가 정하는 B의 class는 \(S+\lambda g\)이고, 알려진 u에 대해 B(u,u)=0를 적용하면

\[
B=S+S(u,u)g,\qquad A_a=2cB_{ab}u^b.
\]

반면 B를 \(\nabla_{(a}u_{b)}\)로 정의했다면 마지막 계수는 **2c²**이다. 이 둘의 혼용이 c 복원 오류를 낸다. 이 local algebra는 ω나 orbit normal N을 결정하지 않는다.

거리 변환은 아래 W01과 원전의 (7.48)에 따라 처리해야 한다. 실제 관측자의 절편 I에서

\[
D_L=I^2D_A+O(D_A^2),\qquad
c\frac{\partial z}{\partial D_A}\Big|_0
=I^2c\frac{\partial z}{\partial D_L}\Big|_0.
\]

즉 비공동운동 observer에서는 D_L slope를 그대로 null quadratic으로 읽을 수 없다. photon conservation 아래 \(D_L/(1+z)^2\)를 사용하면 D_A와 같다. 실제 flux로 얻는 거리에는 source luminosity calibration 가정도 포함된다.

### 3.4 residual 폐쇄

R01 (5.98)–(5.101)은 에너지·운동량 보존으로도 moment 계가 닫히지 않음을 명시한다. (11.2)의 전단 항을 고립해도 \(\dot\pi_\gamma\), 공간 gradient, octupole divergence, hexadecapole, acceleration coupling이 남는다. 약형에서 각도 미분을 부분적분해 제거하는 것은 **시공간 미분과 collision 잔차를 측정하거나 상계하는 것과 다르다**.

따라서 \(\mathsf A_{\mathscr B}k=r\)의 rank 12는 r이 알려지거나 허용집합이 제한된 경우의 algebra다. 정적 sky가 r을 제공하지는 않는다. collisionless 조건도 이 문제를 제거하지 않는다. R02의 국소평형, R05의 준입자/충돌 모델, R07의 constitutive closure는 가능한 추가 가정의 예이며 자유복사 CMB에 자동 적용되지 않는다.

R01 p96/PDF112와 R07 pp105–106/PDF115–116은 Landau energy frame와 Eckart particle frame를 구별한다. R01 p103/PDF119의 (5.65)–(5.70)는 종별 flux와 total flux의 차이를 명시한다. total q=0만으로 각 종의 속도가 같다고 결론내릴 수 없다. R06 p49의 지적대로 임의 metric에서 T∝G를 정의한 국소 반례는 물리적 dust/kinetic 계열의 존재정리와 다른 범위다.

### 3.5 almost-EGS

R01 Theorem 11.3, p287/PDF303은 팽창하는 Λ 우주의 **영역 전체**에서 물질과 공동운동하는 관측자들의 collisionless radiation이 거의 등방이고, 일부 시간·공간 multipole 미분도 작다는 조건을 둔다. dimensionful moments는 monopole 등에 대해 정규화한다. 작은 multipole amplitude에서 작은 derivative가 따라오지 않는다. 한 worldline의 정적 CMB map만으로 모든 조건을 확인했다고 할 수 없다.

정확한 Theorems 11.1–11.2에는 radiation congruence의 geodesic·expanding 조건과 물질 조건이 따로 있다. 책의 p287에 적힌 당시 미해결 범위를 2026년까지 그대로 미해결이라고 단정하지 않는다. 여기서 확인한 것은 **인용하는 2012년 정리의 가정**이다.

## 4. Maartens v3 §§2–4와의 직접 대조

W01: [Maartens et al., arXiv:2312.09875v3](https://arxiv.org/html/2312.09875v3), §§2–4, (3)–(5),(27),(28),(34)–(37),(59),(62),(67),(68),(72)–(74).

버전 범위: 직접 대조한 것은 **2024-06-14 arXiv v3 HTML**이다. arXiv metadata에는 JCAP 09 (2024) 070, DOI `10.1088/1475-7516/2024/09/070`, accepted-version이라는 설명이 있다. 출판사 version of record의 (37)을 별도로 대조한 것은 아니므로 아래 주의점을 출판본 전체에 확인된 오류나 발행된 정오표로 표현하지 않는다.

Its matter model is geodesic, irrotational dust. A one-event boost does not define an observer congruence. The paper already obtains joint observer-velocity/shear information from Hubble multipoles. It distinguishes area from luminosity distance, retains the boosted vertex redshift, and discusses higher-order contamination; these are prior results, not new contributions here.

| 대조점 | 원문 위치 | 이번 적용 |
|---|---|---|
| source 가속도 | (3)–(5) | arbitrary acceleration 확장은 원문 가정을 변경함 |
| endpoint 절편 | (27), §4.3 첫 문단 | \(\tilde z_o=\Gamma_o^{-1}-1\)을 보존 |
| 거리 변환 | (59),(62) | \(\tilde d_A=\Gamma d_A,\ \tilde d_L=\Gamma^{-1}d_L\) |
| slope 변환 | (67),(68) | \(\tilde H=\partial_{\tilde d_A}\tilde z=\Gamma^{-2}\partial_{\tilde d_L}\tilde z\), c=1 |
| 유한 거리 | (72)–(74) | higher derivatives·curvature 전개는 있음; 이번에 찾은 부분은 universal certified remainder theorem이 아님 |

**독립적인 식 대입으로 발견한 (37)의 주의점.** 이것은 저자들이 인정한 erratum이라는 뜻이 아니다. (34b)의 일차식에서 d=−2(HI+Σ)v+O(|v|²)이다. (37)에 표시된 truncated inverse를 대입하면

\[
-\frac{(HI-\Sigma)d}{2H^2}
=\left(I-\frac{\Sigma^2}{H^2}\right)v+O(|v|^2).
\]

고정된 임의 전단 Σ에서 누락항은 O(|v|)이다. 따라서 추가 small-shear 차수 가정 없이 이를 arbitrary-shear 일차 역산으로 쓰면 안 된다. 예를 들어 \(\Sigma/H=\operatorname{diag}(1/2,-1/2,0)\), v=(ε,0,0)이면 3ε/4를 반환한다. 해당 차수의 올바른 역산은 \(-\tfrac12(HI+\Sigma)^{-1}d\)이며, 역행렬 존재와 inverse norm의 bound가 필요하다. 이것은 위 논문의 정확한 boost 식 (32)–(34)를 반증하지 않는다.

## 5. 신규성 겹침 검색 결과와 남은 한계

검색일 2026-09-30. 두 검색엔진에서 `cosmography arbitrary acceleration observer Hubble intercept ...`, `cosmography intercept slope`, `covariant cosmography stability`, `cosmography deterministic`, `cosmography Lipschitz`, `covariant cosmography finite distance convergence remainder` 및 정확한 논문 제목을 검색했다. 일반 검색의 무관한 결과는 근거에서 제외했다. 검색 부재를 우선권 증명으로 취급하지 않는다.

| ID / 확인 수준 | 직접 읽은 일차 자료 | 정확히 겹치는 부분 | 이번에 확인되지 않은 부분 |
|---|---|---|---|
| W02 / 본문 관련 절 | [Heinesen 2021, v2](https://arxiv.org/html/2010.06534v2), §§2–5, (36)–(41) | general accelerated congruence, 9개 first-order 방향 계수; §5는 unknown small observer boost와 nonzero distance intercept를 이미 포함 | exact all-speed intercept + quotient representative inverse와 그 sharp deterministic constants는 읽은 절에서 찾지 못함. 단순히 ‘가속도와 observer motion을 함께 넣었다’는 신규성 주장은 불가 |
| W03 / 본문 관련 절 | [Heinesen–Korzyński 2024 v1](https://arxiv.org/html/2406.06167v1), §§II–III, VI, IX, Appendix E | position/redshift drift의 별도 관측 채널; shear/vorticity/aberration acceleration의 vector-harmonic 분리 | main results는 큰 규모 가속도를 생략; 부록에는 일반 가속도 유지. ray V와 drift κ의 동일시를 지지하지 않음 |
| W04 / 본문 관련 절 | [Modan–Koksbang 2024 v2](https://arxiv.org/html/2408.07459v2), convergence discussion, Tables 2,4 | LTB에서 local Taylor approximation이 빠르게 나빠질 수 있음; 저차 coefficient ratio의 convergence 추정은 매우 거친 진단 | 모든 admissible spacetime에 적용되는 uniform inverse/remainder bound는 본 대조에서 확인하지 않음 |
| W05 / 본문 관련 절 | [Macpherson–Heinesen 2025 v3](https://arxiv.org/html/2507.01095v3), §§2,5.4 | quiet-universe 조건, expansion/density gradient에 의한 distance dipole, smoothing/convergence 및 local boost 영향 | co-moving dust/추가 smallness를 사용하므로 unrestricted arbitrary-acceleration inverse와 동일 정리 아님. simulation accuracy를 universal bound로 읽지 않음 |
| W06 / 본문 관련 절 | [Hills–Heinesen 2026 v1](https://arxiv.org/html/2601.16844v1), §§2.1–2.3 | 일반 congruence의 luminosity-distance fourth-order 전개와 Szekeres 검증; Padé 비교 | 전개 coefficient와 bounded remainder certificate는 다름. HTML의 (13d) 등 일부 수식 표시는 깨져 있어 여기서 fourth-order 식 자체를 전사·검증하지 않음 |
| W07 / 검색된 arXiv 초록만; 본문 접근 실패 | [Bendtsen–Heinesen–Koksbang 2026](https://arxiv.org/abs/2608.07008) | arbitrary-redshift-centred cosmography라는 매우 근접한 최신 후속 주제 | HTML·abstract open·PDF direct open이 도구에서 실패. 원문 본문 대조를 완료한 것으로 계산하지 않음; 이 때문에 최신 exact novelty exclusion은 미완료 |
| W08 / 초록만 | [Adamek et al. 2024 v2](https://arxiv.org/abs/2402.12165) | observer velocity와 expansion multipoles의 공동 추정 및 survey smoothing | 초록 확인만으로 exact theorem이나 deterministic stability의 포함/부재를 단정하지 않음. 이번에 통계 분석법은 연구하지 않음 |
| W09 / 초록만 | [Sarma et al. 2026 accepted v2](https://arxiv.org/abs/2510.03517) | local LTB 구조의 정확 거리와 covariant cosmography 오차 비교 | 본문 theorem-level 비교는 미실시 |
| W10 / 초록·§§2.1,6.3 | [Kalbouneh et al. 2025 v1](https://arxiv.org/html/2510.02510v1) | CF4·Pantheon+의 expansion multipoles와 matter observer motion을 함께 해석한 직접적인 관측 후속 연구. §6.3은 smooth dust 가정과 작은 스케일에서의 continuum 한계를 명시 | arbitrary accelerated-source exact inverse의 정리는 확인하지 않음. §2.1의 CF4 측정 공분산 미제공·무상관 가정은 기록만 했고 통계 타당성 감사는 수행하지 않음 |

W02 §5 explicitly separates existence of a differentiable expansion from smallness of its remainder. Its boosted fit uses a first-order velocity hierarchy, so its distance intercept is not itself the exact zero-distance redshift inverse considered here. W03 Appendix E is direct prior art for vector-multipole separation, including the need for a nonrotating reference frame.

**허용되는 좁은 결론:** 검토한 본문에서는 ‘absolute 0거리 redshift 절편 + area-distance slope → 임의 가속도를 허용하는 정확한 local inverse’에 특정 uniform deterministic norm bound와 finite-distance certificate를 모두 결합한 동일 정리를 찾지 못했다. 그러나 주변 구성의 상당 부분은 R01, W01–W03의 표준 식 및 기존 확장이고, W07의 본문 접근 공백도 있다. 따라서 현 단계의 기록은 **동일 정리 미발견 / novelty 미확정**이다. 정확한 역산을 다시 적는 것, Taylor 정리의 일반 remainder를 인용하는 것만으로 새로운 물리 결과라고 하지 않는다.

실제 finite-distance certificate에는 최소한 (i) 어떤 거리/affine 변수를 쓸지, (ii) 같은 smooth source congruence와 관측자의 normalization, (iii) caustic-free 구간, (iv) 그 구간의 필요한 covariant derivative·optical curvature 상계, (v) distance-variable 변환의 하한, (vi) 그 가정 아래의 결정론적 오차 norm이 함께 필요하다. z를 독립변수로 쓰면 redshift-map의 적절한 local inverse 조건도 필요하다. 이 항목들은 확률분포나 관측 catalogue만으로 자동 제공되지 않는다.

## 6. 출처 상태와 산출물의 의미

`REFERENCE_MAP.json`은 supplied-file provenance, 실제 읽은 페이지, 시각 확인 여부, correction ID, 외부 원전 URL·버전·읽은 범위를 기록한다. 이 문서의 유도식은 원전의 직접 인용과 구별했다. 외부 논문의 본문을 새로 내려받아 보존하지 않았으며, 제공된 archive 파일은 수정하지 않았다. 이번 작업에서는 통계 연구, 관측 데이터 적합, 대규모 수치 실험을 수행하지 않았다.
