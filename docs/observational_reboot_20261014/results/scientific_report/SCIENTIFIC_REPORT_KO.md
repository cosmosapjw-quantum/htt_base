# HTT 관측 적용: 현재 자료의 조건부 과학 결과

## 주요 결과

**공동 거리 posterior.** Union3의 22개 압축 거리 node와 DESI BGS qiso를 하나의 flat-LCDM 관측법칙으로 적합했다. 기준 cross-covariance 가정 rho=0에서 Ωm=0.357456±0.027084, H0rd=9974.63±204.18 km/s다. 하나의 공통 magnitude offset을 적분하고 128/256/512차 quadrature를 비교했다. 다섯 rho 가정은 각각 공분산 민감도다. rho에 posterior odds를 붙이지 않았으며 H0와 rd를 따로 측정하지 않는다.

**CF4 선택 관측법칙.** 실제 24개 SNIa-only 그룹의 endpoint H posterior mean은 73.216174 km/s/Mpc, ESS는 1120.83다. H는 heliocentric endpoint 계수이며 cosmological H0로 해석하지 않는다. 같은 2,048개 draw ID와 weight에서 공유 zero point, dA, ztrue, dL을 계산했다. 반복측정 PPC exceedance는 0.678020다. 고정된 32개 조건부 주입 표본이 모두 수치 검사를 통과했다. H의 bias는 -0.357125, RMSE는 1.953703다. 이는 선언한 law와 근사 Wald 구간의 복원 검사이며 실제 CF4 coverage 인증이 아니다.

**SMICA 온도 morphology.** STF tensor family의 조건부 Monte Carlo rank는 17/241=0.070539, mask·fitted multipole·통계량의 48개 선택을 포함한 공동 scan rank는 63/241=0.261411다. 두 절차는 같은 관측 하늘과 같은 300개 signal/noise 행을 사용한다. 각 절차 안의 training 60행과 calibration 240행은 서로 겹치지 않지만, 두 결과는 독립 증거가 아니다. 전달 simulation 모형에 조건부인 회고적 rank이며 역사적 p=.039와의 차이를 개선량으로 해석하지 않는다.

**편광과 spectrum.** BK18의 정확한 BB-only release에서 고정 fiducial HL descriptor Q=545.104273를 계산하고 native Cobaya와 대조했다. primordial r fit, evidence, PTE가 아니다. CLASS의 200개 고유 split-noise 쌍은 고정 두 mask와 여섯 feature를 사용해 rank=0.00621118를 얻었다. EE가 joint maximum을 주도하며 독립 split-noise 근사에 조건부다. 관측 half-difference의 signal leakage, foreground, systematics를 검증한 physical null은 아니다.

FFP10의 첫 raw signal/noise 쌍을 NSIDE2048에서 직접 spin-2 변환했다. U±를 명시한 formal operator의 선형성과 signed cross term이 닫혔다. 좌표·polarization·raw-vs-005a processing bridge는 여전히 HOLD다. 한 쌍에서 ensemble null p를 계산하지 않았다. Planck/ACT/SPT spectrum residual은 해당 reference·window·covariance·foreground 조건에 묶이며, BeyondPlanck posterior-mean map도 독립 하늘이 아니다.

**다른 실제 자료.** COSMOS-Web 784016행 전체를 79개 batch로 검사했다. zfinal=0 placeholder를 포함한 출판값의 retention이며 galaxy photo-z 분포나 완전성 추정이 아니다. Gaia 4756개 frame source는 공개된 2×2 공분산으로 spin/glide를 적합하고 고정 8개 octant를 leave-out했다. upstream outcome-selected 표본이므로 독립 frame physics 검정이 아니다. CCHP의 183543개 photometry 행의 radial color, KiDS의 다섯 N(z), Union3 node 삭제, SDSS observer-box mock과 JWST의 공유 method calibration 결과도 연결했다.

Planck PR3의 정확한 source window·linear correction·공분산으로 reconstructed φφ reference amplitude A=1.009562±0.026253를 얻었다. fixed-CMB variant는 0.995252±0.024119의 같은 자료 민감도다. reference cosmology 자체가 Planck lensing을 사용하므로 release-consistency 결과다. CMB-marginalized 제품도 primary CMB 정보를 사용했으며 독립 calibration이나 독립 likelihood가 아니다. [상세 source와 native 대조](../planck_pr3_peak_closeout_v1/report.md).

