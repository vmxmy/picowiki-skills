---
name: llm-wiki
description: "Initialize and maintain a personal LLM Wiki knowledge base using Karpathy's pattern — a persistent, compounding wiki where the LLM builds and maintains structured markdown files over raw sources. Use this skill whenever the user mentions: setting up a knowledge base, creating a wiki, building an LLM wiki, ingesting sources into a wiki, maintaining a personal wiki, Obsidian vault setup for AI, 'llm wiki', or wants to create/initialize/maintain a personal knowledge management system. Also trigger when the user wants to organize research, build a reading companion wiki, or do competitive analysis/due diligence with structured knowledge accumulation."
---

# LLM Wiki — Persistent Personal Knowledge Base

This skill implements Karpathy's LLM Wiki pattern: instead of stateless RAG retrieval on every query, the LLM incrementally builds and maintains a persistent, interlinked collection of markdown files that compounds over time.

The wiki is a persistent, compounding artifact. Cross-references are already there. Contradictions are already flagged. Synthesis already reflects everything you've read. The wiki keeps getting richer with every source you add and every question you ask.

## Core Principle

The human curates sources and asks questions. The LLM does everything else — summarizing, cross-referencing, filing, and bookkeeping that makes a knowledge base useful over time.

Think of it this way: **Obsidian is the IDE, the LLM is the programmer, the wiki is the codebase.** You never (or rarely) write wiki pages yourself.

## Three-Layer Architecture

```
vault/
├── raw/                # Immutable source documents (read-only for LLM)
│   └── assets/         # Downloaded images, attachments
├── wiki/               # LLM-generated pages (LLM owns this layer)
│   ├── sources/        # Per-source summary pages
│   ├── concepts/       # Concept/topic pages
│   ├── entities/       # People, organizations, products, etc.
│   └── comparisons/    # Analyses, comparisons, synthesis pages
├── output/             # Query results, reports, slides
├── SCHEMA.md           # LLM behavior rules (co-evolved with user)
├── index.md            # Content catalog of all wiki pages
└── log.md              # Chronological operation log
```

**Raw** — Your curated source documents. Articles, papers, images, data files. Immutable: the LLM reads but never modifies.

**Wiki** — LLM-generated markdown files. Summaries, entity pages, concept pages, comparisons, overview, synthesis. The LLM owns this layer entirely. You read it; the LLM writes it.

**Schema** — A document that tells the LLM how the wiki is structured, what conventions to follow, and what workflows to use. This is the key configuration — it makes the LLM a disciplined wiki maintainer rather than a generic chatbot. You and the LLM co-evolve this over time.

## Initialization Workflow

### Step 1: Detect Vault Path

Search for existing Obsidian vaults on the user's system. Check these locations in order:

