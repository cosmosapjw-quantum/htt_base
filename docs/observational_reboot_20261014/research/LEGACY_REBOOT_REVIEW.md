# LEGACY_REBOOT_REVIEW — 역사적 관측 목표와 현재 tensor 통계의 대응
작성: 2026-10-14 / R2–R5,R9 문헌·legacy lane. 이번 lane은 원격 저장소를 변경하지 않는다.

## 자료의 정체와 실제 읽기

project_sources/20-report-1-.pdf에서 추출된 source_reads/legacy_report.txt를 처음부터 끝까지 읽었다(2006행, 36 PDF pages). 표지는 **HTT RESEARCH COMPENDIUM / 수학·물리·통계 종합 이론 보고서 / 2026년 9월13일 한국어 편집판1**이며 “기존 문서·구현·증명 근거의 종합. 새로운 연구 계산이나 증명 판정은 수행하지 않음”이라고 명시한다. 목차 i–ii 뒤 printed pp1–33이므로 printed p는 PDF page p+3이다. 이 파일은 폐기 전 Planck SMICA 관측 p 계산 원본이 아니며 최신 유지 이론과 관측 적격성의 종합판이다. 따라서 ‘옛 분석’의 증거는 별도 generated output·score/null manifest·source 코드에서 찾아야 한다.

직접 선택 조사한 기존 출력:
- HTT_OBSERVATIONAL_UPGRADE_R2_20261013/sources/HTT/HTT/outputs/ppc_results.json 및 data/obs_defaults.json 전체 읽음.
- 같은 archive README, code_data_audit_report·original mathematical/overall audit의 관련 검색 구간.
- project_sources/14-bianchireview87.tar-1-.gz 목록과 report/vals.json, report/coverage.json, AUDIT-REPORT-v1.3.md 선택 구간. solver numerics의 residual 자료이며 SMICA p source로 채택하지 않음.
- project_sources/18-literatures.zip,19-papers.zip,11-lowell_bianchi_codex_automation_kit.zip 및 10-bianchirustcoreRDAGcomplete.tar.gz는 파일 목록을 조사했다. 모든 책/PDF/코드를 읽었다고 주장하지 않는다.
- 붙은 01-Low-ell-Bianchi-Einstein-Boltzmann-Solver.txt의 audit contract와 04-Adaptive-CMB-Code-Development-Protocol.txt의 relevant physical/code/observable contract를 읽었다. prompt 문서에 나오는 대형 audit 역할 배치는 현재 lane의 실행 receipt가 아니다.
- 실제 SciSpace semantic search 1회(10 results), Exa 검색 7회(각 numResults=5; 35 requested result slots), Exa fetch 4 batch를 수행했다. primary source 9개를 선정; full fetch 반환과 선택 formula/section reading scope는 PRIMARY_SOURCES.json에 있다. random incorrect arXiv 1706.03775는 hydrodynamic paper라 제외했다. 해당 잘못된 URL은 raw trace에 보존하고 아무 scientific support에도 쓰지 않는다.

## 과거 숫자와 현재 숫자의 provenance

