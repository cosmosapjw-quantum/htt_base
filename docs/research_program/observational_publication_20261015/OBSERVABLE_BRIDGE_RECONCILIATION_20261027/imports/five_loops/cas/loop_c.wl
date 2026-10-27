(* LOOP C: exact polynomial sphere projections; no ODE/solver. *)
ClearAll[x,y,z,s1,s2,s3,s4,s5,b1,b2,b3,h,a1,a2,a3,d1,d2,d3];
n={x,y,z}; ss={{s1,s3,s4},{s3,s2,s5},{s4,s5,-s1-s2}};
bb={b1,b2,b3}; aa={a1,a2,a3}; dd={d1,d2,d3};
pp=IdentityMatrix[3]-Outer[Times,n,n];
mu=pp.ss.n+Cross[n,bb]+pp.dd;
rad=h+n.ss.n-aa.n;
avgMon[e_List]:=If[AnyTrue[e,OddQ],0,Times@@(Factorial2/@(e-1))/Factorial2[Total[e]+1]];
avg[f_]:=Total[(#[[2]] avgMon[#[[1]]])& /@ CoefficientRules[Expand[f],{x,y,z}]];
invS=5 Table[avg[(mu[[i]] n[[j]]+mu[[j]] n[[i]])/2],{i,3},{j,3}];
invB=-3/2 (avg /@ Cross[n,mu]); invD=3/2 (avg /@ mu);
invRadS=15/2 Table[avg[rad (n[[i]] n[[j]]-KroneckerDelta[i,j]/3)],{i,3},{j,3}];
checks={Simplify[invS-ss],Simplify[invB-bb],Simplify[invD-dd],
Simplify[invRadS-ss],Simplify[avg[rad]-h],Simplify[-3(avg /@ (rad n))-aa],
Simplify[avg[rad^2+mu.mu]-(h^2+Tr[ss.ss]/3+aa.aa/3+2 bb.bb/3+2 dd.dd/3)]};
checks
