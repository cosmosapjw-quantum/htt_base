(* Exact finite rest-frame algebra, shared CLAIM_CONTRACT.json. *)
Clear[cc, d, gap, l1, l2, l3];
l = {l1, l2, l3};
Dcols = Array[d, {4,3}];
B = Table[-cc Dcols[[mu,i]]/l[[i]], {mu,4}, {i,3}];
K = B[[2;;4]];
theta = Tr[K];
shear = (K+Transpose[K])/2-theta IdentityMatrix[3]/3;
vort = (K-Transpose[K])/2;
axis = {vort[[2,3]],vort[[3,1]],vort[[1,2]]};
accel = cc B[[1]];
lhs = theta^2/3+Tr[shear.Transpose[shear]]+2 axis.axis+
  accel.accel/cc^2;
rhsExact = Total[Flatten[B]^2];
Print["VERSION=",System`$Version];
Print["ORTHOGONAL_DECOMPOSITION_RESIDUAL=",
  ToString[InputForm[FullSimplify[lhs-rhsExact]]]];
Print["COLUMN_NORM=",ToString[InputForm[FullSimplify[rhsExact]]]];
Print["GAP_BOUND_TERM=",ToString[InputForm[cc^2 Total[Flatten[Dcols]^2]/gap^2]]];
Print["GAP_ASSUMPTIONS=cc>0,gap>0,Abs[l_i]>=gap for i=1..3"];
Print["EIGENVECTOR_DERIVATIVE=-(cc) Inverse[L].D from differentiating T.u=-epsilon u and rest projection"];
Print["NEGATIVE_CONTROL=for T^a_b=-rho delta^a_b, L=0; any future unit timelike u is an eigenvector"];
Print["DIVERGENCE_RELATION=nabla_a A^a = D_a A^a + A^2/cc^2 for A.u=0"];
Print["VORTICITY_SIGN=omega_ij=(K_ij-K_ji)/2 (derivative-first); reversed convention changes sign"];
