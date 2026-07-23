#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARDS = ROOT / "pr_cards"
DOCS.mkdir(exist_ok=True)
CARDS.mkdir(exist_ok=True)

HOSTILE = [
    ("H3-01", "Dependency theatre", "외부 패키지 수가 늘어도 기존 계산을 wrapper로 재현할 뿐이면 과학적 독창성은 0이다. package count가 evidence count로 오인될 위험이 크다."),
    ("H3-02", "False independence of external codes", "CAMB, CLASS, CCL, emulators와 여러 map package가 같은 perturbation equations, cosmological priors와 upstream data를 공유하므로 코드 간 agreement를 독립 검증으로 셀 수 없다."),
    ("H3-03", "Version, license and API drift", "빠르게 변하는 JAX·S2·SBI 생태계를 pin하지 않으면 결과와 gradient가 재현되지 않으며, 라이선스 조건을 놓치면 공개 패키지 자체가 불가능하다."),
    ("H3-04", "Fail-open optional dependencies", "optional package import 실패 때 toy fallback을 조용히 사용하면 production 결과가 외부 oracle을 거친 것처럼 보이는 false green이 된다."),
    ("H3-05", "Tool-selection multiplicity", "수십 개 statistic·simulator·inference engine 중 잘 작동하는 것만 고르면 package selection 자체가 look-elsewhere effect다."),
    ("H3-06", "Toy DGP masquerading as cosmology", "dependency-free shell mock은 software test에는 유용하지만 실제 SW/ISW/Doppler, reionization, selection physics를 포함하지 않으므로 cosmological conclusion을 지지할 수 없다."),
    ("H3-07", "Shared FLRW assumption", "CAMB·CLASS·nanoCMB는 FLRW perturbation theory를 전제로 하므로 global anisotropic geometry 또는 Bianchi tilt를 검증하는 oracle이 아니다."),
    ("H3-08", "GLASS/lognormal limitations", "GLASS의 빠른 shell mock은 저차 통계와 비선형 velocity·rare structure를 충분히 재현하지 않을 수 있어 local-structure dipole와 kSZ small-scale coupling을 과소모델링할 수 있다."),
    ("H3-09", "The phrase redshift-dependent CMB pole is ill-defined", "우리는 한 위치에서 하나의 CMB sky만 본다. shell contribution, cumulative line-of-sight pole, remote dipole field, remote quadrupole field를 구분하지 않으면 서로 다른 object를 같은 pole(z)로 부르게 된다."),
    ("H3-10", "Pole definition non-uniqueness", "maximum angular-momentum axis, minimum axis, multipole vectors와 area normals는 동일하지 않다. 결과가 pole definition 선택에 따라 바뀔 수 있다."),
    ("H3-11", "Eigenvalue degeneracy instability", "low power 또는 nearly degenerate power tensor에서는 작은 noise·mask 변화가 pole을 큰 각도로 회전시킨다. pole direction이 식별되지 않았는데 finite cone을 보고할 수 있다."),
    ("H3-12", "Mask and foreground rotation", "Planck mask, inpainting, monopole/dipole removal, foreground complexity와 component separation이 low-ell poles를 회전시킬 수 있다."),
    ("H3-13", "Planck component maps are not independent skies", "SMICA, Commander, NILC, SEVEM 일치는 독립 확인이 아니라 같은 sky의 pipeline sensitivity다. 이를 replicate count로 세면 과신한다."),
    ("H3-14", "Boost operator order and convention risk", "local Doppler modulation, thermodynamic temperature, aberration direction remapping과 beam/pixel effects를 동일 order와 convention으로 처리하지 않으면 local-boost signature가 잘못된다."),
    ("H3-15", "Phenomenological global tilt strawman", "간단한 fixed-axis injection을 global tilt로 부르면 실제 Bianchi/multi-fluid transfer보다 구분하기 쉬운 대안을 만들어 method performance를 부풀린다."),
    ("H3-16", "Arbitrary shell decomposition", "SW/early-ISW/late-ISW/Doppler를 redshift shell에 분배하는 방식과 cumulative convention이 pole trajectory를 바꿀 수 있다."),
    ("H3-17", "Shells are correlated and cosmic-variance limited", "redshift bins의 remote fields와 cumulative poles는 같은 primordial modes를 공유한다. 독립 bin으로 취급하면 유효 정보량을 과대평가한다."),
    ("H3-18", "kSZ optical-depth bias", "remote dipole reconstruction amplitude는 galaxy-electron cross-correlation과 optical-depth bias에 강하게 의존한다. pole와 amplitude를 cosmological velocity로 직접 읽을 수 없다."),
    ("H3-19", "pSZ is currently low signal-to-noise", "현재 Planck/ACT/unWISE/CIB remote-quadrupole constraints는 O(1) S/N 수준이므로, 강한 global-tilt 판정을 낼 정보가 없다."),
    ("H3-20", "kSZ/pSZ foreground and mean-field bias", "tSZ, CIB, Galactic foreground, mask mean field와 estimator monopole가 remote-field pole을 만들 수 있다."),
    ("H3-21", "Published remote-field products may be unavailable", "논문 결과만 있고 full reconstruction maps/code가 공개되지 않으면 exact data comparison은 재현 불가능할 수 있다."),
    ("H3-22", "Source superposition defeats single-label classification", "local boost, local structure, calibration and global mode가 동시에 존재할 수 있는데 single-class classifier는 가장 가까운 잘못된 source를 강제한다."),
    ("H3-23", "Model-list misspecification", "source library에 실제 mechanism이 없으면 evidence와 neural classifier 모두 confidence를 내면서 틀릴 수 있다."),
    ("H3-24", "SBI overconfidence", "neural SBI는 simulator와 training prior가 null direction을 닫아 좁은 posterior를 만들 수 있으며, identification이 아니라 model restriction을 학습할 수 있다."),
    ("H3-25", "Partial identification can be vacuous", "identified interval이 [0,1]에 가깝다면 정직하지만 과학적 leverage가 없다. favourable nuisance bounds를 골라 interval을 줄일 위험이 있다."),
    ("H3-26", "Adaptive scan multiplicity", "새 package, statistic, depth bin을 결과를 보며 추가하면 fixed-analysis p-value와 coverage가 무효가 된다."),
    ("H3-27", "Local LSS simulator mismatch", "CONCEPT/JaxPM/PySCo의 box size, resolution, force solver와 missing long modes가 bulk-flow/tilt identifiability를 바꾼다."),
    ("H3-28", "Cross-code agreement is not truth", "두 N-body code가 같은 initial conditions와 approximations를 사용하면 agreement가 common bias를 숨길 수 있다."),
    ("H3-29", "Storage and provenance creep", "100 GB ceiling 안에서도 partial downloads, cached files, generated maps와 summaries가 뒤섞이면 실제 input lineage와 재현성이 무너진다."),
    ("H3-30", "Track-I/Track-II leakage", "phenomenological coherent source 또는 FLRW remote field가 native Bianchi transfer인 것처럼 family/geometry claim에 소비될 위험이 있다."),
    ("H3-31", "Native solver adapter mismatch", "Bianchi solver가 다른 tetrad, harmonic phase, epoch, polarization convention을 쓰면 adapter가 수치적으로 작동해도 물리적으로 틀릴 수 있다."),
    ("H3-32", "Actual-data anomaly mining", "Planck pole, redshift bins, tracer와 source statistics를 사후 선택하면 local/global distinction이 새로운 anomaly catalogue가 된다."),
    ("H3-33", "Unoriented-axis ambiguity", "pole은 p와 -p가 같은 축이다. signed dipole, handedness와 unoriented quadrupole axis를 같은 alignment statistic에 넣으면 의미가 사라진다."),
    ("H3-34", "Benchmark novelty may be dismissed", "새 benchmark만 제시하고 실제 cosmological design 또는 data conclusion을 못 내면 methodology contribution이 niche software exercise로 평가될 수 있다."),
]

