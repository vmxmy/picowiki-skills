---
name: multi-agent-prompt-designer
description: Design complete multi-agent collaboration prompts specifically for PicoClaw runtimes, using PicoClaw native mechanisms such as Heartbeat, cron, SubTurn, steering, Continue, EventBus, spawn, and spawn_status. Use when the user wants to turn a goal into a full orchestration prompt with task decomposition, parallel agent roles, tool discovery strategy, phase planning, watchdog rules, tracking artifacts, agent writeback rules, and user notification checkpoints. Triggers include requests like "设计多agent任务", "生成多agent prompt", "把目标拆成并行agent协作", "设计高并发 agent 压测任务", or any request to convert a goal into a runnable PicoClaw mission prompt.
---

# Multi-Agent Prompt Designer

Design one execution-ready prompt for PicoClaw to run.

Do not execute the mission yourself.
Do not output a plan plus commentary by default.
Return a single complete prompt unless the user explicitly asks for rationale.

## PicoClaw-Native Rule

Default to PicoClaw-native orchestration, not a generic multi-agent abstraction.

Unless the user explicitly asks for portability, the prompt you generate should be written to fit PicoClaw's native mechanisms:
- `Heartbeat` for periodic wake-ups and watchdog continuity
- `cron` for lower-frequency scheduled sweeps and audits
- `spawn` / `SubTurn` for child work
- `spawn_status` for runtime observability when available
- `EventBus` events for subturn lifecycle awareness
- `steering` and `Continue()` for re-entry and deferred follow-up
- `InterruptGraceful` / `InterruptHard` semantics for controlled recovery or shutdown

Do not write the prompt as if it were for a generic task queue unless the user explicitly asks for that.

## Core Output Contract

Produce one complete runtime-facing prompt that:
- starts from the user's goal
- decomposes work into agent roles and workstreams
- maximizes safe parallelism within PicoClaw's native SubTurn and heartbeat model
- explicitly plans tool discovery and tool usage
- defines a reconnaissance stage before the full mission when the final task design depends on unknowns
- defines orchestration phases, deadlines, stop conditions, and watchdog behavior
- requires traceable task artifacts in a task folder
- defines final deliverables and user notifications

Default response format:
1. one-line title
2. one fenced code block containing the full prompt

## Mandatory Tracking Contract

Every prompt produced by this skill must require the runtime to create a task folder with traceable execution artifacts.

Unless the user requests otherwise, require these files:
- `SPEC.md`
- `STATUS.json`
- `EXECUTION_LOG.md`
- `RESULTS.tsv`
- `AGENTS/<agent-name>.md`
- `FINAL/report.md`

### `SPEC.md`

Treat `SPEC.md` as the canonical human-readable task decomposition document.
It should contain:
- task title
- objective
- runtime assumptions
- constraints
- final deliverable definition
- orchestration topology
- phase plan
- agent roster
- task decomposition table
- success criteria
- failure handling rules
- current status summary

Use a task decomposition table like:

| Task ID | Scope | Owner Agent | Depends On | Output | Status |
|---|---|---|---|---|---|

### `RESULTS.tsv`

Treat `RESULTS.tsv` as the canonical compact decision ledger for attempts and outcomes.
Use it to separate decision-grade records from narrative logs.

It should usually contain columns such as:
- `timestamp`
- `agent`
- `task_id`
- `attempt`
- `status`
- `keep_or_discard`
- `artifact`
- `summary`

Use `keep_or_discard` to record whether a result advances the mission design or is rejected as noise, dead-end, or failed attempt.

### `STATUS.json`

Treat `STATUS.json` as the canonical machine-readable state board.
It should usually include:
- `task_id`
- `title`
- `started_at`
- `updated_at`
- `current_phase`
- `deadline` when applicable
- `total_agents`
- `queued_count`
- `running_count`
- `done_count`
- `failed_count`
- `timed_out_count`
- `agents` map keyed by agent name

Each agent entry should usually include:
- `status`
- `goal`
- `artifact_path`
- `last_update`
- `summary`
- `restart_count`
- `last_heartbeat` when applicable
- `failure_reason` when applicable

### Concurrency Approval Gate

Every prompt must require an explicit user confirmation of the maximum concurrent agent process count before full execution begins.

The prompt should require the coordinator to:
- inspect runtime constraints and estimate a safe concurrency range
- present the proposed maximum concurrent agent count to the user
- wait for user confirmation before launching the main worker wave
- record the approved limit in `SPEC.md` and `STATUS.json`

Default rule:
- reconnaissance may run with a very small safe starter set if needed
- the full mission must not begin until the user confirms the concurrency cap

### Baseline-First Protocol

When the task is open-ended, high-concurrency, long-running, or source-dependent, require a baseline stage before the main mission.

