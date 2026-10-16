# htt_base 공개 데이터 로컬 수집과 검증

2026-10-16 KST. 목적: `/mnt/extdrive/workdir`에 원본의 SHA-256 및 요청 URL을 봉인하면서 필요한 공개 관측자료를 내려받는다. **이 패키지는 현재 ChatGPT 샌드박스에서 네트워크 다운로드를 수행하지 않았다.** 로컬 실행 전 각 URL의 TLS 연결 가능성과 서비스 상태를 확인한다. 수치/구현 단위 테스트만 수행했다.

## 0. 의존성 및 마운트 확인

```bash
# 사용자의 Ubuntu local 터미널에서. 외장 드라이브가 실제로 마운트되어 있는지 먼저 확인.
mountpoint /mnt/extdrive || true
df -h /mnt/extdrive
mkdir -p /mnt/extdrive/workdir
cd /mnt/extdrive/workdir
# 전달받은 HTT_OPEN_PHYSICS_DATA_THEORY_20261016.zip을 이 디렉터리에 둔 후:
unzip -q HTT_OPEN_PHYSICS_DATA_THEORY_20261016.zip -d htt_open_physics_20261016
cd htt_open_physics_20261016
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q tests
```

`requests`나 root 권한은 필수가 아니다. 다운로드는 Python 표준 라이브러리 HTTPS 스트리밍으로 수행한다. 대용량 파일은 4 MiB 블록 처리하며 `.part` 경로로 이어받기 지원, 서버가 Range를 무시하면 처음부터 안전하게 다시 받는다. 다운로드가 성공해야만 원자적으로 최종 파일로 이동한다. `DOWNLOAD_RECEIPTS.json`에 URL, SHA-256, 크기, 시각을 기록한다. 이미 있는 파일의 해시가 receipt와 다르면 자동 덮어쓰지 않는다. 실제 release-authenticity는 공식 제공 checksum이나 원본 header와 별도 비교해야 한다.

## 1. 기본 경량 세트: CF4 원본 + PR3 온도/편광 마스크

```bash
ROOT=/mnt/extdrive/workdir/htt_open_data
python scripts/htt_data_fetch.py --root "$ROOT" --dry-run
python scripts/htt_data_fetch.py --root "$ROOT" --group cf4 --group planck_masks
python scripts/htt_data_fetch.py --root "$ROOT" --group cf4 --group planck_masks --verify
python scripts/htt_input_validate.py --root "$ROOT"
```

CF4 **VizieR 배포**의 table2(55,877), table3·table4(각 38,053) 고정폭 ASCII를 계획한다. 출판물 요약의 38,065개 그룹과 VizieR 제공 파일의 38,053행을 혼동하지 않는다. 다운로드 URL은 CDS 표준 FTP-over-HTTPS 경로로 등록되어 있지만, 여기서는 실제 HTTP 응답을 검사하지 못했다. 서비스 경로가 변경되거나 제한된다면 자동으로 다른 해석의 테이블로 대체하지 않고 오류를 보존하며 공식 [VizieR 카탈로그](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/ApJ/944/94)에서 해당 릴리스의 원본 링크를 갱신한다.

## 2. 선택적 중·대용량 Planck 원본

```bash
# SMICA 실제 T/Q/U full map: 약 1.9 GB, 추가 여유 공간 확보 필수
python scripts/htt_data_fetch.py --root "$ROOT" --group planck_full
# half mission 및 odd/even ring, 같은 물리적 하늘이므로 독립 실현 수를 늘리지 않는다
python scripts/htt_data_fetch.py --root "$ROOT" --group planck_splits
# Commander, NILC, SEVEM, SMICA-noSZ(I ONLY)
python scripts/htt_data_fetch.py --root "$ROOT" --group planck_alternates
python scripts/htt_data_fetch.py --root "$ROOT" --group planck_full --group planck_splits --verify
python scripts/htt_input_validate.py --root "$ROOT"
```

**주의:** 이 함수의 다운로드 레지스트리는 Planck PR3의 *full map, split, mask*까지만 제공한다. FFP10 999 CMB + 300 noise/systematics와 E2E 처리 전체는 하나의 작은 파일이 아니므로 하드코딩된 임의의 시뮬레이션 URL을 만들지 않았다. ESA PLA의 정확한 `dx12_v3_{method}_{cmb,noise,...}_mc_?????_raw.fits` source identity, mask, noise split, simulation ID 리스트를 먼저 `provenance/`에 기록한 뒤 선택된 조합만 추가해 다운로드한다. noise ID를 재사용한 999×300 조합은 독립 실현 299,700개가 아니다. 고유한 CMB draw와 반복된 noise realization의 dependence를 보존한다.

