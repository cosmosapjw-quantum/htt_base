ClearAll["Global`*"];
ss={{s11,s12,s13},{s12,s22,s23},{s13,s23,-s11-s22}}; ww={{0,w12,w13},{-w12,0,w23},{-w13,-w23,0}};
kr=KroneckerDelta;
mm=Table[Sum[(ss+ww)[[i,k]] kr[k,j]/3,{k,3}]-Sum[(ss+ww)[[k,l]] (kr[i,j] kr[k,l]+kr[i,k] kr[j,l]+kr[i,l] kr[j,k])/15,{k,3},{l,3}],{i,3},{j,3}];
sym=(mm+Transpose[mm])/2; anti=(mm-Transpose[mm])/2;
<|"SphereMomentM"->Simplify[mm],"ShearRecoveryResidual"->Simplify[5sym-ss],"VorticityRecoveryResidual"->Simplify[3anti-ww],"Trace"->Simplify[Tr[mm]]|>
