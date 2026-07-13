# NSC self-adversarial audit — Stage 8: PDR (final adjudication / referee report)

_2026-07-13. Synthesized from: 10 CoVe correctness lanes, 6 web-CRAG novelty lanes, 3-referee
significance panel, 3-axis attacker/defender/judge debates, 1 completeness critic
(workflow `wf_49ea55ab-643`, 29/29 agents, 0 errors, ~2.78M subagent tokens, 444 tool calls),
plus the in-session independent verification of every load-bearing finding
(`09_inhouse_verification.md`). Internal dev-tier ledger; never rendered into any report._

## 0. Executive verdict

**As-shipped: REJECT-AND-RESUBMIT at JCAP/PRD.** Two P0 defects (both independently verified
in-session, one bit-for-bit) invalidate the two most prominent data headlines; fifteen P1s
require fixes. **The theorem/framework/consistency-null sectors survive at their claimed tiers**
(with registry-hygiene P1s), and a clear, fully-enumerated remediation path exists. The single
most significant NEW scientific output of this cycle is, ironically, produced by the audit
itself: the CF4 catalogue Vpec column carries a physically impossible deep-shell radial
monopole (−612 → −5765 km/s over r = 220–520 h⁻¹Mpc) that converts, through anisotropic sky
coverage, into a fake ~470 km/s MV "bulk flow" — a publishable systematics result about
raw-Vpec-based bulk-flow claims.

| Axis | As-shipped | Post-surgery (must-fixes executed) |
|---|---|---|
| Correctness | **2/5** (PV-sector headlines refuted; theorem sector sound) | 4/5 achievable |
| Novelty | **2/5** (data lanes confirmatory/incremental; one NEW pillar, single-sourced) | 3/5 (if IM-transfer prior-art search survives) |
| Significance | **2/5** (panel unanimous, as-headlined) | 3/5 (re-scoped corpus, debate-judge object) |

## 1. Meta-adjudication (completeness-critic items 1, 9, 14)

- **Scored object fixed**: the referee panel scored the corpus AS-SHIPPED; the debate judges
  scored the POST-CONCESSION reshaped corpus. Both are reported above under their proper
  objects; the uniform judge 3/3/3 is accepted only under the post-surgery object.
- **Census contradiction resolved**: the critic recounted `egs_results_table_v9.json` at HEAD —
  78 rows; 44 proven-tier (18 proven_gate + 14 proven_symbolic + 6 proven_seal + 6 proven);
  9 measured + 3 measured_diagnostic + 5 measured_synth + 2 measured_partial + 1 measured_no_go.
  The novelty-debate attacker's census was EXACT; the significance judge's "80 rows / 15
  measured" kill of that census was false and is REVERSED (attacker point restored).
- **Panel dependency disclosed**: all three referees consumed the same two lane digests, so
  their 3-way agreement is derivative, not independent confirmation.

## 2. Correctness axis (2 P0 + 15 P1 + 15 P2 + ~21 P3)

### P0 (both independently verified in-session — see 09_inhouse_verification.md)

**P0-1 (C1, K5-MV) — REFUTED headline.** |B|(200) = 405 km/s and the 4.4–5.4σ ΛCDM tension are
dominated by un-nulled radial-monopole leakage from the CF4 Vpec column (deep-shell iv-means
−612/−1965/−3853/−5765 km/s; pure-monopole MV response 473 km/s at direction-dot 0.993 with the
headline; monopole-nulled constrained MV: |B| = 94.8 ± ~77 km/s, p = 0.647, **0.46σ**). The
"consistency with Watkins 419±36" was scalar-amplitude-only (vector 81.6° / ~540 km/s apart)
and coincidental. R=50 results survive (leak 21 vs 173 km/s). Downstream casualties: K5-MOCKSIG
(calibrated the artifact — its linear GRF mocks contain no radial systematic by construction,
so the calibration could not catch it), K5-LCDMCV |B|=340.7 (same column, no monopole-null run),
Ω_tilt = 4.07e-7, the CF4-rapidity containment rows quoted on Teff/MES surfaces (U2/K5-V8).

