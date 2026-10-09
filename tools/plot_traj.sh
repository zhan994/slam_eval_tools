#!/bin/sh
# Usage: sh tools/plot_traj_example.sh
# Replace the paths below with your TUM trajectory files.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
python_bin=${PYTHON:-python3}

# Relative paths below are resolved from the repository root.
cd "$repo_root"
data_dir="/home/zhan"
output_dir="/home/zhan"

reference="$data_dir/NJFlatB01.txt"
garlio="$data_dir/NJFlatB01_GARLIO.txt"
dlio="$data_dir/NJFlatB01_DLIO.txt"
fast_lio2="$data_dir/NJFlatB01_FASTLIO2.txt"
faster_lio="$data_dir/NJFlatB01_FASTERLIO.txt"

# none: original coordinates; origin/se3/sim3: align using matched timestamps.
alignment="none"

exec "$python_bin" "$script_dir/plot_traj.py" \
  "$garlio" "$dlio" "$fast_lio2" "$faster_lio" \
  --ref "$reference" \
  --labels "GaRLIO" "DLIO" "FAST-LIO2" "Faster-LIO" \
  --colors '#2970ff' '#e74c3c' '#edae40' '#48ad2a' \
  --align "$alignment" \
  --t-max-diff 0.01 \
  --figsize 10 7.5 \
  --legend-cols 5 \
  --output "$output_dir/comparison.pdf" "$output_dir/comparison.png" \
  --dpi 300
