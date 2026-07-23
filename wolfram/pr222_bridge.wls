Needs["xAct`xTensor`"]; Print["XACT_LOAD_OK"];
W = {{10,1,0},{2,8,1},{0,2,7},{6,3,2}};
G = Transpose[W].W;
detG = Det[G];
multiRank = MatrixRank[W];
singleRank = MatrixRank[W[[1;;1]]];
Print["det_G=", detG]; Print["multi_rank=", multiRank]; Print["single_rank=", singleRank];
If[detG === 394584 && multiRank === 3 && singleRank === 1, Print["PR222_WOLFRAM_PASS"], Print["PR222_WOLFRAM_FAIL"]];
Exit[0];
