# S01: x,F,Pi,Q,G_F 정의역 및 수치 검산

서로 다른 물리적 의미를 가진 함수들을 구분하고 HTT joint finite atom의 signed/undefined mass를 보존하는 코드를 구현했다. 예시 데이터는 완전히 **합성된 세 원자**이므로 어떠한 실제 Planck/CF4 posterior, anisotropy 발견, model p-value도 추정하지 않는다.

x_C=Sigma2-W2+Omega_tilt+DeltaOmega_k; Q=x_C/U_sigma, U_sigma>0 인 구역만 정의; Q는 total-x 물리적 포화율이 아니다. F=sector_value/sector_ceiling은 sign-clean 구역과 양의 sector bound를 요구한다. Pi_Q(t)=P(Q>t)는 strictly greater-than이며 정의되지 않은 Q의 원래 posterior 질량을 지워 재정규화하지 않는다. G_F는 명시적 depth bins의 F mean과 사전 지정 floor δ로만 계산한다. F4=<T^4>/T0^4 볼로메트릭 모멘트는 F가 아니다.

합성 예시의 undefined Q mass=0.25; G_F outer interval=[0.48888888888888893, 1.6800000000000002]. 실자료 적용은 동일 physical likelihood와 sample IDs/cross-source covariance, 공통 tetrad/curvature/frame가 식별된 경우만 observational claim으로 허용된다.
