# Power and Energy Analysis

## Measurement Scope

Power and energy are measured per completed Alpamayo inference. The primary reported metric is GPU-only energy, using the Jetson INA GPU rail `vdd_gpu_w`. 

The analysis is per inference.

## Power Sampling

The platform power sampler records instantaneous Jetson INA rail power with wall-clock timestamps at 200 Hz. Rails are resolved by sensor/rail name rather than by a fixed hwmon index, so the columns remain meaningful even if Linux enumerates sensors differently.

Important rails:

| Column | Meaning | Reporting use |
|---|---|---|
| `vdd_gpu_w` | GPU rail power | Primary GPU-only power and energy result |
| `total_w` | Total module/board input power | Secondary total-system context |
| `vdd_cpu_soc_mss_w` | CPU/SOC/MSS rail power | Secondary rail breakdown |
| `vin_sys_5v0_w` | 5 V system rail power | Secondary rail breakdown |
| `module_sum_w` | Sum of INA module rails | Secondary module-level context |



## Energy Computation

For each inference, the GPU energy is the integral of GPU rail power over the model window. I.e., GPU energy per inference equals the area under `vdd_gpu_w` from model start to model end. Average active GPU power is computed by dividing that GPU energy by the model-window duration. 


## Peak GPU Power

Peak GPU power is computed by taking the maximum `vdd_gpu_w` sample inside each inference model window, then summarizing those per-inference peaks across the run.

Peak power is sensitive to sampler cadence. Peaks should only be compared across runs that used the same sampling rate, and the sampling cadence should be reported with the plot or table.

## Dataset and Sweep Interpretation

Waymo and MCity are not identical workloads. Waymo uses four cameras and more image history per inference, while MCity uses one camera. Dataset comparisons therefore reflect both dataset/workload differences and camera-count differences unless a same-dataset camera ablation is used.

For parameter sweeps, only the parameter under test should vary. Current default-parameter analyses use default `precision_mode=bf16`, `max_generation_length=64`, `num_trajectory_samples=1`, and `num_diffusion_steps=5` unless that parameter is the sweep variable.

## Result Artifacts Copied Here

The copied CSVs and plots in this folder are report-ready summaries. Raw per-run files remain in the original `results/` tree as `power_samples.csv` and `energy_per_inference.csv`.

| File | Contents |
|---|---|
| `characterization_dataset_baselines.csv` | Baseline Waymo/MCity latency, inference count, GPU power, GPU energy, total energy, tokens, and accuracy where available |
| `dataset_power_energy_summary.csv` | Earlier compact Waymo-vs-MCity power/energy comparison |
| `characterization_peak_power.csv` | Per-run rail peak/active/overall power summary |
| `token_cap_latency_power_energy_clean_only_summary.csv` | Clean Waymo token-cap latency/power/energy summary |
| `token_cap_mcity_summary.csv` | MCity token-cap latency/power/energy summary |
| `diffusion_step_summary.csv` | Dataset-matched diffusion-step latency/power/energy summary |
| `precision_summary.csv` | Corrected default-parameter precision latency/power/energy/memory/accuracy summary |
| `trajectory_sample_summary.csv` | Corrected default-parameter trajectory-sample-count latency/power/energy summary |
| `camera_ablation_summary.csv` | Same-dataset camera-count latency/power/energy/accuracy summary |
| `best_of_k_summary.csv` | Best-of-K accuracy summary; energy for K runs is in `trajectory_sample_summary.csv` |
| `characterization_waymo_mcity_latency_energy_bars.png` | Waymo-vs-MCity latency and GPU energy plot |
| `characterization_waymo_mcity_peak_gpu_power_bars.png` | Waymo-vs-MCity peak GPU power plot |
| `mcity_waymo_gpu_power_energy_bar.png` | Earlier MCity-vs-Waymo GPU power/energy bar plot |
| `mcity_gpu_energy_time_power.png` | MCity per-inference GPU energy/time/power plot |
| `mcity_energy_by_rail.png` | MCity rail-energy breakdown |
| `token_cap_latency_power_energy_bars_clean_only.png` | Clean Waymo token-cap power/energy bars |
| `token_cap_mcity_sweep.png` | MCity token-cap sweep plot |
| `diffusion_step_sweep.png` | Dataset-matched diffusion-step plot |
| `precision_latency_power_accuracy_bars.png` | Corrected precision latency/power/energy/accuracy plot |
| `trajectory_sample_sweep.png` | Corrected trajectory-sample-count plot |
| `camera_ablation_sweep.png` | Same-dataset camera-count ablation plot |
| `nav_abc_bars.png` | Navigation text A/B/C plot with latency/power/energy/accuracy |

