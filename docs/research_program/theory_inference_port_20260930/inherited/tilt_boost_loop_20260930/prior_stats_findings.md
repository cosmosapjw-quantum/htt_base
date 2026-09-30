# Tilt / non-tilt / endpoint observer motion: 선행 근거와 부분식별 명제

작성일: 2026-09-30 KST. 담당 범위는 선행 문서 읽기, 정의 정비, 직접 통계·대수 유도다. 실관측 fit, 최신 저장소 감사, 형식 커널 검증, 기존 판정 승격은 수행하지 않았다. 아래 새 명제는 독립 심사 전 `derived`이며 최종 승인 문서가 아니다.

## 1. 실제 읽은 선행 근거와 계승 한계

- `bianchi_identification_20260929/prior_audit.md`: 동일 full-data-law fibre, MES quotient, 기존 I1/I2/I3 범위.
- `bianchi_identification_20260929/CLAIMS.json`: BIC-01–08의 전제와 판단. BIC-07은 관측→공간 tensor/derivative 응답 결손, BIC-08은 실자료 분류 미실행이다.
- `bianchi_identification_20260929/REPORT_KO.md`, §§7–8: endpoint와 global tilt의 차이, calibrated outer-set exclusion.
- `report_20260929/sources/repo/docs/research_reports/theory_synthesis_20260913/REPORT.md`, §§2–4, 12–13: RO/RM/MO 세 쌍, counter-streaming, exact local boost, processed nuisance quotient, depth response. 이 원문 일부 절은 단위벡터 및 c=1이므로 이 문서의 물리 four-velocity와 자동 혼합하지 않는다.
- `.../theory_packs/T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md`, §§1–3: 절대 blackbody thermodynamic temperature의 exact d=1 Lorentz pullback. 고정 출처는 PR442, commit `29427a1f7f2c5d46e43ffe03053c4ac13e969228`이라고 원문이 기록한다. 이번에는 현재 원격 pin을 다시 감사하지 않았다.
- `.../theory_packs/T6_WU011_PROCESSED_RESPONSE_QUOTIENT_THEOREM_PACK.md`, §3: boost → beam/pixel → map synthesis → joint low-mode fit → commonization의 처리 순서.

선행 내용은 이미 local-observer transformation이 global matter tilt의 transfer function이 아니라고 명시했다. 따라서 다음 결과는 이 구별을 폐기하지 않고, 어떤 추가 입력에서 구별이 가능한지를 정식화한다.

## 2. 분류 대상은 세 가지 배타적 label이 아니다

Signature는 (-,+,+,+), 미래방향 물리 four-velocity는 각각 제곱 -c²이다. N은 선언된 공간균질 foliation의 normal, U는 명시한 물질 성분의 four-velocity, O는 관측 사건의 observer four-velocity다. radiation reference R은 존재·정의가 따로 정해졌을 때만 도입한다. 총 복사 stress의 zero-flux eigenframe과 모든 복사 multipole가 등방적인 frame은 같은 조건이 아니다.

어떤 두 unit physical four-velocity X,Y에 대해서도

\[
\gamma_{XY}=-\frac{g(X,Y)}{c^2}\ge1,\quad
\eta_{XY}=\operatorname{arcosh}\gamma_{XY},\quad
\beta_{X|Y}^{a}=\frac{X^a}{c\gamma_{XY}}-\frac{Y^a}{c},
\]
\[
Y\cdot\beta_{X|Y}=0,\qquad
\beta_{X|Y}^{2}=1-\gamma_{XY}^{-2},\qquad
X=\gamma_{XY}(Y+c\beta_{X|Y}).
\]

ηは無次元、βも無次元であり、物理速度は cβ である。ηやγは同一点の tetrad 変更で不変だが、参照する物理ベクトル Y を変更すれば別の量になる。

基本の二軸は

1. **homogeneous-normal に対する物質 tilt**: η_UN。
2. **選んだ物質 U に対する observer endpoint motion**: η_OU。

である。β_ONを記録してもよいが、それを自動的にβ_OUと同一視してはいけない。