ADVOCATE = [
    ("A3-01", "Package-count가 아니라 scientific leverage gate를 도입한다. rank gain, source-confusion reduction, calibrated abstention, model-inadequacy discovery 또는 computational accessibility 중 하나가 없으면 plugin을 archive한다."),
    ("A3-02", "oracle lineage graph를 만들고 equation/data/author lineage가 겹치는 엔진은 correlated oracle로 처리한다. 독립성은 코드 이름이 아니라 derivation과 input graph로 정량화한다."),
    ("A3-03", "PR intake마다 exact release/commit, license, wheel/container digest와 official example hash를 고정하고 API drift mutation을 CI에 넣는다."),
    ("A3-04", "optional plugin은 explicit BLOCKED_PLUGIN_MISSING만 반환한다. toy core는 별도 reference-DGP type이며 external_result flag를 절대 받을 수 없다."),
    ("A3-05", "모든 package/statistic 후보를 predeclared spike family로 등록하고 evaluation holdout과 anytime-valid e-value를 사용해 도구 탐색 자체의 multiplicity를 제어한다."),
    ("A3-06", "reference DGP는 gate mechanics에만 사용하고 CAMB/CLASS/GLASS와 native solver로 단계별로 교체한다. binning instability 같은 실패를 expected blocker로 만들어 물리 kernel 없이는 promotion하지 못하게 한다."),
    ("A3-07", "Track I은 FLRW/source-systematics discrimination을 완결하고, global anisotropic transfer는 Track II native solver에서만 연다. 두 track 결과를 common latent cosmology에서 합쳐 원래 범위를 유지한다."),
    ("A3-08", "GLASS를 low-cost shell generator로 쓰되 PM/N-body and WebSky/HalfDome subset으로 response envelope를 검증한다. disagreement는 simulator-form nuisance로 identified set에 넣는다."),
    ("A3-09", "PoleBundle을 shell-source, cumulative-observer, remote-dipole, remote-quadrupole 네 타입으로 분리하고 arithmetic/likelihood bridge를 typed receipt로만 허용한다."),
    ("A3-10", "pole-definition family를 동시에 계산하고 definition-stable identified axis 또는 set-valued pole region을 보고한다. 한 definition의 유리한 결과만 선택할 수 없게 한다."),
    ("A3-11", "power-tensor eigen-gap을 axis identifiability statistic으로 사용하고 gap이 작으면 방향 대신 full tensor/axis cone 또는 UNDETERMINED를 반환한다."),
    ("A3-12", "mask/inpainting/foreground/component-separation을 nuisance family로 사전 등록하고 map-product union 위의 pole region과 source rank를 계산한다."),
    ("A3-13", "Planck map 간 일치를 pipeline robustness로만 보고하고 independent simulation/data replication과 구분한다. common-sky covariance를 명시한다."),
    ("A3-14", "repo의 exact pixel-space boost operator, analytic first-order kernel, independent map remapping을 3-way cross-check하고 amplitude/direction mutation이 statistic을 바꾸는 load-bearing test를 요구한다."),
    ("A3-15", "Track-I global source family를 여러 redshift profile, multipole morphology와 superposition으로 넓히고, Track-II native Bianchi template에 대한 worst-case transfer test를 사전 설계한다."),
    ("A3-16", "CAMB, CLASS와 readable nanoCMB의 line-of-sight kernels로 shell convention을 교차검증하고, shell-refinement convergence와 source-term conservation identity를 gate로 둔다."),
    ("A3-17", "full cross-shell covariance, KL/effective mode count와 principal components를 사용한다. bin 수가 아니라 nonzero remote-field eigenmodes를 정보량으로 센다."),
    ("A3-18", "optical-depth bias를 amplitude nuisance로 분리하고 pole-only, amplitude+pole, external baryon-prior branches를 따로 보고한다. global-axis claim은 amplitude calibration에 의존하지 않는 signed/cross-bin statistic으로 검증한다."),
    ("A3-19", "현재 pSZ 저 S/N을 null로 숨기지 않고 remote-quadrupole identified region에 통합한다. low S/N에서도 local-only model의 특정 coherent pattern을 배제할 수 있는지 power analysis를 한다."),
    ("A3-20", "frequency maps, component-separated maps, foreground injections와 estimator mean-field cross-fit을 모두 사용하는 adversarial remote-field pipeline을 만든다."),
    ("A3-21", "published summary reproduction, public-map reimplementation, author-code acquisition을 세 단계로 등록한다. map이 없으면 summary-level likelihood만 사용하고 exact-map claim을 차단한다."),
    ("A3-22", "single labels 대신 source superposition model과 set-valued mixture weights를 기본으로 두고, combined model이 우세하면 mandatory abstention을 반환한다."),
    ("A3-23", "unknown-source contamination branch와 posterior predictive/model criticism을 넣어 model list 밖의 data에는 confident classification이 아니라 inadequate status를 낸다."),
    ("A3-24", "SBI posterior를 weak identified region과 비교해 contraction을 data/model/prior contribution으로 분해하고 null-direction KL 및 simulator-shift coverage를 공개한다."),
    ("A3-25", "nuisance set은 external validation과 pre-registration으로만 줄이며 interval width 자체를 design objective로 사용해 어떤 추가 observable이 실제 leverage를 주는지 최적화한다."),
    ("A3-26", "confidence sequences/e-values와 frozen search families를 도입해 package·statistic·depth 확장을 optional-stopping-safe하게 만든다."),
    ("A3-27", "box size/resolution/long-mode injection grid를 predeclare하고 observer ensemble을 사용한다. long-mode missingness는 explicit response-null로 판정한다."),
    ("A3-28", "independent initial conditions, different force solvers and analytic linear theory를 함께 사용하고 cross-code discrepancy envelope를 model-form uncertainty로 보존한다."),
    ("A3-29", "download, cached, extracted, generated and summary bytes를 분리한 storage receipt와 100 GB hard gate를 만든다. raw deletion은 replacement-ready hash receipt 이후에만 허용한다."),
    ("A3-30", "Track-I artifact schema에 native capability bit를 물리적으로 넣지 못하게 하고, Track-II consumer는 real SolverDeliveryReceipt 없이는 exit 3으로 막는다."),
    ("A3-31", "solver handshake에 tetrad/frame, harmonic phase, spin convention, time/redshift, units와 FLRW/analytic limits를 포함한 semantic conformance suite를 둔다."),
    ("A3-32", "Planck statistics, redshift bins와 source hypotheses를 observed map을 열기 전에 freeze하고 global max-statistic/held-out replication을 적용한다."),
    ("A3-33", "axis, oriented vector, parity/handedness object를 서로 다른 type으로 구분한다. unoriented alignment에는 |dot|, signed dipole에는 signed dot을 사용한다."),
    ("A3-34", "benchmark를 끝점으로 두지 않고 optimal survey/statistic design, finite-window no-go/identification theorem과 public-data remote-field application까지 연결한다."),
]

