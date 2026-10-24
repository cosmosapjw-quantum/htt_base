# Independent actual-result review: HOLD

The first and only independent check stopped at `check.py:161` with `NEW_ZERO_LEVERAGE_MASK_MISMATCH`. No rerun occurred. The candidate numerical factor and its original result remain unchanged.

## Blocking finding

**Medium severity; contract acceptance blocked.** In the author's `factor.py:176`, `FACTOR.npz/extra_zero_leverage_mask` copies the parent's mask. It therefore describes the old K_hat, not the new exact K_fact. The actual SBFm channel has one singleton: original row 1484, group ID 11274. It is the reference and has no nonreference contrast. Its entire K_fact column is consequently exact zero. The inherited mask is false there. This is a newly introduced zero-leverage row, additional to the 944 mixed rows, which the contract requires to be explicit.

The exact factor and its values do not fail at this point; the saved metadata misrepresents effective leverage. At least the row above is proved wrong. The complete mismatch set was not persisted before the first-failure stop and is not asserted here.

The expected current mask is: every nonreference column is zero exactly when all five L entries are zero; every reference column is zero exactly when the exact sum of that channel's nonreference L entries is zero; mixed columns are zero. The current additional-zero mask is this full exact-zero mask excluding mixed rows. The old source mask can remain under an explicitly inherited-source name.

## Observed validation before the failure

The bound sequential checker reached line 161 only after its source/candidate hashes, all 35,970 IDs/order, support, seven channels, 35,026 singleton rows, 944 mixed structural zeros, reference rule, integer pair construction and bit-preserved L checks passed. Its independent integer-dyadic direct evaluation L*(y_i-y_ref) exactly matched all five candidate rational values. It also matched the exact old contraction, seven channel sums, correction, D-weighted price, display rational errors, saved-parent difference, all tensor components, full numerical KB/KN matrices, norms, singular values and rank-at-tolerance labels.

These are partial validation results, evidenced by the immutable checker and first-failure traceback. NUMERIC_CHECK.json was not produced because serialization follows the failed assertion. No all-checks PASS is claimed.

The reviewer's combined actual row/channel-remapping checks, independent subnormal/tiny-nonzero witnesses, final identity rehash and successful output serialization occur after line 161 and were not executed. The author's separately bound controls did execute successfully; final source lines 63-70 include the required combined row/channel permutation, closing the preliminary preparation concern.

## Mathematical and claim scope

The integer pair structure establishes D_diff A=0 for every fixed admitted support-simplex A: each pair joins singleton rows with the same one-hot channel response and no mixed row enters. Thus the stored rational factor removes the admitted additive calibration mean, covariance and residual-calibration cross terms whenever the required moments exist. This statement concerns the fixed source model and exact factored operation. Rounded matrix expansion or ordinary floating evaluation retains a numerical-only ceiling.

KB and KN remain numerical diagnostics, with reported Frobenius residuals 2.910753887385572e-15 and 3.09126881657751e-15 respectively. They do not certify exact unbiased coordinates or nuisance immunity. Physical response, residual covariance, selection, PV and empirical null remain unresolved; original H02/H03/H04, native family and four-axis CAS status receive no promotion.

## Bounded repair handoff

Derive the current exact zero-leverage mask from the existing saved factor and correct only factor/result/report metadata in a new preserved repair candidate. Preserve all original arrays and exact values except the erroneous mask, retain the source mask under an unambiguous inherited name if needed, and identify the additional zero row(s) and cause. No estimator fit, old source producer, catalogue, exact full-data contraction or original control replay is needed. Preserve this failed candidate, checker and receipt. Root will route the repair and charge it to the same account; a different fresh reviewer must inspect the changed candidate because this review seeds the repair definition.

## Resource observation

One group started. The child was reaped at 2.410455375 s; products fsync observation was 2.508039219 s; outer monotonic after receipt fsync was 2.838776773 s. External /usr/bin/time reported 2.88 s and lifetime maximum RSS 51,436 KiB; combined polled runner/child RSS was 71,258,112 bytes. The first exec API yielded (host wait 1.001469008 s, API wall 1.207 s, functions display 1.3 s); the completion poll used host wait 0.000013486 s and API wall 0.002 s. Because execution spanned a yielded session, these API segments are not a whole-command timing. A 3.0 s conservative debit is suggested, explicitly not an exact measurement, subject to root settlement of overlapping observations once. No account was reset.

