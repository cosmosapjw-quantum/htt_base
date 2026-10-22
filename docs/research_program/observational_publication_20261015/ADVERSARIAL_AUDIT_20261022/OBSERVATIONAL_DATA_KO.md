# 관측자료 및 외부 입력 계약

2026-10-22. 공개·무인증 경로 우선. 파일 크기는 identity/용량 계획 정보이며 다운로드 상한이 아니다.
사용자가 밝힌 외장하드 여유 2 TB 이상은 예산 한도가 아니다. 실제 mount와 free space를 확인하고
기존 reserve 2 GiB 및 스트리밍 공간 검사를 유지한다. raw FITS/archive/PDF는 Git에 넣지 않는다.

| 필요한 입력 | 확보 상태/공개 경로 | 다음 과학적 소비 |
|---|---|---|
| Quaia G<20 catalogue | [Zenodo10403370 v1.0.0](https://zenodo.org/records/10403370), 99,786,240 bytes; 이번 세션 미다운로드 | Gaia source_id join, 적색편이와 표본 분리 |
| Quaia NSIDE64 G<20 상대 선택 지도 | 같은 record, 400,320 bytes; 실제 다운로드·hash/schema 확인 | 선택/마스크 nuisance; 절대 inclusion probability로 역가중 금지 |
| Quaia selection template ZIP | 같은 record, 879,199 bytes; 실제 CRC/7개 NumPy 지도 확인 | 먼지·별·scan depth 등 nuisance; 음수 template값을 확률로 읽지 않음 |
| Gaia proper motion와 source별 covariance | 기존1,614,173행 캐시 먼저 재사용; 부족한 source_id만 [공개 Gaia Archive](https://gea.esac.esa.int/archive/)에서 anonymous TAP | pmra/pmdec, errors, correlation, source quality와 selection cohort 확인; 전체 TAP 재실행 금지 |
| source 간 astrometric covariance 또는 qualified nuisance law | Table2 compressed ICRS covariance 확보; 완전한 공간계통오차 공분산은 아님 | 고차 VSH/scan/selection hypermodel과 coverage; 위치 covariance를 PM covariance로 대체 금지 |
| Pantheon+ 실제 magnitude/redshift 표준화와 PV source model | 이미 받은 catalogue/covariance/row IDs 재사용; [공식 DataRelease](https://github.com/PantheonPlusSH0ES/DataRelease) | m_b_corr,zHD,zHEL의 같은-source transform과 fixed-data derivative 분리 |
| CF4 contributor/parent-selection/calibration law | 기존628target/627scored+host crosswalk 재사용; full export/law 미확보 | selected-cohort likelihood 또는 source-supported bounds; row survival fraction만으로 전체 포함확률 추정 금지 |
| matched Planck total-output/null maps 및 연산자 | 기존 PR3/PR4 cache 우선; [ESA NPIPE](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/NPIPE_maps), [NERSC](https://portal.nersc.gov/project/cmb/planck2020/) | observed와 null에 같은 mask/beam/weights/polarization/foreground treatment, whole-sky realization IDs |
| polarized Bianchi family/history atlas | source-qualified 공개 payload 아직 미확보 | B02 전용 blocker; 여기서 solver/ODE 생성 금지 |

기본 새 묶음은 101,065,759 bytes(약101.07 MB,96.38 MiB).
이 세션에서 받은 두 보조 파일 합은 1,279,519 bytes, 남은 catalogue는99,786,240 bytes다.
소유자 캐시와 이 세션 캐시는 별개이므로 local에서는 receipt를 먼저 대조한다.
모든 후속 자료의 총량은 확정할 수 없다. Planck realization 수와 선택한 product에 따라 달라지며,
이미 존재하는 자료를 다시 계산한 다운로드 예상량에 더하지 않는다.

```bash
python scripts/htt_fetch_open_inputs.py \
  --manifest docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/ACQUISITION_MANIFEST.json \
  --data-root /mnt/extdrive/workdir/htt_open_data --fetch
```

명령 실행 전 실제 외장 mount를 확인한다. `--budget-gib`를 추가하지 않는다.
manifest의 `expected_bytes` 및 MD5는 upstream 제품 identity 검사다.
다운로더는 SHA256 receipt를 남기며 ZIP은 CRC만 스트리밍 검사하고 추출하거나 코드를 실행하지 않는다.
checksum/형식 통과가 source selection/physical likelihood 승인인 것은 아니다.

Quaia 선택 FITS에는 COORDSYS가 없고 NSIDE64/RING이 있다.
현재 author repository `4c4b258b9a89c03c782bd731a1ae3dcdc8ff2409`의
selection producer는 ra/dec를 `hp.ang2pix(...,lonlat=True)`로 binning한다.
이는 equatorial 해석과 일치하지만 2023 release 생성 commit과의 동일성은 아직 확인되지 않았다.
분석 전에 이 연결을 확인한다. [검사 결과](data/QUAIA_SCHEMA_RESULT.json),
[현재 producer 근거](data/PRODUCER_BINDING.json).

## 이번에 실제 읽은 새로운 primary 문헌의 사용

- [Klioner et al.2021,2012.02036](https://arxiv.org/abs/2012.02036), A&A649A9,
  DOI10.1051/0004-6361/202039734: observer aberration과 Table2 파라미터/상관.
  PDF Table2를 직접 확인했다. 요약 가속도 covariance를 cosmic-fluid A covariance로 바꾸지 않는다.
- [Brown,Bastian,Klioner2025,2503.03389v1](https://arxiv.org/html/2503.03389v1):
  BCRS/ICRS/observer coordinate acceleration 해석.
- [Nguyen & Murray2026,2605.30367v3](https://arxiv.org/html/2605.30367v3):
  고차 angular nuisance를 포함한 분석에서 기존 formal uncertainty보다 넓은 범위가 가능함.
  검색기의 unversioned stale v1 숫자를 쓰지 않았다. marginal interval만으로 joint covariance를 만들지 않는다.
- [Quaia v1.0.0](https://zenodo.org/records/10403370): 상대 선택 지도라는 release의 명시적 주의와 파일 metadata.
- [Horstmann et al.,2111.03055v2](https://arxiv.org/html/2111.03055v2):
  observer/source distance 변환의 비교 근거. 이번 finite test는 명시한 bolometric 실험에 한정한다.
- [Springob et al.2014](https://doi.org/10.1093/mnras/stu1743),
  [6dFGSv 설명](http://www.6dfgs.net/vfield/veldata.pdf): 보다 단순한 선택 cohort 대안.
  정확한 데이터 payload URL은 아직 검증하지 않았으므로 auto-fetch 목록에는 넣지 않았다.
  CF4와 중첩되므로 독립 거리 표본으로 결합하지 않는다.

Exa/SciSpace는 후보·버전 검색에, primary paper/release와 실제 파일은 수치·제품 계약에 사용했다.
Wolfram의 유한 boost algebra 대조는 theory/WOLFRAM_CHECK.json에 있으며,
Wolfram 한 축의 계산을 전체 CAS 또는 관측 검증으로 표현하지 않는다.
