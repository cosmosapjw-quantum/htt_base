# HTT/MES 카탈로그 재사용·초기 연구 계보 조사

2026-09-28. 이 보고서는 **첨부 archive의 복원·정적 조회·선별 정독**이다. 과거 과학 주장이나 실행 PASS를 현재 재승인하지 않는다. 최신 GitHub 조사와 2026-09-16 이후 R9/R10·MES R1/R2는 별도 현재 조사와 합쳐야 한다.

## 1. DB를 다시 펼치지 않고 재개할 수 있다

`03_CATALOG.zip`의 `history/HTT_CATALOG_SCAN_57ecfe21_PORTABLE.zip`을 안전한 상대경로로 복원했다. 내부 44개 항목, 247,403,459 bytes이며, manifest에 등재된 43개 파일은 모두 크기·SHA-256이 일치한다. 기존 조회 스크립트를 읽은 뒤 MES/local boost/response 3개 조회를 실제 실행해 exit 0과 결과를 확인했다.

- 카탈로그 배포 commit: `57ecfe2176bf8be28327edf500a4ca5136c6b15b`.
- R8 snapshot membership 기준: `efc5f30666b96782f946375551f0068bb3a30f74`.
- 역사적 원 DB: 10,820,591,616 bytes, SHA-256 `42942d7485d4650075b0ec6baa2059d8b8e715bea9c3d59d772c301854d20e25`.
- 이번 작업은 원 DB와 57개 압축 조각을 materialize하지 않았다. 이번에 삭제한 DB도 없다. 이미 보존된 portable locator/excerpt가 충분하므로 원 DB 복원·삭제를 반복할 이유가 없다.
- `observed_commit`은 대표 관찰 commit이다. 최신 버전·최초 도입 commit이라는 의미가 아니다. 카탈로그에는 현재 원격 refs의 권위가 없다.

21개 gzip JSONL을 모두 순차 파싱했고, 행 수가 보존된 verification receipt와 일치했다. SQL schema와 실제 export 키를 함께 보존했다. 원 SQLite FTS·전체 `contents.parsed`·모든 scientific source를 복원한 것은 아니다.

| 메타데이터 | 이번 읽기 행 수 |
|---|---:|
| sources | 99 |
| refs | 6,799 |
| commits | 79,880 |
| commit aliases | 839 |
| snapshots | 225 |
| snapshot members | 1,081,074 |
| trees | 1,178,659 |
| files | 305,527 |
| filesystem | 591,920 |
| gaps | 268 |
| selected-file edges | 47,477 |
| acquisition candidates | 1,235 |

8개 topic excerpt의 행 수는 CF4 43,349; CMB product law 14,198; full Q/O 23,705; MES 54,754; local/global 24,605; JWST 4,648; DESI/Union3 12,032; Teff 18,682다. 주제 간 중복이 있으므로 고유 성과 수로 합산하지 않는다. 원 DB의 1,675,716 records와 10,901,211 edges 전체를 이 excerpt가 대체하지 않는다.

## 2. 최소 code/theory locator 묶음

전체 305,527개 파일 locator의 **경로**를 검색했다. 넓은 후보는 15,931개 역사적 파일 버전이다. source=`htt_base`, 직접 코드/문서, `htt/`, `docs/`, `tests/` 경로로 좁힌 MES·local/global·response·optics 관련 후보는 36개 고유 경로 / 66개 버전이다. 이 중 R8 snapshot membership이 확인되는 버전은 26개다. 경로 패턴 기반 선정이므로 완전한 semantic dependency closure나 전수 코드 정독이라고 부르지 않는다.

`catalog/targeted_source_paths.json`은 각 버전의 `file_id`, 대표 commit, Git blob, content SHA-256, R8 membership을 보존한다. `catalog/selected_file_locators.jsonl.gz`에는 source ID/origin/container/root를 포함하는 넓은 목록이 남아 있다.

