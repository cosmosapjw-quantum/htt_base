# R87 P0-B: CF4 실제 method contrast와 coherent PV 식별성 정리

**2026-11-20 KST. Source-conditioned derived/numerically checked, not a physical cosmological detection.**

입력은 original CF4 38,053 group table3/table4, R54/R58 selected 35,970 unique group IDs. J2000 ICRS observer-to-source n, CMB V3k/c, c=299792.458 km/s. Source SHA와 release ReadMe 원본은 R87 RESULT.json 및 CONTRACT.md에 고정한다.

## T1. Group-shared distance/PV를 소거하는 method-contrast 정리

여섯 방법 SNIA, FP, TF, SBFO, SBFI, SNII에 대한 published group distance modulus를 \(\mu_{gm}\) (mag), quoted error를 \(\sigma_{gm}>0\)라 하자. 이 release 숫자는 **이미 CF4 MCMC로 intercalibrated된 posterior-derived group summary**이므로 independent raw method likelihood가 아니다. CAL group modulus는 있으나 해당 per-method e_DMcal이 없으므로 CAL은 source lineage에만 남긴다.

조건부 weighted residual 목적함수 \(\mathcal L=\sum_{gm}w_{gm}(\mu_{gm}-a_g-\delta_m)^2\), \(w_{gm}=\sigma_{gm}^{-2}\), 그룹별 임의 common modulus \(a_g\)를 profile하면
\[
 P_g=\operatorname{diag}(w_g)-\frac{w_gw_g^T}{W_g},\quad
 W_g=\sum_mw_{gm},\quad
 F=\sum_gP_g,\quad b=\sum_gP_g\mu_g.
\]
**Derived theorem:** \(P_g{\bf1}=0\)이고 \(P_g\succeq0\). 그러므로 한 1PGC group의 물리적 true distance 및 radial PV 등 모든 공통 additive bias는 method-contrast에서 정확히 소거된다. 여러 방법이 동일 그룹에 있어도 한 물리적 group이고 독립 group sample size가 늘지 않는다. F는 edge weight \(w_{gm}w_{gn}/W_g\)를 갖는 6-method graph Laplacian이다. 연결된 source graph에 대해 rank(F)=5, 단 하나의 common additive method gauge가 미정이다. \(\delta_{\rm SNIA}=0\)은 단지 그 gauge의 좌표 선택이며 SN Ia의 절대 zero-point가 정확하다는 가정/측정이 아니다.

수치적으로 큰 diagonal 두 항을 빼면 일방법 group 35k 개가 허위 수치 정보를 만들 수 있어, R87 구현은 쌍별 edge weight만 누적하고 diagonal을 row sum으로 구성한다. 실제 F gauge-null residual은 약 \(1.14\times10^{-12}\) mag^-2이다. R87 테스트는 원래 group \(a_g\)의 임의 변화에 대한 정확한 projection 불변성과 독립적인 two-method edge-graph 검산을 포함한다.

실제 selected 35,970 group에는 원래 7 method-presence flags의 multi-positive가 926개이지만 CAL e_DMcal 부재 등으로 유효한 six-method joint-error contrast는 **922개 distinct groups**뿐이다. 일곱 flags 모두 zero인 185, CAL-only 두 group (20679, 59927), CAL+하나의 six-method만 있는 네 group은 구분한다. Fit source network는 rank 5이고 SNIA 기준 residual mag는
\[
 (0,-0.12134593,-0.17739771,-0.29381009,-0.11105237,+0.04683285).
\]
이는 이미 intercalibrated된 제품의 *residual method consistency* 수치다. Working diagonal Gaussian pseudo-errors를 새로운 absolute zero-point posterior, physical calibration covariance나 source-matched p-value로 해석할 수 없다. 원시 pre-intercalibration measure/CAL sigma 또는 joint MCMC chain 없이는 \(\Sigma_{\rm cal}\) 및 정확한 group calibration Jacobian을 역구성할 수 없다.

## T2. Source-disjoint spatial heldout가 검정하는 것과 검정하지 않는 것

네 개의 사전 지정된 fixed ICRS RA 영역 [0,90), [90,180), [180,270), [270,360) deg에서 한 그룹 ID는 정확히 하나의 fold에만 속한다. 다른 세 영역에서 잔여 method offset을 fit하고 남긴 fold의 group-profiled method residual loss를 평가한다. 실제 source train/test group 교집합은 모든 fold에서 0, heldout counts 3737,13421,15810,3002, loss \(\mathcal L_{\rm test}(\widehat\delta_{\rm train})-\mathcal L_{\rm test}(0)\)는 약 \(-30.657,-4.223,-42.074,-25.203\)다. 이들은 source-product spatial residual consistency 숫자이고 독립 물리 coverage 확률이나 sigma가 아니다. 원래 CF4 상호보정 MCMC는 모든 sky region을 사용했으므로 upstream method calibration에 data leakage가 존재한다.