| 物質状態 | Observer | η_UN | η_OU | 解釈 |
|---|---|---:|---:|---|
| non-tilted | U-comoving | 0 | 0 | U=N=O |
| non-tilted | Uに対してmoving | 0 | >0 | endpoint motionのみ |
| tilted | U-comoving | >0 | 0 | O=U≠N; global tiltあり、局所物質に対する余剰運動なし |
| tilted | Uに対してmoving | >0 | >0 | tiltとendpoint motionが共存 |

「local boost」が単なる tetrad の書き換えなのか、Oを別の物理的観測者に変更する操作なのかも分ける。前者はγ_UNを変えず、後者でも同じ物理状態中のUとN自体は変わらない。

局所値η_UN(p)>0はその点の非直交性を示す。G3がU,Nを保存するならその軌道全体でも同じである。一方η_UN(p)=0だけで時間区間全体のnon-tilted性は証明できない。定義域Dの分類には
\[
\eta_{UN,D}^{\max}=\sup_{p\in D}\eta_{UN}(p)
\]
または明示した動力学・初期値一意性が必要である。sup=0がD上のnon-tiltedである。遠方の接空間のベクトル成分をそのまま減算してはならない。比較には輸送規則または各点で定義した不変量を使う。

## 3. Observer orbit の正確な null とその限界

同一observer eventでの入射 photon phase-space fieldを f、endpoint Lorentz pullbackを B_b、宣言した装置・mask・selection・推定処理を P とする。baseline physicsに許された集合を F_0 とすれば
\[
\mathcal M_{\rm endpoint}
=\{P[B_bf]: f\in\mathcal F_0,\ |b|<1\}.
\tag{S1}
\]
同じbは同一eventの全direction/frequency/channelに適用する。別channelごと、別redshift-binごとに独立bを選んだ和集合ではない。周波数重み、screen basis、aberration、Doppler因子を各observableに正しく反映する。

選択を含む観測の定義域も固定しなければならない。boostでredshiftが変われば観測redshift-binへの所属は変わる。従って処理済みbinだけに一定dipoleを引く操作は一般に式(S1)と同値でない。同じphoton/sourceと同じemitter velocityを保持するとobserver energyの変換から
\[
E'_o=D_oE_o,\qquad 1+z'=(1+z)/D_o
\]
が直接従う。これは座標binのラベルを固定したままの比較ではない。

有限観測時間を持つastrometryでは、単一eventのbを数年間一定と仮定しない。observer worldline、加速度、tetrad transport、ephemerisを指定したB_{b(\tau)}と時間積分・fitをPに含める。

### 3.1 単なる non-tilt と「異方性がboostのみ」は別仮説

U=Nは、shearやanisotropic curvatureやintrinsic radiation anisotropyを0とする条件ではない。従って「non-tilted Bianchi + observer motion」の許容集合と「等方なrest radiationがobserver motionで異方的に見える」の集合は異なる。後者を純粋運動学的CMB anisotropy仮説と呼ぶなら、F_0にその等方性・スペクトル条件を明記しなければならない。

### 3.2 自由なintrinsic skyを許すとendpoint速度は同定不能

F_0がすべての正の絶対blackbody温度場であり、理想full skyが観測されたとする。任意bについてB_bは正の温度場上の可逆写像なので
\[
T_{\rm intrinsic}^{(b)}=B_b^{-1}T_{\rm observed}>0
\]
を選べる。このradiation response modelの中では全bが同じobserved skyを説明する。同じdetector lawを適用すれば同じfull data lawでもある。これは大きいデータ量では解けず、intrinsic familyへの物理制約、独立のvelocity/reference情報、または別観測の応答が必要である。

ただし任意の逆変換したskyが任意の指定Einstein/matter/Bianchi source模型で実現するとは主張しない。F_0をそのphysical imageに狭めた後に、同じfiberが残るかを改めて判断する。

### 3.3 Exact inverse-temperature monopole–dipole criterion

新しい直接導出: 正の絶対方向別blackbody温度T_o(n_o)が、ある一つの等方blackbody T_0>0をendpoint boostして得られるための必要十分条件は
\[
\frac1{T_o(n_o)}=a+b\cdot n_o,\qquad a>|b|.
\tag{S2}
\]
前提は理想full skyとd=1のthermodynamic temperatureである。T5のexact formula
\[
T_o(n_o)=\frac{T_0}{\gamma(1-\beta\cdot n_o)}
\]
から必要性は a=γ/T_0, b=-γβ/T_0。逆に式(S2)なら
\[
\beta=-b/a,\quad
T_0=(a^2-|b|^2)^{-1/2},\quad
\gamma=\frac{a}{\sqrt{a^2-|b|^2}}
\]
で元の式を再構成する。a,bの単位は K⁻¹。β→0ではb→0かつT_o=T_0。

