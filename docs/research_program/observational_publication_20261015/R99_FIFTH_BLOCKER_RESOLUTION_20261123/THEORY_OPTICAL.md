# R99 · Bianchi 배경의 유한 적색편이 Jacobi 거리와 프레임 응답

## 결과와 적용 조건

R98의 R49 Einstein–Euler 궤적에서 같은 관측 사건을 지나는 광선족을 하늘 방향으로 미분하면, 사건별 단면적과 측정 적색편이에서의 각지름거리 \(D_A(z,\hat n)\)를 구성할 수 있다. 광자 파수 \(k\)의 정상계 에너지 \(E\), 전파방향 \(p\), 각도에 대한 방향 변화 \(Q_A\), 이웃 광선 사이의 위치 변화 \(X_A\)가 필요한 상태다. 위치 변화는 같은 시각의 서로 다른 광선 끝점 사이의 물리적 변위다. 기존 수송기의 편광 screen 벡터만으로 그 크기를 정할 수 없다.

유도는 공간적 균질성, 단위 lapse·영 shift를 갖는 geodesic normal congruence, Fermi 수송한 정규직교 spatial tetrad, torsion-free Levi-Civita 접속, 기하광학을 가정한다. \(H>0\)인 구간에서 \(N=\ln a\)를 시계로 쓴다. Class A/B의 구분은 \(C^k{}_{ij}\)에 들어가며 별도 유형별 좌표 chart가 필요하지 않다. R98이 실제로 제공하는 초기값은 FLRW, I, V, VII_h, VI_h 다섯 개다. 그 밖의 계열은 동일 조건을 만족하는 실제 \(H,\sigma,A,n\) 이력을 추가로 지정해야 한다. 이 절의 수치는 두 정확한 시험계량에 대한 경량 계산이다. 실측 거리·모수 제약과 원시 복사수송은 별개 의무로 남는다.

## R2–R3 · 원본과 관례

기준 커밋은 `eee33d7ed33e1af10d7c6a3c453810ecb227e461`이다. 경로는 `htt_base` 루트 기준이다.

| 재사용 원본 | 역할 | 기준 파일 SHA-256 |
|---|---|---|
| `htt/bass/background/convention_bridge.py` 304행 | `build_structure_tensor_with_sign`, R49에서 `a_sign=+1` | `28042f5a6ab15e3039f90a3dd6d2ce21d32f8b1192a69147f9844881e1b72a6b` |
| `htt/bass/background/tilted_bianchi_state.py` 421행 | `build_4d_bianchi_connection`, 미분 인덱스가 마지막 | `e36dd616f4d0e2998e48e1a50ae9b67e1cd48842ef5b52ee2b1e4b94b888fe04` |
| `htt/bass/background/general_tilted_evolution.py` | R49 배경, 구조상수 시간진화, 궤적 종별 속도 | `9679d7651a0f29adae712afc8fff9a67731f88970925ce1ef9bdb5f42d207ddd` |
| `htt/bass/transport/general_bianchi_transfer.py` 590행 | `integrate_polarized_geodesics`, \(p_o=-n,\ \ln(E/E_o)=0\)에서 출발하는 역방향 적분 | `9bcb541d35cabc05b8c325a58bbef57f253627203ff1ac1c354e4bd789f60410` |
| `scripts/r98/bianchi_history.py` 52, 82, 92행 | `early_state/background/background_checks`, 초기 정상계 및 \(H_*\) 단위 복원 | `034eed5ae0429153f24949aca2e5d8e820ba36200198a1610e8c8551ac137404` |

계량 부호는 \((-+++)\)이다. 실제 R98에서 \(H_*=H_{\rm ref}(z_v=1600)\,[{\rm s}^{-1}]\), \(\tau=H_*t\), \(x_{\rm unit}=c/H_*\)이다. 아래 \(H=dN/d\tau\), \(\sigma,A,n,C,\Gamma\)는 해당 기하 단위의 무차원 값이다. \(p\)는 미래향 광자의 신체축 성분이고 \(n=-p_o\)는 정상계 하늘에서 소스를 향하는 시선이다. 궤적 데이터는 \(N_i\le N\le N_o\)에서만 보간한다. 적분은 \(N_o\)에서 과거로 진행한다.

## R4–R5 · 광선족의 일차 변화

