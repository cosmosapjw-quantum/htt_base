# Legacy 전수 코드 정독·통합과 DP–MZ 확장 연구

2026-11-23 KST · 첨부 18개 패키지 · R1–R10 이론 연구 · 탐색 결과

이번 산출물은 **원본 보존형 통합 카탈로그와 실행 가능한 유한계 연구 core**다. 첨부 코드의 실제 본문을 읽어 역할·입출력·의존성·한계·재사용점을 기록하고, 동일 바이트를 하나로 모았다. 서로 다른 구현과 문서 변형은 SHA별로 유지했다. 이를 바탕으로 기존 두 단계의 DP–MZ 연구를 여덟 경로로 확장하고, 직접 유도·반례·수치 계산을 수행했다.

실제 GitHub의 기준은 `main`과 연구 branch를 구별했다. 아래 결과를 current production solver에 병합하거나 과학 DAG의 완료 상태로 승격하지 않았다. **원 저장소 수정·stage·commit·push는 없다.**

## R1. 연구 위치와 실행 계약

### 질문

첨부 legacy에서 실제로 계산하는 수학적 연산을 추출하면, 최근 연구의 다음 두 축을 어느 부분까지 보강할 수 있는가?

1. Doi–Peliti(DP)의 공동 확률법칙·선택 과정과 Mori–Zwanzig(MZ)의 숨은 상태·memory를 현재 물리 응답 및 다섯 관측 변수에 연결한다.
2. 독립변수를 물리적 시간에 한정하지 않고, 노출·flux cut·평활화·optical depth·covariance parameter·depth 등의 변화에 대한 응답으로 해석한다.

이번에는 특정 closure 하나를 채택하는 수렴 단계로 바꾸지 않았다. 먼저 상이한 실패 원인에 대응하는 여덟 후보를 만들고, 각각을 구체적인 생성자·projection·관측량·저비용 반례에 연결했다. 숫자나 label만 재정리하는 대신 공통 수학 함수를 구현했다.

### 기준과 권한

| 항목 | 확인한 기준 |
|---|---|
| 저장소 | `cosmosapjw-quantum/htt_base` |
| GitHub main | `f1007dd3e41c07eccd64024dd6b44fb5a40a3612` |
| 연구 branch | `research/r69-observable-physics-bridges-20261118` |
| 연구 HEAD | `f8931fbef075d55c2c2a3caee8b8f5db5174b16b` |
| 실제 R100 과학 변경 commit | `11f906a06f340ab96f9c35899600d205ef02a46b` |
| 연구 branch와 main 차이 | ahead 1097 / behind 0 |
| canonical science graph | R78 `INTEGRATED_DAG.json`, 60 nodes / 129 edges |
| 원 graph SHA-256 | `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11` |

HEAD는 read-only `git ls-remote`와 GitHub connector로 확인하고 작업 말미에 다시 대조했다. R100 보고서 전체를 읽었으며, 현재 연결할 API의 SHA와 signature를 확인했다. **이번 전수 정독의 분모는 첨부 코드다. 현재 저장소 전체를 새로 전수 정독했다는 뜻이 아니다.** 로컬에 보존한 graph reference는 JSON 재직렬화본이므로 원본 graph와 semantic reference이며 byte identity를 주장하지 않는다. 상세는 `CURRENT_REFERENCE_PROVENANCE.json`에 있다.

R100은 이미 CF4 SDSS/6dF genealogy·sign, full-k covariance, finite-redshift optical drift, radio GLM/reselection, Gaia supported-subspace whitening, self-consistent radiation/shear/baryon 계산을 보유한다. legacy가 이를 대체하도록 제안하지 않는다. 추가 연구는 이 실제 연산자와 확률법칙의 어느 경계에 연결할지를 정한다. R100 보고서와 current code anchor가 이 상태 설명의 출처다.

## R2. 전수 정독·중복 통합·근거 재사용

### 정독의 분모와 내용

| 항목 | 결과 |
|---|---:|
| 첨부 최상위 ZIP | 18 |
| 재귀적 원본 파일 위치 | 2,961 |
| 서로 다른 원본 바이트 | 2,430 |
| 동일 바이트로 통합한 중복 출현 | 531 |
| 본문 의미 검토를 마친 고유 코드 | **992 / 992** |
| 추가로 전체를 읽은 build recipe | 2 Makefiles |
| 전체를 읽은 archive 진입 README | 17 |
| 형식별 파싱·색인한 non-code objects | 1,438 |
| 서로 다른 내용의 동일 basename 코드 family | 156 |
| 서로 다른 바이트이지만 AST가 같은 group | 7 |
| 코드 정독 누락 | **0** |

고유 코드 구성은 Python 853, Rust 131, shell 4, Wolfram `.wl/.wls` 4다. 전부 본문 또는 검토된 base+전체 exact diff로 읽었다. 읽기 방식별 합계: full_source 907, base_plus_full_diff 85.

정독 기록은 각 SHA마다 역할, 실제 동작, 입력과 출력, 의존성, 함수 또는 근거 위치, 한계, DP–MZ 연결을 담는다. 전체 원문을 읽은 경우와 이미 읽은 base에 **전체 diff를 읽고 재구성을 확인한 경우**를 구별했다. 단순 AST·hash scan을 정독으로 세지 않았다. 같은 바이트의 여러 위치는 하나의 본문 검토를 공유하지만, 위치에 따라 달라질 수 있는 import resolution은 별도 한계로 남겼다.

보조 문서·그림·데이터는 모든 파일의 바이트를 보존하고 형식에 맞게 파싱·색인화했다. PDF는 텍스트 추출, 그림은 전체 decode와 OCR, NPZ는 배열 헤더와 실제 numeric array 로드, XLSX는 모든 셀·formula XML, JSON/CSV/JSONL는 전체 구조·행을 확인했다. **821개 텍스트 문서의 모든 수학적 논증과 231개 그림을 전부 의미적으로 심사했다는 뜻은 아니다.** 331개 `.pyc`는 header와 가능한 source 경로만 기록하고 실행·역컴파일하지 않았다.

파일 자체의 결손도 보존했다. `mz_cmb_truncation/summary.json`은 2,774문자에서 `Sigma_exact_at_iomega` 값을 쓰다 끊긴 JSON이다. `extract_cmb_like_products.py`의 한 역사적 변형은 line 28의 끝나지 않은 문자열 때문에 Python parse가 실패한다. 원본 파일을 조용히 복구한 것처럼 표시하지 않았다. scanner의 NumPy private API 오류와 OCR thread timeout은 도구 실행 문제로 분리해 public header API·제한된 thread 설정으로 재검사했고, 원본 truncated JSON만 남았다.

### 통합의 세 층

