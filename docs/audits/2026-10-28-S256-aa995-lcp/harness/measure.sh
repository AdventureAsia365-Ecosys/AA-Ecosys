#!/usr/bin/env bash
# AA-995 S256: Lighthouse mobile (default emulation + simulated throttling), 3 runs per page, then the median.
# Usage: bash measure.sh <label> [base=http://localhost:3995] [runs=3]
set -u
D=/home/nghiep/projects/AA-Ecosys/.tmp-session/S256/aa995
LABEL=$1; B=${2:-http://localhost:3995}; RUNS=${3:-3}
LH=/home/nghiep/.npm/_npx/8b4cb255bb85bc41/node_modules/lighthouse/cli/index.js
OUT=$D/lh/$LABEL; mkdir -p $OUT
PAGES=${PAGES:-"home|/ tour|/tours/sri-lanka-cultural-tour-kandy-dambulla-and-sigiriya-3-days-sri-lanka-28e22489 bhutan|/destinations/bhutan destinations|/destinations"}
for p in $PAGES; do
  n=${p%%|*}; u=${p#*|}
  for i in $(seq 1 $RUNS); do
    CHROME_PATH=/usr/bin/google-chrome timeout 180 node $LH "$B$u" --quiet --output=json --output-path=$OUT/$n-$i.json \
      --chrome-flags="--headless=new --no-sandbox --ignore-certificate-errors" --only-categories=performance ${EXTRA:-} </dev/null >/dev/null 2>&1 || echo "run failed $n $i"
  done
done
python3 $D/summarize.py $OUT
