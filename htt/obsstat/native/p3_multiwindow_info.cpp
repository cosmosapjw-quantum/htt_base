// R83 optional source-coherent H03 multiwindow WLS sufficient statistics.
// F_j = sum_i w_ij X_i X_i^T; b_j = sum_i w_ij X_i y_i.
// Four overlapping redshift windows share the exact same selected CF4 group IDs.
// C++17, long-double summation, OpenMP across independent windows, no fast-math.
// Not a full peculiar-velocity/calibration covariance or physical H(z,n).
#include <cstdint>
#include <cmath>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

extern "C" int htt_p3_multiwindow_info_v1(
    std::int64_t n,std::int32_t p,std::int32_t nw,
    const double* X,const double* W,const double* y,
    std::int32_t threads,double* F,double* b) noexcept {
  if(n<1 || p<1 || p>16 || nw<1 || nw>16 ||
     !X || !W || !y || !F || !b || threads<1 || threads>32)return 1;
  int error=0;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(threads) reduction(|:error)
#endif
  for (int j=0;j<nw;++j){
    const std::size_t p2=static_cast<std::size_t>(p)*p;
    std::vector<long double> local(p2,0.L),score(p,0.L);
    for (std::int64_t i=0;i<n;++i){
      const long double w=W[static_cast<std::size_t>(i)*nw+j];
      const long double yi=y[i];
      if (!(w>=0) || !std::isfinite(W[static_cast<std::size_t>(i)*nw+j]) ||
          !std::isfinite(y[i])){error|=2;break;}
      const double* xi=X+static_cast<std::size_t>(i)*p;
      for(int a=0;a<p;++a){
        const long double z=xi[a];
        score[a]+=w*z*yi;
        for(int k=a;k<p;++k)local[static_cast<std::size_t>(a)*p+k]+=w*z*xi[k];
      }
    }
    if(error)continue;
    for(int a=0;a<p;++a){
      const double val=static_cast<double>(score[a]);
      if(!std::isfinite(val)){error|=4;break;}
      b[j*p+a]=val;
      for(int k=a;k<p;++k){
        const double z=static_cast<double>(local[static_cast<std::size_t>(a)*p+k]);
        if(!std::isfinite(z)){error|=4;break;}
        F[static_cast<std::size_t>(j)*p2+a*p+k]=z;
        F[static_cast<std::size_t>(j)*p2+k*p+a]=z;
      }
    }
  }
  return error;
}
