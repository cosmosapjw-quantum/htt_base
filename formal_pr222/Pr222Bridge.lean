import Pr222Bridge.Basic
open Pr222Bridge
def main : IO Unit := do
  IO.println s!"det_G={detG}"
  IO.println s!"single_window_minor={singleWindowMinor}"
  IO.println (if checks then "PR222_LEAN_PASS" else "PR222_LEAN_FAIL")
