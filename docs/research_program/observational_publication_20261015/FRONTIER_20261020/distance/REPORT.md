# Distance-source frontier, 2026-10-20

Owner `obsstat/htt`; C0; `DIAGNOSTIC_ONLY`; non-claim-bearing. Transfer source none. Requested worker gpt-6.1-sol/high; observed UNKNOWN. Parent is sole publisher. Original H02/K04/S02/S04 remain HOLD.

The useful new result is a **source-bound conditional calibration/flow likelihood and response contract**, developed in [CONDITIONAL_MODEL.md](CONDITIONAL_MODEL.md). It gives an explicit factorization, a finite-redshift derivative with the radial-flow gradient retained, and a constructive fixed-public-covariance branch. It supports a future rank/quotient audit using existing cached sky/depth/covariance arrays. It does not supply the missing full composite-survey selection law or a GR optical-to-kinematic STF mapping.

The primary sources are [Stiskalek, Desmond & Lavaux, arXiv:2509.14997v2](https://arxiv.org/html/2509.14997v2), published January 2026, and the [July 2026 joint TFR/FP/SN follow-up](https://doi.org/10.1093/mnras/stag1266). The former's explicit latent-PV Pantheon branch used a privately supplied PV-removed covariance. This limits exact replay of that branch. A separate analysis can retain the full public covariance exactly once and change only the deterministic mean under stated working assumptions. No covariance subtraction is proposed.

## Actual new payload and rejected acquisition routes

| Route | Actual evidence | Use and limit |
|---|---|---|
| Author [CF4catalog notebook](https://github.com/ekourkchi/CF4catalog/blob/2f4c23c8810c35b494bf4d7c86b38e114109a022/SNIa_groups-catal.ipynb) | Original 55,985 bytes; pinned Git blob and SHA-256 in registry; cells inspected as JSON | Primary compilation code and partial PGC/SNIa/1PGC output. Input CSV absent; notebook reports 1009 rows, so it is not silently treated as the released 1008-host contributor table. |
| [NumCosmo fixture](https://github.com/NumCosmo/NumCosmo/blob/91ecab49a0b3c48846fd128cd8ada8c7ca6e0620/tests/python/conftest.py) | Original 14,502 bytes; comment labels EDD export 2026-10-17; safe AST extraction finds 5 header lines, 6 rows, 45 fields | New source-claimed exact identities: 2006sr→250→250; 2008hj→282→282; 2003it→415→415; 2000dg→465→616; 2002hw→515→515; 1998dk→963→963. First five agree with author notebook. This is an excerpt, not complete contributor genealogy or live EDD verification. |
| New NumCosmo release asset | Original 368,361 bytes; remote SHA-256 matches locally | Numeric catalogue serialization drops SNIa strings. Inspected as opaque bytes/hash only; never loaded. Redundant with existing CF4 numeric inputs; not recommended for acquisition or analysis. |
| Full contributor CSV | Three notebook-named GitHub paths return 404; repository tree confirms absence | No full public SN-ID→PGC→group export obtained. EDD human challenge was not revisited or bypassed. |
| CANDEL code | Exa indexes author README/docs; live GitHub connector/API return 404, direct docs return 403 | Do not claim a verified downloadable code release or adopt indexed license metadata. The accessible paper suffices for the written conditional contract. |
| HI parent selection | Fresh author HI tree and primary article checked | No qualified 5460-object inspection/rejection list found. A 10,386,030-byte generic `kleda_orig.csv` exists in the author tree but was not downloaded or mistaken for the parent. Completed 628-target genealogy remains valid. |
| Grouped64 producer convention | Official page and fresh producer-focused search checked | No new exact origin/spacing/channel/estimator contract. Third-party code assumptions cannot resolve the existing SOURCE_CONFLICT. No grid re-download or sphere probe. |

The fixture's `SNIa` field permits slash-separated multiple names. `pgc` identifies the host; `1PGC` identifies the group's brightest member. `DM_zp` is the absolute-calibrator-shifted modulus; `DM_av` is a weighted average on its stated compilation scale; `eDM` is the **minimum** reported modulus error, not a released joint covariance. The derived schema retains these distinctions.

## Concrete next local action

Use [next_task.json](next_task.json) as a bounded proposal: construct the calibration/flow nuisance response on already cached selected rows, retain the public total covariance once, and inspect the residual calibration-column rank. This is a conditional identifiability calculation, not a one-use catalogue campaign, calibrated significance or node promotion. A physical common-congruence response, full parent selection, complete contributors and cross-catalogue error law remain separate requirements.

All raw source payloads, metadata, hashes and availability observations are in [source_registry.json](source_registry.json). Total locally stored source material is 1,181,937 bytes, including metadata and derived text. Required **additional** remote download for this proposal: **0 bytes**. No previous 628-HI, 654-host, SH0ES ladder, SDSS mocks, Pantheon simulation or flow-grid analysis was repeated. Only safe parsing and source/schema checks ran.

## Skill and claim audit

Applied project claim-firewall, claim-provenance and physics-math audit skills. Evidence, assumptions, CMB frame, velocity units, response signs, zero-gradient and low-z limits are explicit. No geometry, global-tilt, independent-survey or coverage claim is made. The dimensional implicit differentiation is derived; full forward-model integration and cached-data rank audit remain SPECIFIED. No numerical inference or native solver ran. A covariance identity conflict, field-gradient omission, invalid distance root, or proposed promotion from six rows aborts downstream admission. No permanent scientific ledger update is needed. Independent review belongs to the parent workflow.