したがってinverse-temperatureのℓ≥2残差は、この限定されたpure isotropic-radiation endpoint仮説へのexact consistency diagnosticとなる。元のT自体には有限boostによりquadrupole以上が存在するので、Tの高次multipoleゼロを要求してはいけない。

この結果が識別するのは**radiation-isotropy frameに対するobserver速度**であり、UまたはNを独立に与えなければη_UNの識別ではない。またrest spectrumが非Planck的・方向依存なら適用しない。絶対monopoleを除いたmap、foreground-cleaned残差、beam/mask後の逆温度に式(S2)を無修正で適用してはいけない。noisy Tを単純に逆数へ変換するとbiasと共分散が変わるため、統計実装はTまたはphoton dataのforward lawでcalibrateする。

## 4. 型×tilt×observerの共同部分識別

物理状態θには(g,G3,N,U,O,radiation,source history,boundary,observation operator,nuisance)を同時に含める。type label tは宣言したG3のLie algebra classであり、metric単独の常に一意なラベルではない。物質のtilt label aとobserver label bは前節の定義に従い
\[
\mathscr L(\theta)=(t,a,b)
\]
を作る。一つのcomplete stateが複数G3を許すならset-valued labelにする。異なるfoliation Nを認める場合、tiltの相手も変わるのでNのprovenanceをlabelに保持する。

### 4.1 全法則を用いる一般形

各θに対し統計モデルP_θと受容域A_θが
\[
P_\theta\{Y\in A_\theta\}\ge1-\alpha
\]
を満たすとする。反転した
\[
\widehat\Theta_\alpha(Y)=\{\theta:Y\in A_\theta\},\qquad
\widehat{\mathscr L}_\alpha(Y)=\bigcup_{\theta\in\widehat\Theta_\alpha(Y)}\mathscr L(\theta)
\tag{S3}
\]
はtrue stateのすべての許容ラベルを確率≥1−αで保持する。証明はθ_trueが\hatΘに入る事象をlabel写像した包含だけである。これによりBianchi型と二つの速度軸を別々に推定して誤って組み合わせることを避ける。

### 4.2 Sound outer imageで計算する形

同一観測feature空間のmean等をm(θ)、label-cell ℓの実imageをM_ℓ、sound enclosureをM_ℓ^outとする。真のmをuniform probability≥1−αで覆うC_α(Y)があれば
\[
\widehat L_\alpha=\{\ell:C_\alpha(Y)\cap M_\ell^{\rm out}\ne\varnothing\}
\tag{S4}
\]
が同じ保持保証を持つ。未知初期skyやsource velocity、有限深さ近似誤差、frame calibration、normal/source変換の誤差は外集合に入れる。

特定ラベルの空交差をcertifyすればその条件下で排除できる。非空交差はrealizationの証明でなく、optimizerの探索失敗は空集合証明でもない。M_ℓ^outのsoundnessも確率1−δなら保証は少なくとも1−α−δに下がる。meanだけに基づく(S4)はcovarianceまたは高次lawの区別を失うことがある。

pure endpoint仮説の排除はC_α∩M_endpoint^out=∅という特殊例である。これはbaseline family、systematics、source assumptionsの合成仮説の排除であり、それだけで「global tiltが原因」と確定しない。intrinsic anisotropy、inhomogeneity、別物質、calibration不備なども宣言した候補宇宙に含める必要がある。

## 5. Exact zeroと実用的non-tiltの区別

各ペアについてd_XY=γ_XY−1≥0を用いると、極小速度でも定義上の違いを明確にできる。
\[
|\beta_{X|Y}|^2=\frac{d_{XY}(d_{XY}+2)}{(1+d_{XY})^2},\qquad
\eta_{XY}=\operatorname{arcosh}(1+d_{XY}).
\]
共同\hatΘ_α上で
\[
[d^-_{UN},d^+_{UN}]=[\inf_{\hat\Theta_\alpha}d_{UN},\sup_{\hat\Theta_\alpha}d_{UN}]
\]
等を計算する。ηやdomain-supでも同じ写像ができる。

