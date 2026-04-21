# Low-ℓ Tetrad-Based Bianchi CMB Solver — PR/WBS Reference Plan

## 0. 문서 목적

이 문서는 `lowell_bianchi_solver_reference.md`를 **실행 가능한 PR/WBS 문서**로 재구성한 것이다. 목표는 다음 네 가지다.

1. low-ℓ 전용 tetrad-based orthogonal/tilted Bianchi CMB solver의 **권위 경로(authority path)** 를 고정한다.
2. background / perturbation / IC / TCA / recombination / reionization / LoS / likelihood를 **구현 단위(PR)** 로 분해한다.
3. 각 PR마다 **산출물, smoke test, kill criterion, done definition** 을 명시한다.
4. 세션별 진척도를 기록할 수 있도록 **scoreboard** 를 제공한다.

이 문서는 연구 노트가 아니라 **실행 문서**다. 따라서 수식은 “무엇을 구현해야 하는가”의 기준으로 포함하고, 이론 전개 전체를 다시 장문으로 반복하지 않는다.

---

## 1. Core authority freeze

### 1.1 절대 유지할 권위 경로

이 문서 전체에서 절대로 바꾸지 않는 핵심은 다음과 같다.

- **exact Bianchi background transport**
- **exact electron-frame Thomson tensor**
- **transport는 \(n^a\)-frame, source/collision/visibility는 \(u_e^a\)-frame**
- **first-pass isotropic scalar recombination history + anisotropic source evaluation**
- **homogeneous reionization + anisotropic rescattering source**
- **FLRW limit에서 CAMB regular adiabatic IC recovery**

즉 low-ℓ solver의 핵심은

\[
\boxed{
\text{exact Bianchi transport + exact electron-frame Thomson tensor + explicit }(\Theta_2,E_2)
\text{ + scalar }x_e(\eta)\text{ + anisotropic LoS/likelihood}
}
\]

이다.

### 1.2 production first-pass 범위 밖

아래는 **deferred** 로 둔다.

1. anisotropic HyRec / RECFAST / Peebles \(C\)-factor
2. direction-dependent escape probability
3. patchy reionization
4. full high-ℓ Einstein–Boltzmann hierarchy
5. full vector/tensor primordial regular series의 상세 계수
6. non-classical Thomson / Compton kernel

즉 이 문서는 어디까지나 **low-ℓ production first-pass** 기준이다.

---

## 2. 기본 컨벤션과 최소 상태벡터

### 2.1 기하와 부호

metric signature는

\[
(-,+,+,+)
\]

로 둔다. 기본 관측자 congruence를 \(n^a\)라 하여

\[
g_{ab}=-n_an_b+h_{ab},\qquad h_{ab}n^b=0
\]

로 \(1+3\) 분해한다.

운동학 분해는

\[
\nabla_a n_b=-n_aA_b+\frac13\Theta h_{ab}+\sigma_{ab}+\omega_{ab}
\]

이다.

### 2.2 기본 프레임 선택

문서 전체의 기본 선택은

\[
\boxed{\text{transport는 }n^a\text{-frame},\qquad \text{collision/source/visibility는 }u_e^a\text{-frame}}
\]

이다.

### 2.3 low-ℓ baseline 상태벡터

#### background state
\[
\{\alpha,\beta_{ab},\Sigma_{ab},{}^{(3)}R_{ab},C^i{}_{jk}\}
\]

#### matter state
\[
\{\rho_c,\rho_b,v_c,v_b,v_e\}
\]

orthogonal이면 \(v_s=0\), tilted면 species별 \(v_s\neq0\).

#### radiation state
\[
\{\Theta_0,\Theta_1,\Theta_2,E_2\}
\]
필요하면
\[
\{\Theta_3,E_3\}
\]
추가.

#### neutrino state
\[
\{\Delta_\nu,q_\nu,\pi_\nu,G_3\}
\]

#### ionization / visibility state
\[
\{x_e(\eta),\Gamma_T,\kappa,g\}
\]

tilted면
\[
\{\tilde\Gamma_T(e),\tilde g(e)\}
\]

