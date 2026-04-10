---
name: harness-setup
description: Use when starting a new autonomous long-task experiment session — any workflow where an AI agent will run iterative experiments unattended for an extended period. Covers: agreeing on a session tag, creating a branch, reading all in-scope files, verifying prerequisites, initializing the results log, and getting one human confirmation before handing off to the loop. Trigger on phrases like "kick off a new run", "start a new experiment session", "set up harness", "initialize research session", "let's start experimenting", or "set up a new autoresearch run". Use this skill proactively whenever a session needs to be bootstrapped from scratch.
---

# Harness Setup

This skill covers the **one-time setup** before the experiment loop starts. It is designed for autonomous long-running sessions where a human may not be present once the loop begins. Getting setup right matters — a bad baseline or missing data causes silent failures hours later.

## Step 1 — Agree on session tag

Propose a short tag based on today's date and domain (e.g. `apr10`, `ml-apr10`, `run-b`).

Check the tag is unused:
```bash
git branch -a | grep <tag>
```
If it exists, propose a variant (`apr10b`, `apr10-2`). Confirm with user.

## Step 2 — Create branch

```bash
git checkout -b <namespace>/<tag>
```

The namespace comes from the PROGRAM file (e.g. `autoresearch/apr10`). If not specified, use `runs/<tag>`.

## Step 3 — Read all in-scope files

Read in this order, without skipping:

1. **PROGRAM file** — the agent's research instructions (e.g. `program.md`). Understand: goals, constraints, editable zone, oracle location, run command, metric key, budget.
2. **Oracle file** — read-only. Extract: fixed constants (time budget, sequence length, vocab size), evaluation function signature, metric extraction pattern.
3. **Editable zone** — current state. This becomes the baseline you're trying to beat.

If you're unsure which file is which, look for the pattern: *one file defines what to measure and how; another file is the thing being measured*.

## Step 4 — Verify prerequisites

Check that required runtime artifacts exist:
- Cached datasets / model weights
- Pre-built tokenizer / index
- Any output of a one-time `prepare` or `setup` script

```bash
ls <expected_cache_dir>
```

**If prerequisites are missing: stop. Tell the human exactly what command to run. Do not proceed to the loop.**

## Step 5 — Initialize results log

```bash
printf "commit\t<metric_field>\t<resource_field>\tstatus\tdescription\n" > results.tsv
```

Replace `<metric_field>` and `<resource_field>` with the actual field names from the oracle (e.g. `val_bpb`, `memory_gb`).

**Do NOT `git add results.tsv`.** It stays untracked for the entire session.

## Step 6 — Confirm and go

Summarize for the human:
- Branch name
- Baseline state (brief description of current editable zone)
- Prerequisites: ✓ present / ✗ missing
- Run command and metric extraction pattern
- What "keep" vs "discard" means for this session

Wait for one human acknowledgment. Then hand off to `harness-loop`.

**After this ack, never pause for human input again unless the loop explicitly fails to recover.**
