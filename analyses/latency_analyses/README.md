# Latency Analysis

## Measurement Scope

Latency is measured per completed Alpamayo inference. The primary latency value is model-window duration, not bag frame interval and not full callback time.

For inference `i`, the reported model duration is:

`T_i = end_wall_s_i - model_start_wall_s_i`

The broader `duration_s` field includes input preparation before the model window. Stage latency is reported only for runs with NVTX/stage instrumentation.

Because Alpamayo runs one inference at a time on one GPU, completed inference count can be much lower than camera-frame count. This is expected when model latency exceeds the trigger period: the active-inference guard prevents overlapping model executions. It should not be interpreted as camera frame loss without checking camera-validation artifacts.

## Baseline Throughput and Freshness

Baseline latency is compared across Waymo and MCity using `inference_metrics.csv` rows. Sustained throughput is computed as completed inferences and published trajectories over replay span. Because the bags are replayed slower than real time, both wall-clock FPS and simulated-time FPS are reported.

Input freshness is measured by joining camera receipts to inference rows by inference index. Two freshness quantities are used:

| Quantity | Meaning |
|---|---|
| `odom_minus_camera_stamp` | Age of the selected camera history relative to the odometry/inference stamp |
| `camera_staleness` | Whether newer camera frames existed but were not selected |

The report baseline found that the node selected the newest available frames: camera staleness was zero in the baseline reruns.

## Latency Levers

The report evaluates latency with one parameter varied at a time and all other model/runtime parameters fixed. Current default-parameter analyses keep `precision_mode=bf16`, `max_generation_length=64`, `num_trajectory_samples=1`, and `num_diffusion_steps=5`, unless that parameter is the sweep variable.

Latency-relevant studies copied here:

| Study | Varied parameter | Main interpretation |
|---|---|---|
| Baseline dataset comparison | none | Waymo is heavier because it uses four cameras / 16 images per inference; MCity uses one camera / 4 images |
| Token cap, Waymo | `max_generation_length={16,32,64}` | Cap is mostly inert on the clean Waymo segment because realized reasoning tokens stay well below the cap |
| Token cap, MCity | `max_generation_length={16,32,64}` | MCity reasoning length responds to the cap, but latency/energy are still affected by scene mix |
| Diffusion steps | `num_diffusion_steps={2,5,10}` | MCity latency grows clearly with steps; Waymo is partly masked by decode/prompt variance |
| Numeric precision | `precision_mode={bf16,fp16}` | FP16 is slower and higher-energy than BF16 on this Thor stack |
| Trajectory samples | `num_trajectory_samples={1,2,4}` | K is the most expensive latency lever measured; latency and energy rise sharply |
| Camera count | 1, 2, 4 Waymo cameras | Same-dataset camera count strongly changes latency, energy, and accuracy |
| Navigation text | stamped nav prompt A/B/C | CFG-nav dual pass increases latency versus non-nav baseline |

## Stage Breakdown

For stage attribution, the node uses NVTX stage ranges and an Nsight Systems capture is summarized by stage. Kernel-name aggregation alone is insufficient because stages share GEMM kernels, so the stage split relies on NVTX ranges.

The report treats end-to-end model latency as a serial sum of:

| Stage | Role | Reported finding |
|---|---|---|
| `vision_encode` | Image feature extraction | Smallest stage, about 5.6% of GPU time in the staged capture |
| `prefill` | Full prompt VLM prefill | Compute-dense, about 12.8% |
| `reason_decode` | Autoregressive reasoning tokens | Dominant latency driver, about 71.4%, memory-bandwidth-bound |
| `traj_diffusion_expert` | Trajectory diffusion expert | About 10.2%, scales with diffusion steps and K |

This stage result explains the sweep behavior: decode length is the strongest per-frame latency driver, diffusion steps and K scale the expert loop, and camera count changes prompt/vision/prefill workload.

## Reporting Guidance

For latency tables, report:

| Metric | Source / interpretation |
|---|---|
| `model_duration_ms_mean` | Mean model-window latency per completed inference |
| `model_duration_ms_std` | Run-to-run/per-inference variability within the run |
| `n_inferences` | Completed model calls; not expected to equal camera frame count |
| `wall_inference_fps` | Completed inferences per wall-clock second |
| `sim_inference_fps` | Completed inferences per simulated replay second |
| `reason_tokens_mean` | Scene/reasoning complexity proxy |
| `camera_staleness_max_s` | Whether newer frames existed but were not selected |

When explaining low inference counts, cite the serial active-inference guard and warmup/history requirement before claiming frame drops. Camera drops should be supported by `camera_validation.txt` or receipt-derived freshness metrics.

## Result Artifacts Copied Here

| File | Contents |
|---|---|
| `data/characterization_dataset_baselines.csv` | Waymo/MCity baseline latency, tokens, inference count, energy, and accuracy where available |
| `data/characterization_throughput_freshness.csv` | Per-run wall/sim FPS, inference intervals, model duration, camera counts, and freshness aggregates |
| `data/characterization_input_age_per_inference.csv` | Per-inference camera freshness rows |
| `data/token_cap_latency_power_energy_clean_only_summary.csv` | Clean Waymo token-cap latency/power/energy summary |
| `data/token_cap_mcity_summary.csv` | MCity token-cap latency/power/energy summary |
| `data/diffusion_step_summary.csv` | Waymo+MCity diffusion-step latency/power/energy/accuracy summary |
| `data/precision_summary.csv` | Corrected default-parameter BF16/FP16 latency/power/energy/memory/accuracy summary |
| `data/trajectory_sample_summary.csv` | Corrected default-parameter K-sweep latency/power/energy summary |
| `data/camera_ablation_summary.csv` | Same-dataset Waymo camera-count latency/power/energy/accuracy summary |
| `data/stage_summary.csv` | NVTX stage-level GPU-time split and stage interpretation |
| `data/stage_kernels.csv` | Dominant kernels by stage from the staged Nsight capture |
| `data/per_frame_timeseries.csv` | Per-frame stage timing series |
| `data/per_frame_enriched.csv` | Per-frame profile rows enriched with token/FLOP timing context |
| `data/kv_vs_latency.csv` | KV/memory-vs-latency diagnostic rows |
| `plot/latency_energy_bars.png` | Baseline Waymo-vs-MCity model latency and GPU energy |
| `plot/throughput_tokens_bars.png` | Baseline throughput and reasoning-token comparison |
| `plot/latency_vs_complexity.png` | Per-inference latency vs reasoning-token count |
| `plot/latency_vs_complexity_perrerun.png` | Per-rerun latency-vs-complexity diagnostic |
| `plot/token_cap_latency_energy.png` | Waymo token-cap latency/power/energy plot |
| `plot/token_cap_mcity_sweep.png` | MCity token-cap latency/power/energy plot |
| `plot/diffusion_step_sweep.png` | Dataset-matched diffusion-step latency/power/energy plot |
| `plot/precision_bars.png` | BF16/FP16 latency/power/energy/accuracy plot |
| `plot/trajectory_sample_sweep.png` | K=1/2/4 latency/power/energy plot |
| `plot/per_frame_timeseries.png` | Stage timing time series from the staged capture |
| `plot/camera_ablation_sweep.png` | Camera-count latency/power/energy/accuracy plot |
| `plot/nav_abc_bars.png` | Stamped navigation A/B/C latency/power/energy/accuracy plot |
| `plot/kv_vs_latency.png` | KV/memory-vs-latency diagnostic plot |

