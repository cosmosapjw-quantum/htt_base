# Fresh native review: actual L03 pilot and L02 application

Requested reviewer `gpt-6-astra/xhigh`; independently observed model/effort
`UNKNOWN`. Fresh bounded read-only review, separate from the implementing worker
and parent test-fixture author; no raw-bank rerun or file mutation.

Verdict: **PASS_SCOPED_L03_SOURCE_CONDITIONAL_PILOT_AND_L02_APPLICATION**.
No blocking implementation/numerical finding. Original **L03 HOLD**, **L04
NOT_COMPLETED**, and paper **NOT_READY_TO_SUBMIT**.

Identities reviewed at parent HEAD `c0ed65c00e4be6de81443ace044ee9983fac6687`:

- PILOT.json: `49c95f3ae8fa35a34818770e3393eed044988ab36690ed48ffd84b744db1820e`.
- PILOT_COEFFICIENTS.npz: `75a9a46c3cb2f576c994fefec248805cc604532345f7843bcd487ca848953123`.
- L02_ON_EIGHT_PAIR_PILOT.json: `accf98acaad10c48093599ee2da19f8b153495273035c0b48ed08073a47e7803`.
- tests/obsstat/test_htt_publication_dag.py: `a7be51a993255c8bb4fae8fd9ede80dc9bdded2757d0b07df1543df6b84bd2a6`.
- tests/htt/test_sixpaper_goal_execution.py: `562ccb95dfeda29a40414cf5d3afb989907029e05cf21a930abef4166575473b`.

Seventeen hash bindings, including external cache/code/dependencies/original
chart/preserved attempt, match. Sixteen raw-source records match the existing
manifest; the reviewer did not reread the large FITS. All 36 scalar and 64 spin
columns agree with native healpy/historical conventions within `7.63e-15` and
`4.18e-15` absolute. Independent SVD fits of sixteen cached components reproduce
coefficients within `5.2815e-15` relative; eight paired map sums within
`4.5391e-15`. Supports T26846/P30021, mask identities, IDs, storage convention,
design ranks 36/64 and centred sample rank seven agree. No covariance inversion.

All 120 axis-overlap values agree with independent SVD within `1.5765e-14`;
C2/C3 agree exactly. Independently expanded noise-energy changes agree within
`5.97e-16`. Streaming versus direct child reduction at actual resolution ratio32
with big-endian interleaved 1024-element vectors agrees exactly for chunk sizes
1024,7168,262144. Selected-invalid data are rejected; masked-invalid accepted.
The attempt1 backup hash and four original guard/reduction ASTs are unchanged.
Its explicitly approved performance repair changes traversal/summation only.

Author and parent each ran the 25 focused tests, PASS; parent inspected both PNGs.
The actual baseline passed 432 field and 432 cross-field metamorphic checks.

## Integration-test repair

Parent's prior correct-path run yielded seven failures/eleven passes, retained in
the published H02 upstream PR delta. The two-file repair separates advancing live
DAG state from manufactured four-anchor/nine-ready scheduling fixtures and the
unchanged fourteen-node EXECUTION_GOALS intake snapshot. It retains those exact
assertions, adds live/progress tests, and makes the cycle fixture reach the cycle
guard instead of the earlier completion guard. No scientific validator,
acceptance, dependency or canonical input was weakened. Parent **20 PASS**;
reviewer independently **20 PASS in .40s**, using `python -B -m pytest
-p no:cacheprovider -q` on those two files with two threads.

## Qualification that governs downstream consumption

Fields named `independent_pair_count`, `independent_realizations`, and “eight
independent pair IDs” denote **eight distinct nominal simulation-ID units**, not
established stochastic independence. This clarification governs the frozen pilot
metadata at source_matched_pilot.py:243, diagnose_and_plot.py:39,
apply_l02_family.py:161 and QUALIFICATION_KO.md:152. Numerical output bytes need
not change; no physical independence or significance is admitted.

[Planck IV](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html)
supports fixed-weight processing and the declared ±5% sensitivity, not coverage
for this statistic. [Planck VIII, sections 2.1 and 4.4/Fig22](https://www.aanda.org/articles/aa/full_html/2020/09/aa33886-18/aa33886-18.html)
distinguishes released split noise from absent 2018 half-mission FFP10 CMB
products: its FFP9 substitution shares seeds but uses different effective beams.
It also identifies weak shared residuals between noise simulations. Public split
products are not proof of the required matched joint law. Locally absent files
are acquisition/integration work, not a claim of public impossibility; residual
foreground/response/weight-selection and statistic-specific coverage still need
qualification. No pilot PASS closes L03 or L04.
