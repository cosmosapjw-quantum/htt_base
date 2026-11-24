# R109 · 유한 tilt Bianchi 하늘의 부호 있는 전송과 조화 통계

기준은 R108 커밋 `6ca0a914d47d3c5eb4935926010970051f2008d3`이다. 아래 R1–R10은 명시된 근사에서 계산할 양과 판별 시험을 정의한다. 새로운 Rust 구현의 시험 통과 여부는 실행 영수증에서 판정한다. 기하와 운동량은 서명 (−,+,+,+), 오른손 공간 삼각대, ε₁₂₃=+1, 법선 길이시각 s=ct, K=HI+σ를 사용한다. H, σ, a, N은 모두 길이⁻¹, β는 속도/c, ρ와 q는 에너지밀도, 물리적 에너지 유속은 cq다.

| 확인한 Dropbox 원본 | 판독 위치 | SHA-256 |
|---|---|---|
| `/dossier/Dossier_I_Homogeneous_Geometry.pdf` | §§1.1–1.2, commutator·곡률·Codazzi strata | ce2e1b930612f0672e88284fd74b0660d1986fee093ad8fc760e89631bc49dc3 |
| `/dossier/Dossier_II_Kinetic_Transport.pdf` | §§1.4–1.5, 1.7, 식 (1.25)–(1.48), (1.70)–(1.72) | 8e4a20c228cb4f6760d258b9ecafb142423a7140698d45871b0151593feef075 |
| `/dossier/Dossier_VII_Observation.pdf` | §§1.1–1.4, 유한 관측자와 분석기, Kasner 축 운동량 | 562db108b9a6ce5a80e60d3c1303a89b65580168b06b2a6c45d62e11196034ad |
| `/dossier/BASS_Integrated_Dossier.pdf` | 인쇄면 59–60, 식 (5.97) 직후의 하늘 두 점 함수 | 3364768815063aa92915271d74df73e4026e42ccb3b66fb7d13425dce8c0ca0d |

위 경로의 October 폴더에는 통합본 및 I–VII가 있다. 별도의 `/bianchi/Dossier_II_Restored_Revised.pdf`(September 개정판) §18 식 (128)–(129)는 균질 이력과 공간 섭동의 선형화를 분리한다. REC/REI 고유 nₑ 및 시계는 [R105의 원본 잠금](../R105_RESEARCH_20261124/SOLVER_SOURCES_KO.md)과 [R108의 실제 z<4 경계](../R108_LOS_ATLAS_DATA_20261124/RESULTS_KO.md)를 함께 사용한다.

## R1 · 모든 Bianchi 계열에 대한 기하 입력

오른손 기저에서 [eᵢ,eⱼ]=Cᵏᵢⱼeₖ, Cᵏᵢⱼ=εᵢⱼₗNˡᵏ+aᵢδᵏⱼ−aⱼδᵏᵢ, N=Nᵀ, Na=0이다. Koszul 식 2Γʳᵢⱼ=Cʳᵢⱼ−Cⁱⱼᵣ+Cʲᵣᵢ로부터 ³R=−6a²−tr(N²)+(tr N)²/2. V에서 −6a², N=νI인 IX에서 3ν²/2다. 이는 R107의 과거 곡률 배율 오류를 판별한다. class A는 a=0에서 N 고유값 부호로 I(0,0,0), II(+,0,0), VI₀(0,+,−), VII₀(0,+,+), VIII(+,+,−), IX(+,+,+)를 포함한다. class B는 a=(A,0,0), N=diag(0,n₂,n₃)에서 V(rank 0), IV(rank 1), VIₕ(h<0), VIIₕ(h>0), h=A²/(n₂n₃)다. III=VI₋₁, 예외 VI₋₁/₉는 별도 rank 층이다. 한때의 고유값 중복과 Lie 계열을 구별한다. 각 fixture는 실제 commutator의 Jacobi, 곡률 및 proper rotation 공변성을 검산한다.

## R2 · 제약과 유한 proper tilt

