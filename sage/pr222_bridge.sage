W = matrix(QQ, [[10,1,0],[2,8,1],[0,2,7],[6,3,2]])
G = W.transpose()*W
detG = G.det(); multi = W.rank(); single = W[0:1,:].rank()
print("det_G=%s"%detG); print("multi_rank=%s"%multi); print("single_rank=%s"%single)
print("PR222_SAGE_PASS" if (detG==394584 and multi==3 and single==1) else "PR222_SAGE_FAIL")
