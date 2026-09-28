# MES 원전 확인 — fresh evidence note

작성: 2026-09-20. 범위: almost-EGS/MES 가정과 shear bound의 정확한 의미, 수치 진화 없는 완화 방향. 기존 HTT 판정은 읽거나 가져오지 않았다. 본 메모는 optical endpoint/dynamics 연구의 조건부 문헌 입력이며 native H0, admission, 후보 승격을 판정하지 않는다.

## Convention and claim ceiling

서명은 (-,+,+,+)이다. 물리적 4-속도는 \(U^aU_a=-c^2\), \(u^a=U^a/c\), \(h_{ab}=g_{ab}+u_au_b\). 아래 \(\Theta=3H\), \(\sigma_{ab}\)는 물리적 시간 역수 단위이다. \(D\)는 투영 공간 미분, dot은 물리적 고유시간 미분이다. 분포 적분을 사용할 때 \(\hbar,k_B,c\)를 1로 놓지 않는다. 필요하면 흑체 에너지 밀도는 \(\mu=\pi^2k_B^4T^4/(15\hbar^3c^3)\).

문헌 정리는 `literature-supported`; 아래 norm 변환은 `derived`; 새로운 완화 정리의 성립은 `unresolved`이다. 원문들의 점근적 1차 논의를 유한 오차의 비섭동 정리로 자동 해석하지 않는다.

## 직접 확인한 핵심 원전 5개

**S1 — Stoeger, Maartens & Ellis, ApJ 443, 1–5 (1995 April 10), “Proving Almost-Homogeneity…”**

