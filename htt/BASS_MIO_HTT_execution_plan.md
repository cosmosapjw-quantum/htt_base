# BASS / MIO / HTT / TSC 업그레이드 실행계획안 (v3)

이 문서는 기존 실행계획안을 다음 세 가지 수정 원칙에 맞게 다시 정리한 버전이다.

1. **BASS는 canonical runtime owner인 Bianchi anisotropy system solver다.**
2. **MIO는 model-independent observatory다.**
3. **HTT는 hubble tilt tracker다.**
4. **기존 “Teff 파트”는 이름을 바꾼다. 새 이름은 TSC — Trace Semantics Controller다.**

중요:
- **Teff는 더 이상 아키텍처 모듈 이름이 아니다.**
- **Teff는 TSC 안에서 쓰이는 reduced trace/intensity chart의 수학적 이름**으로만 남는다.
- 이 변경 이유는, theorem/proof-obligation/validation 문서들이 공통으로 요구하는 바가
  “Teff는 full solver가 아니라 trace/intensity block semantics + source bridge + diagnostic layer”이기 때문이다.

---

## 0. 초압축 요약

- **BASS**는 exact Bianchi transport + exact electron-frame Thomson tensor를 core authority로 가진다.
- **MIO**는 global tilt / global anisotropy / model-independent observatory language를 담당한다.
- **HTT**는 local boost patch / survey patch / observer contamination semantics를 담당한다.
- **TSC**(새 이름)는 reduced trace/intensity chart, exact on-manifold source bridge, admissibility maintenance, one-field/two-field upgrade semantics를 담당한다.
- 최종 allow/block, source adequacy consumption, validation label emission은 **BASS만** 가진다.
- TSC는 runtime owner가 아니다.
- first pass에서 recombination microphysics는 isotropic history로 두고, visibility/source evaluation을 anisotropic하게 만드는 게 맞다. low-ell polarization 때문에 **reionization이 recombination보다 우선**이다.

---

## 1. 전역 architecture 헌법 문장

### 1.1 solver ontology

- **Characteristics = full transport closure**
- **BASS = canonical runtime owner**
- **Teff = reduced trace/intensity chart (수학적 ansatz 이름)**
- **TSC = 그 Teff chart를 operational하게 다루는 controller layer**

정직한 architecture 문장은 다음으로 고정한다.

> full nonperturbative solver의 본체는 characteristics이며, reduction은 transport law를 대체하지 않고 trace/intensity block 위의 statistical chart와 source bridge, diagnostic controller로만 작동한다.

### 1.2 exactness authority

목표는 “nonlinear Thomson kernel” 자체가 아니다.  
핵심 authority는 아래다.

1. **exact Bianchi transport**
2. **exact electron-frame Thomson tensor**
3. **tilt + shear + projection에 의해 생기는 nonlinear moment coupling**
4. **observer-side validated extraction**

즉 비선형성의 핵심은 “kernel이 본질적으로 nonlinear이라서”가 아니라,
**exact transport + exact collision tensor + anisotropic moment projection**에서 생긴다.

---

## 2. BASS 실행계획 (업그레이드본)

## 2.1 시작 모티베이션

BASS는 **Bianchi anisotropy system solver**다.  
이 이름을 정직하게 따르면, BASS의 1차 목표는 “저차 truncation이 어떻게든 돈다”가 아니라 **low-ℓ 전체를 정확히 구현하는 canonical solver baseline**이어야 한다.

따라서 BASS의 core authority는
- exact Bianchi background
- exact photon ray / polarization-basis transport
- exact electron-frame Thomson tensor
- anisotropic LoS / validated observer extractor
다.

## 2.2 BASS가 canonical runtime owner로 가지는 것

아래 항목은 전부 **BASS가 canonical runtime owner**로 가진다.

- low-ℓ transport spine
- streaming / collision / observable bridge wiring
- boost-domain policy enforcement
- sigma_min gate consumption
- source-side adequacy consumption
- validation label emission
- final reduction allow/block decision

즉,
- MIO는 gate owner가 아니다.
- HTT는 gate owner가 아니다.
- TSC도 gate owner가 아니다.

## 2.3 핵심 설계 고정점

- 목표는 **exact Bianchi transport + exact electron-frame Thomson tensor**다.
- first pass에서는 \(x_e(\eta), T_m(\eta)\) 같은 recombination microphysics를 isotropic history로 두고,
  visibility/source evaluation만 anisotropic하게 바꾸는 게 맞다.
