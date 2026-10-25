# 불완전 거리 표본의 유한 표적 잔차 부분식별과 공분산 가정 민감도

2026-10-24 · 저자 `/root/r26_p1_estimand_final_synthesis` · owner `htt` · C0 경험적 조건부 방법론 결과.

**판정: `FINISH_SEPARATE_METHODS_RESULT`.** 기존 실제 628/274 자료로 아래 결과를 완결한다. 이것을 원래 P1의 같은 물리적 함수에 대한 좁은 측정으로 인정할 근거는 없다. **S04의 법칙 자격은 HOLD**다. 다만 원래 S02의 조건부 유한 공동 표본 및 S03의 선언된 민감도라는 좁은 수락 문구는 기존 H03 결과로 뒷받침된다. S04의 물리적 map 의무를 S02/S03에 소급하여 추가하지 않는다. S02/S03 전체 scoped acceptance의 독립 판정은 아래 정확한 문구와 근거로 별도 검토자가 내릴 수 있으며, 현재 canonical 상태나 완료 수를 이 저자가 바꾸지 않는다. S05–S06 준비도는 미승격이다. 저자 종합은 완료되었으며 이 문서에 대한 별도 표적 독립 검토는 아직 수행되지 않았다. 이는 제출 또는 출판 승인서가 아니다.

## 원고에 사용할 수 있는 결과 문장

628개로 고정된 거리 관측 표적 중 공개된 274개 결과를 이용하여, 같은 행과 그룹 단위 분할에 정의된 예측 잔차의 유한 표적 분포를 분석하였다. 임계값 (t=0.5\,\mathrm{mag})에서 절대 잔차 초과 사건은 사전에 보존된 12개 모형·공분산 경우에서 71–80개였다. 나머지 354개 사건 결과에 제한을 두지 않으면, 균등 유한 표적 비율의 달성 가능한 양 끝점 사이 폭은 모든 경우에 정확히 (354/628=0.5636942675159236)이다. 관측 부분에 정규화된 밀도비 민감도 (\Gamma=2)를 허용하면 기존 결과의 폭은 0.733280–0.754777로 넓어진다. 이 구간은 명시된 유한 표적·누락 사건 모형의 끝점 범위이며, 물리적 이방성의 posterior 또는 신뢰구간이 아니다.

동일한 274개 행의 공동 held-out 예측 점수에서, 그룹 상관 항을 두지 않은 두 경우에는 광학 STF 모형 B가 응답 가중 벡터 모형 A보다 높았지만, 선언된 그룹 공분산 척도 (b=0.29\,\mathrm{mag})를 사용한 두 경우에는 A가 더 높았다. 따라서 이 자료에서 A/B의 순위는 관측으로 검증되지 않은 공분산 선택에 민감하다. 여덟 B/C 적합의 전체 계수 공분산을 투영한 광학 STF 기준 타원체는 모두 영 텐서를 포함하였다. 영이 아닌 점추정치만으로 양의 shear 하한을 주장할 수 없다. 이 두 결론은 실제 저장된 행·텐서·공분산에 관한 조건부 결과이며, 일반적인 물리 null의 참이나 등방성 검출을 뜻하지 않는다.

## 1. 원래 P1과의 동일성 판정

원래 `PUBLICATION_DAG.json`의 P1 질문은 실제 공동 관측법칙에 조건화한 signed (x_C,Q,F,\Pi(t),G_F)의 posterior/identified set이다. S04는 완전한 (x_C) 대신 **qualified narrower identifiable functional**을 허용한다. 따라서 모든 물리 sector를 반드시 측정해야 하는 것은 아니다. 그러나 이 허용이 임의의 mag 잔차 사건을 같은 함수로 바꾸지는 않는다.

