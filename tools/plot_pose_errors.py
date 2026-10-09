#!/usr/bin/env python3
"""Plot XYZ/RPY components and total translation/rotation errors versus time."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from evo.core import metrics, sync
from tools.plot_traj import PLOT_STYLE, parser as trajectory_parser, run


def pose_errors(reference, estimate, max_diff=0.01):
    """Return matched time, XYZ, RPY, translation norm and rotation angle.

    RPY uses evo's fixed-axis sxyz convention (R = Rz(yaw) Ry(pitch) Rx(roll)).
    Errors are estimate minus reference, wrapped to [-180, 180) degrees.
    These are Euler-component differences, not Euler angles of a relative pose.
    """
    ref_sync, est_sync = sync.associate_trajectories(
        reference, estimate, max_diff=max_diff)
    xyz = est_sync.positions_xyz - ref_sync.positions_xyz
    rpy = (est_sync.get_orientations_euler("sxyz")
           - ref_sync.get_orientations_euler("sxyz"))
    rpy = np.rad2deg((rpy + np.pi) % (2 * np.pi) - np.pi)
    # All algorithms use the same ground truth time origin, including partial runs.
    time = ref_sync.timestamps - reference.timestamps[0]
    translation = metrics.APE(metrics.PoseRelation.translation_part)
    rotation = metrics.APE(metrics.PoseRelation.rotation_angle_deg)
    translation.process_data((ref_sync, est_sync))
    rotation.process_data((ref_sync, est_sync))
    return time, xyz, rpy, translation.error, rotation.error


def component_errors(reference, estimate, max_diff=0.01):
    """Return just the time and signed XYZ/wrapped RPY component errors."""
    return pose_errors(reference, estimate, max_diff)[:3]


def plot_errors(reference, estimates, labels, colors, args):
    import matplotlib.pyplot as plt

    series = [pose_errors(reference, estimate, args.t_max_diff)
              for estimate in estimates]
    for label, values in zip(labels, series):
        print(f"{label}: {len(values[0])} matched poses (tolerance {args.t_max_diff:g} s)")
    columns = min(args.legend_cols, len(estimates))
    legend_rows = (len(estimates) + columns - 1) // columns
    with plt.rc_context(PLOT_STYLE):
        fig = plt.figure(figsize=args.figsize, layout="constrained")
        grid = fig.add_gridspec(5, 2, height_ratios=[0.18 * legend_rows, 1, 1, 1, 1])
        legend_ax = fig.add_subplot(grid[0, :])
        legend_ax.set_axis_off()
        shared = None
        handles = []
        axes_by_column = [[], []]
        for row in range(4):
            for col in range(2):
                ax = fig.add_subplot(grid[row + 1, col], sharex=shared)
                axes_by_column[col].append(ax)
                if shared is None:
                    shared = ax
                ax.axhline(0, color="black", linestyle="--", linewidth=1,
                           alpha=0.65, zorder=1)
                for label, color, (time, xyz, rpy, translation, rotation) in zip(labels, colors, series):
                    if row == 3:
                        values = translation if col == 0 else rotation
                    else:
                        values = (xyz if col == 0 else rpy)[:, row]
                    line, = ax.plot(time, values, color=color,
                                    linewidth=1.8, label=label)
                    if row == 0 and col == 0:
                        handles.append(line)
                if row == 3:
                    ax.set_ylabel("Translation\nerror (m)" if col == 0
                                  else "Rotation\nerror (deg)")
                    ax.set_ylim(bottom=0)
                else:
                    ax.set_ylabel((r"$%s$ error (m)" % "xyz"[row]) if col == 0
                                  else f"{('Roll', 'Pitch', 'Yaw')[row]} error\n(deg)")
                ax.grid(True)
                ax.set_axisbelow(True)
                ax.margins(x=0.02, y=0.08)
                ax.tick_params(direction="out", width=0.8,
                               labelbottom=(row == 3))
                if row == 3:
                    ax.set_xlabel("Time (s)")
        for column_axes in axes_by_column:
            fig.align_ylabels(column_axes)
        legend_ax.legend(handles=handles, loc="center", ncol=columns,
                         frameon=False, handlelength=2, handletextpad=0.4,
                         columnspacing=0.9)
        if args.title:
            fig.suptitle(args.title)
    return fig


def parser():
    result = trajectory_parser()
    result.description = __doc__
    result.set_defaults(figsize=(12, 6.5), output=[Path("pose_errors.pdf")])
    for action in result._actions:
        if action.dest == "t_max_diff":
            action.help = "timestamp association tolerance for errors and alignment, seconds"
    return result


def main(argv=None):
    run(argv, parser, plot_errors)


if __name__ == "__main__":
    main()
