# Runtime Patterns

Use this file when choosing the orchestration topology for a PicoClaw/Nanobot-style runtime.

## Doctor-First Pattern

Use this pattern at the start of nearly all PicoClaw missions.

### Rule
Before major decomposition, inspect the local environment and record what is actually available.

### At minimum, check
- reachable MCP servers or configured MCP capabilities
- installed CLI tools relevant to the mission
- installed skills relevant to the mission
- whether built-in `heartbeat`, `cron`, `spawn_status`, and core web tools are enabled

### Output
The doctor step should update `SPEC.md` and `STATUS.json` with a concise capability inventory before the main mission design is finalized.

## PicoClaw Native Building Blocks

Prefer composing missions from PicoClaw's native primitives instead of inventing a generic scheduler model.

Primary building blocks:
- `HeartbeatService` for periodic wake-up
- `cron` for scheduled sweeps and lower-frequency checks
- `spawn` / `SubTurn` for child work
- `spawn_status` for subagent visibility when available
- `EventBus` for lifecycle observability
- `steering` and `Continue()` for re-entry after deferred or queued follow-up
- `InterruptGraceful` and `InterruptHard` for controlled interruption

Design missions so these primitives do the work directly.
Only invent extra abstraction layers when PicoClaw cannot express the needed behavior natively.

## Selection Guide

Choose the lightest pattern that can still solve the task well.

| Pattern | Best for | Avoid when |
|---|---|---|
| Hub-and-spoke | Most tasks with one clear coordinator | Workers depend heavily on each other's intermediate output |
| Layered pipeline | Research, coding, validation, staged synthesis | The task needs very fast fan-out and loose coupling |
| Burst fan-out | Monitoring, market watch, broad search, stress tests | The work requires deep shared context |
| Dual-track | Contested topics, policy analysis, high uncertainty | Evidence is already narrow and clean |
| Map-reduce | Large repeated source sets with one extraction schema | Each item needs deep bespoke reasoning |

Default choice: hub-and-spoke.

## 1. Hub-and-Spoke

### Shape
- 1 coordinator
- N specialized workers
- optional verifier
- optional synthesizer

### Use when
- The user gives one main goal
- Most workstreams are independent
- You want simple orchestration with strong convergence

### Strengths
- Easy to explain
- Easy to monitor
- Good balance between parallelism and control

### Risks
- Coordinator becomes overloaded
- Workers drift into overlapping scopes unless roles are sharp

### Design rule
Give each worker a distinct evidence domain or decision question.

## 2. Layered Pipeline

### Shape
- discovery agents
- analysis agents
- validation agents
- synthesis agent

### Use when
- The task naturally has stages
- Later work depends on earlier evidence
- You need explicit quality gates

### Strengths
- Produces cleaner outputs
- Easier to control quality
- Good for coding, research, and audit flows

### Risks
- Less parallel than burst fan-out
- Can bottleneck at stage transitions

### Design rule
Define exact handoff artifacts between stages.
Examples:
- discovery -> source list
- analysis -> findings table
- validation -> contradiction log
- synthesis -> final brief

## 3. Burst Fan-Out

### Shape
- 1 coordinator
- many narrow scouts
- 1-3 merger agents
- optional critic

### Use when
- Coverage matters more than depth at first
- Time budget is short
- The task benefits from many narrow parallel probes

### Strengths
- Maximizes breadth quickly
- Good for time-boxed search and monitoring
- Good for stress testing parallel runtimes

### Risks
- Duplicate work
- Shallow findings
- High merge pressure
- Easy to overwhelm synthesis

### Design rule
Workers must be narrow, not generic.
Good:
- `oil-agent`
- `vix-agent`
- `china-adr-agent`

Bad:
- `market-agent-1`
- `market-agent-2`

## 4. Dual-Track

### Shape
- evidence-gathering track
- contradiction or skeptic track
- reconciler

### Use when
- The domain is noisy or contested
- False consensus is dangerous
- The user wants a strong argument, not just broad coverage