| 원래 의무 | 현재 자료가 제공하는 것 | 남는 정확한 차이 |
|---|---|---|
| S01: signed x, Q source anchor, sign-clean samplewise F, strict Pi와 unknown mass, fixed floor/depth G_F | 원래 정의·경계와 공동 ID 보존 계약 | 이 계약은 재사용한다. 물리적 함수의 관측값을 새로 공급하지 않는다. |
| S02: one joint source, exact normalized weights; unknown posterior mass 미재정규화 | H03의 공동 2048 working-law 표본, 동일 source와 원래 1/2048 가중치, 물리 unknown mass 1 | 이 좁은 수치 수락 문구에는 기존 긍정 근거가 있다. physical posterior를 새로 측정하지 않아도 unknown을 보존한 조건부 유한 pushforward를 보고할 수 있다. 274행의 다른 source로 이 근거를 대체하지 않는다. |
| S03: denominator/selection 변화의 비자명한 효과, zero/missing 구별 | 같은 H03 source의 actual north fit, anchor/floor/depth 및 normalized selection 민감도 | 이 좁은 수치 수락 문구에도 기존 긍정 근거가 있다. apparent anchor의 민감도를 보고하는 것과 이를 physical Q라고 인정하는 것은 별도다. 명시적 독립 검토 없이 기존 pending을 자동 승격하지 않는다. |
| S04: actual selected likelihood 또는 justified outer interval; qualified narrower functional 허용 | 실제 관측 잔차의 유한 표적 outer hull, 조건부 Gaussian 모형 비교 | 잔차 사건의 outer hull 자체는 정당화되지만 원래 물리적 함수와의 source·unit·domain 대응이 없다. 광학 STF도 아직 선택 창의 선형 시나리오이고 calibrated physical event가 아니다. |

이것은 **628/274 잔차 결과**의 동일성을 부정하는 한 번의 판정이며, 기존 **2048 공동 H03 결과**의 좁은 계산 수락을 부정하는 판정이 아니다. 모든 미래의 좁은 물리적 함수 측정이 불가능하다는 정리도 아니다. 근거: [DAG]와 [S01-THEORY], [S01-CODE], [H03-SENSITIVITY], [H03-RESULT], [DISTANCE], [OPTICAL].

독립 검토자가 사용할 정확한 원래 문구와 dependency는 다음과 같다.

- **S02**, dependencies **S01, E2**. Objective: `Run actual-data conditional finite draw pushforward, retaining unknown physical sectors`. Acceptance: `One joint source, exact normalized weights; posterior unknown mass not silently renormalized`. Output: `paired functional arrays + Pi interval plots`. Tests: `strict tail and interval end cases`, `same sky never treated as nine draws`.
- **S03**, dependencies **S02, X01**. Objective: `Evaluate nontrivial anchor/floor, depth and selection sensitivity`. Acceptance: `Outputs change on declared denominator/selection, zero/missing distinct`. Output: `source-coupled statistical invariants and counterexample figure`. Test: `floor G_F and signed-quotient boundary adversarial injections`.

S02 근거는 [H03-RESULT]의 `sample_count=2048`, `joint_unit=one coupled four-window 36-vector`, `weight=0.00048828125`, `weight_sum=1`, full 36×36 공동 covariance, `physical_functionals.unknown_mass=1`, strict-tail interval 끝점 및 original sample-ID 보존을 명시한 [H03-SENSITIVITY]의 12개 통과 테스트와 paired array/figure 경로다. 이것은 실제 35,970-group 충분통계에 조건화한 deterministic Sobol finite measure이며 새로운 posterior 또는 raw-data refit이 아니다.

S03 근거는 같은 source의 실제 north-weighted 변화 \((-3.966,+8.918,+0.395,-16.834)\%\), \(g(B,\delta)=\max(A_j,B\delta)/\max(A_0,B\delta)\)의 product identity, effective floor .005에서 .05로 바꿀 때 .06/.025 median이 1.718693에서 1.025396으로 바뀌는 저장값, selection \(\Gamma=1\)에서 \(\Gamma=2\)로 바꿀 때 joint-event point .60302734375가 [.301513671875,.801513671875]로 넓어지는 저장값, zero·strict tie·missing 구별 테스트다. 감도 grid는 retrospective라고 표시되어 있으며 detection preregistration을 주장하지 않는다.

**판정 층위:** (i) 위 원래 수치 문구는 기존 결과에서 충족 근거가 있다. (ii) 원래 전체 scoped node의 output/test/dependency까지 충족되었다는 최종 판정은 별도 독립 검토가 그 정확한 범위를 확인해야 한다. 이 저자는 여기서 paired NPZ나 옛 테스트를 재실행·독립 검증하지 않았으므로 기존 보고된 12 PASS를 새로운 PASS로 바꾸지 않는다. 현재 읽은 자료에서는 S02/S03의 위 수치 문구에 실패한 구체적인 원래 clause를 찾지 못했다. (iii) 그러한 scoped 완료가 인정되더라도 S04의 물리 law 자격, 원래 P1의 physical inference 또는 제출 준비도는 승격되지 않는다. 오래된 `next_action`이나 보고서의 physical-HOLD 문장을 원래 acceptance에 없는 추가 AND로 사용하지 않는다. 이 구분은 추가 과학 실행을 요청하지 않으며 이번 한 번의 표적 검토에 포함된다.

