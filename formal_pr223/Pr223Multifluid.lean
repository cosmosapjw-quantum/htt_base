import Pr223Multifluid.Basic
open Pr223Multifluid
def main : IO Unit := do
  IO.println s!"first_moment={firstMoment}"
  IO.println s!"trace_K={traceK}"
  IO.println s!"aniso3_trace={aniso3Trace}"
  IO.println (if checks then "PR223_LEAN_PASS" else "PR223_LEAN_FAIL")
