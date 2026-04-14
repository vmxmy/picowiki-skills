#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

HOME = Path.home()
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = Path(os.environ.get("HERMES_LLM_WIKI_SKILL_DIR", SCRIPT_DIR.parent)).resolve()
STATE_DIR = Path(os.environ.get("HERMES_LLM_WIKI_STATE_DIR", HOME / ".hermes/state/llm-wiki")).resolve()
SELECTED_VAULT_FILE = STATE_DIR / "selected-vault-path.txt"
WIKI_ROOT_FILE = STATE_DIR / "wiki-root-path.txt"
LAST_REFRESH_FILE = STATE_DIR / "last-refresh-at.txt"
RUNTIME_DIR = Path(os.environ.get("HERMES_LLM_WIKI_RUNTIME_DIR", SKILL_DIR / "runtime")).resolve()
REGISTRY_MD = RUNTIME_DIR / "wiki-structure.log.md"
REGISTRY_JSON = RUNTIME_DIR / "subwiki-registry.json"
EVENT_LOG = RUNTIME_DIR / "wiki-events.log"
SCHEMA_TEMPLATE = SKILL_DIR / "references/schema-template.md"
REGISTRY_SCHEMA_VERSION = 2
STALE_REFRESH_SECONDS = int(os.environ.get("HERMES_LLM_WIKI_STALE_REFRESH_SECONDS", "600"))

SEARCH_ROOTS = [
    HOME,
    HOME / "Documents",
    HOME / ".hermes/obsidian",
    HOME / "obsidian",
    HOME / "Obsidian_Vault",
]


@dataclass
class Candidate:
    path: Path
    canonical_path: Path
    aliases: set[str]
    markers: list[str]
    score: int
    source_hints: set[str]
    structure: list[str]

    def selected(self, selected: Path | None) -> bool:
        return selected is not None and self.canonical_path == selected

    def under_root(self, remembered_root: Path | None) -> bool:
        return remembered_root is not None and is_under(self.canonical_path, remembered_root)

    def ambiguity_flags(self, remembered_root: Path | None) -> list[str]:
        flags: list[str] = []
        if self.under_root(remembered_root):
            flags.append("under-root")
        if "SCHEMA.md" not in self.markers and "CLAUDE.md" not in self.markers:
            flags.append("missing-schema")
        if "raw/" not in self.markers or "wiki/" not in self.markers:
            flags.append("non-canonical-layout")
        if self.path.name == "vault":
            flags.append("nested-vault")
        return flags

    def as_json(self, remembered_root: Path | None, selected: Path | None) -> dict:
        return {
            "path": str(self.path),
            "canonical_path": str(self.canonical_path),
            "aliases": sorted(self.aliases),
            "markers": self.markers,
            "score": self.score,
            "selected": self.selected(selected),
            "under_root": self.under_root(remembered_root),
            "last_seen": now_iso(),
            "source_hints": sorted(self.source_hints),
            "ambiguity_flags": self.ambiguity_flags(remembered_root),
            "structure": self.structure,
        }


def now_human() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    EVENT_LOG.touch(exist_ok=True)


def canonicalize(path: str | Path) -> Path:
    p = Path(path).expanduser()
    try:
        return p.resolve(strict=False)
    except Exception:
        return p


def read_state(path: Path) -> Path | None:
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return None
    return canonicalize(content)


def write_state(path: Path, value: Path) -> None:
    ensure_dirs()
    value = canonicalize(value)
    path.write_text(f"{value}\n", encoding="utf-8")
    saved = read_state(path)
    if saved != value:
        raise RuntimeError(f"failed to verify state file write: {path}")


