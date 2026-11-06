# HTT R39: 관측량 식별성 중심의 수렴 연구

**기준일:** 2026-11-07 (Asia/Seoul)  
**저장소:** cosmosapjw-quantum/htt_base  
**R38 기준:** research/observational-convergence-r38-20261107 @ 05e9d53449bd02973848da3306f72f63edd7fc54  
**R39 브랜치:** research/r39-observational-identifiability-20261107  
**주장 상한:** C0 / 설계·코드 계약. 관측 검출 또는 Bianchi 가족 판정 없음.

## 핵심 결정

R39는 scalar x_C가 아니라 tensorized HTT의 벡터/텐서 기능값 bundle x를 주 estimand로 삼는다. x는 sample × functional이며 각 functional의 rank/parity/frame/units/support를 보존한다. x_C는 기존 signed budget의 선택적 scalar projection으로만 유지한다. 물리 상태, 관측 carrier, nuisance, anchors 및 response remainder를 하나의 joint region에 보존하고 각 functional의 identified-set/posterior image를 계산한다.

상세 적용 규격은 VECTOR_TENSOR_X_FRAMEWORK.md에 있다. 이 문서는 기존 R8/R9의 vector/tensor MES, joint state, functional images, full covariance 및 depth path를 이번 cosmology programme에 연결한다. 이 통합 자체가 새 수학 정리나 관측 discovery라는 주장은 하지 않는다.

## R38 검증 결과

R38 branch와 commit은 실제 GitHub에서 확인했다. 그러나 R38 README의 미실행 서술과 DAG/claim ledger/EXECUTION_REPORT의 완료 서술이 충돌한다. joint adapter의 기본 경로에는 zero vector, identity/임의 diagonal covariance, hard-coded NVSS/Quaia summary, Pantheon random/zero fallback이 있다. response rank 스크립트는 수동 설계행렬과 block diagonal covariance를 구성한다. 보고된 condition number는 약 2.5342e17이고 chain summary의 parameters는 빈 객체다. 따라서 R38 joint posterior, rank 13/17, PPC, Bianchi selection은 source replay 전까지 observed inference로 인정하지 않는다.

기존 단일 probe 산출물과 morphology/theory work는 provenance를 분리해 보존한다. 이번 세션은 로컬 데이터에 접근하거나 실제 map/catalogue 분석을 실행하지 않았다.

## 과학 프로그램

여섯 독립 이론 루프:
1. low-ell morphology → T/E signed carriers, BipoSH, phase/planarity/parity, frequency/mask/beam transfer;
2. dipole anomaly → observer boost, residual radiation dipole, matter-radiation relative velocity, selection-aware tracer count dipole;
3. beyond-FLRW kinematics → congruence-dependent H, acceleration, shear, vorticity and optical/astrometric response;
4. anisotropy/Bianchi → spatial Ricci, electric/magnetic Weyl, structure constants, dynamics and family-specific transfer;
5. redshift/direction-dependent Hubble factor → local z→0 optical coefficient vs finite-z light-cone multipoles;
6. local boost vs global tilt → ordered tetrad map and nuisance-projected source-conditioned identifiable quotient.

주 분석 블록은 CMB T/E boost/BipoSH, Quaia/NVSS/RACS source counts, Gaia E/B VSH다. Pantheon+/CF4는 directional distance/Hubble validation 블록이다. DESI isotropic BAO compression에는 sky-axis leverage가 없으므로 directional evidence로 전환하지 않는다.

## HTT five-variable semantics

- x: heterogeneous sample × functional vector/tensor bundle.
- Q: matching anchor/gauge/margin.
- F: directional support, sample pushforward, measure-defined occupancy.
- Pi: strict exceedance surface under a named law; not automatically a p-value.
- G_F: full-covariance functional depth path.

다섯 output은 하나의 common state/region의 pushforward이지 독립 likelihood parameter가 아니다. Rank/parity, O(3)/SO(3), nonconvex/chiral strata, unavailable/undefined/unbounded/unresolved 상태를 보존한다. Unknown physical components are not zero-filled.

## 코드 변경 및 미수행 경계

R39 branch는 non-collinear exact two-frame velocity transformation을 수정하고 regression tests를 추가했다. Wolfram에서 collinear limit 및 non-collinear numerical-symbolic fixture를 확인했다. 로컬 pytest/CI는 실행하지 않았다. from_parameters의 beta_MO first-order closure, directional H acceleration units, R38 likelihood adapters and actual response-rank construction still need local repairs.

이번 작업은 GitHub-only다. 로컬 데이터 rehash, map/catalogue analysis, Cobaya sampler, new posterior, native Bianchi transfer and local test execution은 수행하지 않았다. See EXECUTION_REPORT.md and LOCAL_AGENT_RESUME.md.
