# SCHEMA.md Template

This is the template for the wiki's SCHEMA.md file. Customize it during initialization based on the user's domain and preferences.

---

Copy the template below and fill in the bracketed sections. Remove sections that don't apply to the user's use case.

---

```markdown
# LLM Wiki Schema

This document defines how the wiki is structured, what conventions to follow, and what workflows to use. This is the key configuration — it makes the LLM a disciplined wiki maintainer rather than a generic chatbot.

## Domain

[Describe the wiki's purpose here. Examples:]
- Personal knowledge management (health, goals, psychology, self-improvement)
- Research wiki (going deep on a topic over weeks/months)
- Reading companion (filing chapters, building character/theme pages)
- Business/team wiki (Slack threads, meeting transcripts, project docs)
- Competitive analysis, due diligence, trip planning, course notes, hobby deep-dives

## Directory Structure

```
vault/
├── raw/                # Immutable sources (read-only)
│   └── assets/         # Images, attachments
├── wiki/               # LLM workspace
│   ├── sources/        # Per-source summary pages
│   ├── concepts/       # Concept/topic pages
│   ├── entities/       # People, organizations, products
│   └── comparisons/    # Analyses, comparisons, synthesis
├── output/             # Query results, reports, slides
├── SCHEMA.md           # This file
├── index.md            # Page catalog
└── log.md              # Operation log
```

## Page Types and Naming

| Type | Path | Naming Convention |
|------|------|-------------------|
| Source summary | `wiki/sources/` | `YYYY-MM-DD_source-title.md` |
| Concept | `wiki/concepts/` | `concept-name.md` (lowercase, hyphenated) |
| Entity | `wiki/entities/` | `entity-name.md` (lowercase, hyphenated) |
| Comparison | `wiki/comparisons/` | `topic-a-vs-topic-b.md` |
| Query result | `output/` | `YYYY-MM-DD_query-topic.md` |

## Frontmatter Standard

Every wiki page MUST have YAML frontmatter. Required fields:

```yaml
---
type: source | concept | entity | comparison | output
title: "Human-readable title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
confidence: high | medium | low
related:
  - "[[other-page]]"
---
```

### Additional fields by type

**Source pages:**
```yaml
source_file: raw/filename.md
source_type: article | paper | book | podcast | video | thread
authors: ["Name"]
```

**Entity pages:**
```yaml
category: person | organization | product | technology | event
aliases: ["Alternative Name"]
```

**Concept pages:**
```yaml
source_count: 3        # Number of sources contributing to this concept
maturity: emerging | developing | mature
```

## Linking Conventions

- Use Obsidian wikilinks: `[[page-name]]` for internal links
- Links are bidirectional — Obsidian handles backlinks automatically
- When mentioning a concept or entity for the first time in a page, link it
- Prefer linking to concept/entity pages over source pages in synthesis text
- Use `[[page-name|display text]]` for cleaner prose when needed

## Workflows

### Ingest Workflow

When a new source is added to raw/:

1. Read the source document completely
2. Extract: key arguments, entities mentioned, concepts covered, data points
3. Create source summary page in `wiki/sources/`
4. For each significant entity mentioned:
   - If entity page exists: update with new information, noting which source contributed
   - If not: create new entity page in `wiki/entities/`
5. For each significant concept covered:
   - If concept page exists: integrate new perspective, note agreements/contradictions with prior sources
   - If not: create new concept page in `wiki/concepts/`
6. Update `index.md` with all new/modified pages
7. Append to `log.md`: `## [YYYY-MM-DD] ingest | Source Title`

**Ingest mode**: [interactive | batch]
- Interactive: discuss key takeaways with user before writing, ask what to emphasize
- Batch: process immediately, user reviews after

### Query Workflow

When answering a question:

1. Read `index.md` to locate relevant pages
2. Read the most relevant 5-10 wiki pages
3. Synthesize answer with `[[wikilink]]` citations for each claim
4. If the answer is substantial (comparison, analysis, new connection):
   - Create a new page in `wiki/comparisons/` or `output/`
   - Update `index.md` and `log.md`

### Lint Workflow

Health check the wiki:

1. Scan all wiki pages for:
   - Contradictions between pages (flag with ⚠️)
   - Stale claims superseded by newer sources
   - Orphan pages (no inbound links)
   - Missing concept pages (mentioned but not linked)
   - Broken wikilinks (pointing to non-existent pages)
2. Generate a lint report in `output/YYYY-MM-DD-lint.md`
3. Suggest: new questions to investigate, sources to find, pages to create
4. Append to `log.md`: `## [YYYY-MM-DD] lint | Summary`

## Co-evolution Notes

This schema is a living document. After the first 10-20 ingests, revisit and refine:
- Are the page types sufficient, or do we need new categories?
- Is the frontmatter capturing what's useful?
- Are the naming conventions working?
- Should we add new workflows?

Track schema changes in log.md: `## [YYYY-MM-DD] schema | Updated page types, added confidence field`
```