# PR definitions.  Each card receives strict common gates plus PR-specific gates.
PRS = [
    dict(id=247, wave=35, track="I", title="External ecosystem intake, immutable package/data ledger", deps=[], cost="medium", risk="medium", hostile=["H3-01","H3-03","H3-05","H3-29"], target="모든 외부 library, paper code, dataset과 program을 version/license/storage/scientific-leverage가 고정된 연구 객체로 만든다.", falsifier="설치되지 않거나 license/version이 다른 package가 동일 authenticated plugin으로 통과한다.", work="external ecosystem ledger, 3-day spike protocol, storage accounting, package-selection family를 구현한다.", assets=["experiments/plugin_probe.py", "configs/external_ecosystem_ledger.json", "configs/data_recipes.json"], specific_pass=["최소 20개 후보의 official source, role, Track, install profile과 decisive leverage test가 채워진다.", "download/cached/extracted/generated bytes가 분리되고 100 GB hard limit simulator가 통과한다."], specific_fail=["package name만 있고 scientific leverage 또는 license receipt가 없으면 FAIL.", "observed result를 본 뒤 package candidate family를 축소하면 새 analysis ID를 요구한다."], max_claim="외부 생태계가 content-addressed, falsifier-bearing research substrate로 등록됐다."),
    dict(id=248, wave=35, track="I", title="Fail-closed plugin adapter and capability receipt", deps=[247], cost="medium", risk="high", hostile=["H3-02","H3-04","H3-30"], target="optional package 실패와 Track-II capability 누수를 silent fallback 없이 차단하는 typed adapter layer를 구축한다.", falsifier="CAMB import 실패 후 toy spectrum이 external CAMB result로 stamp된다.", work="PluginSpec, capability bits, BLOCKED_PLUGIN_MISSING, lineage/independence graph와 track boundary validator를 구현한다.", assets=["src/htt_ext/plugins/registry.py", "experiments/plugin_probe.py", "experiments/track_boundary_validator.py"], specific_pass=["모든 missing optional plugin이 core failure가 아니라 explicit blocked receipt를 낸다.", "Track I에서 native capability marker 하나라도 요청하면 nonzero exit가 난다."], specific_fail=["fallback 결과가 external_result=true를 받으면 FAIL.", "코드 이름만으로 oracle independence를 두 번 계상하면 FAIL."], max_claim="외부 plugin과 native capability가 fail-closed type system으로 격리됐다."),
    dict(id=249, wave=35, track="I", title="Hermetic workflow, summary exchange and clean-repo overlay", deps=[247,248], cost="medium", risk="medium", hostile=["H3-03","H3-29"], target="clean checkout에서 외부 adapter, summary, covariance와 PR artifacts를 재생성하는 local workflow를 만든다.", falsifier="bundle 밖 /mnt 경로나 untracked cache가 없으면 결과가 달라진다.", work="Snakemake target design, SACC-like exchange schema, overlay installer, environment receipts와 clean-CWD tests를 구현한다.", assets=["tools/install_into_repo.py", "tools/verify_bundle.py", "Makefile", "schemas/plugin_receipt.schema.json"], specific_pass=["dry-run installer가 충돌을 검출하고 apply 후 clean repo에서 make validate가 동작한다.", "summary/covariance artifact가 units, frame, mask, seed와 upstream hash를 가진다."], specific_fail=["absolute local path가 publication artifact에 남으면 FAIL.", "installer가 기존 repo 파일을 무통보 overwrite하면 FAIL."], max_claim="패키지가 local htt_base checkout 안에서 hermetic overlay로 실행된다."),
    dict(id=250, wave=35, track="I", title="External-oracle independence and mutation laboratory", deps=[247,248,249], cost="high", risk="high", hostile=["H3-01","H3-02","H3-05","H3-28"], target="외부 package 통합이 실제 rank/coverage/source-discrimination leverage를 주는지 hostile mutation으로 판정한다.", falsifier="package output을 constant 또는 다른 package copy로 바꿔도 gate가 green이다.", work="oracle lineage, package-removal, version-drift, sign/unit, shared-input and selection-multiplicity mutations를 구현한다.", assets=["experiments/rotation_covariance_test.py", "experiments/binning_stability_demo.py", "docs/01_HOSTILE_REFEREE_STEELMAN_EXTERNAL_FUSION.md"], specific_pass=["각 production plugin마다 최소 3개 load-bearing mutation이 모두 kill된다.", "공유 equation/input lineage를 가진 oracle agreement는 독립 evidence count에서 제외된다."], specific_fail=["tool removal 후 scientific metric이 동일하면 해당 plugin은 archive.", "favourable tool만 holdout에 남기면 whole family calibration을 다시 한다."], max_claim="외부 package가 wrapper가 아니라 load-bearing scientific component임이 검증됐다."),
    dict(id=251, wave=36, track="I", title="Low-ell pole definitions, rotations and identifiability", deps=[249,250], cost="medium", risk="medium", hostile=["H3-09","H3-10","H3-11","H3-33"], target="low-ell pole를 oriented/unoriented type과 eigen-gap을 포함한 well-defined object로 만든다.", falsifier="active rotation 후 pole이 함께 회전하지 않거나 eigen-degenerate case에 finite identified axis가 나온다.", work="power-tensor pole, max/min angular momentum and optional multipole-vector definitions, rotation covariance와 degeneracy status를 구현한다.", assets=["src/htt_ext/lowell/poles.py", "experiments/rotation_covariance_test.py", "tests/test_lowell_core.py"], specific_pass=["ell=1..5 random 100-case rotation covariance worst error <1e-9.", "axis sign ambiguity가 type-level로 보존되고 signed/unoriented dot mutation이 검출된다."], specific_fail=["pole definition 변경이 same analysis ID로 허용되면 FAIL.", "eigen-gap threshold 이하에서 point pole을 보고하면 FAIL."], max_claim="등록된 low-ell pole family가 rotation-covariant하고 identifiability-aware하다."),
    dict(id=252, wave=36, track="I", title="Shell-resolved and cumulative low-ell reference DGP", deps=[251], cost="medium", risk="medium", hostile=["H3-06","H3-09","H3-16","H3-17"], target="shell-source, cumulative-observer, remote field를 분리한 transparent reference DGP를 만든다.", falsifier="local observer term이 remote shell field에 자동 주입되거나 shell covariance가 무시된다.", work="correlated real-sky alms, shell/cumulative trajectories, source profiles와 exact seed receipts를 구현한다.", assets=["src/htt_ext/lowell/alm.py", "src/htt_ext/lowell/shells.py", "experiments/lowell_shell_poles_demo.py"], specific_pass=["모든 shell alm이 reality condition과 PSD covariance를 만족한다.", "LOCAL_BOOST remote-field negative control이 isotropic remote field와 bit-identical하다."], specific_fail=["reference DGP output을 physical CAMB/CLASS result로 stamp하면 FAIL.", "cross-shell covariance를 diagonal로 대체하면 mutation이 살아남아 FAIL."], max_claim="source-identification과 gate 검증용 shell-pole reference DGP가 준비됐다."),
    dict(id=253, wave=36, track="I", title="CAMB, CLASS and nanoCMB shell-transfer cross-check", deps=[248,250,252], cost="high", risk="high", hostile=["H3-06","H3-07","H3-16"], target="SW, Doppler, early/late ISW와 source-window contributions의 redshift kernels를 세 independent implementations로 계산한다.", falsifier="shell refinement 또는 code cross-check에서 total low-ell transfer가 보존되지 않는다.", work="CAMB source windows, CLASS transfer output and readable nanoCMB line-of-sight adapter를 구현하고 shell sum identity를 검증한다.", assets=["src/htt_ext/plugins/camb_adapter.py", "src/htt_ext/plugins/class_adapter.py", "experiments/binning_stability_demo.py", "experiments/shell_kernel_conservation_demo.py", "src/htt_ext/lowell/transfer.py"], specific_pass=["total Cl/alm transfer가 CAMB-CLASS 사이 preregistered tolerance 내 일치한다.", "두 shell refinement에서 cumulative pole and power shift가 declared tolerance 아래다."], specific_fail=["reference DGP의 unstable binning을 물리 result로 사용하면 FAIL.", "FLRW transfer agreement를 anisotropic solver validation으로 승격하면 FAIL."], max_claim="FLRW low-ell source terms의 shell-resolved transfer가 code-cross-checked됐다."),
    dict(id=254, wave=36, track="I", title="GLASS lightcone, PySM foreground and masked-sky adapter", deps=[248,249,252,253], cost="high", risk="medium", hostile=["H3-08","H3-12","H3-17"], target="redshift shell LSS, survey window, foreground와 mask가 pole trajectory에 미치는 영향을 full-sky mocks로 정량화한다.", falsifier="mask/foreground가 pole을 회전시키는데 covariance/nuisance region이 이를 포함하지 않는다.", work="GLASS shell fields, PySM/PanEx foreground, healpy/NaMaster masking and common-seed cross-fields를 구현한다.", assets=["src/htt_ext/plugins/glass_adapter.py", "configs/data_recipes.json", "configs/external_ecosystem_ledger.json"], specific_pass=["input two-point statistics가 target spectra를 tolerance 내 재현한다.", "mask/foreground family를 적용한 95% pole region coverage가 nominal이다."], specific_fail=["GLASS mock를 nonlinear velocity truth로 사용하면 FAIL.", "different mask pipelines를 independent skies로 세면 FAIL."], max_claim="foreground/window-conditioned shell-pole response envelope가 구축됐다."),
    dict(id=255, wave=36, track="I", title="Load-bearing exact local-boost operator", deps=[251,253,254], cost="high", risk="high", hostile=["H3-14","H3-32"], target="thermodynamic Doppler와 aberration을 일관되게 적용하고 local endpoint contribution을 remote/global source와 분리한다.", falsifier="boost amplitude/direction을 0 또는 회전시켜도 claimed statistic이 변하지 않는다.", work="repo exact pixel-space operator, analytic first-order kernel and independent remapping cross-check를 연결한다.", assets=["experiments/local_boost_global_tilt_benchmark.py", "docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md"], specific_pass=["amplitude 0.5/1/1.5 scan에서 likelihood minimum이 injected amplitude tolerance 내에 있다.", "90-degree axis rotation과 sign flip negative controls가 preregistered score degradation을 보인다."], specific_fail=["common template subtraction으로 template가 score에서 상쇄되면 FAIL.", "Doppler-only 또는 aberration-only result를 exact boost라 부르면 FAIL."], max_claim="local observer boost response가 load-bearing and convention-cross-checked됐다."),
    dict(id=256, wave=36, track="I", title="Adversarial global-coherence source family", deps=[251,252,253], cost="medium", risk="high", hostile=["H3-15","H3-22","H3-23"], target="단일 fixed-axis strawman이 아닌 redshift profile, multipole morphology and source-superposition family를 구축한다.", falsifier="training family 밖 profile에서 classifier가 confident global result를 낸다.", work="global coherent, local structure, calibration, mixture, unknown-source generators and held-out profiles를 구현한다.", assets=["src/htt_ext/lowell/shells.py", "experiments/local_boost_global_tilt_benchmark.py"], specific_pass=["held-out source profiles에서 inadequate/abstention calibration이 nominal이다.", "combined source model이 single-source보다 우수할 때 mandatory mixture status가 나온다."], specific_fail=["single fixed-axis injection만으로 global performance를 주장하면 FAIL.", "unknown-source cell에 confident known label을 허용하면 FAIL."], max_claim="local/global discrimination용 adversarial source family가 구축됐다."),
    dict(id=257, wave=36, track="I", title="Pole trajectories, covariance, degeneracy and binning semantics", deps=[251,252,253,254,256], cost="high", risk="high", hostile=["H3-10","H3-11","H3-16","H3-17","H3-33"], target="pole drift, cross-shell alignment, eigen-gap, cross-l alignment과 effective remote modes를 covariance-aware statistic으로 정의한다.", falsifier="shell 수를 늘리기만 해 significance가 임의로 증가한다.", work="PoleTrajectory summaries, full covariance, PCA mode count, bin-refinement and pole-definition sensitivity를 구현한다.", assets=["src/htt_ext/lowell/discrimination.py", "experiments/binning_stability_demo.py", "experiments/pole_response_rank_demo.py"], specific_pass=["effective mode count가 covariance rank와 일치하고 duplicate bins가 information을 늘리지 않는다.", "pole-definition and shell-mesh family 전체에서 conclusion status가 predeclared stability rule을 만족한다."], specific_fail=["bin independence assumption 또는 pole sign confusion이 발견되면 FAIL.", "expected binning blocker를 무시하고 result를 promote하면 FAIL."], max_claim="redshift/depth pole summaries가 covariance and definition aware하게 등록됐다."),
    dict(id=258, wave=36, track="I", title="Planck local low-ell pole extraction and common-sky stability", deps=[249,251,254,257], cost="medium", risk="high", hostile=["H3-12","H3-13","H3-32"], target="official Planck maps에서 local observed pole region을 component-separation/mask nuisance와 함께 추출한다.", falsifier="map/mask change가 preregistered region 밖 pole shift를 만들거나 pipeline asymmetry가 null에서 size를 깨뜨린다.", work="PR3 and optional NPIPE map recipes, common masks, monopole/dipole removal, map2alm and map-product union region을 구현한다.", assets=["experiments/planck_lowell_poles.py", "configs/data_recipes.json", "docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md"], specific_pass=["SMICA/Commander/NILC/SEVEM을 동일 pipeline으로 처리하고 common-sky covariance를 명시한다.", "simulation-calibrated pole cone and statistic ranks가 finite resolution floor 위에서 유효하다."], specific_fail=["component maps를 독립 replication으로 곱하면 FAIL.", "observed pole를 본 뒤 mask, l range or definition을 바꾸면 새 family calibration이 필요하다."], max_claim="우리 위치에서의 Planck low-ell pole region이 pipeline-conditional하게 측정됐다."),
    dict(id=259, wave=37, track="I", title="Remote dipole/quadrupole linear field kernels and mocks", deps=[253,254,256,257], cost="high", risk="high", hostile=["H3-09","H3-17","H3-18","H3-19"], target="redshift-binned remote CMB dipole/quadrupole field의 correlated signal/noise covariance를 구축한다.", falsifier="local observer boost가 remote field에 자동 나타나거나 remote covariance가 non-PSD다.", work="Deutsch et al. remote kernels, SW/ISW/Doppler decomposition, GLASS electron/tracer shells and PCA modes를 구현한다.", assets=["src/htt_ext/remote/fields.py", "experiments/remote_fields_demo.py"], specific_pass=["remote local-boost negative control이 exact zero endpoint injection을 보인다.", "signal and reconstruction covariance가 PSD이고 analytic limits와 일치한다."], specific_fail=["remote dipole amplitude를 optical-depth bias 없이 velocity로 부르면 FAIL.", "quadrupole low S/N에서 point pole을 강제하면 FAIL."], max_claim="remote dipole/quadrupole shell-field simulation substrate가 구축됐다."),
    dict(id=260, wave=37, track="I", title="kSZ remote-dipole quadratic estimator prototype", deps=[259], cost="high", risk="high", hostile=["H3-18","H3-20","H3-21"], target="mock CMB×galaxy data에서 remote dipole field를 reconstruction하고 optical-depth/foreground nuisance를 분리한다.", falsifier="null or foreground-only mocks에서 coherent remote pole가 nominal rate보다 자주 검출된다.", work="curved/full-sky quadratic estimator prototype, mean-field cross-fit, optical-depth bias and frequency-map stress를 구현한다.", assets=["experiments/remote_fields_demo.py", "docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md"], specific_pass=["injection recovery, null size, redshift-bin covariance and monopole-removal mutation이 모두 통과한다.", "amplitude-free pole statistic과 amplitude-sensitive branch를 분리한다."], specific_fail=["single component-separated map만으로 foreground robustness를 주장하면 FAIL.", "published summary를 reconstruction map처럼 사용하면 FAIL."], max_claim="kSZ remote-dipole reconstruction method가 mock-calibrated됐다."),
    dict(id=261, wave=37, track="I", title="pSZ remote-quadrupole/bispectrum prototype", deps=[259], cost="high", risk="high", hostile=["H3-19","H3-20","H3-21"], target="remote quadrupole field와 pSZ CMB-CMB-galaxy bispectrum을 low-S/N에서도 honest identified region으로 분석한다.", falsifier="null maps에서 remote quadrupole pole가 identified되거나 expected O(1) S/N를 초과한 significance가 생긴다.", work="quadrupole estimator/bispectrum, optical-depth bias, frequency/foreground and z~1-2 tracer windows를 구현한다.", assets=["src/htt_ext/remote/fields.py", "docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md"], specific_pass=["published Planck+ACT+unWISE/CIB summary-level constraints를 tolerance 내 재현한다.", "low eigen-gap bins은 direction-UNDETERMINED로 분류된다."], specific_fail=["non-detection을 zero remote quadrupole로 해석하면 FAIL.", "tensor/global tilt inference를 pSZ amplitude nuisance 없이 수행하면 FAIL."], max_claim="pSZ remote-quadrupole method와 current-data constraint interface가 구축됐다."),
    dict(id=262, wave=37, track="I", title="Current remote-field data receipts and comparison", deps=[258,260,261], cost="high", risk="high", hostile=["H3-18","H3-19","H3-21","H3-32"], target="Planck+unWISE, ACT+DESI and Planck/ACT pSZ literature/data를 reproducible summary/map tiers로 연결한다.", falsifier="public map/code가 없는 결과를 exact reconstruction comparison으로 표시한다.", work="paper-summary, public-products and full-reconstruction 세 evidence tier, data/version/source receipts and comparison tables를 구현한다.", assets=["configs/data_recipes.json", "docs/07_WEB_LITERATURE_AND_SOFTWARE_CONTEXT.md"], specific_pass=["각 external result가 summary/map/code availability와 covariance scope를 명시한다.", "local Planck poles와 remote constraints의 joint comparison이 common covariance assumptions를 공개한다."], specific_fail=["literature number를 raw data result로 승격하면 FAIL.", "latest remote-field result의 publication/date/version을 검증하지 못하면 BLOCKED."], max_claim="현재 public remote-field evidence가 tiered, reproducible comparison object로 연결됐다."),
    dict(id=263, wave=37, track="I", title="Redshift-pole response Jacobian and identifiability atlas", deps=[255,256,257,259,260,261], cost="high", risk="high", hostile=["H3-17","H3-22","H3-23","H3-34"], target="local boost, LSS, calibration, global coherent and remote-field parameters에 대한 nuisance-projected pole response rank를 계산한다.", falsifier="preinserted zero/nonzero columns로 rank를 선언하거나 duplicated bins가 rank를 올린다.", work="finite difference/autodiff Jacobian, singular spectrum, null/weak directions and optimal reopening candidate를 구현한다.", assets=["experiments/pole_response_rank_demo.py", "src/htt_ext/lowell/discrimination.py"], specific_pass=["at least two independent derivative routes가 singular values를 tolerance 내 재현한다.", "bin duplication, map-product duplication and nuisance projection mutations이 rank를 올리지 않는다."], specific_fail=["registered design을 hard-code해 data-derived rank라 부르면 FAIL.", "weak singular direction에 finite point posterior만 보고하면 FAIL."], max_claim="redshift-resolved pole observables의 source identifiability phase diagram이 구축됐다."),
    dict(id=264, wave=37, track="I", title="Local boost/global tilt/source-superposition discriminator", deps=[256,257,258,262,263], cost="high", risk="high", hostile=["H3-22","H3-23","H3-32","H3-34"], target="local-only, global-only, LSS/systematic and superposition models을 mandatory abstention과 함께 구분한다.", falsifier="confusable or unknown-source data에 confident global label이 나온다.", work="centroid/conjugate baseline, combined model, held-out profiles, adequacy and abstention gates를 구현한다.", assets=["experiments/local_boost_global_tilt_benchmark.py", "src/htt_ext/lowell/discrimination.py"], specific_pass=["blind synthetic matrix에서 clean cells recovery와 confusable/superposition abstention이 preregistered rate를 충족한다.", "current-data use는 all source-model adequacy and held-out gains를 통과해야 한다."], specific_fail=["single-label accuracy만 보고 combined competitor를 생략하면 FAIL.", "data를 본 뒤 source list나 thresholds를 바꾸면 새 calibration이 필요하다."], max_claim="redshift pole와 remote fields를 이용한 local/global discrimination candidate가 calibration됐다."),
    dict(id=265, wave=37, track="I", title="Partial identification, confidence sets and pole-region coverage", deps=[257,263,264], cost="high", risk="high", hostile=["H3-11","H3-17","H3-24","H3-25"], target="global coherent fraction, axis and source mixture를 point posterior가 아니라 coverage-calibrated set으로 추론한다.", falsifier="weak/nonidentified DGP에서 narrow set 또는 false point-ID가 nominal 이상 발생한다.", work="coherence moment identified set, joint axis/fraction optimizer, estimated covariance and simulator-shift coverage를 구현한다.", assets=["src/htt_ext/lowell/identified.py", "experiments/coherent_fraction_demo.py"], specific_pass=["point/weak/non-ID grid의 95% target에 99% binomial lower bound >=0.93.", "nuisance set freeze, mesh refinement and independent endpoint solver가 일치한다."], specific_fail=["interval width를 보고 nuisance bounds를 축소하면 FAIL.", "EMPTY/UNBOUNDED/UNDETERMINED를 point estimate로 변환하면 FAIL."], max_claim="local/global mixture의 set-valued inference가 nominal coverage를 가진다."),
    dict(id=266, wave=38, track="I", title="CosmoID-Bench external-tool task suite", deps=[250,263,264,265], cost="high", risk="medium", hostile=["H3-01","H3-05","H3-24","H3-34"], target="point/partial/non-identification과 source confounding을 cosmology SBI benchmark task로 공개한다.", falsifier="benchmark가 HTT에 유리한 toy만 포함하거나 reference posterior가 없는 non-ID task를 억지 posterior로 채운다.", work="sbibm-compatible tasks, false-point-ID, set coverage, prior exposure, abstention precision and simulator-shift metrics를 구현한다.", assets=["experiments/local_boost_global_tilt_benchmark.py", "experiments/coherent_fraction_demo.py", "configs/external_ecosystem_ledger.json"], specific_pass=["최소 6 task와 3 inference baselines, hidden holdout generator가 포함된다.", "external method가 HTT보다 우수한 task도 결과에 보존한다."], specific_fail=["benchmark selection을 observed performance 후 변경하면 FAIL.", "nonidentified task에 single reference posterior만 진실로 두면 FAIL."], max_claim="cosmology partial/non-identification benchmark suite가 외부 방법 비교에 준비됐다."),
    dict(id=267, wave=38, track="I", title="Low-ell morphology zoo and robustness envelope", deps=[254,257,263,266], cost="high", risk="high", hostile=["H3-05","H3-10","H3-12","H3-34"], target="Cl, pseudo-Cl, BiPoSH, wavelet, scattering, Minkowski/topology가 source rank와 robustness에 주는 정보를 비교한다.", falsifier="statistic family를 선택한 evaluation data에서 rank gain이 사라진다.", work="NaMaster/S2FFT/S2WAV and optional topology adapters, common simulations, complexity/cost and held-out response atlas를 구현한다.", assets=["configs/external_ecosystem_ledger.json", "experiments/pole_response_rank_demo.py"], specific_pass=["statistic selection은 training simulations에서만 하고 holdout rank/coverage로 평가한다.", "foreground/mask complexity 증가 시 confidence가 부당하게 증가하지 않는다."], specific_fail=["smallest p-value만 보고 morphology gain이라 부르면 FAIL.", "experimental plugin failure가 baseline result를 바꾸면 FAIL."], max_claim="low-ell morphology statistic의 identifiability/robustness phase diagram이 완성됐다."),
    dict(id=268, wave=38, track="I", title="E-optimal observable and survey design", deps=[263,265,267], cost="high", risk="medium", hostile=["H3-25","H3-34"], target="identified interval을 줄이고 weakest singular direction을 여는 최소 observable/depth/frequency design을 최적화한다.", falsifier="optimized design이 independent simulations에서 rank/coverage gain을 재현하지 못한다.", work="CVXPY/CVXPYlayers E/D-optimal design, cost constraints, differentiable support function and held-out validation을 구현한다.", assets=["configs/external_ecosystem_ledger.json", "experiments/pole_response_rank_demo.py"], specific_pass=["convex solver와 brute-force small problem가 동일 optimum을 찾는다.", "optimized design은 holdout에서 preregistered singular-value or interval-width gain을 달성한다."], specific_fail=["evaluation data로 weights를 재최적화하면 FAIL.", "unregistered observable response를 nonzero로 가정하면 FAIL."], max_claim="local/global distinction을 위한 계산 가능한 optimal observation design을 제시한다."),
    dict(id=269, wave=38, track="I", title="Local PM/N-body observer ensemble adapters", deps=[247,248,250,254], cost="high", risk="high", hostile=["H3-08","H3-27","H3-28","H3-29"], target="CONCEPT/JaxPM/PySCo로 finite-window velocity, local structure and shell poles를 cross-code observer ensemble에서 생성한다.", falsifier="box size/resolution/long-mode 변화가 conclusion을 바꾸지만 model-form uncertainty에 반영되지 않는다.", work="small PM configs, common IC and independent IC branches, observer sampling, summary-only storage and linear-theory oracle를 구현한다.", assets=["configs/external_ecosystem_ledger.json", "configs/data_recipes.json"], specific_pass=["최소 두 simulator와 analytic linear limit가 variance/power를 tolerance 내 재현한다.", "box/resolution grid와 long-mode injection 결과가 model-form envelope에 포함된다."], specific_fail=["same-box observers를 independent simulations로 세면 FAIL.", "100 GB storage gate를 넘거나 raw lifecycle receipt가 없으면 BLOCKED."], max_claim="local LSS/velocity uncertainty의 cross-code simulation envelope가 구축됐다."),
    dict(id=270, wave=38, track="I", title="Finite-window bulk-flow to homogeneous-mode bridge", deps=[265,269], cost="high", risk="high", hostile=["H3-17","H3-22","H3-25","H3-27"], target="multi-window velocity tomography가 homogeneous coherent mode를 언제 식별/비식별하는지 theorem과 mocks로 결정한다.", falsifier="single-window bulk amplitude를 homogeneous tilt point estimate로 바꿀 수 있다.", work="window operators, stochastic LSS covariance, calibration/selection nuisance and joint identified set를 구현한다.", assets=["context/round2/experiments/bulk_to_tilt_bridge.py", "experiments/coherent_fraction_demo.py"], specific_pass=["single-window non-ID and multi-window rank reopening analytic fixtures를 재현한다.", "observer-ensemble coverage and model-form envelope가 nominal이다."], specific_fail=["bulk flow=tilt equality를 bridge 없이 사용하면 FAIL.", "favourable window만 골라 global coherence를 주장하면 FAIL."], max_claim="finite-window velocity가 homogeneous coherent mode를 식별하는 조건 또는 no-go region이 확립됐다."),
    dict(id=271, wave=38, track="I", title="Relativistic redshift-dipole tomography", deps=[254,263,265,269], cost="high", risk="high", hostile=["H3-22","H3-23","H3-27","H3-32"], target="COFFE/GLASS/pycorr/pypower를 이용해 kinematic, density, Doppler, lensing, wide-angle, selection and global dipole를 redshift/tracer별로 분리한다.", falsifier="survey random/window correction 없이 global source를 식별한다.", work="theory templates, mock catalog, data/random estimator, cap/tracer covariance and source-superposition model을 구현한다.", assets=["configs/external_ecosystem_ledger.json", "configs/data_recipes.json"], specific_pass=["random catalogs에서 estimator mean이 zero within covariance다.", "held-out tracer/redshift cells에서 source-confusion and abstention calibration이 nominal이다."], specific_fail=["single amplitude or common beta likelihood로 모든 source를 합치면 FAIL.", "official survey window 없는 actual-data claim은 BLOCKED."], max_claim="survey-window-conditioned relativistic dipole source tomography가 구축됐다."),
    dict(id=272, wave=39, track="I", title="SBI, NumPyro and independent inference baselines", deps=[266,267,270,271], cost="high", risk="high", hostile=["H3-24","H3-25"], target="neural and conventional posterior contraction을 weak identified region, prior exposure and simulator shift와 비교한다.", falsifier="nonidentified direction에서 posterior가 좁아져도 data information으로 분류된다.", work="sbi SNPE/SNRE, NumPyro NUTS, optional Cobaya, calibration and contraction-attribution metrics를 구현한다.", assets=["configs/external_ecosystem_ledger.json", "experiments/coherent_fraction_demo.py"], specific_pass=["simulator-matched SBC/coverage와 simulator-shift adequacy/abstention을 모두 보고한다.", "null-direction posterior KL and prior/training-distribution sensitivity가 공개된다."], specific_fail=["narrow posterior alone을 identification으로 판정하면 FAIL.", "HTT보다 나쁜/좋은 baseline을 선택적으로 숨기면 FAIL."], max_claim="posterior contraction의 data/model/prior 기여가 set-valued inference와 함께 정량화됐다."),
    dict(id=273, wave=39, track="I", title="Anytime-valid exploration and Track-I integration report", deps=[247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272], cost="high", risk="high", hostile=["H3-05","H3-26","H3-29","H3-34"], target="package/statistic/mock 확장을 optional-stopping-safe하게 통제하고 solver-independent external-fusion programme를 종합한다.", falsifier="adaptive package/statistic 추가에서 type-I error가 초과하거나 failed plugin/result가 report에서 누락된다.", work="e-process/confidence sequence, frozen family ledger, storage receipts, all Track-I figures and hostile external review를 구현한다.", assets=["experiments/adaptive_scan_evalue_demo.py", "experiments/run_all.py", "docs/04_PUBLICATION_READINESS_MASTER_CHECKLIST_EXTERNAL_FUSION.md"], specific_pass=["maximal-dependence anytime simulations에서 Ville bound가 통과한다.", "Track-I report가 성공, failure, abstention, blocked plugin을 모두 포함한다."], specific_fail=["fixed p-value로 adaptive search를 보고하면 FAIL.", "Track-II capability 또는 geometry claim이 포함되면 FAIL."], max_claim="solver-independent external-fusion methodology와 redshift-pole programme가 pre-native readiness를 달성했다."),
    dict(id=274, wave=40, track="II", title="Native Bianchi Boltzmann SolverDeliveryReceipt", deps=[248,249,250,273], cost="blocked_high", risk="critical", hostile=["H3-07","H3-30","H3-31"], target="temperature/polarization, recombination/reionization and independent benchmarks를 갖춘 real native solver만 Track II를 연다.", falsifier="synthetic fixture, wrapper or missing polarization solver가 Track II를 연다.", work="source/environment/data hashes, tetrad/harmonic conventions, FLRW null, Bianchi-I analytic, conservation, convergence and independent oracle receipt를 검증한다.", assets=["experiments/track_boundary_validator.py", "docs/06_TRACK_BOUNDARY_AND_NATIVE_SOLVER_HANDOFF.md"], specific_pass=["모든 conjunctive solver capability and benchmark가 PASS한다.", "independent reviewer가 source and semantic conventions를 재검증한다."], specific_fail=["receipt 누락 시 exit 3 BLOCKED_NATIVE_REQUIRED.", "temperature-only 또는 no-reionization solver는 FAIL."], max_claim="native Bianchi Boltzmann solver가 Track-II scientific consumption에 인증됐다."),
    dict(id=275, wave=40, track="II", title="Native shell-transfer and remote-observer field interface", deps=[274], cost="high", risk="critical", hostile=["H3-09","H3-16","H3-31"], target="native solver가 source term, observer worldline, shell alms and remote dipole/quadrupole fields를 typed output으로 제공한다.", falsifier="shell sum이 native total map을 재현하지 않거나 frame/phase 변환에서 mismatch가 난다.", work="NativeTransferCard, shell kernels, remote observer fields and CAMB/CLASS FLRW-limit comparison을 구현한다.", assets=["docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md", "docs/06_TRACK_BOUNDARY_AND_NATIVE_SOLVER_HANDOFF.md"], specific_pass=["FLRW limit에서 CAMB/CLASS shell totals와 preregistered tolerance 내 일치한다.", "native shell refinement와 source-term conservation gate가 통과한다."], specific_fail=["adapter가 convention mismatch를 보정 없이 숨기면 FAIL.", "native output을 Track-I phenomenological schema로 lossy cast하면 FAIL."], max_claim="Bianchi native transfer가 redshift/depth shell and remote-field level로 노출됐다."),
    dict(id=276, wave=40, track="II", title="Native redshift/depth low-ell pole evolution atlas", deps=[251,257,275], cost="high", risk="critical", hostile=["H3-10","H3-11","H3-15","H3-17"], target="Bianchi class/mode/initial condition별 local, cumulative and remote pole evolution을 native transfer로 계산한다.", falsifier="pole trajectory가 resolution, gauge/tetrad or source decomposition에 불안정하다.", work="native shell maps, pole-definition family, eigen-gap regions, cross-shell covariance and morphology atlas를 구현한다.", assets=["src/htt_ext/lowell/poles.py", "docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md"], specific_pass=["solver resolution/convention variants에서 identified pole regions가 stable하다.", "degenerate cases는 point axis가 아니라 set/undetermined로 반환된다."], specific_fail=["phenomenological source injection을 native result로 섞으면 FAIL.", "한 Bianchi type/mode의 trajectory를 universal global tilt로 해석하면 FAIL."], max_claim="native anisotropic cosmology의 redshift-dependent low-ell pole atlas가 구축됐다."),
    dict(id=277, wave=40, track="II", title="Native local-boost/global-tilt decomposition", deps=[255,264,275,276], cost="high", risk="critical", hostile=["H3-14","H3-15","H3-22","H3-31"], target="동일 native sky에서 observer boost, homogeneous matter tilt, geometry anisotropy and local structure contributions를 forward decomposition한다.", falsifier="local deboost 후 global component recovery가 injection truth를 재현하지 못한다.", work="paired boosted/unboosted native runs, multi-fluid frame bridges, superposition and subtraction noncommutativity를 구현한다.", assets=["experiments/local_boost_global_tilt_benchmark.py", "docs/06_TRACK_BOUNDARY_AND_NATIVE_SOLVER_HANDOFF.md"], specific_pass=["paired injection recovery and amplitude/direction mutations이 모두 통과한다.", "component decomposition residual이 solver error budget 안에 있다."], specific_fail=["same constant template subtraction이 score에서 상쇄되면 FAIL.", "local observer vector를 homogeneous matter tilt로 자동 cast하면 FAIL."], max_claim="native forward physics에서 local boost와 global tilt의 분해가 검증됐다."),
    dict(id=278, wave=40, track="II", title="Native morphology response Jacobian and family quotient", deps=[263,267,275,276,277], cost="high", risk="critical", hostile=["H3-02","H3-15","H3-23","H3-31"], target="native T/E/B, TB/EB, BiPoSH/wavelet and remote-field response로 Bianchi family/mode equivalence quotient를 계산한다.", falsifier="family label이 달라도 response가 같을 때 별도 evidence로 ranking한다.", work="native finite-difference/adjoint Jacobian, nuisance projection, response equivalence and reopening observable atlas를 구현한다.", assets=["experiments/pole_response_rank_demo.py", "docs/06_TRACK_BOUNDARY_AND_NATIVE_SOLVER_HANDOFF.md"], specific_pass=["two derivative routes와 orientation/parity mirrors가 singular spectrum을 재현한다.", "response-equivalent families가 quotient class로 collapse된다."], specific_fail=["zero columns를 사전 지정해 native rank라 부르면 FAIL.", "family evidence가 within-class nonidentification을 무시하면 FAIL."], max_claim="native morphology에 기반한 Bianchi response equivalence atlas가 확립됐다."),
    dict(id=279, wave=40, track="II", title="Teff/reduced surrogate certification against native solver", deps=[274,275,278], cost="high", risk="high", hostile=["H3-02","H3-07","H3-15"], target="legacy reduced model을 native-error-certified emulator/preconditioner로 전환한다.", falsifier="declared domain에서 surrogate error bound가 깨지거나 out-of-domain query가 accepted다.", work="training/validation split, componentwise error envelope, morphology loss and fail-closed domain API를 구현한다.", assets=["context/round2/experiments/teff_surrogate_certification.py", "configs/external_ecosystem_ledger.json"], specific_pass=["independent native holdout에서 declared norm error가 bound 이내다.", "out-of-domain and resonance cases가 explicit rejection된다."], specific_fail=["old universal ratios를 native truth로 고정하면 FAIL.", "same native runs를 training and validation에 재사용하면 FAIL."], max_claim="Teff/reduced model이 certified native surrogate로 부활했다."),
    dict(id=280, wave=40, track="II", title="Track-II native-theory integration report", deps=[274,275,276,277,278,279], cost="high", risk="critical", hostile=["H3-07","H3-30","H3-31","H3-34"], target="native solver의 redshift pole, response rank, local/global decomposition and surrogate 결과를 hostile review와 함께 freeze한다.", falsifier="any load-bearing native receipt가 missing/failed인데 report가 validated result를 낸다.", work="native artifact DAG, theorem/experiment figures, failures and external theory review를 구현한다.", assets=["docs/04_PUBLICATION_READINESS_MASTER_CHECKLIST_EXTERNAL_FUSION.md", "docs/06_TRACK_BOUNDARY_AND_NATIVE_SOLVER_HANDOFF.md"], specific_pass=["all Track-II artifacts are reproducible from real solver receipt.", "independent external reviewer가 conventions and benchmark results를 재실행한다."], specific_fail=["Track-I toy or phenomenological source가 native figure에 섞이면 FAIL.", "solver failure를 scope caveat만으로 닫으면 FAIL."], max_claim="native Bianchi transfer and redshift-pole research programme가 integration readiness를 달성했다."),
    dict(id=281, wave=41, track="INTEGRATION", title="Common latent cosmology joint multi-probe region", deps=[273,280], cost="high", risk="critical", hostile=["H3-18","H3-22","H3-23","H3-25","H3-30"], target="동일 frame/epoch/matter/geometry model이 local CMB, remote fields, LSS dipoles and velocities를 동시에 생성하는 joint identified/posterior region을 계산한다.", falsifier="서로 양립하지 않는 marginal premises를 Cartesian product로 조립한다.", work="common latent state, joint likelihood/feasible set, cross-survey covariance, source superposition and prior exposure를 구현한다.", assets=["src/htt_ext/lowell/identified.py", "docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md"], specific_pass=["joint solution witness가 nonempty이고 every probe is generated from the same latent draw.", "marginal-box and joint-region difference, null sectors and prior exposure가 공개된다."], specific_fail=["CF4 bulk, Planck pole and class-conditional ceiling을 common model 없이 더하면 FAIL.", "joint covariance 없는 evidence multiplication은 FAIL."], max_claim="local boost/global tilt와 FLRW-departure components의 common-model joint region이 구축됐다."),
    dict(id=282, wave=41, track="INTEGRATION", title="External hostile replication and publication suite", deps=[281], cost="high", risk="critical", hostile=["H3-01","H3-05","H3-21","H3-29","H3-32","H3-34"], target="외부 연구자가 clean hardware에서 core benchmark, Planck poles, remote-field comparison and native results를 재현하고 논문 suite를 adjudicate한다.", falsifier="author environment 없이 load-bearing result 하나라도 재현되지 않거나 negative result가 package에서 누락된다.", work="Zenodo/release archive, containers, data recipes, blind replication, methods/data/native/joint manuscripts and complete claim graph를 구현한다.", assets=["tools/install_into_repo.py", "tools/verify_bundle.py", "MANIFEST.json"], specific_pass=["two external principals independently reproduce preregistered headline tables/figures.", "all failed/abstain/blocked branches are present and publication claims do not exceed receipts."], specific_fail=["external replication이 author-provided outputs only를 읽으면 FAIL.", "latest literature/data state를 재검증하지 않으면 release BLOCKED."], max_claim="외부 통합과 redshift-pole programme가 publication-ready multi-paper scientific suite로 승격됐다."),
]

