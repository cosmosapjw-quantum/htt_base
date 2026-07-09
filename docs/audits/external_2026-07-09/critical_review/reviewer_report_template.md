# 심사평 초안

## Recommendation

**Major revision.** 관측 우주론 결과 논문으로 제출된 것이라면 현재는 reject에 가깝고, 방법론/소프트웨어/감사 프레임워크 논문으로 재구성하면 major revision 후 재심 가능하다.

## Summary

원고는 FLRW 기준에서의 이탈을 상세 anisotropic geometry로 즉시 해석하지 않고, component vector, signed comparator, response rank, identified set, diagnostic/inference separation으로 다루려는 프레임워크를 제안한다. 이 방향은 건전하고, 기존 Bianchi-template식 overclaim을 줄이는 장점이 있다. 그러나 현재 원고는 posterior/evidence나 validated observational inference를 제시하지 않는다. 데이터 그림은 대부분 diagnostic-only이며, selection/covariance/null/transfer gate가 열리지 않았다.

## Major comments

1. \(\Omega_{k,{\rm aniso}}\)의 signed/nonnegative status가 모순적으로 보인다. component cone과 comparator identity 중 어느 쪽을 우선할지 명확히 해야 한다.
2. P31 identified-set sharpness는 추상 component cone에 대한 sharpness로 제한해야 한다. full GR physical realizability로 읽히면 과장이다.
3. P36의 strict inclusion 조건은 false다. \(N(s)=2+s, D(s)=5-s, s\in[0,1]\)에서는 \(c_N,c_D\ne0\)이지만 joint와 naive interval이 같다.
4. P35 coverage theorem은 known Gaussian covariance and smooth endpoint regime에 한정되어야 한다. estimated covariance, active-set changes, post-hoc scanning에는 별도 calibration이 필요하다.
5. 제공 zip은 rendered report package이지 reproducibility package가 아니다. Manifest의 input hashes가 유용하긴 하지만 원본 scripts/data/fixtures가 빠져 있어 심사자가 재현할 수 없다.
6. D01–D24 figure gallery는 appendical diagnostic atlas로 내려야 한다. 본문에서는 posterior/evidence/family claim이 없음을 더 강하게 명시해야 한다.

## Minor comments

- \({}^{3}R\), \(H\), \(\Theta\), congruence convention을 parent constraint 앞에 다시 선언해라.
- \([x_C]_+\)와 \(x_C^+\) endpoint 표기 분리는 유지하되, 전체 원고에서 기계적으로 검사해라.
- “current-data pass”라는 표현은 “current prepared-data diagnostic pass”로 낮추는 것이 안전하다.
- theorem ledger에는 “imported external coefficient”, “symbolic algebra seal”, “synthetic MC witness”, “observational validation”을 별도 열로 분리해라.

## Required revisions before acceptance

1. One-command reproducibility bundle.
2. Corrected theorem statements for P31/P35/P36.
3. Formal curvature-component convention.
4. A compact, publication-facing methods narrative separated from data diagnostics.
5. At least one fully calibrated demonstration, even if synthetic, with predeclared thresholds and covariance handling.
