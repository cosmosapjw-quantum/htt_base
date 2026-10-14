#!/bin/bash
# scratch probe runner: lake env lean on a probe file; output kept next to it
T=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/g16a_coherency_l2_collision_v1_20261013
cd /home/cosmosapjw/lean_oracles/viii_oracle && timeout 900 lake env bash -c "LEAN_PATH=$T/raw/imports:\$LEAN_PATH lean $1" > $1.out 2>&1; echo "exit $?" >> $1.out; cat $1.out
