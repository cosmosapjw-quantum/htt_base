# HTT 세 계보의 구성적 통합: Legacy × 현대 방법론 × 독립 관측

실행일 2026-10-15 KST. 신규 브랜치 \`research/htt-legacy-modern-obs-integrated-20261015\`. 기준선 \`2f053914bd7b1f0594f7f75aa2acaef3e1d5645a\` (Planck FFP10 실제 편광), 독립 CF4 FLRW branch \`d3943ab76362a07132199c763ea9022b642ee446\`을 **실제로 merge**한 통합 HEAD로 연구했다. 2026-07-21 원본 legacy 이론·코드와 2026-10-13 R2 adapter 원본도 각 SHA256와 사용 계약을 \`ORIGINAL_LEGACY_SOURCE_LINEAGE.json\`에 보존했다. 기존 소스 checkout \`obs/solver-free-dossier-20261014\`의 HEAD 13d8d85f, 원래 미커밋 57경로는 변경하지 않는다.

## 1. Legacy의 실제 목적을 복원한 물리·관측 인터페이스

- 원래 \`ch02_framework.tex\` Eq master-identity: 동일 1+3 congruence와 FLRW comparator에서 signed defect \`x = Sigma_std² - W_std² + Omega_tilt + DeltaOmega_k\`. 이 식은 geometry physical forward response를 가진 실제 state sample에 적용한다. 미관측 \`W²\`, tilt, curvature는 자동 0이 아니다.
- 원래 \`ch03_bianchi_bounds.tex\`: MES shear, vorticity, acceleration 여러 정리/계수. 정리·프레임별 조건을 정확히 보존한다. 현재 geodesic lane의 source conditional MES 정규화에 다른 legacy 정리의 \`B_omega\`를 이름만으로 넣지 않는다.
- 원래 \`ch05_teff.tex\` \`Theta-expansion\`: angular \`1 + A P1 + Q P2 + W sinθ cosφ + V sinθ cosθ cosφ\`; 실제 immutable legacy \`TeffMomentMap.moment\` 수치 Gauss-Legendre × Fourier 구적을 원형 참고로 사용한다. \`A,W,Q,V\`는 여기서는 온도 방향장 진폭이며 **물리 shear/vorticity/4-acceleration posterior가 아니다**.
- \`departure_posteriors.py\`, \`filling_fraction\` 및 현대 \`typefree_functionals\`: \`x,Q,Pi,F,G_F\`는 각기 다른 정의역·측도·물리 인증 조건을 갖는다. Bolometric angular functional \`F_4=<Theta^4>_\Omega\`는 MIO의 sign-clean certified sector fraction \`F\`가 아니고 추가 likelihood도 아니다.
- 독립 관측: Planck PR3 실제 같은 CMB 하늘 9개 temperature 처리 계수, gated FFP10 CMB-only 999 및 noise-only 300, 원본 SMICA Q/U + 실제 12+12 source-hashed polarized pilot. CF4 35,970 grouped galaxies의 apparent \`H_eff(z,n)\`, method-calibration sensitivity 및 독립 flat-LCDM luminosity-distance baseline. CMB–CF4 공통 source geometry likelihood가 없으므로 여기서는 별도 노드로 연결만 한다.

## 2. Legacy Teff의 정규화 오류를 원본 훼손 없이 교정

원본 \`ch05_teff.tex\`의 한 표기는
\`12 ∫_{-1}^{1} mu² P2(mu) dmu = 16/5\`를 구면 평균의 계수처럼 사용한다. 하지만 \`<f>_sphere = (1/2)∫_{-1}^{1} f(mu)dmu\`이고,
\`∫ mu² P2 dmu=4/15\`, \`<mu² P2>=2/15\`이다. 따라서 **정규화된 angular fourth moment의 \`A² Q\` 계수는 \`12×2/15=8/5\`**이다. Wolfram 유리수 적분 \`{4/15,2/15,16/5,8/5,0}\` 확인. 원래 실제 legacy numerical \`.moment\` 역시 현대 정확 다항식과 세 일반 A/W/Q/V 사례에서 절대오차 최대 2.0e-15로 일치했다. 따라서 교정은 새 adapter의 **source convention**, 원본 파일은 불변.

임의 축 회전까지 유지하는 새 finite dipole+STF quadrupole의 \`d,S\` invariant kernel은 다음을 계산한다.

\`\`\`
t(n)=d·n+n^T S n, S^T=S, tr S=0
D=d·d, J2=tr S², J3=tr S³, K1=d^T S d, K2=d^T S² d
<t²>=D/3+2J2/15
<t³>=2K1/5+8J3/105
<t⁴>=D²/5+4D J2/35+16K2/35+4J2²/105
F4-1=6<t²>+4<t³>+<t⁴>
\`\`\`

\`F4-1\`을 \`F4-1\`이라는 두 near-unit floating-point 값의 subtraction 없이 직접 계산한다. 회전 불변/finite map injection 검산과 legacy source byte-hash regression tests를 수행했다.

## 3. 독립 Planck 자료에 실제 적용한 사중극·팔중극 확장

최신 \`planck_lowell_irrep_projection.py\`, \`r7_cmb_product_response.py\`의 **orthonormal real Ylm** 및 retained source ID를 그대로 사용한다. \`ell2\`는 5개, \`ell3\`는 7개. 본 연구의 \`t(n)\`에서 물리적으로 측정되지 않은 \`ell1\`은 source-truncation **모형 가정**으로 제외하고 \`ell>=4\`도 포함하지 않는다.

각 Ylm은 차수 ell의 동차조화 다항식이므로 \`t^4\`의 최대 각도차수는 12. 방위각의 Fourier mode |m|<=12를 갖고, φ의 32개 균등점은 이를 정확하게 구적한다. φ 적분 뒤 µ 다항식 차수 <=12는 Gauss–Legendre 8 노드부터 정확하지만 16 노드를 사용하고 24×48 격자로 독립 검증했다. 실제 9 제품의 \`deltaF4\` 16×32 / 24×48 max difference=4.14e-25; 원래 \`ell2\` exact tensor code와 \`ell2+3\` 내 \`ell2 only\` replay max diff=1.16e-25.

**실제 SMICA_FULL 동일 하늘 조건부 계산:**

| 구성 | F4−1 |
|---|---:|
| ell2 only | 9.1671653691e-11 |
| ell3 only | 1.6384901281e-10 |
| ell2–ell3 mixing | -4.2623998415e-17 |
| ell2+ell3 total | 2.5552062388e-10 |

9 처리 제품 \`deltaF4(ell2+3)\` 범위 [2.5316823133e-10, 2.5714313513e-10]. 각각 같은 cosmological sky이며 9개의 독립 실현이 아니다. 실제 FFP10 999 CMB-only의 median \`deltaF4\`=5.9806946500e-10 (5%,16%,50%,84%,95% percentiles machine-readable); 300 noise-only 및 첫 300 ID-paired CMB+noise도 생성했다. 이 source bank는 해당 map-reducer로는 검증됐지만 Planck 최종 end-to-end/null/lensing foreground law라는 주장은 하지 않는다.

### 정확한 power와 morphology 구분

\`q(n)=t_ell2\`는 공간반전에서 짝함수이고 \`o(n)=t_ell3\`는 홀함수다. 따라서
\`\`\`
<t²>=<q²>+<o²>
<t³>=<q³>+3<q o²>
<t⁴>=<q⁴>+6<q² o²>+<o⁴>
F4_mix=12<q o²>+6<q² o²>.
\`\`\`
관측 source exact \`SMICA_FULL\`:
- cubic mixed contribution 12<q o²>=−4.2627419147e-17;
- quartic mixed contribution 6<q² o²>=+3.4207247655e-21;
- total mixed contribution −4.2623998422e-17.
- odd-parity forbidden Gaunt terms maximum 7.93e-32; reconstructed coupling/direct bandlimited operator difference 9.21e-26.

특히 \`6<t²> = (6/(4πT0²))Σ_{ell=2,3,m}|a_lm|²\`, 이미 같은 \`C2,C3\`의 power다. \`F4−1\`을 별도의 독립 evidence 또는 측정된 physical shear로 제시할 수 없다. 실제 SMICA_FULL에서
\`\`\`
power 6<t²>   = 2.5552073679e-10
higher angular shape 4<t³>+<t⁴> = −1.1290799147e-16
normalized s3 = <t³>/<t²>^(3/2) = −0.10157208795
normalized k4 = <t⁴>/<t²>² = 3.1595521463
ell3/ell2 mode power = 1.7873451671
\`\`\`
실제 9 처리제품의 higher shape absolute contribution / power는 6.886e-7 이하. FFP10 source CMB 999개에 대한 normalized skewness quantiles [−.46263848,−.29570655,−.00727479,.32144123,.48635945]. 형태 지표는 진폭 정규화와 분리하지만 **같은 원본 a_lm의 결정론적 함수**로, 독립 likelihood가 아니고 post-hoc 발견을 null significance로 승격할 수 없다.

## 4. MES legacy와 현대 범위 차이: 원본 함수 호출로 증명한 구현 불일치

R2 original adapter의 실제 \`htt/bounds.py\`, \`ssot.py\` SHA:
- \`1c304927fe9f26636cda6cfadf647d439d9d6f7d5b5ca0900559338f5078c76d\`
- \`45ed08cf2fd9649e049c88cb50a3ced8d069fc07efb85c1ead398e3a6e8b8ad8\`.

2026-07-21 별도 archived framework \`bounds.py\`는 \`htt.core.ssot\` import로 패키지 계보가 다르지만, R2와 \`B_sigma/B_omega/B_accel\` 함수 AST 정의가 동일함을 검증했다. 원본 R2 adapter로 source \`epsilon1=0\` 조건부 같은 실제 Planck 9개 \`epsilon2/3\`에 두 theorem algebra를 적용했다.

Legacy shear Bsigma = modern geodesic Bsigma (machine-verified). 그러나
\`\`\`
Bomega_R2 = (3/4)eps1 + 2eps2 + (2/7)eps3
Bomega_current_geodesic = (10/3)eps1 + (2/15)eps2
\`\`\`
이므로 \`U_omega=(3/2)Bomega²\`의 원본 대 현대 비는 **375.019652–379.212958**. 이것은 두 계보의 physical MES theorem/frame/derivative를 동치로 증명하지 않은 상태의 mismatch witness다. 원래 연구 아이디어를 부정하거나 물리적 우주론을 기각하는 발견이 아니라, 섞어서 계산하면 정규화 오류가 발생한다는 소스 검증이다. 원본 \`W²\`를 현대 \`Q=x/U_sigma\`에 동일 physical bound로 가져오기 전에 프레임·정리 계보/원전과 실제 텐서 정의를 다시 맞춰야 한다.

## 5. 실제 독립 CF4 관측 논문 브랜치와 병합

다른 thread/repo의 최신 \`research/htt-cf4-flrw-composition-20261015\` commit \`d3943ab76362a07132199c763ea9022b642ee446\`을 물리 관측 기존 branch와 실제 Git merge(merge commit \`206d2fc7...\`). 두 공유 metadata README/READY_QUEUE conflict는 두 실험 근거를 모두 보존하고 canonical machine \`PUBLICATION_DAG.json\`으로 ready snapshot을 재생성하여 해결했다.

실제 CF4 35,970 group / z in (.01,.1) source-observation inference:

| far–near log H_eff contrast | value |
|---|---:|
| observed apparent cz/D | -0.0727872412 |
| FLRW reference sourcewise cz/dL_FLRW | -0.0455738112 |
| residual after FLRW background response | -0.0272134300 |

Reference flat LCDM H0=74.6 km/s/Mpc, Om=.3153 is a **declared scenario** not a fit to CMB or transfer of the 9 Planck products. Method-composition vs within-method residual accounting is exact but NOT a causal decomposition; actual CF4 selection and peculiar velocity covariance are missing. Legacy \`Delta H∝d^-1\`/\`Delta q∝d^-3\` comparisons must be convolved with this physically valid source radial/angular window; raw H_eff drop cannot be declared beyond-FLRW.

## 6. Publication programme integration and next controlled experiments

Relevant six-paper tracks:
- P1 \`x,F,Pi,Q,G_F\`: mathematically typed legacy and modern posterior pushforward preserved, but source CMB-only F4 cannot identify all physical signed budget components. Do not set missing curvature/vorticity/tilt to zero, do not coerce signed x into certified F. \`S02\` remains pending.
- P2 low-ell morphology: new l2+l3 exact shape and parity invariants, 999 FFP source comparison and actual single Planck sky source products; usable **partial evidence** for \`L02\` but retrospective statistic family and matched null coverage unresolved; \`L01/L03\` physics gates remain.
- P3 redshift Hubble: newly merged source-specific exact flat-LCDM response and method standardization, but \`H02\` selection/systematic/peculiar covariance still incomplete.
- P4 local boost vs global tilt and P6 physical kinematics: current CMB Teff temperature S_ab not equal physical geometry shear; no cosmological global tilt or four-acceleration inferred by this analysis.
- P5 Bianchi identification: no full polarized Bianchi source atlas present in this observational experiment.

The article-worthy observational task is a joint **source-conditional methods/robustness paper** or six independent follow-on physical likelihood analyses, NOT immediately a beyond-FLRW detection. The next useful bounded scientific execution is a preregistered source-matched shape statistic on same-sky Planck masks/beam vs truly end-to-end FFP, and actual CF4 physical peculiar-velocity/selection likelihood, then only physically matched CMB–CF4 common-congruence transport. No physical evidence multiplication or completed publication gate asserted.

Sources: Planck 2018 IV DOI 10.1051/0004-6361/201833881; Planck VII DOI 10.1051/0004-6361/201935201; Rassat et al. 2014 JCAP08(2014)006 DOI 10.1088/1475-7516/2014/08/006 (masking/secondary effects); Stoeger–Araujo–Gebbie 1997 arXiv:astro-ph/9904346; Tully et al 2023 ApJ 944 94 DOI 10.3847/1538-4357/ac94d8; Stiskalek et al 2026 MNRAS 546(2) DOI 10.1093/mnras/staf2048. Legacy code/TeX exact SHA manifest \`ORIGINAL_LEGACY_SOURCE_LINEAGE.json\`; current source files and simulation IDs in individual JSON.

Execution provenance: remote Ubuntu Python 3.12; OpenBLAS 2 threads; Wolfram exact ∫ and polynomial normalization checked; SciSpace/Exa primary-source comparison; native subagent NOT_RUN (no native dispatch tool exposed), local Codex NOT_USED. Original owner checkout unmodified. No automatic merge to main, pull request, journal submission or future background work was performed.

## 7. 별도 관측 PR #531 / #532 소스와의 중복·해석 계약

이번 연구는 2026-10-14 별도 관측 PR #531 및 #532에서 생성한 실제
결과 JSON 11개를 각각의 **정확한 Git commit ref와 SHA256**으로 다시 읽고,
`INDEPENDENT_OBSERVATION_PR_CROSSWALK.json`에 연결했다.

* PR531의 DESI BAO `OA07`은 실제 단일 isotropic flat-LCDM scalar q_iso
  **conditional** profile이다. H(z,sky) 편차, geometric shear 또는
  Planck Bianchi evidence에 대한 추가 독립 검출로 사용할 수 없다.
* PR531 `OA06` SMICA scatter는 이번 FFP10 연구와 **동일한 K1 source
  cache**(`86b792c8213...`)를 사용한다. 동일 simulation source의 통계량을
  관측데이터 2세트로 중복 곱하지 않는다.
* PR532 Planck PR3 9-product 분석은 여전히 **하나의 CMB 하늘**이다.
* PR532 CF4 24 SNIa-only endpoint conditional scenario는 이번 35,970-group
  CF4 source와 같은 **출처 catalogue**다. 실제 galaxy/group overlap ID
  join 및 covariance 법칙 없이는 독립 posterior라고 가정하지 않는다.
* PR532 ACT DR4·SPT3G windowed spectra는 fixed diagnostic이며 Planck
  low-ell fullsky morphology의 동일 sample은 아니다. Union3 compressed
  spline은 개별 SN sky likelihood를 대신하지 않는다. Fiducial lensing
  release 역시 native Bianchi polarized source transfer가 아니다.

이 결과가 정확히 `legacy → upgraded core → observations`의 **무리 없는
공동 데이터/추론 DAG**에서 필요한 입력을 제시한다. 별도 PR/관측 프로그램의
기존 산출물은 역사적으로 보존하고 내용이 같은 잔차·파생량을 새
독립 observational likelihood로 다시 계산하지 않는다.

P1/P2/P3 후속 분석의 최소 공통 목표는 source overlap graph와
물리적 forward transfer를 갖춘 **하나의** selected joint law다.
그 이전에 (x,Q,\Pi)의 full physical posterior나 nonzero global tilt,
vorticity/Bianchi geometry identification을 주장하지 않는다.
