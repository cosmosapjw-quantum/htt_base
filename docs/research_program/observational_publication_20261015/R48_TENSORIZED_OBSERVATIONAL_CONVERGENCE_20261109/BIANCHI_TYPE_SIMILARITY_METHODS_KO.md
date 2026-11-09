# 일반 Bianchi 유형의 기하학적 유사성과 tilt 식별가능성

날짜: 2026-11-09 (Asia/Seoul)  
연구선: R48 geometry-only extension  
상태: **DERIVED + STANDALONE NUMERICAL ORACLE PASS**  
정확한 repository import/pytest: **NOT_RUN**  
경험적 Bianchi family identification: **NOT CLAIMED**

## 1. 범위 잠금

이번 연구는 11개 Bianchi 유형 I, II, III, IV, V, VI₀, VI_h, VII₀, VII_h, VIII, IX의 **공간 Lie algebra와 주어진 직교 불변계량의 유사성** 및 normal-frame에 대한 tilted congruence의 **기하학적 orbit identifiability**만 다룬다.

포함:
- Ellis–MacCallum (a,n) 구조상수 분해와 Class A/B 및 h-분류
- SO(3) frame 회전과 공통 양의 homothety를 제거한 구조 fingerprint
- 왼쪽 불변 공간계량의 3D Ricci tensor와 곡률-only family degeneracy
- tilt vector v의 SO(3)-orbit invariant와 고유값 중복도에 따른 Jacobian rank / 연속 퇴화 차원
- 11개 canonical representative와 h 및 반복 고유값 경계의 독립 oracle

제외:
- Boltzmann hierarchy, Thomson kernel, recombination/visibility, line-of-sight, Cℓ 및 편광 transfer
- Bianchi background/tilted-fluid Einstein ODE를 새로 구성하거나 모든 유형의 physical tilted solution이라고 주장하는 것
- 관측 map, likelihood, Bayesian model selection, Cobaya/MCMC
- local-observer boost/aberration. 이는 FB-8의 GlobalTilt–ObserverBoost 구분을 재사용하되 현재 계산하지 않는다.
- optical first-jet/ray-generator, Jacobi/Sachs, redshift/direction drift. R10 결과는 선행 자산으로 보존하고 현재 scope에서 제외한다.

여기서 “tilt”는 공간절단 법선 nᵃ에 대한 matter congruence의 상대 3-속도 vᵃ만 의미한다. 관측자 peculiar velocity, radiation-to-matter boost, local observer boost와 동일시하지 않는다.

## 2. 구조상수와 Bianchi type

오른손 직교 불변 triad에서
\[
[e_i,e_j]=C^k{}_{ij}e_k,\qquad
C^k{}_{ij}=a_i\delta^k_j-a_j\delta^k_i+\epsilon_{ijm}n^{mk},
\]
여기서 nᵀ=n이고 Jacobi 조건은
\[
n^{ij}a_j=0.
\]
Class A는 a=0, Class B는 a≠0이다. h가 정의되는 Class-B rank-2 stratum에서는
\[
h=\frac{a_i a^i}{\lambda_1(n)\lambda_2(n)},
\]
여기서 λ₁,λ₂는 n의 두 nonzero eigenvalue다. h=-1은 Type III=VI_{h=-1}이고, h<0 및 h≠-1은 VI_h, h>0은 VII_h다.

### 2.1 대수적 type 판별

| Stratum | 판별 |
|---|---|
| Class A, rank(n)=0 | I |
| Class A, rank(n)=1 | II |
| Class A, rank(n)=2, nonzero eigenvalue 부호 혼합 | VI₀ |
| Class A, rank(n)=2, nonzero eigenvalue 같은 부호 | VII₀ |
| Class A, rank(n)=3, definite | IX |
| Class A, rank(n)=3, indefinite | VIII |
| Class B, rank(n)=0 | V |
| Class B, rank(n)=1 | IV |
| Class B, rank(n)=2, h=-1 | III |
| Class B, rank(n)=2, h<0, h≠-1 | VI_h |
| Class B, rank(n)=2, h>0 | VII_h |

이 규칙은 Bianchi Lie-algebra label을 복원한다. 공간 Ricci 곡률이나 관측 패턴만으로 Bianchi label을 결정한다는 주장은 아니다.

## 3. 구조 유사성 fingerprint

