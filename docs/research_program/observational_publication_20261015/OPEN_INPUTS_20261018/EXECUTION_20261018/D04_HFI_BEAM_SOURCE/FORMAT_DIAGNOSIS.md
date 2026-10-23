# Approved bounded format diagnostic

Determination remains `INTAKE_INCOMPLETE`; owner obsstat, scope source-format
qualification only, C0/non-claim-bearing, transfer source none. The original
`inspect_source.py`, `SOURCE_INDEX.json`, tests and `ASSESSMENT.md` are preserved.
This note supplements the first assessment without replacing its first failure.

The frozen source was rehashed successfully to
`187755434816addc045f13a4efd8515bb86b83531adc0eb7586412d9cfca4994`,
86,556,876 bytes. The approved diagnostic read 512 bytes after the first gzip
layer. At offset zero those bytes begin `1f8b0800c9e6555b0003`: another gzip
stream. They do not begin FITS SIMPLE/XTENSION or ZIP. Treating these compressed
bytes as a tar header explains the original checksum failure: bytes 148–155
are `ffe6efb7bff9facb`, not an octal checksum; the independently calculated tar
unsigned and signed checksums would be 86,345 and -695.

The observed nested-gzip signature justified the single approved inner-prefix
probe. It decoded exactly 512 inner bytes from the existing outer 512-byte
prefix, with no additional outer reads. The inner prefix is a GNU tar directory
header:

| Inner prefix byte offset | Literal evidence |
|---|---|
| 0 | `BeamWf_HFI_R3.01/` followed by null padding |
| 124–135 | Declared member size octal zero |
| 148–155 | `012524\x00 `, stored checksum octal 012524 = 5,460 |
| 156 | `5`, directory type |
| 257–262 | `ustar ` |
| 263–264 | ` \x00`, GNU tar version bytes |

Independent checksum calculations on this inner header, with checksum field
replaced by eight spaces, give unsigned 5,460 and signed 5,460. Both match the
stored checksum. No checksum bypass or unexplained prefix skip is indicated.
The directory name is container evidence only; it does not qualify any response,
release-content, full-mission or split-channel semantics.

`PREFIX_DIAGNOSTIC.json` retains exact hex and escaped bytes for both 512-byte
prefixes, frozen-source identity and original source-index hash. New decoded
bytes, charging both layers and replayed bytes: 1,024; cumulative including the
first failed 512: 1,536. Diagnostic elapsed: 0.7750537360552698 s. Prior parent-
observed wall charge: conservatively 0.788 s; cumulative recorded charge:
1.5630558799020946 s of the same 120-second inspection limit. Diagnostic limit:
10 s and 4,096 new decoded bytes. Observed threads: 1; max RSS high-water value:
419,600 KiB; address-space cap: 536,870,912 bytes. No extra acquisition,
filesystem extraction, link following, numerical FITS columns or full inspection
replay occurred. Requested executor gpt-6.1-sol/high; observed runtime UNKNOWN.

Command, canonical interpreter, exit 0:

```text
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D04_HFI_BEAM_SOURCE/diagnose_prefix.py
```

Minimal proposed repair for Astra approval: preserve the first parser; add an
explicit two-gzip-layer source wrapper bound to this observed container. Meter
every delivered decompressed byte in both layers, including all skipped bytes,
against the remaining shared 1 GiB allowance. Use the existing strict tar
checksum/parser behavior on the inner stream. Carry the 1,536 bytes and at least
the conservative 1.563056-second prior charge into any authorized continuation,
along with metadata retained from this diagnostic. Reject unexpected additional
compression rather than recursively unpacking it. A full metadata continuation
has not been run or approved by this diagnostic. All FITS/document semantics
remain unqualified, and separate independent Astra source assessment remains
required before any scoped publication decision.
