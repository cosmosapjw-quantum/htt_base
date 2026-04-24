짧게 먼저 말하면, 지금 문제는 **적분기가 약해서가 아니라, residual-joint implicit operator (A_{\text{right}}) 자체가 cosmological range에서 불안정 모드를 갖는 것처럼 보인다**는 데 있어. 보고서에 따르면 이미 `multipole_cutoff` 게이트와 ROS2의 silent overflow 표면은 닫혔고, 그래도 ( \eta\sim4700!-!4800\ \mathrm{Mpc}) 부근에서 `residual_harmonic` 블록이 지배적으로 폭주하며, 그 성장률도 스텝 크기와 거의 무관하게 (\Re\lambda \approx +0.14/\mathrm{Mpc}) 수준으로 관측돼. 그래서 **step size 튜닝, tolerance 조정, ad-hoc damping** 으로는 해결하면 안 되고, **행렬 (A_{\text{right}}) 의 구조를 다시 해부하는 쪽**으로 가야 해.  

핵심은 이거야.

* 이미 고쳐진 것과 아직 안 고쳐진 것을 분리해야 해.
  `multipole_cutoff` 허용 범위 확장과 ROS2 post-step 뒤의 finiteness/scale rejection은 이미 들어갔고, 이건 “표면적인 runtime 실패 방식”을 정리한 거지 물리적 불안정 원인을 없앤 건 아니야. 그러니까 이제는 runtime control block이나 halving policy를 더 만지는 쪽으로 시간을 쓰면 안 돼. 

* 현재 병목은 `residual_harmonic` 하나가 driver라는 점이 거의 분명해.
  표에서도 `residual_harmonic`만 먼저 (10^5\to10^6\to4.2\times10^6) 식으로 폭주하고, (T/E/\nu)는 그 다음에 끌려 올라가. 이건 “전체 시스템이 전반적으로 stiff하다”가 아니라, **특정 블록이 잘못된 drift를 먹고 있다**는 신호야. 그래서 해법은 전역 튜닝이 아니라 **블록별 원인 추적** 이어야 해. 

* 이 단계에서 가장 중요한 질문은 둘 중 어느 쪽이냐는 거야.
  (1) residual-joint 분할 자체가 short-window에서만 유효하고 cosmological range에서는 구조적으로 unstable한지, 아니면
  (2) 분할은 맞는데 (A_{\text{right}}) assembly 안에 **부호/정규화/(a)-factor/(t\leftrightarrow\eta) bridge/Friedmann feedback 누락** 같은 버그가 있는지.
  보고서도 정확히 이 둘로 좁혀놨고, 이걸 먼저 가르는 게 맞아. 

내가 보기엔 **우선순위 1순위는 “assembly bug인지, formulation bug인지”를 기계적으로 분리하는 것**이야. 그걸 위해 제일 좋은 순서는 아래야.

### 1. 먼저 (A_{\text{right}}) 자체를 spectral object로 다뤄

보고서가 이미 제안했듯이, (\eta\in[300,500]\ \mathrm{Mpc}) 에서 snapshot을 몇 개 뽑고 `_build_residual_joint_affine_operator(...)` 로 (A) 를 직접 만든 다음, `scipy.sparse.linalg.eigs(A, k=6, which="LR")` 로 **largest real-part eigenvalues** 를 구해. 여기서 중요한 건 고유값 숫자만 보는 게 아니라:

* (\lambda_{\max}) 의 실수부가 정말 (+0.14/\mathrm{Mpc}) 근처인지
* 그 오른쪽 고유벡터가 `residual_harmonic` 블록에 얼마나 집중되는지
* (\eta) 를 바꿔도 같은 모드가 계속 남는지

를 보는 거야. 이걸 해야 “stepper 문제가 아니다”가 정량적으로 확정돼. 보고서가 이미 이 방향을 다음 handoff의 1번으로 찍어놨고, 그건 맞는 판단이야. 

