# HTT six-paper: 공개 자료 기반 물리 입력 수용조건 연구 (2026-10-16 KST)

## 판정과 authority

기준: `cosmosapjw-quantum/htt_base` Draft PR #545, head `c352bcfbf4d77b4a9bffc5c109b34d6cb01bff9e`; publication overlay의 `PUBLICATION_DAG.json` (6 papers, 42 nodes). 이 연구는 그 DAG의 해석적·관측적 입력 준비를 위한 별도 연구 결과이며 아직 어떤 물리 수용조건도 PASS로 변경하지 않는다. 기존 상태는 `14 completed_scoped, 28 pending`, `S04,L03,H02,V03,B02,K03,K04` 7개 외부 입력 노드 미충족, 여섯 투고 gate 전부 `NOT_READY_TO_SUBMIT`. 기존 245-card engineering backlog와 미병합 draft/main을 수정하지 않는다.

### 전수조사 방법과 실제 커버리지

2026-09-25~2026-10-16 (KST) 생성 PR을 repo selector와 created-date filter를 가진 GitHub PR query로 조회했다. #471–#545의 연속된 **75개**가 확인됐고 경계의 #470은 2026-09-20 KST 생성으로 제외됐다. PR 전체 75개의 메타데이터·제목·description/claim을 수집하여 `THREE_WEEK_PR_INVENTORY.json`에 게시했다. 33 관측/출판/연구 archive, 32 CAS/formal, 5 유지보수, 5 CAS/runtime 기타. **전수 PR 설명 및 변경 후보 매핑을 했지만, 75개 diff 전체의 line-by-line code-review나 독립 replay가 수행되었다는 의미는 아니다.** 과학적 위험이 높은 #509–521, #524, #526, #532–545와 #479/#484–486/#504–508 등의 변경 경로를 별도 확인하고, 핵심 구현 파일을 원문 읽기로 비교했다. PR #524/#526는 대규모 과거 소스 보존이며 독립된 현재 관측 검증이 아니다.

중요 경로:

* #518 `htt/htt/htt/infer/cf4_product_provider.py`: CF4 원본 group summary만으로 all-method selection·covariance를 보정했다고 주장하지 않으며, `SlotAssumptions`가 정의한 **supplied** magnitude interval, velocity support, cross-covariance identity가 필수. #518 `R2-02/RETURN.md`에 38,053 실제 unique group, 2D latent integration, method-presence만 존재한다는 명시. 현재 35,970 *selected* group과 분리할 것.
* #517 `htt/src/common/structured_inference.py`: 고정 디자인, 주어진 선택함수·공분산의 structured Gaussian/Schur 및 bias interval. 실제 선택법칙을 추론하지 않는다.
* #520 `htt/htt/htt/infer/r7_joint_experiment.py`: 중복 source 제거 후 공통 latent를 한 번 적분하는 normalized selected joint-density interface. 소스별 선택 정규화 및 조건부 독립성은 입력 가정이지 검증 사실 아님.
* #521 `htt/htt/htt/infer/conditional_legacy_pushforward.py`: 원래 ID/weight 보존하는 image 계산은 가능하나 물리 x_C posterior는 구축되지 않음.
* #519 `htt/obsstat/r2_cmb_product_bridge.py`: 실제 product/mask identity가 필요하고, beam/transfer/foreground response는 caller supplied. 과거 intersection 36,433/49,152과 L01 현재 T support 26,846/49,152은 **별개 선택/연산자**. 모르는 beam을 identity라고 놓아 통과시키지 않음.
* #535–539 및 #542/#545: Planck 실제 temperature finite mask geometry와 고-ell leakage의 source-conditioned 결과는 재사용, spin2 E/B의 전체 physical E2E null은 미완.
* #479–486/#506 CAS07: 주어진 Jacobi 곡률 함수, 양의 determinant 및 거리에 관한 *조건부* 수학적 경계. source field 실재성, 관측 가능한 likelihood와 finite-z transfer를 유도·검증했다고 볼 수 없음.
* #504–505: 질량껍질 Lorentz/null form의 한정된 사영대수, tilt history transfer가 아님. #499–503/#508: 에너지 가중치·고차 moment·finite sphere quadrature의 부분 정리; 전역 polarized collision solver 완료와 혼동 금지.

