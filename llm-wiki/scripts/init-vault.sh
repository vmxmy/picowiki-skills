#!/usr/bin/env bash
# init-vault.sh — wrapper around the Python registry manager for llm-wiki

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 "$SCRIPT_DIR/registry_manager.py" "$@"