The baseline stage should:
- establish the initial state of the environment or problem
- test the first viable decomposition
- inspect runtime limits, including safe concurrency
- produce a compact findings package
- update `SPEC.md` before the full mission launches

The baseline should be time-bounded and smaller than the full mission.
Its purpose is to make later orchestration decisions more reliable and comparable.

### Coordinator Watchdog Protocol

Every prompt must require the coordinator or main thread to act as a watchdog.

The watchdog must:
- periodically check global task state and per-agent state
- detect failed, stalled, or non-updating agents
- attempt bounded recovery by restarting affected agents
- keep the task moving until all required work is complete or a hard-stop condition is reached
- prefer runtime-native scheduling such as built-in `cron` and `heartbeat` so watchdog continuity does not depend on a single LLM request staying healthy

Default watchdog behavior to encode into prompts:
- perform a status check on a fixed interval appropriate to the task duration
- run watchdog scheduling through built-in `cron` or `heartbeat` when available
- treat an agent as stalled if it has no meaningful status update within its expected window
- on `failed` or `timed_out`, attempt restart if the agent's work is still required
- on suspected stall, attempt one diagnostic check and then restart if needed
- record every recovery attempt in `EXECUTION_LOG.md` and `STATUS.json`
- increment `restart_count` on each restart

Reliability rule:
- watchdog continuity should not depend on a single LLM call succeeding
- prefer runtime-native periodic wake-up mechanisms to keep watchdog checks alive during provider instability

Recovery should be bounded. The prompt should usually define:
- a per-agent max restart count
- conditions for escalating from retry to task-level failure
- which failures are recoverable versus fatal

### Agent Writeback Protocol

Every prompt must require each agent to write back execution records when it completes meaningful work.

Each agent must:
- update its own `AGENTS/<agent-name>.md`
- append a concise event to `EXECUTION_LOG.md`
- update its status in `STATUS.json`

Each completion record should include:
- timestamp
- agent name
- assigned scope
- tools used
- artifact produced
- outcome: `done` / `failed` / `timed_out`
- concise result summary
- unresolved issues if any
- decision: `advance` / `keep` / `discard` when applicable

Use `advance` or `keep` when the output should shape the next stage.
Use `discard` when the output is a dead-end, duplicate, low-signal result, or failed path that should not guide later decisions.

### User Notification Protocol

Every prompt must require the runtime to notify the user at meaningful checkpoints.

Default notification points:
- task started
- first wave of agents launched
- each phase completed
- major failure cluster or serious bottleneck
- any watchdog escalation to repeated restart or degraded mode
- final report ready

If direct message or notification tools exist, require using them.
Otherwise require the coordinator to emit the best available user-facing update through the active response channel.

### Unrecoverable Failure Protocol

Every prompt must define what to do when the watchdog cannot recover the mission.

Default rule:
- if a required agent or dependency cannot be recovered within the retry budget, stop the task cleanly
- mark the task as failed in `STATUS.json`
- append a clear incident summary to `EXECUTION_LOG.md`
- notify the user with:
  - what failed
  - what recovery attempts were made
  - why the task was stopped
  - concrete next-step suggestions or mitigations

### Completion Rule

A task is not complete unless:
- the final deliverable exists, or the task has been explicitly terminated as unrecoverable
- `SPEC.md` reflects the final decomposition and status
- `STATUS.json` reflects final outcomes
- each completed agent has a writeback record
- the user has been notified of completion or unrecoverable failure

## Optional References

Load these only when they help:
- `references/runtime-patterns.md`
  - Read when choosing a topology such as hub-and-spoke, burst fan-out, monitoring swarm, research pipeline, or coding collaboration.
- `references/prompt-templates.md`
  - Read when drafting the final prompt body and selecting a skeleton that matches the task type.

## Working Method

Think through this workflow before drafting the final prompt.

### 0. Doctor the Environment First

Before planning the full mission, require an environment-doctor pass as the first active step.

The doctor pass should inspect what is actually available locally, especially:
- enabled or reachable MCP capabilities
- installed local CLI tools relevant to the mission
- installed skills that can extend ingestion or execution

For PicoClaw tasks, this doctor pass should be treated as a hard prerequisite before major decomposition decisions.
Do not design the mission as if tools exist until the doctor step confirms they do.

### 1. Normalize the Goal

Extract or infer:
- primary objective
- desired output
- time budget or deadline
- target runtime assumptions
- acceptable risk level
- task type: research, coding, monitoring, synthesis, stress test, or mixed
- whether the task benefits from many narrow agents or fewer broader agents

If some inputs are missing, make the smallest reasonable assumption and encode it clearly inside the prompt.

Exception: do not silently assume the maximum concurrent agent count.
Before the main mission starts, every prompt must require the coordinator to confirm the user-approved maximum concurrent agent process count.
If the user has not specified this limit, the task should stop after setup and ask the user to confirm the concurrency cap before launching the main worker wave.

