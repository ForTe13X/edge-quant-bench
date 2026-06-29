# edge-quant-bench · size-ladder orchestrator (Windows PowerShell)
# The axis that RAN on this box: fixed quant (Q4_K_M), vary params (0.5B / 1.5B / 3B).
# Answers "how small a model still works on-device, and what it costs in latency/size".
# Reproduces results/*.json + REPORT.md exactly.

$ErrorActionPreference = "Stop"
$PY   = "E:\Documents\Dev\June\10th\SPI\.venv\Scripts\python.exe"
$LMS  = "$env:USERPROFILE\.lmstudio\bin\lms.exe"
$ROOT = Split-Path $PSScriptRoot -Parent
Set-Location $ROOT

# on-disk Q4 GGUFs (already present from sibling projects). -c COPIES (keeps the originals in place).
$models = @(
  @{ id="qwen2.5-0.5b"; path="E:\Documents\Dev\June\22nd\release\xiaoyudao-builtinAI-win-test\models\qwen2.5-0.5b-instruct-q4_k_m.gguf" },
  @{ id="qwen2.5-1.5b"; path="E:\Documents\Dev\June\26th\game\models\qwen2.5-1.5b-instruct-q4_k_m.gguf" },
  @{ id="qwen2.5-3b";   path="E:\Documents\Dev\June\26th\game\models\qwen2.5-3b-instruct-q4_k_m.gguf" }
)
foreach ($m in $models) {
  & $LMS import -c -y --user-repo ("local/" + $m.id) $m.path   # import into LM Studio (copy)
  & $PY "bench\runner.py" --model $m.id --tasks "bench\tasks.json" `
        --out ("results\" + $m.id + "-q4_k_m.json") --repeats 2 --max-tokens 96 --timeout 240
}
& $PY "bench\report.py" "results"
Write-Host "Done -> REPORT.md + frontier_size.svg"
