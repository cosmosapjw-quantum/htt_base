# CF4 실제 38,053개 그룹 공통 거리척도 mapping 조사

Table 3: 38053 rows; positive DMav/e_DMav 37825 groups.
나머지 228 그룹은 지정한 중간 group-mean 채널이 없어 직접 source 여부를 별도로 구별한다.
이 중 양의 직접 calibrator DMcal을 갖는 그룹 수 228.

**모든 37825개 유효 행에서 published precision DMzp−DMav = −0.147 mag.**
이는 publication-format deterministic affine relation이지 진짜 distance distribution의 무오차 공분산을 확정한 것은 아니다.
동일 data를 독립 Gaussian likelihood로 여러 번 사용하면 필연적으로 정보 중복이 생긴다.

선택 24개 그룹의 DMav−DMsnIa: 22개 0, 나머지 두 그룹 −0.275, −0.179 mag.
이 두 변형의 멤버/방법 결합 원인은 Table 3에 제공된 method flags만으로 인증되지 않았다.
실제 환산 전에 Table2 host/method-level source and calibration provenance 연결이 필요하다.

## 직접 calibrator와 그룹 결합값의 실측 overlap
두 채널이 모두 제공된 그룹은 108개이고, SN Ia 관측도 가진 그룹은 42개다.
DMcal−DMav의 단순 중앙값은 -0.1330 mag, 중앙절대편차는 0.2190 mag.
이 값은 결과를 보고 선택한 방법별/그룹별 overlap 진단이지 개별 측정의 independent calibrated posterior가 아니다.
Table3에는 DMcal의 그룹별 불확실도 및 event-level cross-covariance가 없고, DMav는 이미 결합된 measurement다.
표본 bootstrap은 독립 그룹을 가정한 기술적 민감도이며 별도 거리척도 정밀도 인증으로 사용하지 않는다.

원전: Tully et al. 2023, CDS J/ApJ/944/94 ReadMe Note 1–5.
