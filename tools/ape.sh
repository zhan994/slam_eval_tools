#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
python_bin=${PYTHON:-python3}

export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

exec "$python_bin" -m evo.main_ape "$@"