공통 양의 homothety와 proper SO(3) frame 회전을 제거하기 위해
\[
\kappa^2=|a|^2+\|n\|_F^2,\qquad
\widehat a=a/\kappa,\qquad \widehat n=n/\kappa
\]
를 정의한다. 구조 fingerprint는
\[
\mathcal F_{\rm alg}=
\left(\mathrm{type}(a,n),\,|\widehat a|,\,
\mathrm{spec}(\widehat n),\,h\right)
\]
로 둔다. Jacobi 조건 n a=0 아래에서 (a,n)의 SO(3) orbit은 이 정규화된 고유값 정보로 고정된다. κ는 similarity quotient에서 제거하지만 물리적 곡률 scale 복원을 위해 별도 저장한다.

본 quotient는 **orthonormal-frame metric Lie-algebra data modulo SO(3) × common positive scale**다. 임의의 좌표변환이나 일반적인 local isometry 분류를 대체한다고 주장하지 않는다. Parity 반전은 SO(3) quotient에 넣지 않으므로 handedness 관련 pseudoscalar를 보존한다.

## 4. 공간곡률 fingerprint와 정확한 비식별성

불변 triad의 Koszul 연결은
\[
\Gamma_{ijk}=\langle\nabla_{e_i}e_j,e_k\rangle
=\frac12\left(C_{kij}-C_{ijk}+C_{jki}\right).
\]
이를 곡률 정의에 넣어 3×3 공변 Ricci 행렬 Rᵢⱼ를 계산한다. 3차원에서는 Riemann tensor의 대수적 정보가 Ricci tensor로 결정되지만, Ricci eigenvalue spectrum만으로 일반 homogeneous metric의 전체 local-isometry class가 결정된다고 가정하지 않는다. 여기서는 curvature-only screening fingerprint로 사용한다.

### 4.1 정확한 곡률-only degeneracy A: I와 VII₀

Type I는 a=0,n=0으로 flat이다. Type VII₀의 대표 stratum n=diag(p,0,p), a=0에서도
\[
R_{ij}=0.
\]
따라서 두 대표 공간계량은 같은 flat intrinsic geometry를 갖지만, 서로 다른 simply-transitive Bianchi group action을 갖는다. 곡률-only 분류기는 group-action label을 식별할 수 없다.

### 4.2 정확한 곡률-only degeneracy B: V와 특별한 VII_h stratum

Type V에서 a=(a,0,0), n=0이면
\[
R_{ij}=-2a^2\delta_{ij}.
\]
Type VII_h에서 a=(a,0,0), n=diag(0,p,p), p>0이면 직접 계산으로 동일하게
\[
R_{ij}=-2a^2\delta_{ij},\qquad h=a^2/p^2>0.
\]
3차원에서 Einstein metric은 constant sectional curvature를 가지므로 두 대표는 같은 hyperbolic intrinsic geometry (K=-a²)를 갖지만 Bianchi group label과 simply-transitive action은 다르다.

이 결과를 “새 Bianchi equivalence theorem”이라고 과장하지 않는다. flat/open-FLRW limits와의 관계는 기존 homogeneous cosmology 문헌에 이미 들어 있다. 이번 연구의 가치는 이 정확한 퇴화를 all-type discriminator의 명시적 no-go test로 고정하고, 구조 fingerprint 및 tilt orbit의 추가 정보 효과를 계량화하는 데 있다.

## 5. Tilt orbit invariant와 식별가능성

v는 normal congruence nᵃ에 대한 물질 congruence의 dimensionless 공간 3-속도이며 |v|<1이다. Nhat=n/κ로 두고
\[
p_0=v^2,\quad p_1=v^T\widehat n v,\quad
p_2=v^T\widehat n^2v
\]
를 정의한다.

n의 고유 frame에서 λᵢ를 고유값, wᵢ=vᵢ²라 하면
\[
\begin{pmatrix}p_0\\p_1\\p_2\end{pmatrix}
=
\begin{pmatrix}
1&1&1\\
\lambda_1&\lambda_2&\lambda_3\\
\lambda_1^2&\lambda_2^2&\lambda_3^2
\end{pmatrix}
\begin{pmatrix}w_1\\w_2\\w_3\end{pmatrix}.
\]
이 moment Jacobian의 rank는 서로 다른 eigenvalue의 개수다. 세 eigenvalue가 distinct이면 squared tilt components는 복원되고, Class-A의
\[
\chi_A=\det[v,\widehat n v,\widehat n^2v]
\]
가 남은 discrete SO(3) handedness/orientation class를 고정한다. 반복 eigenvalue가 있으면 해당 eigenspace 안의 회전각이 식별되지 않으며, v가 그 eigenspace에 투영되는 경우 continuous azimuth degeneracy가 남는다.

