# 다음 이론 단계: 임의 유한 차원의 잔차 Gram 타원체

이 노트는 `CAS11-C02-FINITE-GRAM.json`과 `CAS11-C03-WEIGHTED-PROJECTION.json`의 버전 3 계약만을 입력으로 한 수학적 유도이다. C04의 소스·출력은 읽지 않았고 재실행이나 독립 심사도 하지 않았다. 아래 증명은 새로운 CAS·형식 검증 PASS, 과학적 승인 또는 신규성 주장이 아니다. C02의 동결된 목표는 순방향 함의이며, 아래의 **역방향과 동치 표기는 그 목표 밖의 이론 확장**이다. 기존 계약은 변경하지 않는다.

양의 정수 \(n\)을 임의로 고정하고, \(R=R^T\succeq0\), \(e\in\mathbb R^n\), \(\varepsilon\ge0\)라 하자. \(R^\dagger\)는 양의 고유값만 역수로 바꾸고 영 고유값은 0으로 두는 대칭 Moore–Penrose 의사역행렬이다. 그러면

\[
\bigl[\;\forall a\in\mathbb R^n,
 |a^Te|^2\le2\varepsilon\,a^TRa\;\bigr]
\quad\Longleftrightarrow\quad
\bigl[\;e\in\operatorname{range}R,\qquad
 e^TR^\dagger e\le2\varepsilon\;\bigr].
\tag{1}
\]

여기서 \(R\succeq0\)는 C02의 가정이다. 잔차 Gram 구성에서 이 가정을 확보하는 논리는 아래 C03 연결에 따로 둔다.

**동결 C02 목표에 해당하는 순방향.** 임의의 \(k\in\ker R\)를 보편 부등식에 대입하면
\[
0\le |k^Te|^2\le2\varepsilon\,k^TRk=0.
\]
따라서 \(e\perp\ker R\)이다. 유한 차원의 대칭 행렬에서는
\(\operatorname{range}R=(\ker R)^\perp\)이므로 \(e\in\operatorname{range}R\)를 얻는다. 이 단계는 영 고유방향의 오차 성분을 제거하며, 의사역행렬을 쓰는 것만으로 대체할 수 없다.

이제 \(q=e^TR^\dagger e\ge0\)라 두고 \(a=R^\dagger e\)를 대입한다. \(R^\dagger R R^\dagger=R^\dagger\)에서
\[
a^Te=q,\qquad a^TRa=q,\qquad q^2\le2\varepsilon q.
\]
만일 \(q>2\varepsilon\)라면 \(q>0\)이고 \(q(q-2\varepsilon)>0\)이므로 마지막 부등식에 모순이다. 따라서 \(q\le2\varepsilon\)이다. 이 증명은 \(q\), \(\varepsilon\), 영 고유값 어느 것으로도 나누지 않는다. \(n\)에 관한 추가 조건을 사용하지 않았으므로 모든 양의 정수 \(n\)에 적용된다.

**동결 목표 밖의 역방향.** \(e\in\operatorname{range}R\)와 \(q\le2\varepsilon\)를 가정한다. 직교 고유기저에서 양의 고유값을 \(\lambda_1,\ldots,\lambda_m>0\)라 쓰면, 범위 조건에 의해 \(e\)의 나머지 \(n-m\)개 성분은 0이다. 같은 기저의 좌표를 \(\widetilde a,\widetilde e\)라 하면 유한 합의 Cauchy–Schwarz 부등식으로
\[
\begin{aligned}
|a^Te|^2
&=\left|\sum_{j=1}^{m}
 (\sqrt{\lambda_j}\,\widetilde a_j)
 \frac{\widetilde e_j}{\sqrt{\lambda_j}}\right|^2\\
&\le\left(\sum_{j=1}^{m}\lambda_j\widetilde a_j^2\right)
 \left(\sum_{j=1}^{m}\frac{\widetilde e_j^2}{\lambda_j}\right)
=(a^TRa)q
\le2\varepsilon\,a^TRa.
\end{aligned}
\]
역수는 오직 양의 고유값에만 취했다. \(R=0\)이면 \(m=0\)이고 범위 조건이 \(e=0\)을 강제하므로 양변은 모두 0이다. 순방향에서도 \(\ker R=\mathbb R^n\)이므로 같은 결론을 얻는다. \(\varepsilon=0\)이면 순방향의 보편 부등식이 \(e=0\)을 강제한다. 역방향에서는 \(q=0\)과 범위 조건으로 모든 양의 고유방향 성분까지 0이 되어 \(e=0\)이다. 따라서 두 퇴화 조건이 동시에 성립하는 경우도 포함한다. 특히 범위 조건을 생략한 \(q\le2\varepsilon\)만으로는 (1)이 성립하지 않는다. \(R=0\), \(e\ne0\)가 바로 반례이다.

