// R82: source-coupled four-window strict weighted event bounds.
// Same row = same joint draw. Never renormalize a defined subset or multiply
// four correlated marginals. OpenMP parallel only across thresholds.
#include <array>
#include <cstdint>
#include <cmath>
#ifdef _OPENMP
#include <omp.h>
#endif
extern "C" int htt_p1_joint_tail_v1(
  std::int64_t n,std::int64_t nt,
  const double* q,const double* w,const std::int8_t* reasons,
  const double* thresholds,std::int32_t threads,double* out) noexcept {
  if(n<=0||nt<=0||threads<1||threads>32||
     !q||!w||!reasons||!thresholds||!out)return 1;
  int bad=0;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(threads) reduction(|:bad)
#endif
  for(std::int64_t it=0;it<nt;++it){
    const double t=thresholds[it];
    if(!std::isfinite(t)){bad|=2;continue;}
    std::array<long double,6> lo{},hi{};
    for(std::int64_t i=0;i<n;++i){
      const long double weight=w[i];
      if(weight<0||!std::isfinite(w[i])){bad|=4;break;}
      bool any_yes=false,any_unknown=false,all_yes=true,any_no=false,all_no=true;
      for(int j=0;j<4;++j){
        const std::size_t ix=static_cast<std::size_t>(i)*4+j;
        const int r=reasons[ix];
        if(r<0||r>2){bad|=8;break;}
        const bool known=(r==0);
        const double val=q[ix];
        if((known && !std::isfinite(val)) ||
           (!known && !std::isnan(val))){bad|=16;break;}
        const bool yes=known && val>t;
        const bool no=known && !(val>t);
        if(yes)lo[j]+=weight;
        if(!no)hi[j]+=weight;
        any_yes|=yes;
        any_unknown|=!known;
        all_yes&=yes;
        any_no|=no;
        all_no&=no;
      }
      if(bad)break;
      if(any_yes)lo[4]+=weight;
      if(!all_no)hi[4]+=weight;
      if(all_yes)lo[5]+=weight;
      if(!any_no)hi[5]+=weight;
    }
    if(bad)continue;
    for(int j=0;j<6;++j){
      out[static_cast<std::size_t>(it)*12+j]=static_cast<double>(lo[j]);
      out[static_cast<std::size_t>(it)*12+6+j]=static_cast<double>(hi[j]);
    }
  }
  return bad;
}