- low-ℓ polarization 때문에 **reionization은 recombination보다 우선순위가 높다.**
- exact background를 정말 nonperturbative하게 가려면
  - **Tier A**: \((I(E,\theta,\phi),Q(E,\theta,\phi),U(E,\theta,\phi))\) angular PDE 직접 진화
  - **Tier B**: projected multipole solver
  로 분리해야 한다.

## 2.4 BASS 구현 체크리스트와 점수 규칙

각 항목은 10점 만점이고, 전체 진행률은
\[
\mathrm{Overall}(\%)=\sum_i w_i \frac{s_i}{10}
\]
로 계산한다.

점수 의미:
- 0–2: 개념만 있음
- 3–4: 표기/가정/식 고정
- 5–6: 코드 골격 또는 부분 구현
- 7–8: smoke test + limit check 일부 통과
- 9–10: 수렴/정합성/물리 검증 완료

### Core freeze
가중치 6

### Exact Bianchi background geometry solver
가중치 10

### Exact photon ray + polarization-basis transport
가중치 12

### Exact electron-frame Thomson tensor
가중치 10

### Tilt framework and frame split
가중치 10

### Tier A exact angular PDE
가중치 12

### Tier B projected multipole hierarchy
가중치 8

### Quadrupole-aware TCA
가중치 8

### Recombination minimal modification
가중치 5

### Reionization minimal modification
가중치 5

### Anisotropic LoS / propagator
가중치 8

### Cutoff and convergence plan
가중치 6

### Validation / limits / diagnostics
가중치 10

## 2.5 BASS immediate WBS (정렬본)

### PR-00 — Core freeze / authority fence
- core assumptions 문서화
- frame split 규약: transport는 \(n^a\)-frame, collision/visibility는 \(u_e^a\)-frame
- Tier A / Tier B 분리
- cutoff policy \(L=4/6/8\) 고정

### PR-01 — Exact Bianchi background geometry
- structure constants
- tetrad / connection
- Einstein–Bianchi ODE
- FLRW recovery
- Type I / VII_h 최소 2형 테스트

### PR-02 — Exact ray transport and polarization-basis transport
- anisotropic redshift
- angular advection
- basis rotation
- screen projector transport
- isotropic limit

### PR-03 — Exact electron-frame Thomson tensor
- electron-frame variables
- out/in scattering
- common intensity/polarization tensor source
- classical Thomson limit 명시

### PR-04 — Tilt framework and species frame split
- species 4-velocity registry
- stress-energy decomposition
- baryon/electron tilt vs CDM tilt 분리
- optical-depth correction
- tilt=0 / small-tilt tests

### PR-05 — Tier A exact angular PDE
- \(\mathcal L_B[I,Q,U]=\mathcal C_{\rm Th}[I,Q,U;\tilde u_e]\)
- energy derivative + angular advection + polarization rotation
- Tier A truth backend 역할

### PR-06 — Tier B projected multipole solver
- exact tensor projection 출발
- \(L=4\) minimal, \(L=2\) production 금지
- Tier A comparison hook

### PR-07 — Quadrupole-aware TCA
- \((\Theta_2,E_2)\) explicit closure
- shear injection
- tilded quadrupole closure
- stiff regime / FLRW scalar limit

### PR-08 — Minimal recombination and reionization wiring
- isotropic recombination history ingest
- anisotropic visibility/source wiring
- reionization bump + low-ell polarization source
- rei on/off diagnostics

### PR-09 — Anisotropic LoS / propagator
- scalar \(j_\ell\) single kernel 버림
- matrix propagator
- geometry + rotation + attenuation + source

### PR-10 — Cutoff policy and convergence
- \(L=4/6/8\)
- Type I vs VII_h
- runtime / memory / observable error

### PR-11 — Validation / diagnostics / release gate
- FLRW isotropic limit
- no-tilt limit
- with/without rei
- Tier A vs Tier B
- TT/TE/EE/BB low-ell package
- source decomposition plots

## 2.6 BASS final goal

BASS의 최종 final goal은 아래 한 문장으로 고정한다.

> **exact Bianchi transport + exact electron-frame Thomson tensor + anisotropic LoS + validated observer extractor를 포함한 canonical Bianchi anisotropy system solver**

---

## 3. MIO 실행계획 (업그레이드본)

## 3.1 이름의 의미

MIO는 **model-independent observatory**다.

