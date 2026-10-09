#!/bin/sh
# Edit directories, sequences, methods and templates to match your TUM files.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
python_bin=${PYTHON:-python3}
cd "$repo_root"

data_dir="/home/zhan"
output_dir="/home/zhan"
alignment="none"

exec "$python_bin" "$script_dir/batch_ape_rmse.py" \
  --data-dir "$data_dir" \
  --sequences NJFlatB01 NJFlatB02 \
  --methods GARLIO DLIO FASTLIO2 FASTERLIO \
  --labels "GaRLIO" "DLIO" "FAST-LIO2" "Faster-LIO" \
  --ref-pattern '{sequence}.txt' \
  --est-pattern '{sequence}_{method}.txt' \
  --align "$alignment" \
  --t-max-diff 0.01 \
  --t-offset 0.0 \
  --output "$output_dir/batch_ape_rmse.csv"
