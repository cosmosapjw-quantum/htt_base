# R96 | Three independent R1–R10 theory loops, legacy rescue and local-agent implementation prep

Date: 2026-11-22 KST. Original research branch parent a87df07da328ba6d704e7cf0d554081f52d39213. R78 authority SHA256 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11 (60 nodes/129 edges/NEXT_ID SQ-CF4), unchanged.

## Actual scoped results

**A / SQ-CF4**: Full 35,970 group, 36-coefficient H03/R36/R27 source analysis. Exact C_R36=C_PV+K4 Sigma K4^T+positive R legacy vs C_R95=C_PV+C_H03noise+J7 Sigma7 J7^T. R36-vs-R95 noise difference is indefinite, eigen [-0.903,+0.257], max element abs 0.489, so cannot add them. Woodbury low-rank GLS matches original dense/R95 numerical results. H0 variations quantify model sensitivity, not physical discovery. Physical upstream zero-point/selection/heldout absent.

**B / Planck BiPoSH null**: All 999 SMICA FFP10 original-resolution TEB harmonic checkpoints and 300 distinct noise MC reused. Corrected legacy signed L2 estimator and MC-based full covariance with predeclared shrinkage lambda .05/.20/.40: 60D conditional empirical ranks .10299/.11296/.14286; independent 150/150 split rank .17219; old diagonal R95 .25914. Significant covariance-model dependence; none of these are a calibrated Bianchi detection. Requires same pipeline beam/foreground/mask transfer and physical template.

**C / tilted Bianchi spin2**: Exact scalar/spin ±2 spherical harmonic recurrence, numerical oracle residual 1.78e-16. Sparse T/E/B m-block system for m=-2..2 and ell_max 8/16/32/60 with HyRec2+tanh visibility, constructed STF shear source. Free transport skew-Hermitian, collision quadrupole eigen (-1,-.3), k=0 and m=0 B=0. Runtime for bounded 20 models 0.55 seconds. General curved Bianchi m-mixing and physical all-m higher-moment source not yet solved.

## Source and code rescue

- Seven user-authorized roots: 94,427 physical file entries and 154,590 ZIP/small TAR members indexed read-only into private local SQLite FTS; one original REC broken ZIP remains excluded. 9 related GitHub projects/branches remotely checked; HTT active recursive API tree truncated so local Git SHA remains source authority. No private repo contents included.
- Legacy invalid BiPoSH original is preserved; maintained scripts/r96/legacy_biposh_recovered.py repairs estimator/covariance API, fails closed without source-matched MC.
- Legacy PR13AG high-L skeleton is extended by scripts/r96/spin2_mblock_extension.py, not represented as a new physical Bianchi solver. CF4 legacy method covariance crosswalk and Mayukh gamma repair trace remain source-bound.
- LEGACY_RESCUE_CROSSWALK.json maps five old code owners to corrected numerical successors and specific remaining physical defects. Existing BASS/REC/REI/R49 files are not mutated.

## Tests & reproducibility

Run scoped:
- tests/obsstat/test_r96_three_theory_loops.py
- tests/obsstat/test_r95_science_execution.py and test_r94_accel_solver_preparation.py
- original R49 seven test files, and R78 strict science authority validator.

Current scoped execution recorded 13 R96 + 28 R94–R95 + 22 R49 tests passing; R78 strict 32/32 passed. Original 60 science acceptance not promoted by any source-conditioned result. Independent native subagent delegation not available in this Chat host: NOT_RUN. This is same-session implementation review, not external independent physical referee.

## Exact resume

- THEORY_A_CF4_R1_R10_KO.md / CF4_COVARIANCE_RECONCILIATION.json
- THEORY_B_CMB_R1_R10_KO.md / CMB_MASK_BIPO_CROSSVALIDATED_NULL.json
- THEORY_C_BIANCHI_R1_R10_KO.md / SPIN2_MBLOCK_HIERARCHY.json
- R96_LOCAL_AGENT_60_NODE_DISPATCH.json for every original science ID
- LOCAL_AGENT_HANDOFF_KO.md copyable production action
- SOURCE_REUSE_AUDIT.json and GITHUB_SOURCE_AUDIT.json plus private ~/Downloads/htt_r96_private_index/source_search.sqlite

Next local-agent convergence is three concrete physics tasks, not more auditing: (i) independent pre-intercalibration CF4 likelihood source/selection, (ii) Planck mask/beam injection/matched covariance and source-equivalent MC validation, (iii) full R49 connection projected to non-axisymmetric spin harmonics with physical time-dependent source and E/B m-mixing. Keep geometry/kinematics/morphology analysis running solver-free. Full Bianchi family attribution still blocked.