#### evolution equation skeleton
\[
\mathbf X' = \mathsf L_B[n]\mathbf X + \mathsf C_T[v_e]\mathbf X + \mathbf S_{\rm pert}[v_e]
\]

---

## 3. 점수 규칙

각 PR은 10점 만점으로 평가한다.

- **0–2**: 아이디어/메모 수준
- **3–4**: notation / 가정 / 수식 freeze
- **5–6**: 코드 골격 + 부분 구현
- **7–8**: smoke test + 일부 limit check 통과
- **9–10**: 수렴/정합성/진단까지 완료

전체 진행률은

\[
\mathrm{Progress}(\%)=\sum_i w_i\frac{s_i}{10}
\]

로 계산한다.

---

# Release

**Bianchi Exact-Transport / Exact-Thomson Solver — Low-ℓ Backbone**

---

## PR-00 — Core freeze / authority fence
**가중치:** 6  
**현재 점수:** __ / 10

### 목적
프로젝트의 최상위 철학을 고정한다.

핵심 선언:
- “nonlinear Thomson kernel”이 아니라 **exact Bianchi transport + exact electron-frame Thomson tensor**가 authority path다.
- Tier A / Tier B 역할을 분리한다.
- low-ℓ cutoff 정책 \(L=4/6/8\)를 freeze한다.

### 최소 수식/개념
- background exact transport:
  \[
  \mathcal L_B[I,Q,U]=\mathcal C_{\rm Th}[I,Q,U;\tilde u_e]
  \]
- frame split:
  \[
  \text{transport: }n^a,\qquad \text{collision: }u_e^a
  \]

### WBS
1. core assumptions 문서 작성
2. frame split 규약 작성
3. Tier A / Tier B 역할 정의
4. cutoff policy \(L=4/6/8\) 고정

### 산출물
- `CORE_FREEZE.md`
- `CONVENTIONS_AND_FRAMES.md`
- `TIERS_AND_AUTHORITY.md`

### smoke test
- [ ] “exact transport”, “exact Thomson tensor”, “Tier A/B”, “L=4/6/8”가 모순 없이 정의됨

### kill criterion
- transport / collision frame 정의가 문서마다 다르면 실패
- recombination anisotropy를 first-pass 필수처럼 써두면 실패

### done definition
- 관련 문서 3개 freeze
- 이후 PR 문서들이 이 규약을 참조

---

## PR-01 — Exact Bianchi background geometry solver
**가중치:** 10  
**현재 점수:** __ / 10

### 목적
exact Bianchi background ODE를 먼저 세운다.

### 핵심 변수
\[
\alpha(\eta),\qquad \beta_{ab}(\eta),\qquad \Sigma_{ab}(\eta)=e^\alpha\sigma_{ab},\qquad {}^{(3)}R_{ab}(\eta)
\]

### 구조
\[
\{\alpha,\beta_{ab},\Sigma_{ab},{}^{(3)}R_{ab}\}'=\mathcal F_{\rm Bianchi}[\alpha,\beta,\Sigma,{}^{(3)}R;C^i{}_{jk},T^{\rm tot}_{ab}]
\]

### WBS
1. Bianchi type별 structure constants 정의
2. tetrad / connection coefficient 구현
3. background Einstein–Bianchi ODE 구현
4. isotropic FLRW recovery test
5. Type I / VII_h 최소 2형 테스트

### 산출물
- `background/bianchi_types.py`
- `background/tetrad_geometry.py`
- `background/einstein_bianchi.py`
- `tests/test_background_flrw_limit.py`
- `tests/test_background_typeI_viih.py`

### smoke test
- [ ] Type I background 적분 성공
- [ ] small-anisotropy limit에서 FLRW 복귀
- [ ] \(\sigma_{ab}\to0\)에서 isotropic expansion recovery

### kill criterion
- 부호/차원/시간변수 정의가 문서와 코드에서 다르면 실패
- FLRW limit recovery 실패

### done definition
- Type I / VII_h 모두 안정 동작
- FLRW limit relative error 기준 통과

---

## PR-02 — Exact ray transport and polarization-basis transport
**가중치:** 12  
**현재 점수:** __ / 10

