---
name: harness-decide
description: Use when deciding whether to keep or discard an experiment result in an autonomous harness loop. Applies the simplicity criterion alongside metric comparison to make the keep/discard/crash call. Trigger on "should I keep this?", "was that an improvement?", "keep or revert?", "advancement decision", or as part of any harness experiment loop iteration. Use this skill whenever evaluating whether a change to an editable artifact should be retained based on a measured metric outcome.
---

# Harness Advancement Decision

This skill governs the **keep vs. discard decision** after each experiment run. The goal is not to blindly maximize the primary metric — it's to advance toward the best achievable result while keeping the code understandable and maintainable.

## Primary rule

| Metric outcome | Default decision |
|----------------|-----------------|
| Strictly **improved** | `keep` |
| Equal or **worse** | `discard` → `git reset --hard HEAD~1` |

## Simplicity criterion (applied before finalizing)

The metric alone doesn't tell the full story. Before committing to `keep` or `discard`, weigh complexity cost against improvement magnitude.

### When to override "keep"

If the metric improved but the change added significant complexity (more lines, harder to read, more fragile), ask: *is this improvement large enough to justify the added weight?*

A rough heuristic: if removing the change later would take more than 5 minutes of careful surgery, the improvement needs to be meaningful to justify it.

### When to override "discard" (simplification wins)

If the metric is **flat or marginally worse** but the change **simplifies the code** (removes lines, deletes a component, clarifies intent), this is a **simplification win** — keep it.

Rationale: simpler code is easier to iterate on in future experiments. A slightly worse metric from cleaner code is often worth more than the metric difference suggests.

### Decision matrix

| Metric | Complexity delta | Decision |
|--------|-----------------|----------|
| Improved significantly | Low or neutral | `keep` |
| Improved significantly | High (messy) | `keep` — but note complexity debt |
| Improved marginally | High (messy) | `discard` — not worth it |
| Improved marginally | Low | `keep` |
| Flat | Code simpler | `keep` — simplification win |
| Flat | No change | `discard` |
| Flat | Code more complex | `discard` |
| Worse | Any | `discard` |
| Crash / no output | — | `crash` → reset |

### What "significant" vs "marginal" means

This is domain-specific and should be defined in the PROGRAM file. If not specified, use judgment calibrated to recent history:

- If recent experiments moved the metric by ~0.005, then 0.001 is marginal and 0.01 is significant.
- If all runs move the metric by < 0.001, recalibrate expectations.

When in doubt: a change that improves the metric while deleting code is almost always worth keeping. A change that worsens the metric while adding 20 lines of hacky code is almost never worth keeping.

## After deciding

**Keep:**
```bash
# Stay on current commit. Update results.tsv status to "keep".
# Note in description if complexity debt was incurred.
```

**Discard:**
```bash
git reset --hard HEAD~1
# Verify you're back on the right commit:
git log --oneline -3
# Update results.tsv status to "discard".
```

**Crash:**
```bash
git reset --hard HEAD~1
# Update results.tsv: metric=0.000000, resource=0.0, status=crash
```

## Recording the decision

Always record an honest description in `results.tsv`. Future-you (or the human reviewing results) will appreciate knowing *why* a change was kept or discarded — not just that it was.

Good descriptions:
- `increase LR 0.04→0.06, faster convergence`
- `remove value embeddings, equal perf simpler code`
- `double depth, OOM on H100`
- `switch to GeLU, val_bpb worse by 0.003`
