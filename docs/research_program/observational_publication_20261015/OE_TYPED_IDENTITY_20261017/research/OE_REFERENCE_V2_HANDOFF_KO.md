# HTT P2/L01 OE: conditional reference-qualified source-lock v2

2026-10-17 Asia/Seoul. Scope is **source/data admission for a finite masked spin-2 geometry operator**, not an empirical E/B significance claim. Parent authority: Draft PR #554 (historical v1 code with typed diagnostics) stacked on #553. Canonical `PUBLICATION_DAG.json` blob `ac4a94c3da13f142eaab3b06b5275b58096c95e1` remains immutable.

## 1. Evidence separation

- **User-observed, not assistant-computed**: common SHA256 `c967e45449596c561c940d7ca0d494f1a26d947e6b5a9ef44185fdbf93b036d4`, HM `33226759f339c099818968f777013984f97d5ec2c04e1816f61ae72930b40296`; both matched historical v1 locks and PMASK structural contract.
- OE current local SHA256 and independently located reference SHA256 equal `1b2b4138f791b739938485fa0ebcac5f462e04fbc55626e93d71abd04aac3900`. Their entire 50,331,648-pixel Galactic/NESTED/NSIDE2048 float32 PMASK comparison returned `SEMANTIC_EQUIVALENT_PMASK`, no different pixel. Each source has 201,335,040 bytes. The historical lock `1b2b4138f791b739938485fa0ebcac5f462e04aac3900` is a **45-character, malformed SHA**; it equals the reported 64-digit SHA with the single 19-character substring `fbc55626e93d71abd04` deleted.
- Official public product type/name are documented by NASA/IPAC IRSA, https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/previews/COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00/index.html . However, a separate reference path and identical SHA alone **cannot authenticate which server supplied those bytes**. Provenance status: `USER_REPORTED_IRSA_DOWNLOAD__NOT_PUBLISHER_SIGNED`. The reference data are never said to be official-publisher-SHA-verified.
- **Derived:** given the reported checksums, `BYTE_IDENTICAL(local,reference)` within SHA256 collision resistance; given the reported semantic check, `PMASK_SEMANTIC_EQUIVALENT` for equal fixed-order pixel arrays. Neither is a Planck E/B observational statement.

## 2. Source qualification contract

`v1` remains the default/immutable historical source lock. `v2` uses a separate versioned manifest and is **never auto-enabled by a compare receipt**. Common/HM must pass their existing, unchanged v1 SHA locks and strict PMASK structural check. OE must pass 64-character v2 SHA, strict FITS PMASK structural validation, and match a physically distinct, non-symlink/hardlink reference on both byte digest and all decoded pixel values. `--compare-root` is required for OE; common/HM reference downloads are unnecessary. The computed v2 receipt clearly separates `local BYTE_IDENTICAL`, `REFERENCE_BYTE_IDENTICAL_TO_PINNED_SOURCE`, `SEMANTIC_EQUIVALENT_PMASK`, `provenance user-reported`, and `P2_L01_NOT_READY_FOR_PHYSICAL_CLAIM`.

A malicious reference copied from local under another inode can pass local-content verification. This does not defeat cryptographic identity checks but prevents any unqualified claim of **independent data-acquisition provenance**. Retain the user's original retrieval command/log/URL for manuscript provenance. If official publisher hash is subsequently made available, add it as a separate evidence item and compare; do not retrospectively rewrite historical receipts.

## 3. Geometric caveat and new exact finite construction

Define high-resolution Boolean PMASK fields `m_c,m_h,m_o`, averaging/downsampling operator `D` and strict threshold `t=.5`. The source's original algorithm uses

`M_post = 1{D m_c>t} 1{D m_h>t} 1{D m_o>t}`

and not necessarily

`M_pre = 1{D(m_c m_h m_o)>t}`.

Because `D` is positive, `D(m_c m_h m_o) <= min_j D(m_j)`, hence `M_pre <= M_post` pointwise, but equality does **not** follow. On four manufactured fine pixels, `m_c=(1,1,1,0)`, `m_h=(0,1,1,1)`, `m_o=(1,0,1,1)`, all three averages are 3/4 while the Boolean triple-intersection average is 1/4. Thus `M_post=1`, `M_pre=0`. The chosen policy is correctly recorded; a different policy needs a distinct result provenance and new `K` calculation.

For low and high spin-2 real-design matrices `L,H` on the selected sky, the finite geometric coefficient leakage `K(W)=(L^T W L)^{-1}L^T W H` admits exact update

`K(W+ΔW)-K(W)=[L^T(W+ΔW)L]^{-1} L^T ΔW [H-L K(W)]`,

when both Gram matrices are invertible. Changing the selected geometry may change `K`; pixel count alone is not a quantitative bound. As in PR #554 this identity is **mathematical**, not evidence for physical Planck B-mode contamination.

The native output now includes SHA256 for every effective RING64 Boolean mask (`uint8`, C order) and explicit policy text. This will make subsequent mask/beam/processing comparisons traceable without prematurely granting P2 source null/exchangeability.

## 4. Verification and paper-gate state

| Step | Deliverable | This run's verification | Official 6-paper DAG |
|---|---|---|---|
| R5 scoped continuation | Exact noncommutation counterexample and identification of geometric mask policy | derived, manufactured test PASS | 14/42 |
| C5 | Opt-in `source_lock_v2`, immutable old lock, OE-only independent reference check, per-mask result hashes | implementation written and native-source CLI guarded | 14/42 |
| C6 | Source corruption/reused pin/aliasing/semantic/positive-CLI/bitmap/commutator regressions | **24/24 pytest PASS**, no native FITS in sandbox | 14/42 |
| Publish/handoff | Immutable manifest, command and distinct science/provenance claims | package SHA verification and draft GitHub source readback if posted | 14/42 |

P1=1/6, P2=0/6, P3=2/6, P4=1/6, P5=1/5, P6=2/6, COMMON=7/7. READY=L01,S02. No official node state is promoted by this source repair; P2 physical null, FFP matched simulation, beam+foreground transfer, later look-elsewhere trials and manuscript admission are NOT_RUN. Six papers remain NOT_READY_TO_SUBMIT.

## 5. Next local work

At the owner's machine, retain official reference URL/download log, run v2 verify-only, then geometry production with `--source-lock v2 --compare-root /mnt/extdrive/workdir/htt_planck_irsa_reference`. Check that the spin-frame HEALPix reference and selected mask hashes are stable; preserve `L01_NATIVE_PR3_POL_K64x90_v2.json` and its linked NPZ. Distinguish polarization PMASK geometry from actual Q/U sky, signal response, full high-ell leakage and beam/systematics. No merge or journal submission in this scope.
