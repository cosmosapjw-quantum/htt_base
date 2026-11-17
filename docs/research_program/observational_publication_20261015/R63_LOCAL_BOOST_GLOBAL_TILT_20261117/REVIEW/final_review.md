# R63 독립 최종 과학·코드 심사

판정: **PASS**. 구체적인 과학·구현 blocker는 발견하지 않았고, findings는 빈 배열이다. 이 판정은 선언한 C0 조건부 실제자료 응답 실험과 유한 연구계획의 일관성에 관한 것이다. **P4의 journal submission 판정은 NOT_READY_TO_SUBMIT를 유지한다.**

심사자 `/root/r63_final_review`, 2026-11-17. 요청 model/effort는 gpt-6-astra/xhigh이며 관측된 runtime model/effort는 UNKNOWN이다. 심사자는 이 과학·코드 결과의 작성에 참여하지 않았다. 한 번의 bounded read-only 심사를 수행했고 새 agent, 새 fitting, suite 반복, 원격 파일 변경, commit/push 또는 후속 연구루프를 수행하지 않았다.

기준 HEAD는 `f29bbab420a33aecb1c398ddd961fd45097f536b`, branch는 `research/r63-local-boost-global-tilt-20261117`이다. 동결 manifest의 22개 파일 SHA256을 실제 원격 bytes에서 확인했으며 불일치는 0개였다. manifest SHA256은 `7a6e541d646b099f25a4cb718374ec722328ba18c644a60d85753bcc5cae539b`이다. 개별 hash와 열람 범위는 동반 JSON에 보존했다.

## 과학적 판정 근거

1. **Endpoint와 catalogue chart의 부호·단위가 맞는다.** Sourceward n에 대해 eta를 풀어 쓰면 `(A−1)n·Vs/c − A n·Vo/c + (A+1)n·Vr/c − n·Vd/c + n·a_cal`이다. 여기서 공통 boost/calibration fibre와 고정 catalogue translation이 문서·코드 양쪽에서 일치한다. 고정 관측 redshift와 source emission redshift의 구별, natural logarithm, c의 km/s 단위를 유지한다. 이 fibre를 보편적 spacetime no-go로 승격하지 않는다.

2. **물리 frame의 식별이 일관된다.** 별도 보존된 dust/radiation의 `a^4(epsilon+p) beta` 조건은 `beta_m=b/a`, `beta_r=−Rb`와 일차 momentum compensation을 준다. 추가 photon/CMB-reference closure에서 `Vp=(1+R)W=U`이고 `Vo=Vr−RU/(1+R)`이다. U와 W를 혼동하지 않는다. finite post-decoupling interval, 독립 relative IC, 일차 FLRW 적합성, 이차 stress와 optical remainder 미확립을 명시한 것은 이 결과의 물리적 유효범위를 정확히 제한한다.

3. **Known-offset correction이 올바른 동일 실험의 translation이다.** Published q와 고정 reference dipole의 차이 `(A+1)(q−n·a)/c`를 y에서 빼는 부호가 맞는다. radiative background에는 실제 inherited numerical chi를 사용하는 `ln(chi_old/chi_rad)`를 별도로 전파한다. O, C, design과 source selection을 고정한 공통 offset이므로 모형 간 separation은 바뀌지 않고 score·estimate·p만 바뀐다. fitted a를 독립 observer measurement로 해석하지 않으며 distance/photometry p와 group/method response는 unresolved로 남긴다.

4. **Power 상한은 해당 Gaussian 실험에서 타당하다.** Composite null 전체에서 size를 지키는 검정은 가장 가까운 simple null에서도 같은 size를 지킨다. 그 Gaussian simple pair의 Neyman–Pearson power `Phi(Phi^-1(alpha)+delta)`가 따라서 상한이다. common calibration/STF와 constant bulk를 포함한 동일 nuisance projection, 고정 C, 특정 mean/source family를 전제로 삼고 있다. matter/radiation speed outer body를 더 좁히는 observer/optical 조건은 상한을 증가시키지 않는다. 이 논증은 전체 CF4 raw modes나 unrestricted global tilt에는 확장되지 않는다.

5. **Full tensor 기여와 약한 식별성을 구분했다.** Joint32와 dipole12 비교에 같은 STF/common calibration nuisance를 유지했다. joint precision의 conditional STF innovation 분해는 맞고, dipole-only에서 nuisance가 12개 row를 포화시키면 target response는 0이다. Full32의 history rank3가 물리적 velocity sensitivity를 뜻하지 않는다는 해석도 수치와 맞는다. 초광속인 unconstrained tangent W를 물리 측정으로 발표하지 않는다.

