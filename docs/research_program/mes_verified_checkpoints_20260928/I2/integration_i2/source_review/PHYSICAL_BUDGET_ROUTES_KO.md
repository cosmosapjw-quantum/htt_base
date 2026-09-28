# I2 source-budget 경로 비교

2026-09-28. 범위: I1의 \(Z=\sigma-\mathcal C_p a\), \(a=A/c\), \(\mathcal C_p z=\operatorname{STF}(pz^T)\)에 독립적인 물리 입력을 제공할 수 있는 세 경로를 비교했다. 수치 자료나 관측 잔차 예산은 취득하지 않았다. 본 문서는 후보 생성 보조이며 최종 독립 검토가 아니다.

| 경로 | 정확히 제거하거나 제한하는 것 | 추가로 필요한 입력 | 선택 |
|---|---|---|---|
| Geodesic target congruence: \(a=0\) | \(Z=\sigma\); 순간 등방장에서 dipole residual의 필요성 제거 | quadrupole residual \(r_2\)의 실제 time/spatial/source jet | 최소 모형으로 선택 |
| 비상호작용 barotropic perfect fluid | Euler 식으로 acceleration을 pressure gradient에 연결 | 같은 target frame의 압력 구배와 enthalpy 하한; 불완전 유체나 힘이 있으면 추가 항 | 확장 경로로 보류 |
| 독립 optical drift/cosmography | 조건부로 acceleration·shear에 대한 별도 관측 정보를 제공 | emitter/observer congruence, 거리, frame rotation, ray/endpoint 자료, truncation remainder, 공동 통계 법칙 | 현 입력에는 예산 없어 보류 |

## 1. Euler 경로의 정확한 전제

서명은 \((-+++)\), \(U^aU_a=-c^2\), \(h^a{}_b=\delta^a_b+U^aU_b/c^2\), \(D^U_a=h_a{}^b\nabla_b\)다. 물질 energy density를 \(\mu\), 압력을 \(P\)라 하여 tilt \(p\)와 구별한다. 별도 보존되는 perfect fluid

\[
T^{ab}_{\rm m}=\frac{\mu+P}{c^2}U^aU^b+P g^{ab},
\qquad\nabla_bT^{ab}_{\rm m}=0
\]

를 \(U\)에 직교 투영하면

\[
\frac{\mu+P}{c^2}A_a+D^U_aP=0,
\qquad a_a=-\frac{c D^U_aP}{\mu+P}. \tag{S1}
\]

이 식은 conservation law에서 직접 유도한 것으로, 자연단위 원문의 Euler 식과 일치한다. \(\mu>0,P=0\)인 dust이면 \(a=0\)이다. 반면 coarse-grained galaxy flow를 pressureless geodesic matter로 동일시하는 것은 관측의 결론이 아니라 모형 선택이다. 물질이 복사에 의해 힘을 받거나 imperfect stress를 갖는 경우 (S1)을 그대로 적용하지 않는다.

물리적으로 독립인 자료가 \(\|D^UP\|\le G_P\), \(\mu+P\ge W_{\min}>0\)를 제공하면

\[
\|a\|\le\frac{cG_P}{W_{\min}},\quad
\|\mathcal C_pa\|_F\le\sqrt{\frac23}|p|\frac{cG_P}{W_{\min}}. \tag{S2}
\]

단위는 모두 rate s\(^{-1}\)다. 우변의 예산은 이번 입력에 없으며, 복사식으로 역산한 같은 acceleration을 독립 prior로 재투입하지 않는다.

공간균질성만으로 \(D^UP=0\)이라 할 수 없다. 정규 congruence를 \(N^aN_a=-c^2\), \(U=\gamma(N+cp^iE_i)\), \(E_iP=0\), \(\dot P_N=N^a\nabla_aP\)라 쓰면 직접 투영하여