### 목적
exact Bianchi background 위에서 광자 ray와 편광기저를 운반한다.

### 핵심 수식
광자 4-운동량:
\[
K^a=E(n^a+p^a),\qquad p^ap_a=1,\qquad p^an_a=0
\]

comoving energy:
\[
\epsilon\equiv Ee^\alpha
\]

exact redshift:
\[
\epsilon'=-\epsilon\,e^\alpha p^ip^j\sigma_{ij}=-\epsilon\,\Sigma_{ij}p^ip^j
\]

Stokes PDE:
\[
\left[\partial_\eta+\theta'\partial_\theta+\phi'\partial_\phi-\Sigma_{ij}p^ip^j\partial_{\ln E}\right]I=\mathcal C_I,
\]
\[
\left[\partial_\eta+\theta'\partial_\theta+\phi'\partial_\phi-\Sigma_{ij}p^ip^j\partial_{\ln E}\right](Q\pm iU)\pm 2i\psi'(Q\pm iU)=\mathcal C_\pm.
\]

### WBS
1. comoving energy equation 구현
2. ray direction \((\theta,\phi)\) transport 구현
3. polarization basis / \(\psi\) rotation 구현
4. screen projector 기반 transport 구현
5. isotropic limit test

### 산출물
- `transport/ray_evolution.py`
- `transport/polarization_basis.py`
- `tests/test_ray_isotropic_limit.py`
- `tests/test_polarization_basis_transport.py`

### smoke test
- [ ] \(\epsilon,\theta,\phi,\psi\) evolution stable
- [ ] isotropic limit에서 FLRW free-streaming recovery
- [ ] polarization rotation on/off 비교 가능

### kill criterion
- basis rotation 부호 불안정으로 \(Q/U\) norm 폭주
- ray transport와 background time convention 충돌

### done definition
- ray + basis transport 독립 모듈 분리 완료
- analytic/simple limit 재현

---

## PR-03 — Exact electron-frame Thomson tensor
**가중치:** 10  
**현재 점수:** __ / 10

### 목적
FRW형 \((\Theta_2-\sqrt6E_2)\) shortcut에서 출발하지 말고, electron rest frame exact tensor를 직접 구현한다.

### 핵심 수식
source tensor:
\[
\tilde\zeta_{ab}=\frac34\tilde I_{ab}+\frac92\tilde E_{ab}
\]

exact collision skeleton:
\[
\tilde{\mathcal C}_I(E,\tilde e)
=-\tilde n_e\sigma_T I(E,\tilde e)
+\frac{\tilde n_e\sigma_T}{4\pi}
\left[\tilde I(E)+\tilde\zeta_{ab}(E)\tilde e^a\tilde e^b\right],
\]
\[
\tilde{\mathcal C}_{ab}(E,\tilde e)
=-\tilde n_e\sigma_T P_{ab}(E,\tilde e)
+\frac{\tilde n_e\sigma_T}{4\pi}
\left[\tilde H_a{}^{c_1}\tilde H_b{}^{c_2}\tilde\zeta_{c_1c_2}(E)\right]^{TT}.
\]

### WBS
1. electron-frame 변수 정의
2. out-scattering 구현
3. in-scattering 구현
4. intensity / polarization 공통 source 구현
5. classical Thomson limit 가정 명시

### 산출물
- `collision/exact_thomson_tensor.py`
- `collision/electron_frame.py`
- `tests/test_thomson_linearity.py`
- `docs/THOMSON_AUTHORITY.md`

### smoke test
- [ ] \(af_1+bf_2\) 입력에 대한 collision operator 선형성 확인
- [ ] isotropic radiation input에서 polarization source 0 확인
- [ ] pure quadrupole input에서 expected response 확인

### kill criterion
- collision을 여전히 FRW shortcut으로만 구현하면 실패
- electron frame과 normal frame을 섞어 쓰면 실패

### done definition
- exact tensor API가 Tier A / Tier B 모두에서 재사용 가능
- linearly exact operator test 통과

---

## PR-04 — Tilt framework and species frame split
**가중치:** 10  
**현재 점수:** __ / 10

