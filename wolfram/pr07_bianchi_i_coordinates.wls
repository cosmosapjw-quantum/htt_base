(* Coordinate derivation independent of the production Python RHS. *)
ClearAll["Global`*"];
coords = {t,x,y,z};
g = DiagonalMatrix[{-1,a1[t]^2,a2[t]^2,a3[t]^2}];
ginv = Simplify[Inverse[g]];
(* NB: do not name this Christoffel symbol "Gamma": that collides with the
   protected built-in Gamma (Euler gamma function), which silently voids the
   definition and yields theta=0. Use Chr instead. *)
Chr[mu_,nu_,rho_] := Simplify[1/2 Sum[ginv[[mu,lam]] (
  D[g[[lam,rho]],coords[[nu]]] + D[g[[lam,nu]],coords[[rho]]] - D[g[[nu,rho]],coords[[lam]]]
),{lam,1,4}]];

u = {1,0,0,0};
ucov = Simplify[g.u];
nablaU[mu_,nu_] := Simplify[D[ucov[[mu]],coords[[nu]]] - Sum[Chr[lam,mu,nu] ucov[[lam]],{lam,1,4}]];
theta = Simplify[Sum[ginv[[mu,nu]] nablaU[mu,nu],{mu,1,4},{nu,1,4}]];
H1 = a1'[t]/a1[t]; H2 = a2'[t]/a2[t]; H3 = a3'[t]/a3[t];

<|
 "schema" -> "htt.pr07.wolfram.bianchi_i_coordinates.v1",
 "theta" -> ToString[InputForm[theta]],
 "theta_minus_Hsum_zero" -> TrueQ[Simplify[theta-(H1+H2+H3)] == 0],
 "flrw_theta_minus_3H_zero" -> TrueQ[Simplify[(theta /. {a1->a,a2->a,a3->a}) - 3 a'[t]/a[t]] == 0]
|>
