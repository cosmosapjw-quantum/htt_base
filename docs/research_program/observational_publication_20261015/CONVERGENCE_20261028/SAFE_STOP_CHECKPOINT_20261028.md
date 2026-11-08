# Report and safe-stop checkpoint — 2026-10-28

The first-stage English report passed independent scoped review and the existing controller recorded `convergence_baseline_report`. It is a report-production result; it does not change original physical acceptance, which remains 17/42, with the separate analytic alternate at 18/42. It is not the final integrated report or a submission.

The existing campaign `R23-whole-42-solver-free` remains bound to identity `2b9c0b11dab33758e0ad8c7711376ae29949a345e111df7820fcc8c7cac75ea4`. The active state alias is `.agent-harness/runtime/r23-continuous/STATE.json`, resolving at this checkpoint to `/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/LIVE_STATE.json`. This is a pointer to the existing state, not a state export or a new campaign. The original task/event history and allocations remain in that state.

`R36-06-PR4-MORPHOLOGY` is checkpointed at 56/100 consumed, verified Commander maps; no aggregate p-value is established. Checkpoint sequence 3 identity `2444b2cd4da79d7691e8a17dc7a09855769be94dbb31ff9def27fc66f4fe66cd`. Worker receipt: `/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/WORKER_HANDOFF_003.json`; host corroboration: `/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/HOST_CORROBORATION_003_V2.json`. Existing source/cache/partial products and prior attempts remain on the external disk. Resume only this same task and packet using the existing controller's `prepare-acquisition-resume` and `ack-acquisition-resume` protocol and a reviewed identity-bound plan; do not start a new acquisition or reset attempts.

R37-01 radiation, R37-02 kinematics, R37-03 Hubble, R37-04 classification and R37-05 final report are ready in the existing controller, but were not run in this stop request. Remaining original holds and resume conditions stay in the live state. No native Boltzmann solver, ODE evolution, main merge or journal submission was performed.

The report, source, claim map, six-paper crosswalk, frozen 109-ID legacy scope, and original receipts are in `products/R37-00-FIRST-REPORT/`. Small conditional first48 analysis evidence and the independent report-review chain are in `audit_evidence/`; their path maps preserve the original receipt identities. Large raw FITS and live state remain outside Git.

A controller startup hook may report `ValueError` because the actual state alias resolves outside the repository runtime directory. Campaign name and content identity were independently reconciled; do not replace or reinitialize the state to suppress this advisory. The repeated full-file checkpoint validation is a measured transition-time bottleneck.

Report execution was requested on `gpt-6-sol/high`; the independent final review was requested on `gpt-6-astra/xhigh`. Their actual runtime identities were not independently observed and remain `UNKNOWN`. The final review receipt is retained in `audit_evidence/report_review_chain/`. The initial focused-test import error and the initial checkpoint host-receipt schema rejection were corrected; the raw review and checkpoint histories remain preserved. The candidate manifest's pending-review field describes its creation-time state; the subsequently recorded independent review and live controller are the completion evidence.

For a future continuation, first inspect the existing state without mutating it:

```bash
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json summary
```

Reconcile the active pointer's external resolved path and pending packets before any dispatch. Reapply the owner's `--prefer-task`, `--defer-task` and `--no-discovery` options in the current handoff, and resume R36-06 only through its recorded cooperative checkpoint protocol. Do not treat this stop checkpoint as a new campaign or a final report release.

Validation for this checkpoint: the 13 convergence-controller tests passed with `PYTHONPATH=scripts/codex_harness`; the canonical DAG validator and mirror `--check` passed; seven report artifact hashes and all 138 audit path-map hashes matched. The report had an independent 12-page LaTeX build and figure checks. A full staged whitespace check reports original CRLF CSV and literal generated log whitespace in retained raw evidence; a scoped whitespace check of the edited prose, TeX and status files passed. These evidence bytes were retained unchanged rather than normalized.
