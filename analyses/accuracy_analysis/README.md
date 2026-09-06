# Accuracy Analysis

This folder consolidates the trajectory-accuracy artifacts for Alpamayo in
Autoware. The layout mirrors the other characterization bundles:

- `data/`: copied CSV outputs and compact derived summaries.
- `plot/`: copied report-ready PNG plots.
- `README.md`: methodology, result summary, and artifact map.

## Scope

Accuracy is evaluated only for the Waymo runs because those are the runs with a
usable future ego-motion target and Waymo GT actor boxes. MCity remains present
in some cross-sweep CSVs for latency, power, and energy, but its trajectory
accuracy columns are intentionally `N/A` in this characterization.

The ego ADE/FDE numbers here are a replayed-odometry sanity check, not the
official Waymo planning benchmark.

Unless a sweep explicitly varies a parameter, the default characterization
settings are held fixed:

| Parameter | Default |
| --- | --- |
| `precision_mode` | `bf16` |
| `max_generation_length` | `64` |
| `num_trajectory_samples` | `1` |
| `num_diffusion_steps` | `5` |
| Waymo replay rate | `0.1x` |
| MCity replay rate | `0.5x` |

The standalone baseline in `data/moving_diff2_accuracy_summary.csv` is the
named `moving_diff2` run, so its operating point uses `num_diffusion_steps=2`.

## Ego ADE/FDE Methodology

The evaluator groups the predicted trajectory topic output by prediction, orders
points by trajectory point index, and compares the predicted future ego path with
the replayed future odometry timeline.

For prediction `i`, the evaluation start is:

```text
prediction_start_time = prediction_stamp + stamp_offset_s
```

For each predicted point, the evaluator:

1. Uses the point's `time_from_start` to find the target future timestamp.
2. Interpolates the replayed odometry at that timestamp.
3. Transforms the future odometry pose into the local frame at the prediction
   start.
4. Computes 2D Euclidean displacement error between predicted and replayed
   future ego positions.

Formal per-prediction definitions:

```text
e_{i,k} = ||p_{i,k} - g_{i,k}||_2
ADE_i = (1 / K_i) * sum_{k=1..K_i} e_{i,k}
FDE_i = e_{i,K_i}
```

where `p_{i,k}` is the predicted 2D point, `g_{i,k}` is the aligned replayed
future-ego point, and `K_i` is the number of matched points for prediction `i`.
Reported ADE/FDE are arithmetic means across valid predictions unless a table
explicitly says median.

## GT Actor Interaction Methodology

The GT actor check is separate from ADE/FDE. It loads Waymo GT actor boxes and
checks the planned ego footprint against nearby annotated actors.

Configuration:

| Setting | Value |
| --- | --- |
| Planned ego footprint | oriented rectangle, `4.8 m x 2.1 m` |
| GT classes | vehicle, pedestrian, cyclist |
| `max_range_m` | `120` |
| `gt_tolerance_s` | `0.06` |
| `near_miss_m` | `1.0` |
| `actor_prefilter_m` | `80.0` |

At each aligned timestamp, the evaluator represents the planned ego and GT actor
boxes as oriented polygons. Collision is tested with separating-axis polygon
intersection. Clearance is measured with polygon-edge distance. This check
reports collision counts, near misses, and minimum clearance; it does not compute
ADE/FDE.

## Baseline Result

Waymo `moving_diff2` ego-odometry sanity accuracy:

| Metric | Value |
| --- | ---: |
| Predictions / inferences | `46 / 46` |
| Mean ADE / FDE | `0.107 m / 0.194 m` |
| Median ADE / FDE | `0.031 m / 0.074 m` |
| Std ADE / FDE | `0.204 m / 0.290 m` |

Primary files:

- `data/moving_diff2_accuracy_summary.csv`
- `data/moving_diff2_waymo_eval.csv`
- `data/moving_diff2_waymo_eval_aligned_points.csv`
- `plot/accuracy_per_prediction.png`
- `plot/accuracy_bars.png`
- `plot/moving_diff2_accuracy_table.png`