\(u=(1,p)\), \((\nabla_{e_a}e_b)^d=\Gamma^d{}_{ba}\), \(B^d=\Gamma^d{}_{ba}u^bu^a\)라 놓는다. 무차원 정상계 광자 에너지는 관측점의 정상계 값으로 나누었으며 \(\mathcal E=E/E_o\), \(\mathcal E_o=1\)이다. 지오데식 방정식의 0성분과 공간 성분을 나누면

\[
(\ln\mathcal E)'=-B^0/H,\qquad p'=(-B^{\rm sp}+p B^0)/H,\qquad '=d/dN .
\tag{1}
\]

\(e_0,e_i\)는 \([e_0,e_j]=-K^k{}_je_k\), \(K=H I+\sigma\), \([e_i,e_j]=C^k{}_{ij}e_k\)를 만족한다. 관측점 정상계 하늘에서 정규직교 접기저 \(s_1,s_2\)를 고르고 국소 각변수 \(\alpha_A\)의 미분 \(\partial_A n=s_A\)를 정의한다. 일반 위도 좌표의 \(\partial_\phi n\)에는 \(\sin\theta\)가 있으므로 이를 단위각 벡터와 혼용하지 않는다. \(Q_A=\partial_A p|_\tau\)를 도입한다. 균질성으로 \(\partial_A\Gamma(\tau)=0\)인 tetrad 성분에서 식 (1)을 미분하면

\[
\delta_A B^d=\Gamma^d{}_{ba}\{(0,Q_A)^b u^a+u^b(0,Q_A)^a\},\quad
Q_A'=\frac{-\delta_A B^{\rm sp}+Q_A B^0+p\,\delta_A B^0}{H}.
\tag{2}
\]

광선족의 시공간 사상 \(F(\tau,\alpha)\)에서 \(\partial_\tau F=u^ae_a\), \(\partial_AF=X_A^ie_i\)라 둔다. \(X_A^0=0\)은 같은 정상계 시간 slice에서 비교한 결과다. 좌표계에서 \(\partial_\tau\partial_A F^\mu=\partial_A\partial_\tau F^\mu\)를 쓰고, 위치에 의존하는 frame 벡터도 미분하면 \(\partial_\tau X_A^c-\partial_Au^c=-C^c{}_{ab}u^aX_A^b\)이다. 따라서

\[
 (X_A^k)'=
 \frac{Q_A^k+K^k{}_jX_A^j-p^i C^k{}_{ij}X_A^j}{H}.
 \tag{3}
\]

식 (1)–(3)의 IC는 \(p_o=-n,\ \ln\mathcal E_o=0,\ Q_{A,o}=-s_A,\ X_{A,o}=0\)이다. 무차원 시간과 길이에서 \(X_A\)의 단위는 \(c/H_*\)당 측정한 물리적 길이/단위각이다. 관측점 가까이서 \(X_A=s_A(\tau_o-\tau)+O((\tau_o-\tau)^2)\)이며 단위길이로 바꾸면 \(c(t_o-t)s_A\)이다. 이 부호가 관측자 근방에서 양의 거리와 양의 표준 parity를 고정한다.

아핀 광선의 접벡터를 \(k\)라 하면 고정 아핀 매개변수에서 생성한 Jacobi 변분 \(J\)는 꼭짓점의 \(k\cdot J=0\)을 유지한다. \([k,J]=0\), \(\nabla_k k=0\) 및 \(J(k^2)=0\)이므로 \(d(k\cdot J)/d\lambda=0\)이다. 각 광선을 고정 \(\tau\)나 고정 \(z\) 절단으로 옮기면 연결 벡터에 \(k\)의 배수가 더해진다. 따라서 \(k^\perp/\langle k\rangle\)에서 같은 변분이고, \(X_A\)의 정상계 성분은 \(p\cdot X_A=0\)을 만족한다. 수치에서는 \(|p|^2-1,\ p\cdot Q_A,\ p\cdot X_A\)를 함께 추적할 수 있다.

