# HFI RIMO R3.01 source-content intake

Owner obsstat, source qualification only, C0/non-claim-bearing; transfer source
none. Astra framing `/root/pantheon_source_response_review`, requested
gpt-6-astra/xhigh, observed UNKNOWN. Deterministic executor requested
gpt-6.1-sol/high, observed UNKNOWN. Preserve all completed D04/L01/L02/eight-pair
and scalar POL_BEAM results; no numeric beam/map/noise computation here.

Question: does this actual archive supply split-specific response, matrix or
uncertainty information supporting the original selected-support response
G(R_a-R_b), or what exact source insufficiency remains?

Only official source:
https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/HFI_RIMO_BEAMS_R3.01.tar.gz
Expected86556876bytes, destination outside Git:
/mnt/extdrive/workdir/htt_open_data/planck/PR3/beams/HFI_RIMO_BEAMS_R3.01.tar.gz.
Parent has launched the existing create-only fetch tool in session56304; DO NOT
download again. Reuse its verified object/receipt, preserve partials/failures.
Record provider status/final URL/ETag/Last-Modified/size/gzip/localSHA256; upstream
checksum UNAVAILABLE unless an explicitly linked official checksum exists.
Compare internal release declarations with R3.01; do not resolve conflicts by fiat.

Hard bounds:100000000new HTTP body bytes including any recovery/checksum document;
600s acquisition wall; at most one separately identity-qualified resumable
recovery, no blind overwrite/reset. Metadata inspection120s, <=2threads,
<=1GiB cumulative decompressed stream, <=16MiB retained decoded metadata,
<=4096members, <=1MiB per FITS HDU header or documentation member, <=512MiB
inspection memory. Partial limit => INTAKE_INCOMPLETE, never absence evidence.

Stream without filesystem extraction or upstream execution. Index ordinal,
literal name/type/declaredsize; duplicate names remain distinct. Never follow
links or use member names as output paths. Read bounded README/release/convention
text and all reachable FITS HDU headers, skipping array payloads while charging
skipped decompressed bytes. No numerical FITS columns, beam-function calculation,
square roots of spectrum windows, SHT or processed-map work.

Capture evidenced frequency/detector/full/hm1/hm2/oe1/oe2 bindings; HDU names,
dimensions, columns/types/units/matrix axes/multipole range; amplitude transfer
versus spectrum window versus cross-spectrum mixing/covariance/uncertainty modes;
T/E/B/cross-field definitions and any explicit lm-to-l'm'/spatial/scan dependence;
normalization/pixel-window/calibration/LFI-renormalization/SMICA-weight connections;
uncertainty normalization/eigenvalues/split-channel correlations/confidence meaning.
Names alone do not qualify semantics. A spectrum window matrix is not a harmonic
map-response matrix; full-mission products do not silently bind to splits.

One compact assessment consumes the source index, decisive metadata excerpts
with locations and resource accounting. Its determination must be exactly one:
METADATA_SUPPORTS_NEXT_TARGETED_NUMERIC_READ (exact member/HDU/column/convention,
numeric validity unchecked), SOURCE_INSUFFICIENT_FOR_NAMED_RESPONSE (only after
complete permitted inspection, exact missing fields), or INTAKE_INCOMPLETE
(exact uninspected contents and obstruction). No new permanent gate/registry.

Separate read-only Astra source assessment/review before any scoped publication
decision. No original-node completion, L03 admission, scientific campaign,
map reprocessing, submission or native solver/ODE is authorized here. User's
draft-publication scope remains subject to independent review, not this intake.