6. **다섯 view는 한 공동 법칙의 표현으로 유지된다.** 기존 R58 scaled-SVD GLS 및 stable whitened likelihood를 재사용하고, original target scale로 rank를 판정하며 saturated nuisance에는 정확한 zero를 반환한다. tiny tied response는 직접 구성하여 inverse-Fisher 차이의 상쇄를 피한다. x/Q/Pi/F/G_F를 다섯 primitive parameter나 새 확률법칙으로 주장하지 않는다. physical MES와 occupancy가 unavailable인 것도 유지한다.

## 독립적으로 실행한 최소 대수 검산

저장된 carrier의 작은 행렬만 읽어 14개 operator/order 조합에 대해 새 QR projection을 계산했다. 기존 R63 projection 함수나 fit를 호출하지 않았다. 전체 covariance에 대해 history information을 독립 재구성하고, 저장된 W covariance의 역행렬과 비교했다. 또한 저장된 tied와 constant response의 직접 차이를 사용해 separation을 재구성했다.

| 검산 | 결과 |
|---|---:|
| Independent QR history information vs stored information 최대 상대차 | 2.4623940e−13 |
| Independent information vs W covariance inverse 최대 상대차 | 1.0451927e−12 |
| Direct tied−bulk response로 구한 separation matrix 최대 상대차 | 6.0525522e−8 |
| 재계산된 body 전체 최대 mean distance | 2.385950102930609e−6 |
| 재계산된 alpha=.1 power 상한 | .10000041873090332 |
| Corrected W p의 저장값 대비 최대 절대차 | 0 |
| Corrected free-W body chi-square-change bound 최대값 | 7.072507307971148e−6 |
| Dipole-only nuisance rank | 14개 모두 12 |

직접 tied−bulk를 빼는 검산은 원 구현의 작은 difference 직접 구성보다 cancellation에 불리하다. separation의 약 6e−8 상대차는 power 상한에서 약 1e−14 정도만 바꾸며, headline 결론이나 표시된 유효 자릿수에 영향을 주지 않는다. 원 구현의 방법 선택은 적절하다. 실행 코드와 상세 결과는 `r63_final_review_algebra.sh`, `r63_final_review_algebra.json`에 보존했다.

54-test PASS와 실제-data/42 affine-direct parity는 기존 receipt와 코드 hash를 읽어 확인한 실행 근거다. 이 심사자가 그 suite나 실제자료 fit를 다시 실행했다고 주장하지 않는다. receipt에 기록된 값은 54 passed in2.28s, actual experiment2.2830978659912944s, chart scaled discrepancy4.656612873077393e−12이며 모두 exit0이다.

## 문헌·계획 및 release 경계

[2408.05264v1 원문](https://arxiv.org/html/2408.05264v1)의 main-text intrinsic-dipole 정의, Eqs1/4/29/33/36 및 TableIII를 직접 확인했다. Main text의 Y10 coefficient와 supplementary power-root amplitude 사이 표기 차이, Eq36 cross-term의 표시상 차원 문제 때문에 실행된 저자 inference의 정확한 convention을 별도 확인해야 한다는 판단은 타당하다. 문서가 저자의 수치 실행을 틀렸다고 단정하지 않고 26km/s를 R63 physical U 상한으로 채택하지 않은 점에 동의한다. 이 심사자는 publication-version full text를 읽었다고 주장하지 않는다.

Remote photon/electron dipole의 `w_eff=[1+z/(1+R)]n·U`와 scalar-window pushforward는 선언한 homogeneous mode에서 성립한다. 실제 electron-density reconstruction response, window/bias, source matching과 endpoint map effects가 추가 입력이라는 한정도 남겨 두었다. 연구계획은 그 source 계약을 한 번 닫는 경로와 qualified aberration fallback에 수렴하며, 같은 CF4 fitting을 반복하는 것으로 출판상의 약점을 해결하려 하지 않는다.

Prepared finalizer `scripts/r63/finalize_r63_dag.py`를 전부 정적으로 읽었다. SHA256은 `1a73961cc48c990c5a48339925872a13408db41de9a03037c9550f051eff16de`이다. R1–R9 완료와 PASS review, 286/221 predecessor 상태, original42 payload hash와 기존 paper payload를 mutation 전에 검사하며 P4 companion pointer와 scoped completion만 추가한다. 실행하지 않았으므로 DAG insertion·mirror·publication validation 완료는 이 PASS가 보증하지 않는다. 그것은 parent의 승인된 release 단계에서 확인할 일이다.

CF4 heterogeneous distance/flux calibration, grouping/selection covariance, finite physical/optical remainder, 독립 채널 공동 law와 coverage, source-specific normalization, 원래 P4 acceptance와 standalone novelty는 계속 unresolved다. 이 항목들은 현재 제한된 계산을 반박하는 새 blocker가 아니라 문서가 이미 보존한 물리적·출판상의 미완료 조건이다. 따라서 bounded review는 닫고, **NOT_READY_TO_SUBMIT와 original42 gates를 유지한 scoped release**로 진행할 수 있다.
