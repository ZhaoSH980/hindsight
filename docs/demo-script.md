# Demo script — the 10-minute offline walkthrough

Rehearsed against the committed artifacts (tag `d4-complete`). Everything
below runs **offline**: no API key, no network, no metered LLM calls. The
demo replays the recorded runs in `llm_calls.sqlite` / `runs/`, which is
itself part of the pitch — determinism is a feature, show it off.

---

## 1. Setup

### Option A — single process (recommended for the live demo)

One process serves the API **and** the built frontend at `:8000`. Fewest
moving parts; survives with no Node running.

```bash
# once, or whenever frontend/src changed:
npm run build --prefix frontend

# then (bash):
HINDSIGHT_OFFLINE=1 backend/.venv/Scripts/python -m uvicorn hindsight.api.app:app --port 8000
```

```powershell
# PowerShell equivalent:
$env:HINDSIGHT_OFFLINE = "1"
backend/.venv/Scripts/python -m uvicorn hindsight.api.app:app --port 8000
```

Open **http://localhost:8000** (not :5173 — there is no dev server in this
mode). The backend mounts `frontend/dist` with an SPA fallback, so hard
refreshes on `/runs/...` and `/leaderboard` work.

No `.env` is needed offline: `HINDSIGHT_OFFLINE=1` falls back to placeholder
endpoint config with the recorded model as default, and raises loudly on any
replay-cache miss rather than touching the network.

### Option B — two-process dev pair

`.claude/launch.json` defines both servers for one-click tooling launch
(backend on `:8000` with `HINDSIGHT_OFFLINE=1`, Vite dev server on `:5173`).
Manually:

```bash
HINDSIGHT_OFFLINE=1 backend/.venv/Scripts/python -m uvicorn hindsight.api.app:app --port 8000
npm run dev --prefix frontend   # second terminal; open http://localhost:5173
```

Use this only if you want hot reload; for the interview, Option A.

### Reset between rehearsals

Clicking **Run research** creates a new run directory and rows in
`hindsight.db` (never in `llm_calls.sqlite` — offline mode writes no LLM
rows). To restore the committed state:

```bash
git checkout -- hindsight.db
git clean -nd runs/     # preview: should list only run dirs you just created
git clean -fd runs/     # delete them
git status              # must be clean
```

### Preflight (2 minutes, morning of)

- [ ] `cd backend && .venv/Scripts/python -m pytest -q` → **171 passed**
- [ ] Start Option A; open `:8000`; both cases visible in the Studio
- [ ] `/leaderboard` shows `suite_c3b22b4b`
- [ ] Reset state (above) so the run you do live is the first of the day

---

## 2. The 10-minute talk track

Timings assume ~1 min per beat plus questions at the end. Every number you
say out loud is in a committed artifact — if challenged, open the file.

### Beat 1 — Cold open: the reveal (Studio, ~2 min)

Open the Studio on **NVDA**. Point at the price chart: it just *stops* at
the amber `as_of` line (2025-05-22). Say the line: **"the future does not
exist yet"** — it's rendered under the chart.

Click **Run research**. The live feed streams the real agent trace (plan
steps, tool calls, sandbox audits) — replayed deterministically from the
recorded run, so it cannot die on stage. Memo lands with 4 falsifiable,
dated claims, each with confidence and cited evidence chunks.

Then the moment: **"The outcome window has closed."** Click **Reveal the
future**. The realized price path draws in green past the amber line, and
every claim gets a mechanical hit/miss verdict against it.

> Theme: evaluation of research quality made *falsifiable* — the market
> grades the memo, not a human's taste.

### Beat 2 — Why it behaves the way it does (Trace Explorer, ~2 min)

From the Eval Dashboard's run list (or "View full trace"), open the NVDA
**memory** run `run_nvda_fy26q1_20260704_110357_439805`. Show:

- The full config JSON in the header (`memory_on: true`, model, budgets).
- Filter chips: **Plan 8 / Tool 22 / Validation 1 / Audit 9 / Score 1**.
- Click **Audit**: every sandbox decision is an event. Expand a
  `market_data` entry — `data_max_date: 2025-05-22`, i.e. the gate stamped
  that no bar after as_of ever reached the agent. Denials are audited too.
- The per-agent token ledger at the bottom (planner/analyst/critic/judge).

