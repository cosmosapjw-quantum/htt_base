# 구체적 수정 권고 (v6 → v7 반영용)

각 항목은 (위치 → 문제 → 교체/추가 문안) 형식이다. LaTeX 문안은 그대로 붙여 넣을 수 있도록 작성했다. 우선순위는 심사 보고서 §6과 일치한다.

---

## R1. [치명 F1] \(\Omega_{k,\rm aniso}\) 부호 도메인과 P26 양측-박스 일반화

**위치**: tex 147행 ("All four entries are dimensionless, nonnegative component magnitudes"), §3.3 \(\mathcal{C}_{\rm phys}\), P26 (tex 310–327행), E1 예제.

**문제**: \(\Omega_k=-{}^3R/(6H^2)\)는 \({}^3R>0\)(Bianchi IX/Kantowski–Sachs형)에서 음수이고, MATCHED 참조에서는 열린형도 음수 가능. 비음수 콘은 이 모형들을 무언 배제하며, 단측 널 박스 \([0,U_k]\)는 식별구간 하한을 인위적으로 올린다(등록 예제: 0.11 vs 양측 박스의 0.09).

**교체 문안 (§3.1 끝)**:

```latex
The shear, vorticity, and tilt entries are nonnegative by construction
($w>-1$ assumed for the tilt).  The curvature entry is SIGNED:
$\Omk>0$ for open-type anisotropic curvature (${}^3R<0$ relative to the
reference) and $\Omk<0$ for closed-type (${}^3R>0$; e.g.\ Bianchi~IX or
Kantowski--Sachs branches) or for models less open than a MATCHED
reference.  Accordingly ${\cal C}_{\rm phys}$ is the orthant in the
first three coordinates times $\R$ in the curvature coordinate, and the
MES-type ceiling on the curvature null direction is the TWO-SIDED box
$|\Omk|\le U_k$.  A branch may declare the one-sided restriction
$\Omk\ge0$ (open-type only, FLAT reference); every interval computed
under that declaration is conditional on it.
```

**P26 진술 교체 (널 기여 부분)**:

```latex
x_C^\pm=\left(\hbox{reachable extremes}\right)
+\sum_{j\in{\rm null}}\left[\min(c_jL_j,\,c_jU_j),\;\max(c_jL_j,\,c_jU_j)\right],
```

여기서 \([L_j,U_j]\)는 성분 \(j\)의 선언된 (부호 포함) 천장 박스. 단측 선언 \(L_j=0\)이면 기존 식으로 환원. **E1 예제는 두 줄로**: 단측 선언 시 \([0.11,0.17]\), 양측 곡률 박스 시 \([0.09,0.17]\) — 어느 쪽이 등록 분기인지 명시.

**게이트 영향**: `egs3_identified_set.py`에 곡률 하한 파라미터 추가; E1 witness에 두 사례 모두 수록.

---

## R2. [중요 M1] P36 엄격성 조건 재진술

**위치**: tex 293–304행 (P36).

**문제**: "inclusion is strict whenever \(c_N,c_D\ne0\) and \(\mathcal S\) nondegenerate"는 거짓. 반례: \(c_N>0,\ c_D<0\)이면 naive의 분자·분모 최적 \(s\)가 일치하여 joint = naive.

**교체 문안 (정리 끝 문장)**:

```latex
and the inclusion is STRICT at the upper endpoint iff the numerator and
denominator COMPETE for the shared components there, i.e.\ iff there
exists a component $j$ with $c_{N,j}\,c_{D,j}>0$ and a nondegenerate
$j$-interval in ${\cal S}$ (mutatis mutandis at the lower endpoint).
In the ALIGNED regime, $c_{N,j}c_{D,j}<0$ for all $j$, the independent
optimizations of the naive quotient are attained at a common $s$, and
the two intervals COINCIDE: sharing a nuisance component does not by
itself narrow the identified set.
```

**증명 수정**: "Optimizing over a superset can only widen" 문장 뒤에, 정렬 레짐에서는 product-집합의 최적점이 대각선 위에 있으므로 넓힘이 발생하지 않는다는 한 문장을 추가. (정식 정리: `03_theorem_candidates_ko.md` T2; 수치 검증: exp04, 교정 기준 일치 93/94.)

---

## R3. [중요 M2] P31 sharpness — 강등 또는 적합성 보조정리로 승격

**위치**: tex 329–335행 (P31).

**옵션 (i) — 강등 (즉시 가능)**:

