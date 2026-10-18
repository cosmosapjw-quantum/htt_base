# D06 independent review and one repair closeout — 2026-10-18

Fresh read-only `/root/open_d05_d08_review`; requested Astra/xhigh, observed
UNKNOWN. Final PASS_DIAGNOSTIC_ONLY. Original H02/H04/S02/S04/K04 remain HOLD.

Initial P2: `(xyz+500)/delta` rounds96/128 lower-edge neighbors into the next
cell; nextafter(500,-inf) becomes index128/crashes. The single authorized repair
uses exact representable edges/right-searchsorted on already finite, strictly
inside coordinates; no outside input clipping. Tests cover all-axis exactedge/
nextafter behavior. Independent rational checks pass1152 valid cases and outside
rejection. Final11tests PASS3.94s; author11PASS4.21s.

Original scientific validation passes: all candidate/raw seals, independent
fixed-width494host fields/query,654rows→494hosts/482groups/460cells, all
mean/RMS/proxy quantiles (independent log1p), host radial/XYZ projection
max2.16e-12km/s,53 alternative-input cell changes. Grouped finite/x52/shape checks
pass; missing WCS remains HOLD. Source erratum and old-href/new-script mismatch
are supported by https://projets.ip2i.in2p3.fr/cosmicflows/ . Plot/report checked.

The repaired code preserves all494 cached host indices, prior scientific JSON
values, host ledger and PNG/PDF. Historical producer003e6b2e… and initial
candidate/result remain preserved; current lookup seal recorded separately.
No full-grid analysis or original scientific campaign rerun for this repair.

Final SHA256:

```
candidate digest c33f2d31edbfbd3ae85c706ac4eb3b251d32adbd96b9db7b8c23bbaa37802c51
D06_RESULT.json 741bce941c42d0def4fb84ee612e2aa07156ee81311c7d0af7924d96becc02dc
flow_control.py 470929fc61b89af3dfead88e40d37d737b18c06ad0f1fe0c2daeb04ce4d458d0
```

The corrected mean/RMS is a dependent reconstructed field, not joint draws,
independent CF4 validation, physical distance correction or finite-z remainder.