def clear_state(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def append_event(action: str, details: str) -> None:
    ensure_dirs()
    with EVENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{now_human()} | {action} | {details}\n")


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def detect_markers(path: Path) -> list[str]:
    markers: list[str] = []
    if (path / ".obsidian").is_dir():
        markers.append(".obsidian/")
    for name in ["SCHEMA.md", "CLAUDE.md", "index.md", "INDEX.md", "log.md"]:
        if (path / name).is_file():
            markers.append(name)
    for name in ["raw", "wiki", "output", "articles", "concepts"]:
        if (path / name).is_dir():
            markers.append(f"{name}/")
    return markers


def score_candidate(path: Path, markers: Iterable[str]) -> int:
    marker_set = set(markers)
    score = 0
    if {"raw/", "wiki/"}.issubset(marker_set):
        score += 60
    if "SCHEMA.md" in marker_set:
        score += 18
    if "CLAUDE.md" in marker_set:
        score += 16
    if "index.md" in marker_set or "INDEX.md" in marker_set:
        score += 14
    if "log.md" in marker_set:
        score += 12
    if ".obsidian/" in marker_set:
        score += 8
    if "output/" in marker_set:
        score += 4
    if {"articles/", "concepts/"}.issubset(marker_set):
        score += 22
    if path.name == "vault":
        score += 4
    return score


def has_real_wiki_markers(path: Path) -> bool:
    markers = detect_markers(path)
    return score_candidate(path, markers) >= 30


def shallow_structure(path: Path) -> list[str]:
    items: list[str] = []
    for candidate in sorted(path.rglob("*")):
        try:
            rel = candidate.relative_to(path)
        except ValueError:
            continue
        if len(rel.parts) > 2:
            continue
        rel_s = rel.as_posix()
        if rel_s.startswith(".git/") or rel_s == ".git":
            continue
        if rel_s.startswith(".obsidian/workspace") or rel_s == ".obsidian/cache":
            continue
        items.append(rel_s)
    return items


def obsidian_config_candidates() -> list[Path]:
    config_paths = [
        HOME / "Library/Application Support/obsidian/obsidian.json",
        HOME / ".obsidian/obsidian.json",
        HOME / ".config/obsidian/obsidian.json",
    ]
    candidates: list[Path] = []
    for config_path in config_paths:
        if not config_path.exists():
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        vaults = data.get("vaults", {}) if isinstance(data, dict) else {}
        if not isinstance(vaults, dict):
            continue
        for value in vaults.values():
            if isinstance(value, dict) and value.get("path"):
                candidates.append(canonicalize(value["path"]))
    return candidates


def add_candidate(store: dict[str, Candidate], path: Path, source_hint: str) -> None:
    raw_path = Path(path).expanduser()
    if not raw_path.is_dir():
        return
    canonical_path = canonicalize(raw_path)
    markers = detect_markers(canonical_path)
    score = score_candidate(canonical_path, markers)
    if score < 30:
        return
    key = str(canonical_path)
    alias = str(raw_path)
    if key in store:
        store[key].source_hints.add(source_hint)
        store[key].score = max(store[key].score, score)
        store[key].aliases.add(alias)
        return
    store[key] = Candidate(
        path=canonical_path,
        canonical_path=canonical_path,
        aliases={alias, str(canonical_path)},
        markers=markers,
        score=score,
        source_hints={source_hint},
        structure=shallow_structure(canonical_path),
    )


def collect_from_root(store: dict[str, Candidate], root: Path, source_hint: str) -> None:
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        add_candidate(store, child, source_hint)
        nested_vault = child / "vault"
        if nested_vault.is_dir():
            add_candidate(store, nested_vault, f"{source_hint}:nested-vault")


def collect_candidates() -> tuple[list[Candidate], Path | None, Path | None]:
    selected = read_state(SELECTED_VAULT_FILE)
    root = read_state(WIKI_ROOT_FILE)
    store: dict[str, Candidate] = {}

    if selected and selected.is_dir():
        add_candidate(store, selected, "state:selected")
    if root and root.is_dir():
        collect_from_root(store, root, "state:root")

    for candidate in obsidian_config_candidates():
        add_candidate(store, candidate, "obsidian-config")

    for search_root in SEARCH_ROOTS:
        if not search_root.is_dir():
            continue
        for candidate in search_root.glob("*"):
            if not candidate.is_dir():
                continue
            if root and canonicalize(candidate) == root:
                continue
            add_candidate(store, candidate, f"search-root:{search_root.name or 'home'}")
            nested_vault = candidate / "vault"
            if nested_vault.is_dir():
                add_candidate(store, nested_vault, f"search-root:{search_root.name or 'home'}:nested-vault")

        for obsidian_dir in search_root.rglob(".obsidian"):
            if len(obsidian_dir.relative_to(search_root).parts) > 4:
                continue
            parent = obsidian_dir.parent
            if root and canonicalize(parent) == root:
                continue
            add_candidate(store, parent, f"scan-obsidian:{search_root.name or 'home'}")

    icloud_root = HOME / "Library/Mobile Documents/iCloud~md~obsidian/Documents"
    if icloud_root.is_dir():
        collect_from_root(store, icloud_root, "icloud")

    candidates = sorted(
        store.values(),
        key=lambda c: (
            0 if selected and c.canonical_path == selected else 1,
            0 if root and is_under(c.canonical_path, root) else 1,
            -c.score,
            str(c.canonical_path),
        ),
    )
    return candidates, root, selected


def read_last_refresh() -> datetime | None:
    if not LAST_REFRESH_FILE.exists():
        return None
    raw = LAST_REFRESH_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def stale_status() -> tuple[bool, str]:
    last_refresh = read_last_refresh()
    if last_refresh is None:
        return True, "missing"
    age = datetime.now() - last_refresh
    if age > timedelta(seconds=STALE_REFRESH_SECONDS):
        return True, f"stale:{int(age.total_seconds())}s"
    return False, f"fresh:{int(age.total_seconds())}s"


def recommend_candidate(candidates: list[Candidate], root: Path | None, selected: Path | None) -> tuple[Candidate | None, str]:
    if not candidates:
        return None, "no candidates available"
    if selected:
        for candidate in candidates:
            if candidate.canonical_path == selected:
                return candidate, "explicitly selected sub-wiki"

    best = candidates[0]
    if root and best.under_root(root):
        if len(candidates) > 1:
            second = candidates[1]
            if second.under_root(root) and second.score == best.score:
                return best, "tie under remembered root; ask the user if you need certainty"
        return best, "highest-scoring candidate under remembered root"

    return best, "highest-scoring discovered candidate"


def ambiguity_summary(candidates: list[Candidate], root: Path | None) -> list[str]:
    if len(candidates) < 2:
        return []
    top = candidates[0]
    peers = [c for c in candidates[1:] if c.score == top.score and c.under_root(root) == top.under_root(root)]
    if not peers:
        return []
    lines = [f"top candidate tie on score={top.score}"]
    for peer in [top, *peers[:3]]:
        flags = ", ".join(peer.ambiguity_flags(root)) or "none"
        lines.append(f"{peer.canonical_path} | flags={flags}")
    return lines


def refresh_registry(force: bool = False) -> list[Candidate]:
    ensure_dirs()
    stale, stale_label = stale_status()
    candidates, root, selected = collect_candidates()
    LAST_REFRESH_FILE.write_text(f"{now_iso()}\n", encoding="utf-8")
    recommended, reason = recommend_candidate(candidates, root, selected)
    ambiguity = ambiguity_summary(candidates, root)

    lines = [
        "# LLM Wiki Runtime Registry",
        "",
        f"- schema_version: {REGISTRY_SCHEMA_VERSION}",
        f"- generated_at: {now_human()}",
        f"- previous_refresh_status: {stale_label}",
        f"- remembered_root: {root if root else 'none'}",
        f"- selected_sub_wiki: {selected if selected else 'none'}",
        f"- candidate_count: {len(candidates)}",
        f"- recommended_candidate: {recommended.canonical_path if recommended else 'none'}",
        f"- recommendation_reason: {reason}",
        "",
    ]
    if ambiguity:
        lines.append("## Ambiguity Notes")
        lines.append("")
        for item in ambiguity:
            lines.append(f"- {item}")
        lines.append("")
    lines.append("## Known Sub-Wikis")
    lines.append("")

    if not candidates:
        lines.append("_No sub-wikis discovered._")
    else:
        for candidate in candidates:
            lines.append(f"### `{candidate.canonical_path}`")
            lines.append(f"- score: {candidate.score}")
            lines.append(f"- aliases: {', '.join(sorted(candidate.aliases))}")
            lines.append(f"- markers: {', '.join(candidate.markers) if candidate.markers else 'none'}")
            lines.append(f"- selected: {'yes' if candidate.selected(selected) else 'no'}")
            lines.append(f"- under_remembered_root: {'yes' if candidate.under_root(root) else 'no'}")
            lines.append(f"- source_hints: {', '.join(sorted(candidate.source_hints))}")
            lines.append(f"- ambiguity_flags: {', '.join(candidate.ambiguity_flags(root)) or 'none'}")
            lines.append("- structure:")
            for item in candidate.structure:
                lines.append(f"  - {item}")
            lines.append("")
    REGISTRY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "generated_at": now_iso(),
        "previous_refresh_status": stale_label,
        "remembered_root": str(root) if root else None,
        "selected_sub_wiki": str(selected) if selected else None,
        "candidate_count": len(candidates),
        "recommended_candidate": str(recommended.canonical_path) if recommended else None,
        "recommendation_reason": reason,
        "ambiguity_notes": ambiguity,
        "candidates": [c.as_json(root, selected) for c in candidates],
    }
    REGISTRY_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_event(
        "refresh-registry",
        f"count={len(candidates)} root={root if root else 'none'} selected={selected if selected else 'none'} force={force}",
    )
    return candidates


