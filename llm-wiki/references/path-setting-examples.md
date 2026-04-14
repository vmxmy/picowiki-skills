# Path Setting Examples

Use these examples when updating `llm-wiki` memory and state.

## Set Root

User says:
- `use this root: /home/laoxu/.hermes/obsidian`
- `remember this root for all sub-wikis`
- `obsidian is my wiki root`

Agent must:
1. update durable memory with the canonical root container path
2. write `~/.hermes/state/llm-wiki/wiki-root-path.txt`
3. refresh runtime registry
4. confirm success only after both layers are updated

## Set Active Sub-Wiki

User says:
- `use this wiki: /home/laoxu/.hermes/obsidian/llm-wiki`
- `remember this wiki`
- `switch to the international education wiki`

Agent must:
1. update durable memory with the selected sub-wiki path
2. write `~/.hermes/state/llm-wiki/selected-vault-path.txt`
3. refresh runtime registry
4. confirm success only after both layers are updated

## Inspect Current State

Commands:
- `bash scripts/init-vault.sh --show-current`
- `bash scripts/init-vault.sh --doctor`
- `bash scripts/init-vault.sh --refresh-registry`

## Repair Drift

Commands:
- `bash scripts/init-vault.sh --repair`
- then re-run `bash scripts/init-vault.sh --doctor`