| 대상 | 실제 기록 / 출처 | 통계 의미 | reboot에서의 판정 |
|---|---|---|---|
| historical K1 global maxscan | 부모 source-audit lane이 docs/generated/k1_global_maxscan_e2e_full.json와 v11 report에서 p=.039 확보 | cyclic noise reuse를 가진 conditional empirical rank + cluster-bootstrap calibration; 이 lane은 remote 원문을 독립 재독하지 않음 | 역사적 p row 유지; parent source evidence와 연결. iid sky rank theorem 또는 Bianchi 발견으로 승격하지 않음 |
| archive FLRW_tilt PPC | outputs/ppc_results.json, 2026-03-14, n_ppc=1000: T_b=.012,T_c=.613,T_e=.163,T_h=.905,T_all=.078 | posterior predictive per-channel discrepancy; CMB e/h는 D2/D3 scalar likelihood | 유지하되 SMICA map rank p와 구별. 새 fullsky test의 숫자로 재사용하지 않음 |
| archive BI_tilt PPC | 같은 JSON: T_b=.013,T_c=.607,T_e=.161,T_h=.905,T_all=.079 | 같은 posterior-predictive 설계 | 같은 처리 |
| R8 합성 pool | PDF printed p18,§20; p25,§26: 30 pools, 5 비기각·25 미해결·0기각 | 고정 합성 거리 score의 certified rank enclosure | 구현 근거로 유지. 관측 Planck p 아님 |
| 네 Planck component의 Q/O full-MV | pp7,25,27–28: observation component4/4 reconstruction | 표현 복원, 동일 tensor 보존 | morphology extraction 근거. physical/noise null 적격성 근거는 별도 |
| DESI qiso 95% | p25: [0.9462387032,1.0195221801] | released Gaussian conditional scalar summary | 정해진 법칙의 스칼라 구간. angular Bianchi template 또는 local/global dipole 식별 아님 |
| archive D2/D3 | obs_defaults.json: 225.9,936.9 μK², COM_PowerSpect_CMB-TT-full_R3_01; eps2/3 항목은 Commander | power-spectrum summary provenance | 실제 SMICA map에서 같은 mask/beam/estimator로 재추출해야 하는 입력 |
| archive epsilon | eps2=3.559629e-6,eps3=6.065291e-6 | archive normalization 정의로 보존 | 아래 STF norm normalizer와 값이 달라 같은 epsilon로 자동 통합하지 않음 |

PPC 파일 summary는 matter-dipole 내부 tension을 “data-driven not model failure”로 해석한다. 이번 reboot는 그것을 사실 판정으로 승계하지 않는다. 모델이 두 catalogue 관측을 하나의 β로 동시에 설명하지 못하는 것은 관측·systematic·모형 mapping 중 어느 전제가 불충분한지 따져야 하는 discrepancy다.

관측 p=.039의 raw count, N, exact tail, score version과 bootstrap interval은 parent source-audit receipt가 소유한다. 이 lane은 figure 높이·색상·caption으로 missing p 또는 interval을 추론하지 않았다.

## D_l/C_l와 STF normalizer의 직접 재계산

\[
D_\ell=\frac{\ell(\ell+1)}{2\pi}C_\ell,\quad
\|c_\ell\|^2=(2\ell+1)C_\ell.
\]
온도 \(T_2=Q_{ab}n^an^b,\ T_3=O_{abc}n^an^bn^c\)에서 구면 isotropic moment의 STF contraction을 이용하면
\[
\int T_2^2d\Omega=\frac{8\pi}{15}Q:Q=5C_2,\quad
\int T_3^2d\Omega=\frac{8\pi}{35}O:O=7C_3.
\]
즉 \(Q:Q=75C_2/(8\pi)=75D_2/12\), \(O:O=245C_3/(8\pi)=245D_3/48\).
archive 숫자를 이 식으로 변환한 실제 실행 결과는 C2=236.5619268,C3=490.5596929 μK², Q:Q=1411.875,O:O=4782.09375 μK²다. \(T_0=2.7255\times10^6\,\mu K\)에 tensor norm ratio는 eps2=1.3786434e-5,eps3=2.5372476e-5다. 이 숫자는 **archive D_l에 현재 tensor convention을 적용한 단위·normalization 진단**이며 새 관측 extraction이 아니다. obs_defaults epsilon와 다르다는 것은 명확하므로 원래 epsilon 정의/근거를 연결한 뒤 재사용 여부를 판단한다.

추가 coefficient 충돌: archive MES_bounds.B_omega_coeffs=[.75,2,.2857]인데 PDF §6 source-matched branch는 \(B_\omega=(10/3)\epsilon_1+(2/15)\epsilon_2\). \(B_\sigma\)는 archive roundoff coeff [1.6667,3,.4286]와 exact [5/3,3,3/7]를 구별한다. 전제/정의가 다른 식을 같은 MES law로 채택하지 않는다. parent DAG에는 source normalization adapter와 golden conversion row가 필요하다.

## 페이지·절별 claim 처리표