GT actor provenance note: the report text describes a clean baseline GT-actor
segment with zero collisions and nearest clearance around `0.68 m`. The copied
root-level CSV currently summarizes to `25` prediction rows, `4` predictions
with collisions, `90` total collision events, and minimum clearance `0.0 m`.
That means `data/waymo_gt_actor_eval.csv` should be treated as a mixed or
historical GT-actor artifact unless it is regenerated for the exact clean
baseline slice.

GT actor files:

- `data/waymo_gt_actor_eval.csv`
- `data/waymo_gt_actor_collisions.csv`
- `data/gt_actor_interaction_summary.csv`
- `data/waymo_gt_actor_eval_summary.csv`
- `data/gt_actor_interaction_summary.csv`

## Sweep Results

### Token Cap

Clean-only Waymo token-cap sweep. Only `max_generation_length` changes; diffusion
steps, cameras, precision, K, replay segment, and replay rate are fixed.

| Cap | n | Mean ADE | Mean FDE |
| ---: | ---: | ---: | ---: |
| `16` | `12` | `0.031 m` | `0.073 m` |
| `32` | `12` | `0.030 m` | `0.066 m` |
| `64` | `12` | `0.028 m` | `0.063 m` |

Interpretation: token cap is effectively inert on these clips because actual
generated reasoning length stays far below the cap.

Files:

- `data/token_cap_accuracy_clean_only_summary.csv`
- `data/tok16_waymo_eval.csv`
- `data/tok32_waymo_eval.csv`
- `data/tok64_waymo_eval.csv`
- `plot/token_cap_accuracy.png`

### Diffusion Steps

Dataset-matched diffusion-step sweep. Only `num_diffusion_steps` changes within
each dataset; Waymo has ADE/FDE, MCity accuracy is `N/A`.

| Dataset | Steps | n | Mean ADE | Mean FDE |
| --- | ---: | ---: | ---: | ---: |
| Waymo | `2` | `45` | `0.109 m` | `0.197 m` |
| Waymo | `5` | `46` | `0.117 m` | `0.188 m` |
| Waymo | `10` | `43` | `0.104 m` | `0.201 m` |
| MCity | `2` | `200` | `N/A` | `N/A` |
| MCity | `5` | `156` | `N/A` | `N/A` |
| MCity | `10` | `131` | `N/A` | `N/A` |

Interpretation: Waymo ego ADE/FDE is flat within noise across diffusion steps at
this operating point.

Files:

- `data/diffusion_step_summary.csv`
- `data/waymo_diff2_waymo_eval.csv`
- `data/waymo_diff5_waymo_eval.csv`
- `data/waymo_diff10_waymo_eval.csv`
- `plot/diffusion_step_sweep.png`

### Precision

Default-parameter precision replay. Only `precision_mode` changes. FP8/INT8 did
not complete end-to-end in this setup.

| Dataset | Precision | n | Mean ADE | Mean FDE |
| --- | --- | ---: | ---: | ---: |
| Waymo | `bf16` | `41` | `0.128 m` | `0.204 m` |
| Waymo | `fp16` | `23` | `0.130 m` | `0.210 m` |
| MCity | `bf16` | `163` | `N/A` | `N/A` |
| MCity | `fp16` | `73` | `N/A` | `N/A` |

Interpretation: FP16 does not improve trajectory accuracy and is worse for
runtime/energy in the measured Thor stack.

Files:

- `data/precision_summary.csv`
- `data/precision_waymo_bf16_eval.csv`
- `data/precision_waymo_fp16_eval.csv`
- `plot/precision_bars.png`

### Trajectory Samples

Default-parameter K sweep. Only `num_trajectory_samples` changes. The Autoware
trajectory topic publishes sample 0, so these ADE/FDE numbers are sample-0
accuracy rather than best-of-K accuracy.