**P0-2 (C3, K5-VCORR-ML) — headline unsupported.** fσ8 = 0.40 ± 0.02 is raw 0.486 divided by
sqrt(pk_corr = (370/308.09)²), justified as fixing a "~15% EH98 LINEAR σ_v deficit". Fresh CAMB:
linear σ_v = 309.0 (EH98 correct to 0.3%); 370 = halofit nonlinear (373.1). Premise refuted;
even a charitable nonlinear reading fails (NL/lin covariance ratio at the fitted separations
10–200 Mpc/h is 0.95–1.03, not 1.44). Without the correction the measurement reads
0.486 ± 0.022 — 4.9σ ABOVE the published CF4 0.38, i.e. discrepant (and now also subject to the
P0-1 Vpec monopole, un-checked at depth).

### P1 (verified: V2/V3/V4 in-session; remainder lane-evidenced + spot-checked)

1. (C2) GRF generator violates Hermitian symmetry on kz=0/Nyquist planes → vx/vy under-powered
   (measured 0.843/0.829/0.997 vs analytic band at n=32); produces the advertised 0.925
   "validation" ratio and inflates the calibrated σ. **[verified V2]**
2. (C2) 5.76σ headline silently drops the sibling lane's registered pk_corr treatment; the
   card's "consistent with the rev-r196 analytic range" assertion is false (corrected ≈ 4.4–4.6σ
   — before the P0-1 monopole, which moots the number entirely).
3. (C1) "Consistent with published CF4" is component-selective (vector ~540 km/s away). **[verified V3]**
4. (C4) DESI mock C_ℓ z-quadrature unconverged (nz=40; C_1 inflated ×1.36, C_40 ×1.75).
5. (C4) Mock is not the "IDENTICAL estimator": α not re-estimated per mock → per-cap monopole
   leakage inflates the mock null ~40% in mean. Lane's corrected proxy estimate: verdict
   (consistency) SURVIVES at p ≈ 0.69 — but that number is a 60-mock proxy, not the full rerun.
6. (C5) ACT UL template not passed through mask/reconstruction transfer — C_sig is alm-space
   band power quoted as sky κ power (anti-conservative as a sky limit by ~O(1/fsky)-class factor).
7. (C6) curl/div = 0.009 is the 2nd-order stencil truncation floor (4th-order: 0.00064; analytic
   potential-flow floor 0.0089 ≈ shipped 0.0089) presented as a field measurement; WF
   by-construction irrotationality absent from the new card. No-go STRENGTHENED, label wrong.
8. (C7) Manuscript downstream not reconciled with the re-frozen MES anchor — ch04:1054-1056,
   ch04:1114-1117, ch09:266 (one site unregistered in the open-items ledger).
9. (C8) Registry-internal contradiction on the refuted MES triples' provenance
   (THEOREM_REGISTRY:55-56 vs :905-913); stale "MES-1995 external" caveats on live ledgers.
10. (C9) rev-r195 CV block computes positions from cz-as-Mpc (`r_mpc` = norm of SG km/s
    columns, ×71 too deep); in-card "~10%" caveat wrong by ~×67. Significance was withheld, so
    no false headline shipped — the stated withholding REASON is wrong. **[verified V4]**
11. (C9) σ* railed at the fit-grid floor (50 km/s, χ²_red = 0.33); |B| swings 397→324 over
    σ* 25→60 — undisclosed systematic ~15–40× the quoted ±5.0. **[railing verified V3]**
12. (C10) Coupled-Fisher "1.0417 → 1.0239" is a synthetic-prior number misattributed to the
    JWST-anchored forecast (real JWST break: 1.0013).
13. (C10) JWST forecast card stale (9 anchors) vs crossmatch (14); results table self-contradicts
    (row 24 vs row 77).
14. (C1/C9) Noise model's |V3k| distance proxy: acceptable in the median (0.999) but broad
    low-z tails — with the σ* railing, the noise floor is effectively unconstrained from below.
15. (C4) Shipped C_1 feeding "13.5σ above shot" and the p-value inherits the quadrature error
    (direction: mock null inflated → p = 0.90 conservative for consistency; must be restated
    after the rerun).

### Sectors surviving at tier

