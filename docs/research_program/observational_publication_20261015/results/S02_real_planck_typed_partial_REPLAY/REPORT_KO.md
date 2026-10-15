# P1 S02: 실제 Planck 동일 하늘의 MES source denominator와 물리적 미식별성

실제 Planck 처리 제품 9개는 하나의 하늘이다. 이 코드에서 processing 제품에 확률 가중치를 부여하지 않으며, posterior 표본 9개라고 부르지 않는다.

eps1=0과 모든 관측자 C1/C2 미분 조건을 '추가 가정'했을 때 계산되는 shear-sector U_sigma 범위는 2.51083288e-09–2.59332149e-09; omega-sector U_omega 범위는 2.94274154e-12–3.07340514e-12. 선택한 SMICA_FULL 대비 U_sigma processing spread는 3.1957%.

조건부 counterfactual flat+untilted+geodesic 0<=Sigma2<=U_sigma, 0<=W2<=U_omega일 때 Q∈[-U_omega/U_sigma,1]이다. 하지만 미측정 curvature DeltaOmega_k를 unrestricted signed로 남기면 x_C와 Q는 실수 전체에 미식별이며, 어떤 t에서나 Pi_Q(t)∈[0,1]밖에 말할 수 없다. 이는 posterior p-value나 유의성 구간이 아니다. F 및 G_F도 표본에 대한 실제 positive-sector와 depth source가 없어 미측정이다.
