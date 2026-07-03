# edge-quant-bench

A small benchmark for on-device LLM efficiency. It measures how model size and quantization affect quality, latency, and memory on a consumer AMD APU through a local OpenAI-compatible runtime, such as LM Studio.

The benchmark is intentionally narrow and reproducible:

- Standard-library Python only.
- Every reported number comes from a generation call or a file stat.
- Quality is a deterministic proxy task suite and is labeled as a proxy throughout.
- Hypotheses and decision rules are stored in [PREREG.md](PREREG.md) before measurement.

## Benchmark Axes

| Axis | What varies | What stays fixed | Status |
|---|---|---|---|
| Size ladder | 0.5B / 1.5B / 3B parameters | `Q4_K_M` quantization | Ran on this machine |
| Quant ladder | Q3 / Q4 / Q5 / Q8 bit-widths | `Qwen2.5-1.5B` | Pre-registered; script provided, not run in the offline setup |

## Results: Size Ladder

| Params | Quant | Size | Quality acc | TTFT p50 | Decode tok/s |
|---|---|---|---|---|---|
| 0.5B | Q4_K_M | 0.49 GB | 0.83 | 2.10 s | 259 +/- 16 |
| 1.5B | Q4_K_M | 1.12 GB | 1.00 | 2.11 s | 148 +/- 11 |
| 3.0B | Q4_K_M | 2.10 GB | 0.92 | 2.15 s | 89 +/- 1 |

Observed shape on this setup:

- The 1.5B model is the best point on the proxy suite: 12/12 correct, compared with 11/12 for 3B. This should be read as "1.5B-Q4 is enough for these tasks", not as a general claim that 1.5B outperforms 3B.
- Decode throughput drops about 2.9x from 0.5B to 3B, while TTFT stays near 2.1 s. For this hardware and serving stack, model size matters more than prompt overhead for interactive latency.
- The frontier plot is generated as `frontier_size.svg`.

Absolute latency is hardware- and runtime-specific. The useful result is the relative shape across rungs.

## Run It

```powershell
# Size ladder used for the measured result.
pwsh scripts/run_size_ladder.ps1

# Quant ladder. Requires network or local Hugging Face artifacts and llama.cpp support.
pwsh scripts/quant_ladder.ps1

# One ad-hoc model run.
python bench/runner.py --model qwen2.5-1.5b --tasks bench/tasks.json --out results/x.json
python bench/report.py results
```

## Repository Layout

- `bench/runner.py` streams each generation, measures TTFT and decode throughput, and auto-scores quality.
- `bench/tasks.json` contains 12 deterministic tasks covering arithmetic, extraction, formatting, JSON, and short factual answers.
- `bench/report.py` builds ladder-aware tables, compares results with the preregistered hypotheses, and writes `frontier_*.svg`.
- `PREREG.md` records hypotheses and decision rules before the run.
- `results/` stores per-model JSON, measured file sizes in `meta.json`, and `REPORT.md`.
- `scripts/` contains PowerShell orchestration for each ladder.

## Scope Notes

- Quality is task accuracy on a small proxy suite, not perplexity. The quant/perplexity path is provided through `scripts/quant_ladder.ps1` and requires llama.cpp.
- The quant ladder was not run in the offline development environment, so its result rows are absent.
- Cross-rung comparisons are meaningful within the same machine, runtime, model family, and benchmark task set.
