# Runtime Registry Design

The `llm-wiki` skill maintains a control-plane registry under `~/.hermes/skills/llm-wiki/runtime/`.

## Files

- `wiki-structure.log.md`
  - Human-readable snapshot regenerated on every detect, init, remember, forget, repair, or explicit refresh
  - Stores remembered root, selected sub-wiki, candidate count, candidate scores, markers, source hints, and shallow structure listings
- `subwiki-registry.json`
  - Machine-readable registry for scripts and future agents
  - Stores `schema_version`, `remembered_root`, `selected_sub_wiki`, `candidate_count`, `recommended_candidate`, `recommendation_reason`, ambiguity notes, and an array of candidate objects with `path`, `canonical_path`, `aliases`, `score`, `markers`, `under_root`, `selected`, `last_seen`, `source_hints`, and `structure`
- `wiki-events.log`
  - Append-only event stream
  - Records detection, root changes, selected sub-wiki changes, initialization, refresh, repair, and forget actions with timestamps

## State Files

The registry works together with state files in `~/.hermes/state/llm-wiki/`:

- `wiki-root-path.txt` — remembered parent Obsidian root that stores sub-wikis
- `selected-vault-path.txt` — remembered active sub-wiki path
- `last-refresh-at.txt` — timestamp of the most recent registry refresh

## Update Rules

Refresh the runtime registry whenever the skill:

1. detects wiki candidates
2. initializes a new sub-wiki
3. changes the remembered Obsidian root
4. changes the remembered active sub-wiki
5. performs an explicit `--refresh-registry`
6. runs `--repair`
7. runs `--doctor` or `--show-current`

## Root vs Sub-Wiki Rule

The remembered `obsidian/` directory is treated as a container root. The skill scans its children for actual sub-wikis and should not treat the root itself as a working wiki unless it also has real wiki markers.

## Command Reference

- `bash scripts/init-vault.sh --set-root /path/to/root`
- `bash scripts/init-vault.sh --remember /path/to/sub-wiki`
- `bash scripts/init-vault.sh --refresh-registry`
- `bash scripts/init-vault.sh --show-current`
- `bash scripts/init-vault.sh --doctor`
- `bash scripts/init-vault.sh --repair`
- `bash scripts/init-vault.sh --forget`
