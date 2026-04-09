# picowiki-skills

Custom [Claude Code](https://claude.ai/code) skills used in personal workflow.

## Available Skills

### llm-wiki

Karpathy's LLM Wiki pattern — a persistent, compounding knowledge base where the LLM incrementally builds and maintains structured markdown files over raw sources.

**Key Features:**
- Auto-detect Obsidian vault path
- Initialize full `raw/ → wiki/ → SCHEMA.md` three-layer architecture
- Ingest workflow (source → summary card → concept/entity pages → index)
- Query workflow (search → synthesize → file answer back as new page)
- Lint workflow (contradictions, orphans, gaps, stale content)

**Trigger:** `/llm-wiki` or mentions of "knowledge base", "LLM wiki", "ingest", "Obsidian setup"

**Directory Structure:**
```
vault/
├── raw/          # Immutable source documents (LLM read-only)
├── wiki/
│   ├── sources/      # Per-source summary cards
│   ├── concepts/     # Concept/topic pages
│   ├── entities/     # People, orgs, products
│   └── comparisons/  # Analyses and synthesis
├── output/       # Query results, reports
├── SCHEMA.md    # LLM behavior rules
├── index.md     # Content catalog
└── log.md       # Operation log (append-only)
```

## Installation

```bash
# Clone into your Claude Code skills directory
git clone https://github.com/vmxmy/picowiki-skills.git ~/.claude/skills/picowiki-skills

# Or link specific skills
ln -s ~/.claude/skills/picowiki-skills/llm-wiki ~/.claude/skills/
```

## License

Personal use. No license for redistribution.