Source-selected vs released original table3 method detection fraction은 FP 27509/27602=99.66%, TF 8343/10035=83.14%, SNIA 854/945=90.37%, CAL 11/336=3.27%, optical SBF 15/175=8.57%. 이는 R54/R58의 **analysis-selection conditional on already catalogued groups**, 진짜 unobserved galaxy selection/completeness function이 아니다. 조건부 mask response를 별도로 사용할 수 있지만 \(C_{\rm sel}\)이나 독립 survey null은 없다.

## T3. Coherent radial PV modes와 apparent H03 angular signal의 겹침

H03의 original 9-column apparent source design은 \(X=[d,\ d{\bf n},\ d(nE_A n)]\), \(d=10^{(\mathrm{DMzp}-25)/5}\) Mpc이다. 선언된 조건부 선형-Gaussian working model \(y=X\beta+U\xi+\epsilon\), \(\xi\sim N(0,\Lambda)\), \(\epsilon\sim N(0,D)\)에서 \(C=D+U\Lambda U^T\). **Exact linear algebra theorem:** 만약 \(U=XA\)이면
\[
 \widehat\beta_C=\widehat\beta_D,\qquad
 {\rm Cov}_C(\widehat\beta_C)=(X^TD^{-1}X)^{-1}+A\Lambda A^T.
\]
증명은 diagonal-WLS residual \(r_D\)의 \(X^TD^{-1}r_D=0\)를 Woodbury 식에 대입해 \(X^TC^{-1}r_D=0\)임을 확인하고, \(\widehat\beta_D=\beta+A\xi+(X^TD^{-1}X)^{-1}X^TD^{-1}\epsilon\)의 분산을 계산하면 된다.

실제 source에서 assumed coherent **velocity shear** \(n^iE_{Aij}d\,n^j\)는 H03 apparent STF5 mean span 안에 relative residual ~1e-15로 정확히 놓인다. sigma_shear=1.5 km/s/Mpc라는 **chosen scenario**에서 beta mean difference ~3.3e-12지만 conditional coefficient covariance trace는 31.75배가 된다. 반면 radial **velocity bulk** \(n\cdot B\)는 H03 apparent Hubble dipole \(d\,n\cdot D\)와 다른 거리 의존을 갖는다. Original sample에서 relative projection residual은 0.43-0.44, chosen sigma_bulk=150 km/s만 허용하면 conditional H03 fitted 9 coefficients가 최대 약 4.898 km/s/Mpc 이동한다. Combined low-rank 8 modes에서는 source mean 이동과 큰 covariance 증대가 함께 생긴다.

이는 진짜 coherent velocity covariance나 물리적 normal shear 검출이 아니다. Source-selected 35,970개의 original geometry와 선택된 **assumed** bulk/shear covariance family에서 성립하는 정확한 projection/uncertainty sensitivity mechanism이다. 실제 independent source-matched \(S_{\rm PV}\) field ensemble, physical calibration covariance, instrument selection uncertainty는 별도 필요하다.

## P0-B 과학 판정

Full source-accepted \(C_{\rm phys}=N_{\rm stat}+S_{\rm PV}+J_{\rm cal}\Sigma_{\rm cal}J_{\rm cal}^{T}+C_{\rm sel}\)의 각 항은 source/frame/units/null이 함께 정의되어야 한다. 여기서는 table3 actual method contrast와 reported e_DMzp 기반 **working diagonal** 및 existing PV model의 low-rank **assumed scenarios**만 수치적으로 확인했다. 원본 table3에서 absolute calibration posterior, actual MCMC-to-grouped J_cal, true S_PV source realizations와 C_sel을 추론할 수 없다. Sky out-of-sample source products도 independent upstream calibration coverage가 아니다. 따라서 source diagnostic P0-B 수행은 완료하지만 **FULL_PHYSICAL_COVARIANCE_AND_COVERAGE = BLOCKED**, physical \(\Pi\) 미정, Bianchi/normal-frame physical shear 미정, observed \(G_F\) transport 미정이다. 원래 R78 60/129 scientific DAG 및 SQ-CF4 next unchanged.

**Primary references:** Tully et al., Cosmicflows-4, ApJ 944, 94 (2023), DOI 10.3847/1538-4357/ac94d8, original CDS J/ApJ/944/94 ReadMe and EDD grouped-data dictionary; Duangchan et al., Prior-free cosmological parameter estimation of Cosmicflows-4, A&A 708 (2026), DOI 10.1051/0004-6361/202556645; Watkins et al., Analysing the large-scale bulk flow using Cosmicflows4, MNRAS 524 (2023) 1885, DOI 10.1093/mnras/stad1984. The external literature supports selection/PV/calibration caution but **does not** validate the user's internal R87 conditional scenario as a physical posterior.

**Units:** \(\mu,\delta\) mag; cz, bulk mode km/s; shear mode km/s/Mpc; H03 coefficient km/s/Mpc; covariance coefficient (km/s/Mpc)^2. Signature (-,+,+,+) and c retained throughout.
