#!/usr/bin/env python3
"""Evaluate rotation and translation APE RMSE across sequences and methods."""

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from evo import EvoException
from tools.ape_rmse import ape_rmse
from tools.plot_traj import align_trajectory, load_trajectory


def trajectory_path(data_dir, pattern, sequence, method=""):
    return data_dir / pattern.format(sequence=sequence, method=method)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--data-dir", type=Path, required=True,
                        help="base directory for trajectory path templates")
    result.add_argument("--sequences", nargs="+", required=True,
                        help="sequence names substituted into path templates")
    result.add_argument("--methods", nargs="+", required=True,
                        help="method names substituted into the estimate template")
    result.add_argument("--labels", nargs="+",
                        help="display names, one per method (default: method names)")
    result.add_argument("--ref-pattern", default="{sequence}.txt",
                        help="reference path template (default: {sequence}.txt)")
    result.add_argument("--est-pattern", default="{sequence}_{method}.txt",
                        help="estimate path template (default: {sequence}_{method}.txt)")
    result.add_argument("--align", choices=("none", "origin", "se3", "sim3"),
                        default="none", help="alignment mode (default: none)")
    result.add_argument("--t-max-diff", type=float, default=0.01,
                        help="timestamp association tolerance in seconds")
    result.add_argument("--t-offset", type=float, default=0,
                        help="seconds added to all estimate timestamps")
    result.add_argument("--output", type=Path, default=Path("batch_ape_rmse.csv"),
                        help="CSV output path (default: batch_ape_rmse.csv; overwritten)")
    return result


def evaluate(args):
    """Evaluate every pair independently, retaining failures as empty CSV values."""
    labels = args.labels if args.labels is not None else args.methods
    rows = []
    for sequence in args.sequences:
        ref_path = trajectory_path(args.data_dir, args.ref_pattern, sequence)
        ref_error = None
        try:
            reference = load_trajectory(ref_path)
        except (EvoException, OSError, ValueError) as error:
            ref_error = f"{ref_path}: {error}"
        for method, label in zip(args.methods, labels):
            est_path = trajectory_path(args.data_dir, args.est_pattern, sequence, method)
            row = dict(sequence=sequence, method=method, label=label,
                       matched_poses="", rotation_rmse_deg="", translation_rmse_m="",
                       status="error", error="")
            try:
                if ref_error is not None:
                    raise ValueError(ref_error)
                estimate = load_trajectory(est_path)
                estimate.timestamps += args.t_offset
                align_trajectory(reference, estimate, args.align, args.t_max_diff)
                count, rotation, translation = ape_rmse(reference, estimate, args.t_max_diff)
                row.update(matched_poses=count, rotation_rmse_deg=rotation,
                           translation_rmse_m=translation, status="ok")
            except (EvoException, OSError, ValueError) as error:
                row["error"] = str(error) if ref_error else f"{est_path}: {error}"
            rows.append(row)
    return rows


def main(argv=None):
    arg_parser = parser()
    args = arg_parser.parse_args(argv)
    if args.labels is not None and len(args.labels) != len(args.methods):
        arg_parser.error("--labels must have one entry per method")
    if len(set(args.sequences)) != len(args.sequences) or len(set(args.methods)) != len(args.methods):
        arg_parser.error("sequence and method names must be unique")
    if (not np.isfinite(args.t_max_diff) or args.t_max_diff < 0
            or not np.isfinite(args.t_offset)):
        arg_parser.error("time tolerance must be finite and nonnegative; offset must be finite")
    try:
        trajectory_path(args.data_dir, args.ref_pattern, args.sequences[0])
        trajectory_path(args.data_dir, args.est_pattern, args.sequences[0], args.methods[0])
    except (KeyError, ValueError, IndexError, AttributeError) as error:
        arg_parser.error(f"invalid path template (use {{sequence}} and {{method}}): {error}")

    rows = evaluate(args)
    headers = ("Sequence", "Method", "Matched poses", "Rotation RMSE (deg)",
               "Translation RMSE (m)", "Status")
    display = [headers] + [
        (row["sequence"], row["label"], str(row["matched_poses"]),
         f'{row["rotation_rmse_deg"]:.6f}' if row["status"] == "ok" else "N/A",
         f'{row["translation_rmse_m"]:.6f}' if row["status"] == "ok" else "N/A",
         row["status"]) for row in rows]
    widths = [max(len(row[i]) for row in display) for i in range(len(headers))]
    print(f"APE RMSE (alignment: {args.align}, timestamp tolerance: {args.t_max_diff:g} s)")
    for row in display:
        print("  ".join(value.ljust(width) for value, width in zip(row, widths)))

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    except (OSError, ValueError) as error:
        arg_parser.error(str(error))
    print(f"Saved {args.output}")
    failures = [row for row in rows if row["status"] != "ok"]
    for row in failures:
        print(f'{row["sequence"]} / {row["label"]}: {row["error"]}', file=sys.stderr)
    print(f"Evaluated {len(rows)} combinations: {len(rows) - len(failures)} succeeded, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