소스의 Sachs screen 기저 \(b_B\)는 수송한 두 정규직교 벡터의 정상계 공간 대표를 쓰면 된다. 기존 `integrate_polarized_geodesics`의 공간 screen 수송은 매 단계 \(k\) 성분을 더해 시간 성분을 0으로 고정한 대표다. 정상계 하늘 각도를 열로 하는 \(2\times2\) Jacobi 행렬은 \(\mathsf J_{BA}=(c/H_*)\,b_B\cdot X_A\)이다. \((s_1,s_2)\)를 \(s_1\times s_2=n=-p_o\)로 잡고 같은 orientation을 수송하면, oriented determinant의 무차원 값은 \(S=-p\cdot(X_1\times X_2)\)이다. 초기 양의 orientation을 다른 방식으로 지정하면 기준 orientation 부호를 함께 기록한다. 벡터와 행렬은 screen 회전에 따라 변하지만 \(D_{A,n}=(c/H_*)\sqrt{|S|}\)는 불변이다. \(|S|\)만 저장하면 초점 통과시 영상 parity가 소실된다.

## 프레임 변환과 동일 측정 적색편이의 절단

관측자와 방출자 속도 \(\boldsymbol\beta_{o,e}=\boldsymbol v_{o,e}/c\)를 각 사건 정상계에서 지정한다. \(\mathcal D=\gamma(1-\boldsymbol\beta\cdot p)>0\)이고 \(-k\cdot U=\mathcal D E\)이므로

\[
 1+z(N)=\mathcal E(N)\,\mathcal D_e(N)/\mathcal D_o,\qquad
 D_{A,\rm obs}=\mathcal D_oD_{A,n},\qquad
 D_L=(1+z)^2 D_{A,\rm obs}.
 \tag{4}
\]

면적 관계는 광자 방향의 Lorentz 수차 \(d\Omega_{\rm obs}=\mathcal D_o^{-2}d\Omega_n\)에서 따른다. 방출자 screen으로 옮긴 \(X_A\)는 \(X_A+k f_A\) 꼴이어서 쌍별 내적을 보존한다. 방출자 속도는 지정 사건에서 에너지에 들어가고, 고정한 측정 적색편이에서는 방출 사건도 바꾼다. 마지막 거리는 metric geometric optics, 투명 전파, 광자 수 보존을 사용한다. 주어진 \(D_L\) 정의에 의해 만든 duality 잔차를 독립 검증으로 집계할 수는 없다.

하늘 좌표가 관측자 고유계에 지정되면 \(p'=-n_{\rm obs}\)에서 정상계 방향을 먼저 복원한다. \(d=\gamma_o(1+\beta_o\cdot p')\),
\[
p_o=\{p'+[\gamma_o+\gamma_o^2(\beta_o\cdot p')/(\gamma_o+1)]\beta_o\}/d,\qquad
\mathcal D_o=1/d.
\]
정상계 접기저에서 \(Q_{A,o}=-s_A\)를 초기화하면 최종 거리에 식 (4)의 \(\mathcal D_o\)를 한 번 곱한다. 관측자 고유계 단위각에 대해 역수차 사상의 미분을 직접 취해 \(Q_{A,o}=\partial p_o/\partial\alpha^{\rm obs}_A\)를 초기화하는 대안에서는 변위 열에 이미 해당 수차가 들어 있으며 \(D_A=(c/H_*)\sqrt{|S|}\)를 그대로 쓴다. 전 Jacobi 행렬을 지정 관측자 기저에 표시하려면 역수차 방향 미분의 \(2\times2\) 각도행렬을 정상계 Jacobi에 우곱한다. 이 행렬은 배율 \(\mathcal D_o\)와 두 하늘 기저 사이 회전을 포함한다.

식 (4)의 \(z(N)=z_{\rm target}\)은 실제 이력 내부에서 푼다. 부피 적색편이 \(z_v=e^{-N}-1\)는 별도 변수다. \(\mathcal D_e(N_o)\ne\mathcal D_o\)이면 광로 길이 0인 끝점에도 \(z_o\ne0\)일 수 있다. 임의의 적색편이 이력에는 다중근·접근·범위 밖 목표가 가능하다. 단조성이 보인 구간의 유일근 또는 명시한 가지를 보고하고, 복수 교차나 접하는 근에서는 가지와 해상도 한계를 기록한다. 단순 부호 반전 탐색은 접근을 누락할 수 있다. 관측점의 꼭짓점 \(S=0\)과 물리적 caustic을 구분하며, 중복 초점은 부호를 바꾸지 않을 수 있다. 초점 이후 결과는 영상별 parity 및 가지를 지정한 거리다.

## R4 · 대안인 곡률 적분

