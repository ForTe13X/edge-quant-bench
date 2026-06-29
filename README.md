# edge-quant-bench

A small, **honest-by-construction** benchmark of on-device LLM efficiency: how quantization and model
size trade off **quality ↔ latency ↔ memory** on a real consumer machine (AMD APU), served through a
local OpenAI-compatible runtime (LM Studio). Built to demonstrate the eval discipline a quantization /
efficient-inference role needs — *measure everything, pre-register the prediction, report the negative.*

Stdlib-only Python (no deps to install). Every number is **measured** from a real generation call or a
file stat; nothing is assumed or hand-typed. Quality is a deterministic auto-scored proxy suite — and is
labelled a *proxy* everywhere (the gold metric, perplexity, needs llama.cpp; the script is provided).

## Two axes
| axis | what varies | what's fixed | status |
|---|---|---|---|
| **Size ladder** | params 0.5B / 1.5B / 3B | quant `Q4_K_M` | ✅ ran on this box |
| **Quant ladder** | bit-width Q3 / Q4 / Q5 / Q8 | model `Qwen2.5-1.5B` | ⏸ pre-registered; not fetchable offline here — `scripts/quant_ladder.ps1` |

## Results (size ladder — measured, real)
| params | quant | size | quality_acc | TTFT p50 | decode tok/s |
|---|---|---|---|---|---|
| 0.5B | Q4_K_M | 0.49 GB | 0.83 | 2.10 s | 259 ± 16 |
| **1.5B** | Q4_K_M | 1.12 GB | **1.00** | 2.11 s | 148 ± 11 |
| 3.0B | Q4_K_M | 2.10 GB | 0.92 | 2.15 s | 89 ± 1 |

- **Quality is non-monotone — 1.5B is the sweet spot** (12/12) and beats 3B (11/12) on this suite. Honest
  caveat: the 12-task suite is coarse (1 task = 8.3%), so this says "1.5B-Q4 is already enough for these
  tasks", not "1.5B > 3B in general".
- **Decode throughput falls ~2.9× from 0.5B→3B** (259→89 tok/s); **TTFT is ~flat** (~2.1 s, overhead-bound
  at these sizes) — so on this hardware the lever for interactive latency is *model size*, not prompt cost.
- Frontier plot: `frontier_size.svg`.

> Latency is specific to this AMD-APU box + LM Studio offload — read the **shape**, not the absolutes.

## Run it
```powershell
# size ladder (what ran here): imports the on-disk Q4 GGUFs into LM Studio and benchmarks each
pwsh scripts/run_size_ladder.ps1
# quant ladder (needs network/HF or llama.cpp): downloads Q3/Q4/Q5/Q8 of one model and benchmarks each
pwsh scripts/quant_ladder.ps1
# one model, ad-hoc:
python bench/runner.py --model qwen2.5-1.5b --tasks bench/tasks.json --out results/x.json
python bench/report.py results
```

## Layout
- `bench/runner.py` — streams a generation per task; measures TTFT, decode tok/s (long-gen probe), auto-scores quality.
- `bench/tasks.json` — 12 deterministic tasks (arith / extraction / format / JSON / short-fact).
- `bench/report.py` — ladder-aware tables + verdicts vs hypotheses + `frontier_*.svg`.
- `PREREG.md` — frozen hypotheses + decision rules (committed before the run).
- `results/` — per-model JSON + `meta.json` (measured sizes) + `REPORT.md`.
- `scripts/` — PowerShell orchestrators for each ladder.

## Honesty notes
- Quality = **proxy** (task accuracy), not perplexity. Perplexity ladder = `scripts/quant_ladder.ps1` (B), needs llama.cpp.
- The quant ladder did **not** run in this offline dev environment; its rows are absent, not invented.
- Absolute latency is hardware-specific; cross-rung **shape** is the result.