## 2. 유한 누락 사건 정리와 증명

**정리 — 고정된 628 표적의 잔차 사건 끝점.** 일반적으로 (N=n+M), (0<n\le N)인 고정 표적 집합을 둔다. 관측 집합 (O)의 크기는 (n), 미관측 집합 (U)의 크기는 (M)이다. 하나의 고정된 모형·공분산 경우에서, 저장된 관측 잔차 (r_i\,[\mathrm{mag}])와 (t\ge0\,[\mathrm{mag}])에 대해 (b_i=1\{|r_i|>t\}), (m=\sum_{i\in O}b_i), (e=m/n)라 둔다. 적합과 관측 잔차는 고정하고, 미관측 사건은 각기 0 또는 1로 제한 없이 완성할 수 있다고 가정한다. 미관측 표적에서 예측기가 정의되었다는 주장을 하지 않는다. 이들은 실제 미측정 잔차에 대한 추론이 아니라 제한 없는 사건 확장의 변수다.

균등 유한 표적 비율 (\theta_N=(m+\sum_{i\in U}b_i)/N)의 정확한 달성 집합은

\[
\mathcal I_1=\{(m+k)/N:k=0,\ldots,M\}.
\]

따라서 그 최소 포함 구간은 ([m/N,(m+M)/N]), 폭은 (M/N)이며 양 끝점은 달성된다. 이산 표적 비율에서 구간 안의 모든 실수가 달성된다고 주장하지 않는다.

이제 관측 부분에만 (p_i=1/n), (q_i=w_i/n), (1/\Gamma\le w_i\le\Gamma), (\sum q_i=1), (1\le\Gamma<\infty)를 적용한다. 관측 부분의 총 표적 질량 (n/N)은 고정하며, 미관측 표적은 각각 (1/N)을 유지한다. 이것은 **관측 부분 내부의 선언된 민감도 모형**이고, 전체 628개에 밀도비를 다시 부여하거나 관측 확률을 추정하는 모형이 아니다. 그러면 (q(E)=\sum_{i\in O}q_i b_i)의 정확한 범위는

\[
L_\Gamma(e)=\max\{e/\Gamma,1-\Gamma(1-e)\},\quad
U_\Gamma(e)=\min\{\Gamma e,1-(1-e)/\Gamma\}.
\]

완성된 민감도 함수 (\theta_{N,\Gamma}= (n/N)q(E)+N^{-1}\sum_{U}b_i)의 정확한 집합과 최소 포함 구간은 각각

\[
\mathcal I_\Gamma=\bigcup_{k=0}^{M}
\left[\frac nN L_\Gamma(e)+\frac kN,\frac nN U_\Gamma(e)+\frac kN\right],
\quad
\operatorname{hull}(\mathcal I_\Gamma)=
\left[\frac nN L_\Gamma(e),\frac nN U_\Gamma(e)+\frac MN\right].
\]

**증명.** 관측 사건 질량 (z=q(E))에는 사건 자체의 밀도비 제약 (e/\Gamma\le z\le\Gamma e)와 여사건의 정규화 제약 (1-\Gamma(1-e)\le z\le1-(1-e)/\Gamma)가 동시에 적용된다. (0<e<1)이면 사건 행 모두에 (w=z/e), 여사건 행 모두에 (w=(1-z)/(1-e))를 주어 그 교집합의 모든 (z)를 달성한다. (e=0,1)은 각각 (z=0,1)로 고정된다. 미관측 사건의 합은 정수 (k=0,\ldots,M)를 모두 취할 수 있으므로 위 합집합과 그 hull을 얻는다. 최솟값은 (z=L,k=0), 최댓값은 (z=U,k=M)에서 달성된다. 따라서 hull 폭은 (M/N+(n/N)(U-L)\ge M/N)이다. (\Gamma=1)에서는 (L=U=e)이므로 첫 식을 회복한다. □

