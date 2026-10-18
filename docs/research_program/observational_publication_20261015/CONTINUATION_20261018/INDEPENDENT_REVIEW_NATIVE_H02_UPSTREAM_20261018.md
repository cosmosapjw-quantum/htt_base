# Fresh native review: H02 upstream contributors

Requested reviewer `gpt-6-astra/xhigh`; independently observed runtime `UNKNOWN`.
Fresh bounded context, read-only, separate from the implementing worker. Review
scope was `H02_UPSTREAM_SELECTION_20261018/` and its identified source dependencies,
not earlier reviewer verdicts. Parent integrates and publishes.

Verdict: **PASS for DIAGNOSTIC_ONLY release membership/contributor diagnostics**.
No blocking findings and no repair requested. Original H02 acceptance remains
**HOLD / blocked_external**. No source-qualified likelihood or submission
readiness follows.

Candidate identities:

- Report SHA256 `f183cb8af66de8e951924ef03856451efd273813a66f91e90153fc58e02ea4a5`.
- Result SHA256 `6df91eb9bf5e3b513a328e2819032a1e1ce99946f50d8783c777a0c6627a4720`.
- Generator SHA256 `cc93344fa89326e23d43d440f3ee91e79cf676f34a7327d7ad4591a476c59714`.

The reviewer verified all three identities plus raw sources, selected NPZ, CF4
ReadMe/tables and receipt-listed code. Independent documented fixed-byte parsing,
without calling the generator, reproduced 10,737/9,792 records, 947 table1-only,
two table4-only, eleven absent DMbest values, and 7,573 measured galaxies joining
6,697 selected groups. Every cohort histogram, all 36 quality cells, band route,
group overlap, method/count-missing field and release-difference quantile agreed.

Independent group sets and `math.fsum` reproduced 150 window fields within
`rtol=2e-13, atol=2e-14`; maximum absolute summation-order difference was
`5.68e-13`. Nine file-nonwriting native tests passed. Instead of the tenth test's
temporary-file SHA fixture the reviewer ran an independent in-memory source-SHA
rejection check, also PASS. Author ran all ten original tests; parent independently
ran `.venv/bin/python -m pytest -q .../test_upstream_selection.py`: **10 passed**.
Both parent and reviewer inspected the PNG; labels accurately distinguish
overlapping source-support working mass from selection probability.

The primary paper's optical-preferred DMbest, blank missing bands, common
linewidth dependence and enforced inter-band adjustments support the report's
adoption/independence caveats:
[Kourkchi et al., sections III.4–IV](https://arxiv.org/html/2009.00733v2#S4).

Inherited-input limitation, not a new candidate defect: the frozen selected NPZ
substitutes `0.1` for two released zero uncertainties; all positive source
uncertainties are unchanged. These calculations use that declared working-weight
policy, not raw physical covariance. Historical input bytes/policy were not
changed and prior fits were not repeated.

Missing distances/counts remain missing, galaxies do not multiply group weights,
and group overlap is not additive. Identity membership does not prove unchanged
measurement ingestion. True targeting/detection/selection, shared calibration
and velocity covariance, independent angular anchoring and qualified source-null
processing remain unavailable. No solver/ODE, physical admission or main merge.