Also do not silently assume local tools, MCP servers, or installed skills exist.
Require the doctor step to confirm them first.

### 2. Decompose the Work

Split the mission into:
- doctor work to inspect the local environment first
- reconnaissance work needed before the full mission design is safe or specific
- coordination work
- independent parallel workstreams
- validation or contradiction checking
- synthesis and final reporting

If the final mission depends on unknowns such as tool surface, source quality, runtime limits, environment constraints, or competing decomposition options, require a doctor pass first and then a small reconnaissance phase.

Prefer reconnaissance tasks that are:
- small
- fast
- information-dense
- low-risk
- useful for shaping the later full mission

Avoid overlapping agents with vague scopes.

### 3. Design the Agent Topology

Choose the lightest topology that still fits the task.
Default to hub-and-spoke unless the task clearly needs a burst fan-out or staged pipeline.

For topology guidance, read `references/runtime-patterns.md` when useful.

### 4. Plan Tool Discovery Explicitly

### Research-Mission Tooling Rule

When the user's task is a long-running research, monitoring, investment, competitive, or intelligence mission, the prompt should explicitly reason about whether the runtime has enough information-sourcing capability configured to succeed.

For PicoClaw, treat these categories as especially important:
- `web_search` with multiple search providers for cross-checking
- `web_fetch` for reading full source content
- `heartbeat` and `cron` for long-task continuity
- `spawn_status` for observability of child work
- `send_file` for final report delivery
- `exec` for local transformation, dedup, and report assembly when appropriate
- `MCP` for specialist external capabilities and data sources
- `skills` and `find_skills` for platform-specific or domain-specific ingestion when built-ins are insufficient

For general Web search and fetch, treat PicoClaw built-ins as the default first-line source layer.
The prompt should prefer:
- multiple search engines for cross-checking
- `web_fetch` for full-page reading instead of relying only on snippets
- markdown-friendly fetch output when the mission benefits from structured notes
- explicit source-quality comparisons before trusting a search provider as the main source backbone

If the user wants source classes such as X/Twitter, Reddit, YouTube, Wiki/Wikipedia, market data, or filing databases, do not assume PicoClaw has first-class built-ins for all of them.
The prompt should require reconnaissance to determine whether these sources are available via:
- built-in web tools
- MCP servers
- installed skills
- fallback public-web fetching

For X/Twitter specifically, support these access modes when available:
- browser mode: local browser cookie extraction from a logged-in profile
- cookie injection mode: explicit `auth_token` + `ct0` passed to the X client or wrapper
- Linux/headless preference: if the runtime is Linux, remote, or headless, prefer cookie injection over browser extraction

If the environment uses `bird` as the X client, treat its official site as `https://bird.fast/`.
The prompt should require the coordinator to check which X mode is available and choose the most stable one for the environment.

For YouTube specifically, prefer `yt-dlp` when the environment exposes it, and treat its official source as `https://github.com/yt-dlp/yt-dlp`.
Use it as a specialized ingestion path for:
- video metadata
- channel / playlist extraction
- subtitle or transcript retrieval when available
- long-form source capture before summarization

For Linux or headless environments, `yt-dlp` should generally be treated as a strong default YouTube access path because it does not depend on an interactive browser session in the same way browser-driven extraction does.
The prompt should require reconnaissance to determine whether `yt-dlp` is present and whether the task needs plain metadata, subtitles, transcripts, playlists, or media-adjacent artifacts.

For general Web search, the prompt should require reconnaissance to determine:
- which built-in search providers are enabled
- whether at least two different provider styles are available for cross-checking
- whether `web_fetch` is enabled and configured for useful output
- whether provider-native search should be preferred or overridden
- whether the current Web stack is sufficient, or whether MCP / skills are needed to fill source gaps

Never assume agents will magically know which tools to use.
The prompt must explicitly tell the runtime to:
- inspect available tools first
- prefer PicoClaw built-ins before workarounds
- use `spawn` / `SubTurn` for child work instead of inventing an external worker model
- use `spawn_status` when available for observability
- use multiple search providers when the task depends on current external information and source cross-checking
- use `web_fetch` for full-source reading, preferably in markdown-friendly form when the task benefits from structured notes
- use file tools for persistent artifacts and checkpoints
- use `Heartbeat` and `cron` for watchdog continuity and scheduled checks when available
- discover additional tools only when needed
- check whether specialist information sources are available through MCP or skills when built-ins are insufficient
- avoid redundant full-surface tool discovery across all agents

### 5. Maximize Parallelism Safely

Parallelize:
- independent source collection
- independent domain analysis
- independent verification passes
- broad monitoring coverage

