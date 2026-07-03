# edge-quant-bench · quant-ladder orchestrator (Windows PowerShell)
# Builds the REAL bit-width ladder for ONE base model and benchmarks each rung through LM Studio.
# Two ways to get the rungs — pick whichever your environment allows:
#   (A) lms get  — download prebuilt GGUF quants from Hugging Face (needs network + HF reachable)
#   (B) llama.cpp — quantize an fp16 base yourself (needs llama.cpp; the most "did-the-quantization" story)
#
# This dev box was OFFLINE for HF (lms could not resolve Qwen/* or bartowski/* artifacts), so the quant
# ladder was NOT run here — only the size ladder (scripts/run_size_ladder.ps1). Run this on a connected
# machine to fill PREREG H1–H3 with real numbers. Nothing here fabricates results.

$ErrorActionPreference = "Stop"
$PY   = "python"   # any python3 works (stdlib only)
$LMS  = "$env:USERPROFILE\.lmstudio\bin\lms.exe"
$ROOT = Split-Path $PSScriptRoot -Parent
$REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"        # or bartowski/Qwen2.5-1.5B-Instruct-GGUF
$QUANTS = @("q3_k_m","q4_k_m","q5_k_m","q8_0")
Set-Location $ROOT

# ---- (A) download + benchmark each rung ----------------------------------------------------------
foreach ($q in $QUANTS) {
    Write-Host "==== $q ====" -ForegroundColor Cyan
    & $LMS get "$REPO@$q" --gguf -y          # downloads if missing; no-op if present
    $model = "qwen2.5-1.5b-instruct"          # LM Studio JIT-loads by id on first API call
    & $PY "bench\runner.py" --model "$model" --tasks "bench\tasks.json" `
          --out "results\qwen2.5-1.5b-$q.json" --repeats 2 --max-tokens 96
    # record the real file size into results\meta.json yourself (file stat of the downloaded .gguf),
    # then add this rung to ladders.quant in results\meta.json.
}
& $PY "bench\report.py" "results"
Write-Host "Done -> REPORT.md (quant ladder section now populated)"

# ---- (B) llama.cpp alternative (the strongest 'I did PTQ' story) ---------------------------------
# winget install llama.cpp        # or download a release from github.com/ggml-org/llama.cpp
# # get an fp16 GGUF base once (e.g. convert from HF safetensors, or download *-f16.gguf), then:
# foreach ($q in 'Q3_K_M','Q4_K_M','Q5_K_M','Q8_0') {
#     llama-quantize .\Qwen2.5-1.5B-Instruct-f16.gguf .\qwen2.5-1.5b-$q.gguf $q
# }
# # gold quality metric = perplexity on a held-out text (finer than the task suite):
# foreach ($q in 'Q3_K_M','Q4_K_M','Q5_K_M','Q8_0') {
#     llama-perplexity -m .\qwen2.5-1.5b-$q.gguf -f .\wiki.test.raw 2>&1 | Tee-Object "results\ppl-$q.txt"
# }
