# HTT/MES 연구결과를 Local Codex로 전달하기

이 묶음은 이전 백업 원본 3종과 I1·I2 연구 checkpoint를 함께 전달한다. 저장소 전체 clone, 대화 전문, production solver 설치본은 아니다. 본문에서 말하는 검증은 파일 identity와 복원 동작 검증이며 물리적 주장 승격을 뜻하지 않는다.

## 1. 전달 범위

| 포함물 | 용도 | 기본 복원 동작 |
|---|---|---|
| `backups/HTT_MES_THREAD_BACKUP_20260928_01_RESEARCH.zip` | 누적 연구 원본 372개 payload와 manifest | 외부 ZIP 한 계층만 `research_backup/`에 복원 |
| `backups/HTT_MES_THREAD_BACKUP_20260928_02_EARLY_ARCHIVE.zip` | 이전 대형 archive 2종과 manifest | `early_archive_backup/`에 archive 파일로 복원; 내부 재귀 해제 없음 |
| `backups/HTT_MES_THREAD_BACKUP_20260928_03_CATALOG.zip` | R8 시점 portable catalog·query·locators | 기본 압축 유지; `--catalog` 때만 portable exports 복원 |
| I1 checkpoint ZIP | 최신 main 조사, 선별 원문, I1 유도·계산·독립 검토 | `checkpoints/I1/`에 복원 |
| I2 checkpoint ZIP | 이번 이론 루프의 결과·근거·다음 결정 | `checkpoints/I2/`에 복원 |
| `handoff_i2/`와 `DELIVERY_MANIFEST.json` | 전달 계약, 복원 도구, 파일별 SHA-256·크기 | delivery 폴더에서 직접 읽음 |

대화 링크 본문은 회수하지 못했으므로 **대화 전문 포함**으로 해석하지 않는다. 원격 저장소는 전체 브랜치 목록과 선별 원문을 보존한 것으로, 195개 브랜치 전체 checkout이 아니다. 20종 프로젝트 첨부의 Rust toolchain·vendor·xAct·별도 BASS 번들은 연구결과 archive와 구별되는 선행 도구/자료다. 이 전달물에 중복 합치지 않았으며 필요한 runtime 작업에서 별도로 사용한다.

## 2. 다운로드 후 확인

파일당 512MiB 제한 때문에 전체 ZIP은 `.zip.part01`, `.zip.part02` 두 조각으로 제공한다. 두 조각과 `HTT_MES_LOCAL_CODEX_FULL_20260928.zip.sha256`을 같은 폴더에 받는다. 두 조각은 개별 ZIP이 아니므로 먼저 아래 순서로 연결한다. 아래는 Linux 예시다. 이미 존재하는 delivery/restore 폴더를 재사용하지 않는다.

```bash
cd "$HOME/Downloads"
cat HTT_MES_LOCAL_CODEX_FULL_20260928.zip.part01 \
    HTT_MES_LOCAL_CODEX_FULL_20260928.zip.part02 \
    > HTT_MES_LOCAL_CODEX_FULL_20260928.zip
sha256sum -c HTT_MES_LOCAL_CODEX_FULL_20260928.zip.sha256
mkdir HTT_MES_DELIVERY_20260928
unzip -n HTT_MES_LOCAL_CODEX_FULL_20260928.zip -d HTT_MES_DELIVERY_20260928
```

복원 도구는 인자 없이 실행하면 **검증만** 한다. manifest에 열거된 모든 파일의 byte 수와 SHA-256을 확인하며 실제 압축 해제는 하지 않는다. 아래 `--restore`도 이 검증을 포함하므로 바로 복원할 때는 별도 검증 명령을 먼저 반복할 필요가 없다. 외부 SHA 파일은 전송 오류 확인용이다. SHA와 payload를 함께 바꿀 수 있는 공격자에 대한 서명 인증은 제공하지 않는다.

복원할 때는 명시적으로 새 경로를 지정한다.

```bash
python3 HTT_MES_DELIVERY_20260928/handoff_i2/restore_handoff.py \
  --restore --destination "$HOME/Downloads/HTT_MES_RESTORED_20260928"
```