Do not parallelize:
- work that depends on the same evolving artifact without ownership
- final synthesis before enough evidence exists
- conflicting writes to the same file unless ownership is explicit

Use a bounded mutation surface.
Explicitly limit which artifacts each agent may write.
Default rule:
- child workers spawned through PicoClaw write to their own `AGENTS/<agent-name>.md` and scoped artifacts
- only the coordinator or designated merger updates shared top-level documents such as `SPEC.md`, `STATUS.json`, `RESULTS.tsv`, and final synthesis artifacts
- if workers must write shared artifacts, ownership must be explicit and non-overlapping
- coordinator recovery logic should prefer PicoClaw-native control paths such as heartbeat ticks, steering, `Continue()`, and interrupt semantics before inventing external control channels

When useful, assign for each agent:
- purpose
- scope
- key questions
- expected artifact
- handoff target
- time budget
- allowed write targets

### 6. Force Convergence

Every prompt must define:
- phase boundaries
- reconnaissance completion criteria when reconnaissance is included
- stop conditions
- timeout behavior
- partial-failure behavior
- final synthesis deadline

Default rule:
- reconnaissance should end with a short findings package that informs the full mission design
- partial failure must not block final output unless the failed reconnaissance item was a hard dependency
- unresolved conflicts must be surfaced explicitly in the final report

## Reconnaissance-First Rule

Before designing a full mission, ask whether the runtime needs fresh information to design the mission well.

Use a reconnaissance stage when any of these are true:
- the tool surface is unknown or likely large
- the environment may impose limits such as concurrency, network, time, or permissions
- source quality or coverage is unclear
- the user wants a high-concurrency or long-running mission
- the full task depends on choosing between several decompositions

When reconnaissance is needed, the final prompt should first create several small research tasks whose only goal is to collect design-shaping information for the later full mission.

These reconnaissance tasks should usually answer questions like:
- what local CLI tools are actually available
- what installed skills are actually available
- what MCP capabilities are enabled, reachable, or missing
- what runtime constraints exist
- what sources are high quality versus noisy
- which information-source classes are actually reachable in this runtime
- for X/Twitter, whether access is available through browser extraction or explicit cookie injection
- for YouTube, whether `yt-dlp` or another transcript/content path is available
- whether current-source coverage is enough for the mission or needs MCP / skills expansion
- what decomposition seems most independent
- what failure modes are likely
- what monitoring and restart policy will be needed
- whether built-in `cron` and `heartbeat` are available for watchdog continuity
- what baseline should be established before the main mission

The prompt should require the coordinator to synthesize reconnaissance results into `SPEC.md` before launching the full mission.
It should also require explicit `advance` / `discard` decisions on candidate sources, decompositions, and strategies.

## Prompt Construction Rules

The final prompt should usually contain these sections in order:
1. task title
2. mission or goal
3. PicoClaw runtime assumptions
4. execution principles
5. task folder and tracking requirements
6. doctor step for local MCP / CLI / skills
7. reconnaissance stage, if needed
8. PicoClaw orchestration structure
9. agent roster
10. phase plan
11. PicoClaw-native tool discovery and tool use policy
12. status tracking and writeback rules
13. watchdog, recovery, and convergence rules
14. output format requirements
15. immediate start instructions

Scale the level of detail to the task complexity.
For most prompts, read `references/prompt-templates.md` before drafting.

## Agent Roster Rules

For each agent, define:
- name
- purpose
- scope
- key questions
- expected artifact
- handoff target

Prefer distinct names that match the evidence domain or responsibility.
Good examples:
- `coordinator-agent`
- `tool-scout-agent`
- `source-scout-agent`
- `skeptic-agent`
- `synthesizer-agent`

Avoid generic labels unless the task is purely quantitative fan-out.

## Output Quality Bar

Before finalizing, check:
- Does the prompt clearly decompose the goal?
- Does it use parallel agents only where independence exists?
- Does it make tool discovery explicit?
- Does it define the task folder and tracking artifacts?
- Does it require `RESULTS.tsv` or an equivalent compact decision ledger?
- Does it require a first-step doctor pass for local MCP / CLI / skills?
- Does it require per-agent writeback?
- Does it require user notification?
- Does it define a baseline stage when needed?
- Does it require explicit user confirmation of max concurrent agents before execution?
- Does it prefer PicoClaw-native `cron` / `heartbeat` for watchdog continuity when available?
- Does it use PicoClaw-native control paths such as `spawn`, `SubTurn`, `spawn_status`, `steering`, `Continue()`, and interrupt semantics where relevant?
- Does it define `advance` / `discard` decisions where useful?
- Does it define a bounded mutation surface?
- Does it define convergence and deadlines?
- Does it specify the final deliverable?
- Could PicoClaw start immediately from this prompt without major reinterpretation?

If not, tighten the prompt before returning it.
