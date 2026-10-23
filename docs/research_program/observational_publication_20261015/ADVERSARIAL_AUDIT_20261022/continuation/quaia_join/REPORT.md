# A22-03 — Quaia/Gaia exact-ID covariance linkage

Owner obsstat, C0 source/cohort result, transfer none. Base HEAD a8fd176305fb475947a46f9dacb651805d323741.
New inputs: Quaia v1.0.0 G<20, two relative-selection/template payloads, and only
the 63,696 missing Gaia covariance records. Next consumer: A22-05 redshift E/B.
[Independent review](INDEPENDENT_REVIEW.md) closed with SCOPED_PASS after a
cache-first replay repair; six focused tests passed. Original K03/K04 remain open.

The public [Quaia release](https://zenodo.org/records/10403370) supplied all three
validated inputs (101,065,759 bytes). The existing Gaia 1,614,173-row raw product
was decoded once for a **new exact integer-ID join**, with its frozen hash and
reader reused. No old Gaia fit or covariance-envelope calculation was rerun.
Source IDs never passed through floating-point values.

| Reported z interval | Quaia G<20 | Existing CRF3 match | Missing covariance acquired |
|---|---:|---:|---:|
| [0,1) | 200,785 | 185,864 | 14,921 |
| [1,2) | 369,335 | 346,834 | 22,501 |
| [2,10) | 185,730 | 159,456 | 26,274 |
| Total | 755,850 | 692,154 | 63,696 |

All matching RA/Dec, PM and reported errors agree to the predeclared 1e-10
coordinate-unit tolerance. The anonymous ARI TAP upload requests only unmatched
IDs and four fields; persistent job `1792690491385` completed with QUERY_STATUS=OK.
Its 1,640,346-byte VOTable has exactly the requested unique integer IDs, with no
overflow. The final join contains **755,850 rows, zero losses**. CRF3 membership
is retained as a control flag; it is not an extra analysis cut for the full cohort.
Raw query receipt, XML and payload remain outside Git.

The source-level PM covariance is reconstructed from positive PM errors and
`pmra_pmdec_corr`, with the mas/yr→microas/yr conversion once. It is a marginal
2x2 block, without source-to-source calibration covariance. Redshifts are reported
spectrophotometric estimates; their scalar errors do not describe catastrophic
redshift failures.

[Release-day source binding](SOURCE_BINDING.json) resolves the selection map's
equatorial/RING convention using the actual v1.0.0 author notebook. It also fixes
the measured PM cut `pm < 10**(.4*(G−18.25)) mas/yr`. All catalogue rows pass.
The equation and executable give 1mas/yr at G18.25; the paper's adjacent 2.5 prose
is inconsistent. The relative map and seven templates are covariates, never
absolute probabilities or inverse weights. Producer-byte regeneration is not proved.

Reproduction in the existing checkout:

```bash
.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/quaia_join/test_join.py
# Only on a new join requirement: source reading, not the old Gaia fitting campaign.
.venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/quaia_join/join.py
.venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/quaia_join/supplement.py --collect
```

First production join: exit0 in27.98s; four initial narrow tests passed, expanded
to six with subset NULL and offline replay checks. The
supplement reuses its UWS identity on continuation; it cannot submit a second job
when the existing record matches. Its collector enforces a 2GiB reserve before
and during streaming, HTTP length, raw hash, VOTable status/schema, NULL/finite
fields and exact requested membership. No byte/aggregate cap is imposed. A reviewer
injected an outage and reproduced a cache-read failure in the first collector;
the repaired collector consumes validated local VOT data without a UWS request.

Derived row cache: `/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_gaia_full_join.npz`.
Its current identity and query binding are in [SUPPLEMENT_RESULT.json](SUPPLEMENT_RESULT.json).
The first intersection and loss evidence stay in [RESULT.json](RESULT.json) and
[figure](JOIN.png). The final full cohort preserves response-dependent upstream
selection. Its physical astrometric likelihood still requires source-qualified
spatial covariance and selection treatment; A22-05 will display conditional models.
