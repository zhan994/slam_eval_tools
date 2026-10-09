#!/usr/bin/env python3
"""Report rotation (degrees) and translation (m) APE RMSE for TUM trajectories."""

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from evo import EvoException
from evo.core import metrics, sync
from tools.plot_traj import align_trajectory, load_trajectory


def ape_rmse(reference, estimate, max_diff=0.01):
    """Return matched count, rotation RMSE (degrees), translation RMSE (m)."""
    ref_sync, est_sync = sync.associate_trajectories(
        reference, estimate, max_diff=max_diff)
    values = []
    for relation in (metrics.PoseRelation.rotation_angle_deg,
                     metrics.PoseRelation.translation_part):
        metric = metrics.APE(relation)
        metric.process_data((ref_sync, est_sync))
        values.append(metric.get_statistic(metrics.StatisticsType.rmse))
    return ref_sync.num_poses, *values


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("trajectories", type=Path, nargs="+",
                        help="estimated trajectories in TUM format")
    result.add_argument("--ref", type=Path, required=True,
                        help="ground truth trajectory in TUM format")
    result.add_argument("--labels", nargs="+",
                        help="one method name per estimate (default: file stems)")
    result.add_argument("--align", choices=("none", "origin", "se3", "sim3"),
                        default="none", help="alignment mode (default: none)")
    result.add_argument("--t-max-diff", type=float, default=0.01,
                        help="timestamp association tolerance, seconds (default: 0.01)")
    result.add_argument("--t-offset", type=float, default=0,
                        help="seconds added to all estimate timestamps")
    result.add_argument("--output", type=Path,
                        help="optional CSV output path (existing file is overwritten)")
    return result


def main(argv=None):
    arg_parser = parser()
    args = arg_parser.parse_args(argv)
    labels = args.labels if args.labels is not None else [
        path.stem for path in args.trajectories]
    if len(labels) != len(args.trajectories):
        arg_parser.error("--labels must have one entry per estimate")
    if (not np.isfinite(args.t_max_diff) or args.t_max_diff < 0
            or not np.isfinite(args.t_offset)):
        arg_parser.error("time tolerance must be finite and nonnegative; offset must be finite")

    try:
        reference = load_trajectory(args.ref)
        rows = []
        for path, label in zip(args.trajectories, labels):
            estimate = load_trajectory(path)
            estimate.timestamps += args.t_offset
            align_trajectory(reference, estimate, args.align, args.t_max_diff)
            rows.append((label, *ape_rmse(reference, estimate, args.t_max_diff)))

        headers = ("Method", "Matched poses", "Rotation RMSE (deg)", "Translation RMSE (m)")
        display_rows = [headers] + [
            (label, str(count), f"{rotation:.6f}", f"{translation:.6f}")
            for label, count, rotation, translation in rows]
        widths = [max(len(row[i]) for row in display_rows) for i in range(4)]
        print(f"APE RMSE (alignment: {args.align}, timestamp tolerance: {args.t_max_diff:g} s)")
        for row in display_rows:
            print("  ".join(value.ljust(width) for value, width in zip(row, widths)))

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("w", newline="", encoding="utf-8") as output:
                writer = csv.writer(output)
                writer.writerow(("method", "matched_poses", "rotation_rmse_deg", "translation_rmse_m"))
                writer.writerows(rows)
            print(f"Saved {args.output}")
    except (EvoException, OSError, ValueError) as error:
        arg_parser.error(str(error))


if __name__ == "__main__":
    main()