\(R(X,Y)Z=\nabla_X\nabla_Y Z-\nabla_Y\nabla_X Z-\nabla_{[X,Y]}Z\)의 부호에서, \(R^a{}_{bcd}e_a=R(e_c,e_d)e_b\)로 정의하면
\[
 R^a{}_{bcd}=e_c\Gamma^a{}_{bd}-e_d\Gamma^a{}_{bc}
 +\Gamma^a{}_{mc}\Gamma^m{}_{bd}-\Gamma^a{}_{md}\Gamma^m{}_{bc}
 - C^m{}_{cd}\Gamma^a{}_{bm}.
\]
관측자 고유계의 광자 에너지를 1로 정규화한 과거향 아핀 접벡터 \(l\)에 대해 \(\mathsf D''=\mathcal T\mathsf D\), \(\mathcal T_{AB}=g(b_A,R(l,b_B)l)\), \({\rm tr}\,\mathcal T=-R_{\mu\nu}l^\mu l^\nu\), \(\mathsf D(0)=0,\ d\mathsf D/d\lambda(0)=I\)이다. 여기서 두 번의 미분은 과거로 증가하는 무차원 아핀 변수에 대한 것이다. 식 (1)의 에너지 표기에서는 \(dN/d\lambda=-H\mathcal E/\mathcal D_o\)이다. 이 방법에는 \(\sigma,H,C\)의 시간미분 또는 Einstein–Euler RHS 재평가가 필요하다. 식 (3)은 같은 screen quotient의 infinitesimal beam을 tabulated geometry만으로 계산한다. 두 유한각 광선의 끝점 차분을 쓰는 방법에는 공통 위치 chart 및 각폭 수렴 검사가 더 필요하다.

## R7 · 판별 계산과 재현

평탄 FLRW에서 \(C=\sigma=0\)이므로 \(p,\ Q_A\)가 일정하고 \(X_A=a_e s_A\int_{\tau_e}^{\tau_o} d\tau/a\)이다. \(D_A=c a_e\int_{t_e}^{t_o}dt/a\), \(1+z=a_o/a_e\)를 얻는다. 다음 두 수치 시험의 단위는 \(t_o=H_*^{-1}\), \(t_e=t_o/2\), 길이 \(ct_o\)다. 종단 방향은 \(p_o=(0,0,-1)\)이다.

