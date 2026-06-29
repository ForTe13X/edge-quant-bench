# Substrate over Scale
### A cross-project research program — measuring how little model edge intelligence actually needs

> Working thesis (refined from "structure/quantization/population substitute for scale"):
> **On the edge, a deterministic *substrate* substitutes for model *scale*. Quantization and population are
> cheap *renderers* of substrate-driven behaviour, not independent cognition. The honest question is therefore
> not "can small beat big" but, causally and per-task-class: how large is the *irreducible-fuzzy residual* the
> model must carry once a rich substrate is present — and what does buying it cost in bits, params, agents,
> latency, energy, and dollars.**
>
> This is a for-fun, depth-over-breadth program. Its cultural anchor is the *celebrated honest negative*: the
> single most likely finding (independently predicted by three design lenses) is that the **substrate dominates
> and population/scale barely move the needle** — which demotes the seductive "edge swarm intelligence" story
> to "structure does the work, the model is a skin." Reporting that loudly is the deliverable, not a failure.

It turns six scattered side projects into instruments of one question. Author owns all code except SPI
(employer IP, referenced for method only) and Prism (clean-room, own code).

---

## 1. Why this is one program, not six projects

Every project independently re-invented the same shape: **a deterministic engine enumerates the legal moves and
decides; a small model only renders the irreducible-fuzzy remainder; a budget-aware policy picks the tier; an
event log makes it replayable; a deterministic wrapper makes it safe.** That shared interface
(`engine enumerates candidates → decide() picks within them → validate / fall back`) is the unifying artifact.

| Project | Organ it contributes |
|---|---|
| **小镇有灵 / 小鱼岛** (`June/26th`) | The substrate: event-sourced 6-agent society, model-free coordination ledger, byte-exact `goto_tick` replay, 33 regression invariants, and a live in-miniature tier-scheduler (`AIBackend.probe_capability`/adaptive deadline/`_logic_decide` fallback). |
| **edge-quant-bench** (`June/29th`) | The cost meter: streaming TTFT + decode-throughput probe + deterministic quality proxy + size/quant ladder. Real finding already in hand: quality non-monotone (1.5B-Q4 sweet spot), decode ~2.9× falloff with size, flat TTFT. |
| **毛孩子管家** (`June/24th`) | The tier-swap + safety wrapper: provider abstraction (local/cloud/open, zero business-code change) + deterministic hard guardrails (medical 0% miss / 14 cases). |
| **Prism / axiom-gain** | The substrate-richness prior (structured grounding → small model at ~61% fewer input tokens, 12/12 CI>0) **and** the honesty methodology (pre-registration, real-data calibration, the celebrated `collapses_under_real_calibration` nexus negative). |
| **gamecraft-bench** (`June/22nd`, published) | The eval engine: headless deterministic replay CI + multimodal LLM-as-judge panel (held to its *own* convergence gate here, never trusted as a single number). |
| SPI / 昆仑精驭 (work; method only) | Prior art of the pattern at scale: 30B→8B via distillation/routing + structured grounding on NPU. |

---

## 2. The apparatus — three reusable instruments built once, shared by all experiments

**I1 · The cost + event substrate.** Generalize `edge-quant-bench/bench/runner.py` into a `tier_profiler` that,
per runtime tier (deterministic-rule / SLM@{size×quant} / cloud), emits one uniform profile
`{p50/p95 latency, decode tok/s, peak RSS·VRAM, energy_J (RAPL/HWiNFO or calibrated proxy), quality_proxy, ci95}`.
Define one `DecisionEvent` schema `{task_features, engine_confidence, tier_chosen, deadline_ms, outcome, fell_back,
latency, energy}` that 小镇有灵's `AIBackend`, 毛孩子's `ai.js`, and Prism's fast-path all log **identically**.
That single log is simultaneously the replay tape *and* the scheduler's eval data. Because each model pick is
recorded as an *external input* (candidate-hash keyed by `tick:agent`), the **SLM becomes an ablatable variable**:
pull it, replay byte-for-byte, and the deterministic root stays green — this is what turns "how little model do
you need" from opinion into a measurement.

