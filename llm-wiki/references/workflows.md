# Workflow Details

## Table of Contents

1. [Initialization Flow](#initialization-flow)
2. [Ingest Patterns](#ingest-patterns)
3. [Query Patterns](#query-patterns)
4. [Lint Patterns](#lint-patterns)
5. [Integration with External Tools](#integration-with-external-tools)

## Initialization Flow

### Vault Detection Algorithm

```
1. Parse Obsidian config
   → macOS: ~/Library/Application Support/obsidian/obsidian.json
   → Read "vaults" object for registered vault paths

2. If config not found or no vaults:
   → find ~ -maxdepth 3 -name ".obsidian" -type d 2>/dev/null
   → Parent directory of .obsidian/ is the vault root

3. If still no results:
   → Check iCloud: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/

4. Present results to user:
   → "Found these Obsidian vaults: [list]. Which one to use?"
   → Or: "No vaults found. Where should I create a new one?"
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
- [ ] User confirmed the domain type and workflow preferences

## Ingest Patterns

### Single Source Ingest (Interactive)

Best for: high-value sources, user wants control

```
User: "I added article.md to raw/"
  → Read source
  → "Here are the key takeaways: [list]. What should I emphasize?"
  → User provides guidance
  → Create/update all wiki pages
  → Update index.md and log.md
  → "Done. Created [N] new pages, updated [M] existing pages."
```

### Batch Ingest

Best for: importing many sources at once, catching up

```
User: "I added 10 articles to raw/, process them all"
  → For each source in raw/ not yet in wiki/sources/:
    → Read source
    → Create summary page
    → Update entities and concepts
    → Update index
    → Append to log
  → "Processed [N] sources. Created [X] new pages. Flagged [Y] contradictions."
```

### Incremental Update

When a source is re-read or updated:

```
User: "Re-read raw/article.md, I updated it with new data"
  → Read source (note: raw/ is supposed to be immutable, but user can override)
  → Diff against existing wiki/sources/ page
  → Update all affected wiki pages
  → Note in log: "## [date] re-ingest | Article Title (updated)"
```

## Query Patterns

### Simple Factual Query

```
User: "What does the wiki say about transformer architectures?"
  → Read index.md → find wiki/concepts/transformer-architectures.md
  → Read that page + related entity/source pages
  → Synthesize answer with citations
```

### Comparative Analysis

```
User: "Compare the approaches from source A and source B"
  → Read both source summary pages
  → Read related concept/entity pages
  → Create comparison page in wiki/comparisons/
  → File back into wiki (compounds knowledge)
```

### Exploratory Query

```
User: "What don't we know yet about topic X?"
  → Read all relevant wiki pages
  → Identify gaps, contradictions, weak evidence
  → Suggest: new sources to find, questions to investigate
  → Optionally create a "research agenda" page
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
- It's not listed in index.md (shouldn't happen if ingest is correct)

### Gap Detection

A concept is missing if:
- Multiple source pages mention it but no concept page exists
- Entity pages reference a concept without a wikilink (opportunity to create one)

### Staleness Detection

A page may be stale if:
- Its `updated` date is old relative to new sources that cover the same topic
- New sources contradict or supersede its content without the page being updated

## Integration with External Tools

### Obsidian Web Clipper

- Browser extension saves articles directly to raw/ as markdown
- After clipping, run ingest to process the new source

### Dataview Plugin

If using consistent frontmatter, Dataview queries enable:
- Dynamic tables of all sources by tag
- Lists of entities by category
- Pages sorted by confidence level or update date

### Marp Plugin

For generating slide decks from wiki content:
- Create slide content in output/ directory
- Use `---` separators for slides
- Add `marp: true` to frontmatter

### Git

The wiki is plain markdown files:
- `git init` in the vault for version history
- Commit after each ingest/lint cycle
- Branch for experimental reorganizations
- Share via remote repository for team wikis