## 7개 노드별 construction → observation → acceptance

### H02: 물리적으로 보정된 CF4 selection / 공유 calibration / peculiar velocities

공개 원본 **VizieR J/ApJ/944/94**: `table2` 55,877 개별 은하, `table3`/`table4` 38,053 공개 그룹(논문 초록의 38,065 그룹과 원시 catalog 실제 행수는 구분). 1PGC, DMzp, e_DMzp, RA/Dec, Vh(heliocentric), V3k(CMB), method counts/indicators의 원 행을 고정한다. Table4 `Dist,Vpec,Hi`는 모형 유도량이므로 독립 모형 외 velocity label로 사용하지 않는다.

최소 공개자료 기반 실행: (1) 원본 catalogue 38,053행·selected 35,970행에서 선택 predicate/결측/방법별 겹침·redshift-frame 행렬을 원 source 키로 직접 재현; (2) group constituent table2 ↔ group table3/4 matching으로 각 방법의 측정이 원래 group DMzp에 어떻게 기여했는지 추적; (3) published calibration anchor와 zero-point nuisance를 포함하는 *단일* 관측단위 likelihood 작성; (4) selection intensity `p(select|mu,method,z,sky,quality)`를 raw full-source coverage, 복제 가능한 empirical bounded family 또는 공개 injection mocks로 constrain; (5) cross-method shared calibration + correlated peculiar field covariance의 constrained/uncertain sets; (6) injection recovery/null coverage와 survey-dependent anisotropy/bulk model comparison. W1 Tully–Fisher 한 가지 방법만 사용하는 공통 photometry subset부터 물리 범위를 축소할 수 있으나 모든 CF4 방법/기하학의 gate를 통과한 것은 아님.

수용: exact source hashes/row IDs, error propagation with shared latent, selection normalizer, independent heldout families/patches, covariance PSD and heldout coverage, simulated and negative controls, prior-work Stiskalek 2026 null and Duangchan 2026 simulation comparator. 기존 #518/#520/PR545 rank 결과는 구현 재사용 근거이지 H02 physical PASS 아님.

### L03: Planck component separation + E2E exchangeable null

공개 PLA PR3 실자료 SMICA/Commander/NILC/SEVEM T/Q/U, full/HM/OE split, 실제 common-temperature/Pol mask 및 effective beams/pixel windows, FFP10 component-separated 실험별 **999 CMB and 300 noise/systematic** processing variants. PLA 문서 `dx12_v3_{method}_{cmb,noise,noise_hm1,noise_hm2,noise_oe1,noise_oe2}_mc_?????_raw.fits` 패턴을 사용하되 실제 release filename과 FITS extension, NSIDE, `ORDERING`, units, beam metadata는 다운로드 후 pin한다. 2020 NPIPE(공개 600 simulation maps) 사용 시 PR3와 다른 **독립 release lane**으로 취급한다.

T-only 작은 subset부터: 실제 PR3 T map, 동일 mask/beam, finite high-ell operator, matched 999 CMB × noise pairing rule, group별 independent underlying sky realization IDs. E/B branch에서 native `healpy.alm2map_spin`와 basis convention/EB parity/beam transfer/Pol-mask high-ell remainder, foreground component null + split correlated noises. 최종 null source pipeline 동일성/진폭/분포/온도-편광 cross covariance/자동 상관을 시험하고 사전 선택한 통계량의 empirical tail rank와 look-elsewhere를 별도 계산한다. 999개의 CMB와 300개의 noise로 999×300 *독립 우주*를 만들 수는 없다.

수용: real data와 null의 동일 처리경로 및 source units, injection/recovery, independent sky unit calibration, coverage and systematic adequacy. 현재 32×1053 온도 K 및 finite B는 일부만; L03 원 상태 유지.

### B02: 공개 AniCLASS 5-type polarized physical transfer subset

