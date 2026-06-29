# Results

> Every cell is **measured** (real generation call / file stat). Quality = 12-task deterministic PROXY suite (not perplexity; perplexity needs llama.cpp — see scripts/quant_ladder.ps1). Latency is this-box-specific (AMD APU + LM Studio) — read the SHAPE, not the absolutes.

## Size ladder — fixed Q4_K_M, vary params (measured/exploratory)

| size (params) | quant | params | size | quality_acc | TTFT p50 (s) | decode tok/s |
|---|---|---|---|---|---|---|
| 0.5 | `q4_k_m` | 0.5B | 0.49 GB | 0.8333 | 2.0982 | 258.6±16.1 |
| 1.5 | `q4_k_m` | 1.5B | 1.12 GB | 1.0 | 2.1087 | 147.7±11.2 |
| 3.0 | `q4_k_m` | 3.0B | 2.10 GB | 0.9167 | 2.1492 | 89.4±1.0 |

- **Quality sweet spot:** `q4_k_m` **1.5B** at acc **1.0** (1.12 GB) — best quality-per-byte on this suite.
- **Quality vs params is NON-monotone:** 0.5B=0.8333, 1.5B=1.0, 3.0B=0.9167 — the coarse 12-task suite + small-model variance; bigger ≠ always better here.
- **Decode throughput falls with size (as expected):** 0.5B 259 → 3.0B 89 tok/s (2.89×). TTFT ~flat (overhead-bound at these sizes).

## Quant ladder — fixed 1.5B, vary bit-width (pre-registered H1–H3)

| bits | quant | params | size | quality_acc | TTFT p50 (s) | decode tok/s |
|---|---|---|---|---|---|---|
| 4-bit | `q4_k_m` | 1.5B | 1.12 GB | 1.0 | 2.1087 | 147.7±11.2 |

- **Quant ladder:** need both Q4 and Q8 accuracy (download Q8 — see scripts/quant_ladder.ps1).