Dⱼσʲᵢ=−3σᵢⱼaⱼ−εᵢₘₙNₘᵦσᵦₙ=−κqᵢ, κ=8πG/c⁴. 각 완전유체의 q=(ρ̂+p̂)γ²β, γ=(1−β²)⁻¹ᐟ²이다. 법선 해밀토니안은 3H²=κρ+Λ+σ:σ/2−³R/2. 기하가 요구하는 총 q와 모든 종의 q합이 일치해야 한다. 가령 I에서는 총 q=0이라 단일 물질의 독립적 유한 tilt를 자유롭게 주면 제약을 위반한다. 서로 보상하는 성분이 있으면 개별 tilt는 가능하다. 예외 VI₋₁/₉에서 n₂q₂+3Aq₃=0이고 추가 전단 자유도가 남는다. (ρ̂+p̂)=w>0인 한 보상 성분은 β=2q/(w+√(w²+4q²))로 안정하게 복원한다. R108은 생산식과 일부 helper의 Codazzi 부호가 반대임을 재현했다. 일관성 판정은 각 helper를 (i) 실제 구조상수로 직접 만든 Γ의 Dσ, (ii) 측정한 법선 운동량 −h·T·n과 비교한다. β↦−β에서 q는 홀수, 법선 에너지 보정은 짝수여야 한다. 유한 속도를 갖는 주어진 배경의 광선 시험과 Einstein–Euler를 동시에 만족하는 유한 tilt 해는 각각 표시한다.

## R3 · 광자 에너지, 진행 방향과 스크린

미래지향 p=E(n+e)/c에서 e는 진행방향이고, 법선 관측자의 천구 도래방향은 −e다. II (1.25)–(1.29)의 d ln E/ds=−H−σ:ee, de/ds=g×e에서 g=Ω+a×e+Ne−(tr N)e/2−e×σe. Fermi 삼각대는 Ω=0이다. dO/ds=[g×]O에서 Oeᵢ=e, OᵀO=I, det O=+1이어야 한다. 접선 발산은 3σ:ee+2a·e다. Bianchi I 대각 계량에서는 공변공간운동량 pᵢ 보존으로 E(t)∝√Σᵢ[pᵢ/aᵢ(t)]². 임의 비축 방향의 주파수 및 screen 보존을 이 닫힌 해에 대조한다. BJS VIIₕ 템플릿의 momentum direction→sky 변환 및 방출자·관측자의 Doppler 끝항이 R108에서 따로 확인됐다. R108의 온도 상관은 지정 열린 먼지 VIIₕ 여섯 설정의 결과다. [원 계산](../R108_LOS_ATLAS_DATA_20261124/SOLVER/S4_BJS_COMPARATOR.json)

## R4 · 유한 물질·관측자 boost와 helicity 부호

u=γ(n+β), D=−u·(n+e)=γ(1−β·e)>0, Eᵤ=DE, eᵤ=(n+e)/D−u, dΩᵤ=D⁻²dΩ. screen의 b↦b+(u·b)(n+e)/D는 u와 p에 직교하고 두 벡터의 내적을 보존한다. eᵤ는 u의 rest space에서 표현한 4-벡터다. 공간축 성분은 같은 observer tetrad로 투영한다. 관측자 위치, tetrad, 하늘 기저를 저장한다. 서로 다른 두 boost는 일반적으로 교환하지 않으며, 조합에서는 screen의 회전까지 수송한다. 적색편이 1+z=(−p·u)emit/(−p·u)obs. 길이·편광각은 boost 뒤 역변환, observer별 미소 입체각 변화, 평행/역평행 광자에서 각각 γ(1∓|β|)로 검증한다.

오른손 (u₁,u₂,e)의 pₕ=Q±iU, h=±2. 수동 기저 회전 ψ에서 p′ₕ=e⁻ⁱʰψpₕ. 연결 A=v·∂u, Dₐ⁽ʰ⁾=∂ₐ+ihAₐ이고 수송식 (Dₛ⁽ʰ⁾+RE∂ᴱ+VᴬDᴬ⁽ʰ⁾)pₕ=ih(g·e)pₕ+cₕ. 접선 흐름 V만으로 screen twist를 정할 수 없으므로 g·e 항도 시험한다. 일정각 회전, Q 또는 U만 넣은 해, dyad를 회전한 동일 coherency의 관측자 수축 일치를 비교한다.

## R5 · 전자 정지계의 Thomson 산란과 보존

냉전자·저반동·탄성 Thomson 한계에서 κₑ=nₑ,proper σT는 길이⁻¹. 전파 에너지 모멘트 Fₖ=∫Eᵏ⁻¹F dE에 대해 입사 J에 의한 rest-screen 모멘트 M=∫Dᵢᵏ⁻²JᵢFₖJᵢ†dΩᵢ를 계산한다. 유출 방향에서 손실은 −κₑDₒFₖ, 이득은 (3κₑ/8π)Dₒ¹⁻ᵏJₒ⁻¹SᵤM SᵤJₒ⁻†. k=3은 광자수, k=4는 bolometric energy다. 유한 에너지 빈에서는 식 (1.42)의 F(EₒDₒ/Dᵢ)를 다시 표본화하고 빈 경계 flux를 보존해야 한다. Hermitian 이득 rank≤9는 전 에너지 적분에 대한 명제다.

