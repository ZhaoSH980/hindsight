# Design decisions

Why Hindsight is built the way it is. Each section states the decision, the
alternatives considered, and the reason the alternative lost.

## 1. Reasoning pattern: bounded ReAct inside a deterministic pipeline

**Decision.** The system is a hybrid, not a single named pattern:

- The outer orchestration (Planner → Researcher → Analyst → Critic) is a
  **deterministic state machine**. The LLM's freedom is confined to individual
  decisions inside each stage.
- The Planner runs a **bounded ReAct loop** (Thought → Action → Observation,
  max 8 steps).
- The Critic implements **self-refine**: validation failures go back to the
  Analyst with concrete feedback (max 2 retries).
- The experience library is a **cross-run Reflexion**: graded lessons are
  persisted and retrieved into future runs — gated by the same time sandbox
  as every other information channel.

**Why ReAct for the research planner.**

1. *Task shape.* Research is exploratory: what to look up next depends on what
   the last lookup returned. A pattern that commits to a full plan upfront
   fights the nature of the task.
2. *Evaluability.* Every ReAct step emits an explicit Thought — which is
   exactly the trace event our flight recorder, failure attribution, and
   step-by-step replay are built on. ReAct is the only common pattern that
   leaves a "why" at every step, which is the property this whole project is
   about.
3. *Cost.* Search-based patterns multiply LLM calls per step; our quota is
   metered per call.
4. *Reproducibility.* The record/replay layer requires a deterministic call
   sequence for a fixed input.

**Alternatives considered.**

| Pattern | Why it lost |
|---|---|
| Plan-and-Execute | Upfront commitment breaks on surprises; research findings routinely invalidate the initial plan. Replanning layers add complexity without adding observability. |
| Tree of Thoughts / LATS | Token cost explodes (N branches per step on a per-call quota); branch trees are hard to replay deterministically and hard to grade. Overkill for retrieval-and-synthesis. |
| Free-form multi-agent chat (AutoGen-style group chat) | Non-deterministic turn order makes record/replay and config-vs-config comparison impossible. Cost is unbounded. Debugging is archaeology. |
| Single-shot CoT | No tool access — cannot do research at all. Useful only as a contamination probe (we do use it for that). |

## 2. Multi-agent split: three LLM roles + one deliberately deterministic stage

Three LLM roles (Planner / Analyst / Critic) share one LLM backend and
differ only in system prompt and tool allowlist. The Researcher stage is
**deliberately not an LLM**: it is a deterministic `EvidenceManager` (its
own docstring says so) that executes the planner's retrieval decisions and
normalizes the evidence pool. This is the stronger version of the split,
not a compromise — retrieval is the one stage whose job is mechanical
(fetch, dedupe, stamp through the sandbox gate), so making it deterministic
buys reproducibility and removes a whole class of "the researcher
paraphrased the source" failure modes for free. Whether retrieval was
*sufficient* is still judged — by the evaluation judge's
`retrieval_sufficiency` score — rather than by burning an LLM role on
narrating its own retrieval. The split is by **failure mode**, not by
anthropomorphism:

- Planner owns *direction* errors (researching the wrong thing),
- the Researcher stage owns *retrieval* errors (missing sources — surfaced
  by `retrieval_sufficiency` and `evidence_missing`, since the
  deterministic stage itself cannot misread anything),
- Analyst owns *synthesis* errors (claims not supported by evidence),
- Critic owns *format and consistency* errors.

This maps one-to-one onto the failure-attribution enum used by the evaluation
judge (`evidence_missing` / `misread_evidence` / `reasonable_but_wrong`),
so "why did this run fail" has a structural answer, not just a narrative one.

## 3. No agent framework (LangChain / LangGraph / AutoGen / CrewAI / ...)

The agent loop, tool registry, and orchestration are hand-written
(~a few hundred lines). Reasons:

1. *The differentiation lives in the middleware.* Hindsight's value is the
   time sandbox, the record/replay layer, the trace ledger, and the
   evaluation loop — all cross-cutting concerns that sit **between** the LLM
   call and the tool call. Framework abstractions sit exactly there and get
   in the way; owning the call chain outright is simpler than fighting
   callback APIs.
2. *Deterministic replay.* Replay keys on a hash of the fully-constructed
   request. Frameworks rewrite prompt templates across versions, silently
   invalidating the replay cache.
3. *Auditability.* For an evaluation-driven project, every line between input
   and output should be explainable. A framework would add a dependency tree
   we can't vouch for, to solve orchestration problems we don't have.

This is not a general argument against frameworks — for a product team
shipping many agents, LangGraph's checkpointing or the OpenAI/Claude agent
SDKs are reasonable defaults. It is an argument about *this* project: the
loop is not the hard part here; the instrumentation around it is.

## 4. Native function calling vs prompt-embedded JSON actions

Decided empirically by a Day-1 endpoint probe against the deployment target
(xf-yun MaaS, `astron-code-latest`): if the endpoint supports OpenAI
`tools/tool_choice` semantics reliably, the Planner uses native function
calling; otherwise it falls back to a prompt-embedded JSON action format.
The tool registry and trace protocol are identical in both modes — only the
adapter layer switches. (Result of the probe: recorded in eval-log.)

## 5. Determinism over autonomy

A recurring theme in the choices above: whenever autonomy and observability
conflicted, we chose observability. The JD this project was built against
says it best — the interesting question is not whether an agent can run, but
"how well it performs, why it behaves as it does, and how it can continue to
improve over time". Every mechanism in Hindsight (sandbox audit logs,
structured claims, three-track scores, failure attribution, experience
generations) exists to make one of those three questions answerable with
data instead of anecdotes.
