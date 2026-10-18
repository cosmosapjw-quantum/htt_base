# Source-qualified coordinate precision amendment

Approved by original source framer `/root/pantheon_source_null_contract`, requested
`gpt-6-astra/xhigh`, observed UNKNOWN, before the numerical campaign. Changes
only the RA/DEC versus SIM_RA/DEC comparison in CONTRACT.md. Preserve the
original double-ULP rejection as historical evidence; no numerical tolerance is
relaxed to make a source pass. All other scientific/cumulative limits remain.

Pinned SNANA v11_04e commit3871158844627b3f976e3c0261c466578d6b0a39 proves:

- [sndata.h:198–199/341](https://github.com/RickKessler/SNANA/blob/3871158844627b3f976e3c0261c466578d6b0a39/src/sndata.h#L198): RA/DEC are double; SIM_RA/SIM_DEC are float.
- [snlc_sim.c:21038–21039 and21131–21132](https://github.com/RickKessler/SNANA/blob/3871158844627b3f976e3c0261c466578d6b0a39/src/snlc_sim.c#L21038): both are assigned from GENLC coordinates, narrowing the SIM pair.
- [sntools_dataformat_fits.c:433–434/1813–1820/2074–2076](https://github.com/RickKessler/SNANA/blob/3871158844627b3f976e3c0261c466578d6b0a39/src/sntools_dataformat_fits.c#L1813): SIM values are promoted into value_1D, columns declared1D and written TDOUBLE.

For finite/range-valid/uniquely joined rows, require exact numeric equality:

```
SIM_RA  == float64(float32(RA))
SIM_DEC == float64(float32(DEC))
```

Record `SNANA_FLOAT32_PROMOTED_TO_FITS_FLOAT64`. Use released double RA/DEC
downstream. Any mismatch remains SOURCE_COORDINATE_DISAGREEMENT, not a widened
tolerance, coordinate normalization or inferred frame. Add controls: valid
promotion passes; SIM coordinate changed by one float32 step fails.

Framer acquired two additional original source files outside Git:
`sndata.h`,17958bytes,SHA256
`b7f929cf3146952451c24e434554a5fda5ac95ee06c31b12ed0a677b5ec0bf07`;
`sntools_dataformat_fits.c`,181904bytes,SHA256
`eab64a8183fa805a5bf3a0c36c5618f9bbacd24813736d9f6f623c2c9b292564`.
Additional199862bytes makes planned unique acquisition15687158/20000000bytes.
No paper object was downloaded outside the framing directory; those accesses
were web-only. Update actual acquisition accounting rather than hiding new bytes.

This verifies a source serialization path, not an angular selection law, external
reference frame, physical calibration, H02/S02 acceptance or submission readiness.
