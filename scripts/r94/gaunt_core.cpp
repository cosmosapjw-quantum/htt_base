// R94 C++17/OpenMP kernel: R93 normalized L=2 Gaunt a_lm a*_{l+2,m-M}.
// Pure numerical helper. No external IO, mutable globals or scientific gate.
// Complex128 NumPy input is a contiguous array of interleaved real/imag doubles.
#include <cstddef>
#include <cstdint>
#include <complex>
#include <cmath>

extern "C" int htt_r94_gaunt_project(
    const double * const input,
    int64_t nrow, int64_t nalm, int64_t nterm,
    const int32_t * const idx_a,
    const int32_t * const idx_b,
    const int8_t * const code_a,
    const int8_t * const code_b,
    const double * const weights,
    double gaunt_norm,
    double * const out) noexcept {
  if (!input || !idx_a || !idx_b || !code_a || !code_b ||
      !weights || !out || nrow < 1 || nalm < 1 || nterm < 1 ||
      !std::isfinite(gaunt_norm) || gaunt_norm <= 0.) return 1;
  for (int64_t j=0;j<nterm;++j)
    if (idx_a[j] < 0 || idx_b[j] < 0 ||
        idx_a[j] >= nalm || idx_b[j] >= nalm ||
        code_a[j] < -1 || code_a[j] > 1 ||
        code_b[j] < -1 || code_b[j] > 1 ||
        !std::isfinite(weights[j])) return 2;
  #pragma omp parallel for schedule(static)
  for (int64_t i=0;i<nrow;++i) {
    const double* row = input + 2 * i * nalm;
    std::complex<double> acc(0.0,0.0);
    for (int64_t j=0;j<nterm;++j) {
      const int64_t a = 2LL*idx_a[j], b=2LL*idx_b[j];
      std::complex<double> x(row[a],row[a+1]);
      std::complex<double> y(row[b],row[b+1]);
      if (code_a[j] != 0) {
        x=std::conj(x);
        if (code_a[j] == -1) x = -x;
      }
      if (code_b[j] != 0) {
        y=std::conj(y);
        if (code_b[j] == -1) y = -y;
      }
      acc += weights[j] * x * std::conj(y);
    }
    acc /= gaunt_norm;
    out[2*i]=acc.real();
    out[2*i+1]=acc.imag();
  }
  return 0;
}
