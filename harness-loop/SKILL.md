---
name: harness-loop
description: Use during autonomous long-task experiment sessions to run the core iteration loop. Implements the full cycle: inspect state → formulate hypothesis → modify editable zone → commit → execute → extract metric → log → advance or revert. Trigger on "run experiments", "start the loop", "begin iterating", "keep experimenting", "continue the research session", "run the harness", or any request to autonomously iterate on a task with a measurable metric. Use this skill proactively whenever an experiment loop needs to run. NEVER pause mid-loop to ask the human for direction — only stop if recovery fails completely.
---

# Harness Loop

This skill runs the **core experiment loop** for autonomous long-task sessions. Once started, it runs forever until the human manually stops it. The invariant: every iteration is fully executed, measured, and decided upon — no partial iterations, no asking for human approval mid-run.

## The Loop

### 1. Inspect current state

```bash
git log --oneline -5
git status
```

Know exactly which commit you're on before touching anything. If you're recovering from a previous session, also glance at `results.tsv` to understand where you left off.

### 2. Formulate one hypothesis

Pick one change to make to the editable zone. Be specific: "increase learning rate from 0.04 to 0.06" is a hypothesis. "try some optimizer changes" is not.

**If you feel stuck**, in order:
1. Re-read the PROGRAM file — often the answer is there
2. Review `results.tsv` for near-misses (discarded runs that were close to improving)
3. Try combining two near-miss ideas
4. Try a more structural change (architecture, not hyperparameters)
5. Try something deliberately contrarian — undo an assumption that seemed obvious

**Running out of ideas is not a stopping condition.** Think harder.

### 3. Modify editable zone

Edit only the designated editable artifact. No new imports beyond declared dependencies. Oracle files and PROGRAM files are never touched.

### 4. Commit before running

```bash
git add <editable-file>
git commit -m "<type>: <one-line description of the hypothesis>"
```

Commit **before** running. This is non-negotiable — every executed state must be uniquely addressable in history. If the run crashes, you can always inspect what was running.

### 5. Execute and capture

```bash
<run_command> > run.log 2>&1
```

Never: `tee`, piped output to the terminal, or anything that lets output flood your context. The full log goes to `run.log`. You read back only what you need.

If the run appears to hang beyond `2× expected budget`, kill it:
```bash
kill <pid>   # or Ctrl+C if running synchronously
```
Treat as a crash.

### 6. Extract results

```bash
grep "^<metric_key>:\|^<resource_key>:" run.log
```

These two field names come from the oracle (established during setup). **If this grep returns nothing → crash handler.**

### 7. Crash handler

```bash
tail -n 50 run.log   # read the stack trace
```

Triage:
- **Trivial fix** (typo, missing import, wrong variable name): fix in editable zone, amend or create a new commit, re-run. Max 2 retries.
- **Fundamental problem** (OOM, architecture broken): log as crash, reset, move to next hypothesis.
- **Timeout**: log as crash, reset, move on.

After more than 2 failed retries on the same idea: give up on that idea. Log it, reset, try something different.

### 8. Log to results.tsv

```bash
printf "<commit7>\t<metric>\t<resource>\t<status>\t<description>\n" >> results.tsv
```

| Field | Format | Crash value |
|-------|--------|-------------|
| commit | 7-char git hash | — |
| metric | e.g. `0.997900` (6 decimals) | `0.000000` |
| resource | e.g. `44.0` (GB to 1 decimal) | `0.0` |
| status | `keep` / `discard` / `crash` | `crash` |
| description | plain text, no tabs | short note |

Use **tab separators, not commas**. Commas appear inside descriptions.

### 9. Advance or revert

See the `harness-decide` skill for the full decision logic. Short version:

- Metric improved → `keep` (stay on this commit)
- Metric equal or worse → `discard` (`git reset --hard HEAD~1`)
- But always apply the simplicity criterion before deciding

After a reset, verify you're back where you should be:
```bash
git log --oneline -3
```

### 10. Go to Step 1

No pause. No check-in. No "should I continue?" The human is likely not watching. Keep going.