COMMON_PASS = [
    "SPEC가 claim identity, estimand/domain, frame/order/units, input/output schema, success criteria와 decisive falsifier를 결과 열람 전에 고정한다.",
    "최소 두 개의 독립 구현, analytic limit 또는 genuinely independent external oracle이 declared tolerance 안에서 일치한다.",
    "관련 hostile mutation과 negative control이 전부 nonzero exit, BLOCKED 또는 expected abstention으로 kill된다.",
    "seeded repeat, clean temporary directory와 detached local-repo overlay 실행이 byte-identical 또는 declared tolerance 안에서 재현된다.",
    "모든 input/config/environment/output가 content hash를 갖고 downstream consumer의 stale path scan이 0 hit다.",
    "author와 다른 adjudicator가 code, scientific semantics, pass/fail gate를 서명한다.",
]
COMMON_FAIL = [
    "decisive falsifier가 한 번이라도 살아남으면 promotion을 금지하고 failure receipt를 남긴다.",
    "provenance, frame/type, covariance/null, nuisance/prior 또는 independent adjudication 중 하나라도 없으면 PASS를 반환하지 않는다.",
    "문구 완화, scope 축소, disclaimer 추가만으로 defect를 닫으면 PR을 reject한다.",
    "optional dependency missing, solver unavailable 또는 data absent를 toy fallback으로 대체하면 PR을 BLOCKED 처리한다.",
]