Class B에서는 Jacobi 조건으로 a가 n의 kernel에 놓인다. 따라서
\[
\widehat a=a/|a|,\quad
q_0=\widehat a\cdot v,\quad
q_1=\widehat a\cdot(v\times\widehat n v)
\]
를 더 사용한다. rank-2의 두 nonzero eigenvalue가 distinct이면 p₀,p₁,p₂가 squared components를 복원하고 q₀,q₁가 부호/상대 방향을 고정한다. nonzero eigenvalue가 같으면 해당 2-plane의 SO(2) stabilizer 때문에 한 azimuth가 비식별이다. Type V의 n=0 stratum에서는 a축을 기준으로 transverse tilt의 azimuth 하나가 남고, Type IV rank-1에서는 a축과 n의 한 축이 나머지 null 방향을 고정하므로 일반적인 추가 azimuth는 남지 않는다.

moment matrix의 조건수는 eigenvalue 충돌에 가까워질수록 커진다. exact rank 판정과 practical identifiability/conditioning은 구분한다. 여기서 계산한 것은 기하학적 tilt orbit의 식별가능성이지 Einstein constraint를 만족하는 물리적 fluid solution이나 observational posterior가 아니다.

## 6. 기존 HTT/BASS 연구의 사용 범위

- BASS bianchi_types.py: all-11 (a,n,C) canonical algebra와 Class-A/Class-B/구조상수 convention을 SSOT로 재사용.
- BASS tilt_kinematics.py: current adapters가 acceleration과 vorticity의 부분 항만 전달한다는 제한을 보존. 이를 complete physical vorticity oracle로 쓰지 않는다.
- FB-6 full-coverage test: 22개 fixture가 존재하지만 beta=.1 및 정렬된 tilt 방향의 regression surface이고, DℓTT 일부는 실제 Boltzmann LOS가 아닌 proxy다. all-type physical tilted Einstein solution 증거로 사용하지 않는다.
- FB-8 SDD: global cosmological tilt와 local ObserverBoost를 type-distinct로 분리하는 기존 설계. current fingerprint는 observer boost를 포함하지 않는다.
- KE-OBS seal: LRS Bianchi I/V의 exact kinematic frame 결과는 prior지만, oblique Type-I vorticity의 Einstein-constraint compatibility는 해결되지 않았다.
- R10 first-jet ray-generator inverse, WU-009/010/011 및 R47 Bianchi-I temperature map은 선행 자산으로 보존하되 이번 scope에는 포함하지 않는다.

## 7. 검증 결과와 claim ceiling

독립 temporary package에서 canonical all-11 (a,n,C) fixtures로 35개 pytest가 통과했다. 추가로 유형별 100개의 proper SO(3) rotation과 common positive scaling을 적용한 1,100개 case에서 geometry fingerprint의 최대 residual은 8.9×10⁻¹⁶, tilt fingerprint의 최대 residual은 2.8×10⁻¹⁶이었다. VI₀ 대표의 rank-3 moment inverse는 eigenframe squared tilt components를 최대 절대오차 5.6×10⁻¹⁷로 복원했다. 다만 exact repository import/pytest는 미실행이다.

### 허용되는 주장
- 11개 Bianchi type을 (a,n) rank/inertia/h strata로 판별하는 algebraic classifier.
- SO(3) × common-positive-homothety quotient의 구조 fingerprint.
- 정확한 curvature-only non-identifiability examples.
- tilt orbit invariant와 repeated-eigenvalue 조건의 analytic rank/degeneracy characterization.
- Boltzmann solver 없이 수행하는 geometry-only screening/triage.

### 허용되지 않는 주장
- 관측으로 Bianchi type이 검출되었다.
- tilt가 모든 유형에서 동역학적으로 실현 가능하거나 Einstein constraints를 만족한다.
- curvature fingerprint가 일반 local-isometry classifier다.
- 모든 Bianchi type의 CMB pattern, Cℓ, 편광 또는 likelihood를 재현했다.
- local observer boost, global fluid tilt, fluid vorticity가 동일하다.