‘유지’는 원문 진술의 정확한 범위를 재사용한다는 뜻이다. ‘교체’는 원문의 부주의한 이름을 바꾸거나 archive의 과잉 해석을 새 분석 계약으로 바꾼다는 뜻이다. ‘재계산’은 실제 새 product/null/provider로 다시 계산할 항목이며 이미 실행했다는 뜻이 아니다.

| printed page·section | 보존되는 claim | 판정·구체적 변경 |
|---|---|---|
| p1–2 §1 | source pins efc5f306,6bafca66,04680e99,9b725899는 다른 분기 | 유지; HEAD와 donor의 content/scientific equivalence를 parent audit에 연결 |
| p2–3 §2 | Q/O는 temperature, σ/ω/A는 지정 congruence의 kinematics | 유지; \(Y=M\mathcal T[X]+N\nu+\epsilon\)로 실제 역문제 작성 |
| p3 §3 | signed Gauss budget 및 frame dependence | 유지; scalar curvature와 anisotropic curvature tensor 분리, c restoring adapter |
| p4 §4 | flux cancellation은 stress cancellation 아님; PSD moment | 유지; bounded multi-stream benchmark로 사용 |
| p4–5 §5 | damping 기억·source floor, entropy/visibility·all-observer EGS 조건 | 유지; 한 하늘 C2만으로 all-observer premise를 채우지 않음 |
| p5–6 §6 | source-bound MES coefficients·Θ=3H normalization | 전제별 유지; archive ε와 Bω 계수는 source-match 뒤 재계산 |
| p6–7 §7 | polar/axial parity, invariant/representation dimensions | 유지; finite dimension→finite tests/자동 optimality는 채택하지 않는 원문 판정 유지 |
| p7–8 §8 | real harmonic/STF 등가와 full-MV carrier | 유지; SMICA matched extraction + joint covariance 재계산 |
| p8–10 §9 | cyclic-domain decoder, 한 common rotation의 orbit distance | 유지; full domain completeness 대신 singular strata 명시. 외부 축 질문엔 absolute orientation 보존 |
| p10 §10 | 양의 절대 T의 inverse-square closure 및 Gaussian reciprocal divergence | 유지; 잔차 Q/O에 absolute-temperature reconstruction 이식하지 않음 |
| p10–11 §11 | electron vs normal frame, all-m anisotropic propagator | 유지; Doppler source의 dimension 불일치는 해결 의무. 새 native atlas 전엔 conditional transfer |
| p11–12 §12 | endpoint boost generator와 \(B_Q^*B_Q\), processed quotient | 유지·직접 재유도; finite pixel/mask response rank는 별도 재계산 |
| p12–13 §13 | radial skew blindness, depth response 모형 | 유지·toy example 실행; 실제 W_j와 global history·joint covariance로 재계산 |
| p13 §13.2 | omitted cross covariance가 일반 law와 다름 | 기존 sum-only covariance를 full block 잔차 공식으로 교체해야 함; overlap=independence 아님 |
| p14 §14 | 특정 LRS의 linear curvature slaving | 제한 branch 유지; 모든 Bianchi curvature 식별로 확대하지 않음 |
| p14–15 §15 | 반대 dust stream의 even-T restricted Bianchi-I | 유지·first-order quadrupole history 연결 유도; native cosmological likelihood 아님 |
| p15–16 §16 | common-state feasible set, 부분 식별/empty/unbounded | 유지; 같은 sky MES와 likelihood를 독립 데이터처럼 곱하지 않음 |
| p16 §17 | shared positive denominator의 fractional interval | 유지; nonlinear Pi에 box-vertex rule 복제하지 않음 |
| p16–17 §18 | singular Gaussian support test와 pointwise inversion | 유지; 추정 covariance와 source adequacy는 별도 법칙. ridge는 다른 모델 |
| p17–18 §19 | Hotelling/Hartlap scope, conditional information | 유지; fitted residual freedom/χ² tail을 임의 지정하지 않음 |
| p18 §20 | full-score exchangeability의 p와 enclosure | 유지; whole-sky bundle·selection/fit equivariance·fixed N로 새 p 재계산 |
| p19 §21.1–2 | paired covariance·deterministic compression·body geometry | 유지; old scalar x를 full carrier/control diagnostic으로 교체 |
| p19 §21.3 | dependent e-value average vs conditional-valid product | 유지; independent p 곱 또는 arbitrary depth e-process는 만들지 않음 |
| p20 §22 | registered error envelope와 source-conditional jet support | 유지; 실제 관측 derivative law·remainder 없는 jet를 measured σ로 출력하지 않음 |
| p21–23 §23 | x,Q,F,Pi,G_F→functional/gauge/support/exceedance/depth | 유지; Pi는 p가 아니고 F는 물질 체적 점유율이 아님. fullsky paired draws로 재계산 |
| p23 §24 | response·covariance에 따라 추가 채널 정보 증가 | 유지; polarization/kSZ는 optical-depth/model·mask rank를 실제 구해야 함 |
| p24–25 §25 | 345 source proof records와 physics discoveries 구별 | 유지; novelty claim 없음, proving catalogue를 data identification으로 재분류하지 않음 |
| p25–26 §26 | R8 제한 결과와 held/STOP_INVALID | 유지; 64/1000 rejection cell을 nominal validity PASS로 만들지 않음 |
| p26–27 §27 | geometry→transfer→uncertainty→law 연결 | 새 reboot DAG의 세 실제 경로: morphology p / local-global / conditional-family |
| p27–28 §28 | data used vs interpreted vs conditional distinction | 유지; CF4+QO를 붙이는 것만으로 joint law나 family 식별을 선언하지 않음 |
| p28–33 bibliography/maps | 외부 6 source는 bibliographic/abstract 확인 범위 | 새 actual primary selected-section read를 PS01–PS09로 연결; source list만으로 신규성 인증하지 않음 |