- d^- >0ならexact non-tiltを排除できる。
- 事前に科学目的から選んだd_tolに対してd^+≤d_tolなら、その観測精度・前提でpractical equivalenceを主張できる。
- 0が区間内にあるだけならnon-tiltを確立したのではなく、排除できていない。
- d^-=d^+=0が得られるのは厳密な制約で0が強制される場合等であり、通常の有限精度測定から自動的には出ない。

d_tolまたはη_tolに普遍的な数値はない。chosen datasetの分解能、物理的許容誤差、domain Dに依存する。閾値を事後的に選んで元のcoverageを保存したと主張しない。Exact nullは境界であり、type strataも交差するので、任意のlikelihood ratioに通常のχ²近似を自動適用しない。

## 6. Redshift/depthが追加する情報の条件

線形化された共通模型を
\[
Y_j=L_jb+G_jt+N_j\nu+\varepsilon_j
\]
とし、全depthを一つのjoint vectorにstackする。全noise lawを固定し、二つの許容状態の差(h_b,h_t,h_ν)が
\[
Lh_b+Gh_t+Nh_\nu=0
\tag{S5}
\]
を満たせば同じfull data lawになる。Gaussian meanだけ同じでもcovarianceがθで変わるならこの結論は出ない。

すべてのjでL_j=G_jなら(h,−h,0)はどれだけdepthを増やしてもkernelに残る。逆にnuisance quotient後の実際のL,Gが異なる方向を持てば新しい識別情報があり得る。重要なのは実応答であり、深いsourceでdipoleが続くことや単なるbin数ではない。

このlinear criterionは許容variationに適用する。非線形Einstein/Lie/matter制約でfiberが縮む場合までrank不足を普遍的no-goに拡張してはいけない。有限velocityの合成はLorentz変換を使用する。一階のβ_RO≈β_RM+β_MOをexactなvector和として使わない。非共線boostではspatial frameのWigner回転も管理する。

## 7. MES/tensor統計への接続と禁止すべき読み替え

同一状態・同一観測operator・同一referenceで定義したtensor feature φ(θ)に対するbody B(θ)のgauge γ_B、margin 1−γ_B、方向support Fは、前提に対する利用率を表す。異なるlabelごとに異なるB_ℓを使う場合、同じ数値γ=0.5は同じlikelihood、p値、posterior oddsを意味しない。

label比較の元データは共通feature spaceまたは明示した同値変換でそろえる。Sample-dependent normalizationはデータ依存性と推定誤差をjoint lawへ入れる。可逆な再尺度化は情報量を増やさず、scalarizationは減らし得る。γ_{pB}の最小algebraic liftとphysical tilt/observer fiberの交差を混同しない。

Πは指定された共同法則の上でのみ確率量にする。G_Fのdepth coherenceはendpoint/global responseの違いを表示する補助量として有用だが、共通skyや重複sourceのcross-covarianceを省略したままglobal tiltの有意度にしてはいけない。

## 8. この担当からの実行順序提案

1. `N_authority`, `U_component`, `O_worldline`, `R_definition`, `domain_D`, `velocity_pair`を入力契約の必須fieldにする。pair不明のbetaを受け付けない。
2. 二軸のrapidityとBianchi action labelの共同allowed setを基本出力にする。Exact-zero判定とpractical-equivalenceを別fieldにする。
3. まず(S2)を解析的負例・正例で確かめる。ただし実mapに適用する際はmonopole・spectrum・foreground・instrument処理を入力として固定する。この段階のfitはradiation-frame速度のものである。
4. 実観測pipelineからendpoint responseとphysical tilt responseを別々に供給し、同一joint law・同一source selectionで(S3)/(S4)に接続する。pure endpoint rejectionとpositive tilt identificationを別判定にする。
5. I3のframe/source/finite-depth入力が満たされるまでGaia等をfull kinematic tensor入力として扱わない。総flux=0からすべてのcomponent non-tiltとも結論しない。

本稿だけではどの実データもtilted/non-tilted/boostedへ分類していない。既存I2 `DEFENDED_CONDITIONAL`、I3 `HOLD_INPUT_INCOMPLETE`、BIC-07/BIC-08の観測側未完了を保持する。
