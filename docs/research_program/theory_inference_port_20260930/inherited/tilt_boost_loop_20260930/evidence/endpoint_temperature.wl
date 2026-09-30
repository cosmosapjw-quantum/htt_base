ClearAll["Global`*"];
d=gam(1+b mu); zobs=(1+z)/d-1;
daobs=d da; dlobs=dl/d;
temp=tt/(gg(1-v nu));
aa=gg/tt; bb=-gg v/tt;
<|"redshift_distance_invariant"->Simplify[(1+zobs)daobs-(1+z)da],
"luminosity_distance_invariant"->Simplify[dlobs/(1+zobs)-dl/(1+z)],
"same_ray_ratio_invariant"->Simplify[((1+z1)/d)/((1+z2)/d)-(1+z1)/(1+z2)],
"inverse_temperature_affine"->Simplify[1/temp-aa-bb nu],
"rest_temperature_recovery"->FullSimplify[1/Sqrt[aa^2-bb^2]-tt,tt>0 && 0<=v<1 && gg==1/Sqrt[1-v^2]],
"beta_recovery"->Simplify[-bb/aa-v]|>
