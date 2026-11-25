# R116-B: source-owned REC species thermal evolution

범위: 기존 R115 T1의 bounded implementation. REC 원본 Rust에 H I, He II,
He III 및 W=(1+fHe+xe)Tm 상태와 matched backward Euler 적분을 구현.
원본 2012 HYREC C의 output-only instrumentation을 이용하여 105859 native
species/thermal rows를 재생성했으며 기존 stdout은 byte identical.
HeI scalar rate 27개 C oracle 비교의 최대 상대오차 3.406e-16.
HeIII kinetic rate는 원본의 Saha 이력만으로 확보되지 않는다. supplied
모드는 explicit caller rates가 있는 경우만 허용한다. NativeHeI의 방향별
scalar rate 평균은 조건부 근사이며 polarized spectral transfer가 아니다.

REC commit cb1685271e32223400df0817895952895087ef31:
research/r116_species_thermal/ 에 원본 생성 스크립트, 여섯 compressed
reference slice, oracle, 21 standalone trajectory receipt, 로그를 보존.
137 tests pass. 작은 matched increment의 Newton tolerance 결함 수정.
N=1024,2048,4096에서 최종 successive difference ratio는 helium
xe/Tm 2.075/1.990, H 2.037/2.023, thermal 1.891/2.000.

BASS commit 4e30aeb722a132f87ddfbc44d0f22247d4c6f47e:
--recombination species-thermal --species-reference TSV --feedback recoil.
같은 reference가 초기 species/absolute anchors/opacity를 소유한다.
실제 material sky, host proper density, Hubble, gamma, accepted discrete
density expansion을 전달. 이전 step의 charge offset을 다음 opacity에
반영; negative shifted opacity reject (no clipping).
Thermal and binding ledger is tracer only; matching correction is not
physical heat. T2 global stage-coupled chemistry is not implemented.
228 regular tests + 3 examples pass; 12 mild-tilt/FLRW CLI checks pass.
H/He nuclei 0; charge residual 1.110e-16; discrete continuity 3.400e-16
(by construction); thermal ledger max 6.859e-31 J/H; max Gauss 8.152e-8;
max scaled algebraic residual 1.855e-6 (stiff helium FLRW).
Short helium overlap ray/grid/continuum endpoint agreement recorded.
Old R116-A grid_I and continuum_I six TSVs each byte identical.
Finite mild-tilt checks are not a high-l/long-history or parameter-domain
accuracy certificate. The H-window endpoint refinement is near second
order in this particular case, not a proof of T2.

No changes to REI or R78 science DAG. Independent native subagent review
not run (no native agent capability exposed). Next bounded task:
R117-REC-BASS-COUPLED-STIFF-SDIRK2-01, stage-consistent opacity/species solve,
stiff limits and nonuniform time refinement. HeIII kinetic authority,
phase joins and active thermal/binding spectral exchange remain separate.