즉 MIO는
- global tilt semantics
- background-level anisotropy interpretation
- tilted FLRW / tilted Bianchi의 model-level meaning
- global beta context production

을 담당하는 **observatory-facing interpretation layer**다.

## 3.2 MIO가 가지는 것

- global tilt semantics
- background-level anisotropy interpretation
- model-level meaning of tilted FLRW / tilted Bianchi
- global beta context production
- evidence / posterior / F,Q,Pi / preferred-axis posterior
- BASS outputs를 model-independent observatory language로 번역하는 interpretation firewall

## 3.3 MIO가 가지지 않는 것

- reduction gate owner 아님
- source adequacy owner 아님
- final allow/block owner 아님
- local patch owner 아님

## 3.4 MIO 최종 goal

> **BASS가 생산한 canonical observables와 runtime labels를 global tilt / global anisotropy semantics / model-independent observatory language로 번역하고, evidence / posterior / F,Q,Pi를 산출하는 interpretation controller**

---

## 4. HTT 실행계획 (업그레이드본)

## 4.1 이름의 의미

HTT는 **hubble tilt tracker**다.

즉 HTT는 global semantics를 담당하지 않고,  
**local boost patch / observer contamination / survey patch interpretation**을 담당한다.

## 4.2 HTT가 가지는 것

- local boost patch semantics
- observer contamination / survey patch interpretation
- patch-scale beta context production
- bounded local diagnostic helper

## 4.3 HTT가 가지지 않는 것

- reduction gate owner 아님
- source adequacy owner 아님
- final allow/block owner 아님
- global anisotropy semantics owner 아님

## 4.4 HTT 최종 goal

> **BASS canonical backend를 깨지 않으면서 local boost / local patch / bounded diagnostic를 제공하는 hubble-patch tracking helper layer**

---

## 5. 기존 “Teff 파트”의 새 이름: TSC

## 5.1 왜 이름을 바꾸는가

기존에 이 파트를 그냥 “Teff”라고 부르면 세 가지 오해가 생긴다.

1. Teff가 하나의 runtime module처럼 보인다.
2. Teff가 full solver처럼 보인다.
3. Teff가 source adequacy / allow-block / validation authority를 가진 것처럼 보인다.

하지만 theorem / proof-obligation / validation 문서들이 공통으로 요구하는 바는 다르다.

- Characteristics가 full closure다.
- Teff는 trace/intensity block의 semantics + source bridge + diagnostic layer다.
- Teff는 full polarization solver가 아니다.
- TT/EE/BB/TE의 channelwise responsibility map은 trace / spin-2 / high residual block으로 분리되어야 한다.

따라서 아키텍처 파트 이름을 “Teff”로 두지 않고,  
**TSC — Trace Semantics Controller**로 바꾼다.

## 5.2 새 이름의 뜻

**TSC = Trace Semantics Controller**

- **Trace**: 역할이 trace/intensity block에 국한됨
- **Semantics**: full transport law가 아니라 의미론적/reduced chart 계층임
- **Controller**: runtime owner가 아니라 chart selection, admissibility, upgrade recommendation을 담당

즉
- **Teff는 수학적 chart/ansatz 이름**
- **TSC는 그 chart를 operational하게 다루는 아키텍처 계층 이름**
으로 분리한다.

## 5.3 TSC가 가지는 것

TSC는 아래에 한정된다.

- reduced trace/intensity chart
- exact on-manifold source bridge
- diagnostic-guided controller
- one-field / two-field upgrade semantics
- trace-block admissibility maintenance
  - \(\Theta>0\)
  - BE면 \(\eta\le 0\)

## 5.4 TSC가 가지지 않는 것

- full transport owner 아님
- final reduction allow/block owner 아님
- source adequacy final owner 아님
- full polarization solver 아님
- full spin-2 propagation owner 아님
- global beta / local beta context owner 아님

## 5.5 TSC의 실제 역할

### A. chart layer
- one-field Teff chart
- two-field \((\Theta,\eta)\) chart
- higher-field는 future hierarchy

### B. source bridge layer
- exact on-manifold nonlinear Thomson source bridge
- intensity-side source semantics
- trace-source reconstruction

### C. diagnostic/control layer
- one-field mismatch detection
- two-field upgrade recommendation
- admissibility maintenance
- chart-level false-trigger elimination

### D. explicit non-claims
- Teff가 solver가 된다
- full polarization을 Teff가 닫는다
- BB까지 trace semantics만으로 충분하다
- TSC가 runtime allow/block을 결정한다