> Theme: auditability. The trace is one code path for live streaming and
> replay — what you watched in Beat 1 is literally this file.

### Beat 3 — Attribution, not vibes (Eval Dashboard, ~2 min)

Same run's dashboard. Walk the cards: hit rate 25%, Brier 0.301, grounding
100%, judge scores 4/5. Then the two honesty artifacts:

- **Calibration chart**: bucketed scatter with `n=` labels — no smoothed
  line over 4 points, ever.
- **Claims table**: every miss carries an attribution —
  `reasonable_but_wrong` (process sound, market disagreed) vs
  `evidence_missing` vs `misread_evidence`. That's the answer to "why did
  it miss": retrieval failure, misreading, or an honest wrong call.
- Expand the **contamination probe**: the model, asked bluntly, answers "I
  do not know what happened to NVDA... after May 22, 2025."

### Beat 4 — Evaluation-driven, with receipts (Leaderboard, ~2 min)

Open `/leaderboard`, suite `suite_c3b22b4b`. The story is the **paired
deltas**, not the absolute numbers:

- SMCI: memory Δ = 0.000 — byte-identical to base, because at SMCI's as_of
  **no experience card passes the time gate** (NVDA's outcome window closes
  later). The gate working is visible in the data.
- NVDA: memory run demonstrably changed (SMCI's graded lesson injected into
  all 8 planner calls — verifiable in `llm_calls.sqlite`) and Brier got
  *worse* (+0.039, shown in red). Say it plainly: honest N=1 mechanism
  demo, not a claim that memory helps.
- Point at the line under the matrix: *"N is small by design — this
  compares mechanisms, not statistical significance."*

If asked "how was this built": `docs/eval-log.md` is the development trail —
two prompt fixes were made *because* graded runs failed, each with
before/after scores (the mutual-consistency rule; the critic rubric rewrite).

### Beat 5 — Limitations Q&A (~2 min, invite it)

Volunteer these before being asked; the honest answers are the showcase.

- **"The model might already know what happened."** Correct — parametric
  memory is the fourth channel the sandbox cannot close. We probe it
  per-case (both probes clean) and state exactly what a clean probe does
  and doesn't prove: it rules out blunt recall, not latent memory. Scores
  on a contaminated case would be read as grading-pipeline correctness, not
  research skill. (`docs/evaluation-methodology.md` §3.)
- **"Two cases, four claims — that's not significance."** Agreed, and
  never claimed: small N is a mechanism demo; claims within a run are
  correlated (same ticker, same window); SMCI was *deliberately selected*
  to be a falsification case. That's why the UI prints `n=` on every
  calibration bucket and the leaderboard leads with paired deltas.
  (`docs/evaluation-methodology.md` §2.)
- **"The judge grades its own model's homework."** Yes — self-preference
  risk is real. Relative config comparisons survive it (same judge on both
  sides of every delta), and the judge is audited: all 26 recoverable
  grounding verdicts re-labeled independently, 26/26 agreement — with the
  stated caveat that every verdict in the sample is `supported`, so it
  shows zero false positives, not miss-catching ability. A perturbation
  test is named future work. (`docs/judge-meta-eval.md`.)

---

## 3. Failure drills

**Drill A — dev server dies mid-demo (Option B users).**
The static build is served by the uvicorn process alone. Kill nothing,
just switch the browser tab to `http://localhost:8000` — same app, same
data. (This is why Option A is the default: the drill becomes a no-op.)

**Drill B — a live run hangs or errors.**
Don't debug on stage. The four committed suite runs are permanently
available in the Eval Dashboard's run list — open
`run_nvda_fy26q1_20260704_110357_439805` (memory) or
`run_smci_case3_20260704_105922_28a79f` (base) and continue from Beat 2.
The trace/dashboard/leaderboard beats never depend on the live click.

**Drill C — backend won't start.**
`backend/.venv/Scripts/python -m pytest -q` from `backend/` to see the
actual error; most likely a wrong working directory (launch from repo root)
or a stale port (`--port 8001` and open :8001 — the SPA is origin-relative).

**Drill D — you reset state and the run list looks empty.**
You deleted committed run dirs. `git status` + `git checkout -- runs/` (they
are tracked files) restores them; `git clean -fd runs/` removes only
untracked ones. The reset recipe above previews with `-nd` first for
exactly this reason.
