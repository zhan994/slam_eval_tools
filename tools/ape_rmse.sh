#!/bin/sh
# Replace data_dir and trajectory file names with your TUM files.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
python_bin=${PYTHON:-python3}
cd "$repo_root"

data_dir="/home/zhan"
output_dir="/home/zhan"
alignment="none"

reference="$data_dir/NJFlatB01.txt"
garlio="$data_dir/NJFlatB01_GARLIO.txt"
dlio="$data_dir/NJFlatB01_DLIO.txt"
fast_lio2="$data_dir/NJFlatB01_FASTLIO2.txt"
faster_lio="$data_dir/NJFlatB01_FASTERLIO.txt"

exec "$python_bin" "$script_dir/ape_rmse.py" \
  "$garlio" "$dlio" "$fast_lio2" "$faster_lio" \
  --ref "$reference" \
  --labels "GaRLIO" "DLIO" "FAST-LIO2" "Faster-LIO" \
  --align "$alignment" \
  --t-max-diff 0.01 \
  --t-offset 0.0 \
  --output "$output_dir/ape_rmse.csv"
