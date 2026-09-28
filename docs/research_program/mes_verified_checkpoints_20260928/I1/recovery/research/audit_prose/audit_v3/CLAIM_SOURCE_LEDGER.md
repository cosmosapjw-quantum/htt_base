# 핵심 주장과 원문

접근일 2026-09-08. 저장소 주 기준 5702024e06eff4979087f07f86ee7131d13961ac.

| 주장 | 직접 근거 | 상태 |
|---|---|---|
| MIO reference null이 상관을 보존하지 않음 | htt/src/common/mio_joint_measure.py, matched_null_distribution | 정적 소스 + derived Gaussian 반례 |
| pair Pi 방향의 행 순서 의존 | 같은 파일 _apply_pairing | 정적 소스 + 두 pair 반례 |
| GF는 box envelope | 같은 파일 feasible_range_GF | simplex 직접 유도 |
| selection weight가 precision에 진입 | htt/src/common/bulkflow_likelihood.py | 정규화식 직접 비교 |
| hierarchy 계약은 상태 schema | htt/htt/htt/infer/joint_survey_hierarchy.py | 전문 판독 |
| signed GF ratio endpoint 결함 | htt/obsstat/egs3_gf_interval.py, blob f0827837db208c5dada3120e3aeac349b2f910b6 | exact source + 직접 유도, runtime 미실시 |
| valid/invalid collision 경로 공존 | src/collision/thomson.rs; htt/bass/collision/thomson_pstf.py | 독립 정적 검토 + kernel 유도 |
| finite tilt consumer 연결 미입증 | hierarchy/ver2_native_integrator.py; collision/electron_frame.py | 해당 consumer 구간 판독 |
| fixed-q fibre 안정성 | QO_CONTRACTION_FIBRE_GEOMETRY_20260907.md; QO_FIBRE_HAUSDORFF_STABILITY_20260907.md | 독립 수학 검토 |
| 최신 MES의 response-set 구조 | HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md sections 5–6 | 직접·독립 판독 |
| legacy BF 논증 불충분 | docs/manuscript/ch07_results.tex 667–673 | 직접·독립 판독 + counterexample |
| neutrino 관측 기여율 근거 부족 | docs/manuscript/ch05_teff_corrections.tex 1497–1608 | 직접·독립 판독 |
| TAM/Teff 비교 범주 차이 | 같은 파일 865–946 | 직접·독립 판독 |

## 웹 원문

- Maartens, Ellis & Stoeger, 1995, Limits on Anisotropy and Inhomogeneity from the Cosmic Background Radiation. https://arxiv.org/abs/astro-ph/9501016 . 원논문 abstract·metadata 확인; 제1권의 상세 원문 근거도 보존.
- Nilsson et al., 1999, An almost isotropic cosmic microwave temperature does not imply an almost isotropic universe. https://arxiv.org/abs/astro-ph/9904252 . 원논문 abstract page 확인.
- Stoeger, Araujo & Gebbie, 1999, The Limits on Cosmological Anisotropies and Inhomogeneities from COBE Data. https://arxiv.org/html/astro-ph/9904346v1 . MES 측도와 rms 변환·가정 구간 확인; 보고서의 원문 보조 근거.
- Copi, Huterer & Starkman, 2003 preprint / 2004 publication, Multipole Vectors. https://arxiv.org/abs/astro-ph/0310511 . representation 선행연구.
- Land & Magueijo, 2004, Multipole invariants and non-Gaussianity. https://arxiv.org/abs/astro-ph/0407081 . invariant decomposition 선행연구.
- Ritzwoller, Romano & Shaikh, 2024 preprint, Randomization Inference: Theory and Applications. https://arxiv.org/abs/2406.09521 . permutation/randomization 조건의 문헌 맥락. 보고서의 구체적 null 반례는 직접 유도.
- Mandel, Farr & Gair, 2018 preprint / 2019 publication, Extracting distribution parameters from multiple uncertain observations with selection biases. https://arxiv.org/abs/1809.02063 . selection 정규화의 원논문 맥락.
- Saadeh et al., 2016, How isotropic is the Universe? https://arxiv.org/abs/1605.07178 . mode별 제약 차이의 직접 근거.

GitHub web open은 DisabledError. GitHub 연결 get_repo·고정 blob fetch는 성공. arXiv 1807.04817 open은 실패하여 이번 새 판정의 확인된 원문으로 세지 않았다. 기존 제1권의 문헌 주장은 원기록으로만 보존한다.