**C03가 제공하는 연결과 다음 분석 과제.** C03가 지정한 유한 차원 양의 정부호 내적 공간에서 \(P\)를 \(V\) 위의 \(W\)-직교사영으로 두고 \(r_i=(I-P)K_i\), \(R_{ij}=\langle r_i,r_j\rangle_W\)라 정의하면, 해당 목표는 \(P^2=P\), 잔차의 \(V\)에 대한 직교성, Cauchy–Schwarz 및
\[
a^TRa=\left\|\sum_i a_i r_i\right\|_W^2\ge0
\]
를 제공한다. 여기서 “제공”은 계약이 명시한 수학적 내용과 그 조건부 사용을 뜻하며, 이 노트가 C03의 실행 결과를 확인했다는 뜻이 아니다.

C02를 실제 오차에 적용하려면, 예를 들어 동일한 내적 공간의 어떤 \(z\)에 대해 다음 두 식을 별도로 확보하면 충분하다.
\[
e_i=\langle r_i,z\rangle_W\quad(1\le i\le n),
\qquad \|z\|_W^2\le2\varepsilon.
\tag{2}
\]
그러면 \(a^Te=\langle\sum_i a_i r_i,z\rangle_W\)이므로 C03의 Cauchy–Schwarz가 (1)의 왼쪽을 주고, C02 순방향이 특이 행렬까지 포함한 타원체 제약을 준다. 원래 오차가 \(\langle K_i,z\rangle_W\)로 표현된다면 \(\langle PK_i,z\rangle_W=0\)도 필요하다. 모든 \(v\in V\)에 대한 \(\langle v,z\rangle_W=0\)은 이를 보장하는 충분조건이다. 이 소거 조건과 (2)는 C03의 사영·Gram 항등식만으로 따라오지 않는다.

연속체 또는 물리 모델에서는 \(K_i,z,W\)의 정의, 양의 내적의 정당화, 영집합 동치류와 적분가능성, 사영의 존재를 위한 적절한 Hilbert 공간·닫힌 부분공간 조건, 실제 오차의 표현·모멘트 소거, 그리고 \(\|z\|_W^2\le2\varepsilon\)의 분석적 유도가 남는다. Hessian 상계, Bregman/Taylor 적분, 물리적 미분 상계는 이 유한 행렬 논증에서 생성되지 않는다. 다음 이론 작업의 구체적 목표는 선택한 모델에서 (2)와 필요한 소거 조건을 명시하고 증명하는 것이다.

모든 양의 준정부호 실대칭 행렬은 \(R^{1/2}\)의 열벡터들을 이용한 유한 Gram 표현을 갖는다. 그러나 이러한 대수적 표현은 그 벡터들이 선택한 물리 모델의 \((I-P)K_i\)라는 사실을 입증하지 않는다. 여기의 \(R\)은 결정론적 잔차 Gram 행렬이며 관측 잡음 공분산으로 해석하지 않는다. 공분산으로 사용하려면 확률변수·중심화·기댓값 등에 관한 별도 모델이 필요하다.

단위는 우선 \(K_i,r_i,z,e,R,\varepsilon,a\)를 모두 무차원화한 좌표로 정한다. 물리 단위를 유지할 경우에도, 예를 들어 모든 \(r_i\)의 단위를 \(\rho\), \(z\)의 단위를 \(\zeta\), 가중 내적의 측도·가중치를 무차원, \(a_i\)를 무차원으로 두면 (2)에 따라
\([e_i]=\rho\zeta\), \([R_{ij}]=\rho^2\), \([\varepsilon]=\zeta^2\), \([e^TR^\dagger e]=\zeta^2\)이다. 따라서 두 부등식은 차원상 일치한다. 성분별 물리 단위가 다르면 먼저 각 성분의 기준 척도를 고정해 무차원화한 뒤 위 행렬 연산을 적용해야 한다.

입력 계약 파일의 SHA-256은 다음과 같다. 이는 위 두 파일의 바이트 해시이며, 새로운 실행 또는 결과 해시가 아니다.

| 입력 계약 | SHA-256 |
|---|---|
| CAS11-C02-FINITE-GRAM.json | c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a |
| CAS11-C03-WEIGHTED-PROJECTION.json | a97dc88082095ba636d326ea390cf629b86ca333577a27638c83c2b7f9a55794 |
