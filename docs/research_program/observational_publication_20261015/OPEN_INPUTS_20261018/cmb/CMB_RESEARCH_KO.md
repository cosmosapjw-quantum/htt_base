# 공개 CMB·외부 Bianchi 전이 조사 — 2026-10-18

Owner: obsstat 연구 입력 조사. 범위: R2·R4·R5, EXPLORATORY / NON-CLAIM-BEARING.
기준 HEAD: `4a68995507bf8e672b2551d9030f3ad9f0d2152e`. 관측 런타임: UNKNOWN.
PhysMath Research Loop 1.3.0의 선택 단계·구성적 불변량·NG1–NG7 정책을 적용했다.
자식 에이전트, solver 구축, ODE/적분, 기존 map 처리 재실행, 저장소 복제, 게시를 하지 않았다.

공식 **SMICA PR3 weights archive 전체 바이트를 무인증으로 확보**했다. 또한
SMICA HM1/HM2/OE1/OE2 noise ID00000 각각에서 실제 FITS 헤더 바이트를 무인증으로
받았다. 이 두 결과는 L03의 외부 입력 접근성을 구체적으로 개선한다. 그러나 matched
split CMB response·공동 seed 법칙·잔여 전경·가중치 선택·통계량별 coverage를 아직
제공하지 않아 L03 완료로 바꾸지 않는다. B02/V03에 바로 입장 가능한 공개 polarized
all-m 수치 atlas는 이번 유한 탐색에서 확보하지 못했다. 이 진술은 존재 불가능성
정리나 모든 공개 저장소를 소진했다는 주장이 아니다.

## 실제 접근과 재사용

| 입력 | 관측한 접근 | 사용할 수 있는 범위 |
|---|---|---|
| SMICA weights R3.00 | HTTPS GET 200, 전체 74,625,775 bytes, tar 정상 inspect | 공식 고정 가중치와 transition mask의 출처 |
| SMICA split noise | 네 split 모두 GET 200, 첫 5,760 bytes, FITS magic 및 I/Q/U 헤더 | 실제 무인증 경로·형식 확인; 전체 payload 검증 아님 |
| HFI100 full/HM1 noise | GET 200, FITS 헤더 | 주파수 단계 대체 경로 |
| HFI RIMO beams R3.01 | Range GET 206, gzip magic, 총 86,556,876 bytes | beam archive 공개 바이트 접근; 전체 취득 아님 |
| NERSC→CMB-S4 | 공개 metadata, 파일 전송은 Globus 인증이라고 공식 안내 | “public”과 “no-login” 구별 |
| Zenodo48653/48654 | 전자는 MC chains/plots, 후자는 MP4 네 개 | prior/문헌/그림 문맥; 수치 전이 atlas 아님 |

정확한 URL·auth 상태·receipt는 `DATA_CMB.json`에 있다. 전체 weights 파일 SHA256:
`044ec9bed746ae745ad35a8b6ccf6e603f546083fec328e9c64d866ac9221f93`.
원본 archive는 이 worker 폴더에 남기며 패치/게시 대상에서 제외한다. 재다운로드가 필요 없다.
README와 Python 소스만 읽었고 실행하지 않았다.

공식 archive는 E/B weights `(2,7,4001)`, T의 Xfull/Xhigh 및 각각의 NOSZ weights,
transition mask를 담는다. 소스는 편광에 30–353 GHz 일곱 채널, 온도에 두 sky zone을
사용하며 zone 차이에 ell50–150 cosine highpass를 적용한다. README는 weights에 beam
correction과 LFI renormalization이 포함됨을 명시한다. 따라서 별도 beam을 무비판적으로
다시 적용할 수 없다. archive에는 HM1/HM2/OE1/OE2별로 이름 붙은 weights가 없다.
이 관찰은 split 가중치가 물리적으로 달라야 한다는 증거가 아니라, 현재 artifact가 어떤
분리를 실제 제공하는지에 관한 사실이다.

[공식 CMB maps 문서](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps)는
`noise_hm1/noise_hm2/noise_oe1/noise_oe2` 명명 규칙을 제공한다. 직접 받은 네 파일은
NSIDE2048/RING, 세 vector columns INTENSITY/Q-POLARISATION/U-POLARISATION,
K_CMB이다. nominal ID 일치는 seed 또는 독립성 인증과 다르다. 같은 문서의 BEAM_TF
schema는 INT_BEAM/POL_BEAM을 **full-mission 파일에만** 명시한다.