- 빈 Milne 우주의 V tetrad에 \(a=t/t_o,\ A=(0.6,0.8,0)t_o/t,\ n=\sigma=0\)를 둔다. 열린 FLRW의 정확한 거리는 \(D_A/(ct_o)=(t_e/t_o)\sinh[\ln(t_o/t_e)]=0.375\)다. 이 기저에서 광자 방향이 변하므로 \(p^i C^k{}_{ij}X^j\)의 부호를 판별한다.
- 진공 Kasner I에서 \(a_i=(t/t_o)^{q_i},\ q=(-2,3,6)/7\)로 택한다. \(\sum q_i=\sum q_i^2=1\)이다. 관측점에서 \(a_i=1\)이므로 보존 공간 공변운동량은 관측 방향 성분에 비례한다. 3축 광선에서 \(E/E_o=1/a_3\)이고, 횡방향 운동량 \(k_i\)를 미분하면 \(\partial(dx^i/dt)/\partial(k_i/E_o)=ca_3/a_i^2\)이다. 따라서 \(J_i=ca_i(t_e)\int_{t_e}^{t_o}a_3/a_i^2\,dt\), \(i=1,2\), \(D_A=\sqrt{J_1J_2}\)이다. 일반 Bianchi I의 Jacobi 행렬 및 Saunders 거리와 연결되는 원문은 Fleury, Pitrou & Uzan, *Phys. Rev. D* **91**, 043511 (2015), 식 (7.8), (7.15)–(7.17) 및 Appendix이다. [저자 제공 원문](https://www2.iap.fr/users/pitrou/publi/1410.8473.pdf) · [DOI](https://doi.org/10.1103/PhysRevD.91.043511)

| 지표 | Milne V | Kasner I |
|---|---:|---:|
| 측정 \(z\) | 1.000000000000065 | 0.8114473285278134 |
| 해석 \(z\) | 1 | 0.8114473285278132 |
| 광선족 \(D_A/(ct_o)\) | 0.37500000000005757 | 0.38966059821700305 |
| 해석/독립 1D 구적 \(D_A/(ct_o)\) | 0.375 | 0.3896605982169172 |
| 거리 상대오차 | \(1.5343\times10^{-13}\) | \(2.2049\times10^{-13}\) |
| 끝점 \(\max_A|p\cdot X_A|\) | \(5.24\times10^{-14}\) | 0 |

아래 Python 블록은 두 시험의 전체 입력으로, 생산 모듈은 접속·구조상수 생성기만 import한다. 저장소 루트에서 다음 두 명령으로 이 문서에 포함한 코드를 각각 실행할 수 있다.

```bash
doc=docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123/THEORY_OPTICAL.md
awk '/^```python$/{f=1;next} f && /^```$/{exit} f' "$doc" | PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=htt .venv/bin/python - milne
awk '/^```python$/{f=1;next} f && /^```$/{exit} f' "$doc" | PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=htt .venv/bin/python - kasner
```

```python
import sys
import numpy as np
from scipy.integrate import quad, solve_ivp
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.background.convention_bridge import build_structure_tensor_with_sign

case = sys.argv[1]
assert case in ("milne", "kasner")
milne = case == "milne"
q = np.ones(3) if milne else np.array([-2., 3., 6.]) / 7
m, te = q.mean(), .5
initial = np.r_[0., [0., 0., -1.], [-1., 0., 0., 0., -1., 0.], np.zeros(6)]

def rhs(N, y):
    t = np.exp(N / m)
    H, K = m / t, np.diag(q / t)
    A = np.array([.6, .8, 0.]) / t if milne else np.zeros(3)
    C = build_structure_tensor_with_sign(A, np.zeros((3, 3)), a_sign=1)
    G = build_4d_bianchi_connection(H, K - H * np.eye(3), C)
    p, Q, X = y[1:4], y[4:10].reshape(2, 3), y[10:].reshape(2, 3)
    u, U = np.r_[1., p], np.c_[np.zeros(2), Q]
    B = np.einsum("dba,b,a->d", G, u, u)
    dB = np.einsum("dba,rb,a->rd", G, U, u) + np.einsum("dba,b,ra->rd", G, u, U)
    dp = (-B[1:] + p * B[0]) / H
    dQ = (-dB[:, 1:] + Q * B[0] + p * dB[:, :1]) / H
    dX = (Q + X @ K.T - np.einsum("kij,i,rj->rk", C, p, X)) / H
    return np.r_[-B[0] / H, dp, dQ.ravel(), dX.ravel()]

sol = solve_ivp(rhs, (0., m * np.log(te)), initial, method="DOP853",
                rtol=2e-11, atol=2e-13)
assert sol.success, sol.message
y = sol.y[:, -1]
p, X = y[1:4], y[10:].reshape(2, 3)
DA = np.sqrt(abs(p @ np.cross(*X)))
analytic = te * np.sinh(np.log(1 / te)) if milne else np.sqrt(np.prod([
    te**q[i] * quad(lambda t: t**(q[2] - 2 * q[i]), te, 1)[0] for i in (0, 1)
]))
z, z_exact = np.expm1(y[0]), te**(-q[2]) - 1
print(case, "z,exact", z, z_exact, "distance,exact", DA, analytic,
      "relative_error", abs(DA / analytic - 1), "max_abs_pX", max(abs(X @ p)))
assert abs(DA / analytic - 1) < 1e-9 and abs(z - z_exact) < 1e-9
```

## R9 · 실제 이력에서의 인계

입력은 궤적의 \(N,H,\sigma,A,n\), 물리적 \(H_*\), 선택한 정상계 방출자 속도 이력 \(\beta_e(N)\), 관측자 \(\beta_o\), 하늘 기저, 목표 측정 \(z\)다. 반환에는 이력·프레임 ID, 소스 \(N\), \(\mathcal E,\mathcal D_e,\mathcal D_o\), 실제 측정 \(z\) 잔차, signed area, \(D_A,D_L\) 및 길이 단위, 근 가지와 초점 판정의 근거가 들어간다. 한 방향의 동일 사건에서 boost를 바꾸는 실험과 동일 측정 \(z\)에서 서로 다른 사건을 대조하는 실험은 다른 응답을 준다. R98 실제 거리에는 궤적·광학 적분 수렴 및 프레임별 근을 계량해야 하며, 해당 테스트 결과는 구현 기록에서 별도로 판정한다.