**I2 · The measured tier-scheduler.** Lift `AIBackend.probe_capability`/`_decide_interval`/`decide` into a
standalone policy `π(features) → tier` under a latency+energy budget, with a deterministic fallback always armed.
Evaluated against four baselines — `always-cloud`, `always-SLM`, `fixed-threshold` (today's hardcoded p50 buckets),
and an **offline oracle** (best tier per query) to bound *regret*. Research object, not engineering, only if it
beats fixed-threshold by more than seed variance.

**I3 · `honestbench` — the claim chokepoint (the meta-synergy).** A stdlib library where the only mintable result
is a frozen `Claim` returned by `mint(measurement, gates=[…])`; it cannot be constructed directly and refuses
unless every attached gate passes or is **explicitly waived-with-reason** (the waiver count = machine-visible
honesty debt). Four composable gates, each a faithful port of discipline a project already battle-tested:
- **G1 Discriminability** — task neither floor nor ceiling; sweet-spot pre-registered by a method-*independent*
  oracle (axiom-gain §6c). Knob frozen with a `prereg_hash` before the lens runs.
- **G2 Pre-registered** — prediction + confirm/refute rule frozen before the test point exists; off-line/unfavourable
  points are **kept, never pruned** (edge-quant `PREREG`, axiom-gain DON'T#4).
- **G3 Convergent** — distrust any single fancy number until ≥2 *failure-domain-disjoint* lenses agree; every proxy
  (task-acc-for-perplexity, F1-for-capability, LLM-judge-for-human) labelled with its ceiling (nexus §1). A judge
  panel is only usable inside G3 above a pre-registered inter-judge-agreement floor — never averaged into one number.
- **G4 Real-calibrated** — recompute the effect after rescaling the synthetic substrate to real-data aggregates
  (aggregates-only on disk); verdict ∈ {survives, `collapses_under_real_calibration`, indeterminate}. Mandatory,
  because nexus proved a celebrated headline can evaporate here.
Plus a shared stats core (`boot_ci`, `normal_ci`, `pareto_front`, `spearman`, `straddles_zero`) so every project's
CI and "indeterminate when the CI crosses the bar" rule is *the same code*, and a growing `FAILURE_MODES.md` registry
mapping each self-deception any project caught (construct-swap, grid-pruning, teaching-to-the-test, favourable-slice,
proxy-as-gold) to the reusable assertion that now prevents it for all of them.

> The flywheel: a failure mode caught in one project hardens a gate that protects every project. More projects
> plugged in ⇒ the next claim is auto-defended against more ways of fooling yourself.

---

## 3. Experiments (each pre-registered, each reuses ≥2 projects, each states what would refute it)

- **X0 · Cross-project re-minting + the calibration ceiling generalizes.** Re-derive every existing headline
  (axiom +61%/12-of-12; edge-quant 1.5B-Q4 sweet spot; nexus +0.073 then its collapse) through `honestbench.mint`
  byte-for-byte; the per-headline **waiver count** is the output. Then apply **G4** where it has never been applied:
  recalibrate axiom's token-saving to a *real* document-length corpus, and replace edge-quant's coarse 12-task proxy
  with **llama-perplexity** gold. *Refutes if:* axiom's 61% collapses under real calibration the way nexus did
  (report as loudly), or the perplexity ranking disagrees with task-acc (the proxy was hiding a cliff).
- **X1 · Marginal-bit/param value curve — does the substrate FLATTEN it?** Vary SLM ∈ {0.5/1.5/3B}×{Q3..Q8} + rule
  + cloud tiers; measure quality-per-Joule / per-second frontier and Δquality from dropping a bit / halving params,
  **with the substrate on vs off**. *Refutes if:* substrate-on and substrate-off curves overlap within CI → structure
  does *not* substitute for scale here; the scheduler win is just classic cascade routing.
- **X2 · Token-passing ablation — does the substrate (not the population) carry coordination?** Fix N×1.5B-Q4; compare
  (a) structured model-free ledger vs (b) agents coordinating only by free text through the SLMs. Measure coordination
  success (event-log predicates), **reproducibility** (same seed → byte-identical digest?), cost. *Refutes if:* temp-0
  token-passing also coordinates reproducibly → the substrate is a convenience, not a necessity (report the cost ratio,
  don't claim necessity).
- **X3 · PN/PS causal decomposition — population vs substrate vs scale.** Build the paired-fork harness (designed in
  小镇有灵 `docs/10 §D1/S0`, not yet coded): fork a fixed seed into branches differing by exactly one switch (drop one
  agent / ablate the reputation-commitment subsystem / swap 1.5B→8B); compute necessity/sufficiency (PN/PS) on event-log
  outcomes, always reporting raw `(p1,p0)` and bounds when reflexive effects break monotonicity. *Predicted honest
  negative:* PN(population) low, PN(substrate) high — the rigorous form of 群体演化, quantified, demoting "swarm".
- **X4 · Do hard guardrails compose across the quant ladder?** Wrap every tier (0.5B-Q3 … cloud) in the deterministic
  pre-filter + post-verifier; adversarial medical-redline corpus + paraphrase/injection. *Refutes / degrades if:* any
  quant/paraphrase slips a breach, or low-bit garble spikes the verifier's false-positive rate → "safe but unusable at
  low bits" (report the precision/coverage tradeoff, never just 0-miss).
- **X5 · SLM-as-ablated-variable: the residual.** Via byte-exact replay, ablate the SLM (on/off/smaller/lower-bit) on
  fixed seeds and diff the behavioural outcome → the measured *irreducible-fuzzy residual* per task class = the literal
  "how little model do you need." *Scoped honestly:* only inside the byte-exact window (小镇有灵 documents async drift
  past ~200 ticks). *If residual ≈ 0:* the SLM is decorative here → ship deterministic-only (a strong, clean negative).
- **X6 · The unified frontier.** One cost-per-correct Pareto surface over STRUCTURE × QUANTIZATION × POPULATION on one
  held-out task family, **every point a gated `Claim`**, both local-$0 and cloud-$cost via 毛孩子's provider swap, with
  build-cost amortization and an explicit break-even N\* (axiom's learned-alias N\*=∞ must reproduce). *Refutes seed if:*
  the three axes are redundant (population adds nothing once you have structure+Q4), or no edge config beats one mid-size
  model on cost-per-correct once real dollars are counted.

---

## 4. Roadmap

- **P0 — the shared instrument.** Extract `tier_profiler` (cost+mem+energy) + the `DecisionEvent` schema; wire the cost
  probe into `AIBackend`'s per-agent boundary (verify *zero* behaviour change on the logic backend ⇒ cost=0 floor). Lift
  the stats core into `honestbench/aggregate.py`, byte-identical against both projects' existing fixtures. *Milestone:
  one cost profile + one replayable event tape end-to-end on the APU; both projects import the shared core, all tests green.*
- **P1 — scheduler + the mint chokepoint.** Standalone `π` with the four baselines + oracle regret; `Claim`/`mint` + the
  four gates. *Milestone: X0 re-minting byte-for-byte with per-headline waiver counts; learned-vs-fixed-threshold result.*
- **P2 — the load-bearing pair.** X1 (substrate flatten?) + X2 (token-passing ablation). *Milestone: the "substrate carries
  coordination + reproducibility" result, with the single-APU serial-serving caveat measured, not assumed.*
- **P3 — the causal core.** Build & run X3 PN/PS paired-fork. *Milestone: a causal attribution of coordinated behaviour to
  population vs substrate vs scale — most likely the celebrated negative.*
- **P4 — safety + residual + calibration.** X4 guardrails-across-quant, X5 residual, and apply G4 to axiom/edge-quant
  headlines. *Milestone: the {survives/collapses/indeterminate} table + the measured per-task residual.*
- **P5 — ship the methodology.** X6 unified frontier; write `FAILURE_MODES.md` + a short methods note "Gates for honest
  edge-LLM efficiency claims"; package as a gamecraft-style CI any project can mint a claim through. *Milestone: a
  reproducible, hash-pinned, $0-to-serve artifact; every negative reported as a first-class result.*
- **P5+ (gated on a connected box).** Fill the edge-quant `PREREG` quant ladder (Q3→Q8, currently offline-blocked) so the
  per-agent bit-width axis is real, not pending.

---

## 5. Novelty, and the external-validity ceiling (stated loudly)

**Genuinely novel.** (1) Reproducible swarm results via event-sourcing + byte-exact replay — most LLM multi-agent work is
irreproducible; this is the real edge. (2) **PN/PS causal attribution of emergent coordination** on a fixed-seed event log
(群体演化 quantified, not anecdotal). (3) **SLM-as-ablated-variable** residual measurement — the hand-wavy "~5% irreducible"
turned into a number per task class. (4) A measured online **tier-scheduler grounded in quality/latency/ENERGY** on real
consumer hardware with regret vs an oracle (most routing work optimizes quality-vs-$ on cloud, never Joules on an APU).
(5) **Guardrails-compose-across-the-quant-ladder** as a measured invariant. (6) `honestbench`'s four-gate **mint chokepoint**
with `RealCalibrated` as a mandatory gate and a `FAILURE_MODES` registry — the composition + edge-specialization is the
contribution, not the ingredients.

**Prior art — do not claim as ours.** Indirect-reciprocity / opinion-dynamics / rumor-cooling models; cascade/cost routing;
quantization sweet-spot studies; LLM-judge panels; provider abstraction; deterministic-engine + LLM-skin (PIANO/Concordia);
bootstrap CIs and Pareto frontiers; pre-registration and convergent validity as concepts.

**Ceiling.** N=6–10 agents is *small* — no large-N emergence / power-law / phase-transition claims. A single AMD APU serves
SLMs serially (`MAX_INFLIGHT≈2`), so a swarm may win only on **memory-fit, not throughput** — measure before claiming. The
12-task quality metric is a **coarse proxy** (1 task = 8.3%); upgrade to perplexity before any curve carries weight. Replay
is byte-exact only within the drift-bounded window. Absolute latency/energy are one-box-specific — **report the shape**.
Synthetic substrates can be unrealistically clean (nexus §8g proved it). **The gates make a claim honest-about-itself, not
true**; a real-deployment claim needs real paired cross-source data that does not yet exist.

---

## 6. Dead-ends to avoid

- Don't chase emergent-civilization / role-specialization "swarm intelligence" — that's large-N; at N=6–10 you get
  scaffolding + anecdotes (小镇有灵 `docs/10 §F` already flags this).
- Don't let SLMs coordinate by free text in the *main* system and call it the result — that's the irreproducible baseline;
  it belongs only as the X2 ablation. The edge is that coordination is model-free and event-sourced.
- Don't claim a throughput/cost win without measuring it on *this* hardware (serial APU serving may erase it).
- Don't use an LLM judge as the *primary* metric, and don't average a panel into one confident number — G3's
  disjoint-failure-domain check forbids exactly that ("one-table-three-reads", nexus Phase-A).
- Don't revive the nexus convergence metric as a live feature — its value here is precisely the calibrated *refutation* that
  proves G4 is necessary.
- Don't build a learned/self-evolving scheduler before proving fixed-threshold is insufficient (毛孩子 already found
  self-evolution negative-ROI, with external GPT-5.5 audit concurrence). Same trap.
- Don't over-trust the coarse proxy when ranking tiers (it found 1.5B>3B); a "pick-smallest-that-clears-the-bar" policy on a
  proxy that can't resolve fine degradation will be over-confident.
- Don't build heavy reasoning infra (Prolog/OWL/RETE, ANN/pgvector) at this scale — a forward-chain function + cosine over a
  small table is the right altitude (毛孩子 §8.3).
- Don't tune any gate knob (difficulty band, α-floor, calibration target) *after* seeing its output (teaching-to-the-test /
  construct-swap); freeze with a `prereg_hash`, and disclose any knob tuned for power rather than pretending it was discovered.
- Don't drop unfavourable/off-line points to prettify a trend (the qwen3.6 off-monotone point, the deepseek 4-vs-8-seed
  correction must be kept) — that's the headline-preserving fraud the whole program rejects.

---
*Cross-project research program. Synthesized 2026-06-29 from a 4-lens design panel (edge-swarm / edge-runtime / honest-eval;
the efficiency-frontier lens is folded in). Home repo `edge-quant-bench/docs/` for convenience — the program spans
`June/{22,24,26,29}` + `prism`. Honest, for-fun, depth over breadth.*
