# Independent CF4 FP pooling result review

**Decision: `ACCEPT_FINITE_OPERATOR_RESULT`. Blocking findings: none.** The complete frozen operator question has a valid finite partial answer: reproduction of all 22,653 groups remains `STRUCTURAL/NUMERICAL_HOLD`, while the separate marginal boxes for the 22,599 structurally qualified groups are outer-compatible with one stage offset. A source HOLD is a result of this completed component, not evidence that its computation failed. It does not close H02 or promote the full campaign.

The reviewed candidate files and all ten immutable input identities are sealed by the SHA256 mappings in `RETURN.json` and `INDEPENDENT_CHECK.json`. The read-only checkout observation was branch `research/htt-adaptive-methods-20261023`, HEAD `d93605e66adfececa89b90681124b232a5f90220`, origin `https://github.com/cosmosapjw-quantum/htt_base.git`, with pre-existing changes. This reviewer wrote only its assigned external directory. Requested runtime is `gpt-6-astra/xhigh`; observed runtime remains `UNKNOWN`.

## Verified evidence

The source ReadMe specifies table2 PGC bytes 1–7, group bytes 9–15, FP modulus bytes 66–71 (`F6.3`) and error bytes 73–76 (`F4.2`); table3 group bytes 1–7, count bytes 114–116, FP modulus bytes 118–123 (`F6.3`) and error bytes 125–129 (`F5.3`). The independent check read actual source bytes and decoded the NPZ identity column with stdlib, without importing author/project code. It verified unique 55,877 table2 PGC rows, unique 38,053 table3 group rows, 34,059 SDSS PGC rows, and 35,970 unique retained IDs. The independent raw join recovered exactly 22,653 groups, all 34,257 FP contributors, 34,008 SDSS IDs, and 249 other contributors in 51 groups. The ALL_GALAXY_IDS_IN_SDSS label is not proof of measurement purity.

All 54 structural witnesses, including each contributing raw line and byte offset, match the source. Independent arithmetic covered six saved cases: half-place 48197/34706, one-place 34660/34706, and mixed 29807 under both conventions. The mixed group has 27 SDSS and seven other contributors; omitting those seven changes its nominal mean.

The independent extrema algorithm used exact Fraction fixed points and endpoint sign certificates, plus all four weight vertices for the two-member cases. For a candidate ratio r, the chosen weights minimize or maximize each term w_i(v_i-r), and their sum is exactly zero; positivity of the denominator then proves the global box extremum. This independently confirms the author's sorted-threshold implementation. Exact squaring and 100-digit Decimal checks confirm outward error enclosures. The lexical quantum, source-error inversion directions, endpoint witnesses, offset sign, and active bounds agree. The reviewed integer square-root enclosure is rigorous; output decimal endpoints round outward.

Qualified-group offset intersections, in mag:

| Convention | Lower | Upper | Active groups |
|---|---:|---:|---|
| Half last place | 0.0232272433828276307 | 0.0246941641527098720 | 48197 / 34706 |
| One last place | 0.0220800842992623815 | 0.0257960033305578684 | 34660 / 34706 |

The five author controls and recorded final cohort/witness executions passed. I inspected their code and raw success outputs; the full numerical cohort was not replayed. The zero reported marginal error-disjoint groups is accepted from that observed execution and implementation audit, with independent arithmetic restricted to the witnesses above. Separate projected compatibility does not establish one common set of weights satisfying modulus and error simultaneously, an independent-error law, or a stochastic calibration law. The candidate states these limits correctly.

The published inverse-rms-squared pooling rule, summed-weight error formula, successive scalar offsets and multiple FP subsources are already documented. The formula itself is not the missing input. It does not identify the accepted per-galaxy contributions behind these particular released exceptions. [Tully et al., Cosmicflows-4 v2, sections III.3–4, IV.3 and X.1](https://arxiv.org/html/2209.11238v2).

## Exact remaining source issue and next transition

The 46 missing-target IDs are: 23771, 26143, 28836, 28871, 29432, 32408, 35293, 36016, 37059, 37730, 38253, 39060, 39348, 40668, 40918, 41026, 41528, 43135, 43275, 43884, 44683, 45378, 45549, 48285, 51663, 52138, 52143, 54850, 55819, 57889, 1147801, 1599443, 1726178, 1824359, 2543122, 2576641, 2815876, 3097748, 3294859, 4075028, 4087210, 4239418, 4343358, 5083482, 5085937, 5094549.

The eight count disagreements (raw table2 FP contributors / table3 count) are: 34025: 4/3; 36071: 133/129; 47462: 3/2; 56501: 2/1; 56962: 217/193; 57215: 3/2; 57455: 38/34; 1490017: 1/2.

The release-matched accepted membership and method-exclusion decisions are missing. A cause such as rejection filtering or a changed group assignment has not been proved. In particular, 1490017 has one available contributor against a target count of two, so discarding extra rows cannot resolve all eight cases. Group 23771 has 23 contributors and no FP target; 56962 has 217 against 193. These are precise source questions; neither a relaxed rounding tolerance nor re-running the same computation can answer them.

The next distinct task, if needed by a downstream consumer, is bounded source-stage reconciliation: recover version-matched accepted per-PGC FP membership/group mapping and group/method exclusion decisions, starting with those three discriminating witnesses. Keep all 54 exceptions explicit. If those records are absent, retain the exact source HOLD and advance other ready branches. Do not substitute a selected subset for the frozen all-group target. No candidate repair or generic additional audit is required.

The separate upstream eta-to-CF4 galaxy-modulus problem needs accepted FP-subsource identities and weights (or a justified finite mixture or pure-intersection bound), plus producer distance convention and stage-offset identity. The PGC20919 stage example remains 36.956/0.46 in table2, 36.980/0.460 in table3, with DMav 37.107 and DMzp 36.960. These fields cannot be interchanged.

H02 stays HOLD; historical original 17/42 and alternative 18/42 counts are preserved without reauditing them here. The old 64-box Y0 work and FP/TF/SNIa contrasts were not rerun. This review admits no physical Q/denominator/Pi, posterior, null coverage, native solver or ODE claim.

## Actual resource accounting

One stdlib validation process, one thread, 30-second wall guard, exit 0, empty stderr, reaped. Actual elapsed: 2.9083192360121757 seconds; child peak RSS: 134604 KiB. Prior cumulative 58.69378793798387 → **61.602107173996046 / 600 seconds**, remaining **538.397892826004 seconds**. `CONTINUED_BUDGET.jsonl` is an append-only review sidecar; prior budgets and author evidence were not edited. Raw stdout/stderr and script identity are recorded there.
