ClearAll["Global`*"];
metric=DiagonalMatrix[{-1,1,1,1}]; gam=1/Sqrt[1-v^2];
lor={{gam,gam v,0,0},{gam v,gam,0,0},{0,0,1,0},{0,0,0,1}};
original=DiagonalMatrix[{0,hx,hy,hz}];
obs=Transpose[lor].original.lor; uobs=gam{1,-v,0,0};
sp=obs[[2;;4,2;;4]]; mean=Tr[sp]/3;
h0=obs[[1,1]]+mean; h1=-2obs[[1,2;;4]]; q=sp-mean IdentityMatrix[3];
lift=ArrayFlatten[{{{{h0}}, {(-h1/2)}},{Transpose[{(-h1/2)}],q}}];
ass=Element[{v,hx,hy,hz,nx,ny,nz},Reals] && -1<v<1;
null={-1,nx,ny,nz};
deg=DiagonalMatrix[{0,0,hy,hz}]; udeg={Cosh[r],Sinh[r],0,0};
<|"lorentz_residual"->FullSimplify[Transpose[lor].metric.lor-metric,ass],
"matter_normalization"->FullSimplify[uobs.metric.uobs,ass],
"null_form_residual"->FullSimplify[null.lift.null-null.obs.null,ass && nx^2+ny^2+nz^2==1],
"metric_ambiguity_residual"->FullSimplify[lift-obs+mean metric,ass],
"timelike_eigenvector_residual"->FullSimplify[(metric.lift).uobs+mean uobs,ass],
"reconstruction_residual"->FullSimplify[lift+mean metric-obs,ass],
"dipole"->FullSimplify[h1,ass],
"dipole_linear"->Normal[Series[h1,{v,0,1}]],
"degenerate_timelike_kernel"->FullSimplify[deg.udeg,Element[r,Reals]],
"degenerate_normalization"->FullSimplify[udeg.metric.udeg,Element[r,Reals]]|>
