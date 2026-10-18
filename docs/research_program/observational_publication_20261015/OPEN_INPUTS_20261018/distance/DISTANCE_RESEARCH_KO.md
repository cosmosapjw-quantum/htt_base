# 거리·천문측량 공개 입력: 실제 확보한 GBT 표본 결과와 다음 계산

2026-10-18. Owner `htt`; 선택 범위 R2/R4/R5, 자료·관측 연산자 구성에 한정. 현재 scientific status `DIAGNOSTIC_ONLY`. 원래 H02/S02/K03/K04 acceptance와 17/42 상태는 변경하지 않는다. solver/ODE, full clone/worktree, 출판은 수행하지 않았다. 보존된 RESUME/H02 원천 분석을 읽고 완료된 20-fit/TF join을 재실행하지 않았다. 이 하위 작업에서는 부모 지시에 따라 추가 자식을 만들지 않았다.

가장 유용한 새 입력은 **628개 실제 GBT 관측 대상의 비검출·혼동·품질 결과표**다. 기존 TF 자료는 J/ApJ/**902**/145이며 904/114가 아니다. 새 표는 [Dupuy et al. 2021, Toward Cosmicflows-4: The HI data catalog](https://www.aanda.org/articles/aa/full_html/2021/02/aa39025-20/aa39025-20.html)의 [CDS J/A+A/646/A113](https://cdsarc.cds.unistra.fr/ftp/J/A+A/646/A113/ReadMe)이다. 두 표의 `.gz`는404였고 일반 `.dat`는200이었다. 원천을 보존하고 byte-by-byte schema로 실제 파싱했다.

| 실제 분류 | 628개 중 수 | 이미 관측된 표본 안의 비율 |
|---|---:|---:|
| TF용 linewidth error ≤20 km/s | 385 | 61.306% |
| 그 외 detected quality | 22 | 3.503% |
| 혼동 sentinel e_W50=100 | 29 | 4.618% |
| 비검출 sentinel e_W50=500 | 192 | 30.573% |

Table4 1274개는 GBT385/Nançay889다. **Table4의 GBT PGC 집합이 table2 e_W50≤20 PGC 집합과 정확히 같다.** 628/1274행,63/32폭,각표PGC유일성,분류의 서로소·전체성,385개 집합 동등성을 확인했다. 407은 비검출192/혼동29를 제외한 행 수다. `HI_COHORT_RESULT.json`은 네 결과별 PGC와 telescope별 PGC, 실제 오류코드 histogram을 담는다.

CDS ReadMe에는 GBT628 중685 adequate라는 잘못된 설명문이 있다. 실제385, journal385, table4GBT385와 구별해 그대로 기록했다. 또 journal의 예시 table4에는 Source bibliography가 있지만 **배포 CDS table4에는 Tel만 있고 Source 열이 없다.** 따라서 telescope는 연결할 수 있어도 전체 ADHI/ALFALFA contributor/version genealogy를 복원했다고 부르지 않는다. 100/500은 물리 오차가 아닌 sentinel이다.

분석은 `python analyze_hi_cohort.py --raw-root <원천폴더> --output-dir <출력폴더>`로 재현한다. 원천 파일명은 `cf4_hi_readme.observed`, `cf4_hi_table2_plain.observed`, `cf4_hi_table4_plain.observed`이며 실행 시작에 세 SHA를 검사한다. 결과 그림은 `HI_GBT_OUTCOMES.png/.pdf/.svg`이다. 전체 원천 checksum·정확 URL·실제GET와 부분GET 차이는 `DATA_DISTANCE.json`과 `source_probes.json`, `followup_probes.json`에 있다. 실행은 exit0; 독립검토는 부모 담당이다.

## 구성한 다음 관측 연산

GBT 결과를 기존 frozen TF table1/table4 및 CF4 PGC→1PGC로 연결하면, 관측대상 T=1에 조건부인 품질 경로를 실제로 계산할 수 있다. 기존 그룹 window weight를 w_g라고 하고 outcome a의 group support I_ga=1{그룹 g에 a의 PGC가 하나라도 있음}를 구성하면

\[
 f_a(W)=\frac{\sum_g w_g(W)I_{ga}}{\sum_gw_g(W)}
\]

이다. 하나의 그룹이 여러 outcome에 연결될 수 있으므로 f_a의 합을1로 강제하지 않는다. 새 데이터가 제공하는 것은 `P(outcome|T=1, 이 GBT programme)`의 유한 표본 구성이다. CF4 전체 `P(T=1|방향,z,광도,HI,...)`의 정규화는 제공하지 않는다. 이 차이를 유지한 상태에서 rejected-target의 방향/깊이 편중, TF 표에 들어오지 않은385 accepted 대상, 비검출군이 다른 방법으로 CF4에 존재하는지 검사할 수 있다. 실제 join은 이 export에 frozen raw가 없어 NOT_RUN이며 부모가 기존 raw를 재사용한다.

완전한 선택 likelihood는 관측 y와 잠재 x에 대해

\[
 p(y\mid T{=}1,\theta)=\frac{\int p(y\mid x,\theta)s(x)p(x\mid\theta)dx}{\int s(x)p(x\mid\theta)dx}
\]

를 요구한다. 628개 결과는 이 식의 targeting s(x)를 결정하지 않는다. 이것은 실제 데이터 범위의 구분이며 우주론적 strong no-go 정리가 아니다. NG1–NG7 신규 no-go admission은 주장하지 않는다.

## 최소 후속 확보 우선순위

1. **위 GBT cohort와 기존902/145/CF4 조인**이 가장 작고 즉시 쓸 수 있다. 새로운 global p-value 없이 선택 구성의 실제 공백을 줄인다.
2. **Pantheon+ data+full covariance**: 공식 [DataRelease 고정 commit c447f0f](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b/Pantheon%2B_Data/4_DISTANCES_AND_COVAR). Commit API로 commit과 tree를 구별했다. dat를 실제579283bytes 받았고1701행/1543uniqueCID,calibrator77행43CID,SH0ES-HF277행을 계산했다. Stat+Sys는 총33284960bytes 중65536bytes 부분GET206, 첫 줄1701까지 관찰했으며 전체 다운로드했다고 쓰지 않는다. STATONLY31827416bytes는 API path/size 관찰이다. 동일SN 여러 관측의 off-diagonal와 Cepheid-host covariance를 포함하므로 대각 plotting error로 대체하면 안 된다. VPEC/VPECERR,zHD,zCMB,zHEL,calibrator flags,RADEC가 있어 redshift/frame·survey split sensitivity에 실제로 쓸 수 있다. 이 covariance를 CF4 optical→kinematic mapping 또는 임의 angular calibration covariance라고 바꾸지 않는다.
3. **Pantheon+ simulations**: 실제 `SIM_0001.FITRES.gz`514308bytes를 받고3235SN행, SNANA v11_04e, truth SIM_DLMAG/SIM_VPEC를 읽었다. 10realizations/BS21/LambdaCDM/SALT2는 release README다. FITRES에는 RA/DEC가 없어 이것만으로 directional null을 못 만든다. 실제 LOWZ input은 SIMLIB/KCOR/SEARCHEFF를 `$PS1_ROOT`로 참조한다. 공개 예시는 있지만 완전한 독립 실행 입력을 확보한 상태가 아니다. 기존2GB biascor는 연락 요청 경로이며 anonymous downloadable로 세지 않았다.
4. **Gaia full CRF3 + per-source PM covariance**: [ESA official crossmatch](https://www.cosmos.esa.int/web/gaia/gaia-crf3-cross-match-table)의 ecsv.gz는 fullmembership이며17externalcatalogue flags를 가진다. 56064899bytes중65536bytes만 읽고 partialgzip header를 실제 해석했다. astrometry는 별도 `gaiadr3.gaia_source`와 source_id join해야 한다. ARI 공개TAP의 TOP2 join을 실제200/601bytes로 확인했다. 전체 query는 JSON에 있고 full UWS async execution은 NOT_RUN이다. CRF3 expected1614173, fiveparameter1215942는 [Klioner et al. 2022 §3.4/AppendixC](https://www.aanda.org/articles/aa/full_html/2022/11/aa43483-22/aa43483-22.html)의 원전값이다. DR3와 EDR3 astrometry는 같아 독립 반복이 아니다. 기존4756 frame-rotator sample은 재실행하지 않는다.
5. **독립 radio VSH 비교**: [Truebenbach & Darling2017](https://arxiv.org/html/1710.02099)의 [J/ApJS/233/3/table6.dat](https://cdsarc.cds.unistra.fr/ftp/J/ApJS/233/3/table6.dat)를 실제99085bytes/713행 받았다. PM errors,redshift,epochspan은 있으나 PMRA–PMDec correlation 열은 없다. Gaia와 독립 관측이지만 reference-frame NNR와 jet systematics를 가진다. 원전은 NNR로 secular drift 일부가 제거될 수 있음을 명시한다. 측정 독립과 frame prior 독립을 혼동하지 않는다.

Gaia 각 source의 접평면 covariance는 공개 column으로
\[
 C_i=\begin{pmatrix}\sigma^2_{\mu_{\alpha*}}&\rho_i\sigma_{\mu_{\alpha*}}\sigma_{\mu_\delta}\\\rho_i\sigma_{\mu_{\alpha*}}\sigma_{\mu_\delta}&\sigma^2_{\mu_\delta}\end{pmatrix}
\]
를 만들 수 있다. µα*=µαcosδ convention과 mas/yr→µas/yr1000배를 고정해야 한다. `u_i=P_i a/c + ω×n_i + Σ_{l≥2}(E_lm S_lm+B_lm T_lm)+ε_i`의 저차 VSH를 후보로 둔다. Formal C_i는 source간 scanning/frame covariance를 주지 않는다. Gaia T1은 frame construction에서 억제되고 S1은 Solar-system acceleration glide다. 새 fullsample 또는 VLBA fit가 K03의 cosmic curl/acceleration/tilt 물리transfer를 자동 제공하지 않는다. Published VSH spectrum/Fig10은 동일 Gaia자료의 기준값이며 독립관측 null이 아니다.

[CF author release](https://projets.ip2i.in2p3.fr/cosmicflows/)의 original grouped64³ velocity FITS는 총3150720bytes의 일부만 확인했다. Author의 velocity/error×52와 SGZ/SGY/SGX 문구를 따로 보존했으며 FITS actual axis/units 검증 전에 적용하지 않는다. CF4 자체로 추정한 flow이므로 독립 holdout이 아니며 voxel std는 joint covariance가 아니다. 새 CF4++167773716byte NPZ는 rangeGET만 했고 Oct13,2026 vr_data correction 공지를 기록했다. Link label/script는 `new_CF4pp_mean_std_grids.npz`, 실제 href는 `CF4pp_mean_std_grids.npz`라 identity를 구별해야 한다. 예제는 밖의 좌표를 clip하므로 downstream은 cube밖 좌표를 먼저 reject해야 한다. 이번에는 실행하지 않았다.

Exa는 위 primary release/catalogue 링크와 VSH/NNR의 원전 문맥을 찾는 데 썼고, SciSpace는 Gaia acceleration 및 6dFGS fundamental-plane 원전 검색에 실제 사용했다. 6dF/SDSS 전체 catalogue를 추가로 늘리는 대신 새628target ledger에 수렴했다. Web 도구의 ESA451/A&A403과 shell HTTPS의 실제 성공은 별도로 기록했다. 공개 자료가 없다는 보편 부정은 하지 않는다. 이번에 닫힌 것은 bounded selected-target outcome와 released-data acquisition 경로이며 H02/S02/K03/K04의 물리 mapping/전체법칙은 남는다.

부모의 후속 실제 확보는 별도 `OPEN_INPUTS_20261018/PANTHEON_INPUT_RESULT.json`에 있다. Stat+Sys 전체33284960bytes SHA `abf806d966485e64afdb359c87bffc0ecc00d05eff0a31ced66f247385df0fdc`를 받았다. 원행렬 max asymmetry는3.0000000000038676e−8mag²이며1e−10 대칭성 검사는 실패로 보존됐다. **대칭부에 한한** min eigenvalue=.0008027816532256341은 양수다. 이는 원행렬 대칭성을 증명하거나 likelihood covariance로 채택한 것이 아니다. 내 부분GET 기록은 그대로 남기고 부모 전체확보 근거를 JSON에 추가 연결했다.