[원본 5쪽 스캔](https://articles.adsabs.harvard.edu/pdf/1995ApJ...443....1S). 전체 OCR, p.2–3 그림 직접 확인; §1.2, pp.2–3, 식(7)–(14), (17), (20), (23)–(26), p.5 확인. 관계: `supports / limits`.

- Einstein 방정식, 서로 독립적으로 보존되는 dust와 collisionless radiation, 양의 expansion, dust-comoving geodesic congruence를 가정한다. Geodesic 조건은 별도로 보존되는 무압력 물질의 운동량 방정식에서 나온다.
- 거의 등방인 것은 모든 물질 동반 관측자에 대한 **분포함수**이다. 식(13)은 \(\ell>0\)의 \(F_{A_\ell}\), 시간·공간 미분, 본문은 모든 고차 미분까지 \(O(\epsilon)\)로 가정한다. 식(14)은 에너지 적분과 미분에도 이 차수가 보존됨을 별도로 요구한다.
- 영역 \(U\)는 decoupling 이후 우리 과거 광원뿔 **내부와 근방**이다. Null surface 하나가 아니다.
- 결론은 shear, vorticity, electric/magnetic Weyl, radiation/matter density gradients, expansion gradient가 작다는 것과 **국소적** almost-FLRW metric이다. p.5는 적분된 변동이 작을 영역 크기가 gradient에 의존하며 global topology는 결론 밖이라고 명시한다.

**S2 — Maartens, Ellis & Stoeger, PRD 51, 5942–5945 (1995 May 15), “Improved limits…”**

[APS 논문](https://journals.aps.org/prd/abstract/10.1103/PhysRevD.51.5942), [실제 열람한 APS PDF](https://harvest.aps.org/v2/journals/articles/10.1103/PhysRevD.51.5942/fulltext). 전체 텍스트, p.5944 그림 확인. 관계: `supports / limits`.

식(1)–(4): 온도 PSTF multipole \(\tau_{A_\ell}\)의 amplitude와 3차까지의 시간·공간·혼합 미분에 독립적인 작은 상수를 둔다. 물리단위의 압축 표현은

\[
|\tau_{A_\ell}|<\epsilon_\ell,\qquad
|\partial_\tau^nD^m\tau_{A_\ell}|
 <\epsilon_\ell^{(m,n)}\frac{\Theta^{m+n}}{c^m},
\quad1\le m+n\le3,
\]

이며 실제 미분 순서는 식(2)–(4)를 따른다. 이들은 amplitude만으로 따라오지 않는다. p.5942는 종전 논문의 기하학적 미분 가정 C3를 이 관측량 미분 가정으로 대체한다고 설명한다.

식(23)–(29)은 각각 \(D\mu,\sigma,\omega,D\rho,D\Theta,E_{ab},H_{ab}^{\rm Weyl}\)를 제한한다. 식(5)–(6)의 더 강한 C1′–C2′는 공간 미분이 시간 미분보다 크지 않고, 시간 미분 척도가 \(t_R=T/|\dot T|\simeq H^{-1}\)라는 추정이다. 이에 따라 \(\epsilon_\ell^*\simeq\epsilon_\ell/3\), \(\epsilon_\ell^{**}\simeq\epsilon_\ell/9\), \(\epsilon_\ell^{***}\simeq\epsilon_\ell/27\)를 사용한다. 식(30)–(36)의 간단한 bounds는 이 추가 조건부 결과이다.

**S3 — MES, “Anisotropy and inhomogeneity of the universe from ΔT/T”, preprint 1995 October 24.**

[저자 원문](https://arxiv.org/pdf/astro-ph/9510126). pp.2–6, 식(6)–(14) 확인. 관계: `supports / limits`.

pp.4–5 식(6)–(7)은 S2의 shear bound와 derivative 가정을 다시 명시한다. Intrinsic residual dipole을 무시하는 것은 관측만의 귀결이 아니라 추가 가정이다. 정확한 Bianchi I/거의 공간균질 multipole이라는 추가 조건은 훨씬 강한 shear 결과를 주므로 일반 비균질 상황의 bound와 바꿔 쓰면 안 된다. 식(9)–(13)은 Weyl에는 \({\rm Mpc}^{-2}\), fractional density/expansion gradients에는 \({\rm Mpc}^{-1}\)를 사용한다.

**S4 — Stoeger, Araujo & Gebbie, “The Limits on Cosmological Anisotropies and Inhomogeneities from COBE Data”, arXiv 1999 April 25.**

[저자 원문](https://arxiv.org/pdf/astro-ph/9904346). §§1–4, 식(1)–(21), pp.2–10 확인. 관계: `supports / limits`.

이 논문은 S2의 강한 derivative 가정을 채택한 응용이다. 온도 multipole norm은 \(\delta T/T\)의 PSTF norm이며 µK로 보고된 rms quadrupole/octupole을 그대로 넣지 않는다. 같은 정의에서 \(|\tau_2|=\sqrt{15/2}\,Q_{\rm rms}/T\), \(|\tau_3|=\sqrt{35/2}\,O_{\rm rms}/T\)이다. 식(12)의 \(\epsilon_1=0\)도 추가 가정이다. 특정 관측자의 rms 측정값을 영역 전체의 uniform upper bound로 쓰려면 별도 추론이 필요하다. 현재 데이터의 수치 prior를 이 1999 문헌으로 대체하지 않는다.

**S5 — Roy Maartens, “Is the Universe homogeneous?”, arXiv:1104.1300v2, 2011 October 6.**

[저자 원문](https://arxiv.org/pdf/1104.1300). §§II–IV, pp.5–10, 식(10), (11)–(14), (19), (35), Appendix A37 확인. 관계: `supports / limits / contextual`.

p.9는 almost-EGS를 dust+Λ, expanding region, 모든 comoving 관측자의 작은 분포 multipoles와 일부 작은 derivatives를 전제로 진술한다. 작은 amplitude는 작은 derivative를 함의하지 않으며, 이를 제거하는 문제는 해당 2011 논문에서 미해결이라고 한다. 이는 2026년 문헌 전체의 부재 판정이 아니다. 식(10)은 한 worldline의 CMB 등방성이 transverse spatial derivatives를 결정하지 않음을 설명한다. 식(13)은 low-z directional Hubble coefficient를 expansion, acceleration dipole, shear quadrupole로 분해한다. 원격 SZ 관측은 광원뿔 위 일부 사건의 등방성 검사이지 전체 열린 영역의 모든 multipole derivative 측정은 아니다.

## 연구 입력으로 쓸 수 있는 shear prior

S2 p.5944 식(24), (31), S3 식(6)–(7)에 따라, 위 영역/물질/충돌 없음/미분 가정을 모두 채택하는 1차 MES regime에서

\[
\frac{\|\sigma\|}{\Theta}
 <\frac83\epsilon_2+\epsilon_2^*
 +5\epsilon_1^{\dagger}+\frac97\epsilon_3^{\dagger}
 \quad\longrightarrow\quad
 B:=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3.
\]

여기서 \(\|\sigma\|^2=\sigma_{ab}\sigma^{ab}\); \(\sigma^2=\tfrac12\sigma_{ab}\sigma^{ab}\)라는 다른 scalar convention과 혼동하지 않는다. 화살표는 C1′–C2′를 추가함을 뜻한다. \(\epsilon_1=0\)은 기본식에 포함되지 않는다.

**직접 유도:** \(\Theta=3H>0\), \(x_\sigma=\mathrm{Tr}[(\sigma/H)^2]/6\)이면

\[
x_\sigma=\frac{\|\sigma\|^2}{6H^2}
 <\frac{9B^2}{6}=U_\sigma,\qquad
\boxed{U_\sigma=\frac32 B^2}.
\]

이는 MES의 조건부 leading-order prior를 \(x_\sigma\) convention으로 옮긴 것이다. 유한 오차에서 엄밀한 상한으로 사용하려면 먼저 \(\|\sigma\|/\Theta\le B+\Delta_\sigma\) 같은 나머지 제어를 확보하여 \(U_\sigma=\tfrac32(B+\Delta_\sigma)^2\)로 써야 한다. \(x_\sigma\)는 2차 양이므로 1차 계산에서 얻은 shear를 제곱할 때 이 구분이 특히 중요하다.

## 수치 진화 없는 구성적 완화 방향

아래는 완성된 almost-EGS 확장 정리가 아니라 구체적 판별식을 가진 후보 경로이다.

1. **필요한 유한 residual만 제한.** S5 식(19)의 완전 비선형 quadrupole 방정식에서 \((8\mu/15)\sigma\)와 shear에 선형인 anisotropic-moment 항을 모아 \([(8\mu/15)I+\mathcal M]\sigma=R\)로 쓴다. \(\mu\ge\mu_{\min}>0\), \(\|\mathcal M\|<8\mu_{\min}/15\), \(\|R\|\le r\)라면 elementary operator estimate가 \(\|\sigma\|\le r/(8\mu_{\min}/15-\|\mathcal M\|)\)를 준다. 이것은 미분 각각의 작은 norm보다 필요한 조합만 제한한다. 단 \(R\)의 acceleration/vorticity 및 collision 항을 별도로 제어해야 하며, residual smallness를 CMB amplitude로부터 추론하면 안 된다. \(R\)는 에너지밀도/시간, \(\mathcal M\)은 에너지밀도 단위로 통일한다.

2. **Weak-form 목표로 변경.** Compact-support PSTF test tensor에 hierarchy를 적분하고 integration by parts로 미분을 test tensor에 옮긴다. 유한 moment norm, 알려진 test-function derivative norm, 경계 flux와 geometry-adjoint 항의 제어가 있으면 weighted shear pairing을 제한할 수 있다. 이는 pointwise shear bound보다 약하지만 high-frequency multipole derivatives를 직접 가정하지 않는 연구 목표이다. 충분한 test family와 coercivity 없이는 작은 pairing을 작은 pointwise shear 또는 작은 \(x_\sigma\)로 바꿀 수 없다.

3. **Low-z local shear 관측.** S5 식(13)의 물리단위 표현은 \(\mathcal H(n)=\lim_{z\to0}cz/D_A(n,z)=\Theta/3+A_an^a/c+\sigma_{ab}n^an^b\)이며 방향 부호는 원문의 convention을 따른다. 직접적인 구면 적분으로
   \[
   \left\langle(\mathcal H-\langle\mathcal H\rangle)^2\right\rangle
   =\frac{|A|^2}{3c^2}+\frac{2}{15}\|\sigma\|^2
   \]
   를 얻는다. 따라서 local Hubble anisotropy의 오차 상한 \(\delta_H\)가 실제로 확보되면 \(\|\sigma\|\le\sqrt{15/2}\,\delta_H\). 필요한 것은 finite-z remainder, peculiar-velocity/selection/calibration 오차 제어이다. 이는 한 관측 사건의 shear를 제한하는 경로이며 all-observer conclusion이나 vorticity/Weyl 전체 bound를 주지 않는다.

4. **Dust/geodesic 조건의 유한 완화.** 보존식의 pressure-gradient, acceleration, anisotropic stress, collision/source 항을 버리지 않고 해당 target identity의 nuisance residual로 남긴다. 추가항의 유한 상한을 구하면 위 operator 또는 weak estimate에 더할 수 있다. 이 경우 기존 dust MES 수치계수를 그대로 유지한다는 주장은 하지 않는다.

## provenance와 제한

- 최초 길잡이인 [astro-ph/9501016](https://arxiv.org/pdf/astro-ph/9501016)의 현재 제공 PDF는 arXiv stamp 1995-01-06과 title-page 생성 날짜 2018-10-17이 함께 있고, 확장된 bounds의 식 번호가 journal 판본과 다르다. 날짜를 publication year로 오인하지 않았고 S2의 원본 발행일/식 번호로 교차 확인했다. SciSpace 등 검색 메타데이터보다 원본 표지를 우선했다.
- S2의 density-gradient 표기에는 단위 점검이 필요한 지점이 있어 본 연구 입력의 수치 prior에 사용하지 않는다. 오래된 hierarchy의 세부 계수도 새 유한 residual 정리에는 그대로 전용하지 않고 S5의 비선형 hierarchy 또는 독립 유도로 확인해야 한다.
- 원전 접근: web 도구로 arXiv 텍스트를 열람했고, web PDF 접근이 실패한 두 1995 원문은 원출판사/ADS endpoint를 통해 직접 읽었다. SME는 5쪽 OCR과 핵심 원본 이미지 검증을 했다. 수치 우주 진화는 수행하지 않았다.