def write_hostile():
    lines = [
        "# External-Fusion Round-3 Hostile Referee Steelman",
        "",
        "이 문서는 외부 패키지와 redshift/depth low-ell pole programme에 대해 가능한 가장 강한 반론을 구성한다. 비판의 목적은 scope를 줄이는 것이 아니라 각 주장을 살아남게 할 load-bearing upgrade를 정의하는 것이다.",
        "",
    ]
    for ident, title, text in HOSTILE:
        lines += [f"## {ident} — {title}", "", text, ""]
    (DOCS / "01_HOSTILE_REFEREE_STEELMAN_EXTERNAL_FUSION.md").write_text("\n".join(lines), encoding="utf-8")


def write_advocate():
    lines = [
        "# External-Fusion Round-3 Advocate Steelman Upgrade",
        "",
        "각 항목은 hostile finding을 회피하지 않고 더 강한 successor claim으로 바꾸는 대응이다. 번호는 H3-xx와 일대일 대응한다.",
        "",
    ]
    for (hid, title, _), (aid, text) in zip(HOSTILE, ADVOCATE, strict=True):
        lines += [f"## {aid} responding to {hid} — {title}", "", text, ""]
    (DOCS / "02_ADVOCATE_STEELMAN_UPGRADE_EXTERNAL_FUSION.md").write_text("\n".join(lines), encoding="utf-8")


