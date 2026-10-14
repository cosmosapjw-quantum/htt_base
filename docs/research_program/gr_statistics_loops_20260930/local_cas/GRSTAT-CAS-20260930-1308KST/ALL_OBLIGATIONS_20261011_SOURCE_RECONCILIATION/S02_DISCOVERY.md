# S02 original-plan discovery register (in progress)

This register preserves source-discovered obligations before any proof or
implementation scheduling.  It is not an acceptance ledger and does not alter
the package's 55 canonical baseline cards (including completed PR-204).  The
eleven sources were read against package `UPPER_BACKLOG_COVERAGE.json` and
`PROOF_DAG.json`; their SHA-256 identities are recorded below.

| Family | SHA-256 | S02 disposition |
|---|---|---|
| PR-R revision overlay | `0f539b92d728f914c566ab26cff591216b7e1e0cad815ba61653aa7dcefd2ac9` | `proposed_only`; title/dependency is not DoD evidence |
| PR-N research overlay | `f8fb47860af65499142fd6a05743f2802d3e16352565b0cd854283ba5a2b0e9c` | `proposed_only`; preserve required gates and blocked claims |
| Non-BASS WBS | `a2c9951a4aa69d13c2b079d4a9ce1f76396c3ae1095842633644547c25f2261c` | partial historical/unfinished mix |
| PR07/08/10 registry | `afb13e156720ccbd056ecc21e27522c5251444f00b654acac1eb6381ae54535b` | preserve separate-project PR10 as external producer milestones |
| VT two-pillar plan | `39312eb8e17631516078e3cd385de86f6741d8cae55c024013045eb4790a52ea` | proposed inventory, not canonical acceptance |
| REPORT-FIRST | `4e9ec189835e027bb1f4cad12c4656bfbdb6aa370f2acb93ea5e89c54261cfdf` | historical/report source with unexecuted compiler receipts |
| REFEREE-SEEDED | `455691c6f0303389670903259a2764a1166dc07c4412800be719ab6aa016fe51` | donor findings plus model/experiment contracts |
| PR328 | `0517454672e116ed2ba447d0e978d52c39d21d13e0a7519b2f1f173f3cc1d590` | frozen historical protocol; old worktree/CUH-G procedures retired |
| solver development plan | `465ada0ecbda4e52e05cea51ac4707369f42a222ecbc97a23139b802dfa86c90` | external-producer obligations; no local solver implementation |
| EF3 gate matrix | `38ee34039f017042aeb613939bb58be4fb8e11014b9ac96eaf0169db767e4cd7` | retain `EF3:` namespace; never conflate with canonical PRs |
| R9 campaign DAG | `29125757bb326a867efdbe020b996dadacdbabbec89e4b028f39f3171e2760c6` | capability actions earn output separately |

## Newly discovered stable-ID families

These are registry additions, not statements that their underlying work is
missing or ready.  Each must first receive an exact accepted-source reuse check,
then either a full task card or an explicit source-supported disposition.

- `SRC-STAT-LIKELIHOOD-CALIBRATION`: distinct R010/R012/R040/R041/R042/R050/R051
  prior, FPR, likelihood-branch, sensitivity, PPC and LOOCV criteria.
- `SRC-NB-D2-D28`, `SRC-NB-FILLING-EXPORT`, `SRC-NB-D10-SAVAGE-DICKEY`,
  `SRC-NB-HJ01-REPORT`, `SRC-NB-HTT-MIO-INGEST`, `SRC-NB-CONSISTENCY-GUARDS`.
- `SRC-PR07-PAPER-A`, `SRC-PR07-PAPER-B`, `SRC-PR08-K6-FIELDS`,
  `SRC-PR08-2MRS`.
- `SRC-VT-REGISTRY`, `SRC-VT-STATE`, `SRC-VT-ANCHOR`, `SRC-VT-ORBIT`,
  `SRC-VT-FUNCTIONALS`, `SRC-VT-EXCEEDANCE`, `SRC-VT-DEPTH`,
  `SRC-VT-TYPE-REPORT`, `SRC-VT-PILLAR-T`, `SRC-VT-PILLAR-S`,
  `SRC-VT-BLIND-INTEGRATION`, `SRC-VT-DATA-PILOT`, `SRC-VT-PROOF-ATLAS`.
  Their subinventories retain source identities `VT-T01..14`, `VT-S01..14`,
  `TC-01..20`, `ST-01..25`, `TF-01..12`, `VT-APP-A-U1..U9`, and the 58
  A5/A6 rows; no group-level reuse may silently close an individual row.
- `U-REPORT-COMPILER`, `REPORT-FIRST:R4A1E`, `REFEREE-SEEDED:M1_CMB_MODEL`,
  `REFEREE-SEEDED:M2_REDSHIFT_MODEL`, `REFEREE-SEEDED:M3_EXPERIMENT`, and
  `U-REFEREE-MODEL-EXPERIMENT`.
- `U-EF3-ECOSYSTEM`, `U-EF3-POLE-METHOD`, `U-EF3-ANYTIME`, plus EF3's existing
  namespaced transfer/remote/design families.  `EF3:247` is not `PR-247`.
- `U-R9-JWST-LAW`, `R9-08:UNION3_SCENARIO`, `U-R9-ORBIT-METHOD`,
  `U-R9-DEPTH-DATA`, `U-R9-PHYSICAL-IMAGE`, `U-R9-FUNCTIONAL-IMAGES`,
  `R9-22:PURPOSE_ERROR_SET`, and the distinct R9 response/rank/images/physics
  actions.

## Non-negotiable source dispositions

- Native solver IMEX/P2/P4/A work stays an authenticated external-provider
  delivery condition.  `htt_base` must not implement it.
- Historical terminal/failure/blocked records remain typed evidence; a new
  bounded proof or internal review cannot retroactively satisfy their original
  four-axis or dual-review contracts.
- Data-product requirements remain product-specific: no PR4/RRSS/Planck/CF4/
  JWST/Union3 substitution, zero-fill, or proxy-to-native promotion.
- S02 is still `IN_PROGRESS`: the individual source IDs above need full task
  cards and DAG edges before this discovery node can be called exhaustive.
