#!/usr/bin/env bash
# init-vault.sh — Detect Obsidian vaults and initialize LLM Wiki structure
# Usage: bash init-vault.sh [vault-path]
#   If vault-path is provided, skip detection and use that path.
#   Otherwise, auto-detect vaults and print them for user confirmation.

set -euo pipefail

# --- Vault Detection ---
detect_vaults() {
  local vaults=()

  # 1. Parse Obsidian config (macOS)
  local obsidian_config="$HOME/Library/Application Support/obsidian/obsidian.json"
  if [[ -f "$obsidian_config" ]]; then
    # Extract vault paths from JSON (rough parse, no jq dependency)
    while IFS= read -r line; do
      if [[ "$line" =~ \"path\"[[:space:]]*:[[:space:]]*\"([^\"]+)\" ]]; then
        local p="${BASH_REMATCH[1]}"
        # Handle tilde expansion
        p="${p/#\~/$HOME}"
        if [[ -d "$p" ]]; then
          vaults+=("$p")
        fi
      fi
    done < "$obsidian_config"
  fi

  # 2. Find .obsidian directories (shallow search)
  while IFS= read -r -d '' obsdir; do
    local vault_root
    vault_root="$(dirname "$obsdir")"
    # Deduplicate
    local found=0
    for v in "${vaults[@]+"${vaults[@]}"}"; do
      if [[ "$v" == "$vault_root" ]]; then found=1; break; fi
    done
    if [[ $found -eq 0 ]]; then
      vaults+=("$vault_root")
    fi
  done < <(find "$HOME" -maxdepth 3 -name ".obsidian" -type d -print0 2>/dev/null)

  # 3. iCloud
  local icloud_path="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
  if [[ -d "$icloud_path" ]]; then
    for d in "$icloud_path"/*/; do
      if [[ -d "${d}.obsidian" ]]; then
        local found=0
        for v in "${vaults[@]+"${vaults[@]}"}"; do
          if [[ "$v" == "${d%/}" ]]; then found=1; break; fi
        done
        if [[ $found -eq 0 ]]; then
          vaults+=("${d%/}")
        fi
      fi
    done
  fi

  # Output results
  if [[ ${#vaults[@]} -eq 0 ]]; then
    echo "NO_VAULTS_FOUND"
  else
    for v in "${vaults[@]}"; do
      echo "$v"
    done
  fi
}

# --- Structure Initialization ---
init_structure() {
  local vault_path="$1"

  # Create directories
  mkdir -p "$vault_path/raw/assets"
  mkdir -p "$vault_path/wiki/sources"
  mkdir -p "$vault_path/wiki/concepts"
  mkdir -p "$vault_path/wiki/entities"
  mkdir -p "$vault_path/wiki/comparisons"
  mkdir -p "$vault_path/output"

  echo "Directories created at: $vault_path"
  echo "  raw/           — immutable source documents"
  echo "  raw/assets/    — images and attachments"
  echo "  wiki/sources/  — per-source summary pages"
  echo "  wiki/concepts/ — concept/topic pages"
  echo "  wiki/entities/ — people, orgs, products"
  echo "  wiki/comparisons/ — analyses and synthesis"
  echo "  output/        — query results and reports"
}

# --- Main ---
if [[ $# -ge 1 ]]; then
  # Explicit path provided
  vault_path="$1"
  if [[ ! -d "$vault_path" ]]; then
    echo "Creating new vault directory: $vault_path"
    mkdir -p "$vault_path"
  fi
  init_structure "$vault_path"
else
  # Auto-detect
  echo "Detecting Obsidian vaults..."
  echo "---"
  detect_vaults
fi
