#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "registry_manager.py"


def run(home: Path, *args: str, check: bool = True, stale_seconds: int = 600) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["HERMES_LLM_WIKI_STATE_DIR"] = str(home / ".hermes/state/llm-wiki")
    env["HERMES_LLM_WIKI_RUNTIME_DIR"] = str(home / ".hermes/skills/llm-wiki/runtime")
    env["HERMES_LLM_WIKI_SKILL_DIR"] = str(home / ".hermes/skills/llm-wiki")
    env["HERMES_LLM_WIKI_STALE_REFRESH_SECONDS"] = str(stale_seconds)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=check,
        text=True,
        capture_output=True,
        env=env,
    )


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"expected to find {needle!r} in output:\n{text}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="llm-wiki-test-") as tmp:
        home = Path(tmp)
        root = home / ".hermes/obsidian"
        wiki_a = root / "alpha-wiki"
        wiki_b = root / "beta-wiki"
        nested = root / "workspace" / "vault"

        for wiki in [wiki_a, wiki_b, nested]:
            (wiki / "raw").mkdir(parents=True, exist_ok=True)
            (wiki / "wiki").mkdir(parents=True, exist_ok=True)
            (wiki / "output").mkdir(parents=True, exist_ok=True)
            (wiki / "SCHEMA.md").write_text("# schema\n", encoding="utf-8")
            (wiki / "index.md").write_text("# index\n", encoding="utf-8")
            (wiki / "log.md").write_text("## init\n", encoding="utf-8")
            (wiki / ".obsidian").mkdir(exist_ok=True)

        legacy = home / "legacy-notes"
        (legacy / "articles").mkdir(parents=True, exist_ok=True)
        (legacy / "concepts").mkdir(parents=True, exist_ok=True)
        (legacy / "CLAUDE.md").write_text("# schema\n", encoding="utf-8")
        (legacy / "INDEX.md").write_text("# index\n", encoding="utf-8")
        (legacy / "log.md").write_text("## init\n", encoding="utf-8")

        mirror_root = home / "mirror-root"
        mirror_root.symlink_to(root, target_is_directory=True)

        result = run(home)
        assert_contains(result.stdout, str(wiki_a.resolve()))
        assert_contains(result.stdout, str(wiki_b.resolve()))
        assert_contains(result.stdout, str(nested.resolve()))
        assert_contains(result.stdout, str(legacy.resolve()))
        assert_contains(result.stdout, "score=")

        result = run(home, "--set-root", str(root))
        assert_contains(result.stdout, str(root.resolve()))
        assert_contains(result.stdout, "root_state_file_updated=yes")

        result = run(home, "--remember", str(wiki_a))
        assert_contains(result.stdout, str(wiki_a.resolve()))
        assert_contains(result.stdout, "subwiki_state_file_updated=yes")

        result = run(home, "--show-current")
        assert_contains(result.stdout, f"remembered_root={root.resolve()}")
        assert_contains(result.stdout, f"selected_sub_wiki={wiki_a.resolve()}")
        assert_contains(result.stdout, "recommended_candidate=")

        result = run(home, "--doctor")
        assert_contains(result.stdout, "status: healthy")
        assert_contains(result.stdout, "recommended_candidate:")

        registry_json = home / ".hermes/skills/llm-wiki/runtime/subwiki-registry.json"
        payload = json.loads(registry_json.read_text(encoding="utf-8"))
        if payload["schema_version"] != 2:
            raise AssertionError(f"expected schema_version=2, got {payload['schema_version']}")
        if payload["candidate_count"] < 4:
            raise AssertionError(f"expected >= 4 candidates, got {payload['candidate_count']}")
        if not payload["recommended_candidate"]:
            raise AssertionError("expected a recommended candidate")

        init_target = root / "gamma-wiki"
        result = run(home, str(init_target))
        assert_contains(result.stdout, str(init_target.resolve()))
        if not (init_target / "SCHEMA.md").exists():
            raise AssertionError("init should create SCHEMA.md")
        assert_contains((init_target / "SCHEMA.md").read_text(encoding="utf-8"), "# LLM Wiki Schema")

        result = run(home, "--remember", str(wiki_a))
        assert_contains(result.stdout, str(wiki_a.resolve()))

        selected_state = home / ".hermes/state/llm-wiki/selected-vault-path.txt"
        selected_state.write_text(str(home / "missing-wiki") + "\n", encoding="utf-8")
        result = run(home, "--doctor", check=False)
        if result.returncode == 0:
            raise AssertionError("doctor should fail when selected state is broken")
        assert_contains(result.stdout, "recommended_fixes:")

        result = run(home, "--repair")
        assert_contains(result.stdout, "cleared missing selected sub-wiki")

        result = run(home, "--doctor")
        assert_contains(result.stdout, "status: healthy")

        last_refresh = home / ".hermes/state/llm-wiki/last-refresh-at.txt"
        last_refresh.write_text("2000-01-01T00:00:00\n", encoding="utf-8")
        result = run(home, "--show-current", stale_seconds=1)
        assert_contains(result.stdout, "registry_status=fresh")

        result = run(home, "--forget")
        assert_contains(result.stdout, "Cleared remembered wiki root and selected sub-wiki")

        print("llm-wiki registry_manager tests passed")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
