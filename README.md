# edge-quant-bench

[English](README_EN.md)

一个面向本地端侧 LLM 的小型效率基准。它在消费级 AMD APU 上，通过 LM Studio 等本地 OpenAI 兼容运行时，测量模型尺寸与量化方式对质量、延迟和显存/磁盘占用的影响。

这个基准刻意保持窄而可复现：

- Python 标准库实现，无额外依赖。
- 报告中的数值来自真实生成调用或文件统计。
- 质量指标是确定性的代理任务集，并在文档中明确标为 proxy。
- 预测、假设和判定规则在 [PREREG.md](PREREG.md) 中预先记录。

## 基准轴

| 轴 | 变化项 | 固定项 | 状态 |
|---|---|---|---|
| 尺寸阶梯 | 0.5B / 1.5B / 3B 参数量 | `Q4_K_M` 量化 | 已在本机运行 |
| 量化阶梯 | Q3 / Q4 / Q5 / Q8 | `Qwen2.5-1.5B` | 已预注册，脚本已提供；离线环境未运行 |

## 尺寸阶梯结果

| 参数量 | 量化 | 文件大小 | quality_acc | TTFT p50 | decode tok/s |
|---|---|---|---|---|---|
| 0.5B | Q4_K_M | 0.49 GB | 0.83 | 2.10 s | 259 +/- 16 |
| 1.5B | Q4_K_M | 1.12 GB | 1.00 | 2.11 s | 148 +/- 11 |
| 3.0B | Q4_K_M | 2.10 GB | 0.92 | 2.15 s | 89 +/- 1 |

在这组机器与任务上观察到：

- 1.5B-Q4 在代理任务集上达到 12/12，3B 为 11/12。它说明 1.5B-Q4 已足够完成这些任务，不代表 1.5B 普遍优于 3B。
- 从 0.5B 到 3B，解码吞吐约下降 2.9 倍；TTFT 基本保持在 2.1 秒左右。
- `frontier_size.svg` 展示尺寸阶梯的效率前沿。

绝对延迟与硬件、运行时、模型格式有关。更有意义的是同一环境下各阶梯之间的相对形状。

## 运行

```powershell
# 已实测的尺寸阶梯
pwsh scripts/run_size_ladder.ps1

# 量化阶梯，需要网络或本地 Hugging Face 文件，并依赖 llama.cpp 支持
pwsh scripts/quant_ladder.ps1

# 单模型临时测试
python bench/runner.py --model qwen2.5-1.5b --tasks bench/tasks.json --out results/x.json
python bench/report.py results
```

## 目录

- `bench/runner.py`：流式生成、测量 TTFT 与解码吞吐、自动评分。
- `bench/tasks.json`：12 个确定性任务，覆盖算术、抽取、格式、JSON 与短事实问答。
- `bench/report.py`：生成表格、对照预注册假设、输出 `frontier_*.svg`。
- `PREREG.md`：运行前冻结的假设与判定规则。
- `results/`：每个模型的 JSON、`meta.json` 中的实测文件大小、以及 `REPORT.md`。
- `scripts/`：每个基准阶梯的 PowerShell 编排脚本。

## 边界

- 质量是小型代理任务集准确率，不是困惑度。困惑度/量化路径在 `scripts/quant_ladder.ps1` 中预留，需要 llama.cpp。
- 量化阶梯未在离线开发环境中运行，因此没有填入结果行。
- 跨阶梯比较应限制在同一机器、运行时、模型族与任务集内。