def verify_candidate_relationships(root: Path | None, selected: Path | None, candidates: list[Candidate]) -> list[str]:
    issues: list[str] = []
    if root and not root.is_dir():
        issues.append(f"remembered root does not exist: {root}")
    if selected and not selected.is_dir():
        issues.append(f"selected sub-wiki does not exist: {selected}")
    if root and selected and selected.is_dir() and not is_under(selected, root):
        issues.append(f"selected sub-wiki is not under remembered root: {selected}")
    if selected and candidates and not any(candidate.canonical_path == selected for candidate in candidates):
        issues.append("selected sub-wiki is not present in runtime registry")
    return issues


def show_current() -> int:
    candidates = refresh_registry()
    root = read_state(WIKI_ROOT_FILE)
    selected = read_state(SELECTED_VAULT_FILE)
    recommended, reason = recommend_candidate(candidates, root, selected)
    stale, stale_label = stale_status()
    print(f"remembered_root={root if root else 'none'}")
    print(f"selected_sub_wiki={selected if selected else 'none'}")
    print(f"candidate_count={len(candidates)}")
    print(f"registry_status={'stale' if stale else 'fresh'} ({stale_label})")
    print(f"recommended_candidate={recommended.canonical_path if recommended else 'none'}")
    print(f"recommendation_reason={reason}")
    if candidates:
        print("top_candidates=")
        for candidate in candidates[:5]:
            print(f"  - {candidate.canonical_path} (score={candidate.score})")
    return 0


