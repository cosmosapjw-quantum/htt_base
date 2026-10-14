# SF08 numerical worker handoff

Parent is sole production writer. Worker writes only `/tmp/htt_sf08_worker_20261014`.
Requested `gpt-6.1-sol/high`; observed `UNKNOWN`.

Initial contract `PREDECLARED.json` fixed pooled baseline MCSE target .015 km/s/Mpc from the maximum n=16 H MCSE .020267233322206746. Required total count ceil(16*(.020267233322206746/.015)^2)=30, rounded to32 (16old+16new) per generating law. One narrower shared calibration case .02mag fixed16new perlaw. No counts or numerical tolerances changed after results.

Seed defect: initial baseline SLOT namespace overlapped the initial width PRE namespace. Exact old schedule intersection16 seeds is in `FIRST_FAILURE_SEED_OVERLAP.json`; initial width profile2catalogues are excluded from final statistics. Parent explicitly approved correcting only width seedbase to2026401408; old contract/driver/raw/logs remain. Repaired contract `PREDECLARED_REPAIRED.json` seals retained24baseline rows and declares the corrected seeds before generation. Original completed baseline rows are not rewritten or rerun. One raw-only interrupted checkpoint is replay-compared against unchanged generator arrays before resuming its fit.

Run command:

```bash
OPENBLAS_NUM_THREADS=1 /usr/bin/python3 -B /tmp/htt_sf08_worker_20261014/run_cf4_precision_repaired.py --contract /tmp/htt_sf08_worker_20261014/PREDECLARED_REPAIRED.json --output /tmp/htt_sf08_worker_20261014/campaign_repaired
OPENBLAS_NUM_THREADS=1 /usr/bin/python3 -B /tmp/htt_sf08_worker_20261014/analyze_cf4_precision.py
```

Scientific input guards reuse pinned crosslaw driver, selected-law source, intake, rawloader, original generator, packet and CF4 release inputs. Every new rawNPZ precedes fits. Every completed row records rawSHA and its original contract seal; reused rows additionally have exact rowSHA in repaircontract. Same generated catalogue receives both law fits. Generator law fixed percase. All failures remain recorded, no outcome-based resampling/stopping.

Tests: original affected6crosslaw tests PASS4.178s; scoped repair3checks PASS (counts/target/scenario unchanged except widthseed;64distinctplanned seeds;source drift rejected before output mutation). Primary frozen1e-6 truth/fitpoint logL convergence; first2perlaw/case audited at384/96 versus512/128; index0 refits at384/96 compared with512/128. Measured control thresholds H .001 km/s/Mpc and B .05 km/s were declared before outcomes.

R/C actual flow: R1 calculable conditional selection-sensitivity question; R2 reuse selected-law formulas, sourcepins, original16pair report/catalogues; R3 endpoint/conditional scope and empirical-selection input blocker; R4 pairedmean/MCSE and widthcontrast estimands; R5 derive MCSE SD/sqrt(n), independent-case variance sum and count forecast; R6 same-context formula/grid controls, separate independent review pending parent; R7 actual Python generation+paired fits; R8 fixed-count target evaluation; R9 analysis/report+reusable computations; R10 this handoff. C1 frozen inputs/target; C2 etaweights->generator->twofits->pairedsummary; C3 same quadrature, bounded scaled optimizer, finitewidth; C4 retainedprofile and perrow checkpoints; C5 scratch executor; C6 actual affected tests; C7 generator support/moments, samecatalogue comparisons; C8 grid/refit and Monte Carlo errors; C9 pending fresh parent reviewer; C10 candidate handoff, no scientific admission/publication.

Skill context used:

- `/home/cosmosapjw/.codex/plugins/cache/created-by-me-remote/physmath-research-loop/1.3.0/skills/physmath-research-loop/SKILL.md`
- Same skill's `references/POLICY_INTEGRATION.md`
- Same skill's `references/THEORY_LOOP.md`
- Same skill's `references/CODING_LOOP.md`
- Same skill's `references/SUBAGENT_MODE.md`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/.agents/skills/htt-scientific-code-validation/SKILL.md`

No nested delegation; parent performs independent review and production integration. Scientific admission `NOT_EVALUATED`; prior HOLD unchanged. Artifact class numerical output and experimental evidence; no empirical CF4 completeness/native solver/ODE claim.