def write_roadmap():
    lines = [
        "# External-Fusion Round-3: Local-Repo PR Roadmap and Redshift/Depth Low-ell Pole Programme",
        "",
        "- **문서 상태:** `PROPOSED_ONLY_NOT_IN_ACTIVE_DAG`",
        "- **작성일:** 2026-07-22",
        "- **Owner:** `COMMON`",
        "- **PR range:** PR-247–PR-282",
        "- **Track-I rule:** native Bianchi Boltzmann solver output을 절대 소비하지 않는다.",
        "- **Track-II rule:** real `SolverDeliveryReceipt`가 없으면 scientific command는 exit 3 `BLOCKED_NATIVE_REQUIRED`.",
        "- **Integration rule:** PR-281은 Track-I checkpoint PR-273과 Track-II checkpoint PR-280을 모두 요구한다.",
        "",
        "## 1. 목적",
        "",
        "외부 library·repo·dataset을 단순 dependency로 추가하지 않고, HTT의 response-rank, partial-identification, coverage, source-discrimination과 abstention layer에 결합한다. redshift/depth pole programme는 local observer boost, finite-depth local structure, coherent global source와 native anisotropic geometry를 서로 다른 typed objects로 구분한다.",
        "",
        "## 2. DAG",
        "",
        "```text",
        "TRACK I  PR-247..273 ───────────┐",
        "                                 ├─ PR-281..282 integration/release",
        "TRACK II PR-274..280 (native) ──┘",
        "```",
        "",
        "## 3. 공통 실행 계약",
        "",
        "1. 각 PR은 SPEC → localization → implementation → scientific validation → numerical validation → independent review → closeout 순서로 실행한다.",
        "2. novelty와 readiness는 별도 축이다. 단, public claim은 artifact receipt의 semantic ceiling을 넘을 수 없다.",
        "3. failure, non-identification, inadequate, abstention, plugin missing과 native blocked는 정상 terminal result다.",
        "4. package name이나 test count는 scientific evidence가 아니다.",
        "5. local/global distinction은 source-superposition competitor와 unknown-source branch 없이 완료되지 않는다.",
        "6. pole은 definition, orientation type, mask, map product, shell convention과 covariance를 항상 기록한다.",
        "",
        "## 4. PR 카드",
        "",
    ]
    for pr in PRS:
        pid = pr["id"]
        lines += [
            f"### PR-{pid} — {pr['title']}",
            "",
            f"- **Wave / Track / dependencies / cost / risk:** {pr['wave']} / `{pr['track']}` / {', '.join('PR-'+str(x) for x in pr['deps']) if pr['deps'] else 'none'} / `{pr['cost']}` / `{pr['risk']}`.",
            f"- **Hostile findings:** {', '.join(pr['hostile'])}.",
            f"- **강화 목표 claim:** {pr['target']}",
            f"- **Decisive falsifier:** {pr['falsifier']}",
            f"- **실제로 할 것:** {pr['work']}",
            "- **하지 말 것:** 외부 package 설치 성공, 문구 완화, toy output 또는 diagnostic green만으로 scientific promotion하지 않는다. observed result에 맞춰 statistic/source/bin/nuisance를 변경하지 않는다.",
            "- **제공 asset과 사용법:**",
        ]
        for asset in pr["assets"]:
            command = f"python {asset}" if asset.endswith(".py") else f"read/reference {asset}"
            lines.append(f"  - `{asset}` — `{command}`")
        lines.append("- **PASS gates:**")
        for i, gate in enumerate(COMMON_PASS + pr["specific_pass"], 1):
            lines.append(f"  - [ ] PR-{pid}-P{i}: {gate}")
        lines.append("- **FAIL / kill gates:**")
        for i, gate in enumerate(COMMON_FAIL + pr["specific_fail"], 1):
            lines.append(f"  - [ ] PR-{pid}-F{i}: {gate}")
        if pr["track"] == "II":
            lines.append(f"  - [ ] PR-{pid}-F{len(COMMON_FAIL)+len(pr['specific_fail'])+1}: authenticated native SolverDeliveryReceipt가 없으면 exit 3으로 종료한다.")
        lines += [f"- **최대 승격 claim:** {pr['max_claim']} 단, 모든 conjunctive gate와 non-author adjudication 이후에만 허용.", ""]

        card = {
            **pr,
            "status": "PROPOSED_ONLY_NOT_IN_ACTIVE_DAG",
            "native_solver_required": pr["track"] == "II",
            "pass_gates": COMMON_PASS + pr["specific_pass"],
            "fail_gates": COMMON_FAIL + pr["specific_fail"] + (["native solver receipt missing -> exit 3"] if pr["track"] == "II" else []),
        }
        (CARDS / f"pr-{pid}.json").write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    (DOCS / "03_EXTERNAL_FUSION_PR_ROADMAP_20260722.md").write_text("\n".join(lines), encoding="utf-8")


def write_checklist():
    categories = {
        "A. 외부 패키지·provenance": [
            "모든 production package의 exact release/commit, license와 official example receipt가 있다.",
            "optional plugin missing은 explicit BLOCKED이며 silent fallback이 없다.",
            "oracle independence가 equation/input/author lineage graph로 평가된다.",
            "package/statistic search family가 preregistered되고 adaptive expansion이 anytime-valid하다.",
            "download/cached/extracted/generated/summary bytes가 분리되고 100 GB gate를 통과한다.",
        ],
        "B. low-ell pole object": [
            "shell-source, cumulative-observer, remote dipole, remote quadrupole object가 타입으로 분리된다.",
            "pole definition과 oriented/unoriented status가 명시된다.",
            "rotation covariance와 reality condition이 analytic tolerance를 통과한다.",
            "eigen-gap가 작으면 point axis 대신 UNDETERMINED/set-valued region이 나온다.",
            "pole definition, mask, map product and shell mesh sensitivity가 공개된다.",
        ],
        "C. redshift/source physics": [
            "CAMB, CLASS and readable independent implementation의 shell totals가 일치한다.",
            "SW, Doppler, early/late ISW and observer endpoint contributions가 분리된다.",
            "local boost는 remote fields에 자동 주입되지 않는다.",
            "global source family가 multiple profiles/morphologies/superpositions를 포함한다.",
            "cross-shell covariance and effective mode count가 사용된다.",
        ],
        "D. 실제 CMB와 remote fields": [
            "Planck component maps는 common sky pipeline sensitivity로 처리된다.",
            "official map/mask/version and transforms are hash-bound.",
            "kSZ optical-depth bias와 pSZ amplitude nuisance가 분리된다.",
            "frequency/foreground/mean-field stress tests가 통과한다.",
            "published summary, public maps and full reconstruction code evidence tiers가 구분된다.",
            "actual-data statistics and bins are frozen before unblinding.",
        ],
        "E. 통계·식별": [
            "response Jacobian, singular spectrum, nuisance projection and null sectors가 공개된다.",
            "combined source and unknown-source competitors가 포함된다.",
            "weak/non-ID DGP에서 false point-ID rate가 preregistered ceiling 아래다.",
            "identified region coverage 95% target의 99% lower bound가 0.93 이상이다.",
            "SBI contraction이 data/model/prior contribution으로 분해된다.",
            "simulator shift에서는 overconfident result가 아니라 inadequacy/abstention이 증가한다.",
        ],
        "F. LSS/velocity": [
            "최소 두 PM/N-body code와 analytic linear theory가 교차검증된다.",
            "box size, resolution, long modes, observer dependence와 survey windows가 sweep된다.",
            "single-window bulk flow는 homogeneous tilt로 자동 변환되지 않는다.",
            "multi-window identified set and coverage가 nominal이다.",
            "same-box observers를 independent realization로 세지 않는다.",
        ],
        "G. Track II native solver": [
            "real SolverDeliveryReceipt가 FLRW null, Bianchi-I analytic, T/E/B, recombination/reionization, conservation and convergence를 포함한다.",
            "native shell transfer sum이 native total map을 재현한다.",
            "tetrad/frame/harmonic/spin/redshift conventions가 adapter와 일치한다.",
            "native local boost/global tilt paired runs가 injection truth를 회복한다.",
            "native response-equivalent families가 quotient class로 collapse된다.",
            "surrogate는 independent native holdout에서 certified error를 만족한다.",
        ],
        "H. 공동 통합·출판": [
            "모든 probe는 동일 latent cosmology/frame/epoch에서 생성된다.",
            "joint covariance without double counting is present.",
            "marginal envelope와 common-model joint region이 구분된다.",
            "failed, blocked, abstain and null results가 release에 포함된다.",
            "두 외부 principal이 clean environment에서 headline artifacts를 재현한다.",
            "publication claim이 artifact semantic ceiling을 넘지 않는다.",
        ],
    }
    lines = ["# External-Fusion Publication Readiness Master Checklist", "", "모든 항목은 conjunctive다. 한 개의 load-bearing FAIL도 다른 점수로 상쇄할 수 없다.", ""]
    for title, items in categories.items():
        lines += [f"## {title}", ""] + [f"- [ ] {x}" for x in items] + [""]
    (DOCS / "04_PUBLICATION_READINESS_MASTER_CHECKLIST_EXTERNAL_FUSION.md").write_text("\n".join(lines), encoding="utf-8")


