# LLM Wiki Excellence Task List

This document is the execution checklist for making the `llm-wiki` skill robust, stateful, and reliable for an Obsidian-root-plus-sub-wiki workflow.

## Objective

Make `llm-wiki` excellent at four things:

1. remembering the user's canonical Obsidian root
2. remembering the currently selected sub-wiki
3. keeping memory, state files, and runtime registry in sync
4. helping future agents recover the right wiki context without ambiguity

## Priority 0: Must Not Regress

- [ ] Never treat the remembered Obsidian root container as the active wiki unless it also has real wiki markers
- [ ] Never silently switch the selected sub-wiki if one is already remembered
- [ ] Never report success for `use this root` or `use this wiki` unless both durable memory and local state files were updated
- [ ] Never create a parallel wiki structure when an existing valid sub-wiki already exists

## Priority 1: Persistence Contract

### 1.1 Explicit Root Setting

- [x] On user instructions like `use this root` or `remember this root`, write the root path to durable memory
- [x] On the same turn, write the root path to `~/.hermes/state/llm-wiki/wiki-root-path.txt`
- [x] Read the state file back immediately and verify it matches the intended root path
- [x] Refresh the runtime registry after the write succeeds
- [x] Append a `set-root` event to `runtime/wiki-events.log`

### 1.2 Explicit Wiki Setting

- [x] On user instructions like `use this wiki` or `remember this wiki`, write the sub-wiki path to durable memory
- [x] On the same turn, write the sub-wiki path to `~/.hermes/state/llm-wiki/selected-vault-path.txt`
- [x] Read the state file back immediately and verify it matches the intended sub-wiki path
- [x] Refresh the runtime registry after the write succeeds
- [x] Append a `remember-subwiki` event to `runtime/wiki-events.log`

### 1.3 Completion Rule

- [x] Fail the operation if memory succeeds but state file write fails
- [x] Fail the operation if state file write succeeds but memory update fails
- [x] Do not tell the user the root/wiki was saved until both layers are confirmed

## Priority 2: Runtime Registry

### 2.1 Human-Readable Registry

- [x] Maintain `~/.hermes/skills/llm-wiki/runtime/wiki-structure.log.md`
- [x] Include generation time, remembered root, selected sub-wiki, and candidate count
- [x] Include every known sub-wiki with markers and shallow structure listing
- [x] Mark whether each candidate is under the remembered root
- [x] Mark whether each candidate is currently selected

### 2.2 Event Log

- [x] Maintain append-only `~/.hermes/skills/llm-wiki/runtime/wiki-events.log`
- [x] Standardize event types: `detect`, `set-root`, `remember-subwiki`, `init-subwiki`, `refresh-registry`, `forget`, `repair-state`
- [x] Ensure each event includes timestamp and key fields

### 2.3 Machine-Readable Registry

- [x] Add `~/.hermes/skills/llm-wiki/runtime/subwiki-registry.json`
- [x] Include `root_path`, `selected_subwiki`, `candidate_count`, `candidates`, `markers`, `under_root`, `selected`, `last_seen`
- [x] Keep markdown for human reading and JSON for scripts/automation

## Priority 3: Detection Quality

### 3.1 Candidate Discovery

- [x] Search remembered selected sub-wiki first
- [x] Search children of remembered root second
- [x] Search current workspace and likely directories third
- [x] Search Obsidian config and iCloud as fallback sources
- [x] Detect nested `vault/` directories cleanly

### 3.2 Marker Recognition

- [x] Recognize canonical structures: `SCHEMA.md`, `index.md`, `log.md`, `raw/`, `wiki/`
- [x] Recognize non-canonical structures: `CLAUDE.md`, `INDEX.md`, `articles/`, `concepts/`
- [x] Score candidates by marker strength instead of relying only on binary detection
- [ ] Deduplicate mirrored, nested, or symlinked candidates

### 3.3 Selection Policy

