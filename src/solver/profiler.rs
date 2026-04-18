//! Lightweight profiler for per-function timing.
//! Uses thread-local accumulators to avoid synchronization overhead.
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

static MATRIX_BUILD_NS: AtomicU64 = AtomicU64::new(0);
static RODAS5P_NS: AtomicU64 = AtomicU64::new(0);
static DOPRI5_NS: AtomicU64 = AtomicU64::new(0);
static SOURCE_EXTRACT_NS: AtomicU64 = AtomicU64::new(0);
static LU_FACTOR_NS: AtomicU64 = AtomicU64::new(0);
static BESSEL_NS: AtomicU64 = AtomicU64::new(0);
static KMODE_COUNT: AtomicU64 = AtomicU64::new(0);

pub(crate) fn reset() {
    MATRIX_BUILD_NS.store(0, Ordering::Relaxed);
    RODAS5P_NS.store(0, Ordering::Relaxed);
    DOPRI5_NS.store(0, Ordering::Relaxed);
    SOURCE_EXTRACT_NS.store(0, Ordering::Relaxed);
    LU_FACTOR_NS.store(0, Ordering::Relaxed);
    BESSEL_NS.store(0, Ordering::Relaxed);
    KMODE_COUNT.store(0, Ordering::Relaxed);
}

pub(crate) fn add_matrix_build(ns: u64) { MATRIX_BUILD_NS.fetch_add(ns, Ordering::Relaxed); }
pub(crate) fn add_rodas5p(ns: u64) { RODAS5P_NS.fetch_add(ns, Ordering::Relaxed); }
pub(crate) fn add_dopri5(ns: u64) { DOPRI5_NS.fetch_add(ns, Ordering::Relaxed); }
pub(crate) fn add_source_extract(ns: u64) { SOURCE_EXTRACT_NS.fetch_add(ns, Ordering::Relaxed); }
pub(crate) fn add_lu(ns: u64) { LU_FACTOR_NS.fetch_add(ns, Ordering::Relaxed); }
pub(crate) fn add_bessel(ns: u64) { BESSEL_NS.fetch_add(ns, Ordering::Relaxed); }
pub(crate) fn inc_kmode() { KMODE_COUNT.fetch_add(1, Ordering::Relaxed); }

pub(crate) fn report() -> String {
    let n = KMODE_COUNT.load(Ordering::Relaxed).max(1);
    let mb = MATRIX_BUILD_NS.load(Ordering::Relaxed) as f64 / 1e6;
    let r5 = RODAS5P_NS.load(Ordering::Relaxed) as f64 / 1e6;
    let dp = DOPRI5_NS.load(Ordering::Relaxed) as f64 / 1e6;
    let se = SOURCE_EXTRACT_NS.load(Ordering::Relaxed) as f64 / 1e6;
    let lu = LU_FACTOR_NS.load(Ordering::Relaxed) as f64 / 1e6;
    let bj = BESSEL_NS.load(Ordering::Relaxed) as f64 / 1e6;
    let total = mb + r5 + dp + se;
    format!(
        "PROFILE ({} k-modes):\n\
         Matrix build: {:>8.1} ms ({:>5.1}%) [{:.1} ms/k]\n\
         Rodas5P:      {:>8.1} ms ({:>5.1}%) [{:.1} ms/k]\n\
         DoPri5:       {:>8.1} ms ({:>5.1}%) [{:.1} ms/k]\n\
         Source extr:  {:>8.1} ms ({:>5.1}%) [{:.1} ms/k]\n\
         LU factor:    {:>8.1} ms (incl. in Rodas5P)\n\
         Bessel:       {:>8.1} ms (C_ℓ assembly)\n\
         k-solve sum:  {:>8.1} ms",
        n,
        mb, mb/total.max(1e-9)*100.0, mb/n as f64,
        r5, r5/total.max(1e-9)*100.0, r5/n as f64,
        dp, dp/total.max(1e-9)*100.0, dp/n as f64,
        se, se/total.max(1e-9)*100.0, se/n as f64,
        lu, bj, total
    )
}
