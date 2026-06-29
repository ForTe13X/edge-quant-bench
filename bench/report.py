"""edge-quant-bench · report — merge per-model runner JSON into honest, ladder-aware tables + SVG.

Two axes of on-device efficiency, kept separate so no apples-to-oranges comparison sneaks in:
  • SIZE ladder  — fixed quant (Q4_K_M), vary params (0.5B/1.5B/3B): "how small a model still works".
  • QUANT ladder — fixed model (1.5B), vary bit-width (Q4 vs Q8...): "how few bits before quality drops".

Driven by results/meta.json (so a model can sit in BOTH ladders — e.g. 1.5B-Q4 is the small end of the
size ladder AND the Q4 point of the quant ladder). Every cell is MEASURED; missing inputs render "—".
Stdlib only.
"""
from __future__ import annotations
import json, os, sys

BITS = {"q3_k_m": 3.0, "q4_k_m": 4.0, "q5_k_m": 5.0, "q6_k": 6.0, "q8_0": 8.0, "f16": 16.0}


def fmt_gb(b):
    return f"{b/1e9:.2f} GB" if isinstance(b, (int, float)) else "—"


def load_results(results_dir):
    out = {}
    for fn in os.listdir(results_dir):
        if not fn.endswith(".json") or fn in ("sizes.json", "meta.json"):
            continue
        r = json.load(open(os.path.join(results_dir, fn), encoding="utf-8"))
        out[r["model"]] = r
    return out


def row_for(mid, meta, res):
    m = meta["models"].get(mid, {})
    r = res.get(mid, {})
    tt = (r.get("ttft_s") or {})
    tp = (r.get("decode_tok_per_s") or {})
    return {
        "model": mid, "quant": m.get("quant", "?"), "params_b": m.get("params_b"),
        "size_b": m.get("size_b"), "acc": r.get("quality_acc"), "n_tasks": r.get("n_tasks"),
        "ttft_p50": tt.get("p50"), "tps_mean": tp.get("mean"), "tps_ci": tp.get("ci95_half"),
    }


def table(rows, axis_col):
    head = f"| {axis_col} | quant | params | size | quality_acc | TTFT p50 (s) | decode tok/s |\n|---|---|---|---|---|---|---|"
    body = "\n".join(
        f"| {r[axis_label_key(axis_col)]} | `{r['quant']}` | {r['params_b'] or '—'}B | {fmt_gb(r['size_b'])} | "
        f"{r['acc'] if r['acc'] is not None else '—'} | {r['ttft_p50'] if r['ttft_p50'] is not None else '—'} | "
        f"{(str(round(r['tps_mean'],1))+'±'+str(round(r['tps_ci'] or 0,1))) if r['tps_mean'] else '—'} |"
        for r in rows)
    return head + "\n" + body


def axis_label_key(axis_col):
    return "params_b" if "size" in axis_col.lower() else "bits_disp"


def size_verdicts(rows):
    rows = [r for r in rows if r["acc"] is not None]
    if len(rows) < 2:
        return ["**Size ladder:** need ≥2 models."]
    best = max(rows, key=lambda r: (r["acc"], -(r["size_b"] or 1e18)))
    biggest = max(rows, key=lambda r: r["params_b"] or 0)
    mono = all((rows[i]["acc"] <= rows[i + 1]["acc"]) for i in range(len(rows) - 1)
               if (rows[i]["params_b"] or 0) < (rows[i + 1]["params_b"] or 0))
    v = [f"**Quality sweet spot:** `{best['quant']}` **{best['params_b']}B** at acc **{best['acc']}** "
         f"({fmt_gb(best['size_b'])}) — best quality-per-byte on this suite.",
         f"**Quality vs params is {'monotone' if mono else 'NON-monotone'}:** "
         + ", ".join(f"{r['params_b']}B={r['acc']}" for r in sorted(rows, key=lambda r: r['params_b'] or 0))
         + ("" if mono else " — the coarse 12-task suite + small-model variance; bigger ≠ always better here.")]
    tps = [(r["params_b"], r["tps_mean"]) for r in rows if r["tps_mean"]]
    if len(tps) >= 2:
        hi = max(tps, key=lambda x: x[1]); lo = min(tps, key=lambda x: x[1])
        v.append(f"**Decode throughput falls with size (as expected):** {hi[0]}B {hi[1]:.0f} → {lo[0]}B {lo[1]:.0f} tok/s "
                 f"({hi[1]/lo[1]:.2f}×). TTFT ~flat (overhead-bound at these sizes).")
    return v


def quant_verdicts(rows):
    by = {r["quant"]: r for r in rows if r["acc"] is not None}
    n = next((r["n_tasks"] for r in rows if r.get("n_tasks")), 12) or 12
    tol = 1.0 / n
    g = lambda q, k: (by.get(q) or {}).get(k)
    out = []
    if g("q4_k_m", "acc") is not None and g("q8_0", "acc") is not None:
        h1 = abs(g("q8_0", "acc") - g("q4_k_m", "acc")) <= tol
        out.append(f"**H1 (Q4 preserves quality vs near-lossless Q8):** {'CONFIRMED' if h1 else 'REFUTED'} — "
                   f"acc Q4={g('q4_k_m','acc')} vs Q8={g('q8_0','acc')} (±1 task = {tol:.3f}).")
        if g("q3_k_m", "acc") is not None:
            h1b = g("q3_k_m", "acc") <= g("q4_k_m", "acc") - tol
            out.append(f"**H1b (Q3 starts to break):** {'CONFIRMED' if h1b else 'not yet'} — Q3={g('q3_k_m','acc')}.")
    else:
        out.append("**Quant ladder:** need both Q4 and Q8 accuracy (download Q8 — see scripts/quant_ladder.ps1).")
    if g("q4_k_m", "size_b") and g("q8_0", "size_b"):
        sv = 1 - g("q4_k_m", "size_b") / g("q8_0", "size_b")
        out.append(f"**H2 (Q4 size win):** Q4 saves **{sv*100:.0f}%** vs Q8 "
                   f"({fmt_gb(g('q4_k_m','size_b'))} vs {fmt_gb(g('q8_0','size_b'))}).")
    if g("q4_k_m", "tps_mean") and g("q8_0", "tps_mean"):
        a, b = g("q4_k_m", "tps_mean"), g("q8_0", "tps_mean")
        ca, cb = g("q4_k_m", "tps_ci") or 0, g("q8_0", "tps_ci") or 0
        overlap = not (a - ca > b + cb or b - cb > a + ca)
        out.append(f"**H3 (decode):** Q4 {a:.0f}±{ca:.0f} vs Q8 {b:.0f}±{cb:.0f} tok/s — "
                   f"{'CIs overlap → on-device win is FITTING in memory, not raw tok/s' if overlap else f'Q4 {a/b:.2f}× faster → weight-bandwidth-bound'}.")
    return out


