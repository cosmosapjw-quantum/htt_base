# CF4 35,970-group 실제 관측원 조건부 Schur 식별성

입력 NPZ SHA256: 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c; parent HEAD: 13d8d85fa470d645d008986e8f77d8d0f70fdf54.

모형: DMzp–flat LCDM (Vcmb/c) residual = apparent 5D STF2 + method intercept/slope + independent bulk/dipole nuisance. 고정 대각 Gaussian 오차 가정.

- Full-data nuisance 제거 전 대비 Schur 정보 fraction (ascending): [0.371591095487709, 0.4909142647574501, 0.6606776864825338, 0.95672844020861, 0.9896876442564732].
- 정보 trace retained: 0.594886; 조건부 confidence ellipsoid 선형 크기와 별개인 hypervolume inflation 2.96024.
- Full-data apparent 5D norm 0.0332577424; 조건부 proxy /3 0.0110859141.
- 12 delete-one-sky-patch rank passes: 12/12. Frozen full-QR coefficient regression maxabs 1.21e-16.

방법 family 제외와 sky-region 삭제는 기존 동일 표본과 겹치는 민감도 검사다. 이들 차이는 독립 표본 가설검정 통계량이 아니다. method intercept/slope에 정확히 놓이는 가우시안 calibration covariance는 해당 nuisance를 무제한 profile하면 Schur 정보에 영향을 주지 않는다는 선형대수 정리를 별도 synthetic SPD 확인했다. 반면 angular/depth-correlated cosmic velocity covariance, 선택함수, 물리적인 photon/geodesic 응답은 이 정리로 제거되지 않는다.

**결론:** 이 결과는 조건부 관측 operator의 식별성이지 우주론적 비등방성/물리적 shear의 측정값이나 p-value가 아니다.