## reboot로 바뀌는 과학적 질문

첫 질문은 **등록된 관측 처리·공유 sky null 아래 SMICA의 유지된 tensor morphology가 얼마나 드문가**다. 이는 isotropic null 적합성 질문이며 local/global 또는 Bianchi의 우열을 직접 답하지 않는다. 과거 p를 발견했어도 statistic·mask·source law 변경에 따라 새 p는 재계산해야 한다.

둘째는 **endpoint β와 등록된 global-tilt history가 같은 processed feature 공간에서 nuisance 이후 서로 다른 image를 가지는가**다. 단일 local response를 두 block에 복제하면 분리되지 않지만 실제 depth-weighted response 차이는 분리를 만들 수 있다. 반응 모형과 covariance·error gap을 채운 뒤 conditional power와 신뢰집합을 계산한다. THEORY_REBOOT.md가 이 map과 두 shell rank 예를 유도한다.

셋째는 **어느 Bianchi family의 harmonic/covariance prediction이 실제 관측에 구별되는가**다. native atlas가 incomplete인 현재 상태에서도 transfer-conditional map·toy rank·injection recovery를 실행할 수 있다. family discovery 또는 full source equivalence 판정에는 native geometry/matter/collision/IC/hierarchy error 근거가 필요하다. source_audit·solver lane 결과를 교차 연결하고 closed/unavailable family를 FLRW로 조용히 대체하지 않는다.

## 반환한 객관적 결과와 남은 한 번의 실행

객관적 결과는 PDF provenance 판별, archive PPC 및 D_l normalization 수치 대조, primary selected-source 근거, endpoint boost/STF/quotient/local-global/dependent-law/conditional-Bianchi의 실제 유도와 합성 계산이다. DERIVATION_CHECKS.json와 derivation_checks.py는 실제 실행했다. 관측 새 p, native family atlas, fullsolver fit은 이 lane에서 NOT_COMPUTED/NOT_EXECUTED다.

다음 실행은 parent가 보존한 K1 score/null/p=.039 manifest와 새 fixed-B utility를 바탕으로 historical replay와 upgraded independent-sky/full-pipeline calibration을 분리하는 것이다. 결과는 p 종류, 조건, MC 해상도, actual/exploratory/eligible 상태를 그대로 표시한다. archive 논문의 source placeholder나 SMICA residual을 물리 dipole로 바꾸지 않고, 입력 의무가 열린 곳에서도 등록된 조건부 탐색은 계속한다.