기존 다운로드된 `aniclass-class_aniclass.zip`과 공식 `CyrilPitrou/aniclass` public source의 version/commit/빌드 identity를 대조한다. 공식 구현은 작은 비등방 perturbative FLRW-limit Bianchi I,V,VII0,VIIh,IX의 T/E/B이며 all-11, 임의 tilt, 비선형 recombination/large shear가 아님. CLASS standard FLRW counterpart로 공통 background/recombination 검산. source conventions metric(-,+,+,+), orientation parity, mode and IC classification, scalar/vector/tensor all supported branches/IC, line-of-sight kernel, perturbation order를 lock. 독립 Pontzen–Challinor 2007, Saadeh et al. 2016의 제한된 물리 모드를 수치 비교. 실제 recombination / Thomson polarization / sky response / ell and stepsize convergence + heldout injection이 통과하면 **subset-specific B02 successor**의 acceptance 제안 가능; 기존 전-11 atlas B02를 자동 완료시키지 않는다.

### V03: local-boost endpoint와 global tilt source history

출발점은 PR #504 Lorentz + PR #544 V01 기저 수학. 새로운 물리 항은 
`d_{a\ell m}=M_a^{obs}B_{\ell m}\beta_{RO}+\int dt\,W_{a\ell m}(t)T_{\ell m}(t)\beta_{RM}(t)+N_{a\ell m}\eta`
처럼 관측 처리와 time-dependent tilt / collision/visibility가 독립적으로 결합되는 forward law. 서로 다른 z/reionization kernels, `T/E/B` cross-channel 또는 원격 kSZ dipole의 실제 optical depth/calibration로 response를 검정. **두 kernel이 다르더라도 β_RM(t)=constant이면 local endpoint column과 축퇴 가능**하므로 `SVD(C^-1/2 P_N [M_obs,M_history])`의 사전 rank/condition margin이 필수. CMB observer aberration/dipole 별도 official source; global tilt를 endpoint boost 재사용으로 만들지 않음.

### K03: source-qualified 비방사형 네 장

Gaia DR3 CRF3 quasar VSH astrometric proper-motion field (frame spin & **Solar observer acceleration**, not matter four-acceleration)과 공개 extragalactic source cross-match, sky completeness, parallax/proper-motion covariance and systematics. ideal homogeneous 3×3 velocity gradient model radial n_i G_ij n_j rank6; 충분한 (2) transverse components per object plus consistent distance units/calibration이면 rank9 제조 예제는 가능. 실제 quasar source proper motions reflect observer secular aberration, jet jitter, gravitational lensing etc, not automatically cosmic matter vorticity. 광학·시간 source-frame transfer 및 actual Gaia/CF4 same-population correspondence가 입증되지 않으면 observational `omega/A/beta`가 미식별.

### K04: local optical transfer + H02 선정된 실제 관측 법칙

Heinesen/Kristian–Sachs local sourceward 
`H_obs(n)=θ/3 - A_a n^a/c + σ_ab n^a n^b`, rank 1+3+5=9, vorticity antisymmetry leading local radial projection zero. Jacobi `D''(λ) = \mathcal{T}(λ)D(λ)`와 vertex `D(0)=0,D'(0)=I` (affine normalization lock), redshift flow and finite-z distance series including source velocity, longitudinal gradients, optical focusing, caustics/regularity. PR #479–486/#506 bound only **supplied tidal function**; need physically generated `\mathcal T` from Einstein–Boltzmann/light-cone cosmology and data-anchored priors or empirical verified null. Joint forward `p(y_CF4 | T_optical(ψ), S_H02,η_cal,C_vel)` + matched cross-window, H03 working 32d vs physical 9d mapping and null-space under nuisance. Unidentified directions reported unbounded/undefined.

### S04: 실제 관측 likelihood 하에서 정의된 signed Gauss/HTT 함수

`x_C=(σ_abσ^ab-ω_abω^ab)/(6H^2)+Ω_tilt+ΔΩ_k` with common congruence/normal/epoch, H!=0, signed; `Q=x_C/U_sigma` only positive externally proven shear-sector denominator (not global bound); `F` sign-clean sector only with certified ceiling, `Π` retains unknown mass and strict ties, `G_F` floor/depth coupling.

K02 phenomenological STF or PR521 conditional image supplies none of missing ω/tilt/curvature under common physical transfer. Two honest open alternatives: (a) restrict observational inferand to a *predeclared* physically identifiable subset and own source-covariance likelihood, explicit no total x_C; (b) construct outer identified sets for signed x_C under independently justified compact physical bounds for missing sectors. Without finite bound, interval can be unbounded and Π in [0,1], never fabricate informative posterior. Posterior uncertainty *and* partial-identification width / frequentist coverage must be distinguished (Manski 2003, Imbens–Manski 2004).

