# Mid/High-\(\ell\) Extension PR Plan for the Low-\(\ell\) Bianchi Solver

## 목적

이 문서는 현재의 low-\(\ell\) 전용 Bianchi CMB solver가 **이미 구현 완료되었다고 가정**하고, 이를 **mid-\(\ell\)** 및 **high-\(\ell\)** 영역까지 확장하기 위한 **최소한의 실행 경로**를 PR/WBS 형식으로 정리한 것이다.

핵심 철학은 바꾸지 않는다. 유지할 권위 경로는 다음과 같다.

- exact Bianchi ray / redshift / advection / polarization-basis rotation
- exact electron-frame Thomson tensor
- transport는 \(n^a\)-frame, source/collision/visibility는 \(u_e^a\)-frame
- isotropic scalar recombination history + anisotropic source evaluation
- homogeneous reionization + anisotropic rescattering

즉, mid/high-\(\ell\) 확장의 본질은 **새 물리를 발명하는 것**이 아니라, **low-\(\ell\) 전용 truncation과 quadrupole-centric closure를 production-grade hierarchy / LoS / likelihood로 승격**하는 것이다.

---

## 점수 규칙

각 PR은 10점 만점으로 평가한다.

- **0–2**: 아이디어/메모 수준
- **3–4**: 식/가정/인터페이스 freeze
- **5–6**: 코드 골격 + 부분 구현
- **7–8**: smoke test + 일부 benchmark 통과
- **9–10**: 수렴/정합성/진단까지 완료

전체 진행률은

\[
\mathrm{Progress}(\%)=\sum_i w_i\frac{s_i}{10}
\]

로 계산한다.

---

## PR-H0 — Extension authority freeze
**가중치:** 6  
**현재 점수:** __ / 10

### 목적
mid/high-\(\ell\) 확장에서도 **절대 바꾸지 않을 것**과 **승격할 것**을 명시적으로 고정한다.

### 유지할 authority
- exact Bianchi transport
- exact electron-frame Thomson tensor
- \(n^a\)-transport / \(u_e^a\)-collision split
- scalar recombination history + anisotropic source
- homogeneous reionization

### 승격할 것
- low-\(\ell\) 전용 \((\Theta_0,\Theta_1,\Theta_2,E_2)\) 중심 state
- \(L=4/6/8\) 고정 cutoff
- quadrupole-only closure를 production dynamics처럼 쓰는 방식

### WBS
1. extension scope 문서 작성
2. immutable authority list 작성
3. deprecated low-\(\ell\)-only assumptions 목록화
4. retained hierarchy / LoS / likelihood 분리 방침 freeze

### 산출물
- `MIDHIGH_EXTENSION_FREEZE.md`
- `AUTHORITY_VS_EXTENSION.md`

### smoke test
- [ ] low-\(\ell\) authority path를 그대로 참조하는지 확인
- [ ] anisotropic recombination microphysics가 deferred로 명시되어 있는지 확인
- [ ] quadrupole-aware TCA가 startup/switching 장치로 격하되었는지 확인

### kill criterion
- transport frame과 collision frame이 다시 흔들리면 실패
- low-\(\ell\) cutoff \(L=4/6/8\)를 universal production cutoff처럼 적으면 실패

### done definition
- 모든 후속 PR이 이 freeze 문서를 authority로 참조

---

## PR-H1 — Scalar dynamic hierarchy bridge
**가중치:** 12  
**현재 점수:** __ / 10

### 목적
low-\(\ell\) 전용 상태벡터를 **production-style scalar retained hierarchy**로 승격한다.

기존 low-\(\ell\) 상태:
\[
\{\Theta_0,\Theta_1,\Theta_2,E_2\}
\]

승격 후:
\[
\mathbf X_{\rm dyn}=\{\Theta_{\ell m},E_{\ell m},B_{\ell m}\}_{\ell\le L_{\rm dyn}}
\]

### 배경
- shear는 \(\ell\leftrightarrow \ell\pm2\) coupling을 만듦
- tilt collision은 \(\ell\leftrightarrow \ell\pm1\) coupling을 만듦
- 따라서 quadrupole patch는 production dynamics가 될 수 없음

