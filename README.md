# slam_eval_tools

***Evaluation tools of odometry and SLAM based on core code of  [evo-v1.31.1](https://github.com/MichaelGrupp/evo/tree/86f52ade6da8cc4749c6170b1d2771ea1e0f1c66).***


## Quick Run

### Paper-style trajectory comparison

Plot TUM trajectories with height versus time on top and an equal-aspect XY
trajectory comparison below. Both panels share algorithm colors and a legend;
ground truth is drawn as a black dashed line. No zoom-in panels are added.

```bash
python3 tools/plot_traj.py garlio.tum dlio.tum fast_lio2.tum point_lio.tum \
  --ref ground_truth.tum \
  --labels GaRLIO DLIO FAST-LIO2 Point-LIO \
  --output comparison.pdf comparison.svg comparison.png
```

The script uses this repository's `evo` readers, trajectory validation and
alignment functions. By default it plots the complete trajectories in their
original coordinate frames. Time is relative to the first ground truth
timestamp, using each trajectory's own timestamps without resampling.

- `--align origin|se3|sim3`: optionally align each estimate to ground truth.
  Alignment is fitted using timestamp-associated poses and applied to the full
  estimate. `origin` uses the first matched pose; `sim3` also corrects scale.
- `--t-max-diff 0.01`: maximum timestamp difference for alignment, in seconds.
- `--t-offset 0.0`: offset added to all estimate timestamps before alignment and
  plotting, in seconds.
- `--colors '#2970ff' '#e74c3c' '#edae40' '#48ad2a'`: custom algorithm colors.
- `--figsize 10 7.5`, `--legend-cols 5`, `--title 'Sequence name'`: layout options.
- `--dpi 300`: raster export resolution. `--show` opens an interactive window.

Labels default to file stems. Output defaults to `trajectory_comparison.pdf`;
existing output files are overwritten. The default export works without a GUI.

### XYZ and RPY component errors

```bash
python3 tools/plot_pose_errors.py garlio.tum dlio.tum fast_lio2.tum point_lio.tum \
  --ref ground_truth.tum \
  --labels GaRLIO DLIO FAST-LIO2 Point-LIO \
  --output pose_errors.pdf pose_errors.png
```

The compact 4-by-2 layout shows X/Y/Z errors in the left column and roll/pitch/yaw
errors in the right column. The bottom row shows total translation error (m)
and rotation error (degrees), computed using evo's APE metrics. Translation is
the Euclidean position-error norm; rotation is the angle of the relative
rotation, rather than a norm of the RPY differences. The default figure size is
12 by 6.5 inches; `--figsize` adjusts the panel heights.
The bottom panels show per-pose APE curves. Y-axis labels are aligned within each column.
Algorithms share colors and a legend; the dashed zero line
represents agreement with ground truth. All subplots share a time axis relative
to the first ground truth timestamp. Each estimate is associated independently
with ground truth using evo's nearest-timestamp matching (`--t-max-diff`, default
0.01 seconds), without interpolation. Only matched poses contribute errors.

Position errors are signed estimate-minus-reference components in the common
world frame. RPY errors are differences of fixed-axis XYZ Euler angles (`sxyz`),
wrapped to [-180, 180) degrees. These are Euler-component differences, rather
than Euler angles of a relative rotation; near pitch +/-90 degrees, the Euler
representation is singular and component curves need careful interpretation.

The alignment, time offset, label, color and export options are the same as
`plot_traj.py`. Alignment defaults to `none`; use `--align origin|se3|sim3` if
needed. The default output is `pose_errors.pdf`. Edit the paths in
`tools/plot_pose_errors.sh` and run it with `sh` for a complete example.



## Related Work
[evo](https://github.com/MichaelGrupp/evo/tree/86f52ade6da8cc4749c6170b1d2771ea1e0f1c66): Python package for the evaluation of odometry and SLAM.
