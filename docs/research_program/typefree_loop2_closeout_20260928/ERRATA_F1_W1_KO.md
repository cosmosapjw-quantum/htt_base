# F1 정오표 — TF-W1 kernel 조건의 적용 영역

이 문서는 게시 기준 commit `de3ab20219c46c2b14f1d2ec6bb87508c331634d`의
`docs/research_program/typefree_loop2_20260928/TF_W1_INPUT_KO.md` 마지막 절을
대체 해석한다. 원문과 raw 증거는 수정하거나 삭제하지 않는다.

## 정확한 유한차원 명제

유한차원 normed vector space (V,Y,Z)와 선형사상 (B:V\to Y),
(P:V\to Z)에 대해 다음은 동치다.

1. 어떤 유한한 (C\ge0)가 존재하여 모든 (v\in V)에 대해
   \(\lVert Pv\rVert\le C\lVert Bv\rVert\)이다.
2. \(\ker B\subseteq\ker P\)이다.

1에서 2는 (Bv=0)을 대입하면 즉시 따른다. 2를 가정하면
(L(Bv)=Pv)로 정의한 (L:\operatorname{im}B\to Z)가 well-defined다.
유한차원에서 (L)은 연속이므로 (P=L\circ B)이고
(C=\lVert L\rVert)를 택할 수 있다.

Affine domain (k_0+V)에서는 허용 variation에 대해
(\ker B\cap V\subseteq\ker P)를 사용하고 기준점 (k_0)의 항을 별도로
보존한다. 이 조건은 제약 없는 선형/affine variation domain의 균일한
operator bound에 관한 것이며, 일반 bounded 또는 curved physical feasible
set (K)의 필요조건이 아니다.

## 음성 대조와 실제 feasible set

(B=0), (P=\mathrm{id}), (K=[-1,1])이면 kernel inclusion은 실패하지만
(P(K))는 유계다. 일반 (K)에서는 관측값 (y)에 대한
(P(K\cap B^{-1}\{y\})), 또는 noise·nuisance·source를 함께 넣은 joint
feasible image의 유계성과 직경을 직접 평가해야 한다.

따라서 다음 세 판정은 서로 다르다.

- feasible image의 유계성;
- fiber가 singleton인지에 관한 유일 식별성;
- null/covariance/coverage가 필요한 confidence calibration.

이 보정은 R2의 4/1/2 계수, monopole 와도 열 0, finite-window 적분과
오차식을 바꾸지 않는다. source/time law와 joint anchor가 없으므로 수치
(Q,F,\Pi,G_F), MES percentage 및 p-value는 계속 `UNAVAILABLE`이다.
