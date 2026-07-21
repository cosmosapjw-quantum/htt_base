/-
PR-175 eleven-type anchor arithmetic over ℚ (Lean 4 core, no mathlib).
Closed rational facts only: the external anchor formula evaluated on the
pinned canonical representatives equals the pinned Ricci-scalar values,
the class-B canonical constraint holds, and the VI_h/VII_h h-relations
hold. The symbolic Koszul chains live on the other three axes.
No Bianchi family is ranked or identified.
-/

namespace Pr175Invariant

structure Rep where
  n1 : Rat
  n2 : Rat
  n3 : Rat
  a  : Rat
  expected : Rat

def anchor (r : Rep) : Rat :=
  -(1/2 : Rat) * (r.n1^2 + r.n2^2 + r.n3^2)
    + (r.n1 * r.n2 + r.n2 * r.n3 + r.n3 * r.n1)
    - 6 * r.a^2

def reps : List Rep := [
  ⟨0, 0, 0, 0, 0⟩,            -- I
  ⟨1, 0, 0, 0, -1/2⟩,         -- II
  ⟨1, -1, 0, 0, -2⟩,          -- VI_0
  ⟨1, 1, 0, 0, 0⟩,            -- VII_0
  ⟨1, 1, -1, 0, -5/2⟩,        -- VIII
  ⟨1, 1, 1, 0, 3/2⟩,          -- IX
  ⟨0, 0, 0, 1, -6⟩,           -- V
  ⟨0, 0, 1, 1, -13/2⟩,        -- IV
  ⟨0, 1, -1, 1, -8⟩,          -- III
  ⟨0, 1, -1, 1/2, -7/2⟩,      -- VI_h (h = -1/4)
  ⟨0, 1, 1, 1/2, -3/2⟩        -- VII_h (h = 1/4)
]

def allAnchorsMatch : Bool := reps.all (fun r => anchor r = r.expected)

/-- class B canonical form: a ≠ 0 forces n1 = 0. -/
def classBConstraint : Bool := reps.all (fun r => r.a = 0 || r.n1 = 0)

/-- VI_h (h = -1/4) and VII_h (h = 1/4) rows READ FROM the reps table:
    a^2 = |h| * |n2 n3| with sign(h) = sign(n2 n3). Editing either table
    row breaks this check. -/
def viH : Rep := reps.getD 9 ⟨0, 0, 0, 0, 0⟩
def viiH : Rep := reps.getD 10 ⟨0, 0, 0, 0, 0⟩

def hRelationFor (r : Rep) (h : Rat) : Bool :=
  let prod := r.n2 * r.n3
  (r.a ^ 2 = (if h < 0 then -h else h) *
      (if prod < 0 then -prod else prod))
    && ((0 < h) = (0 < prod)) && (r.n1 = 0)

def hRelations : Bool :=
  hRelationFor viH (-1/4) && hRelationFor viiH (1/4)

theorem anchors_match : allAnchorsMatch = true := by native_decide
theorem class_b : classBConstraint = true := by native_decide
theorem h_rel : hRelations = true := by native_decide

end Pr175Invariant
