# NSC self-adversarial audit (2026-07-13) — novelty / significance / correctness

Owner-requested three-axis self-adversarial audit of all research results to date
(rev-r190..r198 headlines + EGS3 program), executed as the full loop
`self-discover -> step-back -> metacognitive self-ask -> CoVe -> adversarial self-ask ->
web CRAG -> CCoT -> multi-agent debate -> PDR` with a 29-agent workflow
(`wf_49ea55ab-643`: 10 CoVe correctness lanes, 6 web-CRAG novelty lanes, 3-referee
significance panel, 3-axis attacker/defender/judge debates, 1 completeness critic;
29/29 completed, 0 errors) plus in-session independent verification of every load-bearing
finding.

**Internal dev-tier ledger. NEVER rendered into any report (no-meta-dev rule).**

## Headline outcome

REJECT-AND-RESUBMIT as shipped. Two P0s (both independently verified in-session):

- **P0-1**: the K5-MV bulk-flow headline (405 km/s, 4.4-5.4 sigma) is radial-monopole leakage
  from a physically impossible deep-shell systematic in the CF4 Vpec column; monopole-nulled
  MV gives 94.8 km/s, p = 0.647 (0.46 sigma). Verified bit-for-bit (09_inhouse_verification.md).
- **P0-2**: the fsigma8 = 0.40 +/- 0.02 headline divides by pk_corr = (370/308)^2 whose premise
  is refuted — 370 is the NONLINEAR halofit sigma_v (CAMB linear = 309.0; EH98 correct to 0.3%).

Plus 15 P1s. Theorem/framework/consistency-null sectors survive at tier. Remediation is
REV-R199+ scope, owner sign-off required; nothing was modified by this audit.

## File map

| File | Stage |
|---|---|
| 00_scope_and_self_discover.md | 1 self-discover (claim inventory, lane selection) |
| 01_step_back_principles.md | 2 step-back (pre-registered per-axis criteria) |
| 02_metacognitive_self_ask.md | 3 metacognitive self-ask (bias design) |
| 03_cove_correctness_ledger.json | 4 CoVe + 5 adversarial self-ask + 7 CCoT (10 lanes, raw) |
| 04_web_crag_novelty_ledger.json | 6 web CRAG (6 lanes, raw, with search evidence) |
| 05_significance_panel.json | referee panel (3 reports) |
| 06_debate_judgments.json | debate judge rulings (3 axes) |
| 06b_debate_transcripts.json | attacker/defender full transcripts (6) |
| 07_completeness_critique.md | completeness critic (14 gaps) |
| 08_final_referee_report.md | 8 PDR (meta-adjudication, verdicts, ranked must-fix) |
| 09_inhouse_verification.md | in-session independent verification V1-V4 |