실제 Planck FFP10 방법·스플릿별 배포 명세: <https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps> 및 <https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Simulation_data>. ESA/IRSA의 PR3 instrument effective beams는 주파수별로 TB 규모인 것도 있으므로 PR3 CMB map의 처리용 소규모 effective beam transfer function과 원시 effective beam 전체를 분리하고 반드시 파일·메모리 요구량부터 산정한다.

## 3. 공개 이론/관측 소스 리포지터리

```bash
# AniCLASS/Bianchi, Pantheon+ 통계·covariance, CF4 bulk-flow estimator
bash scripts/htt_git_sources.sh "$ROOT"
# 각 저장소의 다운로드한 정확한 HEAD는 $ROOT/provenance/*_git_receipt.txt에 기록
```

별도 이론 solver는 AniCLASS `make class`가 가능한 환경에서 실행하되, 먼저 고정된 Git commit과 `bianchi.ini`, 열역학/편광 정의, 5개 거의 FLRW 타입의 한계를 검증한다. 이 설치/빌드는 이 샌드박스에서 실행하지 않았다. source repo가 예전에 받아진 것과 byte identity가 같은지는 저장된 SHA와 별도 확인한다.

## 4. Gaia DR3 소량 기준계 시험 표본

```bash
python scripts/htt_gaia_pilot.py --root "$ROOT" --print-query
# ESA Gaia TAP 온라인 쿼리. 원본 AGN-CRF3 전체가 아닌 TOP 10000 선택적 pilot
python scripts/htt_gaia_pilot.py --root "$ROOT" --execute
```

`agn_cross_id`와 `gaia_source`를 결합한다. 관측된 quasar proper motion은 celestial reference-frame 회전·태양계 secular aberration을 보정하는 데 사용하고 **직접 물질 소용돌이도 측정치로 간주하지 않는다.** 실제 물질 proper-motion과 별개로 거리/선택/오차/epoch를 맞춰야 K03 physical input이 된다.

## 5. 진행/복구 및 부하 분리

```bash
# SSH 세션이 끊겨도 수집을 유지하고 싶다면 사용자가 local tmux를 직접 실행
tmux new -s htt-download
cd /mnt/extdrive/workdir/htt_open_physics_20261016
source .venv/bin/activate
python scripts/htt_data_fetch.py --root /mnt/extdrive/workdir/htt_open_data --group cf4 --group planck_masks 2>&1 | tee /mnt/extdrive/workdir/htt_fetch.log
# Ctrl-b, d 로 detach, tmux attach -t htt-download로 복귀
```

`df -h`, `du -sh`, `sha256sum`, `python -m pytest`로 점검. `DOWNLOAD_RECEIPTS.json`은 원본 유효성이 아니라 **전송·바이트 기록**이다. `INPUT_STRUCTURE_AUDIT.json`은 구조 확인이고 source-selection physical gate가 아니다.

## 6. 이 패키지에 포함되지 않은 *물리적* 데이터와 확보 조건

- **H02:** EDD의 CF4 W1-band TF photometry/HI linewidth 원자료, parent detection/completeness cuts, method별 calibration priors; 기본 CF4 group composite만으로 selection infer 불가.
- **L03:** PR3 FFP10 정확한 split/foreground/noise E2E 시뮬레이션 ID와 Planck component separation processing beam. 데이터에 없는 300 noise realization을 가짜 독립 표본으로 늘리지 않는다.
- **V03/B02:** AniCLASS는 5개 거의 FLRW 타입만, BASS legacy는 bounded kinetic component. Bianchi I–IX 전체 11 타입의 validated all-m T/E/B evolution은 공개 한 패키지가 아님.
- **K03:** Gaia AGN pilot은 reference frame만. 독립적으로 보정된 galaxy radial + transverse velocity, distances, shared object crossmatch가 필요.
- **S04/K04:** Source-qualified physical likelihood/optical Jacobi transfer는 catalog 파일 자체에서 자동 생성되지 않는다.

## 공식 링크 및 출처

- CF4: <https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/944/94> / <https://doi.org/10.3847/1538-4357/ac94d8>
- Planck PR3 maps: <https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/maps/component-maps/cmb/>
- Planck masks: <https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/>
- Gaia DR3: <https://gea.esac.esa.int/archive/>
- Pantheon+ release: <https://github.com/PantheonPlusSH0ES/DataRelease>
- AniCLASS: <https://github.com/CyrilPitrou/aniclass>
- CF4 W1 TF parent catalog: <https://academic.oup.com/mnras/article/511/4/6160/6523366>