```latex
\begin{lemma}[Identified-set sharpness, convex-program level]
Every point of $[x_C^-,x_C^+]$ is attained by a point of the feasible
set ${\cal G}(y)$; the interval is sharp AS A PROPERTY OF THE REGISTERED
CONVEX PROGRAM.  Whether every such point is additionally realized by an
initial-data set satisfying the full constraint system (Gauss AND
momentum) with declared matter content is a separate physical-realizability
statement, recorded as a conditional obligation (see T3).
\end{lemma}
```

ledger 상태를 COND로 유지하되 "convex-level DER / physical-level OPEN"의 이중 태그 권장.

**옵션 (ii) — 승격**: T3(Codazzi-적합성 보조정리)을 증명해 현 진술을 유지. 핵심 부담: 주어진 도달 성분 \((\Sigma^2,\Omega_t)\)과 박스 값 \((W^2,\Omega_k)\)에 대해, (a) Gauss 예산에서 \(\Omega_m+\Omega_\Lambda=1-x_C\ge0\) 확보(작은 \(x_C\)에서 자동), (b) 운동량 제약을 tilt-유도 에너지플럭스 \(q_a=(\mu+p)\sinh\beta\cosh\beta\,e_a\)로 균형(예: LRS Bianchi V형 국소 구성이 명시 해를 제공 — P5의 제약이 바로 그 예), (c) 에너지 조건 확인. P11은 (b)의 \(\Pi_{ab}\)-부분에만 인용.

---

## R4. [중요 M3] §3.4에 추정-공분산 임계값 분기 추가

**위치**: §3.4 (P35 뒤), §13.4의 M5' 항목과 상호참조.

**추가 문안**:

```latex
\paragraph{Estimated-covariance regime.}  When $C_y$ is estimated from
$N_{\rm sim}$ simulations, the whitened statistics of this subsection
are no longer $\chi^2$: the stage-1 and stage-2 thresholds must either
be rescaled by the Hartlap factor $h=(N_{\rm sim}-m-2)/(N_{\rm sim}-1)$
applied to the quadratic form, or replaced by the Sellentin--Heavens
multivariate-$t$ (equivalently $F$-type) quantiles.  At
$m=10,\ N_{\rm sim}=300$ the uncorrected stage-1 test has true size
$\approx0.07$ at nominal $\alpha_1=0.05$; the effect grows from
percent-level ($m\lesssim10$) to tens of percent ($h=0.83$ at $m=50$,
$N_{\rm sim}=300$).  An EMPTY verdict claimed without this correction
overstates refutation evidence.
```

수치 출처: exp11 (표 포함). "percent-level" 단독 표현은 삭제.

---

## R5. [치명 F2] 실데이터 end-to-end 1건

**권고 구성**: K5 lane이 최단 경로다. 이미 존재하는 재료 — CF4 |B| = 341 ± 102 km/s (D05), K5 mock 공분산, \(\Omega_{\rm tilt}\)-계 kinematic 좌표(D23), MES 천장(P3) — 로:

1. \(y\) = (저-ℓ 사중극 계수 요약, CF4 벌크 성분 3개), \(R\) = 등록 응답(rank 2), 널 = \((W^2,\Omega_k)\) with 양측/단측 선언.
2. A8 실행: stage-1 사양검정 결과 보고 (통과/EMPTY), stage-2 조건부 집합, 널-박스 합성.
3. 산출: \(x_C\in[\cdot,\cdot]\) 또는 상태 판정 + IM 끝점 CI + 민감도(단측 vs 양측 곡률 박스, 천장 2안).

이 한 건이면 "방법론이 실제로 작동한다"는 심사 요건이 충족되고, diagnostic-only 원칙도 유지된다(구간은 posterior가 아니므로).

---

## R6. [치명 F3] 저널 판 재구성 체크리스트

- 감사 어휘 삭제/치환: gate class → "numerical witness (Table N)"; seal → "symbolic verification"; MIO/HTT/OBSSTAT/BASS → 역할 서술("diagnostic layer", "inference layer"); claim tier → 본문 지위 문장.
- §1.1 response map, §12.5 acceptance 표, §15 metadata — 삭제 (감사 부록으로 이관).
- 초록 재작성: 기여 4줄(comparator 유도, 부분식별 의미론, 두-단계 커버리지, e-값 lane) + 결과 1줄 + 한계 1줄.
- P-번호 본문 순서 재부여; DER/COND 정의를 서론에 1문단으로.
- 대문자 강조(REGISTERED, EXACTLY, …) → 이탤릭 또는 삭제.

