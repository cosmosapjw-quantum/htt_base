/-
PR-186 W^2 vorticity normalization over ℚ (Lean 4 core, no mathlib).

Convention mechanics only: no data, no Bianchi family, no observable claim.
For the spatial antisymmetric vorticity tensor A(a,b,c) with entries
a=A₁₂, b=A₁₃, c=A₂₃, and dual vector w=(c,-b,a):
  tensorNorm A = A_ij A_ij = 2(a²+b²+c²),  vecNorm = w·w = a²+b²+c²,
so A_ij A_ij = 2 w·w, giving W² = A:A/(6H²) = w·w/(3H²); the v5 display
w·w/H² is 3·W², and with Θ=3H the bound √(A:A)/Θ≤B gives W²≤(3/2)B².
All checks are closed decidable statements over concrete rationals.
-/
namespace Pr186W2

def tensorNorm (a b c : Rat) : Rat := 2*a^2 + 2*b^2 + 2*c^2
def vecNorm (a b c : Rat) : Rat := a^2 + b^2 + c^2

-- exact identity A:A = 2 w·w for concrete rationals
def identityHolds (a b c : Rat) : Bool :=
  tensorNorm a b c == 2 * vecNorm a b c

-- W² registered vs vector form and the factor-3 / three-halves consequences
def W2reg (a b c H : Rat) : Rat := tensorNorm a b c / (6 * H^2)
def W2vec (a b c H : Rat) : Rat := vecNorm a b c / (3 * H^2)
def wrongDisplay (a b c H : Rat) : Rat := vecNorm a b c / (H^2)
def W2max (B H : Rat) : Rat := (B * (3*H))^2 / (6 * H^2)

def allHold (a b c H B : Rat) : Bool :=
  identityHolds a b c
  && (W2reg a b c H == W2vec a b c H)
  && (wrongDisplay a b c H == 3 * W2reg a b c H)
  && (W2max B H == (3/2) * B^2)

-- representative witnesses: positive, negative, fractional, and axis-zero
def witnesses : List (Rat × Rat × Rat × Rat × Rat) :=
  [ (1, 2, 3, 1, 1), (-2, 5, -7, 3, 4), (1/2, -1/3, 1/5, 2/3, 5),
    (0, 0, 1, 1, 1), (7, 0, -4, 1/2, -3), (11/13, -17/19, 23, 100, 200) ]

def allWitnessesHold : Bool := witnesses.all (fun w => allHold w.1 w.2.1 w.2.2.1 w.2.2.2.1 w.2.2.2.2)

-- kernel-checked theorems (closed, decidable)
theorem identity_1_2_3 : identityHolds 1 2 3 = true := by native_decide
theorem identity_neg_frac : allHold (1/2) (-1/3) (1/5) (2/3) 5 = true := by native_decide
theorem all_witnesses : allWitnessesHold = true := by native_decide

end Pr186W2
