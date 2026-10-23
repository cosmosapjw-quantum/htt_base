# Independent PR4 comparison review — 2026-10-22

**SCOPED_PASS_C0.** No unresolved finding for this descriptive observed-map
comparison. F06 and original L03 remain HOLD. The parent records the separate
read-only reviewer's returned decision; the reviewer did not implement or publish.

Reviewer: native `pr4_comparison_review_20261022`, fresh bounded context;
requested `gpt-6-astra/xhigh`, observed runtime identity `UNKNOWN`.
Base: `d2c11c4a850fadbf1cf181c190c3c30f48425ff3`.

## Evidence and targeted closeout

- Independent focused suite: **4 passed**, exit 0, including the targeted repair.
- Exact algebra, common-basis rotation and the `A=B`, `A=-B` limits passed.
- Independently checked angular ancestry of **32,768 native pixel centers**
  across eight selected NSIDE16 parents.
- Independently calculated scalar powers from **12,288 sampled observed pixels**.
- Checked source-intake, code, result and plot identities; visually inspected
  the figure. It represents scalar parent RMS, with no spin-2 downgrade claim.
- Full-map execution and raw-file hashing were reused from bound evidence.
  No old campaign or full-map execution was repeated by this reviewer.

One concrete test weakness was found and fixed: a relative-comparison assertion
at powers around 1e-8 K_CMB² retained NumPy's default `atol=1e-8`. Replacing D² by
half its value gave lhs `9.424749819822318e-09` versus rhs
`1.345099971186758e-08`, a 29.93% discrepancy that the old assertion accepted.
The worker set `atol=0.0` while retaining `rtol=1e-14`. The reviewer verified the
one-line test change and reran only the focused suite. The adjacent cross check
already had an explicit dimensional absolute tolerance. No maps or plots were
rerun for this repair.

## Final reviewed scientific artifacts

| Artifact | SHA-256 |
|---|---|
| Consumer | `706ee20d64ac04cc7a5df13f5fe9605686b55403de7c0ebb8cf14fa3cd73fb83` |
| Repaired tests | `f90131251fbbc1b7cd1f3182c345e293626cea184dc2e4cfb3b295a082383161` |
| Result | `159b0721ff33114bbd4ef33dcc3be3ad815c292360d9146d50b5ae7492589541` |

The report at review had SHA-256
`e97f131f500601265c53cb69ce13d903300d4e9b09fb16936abcb12698e1aa4a`;
parent subsequently added this decision link in place of its pending-review text.
No scientific values or generating code changed in that annotation.

The reported full result uses 5,214,208 native pixels and
`D²/S²=0.9921957994817991`. This is a source-conditional descriptive statistic;
foreground, processing and instrument differences may contribute. It supplies
neither pure-noise estimation nor null coverage, significance or a physical atlas.

The reviewer checked [healpy's NESTED-to-RING definition](https://healpy.readthedocs.io/en/latest/generated/healpy.pixelfunc.nest2ring.html)
and the [HEALPix hierarchy](https://healpix.sourceforge.io/html/intro_Geometric_Algebraic_Propert.htm).
Applied skill context: repository observable-statistics, claim-firewall,
scientific-code-validation; physmath-research-loop 1.3.0 R6/C9, finite-review and
typed-identity policies; current runtime and project instructions.
