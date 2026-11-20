# R80 · SQ-CF4 복구된 원본 자료의 source lineage 및 mask morphology

실행일: 2026-11-20 KST. 입력 정본: R78 통합 DAG revision 3, NEXT_ID=SQ-CF4; 실제 CF4 CDS J/ApJ/944/94 table3/table4 및 R54/R58 선택 35,970-group 소스와 R36 원래 36×35,970 선형 연산자. 이 작업은 복구된 원본 자료로 source-group identity와 한정된 mask physics를 직접 검산한 작업이며, 전체 SQ-CF4 과학적 수용 조건의 완료나 새 cosmological likelihood가 아니다. 계산 코드는 scripts/r80/audit_cf4_source_lineage.py, machine-readable 결과는 RESULT.json.

## 1. 정본 원본 identity와 관측값 parity

원본 5개 SHA256을 직접 검산했다.
- table3.dat: c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d.
- table4.dat: b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94.
- ReadMe: 2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4.
- selected_source_observables.npz: 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c.
- A_RAW_36x35970.npz: e835df014bf0eb96fd715994c823eec9c8449f98d3f132b1dc736b760fd2772e.

table3와 table4의 고유 1PGC ID는 각각 38,053개이고, R54/R58 선택 표본 35,970개 모두 원본 내 고유 ID로 일대일 조인된다. 원래 R36 36×35,970 operator의 group ID와 순서도 정확히 일치한다. 선택 제외 2,083개. 선택 source 행의 DMzp와 e_DMzp 원본 값에 대한 최대 절댓값 차이는 각각 0이다. \(z_{\rm CMB}=V_{3k}/c\) (c=299792.458 km/s)도 1e-12 이내이며, J2000 원본 방향과 선택 텐서의 방향 벡터는 정확히 동일했다. 이전의 dot/arccos 방식에서 보고한 약 0.006초각은 acos(1)의 수치 반올림 효과였으며 stable chord-distance 공식으로 계산하면 0이다.

## 2. Method presence는 선택된 단일 method-family label이 아니다

기존 R54/R58의 categorical method_family는 FP 26,916, TF 7,614, SN 700, OTHER 740개이며, 원본 table3의 일곱 방법 존재 표시 CAL,SNIA,FP,TF,SBFO,SBFI,SNII와는 의미와 차원이 다르다. 선택 표본 중 모든 table3 method presence 표시가 zero인 그룹 **185개가 전부 OTHER**로 분류되어 있으며, 2개 이상의 method presence가 positive인 그룹도 926개다. 이 결과는 historical source-family assigner와 method별 zero-point/cross covariance를 별도로 읽어야 한다는 증거이지, 해당 185개에 물리적 거리 정보가 없거나 자료가 손상됐다는 주장과 다르다.

## 3. 실제 source mask에 의한 even-shear → odd-hemisphere mixing

CMB dipole Galactic (l,b)=(264.021°,48.253°)를 ICRS/J2000로 변환하여 두 normalized hemisphere의 1·2차 방향 모멘트 \(m_\pm,M_\pm\)를 계산했다. 한 물리적 source congruence의 local \(h(n)=1+d\cdot n+n\Sigma n\) 아래
\[
\Delta\bar h=d\cdot(m_+-m_-)+\Sigma:(M_+-M_-)_{\rm STF}.
\]
Type V total normal j=0, \(\Sigma a=0\), \(\Sigma\) eigenvalues (-s,0,+s)인 조건부 구조에서 방향별 sharp maximum은
\[
\max_{SO(3)}|\Sigma:\Delta M|=s[\lambda_{\max}(\Delta M)-\lambda_{\min}(\Delta M)].
\]
여기서 **s=0.03은 명시적으로 합성 텐서 진폭**이며 CF4에서 shear를 관측했다는 뜻이 아니다.

| 입력 source sky (40–400 Mpc) | group count | Dipole-axis (+/−) counts | s=0.03 sharp leakage |
|---|---:|---:|---:|
| 원래 table4 전체 | 31,649 | 25,035 / 6,614 | 0.01001237065 |
| R54/R58 선택 그룹 | **31,382** | 24,868 / 6,514 | **0.01005736760** |
| 선택 FP | 22,629 | 20,221 / 2,408 | 0.00628535903 |
| 선택 TF | 7,356 | 3,851 / 3,505 | 0.01243797594 |
| 선택 SN | 682 | 327 / 355 | 0.00978147009 |
| 선택 OTHER | 715 | 469 / 246 | 0.00551558927 |

전체 raw group과 실제 selected group의 mask response는 +0.4494% 다르다. 방법별 maximum은 서로 다른 STF 고유축 방향에 대한 것이므로 서로 하나의 tensor로 동시에 포화시킬 수 없다. 결과에는 원본 선택 전체 35,970에 대한 footprint와 group_id mod 5 deterministic geometry partitions도 기록했지만, 이것들은 독립 우주론적 null이나 observational heldout test가 아니다. Actual native Fortran/NumPy 1·2차 source 모멘트 대조는 1e-12 이내로 일치했고, 작은 분할은 명시적 기준 NumPy fallback이었다.

## 4. 검증과 남은 과학적 blocker

**Source-identity PASS:** 복구된 원본 hash, table3/table4 join, R36/R54/R58 35,970 동일 group ID·순서, DMzp·오차, z_CMB, ICRS 방향. **Finite geometry PASS:** 선별·원본 하늘 mask 차이, method별 sharp 누출, native/NumPy parity, 원본 해시 재검산. 결과는 코드와 함께 reproducible source status.

**미해결:** R61의 선택 group method/zero-point nuisance, 실제 \(S_{\rm PV}\)와 \(J_{\rm cal}\Sigma_{\rm cal}J_{\rm cal}^{\top}\), 선택함수 covariance, full sample-level likelihood 및 heldout calibration/coverage. 원래 32D/36D covariance를 35,970개 그룹의 full source-level sufficient likelihood로 임의 승격하지 않는다. 물리적인 normal \(\sigma\), 실제 H(z,n), Bianchi type 식별이나 Pi 등은 이번 결과로 추정되지 않는다.

R78 원래 42개 science gate 및 60-node integrated DAG 상태는 변경하지 않았다. NEXT_ID=SQ-CF4가 유지되며, 다음 bounded slice는 정확한 35,970 선택 group의 방법별 observation genealogy/zero-point and correlated PV/selection covariance를 원 소스로 검증하는 작업이다.