### Strengths
- Surfaces uncertainty
- Reduces hallucinated consensus
- Better for strategy, macro, and policy topics

### Risks
- Can overcomplicate simple tasks
- Final synthesis must actively reconcile differences

### Design rule
Require the final report to preserve unresolved conflicts instead of flattening them.

## 5. Map-Reduce

### Shape
- many mappers process units independently
- reducers merge structured outputs
- final summarizer produces narrative

### Use when
- The task has many repeated items
- Each item can use the same extraction schema
- You need consistency across many artifacts

### Strengths
- Highly scalable
- Easy to standardize
- Good for large corpora

### Risks
- Can feel mechanical
- Poor fit for ambiguous exploratory reasoning

### Design rule
Use a strict per-item output schema.

## Concurrency Approval Pattern

Use this overlay when the PicoClaw mission may fan out into many subagents or when runtime capacity is uncertain.

### Rule
- reconnaissance may estimate a safe concurrency range
- coordinator must ask the user to confirm the maximum concurrent agent process count
- the main worker wave must not start until the user confirms that cap

### Why
- prevents silent overload
- aligns runtime behavior with user risk tolerance
- makes later failures easier to interpret

## Watchdog Coordinator Pattern

Use this overlay when a PicoClaw mission is long-running, high-concurrency, or operationally fragile.

### Shape
- coordinator with watchdog duties
- many workers
- optional merger or synthesizer

### Watchdog duties
- poll global and per-agent status on an interval
- detect failures, stalls, and missing heartbeats
- restart recoverable agents within a bounded retry budget
- escalate unrecoverable faults to task termination
- notify the user on recovery actions and fatal stops
- prefer runtime-native schedulers such as built-in `cron` and `heartbeat` so the watchdog continues during LLM provider instability

### Use when
- the task is time-boxed but long enough for stalls to matter
- the runtime may queue, hang, or partially fail under load
- user trust depends on visible recovery behavior

### Design rule
Make restart policy explicit: interval, stall threshold, max restarts, fatal conditions, and user notification behavior.

### Scheduling rule
If the runtime exposes built-in `cron` or `heartbeat`, use them as the primary watchdog tick source.
Treat direct LLM-driven self-checks as secondary, not primary.


## Baseline-and-Decision Loop

Borrow this pattern when the mission should improve after an initial probe.

### Shape
- small baseline stage
- one or more candidate decompositions or source strategies
- explicit `advance` / `discard` decision
- full mission after the winning baseline

### Use when
- the domain is noisy
- source quality is uncertain
- decomposition quality matters to final performance
- the mission is expensive enough that a bad first design would waste time

### Design rule
Require the coordinator to record which candidate paths are kept and which are discarded.
Do not let every early finding automatically shape the full mission.

## Bounded Mutation Surface

Use this overlay when many agents may otherwise collide on shared artifacts.

### Rule
- workers write only to scoped files
- shared planning and state artifacts are updated only by the coordinator or designated merger
- final synthesis files have explicit ownership

### Use when
- the mission has many agents
- auditability matters
- restart and recovery logic depend on clean ownership

## Research Source Coverage Pattern

Use this overlay for long-running research, market, investment, competitive, or intelligence tasks.

### Rule
Before trusting the mission design, confirm which information-source classes are actually covered in the current PicoClaw environment.
General Web search and full-page fetch should be treated as the baseline source layer that all other specialized sources build on.

### General Web access rule
Treat general Web search + fetch as the default evidence layer.

Preferred pattern:
1. use at least two search providers when source quality matters
2. fetch the full page for important results instead of trusting snippets
3. prefer markdown/plaintext output that can be archived and summarized
4. use specialist sources only after the baseline Web layer is understood

Validation rule:
Require a quick live check of both search and fetch before marking the Web layer as healthy.

### Important source classes
- general web search
- full-page fetch
- company IR and official docs
- X/Twitter
- Reddit
- YouTube / transcripts
- Wiki / Wikipedia / explainer sources
- market data / filings / specialist data providers

