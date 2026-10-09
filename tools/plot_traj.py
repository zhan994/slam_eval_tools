#!/usr/bin/env python3
"""Plot TUM trajectories as height versus time above an XY path comparison."""

import argparse
from pathlib import Path
import sys

# Support both direct execution and `python -m tools.plot_traj`, using local evo.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from evo import EvoException
from evo.core import lie_algebra, sync
from evo.tools.file_interface import read_tum_trajectory_file


COLORS = ("#2970ff", "#e74c3c", "#edae40", "#48ad2a",
          "#9467bd", "#17becf", "#8c564b", "#e377c2")
PLOT_STYLE = {
    "font.family": "DejaVu Sans", "font.size": 13,
    "axes.labelsize": 15, "legend.fontsize": 12,
    "axes.linewidth": 0.8, "grid.color": "#bdbdbd",
    "grid.linewidth": 0.7, "grid.alpha": 0.8,
    "figure.facecolor": "white", "axes.facecolor": "white",
}


def load_trajectory(path):
    """Use evo's reader and validation, with an additional finite-data check."""
    traj = read_tum_trajectory_file(path)
    if not all(np.isfinite(array).all() for array in
               (traj.timestamps, traj.positions_xyz, traj.orientations_quat_wxyz)):
        raise ValueError(f"{path}: trajectory contains NaN or infinite values")
    valid, details = traj.check()
    if not valid:
        raise ValueError(f"{path}: invalid trajectory: {details}")
    return traj


def align_trajectory(reference, estimate, mode, max_diff):
    """Fit on associated poses, then transform the complete estimate in place."""
    if mode == "none":
        return
    ref_sync, est_sync = sync.associate_trajectories(
        reference, estimate, max_diff=max_diff)
    if mode == "origin":
        transform = est_sync.align_origin(ref_sync)
    else:
        rotation, translation, scale = est_sync.align(
            ref_sync, correct_scale=(mode == "sim3"))
        estimate.scale(scale)
        transform = lie_algebra.se3(rotation, translation)
    estimate.transform(transform)


def plot_comparison(reference, estimates, labels, colors, figsize=(10, 7.5),
                    legend_cols=5, title=None):
    """Return a Matplotlib figure; trajectories are read without modification."""
    import matplotlib.pyplot as plt
    from matplotlib.transforms import Bbox

    with plt.rc_context(PLOT_STYLE):
        fig = plt.figure(figsize=figsize, layout="constrained")
        legend_rows = (len(estimates) + legend_cols) // legend_cols
        grid = fig.add_gridspec(3, 1, height_ratios=[0.18 * legend_rows, 0.65, 2])
        legend_ax = fig.add_subplot(grid[0])
        legend_ax.set_axis_off()
        height_ax = fig.add_subplot(grid[1])
        path_ax = fig.add_subplot(grid[2])
        t0 = reference.timestamps[0]

        # Reference stays visible above overlapping estimate curves.
        lines = [height_ax.plot(
            reference.timestamps - t0, reference.positions_xyz[:, 2],
            color="black", linestyle="--", linewidth=1.8,
            label="Ground Truth", zorder=5)[0]]
        path_ax.plot(reference.positions_xyz[:, 0], reference.positions_xyz[:, 1],
                     color="black", linestyle="--", linewidth=1.8, zorder=5)
        for traj, label, color in zip(estimates, labels, colors):
            lines.append(height_ax.plot(
                traj.timestamps - t0, traj.positions_xyz[:, 2],
                color=color, linewidth=2, label=label)[0])
            path_ax.plot(traj.positions_xyz[:, 0], traj.positions_xyz[:, 1],
                         color=color, linewidth=2)

        legend_ax.legend(handles=lines, loc="center", ncol=legend_cols,
                         frameon=False, handlelength=2, handletextpad=0.4,
                         columnspacing=0.9)
        height_ax.set(xlabel="Time (s)", ylabel=r"$z$ (m)")
        path_ax.set(xlabel=r"$x$ (m)", ylabel=r"$y$ (m)")
        # Keep tight XY limits. Let its equal-aspect box determine the width
        # of the height panel rather than padding the trajectory coordinates.
        path_ax.set_aspect("equal", adjustable="box")

        def aligned_position(ax, renderer):
            path_position = path_ax.get_position()
            original_position = ax.get_position(original=True)
            return Bbox.from_bounds(path_position.x0, original_position.y0,
                                    path_position.width, original_position.height)

        height_ax.set_axes_locator(aligned_position)
        legend_ax.set_axes_locator(aligned_position)
        for ax in (height_ax, path_ax):
            ax.set_axisbelow(True)
            ax.grid(True)
            ax.margins(x=0.02, y=0.08)
            ax.tick_params(direction="out", width=0.8)
        if title:
            fig.suptitle(title)
    return fig


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("trajectories", type=Path, nargs="+",
                        help="estimated trajectories in TUM format")
    result.add_argument("--ref", type=Path, required=True,
                        help="ground truth trajectory in TUM format")
    result.add_argument("--labels", nargs="+",
                        help="one legend label per estimate (default: file stems)")
    result.add_argument("--colors", nargs="+",
                        help="one Matplotlib color per estimate")
    result.add_argument("--align", choices=("none", "origin", "se3", "sim3"),
                        default="none", help="alignment mode (default: none)")
    result.add_argument("--t-max-diff", type=float, default=0.01,
                        help="timestamp association tolerance for alignment, seconds")
    result.add_argument("--t-offset", type=float, default=0,
                        help="seconds added to all estimate timestamps")
    result.add_argument("--figsize", type=float, nargs=2, default=(10, 7.5),
                        metavar=("WIDTH", "HEIGHT"), help="figure size in inches")
    result.add_argument("--legend-cols", type=int, default=5)
    result.add_argument("--title", help="optional figure title")
    result.add_argument("--output", type=Path, nargs="+",
                        default=[Path("trajectory_comparison.pdf")],
                        help="output paths, e.g. comparison.pdf comparison.png")
    result.add_argument("--dpi", type=int, default=300)
    result.add_argument("--show", action="store_true", help="show an interactive window")
    return result


