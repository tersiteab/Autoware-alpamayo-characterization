# KV Cache and GPU Memory Analysis


## Measurement Scope

KV-cache size is measured per completed inference from the model cache itself. It is not estimated only from model configuration. The measurement point is after VLM generation and before the trajectory-diffusion expert consumes the cache.

The headline KV metric is `total_kv_mib`. Whole-inference CUDA memory pressure is reported separately as CUDA peak allocation/reservation and peak allocation delta. Those CUDA peak values include KV cache plus activations, temporary buffers, diffusion/expert working memory, and allocator behavior, so they must not be reported as KV-only memory.

## KV Cache Methodology

For each completed inference, the model cache object is walked recursively. The walker handles HuggingFace cache objects, dictionaries, lists, tuples, and objects exposing `key_cache` and `value_cache` attributes. Python object IDs are de-duplicated so the same tensor is not counted twice through multiple references.

For every unique cache tensor, memory is computed from the tensor itself as `numel * element_size`. The total is converted to MiB by dividing by 2^20. Because `element_size` comes from the tensor, the measurement reflects the dtype actually used by the cache in the run.

For non-navigation runs, `total_kv_mib` is the guided prompt cache only. For CFG/navigation runs, the unguided prompt cache is measured separately and added. The navigation branch is not simply a 2x cache multiplier because the unguided path strips the route span; the total depends on the guided cache plus the reduced unguided cache.

## CUDA Memory Methodology

CUDA allocator state is measured around the full inference. The start allocation/reservation is recorded at inference start. Peak memory stats are reset for that inference window. After trajectory publication, the end allocation/reservation and peak allocation/reservation are recorded.

The reported CUDA peak allocation delta is peak allocated memory during the inference minus allocated memory at inference start, converted to MiB. This is a memory-pressure metric for the full inference, not a KV-cache metric.

## Baseline Configuration

The baseline KV comparison uses the preserved Waymo and MCity KV reruns:

| Parameter | Waymo | MCity |
|---|---:|---:|
| Run | `results/kv/waymo_moving_diff2` | `results/kv/mcity_diff2` |
| Cameras / images per inference | 4 / 16 | 1 / 4 |
| `max_generation_length` | 64 | 64 |
| `num_diffusion_steps` | 2 | 2 |
| `num_trajectory_samples` | 1 | 1 |
| `precision_mode` | bf16 | bf16 |
| CFG / navigation | off | off |
| KV measurement point | after VLM generation, before diffusion | after VLM generation, before diffusion |

These baseline KV runs are diff2 operating-point runs. Default-parameter precision and K-sweep KV-related summaries are included separately where relevant.

## Baseline Results

| Metric | Waymo | MCity |
|---|---:|---:|
| Inferences | 43 | 137 |
| Prompt KV sequence length mean | 3083.7 | 845.2 |
| Total KV mean | 433.6 MiB | 118.9 MiB |
| Total KV max | 437.1 MiB | 125.3 MiB |
| Model parameter footprint | 20.64 GiB | 20.64 GiB |
| CUDA peak allocated mean | 21.63 GiB | 20.92 GiB |
| CUDA peak allocation delta mean | 972.5 MiB | 268.2 MiB |
| KV share of peak allocated | 1.96% | 0.55% |
| Generated token slots mean | 11.7 | 18.2 |
| Trajectory-start hit rate | 1.00 | 0.94 |
| GPU energy mean | 108.9 J/inf | 50.5 J/inf |

Waymo total KV is about 3.65x MCity because Waymo feeds four cameras and 16 images per inference, while MCity feeds one camera and 4 images. Visual prompt length dominates KV footprint more than the smaller differences in generated reasoning tokens.

The CUDA peak allocation delta follows the same direction as KV, but the cache is only a small fraction of whole-inference memory pressure. Most peak memory pressure comes from activations, temporary tensors, and diffusion/expert working memory.

## KV Versus Latency

KV capacity and latency are correlated mostly through a shared cause: generated token count. KV capacity grows approximately linearly with sequence length, while decode latency is dominated by repeatedly streaming decoder weights at batch size one. In the preserved KV-vs-latency diagnostic, KV read traffic is roughly 1.2% of decode read traffic when compared with the much larger per-token weight stream, so KV size is not the direct bottleneck by itself.

## Method Comparison

The older and corrected KV sizing formulas have the same per-token slope. The correction changes absolute offsets: non-navigation adds the expert append capacity, while navigation accounts for the route span removed from the unguided prompt. This means KV-vs-token slope conclusions are stable, but absolute provisioning numbers should use the corrected method.

## Alpamayo 1.5 Versus Alpamayo-2-Super

The real-replay comparison shows Alpamayo-2-Super uses about 1.78x the KV cache of Alpamayo 1.5 for similar Waymo prompt lengths. This matches the architectural depth ratio, because both use the same KV heads and head dimension but Alpamayo-2-Super has more decoder layers.

## Result Artifacts Copied Here

| File | Contents |
|---|---|
| `data/kv_memory_summary.csv` | Per-run Waymo/MCity KV and CUDA memory summary |
| `data/kv_memory_per_inference.csv` | Joined per-inference KV, CUDA memory, latency, energy, and FLOP rows |
| `data/waymo_moving_diff2_kv_memory_metrics.csv` | Raw Waymo baseline KV/memory log |
| `data/mcity_diff2_kv_memory_metrics.csv` | Raw MCity baseline KV/memory log |
| `data/kv_vs_latency.csv` | KV capacity/read-traffic versus latency diagnostic |
| `data/kv_method_compare.csv` | Previous versus corrected KV sizing method comparison |
| `data/kv_v15_vs_v2.csv` | Analytical/empirical Alpamayo 1.5 versus Alpamayo-2 KV comparison |
| `data/kv_v15_vs_v2_realrun.csv` | Real replay Alpamayo 1.5 versus Alpamayo-2 KV comparison |
| `data/precision_summary.csv` | Default-parameter precision summary including KV/CUDA memory fields |
| `data/camera_ablation_cam1_kv_memory_metrics.csv`, `data/camera_ablation_cam2_kv_memory_metrics.csv`, `data/camera_ablation_cam4_kv_memory_metrics.csv` | Raw same-dataset camera-count KV logs |
| `data/nav_a_straight_kv_memory_metrics.csv`, `data/nav_b_right_kv_memory_metrics.csv`, `data/nav_c_stop_kv_memory_metrics.csv` | Raw stamped-navigation KV logs for CFG/navigation cache behavior |
| `plot/kv_memory_bars.png` | Report figure for Waymo-vs-MCity KV and CUDA peak comparison |
| `plot/kv_memory_scatter.png` | Report figure for KV footprint versus token count |
| `plot/kv_memory_summary_table.png` | Compact visual KV summary table |
| `plot/kv_vs_latency.png` | KV capacity/read-traffic versus latency diagnostic plot |
| `plot/kv_method_compare.png` | Previous versus corrected method comparison plot |
| `plot/kv_per_inference_timeseries.png` | Per-inference KV time-series plot |
| `plot/kv_per_inference_twinx.png` | Per-inference KV/time-series plot with twin axis |
| `plot/kv_v15_vs_v2.png` | Alpamayo 1.5 versus Alpamayo-2 KV comparison plot |
| `plot/kv_v15_vs_v2_realrun.png` | Real replay Alpamayo 1.5 versus Alpamayo-2 KV comparison plot |
| `plot/kv_vs_tokens.png` | KV versus generated-token diagnostic plot, if present |