실제 적용은 (N=628,n=274,M=354)이다. \(354/628\)은 **경험적 사건 누락 질량**이고 물리적 함수의 unknown mass 1을 대신하지 않는다. (0<e<1)에서만 (\Gamma\to\infty)의 hull이 ([0,1])로 간다. (e=0) 또는 (1)이면 각각 ([0,M/N]), ([n/N,1])이 남는다. 여러 임계값을 동시에 사용할 때 같은 잔차의 초과 사건은 단조 결합되어야 하며, 점별 hull들의 직적을 독립 정보로 사용하지 않는다.

**잔차 평균에 대한 별도 귀결.** 미관측 signed 잔차를 제한 없이 실수 (R)로 완성하는 수학적 모형에서는 전체 평균에 ((M/N)R)가 남으므로 상·하로 무계다. 이것은 잔차 평균의 결과다. 물리적 (x_C)에 대한 무계성이나 물리적 완성의 존재를 증명하지 않는다. 이 정리는 기존 [S01-THEORY], [H03-SENSITIVITY], [SELECTION]의 초등 유한 질량 논증을 현재 estimand에 명시한 것이며, 새로운 이론적 novelty 또는 CAS 4축 통과를 주장하지 않는다.

## 3. 실제 자료에서 남는 세 가지 결론

첫째, [SELECTION]에서 (t=.5\,\mathrm{mag},\Gamma=1)일 때 A/(a=0,b=0)의 정확한 hull은 ([71/628,425/628]), 즉 저장값 ([0.11305732484076435,0.6767515923566879])이다. 다른 11개 경우도 같은 폭을 갖는다. 모든 12개 경우를 보존하므로 가장 유리한 모형만 선택한 결과가 아니다. 이 폭의 끝점 달성은 위의 제한 없는 사건 완성에 상대적인 것이며, actual source 선택법칙·평균적 표본 coverage·5,460개 모집단의 분포는 추정하지 않는다.

둘째, [DISTANCE]의 동일한 다섯 complete-group fold, 총 274행의 저장된 공동 log score는 다음과 같다. 표의 반올림 전 값과 전체 계수·공분산은 RESULT.json에 연결했다. 큰 값이 해당 시나리오 안에서 더 높다.

| (a,b\,[\mathrm{mag}]) | A: angular calibration + response vector | B: angular calibration + STF | C: union |
|---|---:|---:|---:|
| 0, 0 | −220.320018 | −196.843320 | −518.193732 |
| 0, .29 | −194.273316 | −195.138036 | −209.534052 |
| .055, 0 | −231.854820 | −198.339595 | −651.993130 |
| .055, .29 | −193.723069 | −194.545441 | −209.464523 |

여기서 (V(a,b)=\operatorname{diag}(s_i^2-a^2)+a^2\mathbf1\mathbf1^T+b^2GG^T)이고 (G)는 저장된 그룹 소속 행렬이다. (a,b)는 관측으로 분해된 calibration/PV 성분이 아니다. 예측법칙은 training ML scale을 사용하는 정규화된 block-conditional Gaussian plug-in law이며 계수·scale 불확실성을 적분하지 않는다. 모형 A의 (K=-5/[\ln(10)V_{\rm cmb}])는 mag/(km/s)이고, 해당 벡터 계수는 km/s이다. (V_{\rm cmb}=317\,\mathrm{km/s})인 PGC9031의 저속 근사 한계가 보존되며, 사후에 그 행을 버리지 않는다. 순위 역전은 이 고정 비교의 실제 결과이며, 검증된 physical law 사이의 Bayes factor 또는 보편적 B 배제는 아니다.

셋째, [OPTICAL]은 모든 nuisance와 cross block을 포함한 (p=12) 또는 (15)차원 기준 영역 ((\beta-\hat\beta)^TC_{\rm full}^{-1}(\beta-\hat\beta)\le\chi^2_{p,.95})을 다섯 STF 좌표로 투영했다. 모든 투영 영역이 영 텐서를 포함한다.

| (a,b\,[\mathrm{mag}]) | B의 (\|\sigma_{\rm eff}/H\|_F) 기준 범위 | C의 기준 범위 |
|---|---:|---:|
| 0, 0 | [0, 1.048135] | [0, 1.148916] |
| 0, .29 | [0, 1.051248] | [0, 1.120075] |
| .055, 0 | [0, 1.050904] | [0, 1.155737] |
| .055, .29 | [0, 1.051046] | [0, 1.120260] |