def run(argv, parser_factory, figure_builder):
    """Shared CLI loading, alignment and export for custom trajectory figures."""
    arg_parser = parser_factory()
    args = arg_parser.parse_args(argv)
    count = len(args.trajectories)
    labels = args.labels if args.labels is not None else [p.stem for p in args.trajectories]
    if len(labels) != count or (args.colors is not None and len(args.colors) != count):
        arg_parser.error("--labels and --colors must have one entry per estimate")
    if (args.legend_cols < 1 or args.dpi < 1
            or not all(np.isfinite(v) and v > 0 for v in args.figsize)
            or not np.isfinite(args.t_max_diff) or args.t_max_diff < 0
            or not np.isfinite(args.t_offset)):
        arg_parser.error("invalid figure size, DPI, legend columns or time options")

    import matplotlib
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import is_color_like

    colors = args.colors if args.colors is not None else [
        COLORS[i] if i < len(COLORS) else plt.get_cmap("turbo")(
            (i - len(COLORS) + 1) / (count - len(COLORS) + 1))
        for i in range(count)]
    if not all(is_color_like(color) for color in colors):
        arg_parser.error("--colors contains an invalid Matplotlib color")
    fig = None
    try:
        reference = load_trajectory(args.ref)
        estimates = []
        for path in args.trajectories:
            estimate = load_trajectory(path)
            estimate.timestamps += args.t_offset
            align_trajectory(reference, estimate, args.align, args.t_max_diff)
            estimates.append(estimate)
        fig = figure_builder(reference, estimates, labels, colors, args)
        with plt.rc_context({"pdf.fonttype": 42, "ps.fonttype": 42,
                             "svg.fonttype": "none"}):
            for output in args.output:
                output.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(output, dpi=args.dpi, bbox_inches="tight", facecolor="white")
                print(f"Saved {output} (alignment: {args.align})")
        if args.show:
            plt.show()
    except (EvoException, OSError, ValueError) as error:
        arg_parser.error(str(error))
    finally:
        if fig is not None:
            plt.close(fig)


def main(argv=None):
    def build_figure(reference, estimates, labels, colors, args):
        return plot_comparison(reference, estimates, labels, colors, args.figsize,
                               min(args.legend_cols, len(estimates) + 1), args.title)

    run(argv, parser, build_figure)


if __name__ == "__main__":
    main()