[공식 simulation 문서](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php?title=Simulation_data)
§3.3.1은 HFI의 full/HM/OE 다섯 cut와300 IDs를 설명한다. 온도 353GHz dust input에
발견된10% color-correction bug에 대해서는 residual sky-subtraction에도 같은
template를 써서 공개 residual maps에는 영향이 없지만, 뒤에 공개된 corrected input
dust/fiducial과는 달라진다고 설명한다. 따라서 공개 foreground input 하나를 모든
residual realizations의 정확한 입력이라고 결합하는 것은 별도 검증이 필요하다.

[Planck2018 VIII §4.4](https://www.aanda.org/articles/aa/full_html/2020/09/aa33886-18/aa33886-18.html)는
2018 release에 HM FFP10 CMB가 없고 noise만 있으며, FFP9 HM CMB를2018 SMICA
weights로 합쳤다고 명시한다. FFP9/10의 seed는 같아도 effective beam 세부가 다르다.
이는 당시 release에 관한 원전 진술이며, 이후 다른 release의 존재를 배제하지 않는다.
[Planck2018 IV §§3.5,4.4](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html)는
고정된 실제-data weights로 noise/CMB를 전파하는 구성을 설명한다.
[Planck2018 VII §4](https://arxiv.org/abs/1906.02552)는 foreground residual과 noise mismatch의
영향이 분석할 통계량·스케일에 따라 달라질 수 있다고 한다. VIII는 lensing, VII는
isotropy 문헌으로 구별한다.

## 같은 하늘·split에 관한 구성적 결과

다음은 작은 이방성의 선형 응답, 고정된 좌표/마스크/weights, 평균을 제거한 latent
CMB `s`와 CMB에 독립인 nuisance를 가정한 **직접 유도**이다. 원래 estimator의
native mask→child mean→finite regression은 그대로 유지한다. split a의 coefficient를

```math
z_a=G_a R_a s+G_a(n_a+f_a)
```

로 쓴다. R_a는 물리적 beam/map response, G_a는 이미 정의된 유한 관측 연산자이다.
전경/잡음 상관을 포함한 nuisance covariance를 N_ab라 하면

```math
Cov(z_a,z_b)=G_a R_a C_s R_b^\dagger G_b^\dagger+G_a N_{ab}G_b^\dagger.
```

같은 G에서 d=(z_1-z_2)/2를 구성하면 CMB 항은

```math
Cov_s(d)=\tfrac14 G(R_1-R_2)C_s(R_1-R_2)^\dagger G^\dagger.
```

따라서 같은 하늘이라는 사실만으로 split 차이에서 CMB가 정확히 사라지지는 않는다.
응답 차이까지 통제해야 한다. scalar 예에서 R1=1,R2=1+epsilon이면 잔여 분산은
epsilon² Var(s)/4이다. 각 split에 서로 독립 CMB를 넣으면 대신
[1+(1+epsilon)²]Var(s)/4를 얻는다. epsilon→0에서 전자는0, 후자는Var(s)/2이므로
split을 독립 sky로 대체하는 오류를 정확히 드러내는 계산 가능한 검증 예가 된다.
noise도 같은 ID의 모든 split을 한 벡터로 유지해야 N_ab를 보존한다.

실행 가능한 다음 구성은 새로운 solver가 아니라 **이미 계산된 동일 seed CMB의
split response 차이와 같은 ID noise tuple을 원래 G에 통과**시키는 것이다.
선형 신호 조각과 noise tuple을 보존하면 full/HM/OE contrast를 통계량 앞에서
결합할 수 있다. 현재300 noise IDs나999 signal IDs의 단순 순열은 ensemble 크기
표시와 별개로 반복 사용된 nuisance를 공유한다. 실제 독립 단위를 정의한 뒤
cluster 단위 holdout/coverage를 설계해야 한다. 이것은 현재8pair를 다시 처리하라는
지시가 아니다.

weights가 관측 자료에서 추정된 \(\hat w\)라면 고정-weight simulation은 특정
\(\hat w=w_0\)에 대한 응답을 계산한다. 실제 검정의 marginal law와 일치하려면
selection/weight 추정의 조건부 타당성 또는 재추정에 따른 변화 통제가 필요하다.
이 구분은 [BeyondPlanck IV §3](https://www.aanda.org/articles/aa/full_html/2023/07/aa44958-22/aa44958-22.html)의
prior/posterior simulations와 correlation structure 구분을 재사용한다. 이번 검색은
이 원전을 SciSpace semantic search로 발견하고 limitations 열을 조회한 뒤 출판본
원문으로 확인했다. “조건부 simulation과 반복 실험의 law가 다르다” 자체를 새
발견으로 주장하지 않는다.

형태 축의 안정성은 coefficient 변화량만으로 보장되지 않는다. 축을 정하는 대칭
tensor의 spectral gap이 닫히면 작은 response 변화도 큰 축 회전을 만든다. 따라서
다음 유한 평가에서는 coefficient norm bound와 gap을 함께 기록하고 degeneracy를
UNKNOWN으로 유지하는 것이 구성적이다. 모든 통계량에 공통 Lipschitz 상수를
가정하거나8행 rank7 covariance를 invert할 이유가 없다.

## B02/V03와 선행 연구 비교

[Saadeh etal2016 MNRAS](https://doi.org/10.1093/mnras/stw1731)와
[PRL117,131302](https://doi.org/10.1103/PhysRevLett.117.131302)는 ABSolve/ANICOSMO2로
I,V,VII0,VIIh의 scalar/vector/regular·irregular tensor와 편광을 이미 분석했다.
[2007 Pontzen–Challinor](https://arxiv.org/abs/0706.2075)도 Bianchi 편광 선행 연구다.
따라서 “최초 polarized Bianchi 검정”, “최초 all-shear CMB 검정”은 이번 프로젝트의
새로움이 아니다. 가능한 차별점은 검증된 외부 전이를 받아 local-endpoint와 global-history를
구별하고 동일 선택법의 통계량까지 연결하는 실제 결과에 있다. 아직 그 전이가 없다.

[Zenodo48653](https://zenodo.org/records/48653)은 WMAP MC chains/plots,
[48654](https://zenodo.org/records/48654)은 scalar/vector/tensor/SVTT animations이다.
후자는 colormap·투영·스케일이 들어간 영상이므로 정확한 complex alms를 되복원하는
입력으로 삼지 않는다. [저자 AniCosmo 페이지](http://www.jasonmcewen.org/project/anicosmo/)는
현재 code가 아직 공개되지 않았다고 한다. 이 저자 페이지와 저장소 검색으로 atlas
전반의 비존재를 결론 내리지 않는다. 이미 조사한 AniCLASS9312177b notebook은
반복 실행/검사하지 않았다.

신뢰할 수 있는 canonical template 계수
\(t^{X,k}_{\ell m}(\vartheta)\), X=T/E/B, mode k가 도착하면 선형 영역에서

```math
a^{X}_{\ell m}(q,R,\vartheta)
=\sum_k q_k\sum_{m'}D^\ell_{mm'}(R)t^{X,k}_{\ell m'}(\vartheta)
```

로 orientation과 mode amplitude를 유한 합으로 확장할 수 있다. sparse canonical-m
데이터도 명시적 symmetry와 완전한 mode support가 보증되면 all-m representation으로
옮길 수 있다. 이 회전은 primordial IC나 global-history 전달을 생성하지 않으며,
서로 다른 회전이 독립 physical atlas entries를 추가하지도 않는다. 필요한 provenance는
IC/시작 epoch·물질/재이온화 모형·shear 정규화·단위·handedness·spin/frame·ell cutoff·
이미 포함된 beam이다. 곡선/그림/최적합 parameter chain만으로 이 계수를 채우지 않는다.

## 다음 구체적 인계

1. 새 weights archive의 기존 receipt/hash를 재사용한다. 원본을 다시 GET하지 않는다.
2. 필요할 경우 고정된 소수 IDs의 네 split noise만 취득하고 기존8pair와 구별한다.
   다운로드 전/후 총량은 대략 각 파일603.98MB의 table data라는 헤더 추정치이며,
   HTTP Content-Length 또는 전체 hash가 아직 없다고 기록한다.
3. FFP9 HM signal의 실제 공개 경로·same-seed mapping·effective-beam 차이를
   원래 estimator에서 정량화할 수 있는 외부 payload를 확보한다. NERSC portal 인증
   요구를 no-login으로 바꿔 부르지 않는다.
4. B02/V03는 solver 실행 없이 사용 가능한 serialized T/E/B template와 위 provenance를
   찾거나 공급받는다. 이번 검색은 데이터 미확보 결과로 종료한다.

이번 산출물은 DAG17/42나 여섯 원고 NOT_READY 상태를 변경하지 않는다.


게시물의 source_summaries에는 HTTP/JSON 접근 증거만 포함한다. CMB_maps.html, Simulation_data.html 및원본archive는작업원본이며재배포하지않는다. 해당공식URL과본문의절이원전참조다.
