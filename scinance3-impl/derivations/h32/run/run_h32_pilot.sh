#!/bin/bash
# DEC-101 Teil 2: exactly one pilot run into the pinned directory; sha256 of the registered YAML as the start lock
S=/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad
cd /home/user/scinance
Y=scinance3-impl/state/registered/h32_v1.yaml
SHA=$(sha256sum $Y | cut -d' ' -f1)
date -u +%H:%M:%S > $S/h32_pilot.start
PYTHONPATH=/home/user/scinance/src python -u scripts/h32_fm8.py --pilot --registered $Y --registered-sha256 $SHA --panel-base $S/panel/panel_1d --delisted-base $S/panel_delisted_v2 --start-year 2021 --end-year 2026 --as-of 2026-09-28 --allow-partial --out scinance3-impl/state/runs/h32_pilot_v1 --seed 53 > $S/h32_pilot.log 2>&1
echo "rc=$? end=$(date -u +%H:%M:%S) start=$(cat $S/h32_pilot.start)" >> $S/h32_pilot.log
