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

exec "$python_bin" "$script_dir/plot_pose_errors.py" \
  "$garlio" "$dlio" "$fast_lio2" "$faster_lio" \
  --ref "$reference" \
  --labels "GaRLIO" "DLIO" "FAST-LIO2" "Faster-LIO" \
  --colors '#2970ff' '#e74c3c' '#edae40' '#48ad2a' \
  --align "$alignment" \
  --t-max-diff 0.01 \
  --figsize 12 6.5 \
  --output "$output_dir/pose_errors.pdf" "$output_dir/pose_errors.png" \
  --dpi 300
