# HTT 여섯 논문 L01/S02 다음 연구 루프: 실제 R8 마스크의 spin-2 유한 연산자와 공통 STF nuisance 하한

2026-10-17 KST. 상위 publication authority: PR #552 HEAD `41178623ae9eb93fe4d13e5d792b7fd380ce66ce`, `docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json` original blob `ac4a94c3da13f142eaab3b06b5275b58096c95e1`.

## 1. 과학적 동기와 출처 구분

P2/L01의 병목은 실제 Planck PR3 polarized mask source와 저차 E/B에서 고차 polarization 하늘의 전파를 구분해야 한다는 점이다. 별도로 이전 R8 `cmb_controls.npz` (connected Dropbox path `/bianchi/htt_base/docs/generated/tensor_joint_r8/owned_controls/cmb/`)는 이미 사용자의 네 개 PR3 **TEMPERATURE map** 처리본으로부터 얻은 NSIDE64 RING 공통 교집합 `common_mask` (36,433픽셀)를 포함한다. 원본 NPZ SHA256 `196ea21a8bf8a7077560599117390d8e48e77ab2fc91194639fd5ca656e9ec7b`, mask raw bool SHA256 `2d8de2e26e7781d60438206c96016b6ead5d07455d67267e6d4d85d717220311`; `cmb.json` source `R8_SAME_SKY_PIXEL_CONTROL_V1`, `empirical_eligible=false`, `beam_policy=no beam deconvolution`. **이 마스크는 공식 POL PMASK가 아니다.** 여기서는 source-locked 실제 온도마스크의 scalar pixel geometry를 사용할 뿐, Q/U 하늘은 제조된 spin-2 기저이다. POL source acceptance를 거짓으로 선언하지 않는다.

공식 Planck IRSA PR3 mask 자료: https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/masks/; Planck 2018 IV https://doi.org/10.1051/0004-6361/201833881. Hivon et al. MASTER https://doi.org/10.1086/338126, E/B separation https://arxiv.org/abs/astro-ph/0511629, Alonso 2025 https://arxiv.org/abs/2410.07077. 이 연구의 계산량은 pseudo-Cl power estimator가 아니라 유한 Q/U simultaneous masked least-squares *coefficient response* 이다.

### L01 구성적 계산

기본 spin-frame은 각 HEALPix 픽셀의 (e_theta,e_phi), 원본 기존 PR #542 `spin2_finite.py`의 Wigner-d convention `a_{+2}=-(a_E+i a_B)`, `a_{-2}=-(a_E-i a_B)`을 그대로 사용한다. HEALPix RING pixel index -> theta,phi 변환을 pure NumPy로 구현했고 nside1/2/8/16/64 위상, 적도·극 캡 및 parity, spin2 ell2 m0 analytic normalization을 검증했다. 불변량: full-sphere `_2 Y_{20}=sqrt(15/(32 pi)) sin^2(theta)`, 
Integral |Y|² dOmega=1 (Wolfram independent) 및 original source mask bytes.

저차 spin2 64실수열 
A_L (ell2..5 E/B), 고차 spin2 90실수열 
A_H (ell6..8 E/B). 관측선택 행렬 W는 같은 마스크로 Q/U 두 행을 고른다. 

`K=(A_L^T W A_L)^(-1) A_L^T W A_H`, i.e. finite polarized mode-mixing for an OLS projection of manufactured spin2 Q/U on original R8 *temperature* support. Implementation uses QR triangular solve, independent low-identity residual test.

수치 결과 원본 R8 실제 선택 36433/49152=0.741231283; K shape [64,90], low design cond 2.24427618, ||K||₂=1.47070915, ||K_{B<-E}||₂ = ||K_{E<-B}||₂ = 0.8837651091, ||K_{E<-E}||₂ = ||K_{B<-B}||₂ = 1.0997046793. Identity residual 3.1e-15. Full HEALPix64 아닌 source-derived R8 mask에서만 이런 숫자가 나온다. **Planck PR3 full POL mask, beam, foreground, actual E/B coefficients injection, E2E physical null: NOT_RUN**, L01 `pending`.

