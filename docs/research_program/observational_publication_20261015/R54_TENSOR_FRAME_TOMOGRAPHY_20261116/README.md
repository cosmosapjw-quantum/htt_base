# R54 tensor frame tomography (2026-11-16)

Branch `research/r54-tensor-frame-tomography-20261116` on `research/r50-observed-convergence-20261115`. Claim ceiling C0. Authority order: `AGENTS.md`, canonical DAG in
`docs/codex_handoff/pr_backlog.yaml`, then this directory.

| file | role |
|---|---|
| `R54_REPORT_KO.md` | referee verdict, executed results, decisions (Korean) |
| `THEORY_LOOPS.md` | equation register, core calculus, six theory loops |
| `THEOREMS.md` | statements proved without data (T1 to T9, L1, L2), attributions and the prior-work re-check; written by hand, contains no result number |
| `RESULTS/R54_L1_TYPE1_TE.json` | CMB T+E type-I history functionals (executed) |
| `RESULTS/R54_L5_LOWZ_FRAMES.json` | first pass on committed R36 multipoles with the ideal-sky body; count-dipole excess (executed; CF4 part superseded) |
| `RESULTS/R54_L05_CF4_EXACT.json` | CF4 at catalogue level: log-distance estimator, exact LCDM body, nulls under three zero-point nuisance models, hemisphere-step scan (executed) |
| `RESULTS/R54_L05_COSMIC_COV.npz` | cached pair-sum covariance O C_uu O^T (linear and damped) with row labels |
| `RESULTS/R54_L05_STEP_SCAN_COV.npz` | cached pair-sum covariance of the per-family hemisphere steps over the split-axis grid |
| `RESEARCH_DAG.json` | cloud and local nodes, cards, order, stop rule |
| `LOCAL_AGENT_CONTRACT.json` | conventions, equations, API, node specifications |
| `MUTATION_GATES.json`, `MUTATION_GATE_RECEIPT.json` | declared gates and proof that they bite |
| `SELF_AUDIT_PROTOCOL.json` | anti-drift audit for the local agent |
| `ADVERSARIAL_BENCHMARK_SPEC.json` | published targets, tolerances, scoring |
| `PR4_BYPASS_CONTRACT.json` | why and how PR4 is not a blocker |
| `HISTORY_AUDIT.json`, `HISTORY_PR_INDEX.json` | inventory, read coverage, reinterpretations |
| `state/` | research state, evidence ledger, hypothesis graph, decision log, negative results |
| `LOCAL_AGENT_RESTART_PROMPT.txt` | prompt for the local agent |
| `LOCAL_AGENT_HANDOFF_UPDATE.txt`, `HANDOFF_UPDATE.json` | theorem addendum after the programme stop: what arrived, how to bring it into the working branch, addendum tasks R54-A1 to R54-A4 |
| `scripts/r54/handoff_merge.py` (repository root) | merge helper of the update: preflight, apply, finish; never resolves a hand-written file |
| `INDEPENDENT_REVIEW.json` | independent review record |

Rebuild: `python scripts/r54/run_r54_cmb_type1.py && python scripts/r54/run_r54_lowz_frames.py && python scripts/r54/run_r54_cf4_exact.py && python scripts/r54/build_r54_contract.py build`
(the CF4 run reads the two cached pair sums; on 2 cores a cache miss costs about 12 minutes for the main sum and under 2 minutes for the scan).
Tests: `PYTHONPATH=htt/src:htt:. python -m pytest tests/r54 -q`.