def doctor() -> int:
    candidates = refresh_registry()
    root = read_state(WIKI_ROOT_FILE)
    selected = read_state(SELECTED_VAULT_FILE)
    issues = verify_candidate_relationships(root, selected, candidates)
    recommended, reason = recommend_candidate(candidates, root, selected)
    ambiguity = ambiguity_summary(candidates, root)
    stale, stale_label = stale_status()

    print("LLM Wiki doctor report")
    print(f"- remembered_root: {root if root else 'none'}")
    print(f"- selected_sub_wiki: {selected if selected else 'none'}")
    print(f"- candidate_count: {len(candidates)}")
    print(f"- registry_markdown: {REGISTRY_MD}")
    print(f"- registry_json: {REGISTRY_JSON}")
    print(f"- refresh_status: {'stale' if stale else 'fresh'} ({stale_label})")
    print(f"- recommended_candidate: {recommended.canonical_path if recommended else 'none'}")
    print(f"- recommendation_reason: {reason}")
    if LAST_REFRESH_FILE.exists():
        print(f"- last_refresh_at: {LAST_REFRESH_FILE.read_text(encoding='utf-8').strip()}")

    if candidates:
        print("- top_candidates:")
        for candidate in candidates[:5]:
            flags = ", ".join(candidate.ambiguity_flags(root)) or "none"
            print(f"  - {candidate.canonical_path} | score={candidate.score} | flags={flags}")
    if ambiguity:
        print("- ambiguity_notes:")
        for item in ambiguity:
            print(f"  - {item}")

    if issues:
        print("- status: drift-detected")
        print("- recommended_fixes:")
        for issue in issues:
            print(f"  - {issue}")
        print("  - run `bash scripts/init-vault.sh --repair` if the drift is filesystem/state based")
        return 1

    print("- status: healthy")
    append_event("doctor", f"healthy count={len(candidates)}")
    return 0