DESI consistency verdict (survives the lane's own corrected null, pending full rerun); ACT
p = 0.35 isotropy (honest at tier; MF subtraction is a numerical no-op on an already-debiased
release product — relabel); K6 no-go (strengthened); MES geodesic algebra (W2_max arithmetic
closes; 5-sig-fig quoting is spurious precision — P2); parent identity / PSD cone / T1'/T2G /
KE / OMK seals (no math defect found; registry-hygiene P1s only); BipoSH/K1 nulls (match-quality
verified by lane; partial status prominent).

## 3. Novelty axis (2/5 as headlined)

- **Data lanes**: CONFIRMATORY_REPRODUCTION or INCREMENTAL_EXTENSION across the board (MV on
  CF4 = Watkins+2023 territory; mock-through-MV-weights = standard practice since
  Agarwal-Feldman-Watkins 2012; ML velocity-covariance fσ8 = Johnson 2014/Boruah 2020 lineage
  — Boruah 2020 got 0.400 ± 0.017, nearly our headline, uncited; DESI-BGS dipole = first on
  DESI DR1 (incremental) but the clustering-domination conclusion = Gibelyou-Huterer 2012 /
  Yoon-Huterer 2015; ACT κ low-L isotropy = harmonic counterpart of Bashir et al. 2025 on the
  SAME map, uncited; WF irrotationality = by-construction, Zaroubi-Hoffman-Dekel 1999).
- **Critic overrides applied**: cluster-1/2 verdicts re-issued conditional on P0s (an artifact
  cannot be a "reproduction"; 0.486 is not "confirmatory" of 0.38); "NEW" for the non-claim
  scope note reclassified (critic item 8); ACT mean-field "methodological step" adjudicated to
  C5's evidenced no-op position (critic item 7).
- **Sole surviving NEW pillar**: the partial-identification / Imbens-Manski transfer to
  cosmological anisotropy sectors (+ the exact fractional-program interval theorems T2G/T1').
  CAVEAT (critic item 5): adjudicated NEW by ONE lane's null prior-art search; requires a
  targeted adversarial search (GW population/EOS partial-ID, cluster-mass calibration,
  unfolding literature) before any restructure leans on it.
- **Bibliography defects**: `references.bib` Watkins2023 entry conflates the 2009 MV authors
  with the 2023 result (real: Watkins, Allen, Bradford et al., MNRAS 524, 1885); ~25 missing
  citations enumerated across the six cluster ledgers (04_web_crag_novelty_ledger.json),
  including MANDATORY Imbens & Manski 2004, Johnson 2014, Boruah 2020, Bashir 2025,
  Stiskalek 2025 "Velocity Field Olympics", Zaroubi 1999, Ellis & Baldwin 1984.

## 4. Significance axis (2/5 as-shipped; 3/5 re-scoped)

Panel (as-shipped): JCAP referee reject_resubmit (2/2/2); PRD referee major_revisions (3/2/3);
skeptic reject_resubmit (2/2/2). Unanimous core: the corpus as headlined offers no result a
working cosmologist would act on — the tension headlines are refuted, the surviving data lanes
are consistency checks the field already believes, and 44/78 ledger rows are internal proofs.

Re-scoped corpus (debate-judge object), strongest honest package:
1. **CF4 Vpec deep-shell radial systematic + monopole-vulnerability of MV bulk-flow claims**
   (the audit's own finding; new, checkable, field-relevant — bears on published raw-Vpec-based
   tension claims; explicitly does NOT automatically refute Watkins+2023, which uses its own
   bias-corrected velocity estimates).
2. Consistency-null suite at tier (DESI clustering-dominated dipole on DR1 BGS; ACT κ low-L
   UL, properly scoped) — solid, citable, modest.
3. Partial-identification anisotropy statistics + exact interval theorems — potential
   standalone methods paper IF the prior-art search holds.
4. Theorem/dynamics corpus (KE, OMK, MES modernization) — thesis-grade; PRD-marginal alone.

## 5. Consolidated must-fix list (ranked; = remediation scope for a future REV, not this audit)

1. Withdraw/flip K5-MV headline: monopole-nulled MV as the shipped estimator (or bias-corrected
   velocity estimates); propagate to K5-MOCKSIG / K5-LCDMCV / fσ8 depth-cut / Ω_tilt /
   CF4-rapidity theory-surface rows; results table + CLAIM_LEDGER + tickets + CHANGELOG.
2. Remove pk_corr as a "linear" correction everywhere; recompute fσ8 with a Boltzmann linear
   P(k); report the nonlinear treatment as an explicit systematic branch.
3. Hermitianize the GRF generator; rerun the mock ensemble with consistent P(k) treatment;
   restate the empirical floor from the rerun (never from the resolution limit).
4. rev-r195 successor card: recompute the CV block with Dist-based positions; correct the
   withholding rationale and the "~10%" caveat.
5. σ*: extend the fit grid below 50, or free-fit with a profiled floor; disclose the |B|
   sensitivity band.
6. DESI: nz ≥ 200 quadrature + per-mock α re-estimation + full 400-mock rerun; restate p.
7. ACT UL: scope as alm-space band power (or compute the MASTER transfer); relabel the MF step.
8. K6 card: by-construction statement + stencil-floor upper-limit wording (+ 4th-order number).
9. Registry/manuscript hygiene sweep: refuted-triple markers, ch04/ch09 stale sites, JWST
   9-vs-14, misattributed forecast number, 5-sig-fig W2_max presentation.
10. Bibliography: fix Watkins2023; add the enumerated missing citations.
11. Gate-taxonomy postmortem (critic item 10): map each confirmed P0/P1 mechanism onto the gate
    class that would have caught it (systematics-injection gates — monopole injection,
    generator-spectrum gates, unit-provenance gates, convergence gates); the existing gates are
    algebra/regression-class and were structurally blind to all five mechanisms.

## 6. Accepted residual risks + kill-switches (skill contract)

- Six corrections asserted by lanes but not fully rerun (critic item 6) are quoted as ESTIMATES
  (C2 floor-survival, C4 p≈0.69, C5 factor-of-a-few, C10 back-solved 14-anchor forecast) —
  kill-switch: none may headline until its bounded rerun executes.
- The audit's own replacement result (94.8 ± 77) is algebra-validated but not
  injection-validated through the constrained weights with realistic distance errors (critic
  item 12) — treat as the demonstration that the tension is monopole-fragile, NOT yet as the
  measured CF4 bulk flow.
- Uncovered rows (critic items 4, 13): OMK-REOPEN internals, EGS2 NT2 lanes, Teff lanes,
  BipoSH novelty positioning, D_2/x_C production anchor, v9 reproducibility hashes — registered
  OUT-OF-SCOPE, not cleared. Blocked lanes (K1 E2E, COLA, RDN0, native solver) untouched.
- Novelty NEW-pillar single-sourcing (critic item 5) — kill-switch: no paper-restructure
  decision until the adversarial prior-art search on partial identification in astrophysics runs.

## 7. Evidence map (loop stage → artifact)

| Loop stage | Artifact | Execution evidence |
|---|---|---|
| 1 self-discover | 00_scope_and_self_discover.md | claim inventory from egs_results_table_v9.md (78 rows) + open-items ledger |
| 2 step-back | 01_step_back_principles.md | pre-registered per-axis criteria + scoring rubric |
| 3 metacognitive self-ask | 02_metacognitive_self_ask.md | 6 Q/A incl. author-bias mitigation design |
| 4 CoVe | 03_cove_correctness_ledger.json | 10 lanes × ≥6 verification Q/A each, file:line + snippet evidence |
| 5 adversarial self-ask | 03 (strongest_attack fields) + 06b transcripts | per-lane kill-attacks pursued concretely |
| 6 web CRAG | 04_web_crag_novelty_ledger.json | 6 lanes, evidence_of_search = real queries + URLs |
| 7 CCoT | 03 (contrastive fields) | claim vs strongest-alternative adjudications per lane |
| — panel | 05_significance_panel.json | 3 referee reports (scores + must_fix) |
| — debate | 06_debate_judgments.json + 06b_debate_transcripts.json | 3 axes × (attacker, defender, judge) |
| — critic | 07_completeness_critique.md | 14-gap list incl. self-adjudicated census recount |
| 8 PDR | this file | meta-adjudication + verdicts + ranked must-fix |
| in-session verify | 09_inhouse_verification.md | V1 CAMB, V2 GRF variance, V3 bit-for-bit monopole, V4 unit bug |

Workflow: run `wf_49ea55ab-643` (29/29 agents, 0 errors); journal:
`~/.claude/projects/.../subagents/workflows/wf_49ea55ab-643/journal.jsonl`.

## 8. Status updates needed (NOT executed by this audit — owner decision required)

This audit is the deliverable; no card, ledger row, ticket, figure, or manuscript file was
modified. The findings above imply flips of K5-MV / K5-MOCKSIG / K5-VCORR-ML rows from
`measured` to a refuted/withdrawn state and the §5 remediation programme (multiple long reruns).
That is REV-R199+ scope and awaits explicit owner sign-off.