1. **Obsidian config** (most reliable): Parse `~/.obsidian/obsidian.json` or `~/Library/Application Support/obsidian/obsidian.json` for `vaults` entries
2. **Common directories**: `~/Documents/`, `~/`, home directory — look for folders containing `.obsidian/` subdirectory
3. **iCloud sync**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`
4. **Ask the user**: If no vault found, or the user wants a new one

Use `find` with `-maxdepth 3 -name ".obsidian" -type d` to locate vaults efficiently. Do NOT do deep recursive searches — keep it fast.

Present found vaults to the user and confirm which one to use, or let them specify a new path.

### Step 2: Initialize Vault Structure

Once the vault path is confirmed:

1. Create the directory structure (raw/, raw/assets/, wiki/sources/, wiki/concepts/, wiki/entities/, wiki/comparisons/, output/)
2. Generate `SCHEMA.md` from the template — read `references/schema-template.md` and customize based on the user's domain
3. Generate `index.md` — empty catalog with category headings
4. Generate `log.md` — with initialization entry
5. If SCHEMA.md already exists, ask user whether to overwrite or keep existing

After initialization, show the user the created structure and explain the three core operations.

## Core Operations

### Ingest

When the user drops a new source into `raw/` or asks to process a source:

1. **Read the source** — extract key information, arguments, data
2. **Discuss with user** — share key takeaways, ask what to emphasize (optional, skip if user prefers batch mode)
3. **Write summary page** — `wiki/sources/YYYY-MM-DD_source-title.md` with YAML frontmatter
4. **Update entity pages** — create or update `wiki/entities/*.md` for people, orgs, products mentioned
5. **Update concept pages** — create or update `wiki/concepts/*.md` for key topics
6. **Update index.md** — add new pages to the catalog
7. **Append to log.md** — `## [YYYY-MM-DD] ingest | Source Title`

A single source might touch 10-15 wiki pages. This is the compounding effect — each source strengthens the entire web.

**Frontmatter template for source pages:**
```yaml
---
type: source
title: "Source Title"
date: YYYY-MM-DD
tags: [tag1, tag2]
source_file: raw/filename.md
confidence: high | medium | low
related:
  - "[[concept-name]]"
  - "[[entity-name]]"
---
```

### Query

When the user asks a question against the wiki:

1. **Read index.md** — find relevant pages by scanning categories and summaries
2. **Drill into relevant pages** — read the most relevant wiki pages
3. **Synthesize with citations** — reference `[[page-name]]` for each claim
4. **File good answers back** — if the query produced a valuable comparison, analysis, or connection, create a new wiki page (e.g., `wiki/comparisons/analysis-name.md`)

The key insight: **good answers become new wiki pages.** A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history. This way explorations compound in the knowledge base just like ingested sources do.

Output formats vary by question type:
- Markdown page (default)
- Comparison table
- Slide deck (Marp format, stored in output/)
- Chart (matplotlib, stored in output/)
- Canvas view

### Lint

Periodically health-check the wiki. Look for:

- **Contradictions** — pages that make conflicting claims
- **Stale claims** — superseded by newer sources
- **Orphan pages** — no inbound wikilinks
- **Missing concepts** — mentioned across pages but lacking their own page
- **Broken cross-references** — wikilinks pointing to non-existent pages
- **Data gaps** — questions the wiki should answer but can't yet

The LLM is good at suggesting new questions to investigate and new sources to look for. This keeps the wiki healthy as it grows.

Run lint when:
- User explicitly asks for a health check
- After a batch ingest of 5+ sources
- When the user hasn't ingested anything in a while (opportunity to re-synthesize)

## Navigation Files

### index.md

Content-oriented catalog. Each page listed with a link, one-line summary, and optional metadata. Organized by category (entities, concepts, sources, comparisons). The LLM updates it on every ingest. When answering queries, read index first to locate relevant pages.

This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure.

### log.md

Chronological, append-only record. Each entry starts with a consistent prefix for parseability:

```markdown
## [2026-04-08] ingest | Article Title
## [2026-04-08] query | Comparison of X vs Y → filed as [[comparisons/x-vs-y]]
## [2026-04-09] lint | Found 3 orphans, 1 contradiction
```

`grep "^## \[" log.md | tail -5` gives the last 5 entries. The log gives a timeline of the wiki's evolution.

## SCHEMA.md

The schema is the key configuration file. Read `references/schema-template.md` for the full template. On initialization, customize it based on:

- **User's domain** — personal, research, business, reading companion, etc.
- **Source types** — articles, papers, books, podcasts, Slack threads
- **Naming conventions** — how pages should be named
- **Frontmatter fields** — what metadata to track
- **Workflow preferences** — interactive vs batch ingest, supervision level

Co-evolve the schema over time as you figure out what works. After the first 10-20 ingests, revisit and refine based on what patterns emerged.

## Vault Path Detection Reference

Common Obsidian vault locations by platform:

| Platform | Paths |
|----------|-------|
| macOS | `~/Documents/`, `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`, `~/` |
| Linux | `~/Documents/`, `~/` |
| Windows | `%USERPROFILE%\Documents\`, `%APPDATA%\obsidian\` |

Detection strategy:
1. Check Obsidian's own config for registered vaults (most reliable)
2. Shallow `find` (maxdepth 3) for `.obsidian/` directories
3. Ask the user

## Tips

- **Obsidian Web Clipper** — browser extension to save web articles as markdown directly into raw/
- **Download images locally** — in Obsidian: Settings → Files & Links → set attachment folder to `raw/assets/`. Bind "Download attachments" to a hotkey (Ctrl+Shift+D)
- **Graph view** — the best way to see wiki shape: hubs, orphans, clusters
- **Dataview plugin** — if frontmatter is consistent, Dataview generates dynamic tables/lists
- **Marp plugin** — generate slide decks from wiki content
- **Git** — the wiki is just markdown files. You get version history, branching, and collaboration for free

## Optional: Search at Scale

For small-to-medium wikis, the index.md file is sufficient for navigation. As the wiki grows beyond ~100 sources, consider:

- **qmd** — local search engine for markdown with hybrid BM25/vector search and LLM re-ranking. Has both CLI and MCP server.
- **Custom search script** — the LLM can help build one as needed

## Examples

### Ingest Example

User says: "I just added an article about RAG architectures to raw/"

Response flow:
1. Read `raw/rag-architectures.md`
2. Create `wiki/sources/2026-04-08_rag-architectures.md` with summary
3. Update or create `wiki/concepts/rag.md` with new insights
4. Update or create entity pages for mentioned tools/authors
5. Update `index.md` with new pages
6. Append to `log.md`

### Query Example

User asks: "What are the key differences between RAG and fine-tuning?"

Response flow:
1. Read `index.md` to find relevant pages
2. Read `wiki/concepts/rag.md`, `wiki/concepts/fine-tuning.md`, related source pages
3. Synthesize comparison with `[[wikilink]]` citations
4. File the comparison as `wiki/comparisons/rag-vs-fine-tuning.md`
5. Update `index.md` and `log.md`
