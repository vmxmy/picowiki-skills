# Workflow Details

## Table of Contents

1. [Initialization Flow](#initialization-flow)
2. [Ingest Patterns](#ingest-patterns)
3. [Query Patterns](#query-patterns)
4. [Lint Patterns](#lint-patterns)
5. [Troubleshooting](#troubleshooting)
6. [Integration with External Tools](#integration-with-external-tools)

## Initialization Flow

### Vault Detection Algorithm

```
1. Check remembered selected sub-wiki first
   -> durable memory entry for the user's current sub-wiki
   -> local fallback file: ~/.hermes/state/llm-wiki/selected-vault-path.txt
   -> If present and valid, list it first

2. Check remembered Obsidian root container
   -> durable memory entry for the parent obsidian directory
   -> local fallback file: ~/.hermes/state/llm-wiki/wiki-root-path.txt
   -> Enumerate subdirectories under that root and treat them as candidate sub-wikis
   -> Do not treat the remembered root itself as a wiki unless it has real wiki markers

3. Parse Obsidian config
   -> Read registered vault paths from Obsidian config files

4. Scan likely directories
   -> current workspace, ~/Documents, ~, ~/.hermes/obsidian, ~/obsidian, ~/Obsidian_Vault
   -> Prefer sub-wikis under remembered roots over global matches
   -> Score candidates by marker strength

5. Check iCloud as fallback
   -> ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/

6. Present results to user when ambiguous
   -> "Found these sub-wikis: [list]. Which one should I use?"
   -> Or: "No sub-wikis found. Which root folder should I use or where should I create one?"

7. Once the user explicitly chooses a root or sub-wiki
   -> Save root to durable memory and ~/.hermes/state/llm-wiki/wiki-root-path.txt when applicable
   -> Save selected sub-wiki to durable memory and ~/.hermes/state/llm-wiki/selected-vault-path.txt
   -> Refresh ~/.hermes/skills/llm-wiki/runtime/wiki-structure.log.md
   -> Refresh ~/.hermes/skills/llm-wiki/runtime/subwiki-registry.json
   -> Append an event to ~/.hermes/skills/llm-wiki/runtime/wiki-events.log
   -> Treat future explicit user choices as overrides

8. Completion rule for explicit path-setting requests
   -> The operation is only complete after both durable memory and local state files are updated
   -> If one write succeeds and the other does not, retry/fix it before reporting success
```

### First-Time Setup Checklist

After creating the directory structure:

- [ ] raw/ directory exists and is writable
- [ ] raw/assets/ exists for image downloads
- [ ] wiki/sources/ exists
- [ ] wiki/concepts/ exists
- [ ] wiki/entities/ exists
- [ ] wiki/comparisons/ exists
- [ ] output/ exists
- [ ] SCHEMA.md created with domain customization
- [ ] index.md created with category headings
- [ ] log.md created with initialization entry
- [ ] runtime registry refreshed
- [ ] user-facing root/sub-wiki summary returned

### Command Patterns

- `bash scripts/init-vault.sh --set-root /path/to/root`
- `bash scripts/init-vault.sh --remember /path/to/sub-wiki`
- `bash scripts/init-vault.sh --show-current`
- `bash scripts/init-vault.sh --doctor`
- `bash scripts/init-vault.sh --repair`
- `bash scripts/init-vault.sh --refresh-registry`
- `bash scripts/init-vault.sh --forget`

## Ingest Patterns

### Single Source Ingest (Interactive)

Best for: high-value sources, user wants control

```
User: "I added article.md to raw/"
  -> Read source
  -> "Here are the key takeaways: [list]. What should I emphasize?"
  -> User provides guidance
  -> Create/update all wiki pages
  -> Update index.md and log.md
  -> "Done. Created [N] new pages, updated [M] existing pages."
```

### Batch Ingest

Best for: importing many sources at once, catching up

```
User: "I added 10 articles to raw/, process them all"
  -> For each source in raw/ not yet in wiki/sources/:
    -> Read source
    -> Create summary page
    -> Update entities and concepts
    -> Update index
    -> Append to log
  -> "Processed [N] sources. Created [X] new pages. Flagged [Y] contradictions."
```

### Incremental Update

When a source is re-read or updated:

```
User: "Re-read raw/article.md, I updated it with new data"
  -> Read source
  -> Diff against existing wiki/sources/ page
  -> Update all affected wiki pages
  -> Note in log: "## [date] re-ingest | Article Title (updated)"
```

## Query Patterns

### Simple Factual Query

```
User: "What does the wiki say about transformer architectures?"
  -> Read index.md
  -> Read the most relevant concept/entity/source pages
  -> Synthesize answer with citations
```

### Comparative Analysis

```
User: "Compare the approaches from source A and source B"
  -> Read both source summary pages
  -> Read related concept/entity pages
  -> Create comparison page in wiki/comparisons/
  -> File back into wiki
```

### Exploratory Query

```
User: "What don't we know yet about topic X?"
  -> Read all relevant wiki pages
  -> Identify gaps, contradictions, weak evidence
  -> Suggest new sources or questions
  -> Optionally create a research-agenda page
```

## Lint Patterns

### Contradiction Detection

Look for:
- Pages making opposing claims about the same topic
- Confidence levels that should be lowered based on new evidence
- Entity pages with conflicting descriptions

### Orphan Detection

A page is orphaned if:
- No other wiki page links to it
- It is not listed in index.md

### Gap Detection

A concept is missing if:
- Multiple source pages mention it but no concept page exists
- Entity pages reference it without a wikilink

### Staleness Detection

A page may be stale if:
- Its updated date is old relative to newer sources on the same topic
- Newer sources supersede it without the page being refreshed

## Troubleshooting

### State Drift

If the runtime registry disagrees with remembered paths:

- Run `bash scripts/init-vault.sh --doctor`
- If drift is found, run `bash scripts/init-vault.sh --repair`
- If the user explicitly clarified the right path, update both durable memory and the relevant state file in the same turn

### Ambiguous Candidates

If multiple strong sub-wikis are detected:

- Read `runtime/wiki-structure.log.md`
- Compare candidate scores and markers
- Prefer candidates under the remembered root
- Ask the user only if ambiguity remains meaningful

### Missing Paths

If a remembered root or sub-wiki no longer exists:

- Clear or repair the broken state
- Refresh the runtime registry
- Suggest the closest valid candidate instead of silently switching

## Integration with External Tools

### Obsidian Web Clipper

- Save articles directly to raw/ as markdown
- Run ingest after clipping

### Dataview Plugin

If frontmatter stays consistent, Dataview can generate:
- dynamic source tables
- entity lists by category
- confidence or freshness views

### Marp Plugin

For slide decks from wiki content:
- create slide content in output/
- use `---` separators for slides
- add `marp: true` to frontmatter

### Git

The wiki is plain markdown files:
- `git init` in the sub-wiki for history
- commit after major ingest/lint cycles
- branch for experimental reorganizations