### 목적
tilt를 species별로 정의하고, baryon/electron tilt와 CDM tilt를 분리한다.

### 핵심 수식
species 4-velocity:
\[
u_{(s)}^a=\gamma_s(n^a+v_{(s)}^a),\qquad \gamma_s=(1-v_s^2)^{-1/2}
\]

stress-energy decomposition:
\[
q_a^{(s)}=\gamma_s^2(\hat\rho_s+\hat p_s)v_a^{(s)},
\qquad
\pi_{ab}^{(s)}=\gamma_s^2(\hat\rho_s+\hat p_s)v_{\langle a}^{(s)}v_{b\rangle}^{(s)}.
\]

optical depth correction:
\[
d\tilde\tau=\tilde n_e\sigma_T\gamma_e(1+v_e\cdot e)\,dt
\]

### WBS
1. species 4-velocity 구현
2. stress-energy decomposition 구현
3. boost rule for intensity/polarization multipoles
4. optical depth correction 구현
5. “all species same tilt” 금지 또는 toggle화

### 산출물
- `tilt/species_frames.py`
- `tilt/stress_energy.py`
- `tilt/boost_rules.py`
- `tests/test_tilt_frame_split.py`

### smoke test
- [ ] small-tilt limit에서 \(q_a\sim(\rho+p)v_a\) recovery
- [ ] tilt=0이면 orthogonal case로 복귀
- [ ] electron tilt만 넣었을 때 visibility modulation 확인

### kill criterion
- transport frame을 tilt frame으로 몰래 바꾸면 실패
- baryon/electron tilt와 CDM tilt를 구분 못하면 실패

### done definition
- frame split 문서/코드 일치
- tilt가 collision / visibility / source에 일관되게 연결

---

## PR-05 — Tier A exact angular PDE solver
**가중치:** 12  
**현재 점수:** __ / 10

### 목적
배경-level exact angular PDE를 직접 푼다.

### core equation
\[
\mathcal L_B[I,Q,U]=\mathcal C_{\rm Th}[I,Q,U;\tilde u_e]
\]

### WBS
1. angular representation 선택: grid / spectral
2. energy dependence 포함
3. Bianchi transport operator 구현
4. exact Thomson tensor coupling
5. time stepping / stability strategy
6. reference output serialization

### 산출물
- `tierA/angular_pde_solver.py`
- `tierA/state_representation.py`
- `tierA/time_integrator.py`
- `tests/test_tierA_background_only.py`

### smoke test
- [ ] background-only anisotropic run 성공
- [ ] isotropic run에서 FLRW-like static behavior
- [ ] energy/angular resolution 바꿔도 gross instability 없음

### kill criterion
- \(\partial_{\ln E}\) 항 누락
- collision과 transport가 따로 놀면 실패

### done definition
- Tier A가 truth/reference backend 역할 가능
- background anisotropy evolution 결과 저장 가능

---

## PR-06 — Tier B projected multipole solver
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
PSTF 또는 harmonic projection을 이용한 low-ℓ production path를 구현한다.

### 핵심 구조
\[
\mathbf X=\{\Theta_{\ell m},E_{\ell m},B_{\ell m}\}_{\ell\le L}
\]

### WBS
1. PSTF / \((\ell,m)\) basis 고정
2. exact background transport recurrence 구현
3. exact tensor collision의 multipole projection 구현
4. Tier A와 비교 가능한 observable interface 추가
5. source builder와 연결

### 산출물
- `tierB/multipole_basis.py`
- `tierB/projected_solver.py`
- `tierB/collision_projection.py`
- `tests/test_tierB_vs_tierA_lowell.py`

### smoke test
- [ ] \(L=4\) run 성공
- [ ] \(L=2\)는 강제 금지 또는 diagnostic-only
- [ ] low-ℓ에서 Tier A와 정성적 일치

### kill criterion
- FRW shortcut collision을 authority path로 쓰면 실패
- \(L=2\)를 production path로 허용하면 실패

### done definition
- Tier B minimal solver가 \(L=4\) 이상에서 stable
- Tier A와 observable 비교 가능

---