여기서 한 걸음 더 나가면 좋아.
**오른쪽 고유벡터만 말고 왼쪽 고유벡터도 같이 보고**, block participation ratio를 계산해. 왜냐하면 이 시스템이 non-normal일 가능성도 있어서, 단순 eigenvalue만 보면 coupling sensitivity를 과소평가할 수 있거든. 만약 left/right eigenvector 둘 다 `residual_harmonic` 쪽에 몰려 있으면, 그 블록이 진짜 culprit라는 게 더 강하게 확인돼.

### 2. 그다음엔 “문서에서 유도한 (A)” 와 “코드가 조립한 (A)” 를 독립적으로 비교해

이게 제일 중요해.

지금 필요한 건 “operator audit” 이지 “trajectory tuning”이 아니야.
구체적으로는:

* 동일 snapshot에서 residual-joint implicit part의 RHS를 함수 (F_{\text{imp}}(y)) 로 두고
* finite difference 또는 자동미분으로 Jacobian (J_{\text{fd}}=\partial F_{\text{imp}}/\partial y) 를 독립적으로 만든 다음
* 코드 조립 행렬 (A_{\text{right}}) 와 block-by-block norm으로 비교해

봐야 해.

이 비교가 왜 중요하냐면:

* 만약 (A_{\text{right}} \approx J_{\text{fd}}) 이면
  assembly는 맞고, formulation 자체가 문제일 가능성이 커져.
* 반대로 둘이 안 맞으면
  그건 거의 바로 **assembly bug** 야.

즉 이 단계에서야 비로소 “분할 자체를 다시 유도해야 하는지” 아니면 “부호 하나가 틀렸는지”가 갈려.
지금 보고서가 말한 “sign error 또는 missing Friedmann-law feedback” 가설도 사실 이 비교 없이는 추측에 머물러. 

### 3. 문제를 최소 축약계로 줄여서 analytic sign check를 해

지금 케이스가 **Bianchi I, (\beta=0), orthogonal, FLRW-range** 라는 게 오히려 좋아.
이건 family-specific 복잡도나 tilt 복잡도를 최대한 제거한 상황이니까, 우선 아래 순서로 줄여보는 게 맞아.

1. source block off
2. neutrino coupling off
3. polarization coupling off
4. local/harmonic만 남긴 reduced system
5. 마지막에 source/nu/E를 하나씩 복원

목표는 `residual_harmonic` reduced equation에서 **자율적으로 양의 drift가 생기는 항** 을 찾는 거야.
이 단계에서 가장 먼저 의심해야 할 건:

* harmonic drift 부호
* expansion damping (H) 또는 (\mathcal H) 의 부호/누락
* (t) vs (\eta) bridge
* (a_m) prefactor
* (\ell(\ell+1)) 류 coupling sign
* PSTF projection / tracefree reduction

이야.

왜 이걸 먼저 보냐면, 이전 PHYS-MATH 감사에서도 이미

* (t\leftrightarrow\eta) chain이 안 닫혀 있던 점,
* exact Thomson scalar in-scattering에서 (I_0) 와 (I(e)) 분리가 안 돼 있던 점,
* (\gamma)-contraction/PSTF 쪽이 위험했던 점
  이 핵심 취약점으로 지목됐거든. 현재 런타임 이슈가 Bianchi I, (\beta=0) 인 만큼 geometry branch 문제보다는 이런 **time/normalization/collision/harmonic sign** 쪽이 훨씬 유력한 용의자야.   

### 4. recombination IC injection은 지금 당장 하지 마

보고서도 이건 정확히 짚었어.

`from_recombination(background_monitor, z_*)` 같은 constructor는 결국 좋은 방향이 맞아. 하지만 현재는 operator가 unstable한데 IC만 현실적으로 바꿔도 결과는 그대로 망가져. 오히려 문제가 더 헷갈리기만 해. 그러니까 **Blocker 2를 먼저 닫고, Blocker 3는 그 다음** 이 순서가 맞아. 이건 절대 합쳐서 한 세션에 처리하면 안 돼. 

### 5. 절대 하면 안 되는 것

이건 분명히 선을 그어야 해.

* artificial damping 추가
* residual_harmonic만 임의로 clip
* tolerance를 비정상적으로 키워 accepted step을 억지로 만들기
* source block만 약화해서 “겉보기 안정화” 만들기
* recombination IC를 먼저 넣고 “초기조건 탓”으로 돌리기