이런 말은 전부 금지다.

## 5.6 TSC final goal

> **trace/intensity block 위에서 Teff chart family를 operational하게 관리하고, exact on-manifold source bridge와 admissibility/upgrade diagnostics를 제공하는 bounded controller layer**

---

## 6. canonical deliverables (PR-13T 종료 기준)

### D1. canonical reduction policy
하나의 canonical decision object에 아래 세 조건을 통합:
- beta policy
- sigma_min floor
- source-side \(D_{\ge2}\) gate

**Owner: BASS only**

### D2. canonical source adequacy producer consumption
source proxy가 demo가 아니라 실제 BASS loop에서 `allow_reduction` 판정에 쓰여야 한다.

**Owner: BASS only**

### D3. validation label emission
최소 아래 labels가 canonical outputs에 포함:
- `trace_source_adequate`
- `trace_source_inadequate`
- `upgrade_to_twofield_candidate`
- `resolved_spin2_invisibility_risk`
- `mixed_channel_propagation_pending`
- `beta_policy_block`
- `source_Dge2_gate`
- `sigma_min_below_floor`

여기서
- final emission owner는 **BASS**
- `upgrade_to_twofield_candidate`의 chart-level meaning owner는 **TSC**
- observatory-facing interpretation owner는 **MIO**
다.

### D4. ownership freeze
BASS/MIO/HTT/TSC의 역할이 문서와 코드에서 동일하게 표현되어야 한다.

---

## 7. acceptance criteria

### A1. no ownership drift
동일한 runtime decision을 MIO/HTT/TSC가 소유하지 않는다.  
최종 allow/block은 반드시 BASS canonical path에서 나온다.

### A2. no semantic collapse
`global_tilt`와 `local_boost_patch`가 같은 field로 병합되지 않는다.

### A3. no source/propagation conflation
B2/B3/C4 해석 규칙이 canonical outputs에서 보존된다.  
즉 `source adequate, propagation pending` 같은 판정이 실제 가능해야 한다.

### A4. no blind inverse
sigma_min floor 또는 source gate 없이 inverse가 production에서 열리지 않는다.

### A5. no polarization overclaim
TSC는 “intensity-side exact source hook”까지만 말해야 한다.

### A6. no figure-first relapse
PR-13T 완료 전 figure regeneration branch를 열지 않는다.

---

## 8. recommended reintegration order

### T1. ownership freeze first
- BASS runtime owner
- MIO global context owner
- HTT local context owner
- TSC chart/control owner

### T2. source producer before inverse promotion
PR-13R producer와 PR-13S labels를 먼저 canonical BASS loop에 연결한 다음 inverse/runtime reduction을 연다.

### T3. kinematic discipline before mixed-channel claims
beta policy + context split을 canonical path에 먼저 넣고 그 다음 TT/TE 해석을 연다.

### T4. source hook before figure work
PR-13O/P/Q source hooks가 canonical source producer로 연결된 다음에만 artifact producer를 고정한다.

---

## 9. immediate patch sequence

1. ownership table를 BASS/MIO/HTT/TSC 기준으로 다시 작성
2. BASS canonical runtime entrypoint에 reduction decision object 추가
3. source-side adequacy producer 연결
4. validation label emitter 연결
5. kinematic context(global tilt / local boost patch) 주입
6. TSC chart/upgrader interface 분리
7. figure branch는 여전히 금지

---

## 10. repository layout recommendation

repo/
  src/
    bass/
      background/
      transport/
      collision/
      tilt/
      tca/
      history/
      los/
      observer/
      runtime/
      validation/
    mio/
      posterior/
      semantics/
      evidence/
      masking/
      observatory/
    htt/
      local_boost/
      patch/
      tracker/
      diagnostics/
    tsc/
      charts/
      source_bridge/
      admissibility/
      upgrade/
      diagnostics/
  tests/
  docs/
  artifacts/
  figures/
  external_data/

핵심:
- runtime/validation은 BASS 아래
- TSC는 chart/source/admissibility/upgrade만 담당
- MIO/HTT/TSC는 allow/block owner가 아니다

---

## 11. 최종 한 줄 권고

다음 단계의 가장 정직한 문장:
**BASS는 canonical runtime owner인 exact Bianchi transport / exact electron-frame Thomson backend이고,  
MIO는 global observatory interpreter, HTT는 local patch tracker, TSC는 trace semantics controller다.**