def repair_state() -> int:
    root = read_state(WIKI_ROOT_FILE)
    selected = read_state(SELECTED_VAULT_FILE)
    changes: list[str] = []

    if root and not root.is_dir():
        clear_state(WIKI_ROOT_FILE)
        changes.append(f"cleared missing root {root}")
        root = None
    if selected and not selected.is_dir():
        clear_state(SELECTED_VAULT_FILE)
        changes.append(f"cleared missing selected sub-wiki {selected}")
        selected = None

    if selected and not root:
        root = selected.parent
        write_state(WIKI_ROOT_FILE, root)
        changes.append(f"recovered root from selected sub-wiki parent {root}")

    if root and selected and not is_under(selected, root):
        inferred_root = selected.parent
        write_state(WIKI_ROOT_FILE, inferred_root)
        changes.append(f"updated root to selected sub-wiki parent {inferred_root}")
        root = inferred_root

    refresh_registry(force=True)
    details = "; ".join(changes) if changes else "no changes required"
    append_event("repair-state", details)
    print(details)
    return 0


def remember_root(path_str: str) -> int:
    root = canonicalize(path_str)
    if not root.is_dir():
        print(f"Wiki root path does not exist: {root}", file=sys.stderr)
        return 1
    write_state(WIKI_ROOT_FILE, root)
    append_event("set-root", f"root={root}")
    refresh_registry(force=True)
    print("root_memory_expected=yes")
    print("root_state_file_updated=yes")
    print("registry_refreshed=yes")
    print(f"Remembered wiki root: {root}")
    return 0


def remember_subwiki(path_str: str) -> int:
    path = canonicalize(path_str)
    if not path.is_dir():
        print(f"Sub-wiki path does not exist: {path}", file=sys.stderr)
        return 1
    if not has_real_wiki_markers(path):
        print(f"Path does not look like a valid sub-wiki: {path}", file=sys.stderr)
        return 1
    write_state(SELECTED_VAULT_FILE, path)
    append_event("remember-subwiki", f"sub_wiki={path}")
    refresh_registry(force=True)
    print("subwiki_memory_expected=yes")
    print("subwiki_state_file_updated=yes")
    print("registry_refreshed=yes")
    print(f"Remembered preferred sub-wiki: {path}")
    return 0


def forget_paths() -> int:
    clear_state(WIKI_ROOT_FILE)
    clear_state(SELECTED_VAULT_FILE)
    append_event("forget", "cleared root and selected sub-wiki")
    refresh_registry(force=True)
    print("Cleared remembered wiki root and selected sub-wiki")
    return 0


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def render_default_schema(path: Path) -> str:
    if SCHEMA_TEMPLATE.exists():
        template = SCHEMA_TEMPLATE.read_text(encoding="utf-8")
        return (
            "# LLM Wiki Schema\n\n"
            f"Initialized for sub-wiki `{path.name}`. Customize the template below for your domain.\n\n"
            f"Source template: `{SCHEMA_TEMPLATE}`\n\n"
            f"---\n\n{template.strip()}\n"
        )
    return "# LLM Wiki Schema\n\nThis sub-wiki follows the llm-wiki layout with raw/, wiki/, output/, index.md, and log.md.\n"