## 관측법칙과 해석

CF4는 [∫p(eta)Πfi]/[∫p(eta)ΠZi]의 preselection law다. ∫p(eta)Π(fi/Zi)와 다르다. Gaussian redshift 좌표 y=c log(1+Vh/c)와 latent t=c log(1+ztrue)를 구별한다. dL=dA(1+ztrue)^2를 모든 적용 가능한 동일 draw에서 유지했다. Population, velocity width, calibration, absolute scale, finite-distance polynomial은 명시한 scenario다. Calibration prior의 폭을 .05에서 .10 mag로 바꾸는 민감도는 endpoint H를 약 73에서 67로 옮긴다. 유한거리 remainder upper bound를 인증하지 않는다.

공동 거리 law의 rho∈{0,±.25,±.5}는 released marginal covariance를 보존하는 가정 family다. 공통 M~Normal(43,5) mag을 정규화된 Gaussian 적분으로 처리했으며 Om~Uniform(.01,.99), H0rd~Uniform(5000,20000) km/s를 사용했다. CF4와 Union3의 object overlap·calibration, endpoint H→H0 bridge가 없어 CF4를 이 posterior에 곱하지 않았다. ACT+Planck, Planck marginal, PR3 reference, primary CMB, CLASS/FFP/mean map은 공유 정보를 가진 source이므로 별도 조건부 결과로 남긴다.

Monte Carlo rank p, posterior predictive PPC, posterior exceedance Pi, legacy power index를 구별한다. 공동 거리 posterior의 동일 ID/weight 함수상은 E, q_deceleration, H0DL/c, H0DA/c, DM/rd, DH/rd다. 같은 congruence의 Sigma2, W2, tilt, curvature, x ceiling에 대한 관측 bridge가 없으므로 physical x,Q,Pi,F4/MES의 unknown mass는 1이다. Flat-LCDM 거리 reference를 가정했다고 미관측 physical sector를 0으로 채우지 않는다.

## 그림과 상세 보고서

[공동 posterior](../posterior/report.md), [동일 draw 거리 함수상](../posterior/legacy_distance_image.pdf), [CF4 posterior](../cf4/posterior_v1/report.md), [CF4 latent/PPC](../cf4/latent_v1/report.md), [CF4 주입](../cf4/injection_v1/report.md), [BK18](../bk18_fixed_fiducial_v1/report.md), [CLASS](../class_noise_v1/report.md), [FFP 첫 쌍](../spectra_ffp10_first_pair_v1/report.md), [Gaia](../gaia_frame_v1/report.md), [COSMOS](../cosmos_selection_v1/report.md), [JAGB/KiDS](../jagb_kids_v1/report.md).

모든 수치는 report.json의 원본 result에 연결되며 figure_inventory.json이 그림과 source를 연결한다. PDF는 scientific_report.pdf다. 기존 RB00 pilot·calibration·response laboratory, OA/DESI, R7/R8 density·legacy adapter와 covariance/operator helper를 재사용했다. 상위 증명과 동일 입력의 큰 계산을 다시 시작하지 않았다.

## 검증과 잔여 입력

각 묶음에는 저자와 별도의 독립 read-only reviewer를 요청했다(requested Astra/xhigh; observed runtime UNKNOWN). 검토와 push는 scientific admission이나 main merge가 아니다. 원래 RB10/11/12/15의 전체 physical gate는 보존하고, 조건부 거리·보고서는 별도 RB23/25로 연결했다.

남은 입력은 global-history response, 같은 congruence의 physical tensor/MES ceiling·remainder, 실제 full-survey selection·calibration·object overlap law, raw-QE filter·mean field·bias, external native atlas다. FFP source-variant/convention bridge와 CLASS의 physical split law도 남는다. 정확한 상태와 재개 행동은 ../../RETURN.md 및 ../../BLOCKERS.json에 기록한다. 이 저장소에서 새 native Bianchi solver를 구현하지 않았다.
