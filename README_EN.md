# edge-quant-bench

[中文](README.md)

A compact benchmark for local on-device LLM efficiency. It measures how model size and quantization affect quality, latency, and memory or disk footprint on a consumer AMD APU through a local OpenAI-compatible runtime such as LM Studio.

The benchmark is intentionally narrow and reproducible:

- Standard-library Python only.
- Every reported number comes from a real generation call or a file stat.
- Quality is a deterministic proxy task suite and is labeled as a proxy.
- Hypotheses and decision rules are recorded in [PREREG.md](PREREG.md) before measurement.

## Benchmark Axes

| Axis | What varies | What stays fixed | Status |
|---|---|---|---|
| Size ladder | 0.5B / 1.5B / 3B parameters | `Q4_K_M` quantization | Ran on this machine |
| Quant ladder | Q3 / Q4 / Q5 / Q8 bit-widths | `Qwen2.5-1.5B` | Pre-registered; script provided, not run in the offline setup |

## Size-Ladder Results

| Params | Quant | Size | Quality acc | TTFT p50 | Decode tok/s |
|---|---|---|---|---|---|
| 0.5B | Q4_K_M | 0.49 GB | 0.83 | 2.10 s | 259 +/- 16 |
| 1.5B | Q4_K_M | 1.12 GB | 1.00 | 2.11 s | 148 +/- 11 |
| 3.0B | Q4_K_M | 2.10 GB | 0.92 | 2.15 s | 89 +/- 1 |

Observed on this setup:

- 1.5B-Q4 reaches 12/12 on the proxy suite, while 3B reaches 11/12. Read this as "1.5B-Q4 is enough for these tasks", not as a general claim about model quality.
- Decode throughput drops about 2.9x from 0.5B to 3B, while TTFT stays close to 2.1 seconds.
- `frontier_size.svg` shows the size-ladder frontier.

Absolute latency is hardware- and runtime-specific. The useful result is the relative shape across rungs in the same environment.

## Run

```powershell
pwsh scripts/run_size_ladder.ps1
pwsh scripts/quant_ladder.ps1
python bench/runner.py --model qwen2.5-1.5b --tasks bench/tasks.json --out results/x.json
python bench/report.py results
```

## Layout

- `bench/runner.py`: streams generations, measures TTFT and decode throughput, and auto-scores quality.
- `bench/tasks.json`: 12 deterministic tasks covering arithmetic, extraction, formatting, JSON, and short factual answers.
- `bench/report.py`: builds tables, compares results with pre-registered hypotheses, and writes `frontier_*.svg`.
- `PREREG.md`: frozen hypotheses and decision rules.
- `results/`: per-model JSON, measured sizes in `meta.json`, and `REPORT.md`.
- `scripts/`: PowerShell orchestration for each ladder.

## Scope

- Quality is proxy task accuracy, not perplexity. The quant/perplexity path is provided through `scripts/quant_ladder.ps1` and requires llama.cpp.
- The quant ladder was not run in the offline development environment, so its result rows are absent.
- Cross-rung comparisons are meaningful within the same machine, runtime, model family, and task suite.