## PR-07 — Quadrupole-aware TCA
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
explicit \((\Theta_2,E_2)\) state와 shear-corrected quadrupole closure를 넣는다.

### 핵심 수식
source combination:
\[
\Pi^m=\Theta_2^m-\sqrt6E_2^m
\]

TCA closure:
\[
0 \approx S_{2,T}^m+\Gamma_T\left(-\frac{9}{10}\Theta_2^m-\frac{\sqrt6}{10}E_2^m\right),
\]
\[
0 \approx S_{2,E}^m+\Gamma_T\left(-\frac25E_2^m-\frac{3}{5\sqrt6}\Theta_2^m\right).
\]

startup prescription:
\[
\pi_\gamma=\frac{32}{45}k\tau_c(v_b+\sigma),\qquad E_2=\frac{\pi_\gamma}{4}.
\]

### WBS
1. \((\Theta_2,E_2)\) explicit state 추가
2. quadrupole-aware TCA branch 추가
3. source combination \(\Pi\) 구현
4. polarization source 인터페이스 정의
5. FLRW scalar TCA limit test

### 산출물
- `tca/quadrupole_state.py`
- `tca/anisotropic_quadrupole_closure.py`
- `sources/polarization_source_core.py`
- `tests/test_tca_scalar_limit.py`

### smoke test
- [ ] \(\Gamma_T\gg1\)에서 stable
- [ ] FLRW scalar limit에서 standard TCA behavior recovery
- [ ] \(\Theta_2,E_2,\Pi\) time series 저장 가능

### kill criterion
- \(\Theta_2\)를 algebraic shortcut로만 두고 \(E_2\)를 생략하면 실패
- polarization source를 후처리로만 다루면 실패

### done definition
- TT 외에 TE/EE source를 낼 수 있는 최소 polarization core 완성

---

## PR-08 — Recombination + reionization source wiring
**가중치:** 10  
**현재 점수:** __ / 10

### 목적
first pass에서 recombination microphysics는 isotropic history로 유지하되, visibility와 rescattering source를 production path에 올린다.

