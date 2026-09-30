ClearAll["Global`*"];
metric=DiagonalMatrix[{-1,1,1,1}];
beta={b1,b2,b3}; gamma=1/Sqrt[1-beta.beta];
u=gamma Prepend[beta,1]; k={-1,n1,n2,n3};
zeta0=gamma; zeta=gamma beta;
aa=1/(tt Sqrt[1-v^2]); bb=-v/(tt Sqrt[1-v^2]);
ass=Element[{b1,b2,b3,n1,n2,n3},Reals] && beta.beta<1;
<|"intercept_affine_residual"->FullSimplify[k.metric.u-zeta0-zeta.{n1,n2,n3},ass],
"intercept_mass_shell"->FullSimplify[zeta0^2-zeta.zeta,ass],
"intercept_velocity_residual"->FullSimplify[zeta/zeta0-beta,ass],
"rest_temperature_recovery_explicit_substitution"->FullSimplify[1/Sqrt[aa^2-bb^2]-tt,tt>0 && Element[v,Reals] && -1<v<1]|>