### WBS
1. scalar-only retained hierarchy 인터페이스 정의
2. photon temperature hierarchy 확장
3. photon polarization hierarchy 확장
4. neutrino hierarchy production set 설계
5. \(\ell\)-coupling sparse operator 설계
6. \(L_{\rm dyn}\) parameterization

### 산출물
- `hierarchy/scalar_dynamic_hierarchy.py`
- `hierarchy/polarization_dynamic_hierarchy.py`
- `hierarchy/neutrino_dynamic_hierarchy.py`
- `docs/DYNAMIC_HIERARCHY_NOTES.md`

### smoke test
- [ ] \(L_{\rm dyn}\ge 10\)에서 안정 run
- [ ] low-\(\ell\) observable이 기존 solver와 연속적으로 이어짐
- [ ] hierarchy 크기 증가 시 즉시 폭주하지 않음

### kill criterion
- \(\Theta_2,E_2\)만 explicit로 두고 나머지를 가짜 closure로 덮으면 실패
- neutrino를 계속 \((\Delta,q,\pi,G_3)\)에 묶어둔 채 production이라 주장하면 실패

### done definition
- scalar TT/TE/EE를 low–mid-\(\ell\) 연속적으로 생성할 수 있는 동적 hierarchy 완성

---

## PR-H2 — TCA role demotion and switching engine
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
quadrupole-aware TCA를 폐기하지 않고, **production dynamics의 본체**에서 **startup/switching 장치**로 내린다.

### 유지되는 TCA 핵심식
\[
0 \approx S_{2,T}^m+\Gamma_T\left(-\frac{9}{10}\Theta_2^m-\frac{\sqrt6}{10}E_2^m\right),
\]
\[
0 \approx S_{2,E}^m+\Gamma_T\left(-\frac25E_2^m-\frac{3}{5\sqrt6}\Theta_2^m\right)
\]

### WBS
1. startup TCA branch 분리
2. post-switch full hierarchy branch 분리
3. switch criterion 정의 \((k\tau_c,\mathcal H\tau_c,\text{source smoothness})\)
4. continuity correction 설계
5. tilt-inclusive tilded quadrupole switch 유지

### 산출물
- `tca/startup_switch_engine.py`
- `tca/switch_criteria.py`
- `tests/test_tca_to_fullhierarchy_continuity.py`

### smoke test
- [ ] TCA→full hierarchy 전환 시 \(\Theta_2,E_2\) jump가 작음
- [ ] tilt on/off 모두에서 switch가 안정적
- [ ] FLRW scalar limit에서 standard early-time behavior recovery

### kill criterion
- TCA를 production 전체 시간구간에 계속 쓰면 실패
- switch 직후 source나 spectra에 큰 인공 discontinuity가 생기면 실패

### done definition
- early stiff regime은 TCA, 이후는 full hierarchy라는 역할 분담 완료

---

## PR-H3 — Production scalar recombination history adapter
**가중치:** 10  
**현재 점수:** __ / 10

### 목적
synthetic/tanh-only visibility 또는 장난감 \(x_e(z)\)를 production path에서 내리고, **scalar recombination history adapter**를 붙인다.

### 핵심 철학
recombination microphysics 자체를 anisotropic하게 다시 쓰는 게 아니라,
\[
x_e(z),\quad T_m(z),\quad H(z)
\]
는 scalar history를 받아오고, source evaluation만 anisotropic하게 둔다.

### WBS
1. external history table interface 정의
2. \(\Gamma_T,\kappa,g(\eta)\) evaluator 구현
3. scalar history source of truth 고정
4. synthetic fixture를 unit-test-only 경로로 격리
5. FLRW benchmark visibility comparison 추가

### 산출물
- `history/scalar_recombination_adapter.py`
- `history/visibility_evaluator.py`
- `tests/test_visibility_against_scalar_history.py`
- `docs/RECOMBINATION_ADAPTER_POLICY.md`