portable catalog exports도 필요하면 첫 복원 명령에 `--catalog`를 추가한다. 이미 복원했다면 기존 폴더를 덮어쓰지 않고 다른 새 `--destination`을 사용한다. 기본 복원에서는 전체 10.82GB DB를 풀지 않는다. `--catalog`도 약 247MB의 JSONL gzip·CSV·SQL·query 스크립트까지만 꺼내며 DB를 생성하거나 JSONL gzip을 재귀 압축 해제하지 않는다.

분할 다운로드, 재결합 ZIP, 풀린 delivery 원본은 각각 약 0.8GB다. 여기에 기본 복원 약 0.6GB, catalog 선택 시 약 0.5GB의 임시·출력 여유가 추가로 필요하다. 모두 같은 디스크에 유지한다면 **최소 4GB 여유**를 권한다. 이는 큰 DB 복원 용량이 아니다.

도구는 경로 이탈·symlink·중복 경로·DB 파일 추출·512MiB 초과 단일 member·2GiB 초과 archive 해제를 거절한다. 기존 destination을 덮어쓰지 않으며 복원 실패 시 남은 임시 디렉터리 경로를 출력한다. 그 디렉터리를 성공한 복원으로 사용하지 않는다. 신뢰되지 않은 동시 프로세스가 같은 새 출력 디렉터리를 바꾸는 환경은 지원 범위가 아니다.

## 3. Local Codex에 읽힐 파일

기존 `/home/cosmosapjw/Dropbox/bianchi/htt_base`에서 Codex를 연 뒤 다음처럼 요청한다. 실제 다운로드 위치가 다르면 두 경로만 바꾼다.

```text
다음 파일을 읽고 그 실행 계약에 따라 HTT/MES 연구를 이어가라.
/home/cosmosapjw/Downloads/HTT_MES_DELIVERY_20260928/handoff_i2/LOCAL_CODEX_START_PROMPT_KO.txt

DELIVERY_ROOT=/home/cosmosapjw/Downloads/HTT_MES_DELIVERY_20260928
RESTORED_ROOT=/home/cosmosapjw/Downloads/HTT_MES_RESTORED_20260928
EXISTING_REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
```

Codex의 첫 작업은 receipt와 I2의 현재 결론을 확인하고 기존 repo의 branch/HEAD/status를 읽는 것이다. 이 전달의 조사 기준 commit은 `cc162c804eecb3c588efc6edadbe057a8a67301f`, tree는 `f14a536e7934d99bbe67489d1b81e5da0079cb09`다. 현재 main이 달라졌다면 target 관련 delta만 대조한다. 기존 사용자 변경은 유지하고 새 clone/worktree, 자동 checkout/reset, 자동 push를 하지 않는다.

Local Codex가 이어받을 다음 연구의 과학적 내용은 **I2 checkpoint의 최종 보고서·연구 상태·독립 검토 판정**이 결정한다. 여기의 복원 문서가 그 판정을 덮어쓰지 않는다. I1의 잔차 유도 성공을 관측적 식별이나 physical shear 측정 성공으로 승격하지 않는다.

## 4. 로컬 실행을 마친 뒤

`RETURN_HANDOFF_TEMPLATE_KO.md`를 채워 실제 변경·실행·미수행·다음 gate를 구분한다. 실행 로그와 source/commit identity를 결과 ZIP의 manifest에 연결한다. 원본 backup 3종은 다시 복제하지 않고 이번 delivery manifest의 경로·크기·SHA-256으로 참조할 수 있다. 실제 업로드 acknowledgement 없는 원격 백업을 완료로 쓰지 않는다.

복원 도구는 작은 fixture로 검증되어 있으며 실행 증거는 `RESTORE_TEST_RESULTS.json` 및 `restore_tests.log`에 있다. 원본 payload를 로컬에서 실제 복원해 얻는 `RESTORE_RECEIPT.json`은 사용자 환경의 별도 증거다. 도구 테스트 성공과 사용자 환경 복원 성공은 다른 주장이다.
