(* Exact input submitted to the connected Wolfram Language evaluator. *)
Clear[bb, ff, kk, ss];
ff = 4 bb/(3+bb^2);
kk = 3/(2+Sqrt[4-3 ff^2]);
FullSimplify[{kk ff-bb, kk ff^2-4 bb^2/(3+bb^2)}, Assumptions -> 0<bb<1]
