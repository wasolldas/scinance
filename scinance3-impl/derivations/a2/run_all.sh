#!/bin/bash
# Part C: tests, two full runs (bit-identical check), then the official JSON.  Prints only sha256 / counts.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pytest -q -p no:cacheprovider test_c_guards.py | tail -1
for run in 1 2; do
  python3 c1_nullsim.py > /dev/null
  python3 c2_funding.py > /dev/null
  python3 c3_pilot.py > /dev/null
  python3 c_build.py --out "work/a2_teilC_run${run}.json" > /dev/null
  (cd work && sha256sum c1.json c2.json c3.json "a2_teilC_run${run}.json" | sed "s/_run${run}//") > "work/sha_run${run}.txt"
done
cmp work/sha_run1.txt work/sha_run2.txt && echo "zwei Laeufe bitgleich"
cat work/sha_run2.txt
python3 c_build.py
