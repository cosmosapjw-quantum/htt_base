ClearAll["Global`*"];
metric=DiagonalMatrix[{-1,1,1,1}];
beta={b1,b2,b3}; b2sum=beta.beta;
gam=1/Sqrt[1-b2sum]; u=gam Prepend[beta,1];
uc=metric.u; t=(eps+p) Outer[Times,uc,uc]+p metric;
en=t[[1,1]]; j=-t[[2;;4,1]]; stress=t[[2;;4,2;;4]];
ass=Element[{b1,b2,b3,eps,p},Reals] && b2sum<1 && eps+p>0;
f[r_]:=2r/(1+Sqrt[1+4r^2]);
<|"normalization"->FullSimplify[u.metric.u,ass],
"energy_residual"->FullSimplify[en-((eps+p)gam^2-p),ass],
"flux_residual"->FullSimplify[j-(eps+p)gam^2 beta,ass],
"velocity_residual"->FullSimplify[j/(en+p)-beta,ass],
"rank_one_stress_residual"->FullSimplify[stress-p IdentityMatrix[3]-Outer[Times,j,j]/(en+p),ass],
"inverse_beta_residual"->FullSimplify[f[v/(1-v^2)]-v,0<=v<1],
"inverse_monotonic"->FullSimplify[D[f[r],r]>0,r>=0],
"inverse_at_zero"->f[0]|>
