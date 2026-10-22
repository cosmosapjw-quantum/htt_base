#!/bin/bash
# usage: probe.sh <probe.lean>  (scratch; compiles without -o)
T=$(cd "$(dirname "$0")/../.." && pwd)
cd /home/cosmosapjw/lean_oracles/viii_oracle && timeout 900 lake env bash -c "LEAN_PATH=$T/raw/imports:\$LEAN_PATH lean $1" > "$1.out" 2>&1; echo "exit $?" >> "$1.out"; cat "$1.out"