### smoke test
- [ ] production run이 synthetic fixture 없이 돌아감
- [ ] visibility peak/width가 표준 scalar history와 일치
- [ ] low-\(\ell\)와 mid-\(\ell\) source가 동일 history backend를 공유

### kill criterion
- production path가 여전히 장난감 \(x_e(z)\)에 의존하면 실패
- anisotropic atomic kinetics를 끌어와 scope를 불필요하게 키우면 실패

### done definition
- scalar recombination history가 production authority로 승격

---

## PR-H4 — Reionization retention and upgrade
**가중치:** 6  
**현재 점수:** __ / 10

### 목적
reionization을 삭제하지 않고 production scalar high-\(\ell\) path에 유지한다.

### 핵심 source
\[
S_E^{\rm rei}\propto g_{\rm rei}\Pi
\]
또는 tilted면
\[
S_{E,\rm rei}\propto \tilde g_{\rm rei}[\tilde\zeta]^{TT}
\]

### WBS
1. homogeneous tanh rei module 유지/정리
2. hydrogen / HeII 2-step option 추가
3. rei source evaluator를 production source engine에 연결
4. tilt-inclusive visibility modulation 경로 유지

### 산출물
- `history/reionization_production.py`
- `sources/reionization_source.py`
- `tests/test_rei_source_persistence.py`

### smoke test
- [ ] rei on/off가 low-\(\ell\) EE에 계속 반영
- [ ] mid/high-\(\ell\) production에서도 rei path가 끊기지 않음
- [ ] tilt branch에서 \(\tilde g_{\rm rei}\)가 정상 작동

### kill criterion
- high-\(\ell\) 확장을 이유로 rei source를 제거하면 실패
- patchy reionization으로 scope 확장해 메인 경로가 흔들리면 실패

### done definition
- rei가 low/high production source engine 안에 안정적으로 남음

---

## PR-H5 — Generalized anisotropic LoS source engine
**가중치:** 14  
**현재 점수:** __ / 10

### 목적
low-\(\ell\) 전용 small-state propagator를 **mid/high-\(\ell\) production-grade generalized anisotropic LoS engine**으로 승격한다.