| 층 | 실제 처리 | 보존한 구별 |
|---|---|---|
| 파일 바이트 | SHA-256별 원본을 `consolidated/`에 한 번 저장 | 모든 archive/member alias와 원본 경로 |
| 코드 변형 | 같은 basename·AST identity 후보를 별도 index로 묶음 | 다른 바이트·주석·import path·API·provenance는 유지 |
| 반복 수학 연산 | `canonical/research_primitives.py`에 공통 함수 구현 | 원 코드와 교정 core를 분리하고 source SHA·검산을 연결 |

`FILE_OCCURRENCES.tsv`는 2,961개 원본 위치의 장부이고 `FILE_CATALOGUE.json`은 2,430개 고유 바이트의 역할 장부다. `EXACT_DUPLICATES.json`, `VARIANT_FAMILIES.json`, `AST_IDENTICAL_VARIANTS.json`은 서로 다른 동일성 기준을 제공한다. 단일 Python package에 오래된 `to_mio.py`들을 덮어쓰면 HTT posterior adapter와 BASS forward stub가 뒤섞이므로 그렇게 통합하지 않았다. 원 import layout은 `tools/materialize_archive.py`로 복원한다.

### 기존 두 연구에서 재사용한 결과

첫 연구의 exact block memory, unresolved initial force, 동일 parent의 중첩 선택 covariance, Gamma–Poisson/hidden-intensity 확장은 정의를 유지해 재사용했다. 두 번째 연구의

\[
\partial_s\mathbb E_s A=\mathbb E_s(\partial_s A)+\operatorname{Cov}_s(A,\partial_s\log p_s)
\]

와 normalized Feynman–Kac, 두 clock Jacobian, moving basis connection, optical event endpoint 보정도 재사용했다. 이번 새 기여는 이 일반식들을 실제 legacy 실패 지점에 대입하고, 양의 denominator의 signed ratio·전역 순위의 교환가능성·Legendre polynomial convention 등 구체적인 구현 조건으로 내린 것이다.

### 외부 이론의 적용 위치

- **Ma–Bertschinger (1995), Eqs. (49)–(51)**: free-streaming hierarchy와 유한 절단의 반사 문제. 실제 계산은 해당 선형 hierarchy의 source-free 부분에 한정한다. [L1]
- **Blas–Lesgourgues–Tram (2011), §§2–4, Appendix B**: TCA/UFA/RSA는 서로 다른 영역의 근사이며, spherical-Bessel 형태와 high-multipole 절단을 이용한다. 본 연구의 finite-tail 구조 보존이 CLASS의 완성된 근사를 대체한다고 주장하지 않는다. [L2]
- **Zhu–Venturi (2018)**: MZ memory를 Faber 전개로 근사하는 대안. real-pole few-mode ansatz를 유일한 경로로 취급하지 않는 근거다. abstract와 공개 primary text의 관련 부분을 확인했으며 본 구현에 Faber 수렴정리를 이식한 것은 아니다. [L3]
- **Levermore (1996)**: entropy 기반 moment hierarchy의 문헌상 토대. 여기서 직접 증명하는 결과는 finite positive law의 국소 KL 잔차이며 일반 kinetic hierarchy의 모든 실현가능성 정리를 가져오지 않는다. [L4]
- **Dufour (2006), Lemma 2.1 및 §2**와 **Phipson–Smyth (2010)**: Monte Carlo rank의 유한표본 보정과 exchangeability. 이번 nested min-local-rank 절차의 대칭성·반례는 직접 구성했다. [L5,L6]

SciSpace, Exa, Parallel은 문헌 후보·primary text 교차 확인에 사용했다. Wolfram 서비스는 context/evaluation 연결 오류로 계산을 수행하지 못했다. 아래 기호 검산은 **SymPy 1.14.0**, 수치 검산은 **NumPy 2.3.5 / SciPy 1.17.0**에서 실제 수행한 것이다.

## R3. 정의·컨벤션·근거 상태

### 다섯 변수는 자동으로 닫힌 5차원 상태가 아니다

| 항목 | 이번에 유지하는 의미 | 필요한 구조 |
|---|---|---|
| \(x\) | 부호와 방향을 가진 전체 carrier 또는 그 명시된 contraction | tensor/multipole packing, frame, units |
| \(Q\) | 선언된 물리적 허용체·anchor에 대한 gauge/좌표 | source-matched admissible body |
| \(\Pi\) | 지정된 사건·tail과 qualified joint law의 확률 | 같은 표본, strict/inclusive tie 규약, unknown mass |
| \(F\) | 선언된 사건·support의 measure occupancy | 정규화된 공동 measure와 영역 |
| \(G_F\) | 지정한 floor·depth·path의 transport functional | 양의 denominator·동일 시스템·경로 |

legacy의 `Pi=posterior exceedance of Q`, `F_Bayes=mean Q`, `Pi_hpd68=(Pi(0.1),Pi(0.01))` 등은 현재 같은 의미의 양이 아니다. 이런 정의를 같은 이름이라는 이유로 합치지 않았다. 특히 서로 다른 threshold에서의 tail probability 두 개는 하나의 \(\Pi\) posterior HPD interval이 아니다.

\(s\)는 독립변수의 일반 기호다. 모든 \(s\)에 DP Markov generator가 존재하는 것은 아니다. arbitrary covariance parameter나 observer boost는 우선 score/variational response로 다루고, 실제 transition law를 줄 수 있는 exposure·nested threshold에서만 counting-process DP를 사용한다. normalized selection law는 비선형이므로 선형 block MZ를 직접 쓸 때는 unnormalised weight와 정규화 질량 \(Z\)를 포함한 lift 또는 적합한 nonlinear projection을 명시해야 한다.

GR signature는 \((-+++ )\)이다. velocity 표기가 dimensionless이면 \(\boldsymbol\beta=\mathbf v/c\)임을 명시하고, \(c\)를 흡수하지 않는다. \(\eta\)가 시간 단위이면 streaming frequency는 \(\omega=kc\), \(\eta\)가 길이 단위이면 \(\omega=k\)다. DP ladder algebra의 \([a,a^\dagger]=1\)은 입자수 bookkeeping이며 양자화된 \(\hbar\)를 설정한 것이 아니다.

상태 표시는 `literature-supported`, `derived`, `numerically checked`, `implementation-verified`, `conjectural`, `unresolved`, `blocked`를 구별한다. 코드 본문을 읽어 발견한 오류는 `source-derived`로 기술하며 원 코드 실행과 구별한다.

## R4. 여덟 발산 경로와 판별 질문