| 후속 질문 | 우선 읽을 역사적 경로 | 적용 경계 |
|---|---|---|
| MES 전제와 계수 | `htt/src/common/mes_theorem_authority.py`; `htt/obsstat/egs3_mes_rederivation.py`; `htt/bass/observational/planck_mes_bounds.py` | current main의 실제 consumer와 버전을 대조한다. |
| radiation jet에서 tensor shear | `htt/src/common/r7_radiation_jet.py`; `docs/research_reports/theory_packs/K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md` | 관측 jet/미분/remainder가 제공되는지 별도 판정한다. |
| anchor/response와 joint feasible set | `htt/src/common/anchored_response_geometry.py`; `htt/src/common/identified_set.py`; `htt/obsstat/egs3_identified_set.py` | 같은 자료로 만든 anchor를 독립 likelihood로 곱하지 않는다. |
| local observer와 global field | `htt/htt/htt/infer/local_global_discrimination.py`; `htt/htt/htt/infer/mes_local_global_response.py`; `htt/htt/htt/infer/r7_depth_response.py`; `htt/bass/observer/observer_boost.py` | 대표 catalog path는 실제 최신 tree path와 다를 수 있다. |
| 기존 tensorized 연구 묶음 | `docs/research_reports/HTT_TENSORIZED_MES_RESPONSE_SYNTHESIS_20260903.md`; `docs/codex_handoff/mes_tensor_research_integration/RESEARCH_SYNTHESIS.md` | 과거 종합과 R9/R10/R1/R2 사이에 convention/claim crosswalk가 필요하다. |
| 조건부 MES geometry | `docs/research_reports/theory_packs/T3_CONDITIONAL_MES_GEOMETRY_THEOREM_PACK.md` | norm 외부영역과 Einstein–matter reachable set은 다르다. |

2026-09-16 이후 reloptics/CMB kinematic redshift/R9/R10는 9월 12일 catalog로 최신성을 판단할 수 없다. 그들의 원문은 RESEARCH archive 및 현재 원격 tree에서 찾아야 한다. catalog의 optics/redshift excerpt 10건은 이전 기반만 제공한다. `targeted_topic_excerpts.json`의 observer/global, response/identifiability, tensor/derivative 쿼리는 각각 최대 80건을 보존했고 이 cap을 명시했다.

## 3. 초기 archive 계보와 읽기 범위

`02_EARLY_ARCHIVE.zip`의 두 내부 ZIP을 중심으로 ZIP 재귀 목록을 만들었다. 총 28개 archive occurrence 가운데 독립 ZIP identity는 25개이고 3개는 byte-identical duplicate다. 11,254개 ZIP member 메타데이터를 기록했다. 두 TAR(gz)도 payload를 추출하지 않고 716개 member metadata를 읽었다. TAR 내부 추가 archive는 재귀 조사하지 않았다. 이 수는 11,970개 고유 연구 산출물을 의미하지 않는다.

선택한 원문 31개 / 502,843 bytes를 `early_selected/`에 복원하고 SHA-256과 archive locator를 기록했다. 이 중 다음 자료를 실제로 읽었다.

| 자료 | 실제 읽은 깊이 |
|---|---|
| `HTT_CATALOG_SCAN_57ecfe21_KO.md` | 전문 |
| `HTT_RESEARCH_INPUT_FOUNDATION_57ecfe21_KO.md` | 본문 §§1–5와 산출물 개요 |
| 초기 archive `00_READ_FIRST_KO.md`, `CHRONOLOGY_AND_RESUME_KO.md`, `TRANSCRIPT_COVERAGE.json` | 전문 |
| 78-candidate `THEOREM_INDEX_KO.md` | 78개 항목 전체 |
| `PROOFS_AND_COUNTEREXAMPLES_KO.md` | 범위/규약/집계, P17/P18/P22/P23 전문; 전체 증명집 정독 아님 |
| tensor–tilt `RESEARCH_MEMO_KO.md` | §5.1–5.3, §6.2–8.3, §9; 나머지는 제목/목록 스캔 |
| 독립 감사 `audit_v3/report-source.md` | tensorized MES 절 §§Q/O fibre/공동식별 전문, 나머지 제목/관련 문장 검색 |

이전 archive는 전체 대화 export가 아니다. 자체 coverage는 38개 가시 항목(전사17, 요약5, 발췌15, 도구요약1), 원 message ID/timestamp 부재를 명시한다. 2026-08-30 integration branch 생성 이후 새 scientific delta push가 미완료였다는 과거 기록도 보존된다. 이 사실을 현재 repo 상태로 옮기지는 않는다.

## 4. 최신 연구에 이어 붙여야 할 과거의 실질 내용

78 후보의 당시 판정은 61 PROVED, 5 PROVED_STRENGTHENED, 5 CORRECTED, 5 REFUTED, 2 NOT_A_DEFINED_PROPOSITION이었다. 이는 기존 정리·응용·lemma·후보의 합동 판정이며 66개 신규 독창적 정리의 발견도, 이번 재증명도 아니다. 아래 내용은 실제 읽은 과거 논증에 관한 **archived derivation** 상태다.

