# Hindsight D4 — Polish & Showcase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the working system into an interview-ready showcase: a real evaluation suite powering the Leaderboard page, a finalized bilingual README with visuals, an honest evaluation-methodology document, judge meta-evaluation receipts, a rehearsed offline demo script, and a final whole-repo review — ending at tag `d4-complete`.

**Architecture note:** Only ONE small backend addition (suite listing endpoint). Everything else is data (live suite run), frontend (one page), and documents. Live API calls are authorized (quota ample; 429 patience per the D2 owner note).

**Working directory:** repo root `F:/AIProjects/my_show/hindsight`, branch `d1-foundation`. Baseline: tag `d3-complete`, **168 tests green**, offline demo path proven.

**Test-count note:** trust arithmetic over stale literals if review fixes add tests (established convention).

---

### Task 1: Corpus citation hygiene (audit carryover)

The two URL nits from the D1/D2 data audits. WebSearch authorized.

- [ ] `datasets/nvda_fy26q1/docs/ai_capex_skeptic.md` — the doc is dated 2025-05-10 but cites a 2025-03-26 Bloomberg piece. Find a genuinely May-2025 bearish/skeptic AI-capex opinion source (WebSearch; e.g. coverage around the May 2025 "AI capex digestion" debate) and replace the frontmatter `url`. If the BODY references facts sourced only from the old article, keep body claims consistent with the new source's date (verify the body's facts remain accurate for a 2025-05-10 publication — the temporal-consistency red line applies).
- [ ] `datasets/smci_case3/docs/bear_view_margins_governance.md` — dated 2025-02-24 but the URL slug suggests Dec 2024. Find a Feb-2025 source documenting JPMorgan's Underweight/$23 stance or the margin/governance bear case (it persisted into Feb 2025 per the audit) and replace the `url`.
- [ ] Run `cd backend && .venv/Scripts/python -m pytest tests/test_nvda_case.py tests/test_smci_case.py -q` — 7 passed; full suite 168 passed.
- [ ] Commit: `fix(d4): corpus citation dates match document dates`

---

### Task 2: Real evaluation suite run (LIVE — the leaderboard's data)

Produces the suite artifacts the Leaderboard page renders: 2 cases × {base, memory} = 4 runs (~50-65 metered calls; recorded calls replay free on re-launch after any crash).

