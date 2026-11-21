# R91 2차 이론 R1–R10 / 코딩 C1–C10: 실제 실행 범위와 결과

기준 부모 HEAD: `96ea1f33af154f26e68acf7d39346ed86c67c87b` (2026-11-21, KST). 원본 R78 science SSOT SHA-256: `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11`. Metric signature는 \((- + + +)\), \(c=299\,792.458\ \mathrm{km\,s^{-1}}\). 신규 산출물은 **source-conditioned** 분석이며 원본 60개 과학 노드의 acceptance를 승격하지 않는다.

## R1–R3: 과학 계약·원전·과거 작업 계승

- 목표: SQ-CF4의 물리적 입력 상태를 다시 확인하면서, P1–P6와 PHY-01–07을 Boltzmann solver가 필요 없는 자료·모델·계산으로 최대한 전진시킨다.
- R47: solver-free Bianchi I geodesic-temperature 및 SO(3) tensor-orbit likelihood. R49: 일반 Class A/B 및 3-vector tilted matter와 source-conditional posterior. R62: 실제 CF4 35,970 groups, 7 nuisance/working covariance와 210개 tensor morphology 분류, source-response 비가환성 반례. R89/R90: six-paper 자료, 7 PHY 계산 및 84개 조건부 canonical/singular Bianchi witness. 이들 결과는 각각의 원래 claim ceiling을 보존한 채 재사용한다.
- 공식 코드와 문헌: [Cobaya Planck native data](https://github.com/CobayaSampler/planck_native_data), [Cobaya](https://github.com/CobayaSampler/cobaya), [Planck clik](https://github.com/benabed/clik), [Tully et al., Cosmicflows-4](https://iopscience.iop.org/article/10.3847/1538-4357/ac94d8), [Pontzen–Challinor 2007](https://arxiv.org/abs/0706.2075), [Fleury–Pitrou–Uzan, Bianchi I optics](https://arxiv.org/abs/1410.8473), [Saadeh et al., CMB anisotropic mode constraints](https://arxiv.org/abs/1606.05100).
- CAMB 및 Cobaya는 FLRW 대조 스펙트럼과 likelihood에 재사용할 수 있으나, isotropic \(C_\ell\)은 Bianchi 방향성 phase 및 \(a_{\ell m}\) 전달의 대체가 아니다. **CLASS DR1 40 GHz VEB transfer**는 CLASS 망원경의 **instrument response**, AniCLASS/Bianchi Einstein–Boltzmann native transfer와 다르다.

## R4–R5: 모델 후보 및 구성적 유도

### A. 기존 R36 CF4의 Fourier 상관 PV

R36은 동일한 35,970개 CF4 source의 네 개 window × 9 observable = 36차원 H03 추정량에 대하여 EH98 no-wiggle Gaussian density-field를 이용한 조건부 correlated PV를 계산했다. 실수/허수 Fourier kernel로부터 얻은 factor \(U_b\)는 다음을 만족한다.

\[
C_{\mathrm{PV},\,k\in[0.005,0.05]\,h\,\mathrm{Mpc}^{-1}}
=\sum_{b=1}^{2}U_bU_b^{\mathsf T}\succeq0.
\]

각 band의 \(U_b\)는 세 smoothing radius × 36 coordinates를 지원한다. R36 저장 파일의 band별 Fourier Gram과 원본 공분산의 첫 36차원 블록은 상대 Frobenius 오차 **0**으로 일치했다. \(R=5h^{-1}\,\mathrm{Mpc}\)에서

\[
\operatorname{tr}C_{\rm PV}=17.0583503226\,(\mathrm{km\,s^{-1}\,Mpc^{-1}})^2.
\]

Four-window cross-block Frobenius norm은 \(2.7343\), 대각 원소만 남긴 행렬의 norm은 \(3.5815\)이며 비율 \(0.7635\)이다. 따라서 이 finite conditional model에서는 window를 독립 변수로 처리하면 안 된다.

Cholesky GLS로 common 9-coordinate mean의 원래 R36 \(\chi^2=80.1376902394\)를 재현했고, R89 H03의 36개 raw coefficient와 최대 차이 \(4.3\times10^{-11}\)로 일치했다. 다만 R36에서 추가한 source noise SD 150 km/s와 four-method mean-design offset SD 0.4 km/s/Mpc는 **stipulated hyperparameters**, 원저자 upstream calibration이 아니다.

기존 R27 `FACTOR.npz`는 35,970 source의 일곱 method support에 대한 **finite additive-calibration quotient**일 뿐이다. 이미 보정된 발표 모듈러스 \(\mu_{\mathrm{pub}}=\mu_{\mathrm{pre}}+M\delta\)에 대해 임의의 \(\epsilon\)으로

\[
\mu_{\mathrm{pre}}'=\mu_{\mathrm{pre}}-M\epsilon,\qquad
\delta'=\delta+\epsilon
\]

를 취해도 같은 \(\mu_{\mathrm{pub}}\)를 얻는다. 이 gauge 자유도 때문에 발표 후 catalog만으로 **원래 MCMC posterior를 유일하게 역산할 수 없다**. 별도의 원자료·독립 anchor가 주어지면 **새로운 조건부 calibration reconstruction**은 가능하지만 원래 posterior와 동일하다고 할 수 없다.

### B. 이미 있던 Planck 2018 Plik-lite likelihood의 실행

기존 외장하드의 `plik_lite_v22.dataset`, Fortran record 613×613 covariance, TT 215/TE 199/EE 199 bins, Planck R3.01 published best-fit \(D_\ell\) 파일을 실제로 읽었다. Cobaya PlanckPlikLite의 weights 및 다음 likelihood를 그대로 따라 계산했다.

\[
D_\ell=\frac{\ell(\ell+1)}{2\pi}C_\ell,\qquad
\chi^2=(d-A_{\rm Planck}^{-2}t)^{\mathsf T}
C^{-1}(d-A_{\rm Planck}^{-2}t).
\]

고정 \(A_{\rm Planck}=1\)에서 \(\chi^2=585.474565887\) (613 bins), 상수항을 제외한 \(\log L=-292.737283\). 출판된 이론 곡선을 고정한 상태로 **한 가지 calibration parameter**만 profile한 조건부 결과는

\[
\widehat A_{\rm Planck}=1.000832871,\quad
\sigma_{A,\mathrm{conditional}}\simeq0.000775515,\quad
\chi^2_{\min}=584.318294.
\]

실제 CAMB 및 clik binary를 새로 실행한 것이 아니다. 이 분석은 **Planck high-\(\ell\) scalar power baseline**, Bianchi 저-\(\ell\) morphology/null가 아니다.

조건부 Commander quadrupole 크기 \(C_2=1.26130537596\times10^{-10}\,\mathrm K^2\)를 취하고,

\[
Q_A=\frac{\operatorname{diag}(2,-1,-1)}{\sqrt6},
\qquad Q_B=\frac{\operatorname{diag}(1,-1,0)}{\sqrt2}
\]

를 비교하면 두 STF가 \(\operatorname{tr}Q^2=1\)로 동일한 \(C_2=(8\pi/75)\operatorname{tr}(Q^2)\)를 가지지만 고유값 및 \(\chi=\sqrt6\operatorname{tr}(Q^3)/[\operatorname{tr}(Q^2)]^{3/2}\)는 서로 달라 각각 \(\chi_A=1\), \(\chi_B=0\)이다. Wolfram 정확연산과 HEALPix의 상대 \(C_2\) 일치 \(<7\times10^{-16}\)로 확인했다. 이것은 \(C_\ell\)-only가 Bianchi morphology/phase를 보유하지 않는다는 **구성적 반례**이며 관측상 새 Bianchi type 발견은 아니다.

### C. Gaia–Quaia 634,233 source의 실제 selection-weighted VSH

R90에서 공식 Quaia G<20.0 selection map과 기존 692,154 source join의 HEALPix index/selection 값의 **정확한 source identity**를 확립했다. R89와 동일한 품질조건을 거친 634,233개 QSO를 전부 이용해 각 source의 \((\mu_{\alpha*},\mu_{\delta})\) 공분산 및 2×16 tangent VSH E1/B1/E2/B2를 보존한 GLS를 수행했다.

상대 selection \(s_i\)와 선택 가중 \(g\)에 대한 estimator는

\[
F_g=\sum_iB_i^{\mathsf T}[g(s_i)C_i^{-1}]B_i,\qquad
\hat{\beta}_g=F_g^{-1}
\sum_iB_i^{\mathsf T}[g(s_i)C_i^{-1}]y_i.
\]

\(g(s)\in\{1,\ s,\ 1/\max(s,0.20),\ 1/\max(s,0.35)\}\)의 네 다른 working estimand에서 \(E_2\) amplitude는 6.413, 6.237, 6.512, 6.595 \(\mu\mathrm{as\,yr^{-1}}\). Signed E2 계수의 기준 대비 norm 변화는 0, 0.940, 1.179, 0.912 \(\mu\mathrm{as\,yr^{-1}}\)이다. 48개 nside2 sky patch leave-one-out jackknife covariance도 계산했다. 상대 selection map은 calibration된 개별 inclusion probability가 아니므로 역가중 결과를 cosmological shear 검출로 해석하지 않는다.

### D. Tilted Bianchi 모형과 형태론 attribution

R49의 general 3-vector tilt·Class A/B Einstein constraints 및 R62의 7개 nuisance covariance를 재사용한다. R90은 \(q_{\rm normal}=0\)이라는 조건부 Codazzi \(\mathcal C(N,a)\sigma=0\)의 kernel에서 \(\mathrm{SO}(3)\) 회전 자유도를 profile하여 84개 canonical/singular representative compatibility witness를 계산했다. 원래 관측 STF와 physical normal shear 사이에 실제 source transfer가 없으므로, 이는 고유 Bianchi family 식별이 아니다. 물리적으로 자유로운 \(q_a\)까지 허용하면 matter/EOS 제한에 따라 추가적 비식별성이 생길 수 있다.

## R6–R8: 검산·한계·판정

- R36 Fourier factor Gram 및 108D/36D covariance, R27 7-channel source quotient, R89 raw H03 coefficient identity 및 조건부 \(\chi^2\)를 재검산했다.
- Native Plik-lite binned \(C_\ell\) covariance/source와 fixed \(D_\ell\) best-fit reference를 로컬 구현으로 적합했다. TT/TE/EE marginal χ²의 단순 합은 613×613 joint χ²와 같지 않다.
- STF 두 형태의 정확한 non-\(\mathrm{SO}(3)\)-equivalence와 HEALPix 수치 \(C_2\) 등가성을 확인했다.
- Quaia full clean 634,233 source·4 가중방식·48 patch covariance를 계산했다.
- **미완성**: R36 low-\(k\) 외 physical PV, upstream CF4 calibration/selection/heldout, full Commander calibrated null, Gaia AGN/scan null, 일반 tilted non-I finite-\(z\) optical forward and external native polarized all-\(m\) CMB family atlas.

## R9–R10 및 C1–C10: 구현/인계

- R91 `WORK_DAG_OVERLAY.json`은 원본 60개 ID에 과거 상태 및 신규 source evidence를 정확히 연결한다. R78 60/129와 NEXT_ID SQ-CF4는 그대로이며, 전부 과학적 PASS라는 주장은 없다.
- `scripts/r91/deep_scan_inventory.py`는 두 root의 총 349,040개 파일을 **내용을 바꾸지 않고 metadata 전수조사**, 탐색 실패 0건. 전체 파일명과 local 후보 목록은 사적 `~/Downloads/htt_r91_local_inventory/`에만 저장했으며 GitHub에 게시하지 않는다.
- `scripts/r91/{cf4_legacy_pv_requalification,pliklite_baseline,planck_cl_morphology,gaia_quaia_full}.py`와 `run_second_cycle.py --check`는 실제 재현 가능한 수식/코드 연결과 10개 JSON 산출물의 content identity를 제공한다.
- C9: 동일 호스트의 bounded self-review 및 Wolfram STF 수학 검증까지만 시행. 호스트의 native subagent delegation tool이 없어 **native independent review NOT_RUN**.
- 이번 R91의 새 다운로드는 0 bytes. 이미 있는 `/mnt/extdrive/workdir` 자료는 읽기 전용 사용했고 PR4 전체 다운로드와 외장하드 mutation은 하지 않았다.

**다음 과학적 진입점**: R36 Fourier \(k\) support와 실제 CF4++ posterior의 source-matched coverage 확장, R27 + 독립 pre-intercalibration anchor를 통한 새로운 \(J_{\rm cal}\) 구성, Commander full T/E/B source-calibrated null, 일반 Bianchi finite-\(z\) Sachs/Jacobi 및 Gaia/Radio joint selection response. 이들이 원본 물리적 blocker를 대체하는 것이 아니라 해결하기 위한 후속 작업이다.