### X/Twitter access rule
Treat X/Twitter as a specialized source class.
Do not assume first-class PicoClaw support.
Map it explicitly to one of these access modes:
1. browser cookie extraction
2. explicit cookie injection (`auth_token` + `ct0`)
3. other skill- or MCP-backed wrapper

If the chosen wrapper is `bird`, treat `https://bird.fast/` as the official source for the tool.

Preferred order:
- on Linux or headless environments: explicit cookie injection first
- on interactive desktop environments: browser extraction is acceptable if already verified

Validation rule:
Require a minimal live check such as account identification or a simple search/read before marking X as available.

### YouTube access rule
Treat YouTube as a specialized source class.
Do not assume first-class PicoClaw support.
Map it explicitly to one of these access modes:
1. `yt-dlp` local CLI
2. transcript- or media-oriented MCP wrapper
3. installed skill for transcript or content extraction
4. fallback web methods

If the chosen tool is `yt-dlp`, treat `https://github.com/yt-dlp/yt-dlp` as the official source.

Preferred order:
- on Linux or headless environments: `yt-dlp` first
- on interactive environments: `yt-dlp` is still preferred for deterministic extraction; browser methods are secondary

Validation rule:
Require a minimal live check appropriate to the task, such as metadata extraction, subtitle availability, playlist listing, or transcript-oriented retrieval before marking YouTube as available.

### Preferred sourcing order
1. PicoClaw built-in web search + fetch
2. MCP-backed specialist sources
3. installed skills for site- or domain-specific ingestion
4. fallback public web methods

### Design rule
Do not assume every desired source class is first-class in PicoClaw.
Require reconnaissance to map desired sources to actual mechanisms.

## Tool Discovery Patterns

### Pattern A: Shared Tool Scout
One agent inspects available tools and publishes a short tool map.
Best when the runtime has many tools or the surface is unfamiliar.
Risk: becomes a bottleneck if overused.

### Pattern B: Local Tool Discovery
Each worker discovers its own tools based on scope.
Best when scopes are very different and speed matters.
Risk: duplicated discovery effort.

### Pattern C: Hybrid
One tool-scout maps the main surface, while workers discover extras locally if needed.
Default recommendation: hybrid.

## Reconnaissance Swarm

Use this pattern before the full PicoClaw mission when design quality depends on fresh runtime or source information.

### Shape
- 1 coordinator
- 3-8 small reconnaissance agents
- 1 synthesis step that updates the main spec

### Use when
- you do not yet know which tools or sources are best
- runtime constraints may change the mission design
- the user wants a large stress test or long mission and you need safer defaults first

### Typical reconnaissance tasks
- tool-surface scout
- runtime-limits scout
- source-quality scout
- decomposition-options scout
- failure-mode scout
### PicoClaw-specific reconnaissance questions
- which built-in tools are actually enabled
- whether `heartbeat`, `cron`, `spawn_status`, and required channels are available
- what safe SubTurn concurrency appears realistic
- whether steering / Continue can be used for deferred recovery
- which event signals are available for watchdog logic


### Output
The reconnaissance stage should produce a short findings package that updates `SPEC.md` and shapes the later full mission.

### Design rule
Do not let reconnaissance sprawl. Keep it short, bounded, and explicitly upstream of the main mission.

## Agent Count Heuristics

| Task type | Suggested count |
|---|---|
| Small focused task | 3-5 agents |
| Normal research or coding task | 5-10 agents |
| Broad monitoring task | 10-20 agents |
| Stress test or burst coverage | 20-50+ agents |

Only increase agent count when the decomposition creates real independence.

## Convergence Rules

Every prompt should define:
- phase transitions
- stop conditions
- timeout behavior
- partial-failure behavior
- final synthesis deadline

For burst tasks:
- force convergence before the deadline
- allow unfinished workers to be excluded if needed
- require explicit reporting of missing coverage

## Anti-Patterns

Avoid:
- too many generic agents with overlapping scopes
- no explicit synthesis stage
- no deadline or convergence rule
- conflicting writes to the same artifact without ownership
- leaving tool discovery entirely implicit
- no skeptic or verification pass in noisy domains
