# R90 / Quaia G20.0의 신규 관측 소스 정합성 검증

공식 Zenodo Quaia selection_function_NSIDE64_G20.0.fits 와 기존 read-only Gaia/Quaia 실제 source join (692,154 rows)를 정확히 대조했다.

- 기존 join: /mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz
- 신규 다운로드는 기존 ~/Downloads/htt_r90_minimal_inputs/ 안의 공식 Quaia map 2종 + template ZIP (1,679,839 bytes)뿐이다.
- 692,154개 source의 (RA,Dec)로 생성한 ICRS HEALPix NSIDE64 RING index는 기존 join의 pixel_ring64와 **전부 동일**하다.
- 모든 source의 기존 selection_relative와 공식 G20.0 map[pixel] 값의 최대 절대 오차는 **0**이다. join의 모든 source G magnitude는 20.0 미만이다.
- G20.5 공식 map은 별도의 release-matched selection function이다. 기존 G20.0 join으로 대조하면 값은 다르다. 이것은 잘못된 source 결합을 피하기 위한 결과이고, G20.5의 독립 카탈로그 연결 검증 완료가 아니다.
- 따라서 **G20.0 source selection의 좌표계 및 값 동일성은 동일 소스에 한해서 검증됨**. G20.5는 별도 카탈로그 검증 대기.
- 공식 문서 https://zenodo.org/records/10403370 에서 selection function 값은 상대적인 selection indicator이며 absolute probability가 아니다.
- Gaia scan law, source correlation, normal-frame optical transfer, independent AGN/null, physical Pi/G_F 는 이 검증만으로 해소되지 않는다.

재현:
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/r90/qualify_quaia_frame.py --check

검증 출력: QUAIA_COORDINATE_QUALIFICATION.json. 원본 R78, R89, 기존 extdrive source 변경 없음.
