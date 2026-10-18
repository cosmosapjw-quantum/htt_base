# Independent source-qualification review

SCOPED_PASS, no blocking findings. Author /root/hfi_source_intake requested
gpt-6.1-sol/high; fresh independent reviewer /root/hfi_source_review requested
gpt-6-astra/xhigh. Both observed runtime identities remain UNKNOWN. The reviewer
did not frame or implement this candidate, edit files, fetch, replay the archive,
extract members or inspect numerical columns.

Reviewed exact SHA256 identities:

|File|SHA256|
|---|---|
|SOURCE_ASSESSMENT.md|00455a79a18345242949630af427499957eae6ba4d9b00f86afdaa2585c2803f|
|SOURCE_INDEX_DOUBLE_GZIP.json|9f1ade812b50a466efba3750b3b64f1b4bd2be59d7762f2355cc37fd51e24606|
|inspect_double_gzip.py|ad89b5c6835e4f7c200d0290bb8999f1e0453dd296c9eeaff4010e74010f85fc|
|test_double_gzip.py|27a1f93fb1c5d4391f11bb38dec5a5f6456af664ba2311395e8f7c586c1b6665|

Independent offline checks:12tests PASS/2.34s, including corrupt inner/outer gzip
trailers, invalid tar checksum, third-layer rejection, shared cumulative limits
and the preserved parser fixtures. Prior evidence hashes match. The reviewer
checked member/HDU spans and complete index counts:452members,451FITS,1319HDUs;
116T/E/B amplitude-window products,196T-only,139power-window products.

The explicit two-layer amendment retains strict tar checksums and both EOF/CRC
checks; decoded skips/replay are charged to the shared meter. Cumulative
206907570decodedbytes/3.929714recordedseconds carry prior1536bytes/1.563056s.
Metadata/member/header/memory/observed-thread limits remain satisfied. The raw
first failure and bounded format diagnosis are retained, not rewritten as PASS.

Members14/22 explicitly bind 100hm1/100hm2 detector labels and T/E/B B(l)
columns with a header rule to square for power. W(l) is explicitly spectral
cross-talk, not a general map-response operator. The current source-only
assessment supports a separately contracted targeted numeric read.

Draft publication is permitted for this C0/non-claim-bearing source qualification
only. Numerical validity, row-to-multipole convention, normalization, exact map
binding, uncertainty law and original selected-support G(R_a-R_b) remain outside
this review's admission. D04/L03, original17/42 and all six NOT_READY_TO_SUBMIT
states are unchanged. No repair is requested; no source or numerical rerun.
