// R79: optional portable exact-source Gaussian Gaia normal-equation reducer.
// F = sum B^T C_2x2^-1 B; score = sum B^T C^-1 y; chi2 = sum y^T C^-1 y.
// No cosmology, no Bianchi solver, no fast-math or source selection mutation.
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

extern "C" int htt_vsh_normal_v1(
    const std::int64_t n, const std::int32_t p,
    const double* B, const double* y,
    const double* e1, const double* e2, const double* rho,
    const std::int32_t requested_threads,
    double* out_F, double* out_score, double* out_chi) noexcept {
    if (n < 1 || p < 1 || p > 32 || requested_threads < 1 ||
        requested_threads > 64 || B == nullptr || y == nullptr ||
        e1 == nullptr || e2 == nullptr || rho == nullptr ||
        out_F == nullptr || out_score == nullptr || out_chi == nullptr) {
        return 1;
    }
    try {
        const int nt = std::min<std::int64_t>(requested_threads, n);
        const auto p2 = static_cast<std::size_t>(p) * p;
        std::vector<std::vector<long double>> Fs(nt, std::vector<long double>(p2, 0.0L));
        std::vector<std::vector<long double>> bs(nt, std::vector<long double>(p, 0.0L));
        std::vector<long double> cs(nt, 0.0L);
        std::vector<int> errors(nt, 0);
#ifdef _OPENMP
#pragma omp parallel num_threads(nt) if(nt > 1)
#endif
        {
            int tid = 0, workers = 1;
#ifdef _OPENMP
            tid = omp_get_thread_num();
            workers = omp_get_num_threads();
#endif
            auto& F = Fs[tid];
            auto& score = bs[tid];
            long double chi = 0.0L;
            const std::int64_t begin = n * tid / workers;
            const std::int64_t end = n * (tid + 1) / workers;
            for (std::int64_t i = begin; i < end; ++i) {
                const long double s1 = e1[i], s2 = e2[i], r = rho[i];
                if (!(s1 > 0.0L && s2 > 0.0L && std::abs(r) < 1.0L) ||
                    !std::isfinite(static_cast<double>(s1)) ||
                    !std::isfinite(static_cast<double>(s2)) ||
                    !std::isfinite(static_cast<double>(r))) {
                    errors[tid] = 2;
                    break;
                }
                const long double det = 1.0L - r*r;
                const long double w00 = 1.0L/(s1*s1*det);
                const long double w11 = 1.0L/(s2*s2*det);
                const long double w01 = -r/(s1*s2*det);
                const long double mu0 = y[2*i], mu1 = y[2*i+1];
                const long double v0 = w00*mu0 + w01*mu1;
                const long double v1 = w01*mu0 + w11*mu1;
                chi += mu0*v0 + mu1*v1;
                const double* a = B + (2*i)*p;
                const double* b = B + (2*i+1)*p;
                for (int j = 0; j < p; ++j) {
                    const long double x0 = a[j], x1 = b[j];
                    score[j] += x0*v0+x1*v1;
                    for (int k=j; k<p; ++k) {
                        const long double z0=a[k],z1=b[k];
                        F[static_cast<std::size_t>(j)*p+k] +=
                            w00*x0*z0 + w11*x1*z1 + w01*(x0*z1+x1*z0);
                    }
                }
            }
            cs[tid] = chi;
        }
        for (auto error : errors) {
            if (error) return error;
        }
        long double total_chi=0.0L;
        for (int j=0; j<p; ++j) {
            long double v=0;
            for (int t=0;t<nt;++t) v+=bs[t][j];
            out_score[j]=static_cast<double>(v);
            if (!std::isfinite(out_score[j])) return 3;
            for (int k=j;k<p;++k) {
                long double sum=0.0L;
                for (int t=0;t<nt;++t) sum+=Fs[t][static_cast<std::size_t>(j)*p+k];
                const double val=static_cast<double>(sum);
                if (!std::isfinite(val)) return 3;
                out_F[static_cast<std::size_t>(j)*p+k]=val;
                out_F[static_cast<std::size_t>(k)*p+j]=val;
            }
        }
        for (int t=0;t<nt;++t)total_chi+=cs[t];
        out_chi[0]=static_cast<double>(total_chi);
        if (!std::isfinite(out_chi[0])) return 3;
        return 0;
    } catch (...) {
        return 4;
    }
}
