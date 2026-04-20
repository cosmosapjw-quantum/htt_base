# BASS Workspace Snapshot — 2026-04-17/18

Jiwon 의 BASS (Bianchi Anisotropy Solver / Boltzmann And Spectrum Solver) 작업
스냅샷. 이번 세션에서 ① Rust 1.94.1 toolchain 구축, ② obs_bundle.zip 에서 모든
관측값 추출·검증, ③ MASTER_PROMPT_LIST v3.4 실행 착수 준비까지 완료한 시점의
파일들을 한 곳에 정리했다.

관측 데이터 번들 (`obs_bundle.zip`, 249 MB) 과 Rust 배포 tarball (~184 MB) 은
의도적으로 **제외**했다 — 필요 시 별도 채널로 유지.

---

## 디렉토리 구조

```
bass_workspace_snapshot_20260417/
├── README.md                              ← 이 파일
│
├── session_notes/                         ← 이번 세션에서 확정된 사항
│   ├── 01_environment_setup.md              Rust toolchain 설치 / 검증 기록
│   ├── 02_observation_data_extraction.md    obs_bundle 추출 결과 / SSOT 일관성
│   └── 03_next_steps_and_recommendations.md 다음 세션 진입점 / critical path
│
├── session_artifacts/                     ← 이번 세션 생성물
│   ├── obs_master_summary.json              31 datasets 통합 요약 (24 KB)
│   ├── extract_summary.py                   번들 스키마 점검 스크립트
│   └── build_master_summary.py              master summary 생성 스크립트
│
├── dl_pipeline/                           ← 관측 데이터 파이프라인 (소스만)
│   ├── README.md, run_all.sh, requirements.txt
│   ├── config/   sources.json, planck2018_camb_params.json
│   ├── scripts/  fetch.py + 8 extractors
│   └── assets/   targets_cf4_from_desi_bgs.csv, obs_meta/ (INDEX, README, loader)
│
└── project/                               ← /mnt/project 재구조화 (95 files)
    ├── 00_manuscript/             14 files  thesis LaTeX (main, ch01-11, appendices, bib)
    ├── 01_master_plans/           14 files  MASTER/PREP prompt lists, scoreboard, handoffs
    ├── 02_design_documents/        9 files  DOC-01..04, BASS Design v1_0..v1_3, SSOT hardening, physics compendium
    ├── 03_physics_notes/          22 files  BMR, ISW, Teff, EFT, backreaction, recombination, reionization 등
    ├── 04_implementation_specs/   21 files  R-P1/RC/RE/TILT/UV, TCA, solver strategy, CAMB mapping
    ├── 05_surveys_and_updates/     7 files  consolidated surveys, field updates, Tsagas status 등
    ├── 06_audit_protocols/         2 files  PHYS-MATH_AUDIT, PHYS-MATH-CODE
    └── 07_benchmarks/              5 files  benchmark_all.csv, mz_*.csv, pareto_analysis.txt 등
```

---

## project/ 하위 그룹화 기준

**00_manuscript**
Overleaf-compatible thesis 소스. `main.tex` 가 챕터 11 개 + appendices 를
`\input` 으로 조립. `references.bib` 포함.

**01_master_plans**
실행 계획 문서. MASTER_PROMPT_LIST 의 세 버전 (v3_2_FINAL / v3_4 / v4_0),
PREP 트랙 (v2 / v3_1_REVISED), 스코어보드, v3_3 및 v34 amendments.
`project_extension_plan`, `post_bass_programme_v1.md` 가 장기 방향.

**02_design_documents**
Self-contained 설계 문서. DOC-01 (이론 기반) / DOC-02 (extension pipeline) /
DOC-03 (HTT/MIO 인터페이스) / DOC-04 (frontend) 가 v1.0 체계. BASS Design
은 v1_0 → v1_1 (longrange characteristics) → v1_3 (recomb/reion/EFT/backreaction)
순 진화. SSOT Hardening v1.0 과 Physics Compendium v1.0 이 횡단 지원 문서.

**03_physics_notes**
물리/수학 formulation. BMR framework, ISW, Teff, EFT, backreaction (angular /
length), baryon-CDM, neutrino 2차 sources, tilt² cross-terms, recombination /
reionization anisotropic extension.

**04_implementation_specs**
코드 레벨 구현 스펙. R-P1-01/02 (AniCLASS, IMEX-ARK), R-RC-01 (directional
Sobolev), R-RE-01 (EoR codes, ARTIST vs 21cmFAST), R-TILT-01/02/03, R-UV-01
(Mori-Zwanzig). TCA/UFA/RSA 대응안, 5566 DOF 스케일링, CAMB TCA ↔ PSTF mapping.

**05_surveys_and_updates**
field update 및 경쟁 구도. consolidated_research_surveys.md (313 KB) 는
마스터 서베이. field_update_2026_04_04, Tsagas controversy status,
competitive landscape, deep-research-report.

**06_audit_protocols**
PHYS-MATH 감사 루브릭 두 개.

**07_benchmarks**
R-P1-02 (IMEX-ARK), R-UV-01 (MZ kernel) 등의 원본 CSV 벤치마크와 파레토 분석.

---

## 사용법

### 세션 재개 시

```
# 1. 이 zip 전개
unzip bass_workspace_snapshot_20260417.zip

# 2. 권장 출발점
cat bass_workspace_snapshot_20260417/session_notes/03_next_steps_and_recommendations.md

# 3. critical path 노드 확정
less bass_workspace_snapshot_20260417/project/01_master_plans/MASTER_PROMPT_LIST_v3_4.md
less bass_workspace_snapshot_20260417/project/01_master_plans/IMPLEMENTATION_SCOREBOARD.md
```

### 관측값 대조

`session_artifacts/obs_master_summary.json` 이 SSOT. 필요 시
`session_artifacts/build_master_summary.py` 를 obs_bundle 재업로드 후 재실행.

### 논문 재빌드

```
cd project/00_manuscript
pdflatex -shell-escape main
biber main
pdflatex -shell-escape main
pdflatex -shell-escape main
```

---

## 이 스냅샷에서 **제외**된 것

- `obs_bundle.zip` (249 MB, /home/claude/obs/obs/)
- `rust-1.94.1-x86_64-unknown-linux-gnu.tar.xz` (~184 MB)
- 설치된 Rust toolchain 자체 (/home/claude/.rust)
- 빌드 산출물 / cargo 캐시 (/home/claude/.cargo, /home/claude/rust_tests)

이들은 모두 재생성 가능하거나, 원본 파일이 Jiwon 측에 남아있는 자산.