def write_proofs():
    items = [
        ("T-P1", "Pole rotation covariance", "power-tensor pole가 SO(3) active rotation에 공변하고 p~-p axis quotient에서 well-defined임을 증명한다."),
        ("T-P2", "Pole degeneracy instability", "eigen-gap가 0으로 갈 때 Davis-Kahan-type axis error bound가 발산함을 보여 direction abstention threshold를 정당화한다."),
        ("T-P3", "Shell-sum conservation", "registered line-of-sight source decomposition의 shell sum이 total transfer를 재현하는 조건과 discretization remainder를 증명한다."),
        ("T-P4", "Observer endpoint separation", "local Lorentz boost term이 remote dipole/quadrupole field source와 다른 boundary object임을 typed map으로 증명한다."),
        ("T-P5", "Cross-shell effective rank", "correlated redshift bins의 information은 bin count가 아니라 covariance-whitened nonzero modes에 의해 결정됨을 증명한다."),
        ("T-P6", "Pole-definition stability set", "여러 registered pole definitions의 intersection/union을 set-valued axis region으로 구성하고 coverage 조건을 증명한다."),
        ("T-P7", "Source superposition non-identification", "collinear local/systematic/global responses가 mixture weights를 비식별하게 만드는 kernel을 구성한다."),
        ("T-P8", "Remote dipole optical-depth factorization", "amplitude nuisance와 pole direction response가 어떤 조건에서 분리되는지 정리한다."),
        ("T-P9", "Remote quadrupole low-SNR set", "noisy spin-2 remote field에서 point axis 대신 confidence region을 구성하는 theorem을 증명한다."),
        ("T-P10", "Coherent fraction identified set", "r=g+(1-g)b+e moment model과 general convex extension의 sharp interval을 증명한다."),
        ("T-P11", "Cluster/exchangeable remote rank", "shared primordial modes와 reused reconstruction noise 하에서 valid cluster-level finite rank 조건을 증명한다."),
        ("T-P12", "E-optimal rank reopening", "candidate response vectors의 convex design에서 minimum singular value를 최대로 하는 SDP와 dual certificate를 제시한다."),
        ("T-P13", "Finite-window coherent-mode bridge", "multi-window velocity operator가 homogeneous mode를 식별하는 rank condition과 no-go region을 증명한다."),
        ("T-P14", "Simulator-form envelope", "여러 forward simulators의 discrepancy를 nuisance feasible set으로 통합할 때 coverage 보존 조건을 증명한다."),
        ("T-P15", "SBI contraction attribution", "weak identified set 대비 posterior contraction을 prior/model/data restrictions로 분해하는 information inequality를 제안한다."),
        ("T-P16", "Native shell-pole limit", "native Bianchi transfer의 FLRW limit가 CAMB/CLASS shell-pole process로 수렴하는 conformance theorem을 증명한다."),
        ("T-P17", "Native local/global decomposition", "paired boosted/unboosted native runs의 component decomposition과 noncommuting transfer remainder를 bound한다."),
        ("T-P18", "Common latent joint region", "모든 probe가 동일 latent state를 공유할 때 marginal product envelope보다 sharp한 joint support image를 증명한다."),
    ]
    lines = ["# External-Fusion Theorem and Proof Backlog", ""]
    for i, title, text in items:
        lines += [f"## {i} — {title}", "", text, "", "**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.", ""]
    (DOCS / "08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md").write_text("\n".join(lines), encoding="utf-8")


def write_lowell_program():
    content = dedent(r'''
    # Redshift/Depth-Resolved CMB Low-ell Pole Programme

    ## 1. Four distinct objects

    The symbol `pole(z)` is forbidden without a type tag.  The programme uses:

    1. `ShellSourcePole[ell,z_bin]`: the pole of a registered line-of-sight source contribution in a redshift shell.
    2. `CumulativeObserverPole[ell,z_max]`: the pole after accumulating source shells to depth `z_max`, with the local observer endpoint carried separately.
    3. `RemoteDipolePole[z_bin]`: the CMB dipole seen at remote electron locations, reconstructed through kSZ tomography.
    4. `RemoteQuadrupolePole[z_bin]`: the remote CMB quadrupole, reconstructed through pSZ statistics.

    These objects cannot be added or compared without a registered bridge and their full cross-covariance.

    ## 2. Scientific discrimination target

    A local boost is an observer-end boundary transformation.  A coherent global source is present in remote fields and in source-shell transfer.  Local structure is strongest at shallow depth and follows the density/velocity field.  The decisive programme therefore combines:

    \[
    \mathcal O = \{p_\ell^{\rm local},\ p_\ell^{\rm shell}(z),\ v_{\rm eff}(z),\ q_{\rm eff}(z),\delta_g(z)\}
    \]

    rather than comparing one present-day dipole amplitude with one bulk-flow number.

    Registered summary families include

    \[
    A_\ell(z_i,z_j)=|\hat p_\ell(z_i)\cdot\hat p_\ell(z_j)|,
    \]

    cumulative pole drift, remote/local mean-axis separation, cross-ell alignment, power-tensor eigen-gap, and the nuisance-projected response singular spectrum.  Oriented dipoles use a signed dot product; unoriented quadrupole/octupole axes use an absolute dot product.

    ## 3. Track-I simulation stack

    ### Stage I-A — dependency-free reference

    Use `src/htt_ext/lowell` and `src/htt_ext/remote` to validate rotation, reality, source-superposition, coverage and abstention gates.  This stage is never a cosmological transfer result.

    ### Stage I-B — FLRW line-of-sight shell transfer

    - CAMB: baseline CMB spectra, source windows and CMB/source cross-correlations.
    - CLASS: independent perturbation and transfer output.
    - nanoCMB or another readable line-of-sight implementation: source-term audit and shell-sum oracle.
    - healpy/S2FFT: correlated shell alm generation and rotations.

    Redshift bins are frozen before data use.  SW, Doppler, early ISW, late ISW and observer endpoint are stored separately.  Two shell refinements must reproduce the total low-ell transfer and stable identified pole regions.

    ### Stage I-C — LSS, foreground and survey windows

    - GLASS: correlated lightcone density/lensing/tracer shells.
    - PySM3 or selected PanEx products: Galactic foreground complexity.
    - NaMaster/pspy: masked-sky spectra and covariance baselines.
    - S2WAV/S2FFT: directional and differentiable morphology.
    - optional WebSky/PM subsets: non-Gaussian and velocity-field reality checks.

    ### Stage I-D — remote fields

    Implement the remote dipole/quadrupole kernels and mock quadratic estimators following the kSZ/pSZ literature.  Optical-depth bias, galaxy-electron response, foregrounds and estimator mean field remain explicit nuisances.

    ## 4. Actual-data comparison ladder

    1. **Local present-observer pole:** official Planck PR3 SMICA/Commander/NILC/SEVEM maps and common masks.  Map products are one sky and are treated as a nuisance family, not independent replications.
    2. **Remote dipole summary:** Planck + unWISE velocity-reconstruction constraints and, where public products permit, an independent reimplementation.  The ACT+DESI velocity-reconstruction measurements provide a higher-S/N external comparison but have different tracer/window/foreground assumptions.
    3. **Remote quadrupole summary:** the Planck/ACT + unWISE/CIB pSZ bispectrum constraints are incorporated as a low-S/N identified region, not a zero field.
    4. **LSS shell comparison:** GLASS/COFFE and public galaxy maps/catalo gs predict the local-structure contribution and redshift dependence.

    Evidence tiers are `PAPER_SUMMARY`, `PUBLIC_BANDPOWER_OR_MAP`, and `FULL_RECONSTRUCTION_CODE`.  A lower tier cannot masquerade as a higher tier.

    ## 5. Local-boost/global-tilt hypotheses

    - `H_LOCAL`: known observer boost plus FLRW primordial/LSS fields.
    - `H_LSS`: local density/velocity field and survey selection without global coherent source.
    - `H_GLOBAL_PHENO`: adversarial coherent source family used only in Track I.
    - `H_GLOBAL_NATIVE`: native Bianchi/multi-fluid transfer, Track II only.
    - `H_MIX`: superposition of local, LSS, systematics and global components.
    - `H_UNKNOWN`: contamination outside the model list; must yield inadequacy/abstention.

    `H_GLOBAL_PHENO` is not a substitute for `H_GLOBAL_NATIVE`.  Its role is to design and stress-test the statistical machinery before the solver arrives.

    ## 6. Track-II native upgrade

    The native solver must output shell-resolved T/E/B transfer, remote observer dipole/quadrupole fields, frame/tetrad metadata and error estimates.  Paired boosted/unboosted runs establish the local endpoint response.  Only then can a Bianchi family/mode redshift-pole atlas and geometry-level response quotient be constructed.

    ## 7. Strict success criteria

    - Rotation covariance error below 1e-9 for the reference pole implementation.
    - Physical shell totals agree across CAMB/CLASS/readable oracle within preregistered tolerance.
    - Pole region coverage reaches the registered 95% target with a 99% binomial lower bound at least 0.93.
    - Confusable or superposed sources trigger abstention rather than forced global labels.
    - Mask/foreground/map-product variation is contained in the reported region.
    - Remote-field amplitude claims expose optical-depth bias; low-S/N bins do not receive point poles.
    - Actual-data statistics, bins and source family are frozen before unblinding.
    - Track-I outputs never emit Bianchi family or geometry claims.
    ''').strip() + "\n"
    (DOCS / "05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md").write_text(content, encoding="utf-8")


