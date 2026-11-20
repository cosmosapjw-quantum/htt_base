// R81 PHY-07: optional bounded-memory diagonal-weighted Gram/score/chi2.
// Pure numerical linear sufficient statistics, NOT a source-level PV covariance.
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

extern "C" int htt_weighted_gram_v1(
    const std::int64_t n, const std::int32_t p, const double* X,
    const double* w, const double* y, const std::int32_t threads,
    double* F_out, double* score_out, double* chi_out) noexcept {
    if (n<1 || p<1 || p>32 || threads<1 || threads>32 ||
        !X || !w || !y || !F_out || !score_out || !chi_out) return 1;
    try {
        const int nt=std::min<std::int64_t>(n,threads);
        const auto p2=static_cast<std::size_t>(p)*p;
        std::vector<std::vector<long double>> G(nt,std::vector<long double>(p2,0.L));
        std::vector<std::vector<long double>> b(nt,std::vector<long double>(p,0.L));
        std::vector<long double> chi(nt,0.L);
        std::vector<int> fail(nt,0);
#ifdef _OPENMP
#pragma omp parallel num_threads(nt) if(nt>1)
#endif
        {
            int tid=0,workers=1;
#ifdef _OPENMP
            tid=omp_get_thread_num();
            workers=omp_get_num_threads();
#endif
            auto& local=G[tid];
            auto& sc=b[tid];
            long double c=0.L;
            const auto start=n*tid/workers;
            const auto end=n*(tid+1)/workers;
            for (std::int64_t i=start;i<end;++i){
                const long double wi=w[i], yi=y[i];
                if(!(wi>=0.) || !std::isfinite(w[i]) || !std::isfinite(y[i])){
                    fail[tid]=2;break;
                }
                const double* row=X+static_cast<std::size_t>(i)*p;
                c+=wi*yi*yi;
                for (int j=0;j<p;++j){
                    const long double xj=row[j];
                    sc[j]+=wi*xj*yi;
                    for (int k=j;k<p;++k)
                        local[static_cast<std::size_t>(j)*p+k]+=wi*xj*row[k];
                }
            }
            chi[tid]=c;
        }
        for (const int e:fail)if(e)return e;
        for (int j=0;j<p;++j){
            long double c=0.L;
            for (int t=0;t<nt;++t)c+=b[t][j];
            score_out[j]=static_cast<double>(c);
            if(!std::isfinite(score_out[j]))return 3;
            for (int k=j;k<p;++k){
                long double a=0.L;
                for (int t=0;t<nt;++t)a+=G[t][static_cast<std::size_t>(j)*p+k];
                double value=static_cast<double>(a);
                if(!std::isfinite(value))return 3;
                F_out[static_cast<std::size_t>(j)*p+k]=value;
                F_out[static_cast<std::size_t>(k)*p+j]=value;
            }
        }
        long double c=0.L;
        for (int t=0;t<nt;++t)c+=chi[t];
        chi_out[0]=static_cast<double>(c);
        if(!std::isfinite(chi_out[0]))return 3;
        return 0;
    }catch(...){return 4;}
}