### 핵심 개념
FLRW의
\[
j_\ell
\]
대신 exact Bianchi에서는
\[
\mathcal G^{XX'}_{\ell m,\ell' m'}(\eta_0,\eta)
\]
형태의 background-dependent propagator가 필요하다.

### WBS
1. source-vector builder 일반화
2. \(\mathsf L_B\): anisotropic redshift/advection/rotation generalization
3. \(\mathsf C_T\): exact electron-frame collision generalization
4. propagator accumulation / Green-function engine
5. observer projection bridge 연결
6. isotropic FLRW limit recovery

### 산출물
- `los/generalized_anisotropic_source_engine.py`
- `los/propagator_matrix.py`
- `los/source_builder_general.py`
- `tests/test_generalized_los_flrw_limit.py`

### smoke test
- [ ] isotropic limit에서 standard LoS behavior recovery
- [ ] exact Bianchi Type I / VII_h-like에서 stable source propagation
- [ ] TT/TE/EE source channel 분리 진단 가능

### kill criterion
- 여전히 scalar \(j_\ell\)만으로 production path를 돌리면 실패
- propagator에 polarization basis rotation이나 tilted attenuation이 빠지면 실패

### done definition
- scalar mid/high-\(\ell\) production spectra를 생성할 generalized LoS 엔진 완성

---

## PR-H6 — Neutrino production hierarchy upgrade
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
neutrino를 startup용 \((\Delta,q,\pi,G_3)\) 패치에 묶어두지 않고, production-grade hierarchy로 승격한다.

### 배경
collisionless radiation인 neutrino도 mid/high-\(\ell\)에서는 더 높은 \(\ell\)까지 retained hierarchy가 필요하다.

### WBS
1. neutrino retained hierarchy 설계
2. collisionless Bianchi transport operator 연결
3. source feedback를 metric/redshift sector에 재연결
4. scalar FLRW benchmark 비교

### 산출물
- `hierarchy/neutrino_production_hierarchy.py`
- `tests/test_neutrino_hierarchy_flrw.py`

### smoke test
- [ ] neutrino hierarchy 확장 후 scalar TT/TE/EE가 안정
- [ ] FLRW limit에서 neutrino feedback이 정상 작동
- [ ] low-\(\ell\) benchmark와 continuity 보존

### kill criterion
- neutrino를 계속 startup-only 변수처럼 취급하면 실패
- photon hierarchy만 올린 뒤 전체 production이라고 부르면 실패

### done definition
- scalar radiation sector 전체가 production-grade hierarchy를 가짐

---

## PR-H7 — Retained cutoff vs output cutoff split
**가중치:** 6  
**현재 점수:** __ / 10

### 목적
high-\(\ell\) production에서는
- \(L_{\rm dyn}\): retained hierarchy cutoff
- \(\ell_{\max}^{\rm out}\): output spectra/map cutoff  
를 분리해야 한다.

### WBS
1. solver config에서 두 cutoff 분리
2. source engine과 output projector의 인터페이스 조정
3. convergence protocol 작성
4. memory/runtime scaling 측정

### 산출물
- `config/cutoff_policy.py`
- `reports/CUTOFF_POLICY_MIDHIGH.md`
- `tests/test_dyn_vs_out_cutoff.py`

### smoke test
- [ ] \(L_{\rm dyn}\)와 \(\ell_{\max}^{\rm out}\) 독립 조절 가능
- [ ] 두 cutoff를 바꿔도 코드 경로가 깨지지 않음
- [ ] runtime/memory scaling 로그 생성

### kill criterion
- retained/output cutoff를 다시 하나로 묶어버리면 실패
- convergence test 없이 숫자 하나를 production default로 선언하면 실패

### done definition
- cutoff architecture가 production-grade로 승격

---

## PR-H8 — Tier A reference backend preservation
**가중치:** 6  
**현재 점수:** __ / 10

### 목적
Tier A exact angular solver를 production main path로 쓰는 게 아니라, **reference backend**로 남기는 작업.

### 이유
exact Bianchi 문제는 frame-sensitive하고 비등방적이어서, 검증 백엔드가 없으면 나중에 틀린 지점을 추적하기 어렵다.

### WBS
1. Tier A reduced-resolution driver 유지
2. Tier B와 비교 가능한 observable dump 형식 통일
3. 작은 sky sample / 작은 \(\ell\) 범위 cross-check harness 작성
4. discrepancy report 생성기 추가

### 산출물
- `tierA/reference_driver.py`
- `validation/tierA_tierB_crosscheck.py`
- `reports/TIERA_TIERB_DIFF.md`

### smoke test
- [ ] 제한된 설정에서 Tier A/B 비교 가능
- [ ] observable dump 형식 일치
- [ ] discrepancy summary 자동 생성

### kill criterion
- Tier A를 버리면 실패
- Tier A/B가 서로 비교 불가능한 출력형을 쓰면 실패

### done definition
- production 확장 내내 validation anchor 확보

---

## PR-H9 — Scalar mid/high-\(\ell\) benchmark pack
**가중치:** 10  
**현재 점수:** __ / 10

### 목적
실제 산출물을 찍는다. 최소한 scalar TT/TE/EE high-\(\ell\) spectra와 low→mid→high 연속성을 보여주는 benchmark pack이 필요하다. BB는 null/consistency target으로 포함한다.

### WBS
1. scalar TT benchmark
2. scalar TE benchmark
3. scalar EE benchmark
4. scalar BB null/consistency benchmark
5. FLRW limit CAMB/CLASS 비교
6. Type I / VII_h-like sanity case

### 산출물
- `experiments/scalar_midhigh_benchmark.py`
- `plots/scalar_tt_midhigh.png`
- `plots/scalar_te_midhigh.png`
- `plots/scalar_ee_midhigh.png`
- `plots/scalar_bb_nullcheck.png`
- `reports/SCALAR_MIDHIGH_BENCHMARK.md`

### smoke test
- [ ] scalar TT/TE/EE spectra 생성
- [ ] FLRW limit 대조 플롯 생성
- [ ] BB가 FLRW scalar에서 작은 값 유지

### kill criterion
- TT만 그리고 production path라 주장하면 실패
- BB null/consistency check 없이 polarization path 완료라 하면 실패

### done definition
- scalar mid/high-\(\ell\) production path 실질 완성

---

## PR-L0 — Hybrid likelihood architecture freeze
**가중치:** 6  
**현재 점수:** __ / 10

### 목적
exact Bianchi에선 low-\(\ell\) direction-dependent information이 중요하지만, mid/high-\(\ell\)까지 전부 exact map likelihood로 가면 계산량이 너무 크다. 그래서 **hybrid likelihood**를 freeze한다.

\[
\mathcal L
=
\mathcal L_{\rm low\text{-}\ell}^{\rm exact}
\times
\mathcal L_{\rm mid/high}^{\rm compressed}
\]

### WBS
1. low-\(\ell\) exact part 정의
2. mid/high compressed part 정의
3. shared nuisance/foreground interface 정의
4. covariance / compression policy 문서화

### 산출물
- `LIKELIHOOD_ARCH_FREEZE.md`
- `likelihood/hybrid_architecture.py`

### smoke test
- [ ] low/high likelihood가 분리 정의됨
- [ ] exact Bianchi directional information이 low-\(\ell\) 블록에 보존됨

### kill criterion
- all-\(\ell\) exact directional likelihood를 production default로 선언하면 실패
- 반대로 low-\(\ell\) exact directional block을 버리고 \(C_\ell\)만 남기면 실패

### done definition
- hybrid likelihood 철학 고정

---

## PR-L1 — Low-\(\ell\) exact directional block
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
현재 low-\(\ell\) 강점을 그대로 살린다.  
즉
- \(a_{\ell m}^{T,E,B}\) likelihood
- 또는 \(T/Q/U\) map likelihood  
중 하나를 exact directional block으로 production inference에 남긴다.

### WBS
1. low-\(\ell\) alm dump 확정
2. optional map likelihood path 유지
3. observer metadata / frame metadata 저장
4. covariance diagnostics 추가

### 산출물
- `likelihood/lowell_exact_block.py`
- `diagnostics/lowell_alm_dump.py`
- `reports/LOWELL_EXACT_BLOCK.md`

### smoke test
- [ ] low-\(\ell\) exact block이 standalone으로 평가 가능
- [ ] observer-frame metadata 저장
- [ ] exact directional info가 compression 없이 보존됨

### kill criterion
- low-\(\ell\) exact block을 summary \(C_\ell\)만으로 대체하면 실패

### done definition
- 기존 low-\(\ell\) 강점 보존

---

## PR-L2 — Mid/high compressed block
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
mid/high-\(\ell\)는 계산량을 줄이기 위해 compressed likelihood block으로 묶는다.

### 후보
- pseudo-\(C_\ell\)
- compressed harmonic covariance
- block-diagonal approximation

### WBS
1. compression target 선택
2. covariance approximation 문서화
3. spectra ingestion path 작성
4. low/high interface 연결

### 산출물
- `likelihood/midhigh_compressed_block.py`
- `reports/MIDHIGH_COMPRESSION_POLICY.md`

### smoke test
- [ ] mid/high block standalone 평가 가능
- [ ] lowell exact block과 곱해져 full likelihood 구성 가능
- [ ] compression choice를 바꿔도 인터페이스 유지

### kill criterion
- mid/high까지 exact map likelihood를 기본값으로 강제하면 실패
- 반대로 low/high 구분 없이 모두 pseudo-\(C_\ell\)로 축약하면 실패

### done definition
- production inference path 완성

---

## PR-V0 — Vector sector opening
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
scalar가 닫힌 뒤에만 연다. vector는 \(m=\pm1\) bookkeeping, source normalization, polarization coupling을 별도로 열어야 한다.

### WBS
1. \(m=\pm1\) sector bookkeeping
2. vector source dictionary
3. vector observer projection
4. vector TT/TE/EE/BB test

### 산출물
- `modes/vector_sector.py`
- `sources/vector_sources.py`
- `tests/test_vector_sector_smoke.py`

### smoke test
- [ ] synthetic vector source에서 output 생성
- [ ] scalar path와 혼선 없음
- [ ] parity/sign convention 진단 가능

### kill criterion
- scalar sector 코드를 우겨 쓰기만 하고 \(m=\pm1\) normalization을 명시 안 하면 실패

### done definition
- vector sector 독립 smoke-test 완료

---

## PR-T0 — Tensor sector opening
**가중치:** 8  
**현재 점수:** __ / 10

### 목적
tensor는 \(m=\pm2\) sector다. vector보다도 나중에 여는 게 맞다.

### WBS
1. \(m=\pm2\) bookkeeping
2. tensor source dictionary
3. tensor polarization coupling
4. tensor TT/TE/EE/BB test

### 산출물
- `modes/tensor_sector.py`
- `sources/tensor_sources.py`
- `tests/test_tensor_sector_smoke.py`

### smoke test
- [ ] synthetic tensor source output 생성
- [ ] vector/scalar path와 분리 작동
- [ ] tensor BB behavior sanity check 가능

### kill criterion
- tensor sector를 scalar/vector와 섞어버리면 실패

### done definition
- tensor sector 독립 smoke-test 완료

---

## Deferred backlog

다음 항목들은 최소 트랙에서는 **보류**가 맞다.

- anisotropic recombination atomic network
- anisotropic Peebles \(C\)-factor
- direction-dependent escape probability
- patchy reionization
- lensing
- frequency distortions / recoil / induced scattering
- all-\(\ell\) exact map likelihood
- full foreground hierarchy

이유는 간단하다. 지금 단계의 병목은 아직 microphysics가 아니라 **hierarchy / LoS / likelihood 구조**다.

---

## 추천 실행 순서

1. PR-H0 Extension freeze  
2. PR-H1 Scalar dynamic hierarchy bridge  
3. PR-H2 TCA demotion / switching  
4. PR-H3 Scalar recombination adapter  
5. PR-H4 Reionization retention  
6. PR-H5 Generalized anisotropic LoS  
7. PR-H6 Neutrino hierarchy upgrade  
8. PR-H7 Cutoff split  
9. PR-H8 Tier A reference backend  
10. PR-H9 Scalar benchmark pack  
11. PR-L0 Hybrid likelihood freeze  
12. PR-L1 Low-\(\ell\) exact block  
13. PR-L2 Mid/high compressed block  
14. PR-V0 Vector opening  
15. PR-T0 Tensor opening  

---

## 점수판 템플릿

- PR-H0 Extension freeze: __ / 10
- PR-H1 Scalar dynamic hierarchy: __ / 10
- PR-H2 TCA demotion/switching: __ / 10
- PR-H3 Scalar recombination adapter: __ / 10
- PR-H4 Reionization retention: __ / 10
- PR-H5 Generalized anisotropic LoS: __ / 10
- PR-H6 Neutrino hierarchy upgrade: __ / 10
- PR-H7 Cutoff split: __ / 10
- PR-H8 Tier A reference backend: __ / 10
- PR-H9 Scalar benchmark pack: __ / 10
- PR-L0 Hybrid likelihood freeze: __ / 10
- PR-L1 Low-\(\ell\) exact block: __ / 10
- PR-L2 Mid/high compressed block: __ / 10
- PR-V0 Vector opening: __ / 10
- PR-T0 Tensor opening: __ / 10

총점:
\[
\mathrm{Progress}(\%)=\sum_i w_i\frac{s_i}{10}
\]

---

## 최종 한 줄 결론

**mid/high-\(\ell\) 최소 트랙의 본질은 low-\(\ell\) solver를 폐기하는 게 아니라, low-\(\ell\) 전용 truncation을 production-grade hierarchy / LoS / likelihood로 승격하는 것**이다.
