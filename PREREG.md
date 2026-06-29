# Pre-registration — on-device quantization ladder

> Committed **before** the benchmark run, so the result is confirmatory, not post-hoc. Same discipline
> as a real eval: state the prediction + the decision rule + freeze the config, then report whatever
> happens (including a refuted prediction). The hypotheses below are frozen; results live in `REPORT.md`.

## Frozen config
- **Model (one base, several bit-widths)**: `Qwen2.5-1.5B-Instruct` (a non-thinking instruct model, so
  decoded tokens are the answer — avoids the qwen3 "thinking eats the budget" artifact).
- **Quant ladder**: `Q3_K_M`, `Q4_K_M`, `Q5_K_M`, `Q8_0` (Q8_0 ≈ near-lossless reference).
- **Serving**: LM Studio OpenAI-compatible endpoint `http://localhost:1234/v1`, one model loaded at a time.
- **Suite**: `bench/tasks.json` — 12 deterministic auto-scored tasks (arith / extraction / format / JSON /
  short-fact), `temperature=0`, `max_tokens=96`, `repeats=2`; decode tok/s from a separate long-gen probe.
- **Measured**: task-accuracy (quality PROXY), TTFT (streamed), decode tok/s, model file size (bytes).
- **Hardware**: this machine (AMD APU). Absolute latency is hardware-specific; the SHAPE across quants is the result.

## Capability axis
Bit-width (Q3 < Q4 < Q5 < Q8). Q8_0 is the near-lossless anchor; degradation is measured relative to it.

## Hypotheses + decision rules (frozen)
- **H1 — quality holds down to Q4, breaks at Q3.** Predict `acc(Q8) ≈ acc(Q5) ≈ acc(Q4)` (within the suite's
  ±1-task resolution ≈ 8.3%) and `acc(Q3) < acc(Q4)`.
  *Confirm* iff `acc(Q3) ≤ acc(Q4) − 1 task` **and** `|acc(Q8) − acc(Q4)| ≤ 1 task`. *Refute* otherwise.
- **H2 — size scales with bits; Q4 is the size sweet spot.** Predict file size strictly increases Q3<Q4<Q5<Q8
  and Q4 saves ≥40% vs Q8. (Descriptive measurement — report the exact %.)
- **H3 — decode throughput is roughly flat across quants on this box, NOT monotonically faster at lower bits.**
  Rationale: if the 1.5B fully fits in VRAM the decode is not purely weight-bandwidth-bound, so lower bits buy
  little speed; the real win of quantization here is *fitting on device*, not raw tok/s. *Confirm* iff the
  fastest and slowest quant's decode tok/s 95% CIs overlap; *refute* (→ "weight-bandwidth-bound regime") if
  Q3 decode is ≥1.3× Q8 with non-overlapping CIs.

## Honest limits stated up front
- The 12-task suite is COARSE (1 task = 8.3%); it can only catch gross quality cliffs, not fine degradation.
  The fine, standard metric is **perplexity** — needs `llama-perplexity` (see `scripts/quant_ladder.ps1`).
  Task-accuracy here is an honest *proxy*, labelled as such everywhere.
- Absolute tok/s and TTFT are specific to this AMD-APU box and LM Studio's offload settings; treat the
  cross-quant *shape* as the finding, not the absolute numbers.

## Run status (honest)
- The **size ladder** (sibling axis: fixed Q4, vary params 0.5B/1.5B/3B) RAN fully — see `REPORT.md`.
- The **quant ladder above** could NOT be fetched in this offline dev box (`lms get` HF artifact resolution
  failed for `Qwen/*` and `bartowski/*`; no fp16 base on disk and Q4 cannot be up-cast to Q8). The hypotheses
  stand pre-registered; run `scripts/quant_ladder.ps1` on a connected box (or with llama.cpp) to fill them.
  **No quant-ladder numbers are invented.**

→ **Results: `REPORT.md`.**
