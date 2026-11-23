# R101 acquisition wrapper — independent scoped review

I used local fixtures and the frozen R99 product plan. No live provider request or owner-file change was made by the reviewer. The six R101 IDs, URLs, expected lengths and provider MD5 fields match the R99 file (SHA-256 `012ebc7a87a4c5ef8a6c37307232a4c8ad733411163944428aea1cf29df3cdb9`). The two LoTSS HEAD observations have historical attribution. Four records have a provider MD5 and two have only provider length plus locally measured digests.

**Existing-file preservation.** The downloader verifies bytes in a temporary directory on the destination filesystem, then uses hard-link creation to publish without replacement. In two independent simulated concurrent arrivals, a differing same-sized file remained untouched, while an identical file was reused and the six fixture bytes already transferred were accounted. Each trial left only the winning file. Missing execute arguments, default listing and selected dry-run do not send requests or publish product files. The selective-network-free tests loaded the unused optional sky-map import through a stub and used unchanged R99/R100 intake functions.

**Budget finding.** With the initial wrapper, an overlong test response declaring nine bytes, expected size nine and budget nine consumed 262,144 bytes before the R100 streaming check rejected it. No destination payload was published. This occurs because the inherited read requested a fixed full chunk before checking the remainder. For the tested production contract an exact application-level HTTP payload bound requires identity encoding, unambiguous length framing, and capping each underlying read by the current remainder. Transport headers, TCP/TLS overhead and kernel buffers lie outside an application payload count.

**Closed after repair.** The revised R101 reader validates a single matching Content-Length and identity framing, then limits each underlying read to its remaining body length. For 262,144 available fixture bytes and a nine-byte declared payload, the only underlying read requested and consumed nine bytes. For a 262,151-byte limit and 524,288 fixture bytes available, the reads were 262,144 and seven bytes, with a validated 262,151-byte output. A five-byte truncated body under the nine-byte contract left zero products. Ambiguous length/encoding fixtures were rejected before any body read; a mismatched provider MD5 also left no product. All nine retained test methods passed independently. No acquisition defect remains open for the declared fixed-length HTTP payload contract. Actual provider availability was not checked in this review.

| Reviewed candidate file | SHA-256 |
|---|---|
| scripts/r101/acquire.py | `3fede491101f7d576f1871fec68a45beca4503effa8f5abe4bc54d6890eec2d7` |
| tests/obsstat/test_r101_acquire.py | `6a6f462b6f09405f221b5ffeeebf5fca920ac102f4377b640b41f47c7cf7184d` |
| DATA_ACQUISITION_PLAN.json | `ba49c3b5c47676938b522bce94649554f7232a68c3ced8c062b49a61f0ed61d5` |
| DATA_ACTIONS_KO.md | `fb478b74fc8f843b7f1179e4692ab0cbca14472bf2606ceab5c5027f6e149e4c` |