- [x] If a valid selected sub-wiki exists, prefer it
- [x] If not, prefer the strongest candidate under the remembered root
- [ ] If multiple strong candidates exist, ask the user instead of guessing
- [x] If no valid candidates exist, offer to initialize a new sub-wiki

## Priority 4: Drift Detection and Repair

### 4.1 Drift Checks

- [ ] Detect when durable memory root differs from `wiki-root-path.txt`
- [ ] Detect when durable memory selected sub-wiki differs from `selected-vault-path.txt`
- [x] Detect when a remembered sub-wiki no longer exists
- [x] Detect when a selected sub-wiki is no longer under the remembered root

### 4.2 Repair Workflow

- [x] Add a repair routine that reconciles memory, state files, and registry
- [ ] Prefer the most recent explicit user instruction during repair
- [x] Append a `repair-state` event when repair happens
- [x] Report what was repaired to the user

## Priority 5: Initialization Workflow

- [x] When initializing a new sub-wiki, create `raw/`, `raw/assets/`, `wiki/sources/`, `wiki/concepts/`, `wiki/entities/`, `wiki/comparisons/`, and `output/`
- [x] Generate `SCHEMA.md`, `index.md`, and `log.md` if missing
- [x] Remember the new sub-wiki as selected unless the user says otherwise
- [x] Remember the parent directory as root if no root exists yet
- [x] Register the new sub-wiki in runtime registry immediately
- [x] Append an `init-subwiki` event

## Priority 6: Health and Doctor Commands

- [x] Add a `--refresh-registry` command that always rebuilds the control-plane snapshot
- [x] Add a `--doctor` command to validate memory/state/registry consistency
- [x] Add a `--show-current` command to print current root, selected sub-wiki, and candidate summary
- [x] Add a `--repair` command to fix drift automatically where safe

## Priority 7: UX and Safety

- [x] After `set-root`, confirm: memory updated, state file updated, registry refreshed
- [x] After `remember-subwiki`, confirm: selected wiki saved, parent root known, registry refreshed
- [ ] When ambiguity exists, present a numbered candidate list
- [x] When a path is invalid, explain whether it failed marker detection or filesystem existence
- [x] Never overwrite an existing schema file without explicit user approval

## Priority 8: Documentation

- [x] Keep `SKILL.md` aligned with actual script behavior
- [x] Keep `references/workflows.md` aligned with actual script behavior
- [x] Keep `references/runtime-registry.md` aligned with actual runtime files
- [x] Add examples for: `use this root`, `use this wiki`, `switch wiki`, `forget current wiki`, `refresh registry`
- [x] Add troubleshooting notes for stale state, drift, and ambiguous candidates

## Priority 9: Tests

### 9.1 Functional Tests

- [x] Test setting root only
- [x] Test setting selected sub-wiki only
- [ ] Test root plus selected sub-wiki together
- [x] Test forgetting state
- [x] Test refreshing registry
- [ ] Test initializing a new sub-wiki

### 9.2 Edge Cases

- [x] Test missing state files
- [x] Test missing remembered paths
- [ ] Test non-canonical wiki layouts
- [x] Test nested `vault/` paths
- [ ] Test mirrored root locations
- [ ] Test drift between memory and state files

## Priority 10: Definition of Done

- [x] User can say `use this root` and the skill updates memory, state file, event log, and registry correctly
- [x] User can say `use this wiki` and the skill updates memory, state file, event log, and registry correctly
- [x] Future agents can recover the correct root and selected sub-wiki without asking again when state is unambiguous
- [x] Drift is detected and repaired instead of silently ignored
- [x] Registry reflects the current discovered sub-wiki structure at any time

## Recommended Execution Order

1. Finish persistence verification after explicit root/wiki setting
2. Add JSON registry output
3. Add drift detection and repair
4. Add scoring/ranking for candidate quality
5. Add `--doctor` and `--show-current`
6. Add tests for edge cases
7. Polish docs and examples