전자 정지계 등방 비편광 입력은 충돌 영벡터다. 유한 β에서 이 입력을 법선으로 boost한 뒤에도 점별 gain−loss가 소거된다. 반대로 **법선에서 등방**인 에너지밀도 ρ의 복사에는 photon energy와 momentum source가 각각 4κₑργ³β²/3과 4κₑργ³β/3(길이시각)이다. ΔQₑ+ΔQγ=0, u·Qₑ=0, photon-number source=0을 같은 quadrature로 검사한다. γ나 c를 다시 곱하면 이 oracle에서 실패한다. Ray별 e⁻ᵗ 감쇠만 구현한 경우 다른 방향에서의 gain 및 재산란은 검증 범위 밖이다.

## R6 · REC/REI, opacity와 방출 원천

같은 물질 정지계에 있는 H/He에 대해 xₑ=xHII+(nHe/nH)(xHeII+2xHeIII). 상호 배타적 He 분율 합≤1, 모든 분율≥0. 법선 광선에서 양의 dτ=nₑ,proper σT D ds, 물리초에서는 ds=c dt. τ(s,so)=∫s^so κₑD dr, 가시도 g(s)=κₑD exp(−τ), 따라서 ∫g ds=1−exp(−τ(si,so)). nₑ가 영이면 τ=0, 상수 계수에서는 analytic slab가 된다. 미소 tilt에서 β·e 부호, 배우수 γ와 nₑ 중복을 검사한다. 균질 평균 z의 자료를 관측방향별 고정 적색편이로 옮길 때 방출 사건을 먼저 푼다. R108은 5개 z=4 restart와 조건부 z<4 전경의 광학깊이 대역을 시험했다. z<4 이온화 원천·SED·흡수체·UVB가 주어지기 전 donor 일관된 물질사 또는 calibrated EE를 단정할 수 없다. [물질사 경계](../R108_LOS_ATLAS_DATA_20261124/RESULTS_KO.md)

## R7 · 조화 전송, spin과 온도 단위

