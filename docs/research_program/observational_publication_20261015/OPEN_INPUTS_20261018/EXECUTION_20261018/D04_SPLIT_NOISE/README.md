# D04 actual split-noise processing

Goal: acquire and validate the four public PR3 SMICA HM1/HM2/OE1/OE2 noise
products at nominal ID00000, then apply the unchanged original T26846/P30021
native-child estimator and fixed L02 family. Reuse completed full-mission ID0
and the eight-pair cache; do not replay them. Keep the five products as one
nominal-ID tuple, never five independent skies or a covariance ensemble.

Intake branch research/htt-open-input-theory-20261018, HEAD
1528ebd3c4ace48a561b9dcaa6d5f891121a22a5. Parent owns this directory and only the
external split_noise acquisition targets. Other workers own disjoint lanes.
Requested parent route Sol/high; independently observed runtime UNKNOWN.

Completion for this bounded increment: four full FITS identities with explicit
units/order/layout validation; exact original source/mask/operator checks;
joint coefficient/contrast and morphology diagnostics; tests, results, plots,
scope report and a separate fresh read-only review. Fixed weights and beam
provenance must be inspected, not executed as upstream code. Signal response,
foreground/selection coverage and stochastic independence remain separate input
obligations; successful downloads cannot close original L03.

Raw files remain outside Git under
/mnt/extdrive/workdir/htt_open_data/planck/PR3/split_noise/.
Use the manifest's explicit four-product batch, maximum4GiB/reserve2GiB.
Preserve failed partial transfers; reconcile ETag/length/Content-Range before
any recovery. No solver, ODE, main merge or journal submission.