변환 ((\sigma_{\rm eff}/H)_{ab}=-(\ln10/5)B_{ab})는 J2000 observer-to-source 방향의 (B_{ab}\,[\mathrm{mag}])에 대한 작은 이방성·고정 redshift **시나리오**다. 큰 상한이 그 선형 근사를 검증하지 않는다. Model A의 STF는 `UNDEFINED`이며 0을 측정한 것으로 대체하지 않는다. `.95`는 기준 Gaussian 분위수이고 survey coverage가 아니다. 선언된 dimensionless (L^2(h_2/H)) remainder 반경 (r=0,.05,.10,.25)도 측정된 오류가 아니다. 원래 local 관계 (\Sigma_u^2=(\sigma_u:\sigma_u)/(6H_u^2)=(5/4)\langle(h_2/H_u)^2\rangle)에 적용하려면 같은 congruence의 source map, finite-z/boost/selection/calibration remainder의 동시 사건, (0<H_-\le H_u\le H_+)가 필요하다. 이 입력은 없다. 자유 mag 절편은 절대 (H_u\,[\mathrm{s}^{-1}])를 측정하지 않으며, (H_-\le0) 층의 quotient 상한은 유한하다고 할 수 없다.

## 4. 전체 carrier 및 (x,F,\Pi,Q,G_F) 해석 보존

[AUXILIARY]는 같은 274 PGC, 12개 경우에 대해 scalar, 방향 3-vector, row-major 3×3 STF의 공동 배열(274×12×13 저장 좌표, 9개 독립 좌표)을 유지한다. 원래 전체 fit 계수, 모든 공분산과 nuisance cross block은 [DISTANCE]와 [OPTICAL]에 남아 있다. 이 종합은 이들을 scalar score로 대체하지 않는다. 행·창·모형을 새로운 독립 표본으로 만들거나 threshold별 likelihood를 곱하지 않는다.

| 기호 | 이번 결과에서 허용되는 뜻 | 유지되는 물리 경계 |
|---|---|---|
| empirical (x) | 공동 residual scalar/vector/STF carrier | signed (x_C=(\sigma:\sigma-\omega:\omega)/(6H^2)+\Omega_{\rm tilt}+\Delta\Omega_k)는 미측정. 부호를 clip하지 않는다. |
| (F) | 명시된 empirical measure 아래 occupancy를 별도로 보고할 수 있음 | S01의 (F=a/U)는 독립적으로 admissible인 sign-clean sector와 positive ceiling이 있어야 함. 이 잔차나 \(x_C\)를 그 numerator로 채우지 않는다. |
| \(\Pi\) | 여기서는 혼동을 피하려고 \(\theta_{N,\Gamma}(t)\)라 부르는 유한 사건 함수 | 물리 posterior/법칙의 \(\Pi_Q,\Pi_F,\Pi_{G_F}\)가 아니다. 기존 unrestricted outer envelope [0,1], physical unknown mass 1 유지. |
| (Q) | 물리 anchor UNKNOWN | (U_\sigma=3B_\sigma^2/2>0)는 qualified shear anchor일 때만 유효하며 total signed x의 ceiling도 아님. mag 임계값, \(\Gamma\), declared remainder로 Q를 만들지 않는다. |
| (G_F) | auxiliary L/M/H는 입력 heliocentric velocity 창 | true depth 또는 common-congruence gap이 아님. 같은 sky/selection/normalization/joint covariance와 등록 floor를 갖춘 두 물리 F의 ratio는 DOMAIN_UNCERTIFIED. fold index는 depth가 아니다. |

H03의 (A_j=\|s_j\|/H_j)와 (g_j=\max(A_j,B\delta)/\max(A_0,B\delta))는 저장된 apparent diagnostics이다. [H03-RESULT]의 (B\delta\) 의존성과 source별 민감도는 재사용하지만 물리 (Q,G_F)로 이름을 바꾸지 않는다. 원래 (x_C,Q)는 `UNMEASURED`, (F,G_F)는 `DOMAIN_UNCERTIFIED`를 유지한다. 이 문맥의 물리적 정규화는 (H\ne0), 동일 frame/congruence·epoch와 s(^{-1}) 및 s(^{-2}) 수축의 일치를 요구한다.

