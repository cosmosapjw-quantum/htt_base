# HTT/MES 전체 인계 ZIP 검증

I1·I2 원문을 일반 checkout에서 읽을 때는 [702개 파일 통합 안내](../mes_verified_checkpoints_20260928/README_KO.md)를 사용한다. 이 ZIP 검증은 원본 archive 보존의 근거이며, 해당 안내는 개별 Git 추적 파일의 경로·blob 동일성을 기록한다.

2026-09-28 KST. Owner: HTT research archive intake. Scope: original full handoff bytes, contained I1/I2 checkpoints, three backups and restore tool. Claim tier C0 archival/reproducibility only; transfer source 없음. 원본: `/home/cosmosapjw/Dropbox/bianchi/htt_base/HTT_MES_LOCAL_CODEX_FULL_20260928.zip`, SHA-256 `740658f22e9a60be5cbefcd2ea4d6e8725f1f35585a96b02a2d845071d1af672`. 이 문서의 PASS는 파일/복원 검증이며 과학적 입증이나 DB 원본 복원이 아니다.

## 실제 실행

| 검사 | 결과 |
|---|---|
| 전체 ZIP의 CRC 및 member 목록 | 19개 member, `testzip() is None`; `START_HERE_KO.md`의 전체 SHA-256과 일치 |
| `DELIVERY_MANIFEST.json` 검증 | 17개 file의 byte size와 SHA-256 모두 일치; 동봉 `restore_handoff.py`가 실제 입력을 다시 해시하여 `RESTORED` receipt를 생성 |
| 직접 포함된 세 backup ZIP과 I1/I2 checkpoint ZIP | 5개 모두 ZIP CRC 통과; member 수는 각각 373, 3, 2, 683, 19 |
| backup 내부의 중첩 ZIP | SHA-256으로 중복을 제거한 63개 ZIP(깊이 2:42, 3:19, 4:2)의 총 1,544,415,497 uncompressed member bytes를 CRC 검사; 오류 0. 이는 포함 ZIP의 내부 무결성이고 문헌·계산의 재현성 판정은 아니다. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v handoff_i2.test_restore_handoff` | 11/11 통과; path traversal, symlink, 중복, DB 추출, overwrite 및 중단 후 false success receipt 회귀 포함 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -B handoff_i2/restore_handoff.py --restore --catalog --destination /tmp/htt_mes_full_restored_validation_20260928` | 실제 새 임시 경로 복원 성공. `RESTORE_RECEIPT.json` 원문을 보존했다. `verified_files=17`, `catalog_extracted=true`, `database_restored=false`, `repository_mutated=false`. 기본 연구 373 files, early archive 3, I1 683, I2 19, catalog backup 2, portable catalog exports 44 files. |

검증 대상 delivery를 `/tmp/htt_mes_full_delivery_validation_20260928`에 별도로 풀었다. 기존 repo/DB와 사용자 수정은 건드리지 않았다. `build_i2_delivery.py`는 과거 패키지 재생성기이며 현재 원본 입력 stage를 덮어쓰거나 새 archive를 만드는 것이 이 검증의 소비 결정이 아니어서 실행하지 않았다. 백업 안의 역사적 `.py/.wl` 프로그램도 서로 다른 과거 과제를 나타내므로 임의로 모두 실행하지 않았다. 각 ZIP의 모든 파일 바이트는 CRC/manifest 범위에서 확인했지만, 모든 과거 연구 계산을 재실행했다는 뜻은 아니다.

## 과학적 상태

I1의 target `Z=σ−STF(p aᵀ)` 및 조건부 residual-known inverse는 연구 선행식이다. I2의 radiation-only, Λ=0, geodesic-normal Bianchi I의 정적 isotropic sky 반례와 독립 `(H,ρ)` 조건부 sphere는 `DEFENDED_CONDITIONAL`에 머문다. 이번 byte/restore PASS는 I2 논증의 새 독립 물리 판정이 아니며, 실제 shear, 일반 finite tilt Einstein–matter 존재, `D/Π/G`, empirical likelihood, native solver 또는 Bianchi family 판정을 만들지 않는다. 후속 I3 Gaia-CRF3 입력은 [별도 screening](../mes_i3_gaia_screening_20260928/REPORT_KO.md)에서 `HOLD_INPUT_INCOMPLETE`다.

## 등록·배포 경계

이 폴더의 `source/`는 원본 delivery의 manifest, validation, README, 복원 코드·테스트를 변경 없이 복사한 것이다. `RESTORE_RECEIPT.json`은 이 머신의 실제 별도 경로 복원 증거다. 원본 735 MiB ZIP과 세 백업은 단일 Git blob으로 GitHub에 넣지 않는다. 원본 ZIP의 byte-identical asset은 태그 `htt-mes-full-handoff-20260928`의 GitHub prerelease에 게시했다. 원격 asset 크기와 실제 다운로드 파일 769,808,802바이트가 일치하고 SHA-256도 원본과 같은 `740658f22e9a60be5cbefcd2ea4d6e8725f1f35585a96b02a2d845071d1af672`다. `PUBLICATION_RECEIPT.json`에 R1 Git ref 및 R3 asset byte readback을 분리해 기록했다. 내부 원본의 과학적 권위는 이 배포 방식에서 오지 않는다.