1. **C07의 nuisance 구분은 후속 식별 논증에 필수다.** `O=B_Q beta+O_perp`, `O_perp:Q=0`이면 contraction으로 beta가 유일하다. 비식별 반례는 unrestricted `O_int∈STF3`에 대해 `beta→beta+d`, `O_int→O_int−B_Q d`가 관측을 보존한다는 것이다. 실제 primordial octupole의 직교성은 물리 전제로 확보되지 않는다. 그러므로 일반 CMB에서 projection beta를 곧바로 peculiar velocity라고 부를 수 없다.
2. **Ideal Bianchi-I inverse는 이미 더 강한 형태로 존재한다.** 동일 emission time·등방 blackbody·collisionless achromatic 조건에서 `F(n)=T(n)^−2`는 strictly positive quadratic sphere function이고, 역으로 모든 그런 F가 유일한 finite beta 및 SPD M을 갖는다(P18). 따라서 ell>2 residual=0은 Bianchi I의 원인을 식별하지 못한다. nonzero residual만 이상화된 가정의 결합을 반증한다. absolute positive T, monopole/dipole와 관측 연산자가 필요하다. endpoint tensor B를 현재 instantaneous shear로 바꾸려면 별도 history law가 필요하다.
3. **Local boost와 congruence tilt는 이전부터 구분돼 있다.** 점의 velocity가 같아도 `∇u`가 다르면 expansion/shear/acceleration/vorticity는 다르다. 기존 geodesic MES 식에 beta만 대입해 tilted bound로 바꿀 수 없다.
4. **Remote/local 분리에 실제 response rank가 필요하다.** 알려진 `d_s=beta+g_s u`의 rank6는 g_s가 모두 같지 않은 것과 동치다. 일반 알려진 선형 nuisance 아래서는 whitened nuisance projection 이후 rank가 조건이다(P22). 자유 optical depth amplitude가 전역 amplitude와 곱으로 들어가면 rescaling degeneracy가 남는다. 실제 kSZ/pSZ response 확보를 이 대수 정리가 대신하지 않는다.
5. **방사속도는 rotation을 보지 못한다.** `n^T W n=0`이므로 affine radial channel은 bulk3/expansion1/shear5를 full-rank 조건에서 식별하지만 antisymmetric rotation은 식별하지 못한다. astrometric B1도 frame spin과 겹칠 수 있다.
6. **Coverage 의미도 이전에 고정돼 있다.** pointwise test inversion은 true-point coverage다. 전체 identified set 동시 포함으로 승격할 수 없다. data-dependent MES body의 uncertainty는 joint law 또는 별도 error budget에 넣어야 한다(P23).
7. **Representation의 no-go·개선 이력을 보존해야 한다.** SO(3)와 O(3)를 혼동한 STF3 even-invariant completeness, nontrivial stabilizer까지 unique equivariant full frame을 덮는 주장, 일반 intrinsic-O 비식별의 잘못된 표기는 각각 수정/반증돼 있다. Q/O 전체 12성분의 generic rotation quotient는 9차원이며 scalar norm bound로 방향·handedness를 만들 수 없다.
8. **수축 fibre와 안정성은 별도 자산이다.** 과거 audit는 fixed q에서 Q/O contraction fibre의 4차원 kernel, sphere boundary의 sharp 1/2-Hölder sensitivity를 추적했다. 이 결과는 noisy q 변화까지의 안정성이나 물리 response의 식별을 자동으로 주지 않는다.

이상의 결과는 최신 optical observer map과 joint response 연구의 출발점을 좁힌다. 새 연구가 이미 존재하는 ideal inverse나 rank theorem을 다시 최초 발견으로 제시하지 않도록 하고, 실제 새 부분을 **관측 연산자·프레임·congruence·미분/곡률/경계 데이터의 결합**에 둬야 한다.

## 5. 종료 조건과 미해결 범위

카탈로그 복원/조회·전체 locator quick scan·선별 목록 확보는 완료했다. 전체 과학 코드와 모든 증명 전문을 읽거나 검증했다고 주장하지 않는다. 독립 early archive에 남은 source는 미삭제이며 현재 저장소 mutation은 없다. 원 DB 부재는 blocker가 아니다.

최소 후속은 (i) 위 locators와 현재 main/code-catalog/theory-catalog heads 비교, (ii) Sept16+ reloptics/MES R1/R2의 정의·관측자·가정 crosswalk, (iii) local/global 식별에서 실제 response kernel과 nuisance 공간이 어디서 새로 고정됐는지 확인이다. 이 중 선택된 주장 사슬이 원문·현재 consumer·증거까지 연결되면 같은 archive 전체 재감사를 중단하고 그 물리 질문을 전개하면 된다.

검증 원장: `catalog/REUSE_VALIDATION.json`, `catalog/QUERY_REPLAY.json`, `catalog/SELECTION_SUMMARY.json`, `EARLY_ARCHIVE_COVERAGE.json`, `EARLY_ARCHIVE_MEMBER_INVENTORY.jsonl.gz`, `EARLY_TAR_MEMBER_INVENTORY.jsonl.gz`, `CATALOG_READING_LEDGER.json`.
