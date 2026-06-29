"""edge-quant-bench · runner — measure ONE model served at an OpenAI-compatible endpoint.

Honest-by-construction: every number here is MEASURED from a real generation call, never
assumed. Latency uses streaming so TTFT (time-to-first-token) and decode throughput are real,
not derived from a single total. Quality is a small DETERMINISTIC auto-scored smoke suite (temp=0,
exact/format/keyword scorers) — a PROXY for quality, NOT a full eval; the gold perplexity ladder
needs llama-perplexity (see scripts/quant_ladder.ps1). Stdlib only (urllib) — no deps to install.

Usage:
  python runner.py --model "<lmstudio-model-id>" --tasks tasks.json --out results/<id>.json \
                   [--repeats 2] [--endpoint http://localhost:1234/v1] [--max-tokens 96]
"""
from __future__ import annotations
import argparse, json, re, sys, time, urllib.request, urllib.error


def _post_stream(endpoint, model, prompt, max_tokens, timeout):
    """Stream a chat completion. Returns (ttft_s, total_s, text, n_chunks, usage|None, error|None)."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": 0, "stream": True,
        "stream_options": {"include_usage": True},
    }).encode()
    req = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    ttft = None
    parts, chunks, usage = [], 0, None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if obj.get("usage"):
                    usage = obj["usage"]
                for ch in obj.get("choices", []):
                    piece = (ch.get("delta") or {}).get("content")
                    if piece:
                        if ttft is None:
                            ttft = time.perf_counter() - t0
                        parts.append(piece)
                        chunks += 1
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        return None, time.perf_counter() - t0, "".join(parts), chunks, usage, f"{type(e).__name__}: {e}"
    total = time.perf_counter() - t0
    return ttft, total, "".join(parts), chunks, usage, None


# ---- deterministic scorers (a quality PROXY, honestly labelled) -------------------------------
def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def score_task(task, output):
    """Return (passed: bool, detail: str). Scorers are intentionally simple & deterministic."""
    kind = task["scorer"]
    out = _norm(output)
    exp = task.get("expect")
    if kind == "exact":
        # accept the expected token appearing as a standalone answer (models add fluff)
        toks = re.findall(r"[a-z0-9\.\-:apm]+", out)
        return (_norm(exp) in out or _norm(exp) in toks), f"want~{exp!r}"
    if kind == "contains_all":
        return all(_norm(x) in out for x in exp), f"want_all~{exp}"
    if kind == "json_fields":
        try:
            m = re.search(r"\{.*\}", output, re.S)
            obj = json.loads(m.group(0)) if m else json.loads(output)
        except Exception as e:
            return False, f"json_parse_fail:{type(e).__name__}"
        ok = all(k in obj and str(obj[k]).strip() for k in exp)
        return ok, f"need_keys~{exp}"
    if kind == "regex":
        return bool(re.search(exp, output or "", re.I)), f"re~{exp}"
    return False, "unknown_scorer"


def throughput_probe(endpoint, model, timeout, n=2):
    """Decode throughput needs a LONG generation to be meaningful (short answers make total≈ttft and
    tok/s explode). This forces ~200 tokens and measures clean decode tok/s, separate from the task suite."""
    prompt = "Write a single paragraph of about 180 words describing a sunrise over the ocean. Plain prose."
    vals = []
    for _ in range(n):
        ttft, total, text, chunks, usage, err = _post_stream(endpoint, model, prompt, 256, timeout)
        ct = (usage or {}).get("completion_tokens")
        if not err and ttft is not None and total > ttft + 0.05 and isinstance(ct, (int, float)) and ct >= 32:
            vals.append((ct - 1) / (total - ttft))
    return vals


def run(model, tasks, endpoint, repeats, max_tokens, timeout):
    rows, lat_ttft, lat_tps = [], [], []
    for t in tasks:
        best_pass = False
        per_repeat = []
        for r in range(repeats):
            ttft, total, text, chunks, usage, err = _post_stream(endpoint, model, t["prompt"], max_tokens, timeout)
            ct = (usage or {}).get("completion_tokens")
            tps = None
            if ttft is not None and total > ttft and isinstance(ct, (int, float)) and ct > 1:
                tps = (ct - 1) / (total - ttft)  # decode throughput (exclude the first token)
            passed, detail = (False, err) if err else score_task(t, text)
            best_pass = best_pass or passed
            if ttft is not None:
                lat_ttft.append(ttft)
            if tps is not None and isinstance(ct, (int, float)) and ct >= 16:  # short outputs make tok/s unreliable
                lat_tps.append(tps)
            per_repeat.append({"repeat": r, "ttft_s": ttft, "total_s": round(total, 3),
                               "completion_tokens": ct, "tok_per_s": round(tps, 2) if tps else None,
                               "passed": passed, "detail": detail, "output": (text or "")[:200], "error": err})
        rows.append({"id": t["id"], "scorer": t["scorer"], "passed_any": best_pass, "repeats": per_repeat})

    def stats(xs):
        if not xs:
            return None
        xs = sorted(xs); n = len(xs)
        mean = sum(xs) / n
        # 95% CI of the mean via normal approx (honest: small n, reported as such)
        var = sum((x - mean) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
        half = 1.96 * (var ** 0.5) / (n ** 0.5) if n > 1 else 0.0
        return {"n": n, "mean": round(mean, 4), "p50": round(xs[n // 2], 4),
                "ci95_half": round(half, 4), "min": round(xs[0], 4), "max": round(xs[-1], 4)}

    n_pass = sum(1 for x in rows if x["passed_any"])
    probe_vals = throughput_probe(endpoint, model, timeout)  # clean long-gen decode tok/s
    return {
        "model": model, "endpoint": endpoint, "repeats": repeats, "max_tokens": max_tokens,
        "n_tasks": len(tasks), "n_pass": n_pass, "quality_acc": round(n_pass / len(tasks), 4) if tasks else None,
        "ttft_s": stats(lat_ttft),
        "decode_tok_per_s": stats(probe_vals),                # from the long-gen probe (reliable)
        "decode_tok_per_s_suite": stats(lat_tps),             # from suite (only outputs >=16 tok; may be sparse)
        "tasks": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tasks", default="bench/tasks.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--endpoint", default="http://localhost:1234/v1")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--max-tokens", type=int, default=96)
    ap.add_argument("--timeout", type=float, default=180.0)
    a = ap.parse_args()
    tasks = json.load(open(a.tasks, encoding="utf-8"))
    res = run(a.model, tasks, a.endpoint, a.repeats, a.max_tokens, a.timeout)
    import os
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    q = res["quality_acc"]; tt = res["ttft_s"]; tp = res["decode_tok_per_s"]
    print(f"[{a.model}] quality_acc={q}  ttft_p50={tt['p50'] if tt else None}s  "
          f"decode={tp['mean'] if tp else None}±{tp['ci95_half'] if tp else None} tok/s  -> {a.out}")


if __name__ == "__main__":
    main()