| ID | 구성할 대상 | legacy의 구체적 재료 | current 연결 | 이번 판별 |
|---|---|---|---|---|
| A | 수동적 MZ tail·dimensionless phase clock | MZ recurrence, FLRW streaming, block LU | R100 finite hierarchy | Bessel oracle, Schur, 반사 horizon |
| B | score residual로 선택하는 entropy moment 확장 | Bregman identity, tangency, spectral 모드 | P1/PHY-02/06 | 국소 KL 계수와 추가 moment |
| C | collision clock·initial layer·implicit Schur | TCA/visibility, scalar tracking bound | R100 electron-owned collision | 원 식 잔차·opacity 적분 |
| D | same-parent DP 선택·disjoint bin 정보 | source competition·bulkflow/selection scaffolds | R100 19 radio cuts, CF4 | conditional Fisher=profile Fisher |
| E | 교환가능한 전역 null rank | lowell calibration·K1 noise pairing | L03/L04/SQ-CMB-NULL | 정확한 두 행 반례 |
| F | signed ratio 공동 부분식별 | EGS3 shared-null interval·five-view operators | S01–S04/current functionals | negative numerator와 denominator crossing |
| G | 실제 parameter tangent의 관측가능성 | complex shell·screen rotation·multiwindow GLS | Gaia/optical/CF4 covariance | finite Gramian, endpoint 계약 |
| H | 정확한 multipole 곱·hidden stress | theta4·induced tail·counterstream/spectral shadow | PHY-02/06/source flux | exact polynomial·tail norm |

A와 C는 memory를 실제 동역학적 feedback으로 취급한다. B와 H는 필요한 상태를 더 잘 고르는 경로다. D와 E는 확률법칙과 검정 procedure를 바로잡는다. F는 결손을 정직한 interval로 전달하고 G는 어떤 새로운 응답이 실제 식별 정보를 주는지 평가한다. 따라서 여덟 경로를 하나의 거대한 solver 선행조건으로 묶을 필요가 없다.

## R5. 구성적 유도

### A. 고정 hierarchy의 수동적 Schur self-energy

source-free signed brightness moments를

\[
\frac{d I_\ell}{d\eta}
=\omega\frac{\ell I_{\ell-1}-(\ell+1)I_{\ell+1}}{2\ell+1}
\]

로 둔다. 하나의 충분히 큰 full operator를 만든 뒤 resolved/unresolved block을 고른다. \(y_\ell=\sqrt{2\ell+1}I_\ell\)이면 이웃 coupling은

\[
J_{\ell,\ell+1}=-b_\ell,\quad J_{\ell+1,\ell}=b_\ell,
\qquad b_\ell=\frac{\omega(\ell+1)}{\sqrt{(2\ell+1)(2\ell+3)}}.
\]

따라서 \(J^\dagger=-J\). \(J=\left(\begin{smallmatrix}A&B\\C&D\end{smallmatrix}\right)\)로 나누면 \(C=-B^\dagger\), \(D^\dagger=-D\)다. \(y_u\)의 variation of constants를 첫 식에 대입하면

\[
\dot y_r=A y_r+\int_0^\eta B e^{D(\eta-u)}C y_r(u)\,du
+B e^{D\eta}y_u(0).
\]

마지막 initial-force 항을 버리지 않는다. resolvent의 self-energy는

\[
\Sigma(z)=B(zI-D)^{-1}C=-B(zI-D)^{-1}B^\dagger.
\]

임의의 \(v\)에 대해 \(w=(zI-D)^{-1}B^\dagger v\)라 두면

\[
\operatorname{Re}\{v^\dagger[-\Sigma(z)]v\}
=\operatorname{Re}z\,\|w\|^2\ge0,\quad\operatorname{Re}z>0.
\]

이것이 여기서 사용하는 정확한 수동성 조건이다. imaginary-axis에서 어떤 성분의 부호가 맞거나 fit의 pole decay가 양수라는 조건만으로 이를 대신할 수 없다. 고주파에서 \(\Sigma(z)=BC/z+O(z^{-2})\)이므로 free constant feedthrough는0이어야 한다.

큰 \(\ell\)의 constant-tail \(b=\omega/2\)에서는 continued fraction을 직접 풀어

\[
\Sigma_\infty(z)=-\frac{\sqrt{z^2+\omega^2}-z}{2},\qquad
K_\infty(\eta)=-\frac{\omega J_1(\omega\eta)}{2\eta}
\]

를 얻는다. square root는 \(\sqrt{z^2+\omega^2}\sim z\)인 right-half-plane branch다. \(K(0)=-\omega^2/4\), kernel은 진동하며 부호가 바뀐다. 따라서 같은 부호의 real exponential 몇 개만 쓰는 ansatz는 이 kernel을 전 구간에서 그대로 표현하지 못한다. 이것은 **그 ansatz의 표현 제약**이며 합리근사·complex poles·Faber·memory closure 전체의 no-go가 아니다.

clock을 \(\tau=\int^\eta\omega(v)dv\)로 바꾸면, \(\omega>0\)인 순수 streaming에서는 \(dy/d\tau=J_0y\)가 된다. 일반 \(t=t(s)\), \(g=dt/ds\)에서는

\[
\widetilde K(s,u)=g(s)K(t(s),t(u))g(u)
\]

처럼 **두 Jacobian**이 필요하다. \(K\)의 차원은 clock\(^{-2}\), \(\Sigma\)는 clock\(^{-1}\)이다. legacy의 \(\Sigma_{\infty}/\omega^2\) 표시는 잘못된 무차원화이며 \(\Sigma/\omega\), residue/\(\omega^2\), pole/\(\omega\)를 구별해야 한다.

### B. 필요한 moment를 고르는 score 잔차

유한 support에서 \(q_\theta(i)>0\), \(\sum_iq_i=1\)인 exponential family

\[
q_\theta(i)=q_0(i)\exp\{\theta^T T_i-\psi(\theta)\}
\]

와 fixed potential \(\ell_i\)를 둔다. 작은 selection step은 \(p_h\propto q_\theta e^{h\ell}\)다. centered quantities를 \(T_c=T-E T\), \(\ell_c=\ell-E\ell\)라 하면

\[
G=E[T_cT_c^T],\quad c=E[T_c\ell_c],\quad b=G^+c,
\quad R=\ell_c-b^TT_c,\quad\rho^2=E[R^2].
\]

\(E R=0\), \(E[T_cR]=0\). 이는 실제 score에 대한 weighted orthogonal projection이다. 정규화 row는 centering에 포함되어 있다. legacy Bregman three-point identity에서 Pythagorean cancellation이 성립하려면 moment 일치뿐 아니라 gradient difference의 dual span 조건도 필요하며, normalization을 빠뜨린 moment 일치로 대체할 수 없다.

\(p_h/q_\theta=1+h\ell_c+O(h^2)\), \(q_{\theta+hb}/q_\theta=1+hb^TT_c+O(h^2)\)를 KL에 대입하면 선형항은 정규화 때문에 소거되고,

