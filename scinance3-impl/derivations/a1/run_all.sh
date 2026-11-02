#!/bin/sh
# A1 Stufe 1 -- full reproduction (outcome-blind by construction, see a1_common.py / a1_nuisance.py).
# Run from any directory that is NOT the panel folder; python -I keeps the panel folder off sys.path.
set -e
S=/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung
cd /tmp
A1_EXCL1H=0 python -I $S/a1_explore.py            # loads the union panel once, writes cache/a1_data.pkl
for cfg in 0 1; do
  export A1_EXCL1H=$cfg
  python -I $S/a1_window_census.py
  python -I $S/a1_nuisance.py
  python -I $S/a1_formation_sensitivity.py
  python -I $S/a1_psi_by_class.py
  python -I $S/a1_power.py
done
export A1_EXCL1H=0
python -I $S/a1_kill4_ci.py
python -I $S/a1_check_factor.py
python -I $S/a1_selfcheck.py
python -I $S/a1_bookkeeping.py
python -I $S/a1_consolidate.py