## 5. 보조 증거가 닫지 못하는 부분과 역사 보존

[AUXILIARY]에서 원래 628 표적의 auxiliary indicator balance는 관측 결과가 없는 세 target cell 때문에 정확히 infeasible이다. 그 세 표적을 지운 625 표적의 양의 coarse weights는 **다른 estimand**이고 351개의 누락 outcome이 여전히 남는다. 세 unsupported cell 각각의 witness는 관측 내적 0, 표적 내적 \(-1/628\)이다. 더 세밀한 속도 moment도 저장된 정수 gap 2547 km/s 때문에 불가능하다. 양의 가중치나 concentration ESS 271.537086은 outcome law를 식별하지 않는다.

[SN]은 별도 Pantheon+ release commit `c447f0fea703fcd0fff57de5000947b5ca81286b`의 277행/238 literal CID를 사용한다. released total covariance를 한 번만 쓴 조건부 비교이며, 반복 행을 독립 SN으로 세지 않는다. 공동 fit의 calibration–flow cross covariance는 유지한다. CF4와의 cross covariance가 없고 source/selection/optical remainder가 qualified되지 않았으므로 두 자료를 결합하거나 이를 354개 missing outcomes의 대리로 쓰지 않는다. 사적 nominal training/FITRES parity HOLD도 해소되지 않는다.

[R25-EVIDENCE]의 저장된 산술 fold 평균 (E=0.00018321835875531898)은 고정된 대안 mixture가 해당 저장 null denominator보다 우세하지 않았다는 기술적 결과다. 이는 certified e-validity, null의 물리적 진실, posterior odds 또는 물리 \(\Pi\)가 아니다. 해당 과거 작업의 독립 검토는 **HOLD**다. 성공한 서로 다른 null fit은 20개지만 첫 실패 전 실행을 포함한 누적 수는 **적어도 21개**, 원래 cap은 **20개**, 정확한 과거 누적 수는 **UNKNOWN**이다. 수치가 이 사실만으로 거짓이 되는 것은 아니지만 문서 종합은 그 초과를 복구하지 못한다. 과거 ordering/사전등록/failed-source 부재도 소급 복원하지 않는다. 이 종합의 누락 사건 정리와 A/B·STF 결과는 이 cap 초과 작업의 수치나 수락에 의존하지 않는다.

## 6. 출처와 종료

`SOURCE_BINDINGS.json`은 아래 기호를 실제 파일 경로·byte 수·SHA-256에 묶는다. `RESULT.json`은 원래 S01–S06 의무와 위 표의 반올림 전 저장값, 전체 tensor/covariance JSON pointer를 보존한다. `RAW_READ_RECEIPT.json`은 실제 읽기/파싱 범위와 새 계산 0회를 기록한다. hash는 이 종합이 읽은 입력의 동일성이고 과학적 타당성의 증명이 아니다.

- [DAG], [S01-THEORY], [S01-CODE], [H03-SENSITIVITY], [H03-RESULT]: 원래 P1 질문·함수·공동 source 경계.
- [SELECTION], [DISTANCE], [OPTICAL], [SN], [AUXILIARY], [R25-EVIDENCE] 및 각 REPORT: 기존 실제 결과. [REVIEW-SELECTION], [REVIEW-DISTANCE], [REVIEW-OPTICAL], [REVIEW-SN], [REVIEW-AUXILIARY], [REVIEW-R25]는 해당 과거 범위의 독립 검토만 뜻한다.
- [R25-CAP]는 과거 cap 초과의 보존 근거다. [A2-AUDIT]는 이번 제한된 종료 선택의 배경이며 과학적 승인 근거로 사용하지 않았다.

새 fit·LP·catalogue pass·random draw·시뮬레이션·solver/ODE·과학 테스트 재실행은 **0회**다. 기존 수치의 파싱과 문서/출처 조립만 수행했다. 요청 모델/노력은 `gpt-6-astra/xhigh`; 관측 runtime identity는 `UNKNOWN`이다. 이 저자 결과를 한 번의 별도 표적 검토에 전달하고 A2 분기를 끝낸다. 추가 유사 sensitivity node, 새 물리 모형, 원래 상태 승격 또는 예산 재설정을 제안하지 않는다.
