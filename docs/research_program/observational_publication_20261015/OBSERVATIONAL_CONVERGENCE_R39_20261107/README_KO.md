# HTT R39: 관측량 식별성 중심의 수렴 연구

**기준일:** 2026-11-07 (Asia/Seoul)  
**저장소:** cosmosapjw-quantum/htt_base  
**R38 기준:** research/observational-convergence-r38-20261107 @ 05e9d53449bd02973848da3306f72f63edd7fc54  
**R39 브랜치:** research/r39-observational-identifiability-20261107  
**주장 상한:** C0 / 설계·코드 계약. 관측 검출 또는 Bianchi 가족 판정 없음.

## 핵심 결정

R39의 주 parameter는 관측 harmonic 배열만이 아니라 field-valued 또는 선언된 basis로 절단한 kinematical state θ_K={σ_AB, ω_A, A_A, β_RM,A, β_MO,A}다. pointwise finite core는 17 real components이며 β_RO는 1차 closure의 파생 view다. x는 direct kinematic components, H-normalized copies, 혼합 tensor functionals, predicted CMB/count/Gaia/distance carriers를 모두 포함하는 sample × functional bundle다. x_C는 기존 signed budget의 선택적 scalar projection으로만 유지한다. 최종 목표는 D={a_lm,z_i,n_hat_i,flux,distance,proper motion,...}에 대한 단일 source-conditioned L(θ,ψ,η;D)=p(D|θ,ψ,η)를 구성하고, 하나의 joint posterior/compatibility region에서 x,Q,Pi,F,G_F를 산출하는 것이다.

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

## Kinematical theta와 likelihood

물리 state는 \(\sigma_{AB}\)(STF2 polar, 5), \(\omega_A\)(axial vector, 3), \(A_A\)(polar vector, 3), \(\beta_{\rm RM,A}\)(3), \(\beta_{\rm MO,A}\)(3)로 구성한다. \(\beta_{\rm RO}\)는 독립 vector가 아니라 first-order closure 또는 정확한 ordered tetrad composition으로 산출한다. optional \(\Delta\Omega_k\), spatial Ricci, Weyl blocks는 별도 extension이다.

Likelihood는 CMB T/E/B full covariance, selection-aware source-count point process, SN/CF4 direction-dependent distance, Gaia proper-motion VSH를 공통 \(\theta\)에 조건부로 연결한다. 공통 LSS/foreground/overlapping sources/calibration은 shared latent 또는 full cross-covariance로 처리한다. 각 probe의 marginal posterior를 단순 곱하지 않는다.

정식 계약과 예시 registry:
- KINEMATICAL_LIKELIHOOD_MODEL.md
- KINEMATICAL_FUNCTIONAL_REGISTRY.json

## Canonical STF5 chart

Shear 5-vector는 정규직교 기저가 아니라 `(Sxx,Syy,Sxy,Sxz,Syz)` 순서의 `STF5_CARTESIAN_XX_YY_XY_XZ_YZ_V1`이며 `Szz=-Sxx-Syy`다. 따라서 평탄화한 covariance/SVD에는 유도 Gram metric을 쓰거나 명시적으로 orthonormal basis로 변환해야 한다. R39 optical kernel은 이 canonical chart를 사용한다.

## Radial–transverse 광학 응답

선도 국소 radial rate는 \(d(\hat n)=H+\sigma_{ij}n^in^j-A_i n^i/c\)이고, Fermi–Walker triad의 angular drift는 \(\mu=P(\hat n)\sigma\hat n+\hat n\times\omega\)다. Catalogue triad 회전 \(\Omega\)가 있으면 B1은 \(\omega+\Omega\)를 측정한다. 따라서 vorticity 추론에는 독립적인 frame-spin calibration이 필요하다. 이 기존 LOOP C 유도를 R39 코드의 local optical submodule로 재사용했다. 실제 Gaia/CF4 분석 결과는 아니며, local operator의 source-level Jacobian만 설계·구현했다.

## Kinematical frame and functional identity

canonical VelocityFrameBundle의 β_RO, β_RM, β_MO는 모두 하나의 common coordinate_frame과 basis에서 성분이 표현된다. radiation/matter/observer frame ID는 상대운동의 endpoint role이지 각 벡터별 좌표계가 아니다. spatial basis가 다르면 같은 coordinate frame 안에서만 FrameTransport를 적용하며, 외부 자료가 실제로 다른 좌표 tetrad에서 온 경우에만 ordered Lorentz/tetrad bridge가 필요하다. β_RO의 canonical residual/status/remainder와 1차 합산 diagnostic은 구분한다.

기존 Cobaya joint adapter는 실제 관측 likelihood로 admission되지 않았다. zero/identity fallback과 hard-coded dipole, independent marginal log-likelihood 합산이 남아 있어 R39 production inference로 사용할 수 없다. provider 재사용 범위는 DATA_AND_COBAYA_PLAN.md에 기록했다.

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
