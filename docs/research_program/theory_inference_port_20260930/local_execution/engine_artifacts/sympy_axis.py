"""CAS-07/09 finite algebra under the shared CAS_CONTRACT, no data claim."""
import sympy as s

known, undefined, exceed = s.symbols("known undefined exceed", real=True)
assert s.expand((known + exceed) - known - exceed) == 0
assert s.expand((known + undefined) - (known + exceed) - (undefined - exceed)) == 0
# With 0 <= exceed <= undefined, the two differences above are nonnegative.
print("CAS07_INTERVAL_DIFFERENCES=PASS_CONDITIONAL_NONNEGATIVE_INPUTS")

H = s.Matrix([[1, 0, 0], [-1, 1, 0], [0, -1, 1]])
c11, c12, c13, c22, c23, c33 = s.symbols("c11 c12 c13 c22 c23 c33")
C = s.Matrix([[c11, c12, c13], [c12, c22, c23], [c13, c23, c33]])
assert H.det() == 1
assert H.inv() * H == s.eye(3)
assert (H * C * H.T).T == H * C * H.T
print("CAS09_INVERSE_AND_FULL_COVARIANCE=PASS")