- [ ] **Step 1: Launch** from repo root:
  `backend/.venv/Scripts/python -m hindsight.cli suite --cases datasets/smci_case3,datasets/nvda_fy26q1 --presets base,memory`
  Notes: cases auto-sort by as_of (SMCI 2025-02-26 first); the `memory` config on NVDA legally retrieves SMCI experience cards (window ends 2025-04-24 ≤ NVDA's as_of — the time-legal experience flow demo); on SMCI, no cards pass the gate (NVDA windows end later) — that asymmetry is itself showcase material. Expect several minutes; 429 waits are normal; if the process dies, re-launch — replays are free.
- [ ] **Step 2: Inspect** `runs/suites/<suite_id>.json` + the 4 run dirs. Acceptance: 4 runs `done` (an `unverified` run is acceptable; a `failed` run → re-launch once; twice → report the transcripts); summary has per-case per-config scores.
- [ ] **Step 3: eval-log entry**: dated "D4 — evaluation suite" section: suite_id, per-config hit_rate/brier/grounding per case, whether memory-on differed from base on NVDA (did the planner's brief include lesson lines? check the run's trace for the experience block), total calls.
- [ ] **Step 4: Commit** runs + `llm_calls.sqlite` + `hindsight.db` + eval-log: `feat(d4): first real evaluation suite recorded`

---

### Task 3: Suite listing endpoint + Leaderboard page

**Backend (TDD):** add `GET /api/eval/suites` (list) to `backend/hindsight/api/routes_eval.py`:

```python
@router.get("/api/eval/suites")
def list_suites(request: Request):
    state = request.app.state.hindsight
    suites_dir = state.runs_root / "suites"
    out = []
    if suites_dir.exists():
        for p in sorted(suites_dir.glob("*.json")):
            try:
                s = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            out.append(
                {
                    "suite_id": s.get("suite_id", p.stem),
                    "started_at": s.get("started_at"),
                    "cases": s.get("cases", []),
                    "configs": s.get("configs", []),
                    "status": s.get("status", "ok"),
                }
            )
    return out
```

Test (append to `backend/tests/test_api_eval.py`; expect suite total 170):

```python
def test_list_suites(api_root):
    out = api_root / "runs" / "suites"
    out.mkdir(parents=True)
    (out / "s1.json").write_text(
        json.dumps({"suite_id": "s1", "started_at": "t", "cases": ["c"], "configs": ["base"]}),
        encoding="utf-8",
    )
    (out / "junk.json").write_text("{broken", encoding="utf-8")
    client = TestClient(create_app(repo_root=api_root))
    suites = client.get("/api/eval/suites").json()
    assert [s["suite_id"] for s in suites] == ["s1"]  # broken file skipped


def test_list_suites_empty(api_root):
    client = TestClient(create_app(repo_root=api_root))
    assert client.get("/api/eval/suites").json() == []
```

**Frontend:** NEW `frontend/src/pages/Leaderboard.tsx` + route `/leaderboard` + nav link. Must implement:
1. Suite picker (from `/api/eval/suites`, newest first; empty state message).
2. Matrix table: rows = cases, column groups = configs; cells show hit_rate / brier / grounding (— for null); a `status` chip when not "ok"; **paired-delta row**: for each non-base config, Δhit_rate and Δbrier vs `base` per case (computed client-side, green/red by direction — brier lower is better).
3. Quality-vs-cost scatter (Recharts): x = total tokens (sum of scores.cost across agents, from suite_status runs), y = hit_rate; point per (case, config), config-colored, case-labeled. Data: join `/api/eval/suites/{id}` runs (scores_json) — parse defensively.
4. Sample-size honesty line rendered under the matrix (i18n key: e.g. "N is small by design — this compares mechanisms, not statistical significance." / 中文对应).
5. i18n throughout (key-symmetric); `npm run build` exit 0; no @ts-ignore.

Acceptance: with the T2 suite committed, offline backend + dev server → page renders the real matrix/deltas/scatter; EN/中 flips; empty-suite state verified against a fresh temp root. Commit: `feat(d4): leaderboard page with paired deltas and cost-quality scatter`

---

### Task 4: Judge meta-evaluation receipts

Spec §3.4-B: report judge-vs-human agreement on 10-20 grounding judgments.

- [ ] Extract from ALL committed runs (4 D2/D3-era + 4 suite runs): every `grounding` entry the judge produced (claim_id, supported verdict, comment) alongside the claim statement + its cited evidence excerpts (from the run's trace/corpus). Write `docs/judge-meta-eval.md` as a table: run_id / claim_id / statement (truncated) / evidence gist / judge verdict / **human label** / agree?
- [ ] Label each row by REREADING the evidence chunks yourself (does the cited text genuinely support the claim?). Mark the labels' provenance honestly in the doc header: "Labels produced by the Claude coordinator re-reading each cited chunk, intended for author review — relabel any row you disagree with; agreement rate recomputes trivially." Compute and state the agreement rate.
- [ ] If fewer than 10 grounding entries exist across runs, note the shortfall honestly rather than padding.
- [ ] Commit: `docs(d4): judge meta-evaluation labels and agreement rate`

---

### Task 5: Evaluation methodology document

NEW `docs/evaluation-methodology.md` (English, interview-facing). Consolidate — do not invent — from spec §3.2-3.6, eval-log, and the grader/judge code. Required sections:
1. **Three tracks** (outcome / process / cost) with the exact grading semantics summary (baseline P0, at-horizon-end, closed intervals, volatility percentile, ungradable rules).
2. **Statistical limitations** (the honest-framing section reviewers demanded): small N is a mechanism demo, not significance; claims within a run are correlated (same ticker/window); the SMCI failure case is deliberately selected — say so; calibration buckets carry n labels for this reason; paired deltas over absolute ranks.
3. **The three anti-lookahead channels** + the fourth that cannot be closed: parametric memory — contamination probe design and what its output does/doesn't prove.
4. **Judge validity**: self-preference risk (same model), why relative config comparisons survive it, meta-eval receipts (link Task 4's doc + agreement rate).
5. **Reproducibility**: frozen bars, record/replay determinism (byte-identical offline runs — cite the T14/T15 diffs), fixed prompts as versioned code with eval-log receipts.
- [ ] Link it from README's Evaluation section. Commit: `docs(d4): evaluation methodology with honest limitations`

---

### Task 6: README final + 中文版 + banner + visuals

- [ ] **Banner**: hand-craft `docs/assets/banner.svg` — dark (#0a0e14) wide banner (1200×220): "HINDSIGHT" in mono caps + tagline "Research agents, graded by the future." + a minimal masked-price-line motif (past line solid cyan, future dashed green behind a mask edge at an amber as-of line). Pure SVG, no external fonts beyond generic monospace fallback. Reference it at the top of README.
- [ ] **Screenshots**: attempt Preview-tool captures of the three pages + leaderboard (offline backend). If `preview_screenshot` stays flaky, capture via `preview_snapshot` evidence and instead ship a `docs/demo-script.md` reference; do NOT block on GIF — a GIF is nice-to-have (skip gracefully, note in report).
- [ ] **README.md deepen**: leaderboard section (real suite numbers + paired-delta reading guide), methodology + judge-meta-eval links, screenshots if captured, demo-script link, accurate test count badge text, "Built in 4 days as an interview showcase — see docs/eval-log.md for the evaluation-driven development trail" line (own the story).
- [ ] **README.zh.md**: full Chinese translation (not machine-literal — natural technical Chinese), linked from README top ("中文版").
- [ ] `npm run build` still green; backend suite still green. Commit: `docs(d4): final bilingual README with banner and visuals`

---

### Task 7: Demo script + final whole-repo review + wrap-up

- [ ] **`docs/demo-script.md`**: (a) setup: one-command offline demo (uvicorn env HINDSIGHT_OFFLINE=1 + built frontend at :8000, or launch.json pair), reset steps; (b) 10-minute talk track mapped to JD themes — cold open on Studio reveal moment → trace/audit (why it behaves) → eval dashboard attribution → leaderboard deltas (evaluation-driven) → known-limitations Q&A prep (contamination, small-N, judge bias — with the honest answers); (c) failure-mode drill: what to do if the dev server dies mid-demo (静态 build 已可由 uvicorn 单进程服务).
- [ ] **Offline rehearsal**: full click-through of all FOUR pages against the built frontend served by uvicorn alone (single process, closest to interview conditions); checklist in the report.
- [ ] **Final whole-implementation review** (the subagent-driven-development finale): dispatch a fresh reviewer over `git diff d1-complete..HEAD --stat` + spot-depth on the riskiest seams (sandbox integrity, replay determinism, README claims vs reality — every number in README/methodology must trace to an artifact). Findings triaged: Critical/Important fixed before tag; Minor recorded in a `docs/future-work.md`.
- [ ] **`docs/future-work.md`** must also record the conscious scope decisions: case 2 (TSLA) deferred per the D1 plan's pre-sanctioned risk fallback (3→2 cases; EvalSuite scales when it lands); GIF if skipped; chunker heading-only merge polish; CLI UX hardening; the D3 carryover leftovers that stayed acceptable.
- [ ] **Security final pass**: full-history key scan (known doc-quote false positive excepted); `.env` untracked; no stray files outside repo.
- [ ] Full suite exact count; `npm run build` exit 0.
- [ ] Commit `chore(d4): day-4 wrap-up` + tag `d4-complete`.
- [ ] Ask the owner: push to GitHub (private first vs straight public), repo name `hindsight` under ZhaoSH980.

---

## Execution notes

- Conventions unchanged (subagent per task; backend TDD tasks get two-stage review; data/docs tasks get audit-style review; frontend gets acceptance-checklist verification; coordinator amends this plan on sanctioned deviations).
- Task 2 is the only quota-consuming task (~50-65 calls). Everything else offline/replay.
- Preview-tool note for implementers: its launch.json resolves one level ABOVE the repo — any scratch copy there must be deleted after use (three prior tasks confirmed this pattern).