## 우선순위와 예산 (open-source only)

1. **기록·권한·선택의 SSOT**: public CF4 table2/group table3/table4, subgroup flags and SHA256 join; Planck real+mask/beam/FFP identifiers; independent release data ownership. CRF/other datasets cannot be conflated. CF4 H02 and Planck L03 are independent worktrees and can run concurrently.
2. **H02 minimal W1-only proper selected likelihood** + public CF4 group and galaxy raw source; original #517/#518/#520, simulation selected coverage. Deliver matched result with selection sensitivity; fail closed if public metadata insufficient. no invented TF underlying photometry.
3. **L03 temperature-only PR3 operator matched source + FFP10**; start small 20-50 *independent realization IDs* for smoke, then 300/999 via streamed or external HPC not ChatGPT sandbox; only after Pol branch real mask/beam. Report forecast runtime after measuring, never invent memory/time.
4. **B02 physical five-type subset** version-pinned AniCLASS build + accuracy/mode/small-anisotropy regression. Only extend via validated physical equations/IC/curvature branches.
5. **V03/K03/K04** distinct source-time and transverse response once H02 and B02 subsets ready. Public Gaia CRF3 quasar astrometry frame is calibration sanity test, not cosmic field detection; use ACT public maps only if paired velocity/τ/selection data become available.
6. **S04** last: compute only physically supported inferands and uncertainty; retain missing bound/unknown mass honestly. P1 Paper I/II TEFF are tools to audit information support, not substitute for a GR/source field posterior.

No 'download exists' label satisfies source/execution/model adequacy. `OPEN_DATA_GATE_MATRIX.json` enumerates exact named source files/fields and tests node by node. A known-prior result, partial code test, original source archive, actual simulation and physically calibrated likelihood are separate evidence types.

## 독립 수치 audit / TEFF 논문 입력

Inputs are two **user-supplied, unpublished manuscript drafts**:
`TEFF_PAPER_I_arXiv(7).zip` SHA256 `03e07321f702a533ac88f12d32739fe305c45924eae78cda3fec8975b9daa03d`, `TEFF_PAPER_II_arXiv(7).zip` SHA256 `639fb8fc15e3889dedebc3b1c128879ca8670c267478c78643fd4954b947e2c4`; archive CRC PASS. Content used by cited concept and sections only; original manuscript text/assets are NOT republished to public repo.

Paper I establishes exact radial-vs-angular entropy information budget under strict convex conjugate/lift domain; Paper II studies number/energy constraints and unresolved higher kernel responses in Fisher geometry, with velocity-dressed/massive aspects. New separate manufactured MB 4-support mixture holds m0,m3,m4 equal up to 1.8e-15 but different m5,m6 and spectra. For two possible positive spectra s0,s1>0 sharing all retained moments, minimax relative predictor has unique pointwise value `g=2 s0 s1/(s0+s1)` and exact loss `|s0-s1|/(s0+s1)`. At E/(k_B T*)=40 loss 0.98910459; 60 loss 0.99984865. This does NOT assert a universal high-E 100% error for any physically chosen temperature law, or prove spectral unidentifiability for all distributions. Additional physically measured spectral moments, a justified parametric shape/source kinetic equation, or weighted spectral norm and certified tail envelope must be added to make the target rate / photon spectrum inferable. Fisher projection of E² off span{1,E} has nonzero finite weighted residual 5.58354 in manufactured example and vanishes to ~1.3e-14 on adding E². This is direct constructive research for source-law adequacy and prevents angular-only fixes from being mislabeled full spectral coverage. Eight sandbox pytest checks including local optical rank 9/6/12 and ω radial null PASS; no native Einstein–Boltzmann solver executed.

## 결론과 STOP 조건

The 7 original physical input blockers remain **UNRESOLVED**. Mathematical prerequisites and source repositories are now located, with open data staged by priority. Before changing any original DAG status, require (i) independent source/measurement law, (ii) native physical forward, (iii) shared-sky/velocity/selection covariance, (iv) matched injections/coverage and (v) prior-art comparator. Scientific status: `derived`, `numerically_checked` (manufactured), `literature_supported` where primary sources verified; **not** `observational_physical_supported`, `implementation_verified` at native astrophysics, or a publication-ready result.