| Dataset | K | n | Mean ADE0 | Mean FDE0 |
| --- | ---: | ---: | ---: | ---: |
| Waymo | `1` | `53` | `0.103 m` | `0.184 m` |
| Waymo | `2` | `35` | `0.138 m` | `0.181 m` |
| Waymo | `4` | `21` | `0.181 m` | `0.259 m` |
| MCity | `1` | `185` | `N/A` | `N/A` |
| MCity | `2` | `55` | `N/A` | `N/A` |
| MCity | `4` | `89` | `N/A` | `N/A` |

Interpretation: publishing more samples does not improve the published sample-0
path. Any accuracy benefit requires selecting among the generated samples.

Files:

- `data/trajectory_sample_summary.csv`
- `data/traj_samples_waymo_k1_eval.csv`
- `data/traj_samples_waymo_k2_eval.csv`
- `data/traj_samples_waymo_k4_eval.csv`
- `plot/trajectory_sample_sweep.png`

### Best Of K

Best-of-K uses the opt-in all-samples logger and scores every returned sample
against the same replayed-odometry target. This answers whether the sample set
contains a better trajectory, not whether sample 0 improved.

| K | n | ADE0 | minADE_K | FDE0 | minFDE_K |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `1` | `53` | `0.115 m` | `0.115 m` | `0.234 m` | `0.234 m` |
| `2` | `35` | `0.145 m` | `0.085 m` | `0.191 m` | `0.120 m` |
| `4` | `21` | `0.199 m` | `0.104 m` | `0.310 m` | `0.159 m` |

Interpretation: the generated sample set contains substantially better
trajectories than the published sample 0, but the node needs a selector/ranker or
publisher support to realize that gain online.

Files:

- `data/best_of_k_summary.csv`
- `data/best_of_k_waymo_k1_eval.csv`
- `data/best_of_k_waymo_k2_eval.csv`
- `data/best_of_k_waymo_k4_eval.csv`
- `plot/best_of_k_bars.png`

### Camera Ablation

Waymo camera-count ablation. Only the camera set changes; all other knobs are
held fixed.

| Cameras | n | Mean ADE | Mean FDE |
| ---: | ---: | ---: | ---: |
| `1` | `88` | `0.333 m` | `0.905 m` |
| `2` | `79` | `0.151 m` | `0.429 m` |
| `4` | `53` | `0.092 m` | `0.152 m` |

Interpretation: camera count is the strongest measured accuracy lever. Going
from 1 to 4 cameras cuts ADE by about `3.6x` and FDE by about `6x`, at higher
latency, energy, and KV-cache cost.

Files:

- `data/camera_ablation_summary.csv`
- `data/camera_ablation_cam1_eval.csv`
- `data/camera_ablation_cam2_eval.csv`
- `data/camera_ablation_cam4_eval.csv`
- `plot/camera_ablation_sweep.png`

### Stamped Navigation Text

Stamped-nav A/B/C Waymo runs. The runs use the same settings and differ only in
the stamped navigation text published on `/alpamayo/nav_input`.

| Condition | Nav text | n | Mean ADE | Mean FDE |
| --- | --- | ---: | ---: | ---: |
| A | `drive straight` | `29` | `0.104 m` | `0.151 m` |
| B | `turn right` | `33` | `0.106 m` | `0.161 m` |
| C | `stop, red light ahead` | `34` | `0.082 m` | `0.139 m` |

Interpretation: on this scene-constrained segment, stamped nav text barely moves
the trajectory compared with the geometric/image context. The guided navigation
path still costs latency and energy because it uses the CFG-style dual pass.

Files:

- `data/nav_abc_accuracy_summary.csv`
- `data/nav_a_straight_eval.csv`
- `data/nav_b_right_eval.csv`
- `data/nav_c_stop_eval.csv`
- `plot/nav_abc_bars.png`

## Reporting Guidance

When reporting these numbers, state:

- the dataset and replay rate,
- the varied parameter and fixed defaults,
- the number of valid predictions,
- mean ADE/FDE in meters, with median or standard deviation when space allows,
- that ADE/FDE is measured against replayed future ego odometry and is not the
  official Waymo planning benchmark,
- that GT-actor collision/clearance is a separate interaction metric and not an
  ADE/FDE metric.