실제 공식 PMASK용 스크립트 `src/native_planck_pol_response.py`는 사용자가 이미 로컬 `/mnt/extdrive/workdir/htt_open_data/planck/PR3/masks/`에 저장한 common/HM/OE native 2048 polarization FITS를 SHA256으로 fail-closed 재검사 후, `healpy.read_map(...nest=False)`가 원본 NESTED를 RING으로 변환하고 `hp.ud_grade`로 64 RING 화소로 내린다. 각 mask threshold .5를 명시하고 `common` 및 `common∩HM∩OE` 별도의 64x90 spin2 K를 산출한다. Native operator values are **not claimed computed on sandbox** because the FITS files and healpy are not mounted in this sandbox. `native_pol_response` geometry crosscheck with healpy pix2ang runs in local only, and source/PSNR claim needs native healpy spin convention crosscheck. `independent_healpy_spin_convention_check` calls native `healpy.alm2map_spin` for ell=2,3 and E/B m0, rejects mismatched phase or sign before real-mask K; this path is NOT_RUN in this sandbox.

## 2. S02: 네 겹치는 창의 coherent STF systematic 이론

정확히 동일한 CF4 35,970 unique-group NPZ SHA256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`, 원본 H03 통합 covariance 36x36 SHA256 `f73fa930809731e69193ea3f0876efe73c499d1e1ca7af05221d3a004247a404`, 원본 H03 ZIP `303c78ff655237edf87db972ce882142837fac8588d269d6cd861c76346fb219`을 복원했으며, 기존 2048개 **공동** 4-window draws를 원본 동일 seed/저장된 이론 모듈로 재생성. 이는 물리 posterior가 아닌 CF4 working Gaussian source-conditioned draws이다.

창 j의 positive apparent monopole H_j, STF5 vector s_j (고정된 하나의 coefficient basis)와 무차원 ratio `q_j = ||s_j + T_j delta|| / (H_j + deltaH_j)`를 정의한다. `||delta||<=b`, `||T_j||op<=1`, `||T_i-T_j||op<=eta_ij`, `|deltaH_j|<=a_j<H_j`를 **외부에서 공급한 가정**으로 사용한다. 어느 두 창 i,j에서 모두 `q_i<=t`, `q_j<=t`라면 삼각부등식:

`||s_i-s_j|| <= ||s_i+T_i delta|| + ||s_j+T_j delta|| + ||(T_i-T_j)delta|| <= t(H_i+H_j+a_i+a_j)+eta_ij b`.

**대우**: `||s_i-s_j|| > t(H_i+H_j+a_i+a_j)+eta_ij b`이면 모든 허용 shared nuisance completion에서 적어도 하나는 `q>t`이다. 이 pairwise certificate와 기존 independent-rectangle per-window lower indicator의 합집합은 `at-least-one` 사건의 *보수적* lower probability bound다. **Sharp for full coupled four-window feasible set is NOT claimed.** The population posterior and physical signed Gauss Q remain undefined. 다른 source/angles basis이면 T_j가 명시되지 않는 한 취소 불가.

실제 source-conditioned 동일 2048 draws, b=3, a_j=.2 km/s/Mpc, t=.02에서는 기존 rectangle forced 85/2048=0.04150390625, exact common transfer (eta=0) pairwise augmented lower 1094/2048=0.5341796875. eta bound .1 -> 638/2048=.3115234375, .25 ->273/2048=.13330078125, .5 ->106/2048=.0517578125, eta1 ->85/2048=.04150390625. A real method-selection or optical transport prior for eta would be needed to give these numbers an observational meaning; `H02` physical calibration and `K04` finite-z transfer both remain unverified.

## 3. QA, acceptance, next action

Independent checks: Wolfram scalar `_2Y_20` norm=1 and common-offset cancellation symbolic True; Python actual R8 mask geometry, full-sky spin2 low/high near orthogonality, exact low pseudo-inverse, source SHA lock, degenerate b common-offset counterexample, matrix T_i transfer norm bound numerical witnesses, source joint draw ID exchangeability, threshold strict inequalities, transfer mismatch monotonicity. Three-suite 26 tests passed in this run and new-location archive replay required. Native subagent NOT_RUN (no host tool), native Planck POL source & healpy NOT_RUN, Einstein-Boltzmann and physical Gaussian covariance NOT_RUN.

Next local command (official mask source already saved):

```
ROOT=/mnt/extdrive/workdir/htt_open_data
python src/native_planck_pol_response.py --root "$ROOT" --verify-only
python src/native_planck_pol_response.py --root "$ROOT" --out "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90.json"
```

One per-source realistic spin2/beam injection, measured observed high-ell E/B and FFP10 release-matched null still needed before L01/L03 physics admission. For S02, H02 inference must bound or calibrate coherent transfer `eta`, and one physically admissible same-congruence shear,omega,tilt,curvature/MES bound source must be supplied; *no physical unknown mass renormalization*.

Publication DAG original canonical `14/42 completed_scoped`, L01/S02 pending, seven external blockers same, six papers NOT_READY_TO_SUBMIT.