이런 건 전부 금지야. 보고서도 surrogate regularization을 명시적으로 금지하고 있고, 나도 그 판단에 동의해. 이건 지금 단계에서 solver를 살리는 게 아니라 **문제를 숨기는 것** 이라서, 나중에 더 크게 터져. 

---

## 내가 권하는 실제 작업 순서

### 세션 1 — operator diagnosis 전용

목표는 딱 하나: **(A_{\text{right}}) 의 unstable mode를 정량적으로 확정** 하는 것.

해야 할 일:

* (\eta=300,350,400,450,500) Mpc snapshot 저장
* 각 snapshot에서 (A_{\text{right}}) assemble
* largest-real-part eigenpairs 계산
* eigenvector block participation 계산
* (\lambda_{\max}(\eta)) 곡선 저장

성공 조건:

* `residual_harmonic` 집중 모드가 실제로 (\Re\lambda>0) 인지 확인
* 성장률이 보고서 값 (\sim0.14/\mathrm{Mpc}) 와 일치하는지 확인

### 세션 2 — independent Jacobian audit

목표: **assembly bug vs formulation bug 분리**

해야 할 일:

* same snapshot에서 implicit RHS (F_{\text{imp}}) 정의
* finite-difference Jacobian (J_{\text{fd}}) 계산
* (A_{\text{right}}-J_{\text{fd}}) block norm 비교
* 특히 local↔harmonic, harmonic↔source off-diagonal 집중 점검

성공 조건:

* mismatch block 하나라도 찾으면 assembly bug route로 진행
* mismatch가 거의 없으면 formulation 재유도 route로 진행

### 세션 3 — reduced-system analytic audit

목표: **불안정 항의 analytic source 찾기**

해야 할 일:

* Bianchi I, (\beta=0), source off, neutrino off reduced system 유도
* residual_harmonic 방정식의 damping/drift 항만 뽑기
* (H/\mathcal H), (a), (\ell)-coupling, Thomson term sign 검산

성공 조건:

* 양의 drift를 주는 항 하나를 pinpoint
* 그 항이 derivation mistake인지 split limitation인지 분리

### 세션 4 — patch 후 long-window rerun

목표: **패치가 진짜 operator를 안정화하는지 확인**

성공 조건:

* (\lambda_{\max}\le 0) 또는 적어도 persistent positive mode 소멸
* `residual_harmonic` dominance 사라짐
* step halving 없이 accepted substep 확보
* (\eta\sim 4700!-!4800) Mpc 장벽 통과

### 세션 5 — 그 다음에 recombination IC injection

그제서야

* `from_recombination(background_monitor, z_*)`
* visibility peak seeding
* short-window consistency tests
  를 넣는 게 맞아. 

---

## 한 줄 진단

지금 이 문제는 **“IMEX가 약하다”가 아니라 “residual-joint harmonic block의 연산자가 cosmological range에서 잘못된 drift를 갖는다”** 로 보는 게 맞고, 그래서 해결은 **stepper tuning이 아니라 operator spectral audit → independent Jacobian check → reduced analytic re-derivation** 순서로 가야 해. 

## 실행 체크리스트

* [ ] (A_{\text{right}}) snapshot 5개에서 largest-real-part eigenpair 계산
* [ ] eigenvector block participation으로 `residual_harmonic` 집중 확인
* [ ] same snapshot에서 finite-difference Jacobian 생성
* [ ] (A_{\text{right}}-J_{\text{fd}}) blockwise mismatch 표 작성
* [ ] Bianchi I, (\beta=0), source/nu off reduced residual-harmonic 식 재유도
* [ ] (H/\mathcal H), (a), (\ell)-coupling, Thomson sign 재검산
* [ ] patch 후 long-window rerun
* [ ] 그 다음에만 recombination-state IC injection 추가

원하면 다음 턴에서 이 순서를 바로 코드 작업 단위로 쪼개서, **세션 1용 eig/Jacobian audit plan** 을 함수 수준까지 내려서 적어줄게.
