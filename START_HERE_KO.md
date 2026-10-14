# HTT/MES 다운로드 대체 인계본

## 바로 연구 이어받기
이 ZIP을 새 폴더에 풀고 local Codex에 LOCAL_CODEX_START_KO.txt를 전달하세요.
checkpoints/I1, checkpoints/I2에는 기존 두 연구 체크포인트의 파일을 그대로 풀어 넣었습니다.
하네스, 선별 코드/출처, 누적 연구 요약, I1/I2 검증 결과와 I3 프롬프트가 포함됩니다.
대용량 원본 백업 3개의 바이트 전체는 이 경량 ZIP에 포함되지 않습니다.
현재 단계는 I2 DEFENDED_CONDITIONAL이며, 실측 검증이나 사용자 PC 복원 완료를 뜻하지 않습니다.

## 원본 백업까지 모두 받기
1. HTT_FULL_01.zip부터 HTT_FULL_12.zip까지 이 README와 같은 폴더에 놓으세요. 조각 ZIP은 풀지 마세요.
2. 이 폴더에서 `python3 reassemble_full.py`를 실행하세요.
3. 각 조각과 전체 SHA-256이 검증된 뒤 HTT_MES_LOCAL_CODEX_FULL_20260928.zip이 생성됩니다.
4. 생성된 전체 ZIP을 새 폴더에 풀고 handoff_i2/README_KO.md에 따라 복원하세요.
전체 ZIP SHA-256: 740658f22e9a60be5cbefcd2ea4d6e8725f1f35585a96b02a2d845071d1af672
약 1.6GB 이상의 여유 공간이 재조립에 필요하고, 이후 압축 해제 공간은 별도입니다.
스크립트는 기존 출력 파일을 덮어쓰지 않으며, 조각 누락/손상 시 중단합니다.
경량 인계본만으로 전체 원본 백업을 확보했다고 보고하지 마세요.
