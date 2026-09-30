ClearAll["Global`*"];
metric=DiagonalMatrix[{-1,1,1,1}];
u={Cosh[r],Sinh[r],0,0}; gradCov={q0,0,0,0};
hupper=metric+Outer[Times,u,u];
xi=(gradCov.hupper.gradCov)/(-gradCov.metric.gradCov);
(* Minkowski kinematic congruence only; not a single-fluid Einstein solution. c=1. *)
du=rp{Sinh[r],Cosh[r],0,0}; acc=u[[1]] du;
deriv=Table[If[a==1,du[[b]],0],{a,4},{b,4}];
dlower=deriv.metric; proj=IdentityMatrix[4]+Outer[Times,u,metric.u];
bcov=Transpose[proj].dlower.proj;
theta=Tr[deriv]; hcov=metric+Outer[Times,metric.u,metric.u];
shear=(bcov+Transpose[bcov])/2-theta hcov/3;
omega=(bcov-Transpose[bcov])/2;
ass=Element[{r,rp,q0},Reals] && q0!=0;
<|"clock_tilt"->FullSimplify[xi,ass],
"clock_residual"->FullSimplify[xi-(Cosh[r]^2-1),ass],
"theta"->FullSimplify[theta,ass],
"acceleration_norm"->FullSimplify[acc.metric.acc,ass],
"shear_contraction"->FullSimplify[Tr[(metric.shear).(metric.shear)],ass],
"vorticity"->FullSimplify[omega,ass],
"same_velocity_different_acceleration"->FullSimplify[acc/.r->0,ass]|>