aₕℓₘ=∫pₕ {}ₕY*ℓₘ dΩ, 표준 Condon–Shortley 및 정규화 ∫|{}ₕY|²=1. II (1.70)의 내부 E=(a₊₂+a₋₂)/2, B=(a₊₂−a₋₂)/(2i)이다. 이 규약에서 p±=Σ(E±iB) {}±₂Y. HEALPix CMB 규약은 통상 Q±iU=−Σ(E±iB) {}±₂Y이므로, **같은 하늘 방향과 같은 oriented dyad에 정렬한 뒤에만** 그 E/B 쌍에 공통 마이너스를 적용한다. 전파방향↔도래방향 및 IAU↔COSMO U 부호는 각각 별도로 기록한다. 두 성분이 모두 0이 아닌 합성 T/E/B 단일모드를 spin 합성·분석해 TE, TB, EB를 signed complex 값으로 대조한다. 패리티에서 T/E의 (−1)ˡ, B의 (−1)ˡ⁺¹도 검사한다. [HEALPix 편광 부호](https://healpix.sourceforge.io/html/intro_HEALPix_conventions.htm) · [NASA LAMBDA의 IAU/COSMO 기저](https://lambda.gsfc.nasa.gov/product/about/pol_convention.html)

기하 커널의 포텐셜은 차수≤2라서 법선의 순간 free generator는 |ℓ−ℓ′|≤2. 이의 유한시간 전파, 각도별 Doppler·gain, 마스크는 더 먼 ℓ도 연결한다. 온도는 occupation, bolometric brightness, thermodynamic ΔT/T 중 선택해야 한다. 방향별 단일 흑체일 때는 I∝T⁴이고 선형에서 ΔT/T=δI/(4I₀)이다. 여러 온도를 산란시킨 spectrum에는 보편적인 정확한 흑체 온도가 없다. 출력은 단위와 모멘트를 명시한다.

## R8 · 무엇을 Cℓm이라고 부를 수 있는가

하나의 물리 이력·orientation·관측자가 낸 full-sky 결정론적 alms tᵡℓₘ에 대해 모드별 복소 곱을 **Dᵡʸℓₘ=tᵡℓₘ tʸ*ℓₘ**로 정의한다. API에서 이를 Cℓm으로 내보낼 때 `deterministic_mode_product` 의미와 µK² 또는 무차원²를 보존한다. 실지도이면 tℓ,−m=(−1)ᵐt*ℓm 및 Dℓ,−m=D*ℓm. 따라서 실수 m-평균은 [Dℓ0+2Σₘ₌₁ˡ Re Dℓm]/(2ℓ+1). 각 m의 Im TE/TB/EB를 제거하면 그 m의 상대위상 정보를 잃는다. 단일 m의 3×3 행렬 t t†는 PSD, rank≤1, |Dᵡʸ|²=DᵡˣDʸʸ이다. 진정한 covariance에는 등호 대신 Cauchy–Schwarz 부등식만 필요하다. proper rotation은 개별 m을 Wigner D로 섞어도 전 m 합을 보존한다. 음영역 parity에서도 TB/EB를 자동으로 0으로 놓지 않는다.

통합 dossier 인쇄면 59–60에서 요구하는 일반 두 점 함수는 모든 (ℓm,ℓ′m′)에 대한 **E[aᵡℓₘ aʸ*ℓ′ₘ′]**다. 평균 μ가 있으면 이 raw second moment는 μμ†+K이고, K=E[(a−μ)(a−μ)†]. 입력이 동일한 결정론적 템플릿만 반복되면 K=0이다. 하나의 템플릿을 모든 orientation에 대해 Haar 평균하는 별도 모형은 회전불변 second moment를 만들 수 있으나 orientation prior가 그 정의의 일부다. 공간 perturbation transfer G와 초기모드 분포 P가 주어지면 centered K=GPG†(선형·고정 배경). 일반 Bianchi에서는 ℓm과 ℓ′m′의 off-diagonal 성분이 살아 있다. 고유모드, gauge/경계, initial covariance, 물질·공간 perturbation이 주어지기 전 균질 solver로 primordial ensemble spectrum을 예측할 수 없다. [통계적 등방성과 BipoSH](https://doi.org/10.1051/0004-6361/201321534)

## R9 · 수치 격자와 외부 comparator

검증 순서는 FLRW 다극 영, I의 비축 Killing 광선, 올바른 손잡이 VIIₕ의 BJS 관측자·방출자 Doppler 끝항을 포함하는 지도, 유한 β에서 독립 정지계 Thomson 적분이다. 그 뒤 각 계열 및 제약 rank마다 시각·광학두께·각 quadrature·source history·ℓmax를 각각 바꾸고 실제 최대 하위모드 오차·절대 바닥·에너지/flux 잔차를 기록한다. R108은 8개 설정에서 저차 native/LoS(ℓ≤4, 신호 하한 10⁻⁶, 768셀) 차이 ≤1.6×10⁻⁴와 높은 ℓ의 비점근적 셀수렴을 기록했다. VIIₕ BJS 온도 비교는 6개 열린 먼지 설정에서 지도 회전·진폭 적합 후 최소 상관 0.99892였고, 손잡이나 E/B 부호 전체를 이것만으로 검증할 수 없다. R108 S5의 LoS−계층 q/E 차 6.26×10⁻⁵는 계층−유체 3.28×10⁻⁶보다 크다. 평균 Cℓ의 수렴만으로 작은 m의 안정성을 선언하지 않는다. [R108 결과](../R108_LOS_ATLAS_DATA_20261124/RESULTS_KO.md) · [near-FRW 편광 위계의 독립 문헌](https://arxiv.org/abs/0706.2075)

## R10 · 관측 연산자와 수용 가능한 해석

장비가 제공한 선형 지도 연산자 L에 대해 템플릿 평균은 Lμ, 독립 영평균 noise N을 포함하는 공분산은 LKL†+N. mask·beam·pixel·광도대·스캔/플래그 및 E/B 혼합은 L의 일부다. 자세·전단 진폭을 데이터로 찾으면 탐색을 포함한 null이 필요하다. R108 S6는 고정된 마스크·beam 및 384개 방향에서 15계수 설계 전달을 3.2×10⁻¹⁵ 수준까지 재현했고, 해당 단계에서 관측 계수를 채점하지 않았다. Commander 30쌍의 순위 해상도는 1/31이다. 유한 정상/물질 tilt에 대한 기하·충돌 모듈, 정해진 source의 k=0 결정론 하늘, 앙상블 K, 계열의 관측 식별은 각자 다른 검증 자료를 요구한다. 코드 영수증에 함께 기록할 항목은 background/IC와 시계, photon propagation↔sky convention, 관측 tetrad와 spin, 단위, ℓ/m 구간, source history 및 해시, 제약·수렴오차, 그리고 제공된 확률법칙이다. [관측 연산자](../R108_LOS_ATLAS_DATA_20261124/SOLVER/S6_B03_TEMPLATES.json) · [Thomson/편광의 운동론적 근거](https://doi.org/10.1016/j.astropartphys.2020.102494)