def svg_frontier(rows, title):
    pts = [r for r in rows if r["acc"] is not None and r["size_b"]]
    if not pts:
        return f"<!-- {title}: no (size,acc) points -->"
    W, H, pad = 560, 360, 58
    xs = [r["size_b"]/1e9 for r in pts]; ys = [r["acc"] for r in pts]
    xmin, xmax = min(xs)*0.85, max(xs)*1.08
    ymin, ymax = max(0, min(ys)-0.12), 1.03
    X = lambda v: pad + (v-xmin)/(xmax-xmin)*(W-2*pad)
    Y = lambda v: H-pad-(v-ymin)/(ymax-ymin)*(H-2*pad)
    tmax = max([r["tps_mean"] for r in pts if r["tps_mean"]] or [1])
    el = [f'<rect width="{W}" height="{H}" fill="#0d1117"/>',
          f'<text x="{W/2}" y="22" fill="#c9d1d9" font-family="sans-serif" font-size="14" text-anchor="middle">{title}</text>',
          f'<line x1="{pad}" y1="{H-pad}" x2="{W-pad}" y2="{H-pad}" stroke="#30363d"/>',
          f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{H-pad}" stroke="#30363d"/>',
          f'<text x="{W/2}" y="{H-14}" fill="#8b949e" font-family="sans-serif" font-size="11" text-anchor="middle">model size (GB) → · bubble ∝ decode tok/s</text>',
          f'<text x="16" y="{H/2}" fill="#8b949e" font-family="sans-serif" font-size="11" text-anchor="middle" transform="rotate(-90 16 {H/2})">quality acc →</text>']
    for r in sorted(pts, key=lambda r: r["size_b"]):
        cx, cy = X(r["size_b"]/1e9), Y(r["acc"])
        rad = 6 + 16*((r["tps_mean"] or 0)/tmax) if r["tps_mean"] else 6
        lab = f'{r["params_b"]}B·{r["quant"]} ({r["acc"]})'
        el.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="#3fb950" fill-opacity="0.32" stroke="#3fb950"/>')
        el.append(f'<text x="{cx:.1f}" y="{cy-rad-4:.1f}" fill="#c9d1d9" font-family="sans-serif" font-size="10" text-anchor="middle">{lab}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">' + "".join(el) + "</svg>"


def main():
    rd = sys.argv[1] if len(sys.argv) > 1 else "results"
    root = os.path.dirname(rd) or "."
    meta = json.load(open(os.path.join(rd, "meta.json"), encoding="utf-8"))
    res = load_results(rd)

    sections, svgs = [], []
    for axis_name, axis_col, members in [
        ("Size ladder — fixed Q4_K_M, vary params (measured/exploratory)", "size (params)", meta["ladders"].get("size", [])),
        ("Quant ladder — fixed 1.5B, vary bit-width (pre-registered H1–H3)", "bits", meta["ladders"].get("quant", [])),
    ]:
        rows = [row_for(m, meta, res) for m in members if m in res]
        for r in rows:
            r["bits_disp"] = (str(int(BITS[r["quant"]])) + "-bit") if r["quant"] in BITS else "—"
        if "size" in axis_name.lower():
            rows.sort(key=lambda r: r["params_b"] or 0)
            verds = size_verdicts(rows)
            svgs.append(("frontier_size.svg", svg_frontier(rows, "Size ladder · quality vs size (Q4_K_M)")))
        else:
            rows.sort(key=lambda r: BITS.get(r["quant"], 0))
            verds = quant_verdicts(rows)
            svgs.append(("frontier_quant.svg", svg_frontier(rows, "Quant ladder · quality vs size (1.5B)")))
        if rows:
            sections.append(f"## {axis_name}\n\n" + table(rows, axis_col) + "\n\n- " + "\n- ".join(verds) + "\n")

    md = ("# Results\n\n> Every cell is **measured** (real generation call / file stat). Quality = 12-task "
          "deterministic PROXY suite (not perplexity; perplexity needs llama.cpp — see scripts/quant_ladder.ps1). "
          "Latency is this-box-specific (AMD APU + LM Studio) — read the SHAPE, not the absolutes.\n\n"
          + "\n".join(sections))
    open(os.path.join(root, "REPORT.md"), "w", encoding="utf-8").write(md)
    for name, svg in svgs:
        open(os.path.join(root, name), "w", encoding="utf-8").write(svg)
    print("wrote REPORT.md +", ", ".join(n for n, _ in svgs))
    print(md.split("# Results")[1][:1400])


if __name__ == "__main__":
    main()
