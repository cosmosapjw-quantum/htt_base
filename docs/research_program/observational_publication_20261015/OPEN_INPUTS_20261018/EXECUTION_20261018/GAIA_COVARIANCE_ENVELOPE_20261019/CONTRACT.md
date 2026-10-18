# Frozen Gaia working-covariance envelope question — 2026-10-19

Owner obsstat; DIAGNOSTIC_ONLY, C0, transfer_source=none. Parent serializes the
read-only Astra /root/gaia_covariance_bound_frame contract. Requested framer and
independent reviewer gpt-6-astra/xhigh, coding executor gpt-6.1-sol/high; observed
runtime identities UNKNOWN. Base61fb65008c3a7f269690219e25cde6f8883976e3 on
research/htt-open-input-theory-20261018, existing primary checkout only. No
nested agents, new checkout, native solver/ODE, TAP/network, original fit replay,
main merge or journal submission. Existing D05 inputs are read-only.

## Falsifiable goal and frozen inputs

Evaluate all13 coordinatewise maximum variances allowed by published per-source
2x2 working marginal blocks and arbitrary PSD cross-source completions. Existing
D05 formal covariance/12-cell sensitivity do not already provide these maxima.
No physical source/frame covariance law is supplied by this calculation.

D05 is sibling D05_GAIA_RADIO. Required SHA256:

|Input|SHA256|
|---|---|
|D05/observable_vsh.py|318acb829f163eedda76a136a0edc4d247c17a6893f2faf24681e34fd79822b5|
|D05/sufficient_statistics.npz|6d899d4bad30c7f30f6b04ba8381ec623d9d5f6263d464d99d580d38437e2c83|
|D05/RESULTS.json|386bfa19ff1f0c24ec836f2e3e471717edf38c3c10da6d119d70548cf062baa0|
|External full.vot|e8454190bb3be7d10203ecfe6fe90b34d245fb13b9bb72a155242f85e4271810|

Raw /mnt/extdrive/workdir/htt_open_data/gaia/d05_full_20261018/full.vot:
192359368bytes,1614173rows. Verify full raw hash concurrently with ONE source
pass; reuse identical-byte D05 unique-ID/member-set/count/no-overflow evidence.
No raw rows/weights copied into Git or retained after a numerical batch.

KEEP=[0,1,2,6,7,8,9,10,11,12,13,14,15], FRAME=[3,4,5]. Frozen order:
E1_x,E1_y,E1_z,E2_xx-yy,E2_zz,E2_xy,E2_xz,E2_yz,
B2_xx-yy,B2_zz,B2_xy,B2_xz,B2_yz. Reuse D05 design()/Cartesian and
Frobenius-orthonormal STF conventions; these are not normalized Ylm powers.
Physical B1 remains UNKNOWN, not zero. Directions ICRS/J2016.0 degrees;
pmra=mu_alpha*cos(dec), pmdec=mu_delta. Convert errors mas/yr to microas/yr
once, promoting float32 columns to float64 BEFORE scaling. Variance units
microas^2/yr^2. Condition on directions, selected membership and fixed weights.

## Mathematics and claim ceiling

Let cached normal be N, R select KEEP, M=R N^{-1}, and
L_i=M X_i^T C_i^{-1}. This is full-fit coordinate selection, equivalent to
Schur frame quotient. Do NOT discard B1 columns before forming the weights.
Do not accumulate a new RHS, fit catalogue motions, rerun holdouts or radio.
Any displayed coefficient estimate must be copied from existing RESULTS.json.

Assume finite second moments and Cov(epsilon_i)=C_i, with arbitrary joint
Sigma>=0. For row ell_ki of L_i, s_ki=sqrt(ell_ki C_i ell_ki^T),
v_ref,k=sum_i s_ki^2 and v_max,k=(sum_i s_ki)^2. Cauchy-Schwarz yields
Var(qhat_k)<=v_max,k; v_ref is a block-diagonal WORKING reference, not measured
independence. Coordinatewise attainment in the relaxed PSD class follows from
a_i=C_i ell_ki^T/s_ki, epsilon_i=a_i Z+eta_i,
Cov(eta_i)=C_i-a_i a_i^T, independent residuals and Var(Z)=1. For s_ki=0
retain C_i in the residual, without dividing by zero.

The13 maxima need not be jointly attainable. Their diagonal is NOT a joint
covariance or Loewner upper bound. Compatibility with actual Gaia frame/source
constraints is UNKNOWN. Correctness of published working marginal errors after
selection or inclusion of all systematics is not established. Bias/mean errors
are unbounded/unmeasured here. No confidence/coverage/physical-error/cosmic-curl/
vorticity/family or K03 admission follows. Report floating-point evaluations of
the analytic envelope, NOT a directed-rounding numerical certificate or a new
GR theorem. Original17/42/all six NOT_READY_TO_SUBMIT remain unchanged.

Stable evaluation: t_ki=M_k X_i^T, a=t_0/sigma_alpha, b=t_1/sigma_delta;
s_ki^2=b^2+(a-rho_i b)^2/(1-rho_i^2). Accumulate s and s^2 with long-double
or compensated batch sums. Reject invalid/nonfinite values, never clip invalid
quadratics or inflate errors. Source batches at most25000rows; at most2 numerical
threads and512MiB maximum RSS checked during processing. Retain first failures.

## Frozen BINARY2 source schema and single-pass acceptance

VOTABLE version1.4, namespace http://www.ivoa.net/xml/VOTable/v1.3;
RESOURCE type=results; TABLE name=result_1792320789985. All scalar, no arraysize
or VALUES-null attribute. Exact field name / datatype / unit (absent means none):