### 핵심 수식
\[
\Gamma_T(\eta)=a\,n_e(\eta)x_e(\eta)\sigma_T,
\qquad
\kappa(\eta)=\int_\eta^{\eta_0}\Gamma_T(\eta')d\eta',
\qquad
g(\eta)=\Gamma_Te^{-\kappa}
\]

reionization source:
\[
S_E^{\rm rei}(\eta)\propto g_{\rm rei}(\eta)\Pi(\eta)
\]

tilted면
\[
\tilde\Gamma_T(\eta,e)=a\tilde n_e x_e\sigma_T\,\gamma_e(1+v_e\cdot e),
\qquad
S_{E,\rm rei}\propto \tilde g_{\rm rei}[\tilde\zeta]^{TT}
\]

### WBS
1. recombination history adapter 연결
2. scalar visibility \(g(\eta)\) 연결
3. homogeneous tanh reionization 구현
4. \(g_{\rm rei}\Pi\) source 구현
5. tilted면 \(\tilde g,\tilde\zeta\) 경로 추가

### 산출물
- `history/recombination_adapter.py`
- `history/reionization_tanh.py`
- `sources/visibility_weighted_source.py`
- `tests/test_reionization_onoff.py`

### smoke test
- [ ] recombination history ingest 성공
- [ ] rei on/off에 따라 low-ℓ EE 차이 관찰
- [ ] source가 untilded/tilded 선택과 일관됨

### kill criterion
- first pass에서 direction-dependent atomic kinetics까지 강제하면 실패
- reionization 없이 low-ℓ polarization baseline을 주장하면 실패

### done definition
- recombination + reionization source wiring 완료
- low-ℓ EE/TE에 영향이 실제로 나타남

---

## PR-09 — Anisotropic LoS / propagator
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
FLRW의 단일 \(j_\ell\) kernel을 버리고 exact Bianchi propagator를 넣는다.

### 핵심 구조
\[
\mathcal G^{XX'}_{\ell m,\ell' m'}(\eta_0,\eta)
\]

또는 상태벡터 형식으로
\[
\mathbf X' = \mathsf L_B[n]\mathbf X + \mathsf C_T[v_e]\mathbf X + \mathbf S_{\rm pert}[v_e].
\]

### WBS
1. state propagator \(\mathcal G^{XX'}_{\ell m,\ell' m'}\) 정의
2. background geodesic/advection/rotation 내장
3. source vector 최소 구성 연결
4. isotropic limit에서 \(j_\ell\) recovery check
5. tilt-inclusive attenuation/source 교체

### 산출물
- `los/anisotropic_propagator.py`
- `los/source_vector.py`
- `tests/test_los_flrw_recovery.py`
- `tests/test_los_bianchi_transport.py`

### smoke test
- [ ] isotropic limit에서 FLRW kernel recovery
- [ ] Bianchi propagator로 low-ℓ TT/EE run 성공
- [ ] tilt visibility 켠 경우 source 변경 반영

### kill criterion
- 여전히 scalar \(j_\ell\) 하나로 production path를 유지하면 실패
- propagator에 polarization rotation이 빠지면 실패

### done definition
- anisotropic LoS run 가능
- FLRW/Bianchi switch 및 tilt switch 정상

---

## PR-10 — Cutoff policy and convergence campaign
**가중치:** 6  
**현재 점수:** __ / 10

### 목적
\(L=4\) 최소선, \(L=6\) 실전, \(L=8\) 검증이라는 정책을 수치로 확인한다.

### WBS
1. \(L=4\) baseline run
2. \(L=6\) production run
3. \(L=8\) convergence run
4. runtime / memory / observable error 기록
5. Type I vs VII_h 비교

### 산출물
- `experiments/conv_L4_L6_L8.py`
- `reports/CUTOFF_CONVERGENCE.md`
- `figures/conv_lowell_TT.png`
- `figures/conv_lowell_EE.png`

### smoke test
- [ ] L=4,6,8 모두 실행 성공
- [ ] runtime/memory 로그 저장
- [ ] low-ℓ observable 차이 곡선 생성

### kill criterion
- \(L=4\) 하나만 돌리고 convergence를 주장하면 실패
- L 증가 시 물리량이 wildly unstable하면 실패

### done definition
- \(L=4/6/8\) 비교 플롯과 summary 완성
- production cutoff 선택 근거 확보

---

## PR-11 — Validation / diagnostics / release gate
**가중치:** 10  
**현재 점수:** __ / 10

### 목적
논문화 가능한 검증 패키지를 만든다.

### 필수 진단
1. FLRW isotropic limit
2. no-tilt limit
3. no-rei / with-rei 비교
4. Tier A vs Tier B 비교
5. TT/TE/EE/BB low-ℓ plots
6. source decomposition plots
7. convention consistency audit

### 산출물
- `validation/run_full_validation.py`
- `reports/VALIDATION_PACKET.md`
- `figures/lowell_TT_TE_EE_BB.png`
- `figures/source_decomp.png`
- `figures/tierA_vs_tierB.png`

### smoke test
- [ ] validation jobs 모두 실행
- [ ] diagnostic figures render
- [ ] failures are reported as hard fail, not silent pass

### kill criterion
- FLRW limit 없이 Bianchi result만 제시하면 실패
- rei / tilt / cutoff / Tier A-B 비교가 빠지면 실패

### done definition
- release candidate validation packet 완성
- main claims를 뒷받침하는 최소 figure set 확보

---

## 4. observer-side 출력과 direction-dependent likelihood

### 4.1 observer-side 출력
최소 산출물은
\[
T(\hat n),\qquad Q(\hat n),\qquad U(\hat n)
\]
또는
\[
a_{\ell m}^{T},\qquad a_{\ell m}^{E},\qquad a_{\ell m}^{B}
\]
이다.

exact Bianchi에서는 통계적 등방성이 깨지므로 단순 \(C_\ell\)만이 아니라
\[
\langle a_{\ell m}^{X}a_{\ell' m'}^{Y*}\rangle
\]
의 full covariance를 고려하는 것이 더 정직하다.

### 4.2 likelihood 전략
추천 구조는
\[
\boxed{
\text{solve in }\Theta_{\ell m},E_{\ell m},B_{\ell m}
\ \to\ 
\text{evaluate likelihood in }T/Q/U\text{ or }a_{\ell m}^{T,E,B}
}
\]
이다.

즉 solver 내부 표현은 multipole 기반이 유리하고, direction-dependent likelihood의 최종 데이터 표현은 observer-side map 또는 projected \(a_{\ell m}\)가 더 자연스럽다.

---

## 5. background/perturbation IC 요약

### 5.1 background IC

#### orthogonal
\[
v_{(s)}^a(\eta_i)=0,
\qquad
q_a^{(s)}(\eta_i)=0,
\qquad
\pi_{ab}^{(s)}(\eta_i)=0.
\]

#### tilted
species별
\[
v_{e,i},\ v_{b,i},\ v_{c,i},\dots
\]
를 지정해야 하고,
\[
8\pi P_i^{\rm (tot)}
=
e^{-\alpha}\left(\sigma_{jk}C^j{}_{ki}-\sigma_{ij}C^k{}_{kj}\right)
\]
와 일치하도록 잡아야 한다.

### 5.2 perturbation IC: CAMB regular adiabatic seed

low-ℓ solver의 perturbation seed는 FLRW limit에서 CAMB standard IC로 가야 한다. superhorizon startup \(x=k\tau\ll1\)에서 regular seed는

\[
\eta_{\rm cov}
=
2\mathcal B_K^2\left[1-\frac{x^2}{12}\left(\mathcal B_K^2-\frac{10}{4R_\nu+15}\right)\right],
\]
\[
\Delta_\gamma=\Delta_\nu
=
\frac{\mathcal B_K^2}{3}x^2-\frac{\mathcal B_K^2}{15}\omega k^2\tau^3,
\]
\[
\Delta_c=\Delta_b
=
\frac{\mathcal B_K^2}{4}x^2-\frac{\mathcal B_K^2}{20}\omega k^2\tau^3,
\]
\[
q_\gamma=\frac{\mathcal B_K^2}{27}x^3,
\qquad
q_\nu=\frac{\mathcal B_K^2}{27}\frac{4R_\nu+23}{4R_\nu+15}x^3,
\]
\[
\pi_\nu=-\frac{4}{3(4R_\nu+15)}x^2+\cdots,
\qquad
G_3=-\frac{4}{21(4R_\nu+15)}x^3,
\]
\[
Z=-\frac{\mathcal B_K^2}{2}k\tau+\frac{3\mathcal B_K^2}{20}\omega k\tau^2.
\]

flat FLRW limit에서는 \(\mathcal B_K^2\to1\).

### 5.3 photon quadrupole / polarization startup
explicit \((\Theta_2,E_2)\)를 evolve할 경우 startup은 TCA manifold 위에 둔다:
\[
\pi_\gamma=\frac{32}{45}k\tau_c(v_b+\sigma),
\qquad
E_2=\frac{\pi_\gamma}{4}.
\]

즉 orthogonal이든 tilted든 quadrupole를 0으로 두는 것보다 TCA startup이 안정적이다.

### 5.4 orthogonal perturbation IC
\[
\delta X(\eta_i)=X_{\rm CAMB}^{\rm reg}(\eta_i).
\]
즉
\[
\delta\Delta_i,\ \delta q_i,\ \delta\pi_\nu,\ \delta G_3,\ \delta\eta,\ \delta Z
\]
를 그대로 넣고, photons는
\[
\delta\pi_\gamma=\frac{32}{45}k\tau_c(\delta v_b+\delta\sigma),
\qquad
\delta E_2=\frac14\delta\pi_\gamma.
\]
전체값은
\[
X_{\rm tot}=\bar X_{\rm Bianchi}+\delta X.
\]

### 5.5 tilted perturbation IC
먼저 electron frame에서
\[
\delta\tilde X(\eta_i)=X_{\rm CAMB}^{\rm reg}(\eta_i)
\]
를 주고, 그 다음 normal frame으로 boost한다:
\[
\delta X(\eta_i)=\mathrm{Boost}^{-1}_{\bar v_e}\left[\delta\tilde X(\eta_i)\right].
\]

leading-order PSTF boost rule은
\[
\tilde I_{A_\ell}
=
\tilde h_{\langle A_\ell\rangle}{}^{B_\ell} I_{B_\ell}
-(\ell-2)v^b I_{bA_\ell}
-\frac{\ell(\ell+3)}{2\ell+1}v_{\langle a_\ell}I_{A_{\ell-1}\rangle},
\]
\[
\tilde E_{A_\ell}
=
\tilde h_{\langle A_\ell\rangle}{}^{B_\ell} E_{B_\ell}
-\frac{\ell(\ell+3)}{2\ell+1}v_{\langle a_\ell}E_{A_{\ell-1}\rangle}
-\frac{(\ell-2)(\ell-1)(\ell+3)}{(\ell+1)^2}v^bE_{bA_\ell}
-\frac{6}{\ell+1}v^b\epsilon_{bc\langle a_\ell}B_{A_{\ell-1}\rangle}{}^c,
\]
\[
\tilde B_{A_\ell}
=
\tilde h_{\langle A_\ell\rangle}{}^{B_\ell} B_{B_\ell}
-\frac{\ell(\ell+3)}{2\ell+1}v_{\langle a_\ell}B_{A_{\ell-1}\rangle}
-\frac{(\ell-2)(\ell-1)(\ell+3)}{(\ell+1)^2}v^bB_{bA_\ell}
+\frac{6}{\ell+1}v^b\epsilon_{bc\langle a_\ell}E_{A_{\ell-1}\rangle}{}^c.
\]

startup visibility도 electron frame 기준으로
\[
\tilde\Gamma_T(\eta_i,e)=a\tilde n_e x_e\sigma_T\,\gamma_e(1+v_e\cdot e)
\]
를 쓴다.

즉 tilted IC의 핵심은 **CAMB seed 자체를 바꾸는 게 아니라, 어느 frame에서 seed를 주느냐를 바꾸는 것**이다.

---

## 6. 전체 WBS 순서

1. PR-00 Core freeze
2. PR-01 Background geometry
3. PR-02 Ray + basis transport
4. PR-03 Exact Thomson tensor
5. PR-04 Tilt framework
6. PR-05 Tier A angular PDE
7. PR-06 Tier B multipoles
8. PR-07 Quadrupole-aware TCA
9. PR-08 Recombination + reionization wiring
10. PR-09 Anisotropic LoS
11. PR-10 Cutoff convergence
12. PR-11 Validation gate

이 순서는 우선순위

\[
\text{exact transport} \to \text{exact Thomson block} \to \text{explicit quadrupole} \to \text{reionization} \to \text{LoS} \to \text{validation}
\]

에 맞춘 것이다.

---

## 7. 점수 시트 템플릿

- PR-00 Core freeze: __ / 10
- PR-01 Background geometry: __ / 10
- PR-02 Ray transport: __ / 10
- PR-03 Exact Thomson tensor: __ / 10
- PR-04 Tilt framework: __ / 10
- PR-05 Tier A angular PDE: __ / 10
- PR-06 Tier B multipoles: __ / 10
- PR-07 TCA: __ / 10
- PR-08 Recombination/Reionization: __ / 10
- PR-09 Anisotropic LoS: __ / 10
- PR-10 Cutoff/Convergence: __ / 10
- PR-11 Validation: __ / 10

총점:
\[
\mathrm{Progress}(\%)=\sum_i w_i\frac{s_i}{10}
\]

### 해석
- **0–25**: 아이디어/식 정리 단계
- **25–45**: notation freeze 단계
- **45–65**: 부분 구현 + smoke test 단계
- **65–80**: first scientific baseline
- **80–90**: 발표/초안 논문용 baseline
- **90–100**: production-grade validation 완료

---

## 8. 최종 한 줄 요약

\[
\boxed{
\text{low-ℓ tetrad-based Bianchi CMB solver의 PR/WBS 핵심은 }
\text{exact transport authority를 먼저 세우고, explicit }(\Theta_2,E_2)
\text{와 scalar }x_e(\eta),\text{ anisotropic LoS/likelihood를 순차적으로 닫는 것}
}
\]