\[
D^U_aP=\frac{-N_a+\gamma U_a}{c^2}\dot P_N,
\qquad \|D^UP\|=\frac{\gamma|p|}{c}|\dot P_N|. \tag{S3}
\]

따라서 tilted target의 압력 구배는 일반적으로 남는다. (S3)은 본 보고서의 직접 유도이며 독립 symbolic execution은 하지 않았다. 정규 frame과 target frame의 동질성 조건을 혼동하지 않기 위한 식이다.

## 2. \(a=0\)를 선택해도 residual 예산은 생기지 않는다

I1 순간 등방식은

\[
Z=\frac{15}{8\rho}r_2-\frac{3}{4\rho}\mathcal C_pr_1.
\]

선언한 geodesic branch에서는 \(r_1=0\), \(Z=\sigma=15r_2/(8\rho)\)다. 이는 acceleration nuisance를 제거한다. Collisionless condition은 충돌항을 제거하지만, radiation time derivative 또는 projected spatial derivative를 제거하지 않는다. 서로 다른 frame의 공간 미분과 tetrad connection도 구별해야 한다.

문헌의 almost-EGS 전제 역시 anisotropy amplitude의 작음과 시공간 미분의 작음을 별도로 둔다. 본 연구는 그 미분 전제를 정적 CMB sky에서 추론하지 않는다. 정적 sky만으로 source-supported residual radius를 얻을 수 없다는 결론은 유지된다. 독립적인 동일 상태의 expansion/energy input이 있으면 아래 §4의 model-dependent coarse norm bound는 가능하다.

## 3. optical route를 이번 선택으로 삼지 않은 이유

관측 방향 drift에는 source/observer 상대운동에 따른 parallax와 observer acceleration에 따른 aberration이 함께 나타난다. 한 광선 위 angular Liouville generator를 그대로 proper motion으로 사용하면 안 된다. Covariant cosmography의 acceleration 추출도 같은 coarse-grained congruence, 광선 근사, caustic 배제, 전개 나머지 및 reference frame의 조건을 필요로 한다. 이론적으로 독립 acceleration 정보를 제공할 수 있지만 현재 입력은 그러한 공동 관측 예산을 포함하지 않는다.

## 4. 선택한 최소 분기의 더 강한 판별: Einstein–Vlasov

부모 연구의 선택에 맞춰, dust를 추가하지 않고 **Bianchi I의 geodesic normal congruence와 massless collisionless matter**로 \(a=0\) 분기를 구현하는 것을 권한다. \(p=0\), \(\Lambda=0\)를 선택하면 finite tilt의 추가 변수 없이 static sky가 residual을 제한하는지 판별할 수 있다. 이 제한된 반례가 성공하면 더 넓은 원래 domain에서 정적 CMB만으로 생기는 보편 상한을 주장할 수 없다.

원전 Rendall [R4] §2는 Bianchi I에서 covariant spatial momenta \(q_i\)로 쓰면 \(f(t,q_i)=f_0(q_i)\)임을 명시하고, metric 및 extrinsic curvature의 유한 차원 evolution system과 Hamiltonian/momentum constraints를 제시한다. 원문은 \(m=0\)을 포함한다. 원문 \(k_{ij}\)는 \(\dot g=-2k\), 원문의 \(H_R=\operatorname{tr}k\)이므로 부모의 expansion matrix \(K_{\rm exp}\)와는 \(k=-K_{\rm exp}\), \(H_R=-3H\) 관계다. 원문은 geometrized units이므로 SI 복원은 별도 수행해야 한다.

다음 local-existence 논증은 원문의 식에서 본 작업이 추론한 것이다. \(f_0\)를 원점에서 떨어진 compact momentum annulus에 지지되는 smooth nonnegative radial function으로 고정한다. SPD metric 근방에서는 \(q^Tg^{-1}q\)가 지지집합에서 양의 하한을 갖는다. 따라서 energy/stress integrals는 metric의 smooth 함수이고 Einstein evolution 우변도 smooth한 finite-dimensional ODE가 된다. 표준 ODE local existence가 적용된다. Radial \(f_0\)는 초기 STF shear를 diagonalize하는 회전 아래 불변이므로, diagonal frame에서는 원문의 reflection-symmetric subclass를 사용하고 이후 회전으로 되돌릴 수 있다.