```text
0 source_id long absent
1 ra double deg
2 dec double deg
3 pmra double mas.yr**-1
4 pmdec double mas.yr**-1
5 pmra_error float mas.yr**-1
6 pmdec_error float mas.yr**-1
7 pmra_pmdec_corr float absent
8 ra_pmra_corr float absent
9 ra_pmdec_corr float absent
10 dec_pmra_corr float absent
11 dec_pmdec_corr float absent
12 parallax double mas
13 parallax_error float mas
14 astrometric_params_solved short absent
15 ruwe float absent
```

Unaligned big-endian payload types:
>i8,>f8,>f8,>f8,>f8,>f4,>f4,>f4,>f4,>f4,>f4,>f4,>f8,>f4,>i2,>f4.
86payloadbytes plus2maskbytes=88bytes/row. NULL(j) is
(mask[j//8]>>(7-j%8))&1 for zero-basedj; NULL payload bytes remain present.
Required NULL indices0..7: fail on any. Required finite float indices1..7;
errors5,6 strictly positive, abs(correlation7)<1. Unused8..15 may be NULL or
nonfinite: retain missing status, do NOT zero-fill/reject rows/add new cuts.
Preserve D05 finite/unmasked direction validity; introduce no additional
coordinate-domain selection. No source row dropping.

The installed Astropy BINARY2 reader materializes base64 and loops rows;
chunk_size alone is NOT streaming. Implement only this frozen-schema reader,
not a general VOTable library. Reject unexpected schema, external STREAM href,
invalid base64/padding/data after padding, partial final quantum/row, incomplete
XML/missing structure or non-OK QUERY_STATUS including trailing OVERFLOW/ERROR.
Strip only XML whitespace in base64. Consume complete XML/trailer before
accepting outputs. Read once through open binaryFD, hash every original byte;
record FD/path (dev,ino,size,mtime_ns,ctime_ns) before/after, excluding atime,
and reject drift. Exact final count1614173/hash/zero rejected required rows.

Official primary protocol references qualified by framer:
[VOTable1.4 sections5.3–5.6/6](https://www.ivoa.net/documents/VOTable/20191021/REC-VOTable-1.4-20191021.html),
[TAP1.1 section3.4](https://www.ivoa.net/documents/TAP/20190927/REC-TAP-1.1.html),
[DALI1.1 sections4.4–4.4.2](https://www.ivoa.net/documents/DALI/20170517/REC-DALI-1.1.html).
The VOTable prose second-byte 'eighth column' example has an apparent typo;
the explicit one-bit-per-field MSB-first rule above matches installed Astropy
np.unpackbits. Test all16mask positions independently against tiny Astropy
fixtures. [Gaia primary source](https://arxiv.org/html/2204.12574v2) supports
tangent covariance/selection/frame, not a physical completion-class assumption.

## Controls, tolerances and bounded numerical execution

120seconds CUMULATIVE numerical execution for this new question, including
framer preflight, finite controls/parser tests, ONE actual pass and cached review.
First consumed unit is toolchunk37fa5c, exit0, observedwall.041371376s; preserved
in FRAMING_PREFLIGHT.txt and NUMERICAL_USAGE.jsonl. Thus119.958628624s remain
before any lower-tier execution. Source/code reading and writing implementation
are separate. Original D05/SDSS histories/allocations are not reset or merged.
Charge every launched numerical unit/failure. Reconcile incomplete entries
before continuation. No automatic source rerun/cap increase or hidden retries.
One locked budget consumer records exactcommands/start/end/elapsed/exit/cumulative,
source/code identity, actual resource observation and create-only raw/partials.
Independent reviewer remains read-only; any new numerical check is charged to
this same budget. No numerical execution outside the existing .venv/bin/python.

Run finite controls before opening actual catalogue data:
zero weights exactzero; one source C=[[4,1],[1,9]],ell=(1,-2) gives both36;
two sources C_i=I,ell_1=(1,0),ell_2=(-2,0) gives ref5,max9, attained by
crossblockdiag(-1,0) with PSD joint matrix. Test source/component permutations,
sign reversal, batch parity, stable versus direct ell C ell^T and unit scaling;
invalid covariance/nonfinite fail visibly. No observational mock generation.

Parser finite fixtures: all16nullpositions (required0..7fail,unused8..15remain
nullable); nonzero NULL payload consumed; signed/endian values; every chunk
split of short fixture including tags/quanta/rows; all3padding cases;
truncatedrow/XML/base64, trailingERROR/OVERFLOW; compare independent Astropy.
These are finite code controls, NOT replacement physical/null data.

For finite/cached algebra use E(A,B)=maxabs(A-B)/(1+maxabs(B))<=1e-12;
zero-reference tolerance is absolute1e-12, exact-zero kernel still exactzero.
Verify MN=R and equivalent Schur map; saved reference versus existing quotient
covariance under the same normalized tolerance.
For actual stream each positive d_k=(R N^{-1} R^T)_kk must satisfy
abs(sum_i s_ki^2-d_k)/d_k<=1e-10, RELATIVE only/atol0. Also accumulate
F_stream=sum_i L_i X_i,FRAME and require maxabs(F_stream)<=1e-10.
All13outputs finite/nonnegative and
v_max>=(1-1e-10)v_ref, v_max<=(1+1e-10)*n*v_ref.
Do not relax tolerances or choose coordinates after results.

Required coherent increment: code/focusedtests/rawoutcomes, all13 numerical
results and controls/metadata, useful PNG+PDF/report, one fresh independent
read-only Astra review; repair a concrete finding only if approved within the
unchanged cumulative cap. No new mandatory permanent gate/ledger beyond what
this bounded consumer/decision needs. Commit/push/draftPR only after review;
original science admission remains HOLD.