def write_handoff():
    content = dedent('''
    # Track Boundary and Native Solver Handoff Contract

    Track I may consume FLRW Boltzmann codes, lightcone/LSS simulators, phenomenological source injectors and real CMB/LSS products.  It may report response rank, source-confusion, identified sets, coverage and actual-data consistency.  It may not emit a Bianchi family posterior, native anisotropic transfer validation or geometry identification.

    Track II requires an authenticated `SolverDeliveryReceipt` containing source and environment hashes, tetrad/frame conventions, harmonic and spin phases, time/redshift coordinate, T/E/B transfer, recombination/reionization, conservation, FLRW exact null, Bianchi-I analytic benchmark, convergence and an independent oracle.

    `python experiments/track_boundary_validator.py --track II` must exit 3 until the receipt exists.  A synthetic or mock receipt is a blocker fixture, never a scientific unlock.
    ''').strip() + "\n"
    (DOCS / "06_TRACK_BOUNDARY_AND_NATIVE_SOLVER_HANDOFF.md").write_text(content, encoding="utf-8")


def write_literature():
    content = dedent('''
    # Web Literature and Software Context

    Verified for planning on 2026-07-22.  These sources position adapters and data recipes; they are not substitutes for repository-local result receipts.

    ## Core software

    - GLASS, Generator for Large Scale Structure: https://github.com/glass-dev/glass and arXiv:2302.01942.
    - CAMB and CAMB Sources: https://github.com/cmbant/CAMB and https://camb.info/sources/.
    - CLASS: https://github.com/lesgourg/class_public.
    - S2FFT/S2WAV: https://astro-informatics.github.io/s2fft/ and https://astro-informatics.github.io/s2wav/.
    - NaMaster: https://github.com/LSSTDESC/NaMaster.
    - CVXPYlayers: https://cvxpylayers.org/.
    - sbi and sbibm: https://sbi-dev.github.io/sbi/ and https://sbi-benchmark.github.io/.
    - Planck Legacy Archive: https://pla.esac.esa.int/.

    ## Remote CMB fields

    - Deutsch et al., remote dipole and quadrupole quadratic estimators, arXiv:1707.08129.
    - Cayuso et al., simulated remote-dipole reconstruction, arXiv:1806.01290.
    - Bloch & Johnson, Planck + unWISE velocity reconstruction, arXiv:2405.00809.
    - ACT + DESI large-scale velocity reconstruction, JCAP 2025/05/057.
    - Krywonos et al., Planck/ACT + unWISE/CIB pSZ remote-quadrupole constraints, arXiv:2607.16071.

    ## Interpretation

    The remote dipole field is the CMB dipole observed at other spacetime locations and is accessible through kSZ tomography.  The remote quadrupole field is accessible through pSZ statistics.  They provide the direct redshift dimension needed to distinguish an observer-end boost from a source coherent across the past light cone, subject to optical-depth and foreground nuisance modelling.
    ''').strip() + "\n"
    (DOCS / "07_WEB_LITERATURE_AND_SOFTWARE_CONTEXT.md").write_text(content, encoding="utf-8")


def write_catalog():
    lines = [
        "# Executable Asset Catalog",
        "",
        "Core commands run with `PYTHONPATH=src`. Optional scripts fail explicitly when their third-party dependency or data file is absent.",
        "",
        "| Asset | Purpose | Command | PR use |",
        "|---|---|---|---|",
        ("`experiments/rotation_covariance_test.py` | pole SO(3) covariance | `PYTHONPATH=src python experiments/rotation_covariance_test.py` | PR-251"),
        ("`experiments/lowell_shell_poles_demo.py` | shell/cumulative reference trajectories | `PYTHONPATH=src python experiments/lowell_shell_poles_demo.py` | PR-252"),
        ("`experiments/binning_stability_demo.py` | detects reference-DGP shell instability | `PYTHONPATH=src python experiments/binning_stability_demo.py` | PR-253/257"),
        ("`experiments/shell_kernel_conservation_demo.py` | additive shell-kernel conservation gate | `PYTHONPATH=src python experiments/shell_kernel_conservation_demo.py` | PR-253"),
        ("`experiments/planck_map_family_compare.py` | Planck map-family one-sky nuisance comparison | `PYTHONPATH=src python experiments/planck_map_family_compare.py --map SMICA=... --map COMMANDER=... --mask ...` | PR-258"),
        ("`experiments/local_boost_global_tilt_benchmark.py` | source discrimination reference | `PYTHONPATH=src python experiments/local_boost_global_tilt_benchmark.py` | PR-256/264"),
        ("`experiments/remote_fields_demo.py` | remote dipole/quadrupole toy | `PYTHONPATH=src python experiments/remote_fields_demo.py` | PR-259–261"),
        ("`experiments/pole_response_rank_demo.py` | finite-difference source response SVD | `PYTHONPATH=src python experiments/pole_response_rank_demo.py` | PR-263/268"),
        ("`experiments/coherent_fraction_demo.py` | set-valued coherent fraction | `PYTHONPATH=src python experiments/coherent_fraction_demo.py` | PR-265"),
        ("`experiments/planck_lowell_poles.py` | optional actual Planck pole extraction | `PYTHONPATH=src python experiments/planck_lowell_poles.py MAP.fits --mask-fits MASK.fits` | PR-258"),
        ("`experiments/plugin_probe.py` | optional plugin availability | `PYTHONPATH=src python experiments/plugin_probe.py` | PR-247/248"),
        ("`experiments/adaptive_scan_evalue_demo.py` | anytime-valid exploration gate | `python experiments/adaptive_scan_evalue_demo.py` | PR-273"),
        ("`experiments/track_boundary_validator.py` | Track I/II enforcement | `python experiments/track_boundary_validator.py --track II` | PR-248/274"),
        ("`experiments/run_all.py` | reference suite | `PYTHONPATH=src python experiments/run_all.py` | all"),
    ]
    (DOCS / "09_EXECUTABLE_ASSET_CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme():
    content = dedent(r'''
    # HTT External-Fusion Round-3 Bundle

    This self-contained planning and reference-code bundle integrates external cosmology software with HTT's response-rank, partial-identification, coverage and source-discrimination framework. It continues the proposed roadmap at **PR-247** and adds a dedicated **redshift/depth-resolved CMB low-ell pole programme** for distinguishing an observer-end local boost from finite-depth local structure and a coherent global source.

    The core reference suite needs only NumPy and SciPy. External cosmology packages are fail-closed optional plugins: a missing package creates a blocked capability receipt, never a toy result stamped as an external result.

    ## Main documents

    - `docs/01_HOSTILE_REFEREE_STEELMAN_EXTERNAL_FUSION.md`
    - `docs/02_ADVOCATE_STEELMAN_UPGRADE_EXTERNAL_FUSION.md`
    - `docs/03_EXTERNAL_FUSION_PR_ROADMAP_20260722.md`
    - `docs/04_PUBLICATION_READINESS_MASTER_CHECKLIST_EXTERNAL_FUSION.md`
    - `docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md`
    - `docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`
    - `docs/09_EXECUTABLE_ASSET_CATALOG.md`
    - `docs/10_PACKAGE_VALIDATION.md`

    Machine-readable cards live in `pr_cards/`, `PR_GATE_MATRIX.json`, `HOSTILE_ADVOCATE_MATRIX.json`, `configs/` and `schemas/`.

    ## Quick start

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-core.txt
    make validate
    ```

    `make validate` checks the frozen release manifest. After intentionally modifying the bundle, review the diff and use `make freeze` to generate a new manifest.

    Probe optional integrations:

    ```bash
    make plugin-probe
    ```

    Candidate package groups are in `requirements-profiles/*.in`. They are deliberately not frozen locks: each PR must choose and pin exact versions after its official example and license checks.

    ## Local htt_base overlay

    Install non-destructively under `external_fusion_round3/` inside a local checkout:

    ```bash
    python tools/install_into_repo.py --repo /path/to/htt_base --dry-run
    python tools/install_into_repo.py --repo /path/to/htt_base --apply
    cd /path/to/htt_base/external_fusion_round3
    make validate
    ```

    Add `--include-context` only when the bundled historical planning references are needed inside the checkout.

    ## Low-ell pole reference commands

    ```bash
    PYTHONPATH=src python experiments/rotation_covariance_test.py
    PYTHONPATH=src python experiments/lowell_shell_poles_demo.py
    PYTHONPATH=src python experiments/shell_kernel_conservation_demo.py
    PYTHONPATH=src python experiments/local_boost_global_tilt_benchmark.py
    PYTHONPATH=src python experiments/remote_fields_demo.py
    ```

    Optional Planck commands require user-supplied official FITS files and `healpy`:

    ```bash
    PYTHONPATH=src python experiments/planck_lowell_poles.py MAP.fits --mask-fits MASK.fits
    PYTHONPATH=src python experiments/planck_map_family_compare.py \
      --map SMICA=SMICA.fits --map COMMANDER=COMMANDER.fits --mask MASK.fits
    ```

    These Planck scripts are quicklook adapters. Publication use requires matched mask/foreground/null calibration under the relevant PR gates.

    ## Track boundary

    Track I may use FLRW simulators, LSS mocks, remote-field phenomenology and actual-data summaries, but it may not emit Bianchi family or geometry claims. Track II remains intentionally blocked until a real native Bianchi Boltzmann `SolverDeliveryReceipt` passes `schemas/solver_delivery_receipt.schema.json` and all independent benchmark gates.
    ''').strip() + "\n"
    (ROOT / "README.md").write_text(content, encoding="utf-8")


def main():
    write_hostile()
    write_advocate()
    write_roadmap()
    write_checklist()
    write_proofs()
    write_lowell_program()
    write_handoff()
    write_literature()
    write_catalog()
    write_readme()
    matrix = {
        "schema": "htt.external_fusion_round3.pr_matrix.v1",
        "pr_count": len(PRS),
        "prs": [{**pr, "native_solver_required": pr["track"] == "II", "pass_gates": COMMON_PASS + pr["specific_pass"], "fail_gates": COMMON_FAIL + pr["specific_fail"] + (["native solver receipt missing -> exit 3"] if pr["track"] == "II" else [])} for pr in PRS],
        "hostile": [{"id": h[0], "title": h[1], "text": h[2], "advocate": a[1]} for h, a in zip(HOSTILE, ADVOCATE, strict=True)],
    }
    (ROOT / "PR_GATE_MATRIX.json").write_text(json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "PASS", "pr_count": len(PRS), "hostile_count": len(HOSTILE)}, indent=2))


if __name__ == "__main__":
    main()