\[
\min_{\delta\theta}D_{\rm KL}(p_h\|q_{\theta+\delta\theta})
=\frac{h^2}{2}\rho^2+O(h^3).
\]

finite full support·매끄러움·일정 supported rank에서 implicit-function argument로 \(\delta\theta=hb+O(h^2)\)이다. \(\rho=0\)이면 \(\ell\in\operatorname{span}\{1,T\}\). 반대로 \(R\ne0\)일 때 **그 base에서의 고정 함수 \(R(i)\) 자체를 새 statistic으로 추가**하면 \(\ell\)이 확대 span에 정확히 들어간다. fixed pure selection에 대해서는 확대 family가 전체 step을 정확히 표현한다. mutation·상태의존 potential·변하는 support에는 이 global exactness가 따라오지 않는다.

예제 \(q=(1,1,1)/3\), \(T=(-1,0,1)\), \(\ell=(-1,0,2)\)에서는

\[
b=3/2,\quad R=(1/6,-1/3,1/6),\quad\rho^2=1/18.
\]

bounded fixed event의 \(F\) 또는 \(\Pi\) 오차는 Pinsker를 이용해 \(|\Delta F|\le\sqrt{D_{KL}/2}=|h|\rho/2+O(h^2)\)로 제어할 수 있다. unbounded \(x\), singular gauge, denominator floor가 없는 \(G_F\)까지 같은 bound가 자동 확장되지는 않는다.

**수치 보정:** 초기 구현의 raw covariance pseudoinverse는 statistic scale에 따라 작은 비영 모드를 버릴 수 있었다. 독립 검토의 \(T_2=10^{-8}(1,-2,1)\) 반례를 받아, centered statistics를 분산으로 표준화한 뒤 correlation matrix의 pseudoinverse를 계산하도록 고쳤다. `rcond`와 numerical rank를 반환한다. near-collinear 비영 모드를 cutoff로 버린 경우의 residual은 수치 부분공간에 대한 것이며 정확한 전체 span 정리와 구별한다.

### C. collision clock, fast initial layer와 Schur solver

legacy PR13AF에 적힌 식이 \(0=S+\Gamma Mq\)라면 해는

\[
q_{qs}=-\Gamma^{-1}M^{-1}S.
\]