따라서 이 경로는 prescribed-background kinetic counterexample보다 강한 **Einstein constraints를 만족하는 local solution family**를 구성할 수 있다. 다만 큰 shear마다 공통 길이의 존재구간, 공통 Hubble rate, 같은 전체 과거 광원 조건, 실제 CMB 관측 적합성은 따라오지 않는다. \(H\)를 고정한 가족과 \(H\)를 변동시키는 가족은 구별해야 한다. 원전의 결과를 본 프로젝트의 새로운 novelty로 제시하지 않는다.

### 부모 연구에서 확정한 I2 branch와 원전 대응

최종 분기는 \(\Lambda=0\), radiation-only massless Einstein–Vlasov, geodesic normal \(U\), \(p=0\)이다. 이때 \(\rho=\rho_\gamma\)를 energy density로 정규화하고 \(\kappa=8\pi G/c^2\)라 두면 초기 constraints는

\[
3H^2=\kappa\rho+\tfrac12\|S\|_F^2,\qquad j_i=0.
\]

\(g_0=I\), \(f_0(q)=F(|q|)\)와 \(\rho_0>0\)를 고정하고

\[
S_\lambda=\lambda\operatorname{diag}(2,-1,-1),\quad
H_\lambda=\sqrt{\lambda^2+\kappa\rho_0/3},\quad\lambda\ge0
\]

를 택한다. 이는 고정된 등방 radiation 초기분포와 양립하며 모든 초기 directional expansion rates \(H+2\lambda,H-\lambda,H-\lambda\)가 양수다. \(\|S_\lambda\|_F=\sqrt6\lambda\)는 절대 rate로 무한히 커질 수 있지만, 동시에 \(H\)도 변동한다. 정규화 비율은 \(\sqrt6\)에 접근할 뿐 무한하지 않는다. 이것은 순간 등방성이 almost-FLRW를 보장하지 않는 local witness다.

반대로 독립적인 **동일 상태의** \((H,\rho)\)가 주어지면 constraint 자체가
\[
\|S\|_F^2=6H^2-2\kappa\rho
\]
를 준다. 이 radius 조건은 STF 방향을 정하지 않는다. \(0<H\le H_+\), \(\rho\ge\rho_->0\)인 공동 admissible set이면 안전한 상계는 \(\sqrt{6H_+^2-2\kappa\rho_-}\)다. Radicand가 음수이면 그 입력조건의 feasible set은 empty이지 radius 0이 아니다. 이 상계는 CMB의 정적 anisotropy amplitude에서 얻은 것이 아니라 Einstein model과 독립 expansion/energy input에서 얻은 것이다. 전체 target set에 모든 방향별 expansion 양수까지 추가할 경우 \(HI+S\succ0\)와의 교집합을 취해야 하므로 단순 STF sphere 전체와 같다고 해서는 안 된다.

## 판정

- 최소 선택: geodesic normal Bianchi I massless Einstein–Vlasov 분기에서 정적 정보의 한계를 직접 판별한다.
- 물리 source: \(C=0\)은 정확히 닫힌다.
- residual/time-jet budget: 여전히 **unresolved**이며 작은 sky amplitude만으로 추가할 수 없다.
- Tensor direction 또는 더 좁은 bound에는 \(r_2\), 동일 상태의 radiation derivative, 또는 독립 optical shear 정보가 필요하다. Coarse finite norm bound는 동일 상태의 \(H,\rho\) 입력으로도 가능하다. 그러한 입력이 없으면 정확한 non-identification 결과로 이번 loop를 닫는다.