def initialize_subwiki(path_str: str) -> int:
    path = canonicalize(path_str)
    path.mkdir(parents=True, exist_ok=True)
    for rel in [
        "raw/assets",
        "wiki/sources",
        "wiki/concepts",
        "wiki/entities",
        "wiki/comparisons",
        "output",
    ]:
        (path / rel).mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    write_if_missing(path / "SCHEMA.md", render_default_schema(path))
    write_if_missing(
        path / "index.md",
        "# Index\n\n## Sources\n\n## Concepts\n\n## Entities\n\n## Comparisons\n",
    )
    write_if_missing(path / "log.md", f"## [{today}] init | Initialized sub-wiki at {path}\n")

    write_state(SELECTED_VAULT_FILE, path)
    write_state(WIKI_ROOT_FILE, path.parent)
    append_event("init-subwiki", f"sub_wiki={path} root={path.parent}")
    refresh_registry(force=True)

    print(f"Directories created at: {path}")
    print(f"Remembered preferred sub-wiki: {path}")
    print(f"Remembered wiki root: {path.parent}")
    return 0


def print_candidates() -> int:
    candidates = refresh_registry(force=True)
    root = read_state(WIKI_ROOT_FILE)
    ambiguity = ambiguity_summary(candidates, root)
    print("Detecting sub-wikis...")
    print("---")
    if not candidates:
        print("NO_VAULTS_FOUND")
    else:
        for index, candidate in enumerate(candidates, start=1):
            flags = ", ".join(candidate.ambiguity_flags(root)) or "none"
            print(f"{index}. {candidate.canonical_path} (score={candidate.score}, flags={flags})")
    if ambiguity:
        print("---")
        print("Ambiguity notes:")
        for item in ambiguity:
            print(f"- {item}")
    append_event("detect", f"count={len(candidates)}")
    return 0


def usage() -> int:
    print(
        "Usage:\n"
        "  init-vault.sh                      # auto-detect and print sub-wiki candidates\n"
        "  init-vault.sh [sub-wiki-path]      # initialize a specific sub-wiki and remember it\n"
        "  init-vault.sh --set-root PATH      # remember the parent obsidian root that stores sub-wikis\n"
        "  init-vault.sh --remember PATH      # remember an existing preferred sub-wiki path\n"
        "  init-vault.sh --refresh-registry   # rebuild the runtime registry/log snapshot\n"
        "  init-vault.sh --show-current       # print current remembered root, selected sub-wiki, and top candidates\n"
        "  init-vault.sh --doctor             # validate state and registry consistency\n"
        "  init-vault.sh --repair             # repair safe state drift automatically\n"
        "  init-vault.sh --forget             # clear remembered root and sub-wiki paths"
    )
    return 0


def main(argv: list[str]) -> int:
    ensure_dirs()
    if not argv:
        return print_candidates()

    cmd = argv[0]
    if cmd in {"-h", "--help"}:
        return usage()
    if cmd == "--set-root":
        if len(argv) < 2:
            print("missing path for --set-root", file=sys.stderr)
            return 1
        return remember_root(argv[1])
    if cmd == "--remember":
        if len(argv) < 2:
            print("missing path for --remember", file=sys.stderr)
            return 1
        return remember_subwiki(argv[1])
    if cmd == "--refresh-registry":
        refresh_registry(force=True)
        print(f"Refreshed runtime registry: {REGISTRY_MD}")
        return 0
    if cmd == "--show-current":
        return show_current()
    if cmd == "--doctor":
        return doctor()
    if cmd == "--repair":
        return repair_state()
    if cmd == "--forget":
        return forget_paths()
    return initialize_subwiki(cmd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
