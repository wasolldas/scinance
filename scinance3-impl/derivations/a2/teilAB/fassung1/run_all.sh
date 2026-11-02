#!/bin/sh
set -e
cd "$(dirname "$0")"
python3 a2v_oi.py
python3 a2v_sigma30.py
python3 a2v_power.py
python3 a2v_build.py