원본은 반대 부호를 반환했다. 더 일반적으로 \(q'=S-M_c q\), \(M_c=\Gamma B\), \(B>0\)일 때

\[
q(\eta)=U(\eta,0)q(0)+\int_0^\eta U(\eta,u)S(u)du.
\]

constant \(B\)에는 \(u_c=\int\Gamma d\eta\)라는 collision depth가 자연스럽다. \(dq/du_c=S/\Gamma-Bq\). 충분히 천천히 변하는 source에는

\[
q\approx M_c^{-1}S-M_c^{-1}\partial_\eta(M_c^{-1}S)
\]

가 다음 tracking correction이다. 초기조건과 fast mode가 만드는 homogeneous initial layer를 별도로 남겨야 한다. photon–baryon coupling에서는 conserved total momentum과 damped slip을 먼저 분리한다. zero eigenmode를 fast inverse에 넣어서는 안 되며 시간에 따라 baryon loading이 변하면 그 derivative 항도 포함한다.

현재 implicit step의 block solve에도 같은 원리가 적용된다. \((zI-L)y=f\)에서 unresolved block을 제거하면 resolved 행렬은 \(zI-A-B(zI-D)^{-1}C\)다. legacy `block_diag.rs`처럼 cross block을 그냥 버리는 것은 이 Schur correction을 삭제하는 근사다. 작은 coupling을 \(B,C=O(\varepsilon)\)로 둘 때 memory는 \(O(\varepsilon^2)\)지만 초기 unresolved force는 \(O(\varepsilon)\)일 수 있다.

증가하는 \(\eta\)의 opacity \(\Gamma\ge0\)는

\[
\kappa(\eta)=\int_\eta^{\eta_0}\Gamma(v)dv\ge0,
\qquad g(\eta)=\Gamma(\eta)e^{-\kappa(\eta)}
\]

다. finite optical depth에서는 \(\int g d\eta=1-e^{-\kappa(\eta_i)}\)이며 무조건1로 재정규화하면 escape mass를 조건부 법칙으로 바꾸게 된다. physical rate \(n_e\sigma_T c\)와 conformal rate \(a n_e\sigma_T c\), 길이단위 rate \(a n_e\sigma_T\)를 별도로 기록해야 한다.

### D. DP nested selection을 실제 식별 정보로 연결

fixed parent에서 flux threshold \(s\)를 증가시키고 survival \(p(s)\)가 감소한다고 하자. 독립 mark와 적절한 state에서 hazard \(h(s)=-p'(s)/p(s)\)인 pure-death law를 만들 수 있다. forward DP convention \(\partial_s|P\rangle=\widehat L_s|P\rangle\)에서

\[
\widehat L_s=h(s)(1-a^\dagger)a,
\qquad\partial_s G(z,s)=h(s)(1-z)\partial_zG.
\]

따라서 cut별 count를 서로 독립인 표본처럼 취급하지 않고, 동일 parent의 disjoint bins로 표현한다. 이 pure-death 해석은 중첩되는 threshold의 것이다. observer boost처럼 들어오고 나가는 객체가 함께 생기는 일반 parameter 변화에는 실제 marked transition law 또는 직접 reselection tangent가 필요하다.

서로 겹치지 않는 bin count가 \(n_j\sim\mathrm{Poisson}(A r_j(\theta))\)이고 \(R=\sum r_j\)라면, \(N=\sum n_j\)를 조건화했을 때

\[
(n_1,\ldots,n_m)\mid N\sim\mathrm{Multinomial}(N,\pi),
\quad\pi_j=r_j/R.
\]

Poisson 정보행렬의 amplitude block을 직접 제거하면

\[
I^{profile}_{ab}
=A\left[\sum_j\frac{\partial_a r_j\partial_b r_j}{r_j}
-\frac{\partial_aR\partial_bR}{R}\right]
=E[N]\sum_j\frac{\partial_a\pi_j\partial_b\pi_j}{\pi_j}.
\]

즉 공통 absolute amplitude를 nuisance로 보는 한, 조건부 shape 정보는 기대값에서 같은 Schur information을 가진다. 공통 Gamma intensity가 있어도 marks가 amplitude와 독립이면 조건부 bin law의 cancellation은 유지된다. angular/mark-dependent calibration이나 correlated bins를 갖는 경우에는 그 법칙을 새로 구성해야 한다.

이것은 R100 radio 19컷의 구체적인 추가 경로다. 객체 ID가 보존된 baseline에서 인접 cut의 disjoint bins를 만들고 shape response부터 분석한다. **baseline 밖의 rejected population이 없다는 이유로 모든 조건부 shape 분석을 멈출 필요는 없다.** 다만 그 결과로 absolute completeness·전체 source-count amplitude까지 추정할 수는 없다.

### E. 전역 rank 보정에서 필요한 대칭성

관측행을0, simulation 행을1..S라 하고, 높은 값이 극단인 통계 \(T_{ij}\)를 모든 행에서 같은 방법으로 계산하자. \(n=S+1\)에 대해

\[
p_{ij}=\frac{\#\{k:T_{kj}\ge T_{ij}\}}{n},\quad
m_i=\min_jp_{ij},\qquad
p_{global}=\frac{\#\{i:m_i\le m_0\}}{n}.
\]

전체 변환은 row permutation에 equivariant다. null 아래 모든 행이 joint exchangeable이면 \((m_i)\)도 exchangeable이며, inclusive rank는 ties가 있어도 super-uniform이다. 조건부로 고정된 순위 배열에서 \(\alpha n\) 이하 rank를 갖는 행의 수가 \(\lfloor\alpha n\rfloor\) 이하라는 계산으로 보수성을 확인할 수 있다. [L5,L6]

legacy는 관측 local p와 simulation local p를 비대칭적으로 계산했다. S=1, 통계2개에서 각 coordinate가 두 행에0/1을 무작위 배치하는 네 순서 패턴을 전수 열거하면 old global p는 \((1,1/2,1/2,1/2)\), corrected p는 \((1,1,1,1/2)\)다. 명목 \(\alpha=1/2\)에서 old rejection probability는3/4로 초과하고 corrected는1/4다. 단순한 전체 p-value의 `+1`만으로 내부 rank의 비대칭이 고쳐지지 않는다.

이 구현 교정은 **null 생성기의 source qualification과 별개**다. 예를 들어 999 CMB realizations에 300 noise maps를 modulo로 반복 배정하면 ID가 달라도 일부 행이 공통 noise를 공유한다. 그 dependence와 관측행을 포함한 exchangeability를 입증하지 않고 새 rank 함수만 적용하면 검정 보장은 없다. two-sided center를 자료로 추정하는 경우에도 모든 행을 대칭 처리하거나 외부 고정 center를 사용해야 한다.

### F. signed ratio의 정확한 공동 box bound

\[
N=n+c_N^Tu,\quad D=d+c_D^Tu,
\quad n\in[n_-,n_+],\ d\in[d_-,d_+],\ u\in\mathcal B,
\]

이고 전체 box에서 \(D>0\)라 하자. 다른 좌표를 고정하고 한 좌표를 바꿀 때 \(N/D\)의 derivative는 affine numerator 두 계수의 일정한 조합을 양의 \(D^2\)로 나눈 값이다. 따라서 각 좌표에서 단조 또는 상수이고 extrema는 vertex에 존재한다. shared \(u\)의 모든 vertex에서 **독립적인 n,d endpoint 네 조합**을 모두 평가해야 한다.

원본의 두 endpoint pairing은 \(N\)이 음수일 때 실패한다. \(N\in[-2,-1]\), \(D\in[1,2]\)에서 정확한 결과는 \([-2,-1/2]\)지만 원본은 \([-1,-1]\)을 반환했다. common nuisance가 없는 이 작은 예제로도 일반 signed domain의 오류가 드러난다. 수정 core는 denominator가0에 닿거나 가로지르면 유한 ratio interval로 위장하지 않고 거부한다.

실제 feasible set이 box보다 작거나 n,d가 추가로 상관되면 그 joint set을 이용해야 더 날카로운 bound를 얻는다. 본 루틴의 box는 명시된 가정이며 임의의 nonlinear feasible body에 대한 exact solver가 아니다.

### G. 순간적인 null과 parameter-response null의 구별

실제 주어진 parameter-flow \(X'=L X\), 관측 \(Y=H X\)에는

\[
Y'=HLX,\quad\mathcal O=\begin{pmatrix}H\\HL\\HL^2\\\cdots\end{pmatrix},
\qquad W(s_*)=\int_0^{s_*}e^{L^Ts}H^THe^{Ls}ds
\]

를 사용할 수 있다. \(H\)의 null에 있는 성분도 실제 \(L\)이 관측부분으로 섞으면 여러 parameter 위치의 응답으로 식별될 수 있다. \(H(s)\)가 변하면 첫 derivative부터 \(H'+HL\)이다. nonlinear physical observation에서는 실제 variational equation과 output Jacobian을 사용한다.

\(L=\left(\begin{smallmatrix}-1&1\\-1&-1\end{smallmatrix}\right)\), \(H=(1,0)\)이면 rank H=1이지만 rank(H;HL)=2다. 반대로 triangular legacy spectral shadow처럼 resolved temperature→hidden spectral mode만 있고 feedback이 없으면 resolved equation의 \(B=0\), 따라서 \(K=B U_D C=0\)이다. 그래도 새 spectral observable은 달라질 수 있다. **memory 존재, hidden state 존재, 관측 추가의 정보 증가를 구별해야 한다.**

R100 Gaia의 flat-FLRW local/global beta null은 이미 실제 operator와 nuisance projection에서 확인된 문제다. 위 toy의 회전 \(L\)을 임의로 넣어 없앴다고 말할 수 없다. current optical variational generator·독립 관측·curvature/geometry 또는 검증된 추가 calibration이 실제로 바꾸는 \(H,L\)을 가져와야 한다. covariance parameter \(\alpha\)에 대해 \(y\)가 \(\alpha\)와 무관한 고정 평균을 뺀 Gaussian residual이고 \(C(\alpha)>0\)일 때

\[
\partial_\alpha\log p(y)
=\frac12\{y^TC^{-1}C_{,\alpha}C^{-1}y-\operatorname{tr}(C^{-1}C_{,\alpha})\}
\]

를 계산할 수 있다. 평균도 변하면 \((\partial_\alpha\mu)^TC^{-1}(d-\mu)\) 항을 추가한다. singular covariance에는 고정된 supported subspace와 그 위의 determinant·inverse를 따로 정의해야 하며, 현재 core는 positive-definite covariance만 받는다. selected observational law의 정당성도 별도다.

### H. 비선형 multipole 변환과 고차 tail의 정확한 대수

\(\Theta(\mu)=1+A\mu+Q_{pol}P_2(\mu)\)라고 하자. 여기서 \(Q_{pol}\)은 다섯 변수의 gauge \(Q\)가 아니라 legacy polynomial coefficient다. \(\Theta^4=\sum a_\ell P_\ell\)의 정의로부터

\[
a_\ell=\frac{2\ell+1}{2}\int_{-1}^1\Theta(\mu)^4P_\ell(\mu)d\mu
\]

를 계산한다. \(Q_{pol}=0\)만으로도

\[
a_0=1+2A^2+A^4/5,\quad a_3=8A^3/5,\quad a_4=8A^4/35
\]

다. 원본 `teff_forward.py`는 이 항들을 각각 \(6A^4/5,36A^3/5,36A^4/5\)로 넣었다. 또 \(a_8\)에 총5차인 \(A^2Q_{pol}^3\) 항을 포함한다. 작은 관측 파라미터에서 절대 영향이 작다는 것과 다항식 대수의 정확성은 다른 주장이다.

고친 core는 먼저 표준 Legendre 다항식 곱을 완성하고 나중에 필요한 projection을 취한다. \(\Theta=1+\epsilon P_2\)의 제곱에서 \(a_4=18\epsilon^2/35\)다. 표준 Legendre coefficient의 norm은

\[
\frac12\int_{-1}^1\left|\sum_{\ell>L}a_\ell P_\ell\right|^2d\mu
=\sum_{\ell>L}\frac{|a_\ell|^2}{2\ell+1}.
\]

따라서 L=2 tail은 \(a_4^2/9\)다. streaming brightness convention \(\sum(2\ell+1)(-i)^\ell I_\ell P_\ell\)의 energy weight \(2\ell+1\)과 반대처럼 보이는 이유는 coefficient 정의가 다르기 때문이다.

이 결과는 PHY-06의 high-moment enrichment를 정확한 대수로 구현할 수 있게 한다. 다만 \(A\leftrightarrow\beta\), \(Q_{pol}\leftrightarrow\sigma/H\), spectral temperature closure의 물리적 적합성까지 입증하지 않는다. 동일 tilt scalar를 갖는 counterstream pair와 isotropic six streams가 다른 STF stress를 만든다는 legacy 예제는, scalar equality만으로 state closure를 선언하지 않는 별도의 constructive control이다.

## R6. 독립 확인과 해석 보정

| 확인축 | 수행한 확인 | 해석의 한계 |
|---|---|---|
| 부호 | TCA에 원본 출력 직접 대입; \(\kappa\ge0\) direct integral; signed ratio 반례 | 명시된 matrix/clock convention의 검증 |
| 차원 | \(K\sim s^{-2}\), \(\Sigma\sim s^{-1}\); physical/conformal opacity와 c 구별 | 실제 current adapter의 단위 연결은 후속 |
| symmetry | weighted-skew J, permutation-equivariant rank, STF/Legendre convention | release·sampling exchangeability는 데이터 의무 |
| initial/boundary | hidden initial force·finite endpoint·고정 full operator 유지 | source-free finite test가 full cosmology는 아님 |
| 독립 oracle | spherical Bessel, 직접 full inverse, symbolic integral, 전수 rank enumeration | 같은 코드를 재호출하는 self-oracle와 구별 |
| 수치 rank | 독립 검토가 작은 scale의 true moment 탈락 반례를 제시; 표준화로 교정 | near-collinear singular-value cutoff는 여전히 명시된 근사 |

다른 source reviewer가 공통 core와 runner를 별도로 읽는 단회 수학 검토를 수행했다. 수치 rank의 scale 의존이라는 구체적 반례를 반영했고, 그 입력을 회귀 판별식에 추가했다. 검토 범위·결론은 `reviews/INDEPENDENT_MATH_REVIEW.md`에 보존한다. 새 일반 strong no-go를 주장하지 않는다. 알려진 finite-dimensional representation 실패는 그 연산자·관측·가정의 범위로 한정한다.

## R7. 실제 실행 결과

`research/run_discriminators.py`, `run_information_discriminators.py`, `run_polynomial_discriminator.py`를 실행했다. 이 세 runner는 새 core를 검증하고, 정확히 지정한 네 원본 Python 모듈을 독립 namespace에서 직접 불러 반례를 비교한다. 원본 전체 test suite나 Rust crate를 빌드한 것은 아니다.

### A. streaming·memory

초기 \(I_1(0)=1\), 나머지0의 source-free perturbation에서 정확한 해는 \(I_\ell(\tau)=3j_\ell'(\tau)\)다. Lref=160, \(\tau\le100\), low multipoles0..2에 대해 reference–oracle 최대 절대오차는 약 \(1.46\times10^{-13}\). weighted skew residual은 \(1.11\times10^{-15}\), Schur/direct resolvent 차이는 \(2.30\times10^{-15}\), \(\omega(\eta)=1+0.3\sin\eta\)의 variable-clock ODE와 exact exponential 차이는 \(1.58\times10^{-11}\)였다.

| retained L=20 뒤 추가한 tail modes | low0..2 최대오차, \(\tau\le40\) | \(\tau\le80\) | \(\tau\le100\) |
|---:|---:|---:|---:|
| 0 | 0.1880 | 0.6612 | 0.6612 |
| 4 | 0.003691 | 0.6057 | 0.6057 |
| 8 | 1.016e-5 | 0.5611 | 0.5611 |
| 16 | 6.95e-13 | 0.2309 | 0.4935 |
| 32 | 1.46e-13 | 3.91e-7 | 0.04417 |

이는 **같은 hierarchy를 유한하게 연장한 구조 보존 baseline**이다. 새 압축 알고리즘이 장시간 수렴했다고 부르지 않는다. 반사를 늦추는 정도가 horizon에 의존함을 실제로 확인했으므로 closure 비교 시 horizon을 고정해야 한다. A의 다음 경쟁 후보는 passivity-constrained rational approximation, complex-pole/state-space realization, Faber memory다.

### B–H. 판별표

| 대상 | 원본 또는 독립 기준 | 새 계산 |
|---|---|---|
| entropy moment | \(\rho^2=1/18\) | h=0.001에서 최적 KL=2.77747e-8, \(KL/(h^2\rho^2/2)=0.999888\) |
| entropy enrichment | 새 R statistic | 잔차 variance 약1.36e-31, roundoff 수준 |
| scale counterexample | raw covariance pinv가 true moment를 탈락시킬 수 있음 | 분산 표준화 후 numerical rank2·잔차 roundoff; exact 값은 JSON |
| TCA | 원 함수의 \(\|S+\Gamma Mq\|/\|S\|=2\) | 교정 함수 약1.16e-16 |
| optical depth | constant rate·eta=(0,1,2)에서 원본(-2,-1,0) | 교정(2,1,0), direct integral와 일치 |
| signed GF interval | 원 함수[-1,-1] | 교정[-2,-0.5], 직접 grid extrema와 일치 |
| implicit block | cross block 삭제 x=0.5 | full/Schur x=0.46875; 삭제 상대오차6.67% |
| count shape 정보 | full Poisson 정보행렬의 amplitude Schur | conditional multinomial 정보와 모두12.2 |
| response observability | 순간 rank1 | stacked rank2, W eigenvalues0.0281706·0.404162 |
| 전역 rank | \(\alpha=.5\)에서 원본 기각확률.75 | 모든 행 대칭 rank의 기각확률.25 |
| theta4 | A=.1,Qpol=0에서 원본 coefficient 최대오차.0056 | symbolic quadrature 대조6.94e-18 |
| theta4 mixed | A=.1,Qpol=.03에서 원본 최대오차.00552866 | 교정2.22e-16 |
| induced tail | epsilon=.2에서 exact \(a_4=18\epsilon^2/35\) | a4=.0205714, tail norm4.70204e-5 |

숫자의 full precision, 정확한 executed source SHA, 환경 버전과 assertion은 세 `*_RESULTS.json` 및 runner에 남겼다. 위 결과는 finite law·toy matrix·명시된 legacy 함수 수준이다. observed cosmological posterior, native all-family transfer, 실제 PR4 null의 유의도 결과를 새로 생산한 것은 아니다.

## R8. 후보별 판정과 남은 blocker

| 경로 | 이번 판정 | 다음 연구의 열린 의무 |
|---|---|---|
| A | `derived` + `numerically checked` | 실제 source/collision/time dependence를 포함한 고정 generator에서 closure gain·cost 비교 |
| B | finite-law local theorem `derived`; core `implementation-verified` | 물리적 moment domain·actual source score, near-boundary/rank-change 처리 |
| C | 명시된 legacy sign·clock 오류 `implementation-verified` | conserved modes·variable loading·nonlinear radiation backreaction의 실제 current 연결 |
| D | conditional information identity `derived` + checked | same-parent object IDs·marks와 R100 selected catalogue의 실제 bin 실행 |
| E | 구 구현 반례·수정 rank `derived` + verified | PR4/NPIPE split·foreground·noise joint law와 exchangeability |
| F | positive-box exact bound `derived` + verified | current physical feasible body·anchor·unknown mass·floor 명시 |
| G | finite toy의 정보 증가 checked | 실제 optical generator가 null을 깨는지, 독립 관측/외부 calibration |
| H | polynomial identity `derived` + symbolic/numeric checked | physical spectral closure와 source→observer mapping |

### 서로 다른 blocker를 분리한 결과

**코드·수학 연산의 부족:** 이번 core로 signed ratio, TCA 부호, opacity orientation, all-row rank, 정확한 polynomial product를 제공했다. 이는 local agent가 source-bound patch로 옮길 수 있는 구체적인 교정이다. 원본 archive는 변경하지 않았다.

**이론적 토대의 부족:** entropy residual, 수동적 Schur, conditional information, 실제 response observability는 명확한 가정 아래 직접 구성했다. 각 formalism이 임의의 parameter를 automatically physical dynamics로 바꾸어 주지는 않는다는 경계를 수학식에 반영했다.

**데이터·외부 입력의 부족:** CF4 rejected/precalibration denominator, source-qualified PR4/NPIPE split null, Gaia AGIS/AGN·scan calibration, LoTSS RMS/selection map, independent normal flux, external native polarized atlas·anisotropic recombination qualification은 남는다. 이번 toy 또는 legacy 파일 수가 늘었다는 이유로 이 의무를 없애지 않는다. 동시에 conditional radio shape·현존 apparent covariance sensitivity처럼 지금 가능한 좁은 계산을 별도로 진행할 수 있다.

### 추가로 발견했으나 이번에 전체 실행하지 않은 교정 후보

- `three_way_comparison.py`: AniCLASS 비교값에 PSTF 출력을 대입하므로 independent oracle claim이 성립하지 않는다.
- `spectral.rs`: \(I_n=\Gamma(n+1)\operatorname{Li}_{n+1}\) convention이면 \(\partial_\eta I_n=nI_{n-1}\)인데 계수 n이 누락된다. 양의 FD eta에서 발산 급수를 쓰는 분기도 있다.
- `tetrad.rs`: \(a_h=aH/c\)일 때 conformal length는 \(d\eta/da=1/(a a_h)\)인데 코드의 누적식에1/a가 빠진다.
- `rhs.py`: \(\Omega_k\propto a^{-2}H^{-2}\)의 \(d\Omega_k/d\ln a=2q\Omega_k\)와 다른 곡률식을 사용한다.
- `run_integrated.py`: 채널을 제거한 likelihood와 전체채널 FLRW 기준 evidence를 비교하는 경로가 있다. 같은 data space의 Bayes factor가 아니다.
- `theta4_bridge.rs`와 `teff_cl.rs`: m=0 packing 위치가 맞지 않는 경로가 있다. signed full carrier의 명시적 packing contract가 필요하다.
- `tilt/mod.rs`: 서로 다른 tier의 beta ODE에 같은 invariant를 사용한다. constant-w Tier B에는 \(a^{1-3w}\sinh\beta/\cosh^w\beta\), 해당 Tier C에는 \(a^{1-3w}\tanh\beta\)가 대응한다.

이 항목은 파일 정독과 직접 식 대조에서 얻은 `source-derived` 판단이다. 해당 Rust crate 전체를 빌드·실행했다거나 current R100이 동일 오류를 가진다고 보고하지 않는다. exact SHA·함수·variant는 개별 catalogue record에 있다.

## R9. 현재 여섯 대주제·일곱 교차축·60개 노드에 적용

`NODE_APPLICATIONS_60.json/.md`는 실제 canonical ID **60개를 빠짐없이 매핑**한다. 각 항목에 원 상태·목표·acceptance·external_missing, legacy SHA, 후보 경로, current hook, 추가 조건을 기록했다. graph의 7개 R67 연구축과 7개 PHY 조합도 서로 구별한다.

| 대주제 | 지금 적용 가능한 연구 재료 | 완료에 직접 기여하는 다음 계산 |
|---|---|---|
| P1 다섯 변수 | B·F·H | signed common carrier→score response→joint interval; 기존 표본 ID/unknown mass 유지 |
| P2 low-ell | A·E·H | 고정 harmonic/mask operator의 truncation 비교와 source-qualified all-row global calibration |
| P3 directional Hubble | D·F·G | R100 method/sign genealogy를 유지한 selected covariance score·finite-z physical interval |
| P4 local/global tilt·radio | D·E·G | 19 nested cuts의 same-parent bin shape 정보, 실제 optical/boost response의 projected rank |
| P5 Bianchi 분류 | A·C·G·H | Lie/flux/constraint를 보존하는 reduced operator 준비; native atlas 의무는 별도 |
| P6 kinematics | C·F·G·H | 한 congruence의 signed STF·curl·acceleration 및 실제 비방사 관측 응답 |

일곱 교차 PHY의 직접 연결은 다음과 같다.

| 교차 노드 | 이번 연결 |
|---|---|
| PHY-01 | masked hemisphere leakage의 실제 응답을 F·G의 floor/selection/optical 변화에 전달 |
| PHY-02 | photon PSD·normal flux ellipsoid에 B·H의 source-specific moment enrichment |
| PHY-03 | 같은 beta의 photon/count 관계에 D의 mark·selection derivative 결합 |
| PHY-04 | E2/B2 분리와 실제 mask mixing에 G의 optical response 적용 |
| PHY-05 | exceptional rank2와 noisy residual rank3를 구별해 실제 G-operator 관측가능성 평가 |
| PHY-06 | 같은 scalar에서 다른 eigenframe·ell4·stress를 A·B·H로 구별 |
| PHY-07 | 실제 radius variation의 rank12 vs fixed-r rank9에 D·G의 source/covariance 법칙 적용 |

### 공통 core의 코드 계약

`research_primitives.py`는 fixed finite matrices, finite normalized laws, standard Legendre coefficients를 받는다. 정확히 겹친 `P2`, `source_zeta`, `_unit_vec`, `_angular_sep` 네 함수도 별도 공통 helper로 모았고 함수 source hash를 대조했다. directed angle과 antipodal axis angle은 합치지 않았다. source-level 공통화는 함수와 결과로 이루어지며 임의의 legacy production importer를 한꺼번에 바꾸지 않는다. `research/CORE_PROVENANCE.json`이 각 함수의 source anchor, 식, 검증, 미구현 범위를 연결한다.

후속 local patch의 첫 후보는 원본 함수와 같은 입력으로 반례를 재현할 수 있는 E/F/C/H다. A/B/G는 current full operator·실제 law adapter가 준비된 뒤 projection을 선택한다. D는 R100 catalogue IDs가 보존되어 있다면 absolute-selection blocker와 독립적으로 conditional baseline-bin 분석을 먼저 실행할 수 있다.

## R10. 종료점·재현·로컬 인계

이번 종료점은 코드 전수 정독 장부, 원본 복원 가능한 통합본, 여덟 구성적 연구 경로, finite 실험과 exact 반례, canonical 60-node 적용 지도다. **60개 노드를 모두 물리적으로 완료했다는 결과가 아니다.** 현재 scope를 넘는 native all-family 구현이나 새 관측 검출을 산출물에 포함하지 않았다.

통합본을 푼 뒤 새 계산을 재현하는 명령은 다음과 같다.

```bash
python tools/verify_bundle.py
OPENBLAS_NUM_THREADS=1 python research/run_discriminators.py
OPENBLAS_NUM_THREADS=1 python research/run_information_discriminators.py
OPENBLAS_NUM_THREADS=1 python research/run_polynomial_discriminator.py
python tools/materialize_archive.py --list
python tools/materialize_archive.py --archive A17 --output ./restored_A17
```

`--list`의 archive 이름과 ID를 확인하고 선택한다. 복원기는 파일을 복사할 뿐 legacy 코드를 실행하지 않는다. `verify_bundle.py`는 원본 content SHA와 catalogue coverage를 확인하며 과학적 검증 PASS를 대신하지 않는다. 자세한 local agent 실행 순서는 `HANDOFF_LOCAL_AGENT_KO.md`에 있다. 새 변경 전 current branch·HEAD·dirty state를 다시 확인하고, 이 보고서의 archive-relative 문제를 current 코드 오류로 자동 간주하지 않도록 명시했다.

전달본을 별도 경로에서 확인했다. 원 ZIP 18개와 고유 파일 2,430개의 hash가 최초 장부와 일치했다. portable 경로로 고친 세 runner는 정상 종료했고 기존 결과 JSON과 값이 같았다. A17의 29개 파일과 A04의 751개 파일을 새 폴더에 복원해 전체 content SHA를 대조했다. HTML에는 2,430개 record가 들어 있고 source 링크가 모두 존재하며 JavaScript syntax check가 통과했다. 이 범위와 실행 결과는 `DELIVERY_VERIFICATION.json`에 보존했다.

### 자료와 인용

- **[L1]** C.-P. Ma, E. Bertschinger (1995), *Cosmological Perturbation Theory in the Synchronous and Conformal Newtonian Gauges*, ApJ 455, 7. Eqs.49–51 및 hierarchy truncation 논의. https://arxiv.org/abs/astro-ph/9506072
- **[L2]** D. Blas, J. Lesgourgues, T. Tram (2011), *The Cosmic Linear Anisotropy Solving System (CLASS). Part II: Approximation schemes*, JCAP 07,034. §§2–4, Appendix B. https://arxiv.org/abs/1104.2933
- **[L3]** Y. Zhu, D. Venturi (2018), *Faber approximation of the Mori–Zwanzig equation*, Journal of Computational Physics. https://arxiv.org/abs/1708.03806 ; https://doi.org/10.1016/j.jcp.2018.06.047
- **[L4]** C. D. Levermore (1996), *Moment closure hierarchies for kinetic theories*, Journal of Statistical Physics83,1021–1065. https://doi.org/10.1007/BF02179552
- **[L5]** J.-M. Dufour (2006), *Monte Carlo tests with nuisance parameters: A general approach to finite-sample inference and nonstandard asymptotics*, Journal of Econometrics133,443–477. https://doi.org/10.1016/j.jeconom.2005.06.007 ; https://jeanmariedufour.research.mcgill.ca/Dufour_2006_JE_MCT.pdf
- **[L6]** B. Phipson, G. K. Smyth (2010), *Permutation P-values Should Never Be Zero: Calculating Exact P-values When Permutations Are Randomly Drawn*. https://doi.org/10.2202/1544-6115.1585 ; https://gksmyth.github.io/pubs/PermPValuesPreprint.pdf
- **[P1]** `DP_MZ_Auxiliary_Research_20261123.md` — 같은 대화의 앞선 보조 연구. 정의·source law·실행결과의 prior evidence로 재사용.
- **[P2]** `DP_MZ_Parameter_Response_Research_20261123.md` — 같은 대화의 parameter-response 연구. normalized score, clock·basis·endpoint 결과 재사용.
- **[G1]** R100 `REPORT_KO.md` 및 `CURRENT_REFERENCE_PROVENANCE.json`의 current SHA/API 목록. 실제 source/optical 상태의 근거.
- **[C1]** `FILE_CATALOGUE.json`과 `reviews/*.jsonl`. 첨부 원 코드의 full SHA·원 경로·정독 판단.
- **[N1]** `research/DISCRIMINATOR_RESULTS.json`, `INFORMATION_RESULTS.json`, `POLYNOMIAL_RESULTS.json`. 이번 직접 실행의 수치 근거.