---

## R7. [중요 M4] MES ε-계수 부록

**권고**: 부록 "Derivation of the three-budget coefficients"를 추가하고 Maartens–Ellis–Stoeger (1995) PRD 51의 해당 식 번호와 항별 대응표를 제시. 최소안: 계수별 출처 식 번호 + 재유도 스크립트(sympy) seal을 F1 게이트에 추가. 현재 게이트는 "코드=문서 일치"만 보증하고 "문서=문헌 일치"는 보증하지 않는다는 점을 명시.

## R8. [중요 M5] 실측 응답행렬 공개

**권고**: A6 감사 출력에서 실측 채널 whitened \(R\) (또는 그 Gram 행렬)의 수치, 특이값 스펙트럼, 조건수, \(\bm g\)-기저 널공간 벡터를 표로 인쇄. rank-2가 특이값 절단(threshold) 문제로 환원되는 경우 그 절단 기준도 등록.

## R9. [중요 M6/M7/M9] 데이터 도판 수리

- **D10–D12**: 캡션에 "resultant amplitude는 무작위 카탈로그 대조 이전이므로 서베이 창 기하와 분리되지 않음"을 추가. 가능하면 z-셔플 널 참조선 1개.
- **D04/D13**: 제목·캡션에 "uncorrected"를 넣고, 대심도 음의 중앙값 추세는 거리지표 로그-오차(Malmquist형) 편향의 예상 신호임을 1문장 명시. "sign transition"을 물리 신호로 읽지 말라는 경고 포함.
- **D23**: 제목을 "observed-sector proxy dashboard"로 변경, 각 패널에 proxy임과 단위 명시, \(\bm g\) 좌표가 아님을 캡션 1문장으로.
- **D07** 3번 패널: 부록 이동 또는 삭제.

## R10. [중요 M8, 사소 m11] 게이트 판정 정책 인쇄

- §10 e-값 행: "PASS 기준: 평균의 1 초과가 단측 z ≤ 3 이내, 모든 Markov 꼬리 준수" 식의 명문 규칙 추가 (현재 값: z = +1.18 → PASS).
- E3 행: 검정력 곡선을 (진폭 → EMPTY 비율) 쌍으로 인쇄 (현재 "rising to 1.00"에는 x-좌표 부재).
- F3 행(전단-기억): 구동 이력 \(\Pi(t)\)와 \(c_H\) 규약을 witness 표에 병기 — +33%/−20%는 이력 종속 수치임 (exp06 확인).

## R11. 사소 항목 일괄 (m1–m12)

| # | 위치 | 수리 |
|---|---|---|
| m1 | §3.1 tilt 식 | "at \(O(\sinh^2\beta)\)" → "exact for a single perfect fluid; multi-component sources add \(\sum_i(1+w_i)\Omega_i\sinh^2\beta_i\)" |
| m2 | §3.2 parent identity | \(\omega\ne0\) 시 \({}^3R\)의 형식적 정의 각주 |
| m3 | §3.1 | \(H_\theta\) → \(H\) 통일 또는 정의 |
| m4 | P16 | "linear" → "proportional (zero intercept)" |
| m5 | §1 | claim tier·DER/COND 정의 상자 |
| m6 | D07 | 3번 패널 부록행 |
| m7 | 초록 | 기여 중심 재작성·분할 |
| m8 | 전반 | 대문자 강조 제거 |
| m9 | P35(iii) | \(\widehat\sigma^\pm\) 정의 선행 |
| m10 | ledger | 저널 판 재번호 |
| m11 | §10 E3 | 검정력 곡선 좌표 |
| m12 | D05/본문 | 341±102 수치 동기화 |

---

## R12. 출판 전략 (권고)

1. **Paper A** (JCAP/PRD): comparator 유도 + 부분식별/상태대수 + 두-단계 IM 커버리지 + K5 end-to-end 1건. R1–R5 선결.
2. **Paper B** (JCAP/MNRAS/A&A): anytime-valid 저-ℓ 모니터링 설계 + Hartlap/SH 보정 정리(T4) + K1 시뮬레이션 검증.
3. **Paper C** (CQG): 응답-랭크/채널 재개방 정리군 + 실측 R 공개.
4. 데이터 진단 24매는 companion 노트(Zenodo/arXiv 부록)로 분리.

각 논문의 결론에는 "무엇이 아직 측정되지 않았는가"(UNBOUNDED 의미론)를 명시적 절로 두는 것이 이 프로그램의 차별성을 가장 잘 전달한다.
